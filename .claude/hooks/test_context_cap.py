"""Tests for `context_cap.py` — the `PostToolUse` `Bash` hook that tells a developer run to pause.

Runs the real entry point — JSON on stdin, JSON or silence on stdout — the way Claude Code does,
following `test_written_forward_guard.py`'s shape. The hook finds the gauge through
`resolve_core._resolve(project_dir)`, so each test names the project dir it runs against: this
host for the ordinary cases, and a synthetic satellite (no `core/` of its own) for the one that
proves the hook does not reach the gauge by a path relative to itself.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_HOOKS = Path(__file__).resolve().parent
_HOST = _HOOKS.parents[1]
_HOOK = _HOOKS / "context_cap.py"
_CAP_VARIABLE = "KENSAIAPP_CONTEXT_CAP"


def _transcript(path: Path, *, input_tokens=0, cache_read=0, cache_creation=0) -> Path:
    usage = {
        "input_tokens": input_tokens,
        "cache_read_input_tokens": cache_read,
        "cache_creation_input_tokens": cache_creation,
    }
    record = {"type": "assistant", "message": {"id": "m1", "usage": usage}}
    path.write_text(json.dumps(record) + "\n")
    return path


def _run(stdin: str, *, cap: str | None, project_dir: Path = _HOST, hook: Path = _HOOK):
    env = {name: value for name, value in os.environ.items() if name != _CAP_VARIABLE}
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    if cap is not None:
        env[_CAP_VARIABLE] = cap
    return subprocess.run(
        [sys.executable, str(hook)], input=stdin, capture_output=True, text=True, env=env
    )


def _payload(transcript: Path) -> str:
    return json.dumps({"tool_name": "Bash", "transcript_path": str(transcript)})


def _assert_silent(result) -> None:
    assert result.returncode == 0, result.stderr
    assert result.stdout == ""


def test_no_cap_in_the_environment_is_silent(tmp_path):
    transcript = _transcript(tmp_path / "t.jsonl", input_tokens=9_000_000)
    _assert_silent(_run(_payload(transcript), cap=None))


def test_at_or_under_the_cap_is_silent(tmp_path):
    under = _transcript(tmp_path / "under.jsonl", input_tokens=99, cache_read=900)
    exactly = _transcript(tmp_path / "exactly.jsonl", input_tokens=100, cache_read=900)
    _assert_silent(_run(_payload(under), cap="1000"))
    _assert_silent(_run(_payload(exactly), cap="1000"))


def test_over_the_cap_tells_the_developer_to_pause(tmp_path):
    transcript = _transcript(tmp_path / "t.jsonl", input_tokens=1, cache_read=1000)

    result = _run(_payload(transcript), cap="1000")

    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)["hookSpecificOutput"]
    assert output["hookEventName"] == "PostToolUse"
    message = output["additionalContext"]
    assert "1001" in message
    assert "1000" in message
    assert "developer: <key> — implementation paused after task <N>" in message


def test_a_cap_that_is_not_a_positive_integer_is_silent(tmp_path):
    transcript = _transcript(tmp_path / "t.jsonl", input_tokens=9_000_000)
    for cap in ("abc", "0", "-5"):
        _assert_silent(_run(_payload(transcript), cap=cap))


def test_a_cap_python_would_parse_but_that_is_not_plain_digits_is_silent(tmp_path):
    """`int()` reads `1_000`, `+5` and Arabic-Indic digits as numbers; a cap is ASCII digits."""
    transcript = _transcript(tmp_path / "t.jsonl", input_tokens=9_000_000)
    for cap in ("1_000", "+5", "\u0663", "5.0"):
        _assert_silent(_run(_payload(transcript), cap=cap))


def test_a_missing_or_unreadable_transcript_is_silent(tmp_path):
    _assert_silent(_run(_payload(tmp_path / "absent.jsonl"), cap="1"))
    _assert_silent(_run(json.dumps({"tool_name": "Bash"}), cap="1"))
    _assert_silent(_run("this is not json", cap="1"))


def test_a_transcript_with_no_usage_is_silent(tmp_path):
    transcript = tmp_path / "t.jsonl"
    transcript.write_text(json.dumps({"type": "user", "message": {"content": "hi"}}) + "\n")
    _assert_silent(_run(_payload(transcript), cap="1"))


def test_the_gauge_is_found_from_a_satellite(tmp_path):
    satellite = tmp_path / "satellite"
    satellite.mkdir()
    (satellite / ".env").write_text(f"CORE={_HOST / 'core'}\n")
    assert not (satellite / "core").exists()
    transcript = _transcript(tmp_path / "t.jsonl", input_tokens=5_000)

    result = _run(
        _payload(transcript),
        cap="1000",
        project_dir=satellite,
        hook=_HOOK,
    )

    assert result.returncode == 0, result.stderr
    assert "5000" in json.loads(result.stdout)["hookSpecificOutput"]["additionalContext"]


def test_settings_registers_the_hook_on_bash_post_tool_use():
    settings = json.loads((_HOST / ".claude" / "settings.json").read_text())

    entries = settings["hooks"]["PostToolUse"]

    commands = [
        hook["command"]
        for entry in entries
        if entry.get("matcher") == "Bash"
        for hook in entry["hooks"]
    ]
    assert any("context_cap.py" in command for command in commands)
