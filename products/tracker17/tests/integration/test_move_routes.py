"""Integration tests of the move request through the real Site, application and domain (layer 3).

Checks SRS FR-18 (a task moves along its allowed moves and the move is saved), FR-19 (a move the
workflow does not allow changes nothing and gives its reason), NFR-3 (a failed save changes
nothing), NFR-4 (a submission from another site is refused), AC-10, AC-12, AC-13 and AC-18. Change
spec rules CP-296, CP-303 to CP-311 and CP-314 and NFDR QC-7, QC-38, QC-56 and QC-57 are the ones
each test names. Where a test checks words, they are the strings of this change's text record. The
real Site, Tracker and SavedData are used, with an injected Clock and a saver that can be made to
fail; no product name is patched.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

import pytest
from test_pages import Element, parse
from test_routes import FORM, HOST, SAME_ORIGIN, get, page
from test_task_routes import World, focused, follow, location, make_world, utc_zone  # noqa: F401

from web import Response, Site, pages

TITLE = "Set up CI"
LIST = "list"
TASK_PLACE = "task"
STATUS_COLUMN = 1
MOVES_COLUMN = 6


def press(
    site: Site,
    task: int | str,
    status: str | None,
    place: str | None = LIST,
    headers: dict[str, str] | None = None,
) -> Response:
    fields = {}
    if status is not None:
        fields["status"] = status
    if place is not None:
        fields["place"] = place
    body = urlencode(fields).encode("utf-8")
    return site.handle("POST", f"/tasks/{task}/move", {**(headers or SAME_ORIGIN), **FORM}, body)


def world_with(tmp_path: Path, status: str = "todo", title: str = TITLE) -> World:
    """A world holding one task, in the given status, reached by the workflow's own moves."""
    world = make_world(tmp_path)
    world.tracker.add_task(1, title)
    path = {"todo": [], "in-progress": ["in-progress"], "done": ["in-progress", "done"]}
    for step in path[status]:
        world.tracker.move_task(1, step)
    return world


def status_of(world: World, task: int = 1) -> str:
    found = world.tracker.task(task)
    assert found is not None
    return found.status.value


def description(element: Element) -> str:
    return " ".join(found.text() for found in element.described_by())


def rows(root: Element) -> list[list[Element]]:
    (table,) = root.find_all("table")
    (body,) = table.find_all("tbody")
    return [row.find_all("td") for row in body.find_all("tr")]


def buttons(scope: Element) -> list[str]:
    return [button.text() for button in scope.find_all("button")]


REFUSAL_FOR = {
    "todo": (
        "The status of 'Set up CI' is todo, which doesn't allow the move you pressed. "
        "The moves shown are the ones you can press."
    ),
    "in-progress": (
        "The status of 'Set up CI' is in-progress, which doesn't allow the move you pressed. "
        "The moves shown are the ones you can press."
    ),
    "done": (
        "The status of 'Set up CI' is done, which doesn't allow the move you pressed. "
        "A task in done can't be moved."
    ),
}


def test_a_row_press_saves_and_lands_on_the_project_page_at_the_rows_status(
    tmp_path: Path,
) -> None:
    """R1, CP-296, CP-303, CP-305, CP-314: the press is saved once; the landing is the project's
    page, the row's status element is focused and the line describes it."""
    world = world_with(tmp_path)
    saves = world.saver.saves
    response = press(world.site, 1, "in-progress", LIST)
    assert location(response).startswith("/projects/1?") and "#" not in location(response)
    assert world.saver.saves == saves + 1 and status_of(world) == "in-progress"
    root = parse(follow(world.site, response))
    (target,) = focused(root)
    assert target.text() == "in-progress" and target.attrs["tabindex"] == "-1"
    assert description(target) == "You moved 'Set up CI' to in-progress."
    (row,) = rows(root)
    assert row[STATUS_COLUMN].text() == "in-progress"
    assert buttons(row[MOVES_COLUMN]) == ["done", "todo"]


def test_a_task_page_press_saves_and_lands_on_the_task_page_with_no_buttons_at_done(
    tmp_path: Path,
) -> None:
    """R2, CP-299, CP-303, CP-305: the landing is the task's page, whose status area shows done and
    no button."""
    world = world_with(tmp_path, "in-progress")
    response = press(world.site, 1, "done", TASK_PLACE)
    assert location(response).startswith("/tasks/1?") and "#" not in location(response)
    assert status_of(world) == "done"
    root = parse(follow(world.site, response))
    (target,) = focused(root)
    assert target.text() == "done" and description(target) == "You moved 'Set up CI' to done."
    (area,) = [e for e in root.find_all("section") if e.attrs.get("id") == "status"]
    assert target in list(area.walk()) and area.find_all("button") == []


