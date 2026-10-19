"""Contract tests for `OllamaAdapter` — Claude Code aimed at the owner's local Ollama server.

In-process cases build the adapter over a dict for `environ` and a fake `reach`, so no socket is
opened. The cases that need an answering server run a stub HTTP server on `127.0.0.1`, and the
subprocess cases point `KENSAIAPP_OLLAMA_URL` at it: the suite's guard otherwise leaves the
address where nothing listens.
"""

from __future__ import annotations

import dataclasses
import http.server
import inspect
import itertools
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

import pytest

import agent_run
import model_assignment
import pin
import run_intelligence
from agent_run import (ADAPTERS, ClaudeAdapter, HfAdapter, OllamaAdapter, RunRequest, Shape,
                       UnsupportedRequest)
from test_agent_run import _build_pin_host, _flag_count, _flag_value

_SCRIPT = Path(__file__).resolve().parent / "agent_run.py"
_OLLAMA = model_assignment.ASSIGNMENTS["ollama"]
_DEFAULT_ADDRESS = "http://localhost:11434"
_VERBS = {
    Shape.BACKGROUND: ("claude", "--bg"),
    Shape.PRINT: ("claude", "-p"),
    Shape.TURN: ("claude", "--print", "--output-format", "stream-json", "--verbose"),
}
_REFUSAL = "provider 'ollama' needs an Ollama server answering at {address}"


class _Reach:
    """A fake `reach`: answers as told and remembers every address it was asked about."""

    def __init__(self, answers: bool = True) -> None:
        self.answers = answers
        self.asked: list[str] = []

    def __call__(self, address: str) -> bool:
        self.asked.append(address)
        return self.answers


@pytest.fixture
def reach():
    return _Reach()


@pytest.fixture
def adapter(reach):
    return OllamaAdapter({}, reach)


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


def _is_a_claude_model_name(name: str) -> bool:
    return "claude" in name.lower() or name in {
        entry.model for entry in model_assignment.ASSIGNMENTS["claude"].values()
    }


# --- a stub Ollama server ------------------------------------------------------------------------


class _Stub:
    def __init__(self, status: int = 200, delay: float = 0.0) -> None:
        self.status = status
        self.delay = delay
        self.paths: list[str] = []
        owner = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                owner.paths.append(self.path)
                time.sleep(owner.delay)
                self.send_response(owner.status)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *arguments):
                pass

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.address = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()


@pytest.fixture
def stub():
    server = _Stub()
    yield server
    server.close()


# --- the registry and the adapter's own identity -------------------------------------------------


def test_ollama_is_in_every_provider_registry():
    assert "ollama" in run_intelligence.PROVIDERS
    assert "ollama" in ADAPTERS
    assert "ollama" in model_assignment.ASSIGNMENTS


def test_the_ollama_adapter_is_not_the_claude_adapter():
    assert ClaudeAdapter not in type(ADAPTERS["ollama"]).__mro__
    assert "ClaudeAdapter" not in inspect.getsource(OllamaAdapter)


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


# --- routing, credential and the settings layer (CP-496) ----------------------------------------


def _matrix(tmp_path, pins_home):
    """Every shape × pin/no pin × caller settings/none, as (request, settings) pairs."""
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    for shape, pinned, settings in itertools.product(
        list(Shape), (False, True), (None, '{"env":{"A":"1"}}')
    ):
        fields = {"settings": settings}
        if pinned:
            fields.update(pin=made, instance_root=host)
        yield _request(shape, **fields), settings


def test_every_command_points_at_the_local_server(adapter, tmp_path, pins_home):
    for request, settings in _matrix(tmp_path, pins_home):
        for command in _both_commands(adapter, request):
            document = _settings_of(_without_prefix(command))
            assert document["env"]["ANTHROPIC_BASE_URL"] == _DEFAULT_ADDRESS
            assert document["env"]["ANTHROPIC_AUTH_TOKEN"] == "ollama"
            assert document["env"]["ANTHROPIC_API_KEY"] == ""
            assert "apiKeyHelper" not in document
            if settings:
                assert document["env"]["A"] == "1"


