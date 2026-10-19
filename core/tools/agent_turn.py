#!/usr/bin/env python3
"""Run one detached, machine-readable turn in a persistent agent conversation."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

import agent_run
import agent_session
import model_assignment
import pin
import task_context

__version__ = "2.3.0"

# Claude Code's prefix on the tool result of a call a PreToolUse hook refused.
_HOOK_REFUSAL = re.compile(r"(?:Error: )?PreToolUse:\w+ hook error:")


@dataclass(frozen=True)
class TurnLaunch:
    provider: str
    session_id: str
    log_path: Path
    pid: int

    def as_dict(self) -> dict:
        value = asdict(self)
        value["log_path"] = str(self.log_path)
        return value


def _assignment(provider: str, model: str | None, tier: str | None):
    if model and tier:
        raise ValueError("--model and --model-tier are mutually exclusive")
    return model_assignment.resolve(provider, tier) if tier else (
        model_assignment.ModelAssignment(model) if model else None
    )


def claude_command(*, prompt: str, session_id: str, resume: bool, agent: str | None,
                   name: str | None, model: str | None, tier: str | None,
                   add_dirs: tuple[str, ...], settings: str | None,
                   pin: pin.Pin | None = None,
                   instance_root: Path | None = None,
                   effort: agent_run.Effort | None = None) -> tuple[str, ...]:
    """`Shape.TURN` — delegates to `agent_run.ClaudeAdapter`, so a turn carries the pin's Claude
    delivery exactly as any other shape does when `pin` is set (`agent_run._pin_delivery`), and
    today's command unchanged when it is not."""
    request = agent_run.RunRequest(
        prompt=prompt, agent=agent, name=name,
        resume_session_id=session_id if resume else None,
        model=model, model_tier=tier, add_dirs=add_dirs, settings=settings,
        shape=agent_run.Shape.TURN, session_id=session_id, instance_root=instance_root,
        pin=pin, effort=effort,
    )
    return agent_run.ClaudeAdapter().command(request)


def codex_command(*, prompt: str, session_id: str | None, model: str | None,
                  tier: str | None, add_dirs: tuple[str, ...],
                  core_root: Path | None = None,
                  effort: agent_run.Effort | None = None) -> tuple[str, ...]:
    """One detached Codex turn. A caller's `effort` wins over the assignment's own level, as it
    does in `agent_run.CodexAdapter`, and is the level the prompt's identity block reports."""
    argv = ["codex", "exec", "--approve-for-me"]
    if session_id:
        argv.append("resume")
    argv.append("--json")
    assignment = _assignment("codex", model, tier)
    reasoning_effort = (
        effort.value if effort is not None
        else (assignment.reasoning_effort if assignment else None)
    )
    if assignment:
        argv.extend(("--model", assignment.model))
    if reasoning_effort:
        argv.extend(("--config", f'model_reasoning_effort="{reasoning_effort}"'))
    if not session_id:
        for directory in add_dirs:
            argv.extend(("--add-dir", directory))
    if session_id:
        argv.append(session_id)
    if core_root is not None:
        prompt = task_context.codex_bootstrap(
            core_root,
            prompt,
            assignment.model if assignment else None,
            reasoning_effort,
        )
    argv.append(prompt)
    return tuple(argv)


