"""Integration tests of the saved-data location claim, with real files and independent processes.

Checks SRS NFR-3 and AC-16 (one running tracker per saved-data location), NFR-2 (a claim never
changes the saved bytes) and FR-1 (a start on a location it can use). Change spec rules CP-694 to
CP-698, CP-702 and CP-706 and NFDR QC-4, QC-19, QC-22 and QC-42 are the ones each test names. Every
contender is a separate interpreter, because a claim is held by the process that made it; the cases
that interrupt or fail an acquisition run in a child with an audit hook or a profile observer that
raises at the operating-system call, so no name inside a product module is replaced (SDD § 4 TS-2).
"""

from __future__ import annotations

import inspect
import json
import os
import select
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from errors import AppError
from persistence import DEFAULT_LOCATION, LocationInUse, LocationUse, SavedData, UnreadableData

PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent
DEADLINE_SECONDS = 30
SAVED_BYTES = b'{"kept": "as it was"}'

CLAIM_PROGRAM = """
import sys
from pathlib import Path
from persistence import LocationInUse, LocationUse

try:
    with LocationUse(Path(sys.argv[1])):
        print("acquired", flush=True)
except LocationInUse:
    print("in-use", flush=True)
"""

HOLD_PROGRAM = """
import sys
from pathlib import Path
from persistence import LocationUse

with LocationUse(Path(sys.argv[1])) as use:
    use.mark_started()
    print("held", flush=True)
    sys.stdin.readline()
"""

INTERRUPT_PROGRAM = """
import json
import os
import sys
from pathlib import Path
from persistence import LocationInUse, LocationUse

location, mode = Path(sys.argv[1]), sys.argv[2]
MARK = "observer-interruption"
fired = []

if mode == "after-open":

    def audit(event, args):
        if event == "fcntl.flock" and not fired:
            fired.append(event)
            raise KeyboardInterrupt(MARK)

    sys.addaudithook(audit)
else:

    def profile(frame, event, argument):
        if event == "c_return" and getattr(argument, "__name__", "") == "flock":
            fired.append(event)
            raise KeyboardInterrupt(MARK)

    sys.setprofile(profile)

before = len(os.listdir("/dev/fd"))
outcome = "entered"
try:
    with LocationUse(location):
        pass
except KeyboardInterrupt as error:
    outcome = "interrupted:" + str(error)
except LocationInUse:
    outcome = "in-use"
sys.setprofile(None)
print(
    json.dumps(
        {
            "fired": len(fired),
            "outcome": outcome,
            "descriptors": len(os.listdir("/dev/fd")) - before,
        }
    )
)
"""

INJECT_PROGRAM = """
import errno
import json
import os
import sys
from pathlib import Path
from persistence import LocationInUse, LocationUse

location, stage, code = sys.argv[1], sys.argv[2], getattr(errno, sys.argv[3])
EVENTS = {"mkdir": "os.mkdir", "open": "open", "flock": "fcntl.flock"}
fired = []

def audit(event, args):
    if event != EVENTS[stage]:
        return
    if stage != "flock" and str(args[0]) != location:
        return
    fired.append(event)
    raise OSError(code, os.strerror(code))

before = len(os.listdir("/dev/fd"))
sys.addaudithook(audit)
outcome = "not-entered"
try:
    with LocationUse(Path(location)):
        outcome = "entered"
except LocationInUse:
    outcome = "in-use"
print(
    json.dumps(
        {
            "fired": len(fired),
            "outcome": outcome,
            "descriptors": len(os.listdir("/dev/fd")) - before,
            "present": os.path.lexists(location),
        }
    )
)
"""

CONTENDER_PROGRAM = """
import os
import sys
import time
from pathlib import Path
from persistence import LocationUse

location, ready, go = sys.argv[1:4]
blocked = []

def audit(event, args):
    if event == "fcntl.flock" and not blocked:
        blocked.append(event)
        Path(ready).write_text("ready")
        end = time.monotonic() + 30
        while not os.path.exists(go) and time.monotonic() < end:
            time.sleep(0.01)

sys.addaudithook(audit)
with LocationUse(Path(location)) as use:
    use.mark_started()
    print("entered", os.path.isdir(location), flush=True)
    sys.stdin.readline()
"""


