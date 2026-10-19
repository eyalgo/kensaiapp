"""End-to-end tests of adding and editing a task, in Chromium against a tracker run as a process (layer 5).

Checks SRS FR-15 (creating a task), FR-16 (editing its four fields), FR-24 (a due date is a
calendar date), NFR-4 (no script) and NFR-5 (typed text is shown as text), and DR-2 (the Task
entity). Change spec rules CP-106 to CP-110, CP-114, CP-115, CP-118, CP-123, CP-124, CP-127 and
CP-133 (the add), CP-145, CP-146, CP-156, CP-161 and CP-178 (the edit) and NFDR QC-36 are the ones
each test names. The browser's own controls are used for the title limit, the date and the keyboard.
"""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING

from playwright.sync_api import Page, expect

if TYPE_CHECKING:
    from conftest import RunningTracker

MARKUP = '<b>A&B</b> "Q"'
TITLE_MAXIMUM = 200


def create_project(page: Page, address: str, name: str) -> None:
    page.goto(address + "/")
    page.locator("#name").fill(name)
    page.get_by_role("button", name="Create").click()
    page.wait_for_load_state()


def saved_tasks(tracker: RunningTracker) -> list[dict[str, object]]:
    saved = json.loads(tracker.saved_file.read_text(encoding="utf-8"))
    tasks: list[dict[str, object]] = saved["tasks"]
    return tasks


def test_browser_task_title_limit_and_native_date(tracker: RunningTracker, page: Page) -> None:
    """CP-106, CP-107, CP-118, CP-110: ordinary typing stops at the 201st character."""
    create_project(page, tracker.address, "Alpha")
    typed = "t" * (TITLE_MAXIMUM - 1)
    page.locator("#task-title").fill(typed)
    page.locator("#task-title").press_sequentially("uv")
    assert page.locator("#task-title").input_value() == typed + "u"
    page.locator("#task-title").press("Z")
    assert page.locator("#task-title").input_value() == typed + "u"
    assert len(page.locator("#task-title").input_value()) == TITLE_MAXIMUM
    page.locator("#task-due-date").fill("2026-12-01")
    assert page.locator("#task-due-date").input_value() == "2026-12-01"
    assert page.locator("#task-due-date").evaluate("e => e.type") == "date"
    page.get_by_role("button", name="Add").click()
    page.wait_for_load_state()
    assert re.fullmatch(re.escape(tracker.address) + r"/tasks/1\?added", page.url)
    (task,) = saved_tasks(tracker)
    assert task["title"] == typed + "u" and task["due_date"] == "2026-12-01"
    assert task["priority"] == "medium" and task["assignee"] is None


