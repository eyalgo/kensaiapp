"""End-to-end tests of the first path, in Chromium against a tracker run as a process (layer 5).

Checks SRS FR-1 (the start tells the operator where to open the tracker), FR-10 and FR-11 (create
and list projects), NFR-5 (typed text is shown as text), and acceptance criteria AC-6 (a project
survives a stop and a start), AC-12 and AC-20. Change spec rules CP-1, CP-3, CP-10, CP-12, CP-13,
CP-16 to CP-20, CP-23, CP-24 and CP-30 to CP-38 and NFDR QC-36 and QC-55 are the ones each test
names.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import TYPE_CHECKING

from playwright.sync_api import Page, expect

if TYPE_CHECKING:
    from conftest import RunningTracker, TrackerFactory

HOSTILE = "<b>A&B</b>"


def create(page: Page, address: str, name: str, description: str = "") -> None:
    page.goto(address + "/")
    page.locator("#name").fill(name)
    page.locator("#description").fill(description)
    page.get_by_role("button", name="Create").click()
    page.wait_for_load_state()


def listed_names(page: Page, address: str) -> list[str]:
    page.goto(address + "/")
    return [text or "" for text in page.locator("ul.project-list a").all_text_contents()]


def focused_id(page: Page) -> str:
    return page.evaluate("document.activeElement && document.activeElement.id")


def test_the_first_output_is_the_ready_message_address_before_location(
    tracker: RunningTracker,
) -> None:
    """CP-1, QC-55."""
    line = tracker.first_line
    assert line.startswith("The tracker is running.")
    assert tracker.address in line and str(tracker.location) in line
    assert line.index(tracker.address) < line.index(str(tracker.location))
    assert not tracker.address.endswith("/") and not str(tracker.location).endswith("/")


def test_the_first_project_lands_on_its_page_with_spaces_line_break_and_created_line(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-10, CP-13, CP-17, CP-18."""
    page.goto(tracker.address + "/")
    expect(page.locator("main")).to_contain_text("There are no projects yet.")
    expect(page.locator("#name")).to_be_visible()
    create(page, tracker.address, "  Alpha  ", "line one\nline two")
    assert re.fullmatch(re.escape(tracker.address) + r"/projects/1\?created", page.url)
    assert page.locator("h1").text_content() == "  Alpha  "
    assert page.locator("p.description").text_content() == "line one\nline two"
    assert page.locator("p.description").evaluate("e => getComputedStyle(e).whiteSpace") == (
        "pre-wrap"
    )
    expect(page.locator("#created-line")).to_have_text("You created '  Alpha  '.")
    expect(page.locator("p.no-tasks")).to_have_text(
        "This project has no tasks yet. Give the first task a title and press Add."
    )
    assert page.locator("main form").count() == 1
    assert page.locator("main form input").evaluate_all("e => e.map(i => i.name)") == [
        "title",
        "due_date",
    ]
    assert page.locator("main form select").evaluate_all("e => e.map(i => i.name)") == [
        "priority",
        "assignee",
    ]
    assert page.locator("main button").all_text_contents() == ["Add"]
    assert page.locator("textarea").count() == 0
    expect(page.locator("h1")).to_be_focused()
    assert page.evaluate("document.activeElement.tagName") == "H1"


def test_a_created_project_is_listed_after_a_stop_and_a_start(
    trackers: TrackerFactory, location: Path, page: Page
) -> None:
    """CP-3, CP-24, AC-6 (the project half)."""
    first = trackers.start(location)
    create(page, first.address, "Alpha", "x")
    status, stderr = first.stop()
    assert status == 0
    assert "Traceback" not in stderr
    second = trackers.start(location)
    page.goto(second.address + "/")
    expect(page.locator("ul.project-list a")).to_have_text(["Alpha"])
    expect(page.locator("ul.project-list p.description")).to_have_text(["x"])


def test_names_list_in_case_blind_order(tracker: RunningTracker, page: Page) -> None:
    """CP-12."""
    for name in ("beta", "Alpha", "alpha"):
        create(page, tracker.address, name)
    assert listed_names(page, tracker.address) == ["Alpha", "alpha", "beta"]


