"""Contract tests for the provider-neutral agent-run boundary."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import time
import uuid
from dataclasses import replace
from pathlib import Path

import pytest

import agent_run
import agent_turn
import model_assignment
import pin
from agent_run import AgentRunner, ClaudeAdapter, CodexAdapter, GeminiAdapter, RunRequest

_SCRIPT = Path(__file__).resolve().parent / "agent_run.py"


@pytest.fixture
def pins_home(tmp_path):
    home = tmp_path / "pins"
    home.mkdir()
    return home


def _flag_value(command, flag):
    """The flag's value, written either as two tokens or as one `--flag=value`."""
    if flag in command:
        return command[command.index(flag) + 1]
    prefix = f"{flag}="
    return next(token[len(prefix):] for token in command if token.startswith(prefix))


def _flag_count(command, flag):
    """How many times the flag appears, in either writing."""
    return sum(token == flag or token.startswith(f"{flag}=") for token in command)


def _build_pin_host(root: Path) -> Path:
    """Task 7 — a throwaway, non-git host carrying one hook-bearing `settings.json`, one flat
    skill, one grouped skill, one workflow, and two agents (one of which `test_agents_inline_...`
    and `test_the_merged_settings_layer_in_order` override from an instance)."""
    root.mkdir()
    (root / "core").mkdir()
    (root / "core" / "tool.py").write_text("print('host tool')\n")

    (root / ".claude" / "settings.json").parent.mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "settings.json").write_text(
        json.dumps(
            {
                "permissions": {"allow": ["Bash(host:*)"]},
                "hooks": {
                    "SessionStart": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": (
                                        'python3 "${CLAUDE_PROJECT_DIR}/.claude/hooks/'
                                        'resolve_core.py"'
                                    ),
                                }
                            ]
                        }
                    ]
                },
            }
        )
    )

    (root / ".claude" / "agents").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "agents" / "pinned-agent.md").write_text(
        "---\n"
        "name: pinned-agent\n"
        "description: A host agent.\n"
        "tools: Read, Grep\n"
        "model: sonnet\n"
        "---\n\n"
        "You are the pinned agent."
    )
    (root / ".claude" / "agents" / "shared-agent.md").write_text(
        "---\n"
        "name: shared-agent\n"
        "description: The host's own shared-agent.\n"
        "---\n\n"
        "Host body."
    )

    (root / ".claude" / "skills" / "pinned-skill").mkdir(parents=True)
    (root / ".claude" / "skills" / "pinned-skill" / "SKILL.md").write_text("pinned skill\n")

    (root / "skills" / "grp" / ".claude" / "skills" / "grouped-skill").mkdir(parents=True)
    (root / "skills" / "grp" / ".claude" / "skills" / "grouped-skill" / "SKILL.md").write_text(
        "grouped skill\n"
    )

    (root / ".claude" / "workflows").mkdir(parents=True, exist_ok=True)
    (root / ".claude" / "workflows" / "pinned-workflow.js").write_text("// pinned workflow\n")

    return root


class FakeProcesses:
    def __init__(self, returncode=0, pid=4321):
        self.returncode = returncode
        self.pid = pid
        self.calls = []
        self.logged_calls = []
        self.detached_calls = []

    def run(self, argv):
        self.calls.append(tuple(argv))
        return self.returncode

    def run_to_log(self, argv, log_path):
        self.logged_calls.append((tuple(argv), log_path))
        return self.returncode

    def start_detached(self, argv, log_path):
        self.detached_calls.append((tuple(argv), log_path))
        return self.pid


def test_claude_adapter_owns_the_complete_provider_command():
    request = RunRequest(
        prompt="do the work",
        agent="developer",
        model="opus",
        add_dirs=("/first path", "/second"),
        settings='{"env": {"ARM": "control"}}',
    )

    command = ClaudeAdapter().command(request)

    assert command == (
        "claude",
        "--bg",
        "do the work",
        "--agent",
        "developer",
        "--model",
        "opus",
        "--permission-mode",
        "auto",
        "--add-dir=/first path",
        "--add-dir=/second",
        "--settings",
        '{"env": {"ARM": "control"}}',
    )


def test_claude_adapter_omits_absent_optional_values():
    command = ClaudeAdapter().command(RunRequest(prompt="do the minimum"))

    assert command == (
        "claude",
        "--bg",
        "do the minimum",
        "--permission-mode",
        "auto",
    )


def test_claude_adapter_resolves_a_kensaiapp_model_tier():
    command = ClaudeAdapter().command(
        RunRequest(prompt="do the work", model_tier="opus")
    )

    assert command == (
        "claude",
        "--bg",
        "do the work",
        "--model",
        "opus",
        "--permission-mode",
        "auto",
    )


def test_claude_adapter_names_and_resumes_a_provider_session():
    command = ClaudeAdapter().command(
        RunRequest(
            prompt="next turn",
            name="sdd-demo-cpo",
            resume_session_id="session-1",
            model_tier="fable",
        )
    )

    assert command == (
        "claude",
        "--bg",
        "--name",
        "sdd-demo-cpo",
        "--resume",
        "session-1",
        "next turn",
        "--model",
        "fable",
        "--permission-mode",
        "auto",
    )

def test_codex_adapter_maps_the_shared_request_to_non_interactive_exec():
    request = RunRequest(
        prompt="do the work",
        model="gpt-5.6-sol",
        add_dirs=("/first path", "/second"),
    )

    command = CodexAdapter().command(request)

    assert command == (
        "codex",
        "exec",
        "--approve-for-me",
        "--model",
        "gpt-5.6-sol",
        "--add-dir",
        "/first path",
        "--add-dir",
        "/second",
        "do the work",
    )


def test_codex_adapter_uses_configured_model_when_request_omits_one():
    command = CodexAdapter().command(RunRequest(prompt="do the minimum"))

    assert command == (
        "codex",
        "exec",
        "--approve-for-me",
        "do the minimum",
    )


def test_codex_adapter_prepends_the_shared_task_context(tmp_path):
    doctrine = tmp_path / "doctrine"
    doctrine.mkdir()
    (doctrine / "task_map.md").write_text(
        "| When you're about to… | Consult | Layer | Fires |\n"
        "|---|---|---|---|\n"
        "| Commit anything | `commit_format.md` | governance |  |\n",
        encoding="utf-8",
    )

    command = CodexAdapter().command(
        RunRequest(prompt="do the work", core_root=tmp_path)
    )

    prompt = command[-1]
    assert "KENSAIAPP_TASK_MAP" in prompt
    assert "Commit anything → commit_format.md" in prompt
    assert prompt.endswith("do the work")


def test_codex_adapter_threads_a_tier_model_into_runtime_identity(tmp_path):
    command = CodexAdapter().command(
        RunRequest(prompt="do the work", core_root=tmp_path, model_tier="sonnet")
    )

    assert "--model" in command
    assert command[command.index("--model") + 1] == "gpt-5.6-terra"
    assert 'model_reasoning_effort="medium"' in command
    assert 'gpt-5.6-terra <noreply@openai.com>' in command[-1]


def test_codex_adapter_threads_an_explicit_model_verbatim(tmp_path):
    command = CodexAdapter().command(
        RunRequest(prompt="do the work", core_root=tmp_path, model="gpt-explicit-fixture")
    )

    assert command[command.index("--model") + 1] == "gpt-explicit-fixture"
    assert 'gpt-explicit-fixture <noreply@openai.com>' in command[-1]


def test_codex_adapter_resume_uses_the_current_assignment_only(tmp_path):
    command = CodexAdapter().background_command(
        RunRequest(
            prompt="next", core_root=tmp_path, resume_session_id="thread-1", model_tier="opus"
        )
    )

    assert command[command.index("--model") + 1] == "gpt-5.6-sol"
    assert 'gpt-5.6-sol <noreply@openai.com>' in command[-1]
    assert "gpt-5.6-terra" not in command[-1]


def test_codex_adapter_without_an_assignment_gives_the_generic_codex_identity(tmp_path):
    command = CodexAdapter().command(RunRequest(prompt="do the work", core_root=tmp_path))

    assert "--model" not in command
    assert '`--co-authored-by "Codex <noreply@openai.com>"`' in command[-1]


def test_codex_attribution_changes_only_the_prompt(tmp_path):
    # CP-106: for the same request, the runtime context changes the prompt argument
    # and nothing else. The context-less tuples are pinned exactly by the tests above.
    requests = (
        RunRequest(prompt="work", model_tier="sonnet", add_dirs=("/product",)),
        RunRequest(prompt="work", model="gpt-explicit-fixture"),
        RunRequest(prompt="work", resume_session_id="thread-1", model_tier="opus"),
        RunRequest(prompt="work"),
    )
    for request in requests:
        with_context = replace(request, core_root=tmp_path)
        for render in ("command", "background_command"):
            bare = getattr(CodexAdapter(), render)(request)
            attributed = getattr(CodexAdapter(), render)(with_context)

            assert attributed[:-1] == bare[:-1]
            assert attributed[-1].endswith("work")


def test_claude_adapter_contains_no_codex_runtime_identity(tmp_path):
    command = ClaudeAdapter().command(
        RunRequest(prompt="do the work", core_root=tmp_path, model_tier="sonnet")
    )
    joined = " ".join(command)

    assert "noreply@openai.com" not in joined
    assert "Execution surface: Codex" not in joined
    assert "gpt-5.6" not in joined


def test_codex_adapter_refusals_remain_unchanged(tmp_path):
    for request, field in (
        (RunRequest(prompt="w", name="logical-name"), "name"),
        (
            RunRequest(prompt="w", resume_session_id="thread-1", add_dirs=("/x",)),
            "add_dirs on resume",
        ),
    ):
        attributed = replace(request, core_root=tmp_path, model_tier="sonnet")
        for render in (CodexAdapter().command, CodexAdapter().background_command):
            try:
                render(attributed)
            except agent_run.UnsupportedRequest as error:
                assert str(error) == (
                    f"provider 'codex' does not support request fields: {field}"
                )
            else:
                raise AssertionError(f"Codex accepted unsupported {field}")


def test_claude_adapter_does_not_duplicate_codex_bootstrap(tmp_path):
    command = ClaudeAdapter().command(
        RunRequest(prompt="do the work", core_root=tmp_path)
    )

    assert command[-3] == "do the work"
    assert "KENSAIAPP_TASK_MAP" not in " ".join(command)


def test_codex_adapter_resolves_model_and_effort_from_a_kensaiapp_tier():
    command = CodexAdapter().command(
        RunRequest(prompt="do the work", model_tier="opus")
    )

    assert command == (
        "codex",
        "exec",
        "--approve-for-me",
        "--model",
        "gpt-5.6-sol",
        "--config",
        'model_reasoning_effort="high"',
        "do the work",
    )


def test_codex_adapter_resumes_a_thread_with_the_same_tier():
    command = CodexAdapter().background_command(
        RunRequest(
            prompt="next turn",
            resume_session_id="thread-1",
            model_tier="fable",
        )
    )

    assert command == (
        "codex",
        "exec",
        "--approve-for-me",
        "resume",
        "--json",
        "--model",
        "gpt-5.6-sol",
        "--config",
        'model_reasoning_effort="xhigh"',
        "thread-1",
        "next turn",
    )


def test_codex_adapter_refuses_start_only_fields_on_a_resumed_thread():
    for request, field in (
        (RunRequest(prompt="work", name="logical-name"), "name"),
        (
            RunRequest(
                prompt="work",
                resume_session_id="thread-1",
                add_dirs=("/extra",),
            ),
            "add_dirs on resume",
        ),
    ):
        try:
            CodexAdapter().command(request)
        except agent_run.UnsupportedRequest as error:
            assert str(error) == (
                f"provider 'codex' does not support request fields: {field}"
            )
        else:
            raise AssertionError(f"Codex accepted unsupported {field}")

def test_an_explicit_model_and_a_tier_cannot_both_be_requested():
    request = RunRequest(
        prompt="work", model="gpt-5.6-sol", model_tier="opus"
    )

    for adapter in (ClaudeAdapter(), CodexAdapter(), GeminiAdapter()):
        try:
            adapter.command(request)
        except agent_run.UnsupportedRequest as error:
            assert str(error) == (
                "request fields model and model_tier are mutually exclusive"
            )
        else:
            raise AssertionError("adapter accepted a raw model and model tier")


def test_gemini_adapter_maps_a_tier_to_model_and_effort():
    command = GeminiAdapter().command(RunRequest(prompt="do the work", model_tier="opus"))

    assert command == (
        "agy",
        "--mode",
        "accept-edits",
        "--model",
        "gemini-3.1-pro-low",
        "--effort",
        "low",
        "-p",
        "do the work",
    )


def test_gemini_fable_uses_highest_effort():
    command = GeminiAdapter().command(RunRequest(prompt="do the work", model_tier="fable"))

    assert command[command.index("--model") + 1] == "gemini-3.1-pro-high"
    assert command[command.index("--effort") + 1] == "high"


