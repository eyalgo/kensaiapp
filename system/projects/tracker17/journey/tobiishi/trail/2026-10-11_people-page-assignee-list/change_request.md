# Change request — 2026-10-11_people-page-assignee-list

*Opened from station `2026-10-11_people-and-assignees` (item 1 of `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`). First change unit of that station; the station's reached-when 1 to 6 are all this one capability, so it is expected to be the only one.*

---

**Request:** Give the operator a People page for keeping the list of names tasks can be assigned to. Run from `products/tracker17/` under `python3 main.py`. The header of every page that carries it gains a People link (SDD § 4 EX-12). `GET` of the People address shows the assignee list, in the order names were added, with an Add form and a Remove beside each name; the page says nothing of the operator's name and has no comment. Adding a name puts it at the end of the list. A blank name, and a name already on the list (compared exactly), are each refused on the People page where it was entered, with the typed text kept and the saved data unchanged (SRS FR-20; UXD UX-I3, UX-F8). Removing a name removes it with no confirmation step, and its completion line says the name stays on the tasks that carry it (SRS FR-22; UXD UX-S8). After an add the page opens with keyboard focus on the added name and the completion line as that element's accessible description, with no script (SDD § 4 EX-5, EX-14, RT-9). The rules live in `domain/assignees.py`, new here, and the web and application parts call them (SDD § 4 TS-3). The list is stored as the SDD's DR-4 already states, and every string on the page comes from the product's content record, none invented in code.

Tests ship with it: unit tests for `domain/assignees.py`; integration tests through the real server for the header link, the list page, add, both refusals and remove; and an end-to-end test under `products/tracker17/tests/e2e/` that adds a name in a real browser and asserts the focus and accessible-description behaviour above. This is the seed's first focus test on an element that is not a control (SDD § 11 R-2). `pytest products/tracker17/tests/` exits 0 with the unit, integration, end-to-end and architecture layers collected, and `python3 products/tracker17/tests/timed_run.py` still exits 0.

**Must not be weakened or added:** no task, priority, due date or label, and `domain/tasks.py`, `priorities.py`, `due_dates.py` and `labels.py` are not created; the saved form of a task is not changed and no state migration is written; People carries no Your name field and no comment; every test and page that passed before still passes, and no existing test is weakened to fit.

**Left to later stations of the seed:** adding and listing tasks (item 2, `add-and-list-tasks`); changing a task's assignee and the left-the-list rules of SDD § 4 RT-7 (item 3, `edit-task-fields`); the operator's name and comments (`tracker17 · nemawashi · 2026-10-07_comment-on-a-task`).

**Sizing:** the acceptance boundary is one operator capability, keeping the assignee list (SRS FR-20, FR-22; UXD UX-F8; SDD § 6 S-2 item 1; station reached-when 1 to 6). The People link, the page, add with its two refusals, remove and the focus behaviour after an add are one operation's list, error path and proof, and the focus test is that capability's own acceptance, so they stay together (`pm_right_size.md` § *Right-size to one honest merge*). It is one new domain module with its page, and fits one development flow. The task-side use of the list is a different capability, held by later stations.

**Category:** feature
**Behaviour:** changing
**Classified because:** the station's reached-when 2 says the header gains a People link and a page showing the assignee list with Add and Remove, which the product does not have today (`ls products/tracker17/domain` lists `__init__.py projects.py refusals.py state.py text.py`), so new behaviour and a new public page are added to the contract.

**Sealed:** 2026-10-11 — accepted; merged to `main` via `--no-ff`.
