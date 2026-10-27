"""Integration tests of the moves pressed on a filtered list, through the real Site (layer 3).

Realizes SRS FR-18, FR-32 to FR-35 and FR-39 and NFR-9 for a move pressed in a row of a filtered
list, and checks the change spec rules CP-405 and CP-407 to CP-409 and CP-411, the design's T8 and
T9, and NFDR QC-63. The real Site, Tracker and SavedData are used, with an injected Clock and a saver
that can be made to fail. Where a test checks words, they are the strings of this change's text
record.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest
from test_pages import Element, parse
from test_routes import FORM, SAME_ORIGIN, get, header, page
from test_task_routes import World, focused, location, make_world, utc_zone  # noqa: F401

from web import Response

pytestmark = pytest.mark.usefixtures("utc_zone")

TITLE = "Set up CI"
LINE_ID = "move-line"
LIST_ID = "task-list"
LEFT = (
    "You moved '{title}' to {status}, and it no longer matches this filter, "
    "so it has left this list."
)
NOT_IN_LIST_FAILURE = (
    "The tracker couldn't move '{title}' to {status}, and nothing was changed. "
    "The task doesn't match this filter, so press Clear to see it."
)
ADDRESS_FINAL = (
    "The status of '{title}' is {status}, which doesn't allow a move to cancelled. "
    "The task doesn't match this filter, so it isn't in this list."
)
HIDDEN_FILTER = ("filter_status", "filter_priority", "filter_assignee", "filter_label")


def world_of(tmp_path: Path) -> World:
    """Task 1 is high and overdue, 2 is medium, 3 is low, all in todo, with Dana on the list."""
    world = make_world(tmp_path)
    world.tracker.add_task(1, TITLE, "high", "Dana", "2026-10-01")
    world.tracker.add_task(1, "Fix bug", "medium", "", "2026-10-20")
    world.tracker.add_task(1, "Ship", "low", "", "")
    return world


def pairs_of(query: str) -> list[tuple[str, str]]:
    return [
        (key, value)
        for key, values in parse_qs(query, keep_blank_values=True).items()
        for value in values
    ]


def send(
    world: World, path: str, fields: list[tuple[str, str]], headers: dict[str, str] | None = None
) -> Response:
    body = urlencode(fields).encode("utf-8")
    return world.site.handle("POST", path, {**(headers or SAME_ORIGIN), **FORM}, body)


def press(
    world: World,
    task: int,
    status: str,
    carried: list[tuple[str, str]],
    place: str = "list",
) -> Response:
    return send(world, f"/tasks/{task}/move", [("status", status), ("place", place), *carried])


def confirm(
    world: World, task: int, carried: list[tuple[str, str]], place: str = "list"
) -> Response:
    return send(world, f"/tasks/{task}/move/confirm", [("place", place), *carried])


def query_of(response: Response) -> dict[str, list[str]]:
    return parse_qs(urlsplit(location(response)).query, keep_blank_values=True)


def landing(world: World, response: Response) -> tuple[Response, Element]:
    answered = get(world.site, location(response))
    return answered, parse(page(answered, answered.status))


def line_of(root: Element) -> Element | None:
    return root.by_id(LINE_ID)


def table_titles(root: Element) -> list[str]:
    return [row.find_all("td")[0].text() for row in root.find_all("tr")[1:]]


def no_store(response: Response) -> bool:
    return header(response, "Cache-Control") == "no-store"


def selected(root: Element, name: str) -> list[str | None]:
    (control,) = [e for e in root.walk() if e.attrs.get("name") == name and e.tag == "select"]
    return [o.attrs.get("value") for o in control.find_all("option") if "selected" in o.attrs]


HIGH = [("filter_priority", "high")]


def test_each_list_move_path_keeps_filter_choices(tmp_path: Path) -> None:
    """CP-407, T8: a move, the open confirmation, Back out, the confirming press, a workflow refusal
    and a saver failure all keep the choices in forms, redirects, addresses and controls."""
    world = world_of(tmp_path)

    moved = press(world, 1, "in-progress", HIGH)
    assert urlsplit(location(moved)).path == "/projects/1"
    assert query_of(moved)["filter_priority"] == ["high"] and query_of(moved)["moved"] == [
        "in-progress"
    ]
    answered, root = landing(world, moved)
    assert answered.status == 200 and no_store(answered)
    assert selected(root, "filter_priority") == ["high"]

    opened = press(world, 1, "cancelled", HIGH)
    assert query_of(opened)["move_confirm"] == ["cancelled"]
    assert query_of(opened)["filter_priority"] == ["high"]
    answered, root = landing(world, opened)
    assert answered.status == 202 and no_store(answered)
    strip = [e for e in root.walk() if "confirm-strip" in (e.attrs.get("class") or "")]
    assert len(strip) == 1
    forms = strip[0].find_all("form")
    confirming, backing = forms
    assert ("filter_priority", "high") in [
        (e.attrs.get("name"), e.attrs.get("value")) for e in confirming.find_all("input")
    ]
    back_fields = [(e.attrs.get("name"), e.attrs.get("value")) for e in backing.find_all("input")]
    assert ("filter_priority", "high") in back_fields and ("move_back", "cancelled") in back_fields
    assert backing.attrs.get("method") == "get"

    backed = get(
        world.site,
        "/projects/1?" + urlencode([("move_task", "1"), ("move_back", "cancelled"), *HIGH]),
    )
    assert backed.status == 200 and no_store(backed)
    assert selected(parse(page(backed)), "filter_priority") == ["high"]

    confirmed = confirm(world, 1, HIGH)
    assert query_of(confirmed)["moved"] == ["cancelled"] and query_of(confirmed)[
        "filter_priority"
    ] == ["high"]
    assert world.tracker.task(1).status.value == "cancelled"  # type: ignore[union-attr]

    refused = press(world, 1, "done", HIGH)
    assert query_of(refused)["move_refused"] == ["not-allowed"]
    assert query_of(refused)["filter_priority"] == ["high"]

    world.saver.failing = True
    failed = press(world, 2, "in-progress", [("filter_priority", "medium")])
    assert query_of(failed)["move_failed"] == ["in-progress"]
    assert query_of(failed)["filter_priority"] == ["medium"]


def test_status_filtered_move_leaves_with_one_named_completion(tmp_path: Path) -> None:
    """CP-408: the row leaves, one line names the title and new status and says it left, and the
    last matching row yields the no-match state below that line."""
    world = world_of(tmp_path)
    carried = [("filter_status", "todo")]
    answered, root = landing(world, press(world, 1, "in-progress", carried))
    assert answered.status == 200 and no_store(answered)
    assert table_titles(root) == ["Fix bug", "Ship"]
    line = line_of(root)
    assert line is not None
    assert line.text() == LEFT.format(title=TITLE, status="in-progress")
    section = root.by_id(LIST_ID)
    assert section is not None
    assert section.attrs.get("aria-describedby") == LINE_ID and "autofocus" in section.attrs
    assert focused(root) == [section]
    assert "autofocus" not in line.attrs and "tabindex" not in line.attrs

    only = make_world(tmp_path / "only")
    only.tracker.add_task(1, TITLE, "high", "", "")
    answered, root = landing(only, press(only, 1, "in-progress", carried))
    line = line_of(root)
    assert line is not None and line.text() == LEFT.format(title=TITLE, status="in-progress")
    assert root.find_all("table") == []
    assert [e for e in root.walk() if e.attrs.get("id") == "filter-no-match"]
    assert "This project has no tasks yet" not in page(answered)
    assert focused(root) == [root.by_id(LIST_ID)]


@pytest.mark.parametrize("final", ["done", "cancelled"])
def test_overdue_move_to_either_final_status_leaves_the_list(tmp_path: Path, final: str) -> None:
    """CP-408, T8: moving the overdue task to done, or confirming cancelled, removes it from the
    Overdue list with the completion above the results."""
    world = world_of(tmp_path)
    carried = [("filter_overdue", "on")]
    world.tracker.move_task(1, "in-progress")
    if final == "done":
        response = press(world, 1, "done", carried)
    else:
        response = confirm(world, 1, carried)
    answered, root = landing(world, response)
    assert answered.status == 200 and no_store(answered)
    assert table_titles(root) == [] or TITLE not in table_titles(root)
    line = line_of(root)
    assert line is not None and line.text() == LEFT.format(title=TITLE, status=final)
    assert [e for e in root.walk() if e.attrs.get("id") == "filter-no-match"]


def test_priority_filtered_move_keeps_the_row_and_its_existing_focus(tmp_path: Path) -> None:
    """CP-407: a task still matching Priority high stays in place with its existing row outcome."""
    world = world_of(tmp_path)
    answered, root = landing(world, press(world, 1, "in-progress", HIGH))
    assert answered.status == 200
    assert table_titles(root) == [TITLE]
    line = line_of(root)
    assert line is not None and line.text() == f"You moved '{TITLE}' to in-progress."
    assert root.by_id(LIST_ID) is None
    (target,) = focused(root)
    assert (
        target.attrs.get("class") == "status-word"
        and target.attrs.get("aria-describedby") == LINE_ID
    )


def test_off_list_refusal_and_failure_remain_visible(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-409: a stale move from another tab, and a failing saver, give an outcome for a task the
    list does not show; the reason sits above the results with focus on the list section, and the
    state is unchanged on failure."""
    world = world_of(tmp_path)
    carried = [("filter_status", "todo")]
    world.tracker.move_task(1, "in-progress")
    stale = press(world, 1, "in-progress", carried)
    answered, root = landing(world, stale)
    assert answered.status == 200 and no_store(answered)
    line = line_of(root)
    assert line is not None
    moves = [move.value for move in world.tracker.allowed_moves(world.tracker.task(1).status)]  # type: ignore[union-attr]
    assert len(moves) == 3
    assert line.text() == (
        f"The status of '{TITLE}' is in-progress, and a task in in-progress can be moved to "
        f"{moves[0]}, {moves[1]} or {moves[2]}. "
        "The task doesn't match this filter, so press Clear to see it."
    )
    assert focused(root) == [root.by_id(LIST_ID)]
    assert "autofocus" not in line.attrs

    before = world.bytes_on_disk()
    world.saver.failing = True
    failed = press(world, 2, "in-progress", [("filter_status", "in-progress")])
    capsys.readouterr()
    answered, root = landing(world, failed)
    line = line_of(root)
    assert line is not None
    assert line.text() == NOT_IN_LIST_FAILURE.format(title="Fix bug", status="in-progress")
    assert focused(root) == [root.by_id(LIST_ID)]
    assert world.bytes_on_disk() == before
    assert world.tracker.task(2).status.value == "todo"  # type: ignore[union-attr]


