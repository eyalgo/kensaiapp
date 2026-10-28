"""End-to-end tests of the filter controls, in Chromium against a tracker run as a process (layer 5).

Realizes SRS FR-32 to FR-35 and NFR-12 (state is carried by words and every control has a name) for
what only a browser settles: the keys that change a choice and press Apply or Clear, where focus
and the viewport land, and how the filter row reflows. Checks the change spec rules CP-395, CP-405,
CP-411 and CP-408 and the design's T9. The first tests run with scripting off, since the product
sends no script (docs/nfdr.md § 9, layer 5).
"""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import Browser, Page, expect

from application import Tracker
from domain import empty_state
from persistence import SavedData

TITLES = ("Write docs", "Fix bug", "Ship")
MAXIMUM_TABS = 60
FULL_WIDTH = 1280
ZOOM_FACTOR = 4


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 10, 11, 12, 0, tzinfo=UTC)


def seeded(location: Path, long_title: str = "", extra_rows: int = 0) -> None:
    """Save a project of three tasks before the tracker process starts, as a past run left it.
    Extra tasks are dated, so they list before the undated last one."""
    tracker = Tracker(empty_state(), SavedData(location), FixedClock())
    tracker.create_project("Alpha", "")
    tracker.add_assignee("Dana")
    tracker.add_task(1, long_title or TITLES[0], "high", "Dana", "2000-01-01")
    tracker.add_task(1, TITLES[1], "low", "", "2999-01-01")
    tracker.add_task(1, TITLES[2], "medium", "", "")
    tracker.add_task_label(1, "bug")
    for number in range(extra_rows):
        tracker.add_task(1, f"Extra {number}", "high", "", "2000-02-01")


@pytest.fixture
def scriptless(browser: Browser) -> Iterator[Page]:
    context = browser.new_context(java_script_enabled=False)
    context.set_default_timeout(15000)
    yield context.new_page()
    context.close()


def tab_until(page: Page, identifier: str) -> None:
    """Press Tab from the top of the page until the element with this id has focus."""
    page.locator("body").click(position={"x": 1, "y": 1})
    for _ in range(MAXIMUM_TABS):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.id") == identifier:
            return
    raise AssertionError(f"Tab never reached {identifier!r}")


def listed(page: Page) -> list[str]:
    return page.locator("table.task-list tbody tr td:first-child a").all_inner_texts()


def test_filter_apply_and_clear_work_with_keyboard_and_no_script(
    trackers, location: Path, scriptless: Page
) -> None:
    """CP-395, CP-411, T9: browser keys alone change a choice, Apply and Clear; the result links, the
    count and the address follow, with scripting off."""
    seeded(location)
    running = trackers.start(location)
    scriptless.goto(f"{running.address}/projects/1")
    assert listed(scriptless) == list(TITLES)
    tab_until(scriptless, "filter-priority")
    scriptless.keyboard.type("low")
    tab_until(scriptless, "filter-overdue")
    scriptless.keyboard.press("Space")
    tab_until(scriptless, "filter-apply")
    scriptless.keyboard.press("Enter")
    scriptless.wait_for_url(lambda url: "filter_priority=low" in url)
    query = parse_qs(urlsplit(scriptless.url).query, keep_blank_values=True)
    assert query["filter_priority"] == ["low"] and query["filter_overdue"] == ["on"]
    assert urlsplit(scriptless.url).path == "/projects/1"
    expect(scriptless.locator("#filter-count, .no-match")).to_be_visible()
    assert listed(scriptless) == [] and "No tasks match this filter." in scriptless.inner_text(
        "main"
    )
    tab_until(scriptless, "filter-clear")
    scriptless.keyboard.press("Enter")
    scriptless.wait_for_url(lambda url: urlsplit(url).query == "")
    assert urlsplit(scriptless.url).query == "" and listed(scriptless) == list(TITLES)
    assert "match this filter" not in scriptless.inner_text("main")


