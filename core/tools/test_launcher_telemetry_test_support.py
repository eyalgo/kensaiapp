"""Tests for `launcher_telemetry_test_support.py` — the observer and the single-launch checks the
six launcher suites use to show what a launcher prints, exports and hands its run over
`run_telemetry`.

The support is test-only machinery, so what is proved here is the machinery's own honesty: that
observing a launcher changes nothing it prints, that a child shell cannot overwrite what was
observed, that a stated observation is held to exactly what the case states, and that the
real-package skip-versus-failure rule holds (CP-685, CP-689, CP-763). None of it needs the real
telemetry package: the cases that run a launcher use a neutral fixture command, and the
real-package rule is proved in nested pytest runs against fixture homes, as `test_run_telemetry.py`
proves its own.
"""

from __future__ import annotations

import base64
import dataclasses
import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import launcher_telemetry_test_support as support
from test_skill_launcher_telemetry import FIXTURE_COMMAND, install_telemetry_command

_TOOLS = Path(__file__).resolve().parent
_ENDPOINT = "http://127.0.0.1:4318"
_RUN_ID_A = "11111111-1111-4111-8111-111111111111"
_ENDPOINT_KEY = "OTEL_EXPORTER_OTLP_ENDPOINT"
_ATTRIBUTES_KEY = "OTEL_RESOURCE_ATTRIBUTES"

_HEADER = """\
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CORE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
"""

_HELPER_LAUNCHER = _HEADER + """\
source "$CORE_DIR/tools/run_telemetry.sh"
run_telemetry skill=fx provider=claude model= effort= source=default
echo "DRY RUN"
if [ -n "${INSTRUMENT_RUN_SETTINGS:-}" ]; then
  echo "claude --settings '$INSTRUMENT_RUN_SETTINGS'"
else
  echo "claude"
fi
"""

# What `_HELPER_LAUNCHER` stamps: the arm is its folder's name, then the arguments it passes with
# the two empty ones left out. A scratch tree that is no git checkout has no instance to add.
_HELPER_LAUNCHER_PAIRS = [
    ("arm", "fx"), ("run_id", None), ("skill", "fx"), ("provider", "claude"), ("source", "default"),
]


def _make_core(root: Path, **launchers: str) -> Path:
    """A scratch core holding the real helper beside launchers named by keyword, each at
    `core/launchers/fx/<name>.sh`. Returns the core."""
    core = root / "core"
    (core / "tools").mkdir(parents=True)
    shutil.copy(_TOOLS / "run_telemetry.sh", core / "tools" / "run_telemetry.sh")
    folder = core / "launchers" / "fx"
    folder.mkdir(parents=True)
    for name, body in launchers.items():
        script = folder / f"{name}.sh"
        script.write_text(body)
        script.chmod(0o755)
    return core


def _launch_environment(root: Path) -> dict[str, str]:
    """An environment with no telemetry state of its own: HOME and the endpoint under `root`, the
    neutral fixture command installed and named."""
    home = root / "home"
    home.mkdir(exist_ok=True)
    endpoint = root / "endpoint"
    endpoint.write_text(_ENDPOINT + "\n")
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("OTEL_", "INSTRUMENT_RUN_", "KA_"))
        and key not in ("BASH_ENV", "KENSAIAPP_CONTEXT_CAP", "KENSAIAPP_TELEMETRY_COMMAND")
    }
    env["HOME"] = str(home)
    env["INSTRUMENT_RUN_ENDPOINT_FILE"] = str(endpoint)
    env["GIT_CONFIG_GLOBAL"] = os.devnull
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    install_telemetry_command(home, env)
    return env


def _work(root: Path) -> Path:
    work = root / "work"
    work.mkdir(exist_ok=True)
    return work


# --- the observation ------------------------------------------------------------------------------

_PLAIN = _HEADER + """\
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_METRICS_EXPORTER=otlp
export OTEL_LOGS_EXPORTER=otlp
export OTEL_EXPORTER_OTLP_PROTOCOL=http/json
export OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318
export OTEL_RESOURCE_ATTRIBUTES=kensai.arm=fx,kensai.run_id=aaa
export INSTRUMENT_RUN_SETTINGS='{"env":{"OTEL_RESOURCE_ATTRIBUTES":"kensai.arm=fx"}}'
export SECRET_TOKEN=hunter2
echo "          Telemetry:    kensai.arm=fx,kensai.run_id=aaa → http://127.0.0.1:4318"
echo "claude --settings '$INSTRUMENT_RUN_SETTINGS'"
echo "a line on stderr" >&2
exit 7
"""


