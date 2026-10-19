"""End-to-end tests of adding a comment to a task, in Chromium against a tracker run as a process
(layer 5).

Checks SRS FR-28 (a comment is added from the keyboard under the saved name), FR-39 and FR-40 (a
refusal's reason and the comment maximum), NFR-4 (no script), NFR-5 (typed text is shown as text)
and AC-20 (a comment at its maximum is saved whole). Change spec rules CP-243, CP-250, CP-254,
CP-255, CP-256, CP-262 and CP-272 and NFDR QC-36 are the ones each test names. The browser's own
controls are used for the comment maximum and the keyboard. The saved data a task starts with is
written by the product's own SavedData before the tracker process starts, so the page begins with
the comments a test needs and every add is made in the browser.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from playwright.sync_api import Page, expect
from test_labels import tab_until
from test_people import focused_id

from application import LONG_TEXT_MAX, Comment
from domain import restore_state, restore_task
from persistence import SavedData

if TYPE_CHECKING:
    from conftest import RunningTracker, TrackerFactory

MARKUP = '<b>A&B</b> "Q"'
TITLE = "Set up CI"
CREATED = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
EARLIER_COUNT = 40
COMPLETION_LINE = f"You added a comment to '{TITLE}'."
BLANK_REASON = "A comment can't be blank. Type a comment."
NO_NAME_REASON = "A comment needs your name. Set it on the People page, then add the comment."
LINE_WIDTH = 50


def earlier_comments(count: int) -> list[Comment]:
    """Comments by Dana, each of two lines, enough in number to run past the window."""
    return [
        Comment(
            text=f"Earlier comment {number}\nits second line", author="Dana", created_at=CREATED
        )
        for number in range(1, count + 1)
    ]


def start_with(
    trackers: TrackerFactory,
    location: Path,
    *,
    name: str | None,
    comments: list[Comment] | None = None,
) -> RunningTracker:
    """Write one project and one task, `Set up CI`, holding these comments, and start a tracker."""
    task = restore_task(1, 1, TITLE, "todo", "medium", None, [], None, CREATED, comments or [])
    state = restore_state(
        [(1, "Alpha", "")], 2, (), tasks=[task], next_task_id=2, operator_name=name
    )
    SavedData(location).save(state)
    return trackers.start(location)


def saved_comments(tracker: RunningTracker) -> list[dict[str, str]]:
    saved = json.loads(tracker.saved_file.read_text(encoding="utf-8"))
    comments: list[dict[str, str]] = saved["tasks"][0]["comments"]
    return comments


def submit_with_keyboard(page: Page) -> None:
    """From the comment field, Tab to Add and press Enter: the browser's own keys."""
    page.keyboard.press("Tab")
    assert focused_id(page) == "add-comment"
    with page.expect_navigation():
        page.keyboard.press("Enter")


def type_lines(page: Page, *lines: str) -> None:
    """Type each line, with the Enter key between them, into the field that has focus."""
    for position, line in enumerate(lines):
        if position:
            page.keyboard.press("Enter")
        page.keyboard.type(line)


def test_keyboard_comment_add_brings_the_new_comment_into_view_and_focus(
    trackers: TrackerFactory, location: Path, page: Page
) -> None:
    """CP-250, CP-262, CP-272: earlier comments fill more than the window; Tab, type, Tab and Enter
    add one, and the new last comment is in view with focus, described by the one completion line
    that does not itself take focus. Reload, back and forward add nothing again."""
    tracker = start_with(trackers, location, name="Sam", comments=earlier_comments(EARLIER_COUNT))
    page.goto(tracker.address + "/tasks/1")
    viewport = page.viewport_size
    assert viewport is not None
    assert page.evaluate("document.documentElement.scrollHeight") > 2 * viewport["height"]
    expect(page.locator(f"#comment-{EARLIER_COUNT}")).not_to_be_in_viewport()
    tab_until(page, "comment-text")
    page.keyboard.type("Looks good")
    submit_with_keyboard(page)
    added = page.locator(f"#comment-{EARLIER_COUNT + 1}")
    expect(added).to_be_focused()
    expect(added).to_be_in_viewport()
    expect(added).to_contain_text("Looks good")
    expect(added).to_have_accessible_description(COMPLETION_LINE)
    assert page.evaluate("document.activeElement.tabIndex") == -1
    assert focused_id(page) == f"comment-{EARLIER_COUNT + 1}"
    focus_ring = page.evaluate(
        "(() => { const s = getComputedStyle(document.activeElement);"
        " return [s.outlineStyle, s.outlineWidth]; })()"
    )
    assert focus_ring[0] != "none" and focus_ring[1] != "0px"
    comments = saved_comments(tracker)
    assert len(comments) == EARLIER_COUNT + 1
    assert (comments[-1]["text"], comments[-1]["author"]) == ("Looks good", "Sam")
    page.reload()
    page.goto(tracker.address + "/people")
    page.go_back()
    page.go_forward()
    page.go_back()
    assert len(saved_comments(tracker)) == EARLIER_COUNT + 1


