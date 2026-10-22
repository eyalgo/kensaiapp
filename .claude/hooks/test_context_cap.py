"""Tests for `context_cap.py` — the `PostToolUse` `Bash` hook that tells a developer run to pause.

The hook is a composition root over `run`, so these tests hand it a hand-written gateway, a
recording process collaborator and a temporary home, and read what it prints. The package is
never needed: the gauge is behind the telemetry gateway, and what the hook does without it is
the subject of the retry and notice tests. The satellite test runs the real core resolver
against a temporary `.env`, and the entry-point tests start the real file the way Claude Code
does. `test_telemetry_gateway.py` holds the cases that need the package or its absence in a
started interpreter.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_HOOKS = Path(__file__).resolve().parent
_HOST = _HOOKS.parents[1]
_HOOK = _HOOKS / "context_cap.py"
_CAP_VARIABLE = "KENSAIAPP_CONTEXT_CAP"
_NOTICE = "the cap does not cap"


def _load_hook():
    spec = importlib.util.spec_from_file_location("context_cap_under_test", _HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


context_cap = _load_hook()


class _Unavailable(Exception):
    """Stands in for the gateway's own unavailable exception."""


class FakeTelemetry:
    """The facade the hook reads: answers `current_context` from a table, and records calls."""

    def __init__(self, size=None, error=None):
        self.files = object()
        self.size = size
        self.error = error
        self.calls = []

    def current_context(self, path, files):
        self.calls.append((path, files))
        if self.error:
            raise self.error
        return self.size


class FakeGateway:
    """The gateway module as the hook sees it, built by hand."""

    CONTEXT_UNAVAILABLE = _NOTICE
    TelemetryUnavailable = _Unavailable

    def __init__(self, telemetry=None, unavailable=False):
        self.telemetry = telemetry
        self.unavailable = unavailable
        self.builds = 0

    def build_telemetry(self):
        self.builds += 1
        if self.unavailable:
            raise _Unavailable()
        return self.telemetry


class RecordingChild:
    """The process collaborator: records each call and answers with a fixed result."""

    def __init__(self, status=0, stdout=""):
        self.status = status
        self.stdout = stdout
        self.calls = []

    def __call__(self, argv, stdin, environ):
        self.calls.append((argv, stdin, dict(environ)))
        return self.status, self.stdout


def _payload(transcript="/tmp/t.jsonl") -> bytes:
    return json.dumps({"tool_name": "Bash", "transcript_path": str(transcript)}).encode()


def _run(stdin, *, cap, gateway, run_child=None, prefix="/usr/prefix", home=None, extra_env=None):
    environ = {"PATH": "/bin"}
    if cap is not None:
        environ[_CAP_VARIABLE] = cap
    environ.update(extra_env or {})
    context_cap.run(
        stdin,
        environ,
        load_gateway=lambda: gateway,
        run_child=run_child or RecordingChild(),
        prefix=prefix,
        home=home or Path("/nonexistent-home"),
    )


def _venv(home: Path, *, executable=True) -> Path:
    interpreter = home / ".kensaiapp" / "venv" / "bin" / "python"
    interpreter.parent.mkdir(parents=True)
    interpreter.write_text("#!/bin/sh\n")
    interpreter.chmod(0o755 if executable else 0o644)
    return interpreter


def _assert_silent(capsys) -> None:
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_over_the_cap_tells_the_developer_to_pause(capsys):
    telemetry = FakeTelemetry(size=1001)

    _run(_payload("/tmp/t.jsonl"), cap="1000", gateway=FakeGateway(telemetry))

    output = json.loads(capsys.readouterr().out)["hookSpecificOutput"]
    assert output["hookEventName"] == "PostToolUse"
    message = output["additionalContext"]
    assert "1001" in message
    assert "1000" in message
    assert "developer: <key> — implementation paused after task <N>" in message
    assert telemetry.calls == [(Path("/tmp/t.jsonl"), telemetry.files)]


def test_at_or_under_the_cap_is_silent(capsys):
    for size in (999, 1000):
        _run(_payload(), cap="1000", gateway=FakeGateway(FakeTelemetry(size=size)))
        _assert_silent(capsys)


