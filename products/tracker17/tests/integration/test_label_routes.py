"""Integration tests of the label requests through the real Site, application and domain (layer 3).

Checks SRS FR-23 (adding and removing a label from a task's page), FR-39 and FR-40 (a refusal
changes nothing and gives its reason) and NFR-4 (no script). Change spec rules CP-187 to CP-199 and
CP-203 and NFDR QC-7, QC-8, QC-49, QC-56 and QC-57 are the ones each test names. Where a test checks
words, they are the strings of this change's text record. The real Site, Tracker and SavedData are
used, with an injected Clock and a saver that can be made to fail; no product name is patched.
"""

from __future__ import annotations

import threading
from pathlib import Path
from urllib.parse import urlencode

import pytest
from test_pages import Element, parse
from test_routes import FORM, HOST, POLICY, SAME_ORIGIN, get, header, page
from test_task_routes import (
    MovableClock,
    World,
    add_task,
    focused,
    follow,
    location,
    make_world,
)

from application import SHORT_TEXT_MAX, Tracker, TrackerState
from domain import empty_state
from persistence import SavedData
from web import Response, Site, pages

TITLE = "Set up CI"
ADD = "/tasks/1/labels"
REMOVE = "/tasks/1/labels/remove"
EMOJI_200 = "\U0001f600" * SHORT_TEXT_MAX
EMPTY_REASON = "A label needs at least one character. Type a label."
TOO_LONG_REASON = f"A label can't be longer than {SHORT_TEXT_MAX} characters. Type a shorter one."


def send(
    site: Site,
    target: str,
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    **fields: str,
) -> Response:
    sent = urlencode(fields).encode("utf-8") if body is None else body
    return site.handle("POST", target, {**(headers or SAME_ORIGIN), **FORM}, sent)


def add_label(site: Site, label: str, task: int = 1) -> Response:
    return send(site, f"/tasks/{task}/labels", label=label)


def remove_label(site: Site, label: str, task: int = 1) -> Response:
    return send(site, f"/tasks/{task}/labels/remove", label=label)


def world_with(tmp_path: Path, *labels: str) -> World:
    """A world holding one task, `Set up CI`, carrying these labels in this order."""
    world = make_world(tmp_path)
    add_task(world.site, title=TITLE)
    for label in labels:
        world.tracker.add_task_label(1, label)
    return world


def labels_of(world: World) -> tuple[str, ...]:
    task = world.tracker.task(1)
    assert task is not None
    return task.labels


def shown_labels(root: Element) -> list[str]:
    return [e.text() for e in root.walk() if "label-text" in (e.attrs.get("class") or "").split()]


def description(element: Element) -> str:
    return " ".join(found.text() for found in element.described_by())


def label_field(root: Element) -> Element:
    found = root.by_id("new-label")
    assert found is not None
    return found


@pytest.mark.parametrize(
    "value",
    ["ui", "   ", " ui ", "Bug", EMOJI_200],
    ids=["plain", "spaces-only", "surrounding-spaces", "case-distinct", "200-code-points"],
)
def test_label_add_redirects_then_reads_saved_result(tmp_path: Path, value: str) -> None:
    """CP-187, CP-188: the exact value is appended after the others and the answer is a plain
    303."""
    world = world_with(tmp_path, "bug", "base")
    response = add_label(world.site, value)
    assert location(response) == f"/tasks/1?{urlencode({'label_added': value})}"
    assert "#" not in location(response)
    assert labels_of(world) == ("bug", "base", value)
    root = parse(follow(world.site, response))
    assert shown_labels(root) == ["bug", "base", value]
    assert [e.attrs["id"] for e in focused(root)] == ["label-3"]
    assert description(focused(root)[0]) == f"You added the label '{value}' to '{TITLE}'."
    assert SavedData(world.location).load() is not None
    assert world.restarted().tracker.task(1) == world.tracker.task(1)


def test_duplicate_add_redirects_plain_without_save_or_message(tmp_path: Path) -> None:
    """CP-189: nothing is saved, nothing is said, and the file's bytes are as they were."""
    world = world_with(tmp_path, "bug")
    before = (world.bytes_on_disk(), world.saver.saves)
    response = add_label(world.site, "bug")
    assert location(response) == "/tasks/1"
    assert (world.bytes_on_disk(), world.saver.saves) == before
    root = parse(follow(world.site, response))
    assert focused(root) == [] and shown_labels(root) == ["bug"]
    assert "You added" not in root.text() and "can't be longer" not in root.text()


