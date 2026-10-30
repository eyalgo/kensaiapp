"""Integration tests of the start: unreadable saved data served as one page, a held address and the
data directory, through real starts in child processes.

Checks SRS NFR-3 and AC-16 (a start whose location cannot be read, or whose address is held,
releases the location it claimed; a location that is no directory serves the unreadable page), by
change spec rules CP-700, CP-701 and CP-702.

Checks SRS FR-1 (the start prints where to open the tracker and where the data is), FR-3 (a start
whose address something else holds says so in one line), FR-4 and AC-7 (unreadable saved data is
served as one page, left as it was, and points to the setup instructions in README.md), AC-8 (after
the data is set aside the next start is empty), DR-4 (the assignee list), DR-2 (the task rules),
DR-6 and FR-23 (a saved label breaking the label rules) and DR-5 (a saved operator name breaking
the name rule, or not text) and DR-6 and FR-28 (a saved comment breaking a comment rule). Change
spec rules CP-710 to CP-715, CP-724 to CP-726, CP-728, CP-729, CP-732 and CP-734 and the earlier
CP-5, CP-39 to CP-46, CP-55, CP-137, CP-197, CP-205, CP-227, CP-228, CP-233, CP-264, CP-265 and
CP-270 and NFDR QC-47 and QC-58 are the ones each test names. Every unreadable start runs as a
child process read with a deadline, so a start that exits early or never answers fails the test
instead of hanging it.
"""

from __future__ import annotations

import html
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
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any

import pytest

import main
from application import Tracker
from domain import empty_state
from persistence import SavedData, UnreadableData
from web import AddressTaken

PRODUCT_ROOT = Path(main.__file__).resolve().parent
AGAIN_SECTION = "Starting the tracker again"
UNREADABLE = b'{"next_project_id": 3, "projects": [ truncated'
SET_ASIDE_SECTION = "Setting saved data aside"
CLOSING_SENTENCE = (
    f"To start fresh on purpose, follow {SET_ASIDE_SECTION} in the setup instructions."
)
ANNOUNCEMENT_LINE = (
    "The tracker couldn't read its saved data at {location}, and nothing in it was changed. "
    "Open http://127.0.0.1:{port} in your browser to read this on a page. " + CLOSING_SENTENCE
)
READY_LINE = (
    "The tracker is running. Open http://127.0.0.1:{port} in your browser. "
    "Saved data is kept at {location}."
)
FORM_HEADERS = {
    "Sec-Fetch-Site": "same-origin",
    "Content-Type": "application/x-www-form-urlencoded",
}
PAGE_CONTROLS = re.compile(r"<(?:a|form|button|input|select|textarea|nav)[\s>/]", re.IGNORECASE)
DEADLINE_SECONDS = 30
REFUSAL_DEADLINE_SECONDS = 10
SERVE_PROGRAM = (
    "import sys; from pathlib import Path; import main; "
    "sys.exit(main.start(('127.0.0.1', int(sys.argv[2])), Path(sys.argv[1])))"
)
# The same start with an audit hook that notes any outbound connection the server process makes.
AUDITED_PROGRAM = """
import sys
from pathlib import Path
import main

marker = Path(sys.argv[3])

def audit(event, args):
    if event == "socket.connect":
        marker.write_text("connected")

sys.addaudithook(audit)
sys.exit(main.start(('127.0.0.1', int(sys.argv[2])), Path(sys.argv[1])))
"""
_FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")
_ATX_HEADING = re.compile(r"#{1,6} (.*)")


def _listing(directory: Path) -> list[str]:
    return sorted(str(path.relative_to(directory)) for path in directory.rglob("*"))


def _snapshot(directory: Path) -> dict[str, bytes | None]:
    """Every path under the directory with the bytes of each file."""
    return {
        str(path.relative_to(directory)): path.read_bytes() if path.is_file() else None
        for path in sorted(directory.rglob("*"))
    }


def announcement(location: Path, port: int) -> str:
    """The one line an unreadable start writes, for the location as the start shows it."""
    return ANNOUNCEMENT_LINE.format(location=location.absolute(), port=port)


