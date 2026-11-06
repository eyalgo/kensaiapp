"""A `python3` that only fails, for the tests that prove a launcher starts no `python3`."""

from __future__ import annotations

import os
from pathlib import Path


def python3_that_only_fails(directory: Path, path: str | None = None) -> tuple[str, Path]:
    """Put an executable `python3` first on `path` (the running PATH when none is given): it
    appends a line to a marker file and exits 1.

    Returns that PATH and the marker's path. A launcher that still calls `python3` writes the
    marker and fails; one that runs its Python through the runner never reaches the stub, except
    that uv itself probes `python3` on PATH during host-environment discovery.
    New pins are prepared separately using their source host's interpreter. The marker therefore
    holds the command name of the stub's parent, and `python3_calls_outside_uv` reads out of it the
    calls uv did not make.
    """
    stub_dir = directory / "python3-stub-bin"
    stub_dir.mkdir()
    marker = directory / "python3-marker"
    stub = stub_dir / "python3"
    stub.write_text(f'#!/bin/sh\nps -o comm= -p $PPID >> "{marker}"\nexit 1\n')
    stub.chmod(0o755)
    return f"{stub_dir}{os.pathsep}{os.environ['PATH'] if path is None else path}", marker


def python3_calls_outside_uv(marker: Path) -> list[str]:
    """The parents that called the stub `python3` and were not uv: empty when no launcher line
    did."""
    if not marker.exists():
        return []
    return [line for line in marker.read_text().splitlines()
            if os.path.basename(line.strip()) != "uv"]
