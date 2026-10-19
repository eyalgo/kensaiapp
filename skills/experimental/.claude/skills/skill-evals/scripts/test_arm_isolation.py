"""arm_isolation.py detects when one eval arm's executor operated inside its sibling arm's directory.

Both arms of a case (`with_skill` / `without_skill`, or any other pair a skill's evals.json declares)
run concurrently in sibling directories under `<workspace>/<case>/`, and nothing else on this harness
attributes a write to an arm: `harvest_run.py` computes its delta from a hash diff against the tree as
staged (`harvest_run.py:117-121`), which records that a file appeared, never which agent wrote it.

The one surviving signal is each arm's own account of what it did, at
`<case>/<arm>/outputs/transcript.md` — a file the harness already instructs every executor to write
(`run-skill-evals.js:312`), so the check reads something the harness already guarantees exists, in a
location it already fixes.

The false positive this guards hardest against is an arm naming its OWN directory, which every healthy
run does, repeatedly — `test_its_own_arm_is_not_a_crossing` is the test that matters most.

Drive the real CLI as a subprocess, per test_stage_and_harvest.py. The second half of this file drives
aggregate_benchmark.py, whose thin integration this check feeds.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent / "arm_isolation.py"
AGGREGATE = Path(__file__).resolve().parent / "aggregate_benchmark.py"

EXIT_OK = 0
EXIT_PRECONDITION = 2


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def _arm(workspace: Path, case: str, arm: str, transcript: str | None) -> Path:
    """A case/arm directory, with an outputs/transcript.md unless transcript is None."""
    arm_dir = workspace / case / arm
    outputs = arm_dir / "outputs"
    outputs.mkdir(parents=True)
    if transcript is not None:
        (outputs / "transcript.md").write_text(transcript)
    return arm_dir


# --------------------------------------------------------------------------- detection


def test_a_crossing_is_found(tmp_path: Path):
    """The real case this answers: without_skill named with_skill's own inputs and outputs
    (rationale.md § The defect)."""
    ws = tmp_path / "iteration-6"
    _arm(ws, "tag-external-source-with-locator", "with_skill", "wrote to my own inputs/mailmate\n")
    _arm(
        ws, "tag-external-source-with-locator", "without_skill",
        "Read the project binding at "
        ".claude/skills/product-prd/evals/workspace/iteration-6/tag-external-source-with-locator/"
        "with_skill/inputs/mailmate/project.md.\n",
    )

    done = _run(str(ws))
    assert done.returncode == EXIT_OK
    result = json.loads(done.stdout)

    assert len(result["flagged"]) == 1
    flagged = result["flagged"][0]
    assert flagged["case"] == "tag-external-source-with-locator"
    assert flagged["arm"] == "without_skill"
    assert flagged["sibling"] == "with_skill"


def test_the_check_is_symmetric(tmp_path: Path):
    """A with_skill transcript naming without_skill is reported the same way. Neither arm is
    privileged."""
    ws = tmp_path / "iteration-1"
    _arm(ws, "case-one", "without_skill", "produced my own output cleanly\n")
    _arm(ws, "case-one", "with_skill", "found .../without_skill/inputs/x.md already on disk\n")

    result = json.loads(_run(str(ws)).stdout)

    assert len(result["flagged"]) == 1
    flagged = result["flagged"][0]
    assert flagged["case"] == "case-one"
    assert flagged["arm"] == "with_skill"
    assert flagged["sibling"] == "without_skill"


def test_its_own_arm_is_not_a_crossing(tmp_path: Path):
    """A transcript that names only its own arm's paths — which every healthy run does, repeatedly —
    produces no finding. This is the false positive that would make the check worthless."""
    ws = tmp_path / "iteration-1"
    _arm(
        ws, "case-one", "with_skill",
        "with_skill wrote with_skill/outputs/PRD.md. with_skill is done. with_skill again.\n",
    )
    _arm(ws, "case-one", "without_skill", "without_skill produced its own baseline.\n")

    result = json.loads(_run(str(ws)).stdout)

    assert result["flagged"] == []


def test_sibling_arms_are_derived_not_hardcoded(tmp_path: Path):
    """A case with a third arm, or with arms named something other than today's pair, is still
    checked — the siblings of an arm are read from the directory, not a hardcoded pair."""
    ws = tmp_path / "iteration-1"
    _arm(ws, "case-one", "armA", "clean\n")
    _arm(ws, "case-one", "armB", "clean\n")
    _arm(ws, "case-one", "armC", "read armA/outputs/result.md by mistake\n")

    result = json.loads(_run(str(ws)).stdout)

    assert len(result["flagged"]) == 1
    assert result["flagged"][0]["arm"] == "armC"
    assert result["flagged"][0]["sibling"] == "armA"


def test_a_case_with_exactly_one_arm_has_no_sibling_to_cross_into(tmp_path: Path):
    ws = tmp_path / "iteration-1"
    _arm(ws, "case-one", "with_skill", "nothing to name — no sibling exists\n")

    result = json.loads(_run(str(ws)).stdout)

    assert result["flagged"] == []
    assert result["arms_checked"] == 1


def test_a_read_is_reported_the_same_as_a_write(tmp_path: Path):
    """The check reads prose and cannot reliably tell a read from a write — either one spoils the
    case (rationale.md § Why a read counts)."""
    ws = tmp_path / "iteration-1"
    _arm(ws, "case-one", "without_skill", "clean\n")
    _arm(
        ws, "case-one", "with_skill",
        "Read (not wrote) the sibling's file at .../without_skill/inputs/project.md.\n",
    )

    result = json.loads(_run(str(ws)).stdout)

    assert len(result["flagged"]) == 1
    assert result["flagged"][0]["arm"] == "with_skill"


def test_a_missing_transcript_is_unchecked_not_clean(tmp_path: Path):
    """Silence and a pass must not look alike."""
    ws = tmp_path / "iteration-1"
    (ws / "case-one" / "with_skill" / "outputs").mkdir(parents=True)  # no transcript.md
    _arm(ws, "case-one", "without_skill", "clean\n")

    result = json.loads(_run(str(ws)).stdout)

    assert result["flagged"] == []
    assert result["unchecked"] == [{"case": "case-one", "arm": "with_skill"}]
    assert result["arms_checked"] == 1, "the unchecked arm was never actually read"


def test_a_clean_round_says_so(tmp_path: Path):
    """The result records that the check ran and how many arms it read, even with nothing to flag —
    a check invisible when it passes cannot be told apart from one that never ran."""
    ws = tmp_path / "iteration-1"
    _arm(ws, "case-one", "with_skill", "clean\n")
    _arm(ws, "case-one", "without_skill", "clean\n")
    _arm(ws, "case-two", "with_skill", "clean\n")
    _arm(ws, "case-two", "without_skill", "clean\n")

    result = json.loads(_run(str(ws)).stdout)

    assert result["checked"] is True
    assert result["cases_checked"] == 2
    assert result["arms_checked"] == 4
    assert result["flagged"] == []


def test_non_case_entries_at_the_workspace_root_are_skipped(tmp_path: Path):
    """benchmark.json, benchmark.md, run_manifest.json, stage_manifest.json, fixture_guard.json,
    fixture_guard_report.md are all files at the workspace root — never treated as cases."""
    ws = tmp_path / "iteration-1"
    _arm(ws, "case-one", "with_skill", "clean\n")
    _arm(ws, "case-one", "without_skill", "clean\n")
    for name in (
        "benchmark.json", "benchmark.md", "run_manifest.json",
        "stage_manifest.json", "fixture_guard.json", "fixture_guard_report.md",
    ):
        (ws / name).write_text("not a case\n")

    done = _run(str(ws))

    assert done.returncode == EXIT_OK
    result = json.loads(done.stdout)
    assert result["cases_checked"] == 1


def test_workspace_not_found_is_a_precondition_failure(tmp_path: Path):
    done = _run(str(tmp_path / "does-not-exist"))

    assert done.returncode == EXIT_PRECONDITION


# --------------------------------------------------------------------------- aggregate_benchmark.py wiring


def _grading(pass_rate: float) -> str:
    return json.dumps(
        {"summary": {"pass_rate": pass_rate, "passed": int(pass_rate), "failed": 0 if pass_rate else 1,
                      "total": 1}}
    )


def _staged_case(
    workspace: Path, case: str, with_skill_pass: float, without_skill_pass: float,
    crossing_transcript: str | None = None,
) -> None:
    """A case with both arms' grading.json + outputs/transcript.md, matching the flat layout
    aggregate_benchmark.py's `_is_config_dir` recognizes. The crossing text, when given, lands only in
    the without_skill transcript — the shape of the real WS6 defect."""
    for arm, pass_rate in (("with_skill", with_skill_pass), ("without_skill", without_skill_pass)):
        arm_dir = workspace / case / arm
        arm_dir.mkdir(parents=True)
        (arm_dir / "grading.json").write_text(_grading(pass_rate))
        outputs = arm_dir / "outputs"
        outputs.mkdir()
        text = crossing_transcript if (crossing_transcript and arm == "without_skill") else "clean\n"
        (outputs / "transcript.md").write_text(text)


def _aggregate(workspace: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(AGGREGATE), str(workspace)], capture_output=True, text=True)


def test_a_flagged_case_is_recorded_in_benchmark_json(tmp_path: Path):
    ws = tmp_path / "round"
    _staged_case(ws, "clean-case", 1.0, 1.0)
    _staged_case(
        ws, "flagged-case", 1.0, 0.0,
        crossing_transcript=(
            "Read the project binding at .../flagged-case/with_skill/inputs/mailmate/project.md.\n"
        ),
    )

    done = _aggregate(ws)
    assert done.returncode == EXIT_OK

    benchmark = json.loads((ws / "benchmark.json").read_text())
    isolation = benchmark["arm_isolation"]
    assert isolation["checked"] is True
    assert [f["case"] for f in isolation["flagged"]] == ["flagged-case"]
    assert isolation["flagged"][0]["arm"] == "without_skill"
    assert isolation["flagged"][0]["sibling"] == "with_skill"


def test_flagged_case_pass_rates_are_not_excluded_from_the_aggregate(tmp_path: Path):
    """Owner decision 1 (rationale.md, 2026-07-27): annotate only — a flagged case's numbers still
    count toward the mean and the delta, exactly as an unflagged case's would."""
    ws = tmp_path / "round"
    _staged_case(ws, "clean-case", 1.0, 1.0)
    _staged_case(
        ws, "flagged-case", 1.0, 0.0,
        crossing_transcript="names .../flagged-case/with_skill/inputs/x by mistake\n",
    )

    done = _aggregate(ws)
    benchmark = json.loads((ws / "benchmark.json").read_text())

    run_summary = benchmark["run_summary"]
    assert run_summary["with_skill"]["pass_rate"]["mean"] == 1.0
    assert run_summary["without_skill"]["pass_rate"]["mean"] == 0.5
    assert done.returncode == EXIT_OK, "the flag must not change aggregate_benchmark.py's exit code"


