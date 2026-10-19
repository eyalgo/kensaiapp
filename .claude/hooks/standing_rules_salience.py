#!/usr/bin/env python3
"""SessionStart / SubagentStart hook — make the standing rules bind without being consulted.

Most doctrine is reached by aiming at it: you know you are about to commit, so you look up the rule
for committing, and `task_map_salience.py` puts that index in context. A few rules cannot be reached
that way at all. You do not decide to *find a defect while walking*; failing to notice is the very
thing the rule exists to catch, so "consult the map when you are about to" names a moment that never
arrives. Measured 2026-09-02: a satellite session carrying that exact trigger in context still could
not name the rule when asked, which is the whole evidence for this file existing.

So the rows `task_map.md` marks `unprompted` are injected here as **binding** rather than as routes:
they apply whether or not anything is consulted. Serves both events, because a subagent inherits no
context from its parent.

**It names rules; it does not restate them.** The trigger and the doctrine's filename, nothing more.
The one block it carries whole is how to reply to the owner, and that is not a restatement (below).
What each rule *says* belongs to its own body, and a copy here would be a second statement of it —
free to drift, and read instead of the original. `single_source.md` § "The stub is the copy we keep"
is what lets a naming line exist at all: a nudge that must be in-context cannot be a bare pointer.
That exception covers naming, and stops there.

**How to reply to the owner is carried whole.** It binds the first reply, which is written before any
named file would be opened, so `task_context.py` ends the block with § The rules of
`talking_to_the_owner.md`. It is read from that file every time, so it is that file's own text, not a
copy, and nothing here can drift from it.

**Derived, never hardcoded.** Which rows are marked is `task_map.md`'s to say, read at run time. A
list here would be the same hand-picking that kept the boy-scout rule invisible until 2026-09-02.

Fail-open: any error prints nothing and exits 0. A core with no marked rows and no reply rules
injects nothing at all, rather than a heading with nothing under it. Stdlib-only imports.
"""

from __future__ import annotations

import json
import os
import sys

__version__ = "1.1.2"

def _project_dir() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _load():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import _task_map

    return _task_map


def main() -> int:
    event = "SessionStart"
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if isinstance(payload, dict):
            event = payload.get("hook_event_name") or event
    except (ValueError, TypeError):
        pass

    try:
        task_map = _load()
        context = task_map.standing_rules_context(_project_dir())
        if not context:
            return 0  # no standing rules is a real state, and it says nothing
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
