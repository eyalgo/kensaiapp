"""Integration tests of the move request through the real Site, application and domain (layer 3).

Checks SRS FR-18 (a task moves along its allowed moves and the move is saved), FR-19 (a move the
workflow does not allow changes nothing and gives its reason), NFR-3 (a failed save changes
nothing), NFR-4 (a submission from another site is refused), AC-10, AC-12, AC-13 and AC-18. Change
spec rules CP-296, CP-303 to CP-311 and CP-314, the cancel-confirmation change's CP-321, CP-326 to
CP-334 and CP-336, the history-after-confirm change's CP-343, the out-of-date-move change's CP-355
to CP-366 and CP-370, and NFDR QC-7, QC-38, QC-56 and QC-57 are the ones each test names. Where a test checks words, they are the strings of this
change's text record. The real Site, Tracker and SavedData are used, with an injected Clock and a
saver that can be made to fail; no product name is patched.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode

import pytest
from test_pages import Element, parse
from test_routes import FORM, HOST, SAME_ORIGIN, get, header, page
from test_task_routes import World, focused, follow, location, make_world, utc_zone  # noqa: F401

from application import TaskFields
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
    path = {
        "todo": [],
        "in-progress": ["in-progress"],
        "done": ["in-progress", "done"],
        "cancelled": ["cancelled"],
    }
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


SUBMISSION_FOR = {
    "todo": (
        "The status of 'Set up CI' has changed to todo. "
        "A task in todo can be moved to in-progress or cancelled."
    ),
    "in-progress": (
        "The status of 'Set up CI' has changed to in-progress. "
        "A task in in-progress can be moved to done, cancelled or todo."
    ),
    "done": ("The status of 'Set up CI' has changed to done. A task in done can't be moved."),
    "cancelled": (
        "The status of 'Set up CI' has changed to cancelled. A task in cancelled can't be moved."
    ),
}
ADDRESS_FOR = {
    "done": (
        "The status of 'Set up CI' is done, which doesn't allow a move to cancelled. "
        "A task in done can't be moved."
    ),
    "cancelled": (
        "The status of 'Set up CI' is cancelled, which doesn't allow a move to cancelled. "
        "A task in cancelled can't be moved."
    ),
}
CONTROLS = ("a", "button", "form", "input", "select", "textarea")
STATUSES = ("todo", "in-progress", "done", "cancelled")


def named_moves(line: str) -> list[str]:
    """The moves a submission line names, in the order it names them; none when it says the task
    can't be moved."""
    found = re.search(r"can be moved to (.+)\.$", line)
    if found is None:
        return []
    return re.split(r", | or ", found.group(1))


def assert_one_status_line(root: Element, status: str, line: str) -> Element:
    """The refusal contract of CP-358, CP-360 and CP-362: no confirmation, exactly one focused
    non-control status word that the line describes, the line itself taking no focus and holding
    no reload, link or control. Returns the status word."""
    assert strips(root) == []
    (target,) = focused(root)
    assert target.tag not in CONTROLS and target.attrs["tabindex"] == "-1"
    assert target.text() == status
    (described,) = target.described_by()
    assert described.text() == line == description(target)
    assert "autofocus" not in described.attrs and "tabindex" not in described.attrs
    assert [e for e in described.walk() if e.tag in CONTROLS] == []
    assert "reload" not in line.lower() and "pressed" not in line
    return target


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
    assert buttons(row[MOVES_COLUMN]) == ["done", "cancelled", "todo"]


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


def moves_scope(root: Element, place: str) -> Element:
    """Where a place shows the task's moves: its row's moves cell, or the task page's status area."""
    if place == LIST:
        return rows(root)[0][MOVES_COLUMN]
    (area,) = [e for e in root.find_all("section") if e.attrs.get("id") == "status"]
    return area


def status_holder(root: Element, place: str) -> Element:
    return rows(root)[0][STATUS_COLUMN] if place == LIST else moves_scope(root, place)


