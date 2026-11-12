"""The browser way in: open a page in headless Chromium and give a step what the page shows,
through Playwright for Python."""

from __future__ import annotations

from playwright.sync_api import Error, sync_playwright

# Playwright's error for a browser that was never installed starts with this phrase.
MISSING_BROWSER_SIGN = "Executable doesn't exist"

CHROMIUM_MISSING = (
    "The browser way in found no Chromium for Playwright. Run this once on this machine, from "
    "inside the .behave folder: uv run --locked playwright install chromium"
)


class ChromiumMissing(AssertionError):
    """Chromium has not been installed for Playwright on this machine. An assertion error, so
    Behave reports the scenario as failed rather than as an error."""


def page_heading(url: str) -> str:
    """Open `url` in headless Chromium and give back the text of the page's first heading."""
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except Error as error:
            if MISSING_BROWSER_SIGN in str(error):
                raise ChromiumMissing(CHROMIUM_MISSING) from error
            raise
        try:
            page = browser.new_page()
            page.goto(url)
            return page.inner_text("h1")
        finally:
            browser.close()