def test_observer_preserves_launcher_output_and_status(tmp_path):
    core = _make_core(tmp_path, plain=_PLAIN)
    launcher = core / "launchers" / "fx" / "plain.sh"
    env = _launch_environment(tmp_path)
    work = _work(tmp_path)

    unobserved = support.run_launcher(launcher, [], cwd=work, env=env)
    observed = support.run_launcher(
        launcher, [], cwd=work, env=env, observation_dir=tmp_path / "observation"
    )

    assert (observed.stdout, observed.stderr, observed.status) == (
        unobserved.stdout,
        unobserved.stderr,
        unobserved.status,
    )
    assert observed.status == 7
    assert unobserved.exports == {}
    assert set(observed.exports) == set(support.OBSERVED_NAMES)
    assert observed.exports[_ENDPOINT_KEY] == _ENDPOINT
    assert observed.exports["INSTRUMENT_RUN_SETTINGS"] == (
        '{"env":{"OTEL_RESOURCE_ATTRIBUTES":"kensai.arm=fx"}}'
    )
    assert observed.helper_source is None


_STRICT = _HEADER + """\
set -euo pipefail
echo "strict launcher output"
exit "${EXIT_WITH:-0}"
"""


@pytest.mark.parametrize("status", [0, 7])
def test_observer_leaves_a_strict_launchers_status_alone(tmp_path, status):
    """Real launchers run under `set -euo pipefail`, and one that never defined `run_telemetry`
    has no function for the observer's lookup to find: that failure must not become the status."""
    core = _make_core(tmp_path, strict=_STRICT)
    launcher = core / "launchers" / "fx" / "strict.sh"
    env = {**_launch_environment(tmp_path), "EXIT_WITH": str(status)}
    work = _work(tmp_path)

    unobserved = support.run_launcher(launcher, [], cwd=work, env=env)
    observed = support.run_launcher(
        launcher, [], cwd=work, env=env, observation_dir=tmp_path / "observation"
    )

    assert (observed.stdout, observed.stderr, observed.status) == (
        unobserved.stdout,
        unobserved.stderr,
        status,
    )
    assert observed.helper_source is None


def test_observer_records_only_the_allowlisted_names(tmp_path):
    core = _make_core(tmp_path, plain=_PLAIN)
    launcher = core / "launchers" / "fx" / "plain.sh"
    observed = support.run_launcher(
        launcher, [], cwd=_work(tmp_path), env=_launch_environment(tmp_path),
        observation_dir=tmp_path / "observation",
    )

    records = [line.split(" ") for line in observed.record.splitlines() if line.startswith("VAR")]
    recorded = {fields[2] for fields in records}
    assert recorded == set(support.OBSERVED_NAMES)
    assert "SECRET_TOKEN" not in observed.record
    assert "hunter2" not in observed.record
    assert base64.b64encode(b"hunter2").decode() not in observed.record
    assert "HOME" not in observed.record


_CHILD_SHELLS = _HEADER + """\
export CLAUDE_CODE_ENABLE_TELEMETRY=1
export OTEL_RESOURCE_ATTRIBUTES=kensai.arm=fx
export INSTRUMENT_RUN_SETTINGS='{"env":{"OTEL_RESOURCE_ATTRIBUTES":"kensai.arm=fx"}}'
bash -c 'export OTEL_RESOURCE_ATTRIBUTES=poisoned CLAUDE_CODE_ENABLE_TELEMETRY=0 \
  INSTRUMENT_RUN_SETTINGS=poisoned; true'
bash -c 'unset BASH_ENV; export OTEL_RESOURCE_ATTRIBUTES=poisoned; true'
echo "claude --settings '$INSTRUMENT_RUN_SETTINGS'"
"""


