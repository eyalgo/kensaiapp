"""Tests for `core/tools/instrument_run.sh` — the shared telemetry-tagging home.

This is a **sourced bash library**, never run directly, so there is no launcher to invoke here —
that is each caller's own suite's job (Task 4), over the twenty-five launchers that source this
file (`core/tools/test_launcher_instrumentation.py` holds the fleet-wide guard). What is pinned
here is the library's own contract, in its own terms, the same "source a tiny wrapper, call one
function" shape `test_detach_watcher.py` uses for its own sourced library
(`core/doctrine/engineering/languages/shell/testing.md` § Technique 2).

Task 2 — the base OTLP export, gated entirely on whether a published endpoint file exists and
looks like one. Task 3 — the `kensai.arm` / `kensai.run_id` resource attributes, layered on top
once the base export already happens.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import uuid
from pathlib import Path

import pytest

_LIB = Path(__file__).resolve().parent / "instrument_run.sh"

CALL_STUB = """#!/usr/bin/env bash
# Sources the library under test and calls instrument_run with no arguments — the caller sets
# no argument and exports no variable, exactly as a real launcher does — then execs `env` so
# the assertions see exactly what a process spawned right after would inherit.
set -euo pipefail
source "{lib}"
instrument_run
echo "INSTRUMENT_RUN_EXIT=$?"
exec env
"""

USER_ENTRY_STUB = """#!/usr/bin/env bash
# Sources the library and calls instrument_run_user_entry directly — the standalone consumer
# a settings-merge command reaches for, with no live session and nothing already exported.
set -euo pipefail
source "{lib}"
instrument_run_user_entry
echo "INSTRUMENT_RUN_USER_ENTRY_EXIT=$?"
"""


def _write_wrapper(tmp_path: Path, subdir: str = "caller") -> Path:
    """Writes the wrapper into `tmp_path/<subdir>/wrapper.sh`. `subdir` becomes the directory
    name Task 3's derivation reads as the arm — named to make that clear at each call site
    rather than repeated as a magic default."""
    caller_dir = tmp_path / subdir
    caller_dir.mkdir(parents=True, exist_ok=True)
    wrapper = caller_dir / "wrapper.sh"
    wrapper.write_text(CALL_STUB.format(lib=_LIB))
    wrapper.chmod(0o755)
    return wrapper


# The variables instrument_run exports. A machine that enables telemetry in its user settings sets
# them in every shell, so a test that asserts one absent strips them from what it inherits — or it
# measures the machine instead of the code.
TELEMETRY_KEYS = (
    "CLAUDE_CODE_ENABLE_TELEMETRY",
    "OTEL_METRICS_EXPORTER",
    "OTEL_LOGS_EXPORTER",
    "OTEL_EXPORTER_OTLP_PROTOCOL",
    "OTEL_EXPORTER_OTLP_ENDPOINT",
    "OTEL_RESOURCE_ATTRIBUTES",
)


# The one variable the settings carry that is not telemetry: the developer's context cap. The
# chain exports it for the implementation step only, and that step runs this suite — so an
# inherited value would put a key into every settings JSON below that no test asked for.
CONTEXT_CAP_KEY = "KENSAIAPP_CONTEXT_CAP"


def _clean_environ() -> dict[str, str]:
    """The inherited environment less every telemetry variable — by prefix, so an `OTEL_*` the
    library does not export yet is stripped too, not only `TELEMETRY_KEYS` — and less the
    context cap, which reaches the settings the same way."""
    return {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("OTEL_", "CLAUDE_CODE_ENABLE_TELEMETRY")) and key != CONTEXT_CAP_KEY
    }


def _run(
    wrapper: Path, env_overrides: dict | None = None, *, cwd: Path | None = None
) -> subprocess.CompletedProcess:
    """`cwd` defaults to the wrapper's own directory — never the pytest process's cwd, which is
    a real git checkout: without pinning `cwd` here, Task 1's instance derivation would attach
    `kensai.instance` to every one of these calls, and older assertions written before that task
    existed would start seeing an attribute they never asked about. A test that wants the git
    case passes its own `cwd` (`TestInstanceIsDerived` does)."""
    env = _clean_environ()
    env.pop("INSTRUMENT_RUN_ENDPOINT_FILE", None)
    env.pop("INSTRUMENT_RUN_ARM", None)
    env.pop("INSTRUMENT_RUN_WALK_ID", None)
    env.pop("INSTRUMENT_RUN_CHAIN", None)
    env.pop("INSTRUMENT_RUN_ROLE", None)
    env.pop("INSTRUMENT_RUN_AUDIT_TARGET", None)
    for key in TELEMETRY_KEYS:
        env.pop(key, None)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", str(wrapper)],
        cwd=str(cwd or wrapper.parent),
        capture_output=True,
        text=True,
        env=env,
        timeout=15,
    )


def _write_wrapper_with_args(tmp_path: Path, args: list[str], subdir: str = "caller") -> Path:
    """Like `_write_wrapper`, but calls `instrument_run` with the given `key=value` arguments,
    each shell-quoted so a value carrying a space, a comma or any other character survives as
    one argument rather than being re-split by the wrapper's own shell."""
    caller_dir = tmp_path / subdir
    caller_dir.mkdir(parents=True, exist_ok=True)
    wrapper = caller_dir / "wrapper.sh"
    quoted = " ".join(shlex.quote(arg) for arg in args)
    wrapper.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        f'source "{_LIB}"\n'
        f"instrument_run {quoted}\n"
        'echo "INSTRUMENT_RUN_EXIT=$?"\n'
        "exec env\n"
    )
    wrapper.chmod(0o755)
    return wrapper


def _write_user_entry_wrapper(tmp_path: Path) -> Path:
    wrapper = tmp_path / "user_entry_wrapper.sh"
    wrapper.write_text(USER_ENTRY_STUB.format(lib=_LIB))
    wrapper.chmod(0o755)
    return wrapper


def _run_user_entry(tmp_path: Path, env_overrides: dict | None = None) -> subprocess.CompletedProcess:
    wrapper = _write_user_entry_wrapper(tmp_path)
    env = _clean_environ()
    env.pop("INSTRUMENT_RUN_ENDPOINT_FILE", None)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        ["bash", str(wrapper)], capture_output=True, text=True, env=env, timeout=15
    )


_TELEMETRY_PREFIXES = ("OTEL_", "CLAUDE_CODE_ENABLE_TELEMETRY", "INSTRUMENT_RUN_")


def _env_lines(stdout: str) -> dict[str, str]:
    """The exec'd `env` dump, parsed into a dict of the telemetry keys only — good enough here
    because none of the values this suite drives through it contain a literal newline.

    Only the keys this suite asserts on are kept: a failing assertion prints the dict it failed
    over, and the whole environment would print every credential the shell carries."""
    values: dict[str, str] = {}
    for line in stdout.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            if key.startswith(_TELEMETRY_PREFIXES):
                values[key] = value
    return values


# ── Task 2 — the base OTLP export, gated on the published endpoint ────────