# (saved status now, status the earlier page showed, a move that page offered, the real moves
# another tab made since). Each landing status is reached by pressing a move the earlier page
# offered and the saved status no longer allows.
OVERTAKEN = [
    ("todo", "in-progress", "done", ["todo"]),
    ("in-progress", "todo", "in-progress", ["in-progress"]),
    ("done", "in-progress", "todo", ["done"]),
    ("cancelled", "todo", "in-progress", ["cancelled"]),
]


@pytest.mark.parametrize("place", [LIST, TASK_PLACE])
@pytest.mark.parametrize(
    ("landing", "earlier", "pressed", "since"), OVERTAKEN, ids=lambda v: str(v)
)
def test_a_stale_press_is_refused_against_the_saved_status_and_saves_nothing(
    tmp_path: Path, place: str, landing: str, earlier: str, pressed: str, since: list[str]
) -> None:
    """R3, CP-308, CP-312, CP-355, CP-358, CP-359, CP-362, CP-366: the earlier page offered the move,
    another tab then changed the status through the real tracker, and the move is pressed. The file
    and the save count are as they were through the redirect and the landing; the landing shows the
    saved status and its moves, and the line, the focused status word's description, says the
    status has changed and names those moves, in the buttons' order, and no other."""
    world = world_with(tmp_path, earlier)
    offered = buttons(moves_scope(parse(page(get(world.site, base_of(place)))), place))
    assert pressed in offered
    for move in since:
        world.tracker.move_task(1, move)
    assert status_of(world) == landing
    before = snapshot(world)
    response = press(world.site, 1, pressed, place)
    assert location(response).startswith(f"{base_of(place)}?") and "#" not in location(response)
    assert "move_refused=not-allowed" in location(response)
    assert snapshot(world) == before
    root = parse(follow(world.site, response))
    target = assert_one_status_line(root, landing, SUBMISSION_FOR[landing])
    assert target in list(status_holder(root, place).walk())
    saved = world.tracker.task(1)
    assert saved is not None
    workflow = [move.value for move in world.tracker.allowed_moves(saved.status)]
    assert buttons(moves_scope(root, place)) == named_moves(SUBMISSION_FOR[landing]) == workflow
    assert snapshot(world) == before


@pytest.mark.parametrize("place", [LIST, TASK_PLACE])
def test_a_stale_todo_press_after_done_is_refused_and_the_task_stays_done(
    tmp_path: Path, place: str
) -> None:
    """R4, CP-308, CP-355, CP-359: in-progress was shown, the task went to done elsewhere, then todo
    is pressed. The task stays done, shows no button, and the line says it can't be moved."""
    world = world_with(tmp_path, "in-progress")
    assert "todo" in buttons(moves_scope(parse(page(get(world.site, base_of(place)))), place))
    world.tracker.move_task(1, "done")
    before = snapshot(world)
    response = press(world.site, 1, "todo", place)
    assert snapshot(world) == before and status_of(world) == "done"
    root = parse(follow(world.site, response))
    assert_one_status_line(root, "done", SUBMISSION_FOR["done"])
    assert buttons(moves_scope(root, place)) == []
    assert snapshot(world) == before


@pytest.mark.parametrize("place", [LIST, TASK_PLACE])
@pytest.mark.parametrize("status", ["finished", None, "", "Done"], ids=lambda s: repr(s))
def test_a_non_status_or_missing_status_is_refused_and_answered_like_a_stale_press(
    tmp_path: Path, status: str | None, place: str
) -> None:
    """R5, CP-309, CP-357, CP-366: a move naming something that is not a status is answered at the
    same place, with the same line, status word and moves as an overtaken press on the task, and
    saves nothing; the two refusal codes in the landing address are kept."""
    world = world_with(tmp_path)
    before = snapshot(world)
    response = press(world.site, 1, status, place)
    assert snapshot(world) == before
    assert location(response).startswith(f"{base_of(place)}?") and "#" not in location(response)
    assert "move_refused=not-a-status" in location(response)
    root = parse(follow(world.site, response))
    target = assert_one_status_line(root, "todo", SUBMISSION_FOR["todo"])
    assert target in list(status_holder(root, place).walk())
    assert buttons(moves_scope(root, place)) == ["in-progress", "cancelled"]
    assert snapshot(world) == before


