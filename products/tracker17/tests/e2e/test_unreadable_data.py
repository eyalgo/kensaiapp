"""End-to-end test of a start on unreadable saved data, in Chromium against a tracker process
(layer 5).

Checks SRS FR-1 (the start tells the operator where to open the tracker), FR-4 and AC-7
(unreadable saved data is served as one plain page, left as it was) and NFR-5 (typed text is shown
as text). Change spec rules CP-710, CP-711, CP-716, CP-717, CP-719, CP-723 and CP-731 and NFDR QC-36
and QC-55 are the ones the test names.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from playwright.sync_api import Page, expect

if TYPE_CHECKING:
    from conftest import TrackerFactory

DAMAGED = b'{"next_project_id": 3, "projects": [ truncated'
HOSTILE_NAME = 'data<&"'
CONTROLS = "a, form, button, input, select, textarea, nav"
HEADING = "The saved data can't be read"


def test_the_browser_opens_the_unreadable_page_without_controls(
    trackers: TrackerFactory, page: Page, tmp_path: Path
) -> None:
    """CP-731, CP-711, CP-716, CP-717, CP-719, CP-723: the first console line, the exact heading
    and location (with `<`, `&` and `"` as text), no link, form or data control, and a stylesheet
    that loads. The document's own 503 is not a failed resource load."""
    location = tmp_path / HOSTILE_NAME
    location.mkdir()
    (location / "tracker.json").write_bytes(DAMAGED)
    tracker = trackers.start(location)
    assert tracker.first_line == (
        f"The tracker couldn't read its saved data at {location.absolute()}, and nothing in it "
        f"was changed. Open {tracker.address} in your browser to read this on a page. To start "
        "fresh on purpose, follow Setting saved data aside in the setup instructions."
    )
    failed: list[str] = []
    answers: dict[str, int] = {}
    page.on("requestfailed", lambda request: failed.append(request.url))
    page.on("response", lambda response: answers.update({response.url: response.status}))

    response = page.goto(tracker.address + "/")
    page.wait_for_load_state("load")

    assert response is not None and response.status == 503
    expect(page.locator("h1")).to_have_text(HEADING)
    expect(page.locator("h1")).to_have_count(1)
    expect(page.locator("body")).to_contain_text(str(location.absolute()))
    expect(page.locator(CONTROLS)).to_have_count(0)
    assert failed == []
    assert answers[tracker.address + "/style.css"] == 200
    assert tracker.stop() == (0, "")
    assert (location / "tracker.json").read_bytes() == DAMAGED