def test_gemini_haiku_uses_the_efficient_model_at_low_effort():
    command = GeminiAdapter().command(RunRequest(prompt="do the work", model_tier="haiku"))

    assert command[command.index("--model") + 1] == "gemini-3.8-flash-low"
    assert command[command.index("--effort") + 1] == "low"


def test_gemini_caller_effort_wins_over_the_tier():
    command = GeminiAdapter().command(
        RunRequest(prompt="do the work", model_tier="fable", effort=agent_run.Effort.LOW)
    )

    assert command[command.index("--model") + 1] == "gemini-3.1-pro-high"
    assert command[command.index("--effort") + 1] == "low"


def test_gemini_background_streams_json_and_adds_dirs():
    command = GeminiAdapter().background_command(
        RunRequest(
            prompt="next",
            resume_session_id="sess-1",
            model_tier="sonnet",
            add_dirs=("/product path",),
        )
    )

    assert command == (
        "agy",
        "--mode",
        "accept-edits",
        "--output-format",
        "stream-json",
        "--conversation",
        "sess-1",
        "--model",
        "gemini-3.8-flash-medium",
        "--effort",
        "medium",
        "--add-dir",
        "/product path",
        "-p",
        "next",
    )


def test_gemini_skill_path_adds_parent_directory():
    command = GeminiAdapter().command(
        RunRequest(
            prompt="work",
            skill_path=Path("/path/to/skill/SKILL.md"),
        )
    )

    assert "--add-dir" in command
    assert command[command.index("--add-dir") + 1] == "/path/to/skill"


def test_gemini_refuses_a_logical_name():
    try:
        GeminiAdapter().command(RunRequest(prompt="work", name="logical-name"))
    except agent_run.UnsupportedRequest as error:
        assert str(error) == "provider 'gemini' does not support request fields: name"
    else:
        raise AssertionError("Gemini accepted a logical name")


def test_gemini_bootstrap_names_the_assigned_model(tmp_path):
    doctrine = tmp_path / "doctrine"
    doctrine.mkdir()
    (doctrine / "task_map.md").write_text(
        "| When you're about to… | Consult | Layer | Fires |\n"
        "|---|---|---|---|\n"
        "| Commit anything | `commit_format.md` | governance |  |\n",
        encoding="utf-8",
    )
    command = GeminiAdapter().command(
        RunRequest(prompt="do the work", core_root=tmp_path, model_tier="sonnet")
    )

    prompt = command[-1]
    assert command[-2] == "-p"
    assert "KENSAIAPP_TASK_MAP" in prompt
    assert "`--surface Gemini`" in prompt
    assert "gemini-3.8-flash-medium <noreply@google.com>" in prompt
    assert "noreply@openai.com" not in prompt
    assert "noreply@x.ai" not in prompt
    assert prompt.endswith("do the work")


def test_gemini_without_an_assignment_gives_the_generic_identity(tmp_path):
    command = GeminiAdapter().command(RunRequest(prompt="do the work", core_root=tmp_path))

    assert "--model" not in command
    assert '`--co-authored-by "Gemini <noreply@google.com>"`' in command[-1]


def test_codex_background_command_emits_json_lifecycle_events():
    command = CodexAdapter().background_command(RunRequest(prompt="work"))

    assert command == (
        "codex",
        "exec",
        "--approve-for-me",
        "--json",
        "work",
    )


def test_codex_settings_env_prefixes_the_command():
    bare = CodexAdapter().command(RunRequest(prompt="work"))

    command = CodexAdapter().command(
        RunRequest(prompt="work", settings='{"env":{"A":"1","B":"two words"}}')
    )

    assert command == ("env", "A=1", "B=two words", *bare)


def test_codex_settings_env_keeps_document_order():
    command = CodexAdapter().command(
        RunRequest(prompt="work", settings='{"env":{"Z":"last-declared","A":"first-declared"}}')
    )

    assert command[:5] == ("env", "Z=last-declared", "A=first-declared", "codex", "exec")


def test_codex_settings_env_reaches_background_and_resume():
    settings = '{"env":{"A":"1"}}'

    background = CodexAdapter().background_command(RunRequest(prompt="work", settings=settings))
    resumed = CodexAdapter().command(
        RunRequest(prompt="next", resume_session_id="thread-1", settings=settings)
    )

    assert background[:2] == ("env", "A=1")
    assert resumed[:2] == ("env", "A=1")


def test_codex_empty_settings_leave_the_command_unchanged():
    bare = CodexAdapter().command(RunRequest(prompt="work"))

    for settings in ("{}", '{"env":{}}'):
        assert CodexAdapter().command(RunRequest(prompt="work", settings=settings)) == bare


def test_codex_settings_refuses_keys_without_an_equivalent():
    request = RunRequest(prompt="work", settings='{"hooks":{},"env":{},"permissions":{}}')

    try:
        CodexAdapter().command(request)
    except agent_run.UnsupportedRequest as error:
        assert str(error) == (
            "provider 'codex' has no equivalent for settings keys: hooks, permissions"
        )
    else:
        raise AssertionError("Codex accepted unsupported settings keys")


def test_codex_settings_refuses_unknown_keys_sorted_not_by_declaration_order():
    """An edge the responsibility implies but the instruction's behaviours don't enumerate: CP-132
    says the refused keys are sorted, and the instruction's own example (`hooks`, `permissions`)
    happens to already be alphabetical, so it cannot discriminate `sorted()` from declaration
    order. `zeta` before `alpha` in the document can."""
    request = RunRequest(prompt="work", settings='{"zeta":{},"alpha":{}}')

    try:
        CodexAdapter().command(request)
    except agent_run.UnsupportedRequest as error:
        assert str(error) == (
            "provider 'codex' has no equivalent for settings keys: alpha, zeta"
        )
    else:
        raise AssertionError("Codex accepted unsupported settings keys")


def test_codex_settings_refuses_a_malformed_document():
    malformed_documents = (
        "not json",
        "[]",
        '{"env":[]}',
        '{"env":{"1X":"v"}}',
        '{"env":{"A=B":"v"}}',
        '{"env":{"A":1}}',
    )
    for settings in malformed_documents:
        try:
            CodexAdapter().command(RunRequest(prompt="work", settings=settings))
        except agent_run.UnsupportedRequest as error:
            assert str(error) == (
                "provider 'codex' settings must be a JSON object whose env maps "
                "variable names to strings"
            )
        else:
            raise AssertionError(f"Codex accepted malformed settings {settings!r}")


def test_codex_settings_refusal_builds_no_command(tmp_path):
    processes = FakeProcesses()
    runner = AgentRunner({"codex": CodexAdapter()}, processes)
    request = RunRequest(prompt="work", settings='{"hooks":{}}')

    try:
        runner.background("codex", request, tmp_path / "run.jsonl")
    except agent_run.UnsupportedRequest:
        pass
    else:
        raise AssertionError("Codex accepted unsupported settings keys")

    assert processes.detached_calls == []
    assert processes.logged_calls == []


# --- a telemetry-bearing --settings turns on Codex's own OTLP log exporter ------------------------

_RUN_ID = "0b6f3a52-5b7c-4d1e-9a8f-2c4e6d8f0a1b"


def _telemetry_settings(
    *,
    endpoint="http://h:4318",
    protocol="http/json",
    logs_exporter="otlp",
    resource_attributes=f"kensai.arm=skill,kensai.run_id={_RUN_ID}",
    **extra_env,
):
    """The `--settings` document `run_telemetry` builds (`core/tools/run_telemetry.sh`): the base
    telemetry keys, the endpoint, and the resource attributes. A keyword given `None` leaves that
    key out."""
    env = {
        "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
        "OTEL_METRICS_EXPORTER": "otlp",
        "OTEL_LOGS_EXPORTER": logs_exporter,
        "OTEL_EXPORTER_OTLP_PROTOCOL": protocol,
        "OTEL_EXPORTER_OTLP_ENDPOINT": endpoint,
        "OTEL_RESOURCE_ATTRIBUTES": resource_attributes,
        **extra_env,
    }
    return json.dumps({"env": {key: value for key, value in env.items() if value is not None}})


def _exporter_configs(command):
    """Every `--config otel.exporter=…` value on the argv, in order."""
    return [
        command[index + 1]
        for index, token in enumerate(command[:-1])
        if token == "--config" and command[index + 1].startswith("otel.exporter=")
    ]


def test_codex_command_carries_the_exporter_config_from_telemetry_settings():
    command = CodexAdapter().command(RunRequest(prompt="work", settings=_telemetry_settings()))

    assert _exporter_configs(command) == [
        'otel.exporter={otlp-http={endpoint="http://h:4318/v1/logs",protocol="json"}}'
    ]
    assert f"OTEL_RESOURCE_ATTRIBUTES=kensai.arm=skill,kensai.run_id={_RUN_ID}" in command
    assert command[0] == "env"
    assert command.index("codex") > command.index(
        f"OTEL_RESOURCE_ATTRIBUTES=kensai.arm=skill,kensai.run_id={_RUN_ID}"
    )


def test_codex_telemetry_settings_leave_the_env_prefix_as_the_settings_build_it():
    """The exporter config is added to the Codex argv, never to the `env` prefix, which stays
    exactly what `_codex_settings_env` makes of the document (CP-131)."""
    settings = _telemetry_settings()

    command = CodexAdapter().command(RunRequest(prompt="work", settings=settings))

    prefix = agent_run._codex_settings_env(settings)
    assert command[: len(prefix)] == prefix
    assert command[len(prefix)] == "codex"


def test_codex_binary_protocol_maps_from_http_protobuf():
    command = CodexAdapter().command(
        RunRequest(prompt="work", settings=_telemetry_settings(protocol="http/protobuf"))
    )

    assert _exporter_configs(command) == [
        'otel.exporter={otlp-http={endpoint="http://h:4318/v1/logs",protocol="binary"}}'
    ]


def test_codex_skill_shape_carries_the_exporter_config():
    request = RunRequest(
        prompt="work",
        settings=_telemetry_settings(),
        skill_name="example",
        skill_path=Path("/pin/.claude/skills/example/SKILL.md"),
    )
    expected = ['otel.exporter={otlp-http={endpoint="http://h:4318/v1/logs",protocol="json"}}']

    foreground = CodexAdapter().command(request)
    background = CodexAdapter().background_command(request)

    for command in (foreground, background):
        assert Path(command[command.index("--skill-name") - 1]).name == "codex_skill_run.py"
        assert _exporter_configs(command) == expected


def test_codex_exporter_config_reaches_the_resume_shape():
    command = CodexAdapter().command(
        RunRequest(prompt="next", resume_session_id="thread-1", settings=_telemetry_settings())
    )

    assert "resume" in command
    assert _exporter_configs(command) == [
        'otel.exporter={otlp-http={endpoint="http://h:4318/v1/logs",protocol="json"}}'
    ]
    assert command.index("--config") < command.index("thread-1")


def test_codex_endpoint_trailing_slash_gives_a_single_logs_path():
    command = CodexAdapter().command(
        RunRequest(prompt="work", settings=_telemetry_settings(endpoint="http://h:4318/"))
    )

    assert _exporter_configs(command) == [
        'otel.exporter={otlp-http={endpoint="http://h:4318/v1/logs",protocol="json"}}'
    ]


def test_codex_exporter_endpoint_is_a_quoted_toml_string_whatever_it_holds():
    """The `-c` value is a TOML inline table (Codex parses it as TOML), so an endpoint holding a
    quote or a backslash must still read back as itself rather than end the string early."""
    import tomllib

    endpoint = 'http://h:4318/a"b\\c'

    command = CodexAdapter().command(
        RunRequest(prompt="work", settings=_telemetry_settings(endpoint=endpoint))
    )

    (config,) = _exporter_configs(command)
    parsed = tomllib.loads(config.replace("otel.exporter=", "exporter = ", 1))
    assert parsed["exporter"] == {
        "otlp-http": {"endpoint": f"{endpoint}/v1/logs", "protocol": "json"}
    }


def test_codex_settings_without_telemetry_give_no_exporter_config():
    """The uninstrumented path: `run_telemetry` hands over the context cap alone."""
    settings = '{"env":{"KENSAIAPP_CONTEXT_CAP":"150000"}}'

    command = CodexAdapter().command(RunRequest(prompt="work", settings=settings))

    assert _exporter_configs(command) == []
    assert command[:2] == ("env", "KENSAIAPP_CONTEXT_CAP=150000")


def test_codex_unsupported_protocol_gives_no_exporter_config_and_no_refusal():
    command = CodexAdapter().command(
        RunRequest(prompt="work", settings=_telemetry_settings(protocol="grpc"))
    )

    assert _exporter_configs(command) == []
    assert "codex" in command


def test_codex_logs_exporter_other_than_otlp_gives_no_exporter_config():
    command = CodexAdapter().command(
        RunRequest(prompt="work", settings=_telemetry_settings(logs_exporter="none"))
    )

    assert _exporter_configs(command) == []


