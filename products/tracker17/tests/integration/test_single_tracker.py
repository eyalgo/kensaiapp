"""Integration tests of one running tracker per saved-data location, through real starts (layer 2).

Checks SRS NFR-3 and AC-16 (a second start against a location in use is refused and the first goes
on; a start after a kill serves), FR-1 (the ready line), FR-3 (the address line) and FR-4 (the
unreadable-data page a start on unreadable saved data serves). Change spec rules CP-693 to CP-699,
CP-701, CP-702, CP-704, CP-705, CP-713, CP-715 and CP-732 and NFDR QC-52 and QC-58 are the ones
each test names. Every tracker is a separate interpreter running the
product's own start; no test patches a name inside the product (SDD § 4 TS-2). Rare acquisition
failures run in a child with an audit hook that raises at the operating-system call and leaves a
marker file when it fired. Each wait has a deadline, so a second start that serves fails the test
instead of hanging it.
"""

from __future__ import annotations

import http.client
import os
import select
import shutil
import signal
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from domain import empty_state
from persistence import SavedData

PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent
DEADLINE_SECONDS = 30
REFUSAL_DEADLINE_SECONDS = 10
READY_PREFIX = "The tracker is running. Open http://127.0.0.1:"
REFUSAL_LINE = (
    "The tracker didn't start, because another tracker is already running on the same saved "
    "data. Stop that one first, then start this one."
)
ADDRESS_LINE = (
    "The tracker didn't start, because something else is already using the address "
    "127.0.0.1:{port}. Stop that program, then start the tracker again."
)
UNREADABLE_PREFIX = "The tracker couldn't read its saved data at "
DAMAGED = b'{"next_project_id": 3, "projects": [ truncated'
START_PROGRAM = """
import os
import sys
import time
from pathlib import Path
import main

if len(sys.argv) > 4:
    end = time.monotonic() + 30
    while not os.path.exists(sys.argv[4]) and time.monotonic() < end:
        time.sleep(0.005)
raise SystemExit(main.start((sys.argv[1], int(sys.argv[2])), Path(sys.argv[3])))
"""
CLOSING_OBSERVER_PROGRAM = """
import os
import sys
import time
from pathlib import Path
import main

ready, go = sys.argv[4], sys.argv[5]
seen = []

def profile(frame, event, argument):
    if event == "call" and frame.f_code.co_name == "server_close" and not seen:
        seen.append(event)
        Path(ready).write_text("closing")
        end = time.monotonic() + 30
        while not os.path.exists(go) and time.monotonic() < end:
            time.sleep(0.01)

sys.setprofile(profile)
raise SystemExit(main.start((sys.argv[1], int(sys.argv[2])), Path(sys.argv[3])))
"""
INJECTED_START_PROGRAM = """
import errno
import os
import sys
from pathlib import Path
import main

host, port, location, stage, code, marker = sys.argv[1:7]
EVENTS = {"mkdir": "os.mkdir", "open": "open", "flock": "fcntl.flock"}

def audit(event, args):
    if event != EVENTS[stage]:
        return
    if stage != "flock" and str(args[0]) != location:
        return
    Path(marker).write_text(event)
    number = getattr(errno, code)
    raise OSError(number, os.strerror(number))

sys.addaudithook(audit)
raise SystemExit(main.start((host, int(port)), Path(location)))
"""


@dataclass(frozen=True)
class Outcome:
    """How a start ended: its exit status and everything it wrote."""

    status: int
    out: str
    err: str


