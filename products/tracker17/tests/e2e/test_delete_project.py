"""End-to-end tests of deleting a project, in Chromium against a tracker run as a process (layer 5).

Checks SRS FR-13 (deleting a project with its tasks and comments), NFR-12 (state is carried by words
and every control has a name), NFR-3 (nothing is saved until the confirming press), NFR-5 (typed text
is shown as text) and AC-12. Change spec rules CP-571, CP-573, CP-576, CP-577, CP-584 and CP-589, and
the design's T16 and T17, are the ones each test names. Only what a browser settles is tested here:
the keys that press a button, the real double click, the focus landing, the control sizes and the
history traversal.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import Locator, Page, expect
from test_moves import PINNED_BROWSER

from application import Tracker
from domain import empty_state
from persistence import SavedData

if TYPE_CHECKING:
    from conftest import RunningTracker, TrackerFactory

NAME = "Alpha"
TRIGGER = "Delete project"
BACK_OUT = "Back out"
OPENED = "project_delete_confirm"
BACKED = "project_delete_back"
LANDED = "deleted_project="
NOT_FOUND_HEADING = "There's no project at this address"
KEYS = ("Enter", "Space")
MAXIMUM_TABS = 80
MANY_TASKS = 60
CONTROL_HEIGHT = 36
ROW_CONTROL_HEIGHT = 28
RECORDER = (
    "window.__shows = [];"
    " window.addEventListener('pageshow', e => window.__shows.push(e.persisted));"
)


class SeedClock:
    def now(self) -> datetime:
        return datetime(2026, 10, 28, 9, 0, tzinfo=UTC)


def seed(location: Path, name: str = NAME, tasks: int = 1) -> None:
    """Save a project holding `tasks` tasks, so a long list needs no sixty page loads."""
    tracker = Tracker(empty_state(), SavedData(location), SeedClock())
    tracker.create_project(name, "")
    for number in range(1, tasks + 1):
        tracker.add_task(1, f"Row {number}", "", "", "")


def sentence_for(name: str, count: int) -> str:
    if count == 0:
        return f"Delete '{name}', which has no tasks? You can't undo this."
    noun = "1 task" if count == 1 else f"{count} tasks"
    return f"Delete '{name}' and its {noun}? You can't undo this."


def completion_for(name: str, count: int) -> str:
    if count == 0:
        return f"You deleted '{name}', which had no tasks."
    noun = "1 task" if count == 1 else f"{count} tasks"
    return f"You deleted '{name}' and its {noun}."


def started(trackers: TrackerFactory, location: Path, **kwargs: object) -> RunningTracker:
    seed(location, **kwargs)  # type: ignore[arg-type]
    return trackers.start(location)


def saved_bytes(tracker: RunningTracker) -> bytes:
    return tracker.saved_file.read_bytes()


def active_text(page: Page) -> str:
    return page.evaluate("document.activeElement.textContent.trim()")


def tab_to(page: Page, label: str) -> None:
    """Press Tab from the top of the page until the button with this label has focus."""
    page.locator("body").click(position={"x": 1, "y": 1})
    for _ in range(MAXIMUM_TABS):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.tagName") == "BUTTON" and (
            active_text(page) == label
        ):
            return
    raise AssertionError(f"Tab never reached {label}")


def open_with_key(page: Page, key: str) -> None:
    tab_to(page, TRIGGER)
    page.keyboard.press(key)
    page.wait_for_url(lambda url: OPENED in url)
    page.wait_for_load_state("load")
    expect(page.locator("#confirm-sentence")).to_be_focused()


def box_of(locator: Locator) -> dict[str, float]:
    """The element's box in document coordinates, so a scroll between two measurements cancels."""
    return locator.evaluate(
        "(e) => { const r = e.getBoundingClientRect();"
        " return {x: r.x + window.scrollX, y: r.y + window.scrollY,"
        " width: r.width, height: r.height}; }"
    )


