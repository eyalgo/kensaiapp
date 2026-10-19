#!/usr/bin/env python3
"""Start, resume, and inspect persistent provider conversations.

``agent_run`` owns provider command construction and process lifetime. This
module owns the identity that survives one turn: Claude's background-agent ID
or Codex's thread ID. A logical Kensaiapp agent name is metadata around that
provider identity; it is never confused with a role.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Sequence

import agent_run
import model_assignment

__version__ = "2.1.0"

_ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_CLAUDE_ID = re.compile(r"backgrounded\s+·\s+(\S+)")
_TERMINAL_CLAUDE_STATES = {"done", "stopped", "blocked"}


class IdentityTimeout(RuntimeError):
    pass


class InspectFailed(RuntimeError):
    pass


KENSAI_EXIT_EVENT = "kensai.exit"


def exit_without_result_detail(non_json_lines: list[str], code: object, limit: int = 5) -> str:
    """Compose the `detail` for a `kensai.exit` record (`agent_turn.launch`'s exit wrapper) seen
    before any terminal provider event — the log's non-JSON tail (trimmed to the last `limit`
    lines) plus the exit code, so a process that died before emitting a single JSON event still
    surfaces its error text instead of leaving the caller to poll a state that never resolves."""
    tail = "\n".join(non_json_lines[-limit:])
    code_text = f"exit code {code}" if code is not None else "no exit code"
    return f"{tail}\n({code_text})" if tail else f"({code_text})"


@dataclass(frozen=True)
class SessionTurn:
    provider: str
    session_id: str
    logical_name: str | None
    log_path: Path
    pid: int | None

    def as_dict(self) -> dict[str, str | int | None]:
        result = asdict(self)
        result["log_path"] = str(self.log_path)
        return result


@dataclass(frozen=True)
class TurnState:
    """One turn reduced to what an orchestrator acts on. `terminal` says the provider itself
    ended the turn with its own terminal event, as against a `failed` read off a `kensai.exit`
    record that came first; `denials` names the tool of every action the run was refused because
    nobody could approve it (Claude's `result.permission_denials`), in order. `hook_refusals` names
    the tool of each of those that a PreToolUse hook refused instead: the hook's own message told
    the run what to do, so no one was ever asked, and it is not in `denials`."""

    provider: str
    session_id: str | None
    state: str
    last_message: str | None = None
    detail: str | None = None
    terminal: bool = False
    denials: tuple[str, ...] = ()
    hook_refusals: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, str | None]:
        return asdict(self)


def identity_from_log(provider: str, text: str) -> str | None:
    """Read the provider conversation identity from one launch log."""

    if provider == "claude":
        match = _CLAUDE_ID.search(_ANSI.sub("", text))
        return match.group(1) if match else None
    if provider == "codex":
        for line in text.splitlines():
            try:
                event = json.loads(line)
            except (TypeError, ValueError):
                continue
            if event.get("type") == "thread.started" and event.get("thread_id"):
                return str(event["thread_id"])
        return None
    if provider == "gemini":
        for line in text.splitlines():
            try:
                event = json.loads(line)
            except (TypeError, ValueError):
                continue
            conversation_id = event.get("conversation_id") or (
                event.get("result", {}).get("conversation_id")
                if isinstance(event.get("result"), dict)
                else None
            )
            if conversation_id:
                return str(conversation_id)
        return None
    raise agent_run.UnknownProvider(f"unknown provider {provider!r}")


def inspect_gemini_log(text: str, expected_session_id: str | None = None) -> TurnState:
    """Reduce Gemini stream-json events to the state needed by an orchestrator."""
    session_id = expected_session_id
    state = "starting"
    last_message = None
    detail = None
    terminal = False
    denials: tuple[str, ...] = ()
    non_json_lines: list[str] = []
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except (TypeError, ValueError):
            if line.strip():
                non_json_lines.append(line.strip())
            continue
        event_type = event.get("type")
        if event_type == KENSAI_EXIT_EVENT:
            if not terminal:
                state = "failed"
                detail = exit_without_result_detail(non_json_lines, event.get("code"))
            continue
        event_name = event.get("event")
        if event_name == "init":
            session_id = str(event.get("conversation_id") or session_id or "") or None
            state = "running"
        elif event_name == "step_update":
            state = "running"
            step_update = event.get("step_update") or {}
            if step_update.get("step_type") == "agent_response":
                delta = step_update.get("text_delta")
                if delta:
                    last_message = (last_message or "") + delta
        elif event_name == "result":
            res = event.get("result") or {}
            terminal = True
            session_id = str(res.get("conversation_id") or session_id or "") or None
            if res.get("response") is not None:
                last_message = res.get("response")
            if res.get("denied_actions"):
                denials = tuple(
                    str(action.get("action") or "unnamed")
                    for action in res.get("denied_actions")
                    if isinstance(action, dict)
                )
            if res.get("status") == "SUCCESS":
                state = "completed"
            else:
                state = "failed"
                detail = str(res.get("response") or res.get("status"))
    return TurnState(
        "gemini", session_id, state, last_message, detail, terminal=terminal, denials=denials
    )


def inspect_codex_log(text: str, expected_session_id: str | None = None) -> TurnState:
    """Reduce Codex JSONL events to the state needed by an orchestrator.

    A `kensai.exit` record (appended by `agent_turn.launch`'s exit wrapper once the codex
    process has exited) seen before any terminal event (`turn.completed` / `turn.failed` /
    `error`) reports the turn as `failed`, with the log's non-JSON tail as `detail` — the process
    died before emitting anything Codex-shaped. A `kensai.exit` after a terminal event changes
    nothing; a log with no `kensai.exit` record behaves exactly as before this record existed.
    """

    session_id = expected_session_id
    state = "starting"
    last_message = None
    detail = None
    terminal = False
    non_json_lines: list[str] = []
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except (TypeError, ValueError):
            if line.strip():
                non_json_lines.append(line.strip())
            continue
        event_type = event.get("type")
        if event_type == KENSAI_EXIT_EVENT:
            if not terminal:
                state = "failed"
                detail = exit_without_result_detail(non_json_lines, event.get("code"))
            continue
        if event_type == "thread.started":
            session_id = str(event.get("thread_id") or session_id or "") or None
            state = "running"
        elif event_type == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message" and item.get("text") is not None:
                last_message = str(item["text"])
        elif event_type == "turn.completed":
            state = "completed"
            terminal = True
        elif event_type in {"turn.failed", "error"}:
            state = "failed"
            terminal = True
            error = event.get("error")
            detail = json.dumps(error, sort_keys=True) if error is not None else line
    return TurnState("codex", session_id, state, last_message, detail, terminal=terminal)


class SessionRunner:
    def __init__(
        self,
        runner: agent_run.AgentRunner,
        *,
        read_text: Callable[[Path], str] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._runner = runner
        self._read_text = read_text or self._read_log
        self._sleep = sleep

    @staticmethod
    def _read_log(path: Path) -> str:
        try:
            return path.read_text(errors="replace")
        except OSError:
            return ""

    def start(
        self,
        provider: str,
        request: agent_run.RunRequest,
        log_path: Path,
        *,
        identity_timeout: float = 30.0,
    ) -> SessionTurn:
        logical_name = request.name
        provider_request = request
        if provider in {"codex", "gemini"} and request.name:
            provider_request = dataclasses.replace(request, name=None)
        background = self._runner.background(provider, provider_request, log_path)
        session_id = self._await_identity(provider, log_path, identity_timeout)
        return SessionTurn(
            provider,
            session_id,
            logical_name,
            log_path,
            background.pid,
        )

    def resume(
        self,
        turn: SessionTurn,
        request: agent_run.RunRequest,
        log_path: Path,
    ) -> SessionTurn:
        provider_request = dataclasses.replace(
            request,
            name=request.name if turn.provider == "claude" else None,
            resume_session_id=turn.session_id,
        )
        background = self._runner.background(
            turn.provider, provider_request, log_path
        )
        return SessionTurn(
            turn.provider,
            turn.session_id,
            request.name or turn.logical_name,
            log_path,
            background.pid,
        )

    def _await_identity(
        self, provider: str, log_path: Path, timeout: float
    ) -> str:
        deadline = time.monotonic() + timeout
        while True:
            session_id = identity_from_log(provider, self._read_text(log_path))
            if session_id:
                return session_id
            if time.monotonic() >= deadline:
                raise IdentityTimeout(
                    f"provider {provider!r} wrote no session identity to {log_path} "
                    f"within {timeout:g}s"
                )
            self._sleep(min(0.05, max(0.0, deadline - time.monotonic())))


def inspect_claude(session_id: str) -> TurnState:
    """Read one Claude background session from the provider's agent list."""

    try:
        process = subprocess.run(
            ["claude", "agents", "--json", "--all"],
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise InspectFailed(f"could not inspect Claude sessions: {error}") from error
    if process.returncode != 0:
        raise InspectFailed(
            f"`claude agents --json --all` exited {process.returncode}: "
            f"{process.stderr.strip()}"
        )
    try:
        rows = json.loads(process.stdout)
    except (TypeError, ValueError) as error:
        raise InspectFailed("Claude session list was not valid JSON") from error
    for row in rows if isinstance(rows, list) else []:
        if row.get("id") == session_id or row.get("sessionId") == session_id:
            state = str(row.get("state") or "unknown")
            status = str(row.get("status") or "")
            if state in _TERMINAL_CLAUDE_STATES:
                normalized = "completed"
            elif status == "idle":
                normalized = "idle"
            else:
                normalized = "running"
            detail = f"state={state}" + (f", status={status}" if status else "")
            return TurnState("claude", session_id, normalized, detail=detail)
    return TurnState("claude", session_id, "vanished")


def _add_request_arguments(parser: argparse.ArgumentParser, *, resume: bool) -> None:
    parser.add_argument("--provider", required=True, choices=("claude", "codex", "gemini"))
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--name")
    parser.add_argument("--agent")
    model = parser.add_mutually_exclusive_group()
    model.add_argument("--model")
    model.add_argument("--model-tier", choices=model_assignment.TIERS)
    if not resume:
        parser.add_argument("--add-dir", action="append", default=[], dest="add_dirs")
    parser.add_argument("--settings")
    parser.add_argument("--core-dir", type=Path)
    parser.add_argument("--log", type=Path, required=True)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Start, resume, or inspect a persistent provider conversation."
    )
    commands = result.add_subparsers(dest="command", required=True)
    start = commands.add_parser("start")
    _add_request_arguments(start, resume=False)
    start.add_argument("--identity-timeout", type=float, default=30.0)
    resume = commands.add_parser("resume")
    _add_request_arguments(resume, resume=True)
    resume.add_argument("--session-id", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("--provider", required=True, choices=("claude", "codex", "gemini"))
    inspect.add_argument("--session-id", required=True)
    inspect.add_argument("--log", type=Path)
    return result


def _request(args: argparse.Namespace) -> agent_run.RunRequest:
    return agent_run.RunRequest(
        prompt=args.prompt,
        agent=args.agent,
        name=args.name,
        model=args.model,
        model_tier=args.model_tier,
        add_dirs=tuple(getattr(args, "add_dirs", ())),
        settings=args.settings,
        core_root=args.core_dir,
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "inspect":
        if args.provider == "codex":
            if args.log is None:
                print("agent-session: Codex inspect requires --log", file=sys.stderr)
                return 2
            state = inspect_codex_log(
                SessionRunner._read_log(args.log), args.session_id
            )
        elif args.provider == "gemini":
            if args.log is None:
                print("agent-session: Gemini inspect requires --log", file=sys.stderr)
                return 2
            state = inspect_gemini_log(
                SessionRunner._read_log(args.log), args.session_id
            )
        else:
            try:
                state = inspect_claude(args.session_id)
            except InspectFailed as error:
                print(f"agent-session: {error}", file=sys.stderr)
                return 2
        print(json.dumps(state.as_dict(), sort_keys=True))
        return 0

    runner = SessionRunner(agent_run.AgentRunner(agent_run.ADAPTERS, agent_run.Subprocesses()))
    try:
        if args.command == "start":
            turn = runner.start(
                args.provider,
                _request(args),
                args.log,
                identity_timeout=args.identity_timeout,
            )
        else:
            prior = SessionTurn(
                args.provider,
                args.session_id,
                args.name,
                args.log,
                None,
            )
            turn = runner.resume(prior, _request(args), args.log)
    except (
        agent_run.UnknownProvider,
        agent_run.UnsupportedRequest,
        model_assignment.UnknownProvider,
        model_assignment.UnknownTier,
        IdentityTimeout,
        OSError,
    ) as error:
        print(f"agent-session: {error}", file=sys.stderr)
        return 2
    print(json.dumps(turn.as_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
