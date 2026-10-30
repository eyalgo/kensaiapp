"""Integration tests of the quiet stop, with real SIGINT in child processes (layer 3).

Checks SRS FR-1 (the tracker runs until it is stopped), NFR-3 (a stopped tracker releases its saved
data's location) and NFR-11 (the integration layer of the suite). Change spec rules CP-712 (a
tracker serving the unreadable-data page stops the same way and frees the location and the port),
CP-725 (nothing in the saved data changes), CP-714 and CP-732 (a held address wins on unreadable
data, and the refusal test keeps the address line), CP-644 (every Ctrl-C from the ready line until the start returns stops
the tracker with exit 0 and nothing on standard error, a further one included), CP-645 (nothing
more is written and the saved data is untouched), CP-646 and CP-647 (the ready line and the two
refusals are as they were), CP-649 (a proof that fails on the code before this change on every
run) and CP-650 (parts are handed their collaborators; no name inside a part is patched) are what
each test names.

Each child process is its own interpreter, so the signal policy it installs never reaches this
test run. A child reports where it has been over an extra pipe, never on its own standard streams.
Where a test must put a signal at a point of the product's own code, the child watches execution
with the interpreter's profile hook and raises the real signal there. It replaces no name, code
object, file or result of the product. The first test calls the unchanged two-argument `start` and
needs no symbol this change adds, so it also runs against the code before this change.
"""

from __future__ import annotations

import contextlib
import http.client
import json
import os
import re
import select
import signal
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.parse import urlencode

import pytest

import main

PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent
DEADLINE = 30
PHASES = (
    "announced",
    "serve-entry",
    "serving",
    "close-entry",
    "closing",
    "after-close",
    "before-return",
)
READY_LINE = re.compile(
    rb"The tracker is running\. Open http://127\.0\.0\.1:(?P<port>[0-9]+) in your browser\. "
    rb"Saved data is kept at (?P<location>.+)\.\n"
)
UNREADABLE_READY = re.compile(
    rb"The tracker couldn't read its saved data at (?P<location>.+), and nothing in it was "
    rb"changed\. Open http://127\.0\.0\.1:(?P<port>[0-9]+) in your browser to read this on a "
    rb"page\. To start fresh on purpose, follow Setting saved data aside in the setup "
    rb"instructions\.\n"
)
UNREADABLE_DATA = b'{"next_project_id": 3, "projects": [ truncated'
OCCUPIED_START = "The tracker didn't start, because something else is already using the address "
POPULATED_DATA = json.dumps(
    {
        "next_project_id": 2,
        "projects": [{"id": 1, "name": "Alpha", "description": "x"}],
        "assignees": [],
        "next_task_id": 1,
        "tasks": [],
        "operator_name": None,
    }
).encode("utf-8")

# What every child program starts with: the product's entry module, and a way to report a position
# over the pipe whose descriptor the parent hands in as the second argument.
PRELUDE = r"""
import builtins, os, signal, sys
from pathlib import Path
import main
ACK = int(sys.argv[2])
def ack(text):
    os.write(ACK, (text + "\n").encode())
def interrupt():
    signal.raise_signal(signal.SIGINT)
def is_main_module_frame(frame):
    return Path(frame.f_code.co_filename).resolve() == Path(main.__file__).resolve()
"""

# The unchanged start, with a real SIGINT at the first execution boundary after the ready write has
# completed: the profile hook sees the return of the `print` called from the entry module.
READY_WRITE_PROGRAM = (
    PRELUDE
    + r"""
reached = []
def observer(frame, event, argument):
    if event != "c_return" or argument is not builtins.print:
        return
    try:
        if not is_main_module_frame(frame):
            return
        reached.append(frame.f_code.co_name)
        ack("ready-write-completed")
        if len(reached) > 1:
            return
        ack("signal-injected")
    except Exception:
        ack("harness-error")
        os._exit(97)
    interrupt()
sys.setprofile(observer)
result = main.start(("127.0.0.1", 0), Path(sys.argv[1]))
sys.setprofile(None)
ack("returned " + str(result))
sys.exit(result)
"""
)

