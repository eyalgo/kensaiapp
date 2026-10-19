#!/usr/bin/env python3
"""Run a pinned skill through Codex's native app-server skill input.

Directory grants do not register skills. Register the launcher's resolved roots
in this process, verify the selected path, then let Codex inject the skill body.
The server is private to the run, so a renewed pin cannot reuse an old catalogue.
Execution guidance belongs to ../prompts/codex_execution.md, loaded from this runner's core.
Protocol: https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import deque
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence, TextIO

__version__ = "1.1.0"


class ProtocolError(RuntimeError):
    """The server cannot safely complete the requested skill turn."""


class Server(Protocol):
    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]: ...
    def receive(self) -> dict[str, Any]: ...


class StdioServer:
    def __init__(self, reader: TextIO, writer: TextIO) -> None:
        self.reader = reader
        self.writer = writer
        self.next_id = 0
        self.pending: deque[dict[str, Any]] = deque()

    def _read(self) -> dict[str, Any]:
        line = self.reader.readline()
        if not line:
            raise ProtocolError("Codex app-server exited before the turn completed")
        event = json.loads(line)
        if 'id' in event and 'method' in event:
            # Auto-review owns approvals. An interactive request cannot be answered by
            # an unattended launcher, and must never be silently accepted.
            self.writer.write(json.dumps({'id': event['id'], 'error': {
                'code': -32601, 'message': 'Unattended skill runner cannot answer interactive requests'
            }}) + '\n')
            self.writer.flush()
            if event["method"].endswith("/requestApproval"):
                raise ProtocolError(
                    f"interactive-approval-required: {event['method']}; "
                    "the unattended runner cannot obtain human approval; "
                    "the request was not accepted"
                )
            raise ProtocolError(f"Codex requested interactive input: {event['method']}")
        return event

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        self.next_id += 1
        request_id = self.next_id
        self.writer.write(json.dumps({'id': request_id, 'method': method, 'params': params}) + '\n')
        self.writer.flush()
        while True:
            event = self._read()
            if event.get('id') == request_id:
                if 'error' in event:
                    raise ProtocolError(f"{method}: {event['error']}")
                return event['result']
            self.pending.append(event)

    def receive(self) -> dict[str, Any]:
        return self.pending.popleft() if self.pending else self._read()


def run_skill(server: Server, *, cwd: Path, name: str, path: Path,
              roots: Sequence[Path], prompt: str, model: str | None,
              effort: str | None, add_dirs: Sequence[str],
              emit: Callable[[dict[str, Any]], None]) -> int:
    instructions = (Path(__file__).resolve().parents[1] / "prompts" / "codex_execution.md")
    execution_context = instructions.read_text(encoding="utf-8")
    if not execution_context.strip():
        raise ProtocolError(f"Codex execution instructions are empty: {instructions}")
    server.request('initialize', {'clientInfo': {'name': 'kensaiapp', 'version': __version__},
                                  'capabilities': {'experimentalApi': True}})
    server.request('skills/extraRoots/set', {'extraRoots': [str(root.resolve()) for root in roots]})
    catalogue = server.request('skills/list', {'cwds': [str(cwd)], 'forceReload': True})
    selected = next((skill for row in catalogue.get('data', []) for skill in row.get('skills', [])
                     if skill['name'] == name and Path(skill['path']).resolve() == path.resolve()
                     and skill.get('enabled', True)), None)
    if selected is None:
        raise ProtocolError(f"Skill {name!r} not discovered at {path.resolve()}; refusing to start")
    thread = server.request('thread/start', {
        'cwd': str(cwd), 'model': model, 'sandbox': 'workspace-write',
        'approvalPolicy': 'on-request', 'approvalsReviewer': 'auto_review',
        'config': {'sandbox_workspace_write': {'writable_roots': list(add_dirs)}},
    })
    thread_id = thread['thread']['id']
    emit({'type': 'thread.started', 'thread_id': thread_id})
    turn = server.request('turn/start', {
        'threadId': thread_id, 'effort': effort,
        'input': [{"type": "text", "text": execution_context},
                  {'type': 'text', 'text': prompt},
                  {'type': 'skill', 'name': name, 'path': selected['path']}],
    })
    turn_id = turn['turn']['id']
    emit({'type': 'turn.started'})
    while True:
        event = server.receive()
        emit({'type': 'kensai.codex.notification', 'event': event})
        params = event.get('params', {})
        if params.get('threadId') != thread_id:
            continue
        if event.get('method') == 'item/completed':
            item = params['item']
            if item.get('type') == 'agentMessage':
                emit({'type': 'item.completed', 'item': {
                    'type': 'agent_message', 'text': item['text'], 'id': item['id']}})
        if event.get('method') == 'turn/completed' and params['turn']['id'] == turn_id:
            completed = params['turn']['status'] == 'completed'
            emit({'type': 'turn.completed'} if completed else {
                'type': 'turn.failed', 'error': params['turn'].get('error') or params['turn']['status']})
            return 0 if completed else 1


def skill_roots(core_root: Path | None, path: Path) -> list[Path]:
    roots = [path.parent.parent]
    if core_root is not None:
        host = core_root.parent
        roots += [host / '.claude' / 'skills']
        roots += sorted((host / 'skills').glob('*/.claude/skills'))
    return list(dict.fromkeys(root.resolve() for root in roots if root.is_dir()))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--skill-name', required=True)
    parser.add_argument('--skill-path', required=True, type=Path)
    parser.add_argument('--core-dir', type=Path)
    parser.add_argument('--model')
    parser.add_argument('--config', action='append', default=[])
    parser.add_argument('--add-dir', action='append', default=[])
    parser.add_argument('--json', action='store_true')
    parser.add_argument('prompt')
    args = parser.parse_args(argv)
    command = ['codex', 'app-server']
    effort = None
    for config in args.config:
        command.extend(['--config', config])
        if config.startswith('model_reasoning_effort='):
            effort = json.loads(config.split('=', 1)[1])
    def emit(event: dict[str, Any]) -> None:
        if args.json:
            print(json.dumps(event), flush=True)
        elif event['type'] == 'item.completed':
            print(event['item']['text'], flush=True)
        elif event['type'] == 'turn.failed':
            print(event['error'], file=sys.stderr, flush=True)
    try:
        with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                              text=True) as process:
            try:
                assert process.stdin is not None and process.stdout is not None
                return run_skill(StdioServer(process.stdout, process.stdin), cwd=Path.cwd(),
                                 name=args.skill_name, path=args.skill_path,
                                 roots=skill_roots(args.core_dir, args.skill_path),
                                 prompt=args.prompt, model=args.model, effort=effort,
                                 add_dirs=args.add_dir, emit=emit)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
    except (OSError, ValueError, ProtocolError) as error:
        emit({'type': 'turn.failed', 'error': str(error)})
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
