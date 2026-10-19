"""Contract tests for structured provider-process completion observation."""

import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

import watch_process


def _args(tmp_path: Path, *extra):
    log = tmp_path / "run.jsonl"
    return ["--provider", "codex", "--pid", "77", "--log", str(log),
            "--label", "demo", "--notify", "/notify", "--poll-seconds", "0",
            "--timeout-seconds", "1", *extra]


def test_completed_event_reports_and_runs_completion_hook(tmp_path, observed):
    log = tmp_path / "run.jsonl"
    log.write_text('{"type":"turn.completed"}\n')
    sent, hooks = observed["sent"], observed["hooks"]

    result = watch_process.main(_args(tmp_path, "--on-complete", "/hook"))

    assert result == 0
    assert "provider: codex" in sent[0]
    assert hooks == ["completed"]


def test_failed_event_is_not_reported_as_completion(tmp_path, observed):
    log = tmp_path / "run.jsonl"
    log.write_text(json.dumps({"type": "turn.failed", "error": {"message": "bad"}}) + "\n")
    sent, hooks = observed["sent"], observed["hooks"]

    result = watch_process.main(_args(tmp_path, "--on-complete", "/hook"))

    assert result == 1
    assert "run failed" in sent[0]
    assert hooks == ["failed"]


def test_dead_process_without_terminal_event_is_visible(tmp_path, monkeypatch):
    (tmp_path / "run.jsonl").write_text('{"type":"thread.started","thread_id":"t"}\n')
    sent = []
    monkeypatch.setattr(watch_process, "process_alive", lambda pid: False)
    monkeypatch.setattr(watch_process.watch_agent, "notify", lambda path, msg: sent.append(msg))

    result = watch_process.main(_args(tmp_path))

    assert result == 1
    assert "exited without a terminal provider event" in sent[0]


def test_new_completion_marker_can_finish_a_long_running_process(tmp_path, observed, monkeypatch):
    (tmp_path / "run.jsonl").write_text('{"type":"thread.started","thread_id":"t"}\n')
    marker = tmp_path / "done"
    marker.write_text("done")
    sent = observed["sent"]
    monkeypatch.setattr(watch_process.watch_agent, "completion_marker_seen",
                        lambda path, present_before: True)

    result = watch_process.main(_args(tmp_path, "--done-when-exists", str(marker)))

    assert result == 0
    assert "completion marker" in sent[0]


# ── A Claude `--print` run, observed the way a Codex process is ──

SESSION = "0b8f2f6e-5c1a-4a57-9a53-8f9f1f7d2c11"


def _claude_args(tmp_path: Path, *extra):
    log = tmp_path / "run.jsonl"
    return ["--provider", "claude", "--pid", "77", "--log", str(log),
            "--label", "demo", "--notify", "/notify", "--poll-seconds", "0",
            "--timeout-seconds", "1", *extra]


def _claude_log(tmp_path: Path, *events):
    lines = [json.dumps({"type": "system", "subtype": "init", "session_id": SESSION})]
    lines += [json.dumps(event) for event in events]
    (tmp_path / "run.jsonl").write_text("\n".join(lines) + "\n")


def _result(**fields):
    event = {"type": "result", "subtype": "success", "is_error": False, "result": "done",
             "session_id": SESSION}
    event.update(fields)
    return event


@pytest.fixture
def observed(monkeypatch):
    """What the watcher sent, which hook value it handed on, and which pids it stopped."""
    record = {"sent": [], "hooks": [], "stopped": []}
    monkeypatch.setattr(watch_process.watch_agent, "notify",
                        lambda path, msg: record["sent"].append(msg))
    monkeypatch.setattr(watch_process, "_hook",
                        lambda path, value: record["hooks"].append(value))
    monkeypatch.setattr(watch_process, "stop_lingering",
                        lambda pid: record["stopped"].append(pid))
    monkeypatch.setattr(watch_process.watch_agent, "refusal_of", lambda session_id: None)
    return record


def test_claude_success_result_completes_and_names_its_session(tmp_path, observed):
    _claude_log(tmp_path, _result())

    result = watch_process.main(_claude_args(tmp_path, "--on-complete", "/hook"))

    assert result == 0
    assert observed["hooks"] == ["completed"]
    assert "provider: claude" in observed["sent"][0]
    assert f"(run session {SESSION})" in observed["sent"][0]
    assert observed["stopped"] == [77]


