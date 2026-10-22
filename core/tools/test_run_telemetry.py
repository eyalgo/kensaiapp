"""Tests for `core/tools/run_telemetry.sh` — every instrumented launcher's telemetry tagging over
the telemetry package's `turn-on --print`.

The helper is a **sourced bash library**, so each case writes a tiny wrapper that sources it and
calls `run_telemetry`, the "source, then call one function" shape of
`core/doctrine/engineering/languages/shell/testing.md` § Technique 2.

Two suites share this file, and they use different executables on purpose:

- **The real-package matrix** runs the helper alone over the **real** package command, reached
  through a temporary home whose `.kensaiapp/venv` links to the real installed one. Each case states
  what it expects from its own inputs — the status, the lines printed in order, nothing on stderr,
  the six exports or their absence, and the settings document — and only the run id, which the
  package generates per call, is matched by shape. A stand-in would prove nothing about command
  compatibility, so none is used here. Where the command cannot be reached the matrix is skipped,
  with the missing dependency named, and never passes or fails for that reason.
- **The failure-boundary suite** drives the helper with controlled fixture executables, because a
  real package cannot be made to exit non-zero or print garbage on demand.

The command's name is never written in this file. The real-package fixture discovers it through
`telemetry_command.resolve`, before it isolates HOME, from the invoking environment or the source
host's setting, and every case that must be unconfigured says so with an explicit empty
`KENSAIAPP_TELEMETRY_COMMAND`, so the host's own setting cannot change what it expects. The
vendor-neutrality check has nothing to find here.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

import pytest

import telemetry_command
from launcher_telemetry_test_support import (
    SKIP_NOT_PLAIN,
    SKIP_UNSET,
    real_package_skip_reason,
    skip_reason_unreachable,
)

_TOOLS = Path(__file__).resolve().parent
_HELPER = _TOOLS / "run_telemetry.sh"

COMMAND_VARIABLE = "KENSAIAPP_TELEMETRY_COMMAND"
CAP_KEY = "KENSAIAPP_CONTEXT_CAP"
SETTINGS_KEY = "INSTRUMENT_RUN_SETTINGS"
ATTRIBUTES_KEY = "OTEL_RESOURCE_ATTRIBUTES"
ENDPOINT_KEY = "OTEL_EXPORTER_OTLP_ENDPOINT"

# The home the real package is installed under. Read once, before any case isolates HOME.
REAL_HOME = Path.home()

TELEMETRY_KEYS = (
    "CLAUDE_CODE_ENABLE_TELEMETRY",
    "OTEL_METRICS_EXPORTER",
    "OTEL_LOGS_EXPORTER",
    "OTEL_EXPORTER_OTLP_PROTOCOL",
    ENDPOINT_KEY,
    ATTRIBUTES_KEY,
)
CHAIN_TAGS = (
    ("INSTRUMENT_RUN_WALK_ID", "kensai.walk_id"),
    ("INSTRUMENT_RUN_CHAIN", "kensai.chain"),
    ("INSTRUMENT_RUN_ROLE", "kensai.role"),
    ("INSTRUMENT_RUN_AUDIT_TARGET", "kensai.audit_target"),
)
ACCEPTED_KEYS = (
    "project",
    "document",
    "skill",
    "target_instance",
    "provider",
    "model",
    "effort",
    "source",
)
FORBIDDEN_CHARACTERS = (" ", '"', ",", ";", "\\", "=")
RUN_ID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
SENTINEL = "---ENVIRONMENT-AFTER-THE-CALL---"
VALID_ENDPOINT = "http://127.0.0.1:4318"
DEFAULT_SCRIPT_DIR = "/opt/launchers/skill"
NO_PROJECT_CARD = "system/projects/{project}/project.md"
RAW_OUTPUT_MARKER = "RAW-PACKAGE-OUTPUT-MARKER"
FIXTURE_COMMAND = "fixture-command"

# --- the harness --------------------------------------------------------------------------------


@dataclass(frozen=True)
class Outcome:
    """What one call left behind: the process result, the lines the call printed and the
    environment a process spawned right afterwards would inherit."""

    returncode: int
    lines: list[str]
    stderr: str
    environ: dict[str, str]

    @property
    def settings(self) -> dict | None:
        raw = self.environ.get(SETTINGS_KEY)
        return None if raw is None else json.loads(raw)

    @property
    def exports(self) -> dict[str, str]:
        return {key: self.environ[key] for key in TELEMETRY_KEYS if key in self.environ}

    @property
    def attributes(self) -> list[tuple[str, str]] | None:
        raw = self.environ.get(ATTRIBUTES_KEY)
        if raw is None:
            return None
        return [tuple(pair.split("=", 1)) for pair in raw.split(",")]


def _clean_environ(home: Path) -> dict[str, str]:
    """The inherited environment less everything telemetry reads, with HOME isolated."""
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("OTEL_", "INSTRUMENT_RUN_", "CLAUDE_CODE_ENABLE_TELEMETRY"))
        and key not in (CAP_KEY, COMMAND_VARIABLE)
    }
    env["HOME"] = str(home)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    return env


def _write_wrapper(
    directory: Path, library: Path, args: list[str], *, script_dir: str | None,
    before: str = "", body: str | None = None,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    quoted = " ".join(shlex.quote(arg) for arg in args)
    lines = ["#!/usr/bin/env bash", "set -euo pipefail"]
    if script_dir is not None:
        lines.append(f"SCRIPT_DIR={shlex.quote(script_dir)}")
    if before:
        lines.append(before)
    lines.append(f'source "{library}"')
    lines.append(body if body is not None else f"run_telemetry {quoted}")
    lines += [f'echo "{SENTINEL}"', "env"]
    wrapper = directory / "wrapper.sh"
    wrapper.write_text("\n".join(lines) + "\n")
    wrapper.chmod(0o755)
    return wrapper


def _run_wrapper(wrapper: Path, env: dict[str, str], cwd: Path) -> Outcome:
    done = subprocess.run(
        ["bash", str(wrapper)], cwd=str(cwd), capture_output=True, text=True, env=env, timeout=60
    )
    printed, _, after = done.stdout.partition(SENTINEL + "\n")
    environ = {}
    for line in after.splitlines():
        key, separator, value = line.partition("=")
        if separator:
            environ[key] = value
    return Outcome(done.returncode, printed.splitlines(), done.stderr, environ)


class Rig:
    """One isolated home and one working directory to call the helper in."""

    def __init__(self, tmp_path: Path, command_name: str | None = None) -> None:
        self.tmp_path = tmp_path
        self.home = tmp_path / "home"
        self.home.mkdir()
        self.command_name = command_name
        self.endpoint_file = tmp_path / "endpoint"
        self.endpoint_file.write_text(VALID_ENDPOINT + "\n")
        self.cwd = self._make_instance(tmp_path / "instance-root" / "example-instance")
        self._calls = 0

    @staticmethod
    def _git(path: Path, *args: str) -> None:
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null",
             "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-C", str(path), *args],
            check=True, capture_output=True, env={**os.environ, "GIT_CONFIG_GLOBAL": os.devnull,
                                                  "GIT_CONFIG_NOSYSTEM": "1"},
        )

    def make_card(self, root: Path, project: str, line: str | None) -> None:
        card = root / "system" / "projects" / project / "project.md"
        card.parent.mkdir(parents=True, exist_ok=True)
        card.write_text("# Project Context\n\n" + (line + "\n" if line is not None else ""))

    def _make_instance(self, path: Path) -> Path:
        path.mkdir(parents=True)
        self._git(path, "init", "--quiet")
        self.make_card(path, "tools", "**Product path:** core/tools   <!-- a trailing comment -->")
        self._git(path, "commit", "--quiet", "--allow-empty", "-m", "initial")
        return path

    def make_repository(self, name: str) -> Path:
        """A git repository named `name`, for the instance identity cases."""
        path = self.tmp_path / "named" / name
        return self._make_instance(path)

    def environment(self, extra: dict[str, str] | None = None) -> dict[str, str]:
        env = _clean_environ(self.home)
        env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(self.endpoint_file)
        # A rig with no command is *explicitly* unconfigured: absent would let the host's own
        # setting answer, and these cases are about what the helper does without a command.
        env[COMMAND_VARIABLE] = self.command_name if self.command_name is not None else ""
        env.update(extra or {})
        return {key: value for key, value in env.items() if value is not None}

    def call(
        self, library: Path, args: list[str], *, env: dict[str, str] | None = None,
        cwd: Path | None = None, script_dir: str | None = DEFAULT_SCRIPT_DIR, before: str = "",
        body: str | None = None,
    ) -> Outcome:
        self._calls += 1
        wrapper = _write_wrapper(
            self.tmp_path / f"caller{self._calls}" / "caller", library, args,
            script_dir=script_dir, before=before, body=body,
        )
        return _run_wrapper(wrapper, self.environment(env), cwd or self.cwd)

    def install(self, name: str, body: str, *, mode: int = 0o755) -> Path:
        directory = self.home / ".kensaiapp" / "venv" / "bin"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / name
        path.write_text(body)
        path.chmod(mode)
        return path


@pytest.fixture
def rig(tmp_path: Path) -> Rig:
    """A rig for the failure-boundary suite: fixture executables only, no real package."""
    return Rig(tmp_path, FIXTURE_COMMAND)


@pytest.fixture
def real(tmp_path: Path) -> Rig:
    """A rig whose home links to the real installed environment — or the skip that names what is
    missing."""
    discovered = telemetry_command.resolve(_TOOLS.parent, dict(os.environ))
    reason = real_package_skip_reason({COMMAND_VARIABLE: discovered}, REAL_HOME)
    if reason:
        pytest.skip(reason)
    rig = Rig(tmp_path, discovered)
    (rig.home / ".kensaiapp").mkdir()
    (rig.home / ".kensaiapp" / "venv").symlink_to(REAL_HOME / ".kensaiapp" / "venv")
    return rig


# --- stating what a call should leave behind ---------------------------------------------------

BASE_EXPORTS = {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
}
# The one field a case cannot state: the package generates the run id per call.
RUN_ID_PAIR = ("kensai.run_id", None)
ARM_PAIR = ("kensai.arm", "skill")
INSTANCE_PAIR = ("kensai.instance", "example-instance")
UNKNOWN_KEY_NOTICE = (
    "          (unknown telemetry key '{key}' — only project, document, skill, target_instance, "
    "provider, model, effort and source are accepted)"
)
NO_EQUALS_NOTICE = (
    "          (telemetry argument '{argument}' has no '=' — expected key=value; not attached)"
)
REFUSED_VALUE_NOTICE = (
    "          (kensai.{key} '{value}' contains a character OTEL_RESOURCE_ATTRIBUTES cannot carry "
    "— not attached)"
)
NO_INSTANCE_ARM_REFUSED = (
    "          (kensai.arm could not be derived from the calling launcher's directory — "
    "arm not attached)"
)


def _head(*labels: tuple[str, str]) -> list[tuple[str, str | None]]:
    """The pairs every instrumented call from the rig's launcher directory and repository leads
    with, then the labels the case states."""
    return [ARM_PAIR, RUN_ID_PAIR, INSTANCE_PAIR, *labels]


def _run_id(outcome: Outcome) -> str | None:
    for key, value in outcome.attributes or []:
        if key == "kensai.run_id":
            return value
    return None


def _assert_run_id_shape(outcome: Outcome) -> str:
    run_id = _run_id(outcome)
    assert run_id is not None and RUN_ID.fullmatch(run_id), outcome.attributes
    assert str(uuid.UUID(run_id)) == run_id
    return run_id


def assert_instrumented(
    outcome: Outcome, pairs: list[tuple[str, str | None]], *, notices: tuple[str, ...] = (),
    cap: str | None = None, endpoint: str = VALID_ENDPOINT,
) -> None:
    """The complete observation of an instrumented call, stated from the case's own pairs: status,
    nothing on stderr, the refusal lines then the one `Telemetry:` line, all six exports and the
    settings document. Only the run id is matched by shape, and the one value found must then be
    the value every representation carries."""
    run_id = _assert_run_id_shape(outcome)
    stated = [(key, run_id if value is None else value) for key, value in pairs]
    attributes = ",".join(f"{key}={value}" for key, value in stated)
    assert outcome.returncode == 0, outcome.stderr
    assert outcome.stderr == ""
    assert outcome.attributes == stated
    assert outcome.lines == [*notices, f"          Telemetry:    {attributes} → {endpoint}"]
    assert outcome.exports == {
        **BASE_EXPORTS, ENDPOINT_KEY: endpoint, ATTRIBUTES_KEY: attributes
    }
    env = {**BASE_EXPORTS, ENDPOINT_KEY: endpoint, **({CAP_KEY: cap} if cap else {})}
    assert outcome.settings == {"env": {**env, ATTRIBUTES_KEY: attributes}}


def assert_run_uninstrumented(outcome: Outcome, cause: str, *, cap: str | None = None) -> None:
    """The complete observation of a call that leaves the run uninstrumented: status 0, one stdout
    line naming the cause, nothing on stderr, none of the six exports, and the cap alone (or
    nothing) in the settings."""
    assert outcome.returncode == 0, outcome.stderr
    assert outcome.stderr == ""
    assert outcome.lines == [f"          ({cause} — run uninstrumented)"]
    assert outcome.exports == {}
    assert outcome.settings == ({"env": {CAP_KEY: cap}} if cap else None)


def _telemetry_lines(outcome: Outcome) -> list[str]:
    return [line for line in outcome.lines if "Telemetry:" in line]


SPEC_EXAMPLE_ARGS = [
    "skill=development-specs", "project=tools", "provider=claude", "effort=high",
    "source=intelligence",
]


# --- sourcing -----------------------------------------------------------------------------------


def test_sourcing_is_inert(rig: Rig):
    """Sourcing alone, under a strict shell, prints nothing, runs no configured command and
    exports nothing — the contract `detach_watcher.sh` states for its own sourced library."""
    marker = rig.tmp_path / "ran"
    rig.install(FIXTURE_COMMAND, f"#!/bin/sh\ntouch {shlex.quote(str(marker))}\n")
    control = rig.call(_HELPER, [], body=":", before="OPTIONS_BEFORE=$-")
    sourced_only = rig.call(
        _HELPER, [], body='test "$(type -t run_telemetry)" = function || exit 9; '
        'echo "OPTIONS_AFTER=$-"', before="OPTIONS_BEFORE=$-",
    )
    assert sourced_only.returncode == 0, sourced_only.stderr
    assert sourced_only.stderr == ""
    assert sourced_only.lines[:-1] == []
    assert sourced_only.lines[-1].startswith("OPTIONS_AFTER=")
    assert sourced_only.environ == control.environ
    assert not marker.exists()


# --- the real package ---------------------------------------------------------------------------


def _pair(key: str, value: str) -> tuple[str, str]:
    return (f"kensai.{key}", value)


OBSERVATION_CASES = [
    pytest.param(
        SPEC_EXAMPLE_ARGS,
        {"INSTRUMENT_RUN_WALK_ID": "w1", "INSTRUMENT_RUN_ROLE": "architect", CAP_KEY: "250000"},
        _head(
            _pair("skill", "development-specs"), _pair("project", "tools"),
            _pair("product", "tools"), _pair("provider", "claude"), _pair("effort", "high"),
            _pair("source", "intelligence"), _pair("walk_id", "w1"), _pair("role", "architect"),
        ),
        (),
        "250000",
        id="the-specified-example",
    ),
    pytest.param(
        [f"{key}=value-of-{key}" for key in ACCEPTED_KEYS],
        {},
        _head(*[_pair(key, f"value-of-{key}") for key in ACCEPTED_KEYS]),
        (),
        None,
        id="all-eight-keys",
    ),
    pytest.param(
        [f"{key}=value-of-{key}" for key in reversed(ACCEPTED_KEYS)],
        {},
        _head(*[_pair(key, f"value-of-{key}") for key in reversed(ACCEPTED_KEYS)]),
        (),
        None,
        id="changed-caller-order",
    ),
    pytest.param(
        ["skill=a", "project=tools", "skill=b", "project=tools", "document=d", "skill=c"],
        {},
        _head(
            _pair("skill", "a"), _pair("project", "tools"), _pair("product", "tools"),
            _pair("skill", "b"), _pair("project", "tools"), _pair("product", "tools"),
            _pair("document", "d"), _pair("skill", "c"),
        ),
        (),
        None,
        id="repeated-keys-keep-multiplicity-and-product-adjacency",
    ),
    pytest.param(
        ["bogus=1", "nokv", "skill=", "project=tools", "=novalue", "provider=claude"],
        {},
        _head(_pair("project", "tools"), _pair("product", "tools"), _pair("provider", "claude")),
        (
            UNKNOWN_KEY_NOTICE.format(key="bogus"),
            NO_EQUALS_NOTICE.format(argument="nokv"),
            UNKNOWN_KEY_NOTICE.format(key=""),
        ),
        None,
        id="unknown-key-missing-equals-and-empty-value",
    ),
    pytest.param(
        ["skill=development-specs"],
        {
            "INSTRUMENT_RUN_WALK_ID": "walk-1",
            "INSTRUMENT_RUN_CHAIN": "chain-development",
            "INSTRUMENT_RUN_ROLE": "developer",
            "INSTRUMENT_RUN_AUDIT_TARGET": "development-plan",
        },
        _head(
            _pair("skill", "development-specs"), _pair("walk_id", "walk-1"),
            _pair("chain", "chain-development"), _pair("role", "developer"),
            _pair("audit_target", "development-plan"),
        ),
        (),
        None,
        id="every-chain-tag",
    ),
    pytest.param([], {}, _head(), (), None, id="no-arguments"),
]


@pytest.mark.parametrize(("args", "extra", "pairs", "notices", "cap"), OBSERVATION_CASES)
def test_helper_stamps_complete_ordered_observations(
    real: Rig, args, extra, pairs, notices, cap
):
    """E1: each input leaves its complete observation — status, the lines it printed in order,
    nothing on stderr, all six exports and the settings document — with only each launch's own run
    id matched by shape. Every expected value is written from the case's own inputs."""
    outcome = real.call(_HELPER, args, env=extra)
    assert_instrumented(outcome, pairs, notices=notices, cap=cap)


