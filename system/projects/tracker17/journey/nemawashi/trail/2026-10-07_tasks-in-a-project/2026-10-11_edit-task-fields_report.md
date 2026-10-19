# 宿場 Shukuba refine — `2026-10-11_edit-task-fields`

*Unit `2026-10-11_edit-task-fields`, sealed Tobiishi, reviewed 2026-10-12; key named by the caller.
Station `2026-10-11_edit-task-fields` (root). Seed `2026-10-07_tasks-in-a-project`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves rows 2 and 3, the companion items raised |
| 4 | the owner's act | owner | none — is `task-labels` done? Not yet built; its bar has been re-aimed twice (SD-5's saved-label check, then QC-36 and QC-48 in this run) with no owner's-act row on it | 1 | Moves row 1 |
| 5 | cut a seed | Principal PM | none — answered by `nemawashi-refine` after the seed's retire, which writes new product work onto the product's documents for `seeds-from-product-docs` to cut, and cuts work no document should state through `seeds-from-idea` | — | recommendation 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `journey/tobiishi/trail/2026-10-11_edit-task-fields/flow_findings/` — `development-specs.md`, `development-design.md`, `development-plan.md`, `development-content.md`, `development-implementation.md` | 0 blocking. Non-blocking change-local: specs 6, design 1, plan 0 (clean), content 1, implementation 4. One skill-general (implementation: Step 1b counted by test name, not assertion → kaizen `implementation-step1b-count-by-assertion`), not the route's. None names work left without an owner (Considered rows 4, 5) |
| code-integrity report | `.../code-integrity-report.md` (`4436a97ae`) | `Integrity: pass`. No code fix. 34 breaches, 27 caught; 2 tests strengthened, 2 added; 696 passed. Calls: the refused-name echo is optional by design (Architect's), not a test owed (Considered row 6). Nothing surfaced that it could not fix |
| developer's closing commit | `7ada48cae` | Divergences: retained-form fallback and refused-assignee echo beyond the instruction (both from CP-151/CP-166, design § 3 C); one e2e People focus test failed once, then passed three runs (Considered row 2) |
| deferred decisions | absent — no `deferred_decisions.md` in the folder | — |
| the closing commit's `Deferred:` lines | absent — `git log -1 --format=%B 7ada48cae \| grep '^Deferred:'` prints nothing | — |
| corrections owed | `tl_instruction.md` § Corrections owed while there | Three *Owed outside this change's reach* lines: SDD § 3 `application` row (Moves row 2), NFDR QC-21 and ADR-0001 (Moves row 3). Each record still states the unconditional save, measured this run |
| work handed on | `change_spec.md` § Out of Scope | Labels and the saved-label check → `task-labels`, carried (`seed.md:L20`). Rest of UX-S6 → `status-moves` `allowed-moves`, `delete-and-rename` `delete-a-task`, `comment-on-a-task` `comments-on-the-page`, carried. Status, delete, filter, sort, summary → their seeds, carried. Not-found link to All tasks → `narrow-and-sort` `all-tasks-list`, carried (`unpicked/2026-10-11_narrow-and-sort.md:L18`). README § Status and `what_left.md` → `readme-status` (Next moves 2) |

## Upstream

`git log --since=2026-10-07T02:17:39+02:00 --name-status -- products/tracker17/docs/` lists, since the last review (`4ffa77d09`), CONTENT v9 (`64431490b`) and two `what_left.md` updates (`8df0e5156`, `2010c559e`); before it, FDR v4, CONTENT v8, PRD v6, SRS v6, SDD v8 and NFDR v10, each settled. SDD v8 narrowed § 11 R-2 (`SDD.md:L774-L777`), and the seed's prose still read the old R-2 (Moves row 1). `find products/tracker17/docs -name '*_open_issues.md' -not -path '*/trail/*'` printed nothing before this run; `SDD_open_issues.md` and `architecture_open_issues.md` are now live (Moves rows 2, 3).

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: settled`, `pending: null`, so no chain-product is in flight. `system/logs/chain-change-tracker17-state.json` is this refine's own walk (`pending.refine`). `journey/tobiishi/` holds only `trail/`, so no open unit walks a seed or station.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| 1. modify a seed | tracker17 · nemawashi · 2026-10-07_tasks-in-a-project; tracker17 · nemawashi · 2026-10-07_comment-on-a-task; tracker17 · nemawashi · 2026-10-07_status-moves | `task-labels` gains QC-36's typed-text test for a label and QC-48's timing of a label add. A label is free text, labels are an edited field and editing is an NFR-1 action, so the change that adds them owes both. Left off, its design meets the gap that halted `add-and-list-tasks`. Stale prose repaired: the active seed's R-2 sentence follows SDD v8, and `delete-and-rename`, `narrow-and-sort`, `project-summary` are named by the seeds now cut, in all three seeds | `SRS.md:L153-L155` (FR-16), `L189-L191` (FR-23); `nfdr.md:L270-L276` (QC-36), `L396-L398` (QC-48); `fc2f59593`; `SDD.md:L774-L777`; `ls journey/nemawashi/unpicked` → `2026-10-11_delete-and-rename.md … narrow-and-sort.md … project-summary.md`; `grep -rn -i 'not yet cut'` over the live seeds → 5 lines before, 0 after (the new divergence line quotes the phrase) | `1c198c902` |
| 2. raise a companion item | `products/tracker17/docs/SDD_open_issues.md` § 5.1 | SDD § 3's `application` row says every action saves; the sealed edit saves nothing when no field changed. A fact now false | `SDD.md:L201`; `application/tracker.py:L105-L114`; `tl_instruction.md` § Corrections owed, line 1 | `8e04bc951` |
| 3. raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1 | NFDR QC-21 and ADR-0001 say the same; ADR-0001 is append-only, so the item asks the qualification to be recorded beside QC-21 | `nfdr.md:L167-L168`; `adr/0001-rule-core-behind-server-rendered-pages.md:L26-L28`; `adr/README.md:L3-L6`; `tl_instruction.md` § Corrections owed, lines 2–3 | `cc3956f5a` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| 1. tracker17 · shukuba · 2026-10-11_edit-task-fields — the close | Reached-when 1–8 hold now, so the close is owed to the Scrum Master. Reached-when 7's browser suite is green on some runs only; see row 2 | Measured on a `git archive HEAD products/tracker17` copy, `git init`-ed, with the README's `.venv` (`/private/tmp/t17refine.M8A7`): `pytest products/tracker17/tests/` → `696 passed`; `python3 products/tracker17/tests/timed_run.py` → exit 0, `edit a task at 1000 tasks: 35.9 ms`; `pytest products/tracker17/tests/e2e/` × 7 → 4 × `23 passed`, 3 failed runs. Tests: 1 `integration/test_task_pages.py:L278-L291,L386-L420`; 2 `integration/test_task_routes.py:L610`; 3 `L773`; 4 `L728`; 5 `L750`; 6 `L709-L726`; 8 `e2e/test_tasks.py:L117-L140` |
| 2. the browser suite's intermittent failures | Not this station's tests, and already recommended for a seed by the last review; still uncarried, so recommendation 1 repeats it with this run's measurement. A `shukuba-retire` run may land on a red draw | Failing this run: `e2e/test_people.py::test_a_stale_remove_focuses_the_heading_with_the_reason_and_a_reload_link`, plus a 2-failure run. `7ada48cae` body: a `test_first_project.py` focus test failed once. `grep -rn -i 'flak\|intermittent\|every run' journey/nemawashi/unpicked` → nothing |
| 3. tracker17 · nemawashi · 2026-10-07_tasks-in-a-project — `task-labels` under shape 6, as amended | Can be met where it stands. `domain/labels.py`, the label add and remove, the focus test and the SD-5 check are its own work; the timed run exists to extend (QC-48); QC-36's e2e test is its own | `SDD.md:L392-L395` (SD-5), `L461-L464` (TS-5); `nfdr.md:L270-L276`, `L396-L398`; `ls products/tracker17/tests/timed_run.py` exists |
| 4. implementation finding — `web/pages.py` `_edit_form` docstring says nothing is checked while it tests membership | Design sanctions the echo (`change_design.md:81`) and integrity placed it in `web`. The docstring is a found-while-walking repair for the next branch that edits `_edit_form`; a review fixes nothing | `flow_findings/development-implementation.md`, placement bullet; `code-integrity-report.md` § Placement |
| 5. the other change-local flow findings | Each is about this unit's own record (counts, evidence, a missing reason or example row) and ended with it. None names work that now has no owner | the five `flow_findings/*.md` |
| 6. integrity call — is the refused-name echo owed a test? | Optional by the design; the Architect's call, and nothing on the route depends on it | `code-integrity-report.md` § Calls made, 1 |
| 7. tracker17 · nemawashi · 2026-10-07_status-moves — `allowed-moves` adds the move action, `out-of-date-move` times it | Not the next station, and this run amends no station line of that seed; `stations-from-seed` re-cuts its route at the pick (QC-48 has the change that adds an action time it) | `unpicked/2026-10-07_status-moves.md:L17-L19`; `nfdr.md:L396-L398` |
| 8. park, un-pick, drop | Not owed: the station is reached, the seed is not blocked, and a sealed unit is never dropped | `3514edcdc` (the merge) |

## Absent

`deferred_decisions.md` (not produced); `Deferred:` lines (none in `7ada48cae`); halt report (a sealed unit produces none).