# The real interrupt adapter inside the coordinator, with handed listener and announcement
# collaborators; a real SIGINT is raised, and its callback has returned before the next line runs.
PHASE_PROGRAM = (
    PRELUDE
    + r"""
phases = sys.argv[3].split(",")
stops = main.SigintStopRequests()
handler_calls = []
def reach(phase):
    if phase in phases:
        interrupt()
        ack("delivered " + phase)
class Listener:
    def serve_until(self, stop_requested):
        reach("serve-entry")
        reach("serving")
        if {"announced", "serve-entry", "serving"} & set(phases):
            ack("predicate " + str(stop_requested()))
    def server_close(self):
        reach("close-entry")
        reach("closing")
        ack("closed")
        reach("after-close")
def announce():
    print("The tracker is running. (a handed announcement)", flush=True)
    reach("announced")
def observer(frame, event, argument):
    if event == "call" and frame.f_code is main.SigintStopRequests.latch.__code__:
        handler_calls.append(1)
    if event == "return" and frame.f_code is main.serve_until_stopped.__code__:
        reach("before-return")
sys.setprofile(observer)
result = main.serve_until_stopped(listener=Listener(), announce=announce, stops=stops)
sys.setprofile(None)
ack("result " + str(result))
ack("stop-requested " + str(stops.stop_requested()))
ack("handler-calls " + str(len(handler_calls)))
sys.exit(result)
"""
)

# The public start, stopped at its ready write, and again by a second signal at the boundary where
# `start` itself is returning; afterwards the disposition it leaves is read.
RETURN_PROGRAM = (
    PRELUDE
    + r"""
prints = []
def observer(frame, event, argument):
    if event == "c_return" and argument is builtins.print and is_main_module_frame(frame):
        prints.append(1)
        if len(prints) == 1:
            ack("ready-write-completed")
            interrupt()
    if event == "return" and frame.f_code is main.start.__code__:
        ack("start-returning")
        interrupt()
        ack("delivered-while-returning")
sys.setprofile(observer)
result = main.start(("127.0.0.1", 0), Path(sys.argv[1]))
sys.setprofile(None)
disposition = signal.getsignal(signal.SIGINT)
if disposition is signal.default_int_handler:
    ack("disposition raising")
elif callable(disposition):
    ack("disposition callable")
    disposition(signal.SIGINT, None)
    ack("direct-call-returned")
else:
    ack("disposition " + str(disposition))
ack("returned " + str(result))
sys.exit(result)
"""
)

# The public start through a real request: the profile hook runs in every thread and holds the
# real saver at its entry until the parent releases it.
SAVING_PROGRAM = (
    PRELUDE
    + r"""
import threading
import persistence
RELEASE = int(sys.argv[3])
saver_code = persistence.SavedData.save.__code__
def observer(frame, event, argument):
    if event == "call" and frame.f_code is saver_code:
        ack("saver-entered")
        os.read(RELEASE, 1)
threading.setprofile(observer)
sys.setprofile(observer)
sys.exit(main.start(("127.0.0.1", 0), Path(sys.argv[1])))
"""
)

# Arming the real adapter in a process that began with SIGINT ignored.
IGNORED_PROGRAM = (
    PRELUDE
    + r"""
stops = main.SigintStopRequests()
ack("before ignored" if signal.getsignal(signal.SIGINT) == signal.SIG_IGN else "before other")
stops.arm()
ack("after ignored" if signal.getsignal(signal.SIGINT) == signal.SIG_IGN else "after other")
ack("stop-requested " + str(stops.stop_requested()))
"""
)

# Two starts in one interpreter, each stopped at its ready write, then two adapters.
SUCCESSIVE_PROGRAM = (
    PRELUDE
    + r"""
prints = []
def observer(frame, event, argument):
    if event == "c_return" and argument is builtins.print and is_main_module_frame(frame):
        prints.append(1)
        interrupt()
sys.setprofile(observer)
handlers = []
for number in (1, 2):
    location = Path(sys.argv[1]) / str(number)
    ack("start " + str(number) + " returned " + str(main.start(("127.0.0.1", 0), location)))
    handlers.append(signal.getsignal(signal.SIGINT))
sys.setprofile(None)
ack("own-callbacks " + str(handlers[0] != handlers[1]))
class Listener:
    def __init__(self, deliver):
        self.deliver = deliver
    def serve_until(self, stop_requested):
        ack("latch-at-serve " + str(stop_requested()))
        if self.deliver:
            interrupt()
    def server_close(self):
        pass
def announce():
    pass
first, second = main.SigintStopRequests(), main.SigintStopRequests()
main.serve_until_stopped(listener=Listener(True), announce=announce, stops=first)
ack("first " + str(first.stop_requested()))
ack("second-before " + str(second.stop_requested()))
main.serve_until_stopped(listener=Listener(False), announce=announce, stops=second)
ack("second-after " + str(second.stop_requested()))
"""
)


