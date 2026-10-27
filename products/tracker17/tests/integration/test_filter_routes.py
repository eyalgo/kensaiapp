"""Integration tests of the filter request through the real Site, application and domain (layer 3).

Realizes SRS FR-32 to FR-35, FR-39 and NFR-4, NFR-8 and NFR-9 for the request path. Checks the
change spec rules CP-396 to CP-400, CP-402 to CP-406, CP-410, CP-411, CP-413 and CP-416 to CP-417,
the design's T6, T7 and T11, and NFDR QC-7, QC-8, QC-34, QC-35 and QC-54. The real Site, Tracker and
SavedData are used, with an injected Clock and a saver that counts its saves; no product name is
patched. The pages these requests answer with are checked in tests/integration/test_filter_pages.py.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote, urlencode

import pytest
from test_filter_pages import FIELD_NAMES, project, rows_of, three_task_world
from test_pages import parse
from test_routes import FORM, POLICY, SAME_ORIGIN, get, header, page
from test_task_routes import World, make_world, utc_zone  # noqa: F401

from web import routes

pytestmark = pytest.mark.usefixtures("utc_zone")


def titles(world: World, query: str) -> list[str]:
    return rows_of(project(world, query))


EACH_FIELD = [
    ("filter_status=todo", ["Write docs", "Fix bug", "Ship"]),
    ("filter_status=done", []),
    ("filter_priority=high", ["Write docs"]),
    ("filter_priority=low", ["Fix bug"]),
    ("filter_assignee=Dana", ["Write docs"]),
    ("filter_assignee=%20Ari", ["Fix bug"]),
    ("filter_label=ui", ["Fix bug"]),
    ("filter_label=bug", ["Write docs"]),
    ("filter_due_from=2026-10-20", ["Fix bug"]),
    ("filter_due_to=2026-10-01", ["Write docs"]),
    ("filter_due_from=2026-10-01&filter_due_to=2026-10-20", ["Write docs", "Fix bug"]),
    ("filter_due_from=2026-10-20&filter_due_to=2026-10-20", ["Fix bug"]),
    ("filter_overdue=on", ["Write docs"]),
]


@pytest.mark.parametrize(("query", "expected"), EACH_FIELD)
def test_each_get_filter_shows_exactly_its_matches_in_list_order(
    tmp_path: Path, query: str, expected: list[str]
) -> None:
    """CP-396, CP-397, CP-398, T6: every field and every range shape, links in due-then-identity
    order, undated tasks outside any range."""
    assert titles(three_task_world(tmp_path), query) == expected


def test_all_fields_combine_as_and(tmp_path: Path) -> None:
    """CP-396, T6: one task satisfies every field, and each field alone would pass another."""
    world = three_task_world(tmp_path)
    full = (
        "filter_status=todo&filter_priority=high&filter_assignee=Dana&filter_label=bug"
        "&filter_due_from=2026-10-01&filter_due_to=2026-10-05&filter_overdue=on"
    )
    assert titles(world, full) == ["Write docs"]
    assert titles(world, full.replace("filter_priority=high", "filter_priority=low")) == []


def test_reload_bookmark_and_back_recompute_without_saving(tmp_path: Path) -> None:
    """CP-395, CP-399, CP-400, T6: the same address keeps its choices, a later load reflects the
    current state and clock, Clear returns every task, and no request saves."""
    world = three_task_world(tmp_path)
    saves = world.saver.saves
    bytes_before = world.bytes_on_disk()
    address = "filter_status=todo&filter_overdue=on"
    first = project(world, address)
    again = project(world, address)
    assert rows_of(first) == rows_of(again) == ["Write docs"]
    assert "1 task matches this filter." in again.text()
    world.tracker.move_task(1, "in-progress")
    later = project(world, address)
    assert "No tasks match this filter." in later.text()
    cleared = project(world)
    assert rows_of(cleared) == ["Write docs", "Fix bug", "Ship"]
    assert "this filter" not in cleared.text() and "applied" not in cleared.text().lower()
    assert world.saver.saves == saves + 1  # the one move this test itself made
    assert world.bytes_on_disk() != bytes_before


def test_date_boundaries_follow_the_clock_not_the_address(tmp_path: Path) -> None:
    """CP-399: the overdue filter recomputes on the injected clock's day."""
    from datetime import UTC, datetime

    world = three_task_world(tmp_path)
    assert titles(world, "filter_overdue=on") == ["Write docs"]
    world.clock.instant = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)
    assert titles(world, "filter_overdue=on") == ["Write docs", "Fix bug"]


