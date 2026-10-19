"""Contract tests for `HfAdapter` — Claude Code aimed at the Hugging Face router.

Every adapter here is built over a tmp token file holding a sentinel, and `~/.env` is never
read. A test that needs the registered adapter runs `agent_run.py` as a subprocess with `HOME`
pointing at a tmp dir, because `ADAPTERS["hf"]` and `main` both read `Path.home()`.
"""

from __future__ import annotations

import dataclasses
import inspect
import itertools
import json
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest

import agent_run
import model_assignment
import pin
import run_intelligence
from agent_run import (ADAPTERS, AgentRunner, ClaudeAdapter, HfAdapter, RunRequest, Shape,
                       Subprocesses, UnsupportedRequest)
from test_agent_run import FakeProcesses, _build_pin_host, _flag_count, _flag_value

_SCRIPT = Path(__file__).resolve().parent / "agent_run.py"
_SENTINEL = "hf_SENTINEL_do_not_leak"
_ROUTER = "https://router.huggingface.co"
_HF = model_assignment.ASSIGNMENTS["hf"]
_VERBS = {
    Shape.BACKGROUND: ("claude", "--bg"),
    Shape.PRINT: ("claude", "-p"),
    Shape.TURN: ("claude", "--print", "--output-format", "stream-json", "--verbose"),
}


@pytest.fixture
def token_source(tmp_path):
    path = tmp_path / "token.env"
    path.write_text(f"HF_TOKEN={_SENTINEL}\n", encoding="utf-8")
    return path


@pytest.fixture
def adapter(token_source):
    return HfAdapter(token_source)


@pytest.fixture
def pins_home(tmp_path):
    home = tmp_path / "pins"
    home.mkdir()
    return home


def _request(shape: Shape, **fields) -> RunRequest:
    """A request that is valid for `shape`: a turn gets the identity it needs."""
    if shape is Shape.TURN and "resume_session_id" not in fields:
        fields.setdefault("session_id", "turn-1")
    return RunRequest(prompt="work", shape=shape, **fields)


def _settings_of(command: tuple[str, ...]) -> dict:
    """The settings document the command hands Claude Code: inline JSON, or the file it names."""
    value = _flag_value(command, "--settings")
    return json.loads(value if value.lstrip().startswith("{") else Path(value).read_text())


def _environment_of(command: tuple[str, ...]) -> dict[str, str]:
    """The variables an `env KEY=value …` prefix hands the child."""
    if command[0] != "env":
        return {}
    pairs = itertools.takewhile(lambda token: "=" in token, command[1:])
    return dict(pair.split("=", 1) for pair in pairs)


def _without_prefix(command: tuple[str, ...]) -> tuple[str, ...]:
    return command[1 + len(_environment_of(command)):] if command[0] == "env" else command


def _both_commands(adapter, request):
    return (adapter.command(request), adapter.background_command(request))


# --- the registry and the adapter's own identity ------------------------------------------------


def test_hf_is_in_every_provider_registry():
    assert "hf" in run_intelligence.PROVIDERS
    assert "hf" in ADAPTERS
    assert "hf" in model_assignment.ASSIGNMENTS


def test_the_hf_adapter_is_its_own():
    assert ClaudeAdapter not in type(ADAPTERS["hf"]).__mro__
    assert "ClaudeAdapter" not in inspect.getsource(HfAdapter)


@pytest.mark.parametrize("shape", list(Shape))
def test_each_shape_is_claude_code_with_its_verb_and_owner(adapter, shape):
    command = adapter.command(_request(shape))

    assert command[: len(_VERBS[shape])] == _VERBS[shape]
    assert adapter.background_owner(_request(shape)) == (
        "provider" if shape is Shape.BACKGROUND else "process"
    )


@pytest.mark.parametrize("shape", list(Shape))
def test_background_command_of_a_process_shape_is_command_behind_the_detached_env_prefix(
    adapter, shape
):
    request = _request(shape)
    command, background = _both_commands(adapter, request)

    if shape is Shape.BACKGROUND:
        assert background == command
    else:
        assert background == (*agent_run._env_prefix(agent_run._DETACHED_PRINT_ENV), *command)


# --- routing, credential route and the settings layer (CP-449, CP-455) --------------------------