def test_real_package_example_attribute_order(real: Rig):
    """The specified example, asserted outright as an ordered list of keys."""
    new = real.call(
        _HELPER,
        SPEC_EXAMPLE_ARGS,
        env={"INSTRUMENT_RUN_WALK_ID": "w1", "INSTRUMENT_RUN_ROLE": "architect"},
    )
    assert [key for key, _ in new.attributes] == [
        "kensai.arm", "kensai.run_id", "kensai.instance", "kensai.skill", "kensai.project",
        "kensai.product", "kensai.provider", "kensai.effort", "kensai.source", "kensai.walk_id",
        "kensai.role",
    ]
    assert dict(new.attributes)["kensai.arm"] == "skill"
    assert dict(new.attributes)["kensai.instance"] == "example-instance"
    assert dict(new.attributes)["kensai.product"] == "tools"


@pytest.mark.parametrize(
    ("line_args", "expected"),
    [
        (["nokv"], NO_EQUALS_NOTICE.format(argument="nokv")),
        (["bogus=1"], UNKNOWN_KEY_NOTICE.format(key="bogus")),
    ],
)
def test_argument_shape_notices_use_the_published_text(real: Rig, line_args, expected):
    outcome = real.call(_HELPER, ["skill=a", *line_args])
    assert_instrumented(outcome, _head(_pair("skill", "a")), notices=(expected,))