def test_browser_added_task_has_heading_focus_and_description(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-114, CP-123, CP-124: a keyboard add lands with the heading focused and described."""
    create_project(page, tracker.address, "Alpha")
    page.locator("#task-title").fill("  Set up CI  ")
    page.locator("#task-title").press("Enter")
    page.wait_for_load_state()
    expect(page.locator("main h1")).to_be_focused()
    heading = page.locator("main h1")
    expect(heading).to_have_text("  Set up CI  ")
    expect(heading).to_have_accessible_description("You added '  Set up CI  '.")
    assert page.evaluate("document.activeElement.id") == ""
    line = page.locator("#added-line")
    expect(line).to_have_text("You added '  Set up CI  '.")
    assert (
        page.evaluate("document.activeElement === document.getElementById('added-line')") is False
    )
    page.reload()
    expect(page.locator("#added-line")).to_have_count(1)
    page.goto(tracker.address + "/tasks/1")
    expect(page.locator("#added-line")).to_have_count(0)
    assert page.evaluate("document.activeElement.tagName") == "BODY"


def test_browser_task_markup_title_is_literal_on_task_and_project(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-127, CP-133, QC-36: markup in a title is text on the task, the list and the link."""
    create_project(page, tracker.address, "Alpha")
    page.locator("#task-title").fill(MARKUP)
    page.get_by_role("button", name="Add").click()
    page.wait_for_load_state()
    assert page.locator("main h1").text_content() == MARKUP
    assert page.title() == f"{MARKUP} - tracker17"
    assert page.locator("main b").count() == 0
    page.get_by_role("link", name="Projects").click()
    page.get_by_role("link", name="Alpha").click()
    page.wait_for_load_state()
    link = page.locator("table a")
    assert link.text_content() == MARKUP
    assert link.get_attribute("aria-label") == f"{MARKUP}, number 1 on the task list"
    assert page.locator("main b").count() == 0
    link.click()
    page.wait_for_load_state()
    assert re.fullmatch(re.escape(tracker.address) + r"/tasks/1", page.url)
    assert page.locator("main h1").text_content() == MARKUP
    assert page.locator("main b").count() == 0
    expect(page.locator("main")).not_to_contain_text("You added")


def add_task_through_page(page: Page, address: str, title: str) -> None:
    create_project(page, address, "Alpha")
    page.locator("#task-title").fill(title)
    page.get_by_role("button", name="Add").click()
    page.wait_for_load_state()


def test_browser_edit_title_is_literal_on_task_and_project(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-144, CP-178, QC-36: markup in an edited title is text on the task, form and list."""
    add_task_through_page(page, tracker.address, "Plain")
    page.locator("#edit-title").fill(MARKUP)
    page.get_by_role("button", name="Save").click()
    page.wait_for_load_state()
    assert re.fullmatch(re.escape(tracker.address) + r"/tasks/1\?saved", page.url)
    assert page.locator("main h1").text_content() == MARKUP
    assert page.locator("#edit-title").input_value() == MARKUP
    assert page.title() == f"{MARKUP} - tracker17"
    assert page.locator("main b").count() == 0
    expect(page.locator("main h1")).to_have_accessible_description(
        f"You saved changes to '{MARKUP}'."
    )
    assert saved_tasks(tracker)[0]["title"] == MARKUP
    page.get_by_role("link", name="Projects").click()
    page.get_by_role("link", name="Alpha").click()
    page.wait_for_load_state()
    link = page.locator("table a")
    assert link.text_content() == MARKUP
    assert page.locator("main b").count() == 0


def test_browser_edit_controls_and_keyboard_focus(tracker: RunningTracker, page: Page) -> None:
    """CP-145, CP-146, CP-156, CP-161: the browser's own controls, and where focus lands."""
    add_task_through_page(page, tracker.address, "Task")
    typed = "t" * (TITLE_MAXIMUM - 1)
    page.locator("#edit-title").fill(typed)
    page.locator("#edit-title").press_sequentially("uv")
    assert page.locator("#edit-title").input_value() == typed + "u"
    page.locator("#edit-due-date").fill("2026-12-01")
    assert page.locator("#edit-due-date").evaluate("e => e.type") == "date"
    page.locator("#edit-title").press("Enter")
    page.wait_for_load_state()
    expect(page.locator("main h1")).to_be_focused()
    expect(page.locator("main h1")).to_have_accessible_description(
        f"You saved changes to '{typed}u'."
    )
    assert page.locator("#edit-due-date").input_value() == "2026-12-01"
    assert saved_tasks(tracker)[0]["due_date"] == "2026-12-01"
    page.locator("#edit-due-date").fill("")
    page.locator("#edit-title").fill("")
    page.get_by_role("button", name="Save").press("Enter")
    page.wait_for_load_state()
    expect(page.locator("#edit-title")).to_be_focused()
    expect(page.locator("#edit-title")).to_have_accessible_description(
        "A task needs a title. Type one."
    )
    assert page.locator("#edit-due-date").input_value() == ""
    assert saved_tasks(tracker)[0]["due_date"] == "2026-12-01"
    page.locator("#edit-title").fill("Fixed")
    page.get_by_role("button", name="Save").click()
    page.wait_for_load_state()
    assert (
        saved_tasks(tracker)[0]["title"] == "Fixed" and saved_tasks(tracker)[0]["due_date"] is None
    )