def _matrix(token_source, tmp_path, pins_home):
    """Every shape × pin/no pin × caller settings/none, as (adapter, request) pairs."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    for shape, pinned, settings in itertools.product(
        list(Shape), (False, True), (None, '{"env":{"A":"1"}}')
    ):
        fields = {"settings": settings}
        if pinned:
            fields.update(pin=made, instance_root=host)
        yield HfAdapter(token_source), _request(shape, **fields), settings, pinned


def test_every_command_points_at_the_router(token_source, tmp_path, pins_home):
    for adapter, request, settings, pinned in _matrix(token_source, tmp_path, pins_home):
        for command in _both_commands(adapter, request):
            document = _settings_of(_without_prefix(command))
            assert document["env"]["ANTHROPIC_BASE_URL"] == _ROUTER
            if settings:
                assert document["env"]["A"] == "1"


def test_every_command_carries_the_slots_and_the_credential_route(
    token_source, tmp_path, pins_home
):
    """CP-450 and CP-455 over the CP-449 matrix: every command, not one shape, hands the child
    the four model-selection variables, and following its `apiKeyHelper` yields the token."""
    for adapter, request, _, _ in _matrix(token_source, tmp_path, pins_home):
        for command in _both_commands(adapter, request):
            document = _settings_of(_without_prefix(command))
            assert document["env"]["ANTHROPIC_DEFAULT_OPUS_MODEL"] == _HF["opus"].model
            assert document["env"]["ANTHROPIC_DEFAULT_SONNET_MODEL"] == _HF["sonnet"].model
            assert document["env"]["ANTHROPIC_DEFAULT_HAIKU_MODEL"] == _HF["haiku"].model
            assert document["env"]["CLAUDE_CODE_SUBAGENT_MODEL"] == _HF["sonnet"].model
            done = _run_helper(document)
            assert (done.returncode, done.stdout) == (0, _SENTINEL), request


def test_a_pinned_run_keeps_the_callers_settings_in_the_merged_file(
    adapter, tmp_path, pins_home
):
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    request = _request(
        Shape.PRINT, pin=made, instance_root=host, settings='{"env":{"A":"1"}}'
    )

    document = _settings_of(adapter.command(request))

    assert document["env"]["A"] == "1"
    assert document["env"]["ANTHROPIC_BASE_URL"] == _ROUTER
    assert "apiKeyHelper" in document
    assert _flag_count(adapter.command(request), "--settings") == 1


def test_a_resumed_turn_still_carries_the_settings_layer(adapter):
    request = RunRequest(
        prompt="next", shape=Shape.TURN, resume_session_id="s-1", name="n", agent="a",
        add_dirs=("/d",),
    )

    command = adapter.command(request)
    document = _settings_of(command)

    assert document["env"]["ANTHROPIC_BASE_URL"] == _ROUTER
    assert document["env"]["ANTHROPIC_DEFAULT_OPUS_MODEL"] == _HF["opus"].model
    assert "apiKeyHelper" in document
    assert _flag_value(command, "--name") == "n"
    assert _flag_value(command, "--agent") == "a"
    assert _flag_value(command, "--add-dir") == "/d"
    assert _flag_value(command, "--resume") == "s-1"


def test_slots_carry_the_hf_models_and_the_subagent_follows_the_run(adapter):
    tiered = _settings_of(adapter.command(_request(Shape.PRINT, model_tier="haiku")))["env"]
    assert tiered["ANTHROPIC_DEFAULT_OPUS_MODEL"] == _HF["opus"].model
    assert tiered["ANTHROPIC_DEFAULT_SONNET_MODEL"] == _HF["sonnet"].model
    assert tiered["ANTHROPIC_DEFAULT_HAIKU_MODEL"] == _HF["haiku"].model
    assert tiered["CLAUDE_CODE_SUBAGENT_MODEL"] == _HF["haiku"].model

    bare_command = adapter.command(_request(Shape.PRINT))
    bare = _settings_of(bare_command)["env"]
    assert bare["CLAUDE_CODE_SUBAGENT_MODEL"] == _HF["sonnet"].model
    assert "--model" not in bare_command

    named = _settings_of(adapter.command(_request(Shape.PRINT, model="zai-org/GLM-5.1")))["env"]
    assert named["CLAUDE_CODE_SUBAGENT_MODEL"] == "zai-org/GLM-5.1"


def test_the_main_model_follows_the_request(adapter):
    tier = adapter.command(_request(Shape.PRINT, model_tier="opus"))
    explicit = adapter.command(_request(Shape.PRINT, model="m/x:y"))

    assert _flag_value(tier, "--model") == _HF["opus"].model
    assert _flag_value(explicit, "--model") == "m/x:y"
    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(_request(Shape.PRINT, model="m/x", model_tier="opus"))
    assert str(refusal.value) == "request fields model and model_tier are mutually exclusive"


@pytest.mark.parametrize("shape", list(Shape))
@pytest.mark.parametrize("tier", ["opus", "sonnet", "haiku"])
def test_each_assigned_tier_is_the_main_model_in_every_shape(adapter, shape, tier):
    command = adapter.command(_request(shape, model_tier=tier))

    assert _flag_value(command, "--model") == _HF[tier].model
    assert _settings_of(command)["env"]["CLAUDE_CODE_SUBAGENT_MODEL"] == _HF[tier].model


def test_a_tier_outside_tiers_keeps_the_unknown_tier_refusal(adapter):
    with pytest.raises(model_assignment.UnknownTier) as refusal:
        adapter.command(_request(Shape.PRINT, model_tier="ultra"))

    assert str(refusal.value) == (
        "unknown model tier 'ultra'; available tiers: fable, opus, sonnet, haiku"
    )


_OPEN_MODEL = re.compile(r"^[^/\s:]+/[^/\s:]+(:[^/\s:]+)?$")


def test_every_tier_is_an_open_model_or_refused_by_name(adapter):
    claude_values = {a.model for a in model_assignment.ASSIGNMENTS["claude"].values()}
    for tier in model_assignment.TIERS:
        if tier == "fable":
            continue
        model = model_assignment.resolve("hf", tier).model
        assert _OPEN_MODEL.match(model), model
        assert model not in claude_values
        assert "claude" not in model.lower()

    message = "provider 'hf' has no model for tier 'fable'"
    with pytest.raises(model_assignment.NoModelForTier) as direct:
        model_assignment.resolve("hf", "fable")
    assert str(direct.value) == message
    with pytest.raises(UnsupportedRequest) as through_adapter:
        adapter.command(_request(Shape.PRINT, model_tier="fable"))
    assert str(through_adapter.value) == message


# --- the token (CP-454, CP-455) -----------------------------------------------------------------


@pytest.mark.parametrize("content", [None, "OTHER=1\n", "HF_TOKEN=\n"])
@pytest.mark.parametrize("pinned", [False, True])
def test_a_missing_or_empty_token_is_refused(tmp_path, pins_home, content, pinned):
    source = tmp_path / "absent.env"
    if content is not None:
        source.write_text(content, encoding="utf-8")
    fields = {}
    if pinned:
        host = _build_pin_host(tmp_path / "host")
        made = pin.make(host, pins_home)
        fields.update(pin=made, instance_root=host)

    with pytest.raises(UnsupportedRequest) as refusal:
        HfAdapter(source).command(_request(Shape.PRINT, **fields))

    assert "HF_TOKEN" in str(refusal.value) and str(source) in str(refusal.value)
    if pinned:
        assert not (made.root / "instances").exists()


def test_an_undecodable_token_source_is_refused_by_name(tmp_path):
    """CP-454: a source the adapter cannot read holds no usable HF_TOKEN, so it is refused by
    name like a missing one — never escaped as a decoding error."""
    source = tmp_path / "binary.env"
    source.write_bytes(b"HF_TOKEN=\xff\xfe\n")

    with pytest.raises(UnsupportedRequest) as refusal:
        HfAdapter(source).command(_request(Shape.PRINT))

    assert "HF_TOKEN" in str(refusal.value) and str(source) in str(refusal.value)


def test_the_token_never_leaves_its_source(token_source, tmp_path, pins_home):
    for adapter, request, _, pinned in _matrix(token_source, tmp_path, pins_home):
        for command in _both_commands(adapter, request):
            assert all(_SENTINEL not in token for token in command)
            prefix = _environment_of(command)
            assert all(_SENTINEL not in value for value in prefix.values())
            document = _settings_of(_without_prefix(command))
            assert all(_SENTINEL not in value for value in document["env"].values())
            assert _SENTINEL not in json.dumps(document)
        if pinned:
            for written in request.pin.root.rglob("*"):
                if written.is_file() and not written.is_symlink():
                    assert _SENTINEL not in written.read_text(errors="ignore"), written


def test_no_refusal_message_carries_the_token(token_source):
    adapter = HfAdapter(token_source)
    refusals = (
        _request(Shape.PRINT, model_tier="fable"),
        _request(Shape.PRINT, model="m/x", model_tier="opus"),
        _request(Shape.PRINT, core_root=Path("/x")),
        RunRequest(prompt="work", shape=Shape.TURN),
        _request(Shape.PRINT, settings='{"env":{"ANTHROPIC_API_KEY":"k"}}'),
        _request(Shape.PRINT, settings="not json"),
    )
    for request in refusals:
        with pytest.raises(UnsupportedRequest) as refusal:
            adapter.command(request)
        assert _SENTINEL not in str(refusal.value)


def _run_helper(document: dict) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["/bin/sh", "-c", document["apiKeyHelper"]], capture_output=True, text=True, check=False
    )


def test_the_helper_hands_claude_code_the_token(adapter):
    done = _run_helper(_settings_of(adapter.command(_request(Shape.PRINT))))

    assert (done.returncode, done.stdout, done.stderr) == (0, _SENTINEL, "")


def test_the_helper_command_survives_a_token_source_path_with_spaces(tmp_path):
    spaced = tmp_path / "a dir with spaces"
    spaced.mkdir()
    source = spaced / "my token.env"
    source.write_text(f"HF_TOKEN={_SENTINEL}\n", encoding="utf-8")

    done = _run_helper(_settings_of(HfAdapter(source).command(_request(Shape.PRINT))))

    assert (done.returncode, done.stdout) == (0, _SENTINEL)


# --- request fields (CP-456) --------------------------------------------------------------------

_CARRIED = {
    "prompt", "agent", "name", "resume_session_id", "model", "model_tier", "add_dirs",
    "settings", "shape", "session_id", "instance_root", "pin", "effort", "granted_skills",
}
_REFUSED = {"core_root", "skill_name", "skill_path"}


def test_every_request_field_is_carried_or_refused():
    assert {field.name for field in dataclasses.fields(RunRequest)} == _CARRIED | _REFUSED


@pytest.mark.parametrize(
    "fields, names",
    [
        ({"core_root": Path("/c")}, "core_root"),
        ({"skill_name": "s"}, "skill_name"),
        ({"skill_path": Path("/s")}, "skill_path"),
        ({"core_root": Path("/c"), "skill_path": Path("/s")}, "core_root, skill_path"),
        ({"shape": Shape.BACKGROUND, "session_id": "s"}, "session_id on background"),
        ({"shape": Shape.PRINT, "session_id": "s", "resume_session_id": "r"},
         "session_id on resume"),
        ({"instance_root": Path("/i")}, "instance_root without pin"),
        ({"granted_skills": ("g",)}, "granted_skills without pin"),
        ({"core_root": Path("/c"), "shape": Shape.BACKGROUND, "session_id": "s"},
         "core_root, session_id on background"),
    ],
)
def test_a_field_the_adapter_does_not_carry_is_refused_by_name(adapter, fields, names):
    request = RunRequest(prompt="work", **({"shape": Shape.PRINT} | fields))

    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(request)

    assert str(refusal.value) == f"provider 'hf' does not support request fields: {names}"


def test_a_pin_without_an_instance_root_is_refused(adapter, tmp_path, pins_home):
    made = pin.make(_build_pin_host(tmp_path / "host"), pins_home)

    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(_request(Shape.PRINT, pin=made))

    assert str(refusal.value) == (
        "provider 'hf' does not support request fields: pin without instance_root"
    )


@pytest.mark.parametrize("shape", list(Shape))
def test_each_carried_field_puts_its_flag_on_the_command(adapter, shape):
    fields = dict(agent="a", name="n", model="m/x", add_dirs=("/d1", "/d2"),
                  effort=agent_run.Effort.MAX)
    command = adapter.command(_request(shape, **fields))

    assert _flag_value(command, "--agent") == "a"
    assert _flag_value(command, "--name") == "n"
    assert _flag_value(command, "--model") == "m/x"
    assert [t for t in command if t.startswith("--add-dir=")] == ["--add-dir=/d1", "--add-dir=/d2"]
    assert _flag_value(command, "--effort") == "max"
    assert _flag_value(command, "--permission-mode") == "auto"
    assert ("--permission-prompts" in command) is (shape is not Shape.BACKGROUND)
    assert sum("work" in token for token in command[1:]) >= 1


def test_a_resume_and_a_fresh_session_id_are_carried(adapter):
    resumed = adapter.command(_request(Shape.PRINT, resume_session_id="r-1"))
    fresh = adapter.command(_request(Shape.PRINT, session_id="s-1"))
    turn = adapter.command(_request(Shape.TURN, session_id="t-1"))

    assert _flag_value(resumed, "--resume") == "r-1"
    assert _flag_value(fresh, "--session-id") == "s-1"
    assert _flag_value(turn, "--session-id") == "t-1"


def test_a_pinned_run_carries_the_pin_and_the_granted_skills(adapter, tmp_path, pins_home):
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    request = _request(Shape.PRINT, pin=made, instance_root=host, granted_skills=("skill",))

    command = adapter.command(request)

    for flag in ("--setting-sources", "--plugin-dir", "--settings", "--agents", "--add-dir"):
        assert _flag_count(command, flag) == 1, flag
    assert _flag_value(command, "--add-dir") == str(made.root)


def test_the_prompt_is_one_argument_carrying_the_effort_sentence(adapter):
    plain = adapter.command(_request(Shape.PRINT))
    effortful = adapter.command(_request(Shape.PRINT, effort=agent_run.Effort.HIGH))

    assert plain[-1] != effortful[-1]
    assert effortful[-1].startswith("work") or "work" in effortful[-1]


# --- a turn needs an identity (CP-457) ----------------------------------------------------------


def test_a_turn_without_identity_is_refused(adapter):
    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(RunRequest(prompt="work", shape=Shape.TURN))

    assert str(refusal.value) == (
        "provider 'hf' needs a session_id or resume_session_id for a turn"
    )


# --- caller settings cannot re-point the run (CP-458) -------------------------------------------


def test_settings_cannot_repoint_the_run(adapter):
    document = '{"env":{"ANTHROPIC_BASE_URL":"https://x","ANTHROPIC_API_KEY":"k"}}'

    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(_request(Shape.PRINT, settings=document))

    assert str(refusal.value) == (
        "provider 'hf' settings may not set: ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL"
    )


@pytest.mark.parametrize(
    "document, name",
    [
        ({"env": {"ANTHROPIC_BASE_URL": "x"}}, "ANTHROPIC_BASE_URL"),
        ({"env": {"ANTHROPIC_DEFAULT_OPUS_MODEL": "x"}}, "ANTHROPIC_DEFAULT_OPUS_MODEL"),
        ({"env": {"ANTHROPIC_DEFAULT_SONNET_MODEL": "x"}}, "ANTHROPIC_DEFAULT_SONNET_MODEL"),
        ({"env": {"ANTHROPIC_DEFAULT_HAIKU_MODEL": "x"}}, "ANTHROPIC_DEFAULT_HAIKU_MODEL"),
        ({"env": {"CLAUDE_CODE_SUBAGENT_MODEL": "x"}}, "CLAUDE_CODE_SUBAGENT_MODEL"),
        ({"env": {"ANTHROPIC_AUTH_TOKEN": "x"}}, "ANTHROPIC_AUTH_TOKEN"),
        ({"env": {"ANTHROPIC_API_KEY": "x"}}, "ANTHROPIC_API_KEY"),
        ({"env": {"ANTHROPIC_MODEL": "x"}}, "ANTHROPIC_MODEL"),
        ({"model": "x"}, "model"),
        ({"apiKeyHelper": "x"}, "apiKeyHelper"),
    ],
)
def test_each_name_the_run_owns_is_refused_in_caller_settings(adapter, document, name):
    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(_request(Shape.PRINT, settings=json.dumps(document)))

    assert str(refusal.value) == f"provider 'hf' settings may not set: {name}"


@pytest.mark.parametrize("settings", ["not json", "[1]", '{"env": "x"}', '{"env": []}'])
def test_malformed_settings_are_refused_by_name_not_as_a_traceback(adapter, settings):
    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(_request(Shape.PRINT, settings=settings))

    assert str(refusal.value).startswith("provider 'hf' settings must be a JSON object")


def test_a_refusal_is_raised_before_the_token_is_read(tmp_path):
    adapter = HfAdapter(tmp_path / "absent.env")

    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(_request(Shape.PRINT, model_tier="fable"))

    assert "fable" in str(refusal.value) and "HF_TOKEN" not in str(refusal.value)


# --- through the command line (CP-459) ----------------------------------------------------------


def _cli(home: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--provider", "hf", "--prompt", "x", *arguments],
        capture_output=True,
        text=True,
        check=False,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
    )


@pytest.fixture
def home_with_token(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    (home / ".env").write_text(f"HF_TOKEN={_SENTINEL}\n", encoding="utf-8")
    return home


@pytest.mark.parametrize(
    "arguments, message",
    [
        (("--model-tier", "fable", "--dry-run"), "provider 'hf' has no model for tier 'fable'"),
        (("--core-dir", "x", "--dry-run"),
         "provider 'hf' does not support request fields: core_root"),
        (("--settings", '{"env":{"ANTHROPIC_BASE_URL":"https://x"}}', "--dry-run"),
         "provider 'hf' settings may not set: ANTHROPIC_BASE_URL"),
    ],
)
def test_every_hf_refusal_reaches_the_cli_as_one_line(home_with_token, arguments, message):
    done = _cli(home_with_token, *arguments)

    assert done.stdout == ""
    assert done.stderr == f"agent-run: {message}\n"
    assert done.returncode == 2


def test_a_home_with_no_token_is_refused_as_one_line(tmp_path):
    empty_home = tmp_path / "empty"
    empty_home.mkdir()

    done = _cli(empty_home, "--dry-run")

    assert done.stdout == ""
    assert done.returncode == 2
    assert done.stderr.count("\n") == 1 and "Traceback" not in done.stderr
    assert done.stderr.startswith("agent-run: ") and "HF_TOKEN" in done.stderr


def test_a_home_whose_env_cannot_be_decoded_is_refused_as_one_line(tmp_path):
    home = tmp_path / "binary"
    home.mkdir()
    (home / ".env").write_bytes(b"HF_TOKEN=\xff\xfe\n")

    done = _cli(home, "--dry-run")

    assert done.stdout == ""
    assert done.returncode == 2
    assert done.stderr.count("\n") == 1 and "Traceback" not in done.stderr
    assert done.stderr.startswith("agent-run: ") and "HF_TOKEN" in done.stderr


def test_the_registered_adapter_builds_a_command_without_the_token(home_with_token):
    done = _cli(home_with_token, "--dry-run")

    assert done.returncode == 0, done.stderr
    assert "claude" in done.stdout.split()
    assert _SENTINEL not in done.stdout
    assert _SENTINEL not in done.stderr


# --- an hf turn start mints its session id, as a claude one does -------------------------------


def _printed_argv(home: Path, *arguments: str) -> list[str]:
    done = _cli(home, "--print-argv", *arguments)

    assert done.returncode == 0, done.stderr
    return done.stdout.split("\0")[:-1]


def test_cli_print_argv_of_an_hf_turn_start_mints_its_session_id(home_with_token):
    argv = _printed_argv(home_with_token, "--shape", "turn")

    session_id = argv[argv.index("--session-id") + 1]
    assert str(uuid.UUID(session_id)) == session_id


def test_cli_an_hf_turn_given_a_session_id_keeps_it(home_with_token):
    given = "11111111-2222-3333-4444-555555555555"

    argv = _printed_argv(home_with_token, "--shape", "turn", "--session-id", given)

    assert argv[argv.index("--session-id") + 1] == given


def test_cli_an_hf_resume_mints_no_session_id(home_with_token):
    argv = _printed_argv(
        home_with_token, "--shape", "turn", "--resume-session", "resumed-session"
    )

    assert argv[argv.index("--resume") + 1] == "resumed-session"
    assert "--session-id" not in argv


def test_cli_an_hf_print_shape_mints_no_session_id(home_with_token):
    argv = _printed_argv(home_with_token, "--shape", "print")

    assert "--session-id" not in argv


def test_cli_the_minted_hf_session_id_is_not_the_token(home_with_token):
    argv = _printed_argv(home_with_token, "--shape", "turn")

    assert not any(_SENTINEL in argument for argument in argv)


# --- the environment a child is started with ---------------------------------------------------
#
# These tests start `agent_run.py` as a subprocess over stub `claude`, `codex` and `agy` programs
# that write their own environment, whole, to `$ENV_RECORD`. What the stub records is what the
# provider process `agent_run.py` started would have inherited.

_LAUNCH_SENTINEL = "hf_LAUNCH_sentinel_do_not_inherit"
_RECORD_DEADLINE_SECONDS = 20.0
_RECORD_POLL_SECONDS = 0.05
_STUB_NAMES = ("claude", "codex", "agy")
_STUB_SOURCE = """#!{interpreter}
import json
import os

