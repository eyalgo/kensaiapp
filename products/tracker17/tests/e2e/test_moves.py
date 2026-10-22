"""End-to-end tests of the moves, in Chromium against a tracker run as a process (layer 5).

Checks SRS NFR-12 (state is carried by words and every control has a name), UXD UX-A6 (a move is a
button of its own with a pointer target of at least 24 by 24 CSS pixels) and AC-13 (a moved task
shows its new status). Change spec rules CP-300, CP-303 to CP-305, the out-of-date-move change's CP-359, CP-366 and
CP-370, and the design's R-2 (an
`autofocus` element inside a table cell) are the ones each test names, and so are the
cancel-confirmation change's CP-320, CP-323 to CP-327, CP-329, CP-331, CP-337 and CP-342, and the
history-after-confirm change's CP-343 to CP-348 and CP-350. Only what a browser settles
is tested here: the keys that press a button, the pointer target, and the focus landing.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import Locator, Page, expect

if TYPE_CHECKING:
    from conftest import RunningTracker

TITLE = "Set up CI"
MINIMUM_TARGET = 24
MOVE_LINE = f"You moved '{TITLE}' to in-progress."
MOVE_BUTTON = "button.move-button"
MAXIMUM_TABS = 40
LANDING_QUERY = {"move_task": ["1"], "moved": ["in-progress"]}


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
        ["done", "cancelled", "todo"]
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
    expect(page.locator("#status").locator(MOVE_BUTTON)).to_have_text(["done", "cancelled", "todo"])


def test_every_move_button_is_at_least_24_by_24_pixels(tracker: RunningTracker, page: Page) -> None:
    """UX-A6: each move button's bounding box, on the row and in the status area, in both of the
    task's statuses that offer a move."""
    open_task(page, tracker.address)
    addresses = (f"{tracker.address}/projects/1", f"{tracker.address}/tasks/1")
    for offered in (2, 3):
        if offered == 3:
            # The task leaves todo, the status with two moves, for in-progress, the one with three.
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


# --- The cancelled move and its in-place confirmation (cancel-confirmation, CP-320 to CP-337) ---

CANCELLED_NAME = f"Move '{TITLE}' to cancelled"
SENTENCE = f"Move '{TITLE}' to cancelled? A cancelled task can't be moved again."
CANCELLED_LINE = f"You moved '{TITLE}' to cancelled."
DONE_SUBMISSION = f"The status of '{TITLE}' has changed to done. A task in done can't be moved."
DONE_ADDRESS = (
    f"The status of '{TITLE}' is done, which doesn't allow a move to cancelled. "
    "A task in done can't be moved."
)
CANCELLED_ADDRESS = (
    f"The status of '{TITLE}' is cancelled, which doesn't allow a move to cancelled. "
    "A task in cancelled can't be moved."
)
OPENED = "move_confirm=cancelled"
PLACES = ("list", "task")
KEYS = ("Enter", "Space")
SENTENCE_LOCATOR = "#confirm-sentence"
MANY_ROWS = 60
FAR_ROW = 40


def place_address(tracker: RunningTracker, place: str) -> str:
    return f"{tracker.address}/projects/1" if place == "list" else f"{tracker.address}/tasks/1"


def saved_bytes(tracker: RunningTracker) -> bytes:
    return tracker.saved_file.read_bytes()


def active_text(page: Page) -> str:
    return page.evaluate("document.activeElement.textContent.trim()")


def open_with_key(page: Page, key: str, name: str = CANCELLED_NAME) -> None:
    tab_to(page, name)
    page.keyboard.press(key)
    page.wait_for_url(lambda url: OPENED in url)
    # Gate on the finished load: Tab pressed before the autofocus lands starts from the page top.
    expect(page.locator(SENTENCE_LOCATOR)).to_be_focused()