class TestBaseTelemetryExport:
    def test_sourcing_alone_has_no_side_effect(self, tmp_path):
        # The same contract `detach_watcher.sh` states for the same reason: no function call, no
        # output, no export — just defining the function.
        wrapper = tmp_path / "source_only.sh"
        wrapper.write_text(f'#!/usr/bin/env bash\nset -euo pipefail\nsource "{_LIB}"\necho done\n')
        wrapper.chmod(0o755)
        result = subprocess.run(["bash", str(wrapper)], capture_output=True, text=True, timeout=15)
        assert result.returncode == 0
        assert result.stdout.strip() == "done"

    def test_given_a_published_endpoint_the_call_exports_otlp_http_json_to_it(self, tmp_path):
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text("http://localhost:4318\n")
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(endpoint_file)})
        assert result.returncode == 0, result.stderr
        assert "INSTRUMENT_RUN_EXIT=0" in result.stdout
        env_out = _env_lines(result.stdout)
        assert env_out["CLAUDE_CODE_ENABLE_TELEMETRY"] == "1"
        assert env_out["OTEL_METRICS_EXPORTER"] == "otlp"
        assert env_out["OTEL_LOGS_EXPORTER"] == "otlp"
        assert env_out["OTEL_EXPORTER_OTLP_PROTOCOL"] == "http/json"
        assert env_out["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://localhost:4318"

    def test_given_no_such_file_it_exports_nothing_and_returns_success(self, tmp_path):
        missing = tmp_path / "does-not-exist" / "endpoint"
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(missing)})
        assert result.returncode == 0, result.stderr
        assert "INSTRUMENT_RUN_EXIT=0" in result.stdout
        assert "run uninstrumented" in result.stdout
        env_out = _env_lines(result.stdout)
        assert "CLAUDE_CODE_ENABLE_TELEMETRY" not in env_out
        assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in env_out

    def test_never_fails_the_caller_even_though_the_wrapper_runs_under_set_dash_e(self, tmp_path):
        # `set -euo pipefail` in the wrapper is the same guard a real launcher runs under; if
        # instrument_run ever returned non-zero on the no-endpoint path, `set -e` would abort the
        # wrapper before it ever reached `exec env`, and this test would see no output at all.
        missing = tmp_path / "still-missing"
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(missing)})
        assert result.returncode == 0
        assert "PATH=" in result.stdout  # exec env ran — the wrapper was not aborted

    def test_given_an_unreadable_or_malformed_file_it_behaves_as_if_there_were_none(self, tmp_path):
        garbage = tmp_path / "garbage-endpoint"
        garbage.write_text("not a url\n")
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(garbage)})
        assert result.returncode == 0, result.stderr
        assert "INSTRUMENT_RUN_EXIT=0" in result.stdout
        env_out = _env_lines(result.stdout)
        assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in env_out

    @pytest.mark.parametrize(
        "endpoint",
        [
            "http://telemetry.example.com:4318",
            "https://10.0.0.5:4318",
            "http://127.example.com:4318",
            "http://localhost@telemetry.example.com:4318",
            "http://localhost.example.com:4318",
        ],
    )
    def test_an_endpoint_off_this_machine_is_refused_and_nothing_is_exported(
        self, tmp_path, endpoint
    ):
        """Telemetry stays on the user's machine: a published endpoint naming any host but
        loopback is refused like a malformed one."""
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text(endpoint + "\n")
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(endpoint_file)})
        assert result.returncode == 0, result.stderr
        assert "INSTRUMENT_RUN_EXIT=0" in result.stdout
        assert "not on this machine" in result.stdout
        env_out = _env_lines(result.stdout)
        assert "CLAUDE_CODE_ENABLE_TELEMETRY" not in env_out
        assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in env_out

    @pytest.mark.parametrize(
        "endpoint",
        ["http://localhost:4318", "http://127.0.0.1:4318/", "https://[::1]:4318", "http://localhost"],
    )
    def test_a_loopback_endpoint_is_exported(self, tmp_path, endpoint):
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text(endpoint + "\n")
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(endpoint_file)})
        assert result.returncode == 0, result.stderr
        assert _env_lines(result.stdout)["OTEL_EXPORTER_OTLP_ENDPOINT"] == endpoint

    def test_a_directory_where_a_file_is_expected_behaves_as_if_there_were_none(self, tmp_path):
        # A portable stand-in for "unreadable": `[ -r <dir> ]` is true for a directory, so this
        # drives the code path a permission-denied file would drive without depending on chmod
        # semantics a sandboxed test runner might not honour.
        a_directory = tmp_path / "a-directory"
        a_directory.mkdir()
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(a_directory)})
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in env_out

    def test_the_default_path_is_resolved_in_one_place_and_the_suite_never_touches_it(self):
        # "handed in, not computed in the function body" — the default expression lives in
        # exactly one line, and it names the real machine path this suite must never touch
        # directly. Prose above may mention the path again; only the live expression is pinned.
        source = _LIB.read_text()
        assert source.count("INSTRUMENT_RUN_ENDPOINT_FILE:-") == 1
        assert (
            'local endpoint_file="${INSTRUMENT_RUN_ENDPOINT_FILE:-$HOME/.claude/tools/otel-receiver/endpoint}"'
            in source
        )

    def test_the_library_names_no_port_and_no_test_only_path(self):
        source = _LIB.read_text()
        assert "4318" not in source


# ── Task 1 (station 2) — the user entry, a second consumer of the same variable set ────────


