#!/usr/bin/env python3
"""walk_stop.py — the one owner of a launch's process identity and of stopping it.

WHY THIS EXISTS

A walk that waits on a launch had one way out: delete its state file and lock by hand, and the run
and its watcher kept going. Three engines (`chain.py`, `chain_development.py`, `build_idea.py`) each
needed the same stop, and a hand-written copy in each was the shape the owner ruled out.

So the contract, stated here once. A launch names an identity file beside its shim through
`DETACHED_RUN_IDENTITY_FILE`; the run launcher records the run's and the watcher's pid in it, each
with the process's start time (`record`, below). A stop reads the file back and signals a process
only while its pid still has the recorded start time, so a pid the system has recycled is never
signalled.

This module imports only the standard library and no engine, so every engine and `watch_process.py`
import it without a cycle. `process_alive` and `stop_lingering` live here for the same reason: the
engines reach the process-group stop without importing the watcher stack.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import shlex
import signal
import subprocess
import sys
import time
from enum import Enum
from pathlib import Path

__version__ = "1.0.0"

IDENTITY_VARIABLE = "DETACHED_RUN_IDENTITY_FILE"
STOPPED = "stopped"

# What a launch's own process records about itself. A launch must never inherit these from the
# process that started it: they would name the parent's run, not this one.
_INHERITED_RUN_VARIABLES = (
    "DETACHED_RUN_PID", "DETACHED_RUN_SESSION_ID",
    "DETACH_PROCESS_WATCHER_PID", "DETACH_PROCESS_WATCHER_START",
)

_NOTHING_WAS_WAITING = "no launch was waiting"


class DiskFiles:
    """The two disk operations the identity file needs; the real `files` port of this module."""

    def read_text(self, path: str) -> str:
        return Path(path).read_text()

    def write_text(self, path: str, text: str) -> None:
        # Written beside the target and moved into place, so a reader never sees half a file.
        target = Path(path)
        scratch = target.with_name(target.name + ".tmp")
        scratch.write_text(text)
        scratch.replace(target)


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _child_has_exited(pid: int) -> bool:
    """True when this process is the parent and `pid` has exited, zombie included.

    `os.kill(pid, 0)` succeeds on a zombie, so a parent that has not reaped yet would
    otherwise wait out the whole interval and then signal a process that already ended.
    `WNOWAIT` looks without reaping, leaving the caller's own `wait` the status.
    A watcher that is not the parent gets `ChildProcessError` and learns nothing here.
    """
    try:
        return os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT) is not None
    except ChildProcessError:
        return False


def _wait_for_exit(pid: int, seconds: float) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if not process_alive(pid) or _child_has_exited(pid):
            return True
        time.sleep(0.05)
    return not process_alive(pid) or _child_has_exited(pid)


def stop_lingering(pid: int, grace_seconds: float = 30.0, interrupt_seconds: float = 30.0) -> None:
    """Stop a run's process group that outlives its ending: give it `grace_seconds` to exit on its
    own, then SIGINT, then SIGTERM. The pid leads its own session (`start_new_session=True`), so
    the group reaches the provider process under the exit-record wrapper."""
    for signum, wait in ((None, grace_seconds), (signal.SIGINT, interrupt_seconds),
                         (signal.SIGTERM, 0.0)):
        if signum is not None:
            try:
                os.killpg(pid, signum)
            except (ProcessLookupError, PermissionError):
                return
        if _wait_for_exit(pid, wait):
            return


def _collapse(start: str) -> str:
    return " ".join(start.split())


class ProcessTable:
    """The port a stop reaches processes through. A fake satisfies it by having these methods."""

    def start_time(self, pid: int) -> str | None:
        """`ps -o lstart=` for `pid`, whitespace collapsed; `None` when there is no such process.
        `detach_process_watcher.sh` takes the same reading, so writer and checker agree."""
        try:
            result = subprocess.run(
                ["ps", "-o", "lstart=", "-p", str(pid)], capture_output=True, text=True)
        except OSError:
            return None
        text = _collapse(result.stdout)
        return text if result.returncode == 0 and text else None

    def stop_group(self, pid: int) -> None:
        stop_lingering(pid, grace_seconds=0.0)


@dataclasses.dataclass(frozen=True)
class ProcessIdentity:
    pid: int
    start: str | None


@dataclasses.dataclass(frozen=True)
class LaunchIdentity:
    run: ProcessIdentity | None
    watcher: ProcessIdentity | None


def identity_path(shim_path: str) -> str:
    """The identity file of the launch whose shim is at `shim_path`, beside it."""
    return str(Path(shim_path).with_suffix(".identity.json"))


def _launch_environment(env: dict) -> dict:
    return {name: value for name, value in env.items()
            if name != IDENTITY_VARIABLE and name not in _INHERITED_RUN_VARIABLES}


def without_launch_identity(env: dict) -> dict:
    """A copy of `env` for a launch that records no identity."""
    return _launch_environment(env)


def prepare_launch(files: DiskFiles, shim_path: str, env: dict) -> tuple[dict, str]:
    """Empty the identity file beside `shim_path` and return a copy of `env` that names it,
    with the path. An empty file is how a launch the run launcher never recorded reads."""
    path = identity_path(shim_path)
    files.write_text(path, "")
    return {**_launch_environment(env), IDENTITY_VARIABLE: path}, path


def _part(table: ProcessTable, pid: int | None) -> dict | None:
    if pid is None:
        return None
    return {"pid": pid, "start": table.start_time(pid)}


def identity_text(table: ProcessTable, run_pid: int | None, watcher_pid: int | None) -> str:
    """The identity file's JSON. A pid with no process is recorded with a null start."""
    return json.dumps({"run": _part(table, run_pid), "watcher": _part(table, watcher_pid)})