def test_the_address_defaults_to_localhost_and_follows_the_override():
    default_reach = _Reach()
    default = OllamaAdapter({}, default_reach)
    empty = OllamaAdapter({"KENSAIAPP_OLLAMA_URL": ""}, _Reach())
    overridden_reach = _Reach()
    overridden = OllamaAdapter({"KENSAIAPP_OLLAMA_URL": "http://127.0.0.1:1"}, overridden_reach)

    for adapter_under_test, expected in (
        (default, _DEFAULT_ADDRESS),
        (empty, _DEFAULT_ADDRESS),
        (overridden, "http://127.0.0.1:1"),
    ):
        env = _settings_of(adapter_under_test.command(_request(Shape.PRINT)))["env"]
        assert env["ANTHROPIC_BASE_URL"] == expected
    assert default_reach.asked == [_DEFAULT_ADDRESS]
    assert overridden_reach.asked == ["http://127.0.0.1:1"]


def test_the_address_is_read_when_the_command_is_built(reach):
    environ: dict[str, str] = {}
    adapter = OllamaAdapter(environ, reach)
    environ["KENSAIAPP_OLLAMA_URL"] = "http://127.0.0.1:2"

    env = _settings_of(adapter.command(_request(Shape.PRINT)))["env"]

    assert env["ANTHROPIC_BASE_URL"] == "http://127.0.0.1:2"


def test_slots_carry_the_ollama_models_and_the_subagent_follows_the_run(adapter):
    tiered = _settings_of(adapter.command(_request(Shape.PRINT, model_tier="haiku")))["env"]
    assert tiered["ANTHROPIC_DEFAULT_OPUS_MODEL"] == _OLLAMA["opus"].model
    assert tiered["ANTHROPIC_DEFAULT_SONNET_MODEL"] == _OLLAMA["sonnet"].model
    assert tiered["ANTHROPIC_DEFAULT_HAIKU_MODEL"] == _OLLAMA["haiku"].model
    assert tiered["CLAUDE_CODE_SUBAGENT_MODEL"] == "qwen2.5-coder:14b"

    bare_command = adapter.command(_request(Shape.PRINT))
    bare = _settings_of(bare_command)["env"]
    assert bare["CLAUDE_CODE_SUBAGENT_MODEL"] == _OLLAMA["sonnet"].model
    assert "--model" not in bare_command

    named = _settings_of(adapter.command(_request(Shape.PRINT, model="local:7b")))["env"]
    assert named["CLAUDE_CODE_SUBAGENT_MODEL"] == "local:7b"


def test_the_main_model_follows_the_request(adapter):
    fable = adapter.command(_request(Shape.PRINT, model_tier="fable"))
    explicit = adapter.command(_request(Shape.PRINT, model="m:x"))

    assert _flag_value(fable, "--model") == "qwen3.8:27b"
    assert _flag_value(explicit, "--model") == "m:x"
    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(_request(Shape.PRINT, model="m:x", model_tier="opus"))
    assert str(refusal.value) == "request fields model and model_tier are mutually exclusive"


@pytest.mark.parametrize("tier", model_assignment.TIERS)
def test_no_tier_resolves_to_a_claude_model_name(adapter, tier):
    command = adapter.command(_request(Shape.PRINT, model_tier=tier))
    env = _settings_of(command)["env"]
    names = [
        _flag_value(command, "--model"),
        env["ANTHROPIC_DEFAULT_OPUS_MODEL"],
        env["ANTHROPIC_DEFAULT_SONNET_MODEL"],
        env["ANTHROPIC_DEFAULT_HAIKU_MODEL"],
        env["CLAUDE_CODE_SUBAGENT_MODEL"],
    ]

    assert not [name for name in names if _is_a_claude_model_name(name)]


# --- no server, no launch (CP-499) ---------------------------------------------------------------


