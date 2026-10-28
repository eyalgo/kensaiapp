"""Integration tests of the moves pressed on a sorted list, through the real Site (layer 3).

Realizes SRS FR-18, FR-32 to FR-36 and FR-39, and checks the change spec rules CP-439 and CP-440 and
the Layer-3 move rows of CP-449, the design's T8 and T9, existing CP-408 and CP-409, and NFDR QC-5,
QC-38 and QC-63. The real Site, Tracker and SavedData are used, with an injected Clock and a saver that
can be made to fail. Where a test checks words, they are the strings of this change's text record or
the filter's existing ones.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

import pytest
from test_filter_move_routes import (
    LEFT,
    LINE_ID,
    LIST_ID,
    confirm,
    landing,
    line_of,
    no_store,
    press,
    query_of,
    selected,
    table_titles,
)
from test_pages import Element, parse
from test_routes import get, header, page
from test_task_routes import World, focused, location, make_world, utc_zone  # noqa: F401

pytestmark = pytest.mark.usefixtures("utc_zone")

TITLE = "Set up CI"
SORT_KEYS = ("sort_field", "sort_direction")
TITLE_DESCENDING = [("sort_field", "title"), ("sort_direction", "descending")]
PRIORITY_DESCENDING = [("sort_field", "priority"), ("sort_direction", "descending")]


def world_of(tmp_path: Path) -> World:
    """Task 1 is high and overdue, 2 is medium, 3 is low, all in todo, with Dana on the list."""
    world = make_world(tmp_path)
    world.tracker.add_task(1, TITLE, "high", "Dana", "2026-10-01")
    world.tracker.add_task(1, "Fix bug", "medium", "", "2026-10-20")
    world.tracker.add_task(1, "Ship", "low", "", "")
    return world


def sort_pairs(pairs: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return [(key, value) for key, value in pairs if key in SORT_KEYS]


def query_pairs(response: object) -> list[tuple[str, str]]:
    query = urlsplit(location(response)).query  # type: ignore[arg-type]
    return [
        (key, value)
        for key, values in parse_qs(query, keep_blank_values=True).items()
        for value in values
    ]


def hidden_sort_pairs(form: Element) -> list[tuple[str, str]]:
    return [
        (e.attrs.get("name") or "", e.attrs.get("value") or "")
        for e in form.find_all("input")
        if e.attrs.get("type") == "hidden" and (e.attrs.get("name") or "") in SORT_KEYS
    ]


def row_forms(root: Element) -> list[Element]:
    """Every move form in the list's rows."""
    return [f for row in root.find_all("tr")[1:] for f in row.find_all("form")]


def confirm_strip_forms(root: Element) -> list[Element]:
    (strip,) = [e for e in root.walk() if "confirm-strip" in (e.attrs.get("class") or "")]
    return strip.find_all("form")


@pytest.mark.parametrize(
    ("carried", "titles"),
    [
        (TITLE_DESCENDING, ["Ship", "Set up CI"]),
        (
            [("filter_status", "todo"), *PRIORITY_DESCENDING],
            ["Set up CI", "Ship"],
        ),
    ],
)
def test_ordinary_move_preserves_sorted_list_choices(
    tmp_path: Path, carried: list[tuple[str, str]], titles: list[str]
) -> None:
    """CP-439, T8: the rows of a sorted list carry the exact sort pairs, the move redirects with
    them and the landing keeps them in the controls, the rows' forms and the saved order."""
    world = world_of(tmp_path)
    shown = get(world.site, "/projects/1?" + urlencode(carried))
    forms = row_forms(parse(page(shown)))
    assert forms and all(hidden_sort_pairs(f) == sort_pairs(carried) for f in forms)

    moved = press(world, 2, "in-progress", carried)
    assert urlsplit(location(moved)).path == "/projects/1"
    assert sort_pairs(query_pairs(moved)) == sort_pairs(carried)
    answered, root = landing(world, moved)
    assert answered.status == 200 and no_store(answered)
    assert [t for t in table_titles(root) if t != "Fix bug"] == titles
    chosen = dict(sort_pairs(carried))
    assert selected(root, "sort_field") == [chosen["sort_field"]]
    assert selected(root, "sort_direction") == [chosen["sort_direction"]]
    assert all(hidden_sort_pairs(f) == sort_pairs(carried) for f in row_forms(root))
    assert world.tracker.task(2).status.value == "in-progress"  # type: ignore[union-attr]


