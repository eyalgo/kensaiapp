"""Integration tests of the Summary request and the project views' links through the real Site (layer 3).

Checks SRS FR-38 (a project's summary), FR-25 and FR-35 (the overdue rule the list, the filter and
the Summary share), NFR-4 (a request from another site is refused), NFR-8 (a read changes nothing),
AC-13 and AC-14. Change spec rules CP-490 to CP-495, CP-497, CP-505, CP-508, CP-510 and CP-513 to
CP-526 and NFDR QC-7, QC-8, QC-28, QC-33 and QC-34 are the ones each test names; the design rows are
T02 to T05, T07 to T10 and T12. The real Site, Tracker and SavedData are used with an injected
clock; no product name is patched, and the one read count is a subclass handed to the Site.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path

import pytest
from test_pages import Element, parse
from test_routes import POLICY, RecordingSaver, get, header, page
from test_task_routes import HOST, MovableClock, World, make_world, utc_zone  # noqa: F401

from application import ProjectSummary, Tracker
from domain import empty_state, restore_state
from web import Response, Site
from web.pages import NO_MATCH_LINE

pytestmark = pytest.mark.usefixtures("utc_zone")

OVERDUE_HEADING = "Overdue"
SUMMARY = "/projects/1/summary"
TASKS = "/projects/1"
PAIR = [(TASKS, "Tasks"), (SUMMARY, "Summary")]


class CountingTracker(Tracker):
    """The real Tracker, counting the Summary reads it is asked for."""

    def __init__(self, *arguments) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*arguments)
        self.summary_reads = 0

    def project_summary(self, project_id: int) -> ProjectSummary | None:
        self.summary_reads += 1
        return super().project_summary(project_id)


def counting_site() -> tuple[Site, CountingTracker, RecordingSaver]:
    saver = RecordingSaver()
    tracker = CountingTracker(empty_state(), saver, MovableClock())
    tracker.create_project("Alpha", "first")
    tracker.create_project("Gamma", "")
    tracker.add_assignee("ari")
    tracker.add_task(1, "late", "low", "ari", "2026-10-10")
    tracker.add_task(1, "plain", "high", "", "")
    return Site(tracker, HOST), tracker, saver


def summary_rows(root: Element) -> dict[str, str]:
    """Every row of every group, label to numeral (labels are unique in this fixture)."""
    return {
        row.find_all("th")[0].text(): row.find_all("td")[0].text()
        for row in root.find_all("tr")
        if row.find_all("td")
    }


def overdue_titles(root: Element) -> list[str]:
    marked = []
    for row in root.find_all("tr"):
        if any(s.attrs.get("class") == "overdue" for s in row.find_all("span")):
            marked.append(row.find_all("a")[0].text())
    return marked


def listed_titles(root: Element) -> list[str]:
    return [row.find_all("a")[0].text() for row in root.find_all("tbody")[0].find_all("tr")]


SUMMARY_OF = "/projects/{}/summary"
EVERY_COUNT_TARGET = [
    "/projects/1?filter_status=todo",
    "/projects/1?filter_status=in-progress",
    "/projects/1?filter_status=done",
    "/projects/1?filter_status=cancelled",
    "/projects/1?filter_priority=low",
    "/projects/1?filter_priority=medium",
    "/projects/1?filter_priority=high",
    "/projects/1?filter_priority=critical",
    "/projects/1?filter_overdue=on",
]
FILTER_FIELDS = ("status", "priority", "assignee", "label", "due_from", "due_to", "overdue")


def count_anchors(root: Element) -> list[Element]:
    """The anchors inside the Summary's count cells, in page order."""
    return [a for cell in root.find_all("td") for a in cell.find_all("a")]


def label_of(anchor: Element) -> str:
    return anchor.attrs.get("aria-label") or ""


def listed_ids(root: Element) -> list[int]:
    """The task numbers in the first link of each list row, in the order shown."""
    return [
        int(str(row.find_all("a")[0].attrs["href"]).rsplit("/", 1)[1])
        for table in root.find_all("table")
        for row in table.find_all("tbody")[0].find_all("tr")
    ]


