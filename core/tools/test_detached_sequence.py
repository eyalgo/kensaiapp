"""Tests for detached_sequence.py — one detached process that runs a plan's commands one at a time.

Two kinds of case. The sequencing ones hand the runner fakes for everything it reaches the world
through (processes, files, signals), each recording what it was asked in one shared event list, so
"run 2 starts only after run 1's process ended" is read off the order of that list rather than
off a clock. The CLI ones run the real file as a subprocess, and one starts a real `sleep` in its
own session the way every provider run starts, to prove a stop reaches it.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

import detached_sequence

TOOLS = Path(__file__).resolve().parent
COMPLETION_LOG = "/logs/sequence-completion.jsonl"
TERMINAL_EVENT = '{"type": "result", "subtype": "success"}\n'


def command(index: int) -> list[str]:
    return ["agent_run.py", "--background", "--log", f"/logs/run-{index}.jsonl"]


def record(pid: int) -> tuple[int, str, str]:
    return 0, json.dumps({"pid": pid, "session_id": None}) + "\n", ""


class FakeProcesses:
    """Scripted `processes` port: each start answers the next scripted outcome, and a pid reads as
    alive for as many readings as `lifetimes` lists for it, then dead. Every call lands in
    `events`."""

    def __init__(self, events, launches, lifetimes, on_start=None, on_alive=None):
        self.events = events
        self.launches = list(launches)
        self.lifetimes = {pid: list(readings) for pid, readings in lifetimes.items()}
        self.on_start = on_start
        self.on_alive = on_alive

    def start(self, argv):
        self.events.append(("start", argv))
        if self.on_start:
            self.on_start(len([e for e in self.events if e[0] == "start"]))
        outcome = self.launches.pop(0)
        if outcome == "oserror":
            raise OSError("no such program")
        return outcome

    def alive(self, pid):
        readings = self.lifetimes.get(pid, [])
        reading = readings.pop(0) if readings else False
        self.events.append(("alive", pid, reading))
        if self.on_alive:
            self.on_alive(pid, reading)
        return reading

    def stop(self, pid):
        self.events.append(("stop", pid))
        self.lifetimes[pid] = []

    def sleep(self, seconds):
        self.events.append(("sleep",))


class FakeFiles:
    def __init__(self, contents=None):
        self.contents = dict(contents or {})

    def exists(self, path):
        return path in self.contents

    def read_bytes(self, path):
        return self.contents[path]

    def write_bytes(self, path, data):
        self.contents[path] = data


class FakeSignals:
    def __init__(self):
        self.handler = None

    def install(self, handler):
        self.handler = handler

    def deliver(self, signum):
        self.handler(signum)


class Built:
    def __init__(self, launches, lifetimes, files=None, on_start=None, on_alive=None):
        self.events = []
        self.lines = []
        self.signals = FakeSignals()
        self.files = files or FakeFiles()
        self.processes = FakeProcesses(
            self.events,
            launches,
            lifetimes,
            on_start=on_start and (lambda count: on_start(self, count)),
            on_alive=on_alive and (lambda pid, reading: on_alive(self, pid, reading)),
        )
        self.sequence = detached_sequence.Sequence(
            processes=self.processes,
            files=self.files,
            signals=self.signals,
            emit=self.lines.append,
        )

    def starts(self):
        return [event[1] for event in self.events if event[0] == "start"]

    def kinds(self):
        return [event[0] for event in self.events]


def test_commands_start_only_after_prior_process_ends():
    built = Built(
        [record(11), record(12), record(13)], {11: [True, True], 12: [True], 13: [True, True, True]}
    )

    built.sequence.run([command(1), command(2), command(3)])

    assert built.starts() == [command(1), command(2), command(3)]
    for earlier_pid, later in ((11, command(2)), (12, command(3))):
        ended = built.events.index(("alive", earlier_pid, False))
        assert ended < built.events.index(("start", later))
    assert ("alive", 11, True) in built.events


@pytest.mark.parametrize(
    "failure",
    [
        (2, "", "refused: no such agent"),
        "oserror",
        (0, "not a record at all", ""),
        (0, "", ""),
        (0, json.dumps({"session_id": None}), ""),
        (0, json.dumps({"pid": "twelve"}), ""),
    ],
    ids=["non-zero exit", "start failure", "malformed record", "no record", "no pid", "pid text"],
)
def test_failed_or_recordless_command_does_not_skip_later_seats(failure):
    built = Built([failure, record(12)], {12: [True]})

    status = built.sequence.run([command(1), command(2)])

    assert built.starts() == [command(1), command(2)]
    assert ("alive", 12, False) in built.events
    assert status == 0


@pytest.mark.parametrize("signum", [signal.SIGINT, signal.SIGTERM])
def test_stop_during_second_run_stops_it_and_prevents_third(signum):
    def stop_on_second_run(built, pid, reading):
        if pid == 12 and reading:
            built.signals.deliver(signum)

    built = Built(
        [record(11), record(12), record(13)],
        {11: [True], 12: [True, True, True], 13: [True]},
        on_alive=stop_on_second_run,
    )

    status = built.sequence.run([command(1), command(2), command(3)])

    assert ("stop", 12) in built.events
    assert built.starts() == [command(1), command(2)]
    assert status != 0


def test_stop_during_pid_acquisition_leaves_no_detached_run():
    def stop_while_launching_first(built, count):
        if count == 1:
            built.signals.deliver(signal.SIGTERM)

    built = Built(
        [record(11), record(12)],
        {11: [True, True], 12: [True]},
        on_start=stop_while_launching_first,
    )

    built.sequence.run([command(1), command(2)])

    assert ("stop", 11) in built.events
    assert built.starts() == [command(1)]


def test_sequence_finishes_only_after_last_process_ends():
    built = Built([record(11), record(12)], {11: [], 12: [True, True, True]})

    built.sequence.run([command(1), command(2)])

    last_pid_readings = [event for event in built.events if event[:2] == ("alive", 12)]
    assert [event[2] for event in last_pid_readings] == [True, True, True, False]
    assert built.events[-1] == ("alive", 12, False)


def run_cli(*args: str, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(TOOLS / "detached_sequence.py"), *args],
        capture_output=True,
        text=True,
        **kwargs,
    )


def wait_for(condition, seconds: float = 20.0):
    """Poll `condition` until it holds: a detached child is awaited by its effect, not guessed."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        found = condition()
        if found:
            return found
        time.sleep(0.05)
    return condition()