class TestUserEntryLibrary:
    """`instrument_run_user_entry` is the standalone consumer the settings-merge command reaches
    for — no live session, nothing already exported, just a validated endpoint. It must build
    off the exact same base variable set `instrument_run`'s own export and `_instrument_run_settings`
    already agree on, never a second copy of the list."""

    def test_given_a_published_endpoint_it_yields_the_base_entry(self, tmp_path):
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text("http://localhost:4318\n")
        result = _run_user_entry(tmp_path, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(endpoint_file)})
        assert result.returncode == 0, result.stderr
        assert "INSTRUMENT_RUN_USER_ENTRY_EXIT=0" in result.stdout
        lines = [line for line in result.stdout.splitlines() if line.startswith("{")]
        assert lines, f"no JSON line in {result.stdout!r}"
        entry = json.loads(lines[0])
        assert entry == {
            "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
            "OTEL_METRICS_EXPORTER": "otlp",
            "OTEL_LOGS_EXPORTER": "otlp",
            "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
            "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318",
        }

    def test_the_entry_carries_no_resource_attributes(self, tmp_path):
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text("http://localhost:4318\n")
        result = _run_user_entry(tmp_path, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(endpoint_file)})
        lines = [line for line in result.stdout.splitlines() if line.startswith("{")]
        entry = json.loads(lines[0])
        assert "OTEL_RESOURCE_ATTRIBUTES" not in entry

    @pytest.mark.parametrize(
        "make_endpoint_file",
        [
            lambda tmp_path: tmp_path / "does-not-exist",
            lambda tmp_path: _garbage_endpoint_file(tmp_path),
            lambda tmp_path: _directory_endpoint_file(tmp_path),
        ],
        ids=["missing", "malformed", "directory"],
    )
    def test_given_no_usable_endpoint_it_yields_nothing_and_returns_success(
        self, tmp_path, make_endpoint_file
    ):
        endpoint_file = make_endpoint_file(tmp_path)
        result = _run_user_entry(tmp_path, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(endpoint_file)})
        assert result.returncode == 0, result.stderr
        assert "INSTRUMENT_RUN_USER_ENTRY_EXIT=0" in result.stdout
        assert not any(line.startswith("{") for line in result.stdout.splitlines())

    @pytest.mark.skipif(os.geteuid() == 0, reason="root reads a mode-000 file")
    def test_given_an_unreadable_endpoint_file_it_yields_nothing_and_returns_success(
        self, tmp_path
    ):
        # Integrity review (plan Task 1): "no file, an unreadable one, a malformed one or a
        # directory" — the unreadable case had no test.
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text("http://localhost:4318\n")
        endpoint_file.chmod(0o000)
        try:
            result = _run_user_entry(
                tmp_path, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(endpoint_file)}
            )
        finally:
            endpoint_file.chmod(0o600)
        assert result.returncode == 0, result.stderr
        assert "INSTRUMENT_RUN_USER_ENTRY_EXIT=0" in result.stdout
        assert not any(line.startswith("{") for line in result.stdout.splitlines())

    def test_key_set_matches_the_launchers_settings_env_less_resource_attributes(self, tmp_path):
        # The parity this task exists to hold: a change to the variable set must reach both
        # consumers, or this test catches the drift.
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text("http://localhost:4318\n")
        launcher_wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        launcher_result = _run(
            launcher_wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(endpoint_file)}
        )
        launcher_settings = json.loads(_env_lines(launcher_result.stdout)["INSTRUMENT_RUN_SETTINGS"])
        launcher_keys = set(launcher_settings["env"]) - {"OTEL_RESOURCE_ATTRIBUTES"}

        entry_result = _run_user_entry(
            tmp_path, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(endpoint_file)}
        )
        entry_lines = [line for line in entry_result.stdout.splitlines() if line.startswith("{")]
        entry = json.loads(entry_lines[0])

        assert set(entry) == launcher_keys
        assert entry == {k: launcher_settings["env"][k] for k in launcher_keys}


def _garbage_endpoint_file(tmp_path: Path) -> Path:
    garbage = tmp_path / "garbage-endpoint"
    garbage.write_text("not a url\n")
    return garbage


def _directory_endpoint_file(tmp_path: Path) -> Path:
    a_directory = tmp_path / "a-directory"
    a_directory.mkdir()
    return a_directory


# ── Task 3 — the arm and the run id ────────


class TestArmAndRunId:
    """All of these need a real endpoint file — `kensai.arm` / `kensai.run_id` are attached
    only once the base export has already decided to happen (Task 2); an untagged run with no
    endpoint is Task 2's own case, not this one's."""

    def _endpoint_file(self, tmp_path: Path) -> Path:
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text("http://localhost:4318\n")
        return endpoint_file

    def test_with_nothing_set_the_arm_is_the_calling_launchers_own_directory_name(self, tmp_path):
        # Named for a launcher's own directory shape: `core/launchers/ad-hoc-flow/launcher.sh` (retired
        # 2026-09-18; the name is only a fixture) — the wrapper stands in for that file, and its directory name is what must come back.
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        assert "kensai.arm=ad-hoc-flow" in env_out["OTEL_RESOURCE_ATTRIBUTES"]

    def test_a_launcher_copied_to_a_new_directory_gets_the_new_directorys_arm(self, tmp_path):
        # "derived, not passed as a literal by each caller, so a copied launcher cannot inherit
        # its parent's arm" — the same wrapper BYTES, under a different directory name, must
        # report the new name: nothing in the wrapper itself names the arm.
        wrapper = _write_wrapper(tmp_path, subdir="ratify")
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        env_out = _env_lines(result.stdout)
        assert "kensai.arm=ratify" in env_out["OTEL_RESOURCE_ATTRIBUTES"]

    def test_an_environment_override_replaces_the_arm_and_wins(self, tmp_path):
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(
            wrapper,
            {
                "INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path)),
                "INSTRUMENT_RUN_ARM": "canary",
            },
        )
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        assert "kensai.arm=canary" in env_out["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.arm=ad-hoc-flow" not in env_out["OTEL_RESOURCE_ATTRIBUTES"]

    def test_an_arm_value_containing_a_space_is_refused_rather_than_exported(self, tmp_path):
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(
            wrapper,
            {
                "INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path)),
                "INSTRUMENT_RUN_ARM": "two words",
            },
        )
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        # OTEL_RESOURCE_ATTRIBUTES cannot carry the space, so it is refused entirely — but the
        # base OTLP export (Task 2's own concern) still happens; a bad arm must not untag the
        # whole run.
        assert "OTEL_RESOURCE_ATTRIBUTES" not in env_out
        assert env_out["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://localhost:4318"
        assert "not attached" in result.stdout or "not exported" in result.stdout

    def test_a_run_id_accompanies_the_arm_and_is_distinct_per_invocation(self, tmp_path):
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        env_override = {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))}
        first = _env_lines(_run(wrapper, env_override).stdout)
        second = _env_lines(_run(wrapper, env_override).stdout)

        def run_id_of(resource_attributes: str) -> str:
            for pair in resource_attributes.split(","):
                key, _, value = pair.partition("=")
                if key == "kensai.run_id":
                    return value
            raise AssertionError(f"no kensai.run_id in {resource_attributes!r}")

        first_id = run_id_of(first["OTEL_RESOURCE_ATTRIBUTES"])
        second_id = run_id_of(second["OTEL_RESOURCE_ATTRIBUTES"])
        assert first_id and second_id
        assert first_id != second_id
        # Distinct AND a real uuid4 — not just two different short-lived tokens.
        uuid.UUID(first_id)
        uuid.UUID(second_id)

    def test_both_keys_carry_the_kensai_prefix(self, tmp_path):
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        env_out = _env_lines(
            _run(
                wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))}
            ).stdout
        )
        keys = {
            pair.partition("=")[0]
            for pair in env_out["OTEL_RESOURCE_ATTRIBUTES"].split(",")
        }
        assert keys == {"kensai.arm", "kensai.run_id"}