def test_label_remove_redirects_with_survivors_in_order(tmp_path: Path) -> None:
    """CP-192, CP-183: the middle one goes, the rest keep their order; the last one leaves the
    published empty area."""
    world = world_with(tmp_path, "a", "b", "c")
    response = remove_label(world.site, "b")
    assert location(response) == "/tasks/1?label_removed=b"
    assert labels_of(world) == ("a", "c")
    root = parse(follow(world.site, response))
    assert shown_labels(root) == ["a", "c"]
    (heading,) = focused(root)
    assert heading.tag == "h1"
    assert description(heading) == f"You removed the label 'b' from '{TITLE}'."
    remove_label(world.site, "a")
    last = remove_label(world.site, "c")
    root = parse(follow(world.site, last))
    assert labels_of(world) == () and shown_labels(root) == []
    assert "This task has no labels. Type a label and press Add." in root.text()
    assert description(focused(root)[0]) == f"You removed the label 'c' from '{TITLE}'."


@pytest.mark.parametrize(
    ("action", "label", "expected", "field_value"),
    [
        (add_label, "", "/tasks/1?label_refused=empty&label=", ""),
        (add_label, "x" * (SHORT_TEXT_MAX + 1), "/tasks/1?label_refused=too-long", ""),
        (remove_label, "nope", "/tasks/1?label_refused=not-carried&label=nope", ""),
    ],
    ids=["empty-add", "overlong-add", "absent-remove"],
)
def test_each_label_refusal_preserves_saved_bytes_and_shows_reason(
    tmp_path: Path, action, label: str, expected: str, field_value: str
) -> None:
    """CP-190, CP-191, CP-193: the right element takes focus with the reason, the file is as it
    was."""
    world = world_with(tmp_path, "ui")
    before = (world.bytes_on_disk(), world.saver.saves, labels_of(world))
    response = action(world.site, label)
    assert location(response) == expected
    root = parse(follow(world.site, response))
    (target,) = focused(root)
    if action is remove_label:
        assert target.tag == "section"
        assert description(target) == (
            f"The label 'nope' isn't on '{TITLE}'. The labels shown are the ones the task carries."
        )
    else:
        assert target is label_field(root) and target.attrs["value"] == field_value
        assert description(target) == (EMPTY_REASON if label == "" else TOO_LONG_REASON)
    assert shown_labels(root) == ["ui"]
    assert (world.bytes_on_disk(), world.saver.saves, labels_of(world)) == before


@pytest.mark.parametrize("action", [add_label, remove_label], ids=["add", "remove"])
def test_a_missing_task_gets_the_task_not_found_page_for_each_action(
    tmp_path: Path, action
) -> None:
    """CP-194: the redirect names the task, and its page is the not-found page that speaks of
    one."""
    world = world_with(tmp_path, "ui")
    before = (world.bytes_on_disk(), world.saver.saves)
    response = action(world.site, "ui", 99)
    assert location(response) == "/tasks/99"
    answer = get(world.site, "/tasks/99")
    assert answer.status == 404 and answer.body == pages.task_not_found_page().encode("utf-8")
    assert (world.bytes_on_disk(), world.saver.saves) == before


def test_overlong_label_is_absent_from_redirect_and_landing(tmp_path: Path) -> None:
    """CP-191, ADR-0006: none of the sent text travels; a forged label beside the code is
    dropped."""
    world = world_with(tmp_path)
    sent = "Leak" + "x" * SHORT_TEXT_MAX
    response = add_label(world.site, sent)
    assert "Leak" not in location(response)
    landing = follow(world.site, response)
    assert "Leak" not in landing
    forged = page(get(world.site, "/tasks/1?label_refused=too-long&label=Leak"))
    assert "Leak" not in forged
    root = parse(forged)
    assert label_field(root).attrs["value"] == "" and focused(root) == [label_field(root)]
    assert description(label_field(root)) == TOO_LONG_REASON


@pytest.mark.parametrize("sent", [b"a%0D%0Ab", b"a%0Db", b"a%0Ab"], ids=["crlf", "lone-cr", "lf"])
def test_normalized_label_requests_use_exact_membership(tmp_path: Path, sent: bytes) -> None:
    """RT-10: one line-feed conversion and nothing else, for both actions."""
    world = world_with(tmp_path)
    add = send(world.site, ADD, body=b"label=" + sent + b"+")
    assert location(add) == f"/tasks/1?{urlencode({'label_added': 'a' + chr(10) + 'b '})}"
    assert labels_of(world) == ("a\nb ",)
    assert send(world.site, ADD, body=b"label=" + sent + b"+").status == 303
    assert labels_of(world) == ("a\nb ",)
    near = send(world.site, REMOVE, body=b"label=" + sent)
    assert location(near).startswith("/tasks/1?label_refused=not-carried")
    assert labels_of(world) == ("a\nb ",)
    removed = send(world.site, REMOVE, body=b"label=" + sent + b"+")
    assert location(removed).startswith("/tasks/1?label_removed=")
    assert labels_of(world) == ()