record = os.environ["ENV_RECORD"]
with open(record + ".part", "w", encoding="utf-8") as part:
    json.dump(dict(os.environ), part)
os.replace(record + ".part", record)
"""
_SHAPE_NAMES = [shape.value for shape in Shape]
_MODES = ("foreground", "background")


def _write_stubs(directory: Path) -> None:
    directory.mkdir(exist_ok=True)
    for name in _STUB_NAMES:
        stub = directory / name
        stub.write_text(_STUB_SOURCE.format(interpreter=sys.executable), encoding="utf-8")
        stub.chmod(0o755)


def _await_record(record: Path) -> dict[str, str]:
    """The stub's environment, once it has been written whole.

    A detached start returns before its child runs, so the record is awaited against a deadline.
    The stub writes beside the record and renames, so the file is absent or complete.
    """
    deadline = time.monotonic() + _RECORD_DEADLINE_SECONDS
    while not record.exists():
        if time.monotonic() > deadline:
            pytest.fail(f"no child wrote {record} within {_RECORD_DEADLINE_SECONDS} seconds")
        time.sleep(_RECORD_POLL_SECONDS)
    return json.loads(record.read_text(encoding="utf-8"))


# Not `_SCRIPT` itself: `main()` calls `load_dotenv()` with no path, which loads the first `.env`
# on the walk up from the script's own directory, and from `core/tools/` that walk can reach the
# real `~/.env`. A link under `home` puts the test's own `.env` first on the walk. Imports still
# resolve, because Python puts the script's symlink-resolved directory on `sys.path`.
def _script_for(home: Path) -> Path:
    """The `agent_run.py` path the harness starts for a test whose `HOME` is `home`: a link to
    the real script, inside `home`."""
    link = home / "agent_run" / _SCRIPT.name
    if not link.is_symlink():
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(_SCRIPT)
    return link


def _first_env_file_above(script: Path) -> Path | None:
    """The `.env` that `agent_run.py`'s `load_dotenv()`, called with no path, loads when started
    as `script`: the first one on the walk up from the script's own directory."""
    for directory in (script.parent, *script.parent.parents):
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    return None