def test_cancel_open_back_out_and_confirm_keep_sort_choices(tmp_path: Path) -> None:
    """CP-439, T8: opening a cancellation saves nothing, Back out saves nothing, confirming applies
    the allowed move; each address and control keeps the choices and the resulting order."""
    world = world_of(tmp_path)
    carried = [("filter_status", "todo"), *TITLE_DESCENDING]
    before = world.bytes_on_disk()

    opened = press(world, 1, "cancelled", carried)
    assert query_of(opened)["move_confirm"] == ["cancelled"]
    assert sort_pairs(query_pairs(opened)) == TITLE_DESCENDING
    assert world.bytes_on_disk() == before
    answered, root = landing(world, opened)
    assert answered.status == 202 and no_store(answered)
    assert table_titles(root) == ["Ship", TITLE, "Fix bug"]
    confirming, backing = confirm_strip_forms(root)
    assert hidden_sort_pairs(confirming) == TITLE_DESCENDING
    assert hidden_sort_pairs(backing) == TITLE_DESCENDING
    assert backing.attrs.get("method") == "get"
    assert selected(root, "sort_field") == ["title"]

    back_query = [(e.attrs.get("name"), e.attrs.get("value")) for e in backing.find_all("input")]
    backed = get(world.site, "/projects/1?" + urlencode(back_query))  # type: ignore[arg-type]
    assert backed.status == 200 and no_store(backed)
    backed_root = parse(page(backed))
    assert table_titles(backed_root) == ["Ship", TITLE, "Fix bug"]
    assert selected(backed_root, "sort_direction") == ["descending"]
    assert world.bytes_on_disk() == before

    confirmed = confirm(world, 1, carried)
    assert query_of(confirmed)["moved"] == ["cancelled"]
    assert sort_pairs(query_pairs(confirmed)) == TITLE_DESCENDING
    assert world.tracker.task(1).status.value == "cancelled"  # type: ignore[union-attr]
    answered, root = landing(world, confirmed)
    assert answered.status == 200 and no_store(answered)
    assert table_titles(root) == ["Ship", "Fix bug"]
    assert selected(root, "sort_field") == ["title"]