def test_child_shell_cannot_overwrite_launcher_observation(tmp_path):
    core = _make_core(tmp_path, children=_CHILD_SHELLS)
    launcher = core / "launchers" / "fx" / "children.sh"

    observed = support.run_launcher(
        launcher, [], cwd=_work(tmp_path), env=_launch_environment(tmp_path),
        observation_dir=tmp_path / "observation",
    )

    # The child shell really did record itself under its own process id — the case is a real one.
    records = [line.split(" ") for line in observed.record.splitlines() if line.startswith("VAR")]
    processes = {fields[1] for fields in records}
    assert len(processes) >= 2, observed.record
    assert observed.exports[_ATTRIBUTES_KEY] == "kensai.arm=fx"
    assert observed.exports["CLAUDE_CODE_ENABLE_TELEMETRY"] == "1"
    assert observed.exports["INSTRUMENT_RUN_SETTINGS"] == (
        '{"env":{"OTEL_RESOURCE_ATTRIBUTES":"kensai.arm=fx"}}'
    )
    assert observed.handed_settings == {"env": {"OTEL_RESOURCE_ATTRIBUTES": "kensai.arm=fx"}}


def test_a_launcher_that_exports_nothing_observes_unset_names(tmp_path):
    core = _make_core(tmp_path, quiet=_HEADER + 'echo "claude"\n')
    launcher = core / "launchers" / "fx" / "quiet.sh"

    observed = support.run_launcher(
        launcher, [], cwd=_work(tmp_path), env=_launch_environment(tmp_path),
        observation_dir=tmp_path / "observation",
    )

    assert observed.exports == {name: None for name in support.OBSERVED_NAMES}
    assert observed.handed_settings is None


def test_the_launcher_must_not_hand_the_observer_a_startup_file_of_its_own(tmp_path):
    core = _make_core(tmp_path, quiet=_HEADER + 'echo "claude"\n')
    launcher = core / "launchers" / "fx" / "quiet.sh"
    env = _launch_environment(tmp_path)
    env["BASH_ENV"] = str(tmp_path / "theirs")

    with pytest.raises(AssertionError, match="BASH_ENV"):
        support.run_launcher(
            launcher, [], cwd=_work(tmp_path), env=env, observation_dir=tmp_path / "observation"
        )


# --- one launcher run over the real helper --------------------------------------------------------


def test_a_launcher_that_uses_the_helper_is_observed_over_the_helper(tmp_path):
    core = _make_core(tmp_path, launcher=_HELPER_LAUNCHER)
    launcher = core / "launchers" / "fx" / "launcher.sh"

    observation = support.run_launcher(
        launcher, [], cwd=_work(tmp_path), env=_launch_environment(tmp_path),
        observation_dir=tmp_path / "observed",
    )

    support.assert_instrumented_observation(
        observation,
        pairs=_HELPER_LAUNCHER_PAIRS,
        helper=core / "tools" / "run_telemetry.sh",
    )
    assert observation.stdout.splitlines()[1] == "DRY RUN"


def test_the_helper_the_launcher_sourced_is_the_one_the_case_names(tmp_path):
    core = _make_core(tmp_path, launcher=_HELPER_LAUNCHER)
    launcher = core / "launchers" / "fx" / "launcher.sh"

    observation = support.run_launcher(
        launcher, [], cwd=_work(tmp_path), env=_launch_environment(tmp_path),
        observation_dir=tmp_path / "observed",
    )

    assert Path(observation.helper_source).resolve() == (
        core / "tools" / "run_telemetry.sh"
    ).resolve()
    with pytest.raises(AssertionError, match="not"):
        support.assert_instrumented_observation(
            observation, pairs=_HELPER_LAUNCHER_PAIRS, helper=_TOOLS / "run_telemetry.sh"
        )


# --- a launch with no telemetry -------------------------------------------------------------------


def _uninstrumented(cap: str | None) -> support.Observation:
    env = {"KENSAIAPP_CONTEXT_CAP": cap} if cap else None
    exports = {name: None for name in support.OBSERVED_NAMES}
    if env:
        exports["INSTRUMENT_RUN_SETTINGS"] = json.dumps({"env": env}, separators=(",", ":"))
    return support.Observation(
        status=0,
        stdout="          (no telemetry command configured in KENSAIAPP_TELEMETRY_COMMAND "
        "— run uninstrumented)\n",
        stderr="",
        exports=exports,
        handed_settings={"env": env} if env else None,
        helper_source="/helper/run_telemetry.sh",
    )