# Titles holding `<`, `&` and a double quote (CP-359, CP-361). The spec's own title stays text even
# if it reached the page unescaped, so the second one forms an element unless it is escaped.
HOSTILE_TITLES = ['a < b & "c"', '<b>a</b> & "c"']


@pytest.mark.parametrize("hostile", HOSTILE_TITLES)
@pytest.mark.parametrize("place", [LIST, TASK_PLACE])
def test_overtaken_press_uses_the_current_title_as_text(
    tmp_path: Path, place: str, hostile: str
) -> None:
    """CP-359, CP-366, QC-36: the title another tab saved after the first page loaded, with `<`, `&`
    and a double quote, is the one the line shows, once, as parsed text: no element is injected and
    nothing is escaped twice."""
    world = world_with(tmp_path, "todo")
    get(world.site, base_of(place))
    world.tracker.edit_task(1, TaskFields(title=hostile), TaskFields(title=TITLE))
    world.tracker.move_task(1, "in-progress")
    before = snapshot(world)
    shown = follow(world.site, press(world.site, 1, "in-progress", place))
    root = parse(shown)
    expected = SUBMISSION_FOR["in-progress"].replace(TITLE, hostile)
    assert_one_status_line(root, "in-progress", expected)
    assert expected.count(hostile) == 1 and description(focused(root)[0]).count(hostile) == 1
    assert "&amp;lt;" not in shown and "&amp;amp;" not in shown and "&amp;quot;" not in shown
    assert [e for e in root.walk() if e.tag == "b"] == []
    assert snapshot(world) == before


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
    assert buttons(rows(root)[0][MOVES_COLUMN]) == ["in-progress", "cancelled"]


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
    """R8, CP-314: only a same-origin submission is applied; a GET to the address changes
    nothing."""
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
    """CP-308, CP-359: the fourth saved status has its own line, and the task stays cancelled."""
    world = world_with(tmp_path)
    world.tracker.move_task(1, "cancelled")
    before = (world.bytes_on_disk(), world.saver.saves)
    root = parse(follow(world.site, press(world.site, 1, "todo", TASK_PLACE)))
    assert description(focused(root)[0]) == SUBMISSION_FOR["cancelled"]
    assert (world.bytes_on_disk(), world.saver.saves) == before


# --- The cancelled move and its in-place confirmation (cancel-confirmation, CP-321 to CP-334) ---

PLACES = [LIST, TASK_PLACE]
ELIGIBLE = ["todo", "in-progress"]
CANCELLED_REASON = "You moved 'Set up CI' to cancelled."
FAILED_LINE = "The tracker couldn't move 'Set up CI' to cancelled, and nothing was changed."


def confirm(
    site: Site,
    task: int | str,
    place: str | None = LIST,
    headers: dict[str, str] | None = None,
    **extra: str,
) -> Response:
    """A submission to the confirming address, as the confirming control sends it."""
    fields = dict(extra)
    if place is not None:
        fields["place"] = place
    body = urlencode(fields).encode("utf-8")
    return site.handle(
        "POST", f"/tasks/{task}/move/confirm", {**(headers or SAME_ORIGIN), **FORM}, body
    )


def snapshot(world: World) -> tuple[bytes, int, object]:
    """Everything a read or a refusal must leave as it was: the file, the saves, the state."""
    return world.bytes_on_disk(), world.saver.saves, world.tracker.project_tasks(1)


