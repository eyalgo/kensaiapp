"""`aggregate_benchmark.py` never prints a confident pass rate over a hole it can detect.

The incident this guards against: a grader wrote `grading.json` one directory level too high (into
the case dir instead of the arm dir). `_is_config_dir` requires a `grading.json` at flat or `run-*`
level (`:152-160`), so the gradingless arm was never *excluded* — it was never *seen*: `_is_eval_dir`
doesn't count it (`:163-167`) and `load_run_results` walks past it (`:187-238`). The well-argued
`MALFORMED_GRADINGS` guard (`:104-119`, `:523-538`) never got a chance to fire, because it only ever
sees a `grading.json` that exists and fails to parse — not one that was never there.

This file adds the module's first test coverage in two layers:

- **Task 1 / Task 2 sections** call `load_run_results` / the count check directly (in-process import,
  unlike every sibling test file in this directory, which drives the CLI as a subprocess) — the
  behaviours under test are `load_run_results`'s return value and the two module-level detector lists,
  neither of which is observable through stdout/exit-code alone.
- **Task 3 section** drives the script as a subprocess, matching the house pattern (`test_arm_isolation.py`,
  `test_fixture_guard.py`) — end-to-end behaviours (exit code, stderr, the written artifacts) are
  exactly what a subprocess invocation observes.

Fixtures are built fresh in `tmp_path` for every test; nothing here reads a committed workspace.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import aggregate_benchmark  # noqa: E402  (import follows the sys.path line it depends on)

AGGREGATE = SCRIPTS_DIR / "aggregate_benchmark.py"

EXIT_OK = 0
EXIT_INCOMPLETE = 2


@pytest.fixture(autouse=True)
def _reset_module_state():
    """ABSENT_ARMS and MALFORMED_GRADINGS are module-level lists that persist across calls within
    one process (the pre-existing MALFORMED_GRADINGS wart, `aggregate_benchmark.py:99-101`) — reset
    around every test so one test's findings never leak into the next."""
    aggregate_benchmark.ABSENT_ARMS.clear()
    aggregate_benchmark.MALFORMED_GRADINGS.clear()
    yield
    aggregate_benchmark.ABSENT_ARMS.clear()
    aggregate_benchmark.MALFORMED_GRADINGS.clear()


# --------------------------------------------------------------------------- fixture helpers


def _grading_json(pass_rate: float = 1.0) -> str:
    return json.dumps({
        "summary": {"pass_rate": pass_rate, "passed": 1, "failed": 0, "total": 1},
    })


def _eval_dir(workspace: Path, name: str, with_metadata: bool = True) -> Path:
    """eval_metadata.json carries no eval_id, so _read_eval_id falls back to the eval's sorted
    position (`aggregate_benchmark.py:170-184`) — unique per eval directory, which matters for
    Task 2's per-eval-id cell counting."""
    eval_dir = workspace / name
    eval_dir.mkdir(parents=True)
    if with_metadata:
        (eval_dir / "eval_metadata.json").write_text(json.dumps({}))
    return eval_dir


def _graded_arm(eval_dir: Path, arm: str, pass_rate: float = 1.0) -> Path:
    """A flat-layout arm directory with a valid grading.json."""
    arm_dir = eval_dir / arm
    arm_dir.mkdir(parents=True)
    (arm_dir / "grading.json").write_text(_grading_json(pass_rate))
    return arm_dir


def _nested_graded_arm(eval_dir: Path, arm: str, run: str = "run-1", pass_rate: float = 1.0) -> Path:
    """The legacy nested layout: <config>/run-N/grading.json."""
    run_dir = eval_dir / arm / run
    run_dir.mkdir(parents=True)
    (run_dir / "grading.json").write_text(_grading_json(pass_rate))
    return eval_dir / arm


def _empty_arm(eval_dir: Path, arm: str) -> Path:
    """An arm directory the harness created but that never received a grading."""
    arm_dir = eval_dir / arm
    arm_dir.mkdir(parents=True)
    return arm_dir


def _empty_run_arm(eval_dir: Path, arm: str, run: str = "run-1") -> Path:
    """An arm with a run-* directory that holds no grading.json — the legacy-layout hole."""
    run_dir = eval_dir / arm / run
    run_dir.mkdir(parents=True)
    return eval_dir / arm