@pytest.mark.parametrize("cap", [None, "250000"])
def test_an_uninstrumented_launch_is_cap_only_or_empty(cap):
    support.assert_uninstrumented(_uninstrumented(cap), cap=cap)


def test_an_uninstrumented_launch_with_a_telemetry_export_fails():
    leaking = _uninstrumented(None)
    leaking = dataclasses.replace(
        leaking, exports={**leaking.exports, "CLAUDE_CODE_ENABLE_TELEMETRY": "1"}
    )

    with pytest.raises(AssertionError):
        support.assert_uninstrumented(leaking, cap=None)
    with pytest.raises(AssertionError):
        support.assert_uninstrumented(_uninstrumented("250000"), cap=None)
    with pytest.raises(AssertionError):
        support.assert_uninstrumented(_uninstrumented(None), cap="250000")


# --- a launch with telemetry: the complete literal observation -----------------------------------

_HELPER_PATH = "/scratch/core/tools/run_telemetry.sh"
_PAIRS = [("arm", "demo"), ("run_id", None), ("skill", "s"), ("provider", "claude")]


def _instrumented(
    *, run_id: str = _RUN_ID_A, attributes: str | None = None, cap: str | None = None,
    endpoint: str = _ENDPOINT,
) -> support.Observation:
    """What a correct instrumented dry run of the `_PAIRS` launch shows."""
    attributes = attributes or f"kensai.arm=demo,kensai.run_id={run_id},kensai.skill=s," \
        "kensai.provider=claude"
    env = {
        "CLAUDE_CODE_ENABLE_TELEMETRY": "1",
        "OTEL_METRICS_EXPORTER": "otlp",
        "OTEL_LOGS_EXPORTER": "otlp",
        "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
        _ENDPOINT_KEY: endpoint,
        **({"KENSAIAPP_CONTEXT_CAP": cap} if cap else {}),
        _ATTRIBUTES_KEY: attributes,
    }
    exports = {name: env[name] for name in support.TELEMETRY_EXPORT_NAMES}
    exports["INSTRUMENT_RUN_SETTINGS"] = json.dumps({"env": env}, separators=(",", ":"))
    return support.Observation(
        status=0,
        stdout=f"          Telemetry:    {attributes} → {endpoint}\n",
        stderr="",
        exports=exports,
        handed_settings={"env": env},
        helper_source=_HELPER_PATH,
    )


def _assert_instrumented(observation, **overrides):
    arguments = {"pairs": _PAIRS, "helper": Path(_HELPER_PATH), **overrides}
    support.assert_instrumented_observation(observation, **arguments)


@pytest.mark.parametrize("cap", [None, "250000"])
def test_a_complete_instrumented_observation_passes(cap):
    _assert_instrumented(_instrumented(cap=cap), cap=cap)


def test_the_run_id_is_matched_by_shape_and_read_back_from_every_representation():
    other = _RUN_ID_A.replace("1", "2", 1)
    attributes = _instrumented().exports[_ATTRIBUTES_KEY]
    elsewhere = attributes.replace(_RUN_ID_A, other)
    leaking = _instrumented()
    in_settings = dataclasses.replace(
        leaking,
        handed_settings={"env": {**leaking.handed_settings["env"], _ATTRIBUTES_KEY: elsewhere}},
    )
    in_exports = dataclasses.replace(
        leaking, exports={**leaking.exports, _ATTRIBUTES_KEY: elsewhere}
    )

    _assert_instrumented(_instrumented(run_id=other))
    for drifted in (in_settings, in_exports):
        with pytest.raises(AssertionError):
            _assert_instrumented(drifted)


@pytest.mark.parametrize(
    "not_a_run_id", ["AAAAAAAA-AAAA-4AAA-8AAA-AAAAAAAAAAAA", "r-1", _RUN_ID_A[:-1]]
)
def test_a_run_id_that_is_not_a_lowercase_uuid_fails(not_a_run_id):
    with pytest.raises(AssertionError):
        _assert_instrumented(_instrumented(run_id=not_a_run_id))


