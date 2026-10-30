"""Integration tests of an unreadable start whose saved-data path holds a byte that is not text
(layer 2), through real starts in child processes.

Checks SRS FR-1 (the start prints where to open the tracker and what happened, and serves until
Ctrl-C), FR-8 (the answer on saved data the tracker cannot read), NFR-3 (a stop leaves the saved
data as it was), NFR-4 (an unreadable start tells the person why) and AC-7 (the unreadable-data
answer). Change spec rules CP-757 (the first and only output is the one line, standard error stays
empty, Ctrl-C stops with status 0), CP-758 (every checked request is answered as on a path with
no such byte), CP-760 (each non-text byte is written as a backslash, an x and two lowercase hex
digits), CP-761 (a relative location is shown as one absolute path), CP-762 (the line is the same
on every console encoding), CP-764 (the saved data is never written, replaced or deleted),
CP-767 (the start beneath a regular file, which never skips), CP-768 (a directory really named
with the byte, skipped on the file system's own refusal) and CP-771 (the first console output is
the line) are what each test names. NFDR QC-11 (a test module names the rules and obligations it
checks), QC-51 (an unreadable start changes nothing) and QC-61 (no operating-system check in a
skip).

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
# The location is entered with the original path: the child decodes the bytes it is given the way
# the file system names them, whatever its own console is.
START_PROGRAM = (
    "import os, sys; from pathlib import Path; import main; "
    "sys.exit(main.start(('127.0.0.1', 0), Path(os.fsdecode(bytes.fromhex(sys.argv[1])))))"
)
PORT_IN_LINE = re.compile(rb"Open http://127\.0\.0\.1:(?P<port>[0-9]+) in your browser")
UNREADABLE_BYTES = b"{ this is not saved data"
REGULAR_FILE_BYTES = b"not a directory"
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


def expected_line(shown: bytes, port: int) -> bytes:
    """The whole line as bytes, with `shown` as the location the line must write."""
    return (
        b"The tracker couldn't read its saved data at " + shown + b", and nothing in it was "
        b"changed. Open http://127.0.0.1:" + str(port).encode() + b" in your browser to read this "
        b"on a page. To start fresh on purpose, follow Setting saved data aside in the setup "
        b"instructions.\n"
    )


def expected_paragraph(shown: str) -> bytes:
    """The page's sentences as served, with `shown` as the location the page must write."""
    return (
        f"The tracker couldn't read its saved data, which is kept at {shown}. "
        "Nothing in it was changed or overwritten. To start fresh on purpose, "
        "follow Setting saved data aside in the setup instructions."
    ).encode()


def child_environment(console: Mapping[str, str]) -> dict[str, str]:
    """The suite's environment with every console setting removed, then the named ones set."""
    environment = {
        name: value for name, value in os.environ.items() if name not in CONSOLE_VARIABLES
    }
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(PRODUCT_ROOT)
    environment.update(console)
    return environment


class _Start:
    """A real `main.start` in its own interpreter, read with a deadline on every wait."""

    def __init__(self, location: Path, console: Mapping[str, str], cwd: Path) -> None:
        self.process = subprocess.Popen(
            [sys.executable, "-c", START_PROGRAM, os.fsencode(location).hex()],
            cwd=cwd,
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

    def request(
        self, port: int, method: str, target: str, headers: Mapping[str, str] | None = None
    ) -> tuple[int, Mapping[str, str], bytes]:
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=DEADLINE_SECONDS)
        try:
            connection.request(
                method, target, body=b"" if method == "POST" else None, headers=dict(headers or {})
            )
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
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

    def begin(self, location: Path, console: Mapping[str, str], cwd: Path = PRODUCT_ROOT) -> _Start:
        started = _Start(location, console, cwd)
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


def listing(directory: Path) -> list[str]:
    return sorted(entry.name for entry in directory.iterdir())


def regular_file(directory: Path) -> Path:
    """A regular file in test-owned storage: a location beneath it cannot be read as saved data."""
    file = directory / "afile"
    file.write_bytes(REGULAR_FILE_BYTES)
    return file


def check_unreadable_start(started: _Start, shown: bytes, page_location: str) -> bytes:
    """Hold the complete first line as bytes, serve the page it names, stop quietly.

    `shown` is the location as the line must write it, built here and never by the start's own
    formatter; `page_location` is the same text for the page. Returns the line.
    """
    line = started.first_line()
    found = PORT_IN_LINE.search(line)
    assert found is not None, line
    port = int(found.group("port"))
    assert line == expected_line(shown, port), line
    status, headers, body = started.request(port, "GET", "/")
    assert status == 503
    assert headers["Cache-Control"] == "no-store"
    assert expected_paragraph(page_location) in body
    page = body.decode("utf-8")
    assert "�" not in page
    assert not any(0xDC80 <= ord(character) <= 0xDCFF for character in page)
    assert started.stop() == (0, b"", b"")
    return line


