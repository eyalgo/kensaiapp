#!/usr/bin/env python3
"""PreToolUse Edit|Write hook — refuse a write that carries written-forward debt into a scoped
markdown file, before it reaches disk.

A `Write` or `Edit` narrating a file's own state — "Status: stub", "not yet wired" — never lands
if this fires first; `core/githooks/pre-commit` is the backstop for whatever it does not catch
(older debt a clean edit passes over, a plain `git commit` with no Claude Code session in front of
it, Codex).

`content` for `Write`, `new_string` for `Edit` — measured, not assumed, against this fleet's own
transcripts (`docs/proposals/written-forward-fires/rationale.md` § 3d): those are the exact and
only input keys either tool carries. A missing key is read as absent, never raised on.

The repo a file belongs to is resolved from the file's own path, never the session's `cwd`:
a pipeline step writes from inside `<repo>/.worktrees/<key>/`, where a
cwd-relative path starts `.worktrees/` and matches no scoped root. `--show-toplevel` returns the
worktree's own root, and the relative path from there is the ordinary one.

`resolve_core._resolve()` is the same `.env`-then-`core/` resolution the session start uses, so
this guard and the session agree on one core — the same checker the `pre-commit` hook execs and
its own pytest tests, never a second copy of the phrase set.

Fails open on every error, matching `resolve_core.py` and `development-bash-approve.py`: a guard
that raises must not break a session.
"""

import json
import os
import subprocess
import sys

__version__ = "1.0.2"

_TEXT_FIELD = {"Write": "content", "Edit": "new_string"}


def _repo_root(file_path: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", os.path.dirname(file_path), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _load_written_forward(project_dir: str):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import resolve_core

    core = resolve_core._resolve(project_dir)
    sys.path.insert(0, os.path.join(core, "tools"))
    import written_forward

    return written_forward


def _emit_deny(hits: list[tuple[int, str]], write_it_forward: str) -> None:
    lines = "\n".join(f"{number}: {text}" for number, text in hits)
    reason = f"{lines}\n\n{write_it_forward}"
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def _handle(payload: dict) -> None:
    field = _TEXT_FIELD.get(payload.get("tool_name"))
    if field is None:
        return  # not Write/Edit

    tool_input = payload.get("tool_input") or {}
    text = tool_input.get(field)
    if text is None:
        return  # missing key → absent

    file_path = tool_input.get("file_path")
    if not file_path or not file_path.endswith(".md"):
        return

    repo = _repo_root(file_path)
    if repo is None:
        return  # git failed — not a repo, or no such directory

    relative = os.path.relpath(file_path, repo)
    written_forward = _load_written_forward(repo)
    if not written_forward.in_scope(relative):
        return

    hits = written_forward.violations_in(text)
    if not hits:
        return

    _emit_deny(hits, written_forward.WRITE_IT_FORWARD)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return  # unparseable → defer

    try:
        _handle(payload)
    except Exception:
        return  # fail-open — a guard that raises must not break a session


if __name__ == "__main__":
    main()