# --- the context cap ----------------------------------------------------------------------------


@pytest.mark.parametrize("endpoint_valid", [True, False], ids=["instrumented", "uninstrumented"])
@pytest.mark.parametrize(
    ("cap_environment", "cap_shell"),
    [({CAP_KEY: "250000"}, ""), ({}, ""), ({CAP_KEY: ""}, ""), ({}, f"{CAP_KEY}=777")],
    ids=["exported-nonempty", "unset", "exported-empty", "shell-local-only"],
)
def test_context_cap_is_carried_only_when_exported_and_nonempty(
    real: Rig, cap_environment, cap_shell, endpoint_valid
):
    """E1/E2: the cap rides in the settings when it is exported and non-empty, on a successful
    call and on an uninstrumented one, and only then."""
    if not endpoint_valid:
        real.endpoint_file.unlink()
    outcome = real.call(_HELPER, ["skill=a"], env=cap_environment, before=cap_shell)
    exported_cap = cap_environment.get(CAP_KEY) or None
    if endpoint_valid:
        assert_instrumented(outcome, _head(_pair("skill", "a")), cap=exported_cap)
    else:
        assert_run_uninstrumented(
            outcome, f"no published telemetry endpoint at {real.endpoint_file}", cap=exported_cap
        )


# --- endpoint failures and loopback forms -------------------------------------------------------


def _break_endpoint(real: Rig, kind: str) -> None:
    endpoint = real.endpoint_file
    if kind == "absent":
        endpoint.unlink()
    elif kind == "unreadable":
        endpoint.chmod(0)
    elif kind == "malformed":
        endpoint.write_text("not an endpoint\n")
    elif kind == "empty":
        endpoint.write_text("")
    elif kind == "directory":
        endpoint.unlink()
        endpoint.mkdir()
    elif kind == "non-loopback":
        endpoint.write_text("http://example.com:4318\n")
    else:
        raise AssertionError(kind)


def _endpoint_cause(kind: str, endpoint_file: Path) -> str:
    """The cause the helper names for each way an endpoint file can fail."""
    if kind in ("absent", "unreadable"):
        return f"no published telemetry endpoint at {endpoint_file}"
    if kind == "non-loopback":
        return f"telemetry endpoint at {endpoint_file} is not on this machine (loopback only)"
    return f"telemetry endpoint at {endpoint_file} is unreadable or malformed"


@pytest.mark.parametrize("cap", ["250000", None], ids=["with-cap", "without-cap"])
@pytest.mark.parametrize(
    "kind", ["absent", "unreadable", "malformed", "empty", "directory", "non-loopback"]
)
def test_endpoint_failures_keep_the_call_successful(real: Rig, kind, cap):
    """E2: an endpoint the package declines leaves the run uninstrumented, with one stdout line
    naming the cause, no new telemetry export and the cap alone in the settings."""
    if kind == "unreadable" and os.geteuid() == 0:
        pytest.skip("equivalence comparison not run: a superuser reads any file")
    _break_endpoint(real, kind)
    outcome = real.call(
        _HELPER, ["skill=a", "project=tools"], env={CAP_KEY: cap} if cap else {}
    )
    assert_run_uninstrumented(outcome, _endpoint_cause(kind, real.endpoint_file), cap=cap)


@pytest.mark.parametrize(
    "endpoint",
    ["http://localhost:4318", "http://127.0.0.1:4318", "http://[::1]:4318",
     "https://127.5.6.7:99/path", "http://localhost"],
)
@pytest.mark.parametrize("how", ["override", "default-file"])
def test_loopback_endpoint_sources_preserve_complete_observations(real: Rig, endpoint, how):
    """E2: every loopback form is accepted, from the explicit override and from the default file
    under HOME, and the exported endpoint is the one written."""
    env: dict[str, str | None] = {}
    if how == "default-file":
        default = real.home / ".claude" / "tools" / "otel-receiver" / "endpoint"
        default.parent.mkdir(parents=True)
        default.write_text(endpoint + "\n")
        env["INSTRUMENT_RUN_ENDPOINT_FILE"] = None
    else:
        real.endpoint_file.write_text(endpoint + "\n")
    outcome = real.call(_HELPER, ["skill=a"], env=env)
    assert_instrumented(outcome, _head(_pair("skill", "a")), endpoint=endpoint)