def _breaking(name):
    base = _instrumented(cap="250000")
    env = base.handed_settings["env"]
    wrong = {
        "status": dataclasses.replace(base, status=3),
        "stderr-line": dataclasses.replace(
            base, stderr="          Telemetry:    kensai.arm=demo → http://x\n"
        ),
        "attribute-order": _instrumented(
            cap="250000",
            attributes=f"kensai.run_id={_RUN_ID_A},kensai.arm=demo,kensai.skill=s,"
            "kensai.provider=claude",
        ),
        "extra-attribute": _instrumented(
            cap="250000", attributes=base.exports[_ATTRIBUTES_KEY] + ",kensai.model=m"
        ),
        "endpoint": _instrumented(cap="250000", endpoint="http://127.0.0.1:9"),
        "unset-export": dataclasses.replace(
            base, exports={**base.exports, "OTEL_LOGS_EXPORTER": None}
        ),
        "export-value": dataclasses.replace(
            base, exports={**base.exports, "OTEL_EXPORTER_OTLP_PROTOCOL": "grpc"}
        ),
        "exported-settings": dataclasses.replace(
            base, exports={**base.exports, "INSTRUMENT_RUN_SETTINGS": "{}"}
        ),
        "handed-settings": dataclasses.replace(
            base,
            handed_settings={"env": {k: v for k, v in env.items() if k != "OTEL_LOGS_EXPORTER"}},
        ),
        "handed-none": dataclasses.replace(base, handed_settings=None),
        "helper": dataclasses.replace(base, helper_source="/elsewhere/run_telemetry.sh"),
        "second-line": dataclasses.replace(
            base, stdout=base.stdout + "          (kensai.arm refused — arm not attached)\n"
        ),
    }
    return wrong[name]


@pytest.mark.parametrize(
    "name",
    [
        "status", "stderr-line", "attribute-order", "extra-attribute", "endpoint", "unset-export",
        "export-value", "exported-settings", "handed-settings", "handed-none", "helper",
        "second-line",
    ],
)
def test_any_difference_from_the_stated_observation_fails(name):
    with pytest.raises(AssertionError):
        _assert_instrumented(_breaking(name), cap="250000")


def test_the_cap_the_case_states_is_the_cap_the_settings_carry():
    with pytest.raises(AssertionError):
        _assert_instrumented(_instrumented(), cap="250000")
    with pytest.raises(AssertionError):
        _assert_instrumented(_instrumented(cap="250000"), cap=None)


# --- an unreachable package is a skip; a reached one that fails is a failure ----------------------

_NESTED_TEST = '''\
import os
import sys
from pathlib import Path

import launcher_telemetry_test_support as support
from test_launcher_telemetry_test_support import (
    _HELPER_LAUNCHER, _HELPER_LAUNCHER_PAIRS, _launch_environment, _make_core, _work,
)


def test_real_package_observation(tmp_path):
    package = support.require_real_package(tmp_path)
    root = tmp_path / "launch"
    root.mkdir()
    core = _make_core(root, launcher=_HELPER_LAUNCHER)
    env = _launch_environment(root)
    env["HOME"] = str(package.home)
    env["KENSAIAPP_TELEMETRY_COMMAND"] = package.command
    observation = support.run_launcher(
        core / "launchers" / "fx" / "launcher.sh", [], cwd=_work(root), env=env,
        observation_dir=root / "observed",
    )
    support.assert_instrumented_observation(
        observation, pairs=_HELPER_LAUNCHER_PAIRS, helper=core / "tools" / "run_telemetry.sh"
    )
'''


def _nested(tmp_path: Path, home: Path, **extra: str) -> subprocess.CompletedProcess:
    tmp_path.mkdir(exist_ok=True)
    test_file = tmp_path / "test_nested_real_package.py"
    test_file.write_text(_NESTED_TEST)
    env = {k: v for k, v in os.environ.items() if k != support.COMMAND_VARIABLE}
    env[support.COMMAND_VARIABLE] = ""
    env["HOME"] = str(home)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(_TOOLS)
    env.update(extra)
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(test_file), "-q", "-rs", "-n", "0",
         "-p", "no:cacheprovider", "--rootdir", str(tmp_path), "-c", os.devnull],
        cwd=str(tmp_path), capture_output=True, text=True, env=env, timeout=300,
    )


