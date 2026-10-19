#!/usr/bin/env python3
"""SessionStart / SubagentStart hook — make the instance manifest's *sections* reachable.

`kensaiapp_structure.md` owns where every file in an instance lives, and it is 900 lines. Measured
over 584 real briefs: 111 name it and only 17 cite a line range, so 94 point an agent at the whole
file; and of the 40 briefs that commission a file, 33 never name it at all. Pointing at a haystack
and pointing at nothing fail the same way — the run invents a location.

This injects the manifest's own section index, with line numbers, so a run can reach the part that
governs its output without reading the rest. It does not say *which* section applies: that is the
brief's job (`agent-invoke` § Step 4), and no hook can see what a run is about to write.

**Derived, never hardcoded.** The index is read from the manifest at run time, so it cannot drift
from it. This was the first block computed rather than copied; `task_map_salience.py` carried a
hand-picked list until 2026-09-02 and now derives too, for the reason this file already gave — a
thing that *can* be computed is.

Serves both events for the same reason `resolve_core.py` does: a subagent does not inherit the
parent's context.

Fail-open: any error prints nothing and exits 0, so the session is never broken. Stdlib only.
"""

from __future__ import annotations

import json
import os
import sys

__version__ = "1.0.1"

SENTINEL = "KENSAIAPP_STRUCTURE_MAP"  # probe marker — the test asserts propagation on it

_MANIFEST = os.path.join("doctrine", "setup", "kensaiapp_structure.md")


def _project_dir() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _core(project_dir: str) -> str:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import resolve_core

    return resolve_core._resolve(project_dir)


def _sections(path: str) -> list[str]:
    """Every `##`/`###` heading with the line it starts at — the manifest's own table of contents,
    computed rather than copied."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        lines = handle.read().splitlines()
    out = []
    for number, line in enumerate(lines, start=1):
        if line.startswith("## "):
            out.append(f"  {line[3:].strip()} — :{number}")
        elif line.startswith("### "):
            out.append(f"    {line[4:].strip()} — :{number}")
    return out


def main() -> int:
    event = "SessionStart"
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if isinstance(payload, dict):
            event = payload.get("hook_event_name") or event
    except (ValueError, TypeError):
        pass

    try:
        manifest = os.path.join(_core(_project_dir()), _MANIFEST)
        sections = _sections(manifest)
        if not sections:
            return 0
        context = (
            f"Instance structure map ({SENTINEL}): `<CORE>/{_MANIFEST.replace(os.sep, '/')}` owns "
            "where every file in an instance lives. Before you create a file, decide its home from "
            "the section that governs it — cite that section, not the whole file:\n"
            + "\n".join(sections)
        )
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
