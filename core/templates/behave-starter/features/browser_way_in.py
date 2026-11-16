"""The browser way in: open a page in headless Chromium and give a step what the page shows,
through Playwright for Python."""

from __future__ import annotations

from playwright.sync_api import Error, sync_playwright

# Playwright's error for a browser that was never installed starts with this phrase.
MISSING_BROWSER_SIGN = "Executable doesn't exist"

# Playwright's errors for a machine without the system libraries its driver or Chromium loads: the
# driver exits before it answers, or Chromium's launch reports the libraries the host lacks.
MISSING_LIBRARIES_SIGNS = (
    "Connection closed while reading from the driver",
    "Host system is missing dependencies",
)

CHROMIUM_MISSING = (
    "The browser way in found no Chromium for Playwright. Run this once on this machine, from "
    "inside the .behave folder: uv run --locked playwright install chromium"
)

LIBRARIES_MISSING = (
    "The browser way in could not start Playwright or Chromium: this machine lacks system "
    "libraries they load, and the output above names them. Install them once on this machine, as "
    "root, from inside the .behave folder: uv run --locked playwright install-deps chromium"
)


class ChromiumMissing(AssertionError):
    """Chromium has not been installed for Playwright on this machine. An assertion error, so
    Behave reports the scenario as failed rather than as an error."""


class LibrariesMissing(AssertionError):
    """The machine lacks system libraries Playwright's driver or Chromium loads. An assertion
    error, for the same reason as `ChromiumMissing`."""


def _names_missing_libraries(error: Exception) -> bool:
    return any(sign in str(error) for sign in MISSING_LIBRARIES_SIGNS)


def page_heading(url: str) -> str:
    """Open `url` in headless Chromium and give back the text of the page's first heading."""
    try:
        playwright = sync_playwright().start()
    except Exception as error:
        if _names_missing_libraries(error):
            raise LibrariesMissing(LIBRARIES_MISSING) from error
        raise
    try:
        try:
            browser = playwright.chromium.launch(headless=True)
        except Error as error:
            if MISSING_BROWSER_SIGN in str(error):
                raise ChromiumMissing(CHROMIUM_MISSING) from error
            if _names_missing_libraries(error):
                raise LibrariesMissing(LIBRARIES_MISSING) from error
            raise
        try:
            page = browser.new_page()
            page.goto(url)
            return page.inner_text("h1")
        finally:
            browser.close()
    finally:
        playwright.stop()
