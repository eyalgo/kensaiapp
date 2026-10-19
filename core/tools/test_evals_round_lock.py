"""Contract tests for `evals_round_lock.py` — the skill-evals round lock.

What is pinned here, and why each earns a test:

- **Staleness is decided by the agent, not by the file.** The lock is only held while the id it
  names is still `working`. Everything else — finished, killed, aged out of the list, machine
  rebooted — is stale and cleared on the way past. A lock that has to be cleared by hand is a lock
  that gets cleared by hand at the wrong moment, so "self-healing" is the property, not a nicety.
- **An unreadable agent list frees the lock rather than holding it.** The guard exists to stop two
  expensive rounds overlapping; a broken `claude agents` says nothing about whether the account is
  busy, and refusing on it would make the launcher unusable for an unrelated reason.
- **The default path is the repo's COMMON git dir.** That is the whole point: every linked worktree
  of a repo shares it, so two worktrees cannot both start a round. `fixture_guard.py` deliberately
  uses the per-worktree dir for the opposite reason, and confusing the two is exactly the bug this
  lock was written to fix. The worktree case is tested against a real `git worktree add`.

Isolation: `claude` is stubbed on PATH and answers from a test-controlled JSON file, so no real
agent is involved. The lock path is driven both ways — through `KENSAIAPP_EVALS_LOCK` for the
behaviour tests, and unset for the path-derivation tests, which use real git repos in `tmp_path`.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_TOOL = Path(__file__).resolve().parent / "evals_round_lock.py"

CLAUDE_STUB = """#!/usr/bin/env bash
if [ -n "${AGENTS_JSON:-}" ] && [ -f "$AGENTS_JSON" ]; then cat "$AGENTS_JSON"; else echo '[]'; fi
"""


@pytest.fixture
def lock(tmp_path):
    """`lock(*argv) -> CompletedProcess` against the tool, with a stubbed `claude` on PATH."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    stub = bin_dir / "claude"
    stub.write_text(CLAUDE_STUB)
    stub.chmod(0o755)

    agents_json = tmp_path / "agents.json"
    lock_path = tmp_path / "round.json"

    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["AGENTS_JSON"] = str(agents_json)
    env["KENSAIAPP_EVALS_LOCK"] = str(lock_path)

    def _run(*argv, cwd=None):
        return subprocess.run(
            [sys.executable, str(_TOOL), *argv],
            cwd=str(cwd or tmp_path), capture_output=True, text=True, env=env,
        )

    def _agents(entries):
        agents_json.write_text(json.dumps(entries))

    def _held(agent_id="a1", state="working"):
        _run("write", "--agent-id", agent_id, "--skill", "demo", "--cwd", "/x", "--iteration", "3")
        if state is not None:
            _agents([{"id": agent_id, "kind": "background", "cwd": "/x", "state": state}])

    _run.path = lock_path
    _run.agents = _agents
    _run.held = _held
    _run.env = env
    return _run


# --- holder: the staleness rule ----------------------------------------------


def test_a_working_round_is_reported_as_the_holder(lock):
    lock.held("a1", "working")
    result = lock("holder")
    assert result.returncode == 0
    assert "a1" in result.stdout and "demo" in result.stdout


def test_a_stopped_round_is_stale_and_the_lock_is_cleared(lock):
    lock.held("a1", "stopped")
    result = lock("holder")
    assert result.stdout.strip() == ""
    assert not lock.path.exists(), "a stale lock must be cleared as the holder check passes"


def test_a_blocked_round_is_stale(lock):
    # `blocked` is a finished-and-idle round, not a running one. Treating it as held would latch the
    # lock shut after the very first round.
    lock.held("a1", "blocked")
    assert lock("holder").stdout.strip() == ""


def test_an_agent_missing_from_the_list_is_stale(lock):
    # The machine rebooted, or the agent aged out. Nothing will ever clear this by itself otherwise.
    lock.held("ghost", state=None)
    lock.agents([])
    assert lock("holder").stdout.strip() == ""
    assert not lock.path.exists()


def test_an_unreadable_agent_list_frees_rather_than_holds(lock):
    lock.held("a1", "working")
    Path(lock.env["AGENTS_JSON"]).write_text("not json")
    assert lock("holder").stdout.strip() == ""


