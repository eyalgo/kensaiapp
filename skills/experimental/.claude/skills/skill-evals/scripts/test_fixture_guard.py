"""`fixture_guard.py` proves an eval run left its fixtures alone, and puts them back when it didn't.

Each test pins one damage mode. The modes matter more than the plumbing: three of them are visible to
`git status`, and the fourth — a file created inside a fixture directory and deleted again — is
visible to nothing but the directory's mtime. That fourth one is the mode actually observed twice in
this repo, so `test_transient_write_is_caught` is the test this script exists for.

Build a throwaway git repo under `tmp_path` and drive the real CLI as a subprocess over its exit-code
contract, never importing it (matching `.claude/tests/test_resolve_core_githooks.py`).
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parent / "fixture_guard.py"

EXIT_CLEAN = 0
EXIT_PRECONDITION = 2
EXIT_DAMAGE = 3
EXIT_REPAIR_INCOMPLETE = 4


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout


def _guard(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(GUARD), *args],
        cwd=repo,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A committed skill tree with one fixture product, shaped like the real thing."""
    root = tmp_path / "instance"
    docs = root / ".claude" / "skills" / "demo" / "evals" / "inputs" / "prod" / "docs"
    docs.mkdir(parents=True)
    (docs.parent / "project.md").write_text(
        "# prod\n\n**Product path:** .claude/skills/demo/evals/inputs/prod\n"
    )
    (docs / "SRS.md").write_text("# SRS\n\nVersion 1.\n")
    (docs / "SRS_open_issues.md").write_text("# Open issues\n\n- one\n")
    (docs / "trail/prd").mkdir(parents=True)
    (docs / "trail/prd" / "cycle-1.md").write_text("# cycle 1\n")
    (root / ".claude" / "skills" / "demo" / "evals" / "evals.json").write_text(
        json.dumps(
            {
                "skill_name": "demo",
                "evals": [
                    {
                        "id": 1,
                        "name": "case-one",
                        "prompt": "read .claude/skills/demo/evals/inputs/prod/project.md",
                        "assertions": [],
                    }
                ],
            }
        )
    )

    # Mirror the real repo: the snapshot store's default home is gitignored (.gitignore:99), so a
    # guard cycle never itself dirties the tree it is protecting.
    (root / ".gitignore").write_text("system/logs/\n")

    _git(root, "init", "-q")
    _git(root, "config", "user.email", "t@example.com")
    _git(root, "config", "user.name", "T")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "fixtures")
    return root


def _skill_dir(repo: Path) -> str:
    return str(repo / ".claude" / "skills" / "demo")


def _fixtures(repo: Path) -> Path:
    return repo / ".claude" / "skills" / "demo" / "evals" / "inputs"


def _snapshot(repo: Path, *extra: str) -> subprocess.CompletedProcess:
    return _guard(repo, "snapshot", "--skill-dir", _skill_dir(repo), *extra)


def _porcelain(repo: Path) -> str:
    return _git(repo, "status", "--porcelain").strip()


def _findings(repo: Path, workspace: Path) -> list[dict]:
    return json.loads((workspace / "fixture_guard.json").read_text())["findings"]


def _kinds(repo: Path, workspace: Path) -> set[str]:
    return {f["kind"] for f in _findings(repo, workspace)}


# --------------------------------------------------------------------------- baseline


def test_clean_run_verifies_and_clears_the_lock(repo: Path, tmp_path: Path):
    assert _snapshot(repo).returncode == EXIT_CLEAN
    workspace = tmp_path / "ws"

    done = _guard(repo, "verify", "--workspace", str(workspace))

    assert done.returncode == EXIT_CLEAN, done.stderr
    assert json.loads((workspace / "fixture_guard.json").read_text())["clean"] is True
    # A clean close is the only thing that clears the lock.
    assert not (repo / ".git" / "kensaiapp-fixture-guard.json").exists()