def base_of(place: str) -> str:
    return "/projects/1" if place == LIST else "/tasks/1"


def strips(root: Element) -> list[Element]:
    return [e for e in root.walk() if "confirm-strip" in (e.attrs.get("class") or "").split()]


def differing_values(before: object, after: object, path: tuple = ()) -> list[tuple]:
    """The paths at which two saved documents differ in a value."""
    if isinstance(before, dict) and isinstance(after, dict) and before.keys() == after.keys():
        return [
            found
            for key in before
            for found in differing_values(before[key], after[key], (*path, key))
        ]
    if isinstance(before, list) and isinstance(after, list) and len(before) == len(after):
        return [
            found
            for index, (old, new) in enumerate(zip(before, after, strict=True))
            for found in differing_values(old, new, (*path, index))
        ]
    return [] if before == after else [path]


@pytest.mark.parametrize("status", ELIGIBLE)
@pytest.mark.parametrize("place", PLACES)
def test_first_press_opens_confirmation_without_a_save(
    tmp_path: Path, place: str, status: str
) -> None:
    """CP-321, CP-336: a press of cancelled from either place and either eligible status answers
    at its own page's confirmation address and saves nothing; the page shows no completion."""
    world = world_with(tmp_path, status)
    before = snapshot(world)
    response = press(world.site, 1, "cancelled", place)
    assert location(response) == f"{base_of(place)}?move_task=1&move_confirm=cancelled"
    assert snapshot(world) == before
    root = parse(page(get(world.site, location(response)), 202))
    assert len(strips(root)) == 1 and "You moved" not in root.text()
    assert snapshot(world) == before


@pytest.mark.parametrize("place", PLACES)
def test_confirmation_and_back_out_reads_never_save(tmp_path: Path, place: str) -> None:
    """CP-326, CP-329, CP-360, CP-370: reading the confirmation or the back-out address, again and
    again, saves nothing; the confirmation refocuses its sentence, the back-out restores the trigger
    with no line, and either address revisited after the move was saved shows the address refusal,
    with a fresh snapshot compared after each revisit."""
    world = world_with(tmp_path)
    before = snapshot(world)
    opened = f"{base_of(place)}?move_task=1&move_confirm=cancelled"
    first, second, third = (page(get(world.site, opened), 202) for _ in range(3))
    assert first == second == third
    (sentence,) = focused(parse(first))
    assert sentence.attrs["id"] == "confirm-sentence"
    backed = parse(page(get(world.site, f"{base_of(place)}?move_task=1&move_back=cancelled")))
    (trigger,) = focused(backed)
    assert trigger.tag == "button" and trigger.text() == "cancelled"
    assert strips(backed) == [] and "You moved" not in backed.text()
    assert snapshot(world) == before
    world.tracker.move_task(1, "cancelled")
    after = snapshot(world)
    for address in (opened, f"{base_of(place)}?move_task=1&move_back=cancelled"):
        for _ in range(2):
            revisited = parse(page(get(world.site, address)))
            assert strips(revisited) == []
            (status,) = focused(revisited)
            assert status.text() == "cancelled"
            assert description(status) == ADDRESS_FOR["cancelled"]
            assert snapshot(world) == after


@pytest.mark.parametrize("final", ["done", "cancelled"])
@pytest.mark.parametrize("place", PLACES)
def test_confirmation_address_at_a_final_status_shows_the_saved_status(
    tmp_path: Path, place: str, final: str
) -> None:
    """CP-343: once the saved status no longer allows the move, the confirmation's address, which
    is what Back now reaches, answers an ordinary 200 page with no strip, sentence, confirming or
    move control for the task; its status in words takes the one focus, described by the address
    refusal's line for that saved status; and the read saves nothing."""
    world = world_with(tmp_path, final)
    before = snapshot(world)
    root = parse(page(get(world.site, f"{base_of(place)}?move_task=1&move_confirm=cancelled")))
    assert strips(root) == [] and root.by_id("confirm-sentence") is None
    move_forms = [
        f for f in root.find_all("form") if "/tasks/1/move" in (f.attrs.get("action") or "")
    ]
    assert move_forms == []
    (status,) = focused(root)
    assert status.text() == final and f"is {final}," in description(status)
    assert description(status) == ADDRESS_FOR[final]
    assert snapshot(world) == before


