"""The browser way in: open a page in headless Chromium and give a step what the page shows,
through Playwright for Python."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from playwright.sync_api import Browser, Error, Page, Playwright, sync_playwright

# Playwright's error for a browser that was never installed starts with this phrase.
MISSING_BROWSER_SIGN = "Executable doesn't exist"

CHROMIUM_MISSING = (
    "The browser way in found no Chromium for Playwright. Run this once on this machine, from "
    "inside the .behave folder: uv run --locked playwright install chromium"
)

# How long one browser action waits for the page before the step fails.
ACTION_TIMEOUT_MS = 15000


class ChromiumMissing(AssertionError):
    """Chromium has not been installed for Playwright on this machine. An assertion error, so
    Behave reports the scenario as failed rather than as an error."""


def _launch(playwright: Playwright) -> Browser:
    try:
        return playwright.chromium.launch(headless=True)
    except Error as error:
        if MISSING_BROWSER_SIGN in str(error):
            raise ChromiumMissing(CHROMIUM_MISSING) from error
        raise


def page_heading(url: str) -> str:
    """Open `url` in headless Chromium and give back the text of the page's first heading."""
    with sync_playwright() as playwright:
        browser = _launch(playwright)
        try:
            page = browser.new_page()
            page.goto(url)
            return page.inner_text("h1")
        finally:
            browser.close()


@contextmanager
def browser_page() -> Iterator[Page]:
    """A page in headless Chromium, for a scenario that works through several pages in turn, as a
    person does in one browser window. The browser closes when the block ends."""
    with sync_playwright() as playwright:
        browser = _launch(playwright)
        try:
            session = browser.new_context()
            session.set_default_timeout(ACTION_TIMEOUT_MS)
            yield session.new_page()
        finally:
            browser.close()
