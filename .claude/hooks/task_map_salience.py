#!/usr/bin/env python3
"""SessionStart / SubagentStart hook — make the task→doctrine map salient.

Injects the map at `<CORE>/doctrine/task_map.md` as a compact index — every route, one line each —
so that before acting on a task Claude knows a doctrine governs it and which one. Serves both events
(a subagent does not inherit the parent's context, which is why this is wired to SubagentStart as
well — same reasoning as `resolve_core.py`).

**Derived, never hardcoded.** The routes are read from the map at run time, so the block cannot
drift from it — the shape `manifest_salience.py` already uses for the structure index. Until
2026-09-02 this file instead carried a hand-picked list of eight of the map's forty-nine triggers,
defended as the sanctioned loading exception (`single_source.md` § "The stub is the copy we keep").
The exception was real; the hand-picking was the defect. `task_map.md` polices that every trigger
named here resolves to a row, and nothing policed the other direction, so a row nobody thought to
add to the list was invisible — and looked, from inside a session, exactly like a row that did not
exist. The boy-scout rule sat outside the list for as long as the list was written by hand. A route
set *can* be computed, so it is, and the invariant is now structural.

This is a *loading* concern, not a doctrine: `task_map.md` owns which routes exist and which of them
fire unprompted, and the doctrine bodies own what each rule says. The rows that fire unprompted are
injected separately, as binding rather than as routes, by `standing_rules_salience.py`.

It references the `<CORE>` token rather than resolving it — `resolve_core.py` (wired to the same
events) injects the resolution; the model sees both blocks and substitutes. Keeping resolution
single-owned is deliberate (each layer owns one thing).

Fail-open: any error prints nothing and exits 0 so the session is never broken. Stdlib-only imports.
"""

from __future__ import annotations

import json
import os
import sys

__version__ = "2.0.1"

def _project_dir() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _load():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import _task_map

    return _task_map


def main() -> int:
    # Resolution does not depend on the payload; we only reflect the incoming
    # event name so one script serves both SessionStart and SubagentStart.
    event = "SessionStart"
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if isinstance(payload, dict):
            event = payload.get("hook_event_name") or event
    except (ValueError, TypeError):
        pass

    try:
        task_map = _load()
        context = task_map.routing_context(_project_dir())
        if not context:
            return 0
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": event,
                "additionalContext": context,
            }
        }))
    except Exception:  # noqa: BLE001 — fail-open by contract
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
