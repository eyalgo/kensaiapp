# 宿場 Shukuba refine — `2026-10-11_people-page-assignee-list`

*Unit `2026-10-11_people-page-assignee-list`, sealed Tobiishi, reviewed 2026-10-11. Key named by the caller.
Station `2026-10-11_people-and-assignees` (root). Seed `2026-10-07_tasks-in-a-project`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves rows 3, 4 |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17` | — | Considered row 1 |
| 3 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 2 | Considered row 1 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1, 2 | Considered row 2 |

Row 4 waits on row 1 because `add-and-list-tasks` rests on `SDD.md`, which the sweep folds.

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `…/tobiishi/trail/2026-10-11_people-page-assignee-list/flow_findings/development-specs.md` | 0 blocking; 3 change-local (altitude ×2, CP-98 examples coverage) |
| flow findings | `…/flow_findings/development-design.md` | 0 blocking; 1 change-local (failed-add focus target not recorded) |
| flow findings | `…/flow_findings/development-plan.md` | 0 blocking; 2 change-local (empty-list failed add unnamed; static checks only at Task 5) |
| flow findings | `…/flow_findings/development-content.md` | 0 blocking; 2 change-local (header block wider than design line; focus notes restated) |
| flow findings | `…/flow_findings/development-implementation.md` | 0 blocking; 3 change-local (renamed/split test names uncounted; `__version__` line cites wrong site; toolchain line) |
| code-integrity report | `…/code-integrity-report.md` | `Integrity: pass`; 5 tests added; surfaced the `__version__` question as the Principal Architect's (Considered row 3) |
| developer's closing commit | `1edaef66c` | divergences recorded (blank check repeated, `_save_then_publish`, `test_shapes.py` names four modules, `__version__`); one e2e failure once in task 3, not recurred (Considered row 4) |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | — |
| the closing commit's `Deferred:` lines | absent — `git log -1 --format=%B 1edaef66c \| grep -n "Deferred\|Failing"` prints nothing, exit 1 | — |
| corrections owed | `…/tl_instruction.md:L124-L142` | ADR-0003 Dependence → Moves row 4; SDD § 11 R-2 and § Open Questions → Moves row 3; CP-104 (`change_spec.md`, a trail record, not edited) and station reached-when 6 → Moves row 1 |
| work handed on | `…/change_spec.md:L125-L134` | task use of the list → `add-and-list-tasks`, `edit-task-fields` (seed lines 18–19); Your name, comments → `comment-on-a-task`; R-84 → `narrow-and-sort`; R-97/R-98 → `project-summary`; README/what-left → `readme-status` (Next moves row 3); SDD Open Question → Moves row 3; not-found body, unreadable-data page, timed-run actions only fence |

## Upstream

`git log --since=2026-10-07T02:17:39+02:00 --name-status -- products/tracker17/docs/` (seed first committed `5d9a6ce09`): PRD v5 (`29352d2fc`, critical priority) and v6 (`cafd1cb92`, second purpose); SRS v5 (`083aa6d92`) and v6 (`b72ea80e6`); CONTENT v8 (`8d2050237`); FDR v3–v4 (`1d67fd17d`, `2c82d3efd`); NFDR v7–v9 (`332311003` … `24aa9ecd8`); the machine-path scrub (`878d25dac`). None changes a line of this seed: it names no priority set (`seed.md:L5-L21`), and the four values already stand in the unpicked seeds that sort or count by priority (`2026-10-11_narrow-and-sort.md:L7`, `2026-10-11_project-summary.md:L7`). Live `*_open_issues.md` before this run: none (`find products/tracker17/docs -name '*_open_issues.md' -not -path '*/trail/*'` printed nothing). After it: `SDD_open_issues.md`, `architecture_open_issues.md` (Moves rows 3, 4).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null` — no chain in flight. `journey/tobiishi/` root holds no open unit (only `trail/`). `chain-change-tracker17-state.json` is pending only on this refine step.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a station | `tracker17 · shukuba · 2026-10-11_people-and-assignees`, reached-when 6 | It asked one `pytest products/tracker17/tests/` run to collect the e2e layer; the collection rule keeps e2e out, so it could not be met as written. It now names the two runs (shape 6; the plan's fourth correction owed). | `products/tracker17/tests/conftest.py:L7-L9`; `…/tl_instruction.md:L138-L142` | `641bb58b5` |
| modify a seed | `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`, lines 18–19 | SRS AC-19 is a stale plain field edit; no field edit exists until `edit-task-fields`, so `add-and-list-tasks` could not meet it where it stood (shape 6). Moved to `edit-task-fields`; divergence line added. | `products/tracker17/docs/SRS.md:L532-L534`; `SDD.md` § 6 S-2 *Command* | `641bb58b5` |
| raise a companion item | `products/tracker17/docs/SDD_open_issues.md` § 5.1 | § 11 R-2 and § Open Questions call the not-a-control focus case wholly unverified; a Chromium test of it now passes. | `SDD.md:L1154-L1164`, `L1769-L1774`; `tests/e2e/test_people.py:L58-L78`; `pytest products/tracker17/tests/e2e/` → `18 passed` | `069e11197` |
| raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1 | ADR-0003's Dependence says the same and is owed the same narrowing. | `adr/0003-no-script-in-any-page.md:L45-L50`; same test and run | `fae779439` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-11_people-and-assignees` | Reached: close owed to the Scrum Master. 1 — `ls products/tracker17/domain/assignees.py` finds it. 2–5 — covered by the integration and e2e tests the integrity pass checked against CP-80 to CP-105. 6 — on a `git archive HEAD` copy: `pytest products/tracker17/tests/` → `355 passed`, 1 failed (`test_data_is_ignored_by_version_control`, which needs a git repo; passes once the copy is `git init`-ed); `pytest products/tracker17/tests/e2e/` → `18 passed`; `timed_run.py` exit 0. Re-aimed once (this run), so no owner's act. | `code-integrity-report.md` § The finding; the commands above, this run |
| `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`, `add-and-list-tasks` (next station) | Can be met where it stands after Moves row 2: the assignee list exists now; the add form, task page, due-date list and `domain/tasks.py`, `priorities.py`, `due_dates.py` are its own work; AC-13's first two cases need only the list marking it builds. | `SRS.md:L509-L512` (AC-13); `SDD.md` § 6 S-2 *Reached when* |
| `products/tracker17/docs/nfdr.md` (the `__version__` question) | Not raised: the product states no version-marker rule and no module carries one, so nothing in the product breaks a rule it states; the integrity pass took reading (b) and named the Principal Architect's seat if it is ever to change. No occurrence of a failure. | `code-integrity-report.md` § Calls made; `languages/python/conventions.md:L135-L141` |
| an e2e flake, `test_a_hand_built_201_character_name_gets_the_reason_and_none_of_the_text` | Failed once in task 3 and has not recurred (18 passed in task 5 ×3, the closing run, the integrity run, and this run). No carrier on one unrepeated failure. | `1edaef66c` Developer Review Notes; `pytest products/tracker17/tests/e2e/` → `18 passed`, this run |
| the 11 non-blocking change-local flow findings | Each is about this unit's own artifacts and ends with it; none names unowned work. | `flow_findings/*.md` above |
| unpicked seeds `comment-on-a-task`, `status-moves`, `narrow-and-sort`, `project-summary`, `delete-and-rename`, `protect-saved-data`; `shukuba/parked/` | Nothing the unit left or upstream moved changes them; the priority set is already current where they name it; `parked/` is empty. | `grep -rn -e pytest -e "both suites" journey/nemawashi/unpicked`; `ls journey/shukuba/parked` → `.gitkeep` |

## Absent

`deferred_decisions.md` (not written by the unit). `Deferred:` lines in the closing commit (none). Halt report (a sealed unit produces none).
