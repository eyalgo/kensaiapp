"""End-to-end tests of renaming a project, in Chromium against a tracker run as a process (layer 5).

Checks SRS FR-10 and FR-39 (the naming rules and their refusals), FR-12 (renaming a project),
NFR-5 (typed text is shown as text), NFR-12 (state is carried by words and a focused control), and
acceptance criteria AC-12 and AC-18. Change spec rules CP-549, CP-550, CP-556, CP-560, CP-561 and
CP-565 and NFDR QC-36 are the ones each test names. Words are those of this change's text record.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from playwright.sync_api import Page, expect

if TYPE_CHECKING:
    from conftest import RunningTracker

HOSTILE = '<b>R&D "x"</b>'
POINTER_FLOOR = 24
TAB_LIMIT = 60


def create(page: Page, address: str, name: str) -> None:
    page.goto(address + "/")
    page.locator("#name").fill(name)
    page.get_by_role("button", name="Create").click()
    page.wait_for_load_state()


def press_and_load(page: Page, key: str) -> None:
    with page.expect_navigation():
        page.keyboard.press(key)
    page.wait_for_load_state()


def field(page: Page):
    return page.get_by_label("Project name")


def save(page: Page):
    return page.get_by_role("button", name="Save")


def tab_to(page: Page, target) -> None:
    """Tab from wherever focus is until the control has it: no pointer, no scripted focus."""
    for _ in range(TAB_LIMIT):
        page.keyboard.press("Tab")
        if target.evaluate("e => e === document.activeElement"):
            return
    raise AssertionError("Tab never reached the control")


def retype(page: Page, name: str) -> None:
    page.keyboard.press("ControlOrMeta+A")
    if name:
        page.keyboard.type(name)
    else:
        page.keyboard.press("Delete")


def outline_of(page: Page) -> str:
    return page.evaluate("getComputedStyle(document.activeElement).outlineStyle")


def test_rename_is_keyboard_operable_and_described(tracker: RunningTracker, page: Page) -> None:
    """CP-549, CP-550, CP-556, CP-560: Tab reaches the field and Save, Enter submits once without
    a confirmation, success and refusal focus the field described by their line, focus is
    visible and Save meets the pointer-target floor."""
    create(page, tracker.address, "Alpha")
    page.goto(tracker.address + "/projects/1")
    tab_to(page, field(page))
    assert outline_of(page) == "solid"
    retype(page, "Beta")
    press_and_load(page, "Enter")
    assert re.fullmatch(re.escape(tracker.address) + r"/projects/1\?.*", page.url)
    expect(page.locator("h1")).to_have_text("Beta")
    expect(page).to_have_title("Beta: Tasks - tracker17")
    expect(field(page)).to_be_focused()
    expect(field(page)).to_have_accessible_description("You renamed 'Alpha' to 'Beta'.")
    assert outline_of(page) == "solid"
    tab_to(page, save(page))
    assert outline_of(page) == "solid"
    box = save(page).bounding_box()
    assert box is not None and box["width"] >= POINTER_FLOOR and box["height"] >= POINTER_FLOOR
    press_and_load(page, "Enter")
    assert page.url == tracker.address + "/projects/1"
    expect(page.locator("main")).not_to_contain_text("You renamed")
    field(page).focus()
    retype(page, "")
    press_and_load(page, "Enter")
    expect(field(page)).to_be_focused()
    expect(field(page)).to_have_accessible_description("A project needs a name. Type one.")
    expect(field(page)).to_have_value("")
    expect(page.locator("h1")).to_have_text("Beta")


def test_a_hostile_name_survives_a_browser_rename_and_history(
    tracker: RunningTracker, page: Page
) -> None:
    """CP-550, CP-556, CP-561, CP-565, QC-36: the name typed with `<`, `&` and quotes shows as typed
    in the heading, title, Projects entry, field and completion; a duplicate is refused; a real
    reload, Back and Forward keep the finished lines and save nothing more."""
    create(page, tracker.address, "Alpha")
    create(page, tracker.address, "Other")
    saved_file = tracker.location / "tracker.json"
    page.goto(tracker.address + "/projects/1")
    field(page).fill(HOSTILE)
    with page.expect_navigation():
        save(page).click()
    page.wait_for_load_state()
    expect(page.locator("h1")).to_have_text(HOSTILE)
    expect(page).to_have_title(f"{HOSTILE}: Tasks - tracker17")
    expect(field(page)).to_have_value(HOSTILE)
    completion = f"You renamed 'Alpha' to '{HOSTILE}'."
    expect(field(page)).to_have_accessible_description(completion)
    success_url = page.url
    page.reload()
    expect(field(page)).to_have_accessible_description(completion)
    page.goto(tracker.address + "/")
    expect(page.locator("ul.project-list a")).to_have_text([HOSTILE, "Other"])
    page.goto(tracker.address + "/projects/2")
    field(page).fill(HOSTILE)
    with page.expect_navigation():
        save(page).click()
    page.wait_for_load_state()
    refusal = f"A project named '{HOSTILE}' already exists. Choose a different name."
    expect(field(page)).to_be_focused()
    expect(field(page)).to_have_accessible_description(refusal)
    expect(field(page)).to_have_value(HOSTILE)
    expect(page.locator("h1")).to_have_text("Other")
    refused_url, before = page.url, saved_file.read_bytes()
    page.reload()
    expect(field(page)).to_have_accessible_description(refusal)
    page.go_back()
    page.go_forward()
    assert page.url == refused_url
    expect(field(page)).to_have_accessible_description(refusal)
    assert saved_file.read_bytes() == before
    page.goto(success_url)
    expect(field(page)).to_have_accessible_description(completion)
    page.go_back()
    page.go_forward()
    expect(field(page)).to_have_accessible_description(completion)
    assert saved_file.read_bytes() == before