def test_browser_maximum_comment_with_line_breaks_is_saved_whole(
    trackers: TrackerFactory, location: Path, page: Page
) -> None:
    """CP-254, CP-272, AC-20: a comment of the field's native maximum with line breaks in it fills
    the field and is saved whole, neither shortened nor refused, though the browser sends each line
    break as two characters."""
    tracker = start_with(trackers, location, name="Sam")
    page.goto(tracker.address + "/tasks/1")
    field = page.locator("#comment-text")
    assert field.get_attribute("maxlength") == str(LONG_TEXT_MAX)
    line = "m" * (LINE_WIDTH - 1) + "\n"
    text = line * (LONG_TEXT_MAX // LINE_WIDTH)
    assert len(text) == LONG_TEXT_MAX
    field.fill(text)
    assert field.input_value() == text
    submit_with_keyboard(page)
    expect(page.locator("#comment-1")).to_be_focused()
    (saved,) = saved_comments(tracker)
    assert saved["text"] == text and len(saved["text"]) == LONG_TEXT_MAX
    assert "\r" not in saved["text"]


def test_browser_comment_text_and_author_render_literally(
    trackers: TrackerFactory, location: Path, page: Page
) -> None:
    """CP-243, CP-272, QC-36: markup characters, spaces and line breaks read back as typed, in the
    text and in the author's name, and the saved text and author are the typed ones."""
    author = f" {MARKUP} Sam "
    tracker = start_with(trackers, location, name=author)
    page.goto(tracker.address + "/tasks/1")
    tab_until(page, "comment-text")
    type_lines(page, f" {MARKUP}", " second  line ")
    submit_with_keyboard(page)
    shown = page.locator("#comment-1")
    expect(shown).to_be_focused()
    typed = f" {MARKUP}\n second  line "
    assert shown.locator(".comment-text").text_content() == typed
    meta = shown.locator(".comment-meta").text_content()
    assert meta is not None and meta.startswith(f"{author}, ")
    assert page.locator("main b").count() == 0 and page.locator("main i").count() == 0
    (saved,) = saved_comments(tracker)
    assert (saved["text"], saved["author"]) == (typed, author)


def test_keyboard_comment_refusals_keep_text_focus_and_description(
    trackers: TrackerFactory, location: Path, page: Page
) -> None:
    """CP-255, CP-256, CP-262, CP-272: with no name saved, and then with a blank comment, adding
    from the keyboard refuses, keeps the field's text and line breaks, leaves focus in the field
    and describes it by the one reason; nothing is saved."""
    tracker = start_with(trackers, location, name=None)
    page.goto(tracker.address + "/tasks/1")
    tab_until(page, "comment-text")
    type_lines(page, "Hi", " there ")
    submit_with_keyboard(page)
    field = page.locator("#comment-text")
    expect(field).to_be_focused()
    expect(field).to_have_value("Hi\n there ")
    expect(field).to_have_accessible_description(NO_NAME_REASON)
    assert saved_comments(tracker) == []
    other = page.context.new_page()
    other.goto(tracker.address + "/people")
    other.locator("#operator-name").fill("Sam")
    with other.expect_navigation():
        other.locator("#operator-name").press("Enter")
    other.close()
    page.keyboard.press("ControlOrMeta+A")
    type_lines(page, "  ", " ")
    submit_with_keyboard(page)
    field = page.locator("#comment-text")
    expect(field).to_be_focused()
    expect(field).to_have_value("  \n ")
    expect(field).to_have_accessible_description(BLANK_REASON)
    assert saved_comments(tracker) == []