def in_progress(page: Page) -> None:
    page.get_by_role("button", name=f"Move '{TITLE}' to in-progress").click()
    page.wait_for_url(lambda url: "moved=in-progress" in url)


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("place", PLACES)
def test_keyboard_opening_focuses_the_visible_sentence(
    tracker: RunningTracker, page: Page, place: str, key: str
) -> None:
    """CP-320, CP-324, CP-337: Enter or Space on the cancelled button opens the confirmation; the
    sentence alone has focus, in view, with a visible ring and no Tab stop of its own; a repeated
    Enter or Space changes nothing; the next two Tabs reach confirm, then back out."""
    open_task(page, tracker.address)
    page.goto(place_address(tracker, place))
    before = saved_bytes(tracker)
    open_with_key(page, key)
    sentence = page.locator(SENTENCE_LOCATOR)
    expect(sentence).to_have_text(SENTENCE)
    expect(sentence).to_be_focused()
    expect(sentence).to_be_in_viewport()
    assert page.evaluate("document.activeElement.tabIndex") == -1
    ring = page.evaluate(
        "(() => { const s = getComputedStyle(document.activeElement);"
        " return [s.outlineStyle, parseFloat(s.outlineWidth)]; })()"
    )
    assert ring[0] != "none" and ring[1] >= 2
    url = page.url
    for repeated in ("Enter", "Space", "Enter"):
        page.keyboard.press(repeated)
    assert page.url == url and saved_bytes(tracker) == before
    expect(page.locator(".confirm-strip")).to_have_count(1)
    expect(sentence).to_be_focused()
    page.keyboard.press("Tab")
    assert active_text(page) == "Move to cancelled"
    page.keyboard.press("Tab")
    assert active_text(page) == "Back out"


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("place", PLACES)
def test_keyboard_confirming_and_back_out_use_their_own_intents(
    tracker: RunningTracker, page: Page, place: str, key: str
) -> None:
    """CP-327, CP-329, CP-337: confirming saves and lands on the described cancelled status;
    backing out saves nothing and returns visible focus to the trigger, with no line, and a later
    Tab traversal has no sentence stop."""
    open_task(page, tracker.address)
    page.goto(place_address(tracker, place))
    before = saved_bytes(tracker)
    open_with_key(page, "Enter")
    page.keyboard.press("Tab")
    page.keyboard.press("Tab")
    assert active_text(page) == "Back out"
    page.keyboard.press(key)
    page.wait_for_url(lambda url: "move_back=cancelled" in url)
    trigger = page.get_by_role("button", name=CANCELLED_NAME)
    expect(trigger).to_be_focused()
    expect(trigger).to_be_in_viewport()
    expect(page.locator(".confirm-strip")).to_have_count(0)
    expect(page.locator("#move-line")).to_have_count(0)
    assert saved_bytes(tracker) == before
    for _ in range(MAXIMUM_TABS):
        page.keyboard.press("Tab")
        assert page.evaluate("document.activeElement.id") != "confirm-sentence"
    open_with_key(page, "Enter")
    page.keyboard.press("Tab")
    assert active_text(page) == "Move to cancelled"
    page.keyboard.press(key)
    page.wait_for_url(lambda url: "moved=cancelled" in url)
    status = page.locator(".status-word")
    expect(status).to_be_focused()
    expect(status).to_have_text("cancelled")
    expect(status).to_be_in_viewport()
    expect(status).to_have_accessible_description(CANCELLED_LINE)
    assert page.evaluate("document.activeElement.tabIndex") == -1
    expect(page.locator(MOVE_BUTTON)).to_have_count(0)
    assert b'"cancelled"' in saved_bytes(tracker)


def box_of(page: Page, selector: str) -> dict[str, float]:
    return locator_box(page.locator(selector))


def locator_box(locator: Locator) -> dict[str, float]:
    """The element's box in document coordinates, so a scroll between two measurements cancels."""
    return locator.evaluate(
        "(e) => { const r = e.getBoundingClientRect();"
        " return {x: r.x + window.scrollX, y: r.y + window.scrollY,"
        " width: r.width, height: r.height}; }"
    )


