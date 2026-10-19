"""End-to-end tests of the People page, in Chromium against a tracker run as a process (layer 5).

Checks SRS FR-20 and FR-22 (the assignee list and removing a name), FR-39 and FR-40 (refusals and
the maximum length), FR-27 (the operator's name), NFR-5 (typed text is shown as text), DR-4 (the
assignee list), DR-5 (the operator name) and acceptance criteria AC-6, AC-12 and AC-17. Change spec
rules CP-82, CP-83, CP-86, CP-87, CP-89, CP-90, CP-94, CP-96, CP-99, CP-100, CP-103, CP-216, CP-220,
CP-224, CP-225 and CP-236 and NFDR QC-36 are the ones each test names. Each test starts the tracker
through `main.start`, so the saved shape and the list's restart are the real ones.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from playwright.sync_api import Page, expect

if TYPE_CHECKING:
    from conftest import RunningTracker, TrackerFactory

HOSTILE = "<b>A&B</b>"
QUOTED = 'O\'Brien "Q" & <i>co</i>'
NARROW_WIDTH = 320
NARROW_HEIGHT = 700


def press_and_load(page: Page, key: str) -> None:
    """Press a key that submits a form, and wait for the answer page to load."""
    with page.expect_navigation():
        page.keyboard.press(key)
    page.wait_for_load_state()


def type_and_add(page: Page, name: str) -> None:
    """Type into the name field and press Enter, with no pointer, as a keyboard user does."""
    page.locator("#assignee-name").focus()
    page.locator("#assignee-name").fill(name)
    press_and_load(page, "Enter")


def add_name(page: Page, address: str, name: str) -> None:
    page.goto(address + "/people")
    type_and_add(page, name)


def focused_id(page: Page) -> str:
    return page.evaluate("document.activeElement && document.activeElement.id")


def focused_tag(page: Page) -> str:
    return page.evaluate("document.activeElement && document.activeElement.tagName")


def listed(page: Page) -> list[str]:
    return [text or "" for text in page.locator(".assignee-name").all_text_contents()]


def assert_added_name_is_focused(page: Page, name: str, position: int) -> None:
    span = page.locator(f"#assignee-{position}")
    assert span.text_content() == name
    assert page.locator("main b, main i").count() == 0
    expect(span).to_be_focused()
    assert focused_id(page) == f"assignee-{position}"
    expect(span).to_be_in_viewport()
    expect(span).to_have_accessible_description(f"You added '{name}' to the assignees.")
    assert page.locator("#assignees-outcome").evaluate("e => e === document.activeElement") is False
    page.keyboard.press("Tab")
    assert focused_id(page) == f"remove-{position}"


def test_added_markup_name_has_browser_focus_and_accessible_description(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-82, CP-86, CP-87, CP-103, QC-36: the first focus test on an element that is no control."""
    add_name(page, tracker.address, HOSTILE)
    assert_added_name_is_focused(page, HOSTILE, 1)
    add_name(page, tracker.address, QUOTED)
    assert listed(page) == [HOSTILE, QUOTED]
    assert_added_name_is_focused(page, QUOTED, 2)
    assert page.locator("script").count() == 0
    saved = tracker.saved_file.read_bytes()
    assert json.loads(saved)["assignees"] == [HOSTILE, QUOTED]
    page.reload()
    page.go_back()
    page.go_forward()
    page.wait_for_load_state()
    assert listed(page) == [HOSTILE, QUOTED]
    assert tracker.saved_file.read_bytes() == saved