def selected_in(root: Element, name: str) -> list[str]:
    (select,) = [e for e in root.find_all("select") if e.attrs.get("name") == name]
    return [o.attrs["value"] or "" for o in select.find_all("option") if "selected" in o.attrs]


def chosen_filters(root: Element) -> dict[str, str]:
    """What each of the seven filter controls holds: its selected value, its date, or on."""
    held: dict[str, str] = {}
    form = root.by_id("filter")
    assert form is not None
    filter_controls = [
        e
        for e in form.find_all("select") + form.find_all("input")
        if (e.attrs.get("name") or "").startswith("filter_")
    ]
    assert len(filter_controls) == len(FILTER_FIELDS) == 7
    for field in FILTER_FIELDS:
        name = f"filter_{field}"
        (control,) = [
            e
            for e in form.find_all("select") + form.find_all("input")
            if e.attrs.get("name") == name
        ]
        if control.tag == "select":
            held[field] = "".join(selected_in(form, name))
        elif control.attrs.get("type") == "checkbox":
            held[field] = "on" if "checked" in control.attrs else ""
        else:
            held[field] = control.attrs.get("value") or ""
    return held


def lone(field: str, value: str) -> dict[str, str]:
    """The seven controls with exactly one choice made."""
    return {name: (value if name == field else "") for name in FILTER_FIELDS}


# Each Summary link in page order: (its address, the one control it chooses, that choice).
NINE = [
    (EVERY_COUNT_TARGET[0], "status", "todo"),
    (EVERY_COUNT_TARGET[1], "status", "in-progress"),
    (EVERY_COUNT_TARGET[2], "status", "done"),
    (EVERY_COUNT_TARGET[3], "status", "cancelled"),
    (EVERY_COUNT_TARGET[4], "priority", "low"),
    (EVERY_COUNT_TARGET[5], "priority", "medium"),
    (EVERY_COUNT_TARGET[6], "priority", "high"),
    (EVERY_COUNT_TARGET[7], "priority", "critical"),
    (EVERY_COUNT_TARGET[8], "overdue", "on"),
]


def fixture_a(tmp_path: Path) -> World:
    """The spec's Fixture A on the clock's day 2026-10-11. Alpha: T1 todo/low/yesterday/unassigned,
    T2 in-progress/medium/undated/ari, T3 done/high/past/ari, T4 cancelled/critical/undated/dan
    (unlisted), T5 todo/critical/today/eve (unlisted). Beta holds one todo task for bo; Gamma
    none."""
    world = make_world(tmp_path, people=("ari", "bo"), projects=("Alpha", "Beta", "Gamma"))
    tracker = world.tracker
    tracker.add_assignee("dan")
    tracker.add_assignee("eve")
    tracker.add_task(1, "T1", "low", "", "2026-10-10")
    tracker.add_task(1, "T2", "medium", "ari", "")
    tracker.add_task(1, "T3", "high", "ari", "2026-10-01")
    tracker.add_task(1, "T4", "critical", "dan", "")
    tracker.add_task(1, "T5", "critical", "eve", "2026-10-11")
    tracker.add_task(2, "B1", "medium", "bo", "")
    tracker.move_task(2, "in-progress")
    tracker.move_task(3, "in-progress")
    tracker.move_task(3, "done")
    tracker.move_task(4, "cancelled")
    tracker.remove_assignee("dan")
    tracker.remove_assignee("eve")
    return world


MEMBERS = {
    "todo": [1, 5],
    "in-progress": [2],
    "done": [3],
    "cancelled": [4],
    "low": [1],
    "medium": [2],
    "high": [3],
    "critical": [4, 5],
    "on": [1],
}


def match_line(count: int) -> str:
    return "1 task matches this filter." if count == 1 else f"{count} tasks match this filter."


