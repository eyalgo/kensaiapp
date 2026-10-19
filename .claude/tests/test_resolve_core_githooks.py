"""`resolve_core.py` wires `core.hooksPath`, and knows when not to.

`core.hooksPath` is local, untracked git config, so a clone never carries it and
the git-native commit-msg trailer check starts inert — a commit with no `Role:`
or `Surface:` is accepted in silence. The hook sets it when nothing else has.

Each test below pins one guard. The guards matter more than the wiring: setting
`core.hooksPath` makes git ignore `.git/hooks/` entirely, and linked worktrees
share one `.git/config`, so a careless write breaks other trees silently.

Run the hook as a subprocess over its stdin/stdout contract, exactly as a
session does — never import it (matching `kensaiapp-set-core/tests/test_resolution.py`).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# .../.claude/tests/test_resolve_core_githooks.py -> parents[1] == .../.claude
RESOLVE_CORE = Path(__file__).resolve().parents[1] / "hooks" / "resolve_core.py"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    ).stdout.strip()


def _run_hook(project_dir: Path) -> str:
    """Drive the hook the way a session does; return its additionalContext."""
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    env.pop("CLAUDE_ENV_FILE", None)
    done = subprocess.run(
        [sys.executable, str(RESOLVE_CORE)],
        input='{"hook_event_name": "SessionStart"}',
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"]


def _hooks_path(repo: Path) -> str | None:
    p = subprocess.run(
        ["git", "config", "--get", "core.hooksPath"],
        cwd=repo, capture_output=True, text=True,
    )
    return p.stdout.strip() if p.returncode == 0 else None


def _instance(tmp_path: Path) -> Path:
    """A git repo shaped like a kensaiapp: a vendored core/ with githooks/."""
    repo = tmp_path / "instance"
    (repo / "core" / "githooks").mkdir(parents=True)
    (repo / "core" / "githooks" / "commit-msg").write_text("#!/bin/sh\nexit 0\n")
    _git(repo.parent, "init", "-q", str(repo))
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    return repo


def test_wires_hookspath_when_unset(tmp_path):
    repo = _instance(tmp_path)
    assert _hooks_path(repo) is None, "precondition: a fresh repo carries no hooksPath"

    context = _run_hook(repo)

    assert _hooks_path(repo) == str(repo / "core" / "githooks")
    assert "core.hooksPath" in context, "the session must see that config changed"


def test_does_not_override_a_value_someone_chose(tmp_path):
    repo = _instance(tmp_path)
    _git(repo, "config", "core.hooksPath", "/somewhere/else")

    _run_hook(repo)

    assert _hooks_path(repo) == "/somewhere/else"


def test_does_not_write_from_inside_a_linked_worktree(tmp_path):
    """Worktrees share the main repo's .git/config.

    A worktree resolves <CORE> to its own core/, so writing that path would
    repoint every tree at a directory that dies with the worktree.
    """
    repo = _instance(tmp_path)
    (repo / "f.txt").write_text("x\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "seed")
    wt = tmp_path / "wt"
    _git(repo, "worktree", "add", "-q", str(wt), "-b", "probe")

    _run_hook(wt)

    assert _hooks_path(repo) is None, "the shared config must be untouched"
    assert _hooks_path(wt) is None


def test_does_not_shadow_a_users_active_hooks(tmp_path):
    """Setting core.hooksPath makes git ignore .git/hooks/ entirely."""
    repo = _instance(tmp_path)
    hook = Path(_git(repo, "rev-parse", "--absolute-git-dir")) / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text("#!/bin/sh\nexit 0\n")
    hook.chmod(0o755)

    _run_hook(repo)

    assert _hooks_path(repo) is None, "a user's own hooks must not be silently disabled"


def test_sample_hooks_do_not_count_as_active(tmp_path):
    """A fresh clone ships .git/hooks/*.sample; git never runs them."""
    repo = _instance(tmp_path)
    samples = Path(_git(repo, "rev-parse", "--absolute-git-dir")) / "hooks"
    samples.mkdir(parents=True, exist_ok=True)
    (samples / "pre-commit.sample").write_text("#!/bin/sh\nexit 0\n")

    _run_hook(repo)

    assert _hooks_path(repo) == str(repo / "core" / "githooks")


def test_resolution_still_works_when_wiring_is_impossible(tmp_path):
    """Fail-open: no core/githooks, not even a git repo — <CORE> still resolves."""
    plain = tmp_path / "plain"
    plain.mkdir()

    context = _run_hook(plain)

    assert str(plain / "core") in context
    assert "core.hooksPath" not in context
