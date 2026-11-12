from __future__ import annotations

from behave import then, when
from behave.runner import Context
from browser_way_in import page_heading


@when("the page is opened through the browser way in")
def the_page_is_opened_through_the_browser_way_in(context: Context) -> None:
    context.shown_heading = page_heading(context.page_url)


@then('the browser shows the heading "{heading}"')
def the_browser_shows_the_heading(context: Context, heading: str) -> None:
    assert context.shown_heading == heading, context.shown_heading