@pytest.mark.parametrize("action", ["add", "remove"])
def test_label_save_failure_reports_failure_without_publication(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], action: str
) -> None:
    """QC-49, QC-56, QC-57: nothing changes, the console names action then error, the page says
    the published failure and shows no Python text and no success line."""
    world = world_with(tmp_path, "ui")
    before = (world.bytes_on_disk(), labels_of(world))
    world.saver.failing = True
    capsys.readouterr()
    sent = " x " if action == "add" else "ui"
    response = (add_label if action == "add" else remove_label)(world.site, sent)
    verb = "add the label ' x ' to" if action == "add" else "remove the label 'ui' from"
    assert capsys.readouterr().err.splitlines() == [
        f"The tracker couldn't {verb} '{TITLE}', and nothing was changed.",
        "PermissionError: the disk said no",
    ]
    assert location(response) == f"/tasks/1?{urlencode({'label_failed': action, 'label': sent})}"
    landing = follow(world.site, response)
    for leaked in ("PermissionError", "disk said no", "Traceback", "You added", "You removed"):
        assert leaked not in landing, leaked
    root = parse(landing)
    (target,) = focused(root)
    assert target.tag == ("form" if action == "add" else "section")
    assert description(target) == (
        f"The tracker couldn't {verb} '{TITLE}', and nothing was changed. "
        + ("What you typed is still in the form. Try again." if action == "add" else "Try again.")
    )
    assert label_field(root).attrs["value"] == (" x " if action == "add" else "")
    assert (world.bytes_on_disk(), labels_of(world)) == before
    world.saver.failing = False
    assert capsys.readouterr().err == ""


@pytest.mark.parametrize("action", ["add", "remove"])
def test_a_label_failure_before_the_title_is_read_uses_the_short_console_line(
    capsys: pytest.CaptureFixture[str], action: str
) -> None:
    """The title could not be read, so the first line names the label alone."""

    class Breaking(Tracker):
        def add_task_label(self, task_id: int, label: str):  # type: ignore[no-untyped-def]
            raise RuntimeError("boom")

        def remove_task_label(self, task_id: int, label: str):  # type: ignore[no-untyped-def]
            raise RuntimeError("boom")

    class Quiet:
        def save(self, state: TrackerState) -> None:
            return None

    site = Site(Breaking(empty_state(), Quiet(), MovableClock()), HOST)
    capsys.readouterr()
    response = (add_label if action == "add" else remove_label)(site, "ui", 5)
    assert capsys.readouterr().err.splitlines() == [
        f"The tracker couldn't {action} the label 'ui', and nothing was changed.",
        "RuntimeError: boom",
    ]
    assert location(response) == f"/tasks/5?{urlencode({'label_failed': action, 'label': 'ui'})}"


def test_label_outcome_query_is_stateless_and_presence_based(tmp_path: Path) -> None:
    """QC-8, ADR-0006: a blank value is not an absent one, and a reload or a back changes
    nothing."""
    world = world_with(tmp_path, "ui")
    saves = world.saver.saves
    blank = parse(page(get(world.site, "/tasks/1?label_removed=")))
    assert description(focused(blank)[0]) == f"You removed the label '' from '{TITLE}'."
    absent = parse(page(get(world.site, "/tasks/1")))
    assert focused(absent) == []
    for unknown in ("label_refused=bogus", "label_failed=other"):
        shown = page(get(world.site, f"/tasks/1?{unknown}&label=Leak"))
        assert "Leak" not in shown and focused(parse(shown)) == []
    mixed = parse(
        page(
            get(
                world.site,
                "/tasks/1?label_refused=empty&label_failed=add&label_added=ui&label_removed=x"
                "&saved&edit_refused=blank-title",
            )
        )
    )
    assert focused(mixed) == [label_field(mixed)]
    assert description(label_field(mixed)) == EMPTY_REASON
    for _ in range(3):
        get(world.site, "/tasks/1?label_added=ui")
        get(world.site, "/tasks/1?label_removed=ui")
    assert (world.saver.saves, labels_of(world)) == (saves, ("ui",))