@pytest.mark.parametrize("place", PLACES)
def test_confirmation_preserves_trigger_geometry_and_target_sizes(
    tracker: RunningTracker, page: Page, place: str
) -> None:
    """CP-320, CP-322, CP-323: the sentence covers the whole rectangle the cancelled button stood
    in and is at least as tall; confirm is as tall as the trigger and sits below it; all three
    controls are at least 24 by 24 pixels. The title is long and holds markup, shown as typed."""
    long_title = '<b>Set up</b> & "quote" ' + "a-long-wordless-title-part " * 6
    page.goto(tracker.address + "/")
    page.locator("#name").fill("Alpha")
    page.get_by_role("button", name="Create").click()
    page.wait_for_load_state()
    page.locator("#task-title").fill(long_title)
    page.locator("#task-title").press("Enter")
    page.wait_for_load_state()
    page.goto(place_address(tracker, place))
    name = f"Move '{long_title}' to cancelled"
    trigger = page.get_by_role("button", name=name)
    old = locator_box(trigger)
    trigger.click()
    page.wait_for_url(lambda url: OPENED in url)
    sentence = box_of(page, SENTENCE_LOCATOR)
    confirm = box_of(page, ".button-confirm")
    back = box_of(page, ".button-secondary")
    assert sentence["x"] <= old["x"] + 0.5 and sentence["y"] <= old["y"] + 0.5
    assert sentence["x"] + sentence["width"] >= old["x"] + old["width"] - 0.5
    assert sentence["y"] + sentence["height"] >= old["y"] + old["height"] - 0.5
    assert sentence["height"] >= old["height"] - 0.5
    assert abs(confirm["height"] - old["height"]) <= 0.5
    assert confirm["y"] >= old["y"] + old["height"] - 0.5
    for box in (confirm, back, sentence):
        assert box["width"] >= MINIMUM_TARGET and box["height"] >= MINIMUM_TARGET
    expect(page.locator(SENTENCE_LOCATOR)).to_have_text(
        f"Move '{long_title}' to cancelled? A cancelled task can't be moved again."
    )


def add_rows(page: Page, address: str) -> None:
    """Create a project and MANY_ROWS tasks, the far one first among the titles the test names."""
    page.goto(address + "/")
    page.locator("#name").fill("Alpha")
    page.get_by_role("button", name="Create").click()
    page.wait_for_load_state()
    for number in range(1, MANY_ROWS + 1):
        page.locator("#task-title").fill(f"Row {number}")
        page.locator("#task-title").press("Enter")
        page.wait_for_load_state()
        page.goto(f"{address}/projects/1")


def scroll_to_middle(page: Page, selector: str) -> None:
    """A nonzero, partial scroll that leaves the element at the middle of the viewport."""
    page.evaluate(
        "(selector) => { const r = document.querySelector(selector).getBoundingClientRect();"
        " window.scrollBy(0, r.top + r.height / 2 - window.innerHeight / 2); }",
        selector,
    )


@pytest.mark.parametrize("point", ["interior", "far-edge"])
@pytest.mark.parametrize("case", ["short-row", "task-page", "row-40-of-60"])
def test_double_click_never_confirms_at_the_original_trigger_coordinates(
    tracker: RunningTracker, page: Page, case: str, point: str
) -> None:
    """CP-325, CP-337: a real double click on the cancelled button, then a third click at the same
    coordinate once the new document is in, which hits the sentence; the confirmation is showing
    and nothing is saved."""
    if case == "row-40-of-60":
        add_rows(page, tracker.address)
        title = f"Row {FAR_ROW}"
        page.goto(f"{tracker.address}/projects/1")
        selector = f"button[aria-label=\"Move '{title}' to cancelled\"]"
        scroll_to_middle(page, selector)
        assert page.evaluate("window.scrollY") > 0
    else:
        open_task(page, tracker.address)
        title = TITLE
        page.goto(place_address(tracker, "list" if case == "short-row" else "task"))
        selector = f"button[aria-label=\"Move '{title}' to cancelled\"]"
        if case == "task-page":
            scroll_to_middle(page, selector)
    before = saved_bytes(tracker)
    box = page.locator(selector).bounding_box()
    assert box is not None
    x = box["x"] + (box["width"] / 2 if point == "interior" else box["width"] - 1.5)
    y = box["y"] + (box["height"] / 2 if point == "interior" else box["height"] - 1.5)
    page.mouse.dblclick(x, y)
    page.wait_for_url(lambda url: OPENED in url)
    page.wait_for_load_state("load")
    expect(page.locator(SENTENCE_LOCATOR)).to_be_visible()
    hit = page.evaluate(
        "([x, y]) => { const e = document.elementFromPoint(x, y);"
        " return e ? e.closest('#confirm-sentence') !== null : false; }",
        [x, y],
    )
    assert hit, "the original coordinate must land on the sentence"
    page.mouse.click(x, y)
    page.wait_for_timeout(300)
    expect(page.locator(".confirm-strip")).to_have_count(1)
    assert OPENED in page.url and "moved=" not in page.url
    assert saved_bytes(tracker) == before
    assert b'"cancelled"' not in saved_bytes(tracker)


