"""Contract tests for persistent provider conversation identity."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import agent_session

_SCRIPT = Path(__file__).resolve().parent / "agent_session.py"


def test_claude_identity_is_read_from_ansi_wrapped_launch_output():
    text = "\x1b[32m  ⏿  backgrounded · agent-123 · demo\x1b[0m\n"

    assert agent_session.identity_from_log("claude", text) == "agent-123"


def test_codex_identity_is_read_from_the_thread_started_event():
    text = "noise\n" + json.dumps(
        {"type": "thread.started", "thread_id": "thread-123"}
    )

    assert agent_session.identity_from_log("codex", text) == "thread-123"


def test_codex_log_reduces_to_completion_and_the_last_agent_message():
    text = "\n".join(
        json.dumps(event)
        for event in (
            {"type": "thread.started", "thread_id": "thread-1"},
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "first"},
            },
            {
                "type": "item.completed",
                "item": {"type": "agent_message", "text": "final reply"},
            },
            {"type": "turn.completed"},
        )
    )

    assert agent_session.inspect_codex_log(text) == agent_session.TurnState(
        "codex", "thread-1", "completed", "final reply", terminal=True
    )


def test_codex_log_reports_a_failed_turn_without_losing_thread_identity():
    text = "\n".join(
        (
            '{"type":"thread.started","thread_id":"thread-1"}',
            '{"type":"turn.failed","error":{"message":"nope"}}',
        )
    )

    state = agent_session.inspect_codex_log(text)

    assert state.state == "failed"
    assert state.session_id == "thread-1"
    assert state.detail == '{"message": "nope"}'


def test_codex_log_reports_failed_when_the_exit_record_precedes_any_terminal_event():
    """A codex process that dies before emitting a single JSON event — the same failure mode as
    the claude case (`test_agent_turn.py`'s product-sdd run-30 test) — leaves only its plain-text
    error plus the exit wrapper's `kensai.exit` record. Provider parity: same behaviour as
    claude."""
    text = "\n".join((
        "Error: boom",
        json.dumps({"type": "kensai.exit", "code": 1}),
    ))

    state = agent_session.inspect_codex_log(text)

    assert state.state == "failed"
    assert "boom" in state.detail
    assert "exit code 1" in state.detail


def test_codex_log_exit_record_after_turn_completed_changes_nothing():
    text = "\n".join((
        json.dumps({"type": "thread.started", "thread_id": "thread-1"}),
        json.dumps({"type": "turn.completed"}),
        json.dumps({"type": "kensai.exit", "code": 0}),
    ))

    state = agent_session.inspect_codex_log(text)

    assert state.state == "completed"
    assert state.session_id == "thread-1"


def test_codex_log_without_an_exit_record_is_unchanged():
    text = json.dumps({"type": "thread.started", "thread_id": "thread-1"})

    state = agent_session.inspect_codex_log(text)

    assert state.state == "running"
    assert state.detail is None


def _write_executable(path: Path, text: str) -> None:
    path.write_text(text)
    path.chmod(0o755)


def _read_when_present(path: Path, timeout: float = 30.0) -> str:
    # The fake codex is a detached child that can start seconds late under a parallel suite, and
    # its `open(..., 'w')` makes the file before the write lands — so an empty file is not there
    # yet. The wait returns the moment the text is, so the long ceiling costs a green run nothing.
    deadline = time.monotonic() + timeout
    while True:
        try:
            text = path.read_text()
            if text:
                return text
        except FileNotFoundError:
            pass
        if time.monotonic() >= deadline:
            raise FileNotFoundError(f"{path} was not written within {timeout}s")
        time.sleep(0.01)


def test_cli_starts_codex_and_returns_the_durable_thread_identity(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    argv_log = tmp_path / "argv.json"
    _write_executable(
        bin_dir / "codex",
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "open(os.environ['ARGV_LOG'], 'w').write(json.dumps(sys.argv[1:]))\n"
        "print(json.dumps({'type':'thread.started','thread_id':'thread-7'}), flush=True)\n"
        "print(json.dumps({'type':'turn.completed'}), flush=True)\n",
    )
    log_path = tmp_path / "start.jsonl"
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["ARGV_LOG"] = str(argv_log)

    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "start",
            "--provider",
            "codex",
            "--name",
            "sdd-demo-cpo",
            "--prompt",
            "first turn",
            "--model-tier",
            "fable",
            "--log",
            str(log_path),
        ],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "log_path": str(log_path),
        "logical_name": "sdd-demo-cpo",
        "pid": json.loads(result.stdout)["pid"],
        "provider": "codex",
        "session_id": "thread-7",
    }
    assert isinstance(json.loads(result.stdout)["pid"], int)
    argv = json.loads(_read_when_present(argv_log))
    assert argv[:3] == ["exec", "--approve-for-me", "--json"]
    assert argv[-1] == "first turn"


def test_cli_resumes_codex_by_thread_id(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    argv_log = tmp_path / "argv.json"
    _write_executable(
        bin_dir / "codex",
        "#!/usr/bin/env python3\n"
        "import json, os, sys\n"
        "open(os.environ['ARGV_LOG'], 'w').write(json.dumps(sys.argv[1:]))\n"
        "print(json.dumps({'type':'turn.completed'}), flush=True)\n",
    )
    log_path = tmp_path / "resume.jsonl"
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["ARGV_LOG"] = str(argv_log)

    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "resume",
            "--provider",
            "codex",
            "--session-id",
            "thread-7",
            "--name",
            "sdd-demo-cpo",
            "--prompt",
            "next turn",
            "--model-tier",
            "fable",
            "--log",
            str(log_path),
        ],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    launch = json.loads(result.stdout)
    assert launch["session_id"] == "thread-7"
    assert launch["logical_name"] == "sdd-demo-cpo"
    argv = json.loads(_read_when_present(argv_log))
    assert argv[:5] == [
        "exec", "--approve-for-me", "resume", "--json", "--model"
    ]
    assert argv[-2:] == ["thread-7", "next turn"]


def test_cli_inspects_a_codex_turn_log(tmp_path):
    log_path = tmp_path / "turn.jsonl"
    log_path.write_text(
        '{"type":"thread.started","thread_id":"thread-7"}\n'
        '{"type":"item.completed","item":{"type":"agent_message","text":"done"}}\n'
        '{"type":"turn.completed"}\n'
    )

    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "inspect",
            "--provider",
            "codex",
            "--session-id",
            "thread-7",
            "--log",
            str(log_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "denials": [],
        "hook_refusals": [],
        "detail": None,
        "last_message": "done",
        "provider": "codex",
        "session_id": "thread-7",
        "state": "completed",
        "terminal": True,
    }


def test_gemini_identity_is_read_from_init_event():
    text = '{"event":"init","conversation_id":"gem-123"}\n'
    assert agent_session.identity_from_log("gemini", text) == "gem-123"


def test_gemini_log_reduces_to_completion_and_response():
    text = "\n".join((
        '{"event":"init","conversation_id":"gem-1"}',
        '{"event":"step_update","step_update":{"step_type":"agent_response","text_delta":"done"}}',
        '{"event":"result","result":{"conversation_id":"gem-1","status":"SUCCESS","response":"done"}}',
    ))

    assert agent_session.inspect_gemini_log(text) == agent_session.TurnState(
        "gemini", "gem-1", "completed", "done", terminal=True
    )


def test_gemini_log_reports_denials_and_failure():
    text = json.dumps({
        "event": "result",
        "result": {
            "conversation_id": "gem-1",
            "status": "FAILED",
            "response": "blocked",
            "denied_actions": [{"action": "command"}],
        },
    })

    state = agent_session.inspect_gemini_log(text)
    assert state.state == "failed"
    assert state.denials == ("command",)
    assert state.detail == "blocked"
    assert state.terminal is True


def test_gemini_log_reports_failed_when_exit_record_precedes_result():
    text = "\n".join((
        "Error: crash",
        json.dumps({"type": "kensai.exit", "code": 1}),
    ))

    state = agent_session.inspect_gemini_log(text)
    assert state.state == "failed"
    assert "crash" in state.detail
    assert "exit code 1" in state.detail


def test_cli_inspects_a_gemini_turn_log(tmp_path):
    log_path = tmp_path / "gemini_turn.jsonl"
    log_path.write_text(
        '{"event":"init","conversation_id":"gem-7"}\n'
        '{"event":"result","result":{"conversation_id":"gem-7","status":"SUCCESS","response":"all good"}}\n'
    )

    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "inspect",
            "--provider",
            "gemini",
            "--session-id",
            "gem-7",
            "--log",
            str(log_path),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "denials": [],
        "hook_refusals": [],
        "detail": None,
        "last_message": "all good",
        "provider": "gemini",
        "session_id": "gem-7",
        "state": "completed",
        "terminal": True,
    }
