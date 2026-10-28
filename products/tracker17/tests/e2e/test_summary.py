"""End-to-end tests of a project's Summary, in Chromium against a tracker run as a process (layer 5).

Checks SRS FR-38 (a project's summary as plain numbers), NFR-5 (typed text is shown as text) and
NFR-12 (every control has a name, state is carried by words). Change spec rules CP-494, CP-501,
CP-511 and CP-512 and the design rows T16 and T17 are the ones each test names. The tracker is
seeded through the real saved data before it starts, as a past run left it.
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
    tracker.add_task(1, "stray", "medium", "gone", "")
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
    """CP-494, CP-511, T16: Alpha's Tasks, then Summary, then Tasks again, each with its title and
    the pair; the counts are plain numbers; an empty project shows zeros and the first-task line;
    entering from a scrolled Tasks page opens the Summary at its start."""
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
    assert page.locator("main a").all_inner_texts() == ["Tasks", "Summary"]
    assert page.locator("main form, main input, main button, main script").count() == 0
    views(page).get_by_role("link", name="Tasks").click()
    expect(page).to_have_title("Alpha: Tasks - tracker17")
    assert page.url == f"{running.address}/projects/1"
    page.goto(f"{running.address}/projects/2/summary")
    expect(page).to_have_title("Gamma: Summary - tracker17")
    assert set(counts(page).values()) == {"0"}
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
    """CP-512, T17: Tab and Enter reach and activate both view links, each shows a focus ring when
    focused, and each is at least 24 by 24 CSS pixels."""
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


def test_summary_names_and_groups_reflow_at_four_hundred_percent(
    trackers, location: Path, browser: Browser
) -> None:
    """CP-501, CP-512, T17: 400% zoom of a 1280-pixel window is a 320-pixel-wide viewport (the
    method the filter and sort proofs use). Long, special-character names show as typed text, the
    title is exact, the groups wrap inside the window and the page does not scroll sideways."""
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
    context.close()
