"""PATH helpers shared by launcher subprocess tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def path_without_caffeinate(env, sandbox):
    """A PATH holding everything the real one does EXCEPT `caffeinate` — one directory of symlinks,
    built from the PATH `env` already carries, with that single name left out.

    Shadowing cannot stand in for this: `command -v` walks past a non-executable file and finds the
    real `/usr/bin/caffeinate` further down, so on a Mac the only honest way to reach the
    not-macOS branch is a PATH that genuinely lacks the binary. Everything else stays reachable, so
    a run under this PATH fails only for the reason the test is about.

    A version-manager `shims/` directory is skipped and `python3` is pointed straight at the running
    interpreter instead. A pyenv shim re-execs `pyenv exec python3`, which resolves `python3` off
    PATH again — it strips its OWN shims directory to break that cycle, and cannot know about this
    one, so a symlinked shim here spins forever at 100% CPU and outlives the test.
    """
    sandbox.mkdir(parents=True, exist_ok=True)
    for directory in env["PATH"].split(os.pathsep):
        source = Path(directory)
        if not source.is_dir() or source.name == "shims":
            continue
        for entry in source.iterdir():
            if entry.name == "caffeinate":
                continue
            try:
                (sandbox / entry.name).symlink_to(entry)
            except (FileExistsError, OSError):
                pass          # first PATH entry wins, exactly as a real PATH lookup does
    for name in ("python3", "python"):
        link = sandbox / name
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(sys.executable)
    return str(sandbox)
