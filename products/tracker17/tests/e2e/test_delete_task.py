"""End-to-end tests of deleting a task, in Chromium against a tracker run as a process (layer 5).

Checks SRS FR-17 (deleting a task with its comments), NFR-12 (state is carried by words and every
control has a name), NFR-3 (nothing is saved until the confirming press) and AC-12. Change spec
rules CP-531, CP-532, CP-534, CP-584, CP-585 and CP-589, and the design's T5, T8 and T18, are the
ones each test names. Only what
a browser settles is tested here: the keys that press a button, the real double click, the focus
landing, the history traversal and the sizes of the controls: Delete task's first press, in each
form the page shows it, and its confirmation are both DESIGN's full-size control height (change
spec rules CP-609 to CP-612 and CP-614, design T1 to T3).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import Locator, Page, expect
from test_delete_project import CONTROL_HEIGHT, box_of
from test_moves import PINNED_BROWSER

if TYPE_CHECKING:
    from conftest import RunningTracker

TITLE = "Set up CI"
SENTENCE = f"Delete '{TITLE}'? You can't undo this."
COMPLETION = f"You deleted '{TITLE}'."
OPENED = "delete_confirm"
BACKED = "delete_back"
FAILED = "delete_failed"
FAILURE = f"The tracker couldn't delete '{TITLE}', and nothing was changed. Try again."
PARTIAL_FILE = "tracker.json.partial"
TOLERANCE = 0.5
TRIGGER = "Delete task"
NOT_FOUND_HEADING = "There's no task at this address"
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


def test_confirmation_is_loaded_afresh_after_confirming(
    tracker: RunningTracker, history_page: Page
) -> None:
    """CP-584, CP-585, CP-589, T18: on the pinned browser, going back to the confirmation after
    confirming issues a new request and shows the task's not-found page, and so does Forward then
    Back again; the saved bytes do not change."""
    page = history_page
    browser = page.context.browser
    assert browser is not None and browser.version == PINNED_BROWSER
    page.add_init_script(RECORDER)
    open_task(page, tracker.address)
    page.goto(f"{tracker.address}/tasks/1")
    page.get_by_role("button", name=TRIGGER).click()
    page.wait_for_url(lambda url: OPENED in url)
    confirmation = page.url
    page.get_by_role("button", name=TRIGGER).click()
    page.wait_for_url(lambda url: "deleted_task=" in url)
    landing = page.url
    after = saved_bytes(tracker)
    requested: list[str] = []
    page.on("request", lambda request: requested.append(request.url))

    for step in ("back", "forward-then-back"):
        if step == "forward-then-back":
            page.go_forward(wait_until="commit")
            page.wait_for_url(landing, wait_until="commit")
        requested.clear()
        page.go_back(wait_until="commit")
        page.wait_for_url(confirmation, wait_until="commit")
        expect(page.locator("main h1")).to_have_text(NOT_FOUND_HEADING)
        expect(page.locator(".confirm-strip")).to_have_count(0)
        assert confirmation in requested, step
        page.wait_for_function("window.__shows && window.__shows.length >= 1")
        assert page.evaluate("window.__shows") == [False], step
        assert saved_bytes(tracker) == after, step


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


def assert_full_size(box: dict[str, float], what: str) -> None:
    assert abs(box["height"] - CONTROL_HEIGHT) <= TOLERANCE, f"{what} is {box['height']}px tall"


def secondary_look(button: Locator) -> dict[str, str]:
    """The paint DESIGN's secondary button gives: surface fill, ink type, and a muted edge."""
    return button.evaluate(
        "(e) => { const s = getComputedStyle(e);"
        " return {fill: s.backgroundColor, ink: s.color, edge: s.borderTopColor,"
        " edgeWidth: s.borderTopWidth}; }"
    )


