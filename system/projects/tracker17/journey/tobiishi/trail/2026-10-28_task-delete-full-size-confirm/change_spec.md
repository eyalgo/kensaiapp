# Change Spec — Delete task's first press and its confirmation take the full-size height

**Date:** 2026-10-29
**Category:** feature
**Behaviour:** changing
**Request:** Make Delete task's confirmation the same height as the Delete task button it replaces. DESIGN.md `components.confirm-strip` says the strip's sentence and confirming button take the height of the button the strip replaces: `spacing.row-control` for a status move, `spacing.control` for a full-size secondary button, which Delete task's first press is. Today the task strip is built with the `row-control` size in `_delete_strip` (`products/tracker17/web/pages.py`), so its confirming button is 28px against the 36px first press. Give Delete task's strip the full-size (`spacing.control`) sizing Delete project's strip already uses, so at `/tasks/<id>?delete_confirm` the confirming button measures 36px (±0.5), equal to the first press at `/tasks/<id>`, and the sentence is at least that tall. Add an end-to-end test in `products/tracker17/tests/e2e/` that measures Delete task's confirming button against its first press (bounding boxes, as the neighbouring tests do) and fails on `main` today. Correct the assertion in `tests/e2e/test_delete_project.py` that pins Delete task's confirming button at `ROW_CONTROL_HEIGHT`, which this change makes false. Both suites must pass, `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` run on its own, since the card's `Test command:` skips `tests/e2e/`. Sizing: one capability (Delete task's confirmation sizing) and one merge; acceptance boundary is station `2026-10-28_task-delete-full-size-confirm`'s reached-when, sourced from DESIGN `components.confirm-strip`. What must not be weakened: status-move confirmations keep `spacing.row-control` (28px at `/projects/<id>?move_task=<id>&move_confirm=cancelled`); the back-out control stays full-size everywhere (RN-25); no page's wording, focus behaviour, strip part order, or Delete project's strip changes; task deletion itself (what is saved, redirects, failure line) stays as walked; existing Delete task tests pass unchanged apart from the one corrected assertion; no moving of tasks between projects (SRS FR-14) and no change of a project's description (UXD § 10).
**Language resolution:** Python — step 1 (`project.md` `Languages:`) — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with its seven concerns

---

## Change Summary

On a task's page, Delete task's first press and the confirmation that replaces it both take DESIGN's full-size control height, 36px. Today both are 28px, so the request's premise that the first press is already 36px is false (Locked Answers, Gap 1), and the request's outcome needs the first press resized as well as the strip.

File paths below are relative to the product, whose location is `system/projects/tracker17/project.md` `Product path:`.

---

## Rules

### Delete task's first press

- **CP-609:** On a task's page (`/tasks/<id>`), Delete task's first press is the full-size {components.button-secondary} that DESIGN § Components names it ("{components.button-secondary} is every other full-size button: … Delete task's first press …", `docs/DESIGN.md:450-452`), and it measures `spacing.control`, 36px (±0.5), tall. This holds in each form the page shows the first press: the ordinary page, the page restored after Back out (its address carries `delete_back`), and the page after a failed save. Today it measures 28px: it is styled as a row-control button (`web/pages.py:890`, class `delete-button`; `web/style.css:228-244`, `height: 28px`).

### Delete task's confirmation

- **CP-610:** At `/tasks/<id>?delete_confirm`, the confirmation's confirming button ("Delete task") measures `spacing.control`, 36px (±0.5), tall, and its height is within 0.5px of the first press's height measured at `/tasks/<id>` (DESIGN `components.confirm-strip`, `docs/DESIGN.md:457-466`). Today it measures 28px, because the strip is built at the row-control size (`web/pages.py:855-863`, `size=TRIGGER_SIZE`, `"row-control"`).
- **CP-611:** At `/tasks/<id>?delete_confirm`, the confirmation's sentence ("Delete '{title}'? You can't undo this.") is at least 36px (−0.5) tall, at least the first press's height, and still covers the whole spot the first press stood in (DESIGN RN-25).
- **CP-612:** At `/tasks/<id>?delete_confirm`, the back-out control ("Back out") stays the full-size {components.button-secondary}, 36px (±0.5) tall (DESIGN RN-25). It measures 36px today, and this change keeps it.

### What stays as it is

- **CP-613:** Every status-move confirmation keeps `spacing.row-control`: at `/projects/<id>?move_task=<id>&move_confirm=cancelled` the confirming button ("Move to cancelled") measures 28px (±0.5) tall, as it does today.

### Tests and checks

- **CP-614:** An end-to-end test under `tests/e2e/` opens a task's page, measures Delete task's first press at `/tasks/<id>`, then measures the confirmation at `/tasks/<id>?delete_confirm`, using bounding boxes in Chromium as the neighbouring tests do. It asserts CP-609, CP-610 and CP-611: the first press and the confirming button are each 36px (±0.5) and within 0.5px of each other, and the sentence is at least the first press's height. It fails on the code as it stands at the commit this change starts from, where both the first press and the confirming button measure 28px, and it passes after the change.
- **CP-615:** In `tests/e2e/test_delete_project.py`, `test_project_strip_uses_full_size_controls`, the assertion on the `/tasks/1?delete_confirm` confirming button (`task_confirm`) changes from `ROW_CONTROL_HEIGHT` to `CONTROL_HEIGHT` (36px, ±0.5). The same test's assertion that the status-move confirming button at `/projects/1?move_task=1&move_confirm=cancelled` is `ROW_CONTROL_HEIGHT` stays as it is. No other existing test changes.
- **CP-616:** Both suites pass (SDD § 2, "'Both suites pass' means `pytest tests/` exits 0 and `pytest tests/e2e/` exits 0"; SDD § 4 TS-1): from the change worktree's root, `pytest products/tracker17/tests/` exits 0, and `pytest products/tracker17/tests/e2e/` exits 0, run on its own because the first command does not collect `tests/e2e/` (`tests/conftest.py:7-9`).
- **CP-617:** The code passes the three commands NFDR QC-62 names, each exiting 0 when run from the product root: `ruff format --check .`, `ruff check .`, and `mypy main.py errors.py domain application persistence web`, at the versions QC-39 pins.
- **CP-618:** The test module that holds CP-614's test names in its opening docstring the SRS requirements or acceptance criteria it checks, every path a docstring names exists, and that module is among the test modules `domain/tasks.py`'s opening docstring names (NFDR QC-11; checked by `tests/architecture/test_trace.py` in `pytest tests/`).

---

## Examples

| Scenario | Expected behavior | Rules |
|---|---|---|
| Open `/tasks/1` for a task in an open status | Delete task's first press measures 36px (±0.5) tall. Today: 28px. | CP-609 |
| Press Back out on `/tasks/1?delete_confirm` | The restored Delete task button measures 36px (±0.5) tall. | CP-609 |
| Press the confirming "Delete task" on `/tasks/1?delete_confirm` while the save fails | The page shows the failure line, and the restored Delete task button measures 36px (±0.5) tall. | CP-609 |
| Open `/tasks/1?delete_confirm` | The confirming button measures 36px (±0.5), within 0.5px of the first press at `/tasks/1`; the sentence is at least 36px tall and covers the first press's spot; Back out measures 36px. Today: confirming button 28px. | CP-610, CP-611, CP-612 |
| Open `/projects/1?move_task=1&move_confirm=cancelled` | The "Move to cancelled" confirming button measures 28px (±0.5). Unchanged. | CP-613 |
| Run CP-614's test against the code at the change's starting commit | It fails: the first press and the confirming button both measure 28px, not 36px. | CP-614 |
| Run CP-614's test after the change | It passes. | CP-614 |
| Run `test_project_strip_uses_full_size_controls` after the change | It passes, with the task confirmation asserted at `CONTROL_HEIGHT` and the move confirmation still at `ROW_CONTROL_HEIGHT`. | CP-615, CP-613 |
| Run `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` after the change | Both exit 0. | CP-616 |
| Run `ruff format --check .`, `ruff check .`, `mypy main.py errors.py domain application persistence web` from the product root after the change | Each exits 0. | CP-617 |
| Run `pytest tests/` with CP-614's test in a module whose docstring names no SRS requirement or acceptance criterion | `test_every_test_module_names_a_requirement_or_acceptance_criterion` fails; the change does not land that way. | CP-618 |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| Delete task's first press measures 28px today, not the 36px the request states (CP-609, Gap 1) | A measurement test placed in a disposable clone at `62123a148`, run with `pytest -s` in Chromium 153 under `playwright==1.63.0` against a tracker started by `main` through the e2e fixtures (a real start) | `trigger=28 sentence=103.5 confirm=28 back=36` |
| The first press is styled at the row-control height | Read `web/pages.py:885-891` and `web/style.css:228-244` | The button carries `class="delete-button"`; `button.delete-button` sets `height: 28px`, with a comment saying the control is "the same size and look" as a status move |
| The strip is built at the row-control size (CP-610) | Read `web/pages.py:855-863` and `:765` | `_delete_strip` passes `size=TRIGGER_SIZE`; `TRIGGER_SIZE = "row-control"`; Delete project's strip passes `size=FULL_SIZE` (`:953`), `FULL_SIZE = "control"` (`:897`) |
| Giving only the strip the full size, as the request describes, leaves the confirming button taller than the first press (Gap 1) | The same measurement in the clone, with `_delete_strip` changed to `FULL_SIZE` and the first press left as it is | `trigger=28 sentence=111.5 confirm=36 back=36`; the equality assertion failed |
| CP-609 to CP-613 can all hold together, and no existing test other than the one CP-615 corrects pins the old heights (CP-615, "No other existing test changes") | In the clone: strip at `FULL_SIZE`, first press given the `button-secondary` class, the `task_confirm` assertion changed to `CONTROL_HEIGHT`; then `pytest products/tracker17/tests/` from the clone root and `pytest -s tests/e2e/` from the product root | Measurement `trigger=36 sentence=111.5 confirm=36 back=36`; e2e `118 passed`; `tests/` 2628 passed and 1 failed, the failure being `test_every_test_module_names_a_requirement_or_acceptance_criterion` on the measurement module, whose docstring named no requirement (the case CP-618 states) |
| The status-move confirmation measures 28px today and the project strip 36px (CP-613) | `tests/e2e/test_delete_project.py::test_project_strip_uses_full_size_controls` run in the clone at `62123a148` | Passed; it asserts the move confirming button at `ROW_CONTROL_HEIGHT` (`:217`) and the task confirming button at `ROW_CONTROL_HEIGHT` (`:220`) |
| The three QC-62 commands pass on the code today (CP-617) | Ran each from the product root in the change worktree at `62123a148`, with `ruff==0.16.10` and `mypy==2.4.0` from `tests/requirements.txt` | `ruff format --check .` exit 0 (269 files already formatted); `ruff check .` exit 0; `mypy …` exit 0 (no issues in 27 source files) |
| `domain/tasks.py`'s docstring names `tests/e2e/test_delete_task.py` (CP-618) | Read the opening docstring | Line 26 of the docstring names `tests/e2e/test_delete_task.py` |
| `pytest tests/` does not collect `tests/e2e/` (CP-616) | Read `tests/conftest.py:7-9` | "The collection rule keeps `pytest tests/` from collecting `tests/e2e/`" |

No rule pins output that renders a language-level fact: every height here is a value the product's stylesheet chooses, so no rendering row is owed.

---

## Out of Scope

- Delete project's first press and its confirmation: unchanged.
- The wording of any page, where keyboard focus lands, and the order of the strip's parts: unchanged.
- Task deletion itself — what is saved, where it redirects, the failure line's words: unchanged.
- Any other visual property of Delete task's first press beyond its height and its being DESIGN's {components.button-secondary}: not pinned here.
- Status-move buttons and their strips, on a task row, on All tasks or on the task page: not resized.
- Moving a task between projects (SRS FR-14) and changing a project's description (UXD § 10).

---

## Locked Answers (the divergence record — self-review 2026-10-29)

- **Gap 1 — the first press is 28px, not 36px (correcting the request's claim; CP-609):** The request, and the station's reached-when, say the confirming button is "28px against the 36px first press". Measured in the running app, Delete task's first press is 28px today (Verified Claims, row 1). Giving only the strip the full size would make the confirming button 36px against a 28px first press (row 4). That breaks DESIGN's rule that the confirmation takes the height of the button it replaces, and it misses the request's own outcome, "36px (±0.5), equal to the first press". That outcome can't be met unless the first press is 36px too. DESIGN § Components names Delete task's first press a full-size {components.button-secondary}. So the spec makes the first press 36px (CP-609) as well as the strip (CP-610). This is one capability, not two: DESIGN `components.confirm-strip`, the request's acceptance boundary, sizes the strip to the first press's full height, and both measurements belong to that one statement. Both suites pass with the change applied, with no existing test changed beyond CP-615 (row 5), so nothing the request says must not be weakened is weakened.
- **Gap 2 — the code checks in NFDR QC-62 (entry e; CP-617):** The request does not mention them. QC-62 requires every change to pass `ruff format --check .`, `ruff check .` and the stated `mypy` command, so they are stated as a rule.
- **Gap 3 — the test-module docstring rule in NFDR QC-11 (entry e; CP-618):** The request does not mention it. QC-11 requires every test module to name the requirements or acceptance criteria it checks, and the entry module `domain/tasks.py` to name the test modules that check it. A new test module that does neither fails `pytest tests/` (row 5), so the rule is stated.
- **Gap 4 — the forms of the first press (entry b; CP-609):** The request names only `/tasks/<id>`. The page shows the same first press in three forms: ordinary, restored after Back out, and after a failed save. CP-609 covers all three, so the confirmation always replaces a 36px button whatever form it opened from.
- **Gap 5 — "fails on main today" (entry b; CP-614):** The request's reason the test fails on `main` (a 28px button against a 36px first press) is false, per Gap 1. The test still fails there, because both measure 28px against the required 36px. CP-614 states the failure in those terms.