@pytest.mark.parametrize("endpoint", [None, ""])
def test_codex_settings_without_an_endpoint_give_no_exporter_config(endpoint):
    command = CodexAdapter().command(
        RunRequest(prompt="work", settings=_telemetry_settings(endpoint=endpoint))
    )

    assert _exporter_configs(command) == []


@pytest.mark.parametrize("absent", ["protocol", "logs_exporter"])
def test_codex_settings_missing_the_protocol_or_the_logs_exporter_give_no_exporter_config(absent):
    """Only `OTEL_LOGS_EXPORTER=otlp` with an `http/json` or `http/protobuf` protocol turns the
    exporter on; "anything else yields no exporter config and no refusal" — an absent key too,
    never a default filled in for it."""
    command = CodexAdapter().command(
        RunRequest(prompt="work", settings=_telemetry_settings(**{absent: None}))
    )

    assert _exporter_configs(command) == []
    assert "codex" in command


def test_codex_settings_without_a_run_id_still_configure_the_exporter():
    """A settings document with the base keys and no `kensai.run_id` still configures the
    exporter, and the run still emits, as a Claude run does. `run_telemetry` never builds such a
    document. Every document it hands over with the base keys carries exactly one run id."""
    for resource_attributes in (None, "kensai.instance=example-host"):
        command = CodexAdapter().command(
            RunRequest(
                prompt="work",
                settings=_telemetry_settings(resource_attributes=resource_attributes),
            )
        )

        assert _exporter_configs(command) == [
            'otel.exporter={otlp-http={endpoint="http://h:4318/v1/logs",protocol="json"}}'
        ]
        assert not any("kensai.run_id" in token for token in command)


def test_codex_exporter_translation_keeps_existing_settings_refusals():
    telemetry = json.loads(_telemetry_settings())
    with_a_foreign_key = json.dumps({**telemetry, "hooks": {}})
    with_a_non_string_value = json.dumps({"env": {**telemetry["env"], "A": 1}})

    foreign_key_refusal = "no equivalent for settings keys: hooks"
    with pytest.raises(agent_run.UnsupportedRequest, match=foreign_key_refusal):
        CodexAdapter().command(RunRequest(prompt="work", settings=with_a_foreign_key))
    with pytest.raises(agent_run.UnsupportedRequest, match="must be a JSON object"):
        CodexAdapter().command(RunRequest(prompt="work", settings=with_a_non_string_value))


def test_gemini_command_carries_no_exporter_config():
    command = GeminiAdapter().command(RunRequest(prompt="work", settings=_telemetry_settings()))

    assert not any("otel.exporter" in token for token in command)
    assert command[: len(agent_run._codex_settings_env(_telemetry_settings(), "gemini"))] == (
        agent_run._codex_settings_env(_telemetry_settings(), "gemini")
    )


def _init_instance_agent(root: Path, stem: str, *, model: str | None = None) -> Path:
    """A throwaway instance holding one `.claude/agents/<stem>.md`, with a `model:` frontmatter
    line when `model` is given."""
    agent_dir = root / ".claude" / "agents"
    agent_dir.mkdir(parents=True, exist_ok=True)
    frontmatter = f"---\nname: {stem}\n"
    if model is not None:
        frontmatter += f"model: {model}\n"
    frontmatter += "---\n\n"
    path = agent_dir / f"{stem}.md"
    path.write_text(f"{frontmatter}You are the {stem} agent.")
    return path


def test_codex_agent_prompt_names_the_agent_and_its_file(tmp_path):
    sat = tmp_path / "sat"
    agent_path = _init_instance_agent(sat, "dev")

    command = CodexAdapter().command(RunRequest(prompt="do the work", agent="dev", instance_root=sat))

    assert command[-1] == (
        f"You are running as the dev agent. Read {agent_path.resolve()} in full and follow it "
        "as your agent identity before doing this task: do the work"
    )


def test_codex_agent_sentence_follows_the_task_context(tmp_path):
    sat = tmp_path / "sat"
    _init_instance_agent(sat, "dev")
    doctrine = tmp_path / "doctrine"
    doctrine.mkdir()
    (doctrine / "task_map.md").write_text(
        "| When you're about to… | Consult | Layer | Fires |\n"
        "|---|---|---|---|\n"
        "| Commit anything | `commit_format.md` | governance |  |\n",
        encoding="utf-8",
    )

    command = CodexAdapter().command(
        RunRequest(prompt="do the work", agent="dev", instance_root=sat, core_root=tmp_path)
    )

    prompt = command[-1]
    core_at = prompt.index("Kensaiapp core resolution:")
    agent_at = prompt.index("You are running as the dev agent.")
    prompt_at = prompt.index("do the work")
    assert core_at < agent_at < prompt_at


def test_codex_agent_sentence_is_carried_on_resume(tmp_path):
    sat = tmp_path / "sat"
    _init_instance_agent(sat, "dev")

    command = CodexAdapter().command(
        RunRequest(prompt="next", agent="dev", instance_root=sat, resume_session_id="thread-1")
    )

    assert "You are running as the dev agent." in command[-1]


def test_codex_agent_is_the_instances_own_over_the_pins(tmp_path, pins_home):
    host = _build_pin_host(tmp_path / "host")
    (host / ".claude" / "agents" / "dev.md").write_text(
        "---\nname: dev\n---\n\nHost's dev agent."
    )
    made = pin.make(host, pins_home)
    sat = tmp_path / "sat"
    own_path = _init_instance_agent(sat, "dev")

    command = CodexAdapter().command(
        RunRequest(prompt="work", agent="dev", instance_root=sat, pin=made)
    )

    assert str(own_path.resolve()) in command[-1]


def test_an_agent_files_model_line_is_not_a_fallback(tmp_path):
    """Nothing falls back to an agent file's `model:` — with no model passed, none is forced,
    on either provider that reads the file."""
    sat = tmp_path / "sat"
    _init_instance_agent(sat, "dev", model="opus")

    for adapter in (CodexAdapter(), GeminiAdapter()):
        command = adapter.command(RunRequest(prompt="work", agent="dev", instance_root=sat))
        assert "--model" not in command
        assert not [arg for arg in command if "reasoning_effort" in arg]


def test_codex_agent_without_a_model_field_forces_no_model(tmp_path):
    """Edge implied by CP-129/CP-130 but not enumerated in the instruction's own behaviours: an
    agent file that carries no `model:` frontmatter at all is not a non-tier model (CP-130 refuses
    only *when a `model:` is present and not a tier*) — it is simply nothing to fall back to, and
    the generic Codex identity is unaffected."""
    sat = tmp_path / "sat"
    _init_instance_agent(sat, "dev")

    command = CodexAdapter().command(RunRequest(prompt="work", agent="dev", instance_root=sat))

    assert "--model" not in command


def test_codex_agent_without_an_instance_root_is_refused():
    try:
        CodexAdapter().command(RunRequest(prompt="work", agent="dev"))
    except agent_run.UnsupportedRequest as error:
        assert str(error) == "provider 'codex' needs an instance root to find agent 'dev'"
    else:
        raise AssertionError("Codex accepted an agent request with no instance root")


def test_codex_unknown_agent_is_refused(tmp_path):
    sat = tmp_path / "sat"
    sat.mkdir()

    try:
        CodexAdapter().command(RunRequest(prompt="work", agent="ghost", instance_root=sat))
    except agent_run.UnsupportedRequest as error:
        assert str(error) == f"provider 'codex' found no agent file for 'ghost' under {sat}"
    else:
        raise AssertionError("Codex accepted an unknown agent")


def test_runner_delegates_execution_and_propagates_the_exit_status():
    processes = FakeProcesses(returncode=17)
    runner = AgentRunner({"claude": ClaudeAdapter()}, processes)

    status = runner.run("claude", RunRequest(prompt="work"))

    assert status == 17
    assert processes.calls == [
        ("claude", "--bg", "work", "--permission-mode", "auto")
    ]


def test_background_claude_uses_the_provider_owned_launch(tmp_path):
    processes = FakeProcesses()
    runner = AgentRunner({"claude": ClaudeAdapter()}, processes)
    log_path = tmp_path / "claude.jsonl"

    result = runner.background("claude", RunRequest(prompt="work"), log_path)

    assert result == agent_run.BackgroundRun(
        provider="claude",
        owner="provider",
        log_path=log_path,
    )
    assert processes.logged_calls == [
        (("claude", "--bg", "work", "--permission-mode", "auto"), log_path)
    ]
    assert processes.detached_calls == []


def test_background_codex_uses_a_detached_process_and_returns_its_pid(tmp_path):
    processes = FakeProcesses(pid=7654)
    runner = AgentRunner({"codex": CodexAdapter()}, processes)
    log_path = tmp_path / "codex.jsonl"

    result = runner.background("codex", RunRequest(prompt="work"), log_path)

    assert result == agent_run.BackgroundRun(
        provider="codex",
        owner="process",
        log_path=log_path,
        pid=7654,
    )
    assert processes.logged_calls == []
    assert processes.detached_calls == [
        (
            (
                "codex",
                "exec",
                "--approve-for-me",
                "--json",
                "work",
            ),
            log_path,
        )
    ]


def test_a_failed_provider_owned_background_launch_is_reported(tmp_path):
    processes = FakeProcesses(returncode=23)
    runner = AgentRunner({"claude": ClaudeAdapter()}, processes)

    try:
        runner.background("claude", RunRequest(prompt="work"), tmp_path / "run.log")
    except agent_run.LaunchFailed as error:
        assert error.returncode == 23
        assert str(error) == "provider 'claude' launch command exited 23"
    else:
        raise AssertionError("failed launch was accepted")


def test_unknown_provider_is_refused_before_any_process_runs():
    processes = FakeProcesses()
    runner = AgentRunner({"claude": ClaudeAdapter()}, processes)

    try:
        runner.run("not-real", RunRequest(prompt="work"))
    except agent_run.UnknownProvider as error:
        assert str(error) == "unknown provider 'not-real'; available providers: claude"
    else:
        raise AssertionError("unknown provider was accepted")

    assert processes.calls == []


def test_cli_dry_run_prints_a_shell_safe_provider_command_and_spawns_nothing():
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "claude",
            "--prompt",
            "prompt with spaces and 'quotes'",
            "--add-dir",
            "/a path",
            "--dry-run",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout == (
        "claude --bg 'prompt with spaces and '\"'\"'quotes'\"'\"'' "
        "--permission-mode auto '--add-dir=/a path'\n"
    )


def test_cli_reports_an_unknown_provider_plainly():
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "not-real",
            "--prompt",
            "work",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == (
        "agent-run: unknown provider 'not-real'; "
        "available providers: claude, codex, gemini, hf, ollama\n"
    )


def test_cli_dry_run_prints_the_codex_command():
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "codex",
            "--prompt",
            "work in this repo",
            "--model",
            "gpt-5.6-sol",
            "--add-dir",
            "/a path",
            "--dry-run",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout == (
        "codex exec --approve-for-me --model gpt-5.6-sol "
        "--add-dir '/a path' 'work in this repo'\n"
    )


def test_cli_dry_run_prints_the_gemini_command():
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "gemini",
            "--prompt",
            "work in this repo",
            "--model-tier",
            "sonnet",
            "--add-dir",
            "/a path",
            "--dry-run",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert result.stdout == (
        "agy --mode accept-edits --model gemini-3.8-flash-medium --effort medium "
        "--add-dir '/a path' -p 'work in this repo'\n"
    )


def test_cli_dry_run_resolves_a_codex_model_tier():
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "codex",
            "--prompt",
            "work",
            "--model-tier",
            "sonnet",
            "--dry-run",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == (
        "codex exec --approve-for-me --model gpt-5.6-terra "
        "--config 'model_reasoning_effort=\"medium\"' work\n"
    )


def test_cli_dry_run_shows_the_codex_settings_env():
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "codex",
            "--prompt",
            "work",
            "--settings",
            '{"env":{"A":"1"}}',
            "--dry-run",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.startswith("env A=1 codex exec --approve-for-me")


def test_cli_refuses_codex_settings_without_an_equivalent():
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "codex",
            "--prompt",
            "work",
            "--settings",
            '{"hooks":{}}',
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == (
        "agent-run: provider 'codex' has no equivalent for settings keys: hooks\n"
    )


def test_cli_refuses_a_raw_model_and_model_tier_together():
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "codex",
            "--prompt",
            "work",
            "--model",
            "gpt-5.6-sol",
            "--model-tier",
            "opus",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "not allowed with argument --model" in result.stderr