@pytest.mark.parametrize("pinned", [False, True])
def test_an_unreachable_server_is_refused_naming_the_address(tmp_path, pins_home, pinned):
    adapter = OllamaAdapter({"KENSAIAPP_OLLAMA_URL": "http://127.0.0.1:9"}, _Reach(False))
    fields = {}
    if pinned:
        host = _build_pin_host(tmp_path / "host")
        fields.update(pin=pin.make(host, pins_home), instance_root=host)

    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(_request(Shape.PRINT, **fields))

    assert str(refusal.value) == _REFUSAL.format(address="http://127.0.0.1:9")
    if pinned:
        assert not list((fields["pin"].root / "instances").glob("*"))


def test_reach_is_asked_last(reach):
    adapter = OllamaAdapter({}, reach)

    with pytest.raises(model_assignment.UnknownTier) as refusal:
        adapter.command(_request(Shape.PRINT, model_tier="not-a-tier"))
    with pytest.raises(UnsupportedRequest):
        adapter.command(_request(Shape.PRINT, core_root=Path("/c")))
    with pytest.raises(UnsupportedRequest):
        adapter.command(_request(Shape.PRINT, settings='{"model": "x"}'))
    with pytest.raises(UnsupportedRequest):
        adapter.command(RunRequest(prompt="work", shape=Shape.TURN))

    assert "not-a-tier" in str(refusal.value)
    assert reach.asked == []


# --- request fields (CP-498) ---------------------------------------------------------------------

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

    assert str(refusal.value) == f"provider 'ollama' does not support request fields: {names}"


def test_a_pin_without_an_instance_root_is_refused(adapter, tmp_path, pins_home):
    made = pin.make(_build_pin_host(tmp_path / "host"), pins_home)

    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(_request(Shape.PRINT, pin=made))

    assert str(refusal.value) == (
        "provider 'ollama' does not support request fields: pin without instance_root"
    )


@pytest.mark.parametrize("shape", list(Shape))
def test_each_carried_field_puts_its_flag_on_the_command(adapter, shape):
    fields = dict(agent="a", name="n", model="m:x", add_dirs=("/d1", "/d2"),
                  effort=agent_run.Effort.MAX)
    command = adapter.command(_request(shape, **fields))

    assert _flag_value(command, "--agent") == "a"
    assert _flag_value(command, "--name") == "n"
    assert _flag_value(command, "--model") == "m:x"
    assert [t for t in command if t.startswith("--add-dir=")] == ["--add-dir=/d1", "--add-dir=/d2"]
    assert _flag_value(command, "--effort") == "max"
    assert _flag_value(command, "--permission-mode") == "auto"
    assert ("--permission-prompts" in command) is (shape is not Shape.BACKGROUND)


def test_a_pinned_run_carries_the_pin_and_the_granted_skills(adapter, tmp_path, pins_home):
    host = _build_pin_host(tmp_path / "host")
    made = pin.make(host, pins_home)
    request = _request(Shape.PRINT, pin=made, instance_root=host, granted_skills=("skill",))

    command = adapter.command(request)

    for flag in ("--setting-sources", "--plugin-dir", "--settings", "--agents", "--add-dir"):
        assert _flag_count(command, flag) == 1, flag
    assert _flag_value(command, "--add-dir") == str(made.root)


def test_a_turn_without_identity_is_refused(adapter):
    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(RunRequest(prompt="work", shape=Shape.TURN))

    assert str(refusal.value) == (
        "provider 'ollama' needs a session_id or resume_session_id for a turn"
    )


# --- caller settings cannot re-point the run (CP-498) --------------------------------------------

_OWNED = [({"env": {name: "x"}}, name) for name in sorted(agent_run._HF_OWNED_ENV)] + [
    ({"model": "x"}, "model"),
    ({"apiKeyHelper": "x"}, "apiKeyHelper"),
]