@pytest.mark.parametrize("status", ELIGIBLE)
@pytest.mark.parametrize("place", PLACES)
def test_confirming_saves_once_and_only_the_status_changes(
    tmp_path: Path, place: str, status: str
) -> None:
    """CP-327, CP-336: the confirming press saves once, the task's status is the one saved value
    that differs, and the landing has one described completion and no moves."""
    world = world_with(tmp_path, status)
    before_document = json.loads(world.bytes_on_disk())
    saves = world.saver.saves
    response = confirm(world.site, 1, place)
    assert location(response).startswith(f"{base_of(place)}?") and "#" not in location(response)
    assert world.saver.saves == saves + 1 and status_of(world) == "cancelled"
    (changed,) = differing_values(before_document, json.loads(world.bytes_on_disk()))
    assert changed[-1] == "status"
    landing = follow(world.site, response)
    root = parse(landing)
    (target,) = focused(root)
    assert target.text() == "cancelled" and target.attrs["tabindex"] == "-1"
    assert description(target) == CANCELLED_REASON
    assert strips(root) == []
    assert len([e for e in root.walk() if e.attrs.get("id") == "move-line"]) == 1
    assert [b for b in root.find_all("button") if "move-button" in b.attrs.get("class", "")] == []
    saves = world.saver.saves
    assert page(get(world.site, location(response))) == landing
    assert world.saver.saves == saves


def test_confirming_an_overdue_task_clears_the_row_marker(
    tmp_path: Path,
    utc_zone: None,  # noqa: F811
) -> None:
    """CP-328: today is 2026-10-19 by the clock handed in; the due date is overdue before the
    confirmation and unmarked after it, with no product name patched."""
    world = make_world(tmp_path)
    world.clock.instant = datetime(2026, 10, 19, 12, 0, tzinfo=UTC)
    world.tracker.add_task(1, "A", due_date="2026-10-18")
    assert "Overdue" in rows(parse(page(get(world.site, "/projects/1"))))[0][5].text()
    confirm(world.site, 1, LIST)
    assert "Overdue" not in rows(parse(page(get(world.site, "/projects/1"))))[0][5].text()


@pytest.mark.parametrize("status", ["todo", "in-progress", "done", "cancelled"])
def test_ordinary_cancelled_submission_cannot_claim_confirmation(
    tmp_path: Path, status: str
) -> None:
    """CP-330, CP-336: the ordinary move address with cancelled opens or refuses and never saves,
    whatever confirmation or shown-status fields it carries; the confirming address fixes its
    target to cancelled whatever status a field names."""
    world = world_with(tmp_path, status)
    before = snapshot(world)
    forged = urlencode(
        {
            "status": "cancelled",
            "place": LIST,
            "confirm": "cancelled",
            "confirmed": "true",
            "move_confirm": "cancelled",
            "shown_status": status,
        }
    ).encode("utf-8")
    response = world.site.handle("POST", "/tasks/1/move", {**SAME_ORIGIN, **FORM}, forged)
    assert snapshot(world) == before
    expected = (
        "/projects/1?move_task=1&move_confirm=cancelled"
        if status in ELIGIBLE
        else "/projects/1?move_refused=not-allowed&move_task=1"
    )
    assert location(response) == expected


def test_the_confirming_address_ignores_a_status_field(tmp_path: Path) -> None:
    """CP-330: a submitted status does not select another operation at the confirming address."""
    world = world_with(tmp_path, "in-progress")
    confirm(world.site, 1, LIST, status="done")
    assert status_of(world) == "cancelled"