def _launching_environment(
    tmp_path: Path,
    home: Path,
    *,
    launch_token: str | None = _LAUNCH_SENTINEL,
    extra_environment: dict[str, str] | None = None,
) -> dict[str, str]:
    """The environment one `agent_run.py` start is launched with: `HOME`, a `PATH` that finds
    the stubs, `ENV_RECORD`, `CONTROL_VAR=ctl`, `HF_TOKEN` when `launch_token` is not None,
    and `extra_environment` over the top."""
    return {
        "HOME": str(home),
        "PATH": f"{tmp_path / 'stubs'}:/usr/bin:/bin",
        "ENV_RECORD": str(tmp_path / "child_environment.json"),
        "CONTROL_VAR": "ctl",
        **({"HF_TOKEN": launch_token} if launch_token is not None else {}),
        **(extra_environment or {}),
    }


def _child_environment(
    tmp_path: Path,
    home: Path,
    provider: str,
    shape: str,
    mode: str,
    *,
    launch_token: str | None = _LAUNCH_SENTINEL,
    extra_environment: dict[str, str] | None = None,
) -> dict[str, str]:
    """The environment the child of one `agent_run.py` start received, the start launched with
    `_launching_environment` for the same arguments."""
    _write_stubs(tmp_path / "stubs")
    launching = _launching_environment(
        tmp_path, home, launch_token=launch_token, extra_environment=extra_environment
    )
    arguments = ["--provider", provider, "--prompt", "x", "--shape", shape]
    if provider == "hf" and shape == Shape.TURN.value:
        arguments += ["--session-id", str(uuid.uuid4())]
    if mode == "background":
        arguments += ["--background", "--log", str(tmp_path / "run.log")]
    done = subprocess.run(
        [sys.executable, str(_script_for(home)), *arguments],
        capture_output=True,
        text=True,
        check=False,
        env=launching,
    )
    assert done.returncode == 0, done.stderr
    return _await_record(Path(launching["ENV_RECORD"]))