def _malformed_arm(eval_dir: Path, arm: str) -> Path:
    arm_dir = eval_dir / arm
    arm_dir.mkdir(parents=True)
    (arm_dir / "grading.json").write_text("{not valid json")
    return arm_dir


# --------------------------------------------------------------------------- Task 1 — discovery-time detection


def test_incident_shape_is_detected_and_named(tmp_path: Path, capsys):
    """Fixture: two evals, each with two arms; one arm dir present but its grading.json moved up
    into the case dir. Exactly one ABSENT_ARMS entry names `<case>/<arm>`, the printed ERROR names
    the arm path, the message names the stray case-level grading.json — and every graded arm is
    still present in the returned results, unchanged."""
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "reentry-fold-and-close")
    _graded_arm(eval1, "with_skill")
    _empty_arm(eval1, "without_skill")
    (eval1 / "grading.json").write_text(_grading_json())  # the stray, misplaced file

    eval2 = _eval_dir(ws, "second-case")
    _graded_arm(eval2, "with_skill")
    _graded_arm(eval2, "without_skill")

    results = aggregate_benchmark.load_run_results(ws)

    assert len(aggregate_benchmark.ABSENT_ARMS) == 1
    identifier, reason = aggregate_benchmark.ABSENT_ARMS[0]
    assert identifier == "reentry-fold-and-close/without_skill"
    assert "grading.json" in reason
    assert "reentry-fold-and-close/grading.json" in reason

    err = capsys.readouterr().out
    assert "ERROR" in err
    assert "reentry-fold-and-close/without_skill" in err

    assert len(results["with_skill"]) == 2
    assert len(results["without_skill"]) == 1


def test_absent_grading_with_no_stray_file_is_still_detected(tmp_path: Path):
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "case-a")
    _graded_arm(eval1, "with_skill")
    _empty_arm(eval1, "without_skill")

    aggregate_benchmark.load_run_results(ws)

    assert len(aggregate_benchmark.ABSENT_ARMS) == 1
    identifier, reason = aggregate_benchmark.ABSENT_ARMS[0]
    assert identifier == "case-a/without_skill"
    assert "misplaced" not in reason
    assert "stray" not in reason


def test_whole_eval_with_no_graded_arm_is_detected(tmp_path: Path):
    """Eval dir with eval_metadata.json and two arm dirs, neither holding a grading — both arms
    are recorded (naming the eval), and load_run_results's results contain nothing for it."""
    ws = tmp_path / "workspace"
    broken_eval = _eval_dir(ws, "abandoned-case")
    _empty_arm(broken_eval, "with_skill")
    _empty_arm(broken_eval, "without_skill")

    good_eval = _eval_dir(ws, "healthy-case")
    _graded_arm(good_eval, "with_skill")
    _graded_arm(good_eval, "without_skill")

    results = aggregate_benchmark.load_run_results(ws)

    identifiers = {identifier for identifier, _ in aggregate_benchmark.ABSENT_ARMS}
    assert "abandoned-case/with_skill" in identifiers
    assert "abandoned-case/without_skill" in identifiers

    assert len(results["with_skill"]) == 1
    assert len(results["without_skill"]) == 1


def test_complete_workspace_records_nothing(tmp_path: Path, capsys):
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "case-a")
    _graded_arm(eval1, "with_skill")
    _graded_arm(eval1, "without_skill")

    aggregate_benchmark.load_run_results(ws)

    assert aggregate_benchmark.ABSENT_ARMS == []
    assert "ERROR" not in capsys.readouterr().out


def test_legacy_nested_layout_both_directions(tmp_path: Path):
    """An arm with run-1/grading.json is not flagged; an arm whose only run-* dirs hold no
    grading.json is flagged."""
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "case-a")
    _nested_graded_arm(eval1, "with_skill")
    _empty_run_arm(eval1, "without_skill")

    results = aggregate_benchmark.load_run_results(ws)

    identifiers = {identifier for identifier, _ in aggregate_benchmark.ABSENT_ARMS}
    assert "case-a/without_skill" in identifiers
    assert "case-a/with_skill" not in identifiers
    assert len(results["with_skill"]) == 1


def test_malformed_but_present_grading_is_not_double_flagged(tmp_path: Path):
    """An arm whose grading.json exists but is invalid JSON lands in MALFORMED_GRADINGS
    (existing behaviour) and produces no absent-arm entry."""
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "case-a")
    _malformed_arm(eval1, "with_skill")
    _graded_arm(eval1, "without_skill")

    aggregate_benchmark.load_run_results(ws)

    assert aggregate_benchmark.ABSENT_ARMS == []
    assert len(aggregate_benchmark.MALFORMED_GRADINGS) == 1


