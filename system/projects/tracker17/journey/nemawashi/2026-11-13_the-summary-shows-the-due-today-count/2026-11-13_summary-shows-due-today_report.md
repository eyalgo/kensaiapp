# 宿場 Shukuba refine — `2026-11-13_summary-shows-due-today`

*Unit `2026-11-13_summary-shows-due-today`, sealed Tobiishi, reviewed 2026-11-13. Key named by the caller.
Station `2026-11-13_summary-shows-due-today` (root). Seed `2026-11-13_the-summary-shows-the-due-today-count`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-11-13_summary-shows-due-today` | — | Considered row 1 |
| 2 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 1 | recommendation 1 |
| 3 | drop a seed | Principal PM | none — decided by `nemawashi-refine` after the seed's retire, which runs the drop itself | 2 | recommendation 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-11-13_summary-shows-due-today`, `flow_findings/development-specs.md` | 0 blocking, 4 change-local (a third page-row consumer, `test_delete_routes.py`, unlisted; no base run of the gates; one-date claim read, not run; mechanism in rules), 0 skill-general |
| flow findings | the same, `flow_findings/development-design.md` | 0 blocking, 1 change-local: CP-817 docstrings named for three of the changed test modules only |
| flow findings | the same, `flow_findings/development-plan.md` | 0 blocking, 2 change-local: CP-817 module count, and the trace test's module missing from Task 1's header |
| flow findings | the same, `flow_findings/development-content.md` | 0 blocking, 1 change-local: the plan's fragment-plus-date shape against the text's one string `Due on {date}` |
| flow findings | the same, `flow_findings/development-implementation.md` | 0 blocking, 3 change-local: the 100-column proof could not fail; `Instruction cases not delivered: 0` hides the unwritten `test_summary_trace_names_ac13`; Task 2 notes no per-rule mutation. Skill-general: none |
| code-integrity report | the same, `code-integrity-report.md` | `Integrity: pass`; one test tightened to pin the row's place, docstrings reflowed, no product code changed. Calls made: the timed-run tests read the real clock (Considered row 4); no separate AC-13 trace test (Considered row 3) |
| security report | the same, `security-report.md` | `Security: reported`, no hole, every scanner ran. § Left for the PM: the dependency audit did not run, the NFDR names none — QC-40 already says so, no companion owed (Considered row 2) |
| developer's closing commit | `<a commit not in the public history>` | Divergences: the AC-13 trace test folded into the existing set test; the midnight timed-run test and `test_delete_routes.py` edited, neither named by the instruction |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | — |
| the closing commit's `Deferred:` lines | absent — `git show -s --format=%B <a commit not in the public history> \| grep '^Deferred:'` prints nothing | — |
| corrections owed | `tl_instruction.md` § Corrections owed while there | One *Owed outside this change's reach* line: `docs/what_left.md`'s entry for the count. Already done in the unit — `6ce827a34` empties it, and the file reads "Nothing is left to build."; no companion owed |
| work handed on | `change_spec.md` § Out of Scope | Five lines, all fences (no list marker or filter, no Overdue change, no link, no saved-data change, no document edit); nothing handed on |

## Upstream

`git log --since=2026-11-13T16:25:36+01:00 --name-status -- products/tracker17/docs/` (seed first committed then): `243f1f6f6` FDR version 8 settled with the count at R-129 to R-131 (already read by the seed, divergence of the earlier refine); `e1c521d02` NFDR version 32 settled, QC-64's pointer names `testing_python.md` § Rules, its companion removed — binds no due-today entry (its own version line, RN-83); `6ce827a34` `what_left.md` emptied by this unit. Live `*_open_issues.md` under `products/tracker17/docs/`: none (`ls` matches nothing).

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: settled`, `pending: null` — no product-docs chain in flight. `journey/tobiishi/` holds only `trail/`, so no unit is open. The walk state's pending `refine` step is this run.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a seed | `tracker17 · nemawashi · 2026-11-13_the-content-carries-the-due-today-count` | § Out said the build seed waits for this one; the count is built | `products/tracker17/docs/what_left.md` ("Nothing is left to build."); merge `e4209621a` | `7c742ad63` |
| modify a seed | `tracker17 · nemawashi · 2026-11-13_the-srs-carries-the-due-today-count` | Same stale wait, in § Out | the same | `7c742ad63` |
| modify a seed | `tracker17 · nemawashi · 2026-11-13_the-uxd-carries-the-due-today-count` | Same stale wait, in § Out | the same | `7c742ad63` |
| modify a seed | `tracker17 · nemawashi · 2026-11-13_the-sdd-carries-the-due-today-count` | Same stale wait, in § Out | the same | `7c742ad63` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-11-13_summary-shows-due-today` | Reached-when 1–5 hold on `main`; the close is the Scrum Master's, owed | In a clone at `e4209621a`: `tests/` `3383 passed, 2 skipped`; `tests/e2e/` `122 passed`; `python3 tests/timed_run.py` exit 0. The grep prints `domain/summary.py:86` (field), `:113` (count), `web/pages.py:1828` (use). The row sits after "Overdue" in "Due dates", pinned by `test_summary_of_a_built_project_counts_due_on_the_date_and_excludes_the_rest` (`code-integrity-report.md` § Tests added or fixed). The tests failed first in red commits `17e5a7b92` and `32bfdb0ee` |
| `products/tracker17/docs/nfdr.md` QC-40 | The security line asks the NFDR to state that no dependency audit exists, and QC-40 already says so | `security-report.md` § Left for the PM; `products/tracker17/docs/nfdr.md` L511-L512 ("no audit command exists for this product") |
| AC-13 in the trace set | Change-local. Removing `AC-13` from `SUMMARY_REQUIREMENTS` would leave the suite green (implementation finding). That is a weaker trace pin, not product behaviour, and no product document is wrong; it ends with the unit | `flow_findings/development-implementation.md`, second item; `code-integrity-report.md` § Calls made |
| `tests/integration/test_timed_run.py` real-clock reads | No occurrence: a failure across local midnight is possible, but none is measured, and the doctrine forbids the real clock at layer 1 only. The parked station's bar covers `def now(` stand-ins, not this | `code-integrity-report.md` § Calls made, first item |
| `tracker17 · shukuba · 2026-11-13_clock-fake-and-suite` (parked) | Its ground did not move. Its bar 3's "before" count is dated, and still measures 25 lines in 24 files | `grep -rEn --include='*.py' '^\s+def now\(' tests \| wc -l` → `25`; `-l … \| wc -l` → `24`, from `products/tracker17` |
| `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` | Independent of the count; nothing the unit left or upstream moved touches it | the seed's § Relation to existing work; NFDR version 32 changes QC-64's pointer only |
| `tracker17 · nemawashi · 2026-11-13_the-summary-shows-the-due-today-count` | Its one station is reached, so it is fully walked once the close lands. Retire recommended, not made | Considered row 1 |
| The four fold seeds' § What it is greps | Cut-state records; each seed's earlier divergence line already says so | each fold seed's divergence line of the earlier refine |

## Absent

`deferred_decisions.md` (not written by the unit); `Deferred:` lines in the closing commit (none); live companions under `products/tracker17/docs/` (none).