def test_the_harness_reads_no_env_file_above_its_home(home_with_token):
    assert _first_env_file_above(_script_for(home_with_token)) == home_with_token / ".env"


_NON_HF_STARTS = [
    *((("claude", shape), mode) for shape in _SHAPE_NAMES for mode in _MODES),
    *((("codex", "print"), mode) for mode in _MODES),
    *((("gemini", "print"), mode) for mode in _MODES),
]


@pytest.mark.parametrize(
    "start, mode",
    _NON_HF_STARTS,
    ids=[f"{provider}-{shape}-{mode}" for (provider, shape), mode in _NON_HF_STARTS],
)
def test_a_non_hf_child_still_inherits_the_token(tmp_path, home_with_token, start, mode):
    provider, shape = start

    record = _child_environment(tmp_path, home_with_token, provider, shape, mode)

    assert record["HF_TOKEN"] == _LAUNCH_SENTINEL
    assert record["CONTROL_VAR"] == "ctl"


def test_a_runner_over_an_adapter_that_withholds_nothing_makes_todays_call(tmp_path):
    processes = FakeProcesses()
    runner = AgentRunner({"claude": ClaudeAdapter()}, processes)

    runner.run("claude", _request(Shape.PRINT))
    runner.background("claude", _request(Shape.BACKGROUND), tmp_path / "provider.log")
    runner.background("claude", _request(Shape.PRINT), tmp_path / "process.log")

    assert len(processes.calls) == 1
    assert len(processes.logged_calls) == 1
    assert len(processes.detached_calls) == 1