# --- the percent, instance and arm behaviours ----------------------------------------------------


def test_percent_values_keep_the_helper_encoding(real: Rig):
    """E3 / CP-760.1: a `%` in an argument value is carried as `%000025`."""
    outcome = real.call(_HELPER, ["model=50%", "skill=a%b", "provider=claude"])
    assert_instrumented(
        outcome,
        _head(_pair("model", "50%000025"), _pair("skill", "a%000025b"),
              _pair("provider", "claude")),
    )


def test_percent_in_the_arm_product_and_chain_tags_is_carried_encoded(real: Rig):
    """E3 / CP-760.1, beyond the eight arguments: the arm, the product and each of the four chain
    tags are handed to the package as labels too, so a `%` in any of them is carried as
    `%000025`."""
    root = real.make_repository("percent-labels")
    real.make_card(root, "tools", "**Product path:** core/p%q")
    outcome = real.call(
        _HELPER, ["project=tools", "skill=a"], cwd=root,
        env={"INSTRUMENT_RUN_ARM": "arm%1", "INSTRUMENT_RUN_WALK_ID": "w%1",
             "INSTRUMENT_RUN_CHAIN": "c%3", "INSTRUMENT_RUN_ROLE": "role%2",
             "INSTRUMENT_RUN_AUDIT_TARGET": "t%4"},
    )
    assert_instrumented(
        outcome,
        [
            _pair("arm", "arm%0000251"), RUN_ID_PAIR, _pair("instance", "percent-labels"),
            _pair("project", "tools"), _pair("product", "p%000025q"), _pair("skill", "a"),
            _pair("walk_id", "w%0000251"), _pair("chain", "c%0000253"),
            _pair("role", "role%0000252"), _pair("audit_target", "t%0000254"),
        ],
    )


@pytest.mark.parametrize("character", ["\x01", "\x1b", "\x7f"], ids=["soh", "escape", "delete"])
def test_a_control_character_outside_the_refused_set_is_carried(real: Rig, character):
    """Only whitespace, a double quote, a comma, a semicolon, a backslash and an `=` are refused
    (CP-647), so a value holding another control character is attached. The run stays
    instrumented whether it arrives as an argument or as a chain tag."""
    value = f"a{character}b"
    outcome = real.call(
        _HELPER, ["skill=a", f"model={value}"], env={"INSTRUMENT_RUN_ROLE": f"r{character}"}
    )
    assert_instrumented(
        outcome, _head(_pair("skill", "a"), _pair("model", value), _pair("role", f"r{character}"))
    )


@pytest.mark.parametrize("character", [" ", '"', ",", ";", "\\", "=", "%"],
                         ids=["space", "quote", "comma", "semicolon", "backslash", "equals",
                              "percent"])
def test_special_instance_names_are_left_off_or_carried(real: Rig, character):
    """E3/E5 / CP-760.2: an instance name holding whitespace, `"`, `,`, `;`, `\\` or `=` is left off
    the attributes, and no line names it. An instance name holding `%` is carried as written."""
    name = f"a{character}b"
    repository = real.make_repository(name)
    outcome = real.call(_HELPER, ["skill=a"], cwd=repository)
    if character == "%":
        assert_instrumented(
            outcome, [ARM_PAIR, RUN_ID_PAIR, _pair("instance", name), _pair("skill", "a")]
        )
        return
    assert_instrumented(outcome, [ARM_PAIR, RUN_ID_PAIR, _pair("skill", "a")])


def test_a_refused_arm_a_refused_instance_and_a_percent_label_combine(real: Rig):
    """E3 / CP-760.1–3 together: a refused arm, a refused instance and a percent label in one
    call."""
    repository = real.make_repository("my dir")
    outcome = real.call(_HELPER, ["model=50%", "skill=a"], cwd=repository,
                        env={"INSTRUMENT_RUN_ARM": "a b"})
    assert_instrumented(
        outcome,
        [RUN_ID_PAIR, _pair("model", "50%000025"), _pair("skill", "a")],
        notices=(
            "          (kensai.arm 'a b' contains whitespace — OTEL_RESOURCE_ATTRIBUTES cannot "
            "carry one; arm not attached)",
        ),
    )


ARM_REFUSALS = [
    pytest.param(
        "a b",
        "          (kensai.arm 'a b' contains whitespace — OTEL_RESOURCE_ATTRIBUTES cannot carry "
        "one; arm not attached)",
        id="whitespace",
    ),
    *[
        pytest.param(
            f"a{character}b",
            f"          (kensai.arm 'a{character}b' contains a character OTEL_RESOURCE_ATTRIBUTES "
            "cannot carry — arm not attached)",
            id=name,
        )
        for character, name in (('"', "quote"), (",", "comma"), (";", "semicolon"),
                                ("\\", "backslash"), ("=", "equals"))
    ],
    *[
        pytest.param(arm, NO_INSTANCE_ARM_REFUSED, id=name)
        for arm, name in (("/", "root"), (".", "dot"), ("..", "dot-dot"))
    ],
]


@pytest.mark.parametrize(("arm", "line"), ARM_REFUSALS)
def test_invalid_arm_keeps_the_helpers_run_id(real: Rig, arm, line):
    """E3/E4 / CP-760.3, CP-647: a refused arm is named on one stdout line and not attached, and
    the attributes still carry `kensai.run_id`."""
    outcome = real.call(_HELPER, ["skill=a"], env={"INSTRUMENT_RUN_ARM": arm})
    assert_instrumented(
        outcome, [RUN_ID_PAIR, INSTANCE_PAIR, _pair("skill", "a")], notices=(line,)
    )


def test_an_arm_that_cannot_be_derived_is_refused(real: Rig):
    """E4: a launcher directory of `/` yields no arm, with the fixed line and a run id."""
    outcome = real.call(_HELPER, ["skill=a"], script_dir="/")
    assert_instrumented(
        outcome, [RUN_ID_PAIR, INSTANCE_PAIR, _pair("skill", "a")],
        notices=(NO_INSTANCE_ARM_REFUSED,),
    )


@pytest.mark.parametrize(
    ("script_dir", "env", "expected_arm"),
    [
        (DEFAULT_SCRIPT_DIR, {"INSTRUMENT_RUN_ARM": "custom-arm"}, "custom-arm"),
        (DEFAULT_SCRIPT_DIR, {}, "skill"),
        (DEFAULT_SCRIPT_DIR, {"INSTRUMENT_RUN_ARM": ""}, "skill"),
        ("/some/absolute/launcher-folder", {}, "launcher-folder"),
        (None, {}, "caller"),
        ("relative/folder", {}, "caller"),
    ],
    ids=["explicit-override", "unset-override", "empty-override-falls-back", "absolute-caller-dir",
         "caller-path-fallback", "relative-script-dir-falls-back"],
)
def test_arm_override_and_caller_fallback_sources(real: Rig, script_dir, env, expected_arm):
    outcome = real.call(_HELPER, ["skill=a"], script_dir=script_dir, env=env)
    assert_instrumented(
        outcome, [_pair("arm", expected_arm), RUN_ID_PAIR, INSTANCE_PAIR, _pair("skill", "a")]
    )


def test_successive_calls_have_distinct_lowercase_uuids(real: Rig):
    """E4 / CP-646: every launch gets its own id, in 8-4-4-4-12 lowercase hexadecimal, and each
    separate call carries its one id in every representation: the line, the exports and the
    settings."""
    first = real.call(_HELPER, ["skill=a"])
    second = real.call(_HELPER, ["skill=a"])
    for outcome in (first, second):
        assert_instrumented(outcome, _head(_pair("skill", "a")))
    in_one_shell = real.call(
        _HELPER, [],
        body='run_telemetry skill=a >/dev/null; first="$OTEL_RESOURCE_ATTRIBUTES"; '
        'run_telemetry skill=a >/dev/null; echo "FIRST=$first"; '
        'echo "SECOND=$OTEL_RESOURCE_ATTRIBUTES"',
    )
    ids = [_assert_run_id_shape(first), _assert_run_id_shape(second)]
    for line in in_one_shell.lines:
        if "=" in line:
            ids.append(RUN_ID.search(line.partition("=")[2]).group(0))
    assert len(ids) == 4 and len(set(ids)) == 4
    for value in ids:
        assert RUN_ID.fullmatch(value)
        assert str(uuid.UUID(value)) == value


