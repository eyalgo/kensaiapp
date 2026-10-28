"""Integration tests of the sort request through the real Site, application and domain (layer 3).

Realizes SRS FR-36, FR-39 and NFR-4, NFR-8 and NFR-9 for the request path. Checks the change spec
rules CP-428 to CP-438, CP-441 to CP-444 and CP-447, the design's T6 and T7, and NFDR QC-7 and QC-8.
The real Site, Tracker and SavedData are used, with an injected Clock and a saver that counts its
saves; no product name is patched. The controls and words these requests answer with are checked in
tests/integration/test_sort_pages.py.
"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

import pytest
from test_pages import Element, parse
from test_routes import get, page
from test_task_routes import World, make_world, utc_zone  # noqa: F401

pytestmark = pytest.mark.usefixtures("utc_zone")

# id: (title, priority, due date). Storage order is creation order; the sorts below must not
# depend on anything else.
TASKS = (
    ("beta", "high", "2026-10-10"),
    ("Alpha", "low", "2026-10-02"),
    ("alpha", "critical", ""),
    ("Zed", "low", "2026-10-02"),
    ("Gamma", "medium", ""),
)


def sort_world(tmp_path: Path) -> World:
    world = make_world(tmp_path)
    for title, priority, due in TASKS:
        world.tracker.add_task(1, title, priority, "", due)
    return world


def listed(root: Element) -> list[int]:
    """The task numbers in the title links of the list, in the order shown."""
    return [
        int(str(a.attrs["href"]).rsplit("/", 1)[1])
        for table in root.find_all("table")
        for a in table.find_all("a")
    ]


def sorted_page(world: World, query: str = "", status: int = 200) -> Element:
    target = "/projects/1" + (f"?{query}" if query else "")
    return parse(page(get(world.site, target), status))


def selected(root: Element, name: str) -> list[str]:
    (select,) = [e for e in root.find_all("select") if e.attrs.get("name") == name]
    return [o.attrs["value"] for o in select.find_all("option") if "selected" in o.attrs]


EVERY_COMBINATION = [
    ("due_date", "ascending", [2, 4, 1, 3, 5]),
    ("due_date", "descending", [1, 2, 4, 3, 5]),
    ("priority", "ascending", [2, 4, 5, 1, 3]),
    ("priority", "descending", [3, 1, 5, 2, 4]),
    ("created_time", "ascending", [1, 2, 3, 4, 5]),
    ("created_time", "descending", [5, 4, 3, 2, 1]),
    ("title", "ascending", [2, 3, 1, 5, 4]),
    ("title", "descending", [4, 5, 1, 2, 3]),
]


@pytest.mark.parametrize(("field", "direction", "expected"), EVERY_COMBINATION)
def test_every_sort_field_and_direction_reaches_the_real_site(
    tmp_path: Path, field: str, direction: str, expected: list[int]
) -> None:
    """CP-429 to CP-433, CP-435, T6: ordered task links, retained controls and the count; undated
    tasks last in both due directions and ties in ascending task number in both directions."""
    root = sorted_page(sort_world(tmp_path), f"sort_field={field}&sort_direction={direction}")
    assert listed(root) == expected
    assert selected(root, "sort_field") == [field]
    assert selected(root, "sort_direction") == [direction]
    assert "This project has 5 tasks." in root.text()


def test_the_unsorted_address_keeps_todays_order_and_no_count(tmp_path: Path) -> None:
    """CP-428, CP-436, T6: no key, blank keys and unknown keys give due date ascending."""
    world = sort_world(tmp_path)
    for query in ("", "sort_field=&sort_direction=", "sort=title&direction=descending"):
        root = sorted_page(world, query)
        assert listed(root) == [2, 4, 1, 3, 5], query
        assert "This project has" not in root.text(), query


def test_each_control_defaults_independently(tmp_path: Path) -> None:
    """CP-428, CP-436, T6: a field alone sorts ascending, a direction alone sorts by due date, and
    explicit defaults are a nonempty choice that shows the count."""
    world = sort_world(tmp_path)
    assert listed(sorted_page(world, "sort_field=title")) == [2, 3, 1, 5, 4]
    direction_alone = sorted_page(world, "sort_direction=descending")
    assert listed(direction_alone) == [1, 2, 4, 3, 5]
    assert selected(direction_alone, "sort_field") == ["due_date"]
    assert "This project has 5 tasks." in direction_alone.text()
    explicit = sorted_page(world, "sort_field=due_date&sort_direction=ascending")
    assert listed(explicit) == [2, 4, 1, 3, 5]
    assert "This project has 5 tasks." in explicit.text()
    blank_field = sorted_page(world, "sort_field=&sort_direction=descending")
    assert listed(blank_field) == [1, 2, 4, 3, 5]


def test_a_sort_over_a_filter_keeps_the_filters_matches(tmp_path: Path) -> None:
    """CP-434, T6: status plus priority descending, a priority filter with a title sort and a
    combined range all list exactly the filter's matches in the sort's order."""
    world = sort_world(tmp_path)
    world.tracker.move_task(3, "in-progress")
    todo = sorted_page(world, "filter_status=todo&sort_field=priority&sort_direction=descending")
    assert listed(todo) == [1, 5, 2, 4]
    assert "4 tasks match this filter." in todo.text()
    low = sorted_page(world, "filter_priority=low&sort_field=title&sort_direction=descending")
    assert listed(low) == [4, 2]
    dated = sorted_page(
        world,
        "filter_due_from=2026-10-02&filter_due_to=2026-10-02&sort_field=created_time"
        "&sort_direction=descending",
    )
    assert listed(dated) == [4, 2]
    assert selected(dated, "sort_field") == ["created_time"]
    unsorted = sorted_page(world, "filter_status=in-progress")
    assert listed(unsorted) == [3]


def test_a_valid_filter_matching_nothing_shows_no_list_with_or_without_a_sort(
    tmp_path: Path,
) -> None:
    """CP-401, CP-435 reading, T6: the filter's empty sentence and no table either way."""
    world = sort_world(tmp_path)
    for query in ("filter_label=ui", "filter_label=ui&sort_field=title"):
        root = sorted_page(world, query)
        assert listed(root) == [], query
        assert "No tasks match this filter." in root.text(), query
        assert root.find_all("table") == [], query