# --- an hf child's environment holds no token ----------------------------------------------------

_HF_STARTS = [(shape, mode) for shape in _SHAPE_NAMES for mode in _MODES]
_HF_START_IDS = [f"{shape}-{mode}" for shape, mode in _HF_STARTS]


def _holds_in_no_key_or_value(record: dict[str, str], text: str) -> bool:
    return not any(text in key or text in value for key, value in record.items())


@pytest.mark.parametrize("shape, mode", _HF_STARTS, ids=_HF_START_IDS)
def test_the_hf_child_inherits_no_token(tmp_path, home_with_token, shape, mode):
    near_name = {"HF_HOME": "hf-home"}
    record = _child_environment(
        tmp_path, home_with_token, "hf", shape, mode, extra_environment=near_name
    )

    assert record["CONTROL_VAR"] == "ctl"
    kept = _launching_environment(tmp_path, home_with_token, extra_environment=near_name)
    del kept["HF_TOKEN"]
    assert kept.items() <= record.items()
    assert "HF_TOKEN" not in record
    assert _holds_in_no_key_or_value(record, _LAUNCH_SENTINEL)
    assert _holds_in_no_key_or_value(record, _SENTINEL)
    if mode == "background" and shape != Shape.BACKGROUND.value:
        assert agent_run._DETACHED_PRINT_ENV.items() <= record.items()