@pytest.mark.parametrize("place", PLACES)
def test_stale_first_press_refuses_at_the_visible_current_status(
    tracker: RunningTracker, page: Page, place: str
) -> None:
    """CP-331, CP-337, CP-359, CP-370: a second tab takes the task to done; the first tab's
    cancelled press opens no confirmation and saves nothing, and the current status is focused, in
    view and described by the overtaken press's line."""
    open_task(page, tracker.address)
    page.goto(place_address(tracker, place))
    other = page.context.new_page()
    other.goto(f"{tracker.address}/tasks/1")
    in_progress(other)
    other.get_by_role("button", name=f"Move '{TITLE}' to done").click()
    other.wait_for_url(lambda url: "moved=done" in url)
    other.close()
    before = saved_bytes(tracker)
    page.get_by_role("button", name=CANCELLED_NAME).click()
    page.wait_for_url(lambda url: "move_refused=not-allowed" in url)
    expect(page.locator(".confirm-strip")).to_have_count(0)
    status = page.locator(".status-word")
    expect(status).to_be_focused()
    expect(status).to_have_text("done")
    expect(status).to_be_in_viewport()
    expect(status).to_have_accessible_description(DONE_SUBMISSION)
    assert saved_bytes(tracker) == before


# Titles holding `<`, `&` and a double quote (CP-359, CP-361). The spec's own title stays text even
# if it reached the page unescaped, so the second one forms an element unless it is escaped.
HOSTILE_TITLES = ('a < b & "c"', '<b>a</b> & "c"')


@pytest.mark.parametrize("title", HOSTILE_TITLES)
@pytest.mark.parametrize("place", PLACES)
def test_overtaken_press_shows_the_title_as_typed(
    tracker: RunningTracker, page: Page, place: str, title: str
) -> None:
    """CP-359, CP-366, QC-36: a title holding `<`, `&` and a double quote reaches the overtaken
    press's line as text, once: the browser reads the line as typed and finds no element in it."""
    open_task(page, tracker.address, title)
    page.goto(place_address(tracker, place))
    other = page.context.new_page()
    other.goto(f"{tracker.address}/tasks/1")
    for move in ("in-progress", "done"):
        other.get_by_role("button", name=f"Move '{title}' to {move}", exact=True).click()
        other.wait_for_url(lambda url, move=move: f"moved={move}" in url)
    other.close()
    before = saved_bytes(tracker)
    page.get_by_role("button", name=f"Move '{title}' to in-progress", exact=True).click()
    page.wait_for_url(lambda url: "move_refused=not-allowed" in url)
    status = page.locator(".status-word")
    expect(status).to_be_focused()
    expect(status).to_have_accessible_description(
        f"The status of '{title}' has changed to done. A task in done can't be moved."
    )
    expect(page.locator("#move-line *")).to_have_count(0)
    assert saved_bytes(tracker) == before


