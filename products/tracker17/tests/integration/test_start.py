"""Integration tests of the start: unreadable saved data, a held address and the data directory.

Checks SRS FR-1 (the start prints where to open the tracker and where the data is), FR-3 (a start
whose address something else holds says so in one line), FR-4 and AC-7 (unreadable saved data is
refused whole, left as it was, and points to the setup instructions in README.md), DR-4 (the
assignee list), DR-2 (the task rules), DR-6 and FR-23 (a saved label breaking the label rules) and
DR-5 (a saved operator name breaking the name rule, or not text) and DR-6 and FR-28 (a saved
comment breaking a comment rule). Change spec rules CP-5, CP-7, CP-39 to CP-46, CP-55, CP-65, CP-67
and CP-101, CP-137, CP-197, CP-205, CP-227, CP-228, CP-233 and CP-264, CP-265 and CP-270 and NFDR
QC-47 and QC-58 are the ones each test names.
"""

from __future__ import annotations

import json
import re
import signal
import socket
import subprocess
import sys
import threading
from collections.abc import Iterator
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
CLOSING_SENTENCE = f"See {SET_ASIDE_SECTION} in the setup instructions."
UNREADABLE_LINE = (
    "The tracker didn't start, because it couldn't read its saved data at {location}. "
    "Nothing in it was changed. " + CLOSING_SENTENCE
)
_FENCE = re.compile(r" {0,3}(`{3,}|~{3,})")
_ATX_HEADING = re.compile(r"#{1,6} (.*)")


def _listing(directory: Path) -> list[str]:
    return sorted(str(path.relative_to(directory)) for path in directory.rglob("*"))