# The public start, left running until the parent stops it.
IDLE_PROGRAM = (
    PRELUDE
    + r"""
sys.exit(main.start(("127.0.0.1", 0), Path(sys.argv[1])))
"""
)

# The same, on the port the parent hands in as the third argument.
FIXED_PORT_PROGRAM = (
    PRELUDE
    + r"""
sys.exit(main.start(("127.0.0.1", int(sys.argv[3])), Path(sys.argv[1])))
"""
)


class Acks:
    """The pipe a child reports its positions over, read here a line at a time."""

    def __init__(self) -> None:
        self.read_descriptor, self.write_descriptor = os.pipe()
        self.lines: list[str] = []
        self._pending = b""

    def _absorb(self, chunk: bytes) -> None:
        *whole, self._pending = (self._pending + chunk).split(b"\n")
        self.lines += [line.decode("utf-8") for line in whole]

    def wait_for(self, line: str) -> None:
        deadline = time.monotonic() + DEADLINE
        while line not in self.lines:
            remaining = deadline - time.monotonic()
            assert remaining > 0, f"the child never reported {line!r}: {self.lines}"
            ready, _, _ = select.select([self.read_descriptor], [], [], remaining)
            if not ready:
                continue
            chunk = os.read(self.read_descriptor, 4096)
            assert chunk, f"the child ended without reporting {line!r}: {self.lines}"
            self._absorb(chunk)

    def drain(self) -> list[str]:
        """Every line the child wrote; call once the child has ended and the write end is closed."""
        while chunk := os.read(self.read_descriptor, 4096):
            self._absorb(chunk)
        return self.lines

    def close(self) -> None:
        os.close(self.read_descriptor)


class Child:
    """A child interpreter running a program, with the pipe it reports over."""

    def __init__(
        self,
        program: str,
        location: Path,
        *arguments: str,
        ignoring_interrupt: bool = False,
        extra_descriptors: tuple[int, ...] = (),
    ) -> None:
        self.acks = Acks()
        command = [sys.executable, "-c", program, str(location), str(self.acks.write_descriptor)]
        command += list(arguments)
        if ignoring_interrupt:
            command = ["/bin/sh", "-c", 'trap "" INT; exec "$@"', "sh", *command]
        self.process = subprocess.Popen(
            command,
            cwd=PRODUCT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            pass_fds=(self.acks.write_descriptor, *extra_descriptors),
        )
        os.close(self.acks.write_descriptor)

    def finish(self) -> tuple[int, bytes, bytes, list[str]]:
        """Wait for the child to end within the deadline: status, stdout, stderr and its reports."""
        try:
            stdout, stderr = self.process.communicate(timeout=DEADLINE)
        finally:
            if self.process.poll() is None:
                self.process.kill()
                self.process.communicate()
        lines = self.acks.drain()
        self.acks.close()
        return self.process.returncode, stdout, stderr, lines


def _seen(phase: str) -> int:
    """How many handler calls the child's profile hook can count for a signal sent at the phase.

    The hook is switched off while its own callback runs, so a signal sent from inside it, as the
    one just before the coordinator returns is, runs the handler unseen. Its completion shows in the
    report written after the send and in the flag the handler sets.
    """
    return 0 if phase == "before-return" else 1


def snapshot(root: Path) -> dict[str, bytes | None]:
    """Every path under the root, relative to it, with the bytes of each file."""
    return {
        str(path.relative_to(root)): path.read_bytes() if path.is_file() else None
        for path in sorted(root.rglob("*"))
    }


def test_real_start_stops_at_the_completed_ready_write(tmp_path: Path) -> None:
    """CP-644, CP-646, CP-649: a SIGINT right after the ready write stops the unchanged start."""
    child = Child(READY_WRITE_PROGRAM, tmp_path)

    status, stdout, stderr, reports = child.finish()

    assert reports[:2] == ["ready-write-completed", "signal-injected"], (
        f"the observer did not reach its target exactly once: {reports}"
    )
    assert status == 0, stderr.decode("utf-8", errors="replace")
    assert stderr == b""
    assert reports == ["ready-write-completed", "signal-injected", "returned 0"]
    matched = READY_LINE.fullmatch(stdout)
    assert matched is not None, stdout
    assert matched.group("location") == str(tmp_path.absolute()).encode("utf-8")