def test_every_summary_count_opens_exactly_its_project_members(tmp_path: Path) -> None:
    """CP-514, CP-516, CP-517, CP-523, CP-525, AC-14, T02: on Fixture A every one of Alpha's nine
    count links shows its numeral, its exact address and exactly the tasks the fixture says are
    members (written out here, not derived with the product's filter or summary), with the right
    singular or plural match line; the other cells stay plain and the nine names stay distinct."""
    world = fixture_a(tmp_path)
    root = parse(page(get(world.site, SUMMARY)))
    anchors = count_anchors(root)
    assert [a.attrs["href"] for a in anchors] == [address for address, _, _ in NINE]
    numerals = [a.text() for a in anchors]
    assert numerals == ["2", "1", "1", "1", "1", "1", "1", "2", "1"]
    assert summary_rows(root)["Total"] == "5" and summary_rows(root)["No due date"] == "2"
    assert len({label_of(a) for a in anchors}) == 9
    for (address, _, choice), anchor in zip(NINE, anchors, strict=True):
        destination = parse(page(get(world.site, address)))
        assert sorted(listed_ids(destination)) == MEMBERS[choice], address
        count = len(MEMBERS[choice])
        assert anchor.text() == str(count)
        line = destination.by_id("filter-count")
        assert line is not None and line.text() == match_line(count), address


def test_count_destinations_select_one_filter_and_default_sort(tmp_path: Path) -> None:
    """CP-516, CP-517, CP-523, T03: on all nine destinations only the intended filter has a
    choice, the other six are empty or off, the sort controls show due date ascending, and there
    are still exactly seven filter fields; a second world with due dates out of creation order, a
    due-date tie and an undated match shows the default order on the todo, critical and overdue
    destinations."""
    world = fixture_a(tmp_path)
    for address, field, choice in NINE:
        destination = parse(page(get(world.site, address)))
        assert chosen_filters(destination) == lone(field, choice), address
        assert selected_in(destination, "sort_field") == ["due_date"], address
        assert selected_in(destination, "sort_direction") == ["ascending"], address
        assert len(chosen_filters(destination)) == 7
    other = make_world(tmp_path / "sorted", projects=("Alpha",))
    for title, due in (
        ("X1", "2026-10-20"),
        ("X2", "2026-10-05"),
        ("X3", ""),
        ("X4", "2026-10-05"),
    ):
        other.tracker.add_task(1, title, "critical", "", due)
    expected = {
        "/projects/1?filter_status=todo": [2, 4, 1, 3],
        "/projects/1?filter_priority=critical": [2, 4, 1, 3],
        "/projects/1?filter_overdue=on": [2, 4],
    }
    for address, order in expected.items():
        assert listed_ids(parse(page(get(other.site, address)))) == order, address
    summary = parse(page(get(other.site, SUMMARY)))
    hrefs = [a.attrs["href"] for a in count_anchors(summary)]
    assert all(address in hrefs for address in expected)


def test_zero_links_on_populated_project_show_no_match(tmp_path: Path) -> None:
    """CP-513, CP-518, CP-525, T04: each zero status, priority and overdue count of populated Beta
    (its done 0 among them) opens a 200 page with its one selected control, the exact no-match
    line, no task row and no not-found page."""
    world = fixture_a(tmp_path)
    root = parse(page(get(world.site, SUMMARY_OF.format(2))))
    zeros = [a for a in count_anchors(root) if a.text() == "0"]
    assert len(zeros) == 7
    for anchor in zeros:
        response = get(world.site, anchor.attrs["href"] or "")
        destination = parse(page(response))
        assert [e.text() for e in destination.find_all("title")] == ["Beta: Tasks - tracker17"]
        line = destination.by_id("filter-no-match")
        assert line is not None and line.text() == NO_MATCH_LINE
        assert destination.find_all("tbody") == [] or listed_ids(destination) == []
        chosen = chosen_filters(destination)
        assert sorted(value for value in chosen.values() if value) != []
        assert len([value for value in chosen.values() if value]) == 1
    done = [a for a in zeros if "done" in label_of(a)]
    assert len(done) == 1 and done[0].attrs["href"] == "/projects/2?filter_status=done"


def test_empty_project_count_links_keep_no_tasks_state(tmp_path: Path) -> None:
    """CP-513, CP-515, CP-518, T05: all nine of empty Gamma's count links answer 200 with the
    existing no-tasks invitation, never the no-match line or a not-found page, and Gamma's
    Summary keeps its invitation and base Tasks target."""
    world = fixture_a(tmp_path)
    summary = parse(page(get(world.site, SUMMARY_OF.format(3))))
    anchors = count_anchors(summary)
    assert len(anchors) == 9
    (invitation,) = [p for p in summary.find_all("p") if p.attrs.get("class") == "no-tasks"]
    assert [a.attrs["href"] for a in invitation.find_all("a")] == ["/projects/3"]
    for anchor in anchors:
        destination = parse(page(get(world.site, anchor.attrs["href"] or "")))
        assert [e.text() for e in destination.find_all("title")] == ["Gamma: Tasks - tracker17"]
        assert destination.by_id("filter-no-match") is None
        assert [p for p in destination.find_all("p") if p.attrs.get("class") == "no-tasks"]