def test_a_refused_name_puts_focus_in_the_name_field_with_the_reason_as_its_description(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-19."""
    create(page, tracker.address, "Alpha", "first")
    create(page, tracker.address, "Alpha", "notes")
    expect(page.locator("#name")).to_be_focused()
    assert focused_id(page) == "name"
    reason = page.locator("#name-reason").inner_text()
    assert reason.strip()
    expect(page.locator("#name")).to_have_accessible_description(reason)
    expect(page.locator("#name")).to_have_value("Alpha")
    expect(page.locator("#description")).to_have_value("notes")


def test_a_description_of_4000_characters_with_line_breaks_is_saved_whole(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-16, AC-20. The last characters are typed, so the form's own limit is in play."""
    head = ("x" * 79 + "\n") * 49 + "y" * 70
    tail = "\nabcdefghi"
    expected = head + tail
    assert len(expected) == 4000 and expected.count("\n") == 50
    page.goto(tracker.address + "/")
    page.locator("#name").fill("Alpha")
    page.locator("#description").fill(head)
    page.locator("#description").press_sequentially(tail)
    assert page.locator("#description").input_value() == expected
    page.locator("#description").press("Z")
    assert page.locator("#description").input_value() == expected
    page.get_by_role("button", name="Create").click()
    page.wait_for_load_state()
    saved = json.loads(tracker.saved_file.read_text(encoding="utf-8"))
    assert saved["projects"][0]["description"] == expected


def _hand_built(tracker: RunningTracker, page: Page, name: str, description: str) -> str:
    """Send a request the form cannot, and open the address it answers with."""
    before = tracker.saved_file.read_bytes()
    answer = page.request.post(
        tracker.address + "/projects",
        form={"name": name, "description": description},
        headers={"Host": f"{tracker.host}:{tracker.port}", "Sec-Fetch-Site": "same-origin"},
        max_redirects=0,
    )
    assert answer.status == 303
    address = answer.headers["location"]
    page.goto(tracker.address + address)
    assert tracker.saved_file.read_bytes() == before
    return address


def test_a_hand_built_201_character_name_gets_the_reason_and_none_of_the_text(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-20, AC-12."""
    create(page, tracker.address, "Alpha", "d")
    sent = "ç" * 201
    address = _hand_built(tracker, page, sent, "d")
    assert sent[:20] not in address and "%C3%A7" not in address
    expect(page.locator("#name")).to_be_focused()
    assert focused_id(page) == "name"
    assert page.locator("#name-reason").inner_text().strip()
    assert "ç" not in page.content()


def test_a_hand_built_over_long_description_is_refused(tracker: RunningTracker, page: Page) -> None:
    """CP-16, the 4001st character."""
    create(page, tracker.address, "Alpha", "d")
    sent = "ç" * 4001
    address = _hand_built(tracker, page, "Beta", sent)
    assert "%C3%A7" not in address
    expect(page.locator("#description")).to_be_focused()
    assert focused_id(page) == "description"
    assert page.locator("#description-reason").inner_text().strip()
    assert "ç" not in page.content()
    expect(page.locator("#description")).to_have_value("")


def test_markup_in_a_name_shows_as_text(tracker: RunningTracker, page: Page) -> None:
    """CP-23."""
    create(page, tracker.address, HOSTILE, HOSTILE)
    assert page.locator("h1").text_content() == HOSTILE
    assert page.locator("main b").count() == 0
    assert listed_names(page, tracker.address) == [HOSTILE]
    assert page.locator("main b").count() == 0


def test_an_address_with_no_project_shows_the_not_found_page(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-33, CP-34."""
    response = page.goto(tracker.address + "/projects/99")
    assert response is not None and response.status == 404
    expect(page.locator("main h1")).to_have_count(1)
    assert page.locator("form, input, textarea, button").count() == 0
    header = page.eval_on_selector_all("header a", "elements => elements.map(e => e.href)")
    assert header == [tracker.address + "/", tracker.address + "/people"]
    body = page.eval_on_selector_all("main a", "elements => elements.map(e => e.href)")
    assert body == [tracker.address + "/"]
    page.locator("main a").click()
    page.wait_for_load_state()
    assert page.url == tracker.address + "/"
    expect(page.locator("h1")).to_have_text("Projects")


def test_not_found_requests_write_nothing(
    trackers: TrackerFactory, location: Path, page: Page
) -> None:
    """CP-36: no saved data is created, and saved data's bytes stay the same."""
    tracker = trackers.start(location)
    for path in ("/projects/99", "/nowhere"):
        page.goto(tracker.address + path)
    assert not tracker.location.exists()
    create(page, tracker.address, "Alpha")
    saved = tracker.saved_file.read_bytes()
    for path in ("/projects/99", "/nowhere"):
        page.goto(tracker.address + path)
    assert tracker.saved_file.read_bytes() == saved