class TestArmSurvivesHowTheLauncherWasStarted:
    """Task 3, first behaviour, held against the shapes a launcher is really started in:
    *"With nothing set, the arm is the calling launcher's own directory name — derived, not
    passed as a literal by each caller."*

    `TestArmAndRunId` above drives a bare wrapper started by absolute path. A real launcher is a
    different shape in two ways that both bear on the derivation, and neither is exercised
    there: it resolves its own `SCRIPT_DIR` and then **`cd`s to the instance root** long before
    it reaches the instrument call (all twenty-five do — `cd "$INSTANCE_ROOT"`), and it can be
    started by a path that is relative to where it already is. The intent puts no condition on
    either: the arm is the launcher's own directory name, whichever way it was started.

    `--instance-root` is the launcher's own documented flag for decoupling the instance from the
    cwd, so starting one from inside its own folder and pointing it at an instance elsewhere is
    a supported invocation, not a misuse.
    """

    # The real launcher opening, in the four lines every one of the twenty-five shares: resolve
    # SCRIPT_DIR from this file, take the instance root from the cwd or --instance-root, cd
    # there, and only much later source the library and call it with no arguments.
    LAUNCHER_SHAPED_STUB = (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        'INSTANCE_ROOT="$PWD"\n'
        '[ "${1:-}" = "--instance-root" ] && { INSTANCE_ROOT="$2"; shift 2; }\n'
        'cd "$INSTANCE_ROOT"\n'
        'source "__LIB__"\n'
        "instrument_run\n"
        "exec env\n"
    )

    def _launcher(self, tmp_path: Path, name: str) -> Path:
        launcher_dir = tmp_path / "launchers" / name
        launcher_dir.mkdir(parents=True, exist_ok=True)
        launcher = launcher_dir / "launcher.sh"
        launcher.write_text(self.LAUNCHER_SHAPED_STUB.replace("__LIB__", str(_LIB)))
        launcher.chmod(0o755)
        return launcher

    def _arm_of(self, result: subprocess.CompletedProcess) -> str:
        assert result.returncode == 0, result.stderr
        attributes = _env_lines(result.stdout).get("OTEL_RESOURCE_ATTRIBUTES", "")
        assert attributes, f"nothing was tagged at all; telemetry lines were {_env_lines(result.stdout)!r}"
        for pair in attributes.split(","):
            key, _, value = pair.partition("=")
            if key == "kensai.arm":
                return value
        raise AssertionError(f"no kensai.arm in {attributes!r}")

    def _run_from(self, cwd: Path, argv: list[str], endpoint_file: Path):
        env = _clean_environ()
        env.pop("INSTRUMENT_RUN_ARM", None)
        for key in TELEMETRY_KEYS:
            env.pop(key, None)
        env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint_file)
        return subprocess.run(
            argv, cwd=str(cwd), capture_output=True, text=True, env=env, timeout=15
        )

    @pytest.fixture
    def endpoint_file(self, tmp_path) -> Path:
        published = tmp_path / "endpoint"
        published.write_text("http://localhost:4318\n")
        return published

    def test_started_by_a_path_relative_to_its_own_folder(self, tmp_path, endpoint_file):
        """`cd <the launcher's folder> && ./launcher.sh` — the instance root is the cwd, which
        is where the launcher already sits. The arm is still the launcher's directory name."""
        launcher = self._launcher(tmp_path, "ratify")
        result = self._run_from(launcher.parent, ["./launcher.sh"], endpoint_file)
        assert self._arm_of(result) == "ratify"

    def test_started_from_its_own_folder_against_an_instance_root_elsewhere(
        self, tmp_path, endpoint_file
    ):
        """`cd <the launcher's folder> && ./launcher.sh --instance-root <elsewhere>` — the
        launcher's own flag for the case where the instance is not the cwd. The arm names the
        launcher, never the instance it was pointed at."""
        launcher = self._launcher(tmp_path, "ratify")
        instance_root = tmp_path / "some-instance"
        instance_root.mkdir()
        result = self._run_from(
            launcher.parent,
            ["./launcher.sh", "--instance-root", str(instance_root)],
            endpoint_file,
        )
        arm = self._arm_of(result)
        assert arm != "some-instance", "the arm named the instance root, not the launcher"
        assert arm == "ratify"

    def test_started_by_absolute_path_from_an_unrelated_cwd(self, tmp_path, endpoint_file):
        """The documented invocation — `<CORE>/launchers/<name>/launcher.sh`, run from the
        instance root. Held here beside the other two so all three shapes are one comparison."""
        launcher = self._launcher(tmp_path, "ratify")
        instance_root = tmp_path / "some-instance"
        instance_root.mkdir()
        result = self._run_from(instance_root, ["bash", str(launcher)], endpoint_file)
        assert self._arm_of(result) == "ratify"

    def test_a_launcher_copied_to_a_sibling_folder_reports_the_new_folder(
        self, tmp_path, endpoint_file
    ):
        """The property the derivation exists for — "so a copied launcher cannot inherit its
        parent's arm" — asserted under the relative shape too, where the byte-identical file in
        a differently-named folder must report the new name rather than a shared constant."""
        copied = self._launcher(tmp_path, "ratify-copy")
        result = self._run_from(copied.parent, ["./launcher.sh"], endpoint_file)
        assert self._arm_of(result) == "ratify-copy"


# ── Task 6 — the console fallback, measured ────────


# ── Task 7 — the variables reach a backgrounded run ────────


class TestHandsItsVariablesOverAsSettings:
    """An exported variable never reaches a `claude --bg` session; `--settings '{"env": …}'` does —
    measured 2026-09-10 over three haiku probes against the live receiver. So the call
    also leaves one value a launcher hands to its spawn, and it must carry exactly what was
    exported: a variable in one and not the other is a foreground run and a background run
    reporting under different attributes."""

    _TELEMETRY_KEYS = TELEMETRY_KEYS

    def _endpoint_file(self, tmp_path: Path) -> Path:
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text("http://localhost:4318\n")
        return endpoint_file

    def test_given_a_published_endpoint_the_settings_carry_exactly_what_was_exported(self, tmp_path):
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        settings = json.loads(env_out["INSTRUMENT_RUN_SETTINGS"])
        assert set(settings) == {"env"}
        assert settings["env"] == {key: env_out[key] for key in self._TELEMETRY_KEYS}
        assert "kensai.arm=ad-hoc-flow" in settings["env"]["OTEL_RESOURCE_ATTRIBUTES"]

    def test_given_no_endpoint_no_settings_are_left_behind(self, tmp_path):
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(tmp_path / "absent")})
        assert result.returncode == 0, result.stderr
        assert "INSTRUMENT_RUN_SETTINGS" not in _env_lines(result.stdout)

    def test_a_refused_arm_leaves_the_settings_without_the_resource_attributes(self, tmp_path):
        # The arm guard refuses whitespace and exports no OTEL_RESOURCE_ATTRIBUTES; the settings
        # match that rather than re-adding what the export withheld.
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {
            "INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path)),
            "INSTRUMENT_RUN_ARM": "two words",
        })
        assert result.returncode == 0, result.stderr
        settings = json.loads(_env_lines(result.stdout)["INSTRUMENT_RUN_SETTINGS"])
        assert "OTEL_RESOURCE_ATTRIBUTES" not in settings["env"]
        assert settings["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://localhost:4318"

    def test_the_settings_name_no_console_exporter(self, tmp_path):
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        settings = json.loads(_env_lines(result.stdout)["INSTRUMENT_RUN_SETTINGS"])
        assert not any("console" in value for value in settings["env"].values())

    def test_an_exported_context_cap_rides_the_settings_env(self, tmp_path):
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {
            "INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path)),
            CONTEXT_CAP_KEY: "80000",
        })
        assert result.returncode == 0, result.stderr
        settings = json.loads(_env_lines(result.stdout)["INSTRUMENT_RUN_SETTINGS"])
        assert settings["env"][CONTEXT_CAP_KEY] == "80000"
        assert set(settings["env"]) - {CONTEXT_CAP_KEY} >= set(self._TELEMETRY_KEYS) - {
            "OTEL_RESOURCE_ATTRIBUTES"
        }

    def test_an_unexported_context_cap_is_absent_and_nothing_raises(self, tmp_path):
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        settings = json.loads(_env_lines(result.stdout)["INSTRUMENT_RUN_SETTINGS"])
        assert CONTEXT_CAP_KEY not in settings["env"]
        assert settings["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://localhost:4318"

    def test_an_exported_context_cap_reaches_the_settings_of_an_uninstrumented_run(self, tmp_path):
        """CP-58 checks the developer's context on every implementation run, not only on a machine
        that publishes a telemetry endpoint. The cap has no other route into a `claude --bg`
        session, so a run left uninstrumented still hands it over — and nothing else, since no
        telemetry was exported for the settings to carry."""
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {
            "INSTRUMENT_RUN_ENDPOINT_FILE": str(tmp_path / "absent"),
            CONTEXT_CAP_KEY: "80000",
        })
        assert result.returncode == 0, result.stderr
        assert "run uninstrumented" in result.stdout
        settings = json.loads(_env_lines(result.stdout)["INSTRUMENT_RUN_SETTINGS"])
        assert settings == {"env": {CONTEXT_CAP_KEY: "80000"}}

    def test_an_empty_context_cap_is_left_out_like_an_unexported_one(self, tmp_path):
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {
            "INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path)),
            CONTEXT_CAP_KEY: "",
        })
        assert result.returncode == 0, result.stderr
        settings = json.loads(_env_lines(result.stdout)["INSTRUMENT_RUN_SETTINGS"])
        assert CONTEXT_CAP_KEY not in settings["env"]