class _Child:
    """One interpreter running a program from this module, read with a deadline on every wait."""

    def __init__(self, program: str, *arguments: str, cwd: Path | None = None) -> None:
        self.process = subprocess.Popen(
            [sys.executable, "-c", program, *arguments],
            cwd=cwd or PRODUCT_ROOT,
            env={**os.environ, "PYTHONPATH": str(PRODUCT_ROOT), "PYTHONDONTWRITEBYTECODE": "1"},
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._pending = b""

    def line(self) -> str:
        """The next line the child wrote, or a failure that carries what it wrote to stderr."""
        assert self.process.stdout is not None
        end = time.monotonic() + DEADLINE_SECONDS
        while b"\n" not in self._pending:
            remaining = end - time.monotonic()
            if remaining <= 0 or not select.select([self.process.stdout], [], [], remaining)[0]:
                raise AssertionError(f"no line within {DEADLINE_SECONDS} seconds\n{self._report()}")
            chunk = os.read(self.process.stdout.fileno(), 4096)
            if not chunk:
                raise AssertionError(f"the child ended without the line\n{self._report()}")
            self._pending += chunk
        text, _, self._pending = self._pending.partition(b"\n")
        return text.decode()

    def finish(self) -> tuple[int, str]:
        """Let the child end, and return its exit status and everything else it wrote."""
        assert self.process.stdin is not None
        try:
            self.process.stdin.write(b"\n")
            self.process.stdin.flush()
        except BrokenPipeError:
            pass
        try:
            out, _ = self.process.communicate(timeout=DEADLINE_SECONDS)
        except subprocess.TimeoutExpired:
            raise AssertionError(f"the child did not end\n{self._report()}") from None
        return self.process.returncode, (self._pending + out).decode()

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.kill()
        self.process.communicate()

    def _report(self) -> str:
        self.process.kill()
        _, errors = self.process.communicate()
        return f"child standard error:\n{errors.decode()}"


@contextmanager
def _holding(location: Path) -> Iterator[None]:
    """A separate process that holds the claim on the location until the block ends."""
    holder = _Child(HOLD_PROGRAM, str(location))
    try:
        assert holder.line() == "held"
        yield
    finally:
        holder.close()


def _claim_outcome(location: str | Path, cwd: Path | None = None) -> str:
    """What a fresh process finds when it tries the claim: `acquired` or `in-use`."""
    child = _Child(CLAIM_PROGRAM, str(location), cwd=cwd)
    try:
        answer = child.line()
        status, rest = child.finish()
    finally:
        child.close()
    assert status == 0, rest
    return answer


def _run_json(program: str, *arguments: str) -> dict[str, object]:
    child = _Child(program, *arguments)
    try:
        report = json.loads(child.line())
        status, rest = child.finish()
    finally:
        child.close()
    assert status == 0, rest
    assert isinstance(report, dict)
    return report


def _snapshot(directory: Path) -> dict[str, bytes | None]:
    """Every entry under the directory, with the bytes of each file."""
    return {
        str(path.relative_to(directory)): path.read_bytes() if path.is_file() else None
        for path in sorted(directory.rglob("*"))
    }


def _populated(tmp_path: Path, name: str = "saved") -> Path:
    location = tmp_path / name
    location.mkdir()
    (location / "tracker.json").write_bytes(SAVED_BYTES)
    return location


class _BodyFailed(Exception):
    """The sentinel a body raises, to show it comes out of the claim unchanged."""


def test_constructing_location_use_claims_and_creates_nothing(tmp_path: Path) -> None:
    """CP-706: construction acquires nothing and creates nothing."""
    absent = tmp_path / "absent"
    existing = tmp_path / "existing"
    existing.mkdir()
    constructed = [LocationUse(absent), LocationUse(existing)]
    assert len(constructed) == 2
    assert not absent.exists()
    assert _claim_outcome(existing) == "acquired"
    assert not absent.exists()


def test_location_in_use_is_the_shared_typed_error() -> None:
    """CP-706, QC-4: the signal derives from the one base error; the old exports stay as they were."""
    assert issubclass(LocationInUse, AppError)
    assert LocationInUse is not AppError
    assert list(inspect.signature(SavedData).parameters) == ["location"]
    assert issubclass(UnreadableData, AppError)
    assert isinstance(DEFAULT_LOCATION, Path)


def test_entered_location_excludes_another_process_before_any_save(tmp_path: Path) -> None:
    """CP-694, CP-695, CP-698: an entered claim refuses a contender at once, with no saved file."""
    location = tmp_path / "saved"
    location.mkdir()
    started = time.monotonic()
    with LocationUse(location):
        assert not (location / "tracker.json").exists()
        assert _claim_outcome(location) == "in-use"
    assert time.monotonic() - started < DEADLINE_SECONDS
    with _holding(location):
        with pytest.raises(LocationInUse):
            with LocationUse(location):
                pytest.fail("the body of a refused claim ran")
    assert not (location / "tracker.json").exists()


@pytest.mark.parametrize("alias", ["absolute", "relative", "symlink"])
def test_aliases_contend_but_another_directory_does_not(tmp_path: Path, alias: str) -> None:
    """CP-697: every way of naming the directory meets its claim; another directory does not."""
    location = tmp_path / "saved"
    location.mkdir()
    other = tmp_path / "other"
    other.mkdir()
    (tmp_path / "link").symlink_to(location, target_is_directory=True)
    named = {"absolute": str(location), "relative": "saved", "symlink": str(tmp_path / "link")}
    with _holding(location):
        assert _claim_outcome(named[alias], cwd=tmp_path) == "in-use"
        assert _claim_outcome(other) == "acquired"
        assert _claim_outcome("other", cwd=tmp_path) == "acquired"


def test_context_exit_releases_the_claim(tmp_path: Path) -> None:
    """CP-694, CP-706: both kinds of exit release the claim; the body's exception is unchanged."""
    location = _populated(tmp_path)
    before = _snapshot(location)
    with LocationUse(location):
        assert _snapshot(location) == before
        assert _claim_outcome(location) == "in-use"
    assert _claim_outcome(location) == "acquired"
    sentinel = _BodyFailed("the body failed")
    with pytest.raises(_BodyFailed) as caught:
        with LocationUse(location):
            raise sentinel
    assert caught.value is sentinel
    assert _claim_outcome(location) == "acquired"
    assert _snapshot(location) == before


@pytest.mark.parametrize("mode", ["after-open", "after-lock"])
def test_interruption_during_entry_releases_partial_resources(tmp_path: Path, mode: str) -> None:
    """CP-706: an interruption mid-entry propagates unchanged and leaves no descriptor behind."""
    location = _populated(tmp_path)
    report = _run_json(INTERRUPT_PROGRAM, str(location), mode)
    assert report == {"fired": 1, "outcome": "interrupted:observer-interruption", "descriptors": 0}
    assert _claim_outcome(location) == "acquired"
    assert _snapshot(location) == {"tracker.json": SAVED_BYTES}


@pytest.mark.parametrize(
    ("stage", "code", "initially_absent"),
    [
        ("mkdir", "EACCES", True),
        ("mkdir", "EROFS", True),
        ("open", "EACCES", True),
        ("open", "EACCES", False),
        ("open", "EWOULDBLOCK", True),
        ("open", "EWOULDBLOCK", False),
        ("open", "EMFILE", False),
        ("flock", "EOPNOTSUPP", True),
        ("flock", "EOPNOTSUPP", False),
        ("flock", "ENOLCK", True),
        ("flock", "ENOLCK", False),
    ],
)
def test_non_contention_acquisition_failure_enters_without_a_claim(
    tmp_path: Path, stage: str, code: str, initially_absent: bool
) -> None:
    """CP-702: only the lock call's own contention is another tracker; the rest enters, unclaimed."""
    location = tmp_path / "saved"
    if not initially_absent:
        location.mkdir()
    report = _run_json(INJECT_PROGRAM, str(location), stage, code)
    assert report == {
        "fired": 1,
        "outcome": "entered",
        "descriptors": 0,
        "present": not initially_absent,
    }
    assert _claim_outcome(location) == "acquired"


@pytest.mark.parametrize(
    "setup", ["absent", "preexisting-empty", "populated", "populated-after-entry"]
)
def test_failed_start_restores_only_its_own_empty_leaf(tmp_path: Path, setup: str) -> None:
    """CP-701, CP-706: a failed start removes only the empty leaf it made, and no saved byte."""
    location = tmp_path / "saved"
    if setup == "populated":
        location = _populated(tmp_path)
    elif setup == "preexisting-empty":
        location.mkdir()
    before = _snapshot(location) if location.exists() else None
    with pytest.raises(_BodyFailed):
        with LocationUse(location):
            if setup == "populated-after-entry":
                (location / "tracker.json").write_bytes(SAVED_BYTES)
            raise _BodyFailed
    if setup == "absent":
        assert not location.exists()
    elif setup == "populated-after-entry":
        assert _snapshot(location) == {"tracker.json": SAVED_BYTES}
    else:
        assert _snapshot(location) == before
    assert _claim_outcome(location) == "acquired"


@pytest.mark.parametrize("exit_kind", ["normal", "exceptional"])
def test_successful_start_keeps_its_empty_location(tmp_path: Path, exit_kind: str) -> None:
    """CP-703: a started claim saves no file and leaves the empty location it made."""
    location = tmp_path / "saved"
    if exit_kind == "normal":
        with LocationUse(location) as use:
            use.mark_started()
            assert _snapshot(location) == {}
    else:
        with pytest.raises(_BodyFailed):
            with LocationUse(location) as use:
                use.mark_started()
                raise _BodyFailed
    assert location.is_dir()
    assert _snapshot(location) == {}
    assert _claim_outcome(location) == "acquired"
    assert location.is_dir()


def _wait_for(path: Path) -> None:
    end = time.monotonic() + DEADLINE_SECONDS
    while not path.exists():
        assert time.monotonic() < end, f"{path.name} did not appear"
        time.sleep(0.01)


def test_contender_reacquires_the_live_directory_after_owner_rollback(tmp_path: Path) -> None:
    """CP-697, CP-698: a claim on a directory the rollback unlinked is not a claim on the path."""
    location = tmp_path / "saved"
    ready, go = tmp_path / "ready", tmp_path / "go"
    contender: _Child | None = None
    try:
        with pytest.raises(_BodyFailed):
            with LocationUse(location):
                contender = _Child(CONTENDER_PROGRAM, str(location), str(ready), str(go))
                _wait_for(ready)
                raise _BodyFailed
        assert not location.exists()
        go.write_text("go")
        assert contender is not None
        assert contender.line() == "entered True"
        assert location.is_dir()
        assert _claim_outcome(location) == "in-use"
        assert location.is_dir()
    finally:
        if contender is not None:
            contender.close()
