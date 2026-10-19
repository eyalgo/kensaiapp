# Change request — 2026-10-07_create-a-project-that-stays

*Opened from station `2026-10-07_a-project-that-stays` (item 1 of `tracker17 · nemawashi · 2026-10-07_first-project`). First change unit of that station; the station may take more.*

---

**Request:** Make `python3 main.py` start a working tracker in which a person can create a first project, see it, and still find it after stopping and starting. Run it from `products/tracker17/`. It prints the address and the saved-data location, nothing before them, and serves until stopped. The browser shows the first-run Projects page with the create form. Beside the description field a note says the description cannot be changed later and gives the most characters it holds, and that number equals the field's `maxlength`. Creating a project lands on its own page, which shows its name and description and says it has no tasks yet, with no add-task form. A blank name and a name already in use (case ignored) are each refused beside the name field, the typed text is kept, and the page opens with keyboard focus in the name field and the reason as its accessible description. A name over the maximum, sent in a request no page can send, gets the page that gives the reason, holds none of the sent text, and leaves the saved data unchanged. Projects lists every project by name, and a project is still listed after a stop and a start. The data is saved under `data/`, which stays out of version control, so `git status --short` lists nothing there after a project is created. This is one path through all five parts and all seven seams of SDD § 3 (`domain/projects.py`, `application/`, `persistence/`, `web/`, `main.py`), not a shortcut through one. A start that cannot read the saved data stops with one plain message and writes nothing (SDD § 4 SD-4).

Tests ship with it: `pytest tests/` and `pytest tests/e2e/` each exit 0, between them holding at least one unit, one integration and one end-to-end test. They include the tests SRS AC-6 (for a project) describes, an end-to-end test of focus and accessible description on a refused name (SDD § 4 EX-4, EX-14, RT-9), an end-to-end test filling the description to its maximum with line breaks and finding it saved whole (AC-20, description half), the over-long name test (AC-12, § 4 RT-8, RT-10, § 11 R-10), and the integration test that the sentence's number equals `maxlength`. SRS AC-9 (interrupted save) and AC-18 (visible failures) are covered here as far as saving a project and starting the tracker reach them.

**Must not be weakened or added:** the SDD's seams are used as written; no tasks, add-task form, People or All tasks links, rename or delete; no unreadable-data page and no second-tracker refusal; the setup README is not touched beyond what the tests need.

**Left to later change units of this station:** the not-found page for an address with no project, the one plain message when something else holds the address, and the check that the station's whole reached-when holds. The README is the next station.

**Sizing:** the acceptance boundary is one operator action, creating a project and finding it again after a restart (SDD § 6 S-1, *Behaviour*, with the *Command* tests that pin it). Its refusals, saving and tests stay together (`pm_right_size.md` § *Right-size to one honest merge*). The not-found page and the address-taken message are separate responsibilities (routing an unknown address, reporting a failed start) with their own acceptance boundaries, so they are the next unit. The whole station in one flow would span five parts, seven seams and the full suite, which is the delivery-size obstacle.

**Category:** feature
**Behaviour:** changing
**Classified because:** the station's reached-when adds a start command, pages, a saved-data contract and refusals to a product whose `main.py:main` is empty; that adds to the contract.

**Sealed:** 2026-10-07 — accepted; merged to `main` via `--no-ff`.