def test_unreachable_package_skips_but_reached_failure_fails(tmp_path):
    unset_home = tmp_path / "unset"
    unset_home.mkdir()
    unset = _nested(tmp_path / "n1", unset_home)
    assert unset.returncode == 0, unset.stdout + unset.stderr
    assert support.SKIP_UNSET in unset.stdout
    assert "skipped" in unset.stdout
    assert "passed" not in unset.stdout and "failed" not in unset.stdout

    missing_home = tmp_path / "missing"
    missing_home.mkdir()
    absent = _nested(tmp_path / "n2", missing_home, **{support.COMMAND_VARIABLE: "no-such-command"})
    path = missing_home / ".kensaiapp" / "venv" / "bin" / "no-such-command"
    assert absent.returncode == 0, absent.stdout + absent.stderr
    assert support.skip_reason_unreachable(path) in absent.stdout
    assert "failed" not in absent.stdout and "passed" not in absent.stdout

    for mode, number in (("exit-3", 3), ("garbage", 4)):
        reached_home = tmp_path / f"reached-{mode}"
        bin_dir = reached_home / ".kensaiapp" / "venv" / "bin"
        bin_dir.mkdir(parents=True)
        command = bin_dir / FIXTURE_COMMAND
        if mode == "exit-3":
            command.write_text("#!/bin/sh\nexit 3\n")
        else:
            command.write_text("#!/bin/sh\necho 'this is not a settings document'\n")
        command.chmod(0o755)
        reached = _nested(
            tmp_path / f"n{number + 2}", reached_home, **{support.COMMAND_VARIABLE: FIXTURE_COMMAND}
        )
        assert reached.returncode == 1, reached.stdout + reached.stderr
        assert "failed" in reached.stdout and "skipped" not in reached.stdout


def test_the_skip_decision_names_what_is_missing(tmp_path):
    reason = support.real_package_skip_reason
    assert reason({}, tmp_path) == support.SKIP_UNSET
    assert reason({support.COMMAND_VARIABLE: ""}, tmp_path) == support.SKIP_UNSET
    assert reason({support.COMMAND_VARIABLE: "a/b"}, tmp_path) == support.SKIP_NOT_PLAIN
    unreachable = reason({support.COMMAND_VARIABLE: "absent-command"}, tmp_path)
    assert unreachable == support.skip_reason_unreachable(
        tmp_path / ".kensaiapp" / "venv" / "bin" / "absent-command"
    )
    present = tmp_path / ".kensaiapp" / "venv" / "bin"
    present.mkdir(parents=True)
    (present / "present-command").write_text("#!/bin/sh\n")
    (present / "present-command").chmod(0o755)
    assert reason({support.COMMAND_VARIABLE: "present-command"}, tmp_path) is None


# --- the provenance assertion ---------------------------------------------------------------------


_GOOD_CALL = (
    'run_telemetry skill="$skill" project="$project" provider="$provider" model="$m" '
    'effort="$e" source="$s"\n'
)


def _launcher_text(tmp_path: Path, text: str) -> Path:
    launcher = tmp_path / "launcher.sh"
    launcher.write_text(text)
    return launcher


def test_helper_provenance_requires_four_keys_on_the_call_line(tmp_path):
    support.assert_run_telemetry_call_carries_provenance(_launcher_text(tmp_path, _GOOD_CALL))

    # Definitions, `source` lines, a path and a comment are not calls, whatever follows them.
    around = (
        "# run_telemetry provider= model= effort= source=\n"
        'source "$CORE_DIR/tools/run_telemetry.sh"\n'
        "run_telemetry() { :; }\n"
        "echo run_telemetry provider= model= effort= source=\n"
    )
    support.assert_run_telemetry_call_carries_provenance(
        _launcher_text(tmp_path, around + _GOOD_CALL)
    )


_FOUR = 'run_telemetry provider="$p" model="$m" effort="$e" source="$s"\n'
_NO_CALL = "no run_telemetry call"


