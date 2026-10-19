"""Staging gives each run its own fixtures; harvest records what the run did to them.

Together these let an eval measure a skill's real filesystem contract. Before them, a with-skill run had
two contradictory instructions — the harness said "write to outputs/", the skill said "write to
<Product path>/docs/" — and every archived executor resolved it by sandboxing itself, so the assertions
about where files land were green because the skill was NOT followed.

The tests below pin the properties that make the measurement honest. Two matter most:
`test_arms_are_independent` (one arm's write must never become the other's input) and
`test_staging_rewrite_is_not_reported_as_a_run_change` (the baseline is the tree as staged, not the
pristine fixture — otherwise staging's own edit to every project.md reads as the run's work).

Drive the real CLIs as subprocesses, per test_fixture_guard.py.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent
STAGE = SCRIPTS / "stage_fixtures.py"
HARVEST = SCRIPTS / "harvest_run.py"

EXIT_OK = 0
EXIT_PRECONDITION = 2


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout


def _run(script: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args], capture_output=True, text=True
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A skill with two fixture products, one carrying an answered companion."""
    root = tmp_path / "instance"
    inputs = root / ".claude" / "skills" / "demo" / "evals" / "inputs"

    for name in ("alpha", "beta"):
        docs = inputs / name / "docs"
        docs.mkdir(parents=True)
        (inputs / name / "project.md").write_text(
            f"# {name}\n\n**Product path:** .claude/skills/demo/evals/inputs/{name}   "
            "<!-- eval fixture: RELATIVE; the with-skill config sandboxes the write. -->\n"
        )
        (docs / "PRD.md").write_text(f"# PRD {name}\n")
    (inputs / "alpha" / "docs" / "SRS_open_issues.md").write_text(
        "# Open issues\n\n- **Answer:** never expire\n- **Confirm or override:** confirm.\n"
    )
    # An annotations README at the inputs root (must NOT be copied) and one nested inside a product
    # (product content — must be copied).
    (inputs / "README.md").write_text("Case 1 expects a two-bucket companion.\n")
    (inputs / "alpha" / "docs" / "README.md").write_text("product-owned readme\n")

    (inputs.parent / "evals.json").write_text(
        json.dumps(
            {
                "skill_name": "demo",
                "evals": [
                    {
                        "id": 1,
                        "name": "case-one",
                        "prompt": "Read .claude/skills/demo/evals/inputs/alpha/project.md and go.",
                        "assertions": [],
                    },
                    {
                        "id": 2,
                        "name": "case-two",
                        "prompt": "Nothing here names a fixture; also ~/elsewhere/inputs/x stays.",
                        "assertions": [],
                    },
                ],
            }
        )
    )

    (root / ".gitignore").write_text(".claude/skills/*/evals/workspace/\n")
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "T")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "fixtures")
    return root


def _skill(repo: Path) -> str:
    return str(repo / ".claude" / "skills" / "demo")


def _ws(repo: Path) -> str:
    return str(repo / ".claude" / "skills" / "demo" / "evals" / "workspace" / "iteration-1")


def _stage(repo: Path) -> subprocess.CompletedProcess:
    return _run(STAGE, "--skill-dir", _skill(repo), "--workspace", _ws(repo))


# --------------------------------------------------------------------------- staging


def test_every_case_and_arm_gets_its_own_copy(repo: Path):
    assert _stage(repo).returncode == EXIT_OK

    ws = Path(_ws(repo))
    for case in ("case-one", "case-two"):
        for arm in ("with_skill", "without_skill"):
            assert (ws / case / arm / "inputs" / "alpha" / "docs" / "PRD.md").is_file()
            assert (ws / case / arm / "staged_manifest.json").is_file()


def test_arms_are_independent(repo: Path):
    """One arm's write must never reach the other — both arms run in parallel on one case."""
    _stage(repo)
    ws = Path(_ws(repo))
    mine = ws / "case-one" / "with_skill" / "inputs" / "alpha" / "docs"
    theirs = ws / "case-one" / "without_skill" / "inputs" / "alpha" / "docs"

    (mine / "SRS.md").write_text("written by the with-skill arm\n")

    assert not (theirs / "SRS.md").exists()


def test_binding_points_at_its_own_copy_and_stays_relative(repo: Path):
    """Absolute would flip the skill to its 'the repo is the product' branch — a different code path."""
    _stage(repo)
    text = (
        Path(_ws(repo)) / "case-one" / "with_skill" / "inputs" / "alpha" / "project.md"
    ).read_text()

    line = next(ln for ln in text.splitlines() if "Product path:" in ln)
    path = line.split("**Product path:**")[1].strip()
    assert not path.startswith("/"), "a staged binding must stay repo-relative"
    assert path.endswith("iteration-1/case-one/with_skill/inputs/alpha")
    assert "sandboxes the write" not in line, "the false sandbox claim must not reach the executor"


def test_annotations_readme_is_excluded_but_product_readme_is_kept(repo: Path):
    _stage(repo)
    staged = Path(_ws(repo)) / "case-one" / "with_skill" / "inputs"

    assert not (staged / "README.md").exists(), "the answer key must not be staged"
    assert (staged / "alpha" / "docs" / "README.md").is_file(), "product content must be"


