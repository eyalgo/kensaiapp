"""End-to-end tests of the moves, in Chromium against a tracker run as a process (layer 5).

Checks SRS NFR-12 (state is carried by words and every control has a name), UXD UX-A6 (a move is a
button of its own with a pointer target of at least 24 by 24 CSS pixels) and AC-13 (a moved task
shows its new status). Change spec rules CP-300, CP-303 to CP-305 and the design's R-2 (an
`autofocus` element inside a table cell) are the ones each test names. Only what a browser settles
is tested here: the keys that press a button, the pointer target, and the focus landing.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlsplit

from playwright.sync_api import Page, expect

if TYPE_CHECKING:
    from conftest import RunningTracker

TITLE = "Set up CI"
MINIMUM_TARGET = 24
MOVE_LINE = f"You moved '{TITLE}' to in-progress."
MOVE_BUTTON = "button.move-button"
MAXIMUM_TABS = 40
LANDING_QUERY = {"move_task": ["1"], "moved": ["in-progress"]}


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


def landed_at(path: str) -> Callable[[str], bool]:
    """The landing after moving task 1 to in-progress: this path, no fragment (RT-9), and the
    task and the status in the query, in whatever order the address puts them."""

    def matches(url: str) -> bool:
        parts = urlsplit(url)
        query = parse_qs(parts.query)
        return parts.path == path and not parts.fragment and query == LANDING_QUERY

    return matches


def tab_to(page: Page, name: str) -> None:
    """Press Tab from the top of the page until the control with this accessible name has focus."""
    page.locator("body").click(position={"x": 1, "y": 1})
    for _ in range(MAXIMUM_TABS):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.getAttribute('aria-label')") == name:
            return
    raise AssertionError(f"Tab never reached {name!r}")


def test_tab_to_a_rows_move_button_and_press_space_lands_on_that_rows_status_element(
    tracker: RunningTracker, page: Page
) -> None:
    """E2E1, CP-300, CP-303 to CP-305: Space presses the row's button; the page lands with that
    row's status element focused and in view, outside the Tab stops, described by the line."""
    open_task(page, tracker.address)
    page.goto(f"{tracker.address}/projects/1")
    tab_to(page, f"Move '{TITLE}' to in-progress")
    page.keyboard.press("Space")
    page.wait_for_url(landed_at("/projects/1"))
    status = page.locator("tbody tr td:nth-child(2) .status-word")
    expect(status).to_be_focused()
    expect(status).to_have_text("in-progress")
    expect(status).to_be_in_viewport()
    assert page.evaluate("document.activeElement.tabIndex") == -1
    expect(status).to_have_accessible_description(MOVE_LINE)
    expect(page.locator("tbody tr td:nth-child(7)").locator(MOVE_BUTTON)).to_have_text(
        ["done", "todo"]
    )


def test_the_same_move_from_the_task_page_with_enter_lands_on_the_status_area(
    tracker: RunningTracker, page: Page
) -> None:
    """E2E1, CP-300, CP-303 to CP-305: Enter presses the status area's button; the status word
    has focus, is in view and is described by the line."""
    open_task(page, tracker.address)
    tab_to(page, f"Move '{TITLE}' to in-progress")
    page.keyboard.press("Enter")
    page.wait_for_url(landed_at("/tasks/1"))
    status = page.locator("#task-status")
    expect(status).to_be_focused()
    expect(status).to_have_text("in-progress")
    expect(status).to_be_in_viewport()
    assert page.evaluate("document.activeElement.tabIndex") == -1
    expect(status).to_have_accessible_description(MOVE_LINE)
    expect(page.locator("#status").locator(MOVE_BUTTON)).to_have_text(["done", "todo"])


def test_every_move_button_is_at_least_24_by_24_pixels(tracker: RunningTracker, page: Page) -> None:
    """UX-A6: each move button's bounding box, on the row and in the status area, in both of the
    task's statuses that offer a move."""
    open_task(page, tracker.address)
    addresses = (f"{tracker.address}/projects/1", f"{tracker.address}/tasks/1")
    for offered in (1, 2):
        if offered == 2:
            # The task leaves todo, the status with one move, for in-progress, the one with two.
            page.goto(addresses[1])
            page.get_by_role("button", name=f"Move '{TITLE}' to in-progress").click()
            page.wait_for_url(landed_at("/tasks/1"))
        for address in addresses:
            page.goto(address)
            buttons = page.locator(MOVE_BUTTON)
            expect(buttons).to_have_count(offered)
            for index in range(offered):
                box = buttons.nth(index).bounding_box()
                assert box is not None
                assert box["width"] >= MINIMUM_TARGET and box["height"] >= MINIMUM_TARGET
