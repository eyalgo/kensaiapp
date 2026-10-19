#!/usr/bin/env python3
"""SubagentStop hook — tell the owner a delegated run finished, without a session remembering to.

A `claude --bg` launcher already notifies: `watch_agent.py` is detached to outlive it and pings
`$KENSAIAPP_NOTIFIER` when the run stops. An Agent-tool subagent had nothing equivalent — the
spawning session got a task-notification in its own context and was expected to relay it by hand.

**The obligation was already written down and it did not hold.** `agent-invoke` § Step 6 states it,
and across nine subagent runs in one session (2026-08-22/23) the message was sent six times and
missed three — all three in the busiest stretch, which is where a human is least able to compensate.
That is not an author who needs telling; it is a rule with no surface. This is the surface.

WHY THE MATCHER IS NARROW, AND WHY THAT IS THE REVERSIBLE CHOICE
    Counted over every transcript under `~/.claude/projects/` for this instance on 2026-08-23: 555
    `Agent` spawns across 28 active days — 19.8 a day, and 100 on the day a kaizen fan-out ran. A
    message per subagent is a channel nobody reads, which is the same failure this hook exists to
    fix, reached from the other side. `delegate` alone is 175 spawns, 6.3 a day, the same order as
    the launcher traffic the channel already carries — and it is the type the owner personally
    delegates to and waits on (`agent-invoke` § What this skill covers: "One agent: `delegate`").

    So `settings.json` matches `delegate` and this file checks the type again. The matcher being
    correct and this file depending on it being correct are two different things: the second is how
    a firehose arrives through a filter nobody re-read.

    Widening is a one-line regex edit in `settings.json`. Narrowing after a week of noise does not
    give the owner back the messages he read past. That asymmetry is the whole argument for starting
    here rather than at every agent type.

    **The owner ruled on the width on 2026-08-23: `delegate`, for now.** Recorded here because this
    is where someone lands when they wonder why an agent went unannounced — the question is answered,
    not open, and "for now" is part of the answer. A later widening is the decision moving as
    expected, not a reversal of one.

    **A widening is TWO edits, and half of one ships silently.** The `matcher` in `settings.json`
    and `_ANNOUNCED` below. Change one and the hook looks widened and is not; nothing at runtime
    complains, because each filter is doing exactly its own job. `test_subagent_stop_notify.py`
    § The two filters agree compares them across every agent type in `skills/*/.claude/agents/` and
    fails in both directions, so the half-widening is caught at test time rather than by an agent
    finishing to silence. That test is worth having *because* the ruling is provisional.

WHY IT CANNOT COST THE RUN IT REPORTS ON
    `SubagentStop`'s documented exit-code-2 behaviour is "Prevents the subagent from stopping"
    (`https://code.claude.com/docs/en/hooks.md`, verified 2026-08-23), and a `decision: "block"` on
    stdout does the same thing more quietly. So this file writes nothing to stdout on any path and
    always exits 0 — a stricter reading of the same rule `brief_anchor_guard.py:28` states for
    itself ("Fails open on every error, matching `resolve_core.py`"), because here a raise would not
    merely fail to report a run, it would keep the run from ending.

    The send is also bounded. This event fires before the parent session regains control, so a
    notifier that hangs hangs the session; the subprocess carries a timeout and a timeout is not an
    error.

THE NOTIFIER COMES FROM THE ENVIRONMENT, WITH NO DEFAULT
    `$KENSAIAPP_NOTIFIER`, the same variable every launcher reads. Unset means nothing is sent and
    nothing is said — ordinary configuration, not a failure. There is deliberately no host-global
    fallback path: every satellite runs this file from the host, so a machine path baked in here is a
    machine path in a shared file
    (`kensaiapp_structure.md` § core/tools states the rule for the shared-tools layer).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

__version__ = "1.1.3"

# The one agent type announced today — the owner's ruling of 2026-08-23, for now. See § WHY THE
# MATCHER IS NARROW: this is the second of two filters, the one that does not depend on
# `settings.json` being re-read, and **both move together or neither does**.
_ANNOUNCED = {"delegate"}

# Telegram's sendMessage rejects past 4096 characters and a rejected send is a run nobody hears
# about with an error nobody sees. Measured over this fleet's transcripts on 2026-08-23, a
# delegate's closing message is p90 826 characters and 1589 at the longest, so this keeps
# effectively every real one whole while leaving room for the header.
_BODY_LIMIT = 1500

_DEFAULT_TIMEOUT = 15.0


def _timeout() -> float:
    """How long the send may take. An env knob rather than a flag — a test overrides it to fail
    faster than a real hang, and nothing about a run should ever want to tune it."""
    try:
        return float(os.environ.get("SUBAGENT_STOP_NOTIFY_TIMEOUT") or _DEFAULT_TIMEOUT)
    except (TypeError, ValueError):
        return _DEFAULT_TIMEOUT


def _instance(cwd: str) -> str:
    """Which repo the run was in. Four instances share these hooks, so a message that does not say
    where is ambiguous the first time two of them are running at once."""
    return os.path.basename(str(cwd or "").rstrip("/")) or "unknown"


def _body(message: str) -> str:
    text = (message or "").strip()
    if not text:
        return "(the run left no closing message)"
    if len(text) <= _BODY_LIMIT:
        return text
    return text[:_BODY_LIMIT] + "\n… (truncated)"


def _compose(payload: dict) -> str:
    return (
        f"{payload.get('agent_type') or 'subagent'} finished — {_instance(payload.get('cwd'))}"
        f"  [{payload.get('agent_id') or 'no id'}]\n\n"
        f"{_body(payload.get('last_assistant_message'))}"
    )


def _handle(payload: dict) -> None:
    if payload.get("agent_type") not in _ANNOUNCED:
        return

    notifier = os.environ.get("KENSAIAPP_NOTIFIER")
    if not notifier or not os.path.isfile(notifier):
        return  # absence is configuration — stay silent

    subprocess.run(
        [notifier, _compose(payload)],
        capture_output=True,
        timeout=_timeout(),
        check=False,
    )


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:  # noqa: BLE001 — unparseable → defer
        return
    if not isinstance(payload, dict):
        return
    try:
        _handle(payload)
    except Exception:  # noqa: BLE001 — fail open by contract; see the module docstring
        return


if __name__ == "__main__":
    main()
