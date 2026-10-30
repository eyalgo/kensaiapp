"""Integration tests of a ready start whose saved-data path holds a byte that is not text (layer 2),
through real starts in child processes.

Checks SRS FR-1 (the start prints where to open the tracker and where the data is, and serves until
Ctrl-C) and NFR-3 (a stop leaves the saved data as it was). Change spec rules CP-747 (a readable
start at such a path prints one line, serves, and stops quietly), CP-748 (each non-text byte is
written as a backslash, an x and two lowercase hex digits), CP-749 (valid text beside it stays),
CP-750 (the line is the same on every console encoding), CP-751 (a path with no such byte gives
the line it gave before), CP-752 (the strict UTF-8 start on saved data that does not exist yet),
CP-753 (a valid file wherever the file system can hold the directory, skipped on the file
system's own refusal), CP-754 (no strict console setting writes the four characters, never the raw
byte) and CP-755 (the first output is the address and then the location) are what each test names.
NFDR QC-11 (a test module names the rules and obligations it checks) and QC-55 (the first console
output is the address and then the location).

Every start runs as a child process read with a deadline, so a start that ends early or never
answers fails the test instead of hanging it. The expected path of every case is written out here
as bytes, independently of the code under test.
"""

from __future__ import annotations

import errno
import http.client
import os
import re
import select
import signal
import subprocess
import sys
import time
from collections.abc import Iterator, Mapping
from pathlib import Path

import pytest

import main

PRODUCT_ROOT = Path(main.__file__).resolve().parent
DEADLINE_SECONDS = 30
STOP_DEADLINE_SECONDS = 10
REAP_DEADLINE_SECONDS = 10
# The second argument of `main.start` is entered with the original path: the child decodes the
# bytes it is given the way the file system names them, whatever its own console is.
START_PROGRAM = (
    "import os, sys; from pathlib import Path; import main; "
    "sys.exit(main.start(('127.0.0.1', 0), Path(os.fsdecode(bytes.fromhex(sys.argv[1])))))"
)
READY_LINE = re.compile(
    rb"The tracker is running\. Open http://127\.0\.0\.1:(?P<port>[0-9]+) in your browser\. "
    rb"Saved data is kept at (?P<location>.+)\.\n"
)
EXPECTED_LINE = (
    b"The tracker is running. Open http://127.0.0.1:%d in your browser. Saved data is kept at %b.\n"
)
SAVED_PROJECT = (
    b'{"next_project_id": 2, "projects": [{"id": 1, "name": "Alpha", "description": ""}]}'
)
EMPTY_PAGE_TEXT = "There are no projects yet."
NAMED_PROJECT = "Alpha"
# What the child's console is told, once everything it could have inherited is taken away.
CONSOLE_VARIABLES = (
    "PYTHONIOENCODING",
    "PYTHONUTF8",
    "PYTHONCOERCECLOCALE",
    "LC_ALL",
    "LC_CTYPE",
    "LANG",
)
STRICT_UTF8 = {"PYTHONIOENCODING": "utf-8:strict"}
STRICT_ASCII = {"PYTHONIOENCODING": "ascii:strict"}
C_LOCALE = {"LC_ALL": "C", "PYTHONCOERCECLOCALE": "0"}
UTF8_MODE = {"PYTHONUTF8": "1", "LC_ALL": "C", "PYTHONCOERCECLOCALE": "0"}
# The errors a file system gives for a name it will not hold.
REFUSED_NAME_ERRNOS = (errno.EILSEQ, errno.EINVAL)


def child_environment(console: Mapping[str, str]) -> dict[str, str]:
    """The suite's environment with every console setting removed, then the named ones set."""
    environment = {
        name: value for name, value in os.environ.items() if name not in CONSOLE_VARIABLES
    }
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.update(console)
    return environment


class _Start:
    """A real `main.start` in its own interpreter, read with a deadline on every wait."""

    def __init__(self, location: Path, console: Mapping[str, str]) -> None:
        self.process = subprocess.Popen(
            [sys.executable, "-c", START_PROGRAM, os.fsencode(location).hex()],
            cwd=PRODUCT_ROOT,
            env=child_environment(console),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._pending = b""

    def first_line(self) -> bytes:
        """The first line on standard output, newline included; fails at once if the start ends."""
        assert self.process.stdout is not None
        descriptor = self.process.stdout.fileno()
        end = time.monotonic() + DEADLINE_SECONDS
        while b"\n" not in self._pending:
            if time.monotonic() >= end:
                self.close()
                raise AssertionError(f"no first line within {DEADLINE_SECONDS}s")
            if not select.select([descriptor], [], [], 0.2)[0]:
                continue
            chunk = os.read(descriptor, 4096)
            if not chunk:
                out, err = self.process.communicate(timeout=STOP_DEADLINE_SECONDS)
                raise AssertionError(
                    f"the start ended with status {self.process.returncode} before it served: "
                    f"stdout {self._pending + out!r}, stderr {err.decode(errors='replace')}"
                )
            self._pending += chunk
        line, newline, self._pending = self._pending.partition(b"\n")
        return line + newline

    def get(self, port: int) -> tuple[int, str]:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=DEADLINE_SECONDS)
        try:
            connection.request("GET", "/")
            response = connection.getresponse()
            return response.status, response.read().decode("utf-8")
        finally:
            connection.close()

    def stop(self) -> tuple[int, bytes, bytes]:
        """Ctrl-C, then the status, everything written after the first line, and standard error."""
        self.process.send_signal(signal.SIGINT)
        try:
            out, err = self.process.communicate(timeout=STOP_DEADLINE_SECONDS)
        except subprocess.TimeoutExpired:
            self.close()
            raise AssertionError("the start did not stop on Ctrl-C") from None
        return self.process.returncode, self._pending + out, err

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.kill()
        try:
            self.process.communicate(timeout=REAP_DEADLINE_SECONDS)
        except subprocess.TimeoutExpired:
            pass