@pytest.mark.parametrize("final", ["done", "cancelled"])
def test_stale_off_list_confirmation_address_shows_current_workflow_refusal(
    tmp_path: Path, final: str
) -> None:
    """CP-409, TL review: after another tab makes the task final, reopening its confirmation address
    shows the saved-status refusal above the results, answers 200 with no-store, and offers no
    confirmation. A task still open to cancelled that is off the list shows nothing."""
    world = world_of(tmp_path)
    world.tracker.move_task(1, "in-progress" if final == "done" else "cancelled")
    if final == "done":
        world.tracker.move_task(1, "done")
    address = "/projects/1?" + urlencode(
        [("move_task", "1"), ("move_confirm", "cancelled"), ("filter_status", "todo")]
    )
    answered = get(world.site, address)
    root = parse(page(answered))
    assert answered.status == 200 and no_store(answered)
    line = line_of(root)
    assert line is not None and line.text() == ADDRESS_FINAL.format(title=TITLE, status=final)
    assert [e for e in root.walk() if "confirm-strip" in (e.attrs.get("class") or "")] == []
    assert focused(root) == [root.by_id(LIST_ID)]

    other = get(
        world.site,
        "/projects/1?"
        + urlencode(
            [("move_task", "2"), ("move_confirm", "cancelled"), ("filter_status", "in-progress")]
        ),
    )
    assert other.status == 200
    assert line_of(parse(page(other))) is None


