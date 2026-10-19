# 宿場 Shukuba refine — `2026-10-12_task-labels`

*Unit `2026-10-12_task-labels`, sealed Tobiishi, reviewed 2026-10-12; key named by the caller.
Station `2026-10-12_task-labels` (root). Seed `2026-10-07_tasks-in-a-project`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves row 2, the companion item raised |
| 4 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 1 | recommendation 1 |
| 5 | cut a seed | Principal PM | none — answered by `nemawashi-refine` after the seed's retire, which writes new product work onto the product's documents for `seeds-from-product-docs` to cut, and cuts work no document should state through `seeds-from-idea` | 4 | recommendation 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `journey/tobiishi/trail/2026-10-12_task-labels/flow_findings/` — `development-specs.md`, `development-design.md`, `development-plan.md`, `development-content.md`, `development-implementation.md` | 0 blocking. Non-blocking change-local findings: specs 4, design 2, plan 2, content 3, implementation 2. One skill-general finding (implementation: the closing block covers the last task only → kaizen `implementation-closing-block-covers-last-task-only`) is about the machinery, not the route. The content step's open standard gap became Moves row 2. The specs step's unrun start exit is answered by Considered row 1's measurement. No other finding names work without an owner |
| code-integrity report | `.../code-integrity-report.md` (`1e246a1c8`) | `Integrity: pass`. 1 test fixed, 2 added, 14 long docstring lines reflowed, 813 passed. Calls: five more existing tests changed for CP-182/CP-201/CP-200; no `__version__` marker for product modules (the NFDR's call). Surfaced nothing it could not fix |
| developer's closing commit | `85549516b` | Divergences: an existing timed-run test's ticks extended for the label reads; each label total reported on its own line; carried from tasks 1–4, the `conventions.md:L148` and `testing_python.md:L54` divergences |
| deferred decisions | absent — no `deferred_decisions.md` in the folder | — |
| the closing commit's `Deferred:` lines | absent — `git log -1 --format=%B 85549516b \| grep '^Deferred:'` prints nothing | — |
| corrections owed | absent — `tl_instruction.md` has no § Corrections owed while there (its `##` headings are `Project layout` and `TL Review Notes`) | — |
| work handed on | `change_spec.md` § Out of Scope (`L167-L176`) | Label filter → `narrow-and-sort`, carried (`unpicked/2026-10-11_narrow-and-sort.md:L5`). Status, delete, summary, sort, comments → their seeds, carried (`seed.md` § Out). Unreadable-data pages, FDR R-25/R-26 (Gap 17, handed to this refine) → `protect-saved-data` `unreadable-data-page`, carried (Considered row 3). The other lines only fence |

## Upstream

`git log --since=2026-10-07T02:17:39+02:00 --name-status -- products/tracker17/docs/` (seed first committed `5d9a6ce09`): the newest change is NFDR v11 (`df8ac27ea`, 2026-10-12T01:43), followed by SDD v9 (`33ad1a2a7`). Both folded the companions the last review raised. This unit was specified against them (`change_spec.md` Gap 2 cites QC-21 and RN-45). Nothing moved under `docs/` after the unit opened. Live `*_open_issues.md` before this run: none (`ls products/tracker17/docs/*open_issues*` matched nothing). After it: `CONTENT_open_issues.md` (Moves row 2).

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: settled` and `pending: null`, so no product chain is in flight. `chain-change-tracker17-state.json` has `pending.refine` for this key, which is this run. No change unit is open: `ls journey/tobiishi` lists only `trail`.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a station | tracker17 · shukuba · 2026-10-12_task-labels | Reached-when 4 asked the over-long refusal to keep the typed text. The settled FDR forbids that, so the bar could not be met where it stood (shape 6). It now asks for the reason without the text, and the empty refusal still keeps the text | `products/tracker17/docs/fdr.md:L388-L389` (PD-11); `change_spec.md` Locked Answers Gap 1 (`L182`); `tests/integration/test_label_routes.py:L190-L203` | `eab9df679` |
| raise a companion item | `products/tracker17/docs/CONTENT.md` → `CONTENT_open_issues.md` § 3.1 | Two settled rules in CONTENT.md disagree at a string the product ships. The refusal formula asks for one action; Voice asks for none where none exists | `CONTENT.md:L53`, `L207-L209`; `products/tracker17/web/pages.py:L718-L721`; `change_text.md:L270-L274` | `ce716063d` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| tracker17 · shukuba · 2026-10-12_task-labels | Reached under the amended bar, so its close is owed to the Scrum Master. 1: `domain/labels.py` exists. 2–4: the label pages, routes and refusals are tested through the real site. 5: the saved-label breaks are refused at start. 6–7: the e2e focus and typed-text tests. 8: all gates pass | `ls products/tracker17/domain/labels.py`; `tests/integration/test_label_pages.py:L77-L131`, `test_label_routes.py:L95-L152`, `test_start.py:L399`, `test_saved_data.py:L861`, `tests/e2e/test_labels.py:L50,L149`. On a `git archive 1aaa622e9 products/tracker17` copy, `git init`-ed, with the pinned venv: `pytest products/tracker17/tests/` gave `813 passed`, `pytest products/tracker17/tests/e2e/` gave `27 passed`, and `python3 tests/timed_run.py` exited 0 with `add a label at 1000 tasks: 31.2 ms` |
| tracker17 · nemawashi · 2026-10-07_tasks-in-a-project | Its last line, `task-labels`, is the station whose close is owed. After the close the seed is fully walked, and the retire is recommended (recommendation 1). Its line asks nothing about typed text, so the station's re-aim leaves it true | `seed.md` § Stations — dynamic checklist |
| tracker17 · nemawashi · 2026-10-11_protect-saved-data | Already carries Gap 17. FDR R-25/R-26 describe the unreadable-data page, and its `unreadable-data-page` station builds that page, with one test for each DR-6 break (label breaks included). Its prose already cites the start refusal as today's behaviour | `unpicked/2026-10-11_protect-saved-data.md:L7,L9,L19`; `fdr.md:L112-L116`; `main.py:L41-L48` |
| `CONTENT.md` — two labels on one task that read alike to an assistive technology | Not raised. The form does not occur: no saved task holds two labels that differ only in spaces, or one made only of spaces. CP-188 permits it, but a permitted form is not an occurrence | probe of `products/tracker17/data/tracker.json` for label lists whose stripped values repeat or are blank printed nothing beyond `checked data/tracker.json` |
| tracker17 · nemawashi · 2026-10-07_tasks-in-a-project — the station's re-aim count | No owner's-act row. Since the last report that asked the owner (`2026-10-11_edit-task-fields_report.md` Next moves row 4), `task-labels` has one re-aim, this run's. And once the close lands, no station is left on the seed | Moves row 1 |
| browser suite on `main` | Still fails on some runs, so the seed cut the last two reviews asked for is recommended again (recommendation 2) | 7 more runs of `pytest -q products/tracker17/tests/e2e/` on the same copy: 6 × `27 passed`, 1 × `1 failed, 26 passed` (`test_first_project.py::test_a_hand_built_201_character_name_gets_the_reason_and_none_of_the_text`); `ls journey/nemawashi/unpicked` holds no seed for it |

## Absent

`deferred_decisions.md` (not written by this unit); `Deferred:` lines (none in `85549516b`); `tl_instruction.md` § Corrections owed while there (not in the plan); halt report (a sealed unit produces none).