def test_plain_files_at_eval_level_are_never_flagged(tmp_path: Path):
    """eval_metadata.json sitting beside the arms is not treated as an arm."""
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "case-a", with_metadata=True)
    _graded_arm(eval1, "with_skill")
    _graded_arm(eval1, "without_skill")

    aggregate_benchmark.load_run_results(ws)

    assert aggregate_benchmark.ABSENT_ARMS == []


# --------------------------------------------------------------------------- Task 2 — the count check


def _result(eval_id: int, run_number: int = 1) -> dict:
    """A minimal parsed-result dict, the shape load_run_results returns per run."""
    return {
        "eval_id": eval_id,
        "run_number": run_number,
        "pass_rate": 1.0,
        "passed": 1,
        "failed": 0,
        "total": 1,
        "time_seconds": 0.0,
        "expectations": [],
        "notes": [],
    }


def test_the_incident_shape_is_caught_by_count_alone():
    """One configuration covers eval ids {1,2}, the other {1,2,3}; manifest
    runs_per_configuration: 1 → one entry naming the short configuration, eval 3, 0 of 1."""
    results = {
        "with_skill": [_result(1), _result(2)],
        "without_skill": [_result(1), _result(2), _result(3)],
    }
    manifest = {"runs_per_configuration": 1}

    aggregate_benchmark._check_result_matrix(results, manifest)

    assert len(aggregate_benchmark.ABSENT_ARMS) == 1
    identifier, reason = aggregate_benchmark.ABSENT_ARMS[0]
    assert "with_skill" in identifier
    assert "3" in identifier
    assert "0 of 1" in reason


def test_a_full_matrix_with_a_manifest_records_nothing():
    results = {
        "with_skill": [_result(1), _result(2)],
        "without_skill": [_result(1), _result(2)],
    }
    manifest = {"runs_per_configuration": 1}

    aggregate_benchmark._check_result_matrix(results, manifest)

    assert aggregate_benchmark.ABSENT_ARMS == []


def test_a_full_matrix_without_a_manifest_records_nothing():
    results = {
        "with_skill": [_result(1), _result(2)],
        "without_skill": [_result(1), _result(2)],
    }

    aggregate_benchmark._check_result_matrix(results, None)

    assert aggregate_benchmark.ABSENT_ARMS == []


def test_without_a_manifest_an_uneven_cell_is_caught_against_the_observed_maximum():
    """One cell holds 1 run while the others hold 2 → flagged, with no manifest to declare
    the expectation."""
    results = {
        "with_skill": [_result(1), _result(1, run_number=2), _result(2), _result(2, run_number=2)],
        "without_skill": [_result(1), _result(1, run_number=2), _result(2)],
    }

    aggregate_benchmark._check_result_matrix(results, None)

    assert len(aggregate_benchmark.ABSENT_ARMS) == 1
    identifier, reason = aggregate_benchmark.ABSENT_ARMS[0]
    assert "without_skill" in identifier
    assert "2" in identifier
    assert "1 of 2" in reason


def test_the_manifests_declaration_outranks_observed_uniformity():
    """Manifest says runs_per_configuration: 2, every cell holds 1 → every cell flagged. A
    declared expectation must not be overridden by data that merely looks complete."""
    results = {
        "with_skill": [_result(1)],
        "without_skill": [_result(1)],
    }
    manifest = {"runs_per_configuration": 2}

    aggregate_benchmark._check_result_matrix(results, manifest)

    assert len(aggregate_benchmark.ABSENT_ARMS) == 2
    for identifier, reason in aggregate_benchmark.ABSENT_ARMS:
        assert "1 of 2" in reason


