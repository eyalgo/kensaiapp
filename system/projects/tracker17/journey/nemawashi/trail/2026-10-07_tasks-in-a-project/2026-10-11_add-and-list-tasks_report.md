# 宿場 Shukuba refine — `2026-10-11_add-and-list-tasks`

*Unit `2026-10-11_add-and-list-tasks`, sealed Tobiishi, reviewed 2026-10-11; key named by the caller. It replaces the earlier review of the same unit while it was halted (`00bd3edae`).
Station `2026-10-11_add-and-list-tasks` (root). Seed `2026-10-07_tasks-in-a-project`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves row 3, the companion item raised |
| 4 | the owner's act | owner | none — is `edit-task-fields` done? Not yet built; its bar has been re-aimed three times (AC-19 moved on, field-edit timing, the project as text) with no owner's-act row on it | 1, 3 | Moves row 1 |
| 5 | cut a seed | Principal PM | none — answered by `nemawashi-refine` after the seed's retire, which writes new product work onto the product's documents for `seeds-from-product-docs` to cut, and cuts work no document should state through `seeds-from-idea` | — | recommendation 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `journey/tobiishi/trail/2026-10-11_add-and-list-tasks/flow_findings/` — `development-specs.md`, `development-design.md`, `development-plan.md`, `development-content.md`, `development-implementation.md` | 0 blocking. Change-local, non-blocking: specs 5, design 0 (clean), plan 2, content 1 (the due-date refusal's "Pick one" against `CONTENT.md`'s date rule; Moves row 3), implementation 5. One of the implementation five is the browser suite passing only on some runs (Considered row 2). No skill-general finding |
| code-integrity report | `.../code-integrity-report.md` (`bc581b963`) | `Integrity: pass`. One CP-118 test added. 35 of 37 mutations caught, 1 now covered, 1 cannot be told apart. Calls 1 (`__version__`) and 2 (`maxlength` in UTF-16) are not this route's (Considered rows 5, 6) |
| developer's closing commit | `fa243757d` | Divergence notes: the browser suite failed 3 of 6 runs on a copy of `main` and of the branch, in `test_people.py` / `test_first_project.py` focus cases, with the cause not found (body L57-L58, L61) |
| deferred decisions | absent — no `deferred_decisions.md` in the folder | — |
| the closing commit's `Deferred:` lines | absent — `git show -s --format=%B fa243757d \| grep '^Deferred:'` exits 1 | — |
| corrections owed | `tl_instruction.md:L115-L121` | One *Owed outside this change's reach* line: the station's Guardrail excluding the 1,000-task timed run (`timed-run`). Already true: the halted review's `1801e4666` rewrote it, and the station names no `timed-run` today (Considered row 4) |
| work handed on | `change_spec.md:L159-L166` | Edit form, RT-7, AC-19 → `edit-task-fields`, already carried. Labels → `task-labels`, carried; its saved-label start check was not (Moves row 1). Status, delete, filter, sort, summary → their seeds, carried. Comments → `comment-on-a-task`, carried; its saved-comment start check was not (Moves row 1). UX-S6's "the task's project" → nobody (Moves row 1). Project page title → the Tasks and Summary links (Moves row 2). README § Status and `what_left.md` → `readme-status` at the close (Next moves 2) |

## Upstream