def test_confirming_intent_needs_no_remembered_pending_state(tmp_path: Path) -> None:
    """Design § 3 A.1: a same-origin confirming press applies a currently allowed move with no
    prior opening request; a second one after the cancellation is refused and saves nothing."""
    world = world_with(tmp_path)
    assert "move_refused" not in location(confirm(world.site, 1, TASK_PLACE))
    assert status_of(world) == "cancelled"
    before = snapshot(world)
    again = confirm(world.site, 1, TASK_PLACE)
    assert location(again) == "/tasks/1?move_refused=not-allowed&move_task=1"
    assert snapshot(world) == before


def test_other_moves_keep_their_first_press_outcomes(tmp_path: Path) -> None:
    """CP-330: a move to any status but cancelled still takes effect on its first press, with no
    confirmation; invalid targets, an unknown task and the place fallback answer as they did."""
    world = world_with(tmp_path)
    saves = world.saver.saves
    moved = location(press(world.site, 1, "in-progress", LIST))
    assert moved == "/projects/1?moved=in-progress&move_task=1" and "confirm" not in moved
    assert world.saver.saves == saves + 1 and status_of(world) == "in-progress"
    done = location(press(world.site, 1, "done", None))
    assert done == "/tasks/1?moved=done&move_task=1" and status_of(world) == "done"
    before = snapshot(world)
    refused = location(press(world.site, 1, "finished", LIST))
    assert refused == "/projects/1?move_refused=not-a-status&move_task=1"
    assert location(press(world.site, 999, "done")) == "/tasks/999"
    assert snapshot(world) == before


@pytest.mark.parametrize("place", PLACES)
def test_stale_opening_and_confirmation_use_the_saved_workflow_answer(
    tmp_path: Path, place: str
) -> None:
    """CP-331, CP-332, CP-336, CP-355, CP-370: the saved status decides both intents. After todo
    became in-progress both are accepted; after the earlier page and confirmation were loaded and
    the task went to done or cancelled, the ordinary cancelled press and the confirming press are
    refused with the submission line, and a back-out with the address line, each as the described
    status, with no strip, the same destinations, and the bytes and save count unchanged."""
    world = world_with(tmp_path)
    world.tracker.move_task(1, "in-progress")
    opening = press(world.site, 1, "cancelled", place)
    assert location(opening) == f"{base_of(place)}?move_task=1&move_confirm=cancelled"
    assert "move_refused" not in location(confirm(world.site, 1, place))
    assert status_of(world) == "cancelled"
    for final, since in (("done", ["in-progress", "done"]), ("cancelled", ["cancelled"])):
        world = world_with(tmp_path / final)
        base = base_of(place)
        earlier = parse(page(get(world.site, base)))
        assert "cancelled" in buttons(moves_scope(earlier, place))
        confirmation = parse(
            page(get(world.site, f"{base}?move_task=1&move_confirm=cancelled"), 202)
        )
        assert len(strips(confirmation)) == 1
        for move in since:
            world.tracker.move_task(1, move)
        before = snapshot(world)
        reached = {
            "opening": press(world.site, 1, "cancelled", place),
            "confirming": confirm(world.site, 1, place),
        }
        for response in reached.values():
            assert location(response) == f"{base}?move_refused=not-allowed&move_task=1"
            landing = get(world.site, location(response))
            assert landing.status == 200 and header(landing, "Cache-Control") == "no-store"
            assert_one_status_line(parse(page(landing)), final, SUBMISSION_FOR[final])
            assert snapshot(world) == before
        backed = get(world.site, f"{base}?move_task=1&move_back=cancelled")
        assert backed.status == 200 and header(backed, "Cache-Control") == "no-store"
        assert_one_status_line(parse(page(backed)), final, ADDRESS_FOR[final])
        assert snapshot(world) == before