def test_a_stale_press_is_refused_against_the_saved_status_and_saves_nothing(
    tmp_path: Path,
) -> None:
    """R3, CP-308, CP-312: the page showed todo, another tab moved the task to in-progress, then
    in-progress is pressed. The file is as it was and the reason describes the status element."""
    world = world_with(tmp_path)
    world.tracker.move_task(1, "in-progress")
    before = (world.bytes_on_disk(), world.saver.saves)
    response = press(world.site, 1, "in-progress", LIST)
    assert (world.bytes_on_disk(), world.saver.saves) == before
    root = parse(follow(world.site, response))
    (target,) = focused(root)
    assert target.text() == "in-progress"
    assert description(target) == REFUSAL_FOR["in-progress"]
    assert buttons(rows(root)[0][MOVES_COLUMN]) == ["done", "todo"]


def test_a_stale_todo_press_after_done_is_refused_and_the_task_stays_done(tmp_path: Path) -> None:
    """R4, CP-308: in-progress was shown, the task went to done elsewhere, then todo is pressed."""
    world = world_with(tmp_path, "done")
    before = (world.bytes_on_disk(), world.saver.saves)
    response = press(world.site, 1, "todo", TASK_PLACE)
    assert (world.bytes_on_disk(), world.saver.saves) == before and status_of(world) == "done"
    root = parse(follow(world.site, response))
    (target,) = focused(root)
    assert target.text() == "done" and description(target) == REFUSAL_FOR["done"]
    (area,) = [e for e in root.find_all("section") if e.attrs.get("id") == "status"]
    assert area.find_all("button") == []


