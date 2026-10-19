"""Integration tests of the label actions through the real loopback listener (layer 3).

Checks SRS FR-23 (adding and removing a label), FR-39 (a refusal changes nothing) and NFR-4 (no
script). Change spec rules CP-187 to CP-194 and CP-203 and NFDR QC-32 and QC-35 are the ones each
test names. The real listener serves the real Site, application and domain, with the clock and
the saver handed in; every submission carries the same-origin mark a form sends.
"""

from __future__ import annotations

import http.client
import threading
from collections.abc import Iterator
from datetime import UTC, datetime
from urllib.parse import urlencode

import pytest

from application import SHORT_TEXT_MAX, Tracker, TrackerState
from domain import empty_state
from web import listen

TITLE = "Set up CI"


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 10, 12, 12, 0, tzinfo=UTC)


class HandedSaver:
    """The saver the listener's tracker is handed: it keeps every state it is given."""

    def __init__(self) -> None:
        self.saved: list[TrackerState] = []

    def save(self, state: TrackerState) -> None:
        self.saved.append(state)


@pytest.fixture
def served() -> Iterator[tuple[tuple[str, int], Tracker, HandedSaver]]:
    saver = HandedSaver()
    tracker = Tracker(empty_state(), saver, FixedClock())
    tracker.create_project("Alpha", "")
    tracker.add_task(1, TITLE, "", "", "")
    tracker.add_task(1, "Second", "", "", "")
    tracker.add_task_label(1, "ui")
    listener = listen(("127.0.0.1", 0), tracker)
    thread = threading.Thread(target=listener.serve_forever, daemon=True)
    thread.start()
    address = (str(listener.server_address[0]), int(listener.server_address[1]))
    try:
        yield address, tracker, saver
    finally:
        listener.shutdown()
        thread.join(timeout=10)
        listener.server_close()


def exchange(
    address: tuple[str, int], method: str, target: str, label: str | None = None
) -> tuple[int, dict[str, str], str]:
    """One request over the socket; a submission carries the same-origin mark a form sends."""
    connection = http.client.HTTPConnection(address[0], address[1], timeout=10)
    headers: dict[str, str] = {}
    body = None
    if method == "POST":
        headers = {
            "Sec-Fetch-Site": "same-origin",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        body = urlencode({"label": label or ""}).encode("utf-8")
    try:
        connection.request(method, target, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read().decode("utf-8")
    finally:
        connection.close()


def submit_then_read(address: tuple[str, int], target: str, label: str) -> tuple[str, str]:
    status, headers, _ = exchange(address, "POST", target, label)
    assert status == 303
    landing = headers["Location"]
    status, _, body = exchange(address, "GET", landing)
    assert status == 200
    return landing, body


def test_real_listener_serves_label_area_and_actions(
    served: tuple[tuple[str, int], Tracker, HandedSaver],
) -> None:
    """CP-187 to CP-194, CP-203: the area, an add, a repeat, a remove, each refusal and a stale
    remove, through redirects, and the list showing the result."""
    address, tracker, saver = served
    status, _, populated = exchange(address, "GET", "/tasks/1")
    assert status == 200 and 'action="/tasks/1/labels/remove"' in populated
    assert 'action="/tasks/1/labels"' in populated and ">ui</span>" in populated
    _, _, empty = exchange(address, "GET", "/tasks/2")
    assert "This task has no labels. Type a label and press Add." in empty

    landing, body = submit_then_read(address, "/tasks/1/labels", "new")
    assert landing == "/tasks/1?label_added=new"
    assert f"You added the label 'new' to '{TITLE}'." in body
    saves = len(saver.saved)
    landing, body = submit_then_read(address, "/tasks/1/labels", "new")
    assert landing == "/tasks/1" and len(saver.saved) == saves
    assert "You added" not in body

    landing, body = submit_then_read(address, "/tasks/1/labels/remove", "ui")
    assert landing == "/tasks/1?label_removed=ui"
    assert f"You removed the label 'ui' from '{TITLE}'." in body
    task = tracker.task(1)
    assert task is not None and task.labels == ("new",)

    saves = len(saver.saved)
    landing, body = submit_then_read(address, "/tasks/1/labels", "")
    assert landing == "/tasks/1?label_refused=empty&label="
    assert "A label needs at least one character. Type a label." in body
    landing, body = submit_then_read(address, "/tasks/1/labels", "x" * (SHORT_TEXT_MAX + 1))
    assert landing == "/tasks/1?label_refused=too-long" and "xxxx" not in body
    assert f"A label can't be longer than {SHORT_TEXT_MAX} characters." in body
    landing, body = submit_then_read(address, "/tasks/1/labels/remove", "ui")
    assert landing == "/tasks/1?label_refused=not-carried&label=ui"
    assert f"The label 'ui' isn't on '{TITLE}'." in body
    assert len(saver.saved) == saves

    _, _, listed = exchange(address, "GET", "/projects/1")
    assert "<td" in listed and ">new</td>" in listed and ">none</td>" in listed