def inspect_claude_log(
    text: str, session_id: str | None = None
) -> agent_session.TurnState:
    """Reduce Claude's `stream-json` events to the state needed by an orchestrator.

    A `kensai.exit` record (appended by `launch`'s exit wrapper once the claude process has
    exited) seen before any terminal `result` event reports the turn as `failed`, with the log's
    non-JSON tail as `detail` — the process died before emitting a single stream-json event. A
    `kensai.exit` after a `result` changes nothing; a log with no `kensai.exit` record behaves
    exactly as before this record existed.

    A `permission_denials` entry whose tool result is a PreToolUse hook's refusal goes to
    `hook_refusals` rather than `denials`: Claude lists both, but only the second kind waited on
    a person.
    """
    state, message, detail = "starting", None, None
    terminal = False
    denials: tuple[str, ...] = ()
    hook_refusals: tuple[str, ...] = ()
    hook_refused_ids: set[str] = set()
    non_json_lines: list[str] = []
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            if line.strip():
                non_json_lines.append(line.strip())
            continue
        if event.get("type") == agent_session.KENSAI_EXIT_EVENT:
            if not terminal:
                state = "failed"
                detail = agent_session.exit_without_result_detail(non_json_lines, event.get("code"))
            continue
        session_id = str(event.get("session_id") or session_id or "") or None
        if event.get("type") in {"system", "assistant", "user"}:
            state = "running"
        if event.get("type") == "user":
            hook_refused_ids.update(_hook_refused_tool_use_ids(event))
        if event.get("type") == "result":
            message = event.get("result")
            terminal = True
            refused = [
                denial for denial in event.get("permission_denials") or ()
                if isinstance(denial, dict)
            ]
            denials = tuple(
                str(denial.get("tool_name") or "unnamed") for denial in refused
                if denial.get("tool_use_id") not in hook_refused_ids
            )
            hook_refusals = tuple(
                str(denial.get("tool_name") or "unnamed") for denial in refused
                if denial.get("tool_use_id") in hook_refused_ids
            )
            if event.get("subtype") == "success" and not event.get("is_error"):
                state = "completed"
            else:
                state, detail = "failed", str(event.get("result") or event.get("subtype"))
    return agent_session.TurnState(
        "claude", session_id, state, message, detail, terminal=terminal, denials=denials,
        hook_refusals=hook_refusals,
    )


def _hook_refused_tool_use_ids(event: dict) -> list[str]:
    """The `tool_use_id` of each error tool result in a `user` event whose text opens with
    Claude Code's PreToolUse hook prefix, `PreToolUse:<tool> hook error:`."""
    content = (event.get("message") or {}).get("content")
    if not isinstance(content, list):
        return []
    refused = []
    for block in content:
        if not (isinstance(block, dict) and block.get("type") == "tool_result"
                and block.get("is_error")):
            continue
        text = block.get("content")
        if isinstance(text, list):
            text = "".join(part.get("text", "") for part in text if isinstance(part, dict))
        if isinstance(text, str) and _HOOK_REFUSAL.match(text):
            refused.append(str(block.get("tool_use_id")))
    return refused


def gemini_command(*, prompt: str, session_id: str | None, resume: bool,
                   agent: str | None, model: str | None, tier: str | None,
                   add_dirs: tuple[str, ...], settings: str | None,
                   core_root: Path | None = None,
                   instance_root: Path | None = None,
                   pin: pin.Pin | None = None,
                   effort: agent_run.Effort | None = None) -> tuple[str, ...]:
    """One detached Gemini turn. The log is `stream-json`, reduced by
    `inspect_gemini_log`."""
    request = agent_run.RunRequest(
        prompt=prompt, agent=agent,
        resume_session_id=session_id if resume else None,
        model=model, model_tier=tier, add_dirs=add_dirs, settings=settings,
        core_root=core_root, session_id=None if resume else session_id,
        instance_root=instance_root, pin=pin, effort=effort,
    )
    return agent_run.GeminiAdapter().background_command(request)


def inspect(provider: str, path: Path, session_id: str | None = None):
    text = agent_session.SessionRunner._read_log(path)
    if provider == "codex":
        return agent_session.inspect_codex_log(text, session_id)
    if provider == "gemini":
        return agent_session.inspect_gemini_log(text, session_id)
    if provider in {"claude", "hf", "ollama"}:
        return inspect_claude_log(text, session_id)
    raise agent_run.UnknownProvider(f"unknown provider {provider!r}")