@pytest.mark.parametrize("status", ["finished", None, "", "Done"], ids=lambda s: repr(s))
def test_a_non_status_or_missing_status_is_refused_and_answered_like_a_stale_press(
    tmp_path: Path, status: str | None
) -> None:
    """R5, CP-309: a move naming something that is not a status is answered at the same place,
    with the same reason for the saved status, and saves nothing."""
    world = world_with(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    response = press(world.site, 1, status, LIST)
    assert (world.bytes_on_disk(), world.saver.saves) == before
    assert location(response).startswith("/projects/1?") and "#" not in location(response)
    root = parse(follow(world.site, response))
    (target,) = focused(root)
    assert target.text() == "todo" and description(target) == REFUSAL_FOR["todo"]
    assert target in list(rows(root)[0][STATUS_COLUMN].walk())


def test_an_unknown_task_and_an_unreadable_identity_get_the_not_found_page_and_nothing_is_saved(
    tmp_path: Path,
) -> None:
    """R6, CP-310: task 999 is redirected to its own address, which answers not found; an identity
    of more digits than an int reads answers the not-found page at once."""
    world = world_with(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    unknown = press(world.site, 999, "in-progress")
    assert location(unknown) == "/tasks/999"
    missing = get(world.site, "/tasks/999")
    assert missing.status == 404
    assert missing.body == pages.task_not_found_page().encode("utf-8")
    unreadable = press(world.site, "9" * 5000, "in-progress")
    assert unreadable.status == 404
    assert unreadable.body == pages.task_not_found_page().encode("utf-8")
    assert (world.bytes_on_disk(), world.saver.saves) == before


def test_a_failing_saver_reports_on_the_console_and_the_page_without_exception_text(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """R7, CP-311, QC-56, QC-57: the console's first line names the move, the next the error; the
    page's failure line has no exception text, and the state and the file are as they were."""
    world = world_with(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    world.saver.failing = True
    response = press(world.site, 1, "in-progress", LIST)
    lines = capsys.readouterr().err.splitlines()
    assert (
        lines[0] == "The tracker couldn't move 'Set up CI' to in-progress, and nothing was changed."
    )
    assert lines[1] == "PermissionError: the disk said no"
    world.saver.failing = False
    shown = follow(world.site, response)
    root = parse(shown)
    (target,) = focused(root)
    assert description(target) == (
        "The tracker couldn't move 'Set up CI' to in-progress, and nothing was changed. Try again."
    )
    for leaked in ("PermissionError", "disk said no", "Traceback"):
        assert leaked not in shown
    assert status_of(world) == "todo"
    assert (world.bytes_on_disk(), world.saver.saves) == before
    assert buttons(rows(root)[0][MOVES_COLUMN]) == ["in-progress"]


@pytest.mark.parametrize(
    "mark",
    [
        {"Host": HOST, "Sec-Fetch-Site": "none"},
        {"Host": HOST, "Sec-Fetch-Site": "same-site"},
        {"Host": HOST},
    ],
    ids=["none", "same-site", "unmarked"],
)
def test_a_submission_not_marked_same_origin_is_refused_and_a_get_changes_nothing(
    tmp_path: Path, mark: dict[str, str]
) -> None:
    """R8, CP-314: only a same-origin submission is applied; a GET to the address changes nothing."""
    world = world_with(tmp_path)
    before = (world.bytes_on_disk(), world.saver.saves)
    assert press(world.site, 1, "in-progress", LIST, headers=mark).status == 403
    assert get(world.site, "/tasks/1/move").status == 404
    assert (world.bytes_on_disk(), world.saver.saves) == before and status_of(world) == "todo"


def test_reloading_the_landing_address_shows_the_same_line_and_saves_nothing(
    tmp_path: Path,
) -> None:
    """R9, CP-306: the landing address is read-only; each visit shows the same line."""
    world = world_with(tmp_path)
    landing = location(press(world.site, 1, "in-progress", LIST))
    saves = world.saver.saves
    first, second, third = (page(get(world.site, landing)) for _ in range(3))
    assert first == second == third
    assert description(focused(parse(first))[0]) == "You moved 'Set up CI' to in-progress."
    assert world.saver.saves == saves


def test_overdue_clears_on_done_and_stays_on_todo_on_the_row(
    tmp_path: Path,
    utc_zone: None,  # noqa: F811
) -> None:
    """R10, CP-307: today is 2026-10-19 by the clock handed in. A task due yesterday loses
    Overdue when it is moved to done, and keeps it when it is moved back to todo."""
    world = make_world(tmp_path)
    world.clock.instant = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    for title in ("A", "B"):
        world.tracker.add_task(1, title, due_date="2026-10-18")
        world.tracker.move_task(1 if title == "A" else 2, "in-progress")

    def row_of(title: str) -> list[Element]:
        root = parse(page(get(world.site, "/projects/1")))
        (found,) = [cells for cells in rows(root) if cells[0].text() == title]
        return found

    assert "Overdue" in row_of("A")[5].text() and "Overdue" in row_of("B")[5].text()
    press(world.site, 1, "done")
    press(world.site, 2, "todo")
    assert "Overdue" not in row_of("A")[5].text()
    assert "Overdue" in row_of("B")[5].text()


@pytest.mark.parametrize("place", [None, "", "elsewhere", "LIST"], ids=repr)
def test_a_missing_or_unknown_place_answers_at_the_tasks_page(
    tmp_path: Path, place: str | None
) -> None:
    """R11, QC-38: only the place word `list` sends the landing to the project's page."""
    world = world_with(tmp_path)
    assert location(press(world.site, 1, "in-progress", place)).startswith("/tasks/1?")


def test_list_press_lands_on_the_moved_tasks_own_project_page(tmp_path: Path) -> None:
    """CP-303: with tasks in two projects, a list press on the second project's task lands on
    that project's page and not the first's."""
    world = make_world(tmp_path, projects=("Alpha", "Beta"))
    world.tracker.add_task(1, "First")
    world.tracker.add_task(2, "Second")
    response = press(world.site, 2, "in-progress", LIST)
    assert location(response).startswith("/projects/2?")
    root = parse(follow(world.site, response))
    (row,) = rows(root)
    assert row[0].text() == "Second" and focused(root)[0].text() == "in-progress"


def test_a_press_on_a_cancelled_task_is_refused_with_the_cancelled_reason(tmp_path: Path) -> None:
    """CP-308: the fourth saved status has its own reason, and the task stays cancelled."""
    world = world_with(tmp_path)
    world.tracker.move_task(1, "cancelled")
    before = (world.bytes_on_disk(), world.saver.saves)
    root = parse(follow(world.site, press(world.site, 1, "todo", TASK_PLACE)))
    assert description(focused(root)[0]) == (
        "The status of 'Set up CI' is cancelled, which doesn't allow the move you pressed. "
        "A task in cancelled can't be moved."
    )
    assert (world.bytes_on_disk(), world.saver.saves) == before
