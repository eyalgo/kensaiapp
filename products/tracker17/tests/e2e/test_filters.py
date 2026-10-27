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


def seeded(location: Path, long_title: str = "") -> None:
    """Save a project of three tasks before the tracker process starts, as a past run left it."""
    tracker = Tracker(empty_state(), SavedData(location), FixedClock())
    tracker.create_project("Alpha", "")
    tracker.add_assignee("Dana")
    tracker.add_task(1, long_title or TITLES[0], "high", "Dana", "2000-01-01")
    tracker.add_task(1, TITLES[1], "low", "", "2999-01-01")
    tracker.add_task(1, TITLES[2], "medium", "", "")
    tracker.add_task_label(1, "bug")


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