# --- refusals -----------------------------------------------------------------------------------


@pytest.mark.parametrize("character", FORBIDDEN_CHARACTERS,
                         ids=["space", "quote", "comma", "semicolon", "backslash", "equals"])
def test_refusals_leave_untouched_arguments_and_tags_in_order(real: Rig, character):
    """E4 / CP-647: for each forbidden character, every recognised key is refused alone, with the
    fixed stdout line once, while the untouched pairs stay in the caller's order."""
    bad = f"x{character}y"
    for key in ACCEPTED_KEYS:
        values = {k: bad if k == key else ("tools" if k == "project" else "ok-" + k)
                  for k in ACCEPTED_KEYS}
        args = [f"{k}={values[k]}" for k in ACCEPTED_KEYS]
        stated = []
        for other in ACCEPTED_KEYS:
            if other == key:
                continue
            stated.append(_pair(other, values[other]))
            if other == "project":
                stated.append(_pair("product", "tools"))
        outcome = real.call(_HELPER, args)
        assert_instrumented(
            outcome, _head(*stated),
            notices=(REFUSED_VALUE_NOTICE.format(key=key, value=bad),),
        )


@pytest.mark.parametrize("tag", CHAIN_TAGS, ids=[name for name, _ in CHAIN_TAGS])
def test_each_unexportable_chain_tag_is_silent(real: Rig, tag):
    """E4 / CP-647: a chain or role tag takes a valid value, drops an empty or a refused one
    without a line, and leaves every other pair as it was."""
    variable, attribute = tag
    outcome = real.call(_HELPER, ["skill=a"], env={variable: "valid-value"})
    assert_instrumented(outcome, _head(_pair("skill", "a"), (attribute, "valid-value")))
    for value in ["", *[f"v{c}w" for c in FORBIDDEN_CHARACTERS]]:
        outcome = real.call(_HELPER, ["skill=a"], env={variable: value})
        assert_instrumented(outcome, _head(_pair("skill", "a")))


# --- instance and product -----------------------------------------------------------------------


def test_instance_and_product_identity_comes_from_the_case_inputs(real: Rig):
    """E5: a checkout and a worktree cut from it name the same instance, and a directory outside
    git names none."""
    checkout = real.make_repository("identity-checkout")
    worktree = real.tmp_path / "linked-worktree"
    Rig._git(checkout, "worktree", "add", "--quiet", str(worktree), "-b", "linked")
    outside = real.tmp_path / "outside-git"
    outside.mkdir()
    for place in (checkout, worktree):
        outcome = real.call(_HELPER, ["skill=a"], cwd=place)
        assert_instrumented(
            outcome, [ARM_PAIR, RUN_ID_PAIR, _pair("instance", "identity-checkout"),
                      _pair("skill", "a")],
        )
    outcome = real.call(_HELPER, ["skill=a"], cwd=outside)
    assert_instrumented(outcome, [ARM_PAIR, RUN_ID_PAIR, _pair("skill", "a")])


PRODUCT_CARDS = [
    pytest.param(
        "**Product path:** core/tools   <!-- a trailing comment -->", "tools", id="trailing-comment"
    ),
    pytest.param("**Product path:** /an/absolute/other-product", "other-product", id="absolute"),
    pytest.param("**Product path:**", None, id="empty-line"),
    pytest.param("**Type:** software", None, id="missing-line"),
    pytest.param("**Product path:** core/a,b", None, id="refused-basename"),
    pytest.param(None, None, id="missing-card"),
]


@pytest.mark.parametrize(("line", "product"), PRODUCT_CARDS)
def test_product_follows_each_project_from_its_card(real: Rig, line, product):
    """E5: the first matching `Product path:` line and its first path token supply the product's
    basename; a card, line, path or carriable basename that is missing adds no product."""
    root = real.make_repository("product-instance")
    if line is None:
        card = root / "system" / "projects" / "tools" / "project.md"
        card.unlink()
    else:
        real.make_card(root, "tools", line)
    outcome = real.call(_HELPER, ["project=tools", "skill=a"], cwd=root)
    labels = [_pair("project", "tools"), *([_pair("product", product)] if product else []),
              _pair("skill", "a")]
    assert_instrumented(
        outcome, [ARM_PAIR, RUN_ID_PAIR, _pair("instance", "product-instance"), *labels]
    )


def test_product_reads_the_first_matching_line_and_survives_an_unreadable_card(real: Rig):
    root = real.make_repository("product-lines")
    card = root / "system" / "projects" / "tools" / "project.md"
    card.write_text("**Product path:** first/one\n**Product path:** second/two\n")
    outcome = real.call(_HELPER, ["project=tools"], cwd=root)
    assert_instrumented(
        outcome,
        [ARM_PAIR, RUN_ID_PAIR, _pair("instance", "product-lines"), _pair("project", "tools"),
         _pair("product", "one")],
    )
    if os.geteuid() != 0:
        card.chmod(0)
        outcome = real.call(_HELPER, ["project=tools"], cwd=root)
        assert_instrumented(
            outcome,
            [ARM_PAIR, RUN_ID_PAIR, _pair("instance", "product-lines"), _pair("project", "tools")],
        )


def test_repeated_project_labels_each_keep_their_product(real: Rig):
    root = real.make_repository("product-repeats")
    real.make_card(root, "other", "**Product path:** products/other-product")
    outcome = real.call(
        _HELPER, ["project=tools", "skill=a", "project=other", "project=tools"], cwd=root
    )
    assert_instrumented(
        outcome,
        [
            ARM_PAIR, RUN_ID_PAIR, _pair("instance", "product-repeats"),
            _pair("project", "tools"), _pair("product", "tools"), _pair("skill", "a"),
            _pair("project", "other"), _pair("product", "other-product"),
            _pair("project", "tools"), _pair("product", "tools"),
        ],
    )


# --- a missing dependency is a named skip -------------------------------------------------------


def _nested_pytest(environ: dict[str, str], *selectors: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(Path(__file__).resolve()), "-k",
         " or ".join(selectors), "-q", "-rs", "-n", "0", "-p", "no:cacheprovider"],
        cwd=str(_TOOLS), capture_output=True, text=True, env=environ, timeout=300,
    )


def _nested_environment(home: Path, **extra: str) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k != COMMAND_VARIABLE}
    env[COMMAND_VARIABLE] = ""
    env["HOME"] = str(home)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.update(extra)
    return env


def test_unavailable_real_package_reports_a_named_skip(tmp_path: Path):
    """E6 / CP-761: with the configuration absent, or naming a command that is not there, the
    real-package case is reported skipped — with the missing dependency named — and neither
    passes nor fails. A command that is reached and breaks the contract fails the case instead."""
    selector = "test_helper_stamps_complete_ordered_observations"

    unset_home = tmp_path / "unset"
    unset_home.mkdir()
    unset = _nested_pytest(_nested_environment(unset_home), selector)
    assert unset.returncode == 0, unset.stdout + unset.stderr
    assert SKIP_UNSET in unset.stdout
    assert "skipped" in unset.stdout
    assert "passed" not in unset.stdout and "failed" not in unset.stdout

    missing_home = tmp_path / "missing"
    missing_home.mkdir()
    absent = _nested_pytest(
        _nested_environment(missing_home, **{COMMAND_VARIABLE: "no-such-telemetry-command"}),
        selector,
    )
    path = missing_home / ".kensaiapp" / "venv" / "bin" / "no-such-telemetry-command"
    assert absent.returncode == 0, absent.stdout + absent.stderr
    assert skip_reason_unreachable(path) in absent.stdout
    assert "failed" not in absent.stdout and "passed" not in absent.stdout

    # CP-761: a reached command that exits non-zero, or that prints no settings document, fails.
    for label, body in (
        ("exit-3", "#!/bin/sh\nexit 3\n"),
        ("no-settings-document", "#!/bin/sh\necho 'this is not a settings document'\n"),
    ):
        broken_home = tmp_path / f"broken-{label}"
        (broken_home / ".kensaiapp" / "venv" / "bin").mkdir(parents=True)
        broken = broken_home / ".kensaiapp" / "venv" / "bin" / FIXTURE_COMMAND
        broken.write_text(body)
        broken.chmod(0o755)
        reached = _nested_pytest(
            _nested_environment(broken_home, **{COMMAND_VARIABLE: FIXTURE_COMMAND}), selector
        )
        assert reached.returncode == 1, label + ": " + reached.stdout + reached.stderr
        assert "failed" in reached.stdout and "skipped" not in reached.stdout, label