def test_flagged_case_is_rendered_before_the_summary_table(tmp_path: Path):
    ws = tmp_path / "round"
    _staged_case(
        ws, "flagged-case", 1.0, 0.0,
        crossing_transcript="names .../flagged-case/with_skill/inputs/x by mistake\n",
    )

    _aggregate(ws)
    markdown = (ws / "benchmark.md").read_text()

    assert "flagged-case" in markdown
    isolation_pos = markdown.find("Arm Isolation")
    summary_pos = markdown.find("## Summary")
    assert -1 < isolation_pos < summary_pos, "the caveat must sit before or with the summary table"


def test_a_clean_round_renders_a_one_line_confirmation(tmp_path: Path):
    ws = tmp_path / "round"
    _staged_case(ws, "clean-case", 1.0, 1.0)

    _aggregate(ws)
    markdown = (ws / "benchmark.md").read_text()

    assert "Arm Isolation" in markdown
    assert "no cross-arm contamination found" in markdown


def test_the_flagged_report_names_the_matched_text(tmp_path: Path):
    """The report names the case, the arm whose transcript it was, AND the matched text — the third
    is what lets a reader judge the finding instead of taking it on trust (ad_hoc_plan.md, Task 1,
    'A crossing is found')."""
    ws = tmp_path / "round"
    _staged_case(
        ws, "flagged-case", 1.0, 0.0,
        crossing_transcript="Wrote the PRD at .../flagged-case/with_skill/inputs/mailmate/docs/PRD.md.\n",
    )

    _aggregate(ws)
    flagged = json.loads((ws / "benchmark.json").read_text())["arm_isolation"]["flagged"][0]

    assert "with_skill/inputs/mailmate/docs/PRD.md" in flagged["matched"]
    assert flagged["matched"] in (ws / "benchmark.md").read_text()


