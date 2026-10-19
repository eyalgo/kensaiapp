"""Contract tests for detached persistent provider turns."""

import json
import time
from pathlib import Path

import pytest

import agent_run
import agent_session
import agent_turn
import pin

_SIX_DELIVERY_FLAGS = (
    "--setting-sources", "--plugin-dir", "--settings", "--agents", "--add-dir",
)


def _flag_count(command, flag):
    """How many times the flag appears, written as two tokens or as one `--flag=value`."""
    return sum(token == flag or token.startswith(f"{flag}=") for token in command)


@pytest.fixture
def pins_home(tmp_path):
    home = tmp_path / "pins"
    home.mkdir()
    return home


def test_a_codex_launch_without_a_session_id_reads_the_thread_started_log(tmp_path, monkeypatch):
    def start_detached(self, argv, log_path):
        log_path.write_text(
            '{"type":"thread.started","thread_id":"sess-9"}\n',
            encoding="utf-8",
        )
        return 42

    monkeypatch.setattr(
        agent_turn.agent_run.Subprocesses, "start_detached", start_detached
    )
    turn = agent_turn.launch(
        "codex", ("codex", "exec", "work"), tmp_path / "run.log", None, 1.0
    )

    assert turn.provider == "codex"
    assert turn.session_id == "sess-9"
    assert turn.pid == 42


def test_claude_start_is_a_machine_readable_persistent_turn():
    command = agent_turn.claude_command(
        prompt="work", session_id="uuid-1", resume=False, agent="cpo",
        name="sdd-demo-cpo", model=None, tier="fable", add_dirs=("/skills",),
        settings="telemetry.json",
    )

    assert command == (
        "claude", "--print", "--output-format", "stream-json", "--verbose",
        "--session-id", "uuid-1", "--name", "sdd-demo-cpo", "--agent", "cpo",
        "--model", "fable", "--permission-mode", "auto", "--permission-prompts", "none",
        "--add-dir=/skills", "--settings", "telemetry.json", "work",
    )


def test_claude_resume_uses_the_same_conversation_without_reselecting_agent():
    command = agent_turn.claude_command(
        prompt="next", session_id="uuid-1", resume=True, agent="cpo",
        name="ignored", model=None, tier="fable", add_dirs=("/ignored",), settings="ignored",
    )

    assert command[:7] == (
        "claude", "--print", "--output-format", "stream-json", "--verbose", "--resume", "uuid-1"
    )
    assert "--agent" not in command
    assert not any(token.startswith("--add-dir") for token in command)
    assert command[-1] == "next"


def test_claude_turn_start_carries_the_pin_delivery(tmp_path, pins_home):
    """Task 8 — `claude_command` delegates `pin` and `instance_root` to `ClaudeAdapter`, so a
    turn start carries every one of the six delivery flags exactly once, same as any other
    shape (Task 7's own `test_with_a_pin_every_shape_carries_the_delivery`)."""
    host = tmp_path / "host"
    host.mkdir()
    made = pin.make(host, pins_home)

    command = agent_turn.claude_command(
        prompt="work", session_id="uuid-1", resume=False, agent="cpo",
        name="sdd-demo-cpo", model=None, tier="fable", add_dirs=(), settings=None,
        pin=made, instance_root=host,
    )

    for flag in _SIX_DELIVERY_FLAGS:
        assert _flag_count(command, flag) == 1, (flag, command)
    assert "--session-id" in command
    assert "--agent" in command


def test_claude_turn_resume_carries_the_pin_delivery_but_not_the_agent(tmp_path, pins_home):
    """Task 8 — `--resume` present, `--agent` absent (today's resume behaviour, unchanged), and
    all six delivery flags present anyway — the pin travels with a resumed turn exactly as it
    does with a started one, because a resume is a new `claude` process that reloads its
    settings (CP-109)."""
    host = tmp_path / "host"
    host.mkdir()
    made = pin.make(host, pins_home)

    command = agent_turn.claude_command(
        prompt="next", session_id="uuid-1", resume=True, agent="cpo",
        name="ignored", model=None, tier="fable", add_dirs=(), settings=None,
        pin=made, instance_root=host,
    )

    assert "--resume" in command
    assert "--agent" not in command
    for flag in _SIX_DELIVERY_FLAGS:
        assert _flag_count(command, flag) == 1, (flag, command)


def test_codex_start_and_resume_preserve_model_assignment():
    start = agent_turn.codex_command(prompt="work", session_id=None, model=None,
                                     tier="fable", add_dirs=("/product",))
    resume = agent_turn.codex_command(prompt="next", session_id="thread-1", model=None,
                                      tier="fable", add_dirs=())

    assert start[:3] == ("codex", "exec", "--approve-for-me")
    assert start[-3:] == ("--add-dir", "/product", "work")
    assert resume[:5] == (
        "codex", "exec", "--approve-for-me", "resume", "--json"
    )
    assert resume[-2:] == ("thread-1", "next")