def test_missing_project_wins_over_invalid_filter_choices(tmp_path: Path) -> None:
    """CP-410: an unknown project answers the established 404 page, not a field refusal."""
    world = three_task_world(tmp_path)
    for query in ("filter_status=blocked", "filter_status=a&filter_status=b", "filter_overdue=x"):
        response = get(world.site, f"/projects/99?{query}")
        assert response.status == 404
        assert "filter" not in response.body.decode("utf-8").lower()


REFUSING = [
    "filter_status=blocked",
    "filter_priority=urgent",
    "filter_assignee=carol",
    "filter_due_from=2026-02-30",
    "filter_due_to=2026-02-30",
    "filter_due_from=2026-10-10&filter_due_to=2026-10-01",
    "filter_overdue=maybe",
    *[f"{name}=a&{name}=b" for name in FIELD_NAMES],
    *[f"{name}=&{name}=" for name in FIELD_NAMES],
]


@pytest.mark.parametrize("query", REFUSING)
def test_a_refused_filter_changes_nothing_on_disk(tmp_path: Path, query: str) -> None:
    """CP-402 to CP-406, CP-413, T7: the state, the saver and the real saved bytes stay as they
    were, and the answer is a 200 page with no result."""
    world = three_task_world(tmp_path)
    state, saves, saved = world.tracker.project_tasks(1), world.saver.saves, world.bytes_on_disk()
    response = get(world.site, f"/projects/1?{query}")
    root = parse(page(response))
    assert root.find_all("table") == []
    assert world.tracker.project_tasks(1) == state
    assert world.saver.saves == saves and world.bytes_on_disk() == saved


def test_address_builder_carries_repeated_pairs_and_keeps_its_callers() -> None:
    """Design 3 C: `_address` takes a repeated key, preserving order and empties; the existing
    flag and keyword forms answer exactly as before."""
    assert routes._address("/p") == "/p"
    assert routes._address("/p", "created") == "/p?created"
    assert routes._address("/p", "created", move_task="1") == "/p?created&move_task=1"
    assert (
        routes._address("/p", filter_label=("a", "", "a"), x=" y")
        == "/p?filter_label=a&filter_label=&filter_label=a&x=+y"
    )
    assert routes._address("/p", "f", k=("1",), move_task="2") == "/p?f&k=1&move_task=2"
    assert routes._address("/p", k=()) == "/p"


def test_names_and_labels_round_trip_through_encoded_addresses(tmp_path: Path) -> None:
    """CP-411, T9: surrounding spaces and markup characters in an address select exactly."""
    world = make_world(tmp_path, people=(" <a&b> ",))
    world.tracker.add_task(1, "T", "medium", " <a&b> ", "")
    world.tracker.add_task_label(1, ' "q" ')
    world.tracker.add_task(1, "Other")
    for key, value in (("filter_assignee", " <a&b> "), ("filter_label", ' "q" ')):
        assert titles(world, f"{key}={quote(value, safe='')}") == ["T"]
    assert titles(world, urlencode({"filter_label": ' "q" '})) == ["T"]
    assert titles(world, "filter_label=%22q%22") == []


def test_filter_get_preserves_route_security_and_state_contracts(tmp_path: Path) -> None:
    """CP-417, T11: the route table is unchanged, Apply, reload and Clear answer with the page
    policy and no cookie, the recording saver receives no call, and Apply makes no connection."""
    assert {r.pattern for r in routes.ROUTES} >= {"/projects/[0-9]+"}
    world = three_task_world(tmp_path)
    saves = world.saver.saves
    for query in ("filter_status=todo", "filter_status=todo", "", "filter_status=blocked"):
        response = get(world.site, f"/projects/1?{query}" if query else "/projects/1")
        assert response.status == 200
        assert header(response, "Content-Security-Policy") == POLICY
        assert header(response, "Set-Cookie") is None
        assert header(response, "Clear-Site-Data") is None
    assert world.saver.saves == saves
    for mark in ("cross-site", "same-site"):
        assert (
            get(
                world.site,
                "/projects/1?filter_status=todo",
                {"Host": "127.0.0.1:8017", "Sec-Fetch-Site": mark},
            ).status
            == 403
        )
    assert get(world.site, "/projects/1?filter_status=todo", {"Host": "evil.example"}).status == 403
    assert world.site.handle("POST", "/projects/1", {**SAME_ORIGIN, **FORM}, b"").status == 404