def test_a_cap_that_is_not_a_positive_integer_is_silent_and_never_wires(capsys):
    refused = FakeGateway(FakeTelemetry(size=9_000_000), unavailable=True)
    for cap in (None, "", "abc", "0", "-5", "1_000", "+5", "٣", "5.0"):
        _run(_payload(), cap=cap, gateway=refused)
        _assert_silent(capsys)
    assert refused.builds == 0


def test_bad_json_is_silent_even_with_the_package_missing(capsys):
    refused = FakeGateway(unavailable=True)
    _run(b"this is not json", cap="1", gateway=refused)
    _assert_silent(capsys)
    assert refused.builds == 0


def test_no_usage_or_unreadable_transcript_is_silent_when_telemetry_is_available(capsys):
    _run(_payload("/tmp/absent.jsonl"), cap="1", gateway=FakeGateway(FakeTelemetry(size=None)))
    _assert_silent(capsys)


def test_failures_other_than_a_missing_package_are_silent_through_main(capsys):
    broken_gauge = FakeGateway(FakeTelemetry(error=RuntimeError("gauge broke")))
    child = RecordingChild()
    for stdin in (_payload(), json.dumps({"tool_name": "Bash"}).encode(), b'["a list"]', b"7"):
        context_cap.main(
            stdin, {_CAP_VARIABLE: "1"}, load_gateway=lambda: broken_gauge, run_child=child
        )
        _assert_silent(capsys)
    assert child.calls == []


def test_a_process_failure_during_the_retry_is_silent(tmp_path, capsys):
    _venv(tmp_path)

    def raising(argv, stdin, environ):
        raise OSError("cannot start")

    context_cap.main(
        _payload(), {_CAP_VARIABLE: "1"}, load_gateway=lambda: FakeGateway(unavailable=True),
        run_child=raising, prefix="/usr/base", home=tmp_path,
    )

    _assert_silent(capsys)


@pytest.mark.parametrize("stdin", [b'"scalar"', b"[1, 2]", b'{"other": 1}', b"null", b"{}"])
def test_unavailable_notice_precedes_transcript_access_for_any_json(stdin, capsys):
    telemetry = FakeTelemetry(size=10**9)
    gateway = FakeGateway(telemetry, unavailable=True)

    _run(stdin, cap="1000", gateway=gateway)

    assert capsys.readouterr().out == _NOTICE + "\n"
    assert telemetry.calls == []


def test_hook_retries_once_with_original_input_and_environment(tmp_path, capsys):
    interpreter = _venv(tmp_path)
    child = RecordingChild(status=0, stdout="child output\n")
    stdin = b'{"transcript_path":  "/x",\r\n\t"tool_name" :"Bash"}\n'
    context_cap.run(
        stdin,
        {_CAP_VARIABLE: "5", "CLAUDE_PROJECT_DIR": "/sat", "PYTHONPATH": "/extra"},
        load_gateway=lambda: FakeGateway(unavailable=True),
        run_child=child,
        prefix="/usr/base",
        home=tmp_path,
    )

    assert len(child.calls) == 1
    argv, replayed, environ = child.calls[0]
    assert argv == [str(interpreter), str(_HOOK)]
    assert replayed == stdin
    assert environ == {_CAP_VARIABLE: "5", "CLAUDE_PROJECT_DIR": "/sat", "PYTHONPATH": "/extra"}
    assert capsys.readouterr().out == "child output\n"


def test_a_retry_that_cannot_supply_the_package_either_says_so_once(tmp_path, capsys):
    _venv(tmp_path)
    # the child is the same hook under the venv: it prints the notice and exits 0
    child = RecordingChild(status=0, stdout=_NOTICE + "\n")

    _run(_payload(), cap="1", gateway=FakeGateway(unavailable=True), run_child=child,
         prefix="/usr/base", home=tmp_path)

    assert capsys.readouterr().out == _NOTICE + "\n"
    assert len(child.calls) == 1