def test_cli_background_dry_run_prints_codex_json_command(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "codex",
            "--prompt",
            "work",
            "--background",
            "--log",
            str(tmp_path / "run.jsonl"),
            "--dry-run",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == (
        "codex exec --approve-for-me --json work\n"
    )
    assert not (tmp_path / "run.jsonl").exists()


def test_cli_background_codex_returns_before_the_detached_process_finishes(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    release = tmp_path / "release"
    log_path = tmp_path / "run.jsonl"
    codex = bin_dir / "codex"
    codex.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, time\n"
        "print(json.dumps({'type': 'thread.started', 'thread_id': 't-1'}), flush=True)\n"
        "while not os.path.exists(os.environ['AGENT_RUN_RELEASE']): time.sleep(0.01)\n"
        "print(json.dumps({'type': 'turn.completed'}), flush=True)\n"
    )
    codex.chmod(0o755)
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["AGENT_RUN_RELEASE"] = str(release)

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(_SCRIPT),
                "--provider",
                "codex",
                "--prompt",
                "work",
                "--background",
                "--log",
                str(log_path),
            ],
            text=True,
            capture_output=True,
            check=False,
            timeout=2,
            env=env,
        )
        assert result.returncode == 0, result.stderr
        launch = json.loads(result.stdout)
        assert launch == {
            "log_path": str(log_path),
            "owner": "process",
            "pid": launch["pid"],
            "provider": "codex",
            "session_id": None,
        }
        assert isinstance(launch["pid"], int)
        assert not release.exists()
    finally:
        release.touch()

    # The child is detached before this test releases it. Under the repository's parallel test
    # load, its first interpreter exec can be queued for several seconds after the parent has
    # correctly returned, so the observation budget must cover scheduling rather than redefine
    # the launch contract as synchronous.
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if log_path.exists() and '"type": "turn.completed"' in log_path.read_text():
            break
        time.sleep(0.01)
    else:
        raise AssertionError("detached Codex stub did not finish after release")


def test_cli_background_claude_returns_provider_owned_metadata(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_path = tmp_path / "run.log"
    claude = bin_dir / "claude"
    claude.write_text("#!/usr/bin/env bash\nprintf 'accepted run-1\\n'\n")
    claude.chmod(0o755)
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "claude",
            "--prompt",
            "work",
            "--background",
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
        "owner": "provider",
        "pid": None,
        "provider": "claude",
        "session_id": None,
    }
    assert log_path.read_text() == "accepted run-1\n"


def test_background_shape_keeps_todays_argv():
    """Task 6 — the default shape (no `shape` passed) and an explicit `Shape.BACKGROUND` both
    produce exactly the pre-change ClaudeAdapter output for the same request."""
    fields = dict(
        prompt="next turn",
        name="sdd-demo-cpo",
        resume_session_id="session-1",
        model_tier="fable",
    )
    expected = (
        "claude",
        "--bg",
        "--name",
        "sdd-demo-cpo",
        "--resume",
        "session-1",
        "next turn",
        "--model",
        "fable",
        "--permission-mode",
        "auto",
    )

    assert ClaudeAdapter().command(RunRequest(**fields)) == expected
    assert (
        ClaudeAdapter().command(RunRequest(**fields, shape=agent_run.Shape.BACKGROUND))
        == expected
    )


def test_print_shape_is_product_cards_command():
    """Task 6 — the flags `product-card/launcher.sh:131` assembles today, in the same order."""
    command = ClaudeAdapter().command(
        RunRequest(
            prompt="invoke the product-card skill for the example-product project.",
            agent="principal-pm",
            shape=agent_run.Shape.PRINT,
        )
    )

    assert command == (
        "claude",
        "-p",
        "invoke the product-card skill for the example-product project.",
        "--agent",
        "principal-pm",
        "--permission-mode",
        "auto",
        "--permission-prompts",
        "none",
    )


def test_print_shape_carries_add_dir_and_settings_after_permission_mode():
    command = ClaudeAdapter().command(
        RunRequest(
            prompt="invoke the product-card skill for the example-product project.",
            agent="principal-pm",
            add_dirs=("/skills/product-card",),
            settings='{"env": {}}',
            shape=agent_run.Shape.PRINT,
        )
    )

    assert command == (
        "claude",
        "-p",
        "invoke the product-card skill for the example-product project.",
        "--agent",
        "principal-pm",
        "--permission-mode",
        "auto",
        "--permission-prompts",
        "none",
        "--add-dir=/skills/product-card",
        "--settings",
        '{"env": {}}',
    )


def test_turn_shape_matches_agent_turn_start_and_resume():
    """Task 6 — equal to today's `agent_turn.claude_command` for a start and for a resume."""
    start_expected = agent_turn.claude_command(
        prompt="do the work",
        session_id="session-abc",
        resume=False,
        agent="developer",
        name="turn-name",
        model=None,
        tier="opus",
        add_dirs=("/a",),
        settings='{"env": {}}',
    )
    start_command = ClaudeAdapter().command(
        RunRequest(
            prompt="do the work",
            session_id="session-abc",
            agent="developer",
            name="turn-name",
            model_tier="opus",
            add_dirs=("/a",),
            settings='{"env": {}}',
            shape=agent_run.Shape.TURN,
        )
    )
    assert start_command == start_expected

    resume_expected = agent_turn.claude_command(
        prompt="next turn",
        session_id="session-abc",
        resume=True,
        agent="developer",
        name="turn-name",
        model=None,
        tier="opus",
        add_dirs=("/a",),
        settings='{"env": {}}',
    )
    resume_command = ClaudeAdapter().command(
        RunRequest(
            prompt="next turn",
            resume_session_id="session-abc",
            agent="developer",
            name="turn-name",
            model_tier="opus",
            add_dirs=("/a",),
            settings='{"env": {}}',
            shape=agent_run.Shape.TURN,
        )
    )
    assert resume_command == resume_expected
    assert "--agent" not in resume_command
    assert "--resume" in resume_command
    assert "--session-id" not in resume_command


def test_print_argv_round_trips_awkward_prompts(tmp_path):
    """Task 6 — a prompt holding spaces, both quote kinds, `$`, a backtick and a newline, read
    back by a real bash 3.2-compatible `read -d ''` loop, is byte-identical."""
    prompt = "spaces \"double\" 'single' $DOLLAR `backtick` and\nnewline"
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--provider", "claude", "--prompt", prompt, "--print-argv"],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr

    expected = ClaudeAdapter().command(RunRequest(prompt=prompt))
    assert result.stdout == b"".join(arg.encode("utf-8") + b"\0" for arg in expected)

    argv_file = tmp_path / "argv.nul"
    argv_file.write_bytes(result.stdout)
    read_back = subprocess.run(
        [
            "/bin/bash",
            "-c",
            'args=(); while IFS= read -r -d "" a; do args+=("$a"); done < "$1"; '
            'for a in "${args[@]}"; do printf "%s\\0" "$a"; done',
            "_",
            str(argv_file),
        ],
        capture_output=True,
        check=False,
    )
    assert read_back.returncode == 0, read_back.stderr
    assert read_back.stdout == result.stdout


def test_cli_print_argv_uses_the_requested_shape():
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "claude",
            "--prompt",
            "hi",
            "--agent",
            "principal-pm",
            "--shape",
            "print",
            "--print-argv",
        ],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    argv = tuple(part.decode() for part in result.stdout.split(b"\0")[:-1])
    assert argv == (
        "claude",
        "-p",
        "hi",
        "--agent",
        "principal-pm",
        "--permission-mode",
        "auto",
        "--permission-prompts",
        "none",
    )


def test_cli_turn_shape_carries_the_session_id():
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "claude",
            "--prompt",
            "hi",
            "--shape",
            "turn",
            "--session-id",
            "abc-123",
            "--instance-root",
            "/tmp/some-instance",
            "--print-argv",
        ],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    argv = tuple(part.decode() for part in result.stdout.split(b"\0")[:-1])
    assert argv == (
        "claude",
        "--print",
        "--output-format",
        "stream-json",
        "--verbose",
        "--session-id",
        "abc-123",
        "--permission-mode",
        "auto",
        "--permission-prompts",
        "none",
        "hi",
    )


def test_codex_command_is_unchanged():
    """Task 6 — the Codex adapter's argv is untouched for the existing requests, for every
    shape a `RunRequest` may now carry."""
    request = RunRequest(
        prompt="do the work", model="gpt-5.6-sol", add_dirs=("/first path", "/second")
    )
    baseline = CodexAdapter().command(request)
    assert baseline == (
        "codex",
        "exec",
        "--approve-for-me",
        "--model",
        "gpt-5.6-sol",
        "--add-dir",
        "/first path",
        "--add-dir",
        "/second",
        "do the work",
    )
    for shape in agent_run.Shape:
        assert CodexAdapter().command(replace(request, shape=shape)) == baseline


def test_no_pin_no_delivery():
    """Task 7 — with no pin, no shape carries any of the six delivery flags."""
    six_flags = {
        "--setting-sources",
        "--plugin-dir",
        "--settings",
        "--agents",
        "--append-system-prompt-file",
        "--add-dir",
    }
    for shape in agent_run.Shape:
        request = RunRequest(prompt="work", shape=shape, session_id="s-1")
        command = ClaudeAdapter().command(request)
        assert not any(_flag_count(command, flag) for flag in six_flags), (shape, command)


def test_with_a_pin_every_shape_carries_the_delivery(tmp_path, pins_home):
    """Task 7 — background, print, a turn start and a turn resume each carry every one of the
    six delivery flags exactly once."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    cases = (
        RunRequest(prompt="work", shape=agent_run.Shape.BACKGROUND, pin=made, instance_root=host),
        RunRequest(prompt="work", shape=agent_run.Shape.PRINT, pin=made, instance_root=host),
        RunRequest(
            prompt="work",
            shape=agent_run.Shape.TURN,
            session_id="s-1",
            pin=made,
            instance_root=host,
        ),
        RunRequest(
            prompt="next",
            shape=agent_run.Shape.TURN,
            resume_session_id="s-1",
            pin=made,
            instance_root=host,
        ),
    )
    for request in cases:
        command = ClaudeAdapter().command(request)
        for flag in ("--setting-sources", "--plugin-dir", "--settings", "--agents", "--add-dir"):
            assert _flag_count(command, flag) == 1, (request.shape, flag, command)
        assert _flag_value(command, "--setting-sources") == "user"
        assert _flag_value(command, "--add-dir") == str(made.root)


def test_the_plugin_links_every_owned_skill_once(tmp_path, pins_home):
    """Task 7 — flat and grouped pinned skills plus an instance-owned one appear under the
    plugin's `skills/`, with no name twice."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    sat = tmp_path / "sat"
    own_skill = sat / ".claude" / "skills" / "own-skill"
    own_skill.mkdir(parents=True)
    (own_skill / "SKILL.md").write_text("sat's own\n")

    command = ClaudeAdapter().command(
        RunRequest(prompt="work", pin=made, instance_root=sat, granted_skills=("grouped-skill",))
    )

    plugin_dir = Path(_flag_value(command, "--plugin-dir"))
    names = sorted(entry.name for entry in (plugin_dir / "skills").iterdir())
    assert names == sorted(["pinned-skill", "grouped-skill", "own-skill"])
    assert len(names) == len(set(names))


def _two_group_host(root: Path) -> Path:
    """The pin host plus a second group `grp-b` holding `other-skill`, so a grant to `grp` (which
    holds `grouped-skill`) has a group to not reach."""
    _build_pin_host(root)
    skill_dir = root / "skills" / "grp-b" / ".claude" / "skills" / "other-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("other skill\n")
    return root


def _plugin_skills(command):
    plugin_dir = Path(_flag_value(command, "--plugin-dir"))
    return sorted(entry.name for entry in (plugin_dir / "skills").iterdir())


def _granting(made, instance_root, *skills):
    return RunRequest(
        prompt="work", pin=made, instance_root=instance_root, granted_skills=tuple(skills)
    )


def test_grant_skill_is_repeatable_on_the_cli():
    args = agent_run.parser().parse_args(
        ["--provider", "claude", "--prompt", "p"]
        + ["--grant-skill", "first", "--grant-skill", "second"]
    )

    assert args.granted_skills == ["first", "second"]


def test_grant_skill_reaches_the_request_from_main(tmp_path, pins_home, capsys):
    host = _two_group_host(tmp_path / "host")
    made = pin.make(host, pins_home)

    code = agent_run.main(
        [
            "--provider", "claude", "--prompt", "p", "--pin", str(made.root),
            "--instance-root", str(host), "--grant-skill", "grouped-skill", "--print-argv",
        ]
    )

    assert code == 0
    command = capsys.readouterr().out.split("\0")
    assert _plugin_skills(command) == ["grouped-skill", "pinned-skill"]


def test_repeated_cli_grants_deliver_both_groups(tmp_path, pins_home, capsys):
    host = _two_group_host(tmp_path / "host")
    made = pin.make(host, pins_home)

    code = agent_run.main(
        [
            "--provider", "claude", "--prompt", "p", "--pin", str(made.root),
            "--instance-root", str(host), "--grant-skill", "grouped-skill",
            "--grant-skill", "other-skill", "--print-argv",
        ]
    )

    assert code == 0
    assert _plugin_skills(capsys.readouterr().out.split("\0")) == [
        "grouped-skill", "other-skill", "pinned-skill",
    ]


