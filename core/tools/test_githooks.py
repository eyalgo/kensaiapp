"""Tests for the two git hook shims, `core/githooks/commit-msg` and `core/githooks/pre-commit`.

They are run as git runs them: a scratch repository with no `pyproject.toml` whose
`core.hooksPath` is this host's `core/githooks`, and a `python3` that only exits 1 first on
`PATH`. A shim that reached the machine's `python3` — by name or through a checker's shebang —
would run the stub and be refused with the stub's silence instead of the checker's own message.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

GITHOOKS = Path(__file__).resolve().parent.parent / "githooks"
SHIMS = ("commit-msg", "pre-commit")

TRAILERS = "Role: Developer\nSurface: Claude Code"


def _stub_python3_dir(tmp_path: Path) -> Path:
    stub_dir = tmp_path / "stub-bin"
    stub_dir.mkdir()
    stub = stub_dir / "python3"
    stub.write_text("#!/bin/sh\nexit 1\n")
    stub.chmod(0o755)
    return stub_dir


def _git(
    repo: Path, stub_dir: Path, *args: str, env_overrides: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "PATH": f"{stub_dir}{os.pathsep}{os.environ['PATH']}",
        **(env_overrides or {}),
    }
    return subprocess.run(
        ["git", *args], cwd=repo, env=env, capture_output=True, text=True
    )


def _scratch_repo(tmp_path: Path) -> tuple[Path, Path]:
    """A repo with no pyproject.toml, hooked to this host's shims, and the stub dir."""
    stub_dir = _stub_python3_dir(tmp_path)
    repo = tmp_path / "scratch"
    repo.mkdir()
    for args in (
        ("init", "-q"),
        ("config", "user.email", "t@example.com"),
        ("config", "user.name", "t"),
        ("config", "core.hooksPath", str(GITHOOKS)),
    ):
        assert _git(repo, stub_dir, *args).returncode == 0
    return repo, stub_dir


def _commit_count(repo: Path, stub_dir: Path) -> int:
    result = _git(repo, stub_dir, "rev-list", "--all", "--count")
    return int(result.stdout.strip()) if result.returncode == 0 else 0


def test_neither_shim_names_python3_or_runs_a_checker_by_its_path() -> None:
    for name in SHIMS:
        body = (GITHOOKS / name).read_text(encoding="utf-8")
        checker_lines = [
            line
            for line in body.splitlines()
            if not line.startswith("#") and re.search(r"\.py\b", line)
        ]

        assert "python3" not in body, name
        assert checker_lines, name
        for line in checker_lines:
            assert line.removeprefix("exec ").startswith('"$core/tools/locked_python.sh"'), line


def test_a_well_formed_commit_lands_in_a_repo_with_no_pyproject(tmp_path: Path) -> None:
    repo, stub_dir = _scratch_repo(tmp_path)
    (repo / "note.txt").write_text("hello\n")
    assert _git(repo, stub_dir, "add", "note.txt").returncode == 0

    result = _git(repo, stub_dir, "commit", "-m", f"subject\n\n{TRAILERS}")

    assert result.returncode == 0, result.stderr
    assert _commit_count(repo, stub_dir) == 1


def test_a_commit_without_trailers_is_refused_by_the_checkers_own_message(
    tmp_path: Path,
) -> None:
    repo, stub_dir = _scratch_repo(tmp_path)
    (repo / "note.txt").write_text("hello\n")
    assert _git(repo, stub_dir, "add", "note.txt").returncode == 0

    result = _git(repo, stub_dir, "commit", "-m", "subject only")

    assert result.returncode != 0
    assert _commit_count(repo, stub_dir) == 0
    assert "commit-msg: missing required trailer(s): Role:, Surface:" in result.stderr


def test_a_written_forward_violation_is_refused_by_its_checkers_own_message(
    tmp_path: Path,
) -> None:
    repo, stub_dir = _scratch_repo(tmp_path)
    violation = repo / "core" / "doctrine" / "x.md"
    violation.parent.mkdir(parents=True)
    violation.write_text("Status: stub\n")
    assert _git(repo, stub_dir, "add", "core/doctrine/x.md").returncode == 0

    result = _git(repo, stub_dir, "commit", "-m", f"subject\n\n{TRAILERS}")

    assert result.returncode != 0
    assert _commit_count(repo, stub_dir) == 0
    assert "core/doctrine/x.md:1: Status: stub" in result.stderr
    assert re.search(r"Write it forward", result.stderr)


def test_a_test_reading_the_machine_is_refused_by_its_checkers_own_message(
    tmp_path: Path,
) -> None:
    repo, stub_dir = _scratch_repo(tmp_path)
    test_file = repo / "tests" / "test_a.py"
    test_file.parent.mkdir()
    test_file.write_text("root = Path.home()\n")  # test-isolation: allowed — fixture text for the hook
    assert _git(repo, stub_dir, "add", "tests/test_a.py").returncode == 0

    result = _git(repo, stub_dir, "commit", "-m", f"subject\n\n{TRAILERS}")

    assert result.returncode != 0
    assert _commit_count(repo, stub_dir) == 0
    assert "tests/test_a.py:1: [home-lookup] root = Path.home()" in result.stderr  # test-isolation: allowed — fixture text for the hook
    assert "Fix these lines on this branch" in result.stderr