class TestNoConsoleFallback:
    """`instrument_run.sh`'s own header records the probe this class asserts the conclusion of:
    a detached `claude --bg` run's console export lands nowhere the launcher's redirected file
    can read back — the file that survives the run holds only the `backgrounded · <id>` banner,
    unchanged in size from launch through an explicit `claude stop`. So the treatment that
    matches the answer is exporting no console exporter at all, and this asserts that on the
    actual exported variable VALUES — not by grepping the library's source text for the word,
    which would prove nothing about what a real launch sees."""

    def test_no_exported_value_contains_console(self, tmp_path):
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text("http://localhost:4318\n")
        wrapper = _write_wrapper(tmp_path)
        env_out = _env_lines(
            _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(endpoint_file)}).stdout
        )
        exporter_keys = (
            "OTEL_METRICS_EXPORTER",
            "OTEL_LOGS_EXPORTER",
            "OTEL_EXPORTER_OTLP_PROTOCOL",
        )
        for key in exporter_keys:
            assert "console" not in env_out.get(key, ""), (
                f"{key}={env_out.get(key)!r} names a console exporter, but the probe recorded "
                "in instrument_run.sh's own header found nowhere a --bg run's console output "
                "can be read back from"
            )

    def test_killing_the_receiver_leaves_a_readable_message_not_a_silent_success(self, tmp_path):
        """"Killing the receiver" is, from this library's own vantage point, indistinguishable
        from the receiver never having been installed: both mean the published endpoint file is
        gone (station 1's plist writes it once at start; nothing here or there restores it once
        the process that held it is gone). Simulated the same way Task 2's absent-file case is:
        a path nothing occupies."""
        missing = tmp_path / "receiver-was-here-and-is-now-gone"
        wrapper = _write_wrapper(tmp_path)
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(missing)})

        assert result.returncode == 0, result.stderr
        assert "run uninstrumented" in result.stdout, (
            "a dead receiver must leave something a person can read that says the run was not "
            "collected, not a silent success"
        )
        env_out = _env_lines(result.stdout)
        assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in env_out
        assert "OTEL_RESOURCE_ATTRIBUTES" not in env_out


# ── Task 1 — the instance is derived, not passed ────────


class TestInstanceIsDerived:
    """Every record says which instance ran it, and a launcher cannot get it wrong because the
    launcher never states it — the instance is read from git, not passed."""

    def _git(self, *args: str, cwd: Path) -> None:
        subprocess.run(["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True)

    def _repo(self, tmp_path: Path, name: str) -> Path:
        repo = tmp_path / name
        repo.mkdir()
        self._git("init", "-q", cwd=repo)
        self._git("config", "user.email", "a@b.c", cwd=repo)
        self._git("config", "user.name", "a", cwd=repo)
        (repo / "README.md").write_text("x")
        self._git("add", ".", cwd=repo)
        self._git("commit", "-q", "-m", "first", cwd=repo)
        return repo

    def _endpoint_file(self, tmp_path: Path) -> Path:
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text("http://localhost:4318\n")
        return endpoint_file

    def test_called_inside_a_git_repository_attaches_the_repos_own_name(self, tmp_path):
        repo = self._repo(tmp_path, "an-instance")
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(
            wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))},
            cwd=repo,
        )
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        assert "kensai.instance=an-instance" in env_out["OTEL_RESOURCE_ATTRIBUTES"]

    def test_a_worktree_of_that_repository_yields_the_same_name_as_its_main_checkout(
        self, tmp_path
    ):
        repo = self._repo(tmp_path, "an-instance")
        worktree = tmp_path / "worktree-of-an-instance"
        self._git("worktree", "add", "-q", str(worktree), "-b", "wt-branch", cwd=repo)
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(
            wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))},
            cwd=worktree,
        )
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        assert "kensai.instance=an-instance" in env_out["OTEL_RESOURCE_ATTRIBUTES"]

    def test_called_outside_any_git_repository_attaches_no_instance_and_the_rest_still_goes_out(
        self, tmp_path
    ):
        outside = tmp_path / "no-git-here"
        outside.mkdir()
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(
            wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))},
            cwd=outside,
        )
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        assert "kensai.instance" not in env_out["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.arm=ad-hoc-flow" in env_out["OTEL_RESOURCE_ATTRIBUTES"]

    def test_the_value_reaches_the_settings_exactly_as_it_reaches_the_export(self, tmp_path):
        repo = self._repo(tmp_path, "an-instance")
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(
            wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))},
            cwd=repo,
        )
        env_out = _env_lines(result.stdout)
        settings = json.loads(env_out["INSTRUMENT_RUN_SETTINGS"])
        assert settings["env"]["OTEL_RESOURCE_ATTRIBUTES"] == env_out["OTEL_RESOURCE_ATTRIBUTES"]

    @pytest.mark.parametrize(
        "repo_name", ["an instance", "an,instance"], ids=["space", "comma"]
    )
    def test_an_instance_name_otel_cannot_carry_drops_that_key_alone(self, tmp_path, repo_name):
        """Integrity review, from the station's guardrail: "A bad value drops its own key, not the
        run's tags. When OTEL_RESOURCE_ATTRIBUTES cannot carry a value, that key alone is refused,
        and the arm and the rest still go out." A checkout directory is free to carry a space or a
        comma; the derived instance is a value like any other."""
        repo = self._repo(tmp_path, repo_name)
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(
            wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))},
            cwd=repo,
        )
        assert result.returncode == 0, result.stderr
        attrs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"]
        keys = [pair.partition("=")[0] for pair in attrs.split(",")]
        assert keys == ["kensai.arm", "kensai.run_id"]