@pytest.mark.parametrize("phase", PHASES)
def test_real_signal_stops_quietly_at_each_lifecycle_phase(tmp_path: Path, phase: str) -> None:
    """CP-644: a real SIGINT at each phase, with a hand-written listener and announcement."""
    child = Child(PHASE_PROGRAM, tmp_path, phase)

    status, stdout, stderr, reports = child.finish()

    assert status == 0, stderr.decode("utf-8", errors="replace")
    assert stderr == b""
    assert stdout == b"The tracker is running. (a handed announcement)\n"
    assert f"delivered {phase}" in reports
    assert reports[-3:] == ["result 0", "stop-requested True", f"handler-calls {_seen(phase)}"]
    assert reports.count("closed") == 1


@pytest.mark.parametrize(
    "phases",
    [
        ("announced", "close-entry"),
        ("announced", "closing"),
        ("announced", "after-close"),
        ("announced", "before-return"),
        ("serving", "closing", "before-return"),
    ],
    ids=lambda phases: "+".join(phases),
)
def test_real_signal_accepts_separately_delivered_repeated_stops(
    tmp_path: Path, phases: tuple[str, ...]
) -> None:
    """CP-644: each signal's callback has returned before the next is sent, so none is merged."""
    child = Child(PHASE_PROGRAM, tmp_path, ",".join(phases))

    status, stdout, stderr, reports = child.finish()

    assert status == 0, stderr.decode("utf-8", errors="replace")
    assert stderr == b""
    assert stdout == b"The tracker is running. (a handed announcement)\n"
    delivered = [line for line in reports if line.startswith("delivered ")]
    assert delivered == [f"delivered {phase}" for phase in phases]
    seen = sum(_seen(phase) for phase in phases)
    assert reports[-3:] == ["result 0", "stop-requested True", f"handler-calls {seen}"]


def test_real_start_keeps_the_non_raising_handler_through_its_return(tmp_path: Path) -> None:
    """CP-644: a SIGINT as `start` is returning is still a quiet stop, and the callback stays."""
    child = Child(RETURN_PROGRAM, tmp_path)

    status, stdout, stderr, reports = child.finish()

    assert status == 0, stderr.decode("utf-8", errors="replace")
    assert stderr == b""
    assert READY_LINE.fullmatch(stdout) is not None, stdout
    assert reports == [
        "ready-write-completed",
        "start-returning",
        "delivered-while-returning",
        "disposition callable",
        "direct-call-returned",
        "returned 0",
    ]


def _post_a_project(port: int) -> None:
    """Submit a new project the way a form does; the answer may never come if the tracker stops."""
    body = urlencode({"name": "Alpha", "description": ""}).encode("utf-8")
    headers = {
        "Sec-Fetch-Site": "same-origin",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=DEADLINE)
    try:
        connection.request("POST", "/projects", body=body, headers=headers)
        connection.getresponse().read()
    except (OSError, http.client.HTTPException):
        pass  # the tracker ended while this request was still being saved
    finally:
        connection.close()


def test_real_start_stops_while_a_real_request_is_saving(tmp_path: Path) -> None:
    """CP-644: Ctrl-C with the real saver entered and held is a quiet stop (data not claimed)."""
    release_read, release_write = os.pipe()
    location = tmp_path / "data"
    child = Child(SAVING_PROGRAM, location, str(release_read), extra_descriptors=(release_read,))
    os.close(release_read)
    try:
        assert child.process.stdout is not None
        ready = READY_LINE.fullmatch(child.process.stdout.readline())
        assert ready is not None
        port = int(ready.group("port"))
        submitter = threading.Thread(target=_post_a_project, args=(port,), daemon=True)
        submitter.start()
        child.acks.wait_for("saver-entered")
        child.process.send_signal(signal.SIGINT)
        status, _stdout, stderr, reports = child.finish()
    finally:
        with contextlib.suppress(BrokenPipeError):  # the child has ended and closed its end
            os.write(release_write, b"x")
        os.close(release_write)

    assert status == 0, stderr.decode("utf-8", errors="replace")
    assert stderr == b""
    assert reports == ["saver-entered"]


@pytest.mark.parametrize("saved", [None, POPULATED_DATA], ids=["empty-location", "saved-data"])
def test_idle_stop_preserves_every_saved_path_and_byte(tmp_path: Path, saved: bytes | None) -> None:
    """CP-645, CP-646: an idle stop leaves the same paths and bytes and writes nothing more."""
    if saved is not None:
        (tmp_path / "tracker.json").write_bytes(saved)
    before = snapshot(tmp_path)
    child = Child(IDLE_PROGRAM, tmp_path)

    assert child.process.stdout is not None
    first_line = child.process.stdout.readline()
    assert READY_LINE.fullmatch(first_line) is not None, first_line
    child.process.send_signal(signal.SIGINT)
    status, rest, stderr, _reports = child.finish()

    assert status == 0, stderr.decode("utf-8", errors="replace")
    assert stderr == b""
    assert rest == b""
    assert snapshot(tmp_path) == before