def write_plan(tmp_path: Path, *commands: list[str]) -> Path:
    plan = tmp_path / "plan.jsonl"
    plan.write_text("".join(json.dumps(argv) + "\n" for argv in commands))
    return plan


def test_cli_detaches_and_prints_one_run_record(tmp_path):
    plan = write_plan(tmp_path, [sys.executable, "-c", "print('this is not a run record')"])
    log = tmp_path / "sequence.log"

    result = run_cli("--plan", str(plan), "--log", str(log))

    assert result.returncode == 0
    lines = result.stdout.splitlines()
    assert len(lines) == 1
    printed = json.loads(lines[0])
    assert isinstance(printed["pid"], int) and printed["pid"] > 0
    assert printed["session_id"] is None
    assert wait_for(lambda: log.exists() and "no run record" in log.read_text())


@pytest.mark.parametrize(
    "plan_text",
    [
        None,
        "",
        "\n",
        "this is not json\n",
        "[]\n",
        '["agent_run.py", 3]\n',
        '{"argv": "x"}\n',
        '"x"\n',
    ],
    ids=["unreadable", "empty", "blank", "malformed", "empty cmd", "non-string", "object", "text"],
)
def test_invalid_plan_refuses_before_detaching(tmp_path, plan_text):
    plan = tmp_path / "plan.jsonl"
    if plan_text is not None:
        plan.write_text(plan_text)
    log = tmp_path / "sequence.log"

    result = run_cli("--plan", str(plan), "--log", str(log))

    assert result.returncode != 0
    assert result.stdout == ""
    assert "detached_sequence" in result.stderr
    assert not log.exists()


def test_completion_log_needs_a_final_command_with_a_provider_log(tmp_path):
    plan = write_plan(tmp_path, ["agent_run.py", "--background"])
    log = tmp_path / "sequence.log"

    result = run_cli(
        "--plan", str(plan), "--log", str(log), "--completion-log", str(tmp_path / "done.jsonl")
    )

    assert result.returncode != 0
    assert result.stdout == ""
    assert not log.exists()


def test_completion_log_hides_early_terminal_event():
    exposed_while_alive = []

    def watch_completion_log(built, pid, reading):
        if reading:
            exposed_while_alive.append(built.files.exists(COMPLETION_LOG))

    files = FakeFiles(
        {"/logs/run-1.jsonl": b"first\n", "/logs/run-2.jsonl": TERMINAL_EVENT.encode()}
    )
    built = Built(
        [record(11), record(12)], {11: [True], 12: [True, True]}, files=files,
        on_alive=watch_completion_log,
    )

    built.sequence.run([command(1), command(2)], completion_log=COMPLETION_LOG)

    assert exposed_while_alive == [False, False, False]
    assert files.contents[COMPLETION_LOG] == TERMINAL_EVENT.encode()


def test_absent_final_log_does_not_publish_false_success():
    built = Built([(0, "", ""), record(12)], {12: [True]})
    built.files.contents["/logs/run-1.jsonl"] = TERMINAL_EVENT.encode()

    status = built.sequence.run([command(1), command(2)], completion_log=COMPLETION_LOG)

    assert status == 0
    assert COMPLETION_LOG not in built.files.contents


def test_cli_stop_reaches_the_current_run_for_real(tmp_path):
    started = tmp_path / "run.pid"
    launch = (
        "import json, pathlib, signal, subprocess, sys;"
        # A provider run answers SIGINT; the test's own process may have it ignored (xdist), and
        # a child would inherit that.
        "signal.signal(signal.SIGINT, signal.SIG_DFL);"
        # Detached the way `agent_run.py --background` detaches a run: its output goes to a log,
        # never to the pipe the runner reads the record from.
        "d = subprocess.DEVNULL;"
        "p = subprocess.Popen(['sleep', '60'], stdin=d, stdout=d, stderr=d,"
        " start_new_session=True);"
        f"pathlib.Path({str(started)!r}).write_text(str(p.pid));"
        "print(json.dumps({'pid': p.pid, 'session_id': None}))"
    )
    successor_marker = tmp_path / "successor.started"
    successor = f"import pathlib; pathlib.Path({str(successor_marker)!r}).write_text('started')"
    plan = write_plan(tmp_path, [sys.executable, "-c", launch], [sys.executable, "-c", successor])
    log = tmp_path / "sequence.log"
    runner_pid = json.loads(run_cli("--plan", str(plan), "--log", str(log)).stdout)["pid"]
    run_pid = int(wait_for(lambda: started.exists() and started.read_text() or ""))

    try:
        os.kill(runner_pid, signal.SIGTERM)
        assert wait_for(lambda: not _alive(run_pid))
        assert wait_for(lambda: not _alive(runner_pid))
        assert not successor_marker.exists()
    finally:
        for pid in (run_pid, runner_pid):
            if _alive(pid):
                os.kill(pid, signal.SIGKILL)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True