class _Process:
    """One interpreter, read with a deadline on every wait."""

    def __init__(self, arguments: list[str], cwd: Path) -> None:
        self.process = subprocess.Popen(
            [sys.executable, *arguments],
            cwd=cwd,
            env={**os.environ, "PYTHONPATH": str(PRODUCT_ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._pending = b""

    def event(self) -> tuple[str, str | Outcome]:
        """The next thing the process did: `("line", text)` or `("exit", Outcome)`."""
        assert self.process.stdout is not None
        end = time.monotonic() + DEADLINE_SECONDS
        while b"\n" not in self._pending:
            remaining = end - time.monotonic()
            if remaining <= 0 or not select.select([self.process.stdout], [], [], remaining)[0]:
                raise AssertionError(f"neither a line nor an exit within {DEADLINE_SECONDS}s")
            chunk = os.read(self.process.stdout.fileno(), 4096)
            if not chunk:
                return "exit", self.finish(DEADLINE_SECONDS)
            self._pending += chunk
        text, _, self._pending = self._pending.partition(b"\n")
        return "line", text.decode()

    def ready(self, prefix: str = READY_PREFIX) -> None:
        kind, value = self.event()
        assert kind == "line" and str(value).startswith(prefix), value

    def unreadable_ready(self, location: Path) -> int:
        """Wait for the unreadable-data announcement; return the port it names."""
        kind, value = self.event()
        assert kind == "line" and str(value).startswith(UNREADABLE_PREFIX), value
        assert f"{UNREADABLE_PREFIX}{location.absolute()}, and nothing in it was changed." in str(
            value
        )
        return int(str(value).split("http://127.0.0.1:")[1].split(" ")[0])

    def finish(self, deadline: int = REFUSAL_DEADLINE_SECONDS) -> Outcome:
        """Wait for the process to end on its own and return how it ended."""
        try:
            out, err = self.process.communicate(timeout=deadline)
        except subprocess.TimeoutExpired:
            self.close()
            raise AssertionError("the process kept running: it served instead of ending") from None
        return Outcome(self.process.returncode, (self._pending + out).decode(), err.decode())

    def send(self, number: int) -> None:
        self.process.send_signal(number)

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.kill()
        self.process.communicate()


@dataclass
class _Tracker:
    process: _Process
    port: int

    def status(self, target: str = "/") -> int:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=DEADLINE_SECONDS)
        try:
            connection.request("GET", target)
            return connection.getresponse().status
        finally:
            connection.close()

    def page(self, target: str = "/") -> str:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=DEADLINE_SECONDS)
        try:
            connection.request("GET", target)
            return connection.getresponse().read().decode("utf-8")
        finally:
            connection.close()

    def create_project(self, name: str) -> None:
        """A real save: the form the browser sends to create a project."""
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=DEADLINE_SECONDS)
        try:
            body = f"name={name}&description="
            connection.request(
                "POST",
                "/projects",
                body,
                {
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Sec-Fetch-Site": "same-origin",
                },
            )
            response = connection.getresponse()
            response.read()
            assert response.status in (302, 303), response.status
        finally:
            connection.close()

    def kill(self) -> None:
        self.process.send(signal.SIGKILL)
        self.process.process.wait(timeout=DEADLINE_SECONDS)

    def interrupt(self) -> Outcome:
        self.process.send(signal.SIGINT)
        return self.process.finish()


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


class _Fleet:
    """Starts trackers on free ports and ends any still running when the test is over."""

    def __init__(self, working_directory: Path) -> None:
        self.working_directory = working_directory
        self._started: list[_Process] = []

    def spawn(self, program: str, *arguments: str, cwd: Path | None = None) -> _Process:
        process = _Process(["-c", program, *arguments], cwd or self.working_directory)
        self._started.append(process)
        return process

    def run_script(self, script: str, cwd: Path) -> _Process:
        """The real command: the interpreter given the script's file, with no argument."""
        process = _Process([script], cwd)
        self._started.append(process)
        return process

    def start(self, location: str | Path, port: int | None = None) -> _Tracker:
        chosen = _free_port() if port is None else port
        process = self.spawn(START_PROGRAM, "127.0.0.1", str(chosen), str(location))
        process.ready()
        return _Tracker(process, chosen)

    def start_unreadable(self, location: Path, port: int | None = None) -> _Tracker:
        """A start on data it cannot read: it serves the page, after its one announcement."""
        chosen = _free_port() if port is None else port
        process = self.spawn(START_PROGRAM, "127.0.0.1", str(chosen), str(location))
        assert process.unreadable_ready(location) == chosen
        return _Tracker(process, chosen)

    def refused(
        self, location: str | Path, port: int | None = None, cwd: Path | None = None
    ) -> tuple[Outcome, int]:
        """A start that must end by itself; the port it was given is returned beside its outcome."""
        chosen = _free_port() if port is None else port
        process = self.spawn(START_PROGRAM, "127.0.0.1", str(chosen), str(location), cwd=cwd)
        return process.finish(), chosen

    def close(self) -> None:
        for process in self._started:
            process.close()