@pytest.mark.parametrize("scrolled", [False, True], ids=["short-page", "scrolled-page"])
def test_delete_task_confirmation_matches_full_size_trigger(
    tracker: RunningTracker, page: Page, scrolled: bool
) -> None:
    """CP-609 to CP-612, CP-614, T1: the first press and the confirming button are each 36px and
    within half a pixel of each other, the sentence is at least as tall as the first press, Back out
    is 36px, the first press is painted as the secondary button Back out is, and the sentence
    covers the whole rectangle the first press stood in, in document coordinates across the two
    page loads."""
    open_task(page, tracker.address)
    page.goto(f"{tracker.address}/tasks/1")
    trigger = page.get_by_role("button", name=TRIGGER)
    if scrolled:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        assert page.evaluate("window.scrollY") > 0
    first_press = box_of(trigger)
    first_press_look = secondary_look(trigger)
    if scrolled:
        trigger.click()
    else:
        page.goto(f"{tracker.address}/tasks/1?{OPENED}")
    page.wait_for_url(lambda url: OPENED in url)
    page.wait_for_load_state("load")
    sentence = box_of(page.locator("#confirm-sentence"))
    confirm = box_of(page.locator(".confirm-strip button.button-confirm"))
    back_out = page.locator(".confirm-strip button.button-secondary")
    back = box_of(back_out)
    assert first_press_look == secondary_look(back_out), (
        "the first press is not the secondary button"
    )
    assert_full_size(first_press, "the first press")
    assert_full_size(confirm, "the confirming button")
    assert_full_size(back, "Back out")
    assert abs(first_press["height"] - confirm["height"]) <= TOLERANCE
    assert sentence["height"] >= CONTROL_HEIGHT - TOLERANCE
    assert sentence["height"] >= first_press["height"] - TOLERANCE
    assert sentence["x"] <= first_press["x"] + TOLERANCE
    assert sentence["y"] <= first_press["y"] + TOLERANCE
    assert sentence["x"] + sentence["width"] >= first_press["x"] + first_press["width"] - TOLERANCE
    assert (
        sentence["y"] + sentence["height"] >= first_press["y"] + first_press["height"] - TOLERANCE
    )


def test_delete_task_back_out_restores_full_size_trigger(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-609, T2: Back out restores the first press at 36px with focus and no strip, and saves
    nothing."""
    open_task(page, tracker.address)
    page.goto(f"{tracker.address}/tasks/1?{OPENED}")
    before = saved_bytes(tracker)
    page.get_by_role("button", name="Back out").click()
    page.wait_for_url(lambda url: BACKED in url)
    trigger = page.get_by_role("button", name=TRIGGER)
    expect(trigger).to_be_focused()
    expect(page.locator(".confirm-strip")).to_have_count(0)
    assert_full_size(box_of(trigger), "the restored first press")
    assert saved_bytes(tracker) == before


def test_delete_task_save_failure_restores_full_size_trigger(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-609, T3: when the confirming press cannot save, the restored first press is 36px, has
    focus and is described by the failure line, and the task and the saved bytes remain. The save
    fails because a directory stands where the saver writes its partial file."""
    open_task(page, tracker.address)
    page.goto(f"{tracker.address}/tasks/1?{OPENED}")
    before = saved_bytes(tracker)
    obstruction = tracker.location / PARTIAL_FILE
    obstruction.mkdir()
    try:
        page.locator(".confirm-strip button.button-confirm").click()
        page.wait_for_url(lambda url: FAILED in url)
        trigger = page.get_by_role("button", name=TRIGGER)
        expect(trigger).to_be_focused()
        expect(page.locator("#delete-failure")).to_have_text(FAILURE)
        expect(trigger).to_have_accessible_description(FAILURE)
        expect(page.locator(".confirm-strip")).to_have_count(0)
        assert_full_size(box_of(trigger), "the first press after a failed save")
        assert saved_bytes(tracker) == before
        assert b"Set up CI" in saved_bytes(tracker)
    finally:
        obstruction.rmdir()