`git log --since=2026-10-07T02:17:39+02:00 --format='%h %s' -- products/tracker17/docs/` lists FDR v4 (`2c82d3efd`), CONTENT v8 (`8d2050237`), PRD v6 (`cafd1cb92`), SRS v6 (`b72ea80e6`), SDD v8 (`c2e7d0e7e`) and NFDR v10 (`ceac03d4b`), each settled. Nothing has changed under `docs/` since the halted review (`00bd3edae`). `find products/tracker17/docs -name '*_open_issues.md'` printed nothing before this run. `CONTENT_open_issues.md` is now live (Moves row 3).

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: settled`, `pending: null`. `chain-change-tracker17-state.json` is in flight on this unit's `refine` step, which is this run. No unit is open at `journey/tobiishi/`'s root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a seed | tracker17 · nemawashi · 2026-10-07_tasks-in-a-project (items 3, 4, Source) and tracker17 · nemawashi · 2026-10-07_comment-on-a-task (`comments-on-the-page`) | The spec handed on two pieces of work that no station line carried. First, UX-S6's "the task's project as text" was handed to nobody; it goes on `edit-task-fields`, which builds the task page's form. Second, the start checks for saved labels and comments go on the stations that add those rules. Re-aims of `edit-task-fields`: AC-19 moved on (seed note, `9b38dca46`), field-edit timing added (`1801e4666`), and the project as text added here (`654ecd089`). The seed's Source line now records what the product holds today | `products/tracker17/docs/UXD.md:L312`; `products/tracker17/web/pages.py:L470-L493` shows no project; `products/tracker17/docs/SDD.md:L392-L395`; `change_spec.md:L161-L164` | `654ecd089` |
| modify a seed | tracker17 · nemawashi · 2026-10-11_project-summary (`summary-page`) | The spec handed the project page's title to the Tasks and Summary links. `CONTENT.md`'s title rule names the view, and today the title is the bare project name. Its own commit, made after the first | `change_spec.md:L165`; `products/tracker17/docs/CONTENT.md:L354-L357`; `products/tracker17/web/pages.py:L467` | `7977f9e65` |
| raise a companion item | `products/tracker17/docs/CONTENT.md` → `CONTENT_open_issues.md` § 3.1 | `CONTENT.md`'s date rule bars telling the reader "how to type or pick a date". The shipped due-date refusal says "Pick one". The rule does not say whether that is barred. This is the content audit's finding, and the decision belongs to the document's own seat | `products/tracker17/docs/CONTENT.md:L129-L130`; `products/tracker17/web/pages.py:L276`; `flow_findings/development-content.md` | `c113d5c0b` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| 1. tracker17 · shukuba · 2026-10-11_add-and-list-tasks — the close | Reached-when 1–8 hold now, so the close is owed to the Scrum Master. The seal names only 1 to 7 (`f41327c46`), but 8 holds too. The browser suite is green on 6 of 9 runs; see row 2 | Measured on a `git archive HEAD products/tracker17` copy, `git init`-ed, with the README's `.venv`. `ls domain/{tasks,priorities,due_dates}.py` finds all three. `pytest products/tracker17/tests/` → `574 passed`. `python3 products/tracker17/tests/timed_run.py` → exit 0, `add a task at 1000 tasks: 28.7 ms`. `pytest products/tracker17/tests/e2e/` × 9 → 6 × `21 passed`, 3 failed runs, all in People and first-project tests. Reached-when 8 is `tests/e2e/test_tasks.py:L83-L86` |
| 2. the browser suite's intermittent failures | Not carried by this station, because the failures are not its tests and also fail on a copy of `main` without this change. No seed carries them, and they are work rather than a document gap, so recommendation 1 asks for a seed. A run of `shukuba-retire` may land on a red draw | Failing tests this run: `test_people.py::test_people_keyboard_refusals_and_removal_keep_focus_at_the_action`, `test_first_project.py::test_a_refused_name_puts_focus_in_the_name_field_with_the_reason_as_its_description`, plus one 2-failure run. `fa243757d` body L57. `grep -rn -i -E "flak\|intermittent"` over the seeds → nothing |
| 3. tracker17 · nemawashi · 2026-10-07_tasks-in-a-project — `edit-task-fields` under shape 6 | Can be met where it stands. RT-7 needs the People list (`domain/assignees.py`, which exists) and the edit form (its own work). AC-19 is a field edit (its own work). The timed run exists to extend. UX-S6's project is a field the task already holds | `products/tracker17/docs/SRS.md:L532-L534`; `products/tracker17/docs/SDD.md:L461-L464`; `ls products/tracker17/domain` → `assignees.py … tasks.py` |
| 4. the plan's *Owed outside this change's reach* line | Already true. The station's Guardrail no longer excludes the timed run or names `timed-run`, and reached-when 7 carries it | `tl_instruction.md:L117-L121`; `journey/shukuba/2026-10-11_add-and-list-tasks.md` § Guardrail; `1801e4666` |
| 5. integrity Call 1 — `__version__` on product modules | Belongs to the Python packet's owner, not this project's route | `code-integrity-report.md` § Calls made, 1 |
| 6. integrity Call 2 — `maxlength` counts UTF-16 units against ADR-0007's code points | Settled in the unit as a maximum the field meets. Reversing it needs a script, which CP-110 rules out. No document gap measured | `code-integrity-report.md` § Calls made, 2 |
| 7. the other change-local flow findings | Each is about this unit's own record, such as evidence, counts or test shape, and ended with it. None names work that now has no owner | the five `flow_findings/*.md` |
| 8. tracker17 · nemawashi · 2026-10-07_tasks-in-a-project, item 4 `task-labels`, timing | Unchanged since the halted review. I have no basis for saying whether NFR-1's "editing" covers adding a label | `products/tracker17/docs/SRS.md:L307-L310` |
| 9. drop the unit | Never owed: the unit is sealed | `f41327c46` |

## Absent

`deferred_decisions.md` (not produced); `Deferred:` lines (none in `fa243757d`); halt report (a sealed unit produces none).