@pytest.fixture
def fleet(tmp_path: Path) -> Iterator[_Fleet]:
    working_directory = tmp_path / "elsewhere"
    working_directory.mkdir()
    started = _Fleet(working_directory)
    yield started
    started.close()


def _saved(location: Path) -> Path:
    SavedData(location).save(empty_state())
    return location


def _record(location: Path) -> dict[str, bytes | None]:
    return {
        str(path.relative_to(location)): path.read_bytes() if path.is_file() else None
        for path in sorted(location.rglob("*"))
    }


def _nothing_listens(port: int) -> bool:
    with socket.socket() as probe:
        return probe.connect_ex(("127.0.0.1", port)) != 0


def test_second_tracker_is_refused_without_changing_the_first(
    tmp_path: Path, fleet: _Fleet
) -> None:
    """CP-693, CP-694, CP-704: the one line, exit 1, nothing served, and the first answers."""
    location = _saved(tmp_path / "saved")
    first = fleet.start(location)
    before = _record(location)
    outcome, port = fleet.refused(location)
    assert outcome == Outcome(1, "", REFUSAL_LINE + "\n")
    assert _nothing_listens(port)
    assert _record(location) == before
    assert first.status() == 200


@pytest.mark.parametrize("saved", [True, False], ids=["populated", "never-saved"])
def test_tracker_starts_after_the_owner_is_killed(
    tmp_path: Path, fleet: _Fleet, saved: bool
) -> None:
    """CP-699, CP-703, CP-705: after a refusal is shown, a kill frees the location for a start."""
    location = tmp_path / "saved"
    if saved:
        _saved(location)
    first = fleet.start(location)
    shown, _ = fleet.refused(location)
    assert shown == Outcome(1, "", REFUSAL_LINE + "\n")
    first.kill()
    left = _record(location) if location.exists() else None
    again = fleet.start(location)
    assert again.status() == 200
    assert (_record(location) if location.exists() else None) == left
    if not saved:
        assert not (location / "tracker.json").exists()


def test_start_after_a_kill_serves_what_the_killed_tracker_saved(
    tmp_path: Path, fleet: _Fleet
) -> None:
    """CP-699: the project the killed tracker saved is served, with no word about that tracker."""
    location = tmp_path / "saved"
    first = fleet.start(location)
    first.create_project("Alpha")
    first.kill()
    again = fleet.start(location)
    assert "Alpha" in again.page()
    assert again.interrupt() == Outcome(0, "", "")


@pytest.mark.parametrize("saves", [0, 1, 3])
def test_refusal_keeps_the_claim_before_and_after_saves(
    tmp_path: Path, fleet: _Fleet, saves: int
) -> None:
    """CP-694, CP-695, CP-703: a save replaces the file and the claim stays, so the refusal holds."""
    location = tmp_path / "saved"
    first = fleet.start(location)
    for number in range(saves):
        first.create_project(f"Project{number}")
    assert (location / "tracker.json").exists() == (saves > 0)
    before = _record(location)
    outcome, _ = fleet.refused(location)
    assert outcome == Outcome(1, "", REFUSAL_LINE + "\n")
    assert _record(location) == before
    assert first.status() == 200


def test_location_in_use_wins_over_other_start_refusals(tmp_path: Path, fleet: _Fleet) -> None:
    """CP-696, CP-713: another tracker, then the address; one line each time, whatever the saved
    data holds (unreadable data is no longer a refusal)."""
    location = _saved(tmp_path / "saved")
    first = fleet.start(location)
    same_port, _ = fleet.refused(location, port=first.port)
    assert same_port == Outcome(1, "", REFUSAL_LINE + "\n")
    (location / "tracker.json").write_bytes(DAMAGED)
    before = _record(location)
    damaged, _ = fleet.refused(location)
    assert damaged == Outcome(1, "", REFUSAL_LINE + "\n")
    assert _record(location) == before == {"tracker.json": DAMAGED}
    assert first.status() == 200