def test_move_refusal_and_saver_failure_keep_sort_choices(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """CP-439, T8: a workflow refusal, a bad requested status and a failing saver each land on the
    sorted list with the exact choices, and nothing is reported done."""
    world = world_of(tmp_path)
    carried = PRIORITY_DESCENDING
    before = world.bytes_on_disk()

    refused = press(world, 1, "done", carried)
    assert query_of(refused)["move_refused"] == ["not-allowed"]
    assert sort_pairs(query_pairs(refused)) == carried
    answered, root = landing(world, refused)
    assert answered.status == 200 and no_store(answered)
    assert table_titles(root) == [TITLE, "Fix bug", "Ship"]
    assert "moved" not in query_of(refused)

    bad = press(world, 1, "sideways", carried)
    assert query_of(bad)["move_refused"] == ["not-a-status"]
    assert sort_pairs(query_pairs(bad)) == carried
    assert world.bytes_on_disk() == before

    world.saver.failing = True
    failed = press(world, 2, "in-progress", carried)
    capsys.readouterr()
    assert query_of(failed)["move_failed"] == ["in-progress"]
    assert sort_pairs(query_pairs(failed)) == carried
    answered, root = landing(world, failed)
    assert answered.status == 200 and no_store(answered)
    assert table_titles(root) == [TITLE, "Fix bug", "Ship"]
    assert world.bytes_on_disk() == before
    assert world.tracker.task(2).status.value == "todo"  # type: ignore[union-attr]
    assert "moved" not in query_of(failed)


def test_sorted_move_addresses_use_rendered_page_status(tmp_path: Path) -> None:
    """CP-439, T8, ADR-0010: a pending confirmation alone answers 202; every other move page 200;
    all are no-store with no Clear-Site-Data. A stale or forged confirmation shows the current
    workflow state, and a missing task is the established 404 outside no-store."""
    world = world_of(tmp_path)
    carried = TITLE_DESCENDING
    moved = press(world, 1, "in-progress", carried)
    opened = press(world, 2, "cancelled", carried)
    confirmed = confirm(world, 3, carried)
    for submission in (moved, opened, confirmed):
        assert header(submission, "Clear-Site-Data") is None
    for submission, status in ((moved, 200), (opened, 202), (confirmed, 200)):
        answered = get(world.site, location(submission))
        assert answered.status == status and no_store(answered)
        assert header(answered, "Clear-Site-Data") is None

    # Task 3 is now cancelled: its confirmation address renders no confirmation, only the refusal.
    stale = get(
        world.site,
        "/projects/1?" + urlencode([("move_task", "3"), ("move_confirm", "cancelled"), *carried]),
    )
    stale_root = parse(page(stale))
    assert stale.status == 200 and no_store(stale)
    assert [e for e in stale_root.walk() if "confirm-strip" in (e.attrs.get("class") or "")] == []
    line = line_of(stale_root)
    assert line is not None and "cancelled" in line.text()

    # A confirmation for a task another tab already made final reflects that, not the request.
    world.tracker.move_task(1, "done")
    forged = get(
        world.site,
        "/projects/1?" + urlencode([("move_task", "1"), ("move_confirm", "cancelled"), *carried]),
    )
    assert forged.status == 200 and no_store(forged)
    assert [
        e for e in parse(page(forged)).walk() if "confirm-strip" in (e.attrs.get("class") or "")
    ] == []

    gone = get(
        world.site,
        "/projects/1?" + urlencode([("move_task", "99"), ("move_confirm", "cancelled"), *carried]),
    )
    assert gone.status == 404 and not no_store(gone)


def test_move_leaving_status_filter_keeps_off_list_outcome(tmp_path: Path) -> None:
    """CP-408, T8: a status-filtered move whose row leaves keeps the existing outcome line and list
    focus above the sorted remaining rows."""
    world = world_of(tmp_path)
    carried = [("filter_status", "todo"), *TITLE_DESCENDING]
    answered, root = landing(world, press(world, 1, "in-progress", carried))
    assert answered.status == 200 and no_store(answered)
    assert table_titles(root) == ["Ship", "Fix bug"]
    line = line_of(root)
    assert line is not None
    assert line.text() == LEFT.format(title=TITLE, status="in-progress")
    section = root.by_id(LIST_ID)
    assert section is not None
    assert section.attrs.get("aria-describedby") == LINE_ID and "autofocus" in section.attrs
    assert focused(root) == [section]
    assert selected(root, "sort_field") == ["title"]
    assert all(hidden_sort_pairs(f) == TITLE_DESCENDING for f in row_forms(root))


@pytest.mark.parametrize("confirming", [False, True])
@pytest.mark.parametrize(
    ("bad", "focus"),
    [
        ([("sort_field", "colour")], "sort_field"),
        ([("sort_direction", "sideways")], "sort_direction"),
        ([("sort_field", "title"), ("sort_field", "title")], "sort_field"),
        ([("sort_field", ""), ("sort_field", "")], "sort_field"),
        ([("sort_direction", "ascending"), ("sort_direction", "")], "sort_direction"),
        ([("sort_field", "colour"), ("sort_direction", "sideways")], "sort_field"),
        ([("sort_field", "Title")], "sort_field"),
        ([("sort_direction", " ascending")], "sort_direction"),
        (
            [("sort_field", "title"), ("sort_field", "priority"), ("sort_direction", "up")],
            "sort_field",
        ),
    ],
)
def test_refused_sort_blocks_ordinary_and_confirming_moves(
    tmp_path: Path, bad: list[tuple[str, str]], focus: str, confirming: bool
) -> None:
    """CP-440, T8: every invalid or repeated sort condition saves nothing and opens no
    confirmation; the landing keeps the exact raw values, shows field refusals and focuses only
    the first refused field."""
    world = world_of(tmp_path)
    before = world.bytes_on_disk()
    saves = world.saver.saves
    response = confirm(world, 1, bad) if confirming else press(world, 1, "in-progress", bad)
    assert urlsplit(location(response)).path == "/projects/1"
    assert sort_pairs(query_pairs(response)) == bad
    assert "move_confirm" not in query_of(response) and "moved" not in query_of(response)
    assert world.bytes_on_disk() == before and world.saver.saves == saves
    assert world.tracker.task(1).status.value == "todo"  # type: ignore[union-attr]
    assert "move_confirm" not in query_of(press(world, 1, "cancelled", bad))
    answered, root = landing(world, response)
    assert answered.status == 200 and no_store(answered)
    assert root.find_all("table") == []
    assert [e for e in root.walk() if (e.attrs.get("id") or "").endswith("-reason")]
    assert line_of(root) is None
    (owner,) = focused(root)
    assert owner.attrs.get("name") == focus
    assert world.bytes_on_disk() == before


def test_move_carrying_preserves_blank_repeats_and_absence(tmp_path: Path) -> None:
    """CP-439, T8: a blank value rides the redirect unchanged, a malformed repeat survives
    unchanged, and a request with no sort keys gains none."""
    world = world_of(tmp_path)

    blank = [("sort_field", ""), ("sort_direction", "")]
    moved = press(world, 1, "in-progress", blank)
    assert sort_pairs(query_pairs(moved)) == blank
    assert world.tracker.task(1).status.value == "in-progress"  # type: ignore[union-attr]

    only_field = press(world, 2, "in-progress", [("sort_field", "priority")])
    assert sort_pairs(query_pairs(only_field)) == [("sort_field", "priority")]
    assert "sort_direction" not in query_of(only_field)

    repeated = [("sort_direction", "ascending"), ("sort_direction", "ascending")]
    refused = press(world, 3, "in-progress", repeated)
    assert sort_pairs(query_pairs(refused)) == repeated
    assert world.tracker.task(3).status.value == "todo"  # type: ignore[union-attr]

    plain = press(world, 3, "in-progress", [("filter_priority", "low")])
    assert not [key for key in query_of(plain) if key.startswith("sort_")]
    confirmed = confirm(world, 3, [])
    assert not [key for key in query_of(confirmed) if key.startswith("sort_")]
    assert set(query_of(plain)) == {"filter_priority", "moved", "move_task"}