class _Starts:
    """Starts trackers in child processes and ends any still running when the test is over."""

    def __init__(self) -> None:
        self._starts: list[_Start] = []

    def begin(self, location: Path, console: Mapping[str, str]) -> _Start:
        started = _Start(location, console)
        self._starts.append(started)
        return started

    def close(self) -> None:
        for started in self._starts:
            started.close()


@pytest.fixture
def starts() -> Iterator[_Starts]:
    started = _Starts()
    yield started
    started.close()


def serve_and_stop(
    starts: _Starts,
    directory: Path,
    folder: bytes,
    shown: bytes,
    console: Mapping[str, str],
    page_text: str = EMPTY_PAGE_TEXT,
) -> bytes:
    """Start at `directory`/`folder`, hold the whole ready line, serve, stop quietly.

    `shown` is the folder as the line must write it. The line is checked as raw bytes against a
    location built here from `shown`; the start's own formatter is never asked. Returns the line.
    """
    location = directory / os.fsdecode(folder)
    started = starts.begin(location, console)

    line = started.first_line()
    found = READY_LINE.fullmatch(line)
    assert found is not None, line
    port = int(found.group("port"))
    assert line == EXPECTED_LINE % (port, os.fsencode(directory) + b"/" + shown), line
    status, page = started.get(port)
    assert status == 200
    assert page_text in page
    assert started.stop() == (0, b"", b"")
    return line


@pytest.mark.parametrize("saved", ["missing-data", "valid-file"])
def test_readable_start_prints_non_text_path_and_serves(
    starts: _Starts, tmp_path: Path, saved: str
) -> None:
    """CP-747, CP-748, CP-752, CP-753, CP-755: a strict UTF-8 start at `caf\\xe9` prints the whole
    line with four literal characters, serves the printed address, and stops quietly. Missing data
    never skips; the valid file skips only on the file system's own refusal of the directory."""
    folder = b"caf\xe9"
    page_text = EMPTY_PAGE_TEXT
    if saved == "valid-file":
        directory = tmp_path / os.fsdecode(folder)
        try:
            directory.mkdir()
        except OSError as refusal:
            if refusal.errno not in REFUSED_NAME_ERRNOS:
                raise
            pytest.skip(f"the file system refused the directory name: {refusal}")
        (directory / "tracker.json").write_bytes(SAVED_PROJECT)
        page_text = NAMED_PROJECT
        before = (directory / "tracker.json").read_bytes()

    serve_and_stop(starts, tmp_path, folder, rb"caf\xe9", STRICT_UTF8, page_text)

    if saved == "valid-file":
        assert (tmp_path / os.fsdecode(folder) / "tracker.json").read_bytes() == before


@pytest.mark.parametrize(
    ("console", "folder", "shown"),
    [
        pytest.param(console, folder, shown, id=f"{name}-{label}")
        for name, console in (
            ("strict-ascii", STRICT_ASCII),
            ("c-locale", C_LOCALE),
            ("utf8-mode", UTF8_MODE),
        )
        for label, folder, shown in (
            ("one-byte", b"caf\xe9", rb"caf\xe9"),
            ("consecutive-bytes", b"a\xe9\xff", rb"a\xe9\xff"),
        )
    ],
)
def test_readable_start_path_is_independent_of_console_policy(
    starts: _Starts, tmp_path: Path, console: Mapping[str, str], folder: bytes, shown: bytes
) -> None:
    """CP-748, CP-750, CP-754: under a strict ASCII console, the C locale and Python's UTF-8
    mode, the start writes the same line, four characters for each byte, and never the raw byte,
    a replacement mark or the form `\\udce9`. It serves and stops quietly as under strict UTF-8."""
    line = serve_and_stop(starts, tmp_path, folder, shown, console)

    assert b"\xe9" not in line and b"\xff" not in line
    assert "�".encode() not in line
    assert b"udc" not in line


@pytest.mark.parametrize(
    ("folder", "shown"),
    [
        pytest.param(b"plain", b"plain", id="plain-text"),
        pytest.param("café".encode(), "café".encode(), id="valid-utf8"),
        pytest.param(rb"a\xe9b", rb"a\xe9b", id="real-backslash"),
        pytest.param(b"caf\xc3\xa9\xe9", "café".encode() + rb"\xe9", id="valid-text-and-byte"),
    ],
)
def test_readable_start_preserves_ordinary_and_mixed_paths(
    starts: _Starts, tmp_path: Path, folder: bytes, shown: bytes
) -> None:
    """CP-749, CP-751: on a strict UTF-8 console plain text, a valid `é` written as UTF-8 and a
    real backslash stay as they are; escaping the one non-text byte beside valid text leaves that
    text alone."""
    serve_and_stop(starts, tmp_path, folder, shown, STRICT_UTF8)