def test_real_history_traversal_revalidates_the_confirmation(
    tracker: RunningTracker, history_page: Page
) -> None:
    """CP-326, CP-331, CP-337, CP-343 to CP-345, CP-347, CP-370: with the browser's history cache
    available, reload, back and forward before confirming save nothing; after confirming, going
    back to the old confirmation shows the saved-status refusal and no strip, as a fresh load; a
    successful ordinary move in a second tab invalidates an old confirmation the same way. The
    cache is shown live by an ordinary page restored from it in this run."""
    page = history_page
    page.add_init_script(RECORDER)
    open_task(page, tracker.address)
    ordinary = f"{tracker.address}/tasks/1"
    page.goto(ordinary)
    before = saved_bytes(tracker)
    page.get_by_role("button", name=CANCELLED_NAME).click()
    page.wait_for_url(lambda url: OPENED in url)
    expect(page.locator(".confirm-strip")).to_have_count(1)
    page.reload()
    expect(page.locator(SENTENCE_LOCATOR)).to_be_focused()
    # The cache is live: the ordinary page before the press comes back from it, so the proof below
    # is not vacuous.
    page.go_back(wait_until="commit")
    page.wait_for_function(RESTORED)
    assert page.url == ordinary
    page.go_forward(wait_until="commit")
    expect(page.locator(".confirm-strip")).to_have_count(1)
    expect(page.locator(SENTENCE_LOCATOR)).to_be_focused()
    assert fresh_load(page)
    assert saved_bytes(tracker) == before
    page.get_by_role("button", name="Move to cancelled").click()
    page.wait_for_url(lambda url: "moved=cancelled" in url)
    after = saved_bytes(tracker)
    page.go_back(wait_until="commit")
    expect(page.locator(".confirm-strip")).to_have_count(0)
    status = page.locator(".status-word")
    expect(status).to_have_accessible_description(CANCELLED_ADDRESS)
    assert fresh_load(page)
    assert saved_bytes(tracker) == after
    # A second tab's successful ordinary move leaves no eligible old confirmation behind.
    page.goto(f"{tracker.address}/projects/1")
    page.locator("#task-title").fill("Second")
    page.locator("#task-title").press("Enter")
    page.wait_for_load_state()
    second_name = "Move 'Second' to cancelled"
    page.get_by_role("button", name=second_name).click()
    page.wait_for_url(lambda url: OPENED in url)
    confirmation = page.url
    page.goto(f"{tracker.address}/projects/1")
    other = page.context.new_page()
    other.goto(f"{tracker.address}/tasks/2")
    other.get_by_role("button", name="Move 'Second' to in-progress").click()
    other.wait_for_url(lambda url: "moved=in-progress" in url)
    other.get_by_role("button", name="Move 'Second' to done").click()
    other.wait_for_url(lambda url: "moved=done" in url)
    other.close()
    page.go_back(wait_until="commit")
    assert page.url == confirmation
    expect(page.locator(".confirm-strip")).to_have_count(0)
    assert fresh_load(page)


@pytest.mark.parametrize("title", HOSTILE_TITLES)
@pytest.mark.parametrize("place", PLACES)
def test_address_refusal_shows_the_title_as_typed(
    tracker: RunningTracker, page: Page, place: str, title: str
) -> None:
    """CP-361, CP-366, QC-36: the confirmation's address for a done task whose title holds `<`, `&`
    and a double quote shows the title in the address refusal as text, once: the browser reads the
    line as typed and finds no element in it, and nothing is saved."""
    open_task(page, tracker.address, title)
    for move in ("in-progress", "done"):
        page.get_by_role("button", name=f"Move '{title}' to {move}", exact=True).click()
        page.wait_for_url(lambda url, move=move: f"moved={move}" in url)
    before = saved_bytes(tracker)
    page.goto(f"{place_address(tracker, place)}?move_task=1&{OPENED}")
    status = page.locator(".status-word")
    expect(status).to_be_focused()
    expect(status).to_have_accessible_description(
        f"The status of '{title}' is done, which doesn't allow a move to cancelled. "
        "A task in done can't be moved."
    )
    expect(page.locator("#move-line *")).to_have_count(0)
    assert saved_bytes(tracker) == before