def test_the_skip_decision_names_what_is_missing(tmp_path: Path):
    """The reasons themselves, without a nested run."""
    assert real_package_skip_reason({}, tmp_path) == SKIP_UNSET
    assert real_package_skip_reason({COMMAND_VARIABLE: ""}, tmp_path) == SKIP_UNSET
    assert real_package_skip_reason({COMMAND_VARIABLE: "a/b"}, tmp_path) == SKIP_NOT_PLAIN
    unreachable = real_package_skip_reason({COMMAND_VARIABLE: "absent-command"}, tmp_path)
    assert unreachable == skip_reason_unreachable(
        tmp_path / ".kensaiapp" / "venv" / "bin" / "absent-command"
    )
    present = tmp_path / ".kensaiapp" / "venv" / "bin"
    present.mkdir(parents=True)
    (present / "present-command").write_text("#!/bin/sh\n")
    (present / "present-command").chmod(0o755)
    assert real_package_skip_reason({COMMAND_VARIABLE: "present-command"}, tmp_path) is None


# --- the failure boundary, with fixture executables ----------------------------------------------

BASE_ENV = {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
    ENDPOINT_KEY: VALID_ENDPOINT,
}
GOOD_ATTRIBUTES = "kensai.run_id=0a1b2c3d-0a1b-4c3d-8a1b-0a1b2c3d4e5f,kensai.instance=fixture"


def _document(**overrides) -> str:
    env = {**BASE_ENV, ATTRIBUTES_KEY: GOOD_ATTRIBUTES}
    env.update(overrides)
    return json.dumps({"env": {k: v for k, v in env.items() if v is not ...}})


def _printing(stdout: str, *, status: int = 0, stderr: str = "") -> str:
    return (
        "#!/bin/sh\n"
        f"cat <<'END_OF_FIXTURE'\n{stdout}\nEND_OF_FIXTURE\n"
        f"cat >&2 <<'END_OF_FIXTURE'\n{stderr}\nEND_OF_FIXTURE\n"
        f"exit {status}\n"
    )


FAILURE_FIXTURES = {
    "missing-executable": None,
    "not-executable": ("#!/bin/sh\necho '{}'\n", 0o644),
    "cannot-start": ("#!/nonexistent/interpreter\n", 0o755),
    "nonzero-exit": (_printing("", status=7, stderr=RAW_OUTPUT_MARKER), 0o755),
}
FAILURE_LINE = {
    "missing-executable": "no runnable telemetry command at {path}",
    "not-executable": "no runnable telemetry command at {path}",
    "cannot-start": "telemetry command at {path} could not be started",
    "nonzero-exit": "telemetry command at {path} exited with status 7",
}


UNCONFIGURED_LINE = (
    "          (no telemetry command configured in KENSAIAPP_TELEMETRY_COMMAND — "
    "run uninstrumented)"
)


def _scratch_helper(
    root: Path, *, setting: str | None, pinned: bool = False, resolver: str | None = "real",
    name: str = "scratch",
) -> Path:
    """A copy of the helper and the resolver's collaborators in a scratch host (or a pin of one).

    ``setting`` is the host's ``.telemetry.env`` text, or None for no file. ``resolver`` is
    ``"real"`` to copy the resolver, None to leave it out, or the text of a stand-in resolver.
    Returns the helper copy: the path a launcher's ``source`` line would name.
    """
    host = root / f"{name}-host"
    (host / "core" / "tools").mkdir(parents=True)
    if setting is not None:
        (host / ".telemetry.env").write_text(setting, encoding="utf-8")
    core = host / "core"
    if pinned:
        core = root / f"{name}-pins" / "p1" / "core"
        (core / "tools").mkdir(parents=True)
        (core.parent / "pin.json").write_text(
            json.dumps({"id": "p1", "source_host_root": str(host)}), encoding="utf-8"
        )
    tools = core / "tools"
    shutil.copy2(_HELPER, tools / "run_telemetry.sh")
    for sibling in ("pin.py", "env_file.py"):
        shutil.copy2(_TOOLS / sibling, tools / sibling)
    if resolver == "real":
        shutil.copy2(_TOOLS / "telemetry_command.py", tools / "telemetry_command.py")
    elif resolver is not None:
        (tools / "telemetry_command.py").write_text(resolver, encoding="utf-8")
    return tools / "run_telemetry.sh"


def _only_cause_line(outcome: Outcome) -> str:
    assert len(outcome.lines) == 1, outcome.lines
    return outcome.lines[0]


@pytest.mark.parametrize("cap", ["250000", None], ids=["with-cap", "without-cap"])
@pytest.mark.parametrize("kind", list(FAILURE_FIXTURES))
def test_package_failure_keeps_strict_shell_caller_successful(rig: Rig, kind, cap):
    """F1: an unavailable, unstartable or failing command leaves the run uninstrumented with one
    cause line, the cap alone in the settings, and no raw package output forwarded."""
    spec = FAILURE_FIXTURES[kind]
    if spec is not None:
        rig.install(FIXTURE_COMMAND, spec[0], mode=spec[1])
    path = rig.home / ".kensaiapp" / "venv" / "bin" / FIXTURE_COMMAND
    outcome = rig.call(_HELPER, ["skill=a"], env={CAP_KEY: cap} if cap else {})
    assert outcome.returncode == 0, outcome.stderr
    assert _only_cause_line(outcome) == (
        f"          ({FAILURE_LINE[kind].format(path=path)} — run uninstrumented)"
    )
    assert outcome.exports == {}
    assert outcome.settings == ({"env": {CAP_KEY: cap}} if cap else None)
    assert RAW_OUTPUT_MARKER not in "".join(outcome.lines) + outcome.stderr


INVALID_DOCUMENTS = {
    "invalid-json": "{not json",
    "empty-output-without-an-endpoint-cause": "",
    "json-array": "[]",
    "json-string": json.dumps("text"),
    "env-missing": json.dumps({"other": {}}),
    "env-not-an-object": json.dumps({"env": ["a"]}),
    "base-key-missing": _document(CLAUDE_CODE_ENABLE_TELEMETRY=...),
    "base-key-not-a-string": _document(OTEL_METRICS_EXPORTER=1),
    "endpoint-missing": _document(**{ENDPOINT_KEY: ...}),
    "attributes-missing": _document(**{ATTRIBUTES_KEY: ...}),
    "attributes-not-a-string": _document(**{ATTRIBUTES_KEY: ["kensai.run_id=x"]}),
    "attribute-without-equals": _document(**{ATTRIBUTES_KEY: GOOD_ATTRIBUTES + ",broken"}),
    "attribute-with-empty-key": _document(**{ATTRIBUTES_KEY: GOOD_ATTRIBUTES + ",=value"}),
    "no-run-id": _document(**{ATTRIBUTES_KEY: "kensai.instance=fixture"}),
    "newline-in-a-value": _document(OTEL_LOGS_EXPORTER="otlp\nEXPORT\tINJECTED\tx"),
    "tab-in-a-value": _document(**{ATTRIBUTES_KEY: GOOD_ATTRIBUTES + ",kensai.a=b\tc"}),
}


