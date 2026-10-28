"""End-to-end tests of a project's Summary, in Chromium against a tracker run as a process (layer 5).

Checks SRS FR-38 (a project's summary as numbers, nine of them links), NFR-5 (typed text is shown
as text) and NFR-12 (every control has a name, state is carried by words). Change spec rules
CP-494, CP-501, CP-511, CP-512, CP-518, CP-520, CP-521, CP-522, CP-524 and CP-528 and the design
rows T06, T08, T11, T12, T13, T16 and T17 are the ones each test names. The tracker is seeded
through the real saved data before it starts, as a past run left it.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from playwright.sync_api import Browser, Page, expect

from application import Tracker
from domain import empty_state
from persistence import SavedData

FULL_WIDTH = 1280
ZOOM_FACTOR = 4
MINIMUM_TARGET = 24
MAXIMUM_TABS = 20
LONG_NAME = "n" * 120
SPECIAL_NAME = f'<b>&"x"</b> {LONG_NAME}'
VIEWS = "Project views"
# Alpha as `seeded` leaves it, with `crowd` fillers (low priority, no date, todo): the nine count
# links in page order as (accessible name, address). The filler count raises todo and low.
STATUS_WORDS = ("todo", "in-progress", "done", "cancelled")
PRIORITY_WORDS = ("low", "medium", "high", "critical")


def expected_links(
    project: int, statuses: tuple[int, ...], priorities: tuple[int, ...], overdue: int
) -> list[tuple[str, str]]:
    """The nine links of a Summary as the change text names them, with their addresses."""

    def name(count: int, one: str, many: str) -> str:
        return f"{count} {one}" if count == 1 else f"{count} {many}"

    base = f"/projects/{project}"
    links = [
        (name(n, f"task in {w}", f"tasks in {w}"), f"{base}?filter_status={w}")
        for w, n in zip(STATUS_WORDS, statuses, strict=True)
    ]
    links += [
        (
            name(n, f"task with {w} priority", f"tasks with {w} priority"),
            f"{base}?filter_priority={w}",
        )
        for w, n in zip(PRIORITY_WORDS, priorities, strict=True)
    ]
    links.append((name(overdue, "overdue task", "overdue tasks"), f"{base}?filter_overdue=on"))
    return links


def count_link(page: Page, accessible_name: str):  # type: ignore[no-untyped-def]
    return page.get_by_role("link", name=accessible_name, exact=True)


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 10, 28, 12, 0, tzinfo=UTC)


def seeded(
    location: Path, *, project: str = "Alpha", assignee: str = "Dana", crowd: int = 0
) -> None:
    """Alpha holds an overdue task, an undated task, a done task and an unlisted name, and Gamma
    is empty. `crowd` adds that many more tasks so the Tasks page needs scrolling."""
    tracker = Tracker(empty_state(), SavedData(location), FixedClock())
    tracker.create_project(project, "")
    tracker.create_project("Gamma", "")
    tracker.add_assignee(assignee)
    tracker.add_task(1, "late", "high", assignee, "2026-10-01")
    tracker.add_task(1, "plain", "low", "", "")
    tracker.add_task(1, "finished", "critical", "", "2026-12-01")
    tracker.add_assignee("gone")
    tracker.add_task(1, "stray", "medium", "gone", "")
    tracker.remove_assignee("gone")
    tracker.move_task(3, "in-progress")
    tracker.move_task(3, "done")
    for number in range(crowd):
        tracker.add_task(1, f"filler {number}", "low", "", "")


def counts(page: Page) -> dict[str, str]:
    rows = page.locator("main tbody tr")
    return {
        rows.nth(i).locator("th").inner_text(): rows.nth(i).locator("td").inner_text()
        for i in range(rows.count())
    }


def views(page: Page):  # type: ignore[no-untyped-def]
    return page.get_by_role("navigation", name=VIEWS)


def test_browser_can_open_summary_and_return_to_tasks(trackers, location: Path, page: Page) -> None:
    """CP-494, CP-511, CP-518, CP-520, CP-528, T08, T11, T16: Alpha's Tasks, then Summary, then
    Tasks again, each with its title and the pair; the counts are numbers and nine are links; an
    empty project shows zeros and the first-task line; entering from a scrolled Tasks page opens
    the Summary at its start; a positive count opens its selected list and a zero on a populated
    project opens the no-match line; reload and Back change no saved byte."""
    seeded(location, crowd=30)
    running = trackers.start(location)
    page.set_viewport_size({"width": FULL_WIDTH, "height": 300})
    page.goto(f"{running.address}/projects/1")
    expect(page).to_have_title("Alpha: Tasks - tracker17")
    expect(views(page).get_by_role("link")).to_have_text(["Tasks", "Summary"])
    page.evaluate("window.scrollTo(0, 60)")
    assert page.evaluate("window.scrollY") > 0
    views(page).get_by_role("link", name="Summary").click()
    expect(page).to_have_title("Alpha: Summary - tracker17")
    assert page.evaluate("window.scrollY") == 0
    assert page.locator("main h1").inner_text() == "Alpha"
    expect(views(page).get_by_role("link")).to_have_text(["Tasks", "Summary"])
    shown = counts(page)
    assert shown["Total"] == "34" and shown["done"] == "1" and shown["cancelled"] == "0"
    assert shown["high"] == "1" and shown["critical"] == "1"
    assert shown["Overdue"] == "1" and shown["No due date"] == "32"
    assert shown["Dana"] == "1" and shown["gone"] == "1" and shown["(unassigned)"] == "31"
    assert page.locator("main a").all_inner_texts() == [
        "Tasks",
        "Summary",
        *["33", "0", "1", "0", "31", "1", "1", "1", "1"],
    ]
    assert page.locator("main form, main input, main button, main script").count() == 0
    saved = running.saved_file.read_bytes()
    count_link(page, "33 tasks in todo").click()
    expect(page).to_have_title("Alpha: Tasks - tracker17")
    assert page.url == f"{running.address}/projects/1?filter_status=todo"
    expect(page.locator("#filter-count")).to_have_text("33 tasks match this filter.")
    assert page.locator("#filter-status").input_value() == "todo"
    page.reload()
    expect(page.locator("#filter-count")).to_have_text("33 tasks match this filter.")
    page.go_back()
    expect(page).to_have_title("Alpha: Summary - tracker17")
    count_link(page, "0 tasks in in-progress").click()
    expect(page.locator("#filter-no-match")).to_have_text(
        "No tasks match this filter. Press Clear to see every task."
    )
    assert page.locator("main tbody tr").count() == 0
    page.go_back()
    expect(page).to_have_title("Alpha: Summary - tracker17")
    assert running.saved_file.read_bytes() == saved
    views(page).get_by_role("link", name="Tasks").click()
    expect(page).to_have_title("Alpha: Tasks - tracker17")
    assert page.url == f"{running.address}/projects/1"
    page.goto(f"{running.address}/projects/2/summary")
    expect(page).to_have_title("Gamma: Summary - tracker17")
    assert set(counts(page).values()) == {"0"}
    assert page.locator("main td a").count() == 9
    invitation = page.locator("main p")
    expect(invitation).to_have_text(
        "This project has no tasks yet. Open Tasks to add the first task."
    )
    invitation.get_by_role("link", name="Tasks").click()
    expect(page).to_have_title("Gamma: Tasks - tracker17")


def test_browser_summary_stays_a_snapshot_until_reloaded(
    trackers, location: Path, browser: Browser
) -> None:
    """CP-494, T16: a task added in a second tab leaves the loaded Summary as it was; a reload
    shows the current counts and saves nothing."""
    seeded(location)
    running = trackers.start(location)
    context = browser.new_context()
    context.set_default_timeout(15000)
    first, second = context.new_page(), context.new_page()
    first.goto(f"{running.address}/projects/1/summary")
    assert counts(first)["Total"] == "4"
    second.goto(f"{running.address}/projects/1")
    second.locator("#task-title").fill("added later")
    second.get_by_role("button", name="Add").click()
    second.wait_for_load_state()
    saved = running.saved_file.read_bytes()
    assert counts(first)["Total"] == "4"
    first.wait_for_timeout(500)
    assert counts(first)["Total"] == "4"
    first.reload()
    assert counts(first)["Total"] == "5"
    assert running.saved_file.read_bytes() == saved
    context.close()


def test_browser_count_links_have_distinct_accessible_names(
    trackers, location: Path, page: Page
) -> None:
    """CP-521, CP-522, T06: the browser's own accessible name of each of the nine links is the
    change text's string for zero, singular and plural counts, each link shows only its numeral,
    and across all of a Summary's links equal names reach equal addresses."""
    seeded(location, crowd=2)
    running = trackers.start(location)
    for project, statuses, priorities, overdue in (
        (1, (5, 0, 1, 0), (3, 1, 1, 1), 1),
        (2, (0, 0, 0, 0), (0, 0, 0, 0), 0),
    ):
        page.goto(f"{running.address}/projects/{project}/summary")
        wanted = expected_links(project, statuses, priorities, overdue)
        for accessible_name, address in wanted:
            link = count_link(page, accessible_name)
            assert link.count() == 1, accessible_name
            assert link.get_attribute("href") == address
            assert link.inner_text() == accessible_name.split(" ", 1)[0]
        seen: dict[str, str] = {}
        for link in page.locator("main a").all():
            href = link.get_attribute("href") or ""
            name = link.get_attribute("aria-label") or link.inner_text()
            assert seen.setdefault(name, href) == href, name