def test_verify_without_a_snapshot_is_a_precondition_failure(repo: Path):
    done = _guard(repo, "verify")

    assert done.returncode == EXIT_PRECONDITION
    assert "no open guard" in done.stderr


# --------------------------------------------------------------------------- damage modes


def test_overwrite_is_caught_and_restored(repo: Path, tmp_path: Path):
    _snapshot(repo)
    target = _fixtures(repo) / "prod" / "docs" / "SRS.md"
    original = target.read_bytes()
    target.write_text("DAMAGED\n")
    workspace = tmp_path / "ws"

    assert _guard(repo, "verify", "--workspace", str(workspace)).returncode == EXIT_DAMAGE
    assert "modified" in _kinds(repo, workspace)

    assert _guard(repo, "repair", "--apply").returncode == EXIT_CLEAN
    assert target.read_bytes() == original
    assert _porcelain(repo) == ""


def test_stray_file_is_caught_and_removed(repo: Path, tmp_path: Path):
    _snapshot(repo)
    docs = _fixtures(repo) / "prod" / "docs"
    (docs / "SRS_v2.md").write_text("stray\n")
    (docs / "sub").mkdir()
    (docs / "sub" / "deep.md").write_text("stray\n")
    workspace = tmp_path / "ws"

    assert _guard(repo, "verify", "--workspace", str(workspace)).returncode == EXIT_DAMAGE
    assert "created" in _kinds(repo, workspace)

    assert _guard(repo, "repair", "--apply").returncode == EXIT_CLEAN
    assert not (docs / "SRS_v2.md").exists()
    assert not (docs / "sub").exists(), "a directory the snapshot never had must be pruned"
    assert (docs / "trail/prd").exists(), "a directory the snapshot had must survive"
    assert _porcelain(repo) == ""


def test_staged_deletion_is_caught_and_unstaged_without_a_checkout(
    repo: Path, tmp_path: Path
):
    """The worst mode: the skill's own `--rm` path runs a real `git rm` on a tracked fixture."""
    _snapshot(repo)
    companion = ".claude/skills/demo/evals/inputs/prod/docs/SRS_open_issues.md"
    original = (repo / companion).read_bytes()
    _git(repo, "rm", "-q", companion)
    assert not (repo / companion).exists()
    workspace = tmp_path / "ws"

    assert _guard(repo, "verify", "--workspace", str(workspace)).returncode == EXIT_DAMAGE
    kinds = _kinds(repo, workspace)
    assert "staged-deletion" in kinds
    assert "deleted-worktree" in kinds

    assert _guard(repo, "repair", "--apply").returncode == EXIT_CLEAN
    assert (repo / companion).read_bytes() == original
    assert _porcelain(repo) == "", "index and worktree must both be back"


def test_transient_write_is_caught(repo: Path, tmp_path: Path):
    """Create-then-delete inside a fixture: no tracked content moves, so only the dir mtime shows it.

    This is the mode observed twice in this repo (product-srs/trimly/docs, product-prd/mailmate/docs)
    and the reason the snapshot records per-directory mtimes at all.
    """
    _snapshot(repo)
    docs = _fixtures(repo) / "prod" / "docs"
    time.sleep(0.01)  # filesystem mtime granularity
    ghost = docs / "SRS.md.tmp"
    ghost.write_text("written then removed\n")
    os.unlink(ghost)
    workspace = tmp_path / "ws"

    # The damage is invisible to git, which is exactly the point.
    assert _porcelain(repo) == ""

    done = _guard(repo, "verify", "--workspace", str(workspace))

    assert done.returncode == EXIT_DAMAGE, "a write reached the fixture and must be reported"
    assert "transient-write" in _kinds(repo, workspace)
    report = (workspace / "fixture_guard_report.md").read_text()
    assert "transient-write" in report


# --------------------------------------------------------------------------- user work