def test_people_keyboard_refusals_and_removal_keep_focus_at_the_action(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-83, CP-87, CP-89, CP-90, CP-94, CP-96; design T15."""
    page.on("dialog", lambda dialog: (_ for _ in ()).throw(AssertionError("a confirmation")))
    page.goto(tracker.address + "/people")
    expect(page.locator("main")).to_contain_text("There are no assignees yet.")
    type_and_add(page, "  ")
    expect(page.locator("#assignee-name")).to_be_focused()
    assert focused_id(page) == "assignee-name"
    expect(page.locator("#assignee-name")).to_have_value("  ")
    expect(page.locator("#assignee-name")).to_have_accessible_description(
        "An assignee needs a name. Type one."
    )
    type_and_add(page, "Dana")
    expect(page.locator("#assignee-1")).to_be_focused()
    assert focused_id(page) == "assignee-1"
    type_and_add(page, "Dana")
    expect(page.locator("#assignee-name")).to_be_focused()
    assert focused_id(page) == "assignee-name"
    expect(page.locator("#assignee-name")).to_have_value("Dana")
    expect(page.locator("#assignee-name")).to_have_accessible_description(
        "An assignee named 'Dana' is already on the list. Choose a different name."
    )
    assert focused_tag(page) == "INPUT"

    stops = []
    page.locator("body").evaluate("() => document.activeElement.blur()")
    for _ in range(8):
        page.keyboard.press("Tab")
        stops.append(focused_id(page))
    assert not any(stop.startswith("assignee-") and stop != "assignee-name" for stop in stops)
    assert page.locator(".assignee-name").evaluate("e => e.tabIndex") == -1

    page.locator("#remove-1").focus()
    press_and_load(page, "Enter")
    assert listed(page) == []
    expect(page.locator("#assignees-heading")).to_be_focused()
    assert focused_id(page) == "assignees-heading"
    expect(page.locator("#assignees-heading")).to_have_accessible_description(
        "You removed 'Dana' from the assignees, and tasks that already carry the name keep it."
    )
    expect(page.locator("main")).to_contain_text("There are no assignees yet.")
    expect(page.locator("#assignee-name")).to_be_visible()
    ring = page.locator("#assignees-heading").evaluate(
        "e => [getComputedStyle(e).outlineStyle, getComputedStyle(e).outlineWidth]"
    )
    assert ring == ["solid", "2px"]

    type_and_add(page, "Dana")
    expect(page.locator("#assignee-1")).to_be_focused()
    ring = page.locator("#assignee-1").evaluate(
        "e => [getComputedStyle(e).outlineStyle, getComputedStyle(e).outlineWidth]"
    )
    assert ring == ["solid", "2px"]


def test_a_stale_remove_focuses_the_heading_with_the_reason_and_a_reload_link(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-96."""
    add_name(page, tracker.address, "Dana")
    other = page.context.new_page()
    other.goto(tracker.address + "/people")
    other.locator("#remove-1").focus()
    with other.expect_navigation():
        other.keyboard.press("Enter")
    other.wait_for_load_state()
    other.close()
    saved = tracker.saved_file.read_bytes()
    page.locator("#remove-1").focus()
    press_and_load(page, "Enter")
    expect(page.locator("#assignees-heading")).to_be_focused()
    assert focused_id(page) == "assignees-heading"
    expect(page.locator("#assignees-heading")).to_have_accessible_description(
        "The name 'Dana' is no longer on the assignee list. Open People again to reload the list."
    )
    assert listed(page) == []
    assert tracker.saved_file.read_bytes() == saved
    page.locator("#assignees-outcome a").click()
    page.wait_for_load_state()
    assert page.url == tracker.address + "/people"
    assert page.locator("#assignees-outcome").count() == 0


def test_long_people_names_and_controls_reflow(tracker: RunningTracker, page: Page) -> None:
    """CP-83, CP-87; design T15, UX-A7: no sideways scroll at 1280 pixels at 400% zoom."""
    page.set_viewport_size({"width": NARROW_WIDTH, "height": NARROW_HEIGHT})
    long_names = ["w" * 190, "word " * 38, "Dana"]
    for name in long_names:
        add_name(page, tracker.address, name)
    page.goto(tracker.address + "/people")
    overflow = page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 0
    buttons = page.locator("button", has_text="Remove")
    assert buttons.count() == 3
    for index in range(3):
        box = buttons.nth(index).bounding_box()
        assert box is not None and box["x"] >= 0 and box["x"] + box["width"] <= NARROW_WIDTH
    add_name(page, tracker.address, "Last " + "y" * 150)
    expect(page.locator("#assignee-4")).to_be_focused()
    outline = page.locator("#assignee-4").evaluate("e => getComputedStyle(e).outlineStyle")
    assert focused_id(page) == "assignee-4" and outline == "solid"
    overflow = page.evaluate(
        "document.documentElement.scrollWidth - document.documentElement.clientWidth"
    )
    assert overflow <= 0


def test_the_list_is_there_after_a_stop_and_a_start(
    trackers: TrackerFactory, location: Path, page: Page
) -> None:
    """CP-99, AC-6 (the assignee half)."""
    first = trackers.start(location)
    for name in ("Dana", " Ari ", "dana"):
        add_name(page, first.address, name)
    status, stderr = first.stop()
    assert status == 0 and "Traceback" not in stderr
    second = trackers.start(location)
    page.goto(second.address + "/people")
    assert listed(page) == ["Dana", " Ari ", "dana"]


def test_a_tracker_started_on_data_from_before_the_list_keeps_its_projects(
    trackers: TrackerFactory, location: Path, page: Page
) -> None:
    """CP-100: every project is there, the list is empty, and the file's bytes are unchanged."""
    location.mkdir(parents=True)
    saved_file = location / "tracker.json"
    legacy = {
        "next_project_id": 3,
        "projects": [
            {"id": 1, "name": "Alpha", "description": "first"},
            {"id": 2, "name": "Beta", "description": ""},
        ],
    }
    saved_file.write_bytes(json.dumps(legacy).encode("utf-8"))
    before = saved_file.read_bytes()
    tracker = trackers.start(location)
    assert tracker.first_line.startswith("The tracker is running.")
    page.goto(tracker.address + "/")
    expect(page.locator("ul.project-list a")).to_have_text(["Alpha", "Beta"])
    page.goto(tracker.address + "/people")
    expect(page.locator("main")).to_contain_text("There are no assignees yet.")
    assert saved_file.read_bytes() == before


def keyboard_to_name_field(page: Page) -> None:
    """Tab from wherever focus is to the Your name field: no pointer, no programmatic focus."""
    for _ in range(12):
        if focused_id(page) == "operator-name":
            return
        page.keyboard.press("Tab")
    raise AssertionError("Tab never reached the Your name field")


def type_and_save_name(page: Page, name: str) -> None:
    """Reach the Your name field with Tab, replace its text by typing, and press Enter."""
    keyboard_to_name_field(page)
    page.keyboard.press("ControlOrMeta+A")
    if name:
        page.keyboard.type(name)
    else:
        page.keyboard.press("Backspace")
    press_and_load(page, "Enter")


def test_operator_name_keyboard_set_replace_reload_and_blank_refusal(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-216, CP-220, CP-224, CP-236: a name is set and replaced from the keyboard, survives a
    reload and history movement without another save, and a blank one is refused with the typed
    text kept and the saved data unchanged."""
    page.goto(tracker.address + "/people")
    expect(page.locator("#operator-name")).to_have_value("")
    type_and_save_name(page, "Sam")
    expect(page.locator("#operator-name")).to_be_focused()
    expect(page.locator("#operator-name")).to_have_value("Sam")
    expect(page.locator("#operator-name")).to_have_accessible_description(
        "You set your name to 'Sam'."
    )
    type_and_save_name(page, " Sam Lee ")
    expect(page.locator("#operator-name")).to_have_value(" Sam Lee ")
    saved = tracker.saved_file.read_bytes()
    assert json.loads(saved)["operator_name"] == " Sam Lee "
    page.reload()
    page.go_back()
    page.go_forward()
    page.wait_for_load_state()
    expect(page.locator("#operator-name")).to_have_value(" Sam Lee ")
    assert tracker.saved_file.read_bytes() == saved
    page.goto(tracker.address + "/people")
    type_and_save_name(page, "   ")
    expect(page.locator("#operator-name")).to_be_focused()
    expect(page.locator("#operator-name")).to_have_value("   ")
    expect(page.locator("#operator-name")).to_have_accessible_description(
        "Your name can't be blank. Type a name."
    )
    assert focused_id(page) == "operator-name"
    assert tracker.saved_file.read_bytes() == saved
    assert json.loads(tracker.saved_file.read_bytes())["operator_name"] == " Sam Lee "


def test_operator_markup_name_has_exact_browser_text_and_description(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-225, CP-236, QC-36: a name holding `<`, `&` and quotes is the exact field value and the
    exact completion text, with normal structure around it, focus on the field and its
    description."""
    page.goto(tracker.address + "/people")
    type_and_save_name(page, QUOTED)
    expect(page.locator("#operator-name")).to_have_value(QUOTED)
    expect(page.locator("#operator-name")).to_be_focused()
    expect(page.locator("#operator-name-outcome")).to_have_text(f"You set your name to '{QUOTED}'.")
    expect(page.locator("#operator-name")).to_have_accessible_description(
        f"You set your name to '{QUOTED}'."
    )
    assert page.locator("main b, main i, script").count() == 0
    assert page.locator("section").count() == 2
    assert page.locator("#your-name-heading").text_content() == "Your name"
    assert json.loads(tracker.saved_file.read_bytes())["operator_name"] == QUOTED