@pytest.mark.parametrize(
    "text, reason",
    [
        ('run_telemetry skill="$s" provider="$p" model="$m" effort="$e"\n', "source"),
        ('run_telemetry provider="$p" effort="$e" source="$s"\n', "model"),
        ("run_telemetry\n", "provider"),
        ('run_telemetry skill="$s" # provider= model= effort= source=\n', "provider"),
        ('run_telemetry provider="$p" model="$m" \\\n  effort="$e" source="$s"\n', "effort"),
        ('run_telemetry run_provider="$p" run_model="$m" run_effort="$e" run_source="$s"\n',
         "provider"),
        (_FOUR.replace("run_telemetry ", "run_telemetry_wrapper "), _NO_CALL),
        (_FOUR.replace("run_telemetry ", "xrun_telemetry "), _NO_CALL),
        ("# " + _FOUR, _NO_CALL),
        ("run_telemetry() { :; }\nsource run_telemetry.sh\n", _NO_CALL),
        ("", _NO_CALL),
    ],
    ids=[
        "omitted-source", "omitted-model-and-effort", "bare-call", "keys-in-a-trailing-comment",
        "continued-line", "lookalike-keys", "lookalike-function", "lookalike-prefix",
        "comment-only", "definition-and-source-only", "empty-file",
    ],
)
def test_helper_provenance_rejects_what_the_call_line_does_not_carry(tmp_path, text, reason):
    with pytest.raises(AssertionError, match=reason):
        support.assert_run_telemetry_call_carries_provenance(_launcher_text(tmp_path, text))


# --- the trees a launcher is run in ---------------------------------------------------------------

_REAL_LAUNCHER = _TOOLS.parent / "launchers" / "cold-read" / "launcher.sh"


def test_scratch_core_copies_the_tools_without_their_tests_and_borrows_the_rest(tmp_path):
    launcher = support.scratch_core(tmp_path, _REAL_LAUNCHER)

    core = tmp_path / "core"
    assert launcher == core / "launchers" / "cold-read" / "launcher.sh"
    assert os.access(launcher, os.X_OK)
    assert launcher.read_bytes() == _REAL_LAUNCHER.read_bytes()
    for tool in ("run_telemetry.sh", "telemetry_command.py", "pin.py"):
        assert (core / "tools" / tool).read_bytes() == (_TOOLS / tool).read_bytes()
        assert not (core / "tools" / tool).is_symlink()
    assert not list((core / "tools").glob("test_*"))
    assert not (core / "tools" / "conftest.py").exists()
    assert sorted(path.name for path in (core / "launchers").iterdir()) == ["cold-read"]
    assert not list((core / "launchers" / "cold-read").glob("test_*"))
    assert (core / "prompts").is_symlink()
    assert (core / "prompts").resolve() == _TOOLS.parent / "prompts"


def test_a_pin_is_a_scratch_core_with_a_manifest_naming_its_source_host(tmp_path):
    host = tmp_path / "host"
    host.mkdir()

    launcher = support.make_pin(tmp_path / "pin", _REAL_LAUNCHER, host)

    manifest = json.loads((tmp_path / "pin" / "pin.json").read_text())
    assert manifest["source_host_root"] == str(host)
    assert launcher == tmp_path / "pin" / "core" / "launchers" / "cold-read" / "launcher.sh"


def test_a_satellite_reaches_the_core_through_its_own_symlink(tmp_path):
    launcher = support.scratch_core(tmp_path / "host", _REAL_LAUNCHER)

    bound = support.bind_satellite(launcher, tmp_path / "satellite")

    assert bound == tmp_path / "satellite" / "core" / "launchers" / "cold-read" / "launcher.sh"
    assert (tmp_path / "satellite" / "core").is_symlink()
    assert bound.resolve() == launcher.resolve()


def test_the_telemetry_environment_carries_no_telemetry_state_of_its_own(tmp_path):
    parent = {
        "PATH": "/usr/bin",
        "OTEL_RESOURCE_ATTRIBUTES": "x",
        "INSTRUMENT_RUN_SETTINGS": "{}",
        "KA_ADAPTER_LOG": "x",
        support.COMMAND_VARIABLE: "inherited",
        support.CAP_NAME: "1",
        "KENSAIAPP_PIN": "/pin",
        "BASH_ENV": "/x",
    }
    kept = support.telemetry_environment(parent, home=tmp_path / "h", endpoint_file=tmp_path / "e")
    assert kept == {
        "PATH": "/usr/bin",
        "HOME": str(tmp_path / "h"),
        "INSTRUMENT_RUN_ENDPOINT_FILE": str(tmp_path / "e"),
    }

    explicit = support.telemetry_environment(
        parent, home=tmp_path / "h", endpoint_file=tmp_path / "e", cap="250000", command=""
    )
    assert explicit[support.COMMAND_VARIABLE] == ""
    assert explicit[support.CAP_NAME] == "250000"