@pytest.mark.parametrize("key", KEYS)
@pytest.mark.parametrize("tasks", [1, 0], ids=["short-page", "empty-page"])
def test_project_confirmation_is_keyboard_operable(
    trackers: TrackerFactory, location: Path, page: Page, key: str, tasks: int
) -> None:
    """CP-571, CP-573, CP-576, T16: open by keyboard with the sentence focused and in view; the
    next two Tabs reach the confirming control, then Back out; keyboard Back out restores the
    trigger with focus; keyboard confirm lands on the Projects heading, described by the line."""
    tracker = started(trackers, location, tasks=tasks)
    page.goto(f"{tracker.address}/projects/1")
    before = saved_bytes(tracker)
    open_with_key(page, key)
    sentence = page.locator("#confirm-sentence")
    expect(sentence).to_have_text(sentence_for(NAME, tasks))
    expect(sentence).to_be_in_viewport()
    assert page.evaluate("document.activeElement.tabIndex") == -1
    page.keyboard.press("Tab")
    assert active_text(page) == TRIGGER
    page.keyboard.press("Tab")
    assert active_text(page) == BACK_OUT
    page.keyboard.press(key)
    page.wait_for_url(lambda url: BACKED in url)
    expect(page.get_by_role("button", name=TRIGGER)).to_be_focused()
    expect(page.locator(".confirm-strip")).to_have_count(0)
    assert saved_bytes(tracker) == before
    open_with_key(page, key)
    page.keyboard.press("Tab")
    assert active_text(page) == TRIGGER
    page.keyboard.press(key)
    page.wait_for_url(lambda url: LANDED in url)
    heading = page.locator("main h1")
    expect(heading).to_be_focused()
    expect(heading).to_have_accessible_description(completion_for(NAME, tasks))
    assert page.evaluate("window.scrollY") == 0
    assert b"Alpha" not in saved_bytes(tracker)


@pytest.mark.parametrize(
    "name", [NAME, "A project name long enough to wrap " * 4], ids=["short", "long"]
)
@pytest.mark.parametrize("position", ["part-way", "bottom"])
def test_double_press_never_confirms_project_deletion(
    trackers: TrackerFactory, location: Path, page: Page, position: str, name: str
) -> None:
    """CP-571, CP-589, T16: on a 60-task list, scrolled part-way and at the page's bottom, a real
    double click at the trigger's coordinates only opens the confirmation; the sentence then covers
    that spot, a further click there cannot confirm, and the saved bytes do not change."""
    tracker = started(trackers, location, name=name, tasks=MANY_TASKS)
    page.goto(f"{tracker.address}/projects/1")
    trigger = page.get_by_role("button", name=TRIGGER)
    if position == "bottom":
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    else:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        trigger.scroll_into_view_if_needed()
        assert page.evaluate("window.scrollY") > 0
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
    assert LANDED not in page.url and saved_bytes(tracker) == before
    assert b"Row 1" in saved_bytes(tracker)


def test_project_strip_uses_full_size_controls(
    trackers: TrackerFactory, location: Path, page: Page
) -> None:
    """CP-571, T16: the trigger, the sentence's spot and the confirming control share DESIGN's
    control height and Back out stays full size; the existing task contexts are not resized."""
    tracker = started(trackers, location, tasks=1)
    page.goto(f"{tracker.address}/projects/1")
    trigger = box_of(page.get_by_role("button", name=TRIGGER))
    page.get_by_role("button", name=TRIGGER).click()
    page.wait_for_url(lambda url: OPENED in url)
    sentence = box_of(page.locator("#confirm-sentence"))
    confirm = box_of(page.locator(".confirm-strip button.button-confirm"))
    back = box_of(page.locator(".confirm-strip button.button-secondary"))
    assert abs(trigger["height"] - CONTROL_HEIGHT) <= 0.5
    assert sentence["x"] <= trigger["x"] + 0.5 and sentence["y"] <= trigger["y"] + 0.5
    assert sentence["x"] + sentence["width"] >= trigger["x"] + trigger["width"] - 0.5
    assert sentence["y"] + sentence["height"] >= trigger["y"] + trigger["height"] - 0.5
    assert sentence["height"] >= CONTROL_HEIGHT - 0.5
    assert abs(confirm["height"] - CONTROL_HEIGHT) <= 0.5
    assert abs(back["height"] - CONTROL_HEIGHT) <= 0.5
    assert confirm["y"] >= trigger["y"] + trigger["height"] - 0.5
    for box in (confirm, back, sentence):
        assert box["width"] >= 24 and box["height"] >= 24
    page.goto(f"{tracker.address}/projects/1?move_task=1&move_confirm=cancelled")
    move_confirm = box_of(page.locator(".confirm-strip button.button-confirm"))
    assert abs(move_confirm["height"] - ROW_CONTROL_HEIGHT) <= 0.5
    page.goto(f"{tracker.address}/tasks/1?delete_confirm")
    task_confirm = box_of(page.locator(".confirm-strip button.button-confirm"))
    assert abs(task_confirm["height"] - ROW_CONTROL_HEIGHT) <= 0.5