class _Child:
    """A real `main.start` in its own interpreter, read with a deadline on every wait."""

    def __init__(self, location: Path, port: int, program: str, *extra: str) -> None:
        self.process = subprocess.Popen(
            [sys.executable, "-c", program, str(location), str(port), *extra],
            cwd=PRODUCT_ROOT,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self._pending = b""
        self.port = port
        self.first_line = ""

    def read_first_line(self) -> None:
        """Wait for the first line on standard output; fail at once if the start ends first."""
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
                out, err = self.process.communicate(timeout=REFUSAL_DEADLINE_SECONDS)
                raise AssertionError(
                    f"the start ended with status {self.process.returncode} before it served: "
                    f"stdout {(self._pending + out)!r}, stderr {err!r}"
                )
            self._pending += chunk
        line, _, self._pending = self._pending.partition(b"\n")
        self.first_line = line.decode("utf-8")
        found = re.search(r"http://127\.0\.0\.1:(\d+)", self.first_line)
        assert found is not None, self.first_line
        self.port = int(found.group(1))

    def request(
        self,
        method: str,
        target: str = "/",
        headers: Mapping[str, str] | None = None,
        body: bytes | None = None,
    ) -> tuple[int, dict[str, str], bytes]:
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=DEADLINE_SECONDS)
        try:
            connection.request(method, target, body, dict(headers or {}))
            response = connection.getresponse()
            names = {name.lower(): value for name, value in response.getheaders()}
            return response.status, names, response.read()
        finally:
            connection.close()

    def finish(self, deadline: int = REFUSAL_DEADLINE_SECONDS) -> tuple[int, str, str]:
        """Wait for the start to end by itself: status, everything after the first line, stderr."""
        try:
            out, err = self.process.communicate(timeout=deadline)
        except subprocess.TimeoutExpired:
            self.close()
            raise AssertionError("the start kept running: it served instead of ending") from None
        return self.process.returncode, (self._pending + out).decode(), err.decode()

    def stop(self) -> tuple[int, str, str]:
        """Ctrl-C, then status, everything written after the first line, and stderr."""
        self.process.send_signal(signal.SIGINT)
        return self.finish(DEADLINE_SECONDS)

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.kill()
        self.process.communicate()


class _Starts:
    """Starts trackers in child processes and ends any still running when the test is over."""

    def __init__(self) -> None:
        self._children: list[_Child] = []

    def serve(
        self, location: Path, port: int = 0, program: str = SERVE_PROGRAM, *extra: str
    ) -> _Child:
        """A start that must answer: returns once its first line is read."""
        child = _Child(location, port, program, *extra)
        self._children.append(child)
        child.read_first_line()
        return child

    def refused(self, location: Path, port: int) -> tuple[int, str, str]:
        """A start that must end by itself: its status, standard output and standard error."""
        child = _Child(location, port, SERVE_PROGRAM)
        self._children.append(child)
        return child.finish()

    def close(self) -> None:
        for child in self._children:
            child.close()


@pytest.fixture
def starts() -> Iterator[_Starts]:
    started = _Starts()
    yield started
    started.close()


def _serves_the_page(starts: _Starts, location: Path, content: bytes) -> None:
    """A start on content the tracker cannot read, on a free port, serves the unreadable page.

    The data is independently unreadable, the first line is the announcement, the page is a 503
    naming the heading, and the location's bytes and listing are as they were after a quiet stop.
    """
    saved = location / "tracker.json"
    saved.write_bytes(content)
    before = _listing(location)
    with pytest.raises(UnreadableData) as error:
        SavedData(location).load()
    assert error.value.location == location

    served = starts.serve(location)

    assert served.first_line == announcement(location, served.port)
    status, _, body = served.request("GET", "/")
    assert status == 503
    assert "The saved data can't be read" in html.unescape(body.decode("utf-8"))
    assert served.stop() == (0, "", "")
    assert saved.read_bytes() == content and _listing(location) == before


def test_an_unreadable_start_serves_one_page_and_announces_once(
    starts: _Starts, tmp_path: Path
) -> None:
    """CP-710, CP-711, CP-729: the start stays up, its first line is the one approved line, the
    port is the one it bound, and the same page answers the root, a real route and an unknown
    one."""
    (tmp_path / "tracker.json").write_bytes(UNREADABLE)
    before = _listing(tmp_path)

    served = starts.serve(tmp_path)

    assert served.port != 0
    assert served.first_line == announcement(tmp_path, served.port)
    answers = [served.request("GET", target) for target in ("/", "/people", "/nothing?x=1")]
    assert {status for status, _, _ in answers} == {503}
    assert len({body for _, _, body in answers}) == 1
    page = answers[0][2].decode("utf-8")
    assert PAGE_CONTROLS.search(page) is None
    assert str(tmp_path.absolute()) in html.unescape(page)
    assert served.stop() == (0, "", "")
    assert _listing(tmp_path) == before


def test_an_unreadable_start_changes_nothing_in_the_location(
    starts: _Starts, tmp_path: Path
) -> None:
    """CP-710, CP-725: every byte of the file, and the directory's listing, are as they were."""
    saved = tmp_path / "tracker.json"
    saved.write_bytes(UNREADABLE)
    before = _listing(tmp_path)
    served = starts.serve(tmp_path)
    assert served.request("GET", "/")[0] == 503
    assert served.stop()[0] == 0
    assert saved.read_bytes() == UNREADABLE
    assert _listing(tmp_path) == before


INVALID_FILES = {
    "empty": b"",
    "not-utf8": b"\xff\xfe\x00",
    "missing-key": b'{"next_project_id": 1}',
    "wrong-shape": b"[]",
}

INVALID_ASSIGNEES: dict[str, object] = {
    "empty-name": ["Dana", ""],
    "whitespace-name": ["Dana", "   "],
    "duplicate": ["Dana", "Ari", "Dana"],
    "name-201-characters": ["n" * 201],
    "number-member": ["Dana", 7],
    "null": None,
    "scalar-text": "Dana",
    "mapping": {"Dana": 1},
}