def test_no_venv_or_an_unexecutable_one_prints_the_notice_without_retrying(tmp_path, capsys):
    child = RecordingChild(stdout="must never be forwarded")

    _run(_payload(), cap="1", gateway=FakeGateway(unavailable=True), run_child=child,
         prefix="/usr/base", home=tmp_path)
    assert capsys.readouterr().out == _NOTICE + "\n"

    _venv(tmp_path, executable=False)
    _run(_payload(), cap="1", gateway=FakeGateway(unavailable=True), run_child=child,
         prefix="/usr/base", home=tmp_path)
    assert capsys.readouterr().out == _NOTICE + "\n"
    assert child.calls == []


def test_already_inside_the_venv_does_not_retry(tmp_path, capsys):
    _venv(tmp_path)
    child = RecordingChild()

    _run(_payload(), cap="1", gateway=FakeGateway(unavailable=True), run_child=child,
         prefix=str(tmp_path / ".kensaiapp" / "venv"), home=tmp_path)

    assert capsys.readouterr().out == _NOTICE + "\n"
    assert child.calls == []


def test_a_venv_executable_linked_to_the_current_binary_still_retries(tmp_path, capsys):
    """Identity is the prefix, never the resolved executable: a venv's `python` links to the
    same base binary the caller may be running."""
    base = tmp_path / "base-python"
    base.write_text("#!/bin/sh\n")
    base.chmod(0o755)
    link = tmp_path / ".kensaiapp" / "venv" / "bin" / "python"
    link.parent.mkdir(parents=True)
    link.symlink_to(base)
    child = RecordingChild(stdout="from the venv\n")

    _run(_payload(), cap="1", gateway=FakeGateway(unavailable=True), run_child=child,
         prefix=str(tmp_path / "elsewhere"), home=tmp_path)

    assert len(child.calls) == 1
    assert capsys.readouterr().out == "from the venv\n"


def test_a_failed_retry_forwards_nothing(tmp_path, capsys):
    _venv(tmp_path)
    child = RecordingChild(status=1, stdout="Traceback (most recent call last)\n")

    _run(_payload(), cap="1", gateway=FakeGateway(unavailable=True), run_child=child,
         prefix="/usr/base", home=tmp_path)

    _assert_silent(capsys)
    assert len(child.calls) == 1


def test_the_gateway_is_found_through_the_resolver_from_a_satellite(tmp_path, monkeypatch, capsys):
    """A satellite holds no `core/`; its `.env` names one, and the real resolver reaches the
    gateway there, not by a path beside the hook."""
    core = tmp_path / "elsewhere-core"
    (core / "tools").mkdir(parents=True)
    (core / "tools" / "telemetry_gateway.py").write_text(
        "CONTEXT_UNAVAILABLE = 'from the .env core'\n"
        "class TelemetryUnavailable(Exception):\n    pass\n"
        "def build_telemetry():\n    raise TelemetryUnavailable()\n"
    )
    satellite = tmp_path / "satellite"
    satellite.mkdir()
    (satellite / ".env").write_text(f"CORE={core}\n")
    assert not (satellite / "core").exists()
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(satellite))
    monkeypatch.setattr(sys, "path", list(sys.path))
    for name in ("telemetry_gateway", "resolve_core"):
        monkeypatch.delitem(sys.modules, name, raising=False)

    context_cap.run(
        _payload(), {_CAP_VARIABLE: "1000"}, run_child=RecordingChild(), home=tmp_path
    )

    assert capsys.readouterr().out == "from the .env core\n"


def test_started_as_a_program_the_hook_is_silent_without_a_cap_or_with_bad_input(tmp_path):
    """The real entry point, the way Claude Code starts it: these three states never reach the
    gateway, so they hold whether or not the package is importable."""
    base = {name: v for name, v in os.environ.items() if name != _CAP_VARIABLE}
    base["CLAUDE_PROJECT_DIR"] = str(_HOST)
    for stdin, env in (
        (_payload().decode(), base),
        (_payload().decode(), {**base, _CAP_VARIABLE: "abc"}),
        ("this is not json", {**base, _CAP_VARIABLE: "1"}),
    ):
        result = subprocess.run(
            [sys.executable, str(_HOOK)], input=stdin, capture_output=True, text=True, env=env
        )
        assert (result.returncode, result.stdout, result.stderr) == (0, "", "")


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
