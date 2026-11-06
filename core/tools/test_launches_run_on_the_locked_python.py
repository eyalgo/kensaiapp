"""Standing guard: a launch runs its Python through `locked_python.sh`, never `python3`.

Three greps over the files git tracks in the repository that holds this module, and one check of the
completion shim's text. Each fails naming every line it finds, so a reader sees what to move to the
runner. A line that is a comment is not a call and is not counted. Then every launcher on disk, run
with uv absent from `PATH`, stops with the launch's message and starts nothing.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import completion_shim
from test_locked_python import LAUNCH_MISSING_UV_MESSAGE

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMENT_LINE = re.compile(r":[0-9]+:\s*#")

LAUNCHER_PATHSPECS = ("core/launchers/*/launcher.sh", "core/tools/launch-*.sh")
HELPER_PATHSPECS = (
    "core/tools/*.sh",
    ":!core/tools/launch-*.sh",
    ":!core/tools/locked_python.sh",
)
PYTHON_PATHSPECS = (
    "core/tools/*.py",
    ":!core/tools/test_*",
)


def _grep(*options: str, pathspecs: tuple[str, ...]) -> list[str]:
    """The lines `git grep` finds in tracked files, comment lines left out."""
    result = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "grep", "-n", *options, "--", *pathspecs],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode in (0, 1), result.stderr
    return [line for line in result.stdout.splitlines() if not COMMENT_LINE.search(line)]


def test_no_launcher_line_names_python3() -> None:
    assert _grep("-w", "python3", pathspecs=LAUNCHER_PATHSPECS) == []


def test_no_sourced_helper_line_names_python3() -> None:
    assert _grep("-w", "python3", pathspecs=HELPER_PATHSPECS) == []


def test_no_kensaiapp_python_spawns_python3() -> None:
    hits = _grep("-F", '"python3"', pathspecs=PYTHON_PATHSPECS)
    assert hits == [], "\n".join(hits)


def test_the_completion_shim_template_names_no_python3() -> None:
    text = completion_shim.shim_text("/engine/engine.py", ("advance", "--once"), "/tmp/shim.log")
    assert "python3" not in text


# CP-888 over every launcher on disk, enumerated rather than listed, so a sixteenth launcher is
# held the day it lands. A launch without uv stops at `pin_enter`'s check, before its arguments are
# read, so no arguments are given: the message, the exit and the absence of a pin and of any Python
# are the same whatever the launch would have been.
_LAUNCHERS = sorted(
    [*REPO_ROOT.glob("core/launchers/*/launcher.sh"), *REPO_ROOT.glob("core/tools/launch-*.sh")])


def _launcher_name(launcher: Path) -> str:
    """The name `change_text.md` puts in the message: the folder of a `launcher.sh`, the file's name
    without `.sh` for a flat `launch-*.sh`."""
    return launcher.parent.name if launcher.name == "launcher.sh" else launcher.stem


def test_every_launcher_on_disk_is_enumerated() -> None:
    assert len(_LAUNCHERS) >= 15


@pytest.mark.parametrize("launcher", _LAUNCHERS, ids=_launcher_name)
def test_without_uv_a_launcher_prints_the_launch_message_and_starts_nothing(
        launcher: Path, tmp_path: Path) -> None:
    if shutil.which("uv", path="/usr/bin:/bin"):
        pytest.skip("uv is installed in /usr/bin or /bin, so it cannot be hidden from PATH")
    stub_dir = tmp_path / "python3-stub-bin"
    stub_dir.mkdir()
    marker = tmp_path / "python3-ran"
    stub = stub_dir / "python3"
    stub.write_text(f'#!/bin/sh\necho ran >> "{marker}"\nexit 1\n')
    stub.chmod(0o755)
    home = tmp_path / "home"
    home.mkdir()
    pins_home = tmp_path / "pins"
    pins_home.mkdir()
    env = {
        "HOME": str(home),
        "PATH": f"{stub_dir}{os.pathsep}/usr/bin{os.pathsep}/bin",
        "KENSAIAPP_PINS_HOME": str(pins_home),
    }

    result = subprocess.run(
        [str(launcher)], cwd=str(tmp_path), env=env, capture_output=True, text=True, check=False)

    assert result.returncode == 1
    assert result.stdout == ""
    assert result.stderr == LAUNCH_MISSING_UV_MESSAGE.format(launcher=_launcher_name(launcher))
    assert list(pins_home.iterdir()) == []
    assert not marker.exists()


def test_python_guard_uses_only_the_station_pathspecs():
    assert PYTHON_PATHSPECS == ("core/tools/*.py", ":!core/tools/test_*")


def _run_guard_in_tracked_repository(tmp_path: Path, filename: str):
    """Run the unchanged guard bytes with their own repository-root discovery."""
    tools = tmp_path / "core" / "tools"
    tools.mkdir(parents=True)
    guard = tools / Path(__file__).name
    guard.write_bytes(Path(__file__).read_bytes())
    (tools / filename).write_text('subprocess.run(["python3"])\n')
    for args in (["init", "-q"], ["add", "core/tools"]):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)
    code = (
        "import runpy, sys; "
        "sys.path.insert(0, sys.argv[2]); "
        "guard = runpy.run_path(sys.argv[1]); "
        "guard['test_no_kensaiapp_python_spawns_python3']()"
    )
    return subprocess.run(
        [sys.executable, "-c", code, str(guard), str(REPO_ROOT / "core" / "tools")],
        capture_output=True, text=True, check=False,
    )


def test_python_guard_reports_a_tracked_production_spawn(tmp_path):
    result = _run_guard_in_tracked_repository(tmp_path, "production_spawn.py")
    assert result.returncode != 0
    assert 'core/tools/production_spawn.py:1:subprocess.run(["python3"])' in result.stderr


def test_python_guard_excludes_test_support_by_prefix(tmp_path):
    result = _run_guard_in_tracked_repository(tmp_path, "test_support_spawn.py")
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