@pytest.mark.parametrize("document, name", _OWNED, ids=[name for _, name in _OWNED])
def test_settings_cannot_repoint_the_run(adapter, document, name):
    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(_request(Shape.PRINT, settings=json.dumps(document)))

    assert str(refusal.value) == f"provider 'ollama' settings may not set: {name}"


def test_collisions_are_named_in_sorted_order(adapter):
    document = '{"env":{"ANTHROPIC_BASE_URL":"https://x","ANTHROPIC_API_KEY":"k"},"model":"m"}'

    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(_request(Shape.PRINT, settings=document))

    assert str(refusal.value) == (
        "provider 'ollama' settings may not set: ANTHROPIC_API_KEY, ANTHROPIC_BASE_URL, model"
    )


@pytest.mark.parametrize("settings", ["not json", "[1]", '{"env": "x"}', '{"env": []}'])
def test_malformed_settings_are_refused_by_name_not_as_a_traceback(adapter, settings):
    with pytest.raises(UnsupportedRequest) as refusal:
        adapter.command(_request(Shape.PRINT, settings=settings))

    assert str(refusal.value).startswith("provider 'ollama' settings must be a JSON object")


def test_nothing_is_withheld_from_the_inherited_environment(adapter):
    assert getattr(adapter, "withheld_environment", frozenset()) == frozenset()


# --- the reachability check ----------------------------------------------------------------------


def test_the_reachability_check_reads_api_version(stub):
    assert agent_run._ollama_answers(stub.address) is True
    assert stub.paths == ["/api/version"]


def test_a_server_that_answers_500_is_unreachable():
    server = _Stub(status=500)
    try:
        assert agent_run._ollama_answers(server.address) is False
    finally:
        server.close()


def test_a_port_with_nothing_listening_is_unreachable():
    server = _Stub()
    address = server.address
    server.close()

    assert agent_run._ollama_answers(address) is False


def test_a_server_that_does_not_answer_in_time_is_unreachable():
    server = _Stub(delay=1.0)
    try:
        assert agent_run._ollama_answers(server.address, timeout_seconds=0.1) is False
    finally:
        server.close()


@pytest.mark.parametrize("address", ["not a url", "ftp://127.0.0.1:1", ""])
def test_a_malformed_address_is_unreachable_not_a_traceback(address):
    assert agent_run._ollama_answers(address) is False


def test_the_registered_adapter_asks_the_environment_at_build_time(stub, monkeypatch):
    monkeypatch.setenv("KENSAIAPP_OLLAMA_URL", stub.address)

    env = _settings_of(ADAPTERS["ollama"].command(_request(Shape.PRINT)))["env"]

    assert env["ANTHROPIC_BASE_URL"] == stub.address


# --- through the command line (CP-499) -----------------------------------------------------------


def _cli(home: Path, address: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), "--provider", "ollama", "--prompt", "x", *arguments],
        capture_output=True,
        text=True,
        check=False,
        env={"HOME": str(home), "PATH": "/usr/bin:/bin", "KENSAIAPP_OLLAMA_URL": address},
    )


@pytest.fixture
def home(tmp_path):
    path = tmp_path / "home"
    path.mkdir()
    return path


def _printed_argv(home: Path, address: str, *arguments: str) -> list[str]:
    done = _cli(home, address, "--print-argv", *arguments)

    assert done.returncode == 0, done.stderr
    return done.stdout.split("\0")[:-1]


def test_cli_an_ollama_turn_start_mints_its_session_id(home, stub):
    argv = _printed_argv(home, stub.address, "--shape", "turn")
    session_id = argv[argv.index("--session-id") + 1]

    assert str(uuid.UUID(session_id)) == session_id

    resumed = _printed_argv(home, stub.address, "--shape", "turn", "--resume-session", "r-1")
    assert resumed[resumed.index("--resume") + 1] == "r-1"
    assert "--session-id" not in resumed

    assert "--session-id" not in _printed_argv(home, stub.address, "--shape", "print")


