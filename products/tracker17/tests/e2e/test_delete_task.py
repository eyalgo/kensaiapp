"""End-to-end tests of deleting a task, in Chromium against a tracker run as a process (layer 5).

Checks SRS FR-17 (deleting a task with its comments), NFR-12 (state is carried by words and every
control has a name), NFR-3 (nothing is saved until the confirming press) and AC-12. Change spec
rules CP-531, CP-532 and CP-534, and the design's T5 and T8, are the ones each test names. Only what
a browser settles is tested here: the keys that press a button, the real double click, the focus
landing and the history traversal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import Page, expect

if TYPE_CHECKING:
    from conftest import RunningTracker

TITLE = "Set up CI"
SENTENCE = f"Delete '{TITLE}'? You can't undo this."
COMPLETION = f"You deleted '{TITLE}'."
OPENED = "delete_confirm"
BACKED = "delete_back"
TRIGGER = "Delete task"
KEYS = ("Enter", "Space")
MAXIMUM_TABS = 60
RECORDER = (
    "window.__shows = [];"
    " window.addEventListener('pageshow', e => window.__shows.push(e.persisted));"
)


def open_task(page: Page, address: str, title: str = TITLE) -> None:
    """Create a project and a task through the pages, and land on the task's page."""
    page.goto(address + "/")
    page.locator("#name").fill("Alpha")
    page.get_by_role("button", name="Create").click()
    page.wait_for_load_state()
    page.locator("#task-title").fill(title)
    page.locator("#task-title").press("Enter")
    page.wait_for_load_state()
    expect(page.locator("main h1")).to_be_focused()


def saved_bytes(tracker: RunningTracker) -> bytes:
    return tracker.saved_file.read_bytes()


def active_text(page: Page) -> str:
    return page.evaluate("document.activeElement.textContent.trim()")


def tab_to_trigger(page: Page) -> None:
    """Press Tab from the top of the page until the Delete task control has focus."""
    page.locator("body").click(position={"x": 1, "y": 1})
    for _ in range(MAXIMUM_TABS):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.tagName") == "BUTTON" and (
            active_text(page) == TRIGGER
        ):
            return
    raise AssertionError("Tab never reached Delete task")


def open_with_key(page: Page, key: str) -> None:
    tab_to_trigger(page)
    page.keyboard.press(key)
    page.wait_for_url(lambda url: OPENED in url)
    page.wait_for_load_state("load")
    expect(page.locator("#confirm-sentence")).to_be_focused()


@pytest.mark.parametrize("key", KEYS)
def test_delete_confirmation_is_keyboard_operable(
    tracker: RunningTracker, page: Page, key: str
) -> None:
    """CP-531 to CP-534, T5: open by keyboard with the sentence focused and in view; the next two
    Tabs reach confirm, then Back out; keyboard Back out restores the trigger with focus; keyboard
    confirm lands on the project heading, described by the completion line."""
    open_task(page, tracker.address)
    page.goto(f"{tracker.address}/tasks/1")
    before = saved_bytes(tracker)
    open_with_key(page, key)
    sentence = page.locator("#confirm-sentence")
    expect(sentence).to_have_text(SENTENCE)
    expect(sentence).to_be_in_viewport()
    assert page.evaluate("document.activeElement.tabIndex") == -1
    page.keyboard.press("Tab")
    assert active_text(page) == TRIGGER
    page.keyboard.press("Tab")
    assert active_text(page) == "Back out"
    page.keyboard.press(key)
    page.wait_for_url(lambda url: BACKED in url)
    trigger = page.get_by_role("button", name=TRIGGER)
    expect(trigger).to_be_focused()
    expect(page.locator(".confirm-strip")).to_have_count(0)
    assert saved_bytes(tracker) == before
    open_with_key(page, key)
    page.keyboard.press("Tab")
    assert active_text(page) == TRIGGER
    page.keyboard.press(key)
    page.wait_for_url(lambda url: "deleted_task=" in url)
    heading = page.locator("main h1")
    expect(heading).to_be_focused()
    expect(heading).to_have_accessible_description(COMPLETION)
    assert page.evaluate("window.scrollY") == 0
    assert b"Set up CI" not in saved_bytes(tracker)


def locator_box(page: Page, selector: str) -> dict[str, float]:
    box = page.locator(selector).bounding_box()
    assert box is not None
    return box


@pytest.mark.parametrize("scrolled", [False, True], ids=["short-page", "scrolled-page"])
def test_double_press_never_confirms_deletion(
    tracker: RunningTracker, page: Page, scrolled: bool
) -> None:
    """T5: a real double click at the trigger's coordinates opens the confirmation and deletes
    nothing; a third click at the same point hits the sentence; the strip stands where the
    trigger stood and the saved bytes are untouched."""
    open_task(page, tracker.address)
    page.goto(f"{tracker.address}/tasks/1")
    trigger = page.get_by_role("button", name=TRIGGER)
    if scrolled:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    trigger.scroll_into_view_if_needed()
    before = saved_bytes(tracker)
    box = trigger.bounding_box()
    assert box is not None
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.dblclick(x, y)
    page.wait_for_url(lambda url: OPENED in url)
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
    assert "deleted_task" not in page.url and saved_bytes(tracker) == before
    assert b"Set up CI" in saved_bytes(tracker)


def test_completion_survives_actual_reload_back_and_forward(
    tracker: RunningTracker, history_page: Page
) -> None:
    """CP-534, T5: confirm, reload, navigate away, then use actual Back and Forward; the same
    completion line stays and the saved bytes do not change."""
    page = history_page
    page.add_init_script(RECORDER)
    open_task(page, tracker.address)
    page.goto(f"{tracker.address}/tasks/1")
    page.get_by_role("button", name=TRIGGER).click()
    page.wait_for_url(lambda url: OPENED in url)
    page.get_by_role("button", name=TRIGGER).click()
    page.wait_for_url(lambda url: "deleted_task=" in url)
    landing = page.url
    after = saved_bytes(tracker)
    expect(page.locator("#deleted-line")).to_have_text(COMPLETION)
    page.reload()
    expect(page.locator("#deleted-line")).to_have_text(COMPLETION)
    page.goto(f"{tracker.address}/people")
    page.go_back(wait_until="commit")
    page.wait_for_url(landing, wait_until="commit")
    expect(page.locator("#deleted-line")).to_have_text(COMPLETION)
    page.go_forward(wait_until="commit")
    page.go_back(wait_until="commit")
    expect(page.locator("#deleted-line")).to_have_text(COMPLETION)
    assert saved_bytes(tracker) == after


@pytest.mark.parametrize("title", ['<b>x</b> & "q"', "it's ünï"])
def test_deletion_titles_stay_text_in_the_browser(
    tracker: RunningTracker, page: Page, title: str
) -> None:
    """CP-535, T8: the title shows as text in the sentence and in the completion line."""
    open_task(page, tracker.address, title)
    page.goto(f"{tracker.address}/tasks/1")
    page.get_by_role("button", name=TRIGGER).click()
    page.wait_for_url(lambda url: OPENED in url)
    expect(page.locator("#confirm-sentence")).to_have_text(
        f"Delete '{title}'? You can't undo this."
    )
    expect(page.locator("main b")).to_have_count(0)
    page.get_by_role("button", name=TRIGGER).click()
    page.wait_for_url(lambda url: "deleted_task=" in url)
    expect(page.locator("#deleted-line")).to_have_text(f"You deleted '{title}'.")
    expect(page.locator("main b")).to_have_count(0)