def test_group_set_key_ignores_grant_order_and_duplicates(tmp_path, pins_home):
    host = _two_group_host(tmp_path / "host")
    made = pin.make(host, pins_home)

    first = ClaudeAdapter().command(_granting(made, host, "grouped-skill", "other-skill"))
    second = ClaudeAdapter().command(
        _granting(made, host, "other-skill", "grouped-skill", "other-skill")
    )

    assert _flag_value(first, "--plugin-dir") == _flag_value(second, "--plugin-dir")
    assert _plugin_skills(second) == ["grouped-skill", "other-skill", "pinned-skill"]


def test_a_run_granted_one_group_lists_no_skill_of_another(tmp_path, pins_home):
    host = _two_group_host(tmp_path / "host")
    made = pin.make(host, pins_home)

    command = ClaudeAdapter().command(_granting(made, host, "grouped-skill"))

    assert _plugin_skills(command) == ["grouped-skill", "pinned-skill"]


def test_a_run_with_no_grant_lists_only_flat_and_instance_skills(tmp_path, pins_home):
    host = _two_group_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    sat = tmp_path / "sat"
    own_skill = sat / ".claude" / "skills" / "own-skill"
    own_skill.mkdir(parents=True)
    (own_skill / "SKILL.md").write_text("sat's own\n")

    command = ClaudeAdapter().command(_granting(made, sat))

    assert _plugin_skills(command) == ["own-skill", "pinned-skill"]


def test_two_grants_build_two_plugin_dirs_that_do_not_overwrite(tmp_path, pins_home):
    host = _two_group_host(tmp_path / "host")
    made = pin.make(host, pins_home)

    first = ClaudeAdapter().command(_granting(made, host, "grouped-skill"))
    second = ClaudeAdapter().command(_granting(made, host, "other-skill"))

    assert _flag_value(first, "--plugin-dir") != _flag_value(second, "--plugin-dir")
    assert _plugin_skills(first) == ["grouped-skill", "pinned-skill"]
    assert _plugin_skills(second) == ["other-skill", "pinned-skill"]


def test_the_same_grant_reuses_one_plugin_dir(tmp_path, pins_home):
    host = _two_group_host(tmp_path / "host")
    made = pin.make(host, pins_home)

    first = ClaudeAdapter().command(_granting(made, host, "grouped-skill"))
    second = ClaudeAdapter().command(_granting(made, host, "grouped-skill"))

    assert _flag_value(first, "--plugin-dir") == _flag_value(second, "--plugin-dir")


def test_grants_reaching_one_group_set_share_a_plugin_dir(tmp_path, pins_home):
    host = _two_group_host(tmp_path / "host")
    extra = host / "skills" / "grp" / ".claude" / "skills" / "second-in-grp"
    extra.mkdir(parents=True)
    (extra / "SKILL.md").write_text("second\n")
    made = pin.make(host, pins_home)

    first = ClaudeAdapter().command(_granting(made, host, "grouped-skill"))
    second = ClaudeAdapter().command(_granting(made, host, "second-in-grp"))

    assert _flag_value(first, "--plugin-dir") == _flag_value(second, "--plugin-dir")


def test_a_grant_reaching_no_group_shares_the_no_grant_plugin_dir(tmp_path, pins_home):
    host = _two_group_host(tmp_path / "host")
    made = pin.make(host, pins_home)

    none = ClaudeAdapter().command(_granting(made, host))
    flat = ClaudeAdapter().command(_granting(made, host, "pinned-skill"))

    assert _flag_value(none, "--plugin-dir") == _flag_value(flat, "--plugin-dir")


def test_every_shape_carries_the_six_delivery_flags_once_with_a_grant(tmp_path, pins_home):
    host = _two_group_host(tmp_path / "host")
    (host / "AGENTS.md").write_text("Instance routing instructions.\n")
    made = pin.make(host, pins_home)
    for shape in agent_run.Shape:
        request = replace(
            _granting(made, host, "grouped-skill"), shape=shape, session_id="s-1"
        )
        command = ClaudeAdapter().command(request)
        for flag in (
            "--setting-sources", "--plugin-dir", "--settings", "--agents",
            "--append-system-prompt-file", "--add-dir",
        ):
            assert _flag_count(command, flag) == 1, (shape, flag, command)
        assert _flag_value(command, "--add-dir") == str(made.root)
        assert _flag_value(command, "--setting-sources") == "user"
        instructions = Path(_flag_value(command, "--append-system-prompt-file"))
        assert instructions.read_text() == "Instance routing instructions.\n"
        without_grant = ClaudeAdapter().command(replace(request, granted_skills=()))
        for flag in ("--settings", "--agents", "--append-system-prompt-file"):
            assert _flag_value(command, flag) == _flag_value(without_grant, flag)


def test_codex_and_gemini_commands_are_unchanged_by_a_grant():
    request = RunRequest(prompt="do the work", model="a-model")
    granted = replace(request, granted_skills=("some-skill",))

    assert CodexAdapter().command(granted) == CodexAdapter().command(request)
    assert GeminiAdapter().command(granted) == GeminiAdapter().command(request)


def test_a_claude_run_with_no_pin_ignores_a_grant():
    request = RunRequest(prompt="work")

    assert ClaudeAdapter().command(replace(request, granted_skills=("some-skill",))) == (
        ClaudeAdapter().command(request)
    )


def test_the_plugin_links_the_pinned_workflows(tmp_path, pins_home):
    """Task 7 — the plugin's `workflows/` links the pin's own workflow entries."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)

    command = ClaudeAdapter().command(RunRequest(prompt="work", pin=made, instance_root=host))

    plugin_dir = Path(_flag_value(command, "--plugin-dir"))
    names = [entry.name for entry in (plugin_dir / "workflows").iterdir()]
    assert names == ["pinned-workflow"]


def test_hooks_in_the_merged_settings_point_into_the_pin(tmp_path, pins_home):
    """Task 7 — no `${CLAUDE_PROJECT_DIR}/.claude/hooks/` survives the merge, and each hook
    command names the pin's own `.claude/hooks/`."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)

    command = ClaudeAdapter().command(RunRequest(prompt="work", pin=made, instance_root=host))

    settings_path = Path(_flag_value(command, "--settings"))
    rendered = settings_path.read_text()
    assert "${CLAUDE_PROJECT_DIR}/.claude/hooks/" not in rendered
    assert str(made.root / ".claude" / "hooks") in rendered


def test_the_merged_settings_layer_in_order(tmp_path, pins_home):
    """Task 7 — pinned settings, then the instance's `settings.local.json`, then the caller's
    `--settings`, then the pin's env: an array concatenates without duplicates, an object merges
    key by key, and for a scalar the later layer wins."""
    host = _build_pin_host(tmp_path / "host")
    (host / ".claude" / "settings.json").write_text(
        json.dumps(
            {"permissions": {"allow": ["Bash(host:*)"], "defaultMode": "acceptEdits"}}
        )
    )
    made = pin.make(host, pins_home)
    sat = tmp_path / "sat"
    (sat / ".claude").mkdir(parents=True)
    (sat / ".claude" / "settings.local.json").write_text(
        json.dumps({"permissions": {"allow": ["Bash(sat:*)"], "defaultMode": "plan"}})
    )
    caller_settings = json.dumps(
        {
            "permissions": {
                "allow": ["Bash(host:*)", "Bash(caller:*)"],
                "defaultMode": "bypassPermissions",
            }
        }
    )

    command = ClaudeAdapter().command(
        RunRequest(prompt="work", pin=made, instance_root=sat, settings=caller_settings)
    )

    assert command.count("--settings") == 1
    merged = json.loads(Path(_flag_value(command, "--settings")).read_text())
    assert merged["permissions"]["allow"] == ["Bash(host:*)", "Bash(sat:*)", "Bash(caller:*)"]
    assert merged["permissions"]["defaultMode"] == "bypassPermissions"


@pytest.mark.parametrize(
    "shape", [agent_run.Shape.BACKGROUND, agent_run.Shape.PRINT, agent_run.Shape.TURN]
)
def test_every_pinned_run_carries_bg_isolation_none(tmp_path, pins_home, shape):
    """The pin's `settings.json` holds no `worktree` and the instance has no local file; the
    merged settings still hold `worktree.bgIsolation: none`, in every shape."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    assert "worktree" not in json.loads((made.root / ".claude" / "settings.json").read_text())

    command = ClaudeAdapter().command(
        RunRequest(prompt="work", pin=made, instance_root=host, shape=shape, session_id="s-1")
    )

    merged = json.loads(Path(_flag_value(command, "--settings")).read_text())
    assert merged["worktree"]["bgIsolation"] == "none"


def test_a_pins_own_bg_isolation_is_overridden_by_the_launch_layer(tmp_path, pins_home):
    """CP-458 — "whatever the pin's `settings.json` ... hold[s]": a pin whose tracked settings set
    another `bgIsolation` still launches with `none`, because the launch layer comes after it."""
    host = _build_pin_host(tmp_path / "host")
    settings_path = host / ".claude" / "settings.json"
    document = json.loads(settings_path.read_text())
    document["worktree"] = {"bgIsolation": "worktree"}
    settings_path.write_text(json.dumps(document))
    made = pin.make(host, pins_home)
    assert json.loads((made.root / ".claude" / "settings.json").read_text())["worktree"] == {
        "bgIsolation": "worktree"
    }

    command = ClaudeAdapter().command(RunRequest(prompt="work", pin=made, instance_root=host))

    merged = json.loads(Path(_flag_value(command, "--settings")).read_text())
    assert merged["worktree"]["bgIsolation"] == "none"


def test_an_instance_local_bg_isolation_wins(tmp_path, pins_home):
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    sat = tmp_path / "sat"
    (sat / ".claude").mkdir(parents=True)
    (sat / ".claude" / "settings.local.json").write_text(
        json.dumps({"worktree": {"bgIsolation": "worktree"}})
    )

    command = ClaudeAdapter().command(RunRequest(prompt="work", pin=made, instance_root=sat))

    merged = json.loads(Path(_flag_value(command, "--settings")).read_text())
    assert merged["worktree"]["bgIsolation"] == "worktree"


def test_a_caller_bg_isolation_wins(tmp_path, pins_home):
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    sat = tmp_path / "sat"
    (sat / ".claude").mkdir(parents=True)
    (sat / ".claude" / "settings.local.json").write_text(
        json.dumps({"worktree": {"bgIsolation": "worktree"}})
    )

    command = ClaudeAdapter().command(
        RunRequest(
            prompt="work",
            pin=made,
            instance_root=sat,
            settings=json.dumps({"worktree": {"bgIsolation": "caller"}}),
        )
    )

    merged = json.loads(Path(_flag_value(command, "--settings")).read_text())
    assert merged["worktree"]["bgIsolation"] == "caller"


def test_the_pins_env_reaches_the_merged_settings(tmp_path, pins_home):
    """Task 7 — the merged settings' `env` holds `KENSAIAPP_PIN` and the `GIT_CONFIG_*` triple."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)

    command = ClaudeAdapter().command(RunRequest(prompt="work", pin=made, instance_root=host))

    merged = json.loads(Path(_flag_value(command, "--settings")).read_text())
    assert merged["env"]["KENSAIAPP_PIN"] == str(made.root)
    assert merged["env"]["GIT_CONFIG_KEY_0"] == "core.hooksPath"
    assert merged["env"]["GIT_CONFIG_VALUE_0"] == str(made.root / "core" / "githooks")
    assert merged["env"]["GIT_CONFIG_COUNT"] == "1"