def test_stale_label_action_checks_current_state(tmp_path: Path) -> None:
    """CP-189, CP-193: a page shown earlier acts on the current labels, not on its own."""
    world = world_with(tmp_path, "x")
    assert location(remove_label(world.site, "x")).startswith("/tasks/1?label_removed=")
    saves = world.saver.saves
    stale = remove_label(world.site, "x")
    assert location(stale) == "/tasks/1?label_refused=not-carried&label=x"
    assert world.saver.saves == saves
    assert location(add_label(world.site, "y")).startswith("/tasks/1?label_added=")
    saves = world.saver.saves
    assert location(add_label(world.site, "y")) == "/tasks/1"
    assert world.saver.saves == saves and labels_of(world) == ("y",)


@pytest.mark.parametrize("target", [ADD, REMOVE], ids=["add", "remove"])
@pytest.mark.parametrize(
    "marks",
    [
        {"Host": HOST, "Sec-Fetch-Site": "cross-site"},
        {"Host": HOST, "Sec-Fetch-Site": "same-site"},
        {"Host": HOST, "Sec-Fetch-Site": "none"},
        {"Host": HOST},
        {"Host": "evil.example:8017", "Sec-Fetch-Site": "same-origin"},
    ],
    ids=["cross-site", "same-site", "none", "absent", "bad-host"],
)
def test_label_routes_refuse_a_request_before_any_action(
    tmp_path: Path, target: str, marks: dict[str, str]
) -> None:
    """QC-7, QC-31, QC-34: the Host and fetch checks come first; the state is as it was."""
    world = world_with(tmp_path, "ui")
    before = (world.bytes_on_disk(), world.saver.saves, labels_of(world))
    response = send(world.site, target, headers=marks, label="ui")
    assert response.status == 403 and response.body == b""
    assert (world.bytes_on_disk(), world.saver.saves, labels_of(world)) == before


def test_label_routes_keep_request_and_response_policy(tmp_path: Path) -> None:
    """QC-7, QC-32, QC-53: a malformed body is the existing 400; an accepted one is a 303 with the
    policy and no cookie, and the requests serialize through the save."""
    world = world_with(tmp_path, "ui")
    before = (world.bytes_on_disk(), labels_of(world))
    for target in (ADD, REMOVE):
        bad = send(world.site, target, body=b"label=%FF")
        assert bad.status == 400 and bad.body == b""
    assert (world.bytes_on_disk(), labels_of(world)) == before
    for response in (add_label(world.site, "new"), remove_label(world.site, "ui")):
        assert response.status == 303 and header(response, "Location")
        assert header(response, "Content-Security-Policy") == POLICY
        assert header(response, "Set-Cookie") is None
    entered, release = threading.Event(), threading.Event()
    states: list[TrackerState] = []

    class HeldSaver:
        holding = False

        def save(self, state: TrackerState) -> None:
            states.append(state)
            if self.holding:
                entered.set()
                assert release.wait(timeout=10)

    saver = HeldSaver()
    tracker = Tracker(empty_state(), saver, MovableClock())
    tracker.create_project("Alpha", "")
    tracker.add_task(1, "T", "", "", "")
    held = Site(tracker, HOST)
    saver.holding = True
    states.clear()
    first = threading.Thread(target=add_label, args=(held, "one"))
    second = threading.Thread(target=add_label, args=(held, "two"))
    first.start()
    assert entered.wait(timeout=10)
    second.start()
    second.join(timeout=0.5)
    assert second.is_alive(), "the second label request did not wait for the first save"
    assert len(states) == 1
    release.set()
    first.join(timeout=10)
    second.join(timeout=10)
    assert not first.is_alive() and not second.is_alive()
    assert sorted(states[-1].tasks[0].labels) == ["one", "two"]


def test_labels_cell_keeps_existing_rendering_after_actions(tmp_path: Path) -> None:
    """CP-196, CP-198: the list shows the saved labels as it always did, after a restart too."""
    world = world_with(tmp_path)

    def cell(site: Site) -> str:
        root = parse(page(get(site, "/projects/1")))
        (table,) = root.find_all("table")
        (row,) = table.find_all("tbody")[0].find_all("tr")
        return row.find_all("td")[4].text()

    assert cell(world.site) == "none"
    add_label(world.site, "ui")
    add_label(world.site, " Bug ")
    assert cell(world.site) == "ui,  Bug "
    assert cell(world.restarted().site) == "ui,  Bug "
    remove_label(world.site, "ui")
    remove_label(world.site, " Bug ")
    assert cell(world.restarted().site) == "none"