def tab_to_count_link(page: Page, accessible_name: str) -> None:
    """Press Tab from the top of the page until the count link with this name has focus."""
    page.locator("body").click(position={"x": 1, "y": 1})
    for _ in range(MAXIMUM_TABS):
        page.keyboard.press("Tab")
        if page.evaluate("document.activeElement.getAttribute('aria-label')") == accessible_name:
            return
    raise AssertionError(f"Tab never reached the count link {accessible_name!r}")


def tab_to(page: Page, label: str) -> None:
    """Press Tab from the top of the page until the link with this name has focus."""
    page.locator("body").click(position={"x": 1, "y": 1})
    for _ in range(MAXIMUM_TABS):
        page.keyboard.press("Tab")
        if (
            page.evaluate("document.activeElement.textContent") == label
            and page.evaluate(
                "document.activeElement.closest('nav') && document.activeElement.closest('nav')"
                ".getAttribute('aria-label')"
            )
            == VIEWS
        ):
            return
    raise AssertionError(f"Tab never reached the {label!r} view link")


def test_summary_links_work_with_keyboard_and_visible_focus(
    trackers, location: Path, page: Page
) -> None:
    """CP-512, CP-524, T12, T17: Tab and Enter reach and activate both view links and all nine
    count links, a zero among them, found by accessible name; each shows a focus ring when
    focused, Enter opens its exact destination, and each is at least 24 by 24 CSS pixels."""
    seeded(location)
    running = trackers.start(location)
    page.goto(f"{running.address}/projects/1/summary")
    tab_to(page, "Tasks")
    ring = page.evaluate(
        "[getComputedStyle(document.activeElement).outlineStyle, "
        "getComputedStyle(document.activeElement).outlineWidth]"
    )
    assert ring[0] != "none" and ring[1] != "0px", ring
    page.keyboard.press("Enter")
    expect(page).to_have_title("Alpha: Tasks - tracker17")
    tab_to(page, "Summary")
    ring = page.evaluate(
        "[getComputedStyle(document.activeElement).outlineStyle, "
        "getComputedStyle(document.activeElement).outlineWidth]"
    )
    assert ring[0] != "none" and ring[1] != "0px", ring
    page.keyboard.press("Enter")
    expect(page).to_have_title("Alpha: Summary - tracker17")
    for name in ("Tasks", "Summary"):
        box = views(page).get_by_role("link", name=name).bounding_box()
        assert box is not None
        assert box["width"] >= MINIMUM_TARGET and box["height"] >= MINIMUM_TARGET, (name, box)
    for accessible_name, address in expected_links(1, (3, 0, 1, 0), (1, 1, 1, 1), 1):
        page.goto(f"{running.address}/projects/1/summary")
        box = count_link(page, accessible_name).bounding_box()
        assert box is not None
        assert box["width"] >= MINIMUM_TARGET and box["height"] >= MINIMUM_TARGET, (
            accessible_name,
            box,
        )
        tab_to_count_link(page, accessible_name)
        ring = page.evaluate(
            "[getComputedStyle(document.activeElement).outlineStyle, "
            "getComputedStyle(document.activeElement).outlineWidth]"
        )
        assert ring[0] != "none" and ring[1] != "0px", (accessible_name, ring)
        page.keyboard.press("Enter")
        page.wait_for_url(f"{running.address}{address}")
        assert page.url == f"{running.address}{address}"