def test_claude_error_result_ends_the_run_and_the_disk_decides(tmp_path, observed):
    """A `--bg` session whose turn ended on an error went idle and reached the chain as
    completed; the chain then read the disk. A `--print` run's error result ends it the same
    way, with the error named in the message."""
    _claude_log(tmp_path, _result(subtype="error_during_execution", is_error=True,
                                  result="API Error: overloaded"))

    result = watch_process.main(_claude_args(tmp_path, "--on-complete", "/hook"))

    assert result == 0
    assert observed["hooks"] == ["completed"]
    assert "ended its turn on an error" in observed["sent"][0]
    assert "API Error: overloaded" in observed["sent"][0]


def test_claude_exit_without_a_result_is_failed(tmp_path, observed):
    (tmp_path / "run.jsonl").write_text(
        "Error: bad flag\n" + json.dumps({"type": "kensai.exit", "code": 1}) + "\n"
    )

    result = watch_process.main(_claude_args(tmp_path, "--on-complete", "/hook"))

    assert result == 1
    assert observed["hooks"] == ["failed"]
    assert "Error: bad flag" in observed["sent"][0]


def _hf_args(tmp_path: Path, *extra):
    return ["--provider", "hf", *_claude_args(tmp_path, *extra)[2:]]


def test_hf_success_result_completes_and_names_its_session(tmp_path, observed):
    _claude_log(tmp_path, _result())

    result = watch_process.main(_hf_args(tmp_path, "--on-complete", "/hook"))

    assert result == 0
    assert observed["hooks"] == ["completed"]
    assert "provider: hf" in observed["sent"][0]
    assert f"(run session {SESSION})" in observed["sent"][0]
    assert observed["stopped"] == [77]


def test_hf_error_result_ends_the_run_and_the_disk_decides(tmp_path, observed):
    _claude_log(tmp_path, _result(subtype="error_during_execution", is_error=True,
                                  result="API Error: overloaded"))

    result = watch_process.main(_hf_args(tmp_path, "--on-complete", "/hook"))

    assert result == 0
    assert observed["hooks"] == ["completed"]
    assert "ended its turn on an error" in observed["sent"][0]
    assert "API Error: overloaded" in observed["sent"][0]


def test_hf_exit_without_a_result_is_failed(tmp_path, observed):
    (tmp_path / "run.jsonl").write_text(
        "Error: bad flag\n" + json.dumps({"type": "kensai.exit", "code": 1}) + "\n"
    )

    result = watch_process.main(_hf_args(tmp_path, "--on-complete", "/hook"))

    assert result == 1
    assert observed["hooks"] == ["failed"]
    assert "Error: bad flag" in observed["sent"][0]


def _ollama_args(tmp_path: Path, *extra):
    return ["--provider", "ollama", *_claude_args(tmp_path, *extra)[2:]]


def test_ollama_success_result_completes_and_names_its_session(tmp_path, observed):
    _claude_log(tmp_path, _result())

    result = watch_process.main(_ollama_args(tmp_path, "--on-complete", "/hook"))

    assert result == 0
    assert observed["hooks"] == ["completed"]
    assert "provider: ollama" in observed["sent"][0]
    assert f"(run session {SESSION})" in observed["sent"][0]
    assert observed["stopped"] == [77]


def test_ollama_error_result_ends_the_run_and_the_disk_decides(tmp_path, observed):
    _claude_log(tmp_path, _result(subtype="error_during_execution", is_error=True,
                                  result="API Error: overloaded"))

    result = watch_process.main(_ollama_args(tmp_path, "--on-complete", "/hook"))

    assert result == 0
    assert observed["hooks"] == ["completed"]
    assert "ended its turn on an error" in observed["sent"][0]
    assert "API Error: overloaded" in observed["sent"][0]


def test_ollama_exit_without_a_result_is_failed(tmp_path, observed):
    (tmp_path / "run.jsonl").write_text(
        "Error: bad flag\n" + json.dumps({"type": "kensai.exit", "code": 1}) + "\n"
    )

    result = watch_process.main(_ollama_args(tmp_path, "--on-complete", "/hook"))

    assert result == 1
    assert observed["hooks"] == ["failed"]
    assert "Error: bad flag" in observed["sent"][0]


def test_an_unknown_provider_is_still_refused(tmp_path):
    with pytest.raises(SystemExit) as refusal:
        watch_process.parse_args(["--provider", "other", *_claude_args(tmp_path)[2:]])

    assert refusal.value.code != 0