def test_missing_confirmation_targets_answer_not_found_without_saving(tmp_path: Path) -> None:
    """CP-333, CP-336: an unknown or unreadable identity on the opening, the confirming press and
    the confirmation address answers not found and saves nothing; a list cannot show another
    project's task through its interaction query."""
    world = make_world(tmp_path, projects=("Alpha", "Beta"))
    world.tracker.add_task(1, "Here")
    world.tracker.add_task(2, "There")
    before = (world.bytes_on_disk(), world.saver.saves)
    missing = pages.task_not_found_page().encode("utf-8")
    assert location(press(world.site, 999, "cancelled")) == "/tasks/999"
    assert location(confirm(world.site, 999)) == "/tasks/999"
    huge = "9" * 5000
    for response in (press(world.site, huge, "cancelled"), confirm(world.site, huge)):
        assert response.status == 404 and response.body == missing
    for mode in ("move_confirm", "move_back"):
        for target in ("/projects/1", "/tasks/1"):
            for identity in ("999", huge):
                read = get(world.site, f"{target}?move_task={identity}&{mode}=cancelled")
                assert read.status == 404 and read.body == missing, (target, mode)
    plain = page(get(world.site, "/projects/1"))
    for mode in ("move_confirm", "move_back"):
        assert page(get(world.site, f"/projects/1?move_task=2&{mode}=cancelled")) == plain
    assert (world.bytes_on_disk(), world.saver.saves) == before