def test_arming_preserves_an_inherited_ignored_sigint(tmp_path: Path) -> None:
    """Out of scope kept: a tracker begun with SIGINT ignored keeps it ignored once armed."""
    child = Child(IGNORED_PROGRAM, tmp_path, ignoring_interrupt=True)

    status, _stdout, stderr, reports = child.finish()

    assert status == 0, stderr.decode("utf-8", errors="replace")
    assert reports == ["before ignored", "after ignored", "stop-requested False"]


def test_successive_starts_have_independent_stop_requests(tmp_path: Path) -> None:
    """CP-644: a stop on one start never leaves the next one stopped before it begins."""
    child = Child(SUCCESSIVE_PROGRAM, tmp_path)

    status, _stdout, stderr, reports = child.finish()

    assert status == 0, stderr.decode("utf-8", errors="replace")
    assert reports == [
        "start 1 returned 0",
        "start 2 returned 0",
        "own-callbacks True",
        "latch-at-serve False",
        "first True",
        "second-before False",
        "latch-at-serve False",
        "second-after False",
    ]


def _holder() -> socket.socket:
    held = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    held.bind(("127.0.0.1", 0))
    held.listen()
    return held


@pytest.mark.parametrize(
    ("unreadable", "occupied"),
    [(False, True), (True, True)],
    ids=["occupied-address", "both"],
)
def test_refused_start_retains_its_message_and_saved_bytes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    unreadable: bool,
    occupied: bool,
) -> None:
    """CP-647, CP-714, CP-732: one address line, status 1, no ready line, saved bytes untouched; a
    held address is the only refusal left, whether or not the saved data can be read."""
    if unreadable:
        (tmp_path / "tracker.json").write_bytes(UNREADABLE_DATA)
    before = snapshot(tmp_path)
    held = _holder()
    try:
        host, port = held.getsockname()
        address = (host, port) if occupied else (host, 0)
        status = main.start(address, tmp_path)
    finally:
        held.close()

    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    assert captured.err.count("\n") == 1 and captured.err.endswith("\n")
    assert captured.err.startswith(OCCUPIED_START)
    assert "running" not in captured.err and "couldn't read" not in captured.err
    assert snapshot(tmp_path) == before


UNREADABLE_PROGRAMS = {
    "announcement": READY_WRITE_PROGRAM,
    "idle": IDLE_PROGRAM,
    "return": RETURN_PROGRAM,
}


def _unreadable_announcement(stdout: bytes, location: Path) -> int:
    """The port of the one announcement line a start on unreadable data writes, in full."""
    matched = UNREADABLE_READY.fullmatch(stdout)
    assert matched is not None, stdout
    assert matched.group("location") == str(location.absolute()).encode("utf-8")
    return int(matched.group("port"))


@pytest.mark.parametrize("boundary", UNREADABLE_PROGRAMS)
def test_unreadable_start_stops_quietly_and_releases_its_location(
    tmp_path: Path, boundary: str
) -> None:
    """CP-712, CP-725: a real SIGINT at the announcement, while idle, and as `start` returns
    (repeated, the second delivered separately) ends the page-serving start with status 0 and
    nothing more written; paths and bytes are unchanged and the location and port are free."""
    location = tmp_path / "saved"
    location.mkdir()
    (location / "tracker.json").write_bytes(UNREADABLE_DATA)
    before = snapshot(location)
    child = Child(UNREADABLE_PROGRAMS[boundary], location)
    if boundary == "idle":
        assert child.process.stdout is not None
        first = child.process.stdout.readline()
        child.process.send_signal(signal.SIGINT)
        status, rest, stderr, _reports = child.finish()
        stdout = first + rest
    else:
        status, stdout, stderr, _reports = child.finish()

    assert status == 0, stderr.decode("utf-8", errors="replace")
    assert stderr == b""
    port = _unreadable_announcement(stdout, location)
    assert snapshot(location) == before

    again = Child(FIXED_PORT_PROGRAM, location, str(port))
    assert again.process.stdout is not None
    line = again.process.stdout.readline()
    assert _unreadable_announcement(line, location) == port
    again.process.send_signal(signal.SIGINT)
    status, rest, stderr, _reports = again.finish()
    assert (status, rest, stderr) == (0, b"", b"")
    assert snapshot(location) == before