def test_agents_inline_carry_every_owned_agent(tmp_path, pins_home):
    """Task 7 — the `--agents` JSON parses, each entry has `description` and `prompt` (plus
    `tools` and `model` where the file declares them), and an instance-owned agent replaces the
    pinned one of the same name."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    sat = tmp_path / "sat"
    (sat / ".claude" / "agents").mkdir(parents=True)
    (sat / ".claude" / "agents" / "shared-agent.md").write_text(
        "---\n"
        "name: shared-agent\n"
        "description: The instance's own shared-agent.\n"
        "---\n\n"
        "Instance body."
    )

    command = ClaudeAdapter().command(RunRequest(prompt="work", pin=made, instance_root=sat))

    agents = json.loads(_flag_value(command, "--agents"))
    assert set(agents) == {"pinned-agent", "shared-agent"}
    assert agents["pinned-agent"] == {
        "description": "A host agent.",
        "prompt": "You are the pinned agent.",
        "tools": ["Read", "Grep"],
        "model": "sonnet",
    }
    assert agents["shared-agent"] == {
        "description": "The instance's own shared-agent.",
        "prompt": "Instance body.",
    }


def _group_agent(root: Path, name: str, description: str, group: str | None = None) -> Path:
    """The agent `name` at `skills/<group>/.claude/agents/<name>.md` under `root`."""
    path = root / "skills" / (group or name) / ".claude" / "agents" / f"{name}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nname: {name}\ndescription: {description}\n---\n\nBody of {name}.")
    return path


def _build_grouped_agent_host(root: Path) -> Path:
    """A host whose agents all live in groups: `pm` beside a skill, `qa` and `delegate` alone in
    their groups, a group holding only a skill, and an empty tracked `.claude/agents/`."""
    _build_pin_host(root)
    for flat in (root / ".claude" / "agents").glob("*.md"):
        flat.unlink()
    (root / ".claude" / "agents" / ".gitkeep").write_text("")
    _group_agent(root, "pm", "The pm.")
    pm_skill = root / "skills" / "pm" / ".claude" / "skills" / "pm-skill"
    pm_skill.mkdir(parents=True)
    (pm_skill / "SKILL.md").write_text("pm skill\n")
    _group_agent(root, "qa", "The qa.")
    _group_agent(root, "delegate", "The delegate.")
    lone_skill = root / "skills" / "only-skill" / ".claude" / "skills" / "lone"
    lone_skill.mkdir(parents=True)
    (lone_skill / "SKILL.md").write_text("lone\n")
    return root


def test_pinned_claude_run_agents_json_names_every_grouped_agent(tmp_path, pins_home):
    """CP-40 — a run granted one skill, from `skills/pm/`, still carries every grouped agent,
    the one in a skill-less group included, and no entry for the `.gitkeep`."""
    host = _build_grouped_agent_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    sat = tmp_path / "sat"
    sat.mkdir()

    command = ClaudeAdapter().command(
        RunRequest(prompt="work", pin=made, instance_root=sat, granted_skills=("pm-skill",))
    )

    agents = json.loads(_flag_value(command, "--agents"))
    assert set(agents) == {"pm", "qa", "delegate"}


def test_instance_own_agent_replaces_its_agents_entry(tmp_path, pins_home):
    """CP-40, CP-38 — an instance's own `.claude/agents/pm.md` replaces the grouped `pm` entry
    and adds nothing else."""
    host = _build_grouped_agent_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    sat = tmp_path / "sat"
    (sat / ".claude" / "agents").mkdir(parents=True)
    (sat / ".claude" / "agents" / "pm.md").write_text(
        "---\nname: pm\ndescription: The instance's own pm.\n---\n\nInstance body."
    )

    command = ClaudeAdapter().command(RunRequest(prompt="work", pin=made, instance_root=sat))

    agents = json.loads(_flag_value(command, "--agents"))
    assert set(agents) == {"pm", "qa", "delegate"}
    assert agents["pm"] == {"description": "The instance's own pm.", "prompt": "Instance body."}


@pytest.mark.parametrize(
    "adapter_class, provider", [(CodexAdapter, "codex"), (GeminiAdapter, "gemini")]
)
def test_codex_unpinned_agent_sentence_names_host_group_file(tmp_path, adapter_class, provider):
    """No pin, an instance that holds no `skills/`, the agent in the host's group: the sentence
    names the host's group file."""
    host = tmp_path / "host"
    group_file = _group_agent(host, "pm", "The pm.")
    sat = tmp_path / "sat"
    sat.mkdir()
    request = RunRequest(prompt="work", agent="pm", instance_root=sat)

    sentence, _ = agent_run._codex_agent_context(request, None, provider, host_root=host)

    assert str(group_file.resolve()) in sentence


def test_instance_instructions_are_the_instances_and_absent_when_missing(tmp_path, pins_home):
    """Task 7 — `--append-system-prompt-file` is absent until the instance holds an `AGENTS.md`,
    then names one file carrying the instance's own routing and identity (read live, not the
    pin's), in that order."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)

    without = ClaudeAdapter().command(RunRequest(prompt="work", pin=made, instance_root=host))
    assert "--append-system-prompt-file" not in without

    (host / "AGENTS.md").write_text("Own routing.\n")
    routing_only = ClaudeAdapter().command(RunRequest(prompt="work", pin=made, instance_root=host))
    appended = Path(_flag_value(routing_only, "--append-system-prompt-file"))
    assert appended.read_text() == "Own routing.\n"

    (host / "kensaiapp.md").write_text("Own identity.\n")
    both = ClaudeAdapter().command(RunRequest(prompt="work", pin=made, instance_root=host))
    appended = Path(_flag_value(both, "--append-system-prompt-file"))
    assert appended.read_text() == "Own routing.\n\nOwn identity.\n"
    assert made.root in appended.parents


def test_a_single_file_instance_gets_its_claude_md_whatever_sits_beside_it(tmp_path, pins_home):
    """An instance with no `kensaiapp.md` is on the single-file layout: its `CLAUDE.md` is the
    whole of its instructions and is appended as-is — also when an `AGENTS.md` sits beside it,
    which on that layout is only a pointer back at `CLAUDE.md`."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)

    (host / "CLAUDE.md").write_text("Whole instructions.\n")
    alone = ClaudeAdapter().command(RunRequest(prompt="work", pin=made, instance_root=host))
    assert _flag_value(alone, "--append-system-prompt-file") == str(host / "CLAUDE.md")

    (host / "AGENTS.md").write_text("Read and follow CLAUDE.md.\n")
    beside = ClaudeAdapter().command(RunRequest(prompt="work", pin=made, instance_root=host))
    assert _flag_value(beside, "--append-system-prompt-file") == str(host / "CLAUDE.md")


def test_the_import_line_is_not_what_a_pinned_run_is_handed(tmp_path, pins_home):
    """On the pair layout `CLAUDE.md` is one import line, which an appended file would carry as
    inert text — the run is handed the routing and the identity themselves."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    (host / "CLAUDE.md").write_text("@AGENTS.md\n")
    (host / "AGENTS.md").write_text("Own routing.\n")
    (host / "kensaiapp.md").write_text("Own identity.\n")

    command = ClaudeAdapter().command(RunRequest(prompt="work", pin=made, instance_root=host))

    appended = Path(_flag_value(command, "--append-system-prompt-file"))
    assert appended.read_text() == "Own routing.\n\nOwn identity.\n"


def test_pin_auto_reads_the_inherited_pin(tmp_path, pins_home):
    """Task 7 — `--pin auto` resolves through `pin.inherited(os.environ)`."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    env = dict(os.environ)
    env["KENSAIAPP_PIN"] = str(made.root)

    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "claude",
            "--prompt",
            "work",
            "--pin",
            "auto",
            "--instance-root",
            str(host),
            "--print-argv",
        ],
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    argv = tuple(part.decode() for part in result.stdout.split(b"\0")[:-1])
    assert "--plugin-dir" in argv


def test_pin_explicit_root_is_used_directly(tmp_path, pins_home):
    """Task 7 — `--pin <root>` resolves that literal root rather than the inherited one, the
    discriminating case against `--pin auto`'s own branch."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)

    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "claude",
            "--prompt",
            "work",
            "--pin",
            str(made.root),
            "--instance-root",
            str(host),
            "--print-argv",
        ],
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    argv = tuple(part.decode() for part in result.stdout.split(b"\0")[:-1])
    assert _flag_value(argv, "--add-dir") == str(made.root)


def test_pin_auto_with_a_missing_pin_exits_non_zero(tmp_path):
    """Task 7 — `--pin auto` against a `KENSAIAPP_PIN` naming no complete pin exits non-zero and
    launches nothing."""
    env = dict(os.environ)
    env["KENSAIAPP_PIN"] = str(tmp_path / "gone")

    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "claude",
            "--prompt",
            "work",
            "--pin",
            "auto",
        ],
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode != 0
    assert result.stdout == b""


def test_cli_refuses_a_codex_run_with_a_claude_only_field():
    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "codex",
            "--prompt",
            "work",
            "--agent",
            "developer",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert result.stderr == (
        "agent-run: provider 'codex' needs an instance root to find agent 'developer'\n"
    )


def test_cli_serves_a_codex_agent(tmp_path):
    sat = tmp_path / "sat"
    _init_instance_agent(sat, "dev")

    result = subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--provider",
            "codex",
            "--agent",
            "dev",
            "--instance-root",
            str(sat),
            "--prompt",
            "work",
            "--dry-run",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "You are running as the dev agent." in result.stdout


# --- development-code-integrity: cases the spec states that the branch left untested ---------


def test_codex_settings_refuses_an_env_name_with_a_trailing_newline():
    """CP-133 — a name that does not match `[A-Za-z_][A-Za-z0-9_]*` is refused. `A\\n` does not
    match it: the newline is not in the class."""
    try:
        CodexAdapter().command(RunRequest(prompt="work", settings='{"env":{"A\\n":"v"}}'))
    except agent_run.UnsupportedRequest as error:
        assert str(error) == (
            "provider 'codex' settings must be a JSON object whose env maps "
            "variable names to strings"
        )
    else:
        raise AssertionError("Codex accepted an env name ending in a newline")


def test_codex_generic_refusal_never_lists_agent_or_settings():
    """CP-135 — the generic refusal lists only `name` / `add_dirs on resume`, never `agent` or
    `settings`, even when the request carries both beside `name`."""
    request = RunRequest(prompt="work", agent="dev", settings='{"env":{"A":"1"}}', name="n")

    try:
        CodexAdapter().command(request)
    except agent_run.UnsupportedRequest as error:
        assert str(error) == "provider 'codex' does not support request fields: name"
    else:
        raise AssertionError("Codex accepted a name")


def test_codex_agent_falls_back_to_the_pins_file(tmp_path, pins_home):
    """CP-128 — under a pin, an agent the instance does not hold is the pin's; its `model:` line
    (`sonnet`) sets no model."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    sat = tmp_path / "sat"
    sat.mkdir()

    command = CodexAdapter().command(
        RunRequest(prompt="work", agent="pinned-agent", instance_root=sat, pin=made)
    )

    sentence = command[-1]
    named = sentence.split(" Read ", 1)[1].split(" in full ", 1)[0]
    assert Path(named).is_absolute()
    assert Path(named).is_relative_to(made.root.resolve())
    assert Path(named).name == "pinned-agent.md"
    assert "--model" not in command


def test_codex_agent_file_is_absolute_from_a_relative_instance_root(tmp_path, monkeypatch):
    """CP-127 — `<agent file>` is the absolute path, whatever form the instance root came in."""
    agent_path = _init_instance_agent(tmp_path / "sat", "dev")
    monkeypatch.chdir(tmp_path)

    command = CodexAdapter().command(
        RunRequest(prompt="work", agent="dev", instance_root=Path("sat"))
    )

    assert command[-1].startswith(
        f"You are running as the dev agent. Read {agent_path.resolve()} in full "
    )


def test_codex_settings_env_reaches_the_detached_process(tmp_path):
    """CP-131 — background: the process actually started carries the `env` prefix."""
    processes = FakeProcesses()
    runner = AgentRunner({"codex": CodexAdapter()}, processes)

    runner.background(
        "codex", RunRequest(prompt="work", settings='{"env":{"A":"1"}}'), tmp_path / "run.jsonl"
    )

    (argv, _), = processes.detached_calls
    assert argv[:4] == ("env", "A=1", "codex", "exec")


def test_codex_settings_env_reaches_the_foreground_process():
    """CP-131 — foreground: the process run carries the `env` prefix."""
    processes = FakeProcesses()
    runner = AgentRunner({"codex": CodexAdapter()}, processes)

    runner.run("codex", RunRequest(prompt="work", settings='{"env":{"A":"1"}}'))

    assert processes.calls[0][:4] == ("env", "A=1", "codex", "exec")


def _run_cli(*args):
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args], capture_output=True, check=False
    )


