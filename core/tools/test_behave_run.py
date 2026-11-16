"""Behave on a throwaway copy: the report it gives, and what it leaves as it found it.

Layer 2: a real git repository, the starter's real lock and a real `uv run --locked behave`, all in
the test's temporary folder. The pinned toolchain settings reach `uv` the way
`test_behave_starter.py` hands them, so the run needs no network. Scenarios are written by the tests
as small features over one step, except the first test, which runs the starter whole.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from behave_run import BehaveReport, Overlay, ThrowawayBehave

REPO_ROOT = Path(__file__).resolve().parents[2]
STARTER = REPO_ROOT / "core" / "templates" / "behave-starter"
FOLDER = ".behave"
TOOLCHAIN_SETTINGS = ("UV_CACHE_DIR", "UV_PYTHON_INSTALL_DIR", "PLAYWRIGHT_BROWSERS_PATH")
STEP = 'from behave import given\n\n\n@given("a step")\ndef a_step(context):\n    pass\n'
FAILING_STEP = (
    'from behave import given\n\n\n@given("a failing step")\ndef a_failing_step(context):\n'
    '    raise AssertionError("fails")\n'
)
PASSING_FEATURE = "Feature: Passing\n\n  Scenario: Holds\n    Given a step\n"
FAILING_FEATURE = "Feature: Failing\n\n  Scenario: Breaks\n    Given a failing step\n"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), "-c", "user.name=fixture",
         "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
         "-c", "core.hooksPath=/dev/null", *args],
        capture_output=True, text=True, check=True).stdout.strip()


def _environ(home: Path) -> dict[str, str]:
    """What `uv` is handed: a built PATH, a fresh HOME and the toolchain settings the suite pins."""
    uv = shutil.which("uv")
    assert uv is not None, "uv is not on the PATH the suite runs with"
    toolchain = {name: os.environ[name] for name in TOOLCHAIN_SETTINGS if name in os.environ}
    return {"PATH": os.pathsep.join([str(Path(uv).parent), os.defpath]), "HOME": str(home),
            **toolchain}


def _write(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text, encoding="utf-8")


def _scenario_folder(features: dict[str, str], steps: str = STEP) -> dict[str, str]:
    """The files of a small scenario folder on the starter's real `pyproject.toml` and lock."""
    files = {f"{FOLDER}/pyproject.toml": (STARTER / "pyproject.toml").read_text(encoding="utf-8"),
             f"{FOLDER}/uv.lock": (STARTER / "uv.lock").read_text(encoding="utf-8"),
             f"{FOLDER}/.gitignore": ".venv/\n__pycache__/\n",
             f"{FOLDER}/features/steps/steps.py": steps}
    files.update({f"{FOLDER}/features/{name}": text for name, text in features.items()})
    return files


def _make_repo(path: Path, files: dict[str, str]) -> Path:
    path.mkdir(parents=True)
    _git(path, "init", "-q", "-b", "main")
    _write(path, files)
    _git(path, "add", "-A")
    _git(path, "commit", "-q", "-m", "base")
    return path


def _head(repo: Path) -> str:
    return _git(repo, "rev-parse", "HEAD")


def _status(repo: Path) -> str:
    return _git(repo, "status", "--porcelain")


@pytest.fixture
def home(tmp_path: Path) -> Path:
    folder = tmp_path / "home"
    folder.mkdir()
    return folder


@pytest.fixture
def parent(tmp_path: Path) -> Path:
    """The temporary parent a run makes its scratch directory in, so its listing can be read."""
    folder = tmp_path / "scratch-parent"
    folder.mkdir()
    return folder


def _run(repo: Path, base: str, home: Path, parent: Path, red: Overlay | None = None,
         environ: dict[str, str] | None = None) -> tuple[BehaveReport, BehaveReport | None]:
    return ThrowawayBehave(temp_parent=str(parent)).base_and_red(
        repo=str(repo), base=base, folder=FOLDER, red=red,
        environ=environ if environ is not None else _environ(home))