def create_project(page: Page, address: str, name: str, titles: tuple[str, ...]) -> None:
    """Create a project and its tasks through the pages."""
    page.goto(address + "/")
    page.locator("#name").fill(name)
    page.get_by_role("button", name="Create").click()
    page.wait_for_load_state()
    for title in titles:
        page.locator("#task-title").fill(title)
        page.locator("#task-title").press("Enter")
        page.wait_for_load_state()
        page.goto(f"{address}/projects/1")


@pytest.mark.parametrize("name", [NAME, '<b>R&D "x"</b>'], ids=["plain", "hostile"])
def test_project_completion_survives_actual_reload_back_and_forward(
    tracker: RunningTracker, history_page: Page, name: str
) -> None:
    """CP-576, CP-577, T17: confirm, reload, navigate away, then use actual Back and Forward; the
    same completion line and heading stay, no further save happens, and a hostile name shows
    exactly as typed with nothing injected."""
    page = history_page
    page.add_init_script(RECORDER)
    create_project(page, tracker.address, name, ("One", "Two"))
    page.get_by_role("button", name=TRIGGER).click()
    page.wait_for_url(lambda url: OPENED in url)
    expect(page.locator("#confirm-sentence")).to_have_text(sentence_for(name, 2))
    page.get_by_role("button", name=TRIGGER).click()
    page.wait_for_url(lambda url: LANDED in url)
    landing = page.url
    after = saved_bytes(tracker)
    line = completion_for(name, 2)
    heading = page.locator("main h1")
    expect(heading).to_be_focused()
    expect(heading).to_have_accessible_description(line)
    expect(page.locator("#deleted-project-line")).to_have_text(line)
    expect(page.locator("main b")).to_have_count(0)
    assert b"One" not in saved_bytes(tracker)
    page.reload()
    expect(page.locator("#deleted-project-line")).to_have_text(line)
    page.goto(f"{tracker.address}/people")
    page.go_back(wait_until="commit")
    page.wait_for_url(landing, wait_until="commit")
    expect(page.locator("#deleted-project-line")).to_have_text(line)
    page.go_forward(wait_until="commit")
    page.go_back(wait_until="commit")
    expect(page.locator("#deleted-project-line")).to_have_text(line)
    expect(page.locator("main b")).to_have_count(0)
    assert saved_bytes(tracker) == after


def test_project_confirmation_is_loaded_afresh_after_confirming(
    tracker: RunningTracker, history_page: Page
) -> None:
    """CP-584, CP-589, T17: on the pinned browser, going back to the confirmation after confirming
    issues a new request and shows the project's not-found page, and so does Forward then Back
    again; no confirmation shows and the saved bytes do not change."""
    page = history_page
    browser = page.context.browser
    assert browser is not None and browser.version == PINNED_BROWSER
    page.add_init_script(RECORDER)
    create_project(page, tracker.address, NAME, ("One",))
    page.get_by_role("button", name=TRIGGER).click()
    page.wait_for_url(lambda url: OPENED in url)
    confirmation = page.url
    page.get_by_role("button", name=TRIGGER).click()
    page.wait_for_url(lambda url: LANDED in url)
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