def test_benchmark_json_keeps_every_key_it_already_carried(tmp_path: Path):
    """The round's JSON gains the check's result under exactly one new top-level key; every key the
    file already carried is still present (ad_hoc_plan.md, Task 1, 'Recorded in benchmark.json')."""
    ws = tmp_path / "round"
    _staged_case(ws, "clean-case", 1.0, 1.0)

    _aggregate(ws)
    benchmark = json.loads((ws / "benchmark.json").read_text())

    assert {"metadata", "runs", "run_summary", "notes"} <= set(benchmark)
    assert set(benchmark) - {"metadata", "runs", "run_summary", "notes"} == {"arm_isolation"}, (
        "exactly one new top-level key"
    )


def test_the_delta_is_not_recomputed_for_a_flagged_round(tmp_path: Path):
    """Owner decision 1 (rationale.md, 2026-07-27): the flag annotates — it does not exclude a
    flagged case from the aggregate OR recompute the delta. With the contaminated case still counted
    the delta spans 1.0 vs 0.5; excluding it would collapse the delta to +0.00."""
    ws = tmp_path / "round"
    _staged_case(ws, "clean-case", 1.0, 1.0)
    _staged_case(
        ws, "flagged-case", 1.0, 0.0,
        crossing_transcript="names .../flagged-case/with_skill/inputs/x by mistake\n",
    )

    _aggregate(ws)
    delta = json.loads((ws / "benchmark.json").read_text())["run_summary"]["delta"]

    assert delta["pass_rate"] == "+0.50"