def test_both_detectors_may_name_the_same_hole(tmp_path: Path):
    """On the Task-1 incident fixture, the Task-1 entry (disk walk) and the Task-2 entry (count
    check) coexist — nothing deduplicates them. A second, fully-graded eval is needed so
    "without_skill" is a known configuration for Task 2's matrix to check against."""
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "reentry-fold-and-close")
    _graded_arm(eval1, "with_skill")
    _empty_arm(eval1, "without_skill")
    (eval1 / "grading.json").write_text(_grading_json())

    eval2 = _eval_dir(ws, "second-case")
    _graded_arm(eval2, "with_skill")
    _graded_arm(eval2, "without_skill")

    results = aggregate_benchmark.load_run_results(ws)
    task1_count = len(aggregate_benchmark.ABSENT_ARMS)
    assert task1_count == 1  # sanity: Task 1's own entry landed first

    aggregate_benchmark._check_result_matrix(results, {"runs_per_configuration": 1})

    assert len(aggregate_benchmark.ABSENT_ARMS) == task1_count + 1


# --------------------------------------------------------------------------- Task 3 — the hole is loud


def _run_aggregate(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(AGGREGATE), *args], capture_output=True, text=True
    )


def test_a_holed_fixture_fails_loudly_end_to_end(tmp_path: Path):
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "reentry-fold-and-close")
    _graded_arm(eval1, "with_skill")
    _empty_arm(eval1, "without_skill")
    (eval1 / "grading.json").write_text(_grading_json())
    output = tmp_path / "out" / "benchmark.json"
    output.parent.mkdir()

    done = _run_aggregate(str(ws), "--output", str(output))

    assert done.returncode == EXIT_INCOMPLETE
    assert "INCOMPLETE" in done.stderr
    assert "reentry-fold-and-close/without_skill" in done.stderr

    benchmark = json.loads(output.read_text())
    assert any("reentry-fold-and-close/without_skill" in note for note in benchmark["notes"])
    assert len(benchmark["runs"]) == 1  # only the one grading that parsed

    md_text = output.with_suffix(".md").read_text()
    assert "## Notes" in md_text
    assert "reentry-fold-and-close/without_skill" in md_text


def test_a_complete_fixture_is_untouched_by_the_change(tmp_path: Path):
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "case-a")
    _graded_arm(eval1, "with_skill")
    _graded_arm(eval1, "without_skill")
    output = tmp_path / "out" / "benchmark.json"
    output.parent.mkdir()

    done = _run_aggregate(str(ws), "--output", str(output))

    assert done.returncode == EXIT_OK
    assert "INCOMPLETE" not in done.stderr
    benchmark = json.loads(output.read_text())
    assert benchmark["notes"] == []


def test_absent_and_malformed_together_are_both_surfaced(tmp_path: Path):
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "case-a")
    _malformed_arm(eval1, "with_skill")
    _graded_arm(eval1, "without_skill")

    eval2 = _eval_dir(ws, "case-b")
    _graded_arm(eval2, "with_skill")
    _empty_arm(eval2, "without_skill")
    output = tmp_path / "out" / "benchmark.json"
    output.parent.mkdir()

    done = _run_aggregate(str(ws), "--output", str(output))

    assert done.returncode == EXIT_INCOMPLETE
    benchmark = json.loads(output.read_text())
    joined_notes = " ".join(benchmark["notes"])
    assert "MALFORMED GRADING" in joined_notes
    assert "ABSENT ARM" in joined_notes
    assert "malformed" in done.stderr.lower()
    assert "case-b/without_skill" in done.stderr


def test_benchmark_artifacts_are_written_even_on_failure(tmp_path: Path):
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "case-a")
    _graded_arm(eval1, "with_skill")
    _empty_arm(eval1, "without_skill")
    output = tmp_path / "out" / "benchmark.json"
    output.parent.mkdir()

    done = _run_aggregate(str(ws), "--output", str(output))

    assert done.returncode == EXIT_INCOMPLETE
    assert output.exists()
    assert output.with_suffix(".md").exists()


# ------------------------------------------------- integrity pass — intent-derived, not in the plan's
# ------------------------------------------------- `Behaviours to verify` lists but stated in its intent
#
# The plan's Task 2 intent paragraph states *why* the count check is not redundant with Task 1's disk
# walk, and its § "Configuration names stay generic" states a containment the behaviour lists never
# exercise. Task 1's "plain files at eval level are never flagged" is stated over any plain file, not
# only `eval_metadata.json`. These four tests come from those sentences.


def test_an_arm_directory_absent_from_disk_is_invisible_to_the_disk_walk(tmp_path: Path):
    """Task 2's first stated reason for existing: an arm directory that is *entirely absent* from
    disk leaves nothing for Task 1's walk to see, so the walk must record nothing for it. If this
    ever flags, the count check below is not the thing catching the hole."""
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "case-a")
    _graded_arm(eval1, "with_skill")           # no without_skill directory at all

    eval2 = _eval_dir(ws, "case-b")
    _graded_arm(eval2, "with_skill")
    _graded_arm(eval2, "without_skill")

    aggregate_benchmark.load_run_results(ws)

    assert aggregate_benchmark.ABSENT_ARMS == []


