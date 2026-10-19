# 根回し Nemawashi seed — moving a task through its workflow

## What it is

Serves the Way `fit-to-publish`: the Status workflow is a Core Feature a reader traces to its code (`products/tracker17/README.md:L3-L5`). After this, the operator can move a task through its status workflow from any list row or from the task's page, and a move the workflow does not allow is refused with its reason. Completes Key Use Case 3 toward the Agari's **Works** bar, and adds the Status workflow's entry point (`domain/workflow.py`) toward **Simple to read**.

Rests on SDD § 4 EX-5, EX-6 and EX-7. Its bar is SDD § 6 S-4 *Reached when*: exactly the allowed moves offered as buttons; a move to `cancelled` behind the in-place confirmation, with focus where UX-I2 puts it and a double press that never confirms, also on a scrolled list; an out-of-date move refused; a test for every allowed and refused move, SRS AC-12's out-of-date move and AC-13's third case; the end-to-end focus tests; `tests/timed_run.py` covers a move.

**Why it is here.** It is the first use of the in-place confirmation, which is the interaction most exposed to pages that run no script (§ 9 TO-2, ADR-0003). A failure found here costs the pages of one action, and `delete-and-rename` reuses what is built (SDD § 7, `hands_off_to`).

## Source

Cut from `products/tracker17/docs/SDD.md` § 6 S-4, slug `status-moves` ("After this, the operator can move a task through its status workflow from any list row or from the task's page"). Product re-checked on 2026-10-12, after `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project` was walked: `domain/workflow.py` does not exist (`ls products/tracker17/domain` lists `__init__.py assignees.py due_dates.py labels.py priorities.py projects.py refusals.py state.py tasks.py text.py`). The work is still owed.

## Stations — dynamic checklist

- [ ] allowed-moves — the workflow rule and the move buttons on rows and the task page, with a test for every allowed and refused move
- [ ] cancel-confirmation — the in-place confirmation for `cancelled`, with the focus and double-press end-to-end tests
- [ ] out-of-date-move — the stale-page refusal, the no-longer-overdue rule for finished tasks, and the timed run covering a move

2026-10-12, shukuba-refine after `tracker17` unit `edit-task-fields`: § Relation and § Out name `narrow-and-sort` and `delete-and-rename` by their seeds in `unpicked/`, which are now cut.

## Relation to existing work

Rests on `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`. It also tests `tracker17 · nemawashi · 2026-10-07_first-project`: its confirmation tests show whether pages with no script can carry UX-I2 (SDD § 7, `validates`). `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` rests on it, and `tracker17 · nemawashi · 2026-10-11_delete-and-rename` reuses its confirmation.

## Out (later / elsewhere)

The confirmations on deleting a task and a project (`tracker17 · nemawashi · 2026-10-11_delete-and-rename`). A moved task leaving a list filtered by status (`tracker17 · nemawashi · 2026-10-11_narrow-and-sort`).