def test_codex_turn_prepends_shared_task_context(tmp_path):
    doctrine = tmp_path / "doctrine"
    doctrine.mkdir()
    (doctrine / "task_map.md").write_text(
        "| When you're about to… | Consult | Layer | Fires |\n"
        "|---|---|---|---|\n"
        "| Commit anything | `commit_format.md` | governance |  |\n",
        encoding="utf-8",
    )

    command = agent_turn.codex_command(
        prompt="work", session_id=None, model=None, tier="fable",
        add_dirs=(), core_root=tmp_path,
    )

    assert "KENSAIAPP_TASK_MAP" in command[-1]
    assert command[-1].endswith("work")


def test_codex_turn_uses_the_current_assignment_for_flags_and_identity(tmp_path):
    fresh = agent_turn.codex_command(
        prompt="work", session_id=None, model=None, tier="sonnet",
        add_dirs=(), core_root=tmp_path,
    )
    resumed = agent_turn.codex_command(
        prompt="next", session_id="thread-1", model=None, tier="opus",
        add_dirs=(), core_root=tmp_path,
    )

    assert fresh[fresh.index("--model") + 1] == "gpt-5.6-terra"
    assert 'model_reasoning_effort="medium"' in fresh
    assert 'gpt-5.6-terra <noreply@openai.com>' in fresh[-1]
    assert fresh[-1].count('`--reasoning-effort "medium"`') == 1

    assert resumed[resumed.index("--model") + 1] == "gpt-5.6-sol"
    assert 'model_reasoning_effort="high"' in resumed
    assert 'gpt-5.6-sol <noreply@openai.com>' in resumed[-1]
    assert resumed[-1].count('`--reasoning-effort "high"`') == 1
    assert "gpt-5.6-terra" not in resumed[-1]


def test_codex_turn_start_and_resume_share_provider_and_prompt_effort(tmp_path):
    start = agent_turn.codex_command(
        prompt="work", session_id=None, model=None, tier="opus",
        add_dirs=(), core_root=tmp_path,
    )
    resume = agent_turn.codex_command(
        prompt="next", session_id="thread-1", model=None, tier="opus",
        add_dirs=(), core_root=tmp_path,
    )

    for command in (start, resume):
        assert command.count('model_reasoning_effort="high"') == 1
        assert command[-1].count('`--reasoning-effort "high"`') == 1


def test_codex_turn_threads_an_explicit_model_verbatim(tmp_path):
    command = agent_turn.codex_command(
        prompt="work", session_id=None, model="gpt-explicit-fixture", tier=None,
        add_dirs=(), core_root=tmp_path,
    )

    assert command[command.index("--model") + 1] == "gpt-explicit-fixture"
    assert 'gpt-explicit-fixture <noreply@openai.com>' in command[-1]
    assert "--reasoning-effort" not in command[-1]


def test_codex_turn_without_an_assignment_gives_the_generic_codex_identity(tmp_path):
    command = agent_turn.codex_command(
        prompt="work", session_id=None, model=None, tier=None,
        add_dirs=(), core_root=tmp_path,
    )

    assert "--model" not in command
    assert '`--co-authored-by "Codex <noreply@openai.com>"`' in command[-1]
    assert "--reasoning-effort" not in command[-1]


def test_codex_turn_attribution_changes_only_the_prompt(tmp_path):
    for session_id, add_dirs in ((None, ("/product",)), ("thread-1", ())):
        without_context = agent_turn.codex_command(
            prompt="work", session_id=session_id, model=None, tier="sonnet",
            add_dirs=add_dirs,
        )
        with_context = agent_turn.codex_command(
            prompt="work", session_id=session_id, model=None, tier="sonnet",
            add_dirs=add_dirs, core_root=tmp_path,
        )

        assert without_context[:-1] == with_context[:-1]


def test_claude_turn_contains_no_codex_runtime_identity():
    command = agent_turn.claude_command(
        prompt="work", session_id="uuid-1", resume=False, agent=None,
        name=None, model=None, tier="fable", add_dirs=(), settings=None,
    )

    assert "KENSAIAPP_TASK_MAP" not in " ".join(command)
    assert "noreply@openai.com" not in " ".join(command)


def test_claude_turn_remains_free_of_codex_effort_attribution():
    command = agent_turn.claude_command(
        prompt="work", session_id="uuid-1", resume=False, agent="cpo",
        name="sdd-demo-cpo", model=None, tier="fable", add_dirs=("/skills",),
        settings="telemetry.json",
    )

    rendered = " ".join(command)
    assert "--reasoning-effort" not in rendered
    assert "Execution surface: Codex" not in rendered
    assert "`--surface Codex`" not in rendered
    assert "noreply@openai.com" not in rendered


