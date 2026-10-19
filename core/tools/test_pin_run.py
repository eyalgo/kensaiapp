"""Contract tests for `pin_run.sh` — the shared launcher entry (Task 4).

Drives a synthetic host with a stub launcher (`core/launchers/stub/launcher.sh`) that sources
`pin_run.sh` and calls `pin_enter`, recording what it saw (`CORE_DIR`, its own resolved path, cwd,
argv and the pin env vars) into `$STUB_RECORD`, and dumping a child's environment into
`$STUB_CHILD_ENV_FILE` when that variable is set. Isolation: every test builds its own throwaway
host and pins home under `tmp_path`; the environment passed to each subprocess is built from
scratch (`PATH` + `HOME` + whatever the test needs), never the ambient `os.environ`, so nothing
here reads or writes the real `~/.kensaiapp/pins/`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pin
import pin_host_changed

_PIN_RUN_SH = Path(__file__).parent / "pin_run.sh"
_PIN_PY = Path(__file__).parent / "pin.py"
_PIN_HOST_CHANGED_PY = Path(__file__).parent / "pin_host_changed.py"

_STUB_LAUNCHER = """#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
SCRIPT_PATH="${SCRIPT_DIR}/$(basename "${BASH_SOURCE[0]}")"
CORE_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd -P)"

source "${CORE_DIR}/tools/pin_run.sh"
pin_enter "${CORE_DIR}" "${SCRIPT_PATH}" "$@" || exit $?

{
    echo "core_dir=${CORE_DIR}"
    echo "script_ran_from=${SCRIPT_PATH}"
    echo "cwd=$(pwd -P)"
    echo "argv=$*"
    echo "kensaiapp_pin=${KENSAIAPP_PIN:-}"
    echo "git_config_count=${GIT_CONFIG_COUNT:-}"
    echo "git_config_key_0=${GIT_CONFIG_KEY_0:-}"
    echo "git_config_value_0=${GIT_CONFIG_VALUE_0:-}"
} >> "${STUB_RECORD}"

if [ -n "${STUB_CHILD_ENV_FILE:-}" ]; then
    env > "${STUB_CHILD_ENV_FILE}"