def _assignee_document(assignees: object) -> bytes:
    return json.dumps(
        {
            "next_project_id": 2,
            "projects": [{"id": 1, "name": "Alpha", "description": ""}],
            "assignees": assignees,
        }
    ).encode()


def test_the_announcement_quotes_a_heading_the_readme_has(starts: _Starts, tmp_path: Path) -> None:
    """CP-711, CP-734: the section the announcement names is a heading README.md has."""
    (tmp_path / "tracker.json").write_bytes(UNREADABLE)
    served = starts.serve(tmp_path)
    assert served.first_line.endswith(CLOSING_SENTENCE)
    assert served.stop()[0] == 0
    assert SET_ASIDE_SECTION in _readme_headings()


def _headings(markdown: str) -> list[str]:
    """Every ATX heading line of a Markdown text, any level, its `#` run and one space removed.

    A line inside a fenced code block is code, so it is skipped. A fence closes on a line of its
    own character at least as long as the one that opened it.
    """
    headings = []
    fence = ""
    for line in markdown.splitlines():
        if fence:
            marker = line.strip()
            if marker.startswith(fence) and marker == fence[0] * len(marker):
                fence = ""
            continue
        opening = _FENCE.match(line)
        if opening:
            fence = opening.group(1)
            continue
        heading = _ATX_HEADING.fullmatch(line)
        if heading:
            headings.append(heading.group(1))
    return headings


def _readme_headings() -> list[str]:
    """Every heading of README.md, read by `_headings`."""
    return _headings((PRODUCT_ROOT / "README.md").read_text(encoding="utf-8"))


def test_the_heading_reader_counts_a_heading_and_no_other_line() -> None:
    """CP-55, CP-67: a line that only looks like a heading must not stand in for a missing one.

    The README's command blocks are fenced code, where a `#` line is a shell comment; seven `#`
    and no space after the run are not ATX headings either. Any of them counted as a heading would
    let the CP-67 test pass on a README whose real heading was reworded.
    """
    markdown = (
        "# Title\n"
        "```\n"
        "# Setting saved data aside\n"
        "```\n"
        "~~~~\n"
        "## Starting the tracker again\n"
        "```\n"
        "~~~~\n"
        "####### Setting saved data aside\n"
        "#Setting saved data aside\n"
        "### Setting saved data aside again\n"
        "### Real heading\n"
    )
    assert _headings(markdown) == ["Title", "Setting saved data aside again", "Real heading"]


def test_the_readme_has_both_fixed_headings() -> None:
    """CP-55: the two sections other text points to keep their names."""
    headings = _readme_headings()
    assert AGAIN_SECTION in headings
    assert SET_ASIDE_SECTION in headings


def test_data_is_ignored_by_version_control() -> None:
    """CP-5, QC-47: run from the product root."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", "data/tracker.json"], cwd=PRODUCT_ROOT, check=False
    )
    assert result.returncode == 0


HELD_ANSWER = b"held"
ADDRESS_TAKEN_LINE = (
    "The tracker didn't start, because something else is already using the address {address}. "
    "Stop that program, then start the tracker again."
)


@pytest.fixture
def holder() -> Iterator[socket.socket]:
    """Another program's listening socket on a free loopback port; it answers one connection."""
    held = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    held.bind(("127.0.0.1", 0))
    held.listen()
    try:
        yield held
    finally:
        held.close()


def _holder_still_answers(held: socket.socket) -> bool:
    def serve_one() -> None:
        connection, _ = held.accept()
        with connection:
            connection.sendall(HELD_ANSWER)

    thread = threading.Thread(target=serve_one, daemon=True)
    thread.start()
    with socket.create_connection(held.getsockname(), timeout=10) as connection:
        answer = connection.recv(16)
    thread.join(timeout=10)
    return answer == HELD_ANSWER


