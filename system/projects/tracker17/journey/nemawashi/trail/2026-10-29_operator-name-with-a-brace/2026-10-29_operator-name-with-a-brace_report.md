# 宿場 Shukuba refine — `2026-10-29_operator-name-with-a-brace`

*Unit `2026-10-29_operator-name-with-a-brace`, sealed Tobiishi, reviewed 2026-10-29.
Station `operator-name-with-a-brace` (root). Seed `2026-10-29_operator-name-with-a-brace`. Key named by the caller.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-29_operator-name-with-a-brace` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 1 | recommendation 1 |
| 4 | cut a seed | Principal PM | none — answered by `nemawashi-refine` after the seed's retire, which writes new product work onto the product's documents for `seeds-from-product-docs` to cut, and cuts work no document should state through `seeds-from-idea` | 3 | recommendation 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking; 2 change-local (CP-629/CP-630 tension unrecorded; CP-630 hands down a design decision) — both ended with the unit |
| flow findings | `flow_findings/development-design.md` | clean |
| flow findings | `flow_findings/development-plan.md` | 0 blocking; 2 change-local: the baseline's `12 failed` in `test_start.py` (SIGINT ignored without a terminal) contradicts the spec's green claim with no instruction; Task 2 reruns Task 1's suites — measured again in this run, Considered row 3 |
| flow findings | `flow_findings/development-content.md` | 0 blocking; 1 change-local: a saved name `{value}` reads like the slot CONTENT.md bans — Considered row 4 |
| flow findings | `flow_findings/development-implementation.md` | clean |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`; old code fails 20 of 20 regression cases, guards pass; one docstring reflow to the 100-column rule; `2651 passed` + e2e `121 passed`; nothing left unfixed |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM (line 13): dependency audit did not run, the NFDR names none — no companion owed, Considered row 2 |
| developer's closing commit | `<a commit not in the public history>` | divergences: two parameters added to the page-test rows; the 200-code-point name's exact string chosen; Task 2 an empty commit — none passes outside the instruction |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | — |
| the closing commit's `Deferred:` lines | absent — `<a commit not in the public history>` has no line beginning `Deferred:` | — |
| corrections owed | absent — `tl_instruction.md` has no § Corrections owed while there | — |
| work handed on | `change_spec.md` § Out of Scope (line 139) | "every other page's text building … left to a later seed" — the spec's own read found no site; re-measured, Considered row 5. Every other line fences only |

## Upstream

`git log --diff-filter=A --follow --format=%cI` on the seed → `2026-10-29T01:15:06+01:00`;
`git log --since=2026-10-29T00:00 --name-status -- products/tracker17/docs/` → nothing. No live
`*_open_issues.md` under `products/tracker17/docs/` (`find … -name '*_open_issues.md' -not -path '*/trail/*'` → nothing).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null` — no chain in
flight. `system/logs/chain-change-tracker17-state.json`: `key` is this unit, `pending: refine` — this
run. No other unit at `journey/tobiishi/`'s root.

## Moves

None — no move was owed; see below. (The seed became a folder to hold these two files, which is mechanics, not a route move.)

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-29_operator-name-with-a-brace` | All five reached-when lines hold now, so the close is owed to the Scrum Master. Lines 1–3: the matrix tests for `{x}`, `}`, `{0}` and seven more on saved and failed, plus both refusal guards with `{x}` saved, exist and pass. Line 4: old code fails 20 of 20. Line 5: the full suite passes in a disposable clone at the merge. | `tracker17 · shukuba · 2026-10-29_operator-name-with-a-brace` (lines 11–15); `products/tracker17/tests/integration/test_people_routes.py:521,544,572,591`; `code-integrity-report.md` § Tests added or fixed (`20 failed, 2 passed` on old code); clone at `fe98ceeb3`, `pytest products/tracker17/tests/` → `12 failed, 2639 passed` run as a background job, the 12 all `test_start.py` timeouts; `pytest products/tracker17/tests/integration/test_start.py` in the foreground → `57 passed` |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already says no audit command exists and verifies QC-40 by review, as earlier refines here found. No companion item owed. | `security-report.md` (line 13); `products/tracker17/docs/nfdr.md:354`, `:664` |
| the full suite's `test_start.py`, 12 tests | Measured failure the route does not carry: started as a background job, so SIGINT is ignored, the started tracker never stops, and each test times out at 30 s. The same tests pass in the foreground. Raised in plan findings and plan notes in several units, routed by no refine. Code work → recommendation 2, not a station line on this seed. | `products/tracker17/tests/integration/test_start.py:529` (`child.send_signal(signal.SIGINT)`); `grep -n 'signal' products/tracker17/main.py` → nothing; one case backgrounded → `1 failed in 30.23s`, foreground → `3 passed in 0.31s`; `tl_instruction.md` (line 71) |
| `products/tracker17/docs/CONTENT.md` § Voice, slot ban | The ban is on an *unsubstituted* template slot. A typed name shown as typed is filled data, governed by § Grammar and mechanics, "Quotes". The standard already settles it, so reopening the document earns nothing. | `products/tracker17/docs/CONTENT.md:62-63`; `flow_findings/development-content.md` |
| "other page builds text with `.format` over a typed value" (spec Out of Scope; seed Out) | Does not occur: every remaining `.format` in `web` fills a module constant and passes typed text only as an argument. Nothing to carry or cut. | `grep -n '\.format(' products/tracker17/web/*.py` → 22 hits, each `<CONSTANT>.format(<args>)` (e.g. `pages.py:1368` `template.format(name=_escape(problem.name))`); `security-report.md` § Holes in the code |
| `tracker17 · nemawashi · 2026-10-29_operator-name-with-a-brace` | Its one station is reached, so once the close lands the seed is fully walked. Retire owed (recommendation 1). No other edit owed. | `tracker17 · nemawashi · 2026-10-29_operator-name-with-a-brace` (line 21) |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Untouched by this unit: its sources (SDD § 6 S-8, ADR-0009) did not move. The pick after the retire is `nemawashi-refine`'s to name. | Upstream above |

## Absent

`deferred_decisions.md`, `Deferred:` lines, § Corrections owed while there — none produced by this unit (see Read). No `parked/` stations. The disposable clone at `/private/tmp/refine-OCK2` could not be removed by this run (a safety check refused the `rm -rf`), and is left for the owner to delete.