def _machine_of_its_own(tmp_path: Path) -> tuple[dict[str, str], str]:
    """The hook's environment naming a home folder and a login this test made up, and the home."""
    made_up_home = tmp_path / "made-up-home"
    made_up_home.mkdir()
    overrides = {"HOME": str(made_up_home), "LOGNAME": "pat-the-tester", "USER": "pat-the-tester"}
    return overrides, str(made_up_home)


def test_a_record_naming_the_home_is_refused_by_its_checkers_own_message(
    tmp_path: Path,
) -> None:
    repo, stub_dir = _scratch_repo(tmp_path)
    machine, made_up_home = _machine_of_its_own(tmp_path)
    record = repo / "system" / "projects" / "tracker17" / "journey" / "x.md"
    record.parent.mkdir(parents=True)
    record.write_text(f"cache at {made_up_home}/.cache\n")
    assert _git(repo, stub_dir, "add", "-A").returncode == 0

    result = _git(
        repo, stub_dir, "commit", "-m", f"subject\n\n{TRAILERS}", env_overrides=machine
    )

    assert result.returncode != 0
    assert _commit_count(repo, stub_dir) == 0
    assert "system/projects/tracker17/journey/x.md:1: [home-path] cache at" in result.stderr
    assert "`<home>/…`" in result.stderr


def test_a_record_naming_the_login_the_hook_runs_as_is_refused(tmp_path: Path) -> None:
    repo, stub_dir = _scratch_repo(tmp_path)
    machine, _ = _machine_of_its_own(tmp_path)
    record = repo / "system" / "projects" / "tracker17" / "journey" / "y.md"
    record.parent.mkdir(parents=True)
    record.write_text(f"ran as {machine['LOGNAME']} on port 8017\n")
    assert _git(repo, stub_dir, "add", "-A").returncode == 0

    result = _git(
        repo, stub_dir, "commit", "-m", f"subject\n\n{TRAILERS}", env_overrides=machine
    )

    assert result.returncode != 0
    assert _commit_count(repo, stub_dir) == 0
    assert (
        "system/projects/tracker17/journey/y.md:1: [login] ran as pat-the-tester"
        in result.stderr
    )


def test_one_commit_hears_all_three_pre_commit_refusals(tmp_path: Path) -> None:
    repo, stub_dir = _scratch_repo(tmp_path)
    machine, made_up_home = _machine_of_its_own(tmp_path)
    doctrine = repo / "core" / "doctrine" / "x.md"
    doctrine.parent.mkdir(parents=True)
    doctrine.write_text("Status: stub\n")
    test_file = repo / "tests" / "test_a.py"
    test_file.parent.mkdir()
    test_file.write_text("root = Path.home()\n")  # test-isolation: allowed — fixture text
    record = repo / "docs" / "note.md"
    record.parent.mkdir()
    record.write_text(f"see {made_up_home}/x\n")
    assert _git(repo, stub_dir, "add", "-A").returncode == 0

    result = _git(
        repo, stub_dir, "commit", "-m", f"subject\n\n{TRAILERS}", env_overrides=machine
    )

    assert result.returncode != 0
    assert "core/doctrine/x.md:1: Status: stub" in result.stderr
    assert "tests/test_a.py:1: [home-lookup]" in result.stderr
    assert "docs/note.md:1: [home-path]" in result.stderr


def test_without_uv_a_commit_is_refused_with_the_install_message(tmp_path: Path) -> None:
    """CP-878 — where uv is not on `PATH`, a git hook runs no Python at all: the commit is
    refused, with the runner's message naming the checker that did not run, and the stub
    `python3` first on `PATH` is never reached."""
    git = shutil.which("git")
    assert git is not None
    if shutil.which("uv", path="/usr/bin:/bin"):
        pytest.skip("uv is installed in /usr/bin or /bin, so it cannot be hidden from PATH")
    repo, stub_dir = _scratch_repo(tmp_path)
    marker = tmp_path / "stub-ran"
    (stub_dir / "python3").write_text(f'#!/bin/sh\necho ran > "{marker}"\nexit 1\n')
    (repo / "note.txt").write_text("hello\n")
    assert _git(repo, stub_dir, "add", "note.txt").returncode == 0
    env = {**os.environ, "PATH": f"{stub_dir}{os.pathsep}/usr/bin{os.pathsep}/bin"}

    result = subprocess.run(
        [git, "commit", "-m", f"subject\n\n{TRAILERS}"],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert _commit_count(repo, stub_dir) == 0
    assert (
        "kensaiapp: uv was not found on PATH, so written_forward.py did not run." in result.stderr
    )
    assert "Guide: https://docs.astral.sh/uv/getting-started/installation/" in result.stderr
    assert not marker.exists()