def test_unreadable_start_prints_then_serves_and_stops(starts: _Starts, tmp_path: Path) -> None:
    """CP-757, CP-758, CP-760, CP-764, CP-767, CP-771: under a strict UTF-8 console a start at a
    location holding the byte, beneath a regular file, prints the whole line as its first and only
    output, serves the one page on every address, answers the stylesheet and the same-origin POST
    as on any path, stops on Ctrl-C with status 0 and nothing more written, and leaves the file
    and its directory as they were. This case never skips."""
    file = regular_file(tmp_path)
    before = (file.read_bytes(), listing(tmp_path))
    location = file / os.fsdecode(b"caf\xe9")
    started = starts.begin(location, STRICT_UTF8)

    line = started.first_line()
    found = PORT_IN_LINE.search(line)
    assert found is not None, line
    port = int(found.group("port"))
    shown = os.fsencode(tmp_path) + rb"/afile/caf\xe9"
    assert line == expected_line(shown, port), line
    page_location = os.fsdecode(shown)
    page = started.request(port, "GET", "/")
    assert page[0] == 503
    assert page[1]["Cache-Control"] == "no-store"
    assert expected_paragraph(page_location) in page[2]
    served = page[2].decode("utf-8")
    assert "�" not in served
    assert not any(0xDC80 <= ord(character) <= 0xDCFF for character in served)
    for target in ("/people", "/nothing?x=1", "/?x=1"):
        status, headers, body = started.request(port, "GET", target)
        assert (status, body) == (503, page[2]), target
        assert headers["Cache-Control"] == "no-store"
    status, _, _ = started.request(port, "GET", "/style.css")
    assert status == 200
    status, headers, _ = started.request(
        port, "POST", "/projects", {"Sec-Fetch-Site": "same-origin"}
    )
    assert (status, headers["Location"]) == (303, "/")
    assert started.stop() == (0, b"", b"")

    assert (file.read_bytes(), listing(tmp_path)) == before


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
def test_unreadable_start_is_independent_of_console_encoding(
    starts: _Starts, tmp_path: Path, console: Mapping[str, str], folder: bytes, shown: bytes
) -> None:
    """CP-757, CP-760, CP-762, CP-767: under a strict ASCII console, the C locale and Python's
    UTF-8 mode, the start beneath a regular file writes the same line, four characters for each
    byte and never the raw byte, serves the same page, and stops quietly."""
    file = regular_file(tmp_path)
    started = starts.begin(file / os.fsdecode(folder), console)
    expected = os.fsencode(tmp_path) + b"/afile/" + shown

    line = check_unreadable_start(started, expected, os.fsdecode(expected))

    assert b"\xe9" not in line and b"\xff" not in line
    assert "�".encode() not in line
    assert b"\\udc" not in line
    assert file.read_bytes() == REGULAR_FILE_BYTES


def test_unreadable_start_preserves_a_real_byte_named_saved_file(
    starts: _Starts, tmp_path: Path
) -> None:
    """CP-764, CP-768: in a directory really named with the byte, a `tracker.json` the tracker
    cannot read is shown in the same form, left byte for byte, and no directory named with the
    four-character spelling appears. Only the file system's own refusal of the directory name
    skips it; any other setup failure fails."""
    directory = tmp_path / os.fsdecode(b"caf\xe9")
    try:
        directory.mkdir()
    except OSError as refusal:
        if refusal.errno not in REFUSED_NAME_ERRNOS:
            raise
        pytest.skip(f"the file system refused the directory name: {refusal}")
    saved = directory / "tracker.json"
    saved.write_bytes(UNREADABLE_BYTES)
    before = (saved.read_bytes(), listing(directory), listing(tmp_path))
    started = starts.begin(directory, STRICT_UTF8)
    shown = os.fsencode(tmp_path) + rb"/caf\xe9"

    check_unreadable_start(started, shown, os.fsdecode(shown))

    assert (saved.read_bytes(), listing(directory), listing(tmp_path)) == before
    assert not (tmp_path / r"caf\xe9").exists()


def test_unreadable_relative_byte_path_is_shown_as_one_absolute_path(
    starts: _Starts, tmp_path: Path
) -> None:
    """CP-761, CP-764: a relative location holding the byte, beneath a regular file, is shown on
    the line and on the page as one absolute path in the same form; the file and its directory are
    as they were and no directory with the escape spelling is made."""
    root = tmp_path.resolve()
    file = regular_file(root)
    before = (file.read_bytes(), listing(root))
    location = Path("afile") / os.fsdecode(b"caf\xe9")
    started = starts.begin(location, STRICT_UTF8, cwd=root)
    shown = os.fsencode(root) + rb"/afile/caf\xe9"

    check_unreadable_start(started, shown, os.fsdecode(shown))

    assert (file.read_bytes(), listing(root)) == before
    assert not (root / r"afile/caf\xe9").exists()
