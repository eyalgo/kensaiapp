"""Test support for showing what a launcher gets from `run_telemetry`.

Each instrumented launcher's own suite runs the launcher once over the real helper
(`core/tools/run_telemetry.sh`, over the telemetry package) and states the complete observation its
own inputs call for. This module owns everything those suites share, so six suites make the check
one way rather than six. No production file imports it.

WHAT IT PROVIDES
    `run_launcher`      runs one launcher and returns what it printed, its status, the six
                        telemetry exports and the settings its provider was handed.
    `assert_instrumented_observation`
                        holds a launch to the literal observation a case states: the one
                        `Telemetry:` line, six exports, exported and handed settings.
    `assert_uninstrumented`
                        holds a launch with no telemetry to the cap alone, or nothing.
    `assert_run_telemetry_call_carries_provenance`
                        the same-line four-key check every launcher's suite makes of its own call.
    `require_real_package`
                        a scratch HOME linked to the installed package, or the skip that names what
                        is missing (CP-689).
    `scratch_core` `make_pin` `bind_satellite` `write_host_setting`
                        the trees a launcher is run in: a core of its own (the real tools, minus
                        their tests), a pin of it, and a satellite that binds it.
    `ordinary_launch` `assert_ordinary_launch_is_instrumented`
                        the four ordinary launches of CP-692 and what each must print and hand over.
    `failure_scenario` `assert_failure_scenario`
                        the failure matrix of CP-687, CP-693 and CP-694, one controlled cause each.
    `assert_selection_skips_unreachable_and_fails_reached`
                        a launcher suite's own observation run in nested pytests, to show that an
                        unreachable package skips it and a reached command that fails fails it.

HOW A LAUNCHER IS OBSERVED
    A launcher exports its telemetry to its own shell and hands its settings to the provider on the
    command line. The settings are read off what the dry run prints. The exports are read by a
    Bash startup file (`BASH_ENV`) that registers an EXIT trap: when the launcher's shell exits it
    appends the seven allowlisted names (`OBSERVED_NAMES`) — never the environment — to a file,
    keyed by the shell's process id. The reader keeps only the launcher's own process id, so a
    child shell that records itself, or tries to overwrite a name, changes nothing. The trap only
    appends to a file and returns, so it alters no output and no status. A launcher that `exec`s
    its provider leaves no exit to observe; only dry runs are observed.
"""

from __future__ import annotations

import base64
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

import pytest

import telemetry_command

__version__ = "1.1.0"

COMMAND_VARIABLE = "KENSAIAPP_TELEMETRY_COMMAND"
SETTINGS_NAME = "INSTRUMENT_RUN_SETTINGS"
ATTRIBUTES_NAME = "OTEL_RESOURCE_ATTRIBUTES"
TELEMETRY_EXPORT_NAMES = (
    "CLAUDE_CODE_ENABLE_TELEMETRY",
    "OTEL_METRICS_EXPORTER",
    "OTEL_LOGS_EXPORTER",
    "OTEL_EXPORTER_OTLP_PROTOCOL",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    ATTRIBUTES_NAME,
)
OBSERVED_NAMES = TELEMETRY_EXPORT_NAMES + (SETTINGS_NAME,)
CAP_NAME = "KENSAIAPP_CONTEXT_CAP"
LOOPBACK_ENDPOINT = "http://127.0.0.1:4318"

_TOOLS = Path(__file__).resolve().parent
_CORE_DIR = _TOOLS.parent

# The home the real package is installed under. Read once, before any case isolates HOME.
REAL_HOME = Path.home()

# --- the observer ---------------------------------------------------------------------------------