def test_a_start_with_a_held_address_prints_the_one_line_and_changes_nothing(
    tmp_path: Path, holder: socket.socket, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-39, CP-40, CP-41: one plain line on standard error, nothing on standard output."""
    host, port = holder.getsockname()
    status = main.start((host, port), tmp_path / "data")
    captured = capsys.readouterr()
    assert status != 0
    assert captured.out == ""
    assert captured.err == ADDRESS_TAKEN_LINE.format(address=f"{host}:{port}") + "\n"
    assert "Traceback" not in captured.err
    assert not (tmp_path / "data").exists()
    assert _holder_still_answers(holder)


def test_a_start_on_another_port_names_that_port(
    tmp_path: Path, holder: socket.socket, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-40, Gap 3: the line names the address the start was given, never the fixed 8017."""
    port = holder.getsockname()[1]
    assert port != 8017
    assert main.start(("127.0.0.1", port), tmp_path / "data") != 0
    err = capsys.readouterr().err
    assert f"127.0.0.1:{port}" in err
    assert "8017" not in err


def test_a_held_address_leaves_existing_saved_data_untouched(
    tmp_path: Path, holder: socket.socket, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-41: the file's bytes and the directory's listing are as they were."""
    saved_data = SavedData(tmp_path)
    tracker = Tracker(empty_state(), saved_data, main.SystemClock())
    tracker.create_project("Alpha", "")
    saved = tmp_path / "tracker.json"
    before_bytes, before_listing = saved.read_bytes(), _listing(tmp_path)
    host, port = holder.getsockname()
    assert main.start((host, port), tmp_path) != 0
    assert saved.read_bytes() == before_bytes
    assert _listing(tmp_path) == before_listing
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ADDRESS_TAKEN_LINE.format(address=f"{host}:{port}") + "\n"


def test_a_held_address_wins_on_an_unreadable_start(
    starts: _Starts, tmp_path: Path, holder: socket.socket
) -> None:
    """CP-714, CP-732: the address-taken line only, status 1, no announcement, nothing changed,
    and the released address then serves the page."""
    saved = tmp_path / "tracker.json"
    saved.write_bytes(UNREADABLE)
    before = _listing(tmp_path)
    host, port = holder.getsockname()

    status, out, err = starts.refused(tmp_path, port)

    assert (status, out) == (1, "")
    assert err == ADDRESS_TAKEN_LINE.format(address=f"{host}:{port}") + "\n"
    assert "couldn't read" not in err and "http://" not in err
    assert saved.read_bytes() == UNREADABLE and _listing(tmp_path) == before
    holder.close()
    served = starts.serve(tmp_path, port)
    assert served.first_line == announcement(tmp_path, port)
    assert served.request("GET", "/")[0] == 503
    assert served.stop() == (0, "", "")


def test_an_unrelated_bind_error_on_unreadable_data_propagates_without_a_line(
    starts: _Starts, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-714: another bind failure is not told the address is taken and announces nothing; the
    location it claimed is free for the next start."""
    saved = tmp_path / "tracker.json"
    saved.write_bytes(UNREADABLE)
    before = _listing(tmp_path)
    with pytest.raises(OSError) as caught:
        main.start(("192.0.2.1", 0), tmp_path)
    assert not isinstance(caught.value, AddressTaken)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "already using the address" not in captured.err
    assert "couldn't read" not in captured.err
    assert saved.read_bytes() == UNREADABLE and _listing(tmp_path) == before
    served = starts.serve(tmp_path)
    assert served.request("GET", "/")[0] == 503
    assert served.stop()[0] == 0


def test_a_start_refused_the_address_for_another_reason_is_not_told_it_is_taken(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-42, Gap 5: another bind failure propagates as before; the address message never shows."""
    with pytest.raises(OSError) as caught:
        main.start(("192.0.2.1", 0), tmp_path / "data")
    assert not isinstance(caught.value, AddressTaken)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "already using the address" not in captured.err
    assert not (tmp_path / "data").exists()


TASK_BASE: dict[str, object] = {
    "id": 1,
    "project_id": 1,
    "title": "Plan",
    "status": "todo",
    "priority": "medium",
    "assignee": None,
    "labels": [],
    "due_date": None,
    "created_at": "2026-10-11T09:30:00Z",
    "comments": [],
}
TASK_BREAKS: dict[str, dict[str, object]] = {
    "unknown-priority": {"priority": "urgent"},
    "unknown-status": {"status": "started"},
    "unknown-project": {"project_id": 9},
    "impossible-date": {"due_date": "2026-02-30"},
    "blank-title": {"title": "  "},
    "long-title": {"title": "t" * 201},
    "blank-assignee": {"assignee": " "},
    "identity-not-yet-issued": {"id": 2},
}


def _task_break_document(change: dict[str, object]) -> bytes:
    return json.dumps(
        {
            "next_project_id": 2,
            "projects": [{"id": 1, "name": "Alpha", "description": ""}],
            "assignees": [],
            "next_task_id": 2,
            "tasks": [{**TASK_BASE, **change}],
        }
    ).encode()


DR6_BREAKS = {
    "cannot-read-all-of-it": UNREADABLE,
    "unknown-status": _task_break_document({"status": "started"}),
    "unknown-priority": _task_break_document({"priority": "urgent"}),
    "task-without-its-project": _task_break_document({"project_id": 9}),
    "duplicate-project-name": json.dumps(
        {
            "next_project_id": 3,
            "projects": [
                {"id": 1, "name": "Alpha", "description": ""},
                {"id": 2, "name": "Alpha", "description": ""},
            ],
        }
    ).encode(),
    "reused-task-identity": json.dumps(
        {
            "next_project_id": 2,
            "projects": [{"id": 1, "name": "Alpha", "description": ""}],
            "assignees": [],
            "next_task_id": 2,
            "tasks": [TASK_BASE, {**TASK_BASE, "title": "Other"}],
        }
    ).encode(),
    "overlong-saved-field": _task_break_document({"title": "t" * 201}),
}


@pytest.mark.parametrize("content", list(DR6_BREAKS.values()), ids=list(DR6_BREAKS))
def test_each_dr6_break_serves_without_changing_saved_data(
    starts: _Starts, tmp_path: Path, content: bytes
) -> None:
    """CP-728, CP-725: each kind of break SRS DR-6 names reaches a real 503 page and leaves the
    file's bytes and the location's listing as they were, through the stop."""
    _serves_the_page(starts, tmp_path, content)


def _task_with_labels(identity: int, labels: list[str]) -> dict[str, object]:
    return {
        "id": identity,
        "project_id": 1,
        "title": f"Task {identity}",
        "status": "todo",
        "priority": "medium",
        "assignee": None,
        "labels": labels,
        "due_date": None,
        "created_at": "2026-10-11T09:30:00Z",
        "comments": [],
    }


INVALID_LABELS = {
    "empty-label": [""],
    "label-201-code-points": ["x" * 201],
    "repeated-label": ["bug", "ui", "bug"],
}


def _label_document(labels: list[str]) -> bytes:
    """A valid task before the break, so the load that refuses it has loaded nothing."""
    return json.dumps(
        {
            "next_project_id": 2,
            "projects": [{"id": 1, "name": "Alpha", "description": ""}],
            "assignees": [],
            "next_task_id": 3,
            "tasks": [_task_with_labels(1, ["bug"]), _task_with_labels(2, labels)],
        }
    ).encode()


# --- The operator name at start (SRS DR-5, DR-6; change spec CP-227, CP-228, CP-233) ---

NAME_PROJECT = {"id": 1, "name": "Alpha", "description": "x"}
NAME_TASK = {**_task_with_labels(1, ["bug"]), "assignee": "Dana"}
NAME_DOCUMENT = {
    "next_project_id": 2,
    "projects": [NAME_PROJECT],
    "assignees": ["Dana"],
    "next_task_id": 2,
    "tasks": [NAME_TASK],
}
RUN_START = (
    "import sys; from pathlib import Path; import main; "
    "sys.exit(main.start(('127.0.0.1', 0), Path(sys.argv[1])))"
)


def _name_document(**changes: object) -> bytes:
    return json.dumps({**NAME_DOCUMENT, "operator_name": None, **changes}).encode("utf-8")


def _run_real_start(location: Path) -> tuple[int, bytes]:
    """Start the product's own `main.start` in a child process on a free port, wait for its ready
    line, stop it as Ctrl-C does, and return its exit status and what it wrote to standard error."""
    child = subprocess.Popen(
        [sys.executable, "-c", RUN_START, str(location)],
        cwd=PRODUCT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        assert child.stdout is not None
        ready = child.stdout.readline().decode("utf-8")
        assert ready.startswith("The tracker is running. Open http://127.0.0.1:"), ready
        child.send_signal(signal.SIGINT)
        _, errors = child.communicate(timeout=30)
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate()
    return child.returncode, errors


@pytest.mark.parametrize("keys", [0, 1, 2], ids=["projects-only", "with-assignees", "with-tasks"])
def test_start_reads_each_legacy_form_with_every_existing_value(tmp_path: Path, keys: int) -> None:
    """CP-227, CP-233: each older form starts, keeps its values, and the load rewrites nothing."""
    document = {k: NAME_DOCUMENT[k] for k in ("next_project_id", "projects")}
    if keys >= 1:
        document["assignees"] = NAME_DOCUMENT["assignees"]
    if keys >= 2:
        document["next_task_id"], document["tasks"] = NAME_DOCUMENT["next_task_id"], [NAME_TASK]
    content = json.dumps(document).encode("utf-8")
    saved = tmp_path / "tracker.json"
    saved.write_bytes(content)
    before = _listing(tmp_path)

    state = SavedData(tmp_path).load()
    assert state is not None and state.operator_name is None
    assert [project.name for project in state.projects] == ["Alpha"]
    assert state.assignees == (("Dana",) if keys >= 1 else ())
    assert [(task.title, task.labels) for task in state.tasks] == (
        [("Task 1", ("bug",))] if keys >= 2 else []
    )
    assert state.next_task_id == (2 if keys >= 2 else 1)

    status, errors = _run_real_start(tmp_path)

    assert (status, errors) == (0, b"")
    assert saved.read_bytes() == content and _listing(tmp_path) == before


@pytest.mark.parametrize(
    "value",
    [None, "a" * 199 + chr(0x1F600), "  Sam  "],
    ids=["null", "200-code-points", "surrounded-by-spaces"],
)
def test_start_reads_valid_unset_boundary_and_surrounded_name(
    tmp_path: Path, value: object
) -> None:
    """CP-228, CP-233: null, a name of exactly 200 code points and a space-surrounded name start
    through the real start path, which loads them as given and writes nothing."""
    content = _name_document(operator_name=value)
    saved = tmp_path / "tracker.json"
    saved.write_bytes(content)
    before = _listing(tmp_path)

    state = SavedData(tmp_path).load()
    assert state is not None and state.operator_name == value
    assert state.assignees == ("Dana",) and [task.title for task in state.tasks] == ["Task 1"]

    status, errors = _run_real_start(tmp_path)

    assert (status, errors) == (0, b"")
    assert saved.read_bytes() == content and _listing(tmp_path) == before


# --- Saved comments at start (SRS DR-6, FR-28; change spec CP-264, CP-265, CP-270) ---

COMMENT_AT = "2026-10-11T09:30:00Z"
NON_BMP_CHARACTER = chr(0x1F600)
TEXT_AT_MAXIMUM = "t" * 3999 + NON_BMP_CHARACTER
AUTHOR_AT_MAXIMUM = "a" * 199 + NON_BMP_CHARACTER


def _comment(**changes: object) -> dict[str, object]:
    return {"text": "Seen", "author": "Dana", "created_at": COMMENT_AT, **changes}


def _comment_document(comments: list[dict[str, object]], **changes: object) -> bytes:
    """The saved document of NAME_DOCUMENT with the task's comments replaced."""
    task = {**NAME_TASK, "comments": comments}
    return json.dumps({**NAME_DOCUMENT, "tasks": [task], "operator_name": "Sam", **changes}).encode(
        "utf-8"
    )


INVALID_OPERATOR_NAMES: dict[str, object] = {
    "empty": "",
    "whitespace": "   ",
    "overlong": "n" * 201,
    "numeric": 7,
}
INVALID_COMMENTS = {
    "blank-text": _comment(text=""),
    "whitespace-text": _comment(text=" \n\t 　 \n"),
    "overlong-text": _comment(text="t" * 4001),
    "blank-author": _comment(author=""),
    "whitespace-author": _comment(author="  　"),
    "overlong-author": _comment(author="a" * 201),
}
OTHER_INVALID: dict[str, bytes] = {
    **{f"file-{name}": content for name, content in INVALID_FILES.items()},
    **{f"assignees-{name}": _assignee_document(v) for name, v in INVALID_ASSIGNEES.items()},
    **{f"task-{name}": _task_break_document(change) for name, change in TASK_BREAKS.items()},
    **{f"labels-{name}": _label_document(labels) for name, labels in INVALID_LABELS.items()},
    **{
        f"operator-name-{name}": _name_document(operator_name=v)
        for name, v in INVALID_OPERATOR_NAMES.items()
    },
    **{
        f"comment-{name}": _comment_document([_comment(), c])
        for name, c in INVALID_COMMENTS.items()
    },
}


@pytest.mark.parametrize("content", list(OTHER_INVALID.values()), ids=list(OTHER_INVALID))
def test_other_invalid_saved_values_serve_without_changing_data(
    starts: _Starts, tmp_path: Path, content: bytes
) -> None:
    """CP-710, CP-732, CP-264, CP-270: each saved value that breaks a data rule, and each file the
    tracker cannot read, is refused whole by the load and served as the page on a free port, with
    the bytes and listing as they were."""
    _serves_the_page(starts, tmp_path, content)


@pytest.mark.parametrize(
    ("operator_name", "comments"),
    [
        pytest.param(
            "Sam",
            [
                _comment(text=TEXT_AT_MAXIMUM, author=AUTHOR_AT_MAXIMUM),
                _comment(author="Nobody Now"),
            ],
            id="maxima-and-an-author-other-than-the-saved-name",
        ),
        pytest.param(None, [_comment(), _comment(text="Again", author="Lee")], id="no-saved-name"),
    ],
)
def test_saved_comment_boundaries_and_historical_authors_load(
    tmp_path: Path, operator_name: str | None, comments: list[dict[str, object]]
) -> None:
    """CP-264, CP-270: exact maxima counted in code points, an author other than the saved name and
    comments with no saved name load, start through the real start path and write nothing."""
    content = _comment_document(comments, operator_name=operator_name)
    saved = tmp_path / "tracker.json"
    saved.write_bytes(content)
    before = _listing(tmp_path)

    state = SavedData(tmp_path).load()

    assert state is not None and state.operator_name == operator_name
    loaded = state.tasks[0].comments
    assert [(comment.text, comment.author) for comment in loaded] == [
        (str(comment["text"]), str(comment["author"])) for comment in comments
    ]
    status, errors = _run_real_start(tmp_path)
    assert (status, errors) == (0, b"")
    assert saved.read_bytes() == content and _listing(tmp_path) == before


def _saved_forms() -> list[Any]:
    """The four forms of saved data the tracker reads, each holding a comment where it has tasks."""
    base = {k: NAME_DOCUMENT[k] for k in ("next_project_id", "projects")}
    tasked = {
        **base,
        "assignees": ["Dana"],
        "next_task_id": 2,
        "tasks": [{**NAME_TASK, "comments": [_comment()]}],
    }
    return [
        pytest.param(base, id="projects-only"),
        pytest.param({**base, "assignees": ["Dana"]}, id="with-assignees"),
        pytest.param(tasked, id="with-tasks-and-no-name"),
        pytest.param({**tasked, "operator_name": "Sam"}, id="current"),
    ]


@pytest.mark.parametrize("document", _saved_forms())
def test_every_supported_saved_form_keeps_all_existing_values(
    tmp_path: Path, document: dict[str, Any]
) -> None:
    """CP-265, CP-270: each of the four forms the tracker reads loads and starts with every project,
    task, label, comment, assignee and name it holds, takes the existing default for each key it
    lacks, and the load writes nothing."""
    content = json.dumps(document).encode("utf-8")
    saved = tmp_path / "tracker.json"
    saved.write_bytes(content)
    before = _listing(tmp_path)

    state = SavedData(tmp_path).load()

    assert state is not None
    assert [project.name for project in state.projects] == ["Alpha"]
    assert list(state.assignees) == document.get("assignees", [])
    assert state.operator_name == document.get("operator_name")
    assert state.next_task_id == document.get("next_task_id", 1)
    saved_tasks = document.get("tasks", [])
    assert [(task.title, task.labels, task.assignee) for task in state.tasks] == [
        (task["title"], tuple(task["labels"]), task["assignee"]) for task in saved_tasks
    ]
    assert [
        [(comment.text, comment.author) for comment in task.comments] for task in state.tasks
    ] == [[("Seen", "Dana")] for _ in saved_tasks]
    status, errors = _run_real_start(tmp_path)
    assert (status, errors) == (0, b"")
    assert saved.read_bytes() == content and _listing(tmp_path) == before


ANOTHER_TRACKER_WORDS = "another tracker"


def _start_and_request(location: Path) -> int:
    """A real start on the location on a free port: its ready line, one request, then Ctrl-C."""
    child = subprocess.Popen(
        [sys.executable, "-c", RUN_START, str(location)],
        cwd=PRODUCT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        assert child.stdout is not None
        ready = child.stdout.readline().decode("utf-8")
        assert ready.startswith("The tracker is running. Open http://127.0.0.1:"), ready
        port = int(ready.split("http://127.0.0.1:")[1].split(" ")[0])
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
        try:
            connection.request("GET", "/")
            status = connection.getresponse().status
        finally:
            connection.close()
        child.send_signal(signal.SIGINT)
        child.communicate(timeout=30)
    finally:
        if child.poll() is None:
            child.kill()
            child.communicate()
    return status


def test_a_location_that_is_a_file_serves_without_touching_it(
    starts: _Starts, tmp_path: Path
) -> None:
    """CP-710, CP-725, CP-700: a location that is no directory serves the page, bytes untouched."""
    location = tmp_path / "saved"
    location.write_bytes(b"this is a file")
    before = _listing(tmp_path)
    served = starts.serve(location)
    assert served.first_line == announcement(location, served.port)
    assert served.request("GET", "/")[0] == 503
    assert served.stop() == (0, "", "")
    assert location.read_bytes() == b"this is a file"
    assert _listing(tmp_path) == before


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads a directory whatever its mode")
def test_a_directory_without_read_permission_serves_without_touching_it(
    starts: _Starts, tmp_path: Path
) -> None:
    """CP-710, CP-725, CP-700: a location the tracker may not read serves the page, no refusal.

    The bytes and listing are taken before the permission is removed and compared after the stop
    and the restore, because they cannot be read while it is gone.
    """
    location = tmp_path / "saved"
    location.mkdir()
    (location / "tracker.json").write_bytes(UNREADABLE)
    before = _snapshot(location)
    location.chmod(0o000)
    try:
        served = starts.serve(location)
        assert served.first_line == announcement(location, served.port)
        assert served.request("GET", "/")[0] == 503
        outcome = served.stop()
    finally:
        location.chmod(0o755)
    assert outcome == (0, "", "")
    assert _snapshot(location) == before


def test_an_unreadable_start_releases_its_location_for_retry(
    starts: _Starts, tmp_path: Path
) -> None:
    """CP-712, CP-700: the claim ends with the stop, so repaired data starts and serves 200."""
    (tmp_path / "tracker.json").write_bytes(UNREADABLE)
    before = _listing(tmp_path)
    served = starts.serve(tmp_path)
    assert served.stop() == (0, "", "")
    assert _listing(tmp_path) == before
    SavedData(tmp_path).save(empty_state())
    assert _start_and_request(tmp_path) == 200


@pytest.mark.parametrize("change", ["repaired", "removed"])
def test_external_repair_does_not_change_the_running_unreadable_page(
    starts: _Starts, tmp_path: Path, change: str
) -> None:
    """CP-724, CP-725: the saved data is read once, at start; a repair or a removal while the page
    is served changes no answer and no byte, and the next start reads the data afresh."""
    saved = tmp_path / "tracker.json"
    saved.write_bytes(UNREADABLE)
    served = starts.serve(tmp_path)
    first = served.request("GET", "/")
    if change == "repaired":
        SavedData(tmp_path).save(empty_state())
    else:
        saved.unlink()
    outside = _snapshot(tmp_path)

    again = served.request("GET", "/")
    posted = served.request("POST", "/projects", FORM_HEADERS, b"name=Alpha&description=")

    assert (again[0], again[2]) == (503, first[2])
    assert posted[0] == 303 and posted[1]["location"] == "/"
    assert _snapshot(tmp_path) == outside
    assert served.stop() == (0, "", "")

    restarted = starts.serve(tmp_path)
    assert restarted.first_line == READY_LINE.format(
        port=restarted.port, location=tmp_path.absolute()
    )
    status, _, body = restarted.request("GET", "/")
    assert status == 200
    if change == "removed":
        assert b"There are no projects yet" in body
        assert not saved.exists()
    assert restarted.stop() == (0, "", "")


def test_an_unreadable_lifetime_preserves_all_saved_paths_and_bytes(
    starts: _Starts, tmp_path: Path
) -> None:
    """CP-725, CP-722: the paths and bytes are the same before the start, after reads, after every
    method with checked and refused POSTs, and after the stop; the server opens no connection."""
    location = tmp_path / "saved"
    location.mkdir()
    (location / "tracker.json").write_bytes(UNREADABLE)
    (tmp_path / "audit").mkdir()
    marker = tmp_path / "audit" / "connected"
    before = _snapshot(location)
    served = starts.serve(location, 0, AUDITED_PROGRAM, str(marker))
    assert _snapshot(location) == before

    for target in ("/", "/people", "/nothing"):
        assert served.request("GET", target)[0] == 503
        assert _snapshot(location) == before
    for method in ("GET", "HEAD", "PUT", "DELETE", "PATCH", "OPTIONS"):
        assert served.request(method, "/projects", FORM_HEADERS)[0] == 503
        assert _snapshot(location) == before
    assert served.request("POST", "/projects", FORM_HEADERS, b"name=Alpha")[0] == 303
    assert served.request("POST", "/projects", None, b"name=Alpha")[0] == 403
    cross = {**FORM_HEADERS, "Sec-Fetch-Site": "cross-site"}
    assert served.request("POST", "/projects", cross, b"name=Alpha")[0] == 403
    assert _snapshot(location) == before

    assert served.stop() == (0, "", "")
    assert _snapshot(location) == before
    assert not marker.exists(), "the server process opened an outbound connection"


def _readme_commands(section: str) -> str:
    """The first fenced command block under the README heading with this name."""
    lines = (PRODUCT_ROOT / "README.md").read_text(encoding="utf-8").splitlines()
    start = next(i for i, line in enumerate(lines) if line.lstrip("#").strip() == section)
    opening = next(i for i in range(start, len(lines)) if lines[i].startswith("```"))
    closing = next(i for i in range(opening + 1, len(lines)) if lines[i].startswith("```"))
    return "\n".join(lines[opening + 1 : closing])


def test_set_aside_then_restart_preserves_the_earlier_work(starts: _Starts, tmp_path: Path) -> None:
    """CP-726, CP-730: after the stop, the README's own set-aside commands, run in a copy with a
    scratch home, leave the earlier bytes in the set-aside directory; the next start is empty."""
    copy = tmp_path / "copy"
    location = copy / "products" / "tracker17" / "data"
    location.mkdir(parents=True)
    (location / "tracker.json").write_bytes(UNREADABLE)
    served = starts.serve(location)
    assert served.request("GET", "/")[0] == 503
    assert served.stop() == (0, "", "")

    home = tmp_path / "home"
    home.mkdir()
    commands = _readme_commands(SET_ASIDE_SECTION)
    assert "mv data" in commands
    done = subprocess.run(
        ["/bin/sh", "-c", commands],
        cwd=copy,
        env={**os.environ, "HOME": str(home)},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    (moved,) = (home / "tracker17-set-aside").glob("*/tracker.json")
    assert moved.read_bytes() == UNREADABLE
    assert not location.exists()

    restarted = starts.serve(location)
    assert restarted.first_line == READY_LINE.format(
        port=restarted.port, location=location.absolute()
    )
    status, _, body = restarted.request("GET", "/")
    assert status == 200 and b"There are no projects yet" in body
    assert restarted.stop() == (0, "", "")
    assert moved.read_bytes() == UNREADABLE


@pytest.mark.parametrize("existing", [True, False], ids=["existing", "absent-leaf"])
def test_failed_start_on_a_held_address_releases_its_location_for_retry(
    tmp_path: Path, holder: socket.socket, existing: bool, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-701: a held address leaves the listing as it was, then the released address serves."""
    location = tmp_path / "saved"
    if existing:
        SavedData(location).save(empty_state())
    before = _listing(location) if existing else None
    assert main.start(holder.getsockname(), location) == 1
    assert (_listing(location) if location.exists() else None) == before
    assert ANOTHER_TRACKER_WORDS not in capsys.readouterr().err
    holder.close()
    assert _start_and_request(location) == 200


@pytest.mark.parametrize("existing", [True, False], ids=["existing", "absent-leaf"])
def test_failed_start_on_an_unrelated_bind_error_releases_its_location_for_retry(
    tmp_path: Path, existing: bool, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-701: another bind failure propagates unchanged, with neither refusal and no change."""
    location = tmp_path / "saved"
    if existing:
        SavedData(location).save(empty_state())
    before = _listing(location) if existing else None
    with pytest.raises(OSError) as caught:
        main.start(("192.0.2.1", 0), location)
    assert not isinstance(caught.value, AddressTaken)
    assert (_listing(location) if location.exists() else None) == before
    err = capsys.readouterr().err
    assert ANOTHER_TRACKER_WORDS not in err
    assert "already using the address" not in err
    assert _start_and_request(location) == 200