# ── Task 2 — the launcher's subject, and the product it names ────────


class TestLauncherSubjectAndProduct:
    """The launcher already holds the project, document or skill it works on. It hands that
    over, and the library turns it into attributes."""

    def _endpoint_file(self, tmp_path: Path) -> Path:
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text("http://localhost:4318\n")
        return endpoint_file

    def test_each_accepted_key_is_stamped_as_kensai_key(self, tmp_path):
        wrapper = _write_wrapper_with_args(
            tmp_path,
            ["project=widgetco", "document=fdr", "skill=cold-read",
             "target_instance=sample-instance"],
        )
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        attrs = env_out["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.project=widgetco" in attrs
        assert "kensai.document=fdr" in attrs
        assert "kensai.skill=cold-read" in attrs
        assert "kensai.target_instance=sample-instance" in attrs

    def test_an_unknown_key_is_refused_with_one_line_and_the_call_still_returns_0(self, tmp_path):
        wrapper = _write_wrapper_with_args(tmp_path, ["bogus=value"])
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        assert "INSTRUMENT_RUN_EXIT=0" in result.stdout
        assert "unknown key" in result.stdout
        env_out = _env_lines(result.stdout)
        assert "kensai.bogus" not in env_out.get("OTEL_RESOURCE_ATTRIBUTES", "")

    def test_an_empty_value_attaches_nothing_for_that_key(self, tmp_path):
        wrapper = _write_wrapper_with_args(tmp_path, ["document="])
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        assert "kensai.document" not in env_out.get("OTEL_RESOURCE_ATTRIBUTES", "")

    @pytest.mark.parametrize(
        "bad_value",
        ["has space", 'has"quote', "has,comma", "has;semi", "has\\back", "has=eq"],
        ids=["space", "quote", "comma", "semicolon", "backslash", "equals"],
    )
    def test_a_value_otel_cannot_carry_is_refused_for_that_key_alone(self, tmp_path, bad_value):
        wrapper = _write_wrapper_with_args(tmp_path, [f"document={bad_value}", "skill=cold-read"])
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        assert "kensai.document" not in env_out.get("OTEL_RESOURCE_ATTRIBUTES", "")
        assert "kensai.skill=cold-read" in env_out["OTEL_RESOURCE_ATTRIBUTES"]
        assert "document" in result.stdout

    def test_project_with_a_readable_product_path_attaches_kensai_product(self, tmp_path):
        wrapper = _write_wrapper_with_args(tmp_path, ["project=widgetco"], subdir="ad-hoc-flow")
        project_dir = wrapper.parent / "system" / "projects" / "widgetco"
        project_dir.mkdir(parents=True)
        (project_dir / "project.md").write_text(
            "**Product path:** /home/user/work/private/widgetco-corp/widgetco   "
            "<!-- absolute -->\n"
        )
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        assert "kensai.product=widgetco" in env_out["OTEL_RESOURCE_ATTRIBUTES"]

    def test_no_project_md_attaches_no_product(self, tmp_path):
        wrapper = _write_wrapper_with_args(tmp_path, ["project=widgetco"])
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        assert "kensai.product" not in env_out.get("OTEL_RESOURCE_ATTRIBUTES", "")

    def test_no_product_path_line_attaches_no_product(self, tmp_path):
        wrapper = _write_wrapper_with_args(tmp_path, ["project=widgetco"])
        project_dir = wrapper.parent / "system" / "projects" / "widgetco"
        project_dir.mkdir(parents=True)
        (project_dir / "project.md").write_text("# Project Context\nNo product line here.\n")
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        assert "kensai.product" not in env_out.get("OTEL_RESOURCE_ATTRIBUTES", "")

    def test_an_unknown_key_does_not_drop_an_accepted_key_beside_it(self, tmp_path):
        """Integrity review, Task 2: an unknown key is refused "with one line", and the guardrail
        says a refusal drops its own key, never the run's other tags."""
        wrapper = _write_wrapper_with_args(tmp_path, ["bogus=value", "skill=cold-read"])
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        attrs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.skill=cold-read" in attrs
        assert "kensai.bogus" not in attrs
        assert len([ln for ln in result.stdout.splitlines() if "unknown key" in ln]) == 1

    def test_a_product_otel_cannot_carry_is_dropped_and_the_project_still_goes_out(self, tmp_path):
        """Integrity review, the guardrail applied to the derived product: a Product path whose
        basename carries a comma cannot be exported, so kensai.product alone is refused."""
        wrapper = _write_wrapper_with_args(tmp_path, ["project=widgetco"], subdir="ad-hoc-flow")
        project_dir = wrapper.parent / "system" / "projects" / "widgetco"
        project_dir.mkdir(parents=True)
        (project_dir / "project.md").write_text(
            "**Product path:** /srv/products/widget,co   <!-- absolute -->\n"
        )
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        attrs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.project=widgetco" in attrs
        assert "kensai.product" not in attrs
        assert "kensai.arm=ad-hoc-flow" in attrs

    def test_called_with_no_arguments_behaves_exactly_as_today(self, tmp_path):
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        keys = {
            pair.partition("=")[0] for pair in env_out["OTEL_RESOURCE_ATTRIBUTES"].split(",")
        }
        assert keys == {"kensai.arm", "kensai.run_id"}


# ── Task 3 (bash half) — a chain walk carries one id ────────


class TestChainWalkAttributes:
    """`instrument_run` reads `INSTRUMENT_RUN_WALK_ID` / `INSTRUMENT_RUN_CHAIN` from its
    caller's own environment — set by `chain.py` before it launches a document — and stamps
    `kensai.walk_id` / `kensai.chain` from them."""

    def _endpoint_file(self, tmp_path: Path) -> Path:
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text("http://localhost:4318\n")
        return endpoint_file

    def test_both_set_and_exportable_are_stamped(self, tmp_path):
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(wrapper, {
            "INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path)),
            "INSTRUMENT_RUN_WALK_ID": "walk-123",
            "INSTRUMENT_RUN_CHAIN": "example-foundation",
        })
        assert result.returncode == 0, result.stderr
        attrs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.walk_id=walk-123" in attrs
        assert "kensai.chain=example-foundation" in attrs

    def test_neither_set_stamps_neither(self, tmp_path):
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        attrs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.walk_id" not in attrs
        assert "kensai.chain" not in attrs

    def test_an_unexportable_walk_id_is_dropped_and_the_rest_still_goes_out(self, tmp_path):
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(wrapper, {
            "INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path)),
            "INSTRUMENT_RUN_WALK_ID": "bad,id",
            "INSTRUMENT_RUN_CHAIN": "example-foundation",
        })
        assert result.returncode == 0, result.stderr
        attrs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.walk_id" not in attrs
        assert "kensai.chain=example-foundation" in attrs

    def test_an_unexportable_chain_name_is_dropped_and_the_walk_id_still_goes_out(self, tmp_path):
        """Integrity review, Task 3: stamped "when they are set and carry a value it can export"
        — each of the two on its own, so a bad chain name must not take the walk id with it."""
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(wrapper, {
            "INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path)),
            "INSTRUMENT_RUN_WALK_ID": "walk-123",
            "INSTRUMENT_RUN_CHAIN": "bad chain",
        })
        assert result.returncode == 0, result.stderr
        attrs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.chain" not in attrs
        assert "kensai.walk_id=walk-123" in attrs


# ── Direct identity — a run's responsible role and, on an audit run, the producer it audits ─────


class TestDirectIdentityAttributes:
    """`instrument_run` reads `INSTRUMENT_RUN_ROLE` / `INSTRUMENT_RUN_AUDIT_TARGET` from its
    caller's own environment — set by `chain_development.py` before it launches a step — and
    stamps `kensai.role` / `kensai.audit_target` from them, the same shape `TestChainWalkAttributes`
    exercises for the walk/chain pair. Neither key is added to the launcher's accepted key=value
    arguments (`_INSTRUMENT_RUN_ACCEPTED_KEYS`) — both arrive only through the environment."""

    def _endpoint_file(self, tmp_path: Path) -> Path:
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text("http://localhost:4318\n")
        return endpoint_file

    def test_role_and_audit_target_are_stamped_directly(self, tmp_path):
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(wrapper, {
            "INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path)),
            "INSTRUMENT_RUN_ROLE": "kensaiapp-auditor",
            "INSTRUMENT_RUN_AUDIT_TARGET": "development-plan",
            "INSTRUMENT_RUN_WALK_ID": "walk-123",
            "INSTRUMENT_RUN_CHAIN": "example-foundation",
        })
        assert result.returncode == 0, result.stderr
        attrs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.role=kensaiapp-auditor" in attrs
        assert "kensai.audit_target=development-plan" in attrs
        # The existing walk and chain attributes still emit alongside the two new ones.
        assert "kensai.walk_id=walk-123" in attrs
        assert "kensai.chain=example-foundation" in attrs
        assert "kensai.arm=ad-hoc-flow" in attrs

    def test_unset_role_and_audit_target_stamp_neither(self, tmp_path):
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        attrs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.role" not in attrs
        assert "kensai.audit_target" not in attrs

    def test_unexportable_role_drops_only_role(self, tmp_path):
        """Integrity review: the instruction's behaviour is "while the audit target and existing
        attributes still emit" — so the walk/chain pair is asserted too, not only the target."""
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(wrapper, {
            "INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path)),
            "INSTRUMENT_RUN_ROLE": "bad role",
            "INSTRUMENT_RUN_AUDIT_TARGET": "development-plan",
            "INSTRUMENT_RUN_WALK_ID": "walk-123",
            "INSTRUMENT_RUN_CHAIN": "development",
        })
        assert result.returncode == 0, result.stderr
        attrs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.role" not in attrs
        assert "kensai.audit_target=development-plan" in attrs
        assert "kensai.walk_id=walk-123" in attrs
        assert "kensai.chain=development" in attrs
        assert "kensai.arm=ad-hoc-flow" in attrs

    def test_unexportable_audit_target_drops_only_audit_target(self, tmp_path):
        """Integrity review: "while role and existing attributes still emit" — both halves."""
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(wrapper, {
            "INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path)),
            "INSTRUMENT_RUN_ROLE": "kensaiapp-auditor",
            "INSTRUMENT_RUN_AUDIT_TARGET": "bad,target",
            "INSTRUMENT_RUN_WALK_ID": "walk-123",
            "INSTRUMENT_RUN_CHAIN": "development",
        })
        assert result.returncode == 0, result.stderr
        attrs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.audit_target" not in attrs
        assert "kensai.role=kensaiapp-auditor" in attrs
        assert "kensai.walk_id=walk-123" in attrs
        assert "kensai.chain=development" in attrs
        assert "kensai.arm=ad-hoc-flow" in attrs

    def test_direct_identity_coexists_with_the_launchers_subject_attributes(self, tmp_path):
        """CP-5 and the design's Test Additions row A — "existing walk/chain and subject
        attributes remain alongside them". The skill launcher calls
        `instrument_run skill=… project=…`; those pairs must still go out on the same run."""
        wrapper = _write_wrapper_with_args(
            tmp_path, ["skill=development-audit", "project=tools"], subdir="skill")
        result = _run(wrapper, {
            "INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path)),
            "INSTRUMENT_RUN_ROLE": "kensaiapp-auditor",
            "INSTRUMENT_RUN_AUDIT_TARGET": "development-design",
            "INSTRUMENT_RUN_WALK_ID": "walk-123",
            "INSTRUMENT_RUN_CHAIN": "development",
        })
        assert result.returncode == 0, result.stderr
        pairs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"].split(",")
        keys = [pair.split("=", 1)[0] for pair in pairs]
        assert "kensai.skill=development-audit" in pairs
        assert "kensai.project=tools" in pairs
        assert "kensai.arm=skill" in pairs
        assert "kensai.run_id" in keys
        assert "kensai.walk_id=walk-123" in pairs
        assert "kensai.chain=development" in pairs
        assert "kensai.role=kensaiapp-auditor" in pairs
        assert "kensai.audit_target=development-design" in pairs
        # Each identity is stamped once — never a duplicate key a reader must disambiguate.
        assert len(keys) == len(set(keys))

    def test_role_and_audit_target_are_not_accepted_as_key_value_arguments(self, tmp_path):
        """The design's Internal handoff: identity arrives only through the chain's environment,
        so it never becomes an argument a reader must interpret — `role=` / `audit_target=`
        handed as arguments are refused like any other unknown key."""
        wrapper = _write_wrapper_with_args(
            tmp_path, ["role=kensaiapp-auditor", "audit_target=development-plan"],
            subdir="ad-hoc-flow")
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        attrs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.role" not in attrs
        assert "kensai.audit_target" not in attrs

    def test_settings_carry_direct_identity_without_tool_details(self, tmp_path):
        wrapper = _write_wrapper(tmp_path, subdir="ad-hoc-flow")
        result = _run(wrapper, {
            "INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path)),
            "INSTRUMENT_RUN_ROLE": "kensaiapp-auditor",
            "INSTRUMENT_RUN_AUDIT_TARGET": "development-plan",
        })
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        settings = json.loads(env_out["INSTRUMENT_RUN_SETTINGS"])
        # No new settings key is added beyond the existing telemetry set — the two identities
        # ride inside OTEL_RESOURCE_ATTRIBUTES, not as a new enabling setting.
        assert set(settings["env"]) == set(TELEMETRY_KEYS)
        attrs = settings["env"]["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.role=kensaiapp-auditor" in attrs
        assert "kensai.audit_target=development-plan" in attrs
        forbidden = ("prompt", "tool_input", "tool-input", "command", "file_path", "file-path")
        for key, value in settings["env"].items():
            for term in forbidden:
                assert term not in key.lower()
                assert term not in value.lower()


# ── Vendor neutrality — no port, no host-specific literal ────────


def test_library_source_carries_no_literal_port():
    assert "4318" not in _LIB.read_text()


class TestSurfacedByIntegrity:
    """Two items `code-integrity-report.md` § Surfaced, not settled raised against this library,
    fixed by hand: a bare word is named rather than dropped in silence, and an arm holding a
    character `OTEL_RESOURCE_ATTRIBUTES` cannot carry is refused like every other value."""

    def _endpoint_file(self, tmp_path: Path) -> Path:
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text("http://localhost:4318\n")
        return endpoint_file

    def test_a_bare_word_argument_is_named_in_one_line_and_the_call_still_returns_0(self, tmp_path):
        wrapper = _write_wrapper_with_args(tmp_path, ["widgetco", "project=widgetco"])
        result = _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})
        assert result.returncode == 0, result.stderr
        assert [line for line in result.stdout.splitlines() if "'widgetco'" in line and "no '='" in line]
        assert "kensai.project=widgetco" in _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"]

    def test_an_arm_holding_a_comma_is_refused_and_the_rest_still_goes_out(self, tmp_path):
        wrapper = _write_wrapper_with_args(tmp_path, ["project=widgetco"])
        result = _run(
            wrapper,
            {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path)), "INSTRUMENT_RUN_ARM": "a,b"},
        )
        assert result.returncode == 0, result.stderr
        attrs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"]
        assert "kensai.arm=" not in attrs
        assert "kensai.project=widgetco" in attrs