PINNED_BROWSER = "153.0.8010.12"
CONTROL_TITLE = "Control"
PEOPLE = "/people"
# Test-side only: every document records each pageshow it receives, so a fresh load reads [False]
# and a page restored from the history cache ends in True. The product's pages carry no script.
RECORDER = (
    "window.__shows = [];"
    " window.addEventListener('pageshow', e => window.__shows.push(e.persisted));"
)
RESTORED = "window.__shows && window.__shows.at(-1) === true"
SCENARIOS = [
    pytest.param(("here", ""), id="confirm-here"),
    pytest.param(("done", "after-leaving"), id="other-tab-done-after-leaving"),
    pytest.param(("cancelled", "after-leaving"), id="other-tab-cancelled-after-leaving"),
    pytest.param(("done", "before-leaving"), id="other-tab-done-while-active"),
    pytest.param(("cancelled", "before-leaving"), id="other-tab-cancelled-while-active"),
]


def fresh_load(page: Page) -> bool:
    """True once this document has reported its first pageshow, and it was not a cache restore.

    Waits for the explicit observation: a document with no recorder entry is not a fresh load."""
    page.wait_for_function("window.__shows && window.__shows.length >= 1")
    return page.evaluate("window.__shows") == [False]


def acted_on_scope(page: Page, place: str) -> Locator:
    """The acted-on task's row on the project's page, or the whole main area of its own page."""
    return page.locator("tbody tr", has_text=TITLE) if place == "list" else page.locator("main")


def expect_saved_status_at(
    page: Page, place: str, address: str, word: str, reason: str, *, seen_refusal: bool = False
) -> None:
    """A return to the confirmation's address: the saved status and no confirmation anywhere.

    The first return after the status changed must be a fresh load. A later return may restore the
    refusal page that first return loaded, which is the saved status and never a confirmation;
    even then the document began as a fresh load."""
    assert page.url == address
    scope = acted_on_scope(page, place)
    expect(scope.locator(".confirm-strip")).to_have_count(0)
    expect(page.locator(SENTENCE_LOCATOR)).to_have_count(0)
    for name in ("Move to cancelled", "Back out"):
        expect(scope.get_by_role("button", name=name)).to_have_count(0)
    expect(scope.locator(MOVE_BUTTON)).to_have_count(0)
    status = scope.locator(".status-word")
    expect(status).to_have_text(word)
    expect(status).to_be_focused()
    expect(status).to_be_in_viewport()
    expect(status).to_have_accessible_description(reason)
    if place == "list":
        control = page.locator("tbody tr", has_text=CONTROL_TITLE)
        expect(control.locator(MOVE_BUTTON)).to_have_count(2)
        expect(control.locator(".confirm-strip")).to_have_count(0)
    shows = page.evaluate("window.__shows")
    assert shows == [False] or (seen_refusal and shows == [False, True])


def move_in_other_tab(tracker: RunningTracker, page: Page, actor: str) -> None:
    """A second tab takes the task to done by its ordinary moves, or confirms it to cancelled."""
    other = page.context.new_page()
    other.goto(f"{tracker.address}/tasks/1")
    if actor == "done":
        in_progress(other)
        other.get_by_role("button", name=f"Move '{TITLE}' to done").click()
        other.wait_for_url(lambda url: "moved=done" in url)
    else:
        other.get_by_role("button", name=CANCELLED_NAME).click()
        other.wait_for_url(lambda url: OPENED in url)
        other.get_by_role("button", name="Move to cancelled").click()
        other.wait_for_url(lambda url: "moved=cancelled" in url)
    other.close()