@pytest.mark.parametrize("cap", ["250000", None], ids=["with-cap", "without-cap"])
@pytest.mark.parametrize("kind", list(INVALID_DOCUMENTS))
def test_invalid_package_document_never_becomes_settings(rig: Rig, kind, cap):
    """F1: whatever the command prints that is not a settings document of the expected shape falls
    back, once, to the cap alone; nothing of it reaches the settings or the exports."""
    rig.install(FIXTURE_COMMAND, _printing(INVALID_DOCUMENTS[kind], stderr=RAW_OUTPUT_MARKER))
    path = rig.home / ".kensaiapp" / "venv" / "bin" / FIXTURE_COMMAND
    outcome = rig.call(_HELPER, ["skill=a"], env={CAP_KEY: cap} if cap else {})
    assert outcome.returncode == 0, outcome.stderr
    assert _only_cause_line(outcome) == (
        f"          (telemetry command at {path} did not print a usable settings document"
        " — run uninstrumented)"
    )
    assert outcome.exports == {}
    assert outcome.settings == ({"env": {CAP_KEY: cap}} if cap else None)
    assert "INJECTED" not in json.dumps(outcome.environ)
    assert RAW_OUTPUT_MARKER not in "".join(outcome.lines) + outcome.stderr


def test_output_resembling_shell_commands_remains_data(rig: Rig):
    """F1: a valid document whose values read like shell is exported as the text it is."""
    marker = rig.tmp_path / "evaluated"
    hostile = f"$(touch {marker}) `touch {marker}` ; touch {marker}"
    inert = hostile.replace(",", "")
    rig.install(
        FIXTURE_COMMAND,
        _printing(_document(**{ATTRIBUTES_KEY: GOOD_ATTRIBUTES + ",kensai.x=" + inert})),
    )
    outcome = rig.call(_HELPER, [])
    assert outcome.returncode == 0, outcome.stderr
    assert not marker.exists()
    assert inert in outcome.environ[ATTRIBUTES_KEY]
    assert inert in outcome.settings["env"][ATTRIBUTES_KEY]


@pytest.mark.parametrize(
    "configured",
    ["a/b", "../fixture", "/abs/path/command", "command argument", "command;touch MARKER",
     "$(touch MARKER)", "`touch MARKER`", ".hidden", "-option", "star*", "tab\tname", "quote'name"],
)
def test_configuration_accepts_only_one_executable_basename(rig: Rig, configured):
    """F1: separators, arguments and shell syntax cannot run another path or payload, and a bare
    name is never looked up on PATH."""
    marker = rig.tmp_path / "MARKER"
    configured = configured.replace("MARKER", str(marker))
    rig.install(FIXTURE_COMMAND, f"#!/bin/sh\ntouch {shlex.quote(str(marker))}\n")
    outcome = rig.call(_HELPER, ["skill=a"], env={COMMAND_VARIABLE: configured})
    assert outcome.returncode == 0, outcome.stderr
    assert _only_cause_line(outcome) == (
        "          (KENSAIAPP_TELEMETRY_COMMAND is not a plain command name (name only, no path or "
        "arguments) — run uninstrumented)"
    )
    assert outcome.exports == {} and outcome.settings is None
    assert not marker.exists()


@pytest.mark.parametrize("configured", [None, ""], ids=["absent", "empty"])
def test_missing_configuration_is_an_ordinary_fallback(rig: Rig, configured):
    """An empty value is explicit and reads as unconfigured. An absent one with no setting on the
    core's host does too: the discovery asks a scratch host that holds no setting file."""
    rig.install(FIXTURE_COMMAND, "#!/bin/sh\nexit 0\n")
    library = _HELPER
    if configured is None:
        library = _scratch_helper(rig.tmp_path, setting=None)
    outcome = rig.call(library, ["skill=a"], env={COMMAND_VARIABLE: configured})
    assert outcome.returncode == 0, outcome.stderr
    assert _only_cause_line(outcome) == UNCONFIGURED_LINE


def test_a_bare_name_is_never_searched_on_path(rig: Rig):
    marker = rig.tmp_path / "found-on-path"
    on_path = rig.tmp_path / "bin-on-path"
    on_path.mkdir()
    command = on_path / FIXTURE_COMMAND
    command.write_text(f"#!/bin/sh\ntouch {shlex.quote(str(marker))}\n")
    command.chmod(0o755)
    outcome = rig.call(_HELPER, ["skill=a"], env={"PATH": f"{on_path}:{os.environ['PATH']}"})
    path = rig.home / ".kensaiapp" / "venv" / "bin" / FIXTURE_COMMAND
    assert _only_cause_line(outcome) == (
        f"          (no runnable telemetry command at {path} — run uninstrumented)"
    )
    assert not marker.exists()


GOOD_FIXTURE = _printing(_document(), stderr="          Telemetry:    the package's own line")


def test_each_invocation_discards_inherited_settings(rig: Rig):
    """F1: a settings document inherited from whatever started the caller is never forwarded —
    not on success (the call's own replaces it), not on a failure (the cap alone, or nothing) —
    and a failure after a success in one shell forwards nothing of the success."""
    sentinel = json.dumps({"env": {"INHERITED": "sentinel"}})
    inherited = {SETTINGS_KEY: sentinel}

    failing = rig.call(
        _HELPER, ["skill=a"], env={**inherited, COMMAND_VARIABLE: "absent-command"}
    )
    assert failing.settings is None
    capped = rig.call(_HELPER, ["skill=a"],
                      env={**inherited, COMMAND_VARIABLE: "absent-command", CAP_KEY: "9"})
    assert capped.settings == {"env": {CAP_KEY: "9"}}

    rig.install(FIXTURE_COMMAND, GOOD_FIXTURE)
    succeeding = rig.call(_HELPER, ["skill=a"], env=inherited)
    assert "INHERITED" not in json.dumps(succeeding.settings)
    assert succeeding.settings["env"][ATTRIBUTES_KEY] == succeeding.environ[ATTRIBUTES_KEY]

    sequence = rig.call(
        _HELPER, [],
        body='run_telemetry skill=a >/dev/null; export KENSAIAPP_TELEMETRY_COMMAND=absent-command; '
        'run_telemetry skill=a >/dev/null',
    )
    assert sequence.returncode == 0, sequence.stderr
    assert sequence.settings is None


def test_a_fallback_leaves_an_existing_telemetry_export_untouched(rig: Rig):
    """F1: the helper does not unset what the caller already exported, and exports nothing new when
    it falls back."""
    outcome = rig.call(
        _HELPER, ["skill=a"],
        env={COMMAND_VARIABLE: "absent-command", ENDPOINT_KEY: "http://pre-existing:1"},
    )
    assert outcome.environ[ENDPOINT_KEY] == "http://pre-existing:1"
    assert outcome.exports == {ENDPOINT_KEY: "http://pre-existing:1"}