def test_prompt_is_repointed_and_foreign_paths_are_left_alone(repo: Path):
    done = _stage(repo)
    manifest = json.loads(done.stdout)

    one = manifest["cases"]["case-one"]["with_skill"]["prompt"]
    assert "evals/inputs/alpha" not in one
    assert "iteration-1/case-one/with_skill/inputs/alpha" in one

    two = manifest["cases"]["case-two"]["with_skill"]["prompt"]
    assert "~/elsewhere/inputs/x" in two, "another instance's fixture is not ours to rewrite"


def test_the_pristine_fixture_is_untouched(repo: Path):
    before = _git(repo, "status", "--porcelain")
    _stage(repo)

    assert _git(repo, "status", "--porcelain") == before


def test_workspace_outside_the_repo_is_refused(repo: Path, tmp_path: Path):
    done = _run(STAGE, "--skill-dir", _skill(repo), "--workspace", str(tmp_path / "outside"))

    assert done.returncode == EXIT_PRECONDITION
    assert "must be inside the repo" in done.stderr


def test_a_skill_with_no_fixtures_is_a_clean_no_op(repo: Path):
    bare = repo / ".claude" / "skills" / "bare" / "evals"
    bare.mkdir(parents=True)
    (bare / "evals.json").write_text(json.dumps({"skill_name": "bare", "evals": []}))

    done = _run(STAGE, "--skill-dir", str(bare.parent), "--workspace", _ws(repo))

    assert done.returncode == EXIT_OK
    assert json.loads(done.stdout)["fixture_root"] is None


# --------------------------------------------------------------------------- harvest


def _harvest(repo: Path, case: str = "case-one", arm: str = "with_skill"):
    return _run(HARVEST, "--config-dir", str(Path(_ws(repo)) / case / arm))


def _delta(repo: Path, case: str = "case-one", arm: str = "with_skill") -> dict:
    return json.loads(
        (Path(_ws(repo)) / case / arm / "outputs" / "run_delta.json").read_text()
    )


def test_created_modified_deleted_are_classified(repo: Path):
    """The shape a fixed product-srs run produces: trail written, SRS folded, companion removed."""
    _stage(repo)
    docs = Path(_ws(repo)) / "case-one" / "with_skill" / "inputs" / "alpha" / "docs"
    (docs / "trail/srs").mkdir(parents=True)
    (docs / "trail/srs" / "cycle-1.md").write_bytes((docs / "SRS_open_issues.md").read_bytes())
    (docs / "PRD.md").write_text("# PRD alpha\n\nfolded\n")
    (docs / "SRS_open_issues.md").unlink()

    assert _harvest(repo).returncode == EXIT_OK

    delta = _delta(repo)
    assert delta["created"] == ["alpha/docs/trail/srs/cycle-1.md"]
    assert delta["modified"] == ["alpha/docs/PRD.md"]
    assert delta["deleted"] == ["alpha/docs/SRS_open_issues.md"]


def test_staging_rewrite_is_not_reported_as_a_run_change(repo: Path):
    """The baseline is the tree AS STAGED. Diffing the pristine fixture would blame the run for
    staging's own project.md rewrite — noise in three files per case."""
    _stage(repo)

    assert _harvest(repo).returncode == EXIT_OK

    delta = _delta(repo)
    assert delta == {**delta, "created": [], "modified": [], "deleted": []}


def test_reference_makes_wholeness_checkable_without_the_fixture(repo: Path):
    """'the answered companion is retired WHOLE' becomes a byte diff between two files in outputs/."""
    _stage(repo)
    docs = Path(_ws(repo)) / "case-one" / "with_skill" / "inputs" / "alpha" / "docs"
    original = (docs / "SRS_open_issues.md").read_bytes()
    (docs / "trail/srs").mkdir(parents=True)
    (docs / "trail/srs" / "cycle-1.md").write_bytes(original)
    (docs / "SRS_open_issues.md").unlink()

    _harvest(repo)

    outputs = Path(_ws(repo)) / "case-one" / "with_skill" / "outputs"
    trail = outputs / "product" / "alpha" / "docs" / "trail/srs" / "cycle-1.md"
    reference = outputs / "reference" / "alpha" / "docs" / "SRS_open_issues.md"
    assert trail.read_bytes() == reference.read_bytes() == original


def test_run_delta_sits_at_the_top_of_outputs(repo: Path):
    """Nothing reads outputs/ recursively — grading prompt, grader.md and the viewer are all one level.
    run_delta.json is the flat, always-visible record that makes a path assertion gradeable."""
    _stage(repo)
    _harvest(repo)

    outputs = Path(_ws(repo)) / "case-one" / "with_skill" / "outputs"
    assert (outputs / "run_delta.json").is_file()
    assert "run_delta.json" in [p.name for p in outputs.iterdir() if p.is_file()]


def test_harvest_without_staging_is_a_precondition_failure(repo: Path):
    config = Path(_ws(repo)) / "case-one" / "with_skill"
    (config / "inputs").mkdir(parents=True)

    done = _harvest(repo)

    assert done.returncode == EXIT_PRECONDITION
    assert "not staged" in done.stderr


def test_harvest_with_no_staged_inputs_is_a_clean_no_op(repo: Path):
    config = Path(_ws(repo)) / "case-five" / "with_skill"
    config.mkdir(parents=True)

    done = _harvest(repo, case="case-five")

    assert done.returncode == EXIT_OK
    assert "nothing to harvest" in done.stderr
