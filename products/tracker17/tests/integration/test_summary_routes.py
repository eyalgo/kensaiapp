"""Integration tests of the Summary request and the project views' links through the real Site (layer 3).

Checks SRS FR-38 (a project's summary), FR-25 and FR-35 (the overdue rule the list, the filter and
the Summary share), NFR-4 (a request from another site is refused), NFR-8 (a read changes nothing)
and AC-13. Change spec rules CP-490 to CP-495, CP-497, CP-505, CP-508 and CP-510 and NFDR QC-7,
QC-8, QC-28, QC-33 and QC-34 are the ones each test names; the design rows are T06, T07, T10 and
T12. The real Site, Tracker and SavedData are used with an injected clock; no product name is
patched, and the one read count is a subclass handed to the Site.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from test_pages import Element, parse
from test_routes import POLICY, RecordingSaver, get, header, page
from test_task_routes import HOST, MovableClock, make_world, utc_zone  # noqa: F401

from application import ProjectSummary, Tracker
from domain import empty_state, restore_state
from web import Response, Site

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