def test_the_same_address_reopens_the_same_order_and_clear_restores_every_task(
    tmp_path: Path,
) -> None:
    """CP-433, CP-437, CP-438, T6: the same address twice, a reload after a change and a bookmark
    show current data in the same order; Clear drops every choice and count; Apply adds no
    completion message."""
    world = sort_world(tmp_path)
    saves = world.saver.saves
    address = "filter_priority=low&sort_field=title&sort_direction=descending"
    assert listed(sorted_page(world, address)) == listed(sorted_page(world, address)) == [4, 2]
    world.tracker.add_task(1, "Beta", "low", "", "")
    assert listed(sorted_page(world, address)) == [4, 6, 2]
    cleared = sorted_page(world)
    assert listed(cleared) == [2, 4, 1, 3, 5, 6]
    assert selected(cleared, "sort_field") == ["due_date"]
    assert selected(cleared, "sort_direction") == ["ascending"]
    assert "This project has" not in cleared.text() and "match this filter" not in cleared.text()
    assert "applied" not in sorted_page(world, address).text().lower()
    assert world.saver.saves == saves + 1  # the one task this test added itself


REFUSING = [
    "sort_field=colour",
    "sort_field=Title",
    "sort_field=%20title",
    "sort_field=due-date",
    "sort_direction=sideways",
    "sort_direction=DESC",
    "sort_field=title&sort_field=title",
    "sort_field=&sort_field=",
    "sort_direction=ascending&sort_direction=ascending",
    "sort_direction=&sort_direction=",
    "sort_field=colour&sort_direction=sideways",
    "filter_status=blocked&sort_field=colour",
    "filter_due_from=2026-10-10&filter_due_to=2026-10-01&sort_direction=sideways",
    "filter_label=ui&sort_field=colour",
]


@pytest.mark.parametrize("query", REFUSING)
def test_a_refused_sort_changes_nothing_on_disk_and_lists_nothing(
    tmp_path: Path, query: str
) -> None:
    """CP-441, CP-442, CP-447, T7: the state, the saver and the real saved bytes stay as they were,
    and the answer is a 200 page with no result and no count. A valid filter that matches nothing
    does not hide a malformed sort."""
    world = sort_world(tmp_path)
    state, saves, saved = world.tracker.project_tasks(1), world.saver.saves, world.bytes_on_disk()
    root = sorted_page(world, query)
    assert root.find_all("table") == []
    assert root.by_id("filter-count") is None
    assert "No tasks match this filter" not in root.text()
    assert world.tracker.project_tasks(1) == state
    assert world.saver.saves == saves and world.bytes_on_disk() == saved


def test_a_missing_project_stays_not_found_with_valid_or_invalid_sort_choices(
    tmp_path: Path,
) -> None:
    """CP-444, T7: an unknown project answers the established 404 page, not a refusal."""
    world = sort_world(tmp_path)
    for query in (
        "sort_field=title",
        "sort_field=colour",
        "sort_direction=a&sort_direction=b",
        "filter_status=blocked&sort_field=colour",
    ):
        response = get(world.site, f"/projects/99?{query}")
        assert response.status == 404, query
        body = response.body.decode("utf-8").lower()
        assert "sort" not in body and "direction" not in body, query


def test_values_are_decoded_whole_and_unnormalized(tmp_path: Path) -> None:
    """CP-441, design 3 C: no alias, no case change and no trimming; a percent-encoded token reaches
    the domain exactly, and a plus sign is a space as in any form."""
    world = sort_world(tmp_path)
    accepted = sorted_page(
        world, urlencode({"sort_field": "title", "sort_direction": "descending"})
    )
    assert listed(accepted) == [4, 5, 1, 2, 3]
    for token in ("TITLE", "title+", "%74itle%20", "created", "created-time"):
        assert sorted_page(world, f"sort_field={token}").find_all("table") == [], token
