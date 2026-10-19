#!/usr/bin/env python3
"""detached_sequence.py — one detached process that runs a plan's commands one after another.

WHY THIS EXISTS

A launcher that sends each seat its own run needs the runs to go one at a time: they edit one file,
so two at once would overwrite each other's answers. But a launcher returns at once, so something
else has to wait for run 1 to end before it starts run 2. That something is this process, started
once, detached, with the whole plan.

The plan is a file holding one JSON array of strings per line, each array one complete command —
`agent_run.py --background --log <log>`, which returns once its run is detached and prints one JSON
record naming the run's pid. This runner starts a command, reads that pid, waits until the process
is gone, and only then starts the next. However a run ended — an error, a refusal, no record — the
next command still starts: each run's work is disjoint from the others', so one seat's failure says
nothing about the next seat's items.

A run leads its own session, so a stop aimed at this runner's group never reaches it. The runner's
own SIGINT and SIGTERM handler is what carries a stop on: it stops the current run and starts no
successor.

THE COMPLETION LOG. A watcher waiting for "the last run ended" cannot be pointed at that run's own
log: it reads the log's terminal event as the end, which for runs 1 to N-1 would be the wrong
moment, and for run N would arrive while its process is still winding down. With `--completion-log`
the runner holds the last run's transcript back and writes it to that second file only once the
run's process is dead. A watcher on this runner's pid and that file therefore sees a terminal event
only after the last process has ended. A last run that left no log publishes nothing, so the watcher
reports the missing ending when this runner exits rather than a success that did not happen. A stop
publishes nothing either: a stopped sequence did not complete.

Everything the runner reaches the world through — starting a command, process liveness, sleeping,
files, signals, its output — is handed to `Sequence`; `main` is the only place real ones are built.
"""

from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import walk_stop

__version__ = "1.0.0"

POLL_SECONDS = 2.0
STOPPED_STATUS = 1
_LOG_FLAG = "--log"


class PlanError(ValueError):
    """The plan file cannot be run; the entry point converts it to a message and a non-zero exit."""


