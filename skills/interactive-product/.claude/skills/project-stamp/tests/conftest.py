"""Test support for stamp_project.py — the project-stamp scaffolder.

The tests exercise the script's **documented CLI contract** (project-stamp
SKILL.md + kensaiapp_structure.md §2), never its implementation. Each test runs
the real script as a subprocess so exit codes (2 for a guard, 3 for overwrite)
and stdout are observed exactly as a caller would see them.

Isolation: the script is mirrored into a fresh temp instance root under
`tmp_path` and invoked with `cwd=tmp_path`, so both CWD-relative writes
(`system/projects/...`, `.claude/settings.local.json`) and any
`__file__`-relative resolution land inside the temp tree — never the real repo.
`--core` points at the instance's real `core/` (read-only template reads).
"""

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_INSTANCE_ROOT = Path(__file__).resolve().parents[6]
_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "stamp_project.py"
_CORE = _INSTANCE_ROOT / "core"


@pytest.fixture
def run(tmp_path):
    """Return a callable `run(*cli_args) -> CompletedProcess`.

    Runs the mirrored scaffolder inside `tmp_path` (the fake instance root) with
    `--core` appended. `run.root` is the temp instance root for assertions.
    """
    script_dst = (
        tmp_path / ".claude" / "skills" / "project-stamp" / "scripts"
        / "stamp_project.py"
    )
    script_dst.parent.mkdir(parents=True)
    shutil.copy2(_SCRIPT, script_dst)

    def _run(*cli_args):
        return subprocess.run(
            [sys.executable, str(script_dst), *cli_args, "--core", str(_CORE)],
            cwd=str(tmp_path),
            capture_output=True,
            text=True,
        )

    _run.root = tmp_path
    _run.core = _CORE
    return _run
