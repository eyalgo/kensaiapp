# Change request — 2026-10-07_a-not-found-page

*Opened from station `2026-10-07_a-project-that-stays` (item 1 of `tracker17 · nemawashi · 2026-10-07_first-project`). Second change unit of that station; the station may take more.*

---

**Request:** Make an address for a project that does not exist show the not-found page instead of an empty 404. Run from `products/tracker17/` under `python3 main.py`. Today an unknown address answers 404 with an empty body (`tests/integration/test_routes.py:351-364`, `tests/integration/test_listener.py:88-110`). After this change the browser shows a page that says the project does not exist and links to Projects, and speaks of a project only: it names no task and offers no All tasks link, because tasks do not exist yet (SDD § 6 S-1; UXD UX-S10). The same page answers an address whose project identity is too long to read as a number, and the status stays 404. Nothing is written to `data/` by any of these requests. The page is built through the same parts and seams as the pages already there, with its words taken from the product's content record and no string invented in code.

Tests ship with it: an end-to-end test that an address with no project shows the page with its one link to Projects and that following the link lands on the Projects page, and an integration test per route that answers it, replacing the empty-body checks that no longer hold. `pytest tests/` and `pytest tests/e2e/` each exit 0.

**Must not be weakened or added:** the SDD's seams are used as written; no tasks, add-task form, People or All tasks links, rename or delete; no unreadable-data page and no second-tracker refusal; the one plain message when the address is taken is the next unit; the setup README is not touched beyond what the tests need; project creation, its refusals and saved data keep behaving as sealed in `2026-10-07_create-a-project-that-stays`.

**Left to later change units of this station:** the one plain message when something else holds the address (station reached-when 3), and the check that the station's whole reached-when holds. The README is the next station.

**Sizing:** the acceptance boundary is one operator action, following an address that names no project and being told so with a way back (SDD § 6 S-1, *Behaviour*; UXD UX-S10; station reached-when 2, last sentence). Its page, status, route coverage and tests stay together (`pm_right_size.md` § *Right-size to one honest merge*). The address-taken message is a different system responsibility, reporting a failed start, with its own acceptance boundary, which the previous unit's sizing already named as separate (`journey/tobiishi/trail/2026-10-07_create-a-project-that-stays/change_request.md`, *Sizing*), so it stays the next unit.

**Category:** feature
**Behaviour:** changing
**Classified because:** the station's reached-when 2 ends "An address for a project that does not exist shows the not-found page", and the product answers an empty 404 today, so a page a reader will act on is added to the contract.

**Sealed:** 2026-10-07 — accepted; merged to `main` via `--no-ff`.