def test_second_tracker_is_refused_while_unreadable_page_serves(
    tmp_path: Path, fleet: _Fleet
) -> None:
    """CP-713: the first tracker serves the page; the second gets the CP-693 line and exit 1, the
    first still answers 503, and the saved data is the same."""
    location = tmp_path / "saved"
    location.mkdir()
    (location / "tracker.json").write_bytes(DAMAGED)
    first = fleet.start_unreadable(location)
    before = _record(location)
    outcome, port = fleet.refused(location)
    assert outcome == Outcome(1, "", REFUSAL_LINE + "\n")
    assert _nothing_listens(port)
    assert _record(location) == before == {"tracker.json": DAMAGED}
    assert first.status() == 503
    again, _ = fleet.refused(location, port=first.port)
    assert again == Outcome(1, "", REFUSAL_LINE + "\n")


def test_the_real_second_start_command_gets_the_refusal_and_not_the_address_line(
    tmp_path: Path, fleet: _Fleet
) -> None:
    """CP-696: two real no-argument starts meet one location and one fixed address."""
    copy = tmp_path / "product"
    shutil.copytree(
        PRODUCT_ROOT,
        copy,
        ignore=shutil.ignore_patterns(
            ".venv", "__pycache__", "data", "docs", "tests", ".*_cache", ".git"
        ),
    )
    first = fleet.run_script("main.py", cwd=copy)
    kind, value = first.event()
    assert kind == "line", f"the first start could not hold 127.0.0.1:8017: {value}"
    assert str(value).startswith("The tracker is running. Open http://127.0.0.1:8017 ")
    second = fleet.run_script("main.py", cwd=copy)
    assert second.finish() == Outcome(1, "", REFUSAL_LINE + "\n")
    assert _Tracker(first, 8017).status() == 200


@pytest.mark.parametrize("alias", ["absolute", "relative", "symlink"])
def test_real_starts_resolve_directory_aliases_and_separate_locations(
    tmp_path: Path, fleet: _Fleet, alias: str
) -> None:
    """CP-697, CP-701: aliases of the directory meet its claim; a distinct directory does not."""
    location = _saved(tmp_path / "saved")
    other = _saved(tmp_path / "other")
    (tmp_path / "link").symlink_to(location, target_is_directory=True)
    first = fleet.start(location)
    named = {"absolute": str(location), "relative": "saved", "symlink": str(tmp_path / "link")}
    outcome, _ = fleet.refused(named[alias], cwd=tmp_path)
    assert outcome == Outcome(1, "", REFUSAL_LINE + "\n")
    before = _record(other)
    distinct = fleet.start(other)
    assert distinct.status() == 200
    distinct.interrupt()
    taken, _ = fleet.refused(other, port=first.port)
    assert taken == Outcome(1, "", ADDRESS_LINE.format(port=first.port) + "\n")
    assert _record(other) == before


@pytest.mark.parametrize("existing", [True, False], ids=["existing", "absent-leaf"])
def test_simultaneous_starts_have_one_ready_owner(
    tmp_path: Path, fleet: _Fleet, existing: bool
) -> None:
    """CP-698: of two starts released together, one is ready and the other is refused."""
    for round_number in range(3):
        location = tmp_path / f"saved{round_number}"
        if existing:
            location.mkdir()
        go = tmp_path / f"go{round_number}"
        children = [
            fleet.spawn(START_PROGRAM, "127.0.0.1", str(_free_port()), str(location), str(go))
            for _ in range(2)
        ]
        go.write_text("go")
        events = [child.event() for child in children]
        ready = [child for child, (kind, _) in zip(children, events, strict=True) if kind == "line"]
        refused = [value for kind, value in events if kind == "exit"]
        assert len(ready) == 1 and len(refused) == 1, events
        assert refused == [Outcome(1, "", REFUSAL_LINE + "\n")]
        winner_line = next(value for kind, value in events if kind == "line")
        port = int(str(winner_line).removeprefix(READY_PREFIX).split(" ")[0])
        assert _Tracker(ready[0], port).status() == 200