def test_exit_2_on_a_malformed_grading_is_neither_triggered_nor_suppressed(tmp_path: Path):
    """The check must neither trigger aggregate_benchmark.py's exit 2 nor suppress it. A round that
    is BOTH contaminated and holed still exits 2 — the hole in the data is the louder failure, and
    the advisory flag must not swallow it (ad_hoc_plan.md, Task 1, 'Exit code unchanged')."""
    ws = tmp_path / "round"
    _staged_case(
        ws, "flagged-case", 1.0, 0.0,
        crossing_transcript="names .../flagged-case/with_skill/inputs/x by mistake\n",
    )
    (ws / "flagged-case" / "with_skill" / "grading.json").write_text('{"summary": {unescaped}')

    done = _aggregate(ws)

    assert done.returncode == 2, "an unreadable grading must still exit 2 on a flagged round"


def test_a_non_utf8_transcript_does_not_strand_the_round(tmp_path: Path):
    """The check is advisory, not fatal: a transcript it cannot decode must not cost the round its
    benchmark. A round costs roughly 30M executor tokens, and the intent is explicit that making the
    check fatal 'would also strand an expensive round with no benchmark at all' (ad_hoc_plan.md,
    Task 1). Transcripts are free text written by a model, so undecodable bytes are the untrusted
    input this check newly reads."""
    ws = tmp_path / "round"
    _staged_case(ws, "case-one", 1.0, 0.0)
    (ws / "case-one" / "without_skill" / "outputs" / "transcript.md").write_bytes(
        b"wrote \xff\xfe my own output\n"
    )

    done = _aggregate(ws)

    assert done.returncode == EXIT_OK, "an undecodable transcript must not change the exit code"
    assert (ws / "benchmark.json").exists(), "the round must still get its benchmark"
    assert (ws / "benchmark.md").exists()


def test_a_round_whose_cases_have_no_arms_reports_zero_arms_read(tmp_path: Path):
    """A clean result still records how many arms it read (ad_hoc_plan.md, Task 1, 'A clean round
    says so'). A round staged but never executed has case directories and no arm directories at all,
    so the honest number is zero — it must not report a count it did not earn."""
    ws = tmp_path / "iteration-5"
    (ws / "case-one").mkdir(parents=True)
    (ws / "case-two").mkdir(parents=True)

    result = json.loads(_run(str(ws)).stdout)

    assert result["cases_checked"] == 2
    assert result["arms_checked"] == 0, "no arm was read, so no arm may be counted as read"
    assert result["flagged"] == []


# --------------------------------------------------------- rescue is not crime (recovered status)


def _delta(arm_dir: Path, created: list[str]) -> None:
    """The run_delta.json harvest_run.py writes — the recorded fact of what landed in this arm's
    own tree. Absent in the tests above on purpose: an arm with no delta reads as one whose work
    went elsewhere, which is the pre-existing flagged behaviour."""
    (arm_dir / "outputs" / "run_delta.json").write_text(
        json.dumps({"created": created, "modified": [], "deleted": []})
    )