def test_codex_failed_turn_is_still_failed(tmp_path, observed):
    (tmp_path / "run.jsonl").write_text(
        json.dumps({"type": "turn.failed", "error": {"message": "bad"}}) + "\n"
    )

    result = watch_process.main(_args(tmp_path, "--on-complete", "/hook"))

    assert result == 1
    assert observed["hooks"] == ["failed"]


def test_permission_denials_are_named_in_the_message(tmp_path, observed):
    _claude_log(tmp_path, _result(permission_denials=[
        {"tool_name": "Bash", "tool_use_id": "t1", "tool_input": {"command": "rm -rf /x"}},
        {"tool_name": "Write", "tool_use_id": "t2", "tool_input": {}},
    ]))

    watch_process.main(_claude_args(tmp_path))

    assert "denied 2 actions nobody could approve: Bash, Write" in observed["sent"][0]


def test_a_hook_refusal_is_not_reported_as_a_denial(tmp_path, observed):
    refused = {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t1", "is_error": True,
         "content": "PreToolUse:Skill hook error: This `Skill` call is refused."}]}}
    _claude_log(tmp_path, refused, _result(permission_denials=[
        {"tool_name": "Skill", "tool_use_id": "t1", "tool_input": {}},
    ]))

    watch_process.main(_claude_args(tmp_path))

    assert "nobody could approve" not in observed["sent"][0]
    assert "a hook refused 1 call and told the run what to do instead" in observed["sent"][0]


def test_a_refusal_in_the_transcript_is_named(tmp_path, observed, monkeypatch):
    _claude_log(tmp_path, _result())
    asked = []
    monkeypatch.setattr(watch_process.watch_agent, "refusal_of",
                        lambda session_id: asked.append(session_id) or {"category": "cyber"})

    watch_process.main(_claude_args(tmp_path))

    assert asked == [SESSION]
    assert "model refusal with no fallback — category: cyber" in observed["sent"][0]


def test_multi_turn_run_that_ends_without_its_marker_is_stopped(tmp_path, observed):
    _claude_log(tmp_path, _result())

    result = watch_process.main(_claude_args(
        tmp_path, "--on-complete", "/hook", "--multi-turn",
        "--done-when-exists", str(tmp_path / "never")))

    assert result == 0
    assert observed["hooks"] == ["stopped"]
    assert "without its completion marker" in observed["sent"][0]


def test_multi_turn_run_that_writes_its_marker_completes(tmp_path, observed, monkeypatch):
    _claude_log(tmp_path, _result())
    monkeypatch.setattr(watch_process.watch_agent, "completion_marker_seen",
                        lambda path, present_before: True)

    watch_process.main(_claude_args(
        tmp_path, "--on-complete", "/hook", "--multi-turn",
        "--done-when-exists", str(tmp_path / "done")))

    assert observed["hooks"] == ["completed"]


def test_multi_turn_needs_a_marker(tmp_path):
    with pytest.raises(SystemExit):
        watch_process.main(_claude_args(tmp_path, "--multi-turn"))


def test_produced_nothing_is_handed_on(tmp_path, observed, monkeypatch):
    _claude_log(tmp_path, _result())
    monkeypatch.setattr(watch_process.reporters, "produced_nothing", lambda ctx: True)

    watch_process.main(_claude_args(tmp_path, "--on-complete", "/hook"))

    assert observed["hooks"] == ["produced_nothing"]


def test_timeout_notifies_and_stops_nothing(tmp_path, observed, monkeypatch):
    _claude_log(tmp_path)
    monkeypatch.setattr(watch_process, "process_alive", lambda pid: True)

    result = watch_process.main(_claude_args(
        tmp_path, "--on-complete", "/hook", "--timeout-seconds", "0"))

    assert result == 1
    assert observed["hooks"] == ["timeout"]
    assert observed["stopped"] == []


def test_stop_lingering_interrupts_a_process_group_that_outlives_its_ending(tmp_path):
    # A shell `trap INT` does not fire when SIGINT was ignored on entry, so an unattended
    # runner's ignored SIGINT let this witness survive until SIGTERM (exit -15). The witness
    # installs its own handler, which replaces an inherited ignore.
    previous = signal.signal(signal.SIGINT, signal.SIG_IGN)
    process = subprocess.Popen(
        [sys.executable, "-c",
         "import signal, sys, time\n"
         "signal.signal(signal.SIGINT, lambda *_: sys.exit(0))\n"
         "while True:\n"
         "    time.sleep(60)\n"],
        start_new_session=True,
    )
    try:
        watch_process.stop_lingering(process.pid, grace_seconds=0.1, interrupt_seconds=5)
        assert process.wait(timeout=5) == 0
    finally:
        signal.signal(signal.SIGINT, previous)
        if process.poll() is None:
            process.kill()


