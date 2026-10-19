#!/usr/bin/env python3
"""Observe a detached provider process through its structured event log.

WHAT IT WATCHES
    One process `agent_run.py --background` started and returned the pid of — a Claude
    `--print --output-format stream-json` run or a Codex `exec --json` run — through the log that
    process writes, read by the provider's own inspector (`agent_turn.inspect`). The log ends with
    the `kensai.exit` record `agent_run.Subprocesses.start_detached` appends, so a process that
    dies before its first event still leaves something to read.

WHAT ENDS THE WATCH, AND WHAT THE HOOK IS HANDED
    It reports through the same reporter, notifier and on-complete hook `watch_agent.py` uses for
    a `claude --bg` run, and hands the hook the same words:

    - The provider ended the turn, or the caller's completion marker appeared → the reporter's
      `completed` / `produced_nothing`. For Claude a `result` event of any subtype ends the turn:
      a `--bg` session whose turn ended on an error went idle and reached the chain as completed,
      and the chain read the disk — so an error result does the same, and the message names the
      error. A Codex `turn.failed` stays `failed`, as does a
      process that died with no terminal event (`_AN_ERROR_RESULT_ENDS_THE_TURN`).
    - `--multi-turn`: a run that says it is finished with its marker and ended without it was cut
      off mid-walk → `stopped`, `watch_agent.py`'s own reading of the same ending.
    - The process died with no terminal provider event → `failed`.
    - The deadline passed → `timeout`, stopping nothing, as `watch_agent.py` does.

    After an ending it stops the process if it lingers (`stop_lingering`) — `watch_agent.py`'s
    `claude stop` for a run it watched — with SIGINT first, which ends a `claude -p` turn rather
    than abandoning it (https://code.claude.com/docs/en/headless.md § Stop a run with SIGTERM).
"""

from __future__ import annotations

import argparse
import dataclasses
import os
import sys
import time
from enum import Enum
from pathlib import Path

import agent_turn
import completion_shim
import reporters
import walk_stop
import watch_agent

__version__ = "2.5.0"

# Both stay module attributes here, so a suite that patches `watch_process.<name>` still bites.
process_alive = walk_stop.process_alive
stop_lingering = walk_stop.stop_lingering

# The providers whose error result is still an ending the disk decides on (module docstring).
_AN_ERROR_RESULT_ENDS_THE_TURN = frozenset({"claude", "hf", "ollama"})


class ProcessHookOutcome(str, Enum):
    """Outcomes a structured provider process can hand to an orchestration hook."""

    COMPLETED = "completed"
    PRODUCED_NOTHING = "produced_nothing"
    STOPPED = "stopped"
    FAILED = "failed"
    TIMEOUT = "timeout"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--provider", choices=("claude", "codex", "gemini", "hf", "ollama"), required=True
    )
    parser.add_argument("--pid", type=int, required=True)
    parser.add_argument("--log", required=True)
    parser.add_argument("--label", required=True)
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--reporter", default="generic")
    parser.add_argument("--artifact-path")
    parser.add_argument("--document-stem", default="")
    parser.add_argument("--head-repo")
    parser.add_argument("--done-when-exists")
    parser.add_argument("--multi-turn", action="store_true",
                        help="the run says it is finished with --done-when-exists; ending "
                             "without it is a cut-off, handed on as stopped")
    parser.add_argument("--notify", default=watch_agent.default_notifier())
    parser.add_argument("--on-complete")
    parser.add_argument("--poll-seconds", type=float, default=5.0)
    parser.add_argument("--timeout-seconds", type=float, default=6 * 60 * 60)
    args = parser.parse_args(argv)
    if args.multi_turn and not args.done_when_exists:
        parser.error("--multi-turn requires --done-when-exists")
    return args


def _outcome(args, state, head_before, reports_before):
    head_repo = args.head_repo or args.artifact_path
    ctx = reporters.OutcomeContext(
        label=args.label,
        cwd=args.cwd,
        artifact_path=args.artifact_path,
        document_stem=args.document_stem,
        state=state,
        head_before=head_before,
        head_after=watch_agent.git_head(head_repo),
        reports_before=reports_before,
    )
    try:
        result = reporters.get_reporter(args.reporter)(ctx)
        return dataclasses.replace(
            result, produced_nothing=reporters.produced_nothing(ctx)
        )
    except Exception:
        return reporters.Outcome(f"{args.label}: run ended.")


def _publish_receipt(files, destination: str | None, turn) -> None:
    """Publish the provider's final message at `destination`, before the hook runs. A failure to
    write it never suppresses the hook: the receipt is evidence for the engine, and an engine
    that finds none reads the run as having left none."""
    try:
        completion_shim.write_result(files, destination, turn.last_message)
    except OSError as error:
        print(f"watch_process: could not publish the final message at {destination}: {error}",
              file=sys.stderr, flush=True)


def _hook(path: str | None, outcome: ProcessHookOutcome) -> None:
    if not path:
        return
    watch_agent.run_on_complete_hook(path, outcome)