@pytest.mark.parametrize("confirming", [False, True])
@pytest.mark.parametrize(
    "bad",
    [
        [("filter_status", "todo"), ("filter_status", "done")],
        [("filter_due_from", "2026-10-10"), ("filter_due_to", "2026-10-01")],
        [("filter_assignee", "Nobody")],
    ],
)
def test_invalid_carried_filters_prevent_ordinary_and_confirmed_moves(
    tmp_path: Path, bad: list[tuple[str, str]], confirming: bool
) -> None:
    """CP-405: a repeated field, a reversed range or an unlisted assignee stops either move endpoint
    before any save, and the landing keeps the whole raw attempt and shows the field refusals."""
    world = world_of(tmp_path)
    before = world.bytes_on_disk()
    saves = world.saver.saves
    response = confirm(world, 1, bad) if confirming else press(world, 1, "in-progress", bad)
    assert urlsplit(location(response)).path == "/projects/1"
    assert sorted(pairs_of(urlsplit(location(response)).query)) >= sorted(bad)
    assert world.bytes_on_disk() == before and world.saver.saves == saves
    assert world.tracker.task(1).status.value == "todo"  # type: ignore[union-attr]
    answered, root = landing(world, response)
    assert answered.status == 200 and no_store(answered)
    assert root.find_all("table") == []
    assert [e for e in root.walk() if (e.attrs.get("id") or "").endswith("-reason")]
    assert line_of(root) is None


