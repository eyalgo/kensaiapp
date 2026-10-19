"""Integration tests of the pages' move controls and landing through the real Site (layers 3 and 4).

Checks SRS FR-19 (the moves a task offers and the status shown in words), AC-12, NFR-12 (state is
carried by words and a named control) and UXD UX-A6 (each move is a button of its own). Change spec
rules CP-297 to CP-306, CP-308, CP-311 and CP-313 and NFDR QC-36 are the ones each test names.
Where a test checks words, they are the strings of this change's text record. Pages are read
through the real Site, Tracker and SavedData, with an injected Clock; no product name is patched.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from test_move_routes import (
    LIST,
    REFUSAL_FOR,
    TASK_PLACE,
    TITLE,
    buttons,
    description,
    press,
    rows,
    world_with,
)
from test_pages import Element, parse
from test_routes import get, page
from test_task_routes import World, focused, follow, make_world

CONTROL_TAGS = ("button", "input", "select", "textarea", "a", "form")


def task_page(world: World, query: str = "", task: int = 1) -> Element:
    return parse(page(get(world.site, f"/tasks/{task}{query}")))


def project_page(world: World, query: str = "") -> Element:
    return parse(page(get(world.site, f"/projects/1{query}")))


def status_area(root: Element) -> Element:
    (area,) = [e for e in root.find_all("section") if e.attrs.get("id") == "status"]
    return area


def world_with_all_statuses(tmp_path: Path) -> World:
    world = make_world(tmp_path)
    for title in ("Plain", "Going", "Finished", "Dropped"):
        world.tracker.add_task(1, title)
    world.tracker.move_task(2, "in-progress")
    world.tracker.move_task(3, "in-progress")
    world.tracker.move_task(3, "done")
    world.tracker.move_task(4, "cancelled")
    return world


def test_each_status_row_offers_exactly_its_allowed_moves_except_cancelled(tmp_path: Path) -> None:
    """P1, CP-297, CP-301: todo offers in-progress, in-progress offers done then todo, and done and
    cancelled offer nothing. No page names a move to cancelled, and none asks for confirmation."""
    world = world_with_all_statuses(tmp_path)
    root = project_page(world)
    assert [buttons(cells[6]) for cells in rows(root)] == [
        ["in-progress"],
        ["done", "todo"],
        [],
        [],
    ]
    assert [cells[6].text() for cells in rows(root)[2:]] == ["", ""]
    for shown in [root, *(task_page(world, task=number) for number in range(1, 5))]:
        for element in shown.walk():
            if element.tag in ("button", "input"):
                assert element.text() != "cancelled"
                assert element.attrs.get("value") != "cancelled"
            assert "to cancelled" not in (element.attrs.get("aria-label") or "")
        assert "confirm" not in shown.text().lower()


def test_task_page_shows_the_status_in_words_and_its_moves(tmp_path: Path) -> None:
    """P2, CP-299, CP-300: the status area names the status and offers the moves in order; a done
    task shows the status and no button."""
    world = world_with_all_statuses(tmp_path)
    going = status_area(task_page(world, task=2))
    assert going.find_all("h2")[0].text() == "Status"
    assert going.by_id("task-status") is not None
    assert going.by_id("task-status").text() == "in-progress"
    assert buttons(going) == ["done", "todo"]
    finished = status_area(task_page(world, task=3))
    assert finished.by_id("task-status").text() == "done" and buttons(finished) == []
    root = task_page(world, task=3)
    assert root.find_all("table") == [] and [e.text() for e in root.find_all("dt")] == ["Project"]


def test_the_done_button_name_is_move_title_to_done_on_the_row_and_the_task_page(
    tmp_path: Path,
) -> None:
    """P3, CP-298: the accessible name carries the task and the move; the visible label is the
    status word."""
    world = world_with(tmp_path, "in-progress")
    for root, scope in (
        (project_page(world), lambda r: rows(r)[0][6]),
        (task_page(world), status_area),
    ):
        done = [b for b in scope(root).find_all("button") if b.text() == "done"]
        assert [b.attrs["aria-label"] for b in done] == [f"Move '{TITLE}' to done"]


def test_every_move_control_is_a_lone_submit_button_in_a_post_form_with_no_tabindex_accesskey_or_disabled(
    tmp_path: Path,
) -> None:
    """P4, CP-300: the structural half of the keyboard rule, the browser's keys being E2E1."""
    world = world_with(tmp_path, "in-progress")
    for root in (project_page(world), task_page(world)):
        moves = [b for b in root.walk() if "move-button" in (b.attrs.get("class") or "").split()]
        assert len(moves) == 2
        for button in moves:
            assert button.tag == "button" and button.attrs["type"] == "submit"
            for forbidden in ("tabindex", "accesskey", "disabled"):
                assert forbidden not in button.attrs
            form = button.parent
            assert form is not None and form.tag == "form" and form.attrs["method"] == "post"
            assert form.attrs["action"] == "/tasks/1/move"
            assert form.find_all("button") == [button]
            controls = [e for e in form.walk() if e.tag in ("input", "select", "textarea")]
            assert {e.attrs["type"] for e in controls} == {"hidden"}
            assert {e.attrs["name"] for e in controls} == {"status", "place"}


def test_the_completion_line_and_button_name_escape_the_title_once(tmp_path: Path) -> None:
    """P5, CP-305, QC-36: the line reads exactly as the text record words it, and the markup holds
    the title once-escaped."""
    title = "a < b & c"
    world = world_with(tmp_path, title=title)
    landing = follow(world.site, press(world.site, 1, "in-progress", LIST))
    root = parse(landing)
    assert description(focused(root)[0]) == "You moved 'a < b & c' to in-progress."
    assert (
        "a &lt; b &amp; c" in landing and "&amp;lt;" not in landing and "&amp;amp;" not in landing
    )
    done = [b for b in root.find_all("button") if b.text() == "done"]
    assert [b.attrs["aria-label"] for b in done] == ["Move 'a < b & c' to done"]