def _starter_scenario_locations() -> set[str]:
    """Where each of the starter's scenarios sits, read off its feature files."""
    found = set()
    for feature in sorted((STARTER / "features").glob("*.feature")):
        for number, line in enumerate(feature.read_text(encoding="utf-8").splitlines(), start=1):
            if re.match(r"\s*Scenario:", line):
                found.add(f"features/{feature.name}:{number}")
    return found


def test_the_base_run_reports_each_starter_scenario_with_its_location_and_status(
        tmp_path: Path, home: Path, parent: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    shutil.copytree(STARTER, repo / FOLDER, ignore=shutil.ignore_patterns(".venv", "__pycache__"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "starter")

    base, red = _run(repo, _head(repo), home, parent)

    assert base.unavailable is None, base.unavailable
    assert base.outcomes is not None
    assert {location for location, _ in base.outcomes} == _starter_scenario_locations()
    assert {status for _, status in base.outcomes} == {"passed"}
    assert red is None


def test_a_base_with_no_scenario_reports_an_empty_tuple_not_unavailable(
        tmp_path: Path, home: Path, parent: Path) -> None:
    repo = _make_repo(tmp_path / "repo", _scenario_folder({}))

    base, _ = _run(repo, _head(repo), home, parent)

    assert (base.outcomes, base.unavailable) == ((), None)


def _branch_with_failing_scenario(repo: Path) -> str:
    _git(repo, "checkout", "-q", "-b", "change")
    _write(repo, {f"{FOLDER}/features/failing.feature": FAILING_FEATURE,
                  f"{FOLDER}/features/steps/failing_steps.py": FAILING_STEP})
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "qa: scenarios")
    red = _head(repo)
    _git(repo, "checkout", "-q", "main")
    return red


def test_the_red_overlay_by_commit_reports_an_added_failing_scenario_as_failed(
        tmp_path: Path, home: Path, parent: Path) -> None:
    repo = _make_repo(tmp_path / "repo", _scenario_folder({"passing.feature": PASSING_FEATURE}))
    base_sha = _head(repo)
    red_sha = _branch_with_failing_scenario(repo)

    base, red = _run(repo, base_sha, home, parent, Overlay.commit(red_sha))

    assert base.outcomes == (("features/passing.feature:3", "passed"),)
    assert red is not None and red.unavailable is None
    assert dict(red.outcomes) == {"features/passing.feature:3": "passed",
                                  "features/failing.feature:3": "failed"}


def test_the_red_overlay_by_working_tree_gives_the_same_report_as_by_commit_over_the_same_content(
        tmp_path: Path, home: Path, parent: Path) -> None:
    repo = _make_repo(tmp_path / "repo", _scenario_folder({"passing.feature": PASSING_FEATURE}))
    base_sha = _head(repo)
    red_sha = _branch_with_failing_scenario(repo)
    worktree = tmp_path / "worktree"
    _git(repo, "worktree", "add", "-q", "-b", "draft", str(worktree), base_sha)
    _write(worktree, {f"{FOLDER}/features/failing.feature": FAILING_FEATURE,
                      f"{FOLDER}/features/steps/failing_steps.py": FAILING_STEP})

    _, by_commit = _run(repo, base_sha, home, parent, Overlay.commit(red_sha))
    _, by_tree = _run(repo, base_sha, home, parent, Overlay.tree(str(worktree)))

    assert by_tree is not None and by_commit is not None
    assert by_tree.outcomes == by_commit.outcomes
    assert by_tree.unavailable is None


def test_a_run_leaves_the_source_repo_and_its_worktrees_status_unchanged(
        tmp_path: Path, home: Path, parent: Path) -> None:
    repo = _make_repo(tmp_path / "repo", _scenario_folder({"passing.feature": PASSING_FEATURE}))
    base_sha = _head(repo)
    red_sha = _branch_with_failing_scenario(repo)
    worktree = tmp_path / "worktree"
    _git(repo, "worktree", "add", "-q", "-b", "draft", str(worktree), base_sha)
    _write(worktree, {f"{FOLDER}/features/failing.feature": FAILING_FEATURE,
                      f"{FOLDER}/features/steps/failing_steps.py": FAILING_STEP})
    before = (_status(repo), _status(worktree))

    _run(repo, base_sha, home, parent, Overlay.commit(red_sha))
    _run(repo, base_sha, home, parent, Overlay.tree(str(worktree)))

    assert (_status(repo), _status(worktree)) == before
    assert "failing.feature" in before[1]


def test_a_run_leaves_no_directory_under_the_temporary_parent(
        tmp_path: Path, home: Path, parent: Path) -> None:
    repo = _make_repo(tmp_path / "repo", _scenario_folder({"passing.feature": PASSING_FEATURE}))
    base_sha = _head(repo)
    red_sha = _branch_with_failing_scenario(repo)
    empty_path = tmp_path / "no-uv"
    empty_path.mkdir()

    available = _run(repo, base_sha, home, parent, Overlay.commit(red_sha))
    unavailable = _run(repo, base_sha, home, parent, environ={"PATH": str(empty_path),
                                                              "HOME": str(home)})

    assert available[0].unavailable is None
    assert unavailable[0].unavailable is not None
    assert list(parent.iterdir()) == []


def test_a_path_without_uv_is_unavailable_naming_the_command_and_exit_127(
        tmp_path: Path, home: Path, parent: Path) -> None:
    repo = _make_repo(tmp_path / "repo", _scenario_folder({"passing.feature": PASSING_FEATURE}))
    empty_path = tmp_path / "no-uv"
    empty_path.mkdir()

    base, red = _run(repo, _head(repo), home, parent,
                     environ={"PATH": str(empty_path), "HOME": str(home)})

    assert base.outcomes is None
    assert base.unavailable is not None
    assert base.unavailable.startswith("uv run --locked behave, exit 127, ")
    assert red is None


def test_an_out_of_date_lock_is_unavailable(tmp_path: Path, home: Path, parent: Path) -> None:
    files = _scenario_folder({"passing.feature": PASSING_FEATURE})
    files[f"{FOLDER}/pyproject.toml"] = files[f"{FOLDER}/pyproject.toml"].replace(
        'name = "behave-starter"', 'name = "renamed-after-the-lock"')
    repo = _make_repo(tmp_path / "repo", files)

    base, _ = _run(repo, _head(repo), home, parent)

    assert base.outcomes is None
    assert base.unavailable is not None
    assert base.unavailable.startswith("uv run --locked behave, exit ")


def test_a_missing_scenario_folder_is_unavailable(
        tmp_path: Path, home: Path, parent: Path) -> None:
    repo = _make_repo(tmp_path / "repo", {"README.md": "no scenarios here\n"})

    base, red = _run(repo, _head(repo), home, parent)

    assert base.outcomes is None
    assert base.unavailable == f"uv run --locked behave, no scenario folder at {FOLDER}"
    assert red is None


def test_the_second_report_is_none_when_red_is_none_or_the_base_is_unavailable(
        tmp_path: Path, home: Path, parent: Path) -> None:
    repo = _make_repo(tmp_path / "repo", _scenario_folder({"passing.feature": PASSING_FEATURE}))
    base_sha = _head(repo)
    red_sha = _branch_with_failing_scenario(repo)
    empty_path = tmp_path / "no-uv"
    empty_path.mkdir()

    _, without_red = _run(repo, base_sha, home, parent, red=None)
    _, behind_unavailable_base = _run(repo, base_sha, home, parent, Overlay.commit(red_sha),
                                      environ={"PATH": str(empty_path), "HOME": str(home)})

    assert without_red is None
    assert behind_unavailable_base is None