def test_stop_lingering_leaves_a_process_that_ends_on_its_own(tmp_path):
    process = subprocess.Popen(["/bin/sh", "-c", "sleep 0.1"], start_new_session=True)

    watch_process.stop_lingering(process.pid, grace_seconds=2, interrupt_seconds=0.5)

    assert process.wait(timeout=5) == 0


def test_the_watch_says_it_started_before_anything_else(tmp_path, observed, capsys):
    _claude_log(tmp_path, _result())

    watch_process.main(_claude_args(tmp_path))

    first = capsys.readouterr().err.splitlines()[0]
    assert first.startswith("watch_process: watching demo — claude process 77, log ")


# ── The final-message receipt, published before the hook ──

import completion_shim  # noqa: E402  (grouped with the tests that use it)

RECEIPT_MESSAGE = 'readme-status made commit `abc123` in `/a b/c`.\nSecond "line" — ünï'


def _hook_that_reads_the_receipt(monkeypatch, destination: Path):
    """A stub callback that records what the receipt held at the moment it was called."""
    seen = []

    def hook(path, value):
        seen.append((value, completion_shim.read_result(completion_shim.DiskReceiptFiles(),
                                                        str(destination))))

    monkeypatch.setattr(watch_process, "_hook", hook)
    return seen


@pytest.fixture
def receipt(tmp_path, monkeypatch, observed):
    destination = tmp_path / "out" / "receipt.json"
    destination.parent.mkdir()
    monkeypatch.setenv(completion_shim.RESULT_FILE_VARIABLE, str(destination))
    return destination


def test_a_claude_result_log_is_published_verbatim_before_the_hook(
        tmp_path, receipt, monkeypatch):
    seen = _hook_that_reads_the_receipt(monkeypatch, receipt)
    _claude_log(tmp_path, _result(result=RECEIPT_MESSAGE))

    watch_process.main(_claude_args(tmp_path, "--on-complete", "/hook"))

    assert seen == [("completed", RECEIPT_MESSAGE)]


def test_a_codex_result_log_is_published_verbatim_before_the_hook(
        tmp_path, receipt, monkeypatch):
    seen = _hook_that_reads_the_receipt(monkeypatch, receipt)
    (tmp_path / "run.jsonl").write_text("\n".join(json.dumps(event) for event in (
        {"type": "thread.started", "thread_id": "t"},
        {"type": "item.completed", "item": {"type": "agent_message", "text": "earlier"}},
        {"type": "item.completed", "item": {"type": "agent_message", "text": RECEIPT_MESSAGE}},
        {"type": "turn.completed"})) + "\n")

    watch_process.main(_args(tmp_path, "--on-complete", "/hook"))

    assert seen == [("completed", RECEIPT_MESSAGE)]


def test_a_gemini_result_log_is_published_verbatim_before_the_hook(
        tmp_path, receipt, monkeypatch):
    seen = _hook_that_reads_the_receipt(monkeypatch, receipt)
    (tmp_path / "run.jsonl").write_text("\n".join(json.dumps(event) for event in (
        {"event": "init", "conversation_id": "g1"},
        {"event": "result", "result": {"status": "SUCCESS", "response": RECEIPT_MESSAGE,
                                       "conversation_id": "g1"}})) + "\n")
    argv = _args(tmp_path, "--on-complete", "/hook")
    argv[argv.index("codex")] = "gemini"

    watch_process.main(argv)

    assert seen == [("completed", RECEIPT_MESSAGE)]


@pytest.mark.parametrize("provider", ["hf", "ollama"])
def test_a_claude_shaped_hf_and_ollama_result_log_is_published_verbatim_before_the_hook(
        tmp_path, receipt, monkeypatch, provider):
    seen = _hook_that_reads_the_receipt(monkeypatch, receipt)
    _claude_log(tmp_path, _result(result=RECEIPT_MESSAGE))
    argv = _claude_args(tmp_path, "--on-complete", "/hook")
    argv[argv.index("claude")] = provider

    watch_process.main(argv)

    assert seen == [("completed", RECEIPT_MESSAGE)]


def test_the_hook_still_receives_its_original_outcome_argument(tmp_path, receipt, observed):
    _claude_log(tmp_path, _result(result=RECEIPT_MESSAGE))

    watch_process.main(_claude_args(tmp_path, "--on-complete", "/hook"))

    assert observed["hooks"] == ["completed"]