def test_claude_log_reduces_to_final_reply():
    text = "\n".join((
        json.dumps({"type": "system", "subtype": "init", "session_id": "session-1"}),
        json.dumps({"type": "assistant", "session_id": "session-1"}),
        json.dumps({"type": "result", "subtype": "success", "session_id": "session-1",
                    "is_error": False, "result": "CHANGED: nothing\nMOVE: no_followup"}),
    ))

    state = agent_turn.inspect_claude_log(text)

    assert state.state == "completed"
    assert state.session_id == "session-1"
    assert state.last_message == "CHANGED: nothing\nMOVE: no_followup"


def test_inspect_reads_codex_final_reply_from_jsonl(tmp_path: Path):
    log = tmp_path / "turn.jsonl"
    log.write_text(
        '{"type":"thread.started","thread_id":"thread-1"}\n'
        '{"type":"item.completed","item":{"type":"agent_message","text":"done"}}\n'
        '{"type":"turn.completed"}\n'
    )

    state = agent_turn.inspect("codex", log)

    assert state.state == "completed"
    assert state.session_id == "thread-1"
    assert state.last_message == "done"


def test_claude_log_reports_failed_when_the_exit_record_precedes_any_terminal_event():
    """A process that dies before emitting a single stream-json line — the real product-sdd
    run-30 case — leaves only its plain-text error plus the exit wrapper's `kensai.exit` record.
    That must not read as `starting`/`running` forever."""
    text = "\n".join((
        "Error: Input must be provided either through stdin or as a prompt argument "
        "when using --print",
        json.dumps({"type": "kensai.exit", "code": 1}),
    ))

    state = agent_turn.inspect_claude_log(text)

    assert state.state == "failed"
    assert "Input must be provided" in state.detail
    assert "exit code 1" in state.detail


def test_claude_log_exit_record_after_a_result_changes_nothing():
    text = "\n".join((
        json.dumps({"type": "result", "subtype": "success", "session_id": "session-1",
                    "is_error": False, "result": "done"}),
        json.dumps({"type": "kensai.exit", "code": 0}),
    ))

    state = agent_turn.inspect_claude_log(text)

    assert state.state == "completed"
    assert state.last_message == "done"


def test_claude_log_without_an_exit_record_is_unchanged():
    text = json.dumps({"type": "assistant", "session_id": "session-1"})

    state = agent_turn.inspect_claude_log(text)

    assert state.state == "running"
    assert state.detail is None


def test_launch_reports_failed_when_the_process_dies_without_emitting_json(tmp_path: Path):
    """Real-process proof of the exit wrapper: a tiny command that prints a non-JSON line and
    exits 1 still leaves a terminal, machine-readable state — not an eternal `starting`."""
    log = tmp_path / "turn.jsonl"

    agent_turn.launch(
        "claude", ("/bin/sh", "-c", "echo Error: boom; exit 1"), log, "session-1", 5.0,
    )

    deadline = time.monotonic() + 5.0
    state = agent_turn.inspect_claude_log(agent_session.SessionRunner._read_log(log))
    while state.state == "starting" and time.monotonic() < deadline:
        time.sleep(0.02)
        state = agent_turn.inspect_claude_log(agent_session.SessionRunner._read_log(log))

    assert state.state == "failed"
    assert "boom" in state.detail


def test_claude_log_names_its_permission_denials_and_that_the_turn_ended():
    text = "\n".join((
        json.dumps({"type": "system", "subtype": "init", "session_id": "s-9"}),
        json.dumps({"type": "result", "subtype": "error_during_execution", "is_error": True,
                    "result": "API Error", "session_id": "s-9",
                    "permission_denials": [{"tool_name": "Bash", "tool_use_id": "t",
                                            "tool_input": {"command": "rm -rf /x"}}]}),
    ))

    state = agent_turn.inspect_claude_log(text)

    assert (state.state, state.terminal, state.denials) == ("failed", True, ("Bash",))
    assert agent_turn.inspect_claude_log(
        json.dumps({"type": "kensai.exit", "code": 1})
    ).terminal is False


def test_claude_log_keeps_a_hook_refusal_out_of_its_denials():
    refusal = "PreToolUse:Skill hook error: This `Skill` call is refused."
    text = "\n".join((
        json.dumps({"type": "system", "subtype": "init", "session_id": "s-9"}),
        json.dumps({"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "hook-1", "is_error": True,
             "content": refusal},
            {"type": "tool_result", "tool_use_id": "hook-2", "is_error": True,
             "content": [{"type": "text", "text": refusal}]},
            {"type": "tool_result", "tool_use_id": "person", "is_error": True,
             "content": "Permission for this command was denied"},
        ]}}),
        json.dumps({"type": "result", "subtype": "success", "is_error": False,
                    "result": "done", "session_id": "s-9", "permission_denials": [
                        {"tool_name": "Skill", "tool_use_id": "hook-1", "tool_input": {}},
                        {"tool_name": "Bash", "tool_use_id": "hook-2", "tool_input": {}},
                        {"tool_name": "Bash", "tool_use_id": "person", "tool_input": {}},
                    ]}),
    ))

    state = agent_turn.inspect_claude_log(text)

    assert state.denials == ("Bash",)
    assert state.hook_refusals == ("Skill", "Bash")


