"""The HTTP edge: turns a rendered page into a response."""

from lanternfold.screens import render_goodbye, render_welcome

PAGE_HEADERS = (
    ("Content-Security-Policy", "default-src 'self'"),
    ("X-Content-Type-Options", "nosniff"),
    ("Referrer-Policy", "no-referrer"),
)


def page_response(body: str) -> tuple[str, tuple[tuple[str, str], ...]]:
    """Pair a page body with the page header set."""
    return body, PAGE_HEADERS


def welcome(name: str):
    return page_response(render_welcome(name))


def goodbye():
    return page_response(render_goodbye())