def test_followed_count_reads_current_saved_state(tmp_path: Path) -> None:
    """CP-519, T07: a captured todo link followed after T1 moves on opens only T5 with the
    singular line; the captured Summary text is not touched, and a reload shows the new count."""
    world = fixture_a(tmp_path)
    captured = page(get(world.site, SUMMARY))
    (todo,) = [a for a in count_anchors(parse(captured)) if label_of(a) == "2 tasks in todo"]
    world.tracker.move_task(1, "in-progress")
    destination = parse(page(get(world.site, todo.attrs["href"] or "")))
    assert listed_ids(destination) == [5]
    line = destination.by_id("filter-count")
    assert line is not None and line.text() == "1 task matches this filter."
    assert "2 tasks in todo" in captured
    reloaded = parse(page(get(world.site, SUMMARY)))
    assert label_of(count_anchors(reloaded)[0]) == "1 task in todo"


def test_followed_overdue_count_reads_current_local_day(tmp_path: Path) -> None:
    """CP-519, T07: an overdue link captured before midnight and followed after the handed-in
    clock crosses local midnight lists with the new day, so T5 is now overdue as well; the
    captured Summary keeps saying one."""
    world = fixture_a(tmp_path)
    captured = page(get(world.site, SUMMARY))
    (link,) = [a for a in count_anchors(parse(captured)) if label_of(a) == "1 overdue task"]
    world.clock.instant = world.clock.instant + timedelta(days=1)
    destination = parse(page(get(world.site, link.attrs["href"] or "")))
    assert listed_ids(destination) == [1, 5]
    assert "1 overdue task" in captured
    fresh = parse(page(get(world.site, SUMMARY)))
    assert [label_of(a) for a in count_anchors(fresh)][-1] == "2 overdue tasks"


def test_count_get_and_reload_never_save(tmp_path: Path) -> None:
    """CP-520, T08: following each count link and reloading it changes no Tracker state, makes no
    save, leaves the saved bytes as they were and sets no cookie."""
    world = fixture_a(tmp_path)
    saves, before = world.saver.saves, world.bytes_on_disk()
    state = {pid: world.tracker.project_tasks(pid) for pid in (1, 2, 3)}
    for address, _, _ in NINE:
        for _ in range(2):
            response = get(world.site, address)
            assert response.status == 200 and header(response, "Set-Cookie") is None
    assert world.saver.saves == saves and world.bytes_on_disk() == before
    assert {pid: world.tracker.project_tasks(pid) for pid in (1, 2, 3)} == state


def test_overdue_mark_filter_and_summary_agree(tmp_path: Path) -> None:
    """CP-497, CP-505, CP-508, AC-13, T06: only the open task due yesterday is marked and
    returned by the overdue filter, and the rendered Summary counts 1, beside an open task due
    today, a task with no date, and done and cancelled tasks due yesterday."""
    world = make_world(tmp_path)  # the clock stands at 2026-10-11 and the zone is UTC
    tracker = world.tracker
    tracker.add_task(1, "late", "medium", "", "2026-10-10")
    tracker.add_task(1, "today", "medium", "", "2026-10-11")
    tracker.add_task(1, "finished", "medium", "", "2026-10-10")
    tracker.add_task(1, "dropped", "medium", "", "2026-10-10")
    tracker.add_task(1, "undated", "medium", "", "")
    tracker.move_task(3, "in-progress")
    tracker.move_task(3, "done")
    tracker.move_task(4, "cancelled")

    listed = parse(page(get(world.site, TASKS)))
    assert overdue_titles(listed) == ["late"]
    filtered = parse(page(get(world.site, f"{TASKS}?filter_overdue=on")))
    assert listed_titles(filtered) == ["late"]
    summary = summary_rows(parse(page(get(world.site, SUMMARY))))
    assert summary["Overdue"] == "1"
    assert summary["No due date"] == "1"
    assert summary["Total"] == "5"
    summary_root = parse(page(get(world.site, SUMMARY)))
    (overdue_link,) = [a for a in count_anchors(summary_root) if "overdue" in label_of(a)]
    followed = parse(page(get(world.site, overdue_link.attrs["href"] or "")))
    assert listed_titles(followed) == ["late"]