OUTCOMES = {
    "moved": "move_task=1&moved=in-progress",
    "refused": "move_task=1&move_refused=not-allowed",
    "not-a-status": "move_task=1&move_refused=not-a-status",
    "failed": "move_task=1&move_failed=in-progress",
}
LINES = {
    "moved": "You moved 'Set up CI' to in-progress.",
    "refused": REFUSAL_FOR["todo"],
    "not-a-status": REFUSAL_FOR["todo"],
    "failed": (
        "The tracker couldn't move 'Set up CI' to in-progress, and nothing was changed. Try again."
    ),
}


@pytest.mark.parametrize("outcome", OUTCOMES)
@pytest.mark.parametrize("place", [LIST, TASK_PLACE])
def test_a_landing_page_has_exactly_one_autofocus_on_a_non_control_status_element_that_names_the_line(
    tmp_path: Path, place: str, outcome: str
) -> None:
    """P6, CP-303 to CP-305, CP-308, CP-311, EX-14: one focus, on the status word, in the moved
    row's status cell or the status area; the line is beside the moves, in the row's moves cell or
    the status area, and takes no focus."""
    world = world_with(tmp_path)
    root = (
        project_page(world, "?" + OUTCOMES[outcome])
        if place == LIST
        else task_page(world, "?" + OUTCOMES[outcome])
    )
    (target,) = focused(root)
    assert target.tag not in CONTROL_TAGS and target.attrs["tabindex"] == "-1"
    assert target.text() == "todo"
    (line,) = target.described_by()
    assert line.text() == LINES[outcome]
    assert "autofocus" not in line.attrs and "tabindex" not in line.attrs
    assert [e for e in root.walk() if e.attrs.get("id") == line.attrs["id"]] == [line]
    if place == LIST:
        (row,) = rows(root)
        word_holder, line_holder = row[1], row[6]
    else:
        word_holder = line_holder = status_area(root)
    assert target in list(word_holder.walk())
    assert line in list(line_holder.walk())
    others = [e for e in root.walk() if e.tag == "p" and "outcome" in (e.attrs.get("class") or "")]
    assert len(others) <= 1


def test_a_move_outcome_wins_over_created_label_and_comment_outcomes(tmp_path: Path) -> None:
    """P7, D-7: an address carrying a move outcome beside any other has exactly one focus, the
    move's."""
    world = world_with(tmp_path)
    world.tracker.add_task_label(1, "ui")
    move = OUTCOMES["moved"]
    for other in ("created", "task_refused=blank-title", "task_failed=add"):
        root = project_page(world, f"?{other}&{move}")
        (target,) = focused(root)
        assert description(target) == LINES["moved"] and "You created" not in root.text()
    others = (
        "added",
        "saved",
        "edit_refused=blank-title",
        "edit_failed=save",
        "label_added=ui",
        "label_removed=ui",
        "label_refused=empty",
        "label_failed=add",
        "comment_refused=blank",
        "comment_failed=add",
        "comment_added=1",
    )
    for other in others:
        root = task_page(world, f"?{other}&{move}")
        (target,) = focused(root)
        assert description(target) == LINES["moved"], other
        assert target.text() == "todo"


@pytest.mark.parametrize(
    "query",
    [
        "move_task=1&move_refused=bogus",
        "move_task=1&moved=finished",
        "move_task=1&moved=",
        "move_task=1&move_failed=finished",
        "move_task=999&moved=done",
        "move_task=0&moved=done",
        "move_task=x&moved=done",
        "moved=done",
        "move_refused=not-allowed",
    ],
)
def test_forged_outcomes_render_the_page_plain(tmp_path: Path, query: str) -> None:
    """P8, CP-304: an unknown refusal code, a non-status word or a task that is not on the page
    gives the plain page."""
    world = world_with(tmp_path)
    assert page(get(world.site, f"/projects/1?{query}")) == page(get(world.site, "/projects/1"))
    assert page(get(world.site, f"/tasks/1?{query}")) == page(get(world.site, "/tasks/1"))
    assert focused(parse(page(get(world.site, f"/tasks/1?{query}")))) == []


def test_a_move_outcome_about_one_row_shows_nothing_on_the_other_rows(tmp_path: Path) -> None:
    """CP-303, CP-305: only the moved task's row takes the focus and holds the line."""
    world = make_world(tmp_path)
    world.tracker.add_task(1, "First")
    world.tracker.add_task(1, "Second")
    root = project_page(world, "?move_task=2&moved=in-progress")
    first, second = rows(root)
    assert focused(root) == [second[1].find_all("span")[0]]
    assert first[1].text() == "todo" and first[6].find_all("p") == []
    assert description(focused(root)[0]) == "You moved 'Second' to in-progress."


def test_a_move_outcome_about_a_real_task_of_another_page_renders_the_page_plain(
    tmp_path: Path,
) -> None:
    """P8, CP-303: an outcome naming a task that exists but is not a row of this project's page,
    or is not the task this page shows, is no outcome; the page renders plain."""
    world = make_world(tmp_path, projects=("Alpha", "Beta"))
    world.tracker.add_task(1, "Here")
    world.tracker.add_task(2, "There")
    query = "?move_task=2&moved=in-progress"
    assert page(get(world.site, f"/projects/1{query}")) == page(get(world.site, "/projects/1"))
    assert page(get(world.site, f"/tasks/1{query}")) == page(get(world.site, "/tasks/1"))
    assert focused(project_page(world, query)) == []