def test_without_a_destination_no_receipt_is_written(tmp_path, observed, monkeypatch):
    monkeypatch.delenv(completion_shim.RESULT_FILE_VARIABLE, raising=False)
    _claude_log(tmp_path, _result(result=RECEIPT_MESSAGE))

    watch_process.main(_claude_args(tmp_path, "--on-complete", "/hook"))

    assert [path.name for path in tmp_path.iterdir()] == ["run.jsonl"]
    assert observed["hooks"] == ["completed"]


def test_a_receipt_write_failure_still_calls_the_hook(tmp_path, receipt, observed):
    class Failing(completion_shim.DiskReceiptFiles):
        def write_text(self, path, text):
            raise OSError("disk full")

    _claude_log(tmp_path, _result(result=RECEIPT_MESSAGE))

    result = watch_process.main(_claude_args(tmp_path, "--on-complete", "/hook"),
                                receipt_files=Failing())

    assert result == 0
    assert observed["hooks"] == ["completed"]
    assert completion_shim.read_result(completion_shim.DiskReceiptFiles(), str(receipt)) is None


def test_an_absent_final_message_publishes_null(tmp_path, receipt, monkeypatch):
    seen = _hook_that_reads_the_receipt(monkeypatch, receipt)
    (tmp_path / "run.jsonl").write_text('{"type":"turn.completed"}\n')

    watch_process.main(_args(tmp_path, "--on-complete", "/hook"))

    assert json.loads(receipt.read_text()) == {"last_message": None}
    assert seen == [("completed", None)]


def test_a_failed_outcome_is_unchanged_with_a_destination(
        tmp_path, receipt, observed, monkeypatch):
    (tmp_path / "run.jsonl").write_text('{"type":"turn.failed","error":{"message":"bad"}}\n')
    assert watch_process.main(_args(tmp_path, "--on-complete", "/hook")) == 1
    assert observed["hooks"] == ["failed"]


@pytest.mark.parametrize("ending, write_fails", [
    ("timeout", False), ("stopped", False), ("stopped", True),
])
def test_real_watcher_preserves_timeout_and_cut_off_callbacks(
        tmp_path, monkeypatch, ending, write_fails):
    """Task 2: the real callback observes the receipt, without replacing watcher functions."""
    destination = tmp_path / "receipt.json"
    if write_fails:
        destination = tmp_path / "missing-parent" / "receipt.json"
    monkeypatch.setenv(completion_shim.RESULT_FILE_VARIABLE, str(destination))
    callback_record = tmp_path / "callback.json"
    hook = tmp_path / "hook"
    hook.write_text(
        f"#!{sys.executable}\n"
        "import json, pathlib, sys\n"
        f"receipt = pathlib.Path({str(destination)!r})\n"
        "message = json.loads(receipt.read_text()) if receipt.is_file() else None\n"
        f"pathlib.Path({str(callback_record)!r}).write_text(\n"
        "    json.dumps({'arguments': sys.argv[1:], 'receipt': message}))\n"
    )
    hook.chmod(0o755)
    log = tmp_path / "run.jsonl"
    log.write_text("" if ending == "timeout" else json.dumps({
        "type": "result", "subtype": "success", "is_error": False,
        "result": RECEIPT_MESSAGE,
    }) + "\n")
    process_body = "import time; time.sleep(30)" if ending == "timeout" else "pass"
    held = subprocess.Popen([sys.executable, "-c", process_body],
                            start_new_session=True)
    try:
        if ending == "stopped":
            held.wait(timeout=5)
        result = subprocess.run([
            sys.executable, str(Path(watch_process.__file__).resolve()),
            "--provider", "claude", "--pid", str(held.pid), "--log", str(log),
            "--label", "receipt-test", "--notify", "/usr/bin/true",
            "--on-complete", str(hook), "--timeout-seconds", "0",
            "--multi-turn", "--done-when-exists", str(tmp_path / "never"),
        ], capture_output=True, text=True, timeout=15, env=dict(os.environ))

        assert result.returncode == (1 if ending == "timeout" else 0), result.stderr
        expected_receipt = (
            {"last_message": RECEIPT_MESSAGE}
            if ending == "stopped" and not write_fails else None
        )
        assert json.loads(callback_record.read_text()) == {
            "arguments": [ending], "receipt": expected_receipt,
        }
        if ending == "timeout":
            assert held.poll() is None
    finally:
        if held.poll() is None:
            held.terminate()
        held.wait(timeout=5)