def test_cli_print_argv_shows_the_codex_settings_env():
    """CP-131 — `--print-argv` shows `env`, then `KEY=value`, then the Codex command."""
    result = _run_cli(
        "--provider", "codex", "--prompt", "work", "--settings", '{"env":{"A":"1"}}',
        "--print-argv",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.split(b"\0")[:4] == [b"env", b"A=1", b"codex", b"exec"]


def test_cli_refuses_a_codex_agent_with_no_file(tmp_path):
    """CP-130 — no agent file: exit 2, nothing on stdout, one stderr line naming the agent."""
    sat = tmp_path / "sat"
    sat.mkdir()

    result = _run_cli(
        "--provider", "codex", "--agent", "ghost", "--instance-root", str(sat),
        "--prompt", "work", "--dry-run",
    )

    assert result.returncode == 2
    assert result.stdout == b""
    assert result.stderr.decode() == (
        f"agent-run: provider 'codex' found no agent file for 'ghost' under {sat}\n"
    )


# --- Task 1 — effort ---


def test_cli_help_lists_effort():
    """CP-136 — `--effort` is a documented CLI flag."""
    result = _run_cli("--help")

    assert result.returncode == 0, result.stderr
    assert b"--effort" in result.stdout


def test_cli_refuses_an_effort_outside_the_three():
    """CP-136 — any value outside low/medium/high exits 2 with nothing on stdout."""
    result = _run_cli(
        "--provider", "claude", "--prompt", "x", "--effort", "extreme", "--dry-run",
    )

    assert result.returncode == 2
    assert result.stdout == b""


@pytest.mark.parametrize(
    "shape_args",
    [
        ("--shape", "background"),
        ("--shape", "print"),
        ("--shape", "turn", "--session-id", "s1"),
        ("--shape", "turn", "--resume-session", "s1"),
    ],
    ids=["background", "print", "turn-started", "turn-resumed"],
)
@pytest.mark.parametrize("mode", ["--dry-run", "--print-argv"])
def test_cli_claude_effort_appears_once_in_every_shape(shape_args, mode):
    """CP-137, CP-140 — `--effort` occurs exactly once, in every claude shape, under both
    `--dry-run` and `--print-argv`."""
    result = _run_cli(
        "--provider", "claude", "--prompt", "hi", "--effort", "low", *shape_args, mode,
    )

    assert result.returncode == 0, result.stderr
    if mode == "--dry-run":
        argv = tuple(shlex.split(result.stdout.decode()))
    else:
        argv = tuple(part.decode() for part in result.stdout.split(b"\0")[:-1])
    assert argv.count("--effort") == 1
    assert argv[argv.index("--effort") + 1] == "low"


def test_cli_claude_background_resume_carries_effort_once():
    """CP-137 — `--shape background --resume-session s1 --effort medium` carries one flag."""
    result = _run_cli(
        "--provider", "claude", "--prompt", "hi", "--shape", "background",
        "--resume-session", "s1", "--effort", "medium", "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    argv = tuple(shlex.split(result.stdout.decode()))
    assert argv.count("--effort") == 1
    assert argv[argv.index("--effort") + 1] == "medium"


def test_cli_claude_without_effort_carries_no_effort_token():
    """CP-137 — no `--effort` in, no `--effort` out. Byte-equality with today is held by the
    existing exact-argv tests, unmodified."""
    result = _run_cli("--provider", "claude", "--prompt", "hi", "--dry-run")

    assert result.returncode == 0, result.stderr
    assert "--effort" not in result.stdout.decode()


def test_a_python_request_with_effort_reaches_every_claude_shape():
    """Held below the CLI too, at the adapter level, so a Python caller that builds a
    `RunRequest` directly (never through the CLI) still gets `--effort` in every shape."""
    requests = [
        RunRequest(prompt="work", effort=agent_run.Effort.HIGH, shape=agent_run.Shape.BACKGROUND),
        RunRequest(
            prompt="work", effort=agent_run.Effort.HIGH, shape=agent_run.Shape.BACKGROUND,
            resume_session_id="s1",
        ),
        RunRequest(prompt="work", effort=agent_run.Effort.HIGH, shape=agent_run.Shape.PRINT),
        RunRequest(
            prompt="work", effort=agent_run.Effort.HIGH, shape=agent_run.Shape.PRINT,
            resume_session_id="s1",
        ),
        RunRequest(
            prompt="work", effort=agent_run.Effort.HIGH, shape=agent_run.Shape.TURN,
            session_id="s1",
        ),
        RunRequest(
            prompt="work", effort=agent_run.Effort.HIGH, shape=agent_run.Shape.TURN,
            resume_session_id="s1",
        ),
    ]
    for request in requests:
        command = ClaudeAdapter().command(request)
        assert command.count("--effort") == 1
        assert command[command.index("--effort") + 1] == "high"


def test_codex_request_effort_replaces_the_tiers_level():
    """CP-138 — `--model-tier opus --effort low`: `model_reasoning_effort="low"` exactly once,
    `model_reasoning_effort="high"` absent (opus's own tier level)."""
    result = _run_cli(
        "--provider", "codex", "--prompt", "work", "--model-tier", "opus",
        "--effort", "low", "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    out = result.stdout.decode()
    assert out.count('model_reasoning_effort="low"') == 1
    assert 'model_reasoning_effort="high"' not in out


def test_codex_effort_equal_to_the_tiers_is_emitted_once():
    """CP-138 — `--model-tier opus --effort high`: `model_reasoning_effort` occurs once even
    though the request's effort and the tier's own level agree."""
    result = _run_cli(
        "--provider", "codex", "--prompt", "work", "--model-tier", "opus",
        "--effort", "high", "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.decode().count("model_reasoning_effort") == 1


def test_codex_effort_with_no_tier_model_or_agent_emits_the_setting_and_no_model():
    """CP-138 — `--effort medium` alone: the setting appears and no `--model` does."""
    result = _run_cli(
        "--provider", "codex", "--prompt", "work", "--effort", "medium", "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    out = result.stdout.decode()
    assert 'model_reasoning_effort="medium"' in out
    assert "--model" not in out


def test_codex_effort_on_resume_and_in_background_is_emitted_once(tmp_path):
    """CP-138, CP-140 — `--effort low` on `--resume-session` and under `--background` (the
    `--json` path) each carry the level exactly once."""
    resumed = CodexAdapter().command(
        RunRequest(prompt="next", resume_session_id="t1", effort=agent_run.Effort.LOW)
    )
    assert resumed.count('model_reasoning_effort="low"') == 1

    result = _run_cli(
        "--provider", "codex", "--prompt", "work", "--effort", "low",
        "--background", "--log", str(tmp_path / "run.jsonl"), "--dry-run",
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.decode().count('model_reasoning_effort="low"') == 1


def test_cli_codex_print_argv_carries_the_request_effort_once():
    """CP-140 — `--print-argv` shows the codex command CP-138 describes, as `--dry-run` does:
    one reasoning setting, the request's level, over the tier's."""
    result = _run_cli(
        "--provider", "codex", "--prompt", "work", "--model-tier", "opus",
        "--effort", "low", "--print-argv",
    )

    assert result.returncode == 0, result.stderr
    argv = [part.decode() for part in result.stdout.split(b"\0")[:-1]]
    settings = [arg for arg in argv if arg.startswith("model_reasoning_effort=")]
    assert settings == ['model_reasoning_effort="low"']


def _runtime_core(tmp_path):
    core = tmp_path / "core"
    (core / "doctrine").mkdir(parents=True)
    (core / "doctrine" / "task_map.md").write_text("", encoding="utf-8")
    return core


def test_codex_explicit_effort_reaches_provider_and_runtime_attribution(tmp_path):
    command = CodexAdapter().command(RunRequest(
        prompt="work", model_tier="opus", effort=agent_run.Effort.LOW,
        core_root=_runtime_core(tmp_path),
    ))

    assert command.count('model_reasoning_effort="low"') == 1
    assert 'model_reasoning_effort="high"' not in command
    assert command[-1].count('`--reasoning-effort "low"`') == 1


def test_codex_tier_xhigh_reaches_provider_and_runtime_attribution(tmp_path):
    command = CodexAdapter().command(RunRequest(
        prompt="work", model_tier="fable", core_root=_runtime_core(tmp_path),
    ))

    assert command.count('model_reasoning_effort="xhigh"') == 1
    assert command[-1].count('`--reasoning-effort "xhigh"`') == 1


@pytest.mark.parametrize("background,resume", ((False, False), (False, True), (True, False), (True, True)))
def test_codex_fresh_resume_foreground_and_background_share_the_resolved_effort(tmp_path, background, resume):
    request = RunRequest(
        prompt="work", model_tier="opus", effort=agent_run.Effort.LOW,
        core_root=_runtime_core(tmp_path), resume_session_id="thread-1" if resume else None,
    )
    command = CodexAdapter().background_command(request) if background else CodexAdapter().command(request)

    assert command.count('model_reasoning_effort="low"') == 1
    assert command[-1].count('`--reasoning-effort "low"`') == 1


def test_codex_explicit_model_without_effort_omits_the_builder_instruction(tmp_path):
    command = CodexAdapter().command(RunRequest(
        prompt="work", model="gpt-explicit", core_root=_runtime_core(tmp_path),
    ))

    assert 'gpt-explicit <noreply@openai.com>' in command[-1]
    assert "--reasoning-effort" not in command[-1]


def test_codex_effort_attribution_changes_only_the_prompt_text(tmp_path):
    request = RunRequest(prompt="work", model_tier="opus", effort=agent_run.Effort.LOW)
    without_context = CodexAdapter().command(request)
    with_context = CodexAdapter().command(
        replace(request, core_root=_runtime_core(tmp_path))
    )

    assert without_context[:-1] == with_context[:-1]


def test_claude_commands_remain_free_of_codex_effort_attribution(tmp_path):
    core = _runtime_core(tmp_path)
    requests = (
        RunRequest(prompt="work", effort=agent_run.Effort.LOW, core_root=core),
        RunRequest(
            prompt="work", effort=agent_run.Effort.LOW, core_root=core,
            shape=agent_run.Shape.PRINT,
        ),
        RunRequest(
            prompt="work", effort=agent_run.Effort.LOW, core_root=core,
            shape=agent_run.Shape.TURN, session_id="s-1",
        ),
    )
    commands = []
    for request in requests:
        commands.append(ClaudeAdapter().command(request))
        commands.append(ClaudeAdapter().background_command(request))

    for command in commands:
        rendered = " ".join(command)
        assert "Execution surface: Codex" not in rendered
        assert "`--surface Codex`" not in rendered


# ── A Claude launch tells its run the level it resolved ──


def _effort_sentence(level):
    """The effort sentence as the change's spec writes it — the test's own copy, never read
    back from `task_context`."""
    return (
        f'Pass `--reasoning-effort "{level}"` to the builder; '
        "the launch already resolved this value."
    )


# Every shape a `claude` command is built in, as the `RunRequest` fields that select it.
_CLAUDE_SHAPES = {
    "background": {},
    "print": {"shape": agent_run.Shape.PRINT},
    "turn-started": {"shape": agent_run.Shape.TURN, "session_id": "s-1"},
    "turn-resumed": {"shape": agent_run.Shape.TURN, "resume_session_id": "s1"},
    "background-resuming": {"resume_session_id": "s1"},
    "print-resuming": {"shape": agent_run.Shape.PRINT, "resume_session_id": "s1"},
}
_every_claude_shape = pytest.mark.parametrize(
    "shape", list(_CLAUDE_SHAPES.values()), ids=list(_CLAUDE_SHAPES)
)
_both_renders = pytest.mark.parametrize("render", ("command", "background_command"))
_core_root_given_and_absent = pytest.mark.parametrize(
    "core_root_given", (False, True), ids=("no-core-root", "core-root")
)


def _claude_command(render, tmp_path, *, core_root_given, **fields):
    core_root = _runtime_core(tmp_path) if core_root_given else None
    return getattr(ClaudeAdapter(), render)(
        RunRequest(prompt="work", core_root=core_root, **fields)
    )


@_every_claude_shape
@_both_renders
@pytest.mark.parametrize("level", list(agent_run.Effort), ids=lambda level: level.value)
@_core_root_given_and_absent
def test_claude_command_with_effort_carries_the_sentence_exactly_once(
    tmp_path, shape, render, level, core_root_given
):
    command = _claude_command(
        render, tmp_path, core_root_given=core_root_given, effort=level, **shape
    )
    level_after_the_flag = command[command.index("--effort") + 1]

    # One argument and its whole value: an omitted sentence leaves the list empty, a doubled
    # one or one naming another level makes the value differ.
    assert [argument for argument in command if "--reasoning-effort" in argument] == [
        f"work {_effort_sentence(level_after_the_flag)}"
    ]
    assert level_after_the_flag == level.value


_MAX_PROMPT = f"work {_effort_sentence('max')}"
_DETACHED_ENV = (
    "env",
    "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1",
    "BASH_DEFAULT_TIMEOUT_MS=600000",
    "BASH_MAX_TIMEOUT_MS=21600000",
    "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0",
)
_TURN_HEAD = ("claude", "--print", "--output-format", "stream-json", "--verbose")
_TURN_TAIL = ("--effort", "max", "--permission-mode", "auto", "--permission-prompts", "none")
_FLAGS_AFTER_THE_PROMPT = ("--effort", "max", "--permission-mode", "auto")
# `print` has since gained `--permission-prompts none` (2026-10-19); `background` has not.
_PRINT_FLAGS_AFTER_THE_PROMPT = (*_FLAGS_AFTER_THE_PROMPT, "--permission-prompts", "none")
# The argv each shape had before this change, measured on the pre-change tree with prompt
# `work` and effort `max`, with only the prompt element replaced.
_ARGV_AT_MAX = {
    "background": ("claude", "--bg", _MAX_PROMPT, *_FLAGS_AFTER_THE_PROMPT),
    "print": ("claude", "-p", _MAX_PROMPT, *_PRINT_FLAGS_AFTER_THE_PROMPT),
    "turn-started": (*_TURN_HEAD, "--session-id", "s-1", *_TURN_TAIL, _MAX_PROMPT),
    "turn-resumed": (*_TURN_HEAD, "--resume", "s1", *_TURN_TAIL, _MAX_PROMPT),
    "background-resuming": (
        "claude", "--bg", "--resume", "s1", _MAX_PROMPT, *_FLAGS_AFTER_THE_PROMPT,
    ),
    "print-resuming": (
        "claude", "-p", "--resume", "s1", _MAX_PROMPT, *_PRINT_FLAGS_AFTER_THE_PROMPT,
    ),
}
# `claude --bg` detaches itself; every other shape is detached by this tool, behind its `env`.
_SELF_DETACHING = ("background", "background-resuming")


@pytest.mark.parametrize("name", list(_CLAUDE_SHAPES))
def test_claude_argv_equals_todays_with_only_the_prompt_element_replaced(name):
    request = RunRequest(prompt="work", effort=agent_run.Effort.MAX, **_CLAUDE_SHAPES[name])
    detached_prefix = () if name in _SELF_DETACHING else _DETACHED_ENV

    assert ClaudeAdapter().command(request) == _ARGV_AT_MAX[name]
    assert ClaudeAdapter().background_command(request) == (*detached_prefix, *_ARGV_AT_MAX[name])


_XHIGH_PROMPT = f"do it {_effort_sentence('xhigh')}"
_LOADED_FIELDS = dict(
    agent="cpo", name="run-1", model="claude-opus-x", add_dirs=("/a", "/b"), settings="/s.json",
)
_LOADED_FLAGS_AFTER_THE_PROMPT = (
    "--agent", "cpo", "--model", "claude-opus-x", "--effort", "xhigh",
    "--permission-mode", "auto", "--add-dir=/a", "--add-dir=/b", "--settings", "/s.json",
)
_LOADED_PRINT_FLAGS_AFTER_THE_PROMPT = (
    "--agent", "cpo", "--model", "claude-opus-x", "--effort", "xhigh",
    "--permission-mode", "auto", "--permission-prompts", "none",
    "--add-dir=/a", "--add-dir=/b", "--settings", "/s.json",
)
_LOADED_TURN_TAIL = (
    "--model", "claude-opus-x", "--effort", "xhigh",
    "--permission-mode", "auto", "--permission-prompts", "none",
)
# The argv each shape had before this change for a launch that sets every optional field,
# measured on the pre-change tree (98c30e09a) with prompt `do it` and effort `xhigh`, with only
# the prompt element replaced. The bare requests above leave most flags out, so they cannot see
# one that moved or changed value.
_LOADED_ARGV_AT_XHIGH = {
    "background": (
        "claude", "--bg", "--name", "run-1", _XHIGH_PROMPT, *_LOADED_FLAGS_AFTER_THE_PROMPT,
    ),
    "print": (
        "claude", "-p", "--name", "run-1", _XHIGH_PROMPT, *_LOADED_PRINT_FLAGS_AFTER_THE_PROMPT,
    ),
    "turn-started": (
        *_TURN_HEAD, "--session-id", "s-1", "--name", "run-1", "--agent", "cpo",
        *_LOADED_TURN_TAIL, "--add-dir=/a", "--add-dir=/b", "--settings", "/s.json",
        _XHIGH_PROMPT,
    ),
    "turn-resumed": (*_TURN_HEAD, "--resume", "s1", *_LOADED_TURN_TAIL, _XHIGH_PROMPT),
    "background-resuming": (
        "claude", "--bg", "--name", "run-1", "--resume", "s1", _XHIGH_PROMPT,
        *_LOADED_FLAGS_AFTER_THE_PROMPT,
    ),
    "print-resuming": (
        "claude", "-p", "--name", "run-1", "--resume", "s1", _XHIGH_PROMPT,
        *_LOADED_PRINT_FLAGS_AFTER_THE_PROMPT,
    ),
}


@pytest.mark.parametrize("name", list(_CLAUDE_SHAPES))
def test_a_fully_loaded_claude_argv_equals_todays_with_only_the_prompt_element_replaced(name):
    request = RunRequest(
        prompt="do it", effort=agent_run.Effort.XHIGH, **_LOADED_FIELDS, **_CLAUDE_SHAPES[name]
    )
    detached_prefix = () if name in _SELF_DETACHING else _DETACHED_ENV

    assert ClaudeAdapter().command(request) == _LOADED_ARGV_AT_XHIGH[name]
    assert ClaudeAdapter().background_command(request) == (
        *detached_prefix, *_LOADED_ARGV_AT_XHIGH[name],
    )


def test_claude_prompt_argument_keeps_an_awkward_prompt_byte_for_byte():
    prompt = "  spaces \"double\" 'single' $DOLLAR `backtick` and\n\nnewlines  \n"

    for shape in _CLAUDE_SHAPES.values():
        command = ClaudeAdapter().command(
            RunRequest(prompt=prompt, effort=agent_run.Effort.XHIGH, **shape)
        )

        assert f"{prompt} {_effort_sentence('xhigh')}" in command
        assert prompt not in command


@pytest.mark.parametrize(
    "shape_args",
    [
        ("--shape", "background"),
        ("--shape", "print"),
        ("--shape", "turn", "--session-id", "s1"),
        ("--shape", "turn", "--resume-session", "s1"),
        ("--shape", "background", "--resume-session", "s1"),
        ("--shape", "print", "--resume-session", "s1"),
    ],
    ids=list(_CLAUDE_SHAPES),
)
@pytest.mark.parametrize("mode", ["--dry-run", "--print-argv"])
def test_dry_run_and_print_argv_carry_the_sentence_once_in_every_shape(shape_args, mode):
    result = _run_cli(
        "--provider", "claude", "--prompt", "hi", "--effort", "low", *shape_args, mode,
    )

    assert result.returncode == 0, result.stderr
    if mode == "--dry-run":
        argv = tuple(shlex.split(result.stdout.decode()))
    else:
        argv = tuple(part.decode() for part in result.stdout.split(b"\0")[:-1])
    assert [argument for argument in argv if "--reasoning-effort" in argument] == [
        f"hi {_effort_sentence('low')}"
    ]


@_every_claude_shape
def test_pin_in_force_carries_the_sentence_once_and_pin_delivery_follows_the_argv(
    tmp_path, pins_home, shape
):
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    pinned = RunRequest(
        prompt="work", effort=agent_run.Effort.HIGH, pin=made, instance_root=host, **shape
    )
    unpinned = replace(pinned, pin=None)

    command = ClaudeAdapter().command(pinned)
    shape_argv = ClaudeAdapter().command(unpinned)
    delivery = command[len(shape_argv):]

    assert command[:len(shape_argv)] == shape_argv
    assert [argument for argument in command if "--reasoning-effort" in argument] == [
        f"work {_effort_sentence('high')}"
    ]
    assert "--plugin-dir" in delivery
    # The delivery is the one a launch with no effort gets: the sentence changed the prompt only.
    no_effort = replace(pinned, effort=None)
    assert delivery == ClaudeAdapter().command(no_effort)[
        len(ClaudeAdapter().command(replace(no_effort, pin=None))):
    ]


@_every_claude_shape
@_both_renders
@_core_root_given_and_absent
def test_claude_command_without_effort_has_no_reasoning_effort_in_any_shape(
    tmp_path, shape, render, core_root_given
):
    command = _claude_command(render, tmp_path, core_root_given=core_root_given, **shape)

    assert "--reasoning-effort" not in " ".join(command)
    assert "--effort" not in command
    assert "work" in command


@_every_claude_shape
@_both_renders
def test_claude_with_effort_and_core_root_holds_no_task_map_and_no_execution_surface(
    tmp_path, shape, render
):
    command = _claude_command(
        render, tmp_path, core_root_given=True, effort=agent_run.Effort.LOW, **shape
    )
    rendered = " ".join(command)

    for absent in (
        "KENSAIAPP_TASK_MAP",
        "KENSAIAPP_STANDING_RULES",
        "Execution surface:",
        "--surface",
        "--co-authored-by",
    ):
        assert absent not in rendered


# ── A chain's Claude run is a detached `-p` process, owned the way a Codex run is ──


def test_claude_background_owner_follows_the_shape():
    adapter = ClaudeAdapter()

    assert adapter.background_owner(RunRequest(prompt="work")) == "provider"
    assert adapter.background_owner(
        RunRequest(prompt="work", shape=agent_run.Shape.TURN, session_id="s-1")
    ) == "process"
    assert adapter.background_owner(
        RunRequest(prompt="work", shape=agent_run.Shape.PRINT)
    ) == "process"


def test_codex_background_owner_is_always_the_process():
    assert CodexAdapter().background_owner(RunRequest(prompt="work")) == "process"


def test_background_claude_turn_is_a_detached_process_carrying_its_session_id(tmp_path):
    processes = FakeProcesses(pid=9876)
    runner = AgentRunner({"claude": ClaudeAdapter()}, processes)
    log_path = tmp_path / "claude.jsonl"
    request = RunRequest(prompt="work", shape=agent_run.Shape.TURN, session_id="s-1")

    result = runner.background("claude", request, log_path)

    assert result == agent_run.BackgroundRun(
        provider="claude", owner="process", log_path=log_path, pid=9876, session_id="s-1"
    )
    assert processes.logged_calls == []
    assert processes.detached_calls == [
        (
            (
                "env",
                "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1",
                "BASH_DEFAULT_TIMEOUT_MS=600000",
                "BASH_MAX_TIMEOUT_MS=21600000",
                "CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0",
                "claude",
                "--print",
                "--output-format",
                "stream-json",
                "--verbose",
                "--session-id",
                "s-1",
                "--permission-mode",
                "auto",
                "--permission-prompts",
                "none",
                "work",
            ),
            log_path,
        )
    ]


def test_the_no_background_environment_rides_only_the_detached_command():
    """The foreground turn a seat takes keeps today's argv: the ceiling is the detached run's."""
    request = RunRequest(prompt="work", shape=agent_run.Shape.TURN, session_id="s-1")

    assert ClaudeAdapter().command(request)[0] == "claude"
    detached = ClaudeAdapter().background_command(request)
    assert detached[0] == "env"
    assert "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1" in detached[: detached.index("claude")]


def test_a_provider_owned_background_command_is_unchanged():
    request = RunRequest(prompt="work")

    assert ClaudeAdapter().background_command(request) == ClaudeAdapter().command(request)


def test_start_detached_appends_an_exit_record_once_the_process_ends(tmp_path):
    log_path = tmp_path / "run.jsonl"

    pid = agent_run.Subprocesses().start_detached(("/bin/sh", "-c", "echo hello; exit 3"), log_path)

    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if log_path.exists() and "kensai.exit" in log_path.read_text():
            break
        time.sleep(0.02)
    assert isinstance(pid, int)
    lines = log_path.read_text().splitlines()
    assert lines[0] == "hello"
    assert json.loads(lines[-1]) == {"type": "kensai.exit", "code": 3}


def test_cli_background_turn_mints_a_session_id_and_reports_it(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log_path = tmp_path / "run.jsonl"
    claude = bin_dir / "claude"
    claude.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$@\"\n")
    claude.chmod(0o755)
    env = dict(os.environ)
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"

    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--provider", "claude", "--shape", "turn",
         "--prompt", "work", "--background", "--log", str(log_path)],
        text=True, capture_output=True, check=False, env=env,
    )

    assert result.returncode == 0, result.stderr
    record = json.loads(result.stdout)
    assert record["owner"] == "process"
    assert isinstance(record["pid"], int)
    session_id = record["session_id"]
    assert str(uuid.UUID(session_id)) == session_id
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline and "kensai.exit" not in log_path.read_text():
        time.sleep(0.02)
    argv = log_path.read_text().splitlines()
    assert argv[argv.index("--session-id") + 1] == session_id


def test_cli_print_argv_of_a_turn_start_mints_its_session_id():
    result = subprocess.run(
        [sys.executable, str(_SCRIPT), "--provider", "claude", "--shape", "turn",
         "--prompt", "work", "--print-argv"],
        capture_output=True, check=False,
    )

    assert result.returncode == 0, result.stderr
    argv = result.stdout.decode().split("\0")[:-1]
    assert argv[argv.index("--session-id") + 1] not in ("", "None")


# --- Claude's two levels above high ---


@pytest.mark.parametrize("level", [agent_run.Effort.XHIGH, agent_run.Effort.MAX])
def test_claude_passes_xhigh_and_max_through(level):
    command = ClaudeAdapter().command(RunRequest(prompt="work", effort=level))

    assert command[command.index("--effort") + 1] == level.value


@pytest.mark.parametrize("level", [agent_run.Effort.XHIGH, agent_run.Effort.MAX])
@pytest.mark.parametrize("adapter,provider", [(CodexAdapter(), "codex"), (GeminiAdapter(), "gemini")])
def test_codex_and_gemini_refuse_xhigh_and_max(adapter, provider, level):
    with pytest.raises(agent_run.UnsupportedRequest) as raised:
        adapter.command(RunRequest(prompt="work", effort=level))

    assert provider in str(raised.value)
    assert level.value in str(raised.value)