def launch(provider: str, argv: tuple[str, ...], log_path: Path,
           session_id: str | None, timeout: float) -> TurnLaunch:
    """Start `argv` detached through `agent_run.Subprocesses.start_detached`, logging its combined
    stdout/stderr to `log_path` with a `kensai.exit` record appended once it exits — so the
    returned `TurnLaunch.pid` is the exit-record wrapper's, which lives exactly as long as the
    provider process does and shares its process group.
    """
    pid = agent_run.Subprocesses().start_detached(argv, log_path)
    if provider in {"codex", "gemini"} and session_id is None:
        deadline = time.monotonic() + timeout
        while not session_id:
            session_id = agent_session.identity_from_log(
                provider, agent_session.SessionRunner._read_log(log_path))
            if session_id:
                break
            if time.monotonic() >= deadline:
                raise agent_session.IdentityTimeout(
                    f"{provider} wrote no session identity to {log_path} within {timeout:g}s")
            time.sleep(0.05)
    assert session_id is not None
    return TurnLaunch(provider, session_id, log_path, pid)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser()
    commands = result.add_subparsers(dest="command", required=True)
    for command in ("start", "resume"):
        sub = commands.add_parser(command)
        sub.add_argument("--provider", choices=("claude", "codex", "gemini"), required=True)
        sub.add_argument("--prompt", required=True)
        sub.add_argument("--log", type=Path, required=True)
        sub.add_argument("--session-id", required=command == "resume")
        sub.add_argument("--name")
        sub.add_argument("--agent")
        sub.add_argument("--agent-file", type=Path)
        models = sub.add_mutually_exclusive_group()
        models.add_argument("--model")
        models.add_argument("--model-tier", choices=model_assignment.TIERS)
        sub.add_argument("--add-dir", action="append", default=[])
        sub.add_argument("--settings")
        sub.add_argument("--core-dir", type=Path)
        sub.add_argument("--instance-root", type=Path)
        sub.add_argument("--identity-timeout", type=float, default=30.0)
    inspect_parser = commands.add_parser("inspect")
    inspect_parser.add_argument(
        "--provider", choices=("claude", "codex", "gemini"), required=True
    )
    inspect_parser.add_argument("--session-id", required=True)
    inspect_parser.add_argument("--log", type=Path, required=True)
    return result


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if args.command == "inspect":
        print(json.dumps(inspect(args.provider, args.log, args.session_id).as_dict(), sort_keys=True))
        return 0
    session_id = args.session_id if args.command == "resume" else None
    prompt = args.prompt
    if args.provider in {"codex", "gemini"} and args.command == "start" and args.agent:
        if not args.agent_file:
            print(
                f"agent-turn: {args.provider} agent selection requires --agent-file",
                file=sys.stderr,
            )
            return 2
        prompt = (f"You are running as the {args.agent} agent. Read {args.agent_file} in full "
                  f"and follow it as your agent identity before doing this task:\n\n{prompt}")
    if args.provider == "claude":
        try:
            resolved_pin = pin.inherited(os.environ)
        except pin.PinMissing as error:
            print(f"agent-turn: {error}", file=sys.stderr)
            return 2
        session_id = session_id or str(uuid.uuid4())
        command = claude_command(prompt=prompt, session_id=session_id,
                                 resume=args.command == "resume", agent=args.agent,
                                 name=args.name, model=args.model, tier=args.model_tier,
                                 add_dirs=tuple(args.add_dir), settings=args.settings,
                                 pin=resolved_pin, instance_root=args.instance_root)
    elif args.provider == "gemini":
        session_id = session_id or None
        try:
            command = gemini_command(prompt=prompt, session_id=session_id,
                                     resume=args.command == "resume", agent=None,
                                     model=args.model, tier=args.model_tier,
                                     add_dirs=tuple(args.add_dir), settings=args.settings,
                                     core_root=args.core_dir, instance_root=args.instance_root)
        except (agent_run.UnsupportedRequest, model_assignment.UnknownProvider,
                model_assignment.UnknownTier) as error:
            print(f"agent-turn: {error}", file=sys.stderr)
            return 2
    else:
        if args.settings:
            print("agent-turn: Codex does not support --settings", file=sys.stderr)
            return 2
        command = codex_command(prompt=prompt, session_id=session_id, model=args.model,
                                tier=args.model_tier, add_dirs=tuple(args.add_dir),
                                core_root=args.core_dir)
    try:
        turn = launch(args.provider, command, args.log, session_id, args.identity_timeout)
    except (OSError, ValueError, model_assignment.UnknownTier,
            agent_session.IdentityTimeout) as error:
        print(f"agent-turn: {error}", file=sys.stderr)
        return 2
    print(json.dumps(turn.as_dict(), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