_OBSERVER = r"""# Test-only observer: records the allowlisted names when the launcher's shell exits.
_ka_obs_dump() {
  # The launcher's own options reach this trap: under `set -e` and `pipefail` a failed lookup below
  # (no such function) would end the shell with that failure as its status. The shell is exiting,
  # so lifting them here changes nothing the launcher does.
  set +e +u +o pipefail
  local name state value file
  [ -n "${KA_OBS_FILE:-}" ] || return 0
  {
    for name in __NAMES__; do
      if [ -n "${!name+set}" ]; then state=set; else state=unset; fi
      value="$(printf '%s' "${!name-}" | base64 | tr -d '\n')"
      printf 'VAR %s %s %s %s\n' "$$" "$name" "$state" "$value"
    done
    shopt -s extdebug
    file="$(declare -F run_telemetry 2>/dev/null | { read -r _ _ file; printf '%s' "$file"; })"
    shopt -u extdebug
    printf 'HELPER %s %s\n' "$$" "$file"
  } >> "$KA_OBS_FILE" 2>/dev/null
  return 0
}
trap '_ka_obs_dump' EXIT
""".replace("__NAMES__", " ".join(OBSERVED_NAMES))

_CALL_END = "\x01"


@dataclass(frozen=True)
class Observation:
    """One launch of one launcher: what it printed and exited with, the telemetry names its shell
    held when it exited (`None` for an unset name; empty when it was not observed) and the
    settings its provider was handed (`None` when it was handed none)."""

    status: int
    stdout: str
    stderr: str
    exports: dict[str, str | None]
    handed_settings: dict | None
    helper_source: str | None
    record: str = field(default="", compare=False)

    @property
    def telemetry_lines(self) -> list[str]:
        return [line for line in self.stdout.splitlines() if _is_telemetry_line(line)]

    @property
    def stderr_telemetry_lines(self) -> list[str]:
        return [line for line in self.stderr.splitlines() if _is_telemetry_line(line)]


_NOTICE_PREFIXES = (
    "(kensai.",
    "(unknown telemetry key",
    "(telemetry argument",
)
_INDENT = " " * 10


def _is_telemetry_line(line: str) -> bool:
    """A line the helper prints: the `Telemetry:` line, a refusal, or a
    `(<cause> — run uninstrumented)` line — all indented ten columns."""
    if not line.startswith(_INDENT):
        return False
    stripped = line.strip()
    if stripped.startswith("Telemetry:"):
        return True
    if not (stripped.startswith("(") and stripped.endswith(")")):
        return False
    return "run uninstrumented)" in stripped or stripped.startswith(_NOTICE_PREFIXES)


# --- running a launcher ---------------------------------------------------------------------------


def _write_observer(directory: Path) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    observer = directory / "observer.sh"
    observer.write_text(_OBSERVER)
    record = directory / "observation.log"
    record.write_text("")
    return observer, record


def _read_record(record_text: str, pid: int) -> tuple[dict[str, str | None], str | None]:
    """The names and the helper's source the launcher's own process recorded, last record wins."""
    exports: dict[str, str | None] = {}
    helper: str | None = None
    for line in record_text.splitlines():
        kind, _, rest = line.partition(" ")
        owner, _, rest = rest.partition(" ")
        if owner != str(pid):
            continue
        if kind == "VAR":
            name, state, encoded = rest.split(" ")
            exports[name] = (
                base64.b64decode(encoded).decode("utf-8", errors="replace")
                if state == "set"
                else None
            )
        elif kind == "HELPER":
            helper = rest or None
    return exports, helper


def _settings_document(token: str) -> dict | None:
    """The document one `--settings` value is: the JSON itself, or — the form a pinned launch
    hands, its merged document being a file — the JSON in the file the value names."""
    try:
        return json.loads(token)
    except (ValueError, TypeError):
        pass
    try:
        return json.loads(Path(token).read_text())
    except (OSError, ValueError):
        return None


def _handed_settings(stdout: str) -> dict | None:
    """The settings document a dry run hands its provider on `--settings`, or `None`. A fan-out
    that hands the same document to several runs is one answer; differing documents fail."""
    documents = []
    for match in re.finditer(r"--settings[ =]", stdout):
        lexer = shlex.shlex(stdout[match.end() :], posix=True)
        lexer.whitespace_split = True
        document = _settings_document(lexer.get_token() or "")
        if document is not None:
            documents.append(document)
    assert all(document == documents[0] for document in documents), (
        f"the launch handed different settings documents to its runs: {documents}"
    )
    return documents[0] if documents else None


