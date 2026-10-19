"""Tests for `written_forward_guard.py` — the `PreToolUse` `Edit|Write` guard.

Runs the real entry point — JSON on stdin, JSON or silence on stdout — exactly as Claude Code
does with it, following `test_development_bash_approve.py`'s shape.

Each test resolves its `file_path` inside a fabricated instance repo (a real git repo carrying a
copy of `core/tools/written_forward.py`), because the guard imports that module through
`resolve_core._resolve()` against the repo the file belongs to — there is no shortcut around a
real repo without re-implementing the checker's phrase set a second time.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

_GUARD = Path(__file__).resolve().parent / "written_forward_guard.py"
_WRITTEN_FORWARD = Path(__file__).resolve().parents[2] / "core" / "tools" / "written_forward.py"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)


def _instance(tmp_path: Path) -> Path:
    """A git repo shaped like a kensaiapp instance: a real core/tools/written_forward.py, no
    .env (so `resolve_core._resolve` defaults to `<repo>/core`)."""
    repo = tmp_path / "instance"
    tools_dir = repo / "core" / "tools"
    tools_dir.mkdir(parents=True)
    shutil.copy(_WRITTEN_FORWARD, tools_dir / "written_forward.py")
    (repo / "core" / "doctrine").mkdir(parents=True)
    (repo / "core" / "doctrine" / "governance").mkdir(parents=True)
    (repo / ".claude" / "skills" / "s" / "evals" / "inputs").mkdir(parents=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "seed")
    return repo


def _run(payload) -> subprocess.CompletedProcess:
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [sys.executable, str(_GUARD)],
        input=stdin,
        capture_output=True,
        text=True,
    )


def _verdict(payload):
    """Run the real hook; return the parsed deny decision, or None for silence."""
    result = _run(payload)
    assert result.returncode == 0, result.stderr
    out = result.stdout.strip()
    if not out:
        return None
    return json.loads(out)["hookSpecificOutput"]


# --- deny: a scoped markdown file's Write/Edit carries a violation ----------------------


def test_write_of_scoped_markdown_with_a_violation_is_denied(tmp_path):
    repo = _instance(tmp_path)
    file_path = str(repo / "core" / "doctrine" / "x.md")

    verdict = _verdict({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "Status: stub\n"},
    })

    assert verdict is not None
    assert verdict["permissionDecision"] == "deny"
    assert "Status: stub" in verdict["permissionDecisionReason"]


def test_edit_of_scoped_markdown_with_a_violation_is_denied(tmp_path):
    repo = _instance(tmp_path)
    file_path = str(repo / "core" / "doctrine" / "x.md")

    verdict = _verdict({
        "tool_name": "Edit",
        "tool_input": {
            "file_path": file_path,
            "new_string": "not yet wired",
            "old_string": "clean",
            "replace_all": False,
        },
    })

    assert verdict is not None
    assert verdict["permissionDecision"] == "deny"
    assert "not yet wired" in verdict["permissionDecisionReason"]


def test_edit_reads_new_string_not_old_string(tmp_path):
    """The guard reads what is being written, not what is being removed — this is the shape
    of a fix, and it must pass."""
    repo = _instance(tmp_path)
    file_path = str(repo / "core" / "doctrine" / "x.md")

    verdict = _verdict({
        "tool_name": "Edit",
        "tool_input": {
            "file_path": file_path,
            "new_string": "clean now",
            "old_string": "Status: stub",
            "replace_all": False,
        },
    })

    assert verdict is None


# --- no output: clean content, wrong extension, out of scope, wrong tool ----------------


def test_write_of_clean_markdown_is_not_denied(tmp_path):
    repo = _instance(tmp_path)
    file_path = str(repo / "core" / "doctrine" / "x.md")

    verdict = _verdict({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "nothing wrong here\n"},
    })

    assert verdict is None


def test_write_of_a_python_file_is_not_denied(tmp_path):
    repo = _instance(tmp_path)
    file_path = str(repo / "core" / "doctrine" / "x.py")

    verdict = _verdict({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "# Status: stub\n"},
    })

    assert verdict is None


def test_write_of_a_record_subtree_is_not_denied(tmp_path):
    repo = _instance(tmp_path)
    file_path = str(repo / ".claude" / "skills" / "s" / "evals" / "inputs" / "x.md")

    verdict = _verdict({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "Status: stub\n"},
    })

    assert verdict is None


def test_write_outside_scoped_roots_is_not_denied(tmp_path):
    repo = _instance(tmp_path)
    (repo / "docs" / "proposals" / "p").mkdir(parents=True)
    file_path = str(repo / "docs" / "proposals" / "p" / "x.md")

    verdict = _verdict({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "Status: stub\n"},
    })

    assert verdict is None


def test_bash_tool_call_is_not_denied():
    verdict = _verdict({"tool_name": "Bash", "tool_input": {"command": "echo hi"}})

    assert verdict is None


# --- fail-open: malformed input never breaks the session ---------------------------------


def test_malformed_json_produces_no_output():
    result = _run("not json at all {{{")

    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_a_file_path_outside_any_git_repo_produces_no_output(tmp_path):
    """`git rev-parse --show-toplevel` fails when the file belongs to no repo — there is no
    relative path to score, so the guard defers rather than raising."""
    loose = tmp_path / "loose"
    loose.mkdir()
    file_path = str(loose / "x.md")

    verdict = _verdict({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "Status: stub\n"},
    })

    assert verdict is None


def test_missing_content_key_produces_no_output(tmp_path):
    repo = _instance(tmp_path)
    file_path = str(repo / "core" / "doctrine" / "x.md")

    verdict = _verdict({"tool_name": "Write", "tool_input": {"file_path": file_path}})

    assert verdict is None


# --- worktree resolution: --show-toplevel, never cwd -------------------------------------


def test_file_under_a_worktree_resolves_through_show_toplevel(tmp_path):
    """A pipeline step writes from inside `<repo>/.worktrees/<key>/`. A
    cwd-relative path there starts `.worktrees/` and matches no scoped root; `--show-toplevel`
    must return the worktree's own root so the relative path is the ordinary one."""
    repo = _instance(tmp_path)
    worktree = repo / ".worktrees" / "k"
    _git(repo, "worktree", "add", "-q", str(worktree), "-b", "k")
    (worktree / "core" / "doctrine").mkdir(parents=True, exist_ok=True)
    file_path = str(worktree / "core" / "doctrine" / "x.md")

    verdict = _verdict({
        "tool_name": "Write",
        "tool_input": {"file_path": file_path, "content": "Status: stub\n"},
    })

    assert verdict is not None
    assert verdict["permissionDecision"] == "deny"