@pytest.mark.parametrize("scenario", SCENARIOS)
@pytest.mark.parametrize("place", PLACES)
def test_history_matrix_revalidates_current_saved_status(
    tracker: RunningTracker, history_page: Page, place: str, scenario: tuple[str, str]
) -> None:
    """CP-343 to CP-345, CP-347: on the pinned browser with its history cache available, an ordinary
    page is restored from that cache in this run, and every return to a confirmation's address, on
    the task's page and at its row, by Back or Forward, after this tab or another tab left the task
    at done or cancelled, is a fresh load of the saved status: no strip, sentence or controls,
    status focus in view, the saved-status reason, and the saved bytes untouched by each step."""
    actor, timing = scenario
    page = history_page
    browser = page.context.browser
    assert browser is not None and browser.version == PINNED_BROWSER
    page.add_init_script(RECORDER)
    open_task(page, tracker.address)
    page.goto(f"{tracker.address}/projects/1")
    page.locator("#task-title").fill(CONTROL_TITLE)
    page.locator("#task-title").press("Enter")
    page.wait_for_load_state()
    ordinary = place_address(tracker, place)
    page.goto(ordinary)
    start = saved_bytes(tracker)
    page.get_by_role("button", name=CANCELLED_NAME).click()
    page.wait_for_url(lambda url: OPENED in url)
    confirmation = page.url
    expect(page.locator(".confirm-strip")).to_have_count(1)
    expect(page.locator(SENTENCE_LOCATOR)).to_be_focused()
    page.reload()
    expect(page.locator(SENTENCE_LOCATOR)).to_be_focused()
    assert saved_bytes(tracker) == start
    # The cache is live: the ordinary page before the press comes back from it, so the proof below
    # is not vacuous.
    page.go_back(wait_until="commit")
    page.wait_for_function(RESTORED)
    assert page.url == ordinary
    expect(page.get_by_role("button", name=CANCELLED_NAME)).to_be_visible()
    assert saved_bytes(tracker) == start
    page.go_forward(wait_until="commit")
    assert page.url == confirmation
    expect(page.locator(".confirm-strip")).to_have_count(1)
    expect(page.locator(SENTENCE_LOCATOR)).to_be_focused()
    assert page.evaluate("window.__shows") == [False]
    assert saved_bytes(tracker) == start
    if actor == "here":
        page.get_by_role("button", name="Move to cancelled").click()
        page.wait_for_url(lambda url: "moved=cancelled" in url)
        final = page.url
        word, reason = "cancelled", CANCELLED_ADDRESS
    else:
        final = f"{tracker.address}{PEOPLE}"
        if timing == "after-leaving":
            page.goto(final)
        move_in_other_tab(tracker, page, actor)
        if timing == "before-leaving":
            page.goto(final)
        word, reason = actor, DONE_ADDRESS if actor == "done" else CANCELLED_ADDRESS
    saved = saved_bytes(tracker)
    assert (saved != start) and (word.encode() in saved)
    page.go_back(wait_until="commit")
    expect_saved_status_at(page, place, confirmation, word, reason)
    assert saved_bytes(tracker) == saved
    if actor == "here":
        page.go_back(wait_until="commit")
        assert page.url == ordinary
        assert saved_bytes(tracker) == saved
        page.go_forward(wait_until="commit")
        expect_saved_status_at(page, place, confirmation, word, reason, seen_refusal=True)
        assert saved_bytes(tracker) == saved
    page.go_forward(wait_until="commit")
    assert page.url == final
    assert saved_bytes(tracker) == saved
    page.go_back(wait_until="commit")
    expect_saved_status_at(page, place, confirmation, word, reason, seen_refusal=True)
    assert saved_bytes(tracker) == saved


@pytest.mark.parametrize("key", KEYS)
def test_keyboard_opening_on_a_far_row_focuses_the_visible_sentence(
    tracker: RunningTracker, page: Page, key: str
) -> None:
    """CP-324, CP-337: row 40 of 60, the list scrolled part-way: the key opens the confirmation,
    the sentence has focus and is in view with its ring, and Tab reaches confirm, then back out."""
    add_rows(page, tracker.address)
    page.goto(f"{tracker.address}/projects/1")
    selector = f"button[aria-label=\"Move 'Row {FAR_ROW}' to cancelled\"]"
    scroll_to_middle(page, selector)
    assert page.evaluate("window.scrollY") > 0
    page.locator(selector).focus()
    before = saved_bytes(tracker)
    page.keyboard.press(key)
    page.wait_for_url(lambda url: OPENED in url)
    sentence = page.locator(SENTENCE_LOCATOR)
    expect(sentence).to_be_focused()
    expect(sentence).to_be_in_viewport()
    ring = page.evaluate("getComputedStyle(document.activeElement).outlineStyle")
    assert ring != "none" and page.evaluate("document.activeElement.tabIndex") == -1
    page.keyboard.press("Tab")
    assert active_text(page) == "Move to cancelled"
    page.keyboard.press("Tab")
    assert active_text(page) == "Back out"
    assert saved_bytes(tracker) == before
