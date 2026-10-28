"""End-to-end tests of the sort controls, in Chromium against a tracker run as a process (layer 5).

Realizes SRS FR-36 and NFR-12 (state is carried by words and every control has a name) for what
only a browser settles: the keys that choose a sort and press Apply or Clear with scripting off,
reload and Back and Forward, where focus and the viewport land on a refusal, and how the added
controls reflow. Checks the change spec rules CP-437, CP-442 and CP-445 and the design's T9. The
first test runs with scripting off, since the product sends no script (docs/nfdr.md § 9, layer 5).
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
BY_PRIORITY_DESCENDING = ["Write docs", "Ship", "Fix bug"]
MAXIMUM_TABS = 60
FULL_WIDTH = 1280
ZOOM_FACTOR = 4


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 10, 11, 12, 0, tzinfo=UTC)


def seeded(location: Path) -> None:
    """Save a project of three tasks before the tracker process starts, as a past run left it."""
    tracker = Tracker(empty_state(), SavedData(location), FixedClock())
    tracker.create_project("Alpha", "")
    tracker.add_assignee("Dana")
    tracker.add_task(1, TITLES[0], "high", "Dana", "2000-01-01")
    tracker.add_task(1, TITLES[1], "low", "", "2999-01-01")
    tracker.add_task(1, TITLES[2], "medium", "", "")


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


def test_sort_apply_reload_back_and_clear_work_with_keyboard_and_no_script(
    trackers, location: Path, scriptless: Page
) -> None:
    """CP-437, CP-445, T9: browser keys alone choose Sort by and Direction and press Apply; the
    order, the count and the address follow, a reload and Back and Forward show the same list, and
    Clear returns every task in due date order."""
    seeded(location)
    running = trackers.start(location)
    scriptless.goto(f"{running.address}/projects/1")
    assert listed(scriptless) == list(TITLES)
    tab_until(scriptless, "sort-field")
    scriptless.keyboard.type("Priority")
    tab_until(scriptless, "sort-direction")
    scriptless.keyboard.type("Descending")
    tab_until(scriptless, "filter-apply")
    scriptless.keyboard.press("Enter")
    scriptless.wait_for_url(lambda url: "sort_field=priority" in url)
    query = parse_qs(urlsplit(scriptless.url).query, keep_blank_values=True)
    assert query["sort_field"] == ["priority"] and query["sort_direction"] == ["descending"]
    assert urlsplit(scriptless.url).path == "/projects/1"
    assert listed(scriptless) == BY_PRIORITY_DESCENDING
    assert "This project has 3 tasks." in scriptless.inner_text("main")
    sorted_url = scriptless.url
    scriptless.reload()
    assert scriptless.url == sorted_url and listed(scriptless) == BY_PRIORITY_DESCENDING
    scriptless.goto(f"{running.address}/projects/1")
    assert listed(scriptless) == list(TITLES)
    scriptless.go_back()
    assert scriptless.url == sorted_url and listed(scriptless) == BY_PRIORITY_DESCENDING
    scriptless.go_forward()
    assert listed(scriptless) == list(TITLES)
    scriptless.go_back()
    tab_until(scriptless, "filter-clear")
    scriptless.keyboard.press("Enter")
    scriptless.wait_for_url(lambda url: urlsplit(url).query == "")
    assert listed(scriptless) == list(TITLES)
    assert "This project has" not in scriptless.inner_text("main")


def test_sort_refusal_focus_and_the_added_controls_reflow(
    trackers, location: Path, browser: Browser
) -> None:
    """CP-442, T9: the first refused sort control receives focus and is in view with its reason
    describing it and Clear in view, and at 400% zoom the added controls stack with the filter's
    without clipping or widening the page."""
    seeded(location)
    running = trackers.start(location)
    context = browser.new_context()
    context.set_default_timeout(15000)
    page = context.new_page()
    page.goto(f"{running.address}/projects/1?sort_field=colour&sort_direction=sideways")
    field = page.locator("#sort-field")
    expect(field).to_be_focused()
    expect(field).to_be_in_viewport()
    expect(page.locator("#filter-clear")).to_be_in_viewport()
    assert "Sort by can't be 'colour'" in page.inner_text("#sort-field-reason")
    assert page.get_attribute("#sort-field", "aria-describedby") == "sort-field-reason"
    assert "Direction can't be 'sideways'" in page.inner_text("#sort-direction-reason")
    page.set_viewport_size({"width": FULL_WIDTH // ZOOM_FACTOR, "height": 800})
    page.goto(f"{running.address}/projects/1?sort_field=title")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    box = lambda selector: page.locator(selector).bounding_box()
    assert box("#sort-field")["x"] == box("#sort-direction")["x"] == box("#filter-status")["x"]
    assert box("#sort-direction")["y"] > box("#sort-field")["y"] > box("#filter-overdue")["y"]
    for selector in ("#sort-field", "#sort-direction"):
        found = box(selector)
        assert found["x"] >= 0 and found["x"] + found["width"] <= FULL_WIDTH // ZOOM_FACTOR
    context.close()