@pytest.mark.parametrize(
    "arguments, message",
    [
        (("--dry-run",), _REFUSAL),
        (("--core-dir", "x", "--dry-run"),
         "provider 'ollama' does not support request fields: core_root"),
        (("--settings", '{"env":{"ANTHROPIC_BASE_URL":"https://x"}}', "--dry-run"),
         "provider 'ollama' settings may not set: ANTHROPIC_BASE_URL"),
    ],
    ids=["unreachable", "field", "settings"],
)
def test_every_ollama_refusal_reaches_the_cli_as_one_line(home, arguments, message):
    address = os.environ["KENSAIAPP_OLLAMA_URL"]
    done = _cli(home, address, *arguments)

    assert done.stdout == ""
    assert done.stderr == f"agent-run: {message.format(address=address)}\n"
    assert done.returncode == 2
    assert "Traceback" not in done.stderr


def test_an_answering_server_lets_a_dry_run_through_as_a_claude_command(home, stub):
    done = _cli(home, stub.address, "--dry-run")

    assert done.returncode == 0, done.stderr
    assert done.stdout.startswith("claude ")


# --- hf is unchanged by the shared builder (CP-503) ---------------------------------------------

# Recorded from the base commit e708b5638 before the lift: `HfAdapter(<sentinel .env>)` over a
# fixed request, with the interpreter, the helper script and the token path normalized.
_HF_MODELS = {
    "opus": "zai-org/GLM-5.3:novita",
    "sonnet": "MiniMaxAI/MiniMax-M3:novita",
    "haiku": "deepseek-ai/DeepSeek-V4.1-Flash:novita",
}
_HF_HELPER = "<python> <env_file.py> <token> HF_TOKEN"
_HF_PERMISSIONS = {
    Shape.BACKGROUND: ["--permission-mode", "auto"],
    Shape.PRINT: ["--permission-mode", "auto", "--permission-prompts", "none"],
    Shape.TURN: ["--permission-mode", "auto", "--permission-prompts", "none"],
}
_HF_LEADS = {
    Shape.BACKGROUND: ["claude", "--bg"],
    Shape.PRINT: ["claude", "-p"],
    Shape.TURN: ["claude", "--print", "--output-format", "stream-json", "--verbose",
                 "--session-id", "turn-1"],
}


def _recorded_hf_argv(shape: Shape, tier: str | None) -> list[str]:
    main = _HF_MODELS[tier] if tier else None
    settings = {
        "env": {
            "ANTHROPIC_BASE_URL": "https://router.huggingface.co",
            "ANTHROPIC_DEFAULT_OPUS_MODEL": _HF_MODELS["opus"],
            "ANTHROPIC_DEFAULT_SONNET_MODEL": _HF_MODELS["sonnet"],
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": _HF_MODELS["haiku"],
            "CLAUDE_CODE_SUBAGENT_MODEL": main or _HF_MODELS["sonnet"],
        },
        "apiKeyHelper": _HF_HELPER,
    }
    return [
        *_HF_LEADS[shape],
        *(["--model", main] if main else []),
        *_HF_PERMISSIONS[shape],
        "--settings",
        json.dumps(settings),
        "work",
    ]


@pytest.mark.parametrize("tier", [None, "opus"])
@pytest.mark.parametrize("shape", list(Shape))
def test_hf_commands_are_unchanged_by_the_shared_builder(tmp_path, shape, tier):
    token_source = tmp_path / "token.env"
    token_source.write_text("HF_TOKEN=hf_SENTINEL_do_not_leak\n", encoding="utf-8")
    helper = str(Path(agent_run.__file__).resolve().with_name("env_file.py"))

    def normalized(argv):
        return [
            token.replace(sys.executable, "<python>").replace(helper, "<env_file.py>")
            .replace(str(token_source), "<token>")
            for token in argv
        ]

    adapter = HfAdapter(token_source)
    request = _request(shape, model_tier=tier)

    assert normalized(adapter.command(request)) == _recorded_hf_argv(shape, tier)