def test_snapshot_refuses_a_dirty_fixture_tree(repo: Path):
    (_fixtures(repo) / "prod" / "docs" / "SRS.md").write_text("USER WORK\n")

    done = _snapshot(repo)

    assert done.returncode == EXIT_PRECONDITION
    assert "already dirty" in done.stderr


def test_dirty_override_restores_the_users_bytes_not_head(repo: Path):
    """A run must never 'restore' away the user's own uncommitted work."""
    target = _fixtures(repo) / "prod" / "docs" / "SRS.md"
    target.write_text("USER WORK\n")
    assert _snapshot(repo, "--allow-dirty-inputs").returncode == EXIT_CLEAN

    target.write_text("RUN CLOBBERED IT\n")
    assert _guard(repo, "verify").returncode == EXIT_DAMAGE
    assert _guard(repo, "repair", "--apply").returncode == EXIT_CLEAN

    assert target.read_text() == "USER WORK\n"
    assert _porcelain(repo) != "", "the user's own edit must still be uncommitted"


# --------------------------------------------------------------------------- lock lifecycle


def test_a_second_snapshot_refuses_while_a_lock_is_open(repo: Path):
    assert _snapshot(repo).returncode == EXIT_CLEAN

    blocked = _snapshot(repo)
    assert blocked.returncode == EXIT_PRECONDITION
    assert "still open" in blocked.stderr

    assert _snapshot(repo, "--supersede").returncode == EXIT_CLEAN


def test_damage_retains_the_lock(repo: Path):
    _snapshot(repo)
    (_fixtures(repo) / "prod" / "docs" / "SRS.md").write_text("DAMAGED\n")

    assert _guard(repo, "verify").returncode == EXIT_DAMAGE
    assert (repo / ".git" / "kensaiapp-fixture-guard.json").exists(), (
        "a retained lock is what makes the next run refuse to start"
    )


# --------------------------------------------------------------------------- constraints


def test_no_work_discarding_git_verb_appears_in_the_source():
    """Every restore verb below is force-deferred to a permission prompt by
    `.claude/hooks/development-bash-approve.py`, which would stall an unattended run. Restore is
    built from index-only `git reset -- <path>` plus Python byte writes instead.
    """
    source = GUARD.read_text()
    for forbidden in (
        "git clean",
        "git checkout",
        "git restore",
        "reset --hard",
        "git stash",
        "shutil.rmtree(guarded",
    ):
        assert forbidden not in source, f"{forbidden!r} would stall an unattended run"


def test_audit_reports_a_ghost_write_without_a_snapshot(repo: Path):
    docs = _fixtures(repo) / "prod" / "docs"
    time.sleep(0.01)
    ghost = docs / "leftover.md"
    ghost.write_text("x\n")
    os.unlink(ghost)

    # --min-gap-seconds 0 because the test's create-and-delete is microseconds apart; the 60s default
    # exists so ordinary authoring (directory a hair newer than its last file) is not reported.
    done = _guard(
        repo, "audit", "--skill-dir", _skill_dir(repo), "--min-gap-seconds", "0"
    )

    assert done.returncode == EXIT_CLEAN, "a ghost is a report, not a dirty tree"
    assert "suspected past writes" in done.stdout
    assert "prod/docs" in done.stdout


def test_audit_default_gap_ignores_ordinary_authoring(repo: Path):
    """The committed fixture tree was authored, not damaged — the default must stay quiet on it."""
    done = _guard(repo, "audit", "--skill-dir", _skill_dir(repo))

    assert done.returncode == EXIT_CLEAN
    assert "no directory is meaningfully newer" in done.stdout


def test_a_skill_with_no_fixtures_is_a_clean_no_op(repo: Path, tmp_path: Path):
    bare = repo / ".claude" / "skills" / "bare"
    (bare / "evals").mkdir(parents=True)

    assert _guard(repo, "snapshot", "--skill-dir", str(bare)).returncode == EXIT_CLEAN
    assert _guard(repo, "verify", "--workspace", str(tmp_path / "ws")).returncode == EXIT_CLEAN