def test_move_returns_allow_only_filter_keys(tmp_path: Path) -> None:
    """Design § 3 C, TL review: an unrelated key, an arbitrary return URL and an outcome naming
    another project's task cannot change the destination, become hidden state, or add a line."""
    world = world_of(tmp_path)
    world.tracker.create_project("Beta", "")
    world.tracker.add_task(2, "Elsewhere", "high", "", "")
    carried = [*HIGH, ("next", "http://evil.example/"), ("return", "/people"), ("junk", "1")]
    response = press(world, 1, "in-progress", carried)
    assert urlsplit(location(response)).path == "/projects/1"
    assert set(query_of(response)) == {"filter_priority", "moved", "move_task"}
    opened = confirm(world, 1, carried)
    assert set(query_of(opened)) <= {"filter_priority", "moved", "move_task"}

    shown = get(
        world.site,
        "/projects/1?"
        + urlencode(
            [
                ("filter_priority", "high"),
                ("junk", "x"),
                ("move_task", "1"),
                ("move_confirm", "cancelled"),
            ]
        ),
    )
    root = parse(page(shown, shown.status))
    names = {
        e.attrs.get("name")
        for e in root.walk()
        if e.tag == "input" and e.attrs.get("type") == "hidden"
    }
    assert "junk" not in names and "next" not in names

    foreign = get(
        world.site,
        "/projects/1?"
        + urlencode([("filter_status", "done"), ("move_task", "4"), ("moved", "done")]),
    )
    root = parse(page(foreign))
    assert line_of(root) is None


def test_filtered_move_responses_keep_history_contract(tmp_path: Path) -> None:
    """CP-407, T8: 202 only for a rendered confirmation, 200 otherwise, no-store on the move
    landings, no Clear-Site-Data on any move response, and an absent target still 404."""
    world = world_of(tmp_path)
    carried = [("filter_status", "todo")]
    submissions = [
        press(world, 1, "in-progress", carried),
        press(world, 1, "cancelled", carried),
        confirm(world, 3, carried),
    ]
    for submission in submissions:
        assert header(submission, "Clear-Site-Data") is None
    for submission, status in zip(submissions[:2], (200, 202)):
        answered = get(world.site, location(submission))
        assert answered.status == status and no_store(answered)
        assert header(answered, "Clear-Site-Data") is None
    gone = get(
        world.site,
        "/projects/1?" + urlencode([("move_task", "99"), ("move_confirm", "cancelled"), *carried]),
    )
    assert gone.status == 404
    plain = get(world.site, "/projects/1?" + urlencode(carried))
    assert plain.status == 200 and not no_store(plain)
    task_page = get(world.site, "/tasks/2?move_task=2&moved=in-progress")
    assert task_page.status == 200 and no_store(task_page)


def test_special_filter_values_survive_move_and_confirmation(tmp_path: Path) -> None:
    """CP-411, T9: a label and a name holding `<`, `&`, a quote and spaces survive the encoded
    address and the hidden values exactly, and a repeated value is not collapsed on a refused
    return."""
    world = make_world(tmp_path, people=(" Ari ",))
    label = '<b>&"x" y '
    world.tracker.add_task(1, TITLE, "high", " Ari ", "")
    world.tracker.add_task_label(1, label)
    carried = [("filter_label", label), ("filter_assignee", " Ari ")]
    response = press(world, 1, "cancelled", carried)
    assert sorted(pairs_of(urlsplit(location(response)).query)) >= sorted(carried)
    answered, root = landing(world, response)
    assert answered.status == 202
    hidden = [
        (e.attrs.get("name"), e.attrs.get("value"))
        for e in root.walk()
        if e.tag == "input" and e.attrs.get("type") == "hidden"
    ]
    assert all(pair in hidden for pair in carried)
    assert "<b>" not in page(answered)

    repeated = [("filter_label", label), ("filter_label", label)]
    refused = press(world, 1, "in-progress", repeated)
    assert pairs_of(urlsplit(location(refused)).query).count(("filter_label", label)) == 2