def test_filter_refusal_focus_and_filter_row_reflow(
    trackers, location: Path, browser: Browser
) -> None:
    """CP-405, T9: the first bad control receives focus and is in view with its reason describing
    it, a valid Apply opens at the page start, and at 400% zoom the filter row stacks while only the
    table scrolls sideways."""
    seeded(location, long_title="W" * 150)
    running = trackers.start(location)
    context = browser.new_context()
    context.set_default_timeout(15000)
    page = context.new_page()
    page.goto(f"{running.address}/projects/1?filter_status=blocked&filter_due_to=x")
    status = page.locator("#filter-status")
    expect(status).to_be_focused()
    expect(status).to_be_in_viewport()
    assert "can't be 'blocked'" in page.inner_text("#filter-status-reason")
    assert page.get_attribute("#filter-status", "aria-describedby") == "filter-status-reason"
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.goto(f"{running.address}/projects/1?filter_priority=high")
    assert page.evaluate("window.scrollY") == 0
    assert page.evaluate("document.activeElement === document.body")
    page.set_viewport_size({"width": FULL_WIDTH // ZOOM_FACTOR, "height": 800})
    page.goto(f"{running.address}/projects/1")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    left = lambda selector: page.locator(selector).bounding_box()["x"]
    top = lambda selector: page.locator(selector).bounding_box()["y"]
    assert left("#filter-status") == left("#filter-priority") == left("#filter-label")
    assert top("#filter-priority") > top("#filter-status")
    assert page.evaluate(
        "(() => { const t = document.querySelector('.table-scroll');"
        " return t.scrollWidth > t.clientWidth; })()"
    )
    context.close()


@pytest.mark.parametrize("point", ["interior", "far-edge"])
@pytest.mark.parametrize("extra_rows", [0, 12])
def test_confirmation_opens_under_a_trigger_at_the_pages_bottom(
    trackers, location: Path, browser: Browser, extra_rows: int, point: str
) -> None:
    """CP-325, CP-337: the last row's cancelled button sits at the very bottom of the scrolled
    page. A double click on it opens a confirmation taller than the button, and the third click at
    the same coordinate hits the sentence, so nothing is confirmed. The guarantee holds on a short
    list and on a long one, so it does not rest on the height of what sits above the button."""
    seeded(location, extra_rows=extra_rows)
    running = trackers.start(location)
    context = browser.new_context()
    context.set_default_timeout(15000)
    page = context.new_page()
    page.goto(f"{running.address}/projects/1")
    selector = "button[aria-label=\"Move 'Ship' to cancelled\"]"
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    assert page.evaluate("window.scrollY") > 0
    before = (location / "tracker.json").read_bytes()
    box = page.locator(selector).bounding_box()
    assert box is not None
    x = box["x"] + (box["width"] / 2 if point == "interior" else box["width"] - 1.5)
    y = box["y"] + (box["height"] / 2 if point == "interior" else box["height"] - 1.5)
    page.mouse.dblclick(x, y)
    page.wait_for_url(lambda url: "move_confirm=cancelled" in url)
    page.wait_for_load_state("load")
    expect(page.locator("#confirm-sentence")).to_be_visible()
    hit = page.evaluate(
        "([x, y]) => { const e = document.elementFromPoint(x, y);"
        " return e ? e.closest('#confirm-sentence') !== null : false; }",
        [x, y],
    )
    assert hit, "the original coordinate must land on the sentence"
    page.mouse.click(x, y)
    page.wait_for_timeout(300)
    expect(page.locator(".confirm-strip")).to_have_count(1)
    assert "moved=" not in page.url
    assert (location / "tracker.json").read_bytes() == before
    context.close()


@pytest.mark.parametrize(
    ("query", "title", "status", "last_match"),
    [
        ("filter_status=todo", "Fix bug", "in-progress", False),
        ("filter_overdue=on", "Write docs", "done", True),
    ],
)
def test_off_list_completion_focus_enters_the_list_section(
    trackers,
    location: Path,
    scriptless: Page,
    query: str,
    title: str,
    status: str,
    last_match: bool,
) -> None:
    """CP-408, T9: with scripting off, moving a task out of the filtered list lands on the list
    section holding focus, the line above the results in view, and no focus on the line itself,
    including when the moved task was the last match and the no-match state follows."""
    seeded(location)
    running = trackers.start(location)
    scriptless.goto(f"{running.address}/projects/1?{query}")
    # A todo task is moved to done by way of in-progress; the row stays while it still matches.
    for step in (["in-progress"] if status == "done" else []) + [status]:
        scriptless.locator(f"button[aria-label=\"Move '{title}' to {step}\"]").click()
        scriptless.wait_for_url(lambda url, step=step: f"moved={step}" in url)
    section = scriptless.locator("#task-list")
    expect(section).to_be_focused()
    assert section.get_attribute("aria-describedby") == "move-line"
    assert scriptless.evaluate("document.activeElement.id") == "task-list"
    assert scriptless.evaluate("document.activeElement.closest('#move-line') === null")
    expect(scriptless.locator("#move-line")).to_be_in_viewport()
    assert scriptless.inner_text("#move-line") == (
        f"You moved '{title}' to {status}, and it no longer matches this filter, "
        "so it has left this list."
    )
    assert title not in listed(scriptless)
    if last_match:
        assert listed(scriptless) == []
        expect(scriptless.locator("#filter-no-match")).to_be_visible()
        assert scriptless.evaluate(
            "document.getElementById('move-line').compareDocumentPosition("
            "document.getElementById('filter-no-match')) & Node.DOCUMENT_POSITION_FOLLOWING"
        )


def test_keyboard_reaches_and_filters_all_tasks_without_script(
    trackers, location: Path, scriptless: Page
) -> None:
    """CP-459, CP-467, CP-472, T18: from a project's header, keys reach All tasks, set a filter and
    a sort, apply them, keep the choices, and clear them, with scripting off."""
    seeded(location)
    tracker = trackers.start(location)
    scriptless.goto(tracker.address + "/projects/1")
    scriptless.get_by_role("link", name="All tasks").focus()
    scriptless.keyboard.press("Enter")
    scriptless.wait_for_url(tracker.address + "/tasks")
    expect(scriptless.locator("h1")).to_have_text("All tasks")
    assert listed(scriptless) == ["Write docs", "Fix bug", "Ship"]
    tab_until(scriptless, "filter-priority")
    scriptless.keyboard.type("low")
    tab_until(scriptless, "sort-field")
    scriptless.keyboard.type("Title")
    tab_until(scriptless, "filter-apply")
    scriptless.keyboard.press("Enter")
    scriptless.wait_for_url(lambda url: "filter_priority=low" in url)
    query = parse_qs(urlsplit(scriptless.url).query)
    assert query["filter_priority"] == ["low"] and query["sort_field"] == ["title"]
    assert listed(scriptless) == ["Fix bug"]
    expect(scriptless.locator("#filter-priority")).to_have_value("low")
    tab_until(scriptless, "filter-clear")
    scriptless.keyboard.press("Enter")
    scriptless.wait_for_url(tracker.address + "/tasks")
    assert listed(scriptless) == ["Write docs", "Fix bug", "Ship"]


def test_keyboard_global_filter_sort_move_and_confirmation_keep_choices_without_script(
    trackers, location: Path, scriptless: Page
) -> None:
    """CP-475, CP-476, CP-479, T18: with scripting off, keys press a row's move on All tasks, the
    cancellation's confirmation and its back out; every landing is /tasks with the filter and sort
    kept, focus where the rules put it, and a task the filter no longer matches leaves the list."""
    seeded(location)
    tracker = trackers.start(location)
    choices = "filter_status=todo&sort_field=title&sort_direction=ascending"
    scriptless.goto(f"{tracker.address}/tasks?{choices}")
    assert listed(scriptless) == ["Fix bug", "Ship", "Write docs"]

    scriptless.get_by_role("button", name="Move 'Write docs' to in-progress").focus()
    scriptless.keyboard.press("Enter")
    scriptless.wait_for_url(lambda url: "moved=in-progress" in url)
    query = parse_qs(urlsplit(scriptless.url).query)
    assert urlsplit(scriptless.url).path == "/tasks"
    assert query["filter_status"] == ["todo"] and query["sort_field"] == ["title"]
    assert listed(scriptless) == ["Fix bug", "Ship"]
    assert scriptless.evaluate("document.activeElement.id") == "task-list"
    assert scriptless.inner_text("#move-line") == (
        "You moved 'Write docs' to in-progress, and it no longer matches this filter, "
        "so it has left this list."
    )

    before = tracker.saved_file.read_bytes()
    scriptless.get_by_role("button", name="Move 'Fix bug' to cancelled").focus()
    scriptless.keyboard.press("Enter")
    scriptless.wait_for_url(lambda url: "move_confirm=cancelled" in url)
    assert urlsplit(scriptless.url).path == "/tasks"
    assert scriptless.evaluate("document.activeElement.id") == "confirm-sentence"
    assert tracker.saved_file.read_bytes() == before

    scriptless.get_by_role("button", name="Back out").focus()
    scriptless.keyboard.press("Enter")
    scriptless.wait_for_url(lambda url: "move_back=cancelled" in url)
    assert urlsplit(scriptless.url).path == "/tasks"
    assert parse_qs(urlsplit(scriptless.url).query)["filter_status"] == ["todo"]
    assert listed(scriptless) == ["Fix bug", "Ship"]
    expect(scriptless.get_by_role("button", name="Move 'Fix bug' to cancelled")).to_be_focused()
    assert tracker.saved_file.read_bytes() == before

    scriptless.keyboard.press("Enter")
    scriptless.wait_for_url(lambda url: "move_confirm=cancelled" in url)
    scriptless.get_by_role("button", name="Move to cancelled").focus()
    scriptless.keyboard.press("Enter")
    scriptless.wait_for_url(lambda url: "moved=cancelled" in url)
    query = parse_qs(urlsplit(scriptless.url).query)
    assert urlsplit(scriptless.url).path == "/tasks"
    assert query["filter_status"] == ["todo"] and query["sort_field"] == ["title"]
    assert listed(scriptless) == ["Ship"]
    assert tracker.saved_file.read_bytes() != before