def test_naming_a_sibling_while_producing_your_own_work_is_recovered_not_contaminated(tmp_path: Path):
    """product-prd iteration-7, measured. Since 701db7f the executor prompt *instructs* a run handed
    a path outside its own tree to say so and use its own — so a mention-only check reports the fence
    working as a spoiled round. A working guard that cries wolf is worse than no guard."""
    ws = tmp_path / "iteration-7"
    a = _arm(ws, "tag-external-source-with-locator", "without_skill",
             "The task named a with_skill/.../project.md binding path, but my staged tree is "
             "without_skill/. I resolved the binding to my own tree.\n")
    _delta(a, ["mailmate/docs/PRD.md"])
    b = _arm(ws, "tag-external-source-with-locator", "with_skill", "worked in my own inputs\n")
    _delta(b, ["mailmate/docs/PRD.md"])

    result = json.loads(_run(str(ws)).stdout)
    assert result["flagged"] == []
    assert [e["arm"] for e in result["recovered"]] == ["without_skill"]


def test_naming_a_sibling_while_producing_nothing_is_still_contaminated(tmp_path: Path):
    """product-prd iteration-6, measured: the arm's own tree stayed empty because its work went next
    door, and it graded 0.0. The real crossing must not be softened by the new status."""
    ws = tmp_path / "iteration-6"
    a = _arm(ws, "tag-external-source-with-locator", "without_skill",
             "Read the project binding at .../with_skill/inputs/mailmate/project.md and wrote it there.\n")
    _delta(a, [])
    b = _arm(ws, "tag-external-source-with-locator", "with_skill", "worked in my own inputs\n")
    _delta(b, ["mailmate/docs/PRD.md"])

    result = json.loads(_run(str(ws)).stdout)
    assert [e["arm"] for e in result["flagged"]] == ["without_skill"]
    assert result["recovered"] == []


def test_recovered_reaches_the_json_so_a_bad_binding_is_not_invisible(tmp_path: Path):
    """The fence absorbs the consequence, which is exactly why the cause needs reporting: nothing
    downstream goes wrong, so an unreported recovery is a harness fault nobody ever sees."""
    ws = tmp_path / "iteration-7"
    a = _arm(ws, "case-one", "without_skill", "handed a with_skill path; used my own\n")
    _delta(a, ["out.md"])
    b = _arm(ws, "case-one", "with_skill", "mine\n")
    _delta(b, ["out.md"])

    result = json.loads(_run(str(ws)).stdout)
    assert result["recovered"][0]["sibling"] == "with_skill"
    assert result["recovered"][0]["matched"]


def test_aggregate_imports_under_both_invocation_forms(tmp_path: Path):
    """SKILL.md § Step 3 documents `python -m scripts.aggregate_benchmark`; the tests and the workflow
    use the plain script form. The script form puts scripts/ on sys.path, the -m form does not — so a
    bare `import arm_isolation` raised ModuleNotFoundError under exactly the invocation the skill tells
    a caller to run, and shipped that way because every test drove the other form. Both must resolve."""
    ws = tmp_path / "iteration-1"
    a = _arm(ws, "case-one", "with_skill", "mine\n")
    (a / "outputs" / "run_delta.json").write_text(json.dumps({"created": ["x"], "modified": [], "deleted": []}))
    (a.parent / "with_skill" / "grading.json").write_text(_grading(1.0))
    b = _arm(ws, "case-one", "without_skill", "mine\n")
    (b / "outputs" / "run_delta.json").write_text(json.dumps({"created": ["x"], "modified": [], "deleted": []}))
    (b.parent / "without_skill" / "grading.json").write_text(_grading(0.0))

    skill_evals = AGGREGATE.parent.parent
    for argv, label in (
        (["-m", "scripts.aggregate_benchmark"], "-m package form (documented)"),
        (["scripts/aggregate_benchmark.py"], "plain script form"),
    ):
        done = subprocess.run(
            [sys.executable, *argv, str(ws), "--skill-name", "demo"],
            cwd=str(skill_evals), capture_output=True, text=True,
        )
        assert done.returncode == EXIT_OK, f"{label} failed: {done.stderr[-400:]}"
        assert (ws / "benchmark.json").is_file(), f"{label} produced no benchmark"
