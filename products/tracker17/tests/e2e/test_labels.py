"""End-to-end tests of adding and removing a task's labels, in Chromium against a tracker run as a
process (layer 5).

Checks SRS FR-23 (a label is added and removed from the keyboard), NFR-4 (no script) and NFR-5
(typed text is shown as text). Change spec rules CP-185 to CP-188, CP-192 to CP-195, CP-196 and
CP-207 and NFDR QC-36 are the ones each test names. The browser's own controls are used for the
label maximum and the keyboard. A second page of the same browser stands for another tab.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from playwright.sync_api import Page, expect

if TYPE_CHECKING:
    from conftest import RunningTracker

MARKUP = '<b>A&B</b> "Q"'
TITLE = "Set up CI"
LABEL_MAXIMUM = 200


def open_task(page: Page, address: str) -> None:
    """Create a project and a task through the pages, and land on the task's page."""
    page.goto(address + "/")
    page.locator("#name").fill("Alpha")
    page.get_by_role("button", name="Create").click()
    page.wait_for_load_state()
    page.locator("#task-title").fill(TITLE)
    page.locator("#task-title").press("Enter")
    page.wait_for_load_state()
    expect(page.locator("main h1")).to_be_focused()


def saved_labels(tracker: RunningTracker) -> list[str]:
    saved = json.loads(tracker.saved_file.read_text(encoding="utf-8"))
    labels: list[str] = saved["tasks"][0]["labels"]
    return labels


def add_with_keyboard(page: Page, label: str) -> None:
    page.locator("#new-label").focus()
    page.locator("#new-label").fill(label)
    page.locator("#new-label").press("Enter")
    page.wait_for_load_state()


def test_keyboard_label_add_focuses_label_with_accessible_description(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-187, CP-195, CP-207: the added label's text has focus, is in view and outside the Tab
    stops, and the completion line is its computed accessible description."""
    open_task(page, tracker.address)
    expect(page.locator("#labels")).to_contain_text(
        "This task has no labels. Type a label and press Add."
    )
    add_with_keyboard(page, "ui")
    expect(page.locator("#label-1")).to_be_focused()
    added = page.locator("#label-1")
    expect(added).to_have_text("ui")
    expect(added).to_be_in_viewport()
    assert page.evaluate("document.activeElement.tabIndex") == -1
    expect(added).to_have_accessible_description(f"You added the label 'ui' to '{TITLE}'.")
    assert saved_labels(tracker) == ["ui"]
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") == "remove-label-1"
    add_with_keyboard(page, " second ")
    expect(page.locator("#label-2")).to_be_focused()
    expect(page.locator("#label-2")).to_have_text(" second ")
    assert saved_labels(tracker) == ["ui", " second "]


def test_keyboard_label_remove_and_refusals_focus_the_action(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-190, CP-192, CP-193, CP-195, CP-207: remove from the keyboard lands on the heading; an
    empty add lands on the field; a stale remove lands on the label section."""
    open_task(page, tracker.address)
    add_with_keyboard(page, "ui")
    add_with_keyboard(page, "bug")
    page.locator("#remove-label-1").focus()
    page.locator("#remove-label-1").press("Enter")
    page.wait_for_load_state()
    expect(page.locator("main h1")).to_be_focused()
    expect(page.locator("main h1")).to_have_accessible_description(
        f"You removed the label 'ui' from '{TITLE}'."
    )
    assert saved_labels(tracker) == ["bug"]
    page.locator("#new-label").focus()
    page.locator("#new-label").press("Enter")
    page.wait_for_load_state()
    expect(page.locator("#new-label")).to_be_focused()
    expect(page.locator("#new-label")).to_have_accessible_description(
        "A label needs at least one character. Type a label."
    )
    assert saved_labels(tracker) == ["bug"]
    other = page.context.new_page()
    other.goto(tracker.address + "/tasks/1")
    other.locator("#remove-label-1").click()
    expect(other.locator("main h1")).to_be_focused()
    other.close()
    assert saved_labels(tracker) == []
    page.locator("#remove-label-1").focus()
    page.locator("#remove-label-1").press("Enter")
    page.wait_for_load_state()
    expect(page.locator("#labels")).to_be_focused()
    expect(page.locator("#labels")).to_have_accessible_description(
        f"The label 'bug' isn't on '{TITLE}'. The labels shown are the ones the task carries."
    )
    assert saved_labels(tracker) == []


def tab_until(page: Page, element_id: str, limit: int = 40) -> None:
    """Press Tab, and nothing else, until the element with this id has focus."""
    for _ in range(limit):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.id") == element_id:
            return
    raise AssertionError(f"Tab never reached #{element_id}")


def test_keyboard_alone_tabs_types_adds_and_removes_a_label(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-195 and its Example row: the operator tabs to the label field, types `bug` and presses
    Enter, then tabs to Remove beside `bug` and presses Enter; no pointer and no scripted focus."""
    open_task(page, tracker.address)
    tab_until(page, "new-label")
    page.keyboard.type("bug")
    with page.expect_navigation():
        page.keyboard.press("Enter")
    expect(page.locator("#label-1")).to_be_focused()
    assert saved_labels(tracker) == ["bug"]
    tab_until(page, "remove-label-1")
    expect(page.locator("#remove-label-1")).to_have_accessible_name(
        f"Remove label 'bug' from '{TITLE}'"
    )
    with page.expect_navigation():
        page.keyboard.press("Enter")
    expect(page.locator("main h1")).to_be_focused()
    expect(page.locator("main h1")).to_have_accessible_description(
        f"You removed the label 'bug' from '{TITLE}'."
    )
    assert saved_labels(tracker) == []


def test_markup_label_is_literal_on_task_and_project_list(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-185, CP-186, CP-188, CP-196, QC-36: markup and surrounding spaces read back literally,
    in both places and in the Remove button's name; the field's maximum is the domain's."""
    open_task(page, tracker.address)
    field = page.locator("#new-label")
    assert field.get_attribute("maxlength") == str(LABEL_MAXIMUM)
    typed = f" {MARKUP} "
    add_with_keyboard(page, typed)
    expect(page.locator("#label-1")).to_be_focused()
    assert page.locator("#label-1").text_content() == typed
    assert page.locator("main b").count() == 0
    remove = page.get_by_role("button", name=f"Remove label '{typed}' from '{TITLE}'")
    expect(remove).to_have_count(1)
    assert saved_labels(tracker) == [typed]
    page.get_by_role("link", name="Projects").click()
    page.get_by_role("link", name="Alpha").click()
    page.wait_for_load_state()
    assert page.locator("table tbody td").nth(4).text_content() == typed
    assert page.locator("main b").count() == 0
    page.goto(tracker.address + "/tasks/1")
    maximum = "m" * LABEL_MAXIMUM
    add_with_keyboard(page, maximum)
    assert saved_labels(tracker) == [typed, maximum]