@pytest.mark.parametrize("place", PLACES)
def test_failed_confirming_save_preserves_data_and_reports_the_action(
    tmp_path: Path, place: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-334, QC-56, QC-57: a failing saver leaves the file and the state as they were; the
    terminal names the action then the error; the page says the move did not happen, beside the
    one focused status, with no exception text and no success line."""
    world = world_with(tmp_path)
    before = snapshot(world)
    world.saver.failing = True
    response = confirm(world.site, 1, place)
    lines = capsys.readouterr().err.splitlines()
    assert lines == [FAILED_LINE, "PermissionError: the disk said no"]
    world.saver.failing = False
    shown = follow(world.site, response)
    root = parse(shown)
    (target,) = focused(root)
    assert target.text() == "todo"
    assert description(target) == FAILED_LINE + " Try again."
    assert "You moved" not in shown and strips(root) == []
    for leaked in ("PermissionError", "disk said no", "Traceback"):
        assert leaked not in shown
    assert status_of(world) == "todo" and snapshot(world) == before
    assert "cancelled" in buttons(root)


@pytest.mark.parametrize("mode", ["move_confirm", "move_back"])
@pytest.mark.parametrize("final", ["done", "cancelled"])
@pytest.mark.parametrize("place", PLACES)
def test_cancellation_addresses_at_final_statuses_refuse_as_facts(
    tmp_path: Path, place: str, final: str, mode: str
) -> None:
    """CP-356, CP-360 to CP-362, CP-365, CP-366: the confirmation's and the back-out's address for a
    done or cancelled task, on either page, answers 200 with no-store; its status in words is the
    one focus, described by CP-361's line, which takes no focus and holds no reload, link or
    control; no strip and no move control for the task shows; each load, repeated, saves nothing."""
    world = world_with(tmp_path, final)
    before = snapshot(world)
    address = f"{base_of(place)}?move_task=1&{mode}=cancelled"
    for _ in range(3):
        response = get(world.site, address)
        assert response.status == 200 and header(response, "Cache-Control") == "no-store"
        root = parse(page(response))
        assert_one_status_line(root, final, ADDRESS_FOR[final])
        assert [
            f for f in root.find_all("form") if "/tasks/1/move" in f.attrs.get("action", "")
        ] == []
        assert buttons(moves_scope(root, place)) == []
        assert snapshot(world) == before


@pytest.mark.parametrize("hostile", HOSTILE_TITLES)
@pytest.mark.parametrize("final", ["done", "cancelled"])
@pytest.mark.parametrize("place", PLACES)
def test_address_refusal_shows_the_current_escaped_title(
    tmp_path: Path, place: str, final: str, hostile: str
) -> None:
    """CP-361, CP-366, QC-36: the title renamed after an earlier page was loaded, holding `<`, `&`
    and a double quote, is the one the address refusal shows, once, as parsed text: no injected
    element, nothing escaped twice, and the bytes and save count unchanged."""
    world = world_with(tmp_path, final)
    get(world.site, base_of(place))
    world.tracker.edit_task(1, TaskFields(title=hostile), TaskFields(title=TITLE))
    before = snapshot(world)
    shown = page(get(world.site, f"{base_of(place)}?move_task=1&move_confirm=cancelled"))
    expected = ADDRESS_FOR[final].replace(TITLE, hostile)
    root = parse(shown)
    assert_one_status_line(root, final, expected)
    assert description(focused(root)[0]).count(hostile) == 1
    assert "&amp;lt;" not in shown and "&amp;amp;" not in shown and "&amp;quot;" not in shown
    assert [e for e in root.walk() if e.tag == "b"] == []
    assert snapshot(world) == before


@pytest.mark.parametrize("place", PLACES)
def test_reopening_a_refused_submission_keeps_submission_wording(
    tmp_path: Path, place: str
) -> None:
    """CP-356, CP-363, spec Out of Scope: the context comes from the request, not from the
    message. A refused press's landing address reopened with no press keeps the submission line,
    also beside an interaction query; an unknown outcome word selects nothing new, and an outcome
    word that names the address refusal is no outcome at all. Nothing is saved."""
    world = world_with(tmp_path, "done")
    base = base_of(place)
    before = snapshot(world)
    landing = location(press(world.site, 1, "cancelled", place))
    for _ in range(2):
        assert_one_status_line(
            parse(page(get(world.site, landing))), "done", SUBMISSION_FOR["done"]
        )
    for mode in ("move_confirm", "move_back"):
        beside = f"{base}?move_task=1&move_refused=not-allowed&{mode}=cancelled"
        assert_one_status_line(parse(page(get(world.site, beside))), "done", SUBMISSION_FOR["done"])
        alone = page(get(world.site, f"{base}?move_task=1&{mode}=cancelled"))
        unknown = page(get(world.site, f"{base}?move_task=1&move_refused=bogus&{mode}=cancelled"))
        assert unknown == alone
        assert_one_status_line(parse(alone), "done", ADDRESS_FOR["done"])
    plain = page(get(world.site, base))
    forged = page(get(world.site, f"{base}?move_task=1&move_refused=cancellation-address"))
    assert forged == plain
    assert snapshot(world) == before


@pytest.mark.parametrize("status", ELIGIBLE)
@pytest.mark.parametrize("place", PLACES)
def test_eligible_statuses_keep_both_interaction_gets(
    tmp_path: Path, place: str, status: str
) -> None:
    """CP-356, CP-363, CP-365: for a todo or in-progress task both interaction addresses answer as
    before: the confirmation 202 with its strip and no refusal, the back-out 200 with the restored
    cancelled button focused and no refusal, and neither saves."""
    world = world_with(tmp_path, status)
    before = snapshot(world)
    opened = parse(
        page(get(world.site, f"{base_of(place)}?move_task=1&move_confirm=cancelled"), 202)
    )
    assert len(strips(opened)) == 1 and opened.by_id("move-line") is None
    backed = parse(page(get(world.site, f"{base_of(place)}?move_task=1&move_back=cancelled")))
    (trigger,) = focused(backed)
    assert trigger.tag == "button" and trigger.text() == "cancelled"
    assert strips(backed) == [] and backed.by_id("move-line") is None
    assert snapshot(world) == before
