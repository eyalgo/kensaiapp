"""Steps of a project's Summary, worked through the tracker's pages in a browser.

The dates the steps write and read are the machine's local date, taken once when the tracker is
started, and the day either side of it.
"""

from __future__ import annotations

import re
from contextlib import ExitStack
from datetime import date, datetime, timedelta
from urllib.parse import urlsplit

from behave import given, then, when
from behave.runner import Context
from browser_way_in import browser_page
from playwright.sync_api import Locator, Page, expect
from tracker_program import start_tracker

OPEN_STEPS = {"todo": (), "in-progress": ("in-progress",), "done": ("in-progress", "done")}
CANCEL_CONFIRM = "Move to cancelled"
NO_DUE_DATE = "none"
TODAY_WORDING = re.compile(r"\btoday\b", re.IGNORECASE)


def _dates(context: Context) -> dict[str, str]:
    today: date = context.today
    return {
        "{today}": today.isoformat(),
        "{yesterday}": (today - timedelta(days=1)).isoformat(),
        "{tomorrow}": (today + timedelta(days=1)).isoformat(),
    }


def _with_dates(context: Context, text: str) -> str:
    for marker, value in _dates(context).items():
        text = text.replace(marker, value)
    return text


def _page(context: Context) -> Page:
    page: Page = context.page
    return page


@given("the tracker is running on no saved data")
def the_tracker_is_running(context: Context) -> None:
    context.today = datetime.now().astimezone().date()
    tracker = start_tracker()
    context.add_cleanup(tracker.stop)
    context.address = tracker.address
    stack = ExitStack()
    context.page = stack.enter_context(browser_page())
    context.add_cleanup(stack.close)
    context.projects = {}


def _create_project(context: Context, name: str) -> None:
    page = _page(context)
    page.goto(context.address + "/")
    page.locator("#name").fill(name)
    page.get_by_role("button", name="Create", exact=True).click()
    page.wait_for_url(re.compile(r"/projects/\d+\?created$"))
    context.projects[name] = urlsplit(page.url).path


def _add_task(context: Context, project: str, title: str, due: str, status: str) -> None:
    page = _page(context)
    page.goto(context.address + context.projects[project])
    page.locator("#task-title").fill(title)
    if due != NO_DUE_DATE:
        page.locator("#task-due-date").fill(_with_dates(context, due))
    page.get_by_role("button", name="Add", exact=True).click()
    page.wait_for_url(re.compile(r"/tasks/\d+\?added"))
    if status == "cancelled":
        page.get_by_role("button", name=f"Move '{title}' to cancelled", exact=True).click()
        page.get_by_role("button", name=CANCEL_CONFIRM, exact=True).click()
        page.wait_for_url(re.compile(r"moved=cancelled"))
    else:
        for move in OPEN_STEPS[status]:
            page.get_by_role("button", name=f"Move '{title}' to {move}", exact=True).click()
            page.wait_for_url(re.compile(f"moved={re.escape(move)}"))
    expect(page.locator("#task-status")).to_have_text(status)


@given('the project "{name}" is created')
def the_project_is_created(context: Context, name: str) -> None:
    _create_project(context, name)


@given('the project "{name}" holds these tasks:')
def the_project_holds_these_tasks(context: Context, name: str) -> None:
    _create_project(context, name)
    for row in context.table:
        _add_task(context, name, row["title"], row["due"], row["status"])


@when('the Summary of the project "{name}" is opened')
def the_summary_is_opened(context: Context, name: str) -> None:
    page = _page(context)
    page.goto(context.address + context.projects[name])
    page.get_by_role("navigation", name="Project views").get_by_role(
        "link", name="Summary", exact=True
    ).click()
    expect(page).to_have_title(f"{name}: Summary - tracker17")
    context.project_path = context.projects[name]


def _group(context: Context, heading: str) -> Locator:
    page = _page(context)
    return page.locator("main section.summary-group").filter(
        has=page.get_by_role("heading", name=heading, exact=True)
    )


def _rows(context: Context, heading: str) -> list[tuple[str, str]]:
    rows = _group(context, heading).locator("tbody tr")
    return [
        (rows.nth(i).locator("th").inner_text(), rows.nth(i).locator("td").inner_text())
        for i in range(rows.count())
    ]


def _cell(context: Context, label: str) -> Locator:
    """The count cell of the Summary row with this label, wherever it stands on the page."""
    page = _page(context)
    rows = page.locator("main tbody tr").filter(
        has=page.locator("th", has_text=re.compile(f"^{re.escape(label)}$"))
    )
    assert rows.count() == 1, f"the Summary has {rows.count()} rows labelled {label!r}"
    return rows.locator("td")


@then('the row "{label}" shows {count:d}')
def the_row_shows(context: Context, label: str, count: int) -> None:
    cell = _cell(context, _with_dates(context, label))
    assert cell.inner_text() == str(count), (label, cell.inner_text())


@then('the row "{label}" shows {count:d} as plain text, with no link and no name of its own')
def the_row_shows_plain(context: Context, label: str, count: int) -> None:
    cell = _cell(context, _with_dates(context, label))
    assert cell.inner_text() == str(count), (label, cell.inner_text())
    assert cell.locator("a").count() == 0, f"the {label!r} count holds a link"
    for attribute in ("aria-label", "aria-labelledby"):
        assert cell.get_attribute(attribute) is None, f"the {label!r} count carries {attribute}"


@then('the row "{label}" shows {count:d} as a link named "{name}" to the project\'s overdue tasks')
def the_row_shows_overdue_link(context: Context, label: str, count: int, name: str) -> None:
    cell = _cell(context, label)
    links = cell.get_by_role("link", name=name, exact=True)
    assert links.count() == 1, f"the {label!r} count holds no link named {name!r}"
    assert links.inner_text() == str(count), links.inner_text()
    assert links.get_attribute("href") == f"{context.project_path}?filter_overdue=on", (
        links.get_attribute("href")
    )


@then('the "{heading}" group shows these rows, in this order:')
def the_group_shows_these_rows(context: Context, heading: str) -> None:
    wanted = [(_with_dates(context, row["label"]), row["count"]) for row in context.table]
    shown = _rows(context, heading)
    assert shown == wanted, f"shown {shown}, wanted {wanted}"


@then('the first row of the "{heading}" group is "{label}"')
def the_first_row_is(context: Context, heading: str, label: str) -> None:
    shown = _rows(context, heading)
    assert shown and shown[0][0] == label, f"shown {shown}"


@then('no text on the page reads "Due today" or "Today"')
def no_today_wording(context: Context) -> None:
    text = _page(context).locator("body").inner_text()
    found = TODAY_WORDING.findall(text)
    assert not found, f"the page reads {found}"


@then("the page's counts carry exactly {count:d} links")
def the_counts_carry_links(context: Context, count: int) -> None:
    links = _page(context).locator("main td a")
    assert links.count() == count, f"the counts carry {links.count()} links"


@then('the page shows "{text}"')
def the_page_shows(context: Context, text: str) -> None:
    expect(_page(context).locator("main")).to_contain_text(text)