def _ended_by_provider(provider: str, turn) -> bool:
    return turn.state == "completed" or (
        turn.terminal and provider in _AN_ERROR_RESULT_ENDS_THE_TURN
    )


def _state_note(args, turn, marker_seen: bool, cut_off: bool) -> str:
    """The process's own ending, as a footnote — it qualifies the outcome, never states it."""
    if cut_off:
        note = (f"(run process {args.pid} ended without its completion marker at "
                f"{args.done_when_exists} — provider: {args.provider}; it may have been cut off "
                f"mid-walk)")
    elif turn.terminal and turn.state == "failed":
        note = (f"(run process {args.pid} ended its turn on an error — provider: "
                f"{args.provider}: {turn.detail or 'no detail'})")
    else:
        note = f"(run process {args.pid} completed — provider: {args.provider})"
    if marker_seen:
        note += f"\n(completion marker: {args.done_when_exists})"
    if turn.session_id:
        note += f"\n(run session {turn.session_id})"
    return note


def _denial_note(denials: tuple[str, ...]) -> str:
    count = len(denials)
    noun = "action" if count == 1 else "actions"
    return f"(the run was denied {count} {noun} nobody could approve: {', '.join(denials)})"


def _hook_refusal_note(refusals: tuple[str, ...]) -> str:
    count = len(refusals)
    noun = "call" if count == 1 else "calls"
    return (f"(a hook refused {count} {noun} and told the run what to do instead — no approval "
            f"was needed: {', '.join(refusals)})")


def main(argv=None, *, receipt_files=None) -> int:
    args = parse_args(argv)
    # Read once, at startup: where this watcher publishes the final message, if it was told.
    receipt_destination = os.environ.get(completion_shim.RESULT_FILE_VARIABLE) or None
    receipt_files = receipt_files or completion_shim.DiskReceiptFiles()
    # What makes an empty watcher log mean "the watcher never started", as `watch_agent.py`'s own
    # first line does for a `claude --bg` run.
    print(f"watch_process: watching {args.label} — {args.provider} process {args.pid}, log "
          f"{args.log} — at {time.strftime('%Y-%m-%d %H:%M:%S')}", file=sys.stderr, flush=True)
    head_repo = args.head_repo or args.artifact_path
    head_before = watch_agent.git_head(head_repo)
    reports_before = (
        reporters.self_answer_reports_present(args.artifact_path, args.document_stem or None)
        if args.artifact_path else None
    )
    marker_before = bool(args.done_when_exists and os.path.exists(args.done_when_exists))
    deadline = time.monotonic() + args.timeout_seconds

    while True:
        turn = agent_turn.inspect(args.provider, Path(args.log))
        marker = watch_agent.completion_marker_seen(args.done_when_exists, marker_before)
        if marker or _ended_by_provider(args.provider, turn):
            cut_off = args.multi_turn and not marker
            outcome = _outcome(args, "completed", head_before, reports_before)
            message = outcome.body
            refusal = watch_agent.refusal_of(turn.session_id) if turn.session_id else None
            if refusal:
                message += "\n" + watch_agent.refusal_note(refusal)
            message += "\n" + _state_note(args, turn, marker, cut_off)
            if turn.denials:
                message += "\n" + _denial_note(turn.denials)
            if turn.hook_refusals:
                message += "\n" + _hook_refusal_note(turn.hook_refusals)
            if outcome.footnote:
                message += "\n" + outcome.footnote
            watch_agent.notify(args.notify, message)
            _publish_receipt(receipt_files, receipt_destination, turn)
            if cut_off:
                _hook(args.on_complete, ProcessHookOutcome.STOPPED)
            else:
                _hook(
                    args.on_complete,
                    ProcessHookOutcome.PRODUCED_NOTHING
                    if outcome.produced_nothing
                    else ProcessHookOutcome.COMPLETED,
                )
            stop_lingering(args.pid)
            return 0
        if turn.state == "failed":
            watch_agent.notify(
                args.notify,
                f"⚠️ {args.label}: {args.provider} run failed.\n{turn.detail or 'No detail.'}\n"
                f"(structured log: {args.log})",
            )
            _hook(args.on_complete, ProcessHookOutcome.FAILED)
            return 1
        if not process_alive(args.pid):
            watch_agent.notify(
                args.notify,
                f"⚠️ {args.label}: process {args.pid} exited without a terminal provider event.\n"
                f"(structured log: {args.log})",
            )
            _hook(args.on_complete, ProcessHookOutcome.FAILED)
            return 1
        if time.monotonic() >= deadline:
            break
        time.sleep(args.poll_seconds)

    timeout_message = (
        f"⏱️ {args.label}: process {args.pid} still has no terminal event after "
        f"{int(args.timeout_seconds / 3600)}h — no longer watching.\n"
        f"(structured log: {args.log})"
    )
    if args.done_when_exists:
        timeout_message += f"\nThe marker at {args.done_when_exists} never appeared."
    watch_agent.notify(args.notify, timeout_message)
    _hook(args.on_complete, ProcessHookOutcome.TIMEOUT)
    return 1


if __name__ == "__main__":
    sys.exit(main())