@pytest.mark.parametrize("shape, mode", _HF_STARTS, ids=_HF_START_IDS)
def test_the_hf_child_inherits_no_token_loaded_from_an_env_file(
    tmp_path, home_with_token, shape, mode
):
    dotenv = pytest.importorskip(
        "dotenv", reason="without python-dotenv agent_run.py loads no .env, so there is no route"
    )
    with (home_with_token / ".env").open("a", encoding="utf-8") as env_file:
        env_file.write("ENV_FILE_CONTROL=loaded\n")

    record = _child_environment(
        tmp_path,
        home_with_token,
        "hf",
        shape,
        mode,
        launch_token=None,
        extra_environment={"PYTHONPATH": str(Path(dotenv.__file__).resolve().parent.parent)},
    )

    assert record["ENV_FILE_CONTROL"] == "loaded"
    assert "HF_TOKEN" not in record
    assert _holds_in_no_key_or_value(record, _SENTINEL)


def test_an_empty_hf_token_is_not_inherited(tmp_path, home_with_token):
    record = _child_environment(
        tmp_path, home_with_token, "hf", "print", "foreground", launch_token=""
    )

    assert "HF_TOKEN" not in record


class _WithholdRecordingProcesses:
    """A process port that records the `withhold` each method received."""

    def __init__(self):
        self.withheld = {}

    def run(self, argv, *, withhold=frozenset()):
        self.withheld["run"] = withhold
        return 0

    def run_to_log(self, argv, log_path, *, withhold=frozenset()):
        self.withheld["run_to_log"] = withhold
        return 0

    def start_detached(self, argv, log_path, *, withhold=frozenset()):
        self.withheld["start_detached"] = withhold
        return 4321