def run_launcher(
    launcher: Path,
    argv: Iterable[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    observation_dir: Path | None = None,
    timeout: float = 300,
) -> Observation:
    """Run `launcher` with `argv` from `cwd` in `env` and return the observation. Given an
    `observation_dir` the launcher's shell is observed at exit; without one `exports` is empty."""
    assert "BASH_ENV" not in env, "BASH_ENV is the observer's; the environment must not set it"
    run_env = dict(env)
    record_file = None
    if observation_dir is not None:
        observer, record_file = _write_observer(observation_dir)
        run_env["BASH_ENV"] = str(observer)
        run_env["KA_OBS_FILE"] = str(record_file)
    process = subprocess.Popen(
        [str(launcher), *argv],
        cwd=str(cwd),
        env=run_env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = process.communicate(timeout=timeout)
    exports: dict[str, str | None] = {}
    helper: str | None = None
    record = ""
    if record_file is not None:
        record = record_file.read_text()
        exports, helper = _read_record(record, process.pid)
        assert exports, (
            f"{launcher}: no observation was recorded for the launcher's own process "
            f"{process.pid} — it exited without running its shell's exit (an exec, or a kill)"
        )
    return Observation(
        status=process.returncode,
        stdout=stdout,
        stderr=stderr,
        exports=exports,
        handed_settings=_handed_settings(stdout),
        helper_source=helper,
        record=record,
    )


def _comparable_settings(exports: Mapping[str, str | None]) -> object:
    raw = exports.get(SETTINGS_NAME)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def assert_uninstrumented(observation: Observation, *, cap: str | None) -> None:
    """Fail unless the launch ran with no telemetry: one `(<cause> — run uninstrumented)` line and
    no `Telemetry:` line, none of the six exports, and settings that carry the context cap alone
    when `cap` is given and nothing at all otherwise."""
    lines = observation.telemetry_lines
    assert lines and not any(line.strip().startswith("Telemetry:") for line in lines), lines
    assert not observation.stderr_telemetry_lines, observation.stderr_telemetry_lines
    for name in TELEMETRY_EXPORT_NAMES:
        assert observation.exports.get(name) is None, f"{name} is exported: {observation.exports}"
    if cap is None:
        assert observation.exports.get(SETTINGS_NAME) in (None, ""), observation.exports
        assert observation.handed_settings is None, observation.handed_settings
        return
    expected = {"env": {CAP_NAME: cap}}
    assert _comparable_settings(observation.exports) == expected, observation.exports
    assert observation.handed_settings == expected, observation.handed_settings


# The four exports the package sets whatever the run, and the shape of the run id it generates.
BASE_TELEMETRY_EXPORTS = {
    "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
}
_RUN_ID_PREFIX = "kensai.run_id="
_RUN_ID_SHAPE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_TELEMETRY_LINE_PATTERN = re.compile(
    r"^ {10}Telemetry: {4}(?P<attributes>\S*) → (?P<endpoint>\S+)$"
)


def assert_instrumented_observation(
    observation: Observation,
    *,
    pairs: Iterable[tuple[str, str | None]],
    helper: Path,
    endpoint: str = LOOPBACK_ENDPOINT,
    cap: str | None = None,
) -> None:
    """Fail unless an instrumented dry run is exactly what the case states: status 0,
    `run_telemetry` defined by `helper`, no telemetry on stderr, the one `Telemetry:` line, all six
    exports, the exported settings document and the settings handed to the provider.

    `pairs` are the case's own `kensai.*` attributes in order, each key without its prefix; the one
    value a case cannot state, the run id the package generates, is `None`. It is matched by shape
    (a lowercase UUID) and the value found must be the one every representation carries. Nothing
    else is read back from the observation: the expected lines, exports and settings are built from
    `pairs`, `endpoint` and `cap` alone."""
    run_id = None
    found = observation.telemetry_lines
    assert len(found) == 1, f"expected the one Telemetry: line and no other: {found}"
    shown = _TELEMETRY_LINE_PATTERN.match(found[0])
    assert shown, f"not a Telemetry: line: {found[0]!r}"
    for attribute in shown["attributes"].split(","):
        if attribute.startswith(_RUN_ID_PREFIX):
            run_id = attribute.removeprefix(_RUN_ID_PREFIX)
    assert run_id is not None and _RUN_ID_SHAPE.fullmatch(run_id), found[0]
    attributes = ",".join(
        f"kensai.{key}={run_id if value is None else value}" for key, value in pairs
    )
    environment = {
        **BASE_TELEMETRY_EXPORTS,
        "OTEL_EXPORTER_OTLP_ENDPOINT": endpoint,
        **({CAP_NAME: cap} if cap else {}),
        ATTRIBUTES_NAME: attributes,
    }
    assert observation.status == 0, _failure_report(observation)
    assert observation.helper_source and (
        Path(observation.helper_source).resolve() == Path(helper).resolve()
    ), f"run_telemetry was defined by {observation.helper_source}, not {helper}"
    assert not observation.stderr_telemetry_lines, observation.stderr_telemetry_lines
    assert found == [f"          Telemetry:    {attributes} → {endpoint}"]
    assert {name: observation.exports.get(name) for name in TELEMETRY_EXPORT_NAMES} == {
        name: environment[name] for name in TELEMETRY_EXPORT_NAMES
    }
    assert _comparable_settings(observation.exports) == {"env": environment}
    assert observation.handed_settings == {"env": environment}


# --- the real package -----------------------------------------------------------------------------

SKIP_UNSET = (
    "equivalence comparison not run: KENSAIAPP_TELEMETRY_COMMAND is unset or empty, so the "
    "telemetry package's command cannot be found — set it to the command's name in "
    "~/.kensaiapp/venv/bin"
)
SKIP_NOT_PLAIN = (
    "equivalence comparison not run: KENSAIAPP_TELEMETRY_COMMAND is not a plain command name "
    "(name only, no path or arguments)"
)


def skip_reason_unreachable(path: Path) -> str:
    return (
        f"equivalence comparison not run: no runnable telemetry command at {path} — install the "
        "package in ~/.kensaiapp/venv, or correct KENSAIAPP_TELEMETRY_COMMAND"
    )


def real_package_skip_reason(environ: Mapping[str, str], home: Path) -> str | None:
    """Why the real-package comparison cannot run here, or None when it can."""
    name = environ.get(COMMAND_VARIABLE, "")
    if not name:
        return SKIP_UNSET
    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9._-]*", name):
        return SKIP_NOT_PLAIN
    path = home / ".kensaiapp" / "venv" / "bin" / name
    if not (path.is_file() and os.access(path, os.X_OK)):
        return skip_reason_unreachable(path)
    return None


@dataclass(frozen=True)
class RealPackage:
    """A scratch HOME whose `.kensaiapp/venv` is the installed one, and the command's name."""

    home: Path
    command: str


def require_real_package(
    tmp_path: Path, *, environ: Mapping[str, str] | None = None, real_home: Path | None = None
) -> RealPackage:
    """The real package, reached through a scratch HOME under `tmp_path`, or the pytest skip that
    names what is missing. The command's name is discovered exactly as a launch discovers it —
    from the environment, else from the source host's setting — before any HOME is isolated, so
    nothing here names it. A command that is reached and then breaks the contract is not a skip:
    the comparison that runs it fails."""
    inherited = os.environ if environ is None else environ
    discovered = telemetry_command.resolve(_CORE_DIR, dict(inherited))
    reason = real_package_skip_reason(
        {COMMAND_VARIABLE: discovered}, REAL_HOME if real_home is None else real_home
    )
    if reason:
        pytest.skip(reason)
    home = tmp_path / "home"
    (home / ".kensaiapp").mkdir(parents=True)
    source_home = REAL_HOME if real_home is None else real_home
    (home / ".kensaiapp" / "venv").symlink_to(source_home / ".kensaiapp" / "venv")
    return RealPackage(home=home, command=discovered)


# --- the provenance assertion ---------------------------------------------------------------------

PROVENANCE_KEYS = ("provider", "model", "effort", "source")
_CALL = "run_telemetry"


def _is_run_telemetry_call(line: str) -> bool:
    stripped = line.strip()
    return stripped == _CALL or stripped.startswith(f"{_CALL} ")


def _keys_on(line: str) -> set[str]:
    """The `key=` words the call line itself hands over. A trailing `\\` continues the call onto a
    line this never reads, which is the point: the keys must sit on the call's own line."""
    words = shlex.split(line.strip().removesuffix("\\"), comments=True)
    return {word.split("=", 1)[0] for word in words[1:] if "=" in word}


def assert_run_telemetry_call_carries_provenance(launcher: Path) -> None:
    """Fail unless every `run_telemetry` call in `launcher` carries all four provenance keys on its
    own line. A file with no call fails too, naming the file — an absent call is not a pass. A
    comment, a definition, a `source` line and a lookalike name are not calls."""
    calls = [
        line for line in Path(launcher).read_text().splitlines() if _is_run_telemetry_call(line)
    ]
    assert calls, f"{launcher}: no run_telemetry call on any non-comment line"
    for call in calls:
        missing = [key for key in PROVENANCE_KEYS if key not in _keys_on(call)]
        assert not missing, (
            f"{launcher}: the run_telemetry call does not hand over {', '.join(missing)} "
            f"on its own line: {call.strip()!r}"
        )


# --- the trees a launcher is run in ---------------------------------------------------------------

SETTING_FILE = ".telemetry.env"

# What a scratch core takes from the real one. The tools come without their tests, their caches and
# the panel (a separate app); every other top-level folder of the real core is reached by symlink,
# because a launcher reads its prompts and templates and writes nothing there.
_TOOLS_IGNORE = shutil.ignore_patterns(
    "test_*", "__pycache__", "*.pyc", "tests", "kensaiapp-panel", "conftest.py"
)
_LAUNCHER_IGNORE = shutil.ignore_patterns("test_*", "__pycache__", "*.pyc", "conftest.py")
_BORROWED = ("tools", "launchers")


def scratch_core(root: Path, script: Path, *, siblings: Iterable[str] = ()) -> Path:
    """A core at `root/core` holding a copy of the real tools and of the launcher at `script`
    (plus each sibling launcher named, for a launcher that runs another), so a comparison can put
    other bytes at the helper's path without touching this checkout. Returns the copied launcher,
    at `root/core/launchers/<name>/<script name>`."""
    script = Path(script)
    core = Path(root) / "core"
    core.mkdir(parents=True)
    shutil.copytree(_TOOLS, core / "tools", ignore=_TOOLS_IGNORE)
    for entry in sorted(_CORE_DIR.iterdir()):
        if entry.name not in _BORROWED and not entry.name.startswith("."):
            (core / entry.name).symlink_to(entry)
    launchers = core / "launchers"
    launchers.mkdir()
    for name in (script.parent.name, *siblings):
        shutil.copytree(_CORE_DIR / "launchers" / name, launchers / name, ignore=_LAUNCHER_IGNORE)
    copied = launchers / script.parent.name / script.name
    copied.chmod(0o755)
    return copied


def make_pin(pin_root: Path, script: Path, host: Path, *, siblings: Iterable[str] = ()) -> Path:
    """A pin at `pin_root` of the source host `host`: a scratch core with the `pin.json` that
    marks it a pin beside it, so a launcher neither copies it nor re-executes. Returns the pin's
    copy of the launcher."""
    launcher = scratch_core(pin_root, script, siblings=siblings)
    (pin_root / "pin.json").write_text(
        json.dumps(
            {
                "id": "scratch",
                "source_host_root": str(host),
                "created": "1970-01-01T00:00:00+00:00",
            }
        )
        + "\n"
    )
    return launcher


def bind_satellite(launcher: Path, satellite: Path) -> Path:
    """A satellite at `satellite` whose `core` is the symlink to the core `launcher` sits in, the
    way an instance binds a host's core. Returns the launcher reached through that symlink."""
    launcher = Path(launcher)
    core = launcher.parents[2]
    satellite.mkdir(parents=True, exist_ok=True)
    (satellite / "core").symlink_to(core)
    return satellite / "core" / launcher.relative_to(core)


def write_host_setting(host: Path, command: str) -> Path:
    """The setting `command` is named by, at the source host's root, as the one assignment the
    resolver reads. Returns the file."""
    setting = Path(host) / SETTING_FILE
    setting.write_text(f"{COMMAND_VARIABLE}={command}\n")
    return setting


_TELEMETRY_STATE = ("INSTRUMENT_RUN_", "OTEL_", "KA_")
_UNSET = object()


def telemetry_environment(
    base: Mapping[str, str],
    *,
    home: Path,
    endpoint_file: Path,
    cap: str | None = None,
    command: object = _UNSET,
) -> dict[str, str]:
    """`base` with no telemetry state of its own — no `INSTRUMENT_RUN_*`, `OTEL_*` or `KA_*`
    name, no command, no cap, no pin, no startup file — then HOME and the endpoint file, the cap
    when given and the command when `command` is a string. Left at its default, or `None`, the
    command stays unset, the way an ordinary launch has it; a string, empty included, is an
    explicit answer."""
    env = {
        name: value
        for name, value in base.items()
        if not name.startswith(_TELEMETRY_STATE)
        and name not in (COMMAND_VARIABLE, CAP_NAME, "KENSAIAPP_PIN", "BASH_ENV")
    }
    env["HOME"] = str(home)
    env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
    if cap is not None:
        env[CAP_NAME] = cap
    if isinstance(command, str):
        env[COMMAND_VARIABLE] = command
    return env


def publish_endpoint(endpoint_file: Path, kind: str = "valid") -> str | None:
    """Write the endpoint file for `kind` — `valid` loopback, `absent` (no file), `malformed`,
    `remote` — and return the cause the helper prints for it, or None for `valid`."""
    endpoint_file = Path(endpoint_file)
    endpoint_file.unlink(missing_ok=True)
    if kind == "valid":
        endpoint_file.write_text(LOOPBACK_ENDPOINT + "\n")
        return None
    if kind == "malformed":
        endpoint_file.write_text("not-a-url\n")
        return f"telemetry endpoint at {endpoint_file} is unreadable or malformed"
    if kind == "remote":
        endpoint_file.write_text("http://example.com:4318\n")
        return f"telemetry endpoint at {endpoint_file} is not on this machine (loopback only)"
    assert kind == "absent", f"unknown endpoint kind {kind!r}"
    return f"no published telemetry endpoint at {endpoint_file}"


# --- the four ordinary launches (CP-692) ----------------------------------------------------------

ORDINARY_COMBINATIONS = ("direct-host", "direct-satellite", "pinned-host", "pinned-satellite")


@dataclass(frozen=True)
class OrdinaryLaunch:
    """A launcher to run, the instance it runs for, and the source host that holds the setting."""

    launcher: Path
    instance: Path
    host: Path


def ordinary_launch(
    tmp_path: Path,
    script: Path,
    instance: Path,
    combination: str,
    command: str,
    *,
    siblings: Iterable[str] = (),
) -> OrdinaryLaunch:
    """One of `ORDINARY_COMBINATIONS`: the launcher run from its own core or from a pin of it, for
    the source host itself or for a separate `instance` that binds that core. Only the source
    host holds the setting naming `command`. The host is `instance` when it is the host, and
    `tmp_path/host` when it is not."""
    assert combination in ORDINARY_COMBINATIONS, combination
    pinned, _, host_kind = combination.partition("-")
    is_host = host_kind == "host"
    host = Path(instance) if is_host else Path(tmp_path) / "host"
    host.mkdir(parents=True, exist_ok=True)
    write_host_setting(host, command)
    if pinned == "pinned":
        launcher = make_pin(Path(tmp_path) / "pin", script, host, siblings=siblings)
    else:
        launcher = scratch_core(host, script, siblings=siblings)
        if not is_host:
            launcher = bind_satellite(launcher, Path(instance))
    return OrdinaryLaunch(launcher=launcher, instance=Path(instance), host=host)


def _failure_report(observation: Observation) -> str:
    return (
        f"exit {observation.status}\nstderr: {observation.stderr[-1500:]}\n"
        f"stdout: {observation.stdout[-1500:]}"
    )


def assert_ordinary_launch_is_instrumented(
    observation: Observation, *, environment: Mapping[str, str]
) -> None:
    """Fail unless an ordinary launch — one whose environment holds no command — printed exactly
    one `Telemetry:` line and nothing uninstrumented, handed the published endpoint in its
    settings, and exported the six variables."""
    assert COMMAND_VARIABLE not in environment, "an ordinary launch names no command itself"
    assert observation.status == 0, _failure_report(observation)
    lines = observation.telemetry_lines
    assert [line for line in lines if line.strip().startswith("Telemetry:")] == lines, lines
    assert len(lines) == 1, observation.stdout
    assert lines[0].endswith(f" → {LOOPBACK_ENDPOINT}"), lines[0]
    assert not observation.stderr_telemetry_lines, observation.stderr_telemetry_lines
    assert observation.handed_settings is not None, observation.stdout
    assert observation.handed_settings["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == LOOPBACK_ENDPOINT
    for name in TELEMETRY_EXPORT_NAMES:
        assert observation.exports.get(name), f"{name} is not exported: {observation.exports}"


# --- the failure matrix (CP-687, CP-693, CP-694) --------------------------------------------------

FAILURE_KINDS = (
    "unavailable-command",
    "empty-command",
    "environment-over-setting",
    "no-command-and-no-setting",
    "non-executable-command",
    "failing-command",
    "garbled-command",
    "absent-endpoint",
    "malformed-endpoint",
    "remote-endpoint",
)
_ENDPOINT_KINDS = {
    "absent-endpoint": "absent",
    "malformed-endpoint": "malformed",
    "remote-endpoint": "remote",
}
SENTINEL_SETTINGS = json.dumps(
    {"env": {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://sentinel.invalid/v1"}}
)


@dataclass(frozen=True)
class FailureScenario:
    """The environment a failure case runs in and the one cause its launch must print."""

    environment: dict[str, str]
    cause: str
    host_setting: str | None


def failure_scenario(
    kind: str, base: Mapping[str, str], *, home: Path, endpoint_file: Path, cap: str | None
) -> FailureScenario:
    """The scenario for `kind` over `base`: a neutral executable under `home` (never the real
    package, so an equality comparison never meets one), a valid endpoint unless the kind is an
    endpoint failure, the parent's telemetry settings set to a sentinel the launch must discard,
    and the cap when given. `host_setting` is the command name the source host's setting should
    hold, or None for none."""
    # Imported here: the neutral command is shared with the skill launcher's suite, which holds it.
    from test_skill_launcher_telemetry import (  # noqa: PLC0415
        FIXTURE_COMMAND,
        FIXTURE_MODE_VARIABLE,
        install_telemetry_command,
    )

    assert kind in FAILURE_KINDS, kind
    env = telemetry_environment(base, home=home, endpoint_file=endpoint_file, cap=cap)
    env.pop(FIXTURE_MODE_VARIABLE, None)
    install_telemetry_command(home, env)
    bin_dir = Path(home) / ".kensaiapp" / "venv" / "bin"
    cause = publish_endpoint(endpoint_file, _ENDPOINT_KINDS.get(kind, "valid"))
    host_setting = None
    unconfigured = f"no telemetry command configured in {COMMAND_VARIABLE}"
    if kind == "unavailable-command":
        env[COMMAND_VARIABLE] = "absent-command"
        cause = f"no runnable telemetry command at {bin_dir / 'absent-command'}"
    elif kind == "empty-command":
        env[COMMAND_VARIABLE] = ""
        host_setting = FIXTURE_COMMAND
        cause = unconfigured
    elif kind == "environment-over-setting":
        env[COMMAND_VARIABLE] = "absent-command"
        host_setting = FIXTURE_COMMAND
        cause = f"no runnable telemetry command at {bin_dir / 'absent-command'}"
    elif kind == "no-command-and-no-setting":
        env.pop(COMMAND_VARIABLE)
        cause = unconfigured
    elif kind == "non-executable-command":
        (bin_dir / FIXTURE_COMMAND).chmod(0o644)
        cause = f"no runnable telemetry command at {bin_dir / FIXTURE_COMMAND}"
    elif kind == "failing-command":
        env[FIXTURE_MODE_VARIABLE] = "exit-3"
        cause = f"telemetry command at {bin_dir / FIXTURE_COMMAND} exited with status 3"
    elif kind == "garbled-command":
        env[FIXTURE_MODE_VARIABLE] = "garbage"
        cause = (
            f"telemetry command at {bin_dir / FIXTURE_COMMAND} did not print a usable "
            "settings document"
        )
    env["INSTRUMENT_RUN_SETTINGS"] = SENTINEL_SETTINGS
    assert cause is not None
    return FailureScenario(environment=env, cause=cause, host_setting=host_setting)


def assert_failure_scenario(
    observation: Observation, scenario: FailureScenario, *, cap: str | None
) -> None:
    """Fail unless the launch was never failed by its telemetry: it exited 0, printed the one
    stdout line naming the scenario's cause, carried the cap alone (or nothing) in its settings,
    and kept the sentinel settings it inherited out of them."""
    assert observation.status == 0, _failure_report(observation)
    expected = [f"          ({scenario.cause} — run uninstrumented)"]
    assert observation.telemetry_lines == expected, observation.telemetry_lines
    assert_uninstrumented(observation, cap=cap)
    assert "sentinel" not in json.dumps(observation.handed_settings)
    assert "sentinel" not in json.dumps(observation.exports)


# --- a suite's own comparison, selected in a nested pytest ----------------------------------------


def assert_selection_skips_unreachable_and_fails_reached(tmp_path: Path, test_node: str) -> None:
    """Run the suite test `test_node` (`<file>::<name>`) in four nested pytest runs against fixture
    homes and fail unless each ends as CP-689 requires. With no command named, and with one no home
    holds, it is skipped with the reason that names what is missing, and neither passes nor fails.
    With a command that is reached and then exits non-zero, or prints no settings document, it
    fails — a command that is there and broken is never an unavailable dependency. The runs share
    nothing with this process but the checkout and the interpreter."""
    inherited = {
        name: value
        for name, value in os.environ.items()
        if name not in (COMMAND_VARIABLE, "KENSAIAPP_PIN")
    }

    def nested(label: str, command: str, body: str | None) -> subprocess.CompletedProcess:
        home = tmp_path / f"home-{label}"
        home.mkdir(parents=True)
        if body is not None:
            bin_dir = home / ".kensaiapp" / "venv" / "bin"
            bin_dir.mkdir(parents=True)
            (bin_dir / command).write_text(body)
            (bin_dir / command).chmod(0o755)
        env = dict(inherited, HOME=str(home), PYTHONDONTWRITEBYTECODE="1")
        env[COMMAND_VARIABLE] = command
        return subprocess.run(
            [sys.executable, "-m", "pytest", test_node, "-q", "-rs", "-n", "0",
             "-p", "no:cacheprovider"],
            cwd=str(_CORE_DIR.parent), capture_output=True, text=True, env=env, timeout=600,
        )

    unset = nested("unset", "", None)
    assert unset.returncode == 0, unset.stdout + unset.stderr
    assert SKIP_UNSET in unset.stdout, unset.stdout
    assert "passed" not in unset.stdout and "failed" not in unset.stdout, unset.stdout

    absent = nested("absent", "no-such-command", None)
    path = tmp_path / "home-absent" / ".kensaiapp" / "venv" / "bin" / "no-such-command"
    assert absent.returncode == 0, absent.stdout + absent.stderr
    assert skip_reason_unreachable(path) in absent.stdout, absent.stdout
    assert "passed" not in absent.stdout and "failed" not in absent.stdout, absent.stdout

    for label, body in (
        ("exit-3", "#!/bin/sh\nexit 3\n"),
        ("garbage", "#!/bin/sh\necho this is not a settings document\n"),
    ):
        reached = nested(label, "reached", body)
        assert reached.returncode != 0, reached.stdout + reached.stderr
        assert "failed" in reached.stdout and "skipped" not in reached.stdout, reached.stdout