# ── Provenance — the provider a run went through, the model and effort it went at, and where
#    those came from (change 2026-09-30_runs-record-provider-model-effort-and-source, Task 1) ────


class TestProvenanceKeys:
    """CP-188–190, CP-194: the skill launcher hands over `provider=`, `model=`, `effort=` and
    `source=` beside its subject, and each is stamped `kensai.<key>` under the rules the four
    older keys already follow."""

    _NEW_KEYS = ("provider", "model", "effort", "source")

    def _endpoint_file(self, tmp_path: Path) -> Path:
        endpoint_file = tmp_path / "endpoint"
        endpoint_file.write_text("http://localhost:4318\n")
        return endpoint_file

    def _call(self, tmp_path: Path, args: list[str]) -> subprocess.CompletedProcess:
        wrapper = _write_wrapper_with_args(tmp_path, args, subdir="skill")
        return _run(wrapper, {"INSTRUMENT_RUN_ENDPOINT_FILE": str(self._endpoint_file(tmp_path))})

    def test_provider_model_effort_source_are_stamped_as_kensai_keys(self, tmp_path):
        result = self._call(
            tmp_path,
            ["provider=codex", "model=gpt-6.1-sol", "effort=high", "source=intelligence"],
        )
        assert result.returncode == 0, result.stderr
        env_out = _env_lines(result.stdout)
        exported = env_out["OTEL_RESOURCE_ATTRIBUTES"].split(",")
        settings = json.loads(env_out["INSTRUMENT_RUN_SETTINGS"])
        handed_over = settings["env"]["OTEL_RESOURCE_ATTRIBUTES"].split(",")
        for pair in ("kensai.provider=codex", "kensai.model=gpt-6.1-sol",
                     "kensai.effort=high", "kensai.source=intelligence"):
            assert pair in exported
            assert pair in handed_over

    def test_empty_model_and_effort_attach_nothing_but_source_is_stamped(self, tmp_path):
        result = self._call(
            tmp_path, ["provider=codex", "model=", "effort=", "source=default"]
        )
        assert result.returncode == 0, result.stderr
        keys = [
            pair.partition("=")[0]
            for pair in _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"].split(",")
        ]
        assert "kensai.model" not in keys
        assert "kensai.effort" not in keys
        assert "kensai.provider" in keys
        assert "kensai.source" in keys

    def test_model_containing_a_comma_drops_only_that_key(self, tmp_path):
        result = self._call(
            tmp_path,
            ["skill=ad-hoc-plan", "provider=codex", "model=a,b", "source=tier"],
        )
        assert result.returncode == 0, result.stderr
        assert "INSTRUMENT_RUN_EXIT=0" in result.stdout
        pairs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"].split(",")
        assert not [pair for pair in pairs if pair.startswith("kensai.model=")]
        assert "kensai.provider=codex" in pairs
        assert "kensai.source=tier" in pairs
        assert "kensai.skill=ad-hoc-plan" in pairs
        naming = [line for line in result.stdout.splitlines() if "kensai.model" in line]
        assert len(naming) == 1
        assert "'a,b'" in naming[0]

    @pytest.mark.parametrize("key", _NEW_KEYS)
    def test_each_new_key_with_an_unexportable_value_drops_only_itself(self, tmp_path, key):
        """CP-194 names no key: every one of the four is refused alone, never the others."""
        values = {"provider": "codex", "model": "m", "effort": "high", "source": "tier"}
        values[key] = "has space"
        result = self._call(tmp_path, [f"{k}={v}" for k, v in values.items()])
        assert result.returncode == 0, result.stderr
        pairs = _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"].split(",")
        assert not [pair for pair in pairs if pair.startswith(f"kensai.{key}=")]
        for other in self._NEW_KEYS:
            if other != key:
                assert f"kensai.{other}={values[other]}" in pairs

    def test_existing_keys_and_order_are_unchanged(self, tmp_path):
        """The older keys keep their places; the new ones follow in the call's own argument
        order — here the skill launcher's own order, subject first."""
        result = self._call(
            tmp_path,
            ["skill=development-specs", "project=tools", "provider=claude",
             "model=claude-opus-5-5", "effort=high", "source=intelligence"],
        )
        assert result.returncode == 0, result.stderr
        keys = [
            pair.partition("=")[0]
            for pair in _env_lines(result.stdout)["OTEL_RESOURCE_ATTRIBUTES"].split(",")
        ]
        assert keys == [
            "kensai.arm", "kensai.run_id", "kensai.skill", "kensai.project",
            "kensai.provider", "kensai.model", "kensai.effort", "kensai.source",
        ]

    def test_unknown_key_message_names_all_eight_accepted_keys(self, tmp_path):
        result = self._call(tmp_path, ["bogus=value"])
        assert result.returncode == 0, result.stderr
        refusal = [line for line in result.stdout.splitlines() if "unknown key" in line]
        assert len(refusal) == 1
        for key in ("project", "document", "skill", "target_instance", *self._NEW_KEYS):
            assert key in refusal[0].split("—", 1)[1]