def test_an_arm_directory_absent_from_disk_is_caught_by_the_count_check(tmp_path: Path):
    """The same hole, through the whole tool: the count check must name the empty cell and the run
    must fail with exit 2 — the disk walk cannot reach this one."""
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "case-a")
    _graded_arm(eval1, "with_skill")           # no without_skill directory at all

    eval2 = _eval_dir(ws, "case-b")
    _graded_arm(eval2, "with_skill")
    _graded_arm(eval2, "without_skill")
    output = tmp_path / "out" / "benchmark.json"
    output.parent.mkdir()

    done = _run_aggregate(str(ws), "--output", str(output))

    assert done.returncode == EXIT_INCOMPLETE
    assert "without_skill" in done.stderr
    benchmark = json.loads(output.read_text())
    assert any(
        note.startswith("ABSENT ARM:") and "without_skill" in note and "0 of 1" in note
        for note in benchmark["notes"]
    ), benchmark["notes"]


def test_a_nested_cell_short_of_the_manifests_count_is_caught_from_disk(tmp_path: Path):
    """Task 2's second stated reason for existing: a nested-layout cell that has *some* runs but
    fewer than expected — `run-2` gone while `run-1` remains, which today is only a stray warning.
    Driven from disk with a real run_manifest.json, so the manifest's declaration has to reach the
    check through generate_benchmark, not be handed in by the test."""
    ws = tmp_path / "workspace"
    (ws).mkdir(parents=True, exist_ok=True)
    eval1 = _eval_dir(ws, "case-a")
    _nested_graded_arm(eval1, "with_skill", run="run-1")
    _nested_graded_arm(eval1, "with_skill", run="run-2")
    _nested_graded_arm(eval1, "without_skill", run="run-1")
    (eval1 / "without_skill" / "run-2").mkdir()          # the run that never produced a grading
    (ws / "run_manifest.json").write_text(json.dumps({"runs_per_configuration": 2}))

    benchmark = aggregate_benchmark.generate_benchmark(ws)

    # The arm itself still has run-1, so it is a config dir and Task 1 must not flag it.
    assert all("without_skill" not in i or "of" in r for i, r in aggregate_benchmark.ABSENT_ARMS)
    assert any(
        note.startswith("ABSENT ARM:") and "without_skill" in note and "1 of 2" in note
        for note in benchmark["notes"]
    ), benchmark["notes"]


def test_configuration_names_are_never_hardcoded(tmp_path: Path):
    """The plan's Task 2 containment: nothing hardcodes with_skill / without_skill — the matrix is
    over whatever configurations were found. Both detectors must fire on arms named anything else."""
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "case-a")
    _graded_arm(eval1, "arm_alpha")
    _empty_arm(eval1, "arm_beta")

    eval2 = _eval_dir(ws, "case-b")
    _graded_arm(eval2, "arm_alpha")
    _graded_arm(eval2, "arm_beta")

    results = aggregate_benchmark.load_run_results(ws)
    assert [i for i, _ in aggregate_benchmark.ABSENT_ARMS] == ["case-a/arm_beta"]

    aggregate_benchmark._check_result_matrix(results, {"runs_per_configuration": 1})

    identifiers = [i for i, _ in aggregate_benchmark.ABSENT_ARMS]
    assert any(i.startswith("arm_beta / eval ") for i in identifiers), identifiers


def test_an_unrelated_plain_file_at_eval_level_is_never_flagged(tmp_path: Path):
    """"Plain files at eval level are never flagged" is stated over any file, not only
    eval_metadata.json — an arm is a *directory* without a grading, never a file."""
    ws = tmp_path / "workspace"
    eval1 = _eval_dir(ws, "case-a")
    _graded_arm(eval1, "with_skill")
    _graded_arm(eval1, "without_skill")
    (eval1 / "stage_manifest.json").write_text(json.dumps({}))
    (eval1 / "notes.md").write_text("scratch")

    aggregate_benchmark.load_run_results(ws)

    assert aggregate_benchmark.ABSENT_ARMS == []