_HF_LOGS = {
    "success": "\n".join((
        json.dumps({"type": "system", "subtype": "init", "session_id": "hf-1"}),
        json.dumps({"type": "result", "subtype": "success", "session_id": "hf-1",
                    "is_error": False, "result": "done"}),
    )),
    "error result": "\n".join((
        json.dumps({"type": "system", "subtype": "init", "session_id": "hf-1"}),
        json.dumps({"type": "result", "subtype": "error_during_execution", "is_error": True,
                    "result": "API Error", "session_id": "hf-1"}),
    )),
    "no result": json.dumps({"type": "system", "subtype": "init", "session_id": "hf-1"}),
}


@pytest.mark.parametrize("kind", sorted(_HF_LOGS))
def test_inspect_reads_an_hf_log_as_a_claude_log(tmp_path: Path, kind):
    log = tmp_path / "turn.jsonl"
    log.write_text(_HF_LOGS[kind])

    assert agent_turn.inspect("hf", log, "hf-1") == agent_turn.inspect("claude", log, "hf-1")


@pytest.mark.parametrize("kind", sorted(_HF_LOGS))
def test_inspect_reads_an_ollama_log_as_a_claude_log(tmp_path: Path, kind):
    """An ollama run is the Claude run aimed at the local server, so its log is a Claude log;
    the same three logs the hf case reads."""
    log = tmp_path / "turn.jsonl"
    log.write_text(_HF_LOGS[kind])

    assert agent_turn.inspect("ollama", log, "hf-1") == agent_turn.inspect("claude", log, "hf-1")


def test_inspect_still_refuses_an_unknown_provider(tmp_path: Path):
    log = tmp_path / "turn.jsonl"
    log.write_text(_HF_LOGS["success"])

    with pytest.raises(agent_run.UnknownProvider):
        agent_turn.inspect("other", log)


# --- an effort on every builder (Task 3) -----------------------------------------------------


def _turn(provider, *, resume, effort, tier=None, model="m-1", core_root=None):
    """One turn from the named provider's builder, the way a seat dispatch builds it."""
    session_id = "sess-1" if resume else None
    if provider == "claude":
        return agent_turn.claude_command(
            prompt="go", session_id=session_id or "uuid-1", resume=resume, agent=None,
            name=None, model=model, tier=tier, add_dirs=(), settings=None, effort=effort,
        )
    if provider == "codex":
        return agent_turn.codex_command(
            prompt="go", session_id=session_id, model=model, tier=tier, add_dirs=(),
            core_root=core_root, effort=effort,
        )
    return agent_turn.gemini_command(
        prompt="go", session_id=session_id, resume=resume, agent=None, model=model,
        tier=tier, add_dirs=(), settings=None, core_root=core_root, effort=effort,
    )


def _effort_tokens(provider, command):
    """The tokens a command spends on effort, in the form the provider takes it."""
    if provider == "codex":
        return [token for token in command if token.startswith("model_reasoning_effort=")]
    return [command[i + 1] for i, token in enumerate(command) if token == "--effort"]


@pytest.mark.parametrize("resume", [False, True], ids=["start", "resume"])
@pytest.mark.parametrize("provider", ["claude", "codex", "gemini"])
def test_each_builder_puts_an_effort_on_its_command_once(provider, resume):
    command = _turn(provider, resume=resume, effort=agent_run.Effort.LOW)

    expected = ['model_reasoning_effort="low"'] if provider == "codex" else ["low"]
    assert _effort_tokens(provider, command) == expected
    assert command.count("m-1") == 1


def test_a_codex_effort_wins_over_the_tiers_level(tmp_path):
    command = _turn("codex", resume=False, effort=agent_run.Effort.LOW, tier="fable",
                    model=None, core_root=tmp_path)

    assert _effort_tokens("codex", command) == ['model_reasoning_effort="low"']
    assert 'model_reasoning_effort="xhigh"' not in command
    assert command[-1].count('`--reasoning-effort "low"`') == 1
    assert "xhigh" not in command[-1]


@pytest.mark.parametrize("provider", ["claude", "codex", "gemini"])
def test_no_effort_leaves_every_builders_command_as_today(provider):
    with_effort_left_out = _turn(provider, resume=False, effort=None)

    assert _effort_tokens(provider, with_effort_left_out) == []
