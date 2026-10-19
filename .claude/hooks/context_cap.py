#!/usr/bin/env python3
"""PostToolUse Bash hook — tell a developer run to pause once its context is over the cap.

WHY THIS EXISTS
    A developer run that reads a large `tl_instruction.md` and works a dozen tasks carries a
    context that grows until the run degrades or is cut off. The chain sets
    `KENSAIAPP_CONTEXT_CAP` for the implementation step only; this hook reads the run's own
    transcript, and once the current context is over that cap it injects one instruction: finish
    the task in progress through its last commit, make the pause commit, and end. The chain reads
    that commit as "relaunch after task N" and starts a fresh developer.

    It matches `Bash` and nothing else. The developer commits through Bash, and a task boundary
    is a commit, so a Bash call is the one event that lands at a boundary the run can name.

    **Silent unless the cap is set.** Every other session — an interactive one, another step of
    the chain — has no `KENSAIAPP_CONTEXT_CAP`, and a hook that spoke there would be noise on
    every Bash call in the fleet. The gauge is not even loaded until the cap has been read.

    **The gauge is found through `resolve_core._resolve()`, never a path relative to this file.**
    This hook runs in satellites, which hold no `core/` of their own; the same
    `.env`-then-`core/` resolution the session start uses is the only route that reaches
    `<core>/tools/context_gauge.py` from there (`written_forward_guard.py` loads its checker the
    same way).

    **Fails open on every path** — any error is silence and exit 0, as `written_forward_guard.py`
    does: a hook that raises must not break a session.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path

__version__ = "1.0.1"

CAP_VARIABLE = "KENSAIAPP_CONTEXT_CAP"
PAUSE_SUBJECT = "developer: <key> — implementation paused after task <N>"

_MESSAGE = (
    "Context is {size} tokens, over the {cap}-token cap this run was given. Finish the task in "
    "progress through its last commit, then make the pause commit — subject "
    "`" + PAUSE_SUBJECT + "`, N being the last task you committed — on the instance worktree, "
    "and end the run. A fresh developer resumes from the next task."
)


def _cap_from(raw: str) -> int | None:
    """`raw` as a positive integer, or `None` when it is unset or anything else."""
    raw = raw.strip()
    if not re.fullmatch(r"[0-9]+", raw) or int(raw) == 0:
        return None
    return int(raw)


def _build_gauge() -> Callable[[Path], int | None]:
    """The wiring: load the gauge through the resolved core and hand back the one function the
    check needs, the current context of a transcript. The only place this hook builds a concrete
    `Files`, and only reached once a cap is set."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import resolve_core

    core = resolve_core._resolve(resolve_core._project_dir())
    sys.path.insert(0, os.path.join(core, "tools"))
    import context_gauge
    import run_usage

    files = run_usage.Files()
    return lambda transcript: context_gauge.current_context(transcript, files)


def _handle(payload: dict, cap: int, gauge: Callable[[Path], int | None]) -> None:
    """Say so, once, when the payload's transcript is over `cap`. Silent otherwise."""
    size = gauge(Path(payload["transcript_path"]))
    if size is None or size <= cap:
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": _MESSAGE.format(size=size, cap=cap),
        }
    }))


def main() -> None:
    """Best-effort by contract: any failure is silence and exit 0, because a hook that raises
    must not break the session it watches. This is also the composition root — the one place the
    environment is read and the gauge is built."""
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return  # unparseable → silence

    try:
        cap = _cap_from(os.environ.get(CAP_VARIABLE, ""))
        if cap is None:
            return
        _handle(payload, cap, _build_gauge())
    except Exception:
        return  # fail-open — a hook that raises must not break a session


if __name__ == "__main__":
    main()
