from __future__ import annotations

from behave import then, when
from behave.runner import Context
from server_way_in import request_page


@when("the page is requested through the server way in")
def the_page_is_requested_through_the_server_way_in(context: Context) -> None:
    context.response = request_page(context.page_url)


@then("the response status is {status:d}")
def the_response_status_is(context: Context, status: int) -> None:
    assert context.response.status_code == status, context.response.status_code


@then('the response holds the heading "{heading}"')
def the_response_holds_the_heading(context: Context, heading: str) -> None:
    assert f"<h1>{heading}</h1>" in context.response.text, context.response.text