def test_summary_get_is_a_read_of_the_requested_project() -> None:
    """CP-490, CP-494, T07: 200 HTML, one Summary read per request, the project's current
    metadata, state and saves unchanged over three reloads, and a full Summary whatever filter,
    sort or move choices the address carries."""
    site, tracker, saver = counting_site()
    saves, state = len(saver.saved), tracker.project_tasks(1)
    first = get(site, SUMMARY)
    assert first.status == 200
    assert header(first, "Content-Type") == "text/html; charset=utf-8"
    assert tracker.summary_reads == 1
    plain = page(first)
    root = parse(plain)
    assert root.find_all("h1")[0].text() == "Alpha"
    assert summary_rows(root)["Total"] == "2"
    for _ in range(3):
        assert page(get(site, SUMMARY)) == plain
    assert tracker.summary_reads == 4
    carried = f"{SUMMARY}?filter_status=done&sort_field=title&move_task=1&move_confirm=cancelled"
    assert page(get(site, carried)) == plain
    assert len(saver.saved) == saves and tracker.project_tasks(1) == state
    assert [a.attrs["href"] for a in count_anchors(root)] == EVERY_COUNT_TARGET
    for address in (carried, f"{SUMMARY}?filter_priority=high&sort_direction=descending#x"):
        again = parse(page(get(site, address)))
        assert [a.attrs["href"] for a in count_anchors(again)] == EVERY_COUNT_TARGET


@pytest.mark.parametrize("digits", ["99", "0", "9" * 5000], ids=["unknown", "zero", "oversized"])
def test_summary_missing_and_oversized_identity_use_project_not_found(digits: str) -> None:
    """CP-495, T07: an identity nothing holds, and digits longer than Python parses, answer with the
    page and 404 a missing project's Tasks address gives, titled Not found."""
    site, _, _ = counting_site()
    missing = get(site, f"/projects/{digits}/summary")
    assert missing.status == 404
    assert missing.body == get(site, f"/projects/{digits}").body
    assert [e.text() for e in parse(missing.body.decode()).find_all("title")] == [
        "Not found - tracker17"
    ]


def test_a_renamed_project_keeps_both_addresses_and_shows_the_new_name() -> None:
    """CP-493, T07: successive states with one identity and another name, with no rename action."""
    for name in ("Alpha", "Beta"):
        state = restore_state([(1, name, "")], 2, ())
        site = Site(Tracker(state, RecordingSaver(), MovableClock()), HOST)
        for address, view in ((TASKS, "Tasks"), (SUMMARY, "Summary")):
            root = parse(page(get(site, address)))
            assert root.find_all("h1")[0].text() == name
            assert [e.text() for e in root.find_all("title")] == [f"{name}: {view} - tracker17"]


def pair_under_heading(root: Element) -> list[tuple[str, str]]:
    (main,) = root.find_all("main")
    elements = [child for child in main.children if isinstance(child, Element)]
    assert [e.tag for e in elements[:2]] == ["h1", "nav"], [e.tag for e in elements[:3]]
    return [(link.attrs["href"] or "", link.text()) for link in elements[1].find_all("a")]


TASKS_VIEW_OUTCOMES = [
    "/projects/1",
    "/projects/2",
    "/projects/1?filter_status=todo",
    "/projects/1?sort_field=title",
    "/projects/1?filter_status=todo&sort_field=title&sort_direction=descending",
    "/projects/1?filter_status=done",
    "/projects/1?filter_status=blocked",
    "/projects/1?sort_field=colour",
    "/projects/1?created",
    "/projects/1?task_refused=blank-title",
    "/projects/1?task_failed=add&title=kept",
    "/projects/1?move_task=1&moved=in-progress",
    "/projects/1?move_task=1&move_confirm=cancelled",
    "/projects/1?move_task=1&move_back=cancelled",
    "/projects/1?move_task=1&move_refused=not-allowed",
    "/projects/1?move_task=1&move_failed=in-progress",
]