def _identity_part(value: object) -> ProcessIdentity | None:
    if value is None:
        return None
    if not isinstance(value, dict) or type(value.get("pid")) is not int or "start" not in value:
        raise ValueError("malformed process identity")
    start = value["start"]
    if start is not None and not isinstance(start, str):
        raise ValueError("malformed process start time")
    return ProcessIdentity(value["pid"], start)


def read_identity(files: DiskFiles, path: str) -> LaunchIdentity | None:
    """The recorded identity, or `None` for an empty path and a missing, empty or malformed file."""
    if not path:
        return None
    try:
        text = files.read_text(path)
        data = json.loads(text) if text else None
        if not isinstance(data, dict) or "run" not in data or "watcher" not in data:
            return None
        return LaunchIdentity(run=_identity_part(data["run"]),
                              watcher=_identity_part(data["watcher"]))
    except (OSError, ValueError):
        return None


def _matches(table: ProcessTable, process: ProcessIdentity | None) -> bool:
    """A pid is the recorded process only while its current start time equals the recorded one."""
    if process is None or process.start is None:
        return False
    current = table.start_time(process.pid)
    return current is not None and _collapse(current) == _collapse(process.start)


class LaunchState(str, Enum):
    LIVE = "live"
    GONE = "gone"
    UNRECORDED = "unrecorded"


def launch_state(files: DiskFiles, table: ProcessTable, path: str) -> LaunchState:
    identity = read_identity(files, path)
    if identity is None:
        return LaunchState.UNRECORDED
    if _matches(table, identity.run) or _matches(table, identity.watcher):
        return LaunchState.LIVE
    return LaunchState.GONE


class Outcome(str, Enum):
    STOPPED = "stopped"
    GONE = "already gone"
    UNRECORDED = "no recorded identity"


@dataclasses.dataclass(frozen=True)
class LaunchStop:
    """What a stop did to one launch. The pids are the ones read from the identity file, so the
    text names them; they are `None` for a launch with no identity."""

    label: str
    run: Outcome
    watcher: Outcome
    run_pid: int | None = None
    watcher_pid: int | None = None

    def describe(self) -> str:
        def process(name: str, pid: int | None, outcome: Outcome) -> str:
            return f"{name} {outcome.value}" if pid is None else f"{name} {pid} {outcome.value}"

        return (f"{self.label}: {process('run', self.run_pid, self.run)}, "
                f"{process('watcher', self.watcher_pid, self.watcher)}")


def _stop_process(table: ProcessTable, process: ProcessIdentity | None) -> Outcome:
    if not _matches(table, process):
        return Outcome.GONE
    table.stop_group(process.pid)
    return Outcome.STOPPED


def stop_launch(files: DiskFiles, table: ProcessTable, path: str, label: str) -> LaunchStop:
    """Stop one launch: its watcher first, so it cannot fire the completion hook for the run being
    stopped, then its run. A process is signalled only while its pid still has the recorded
    start."""
    identity = read_identity(files, path)
    if identity is None:
        return LaunchStop(label, Outcome.UNRECORDED, Outcome.UNRECORDED)
    watcher = _stop_process(table, identity.watcher)
    run = _stop_process(table, identity.run)
    return LaunchStop(
        label, run, watcher,
        run_pid=None if identity.run is None else identity.run.pid,
        watcher_pid=None if identity.watcher is None else identity.watcher.pid)


def stop_reason(stopped_at: str, stops: list[LaunchStop]) -> str:
    """The `ended_reason` a stop writes: when it was made and what became of each launch."""
    what = "; ".join(stop.describe() for stop in stops) or _NOTHING_WAS_WAITING
    return f"stopped at {stopped_at}: {what}"


def stop_command(core_dir: str, launcher: str, project: str) -> str:
    script = shlex.quote(f"{core_dir}/launchers/{launcher}/launcher.sh")
    return f"{script} {shlex.quote(project)} --stop"


def refusal_remedy(states: list[LaunchState], command: str) -> str:
    """What a refusal over a live walk offers. Every launch recorded and none live means nothing
    will finish the walk; otherwise it may still finish on its own."""
    if states and all(state == LaunchState.GONE for state in states):
        return f"Nothing will finish it: its runs are gone. Stop it with: {command}"
    return f"Let it finish, or stop it with: {command}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Record a launch's run and watcher identity.")
    commands = parser.add_subparsers(dest="command", required=True)
    record = commands.add_parser("record", help="write the identity file")
    record.add_argument("file")
    record.add_argument("--run-pid", type=int)
    record.add_argument("--watcher-pid", type=int)
    args = parser.parse_args(argv)
    try:
        DiskFiles().write_text(
            args.file, identity_text(ProcessTable(), args.run_pid, args.watcher_pid))
    except OSError as exc:
        print(f"walk_stop: cannot record {args.file}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