def test_summary_names_and_groups_reflow_at_four_hundred_percent(
    trackers, location: Path, browser: Browser
) -> None:
    """CP-501, CP-512, CP-524, T13, T17: 400% zoom of a 1280-pixel window is a 320-pixel-wide
    viewport (the method the filter and sort proofs use). Long, special-character names show as
    typed text, the title is exact, the groups wrap inside the window and the page does not scroll
    sideways."""
    seeded(location, project=SPECIAL_NAME, assignee=SPECIAL_NAME)
    running = trackers.start(location)
    context = browser.new_context(viewport={"width": FULL_WIDTH // ZOOM_FACTOR, "height": 800})
    context.set_default_timeout(15000)
    page = context.new_page()
    page.goto(f"{running.address}/projects/1/summary")
    assert page.title() == f"{SPECIAL_NAME}: Summary - tracker17"
    assert page.locator("main h1").inner_text() == SPECIAL_NAME
    assert page.locator("main b").count() == 0
    assert SPECIAL_NAME in page.locator("main tbody th").all_inner_texts()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    window = FULL_WIDTH // ZOOM_FACTOR
    groups = page.locator("main section.summary-group")
    assert groups.count() == 4
    for index in range(groups.count()):
        box = groups.nth(index).bounding_box()
        assert box is not None and box["x"] >= 0 and box["x"] + box["width"] <= window, box
    assert page.evaluate(
        "[...document.querySelectorAll('main *')].every("
        "e => e.getBoundingClientRect().right <= window.innerWidth + 1)"
    )
    links = page.locator("main td a")
    assert links.count() == 9
    for index in range(links.count()):
        box = links.nth(index).bounding_box()
        assert box is not None and box["x"] >= 0 and box["x"] + box["width"] <= window, box
        assert box["width"] >= MINIMUM_TARGET and box["height"] >= MINIMUM_TARGET, box
    context.close()