def test_an_unreadable_start_returns_non_zero_with_one_message_naming_the_location(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-7: one message, naming the location, and no ready message."""
    (tmp_path / "tracker.json").write_bytes(UNREADABLE)
    status = main.start(("127.0.0.1", 0), tmp_path)
    captured = capsys.readouterr()
    assert status != 0
    messages = [line for line in (captured.out + captured.err).splitlines() if line.strip()]
    assert len(messages) == 1
    assert str(tmp_path) in messages[0]
    assert "http://" not in captured.out + captured.err


def test_an_unreadable_start_changes_nothing_in_the_location(tmp_path: Path) -> None:
    """CP-7: every byte of the file, and the directory's listing, are as they were."""
    saved = tmp_path / "tracker.json"
    saved.write_bytes(UNREADABLE)
    before = _listing(tmp_path)
    assert main.start(("127.0.0.1", 0), tmp_path) != 0
    assert saved.read_bytes() == UNREADABLE
    assert _listing(tmp_path) == before


@pytest.mark.parametrize(
    "content",
    [b"", b"\xff\xfe\x00", b'{"next_project_id": 1}', b"[]"],
    ids=["empty", "not-utf8", "missing-key", "wrong-shape"],
)
def test_other_unreadable_files_are_refused_the_same_way(
    tmp_path: Path, content: bytes, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "tracker.json").write_bytes(content)
    assert main.start(("127.0.0.1", 0), tmp_path) == 1
    assert (tmp_path / "tracker.json").read_bytes() == content
    assert capsys.readouterr().out == ""


def test_an_unreadable_start_writes_exactly_the_one_line_with_the_closing_sentence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-65: one line on standard error, the first half intact and the closing sentence last."""
    (tmp_path / "tracker.json").write_bytes(UNREADABLE)
    status = main.start(("127.0.0.1", 0), tmp_path)
    captured = capsys.readouterr()
    assert status != 0
    assert captured.out == ""
    assert captured.err == UNREADABLE_LINE.format(location=tmp_path.absolute()) + "\n"


INVALID_ASSIGNEE_DOCUMENTS = [
    pytest.param(["Dana", ""], id="empty-name"),
    pytest.param(["Dana", "   "], id="whitespace-name"),
    pytest.param(["Dana", "Ari", "Dana"], id="duplicate"),
    pytest.param(["n" * 201], id="name-201-characters"),
    pytest.param(["Dana", 7], id="number-member"),
    pytest.param(None, id="null"),
    pytest.param("Dana", id="scalar-text"),
    pytest.param({"Dana": 1}, id="mapping"),
]


@pytest.mark.parametrize("assignees", INVALID_ASSIGNEE_DOCUMENTS)
def test_invalid_assignees_stop_start_with_the_existing_plain_message(
    tmp_path: Path, assignees: object, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-101: the same one line as any unreadable saved data, no ready line, bytes untouched."""
    content = json.dumps(
        {
            "next_project_id": 2,
            "projects": [{"id": 1, "name": "Alpha", "description": ""}],
            "assignees": assignees,
        }
    ).encode()
    saved = tmp_path / "tracker.json"
    saved.write_bytes(content)
    before = _listing(tmp_path)

    status = main.start(("127.0.0.1", 0), tmp_path)

    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    assert captured.err == UNREADABLE_LINE.format(location=tmp_path.absolute()) + "\n"
    assert "Traceback" not in captured.err
    assert saved.read_bytes() == content
    assert _listing(tmp_path) == before


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


def test_the_message_closing_sentence_quotes_a_heading_the_readme_has(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-67: the section the unreadable-data line names is a heading README.md has."""
    (tmp_path / "tracker.json").write_bytes(UNREADABLE)
    assert main.start(("127.0.0.1", 0), tmp_path) != 0
    line = capsys.readouterr().err.rstrip("\n")
    assert line.endswith(CLOSING_SENTENCE)
    assert SET_ASIDE_SECTION in _readme_headings()


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


def test_unreadable_saved_data_wins_over_a_held_address(
    tmp_path: Path, holder: socket.socket, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-43: the saved data is read first, so its refusal is the one line shown."""
    saved = tmp_path / "tracker.json"
    saved.write_bytes(UNREADABLE)
    before_listing = _listing(tmp_path)
    assert main.start(holder.getsockname(), tmp_path) != 0
    captured = capsys.readouterr()
    assert captured.out == ""
    lines = captured.err.splitlines()
    assert len(lines) == 1
    assert captured.err == lines[0] + "\n"
    assert str(tmp_path) in lines[0]
    assert "already using the address" not in captured.err
    assert saved.read_bytes() == UNREADABLE
    assert _listing(tmp_path) == before_listing


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


TASK_BREAKS = [
    pytest.param({"priority": "urgent"}, id="unknown-priority"),
    pytest.param({"status": "started"}, id="unknown-status"),
    pytest.param({"project_id": 9}, id="unknown-project"),
    pytest.param({"due_date": "2026-02-30"}, id="impossible-date"),
    pytest.param({"title": "  "}, id="blank-title"),
    pytest.param({"title": "t" * 201}, id="long-title"),
    pytest.param({"assignee": " "}, id="blank-assignee"),
    pytest.param({"id": 2}, id="identity-not-yet-issued"),
]


@pytest.mark.parametrize("change", TASK_BREAKS)
def test_a_saved_task_that_breaks_a_task_rule_stops_start_with_the_plain_message(
    tmp_path: Path, change: dict[str, object], capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-137: the same one line as any unreadable saved data, no ready line, bytes untouched."""
    task = {
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
    content = json.dumps(
        {
            "next_project_id": 2,
            "projects": [{"id": 1, "name": "Alpha", "description": ""}],
            "assignees": [],
            "next_task_id": 2,
            "tasks": [{**task, **change}],
        }
    ).encode()
    saved = tmp_path / "tracker.json"
    saved.write_bytes(content)
    before = _listing(tmp_path)

    status = main.start(("127.0.0.1", 0), tmp_path)

    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    assert captured.err == UNREADABLE_LINE.format(location=tmp_path.absolute()) + "\n"
    assert saved.read_bytes() == content
    assert _listing(tmp_path) == before


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


INVALID_LABEL_COLLECTIONS = [
    pytest.param([""], id="empty-label"),
    pytest.param(["x" * 201], id="label-201-code-points"),
    pytest.param(["bug", "ui", "bug"], id="repeated-label"),
]


@pytest.mark.parametrize("labels", INVALID_LABEL_COLLECTIONS)
def test_invalid_saved_labels_stop_start_with_existing_message(
    tmp_path: Path,
    labels: list[str],
    holder: socket.socket,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """CP-197, CP-205: the existing one line naming the location, nonzero, no ready line and no
    listener, a valid task before the break loaded by nothing, and the bytes and listing as they
    were.

    The start is given an address something else holds. A start that wrongly read the data would
    then print the address-taken line and return, where on a free address it would serve forever;
    the unreadable line comes first (`main.start`), so it is the one asserted here.
    """
    content = json.dumps(
        {
            "next_project_id": 2,
            "projects": [{"id": 1, "name": "Alpha", "description": ""}],
            "assignees": [],
            "next_task_id": 3,
            "tasks": [_task_with_labels(1, ["bug"]), _task_with_labels(2, labels)],
        }
    ).encode()
    saved = tmp_path / "tracker.json"
    saved.write_bytes(content)
    before = _listing(tmp_path)

    host, port = holder.getsockname()

    status = main.start((host, port), tmp_path)

    captured = capsys.readouterr()
    assert status != 0
    assert captured.out == ""
    assert captured.err == UNREADABLE_LINE.format(location=tmp_path.absolute()) + "\n"
    assert "http://" not in captured.out + captured.err
    assert saved.read_bytes() == content
    assert _listing(tmp_path) == before


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


def _unreadable_start(
    tmp_path: Path, content: bytes, capsys: pytest.CaptureFixture[str], holder: socket.socket
) -> None:
    """The existing one line, nonzero, no ready line, and the bytes and listing as they were.

    The address is one something else holds, so a start that wrongly read the data would print the
    address-taken line, or serve forever, instead of the unreadable line asserted here.
    """
    saved = tmp_path / "tracker.json"
    saved.write_bytes(content)
    before = _listing(tmp_path)

    status = main.start(holder.getsockname(), tmp_path)

    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    assert captured.err == UNREADABLE_LINE.format(location=tmp_path.absolute()) + "\n"
    assert "Traceback" not in captured.err and "http://" not in captured.err
    assert saved.read_bytes() == content
    assert _listing(tmp_path) == before


def test_start_refuses_saved_empty_operator_name(
    tmp_path: Path, holder: socket.socket, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-228, CP-233: an empty saved operator name stops the start."""
    _unreadable_start(tmp_path, _name_document(operator_name=""), capsys, holder)


def test_start_refuses_saved_whitespace_operator_name(
    tmp_path: Path, holder: socket.socket, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-228, CP-233: a whitespace-only saved operator name stops the start."""
    _unreadable_start(tmp_path, _name_document(operator_name="   "), capsys, holder)


def test_start_refuses_saved_overlong_operator_name(
    tmp_path: Path, holder: socket.socket, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-228, CP-233: a saved operator name of 201 code points stops the start."""
    _unreadable_start(tmp_path, _name_document(operator_name="n" * 201), capsys, holder)


def test_start_refuses_saved_numeric_operator_name(
    tmp_path: Path, holder: socket.socket, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-228, CP-233: a saved operator name that is a number stops the start."""
    _unreadable_start(tmp_path, _name_document(operator_name=7), capsys, holder)


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


def _unreadable_comment(
    tmp_path: Path,
    holder: socket.socket,
    capsys: pytest.CaptureFixture[str],
    comment: dict[str, object],
) -> None:
    """The whole load refuses and names the location, and the start gives its one existing line.

    The address is held by another program, so a start that read the data would print the
    address-taken line, or serve, instead of the unreadable line.
    """
    content = _comment_document([_comment(), comment])
    saved = tmp_path / "tracker.json"
    saved.write_bytes(content)
    before = _listing(tmp_path)

    with pytest.raises(UnreadableData) as error:
        SavedData(tmp_path).load()

    assert error.value.location == tmp_path
    assert saved.read_bytes() == content and _listing(tmp_path) == before
    _unreadable_start(tmp_path, content, capsys, holder)


def test_saved_comment_blank_text_is_unreadable(
    tmp_path: Path, holder: socket.socket, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-264, CP-270: a comment with empty text refuses the whole load and the start."""
    _unreadable_comment(tmp_path, holder, capsys, _comment(text=""))


def test_saved_comment_whitespace_text_is_unreadable(
    tmp_path: Path, holder: socket.socket, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-264, CP-270: whitespace-only text, line breaks, U+00A0 and U+3000 included, is blank."""
    _unreadable_comment(tmp_path, holder, capsys, _comment(text=" \n\t\u00a0\u3000 \n"))


def test_saved_comment_overlong_text_is_unreadable(
    tmp_path: Path, holder: socket.socket, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-264, CP-270: 4,001 code points is one over the comment maximum."""
    _unreadable_comment(tmp_path, holder, capsys, _comment(text="t" * 4001))


def test_saved_comment_blank_author_is_unreadable(
    tmp_path: Path, holder: socket.socket, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-264, CP-270: a comment with an empty author refuses the whole load and the start."""
    _unreadable_comment(tmp_path, holder, capsys, _comment(author=""))


def test_saved_comment_whitespace_author_is_unreadable(
    tmp_path: Path, holder: socket.socket, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-264, CP-270: a whitespace-only author is blank by the same set the name rules use."""
    _unreadable_comment(tmp_path, holder, capsys, _comment(author="  \u3000"))


def test_saved_comment_overlong_author_is_unreadable(
    tmp_path: Path, holder: socket.socket, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-264, CP-270: 201 code points is one over the name maximum."""
    _unreadable_comment(tmp_path, holder, capsys, _comment(author="a" * 201))


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