fi
"""

# The same stub, entering through `pin_enter_renewing` — the entry `build-idea` alone uses.
_RENEWING_STUB_LAUNCHER = _STUB_LAUNCHER.replace(
    'pin_enter "${CORE_DIR}"', 'pin_enter_renewing "${CORE_DIR}"'
)


def _init_pin_run_host(root: Path) -> Path:
    """A throwaway host at `root` with two stub launchers that source `pin_run.sh`: the plain one
    (`core/launchers/stub/launcher.sh`) calls `pin_enter` and is returned; the renewing one
    (`core/launchers/renewing/launcher.sh`) calls `pin_enter_renewing`."""
    tools_dir = root / "core" / "tools"
    tools_dir.mkdir(parents=True)
    shutil.copy2(_PIN_PY, tools_dir / "pin.py")
    shutil.copy2(_PIN_RUN_SH, tools_dir / "pin_run.sh")
    shutil.copy2(_PIN_HOST_CHANGED_PY, tools_dir / "pin_host_changed.py")

    renewing_dir = root / "core" / "launchers" / "renewing"
    renewing_dir.mkdir(parents=True)
    renewing = renewing_dir / "launcher.sh"
    renewing.write_text(_RENEWING_STUB_LAUNCHER)
    renewing.chmod(0o755)

    stub_dir = root / "core" / "launchers" / "stub"
    stub_dir.mkdir(parents=True)
    stub = stub_dir / "launcher.sh"
    stub.write_text(_STUB_LAUNCHER)
    stub.chmod(0o755)

    return stub


def _base_env(tmp_path: Path, pins_home_dir: Path, record: Path) -> dict:
    return {
        "PATH": os.environ["PATH"],
        "HOME": str(tmp_path),
        "KENSAIAPP_PINS_HOME": str(pins_home_dir),
        "STUB_RECORD": str(record),
    }


class TestPinEnter:
    def test_a_first_launch_makes_a_pin_and_reexecs_from_it(self, tmp_path):
        host = tmp_path / "host"
        stub = _init_pin_run_host(host)
        pins_home_dir = tmp_path / "pins"
        pins_home_dir.mkdir()
        record = tmp_path / "record.txt"

        result = subprocess.run(
            ["bash", str(stub), "one", "two"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env=_base_env(tmp_path, pins_home_dir, record),
        )

        assert result.returncode == 0, result.stderr
        # CP-103: the launcher prints one line, `Pin: <pin root> (new)` — one line for the
        # launch, not one per pass through `pin_enter` (the re-exec'd copy is the same launch).
        pin_lines = [l for l in result.stdout.splitlines() if l.startswith("Pin: ")]
        (made_root,) = [p for p in pins_home_dir.iterdir()]
        assert pin_lines == [f"Pin: {made_root.resolve()} (new)"]

        record_data = dict(
            line.split("=", 1) for line in record.read_text().strip().splitlines()
        )
        assert record_data["core_dir"] != str(host / "core")
        assert pins_home_dir.name in record_data["core_dir"]
        assert record_data["script_ran_from"].startswith(record_data["core_dir"])
        assert record_data["cwd"] == str(tmp_path.resolve())
        assert record_data["argv"] == "one two"

    def test_a_launch_inside_a_pin_makes_no_new_pin(self, tmp_path):
        """CP-165: a launcher entering through `pin_enter` — every launcher except `build-idea` —
        keeps the pin it is inside, whatever the host holds."""
        host = tmp_path / "host"
        _init_pin_run_host(host)
        pins_home_dir = tmp_path / "pins"
        pins_home_dir.mkdir()
        made = pin.make(host, pins_home_dir)
        pinned_stub = made.root / "core" / "launchers" / "stub" / "launcher.sh"
        record = tmp_path / "record.txt"

        result = subprocess.run(
            ["bash", str(pinned_stub), "one"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env=_base_env(tmp_path, pins_home_dir, record),
        )

        assert result.returncode == 0, result.stderr
        pin_lines = [l for l in result.stdout.splitlines() if l.startswith("Pin: ")]
        assert len(pin_lines) == 1
        assert pin_lines[0].endswith("(inherited)")
        assert sorted(p.name for p in pins_home_dir.iterdir()) == [made.id]

    def test_a_launcher_other_than_build_idea_inside_a_pin_on_a_changed_host_inherits(
        self, tmp_path
    ):
        """CP-165, CP-167 case 6: the stub enters through `pin_enter`, as every launcher but
        `build-idea` does. The host's `core/` was edited after the pin, and the launch still keeps
        the pin."""
        host = tmp_path / "host"
        _init_pin_run_host(host)
        pins_home_dir = tmp_path / "pins"
        pins_home_dir.mkdir()
        made = pin.make(host, pins_home_dir)
        (host / "core" / "tools" / "edited_after_the_pin.py").write_text("print('new')\n")
        assert pin_host_changed.compare(made) is pin_host_changed.Verdict.CHANGED
        pinned_stub = made.root / "core" / "launchers" / "stub" / "launcher.sh"
        record = tmp_path / "record.txt"

        result = subprocess.run(
            ["bash", str(pinned_stub), "one"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env=_base_env(tmp_path, pins_home_dir, record),
        )

        assert result.returncode == 0, result.stderr
        pin_lines = [l for l in result.stdout.splitlines() if l.startswith("Pin: ")]
        assert pin_lines == [f"Pin: {made.root.resolve()} (inherited)"]
        assert sorted(p.name for p in pins_home_dir.iterdir()) == [made.id]

    def test_a_launch_through_the_live_path_under_an_inherited_pin_uses_it(self, tmp_path):
        host = tmp_path / "host"
        stub = _init_pin_run_host(host)
        pins_home_dir = tmp_path / "pins"
        pins_home_dir.mkdir()
        made = pin.make(host, pins_home_dir)
        record = tmp_path / "record.txt"

        env = _base_env(tmp_path, pins_home_dir, record)
        env["KENSAIAPP_PIN"] = str(made.root)

        result = subprocess.run(
            ["bash", str(stub), "one"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0, result.stderr
        # CP-104: the launch prints `Pin: <pin root> (inherited)` — once, naming the pin it
        # inherited, however many passes through `pin_enter` the re-exec takes.
        pin_lines = [l for l in result.stdout.splitlines() if l.startswith("Pin: ")]
        assert [l.replace(str(made.root), str(made.root.resolve())) for l in pin_lines] == [
            f"Pin: {made.root.resolve()} (inherited)"
        ]
        assert sorted(p.name for p in pins_home_dir.iterdir()) == [made.id]

        record_data = dict(
            line.split("=", 1) for line in record.read_text().strip().splitlines()
        )
        assert record_data["core_dir"] == str(made.core)

    def test_an_inherited_pin_of_another_host_is_not_used(self, tmp_path):
        host = tmp_path / "host"
        stub = _init_pin_run_host(host)
        other_host = tmp_path / "elsewhere"
        _init_pin_run_host(other_host)
        pins_home_dir = tmp_path / "pins"
        pins_home_dir.mkdir()
        other_pin = pin.make(other_host, pins_home_dir)
        record = tmp_path / "record.txt"

        env = _base_env(tmp_path, pins_home_dir, record)
        env["KENSAIAPP_PIN"] = str(other_pin.root)

        result = subprocess.run(
            ["bash", str(stub), "one"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0, result.stderr
        pin_lines = [l for l in result.stdout.splitlines() if l.startswith("Pin: ")]
        assert any(l.endswith("(new)") for l in pin_lines)
        assert len(list(pins_home_dir.iterdir())) == 2

    def test_a_missing_inherited_pin_refuses(self, tmp_path):
        host = tmp_path / "host"
        stub = _init_pin_run_host(host)
        pins_home_dir = tmp_path / "pins"
        pins_home_dir.mkdir()
        record = tmp_path / "record.txt"
        missing = tmp_path / "nowhere"

        env = _base_env(tmp_path, pins_home_dir, record)
        env["KENSAIAPP_PIN"] = str(missing)

        result = subprocess.run(
            ["bash", str(stub), "one"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode != 0
        assert "nowhere" in result.stderr
        assert list(pins_home_dir.iterdir()) == []
        assert not record.exists()

    def test_a_dry_run_makes_no_pin(self, tmp_path):
        host = tmp_path / "host"
        stub = _init_pin_run_host(host)
        pins_home_dir = tmp_path / "pins"
        pins_home_dir.mkdir()
        record = tmp_path / "record.txt"

        result = subprocess.run(
            ["bash", str(stub), "--dry-run"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env=_base_env(tmp_path, pins_home_dir, record),
        )

        assert result.returncode == 0, result.stderr
        assert list(pins_home_dir.iterdir()) == []
        assert result.stdout.strip() == f"Pin: a new pin of {host.resolve()}"

    def test_a_dry_run_under_an_inherited_pin_names_it_and_makes_none(self, tmp_path):
        """CP-107: `--dry-run` makes no pin, and prints `Pin: <pin root> (inherited)` where a
        pin is already in force — one line, naming that pin."""
        host = tmp_path / "host"
        stub = _init_pin_run_host(host)
        pins_home_dir = tmp_path / "pins"
        pins_home_dir.mkdir()
        made = pin.make(host, pins_home_dir)
        record = tmp_path / "record.txt"

        env = _base_env(tmp_path, pins_home_dir, record)
        env["KENSAIAPP_PIN"] = str(made.root)

        result = subprocess.run(
            ["bash", str(stub), "--dry-run"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0, result.stderr
        pin_lines = [l for l in result.stdout.splitlines() if l.startswith("Pin: ")]
        assert [l.replace(str(made.root), str(made.root.resolve())) for l in pin_lines] == [
            f"Pin: {made.root.resolve()} (inherited)"
        ]
        assert sorted(p.name for p in pins_home_dir.iterdir()) == [made.id]

    def test_a_launcher_started_by_a_pinned_run_prints_its_own_inherited_line(self, tmp_path):
        """CP-104 at depth: a launcher the pinned run starts — from the pin's own copy, with the
        environment the first launch exported — makes no pin and prints its own
        `Pin: <pin root> (inherited)` line. Whatever the first launch does to print one line per
        launch must not silence the next launch down."""
        host = tmp_path / "host"
        stub = _init_pin_run_host(host)
        pins_home_dir = tmp_path / "pins"
        pins_home_dir.mkdir()
        record = tmp_path / "record.txt"
        child_env_file = tmp_path / "child_env.txt"

        env = _base_env(tmp_path, pins_home_dir, record)
        env["STUB_CHILD_ENV_FILE"] = str(child_env_file)
        first = subprocess.run(
            ["bash", str(stub), "outer"],
            cwd=str(tmp_path), capture_output=True, text=True, env=env,
        )
        assert first.returncode == 0, first.stderr
        (made_root,) = [p for p in pins_home_dir.iterdir()]

        child_env = dict(
            line.split("=", 1)
            for line in child_env_file.read_text().splitlines()
            if "=" in line
        )
        child_env.pop("STUB_CHILD_ENV_FILE", None)
        pinned_stub = made_root / "core" / "launchers" / "stub" / "launcher.sh"
        inner = subprocess.run(
            ["bash", str(pinned_stub), "inner"],
            cwd=str(tmp_path), capture_output=True, text=True, env=child_env,
        )

        assert inner.returncode == 0, inner.stderr
        pin_lines = [l for l in inner.stdout.splitlines() if l.startswith("Pin: ")]
        assert pin_lines == [f"Pin: {made_root.resolve()} (inherited)"]
        assert [p.name for p in pins_home_dir.iterdir()] == [made_root.name]

    def test_the_pins_env_reaches_what_the_launcher_starts(self, tmp_path):
        host = tmp_path / "host"
        stub = _init_pin_run_host(host)
        pins_home_dir = tmp_path / "pins"
        pins_home_dir.mkdir()
        record = tmp_path / "record.txt"
        child_env_file = tmp_path / "child_env.txt"

        env = _base_env(tmp_path, pins_home_dir, record)
        env["STUB_CHILD_ENV_FILE"] = str(child_env_file)

        result = subprocess.run(
            ["bash", str(stub), "one"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env=env,
        )

        assert result.returncode == 0, result.stderr
        child_env = dict(
            line.split("=", 1)
            for line in child_env_file.read_text().splitlines()
            if "=" in line
        )
        assert child_env["KENSAIAPP_PIN"]
        assert child_env["GIT_CONFIG_COUNT"] == "1"
        assert child_env["GIT_CONFIG_KEY_0"] == "core.hooksPath"
        assert child_env["GIT_CONFIG_VALUE_0"].endswith("/core/githooks")

    def test_the_library_runs_on_bash_3(self, tmp_path):
        host = tmp_path / "host"
        stub = _init_pin_run_host(host)
        pins_home_dir = tmp_path / "pins"
        pins_home_dir.mkdir()
        record = tmp_path / "record.txt"

        result = subprocess.run(
            ["/bin/bash", str(stub), "one"],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
            env=_base_env(tmp_path, pins_home_dir, record),
        )

        assert result.returncode == 0, result.stderr
        assert record.exists()


def _run_stub(stub: Path, tmp_path: Path, env: dict, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(stub), *args], cwd=str(tmp_path), capture_output=True, text=True, env=env
    )


def _pin_lines(result: subprocess.CompletedProcess) -> list[str]:
    return [line for line in result.stdout.splitlines() if line.startswith("Pin: ")]


def _recorded(record: Path) -> dict:
    return dict(line.split("=", 1) for line in record.read_text().strip().splitlines())


def _snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


class TestPinEnterRenewing:
    """`pin_enter_renewing` is `pin_enter` except where `pin_enter` would inherit: there it first
    asks `pin_host_changed.py` whether the pin's source host changed."""

    def _world(self, tmp_path: Path):
        host = tmp_path / "host"
        _init_pin_run_host(host)
        pins_home_dir = tmp_path / "pins"
        pins_home_dir.mkdir()
        made = pin.make(host, pins_home_dir)
        record = tmp_path / "record.txt"
        env = _base_env(tmp_path, pins_home_dir, record)
        return host, pins_home_dir, made, record, env

    def test_a_renewing_launch_inside_a_pin_on_a_changed_host_makes_one_new_pin_and_runs_from_it(
        self, tmp_path
    ):
        host, pins_home_dir, made, record, env = self._world(tmp_path)
        (host / "core" / "tools" / "edited_after_the_pin.py").write_text("print('new')\n")
        before = _snapshot(made.root)
        pinned_stub = made.root / "core" / "launchers" / "renewing" / "launcher.sh"

        result = _run_stub(pinned_stub, tmp_path, env, "one")

        assert result.returncode == 0, result.stderr
        (new_root,) = [p for p in pins_home_dir.iterdir() if p.name != made.id]
        assert _pin_lines(result) == [f"Pin: {new_root.resolve()} (new)"]
        recorded = _recorded(record)
        assert Path(recorded["core_dir"]).resolve() == (new_root / "core").resolve()
        assert Path(recorded["kensaiapp_pin"]).resolve() == new_root.resolve()
        assert sorted(p.name for p in pins_home_dir.iterdir()) == sorted([made.id, new_root.name])
        assert _snapshot(made.root) == before

    def test_a_renewing_launch_inside_a_pin_on_an_unchanged_host_inherits(self, tmp_path):
        _, pins_home_dir, made, record, env = self._world(tmp_path)
        pinned_stub = made.root / "core" / "launchers" / "renewing" / "launcher.sh"

        result = _run_stub(pinned_stub, tmp_path, env, "one")

        assert result.returncode == 0, result.stderr
        assert _pin_lines(result) == [f"Pin: {made.root.resolve()} (inherited)"]
        assert sorted(p.name for p in pins_home_dir.iterdir()) == [made.id]
        assert Path(_recorded(record)["core_dir"]).resolve() == made.core.resolve()

    def test_a_renewing_launch_under_an_inherited_pin_on_a_changed_host_makes_a_new_pin_of_that_host(
        self, tmp_path
    ):
        host, pins_home_dir, made, record, env = self._world(tmp_path)
        (host / "core" / "tools" / "edited_after_the_pin.py").write_text("print('new')\n")
        env["KENSAIAPP_PIN"] = str(made.root)
        host_stub = host / "core" / "launchers" / "renewing" / "launcher.sh"

        result = _run_stub(host_stub, tmp_path, env, "one")

        assert result.returncode == 0, result.stderr
        (new_root,) = [p for p in pins_home_dir.iterdir() if p.name != made.id]
        assert _pin_lines(result) == [f"Pin: {new_root.resolve()} (new)"]
        manifest = json.loads((new_root / "pin.json").read_text())
        assert manifest["source_host_root"] == str(host.resolve())
        assert Path(_recorded(record)["core_dir"]).resolve() == (new_root / "core").resolve()

    def test_a_renewing_dry_run_on_a_changed_host_names_a_new_pin_and_makes_none(self, tmp_path):
        host, pins_home_dir, made, record, env = self._world(tmp_path)
        (host / "core" / "tools" / "edited_after_the_pin.py").write_text("print('new')\n")
        pinned_stub = made.root / "core" / "launchers" / "renewing" / "launcher.sh"

        result = _run_stub(pinned_stub, tmp_path, env, "--dry-run")

        assert result.returncode == 0, result.stderr
        assert result.stdout.strip() == f"Pin: a new pin of {host.resolve()}"
        assert sorted(p.name for p in pins_home_dir.iterdir()) == [made.id]

    def test_a_renewing_launch_whose_pin_host_is_gone_inherits_and_says_so_on_stderr(
        self, tmp_path
    ):
        host, pins_home_dir, made, record, env = self._world(tmp_path)
        shutil.rmtree(host)
        pinned_stub = made.root / "core" / "launchers" / "renewing" / "launcher.sh"

        result = _run_stub(pinned_stub, tmp_path, env, "one")

        assert result.returncode == 0, result.stderr
        assert _pin_lines(result) == [f"Pin: {made.root.resolve()} (inherited)"]
        (stderr_line,) = [line for line in result.stderr.splitlines() if line.strip()]
        assert str(host.resolve()) in stderr_line
        assert sorted(p.name for p in pins_home_dir.iterdir()) == [made.id]
        assert record.exists()  # the launcher body still ran

    def test_the_re_exec_continuation_does_not_compare_again(self, tmp_path):
        """One launch makes at most one pin. The host's comparator is replaced by one that answers
        `changed` whatever it is asked, so a comparison run on the continuation — the new pin's
        copy of the same launch — would make a second pin and print a second `Pin:` line."""
        host, pins_home_dir, made, record, env = self._world(tmp_path)
        (host / "core" / "tools" / "pin_host_changed.py").write_text(
            f"print('verdict=changed')\nprint('host={host.resolve()}')\n"
        )
        env["KENSAIAPP_PIN"] = str(made.root)
        host_stub = host / "core" / "launchers" / "renewing" / "launcher.sh"

        result = _run_stub(host_stub, tmp_path, env, "one")

        assert result.returncode == 0, result.stderr
        (new_root,) = [p for p in pins_home_dir.iterdir() if p.name != made.id]
        assert _pin_lines(result) == [f"Pin: {new_root.resolve()} (new)"]
        assert Path(_recorded(record)["core_dir"]).resolve() == (new_root / "core").resolve()

    def test_a_renewing_launch_stops_when_the_comparison_fails(self, tmp_path):
        _, pins_home_dir, made, record, env = self._world(tmp_path)
        (made.root / "core" / "tools" / "pin_host_changed.py").write_text(
            "import sys\nprint('the comparison could not read the host', file=sys.stderr)\n"
            "sys.exit(2)\n"
        )
        pinned_stub = made.root / "core" / "launchers" / "renewing" / "launcher.sh"

        result = _run_stub(pinned_stub, tmp_path, env, "one")

        assert result.returncode == 2  # the comparator's own status, passed on
        assert "the comparison could not read the host" in result.stderr
        assert not record.exists()  # the launcher body never ran
        assert sorted(p.name for p in pins_home_dir.iterdir()) == [made.id]
