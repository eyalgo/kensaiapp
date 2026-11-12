"""The command way in: run a program and give a step its exit status and its output.

Python's standard library only."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    exit_status: int
    output: str


def run_program(argv: list[str]) -> CommandResult:
    """Run `argv` with no shell and give back its exit status and its output, standard error
    included."""
    completed = subprocess.run(
        argv, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, check=False
    )
    return CommandResult(exit_status=completed.returncode, output=completed.stdout)