def test_success_prints_one_normalized_telemetry_line(real: Rig, tmp_path: Path):
    """E1/F1: a successful call prints exactly one `Telemetry:` line, with the CP-651 indentation,
    the normalised pair order and the endpoint once; the package's own line on stderr is consumed.
    The package argv is read through a forwarding observer that still runs the real command."""
    observer_home = tmp_path / "observer-home"
    observer_bin = observer_home / ".kensaiapp" / "venv" / "bin"
    observer_bin.mkdir(parents=True)
    log = tmp_path / "argv.log"
    real_command = REAL_HOME / ".kensaiapp" / "venv" / "bin" / real.command_name
    observer = observer_bin / "observer"
    observer.write_text(
        "#!/bin/sh\n"
        f"printf '%s\\n' \"$@\" > {shlex.quote(str(log))}\n"
        f"exec {shlex.quote(str(real_command))} \"$@\"\n"
    )
    observer.chmod(0o755)
    real.home = observer_home
    real.command_name = "observer"
    chain = {
        "INSTRUMENT_RUN_WALK_ID": "w1", "INSTRUMENT_RUN_CHAIN": "c1",
        "INSTRUMENT_RUN_ROLE": "developer", "INSTRUMENT_RUN_AUDIT_TARGET": "t1",
    }
    args = [f"{key}=value-of-{key}" for key in ACCEPTED_KEYS]
    outcome = real.call(_HELPER, args, env=chain)
    assert outcome.returncode == 0, outcome.stderr
    assert outcome.stderr == ""
    attributes = outcome.environ[ATTRIBUTES_KEY]
    assert outcome.lines == [
        f"          Telemetry:    {attributes} → {VALID_ENDPOINT}"
    ]
    argv = log.read_text().splitlines()
    assert argv[:7] == ["turn-on", "--print", "--endpoint-file", str(real.endpoint_file),
                        "--prefix", "kensai", "--label"]
    label_values = [argv[i + 1] for i, token in enumerate(argv) if token == "--label"]
    assert label_values == [
        "arm=skill",
        *[f"{key}=value-of-{key}" for key in ACCEPTED_KEYS],
        "walk_id=w1", "chain=c1", "role=developer", "audit_target=t1",
    ]
    assert [pair.partition("=")[0] for pair in attributes.split(",")][:3] == [
        "kensai.arm", "kensai.run_id", "kensai.instance"
    ]


# --- command discovery: the name when the environment gives none ---------------------------------


def _setting(name: str) -> str:
    return f"{COMMAND_VARIABLE}={name}\n"


@pytest.mark.parametrize("pinned", [False, True], ids=["direct-core", "pinned-core"])
def test_absent_environment_discovers_source_host_command(rig: Rig, pinned):
    """A real helper call with no command variable runs the command its core's source host names,
    from an unrelated working directory, direct or through a pin."""
    rig.install(FIXTURE_COMMAND, GOOD_FIXTURE)
    library = _scratch_helper(rig.tmp_path, setting=_setting(FIXTURE_COMMAND), pinned=pinned)
    outcome = rig.call(library, ["skill=a"], env={COMMAND_VARIABLE: None})
    assert outcome.returncode == 0, outcome.stderr
    assert outcome.stderr == ""
    assert len(_telemetry_lines(outcome)) == 1, outcome.lines
    assert outcome.exports[ENDPOINT_KEY] == VALID_ENDPOINT
    assert outcome.settings["env"][ENDPOINT_KEY] == VALID_ENDPOINT


@pytest.mark.parametrize(
    ("value", "line"),
    [
        ("absent-command", "(no runnable telemetry command at {home}/.kensaiapp/venv/bin/"
                           "absent-command — run uninstrumented)"),
        ("", "(no telemetry command configured in KENSAIAPP_TELEMETRY_COMMAND — "
             "run uninstrumented)"),
        ("not/a-name", "(KENSAIAPP_TELEMETRY_COMMAND is not a plain command name (name only, "
                       "no path or arguments) — run uninstrumented)"),
    ],
    ids=["unavailable", "empty", "invalid"],
)
@pytest.mark.parametrize("resolver", ["real", None], ids=["resolver-present", "resolver-missing"])
def test_explicit_value_including_empty_bypasses_discovery(rig: Rig, value, line, resolver):
    """Membership decides: an explicit value keeps its current handling whatever the setting says,
    and without consulting a resolver that may not even be there."""
    rig.install(FIXTURE_COMMAND, GOOD_FIXTURE)
    library = _scratch_helper(
        rig.tmp_path, setting=_setting(FIXTURE_COMMAND), resolver=resolver
    )
    outcome = rig.call(library, ["skill=a"], env={COMMAND_VARIABLE: value})
    assert outcome.returncode == 0, outcome.stderr
    assert _only_cause_line(outcome) == "          " + line.format(home=rig.home)
    assert outcome.exports == {} and outcome.settings is None


def test_an_explicit_command_works_without_a_resolver(rig: Rig):
    rig.install(FIXTURE_COMMAND, GOOD_FIXTURE)
    library = _scratch_helper(rig.tmp_path, setting=None, resolver=None)
    outcome = rig.call(library, ["skill=a"], env={COMMAND_VARIABLE: FIXTURE_COMMAND})
    assert len(_telemetry_lines(outcome)) == 1, outcome.lines


RESOLVER_FAILURES = {
    "missing": None,
    "exits-non-zero": "import sys\nprint('resolver diagnostic', file=sys.stderr)\nsys.exit(3)\n",
    "exits-non-zero-after-printing-a-name": (
        "import sys\nprint('fixture-command')\nprint('resolver diagnostic', file=sys.stderr)\n"
        "sys.exit(1)\n"
    ),
    "does-not-start": "this is not python (\n",
    "garbled-multiline": "print('fixture-command')\nprint('and another line')\n",
}


@pytest.mark.parametrize("cap", ["250000", None], ids=["with-cap", "without-cap"])
@pytest.mark.parametrize("kind", list(RESOLVER_FAILURES))
def test_missing_or_failed_resolver_is_unconfigured(rig: Rig, kind, cap):
    """A resolver that is missing, fails, cannot start or garbles its answer leaves an absent
    command unconfigured: the one existing stdout cause, no diagnostic of the resolver's, a
    successful return and the cap alone in the settings."""
    rig.install(FIXTURE_COMMAND, GOOD_FIXTURE)
    library = _scratch_helper(
        rig.tmp_path, setting=_setting(FIXTURE_COMMAND), resolver=RESOLVER_FAILURES[kind]
    )
    extra = {COMMAND_VARIABLE: None, **({CAP_KEY: cap} if cap else {})}
    outcome = rig.call(library, ["skill=a"], env=extra)
    assert outcome.returncode == 0, outcome.stderr
    assert _only_cause_line(outcome) == UNCONFIGURED_LINE
    assert outcome.stderr == ""
    assert outcome.exports == {}
    assert outcome.settings == ({"env": {CAP_KEY: cap}} if cap else None)


@pytest.mark.parametrize(
    "data",
    ["a/b", "$(touch MARKER)", "`touch MARKER`", "name;touch MARKER", "two words", ".hidden"],
)
def test_invalid_configured_name_uses_existing_validation(rig: Rig, data):
    """A setting's value is data: never evaluated, never an executable path or an argv."""
    marker = rig.tmp_path / "MARKER"
    data = data.replace("MARKER", str(marker))
    rig.install(FIXTURE_COMMAND, f"#!/bin/sh\ntouch {shlex.quote(str(marker))}\n")
    library = _scratch_helper(rig.tmp_path, setting=f'{COMMAND_VARIABLE}="{data}"\n')
    outcome = rig.call(library, ["skill=a"], env={COMMAND_VARIABLE: None})
    assert outcome.returncode == 0, outcome.stderr
    assert _only_cause_line(outcome) == (
        "          (KENSAIAPP_TELEMETRY_COMMAND is not a plain command name (name only, no path "
        "or arguments) — run uninstrumented)"
    )
    assert not marker.exists()


def test_sourcing_with_setting_has_no_effects(rig: Rig):
    """With a setting present and a resolver that would leave a trace, sourcing alone prints
    nothing, starts nothing, exports nothing and sets no shell option."""
    marker = rig.tmp_path / "resolver-ran"
    library = _scratch_helper(
        rig.tmp_path, setting=_setting(FIXTURE_COMMAND),
        resolver=f"import pathlib\npathlib.Path({str(marker)!r}).write_text('ran')\nprint('x')\n",
    )
    control = rig.call(_HELPER, [], body=":", before="OPTIONS_BEFORE=$-",
                       env={COMMAND_VARIABLE: None})
    sourced = rig.call(
        library, [], env={COMMAND_VARIABLE: None}, before="OPTIONS_BEFORE=$-",
        body='test "$(type -t run_telemetry)" = function || exit 9; echo "OPTIONS_AFTER=$-"',
    )
    assert sourced.returncode == 0, sourced.stderr
    assert sourced.stderr == ""
    assert sourced.lines[:-1] == []
    assert sourced.lines[-1].startswith("OPTIONS_AFTER=")
    assert sourced.environ == control.environ
    assert not marker.exists()