def test_tracker_restarts_after_ctrl_c(tmp_path: Path, fleet: _Fleet) -> None:
    """CP-699: Ctrl-C ends the owner quietly, and the next start on the location serves."""
    location = _saved(tmp_path / "saved")
    first = fleet.start(location)
    first.create_project("Alpha")
    saved = (location / "tracker.json").read_bytes()
    assert first.interrupt() == Outcome(0, "", "")
    again = fleet.start(location)
    assert again.status() == 200
    assert (location / "tracker.json").read_bytes() == saved


@pytest.mark.parametrize("damaged", [False, True], ids=["readable", "unreadable"])
def test_location_claim_remains_held_during_listener_close(
    tmp_path: Path, fleet: _Fleet, damaged: bool
) -> None:
    """CP-695, CP-706, CP-713: the claim outlasts the listener's closure and ends with the start,
    whether the start serves the tracker or the unreadable-data page."""
    location = tmp_path / "saved"
    if damaged:
        location.mkdir()
        (location / "tracker.json").write_bytes(DAMAGED)
    else:
        _saved(location)
    ready, go = tmp_path / "closing", tmp_path / "go"
    port = _free_port()
    owner = fleet.spawn(
        CLOSING_OBSERVER_PROGRAM, "127.0.0.1", str(port), str(location), str(ready), str(go)
    )
    if damaged:
        assert owner.unreadable_ready(location) == port
    else:
        owner.ready()
    owner.send(signal.SIGINT)
    end = time.monotonic() + DEADLINE_SECONDS
    while not ready.exists():
        assert time.monotonic() < end, "the owner never reached the listener's closure"
        time.sleep(0.01)
    outcome, _ = fleet.refused(location)
    assert outcome == Outcome(1, "", REFUSAL_LINE + "\n")
    go.write_text("go")
    assert owner.finish() == Outcome(0, "", "")
    if damaged:
        assert fleet.start_unreadable(location).status() == 503
    else:
        assert fleet.start(location).status() == 200


@pytest.mark.skipif(os.geteuid() == 0, reason="a read-only directory does not stop root")
def test_absent_location_under_a_read_only_parent_still_serves(
    tmp_path: Path, fleet: _Fleet
) -> None:
    """CP-702: a location that cannot be created is not a tracker running there."""
    parent = tmp_path / "parent"
    parent.mkdir()
    parent.chmod(0o555)
    try:
        tracker = fleet.start(parent / "saved")
        assert tracker.status() == 200
    finally:
        parent.chmod(0o755)


@pytest.mark.parametrize(
    ("stage", "code"), [("mkdir", "EACCES"), ("open", "EACCES"), ("flock", "ENOLCK")]
)
@pytest.mark.parametrize(
    "scenario", ["serves", "unreadable", "address-held", "unreadable-and-address-held"]
)
def test_indeterminate_acquisition_keeps_existing_start_behavior(
    tmp_path: Path, fleet: _Fleet, stage: str, code: str, scenario: str
) -> None:
    """CP-696, CP-701, CP-702, CP-715: a claim that cannot be made never prints the refusal line.

    The start goes on in the mode its data chooses: the tracker, or the unreadable-data page; a
    held address gets only the address line whatever the data is.
    """
    location = tmp_path / "saved"
    if scenario.startswith("unreadable"):
        location.mkdir()
        (location / "tracker.json").write_bytes(DAMAGED)
    elif scenario == "serves":
        _saved(location)
    marker = tmp_path / "fired"
    held: socket.socket | None = None
    port = _free_port()
    if scenario.endswith("address-held"):
        held = socket.socket()
        held.bind(("127.0.0.1", port))
        held.listen()
    before = _record(location) if location.exists() else None
    try:
        process = fleet.spawn(
            INJECTED_START_PROGRAM, "127.0.0.1", str(port), str(location), stage, code, str(marker)
        )
        if scenario == "serves":
            process.ready()
            assert _Tracker(process, port).status() == 200
        elif scenario == "unreadable":
            assert process.unreadable_ready(location) == port
            assert _Tracker(process, port).status() == 503
            assert (_record(location) if location.exists() else None) == before
        else:
            outcome = process.finish()
            assert outcome == Outcome(1, "", ADDRESS_LINE.format(port=port) + "\n")
            assert (_record(location) if location.exists() else None) == before
    finally:
        if held is not None:
            held.close()
    assert marker.exists(), "the injected failure never fired"