def _start_all_three_ways(runner: AgentRunner, provider: str, tmp_path: Path) -> None:
    runner.run(provider, _request(Shape.PRINT))
    runner.background(provider, _request(Shape.BACKGROUND), tmp_path / "provider.log")
    runner.background(provider, _request(Shape.PRINT), tmp_path / "process.log")


def test_the_runner_withholds_what_the_adapter_names(tmp_path, adapter):
    processes = _WithholdRecordingProcesses()

    _start_all_three_ways(AgentRunner({"hf": adapter}, processes), "hf", tmp_path)

    assert processes.withheld == {
        "run": frozenset({"HF_TOKEN"}),
        "run_to_log": frozenset({"HF_TOKEN"}),
        "start_detached": frozenset({"HF_TOKEN"}),
    }


def test_the_runner_passes_whatever_set_the_adapter_names(tmp_path):
    class NamingAdapter(ClaudeAdapter):
        withheld_environment = frozenset({"FIRST_NAME", "SECOND_NAME"})

    processes = _WithholdRecordingProcesses()

    _start_all_three_ways(AgentRunner({"naming": NamingAdapter()}, processes), "naming", tmp_path)

    assert set(processes.withheld.values()) == {frozenset({"FIRST_NAME", "SECOND_NAME"})}


def test_the_hf_adapter_names_the_token_it_withholds(adapter):
    assert adapter.withheld_environment == frozenset({agent_run._HF_TOKEN_KEY})


_DUMP_ENVIRONMENT = (
    "import json, os, sys; open(sys.argv[1], 'w').write(json.dumps(dict(os.environ)))"
)
_PORT_METHODS = ("run", "run_to_log", "start_detached")


def _start_through_the_port(method: str, tmp_path: Path, **keywords) -> dict[str, str]:
    """The environment a child of `Subprocesses.<method>` received."""
    record = tmp_path / "port_environment.json"
    argv = [sys.executable, "-c", _DUMP_ENVIRONMENT, str(record)]
    port = Subprocesses()
    if method == "run":
        port.run(argv, **keywords)
    elif method == "run_to_log":
        port.run_to_log(argv, tmp_path / "port.log", **keywords)
    else:
        port.start_detached(argv, tmp_path / "port.log", **keywords)
    return _await_record(record)


@pytest.mark.parametrize("method", _PORT_METHODS)
def test_the_port_withholds_only_the_names_it_is_given(tmp_path, monkeypatch, method):
    monkeypatch.setenv("HF_TOKEN", _LAUNCH_SENTINEL)
    monkeypatch.setenv("CONTROL_VAR", "ctl")
    monkeypatch.delenv("ABSENT_NAME", raising=False)

    record = _start_through_the_port(
        method, tmp_path, withhold=frozenset({"HF_TOKEN", "ABSENT_NAME"})
    )

    assert "HF_TOKEN" not in record
    assert "ABSENT_NAME" not in record
    assert record["CONTROL_VAR"] == "ctl"
    assert "PATH" in record


@pytest.mark.parametrize("keywords", [{}, {"withhold": frozenset()}], ids=["omitted", "empty"])
@pytest.mark.parametrize("method", _PORT_METHODS)
def test_the_port_inherits_everything_when_nothing_is_withheld(
    tmp_path, monkeypatch, method, keywords
):
    monkeypatch.setenv("HF_TOKEN", _LAUNCH_SENTINEL)
    monkeypatch.setenv("CONTROL_VAR", "ctl")

    record = _start_through_the_port(method, tmp_path, **keywords)

    assert record["HF_TOKEN"] == _LAUNCH_SENTINEL
    assert record["CONTROL_VAR"] == "ctl"