class Processes:
    """The process port: start a command to completion, read liveness, stop a run, sleep."""

    def start(self, argv: list[str]) -> tuple[int, str, str]:
        result = subprocess.run(argv, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        return result.returncode, result.stdout, result.stderr

    def alive(self, pid: int) -> bool:
        return walk_stop.process_alive(pid)

    def stop(self, pid: int) -> None:
        walk_stop.stop_lingering(pid, grace_seconds=0.0)

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


class Files:
    """The file port: the three operations the completion log needs."""

    def exists(self, path: str) -> bool:
        return Path(path).exists()

    def read_bytes(self, path: str) -> bytes:
        return Path(path).read_bytes()

    def write_bytes(self, path: str, data: bytes) -> None:
        # Written beside the target and moved into place, so a watcher never reads half a log.
        target = Path(path)
        scratch = target.with_name(target.name + ".tmp")
        scratch.write_bytes(data)
        scratch.replace(target)


class Signals:
    """The signal port: route SIGINT and SIGTERM to one handler taking the signal number."""

    def install(self, handler: Callable[[int], None]) -> None:
        for signum in (signal.SIGINT, signal.SIGTERM):
            signal.signal(signum, lambda received, _frame: handler(received))


def provider_log(argv: list[str]) -> str | None:
    """The `--log` path a command hands the provider run, in either spelling; `None` if absent."""
    for index, argument in enumerate(argv):
        if argument == _LOG_FLAG and index + 1 < len(argv):
            return argv[index + 1]
        if argument.startswith(_LOG_FLAG + "="):
            return argument[len(_LOG_FLAG) + 1:]
    return None


def _run_pid(output: str) -> int | None:
    try:
        record = json.loads(output)
    except json.JSONDecodeError:
        return None
    pid = record.get("pid") if isinstance(record, dict) else None
    return pid if isinstance(pid, int) and not isinstance(pid, bool) and pid > 0 else None


class Sequence:
    """Runs commands one at a time; everything it uses is handed in and it constructs nothing."""

    def __init__(
        self,
        *,
        processes: Processes,
        files: Files,
        signals: Signals,
        emit: Callable[[str], None],
    ) -> None:
        self._processes = processes
        self._files = files
        self._signals = signals
        self._emit = emit
        self._stop_requested = False

    def run(self, commands: list[list[str]], completion_log: str | None = None) -> int:
        """Run every command in order; 0 when all were started and ended, 1 when stopped."""
        self._signals.install(self._on_signal)
        for index, argv in enumerate(commands, start=1):
            if self._stop_requested:
                break
            pid = self._launch(index, len(commands), argv)
            if pid is not None:
                self._wait_until_ended(pid)
        if self._stop_requested:
            self._emit("detached_sequence: stopped — no further command was started")
            return STOPPED_STATUS
        if completion_log is not None:
            self._publish(completion_log, provider_log(commands[-1]))
        return 0

    def _on_signal(self, _signum: int) -> None:
        self._stop_requested = True

    def _launch(self, index: int, total: int, argv: list[str]) -> int | None:
        try:
            returncode, output, errors = self._processes.start(argv)
        except OSError as exc:
            self._emit(f"detached_sequence: command {index} of {total} could not start: {exc}")
            return None
        if returncode != 0:
            self._emit(
                f"detached_sequence: command {index} of {total} was refused (exit {returncode}): "
                f"{errors.strip() or 'no reason given'}"
            )
            return None
        pid = _run_pid(output)
        if pid is None:
            self._emit(f"detached_sequence: command {index} of {total} printed no run record")
            return None
        self._emit(f"detached_sequence: command {index} of {total} started run process {pid}")
        return pid

    def _wait_until_ended(self, pid: int) -> None:
        while self._processes.alive(pid):
            if self._stop_requested:
                self._processes.stop(pid)
                return
            self._processes.sleep(POLL_SECONDS)

    def _publish(self, completion_log: str, final_log: str | None) -> None:
        if final_log is None or not self._files.exists(final_log):
            self._emit(f"detached_sequence: no provider log at {final_log} — nothing published")
            return
        self._files.write_bytes(completion_log, self._files.read_bytes(final_log))


def load_plan(text: str) -> list[list[str]]:
    """The plan's commands, one per nonblank line; raises `PlanError` naming what is wrong."""
    commands: list[list[str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            argv = json.loads(line)
        except json.JSONDecodeError as exc:
            raise PlanError(f"plan line {number} is not JSON: {exc.msg}") from None
        if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
            raise PlanError(f"plan line {number} must be a nonempty JSON array of strings")
        commands.append(argv)
    if not commands:
        raise PlanError("the plan holds no command")
    return commands


def _detach(plan: str, log: str, completion_log: str | None) -> int:
    """Restart this file in its own session, its output to `log`, and print where it is."""
    child = [sys.executable, str(Path(__file__).resolve()), "--plan", plan, "--log", log]
    if completion_log is not None:
        child += ["--completion-log", completion_log]
    child.append("--foreground")
    try:
        with open(log, "ab") as output:
            process = subprocess.Popen(
                child, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT,
                start_new_session=True,
            )
    except OSError as exc:
        print(f"detached_sequence: cannot start the sequence: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"pid": process.pid, "session_id": None}))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a plan's commands one after another.")
    parser.add_argument("--plan", required=True, help="file of one JSON argv array per line")
    parser.add_argument("--log", required=True, help="the sequence's own output")
    parser.add_argument("--completion-log", help="receives the last run's log once it has ended")
    parser.add_argument("--foreground", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    try:
        commands = load_plan(Path(args.plan).read_text())
    except OSError as exc:
        message = f"detached_sequence: cannot read the plan {args.plan}: {exc.strerror}"
        print(message, file=sys.stderr)
        return 1
    except PlanError as exc:
        print(f"detached_sequence: {exc} ({args.plan})", file=sys.stderr)
        return 1
    if args.completion_log is not None and provider_log(commands[-1]) is None:
        print(
            f"detached_sequence: --completion-log needs the last command to carry {_LOG_FLAG} "
            f"<provider log>, and {commands[-1][0]} does not",
            file=sys.stderr,
        )
        return 1

    if not args.foreground:
        return _detach(args.plan, args.log, args.completion_log)
    sequence = Sequence(
        processes=Processes(),
        files=Files(),
        signals=Signals(),
        emit=lambda line: print(line, flush=True),
    )
    return sequence.run(commands, completion_log=args.completion_log)


if __name__ == "__main__":
    sys.exit(main())