@pytest.mark.parametrize(
    ("kind", "cause"),
    [
        ("valid", None),
        ("absent", "no published telemetry endpoint at {file}"),
        ("malformed", "telemetry endpoint at {file} is unreadable or malformed"),
        ("remote", "telemetry endpoint at {file} is not on this machine (loopback only)"),
    ],
)
def test_an_endpoint_is_published_in_the_form_each_cause_needs(tmp_path, kind, cause):
    endpoint_file = tmp_path / "endpoint"
    endpoint_file.write_text("a stale file\n")

    printed = support.publish_endpoint(endpoint_file, kind)

    assert printed == (cause.format(file=endpoint_file) if cause else None)
    assert endpoint_file.exists() == (kind != "absent")
    if kind == "valid":
        assert endpoint_file.read_text() == support.LOOPBACK_ENDPOINT + "\n"


@pytest.mark.parametrize("combination", support.ORDINARY_COMBINATIONS)
def test_an_ordinary_launch_has_the_setting_on_its_source_host_alone(tmp_path, combination):
    instance = tmp_path / "instance"
    instance.mkdir()

    launch = support.ordinary_launch(tmp_path, _REAL_LAUNCHER, instance, combination, "a-command")

    assert launch.instance == instance
    settings = {path.parent for path in tmp_path.rglob(support.SETTING_FILE)}
    assert settings == {launch.host}
    assert launch.host == (instance if combination.endswith("host") else tmp_path / "host")
    setting = (launch.host / support.SETTING_FILE).read_text()
    assert setting == f"{support.COMMAND_VARIABLE}=a-command\n"
    assert bool(list(tmp_path.rglob("pin.json"))) == combination.startswith("pinned")
    assert (instance / "core").is_symlink() == (combination == "direct-satellite")
    assert os.access(launch.launcher, os.X_OK)


_CAUSE_WORDS = {
    "unavailable-command": "no runnable telemetry command at ",
    "empty-command": "no telemetry command configured in ",
    "environment-over-setting": "no runnable telemetry command at ",
    "no-command-and-no-setting": "no telemetry command configured in ",
    "non-executable-command": "no runnable telemetry command at ",
    "failing-command": "exited with status 3",
    "garbled-command": "did not print a usable settings document",
    "absent-endpoint": "no published telemetry endpoint at ",
    "malformed-endpoint": "is unreadable or malformed",
    "remote-endpoint": "is not on this machine (loopback only)",
}


@pytest.mark.parametrize("kind", support.FAILURE_KINDS)
def test_a_failure_kind_has_a_scenario_with_its_one_cause_and_a_sentinel_to_discard(tmp_path, kind):
    scenario = support.failure_scenario(
        kind, {"PATH": "/usr/bin"}, home=tmp_path / "home", endpoint_file=tmp_path / "e", cap="9"
    )

    assert _CAUSE_WORDS[kind] in scenario.cause
    assert scenario.environment["INSTRUMENT_RUN_SETTINGS"] == support.SENTINEL_SETTINGS
    assert scenario.environment[support.CAP_NAME] == "9"
    assert (scenario.host_setting is not None) == (
        kind in ("empty-command", "environment-over-setting")
    )
    assert (support.COMMAND_VARIABLE in scenario.environment) == (
        kind != "no-command-and-no-setting"
    )


def test_every_failure_kind_is_one_the_scenarios_name():
    assert set(_CAUSE_WORDS) == set(support.FAILURE_KINDS)


def test_a_settings_document_handed_as_a_file_is_read_as_the_document(tmp_path):
    """A pinned launch hands its merged settings as a path, not inline."""
    document = {"env": {"OTEL_EXPORTER_OTLP_ENDPOINT": _ENDPOINT}, "hooks": {}}
    merged = tmp_path / "settings.json"
    merged.write_text(json.dumps(document))

    assert support._handed_settings(f"claude --settings {merged} -p go\n") == document
    assert support._handed_settings(f"claude --settings '{json.dumps(document)}'\n") == document
    assert support._handed_settings(f"claude --settings {tmp_path / 'absent.json'}\n") is None