@pytest.mark.parametrize("address", TASKS_VIEW_OUTCOMES)
def test_tasks_view_pair_and_title_survive_every_outcome(address: str) -> None:
    """CP-491, CP-492, T10: every page of the Tasks view carries the pair right under the heading,
    its Tasks link clears every choice, and its title names the view."""
    site, _, _ = counting_site()
    response = get(site, address)
    assert response.status in (200, 202), address
    root = parse(response.body.decode())
    base = "/projects/2" if address.startswith("/projects/2") else TASKS
    assert pair_under_heading(root) == [(base, "Tasks"), (f"{base}/summary", "Summary")]
    name = "Gamma" if base == "/projects/2" else "Alpha"
    assert [e.text() for e in root.find_all("title")] == [f"{name}: Tasks - tracker17"]


def test_new_navigation_preserves_outcome_focus_and_response_contracts() -> None:
    """CP-492, T10, T11: the pair takes no focus and adds no description, the cancellation
    confirmation still answers 202 with no-store, a completion still focuses its own owner, a task
    page keeps its title, and All tasks has no Summary view."""
    site, _, _ = counting_site()
    for address in TASKS_VIEW_OUTCOMES:
        root = parse(get(site, address).body.decode())
        (pair,) = [e for e in root.find_all("nav") if e.attrs.get("aria-label") == "Project views"]
        assert pair.attrs.get("autofocus") is None
        assert [e for e in pair.walk() if "autofocus" in e.attrs] == [], address
        assert len([e for e in root.walk() if "autofocus" in e.attrs]) <= 1, address
    confirm = get(site, "/projects/1?move_task=1&move_confirm=cancelled")
    assert confirm.status == 202 and header(confirm, "Cache-Control") == "no-store"
    created = parse(page(get(site, "/projects/1?created")))
    (focus,) = [e for e in created.walk() if "autofocus" in e.attrs]
    assert focus.tag == "h1" and focus.attrs["aria-describedby"] == "created-line"
    task = parse(page(get(site, "/tasks/1")))
    assert [e.text() for e in task.find_all("title")] == ["late - tracker17"]
    assert [e for e in task.find_all("nav") if e.attrs.get("aria-label")] == []
    everything = parse(page(get(site, "/tasks")))
    assert "Summary" not in everything.text()
    assert [e.text() for e in everything.find_all("title")] == ["All tasks - tracker17"]


@pytest.mark.parametrize(
    "marks",
    [
        {"Host": HOST},
        {"Host": HOST, "Sec-Fetch-Site": "none"},
        {"Host": HOST, "Sec-Fetch-Site": "same-origin"},
    ],
    ids=["absent", "none", "same-origin"],
)
def test_summary_route_inherits_state_headers_and_request_checks(marks: dict[str, str]) -> None:
    """CP-510, NFR-4, QC-7, QC-8, QC-33, QC-34, T12: an allowed read saves nothing, sets no cookie,
    carries the page policy and no policy meta tag; another host or site is refused."""
    site, _, saver = counting_site()
    saves = len(saver.saved)
    response = get(site, SUMMARY, marks)
    assert response.status == 200
    assert header(response, "Content-Security-Policy") == POLICY
    assert "frame-ancestors 'none'" in POLICY and "script-src 'none'" in POLICY
    assert header(response, "Set-Cookie") is None
    root = parse(response.body.decode())
    assert [m for m in root.find_all("meta") if "http-equiv" in m.attrs] == []
    assert len(saver.saved) == saves
    refused: list[Response] = [
        get(site, SUMMARY, {"Host": "evil.example"}),
        get(site, SUMMARY, {"Host": HOST, "Sec-Fetch-Site": "cross-site"}),
        get(site, SUMMARY, {"Host": HOST, "Sec-Fetch-Site": "same-site"}),
    ]
    assert [r.status for r in refused] == [403, 403, 403]
    assert all(r.body == b"" for r in refused)