def test_no_lock_file_means_no_holder(lock):
    assert lock("holder").stdout.strip() == ""
    assert lock("holder").returncode == 0


def test_a_corrupt_lock_file_means_no_holder(lock):
    lock.path.write_text("{ not json")
    assert lock("holder").stdout.strip() == ""


def test_a_lock_without_an_agent_id_is_stale(lock):
    # Identity is the agent id; a lock that names none cannot be checked and must not hold forever.
    lock.path.write_text(json.dumps({"skill": "demo"}))
    assert lock("holder").stdout.strip() == ""
    assert not lock.path.exists()


# --- write / clear ------------------------------------------------------------


def test_write_records_the_round(lock):
    lock("write", "--agent-id", "zz9", "--skill", "product-prd", "--cwd", "/w", "--iteration", "6")
    body = json.loads(lock.path.read_text())
    assert body["agent_id"] == "zz9"
    assert body["skill"] == "product-prd"
    assert body["iteration"] == 6
    assert body["schema_version"] == 1


def test_clear_removes_the_lock(lock):
    lock.held("a1", "working")
    assert lock.path.exists()
    lock("clear")
    assert not lock.path.exists()


def test_clear_on_an_absent_lock_is_not_an_error(lock):
    assert lock("clear").returncode == 0


# --- path derivation ----------------------------------------------------------


def test_the_env_override_wins(lock):
    assert lock("path").stdout.strip() == str(lock.path)


def test_the_default_is_the_repos_common_git_dir(lock, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(repo), check=True)
    env = dict(lock.env)
    env.pop("KENSAIAPP_EVALS_LOCK")
    out = subprocess.run(
        [sys.executable, str(_TOOL), "path"],
        cwd=str(repo), capture_output=True, text=True, env=env,
    ).stdout.strip()
    assert out == str(repo / ".git" / "kensaiapp-skill-evals-round.json")


def test_a_linked_worktree_resolves_to_the_SAME_lock_as_its_repo(lock, tmp_path):
    # The property the whole guard rests on, and the one the first two drafts got wrong: two
    # worktrees of one repo must see ONE lock. --absolute-git-dir would answer
    # <repo>/.git/worktrees/<name> here and give each worktree its own, which is right for
    # fixture_guard.py and exactly wrong for this.
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(repo), check=True)
    (repo / "f.txt").write_text("x")
    subprocess.run(["git", "add", "-A"], cwd=str(repo), check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "-c", "commit.gpgsign=false", "commit", "-q", "-m", "init", "--no-verify"],
                   cwd=str(repo), check=True)
    wt = repo / "wt"
    subprocess.run(["git", "worktree", "add", "-q", "-b", "side", str(wt)], cwd=str(repo), check=True)

    env = dict(lock.env)
    env.pop("KENSAIAPP_EVALS_LOCK")

    def path_from(d):
        return subprocess.run([sys.executable, str(_TOOL), "path"],
                              cwd=str(d), capture_output=True, text=True, env=env).stdout.strip()

    assert path_from(repo) == path_from(wt)
    assert "worktrees" not in path_from(wt)


def test_the_path_is_absolute_even_though_git_may_answer_relatively(lock, tmp_path):
    # `git rev-parse --git-common-dir` answers a bare ".git" from a repo root. Left unresolved the
    # lock would land wherever the caller happened to be standing, which is the opposite of shared.
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=str(repo), check=True)
    env = dict(lock.env)
    env.pop("KENSAIAPP_EVALS_LOCK")
    out = subprocess.run([sys.executable, str(_TOOL), "path"],
                         cwd=str(repo), capture_output=True, text=True, env=env).stdout.strip()
    assert Path(out).is_absolute()


def test_outside_a_git_repo_it_still_answers_a_path(lock, tmp_path):
    # A launcher must not crash because someone ran it somewhere odd; the fallback is <cwd>/.git.
    plain = tmp_path / "plain"
    plain.mkdir()
    env = dict(lock.env)
    env.pop("KENSAIAPP_EVALS_LOCK")
    result = subprocess.run([sys.executable, str(_TOOL), "path"],
                            cwd=str(plain), capture_output=True, text=True, env=env)
    assert result.returncode == 0
    assert result.stdout.strip().endswith("kensaiapp-skill-evals-round.json")
