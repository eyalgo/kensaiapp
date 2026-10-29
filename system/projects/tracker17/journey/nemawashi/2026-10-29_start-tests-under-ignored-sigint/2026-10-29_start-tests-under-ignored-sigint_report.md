# 宿場 Shukuba refine — `2026-10-29_start-tests-under-ignored-sigint`

*Unit `2026-10-29_start-tests-under-ignored-sigint`, sealed Tobiishi, reviewed 2026-10-29.
Station `start-tests-under-ignored-sigint` (root). Seed `2026-10-29_start-tests-under-ignored-sigint`.
Key named by the caller.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | — | Moves row 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-10-29_start-tests-under-ignored-sigint`, `flow_findings/development-specs.md` | 0 blocking, 2 change-local: the e2e stop tests' order dependence was inferred, not run; the "keeps running" invariant is unpinned. The first is answered by measurement (Considered row 3); the second is the spec's own record, no route work |
| flow findings | same unit, `flow_findings/development-design.md` | 0 blocking, 3 change-local (altitude, no named home for the collection rule, the operator-side invariant held by construction). The collection rule is moot once the bar names two suites (Moves row 1) |
| flow findings | same unit, `flow_findings/development-plan.md` | 1 blocking: an NFDR § 10 sentence called false, its edit deferred, while gates required an empty `docs/` diff. Answered: the sentence is not false (Considered row 1). 3 change-local: Task 2's real dependency on Task 1, an unproved restore case, the e2e baseline unmeasured — the last measured here (Considered row 3) |
| flow findings | same unit, `flow_findings/development-implementation.md` | 1 blocking: Task 2 deferred as "depends on task 1", though its proof needs no outer collection, so no test fails on `970f6a4ca`. Carried onto the station (Moves row 1). 3 change-local (101-column line, collection unbuildable, `Suite: green` headline); 1 skill-general, not the route's |
| code-integrity report | same unit, `code-integrity-report.md` | `Integrity: pass`; both deferrals real; suite 2651 passed. Surfaced, not fixed: `tests/conftest.py:1` is 101 columns, inside the deferral. Carried onto the station (Moves row 1) |
| security report | same unit, `security-report.md` | `Security: reported`, no hole. § Left for the PM (line 9): dependency audit did not run, the NFDR names none. No companion owed (Considered row 2) |
| developer's closing commit | `<a commit not in the public history>` | Task 1 landed in part (the session SIGINT fixture), the outer collection backed out after 5 collection errors; Task 2 not written; options named: unique basenames, `__init__.py`, or two commands |
| deferred decisions | same unit, `deferred_decisions.md` | One entry, "Owner: none — for shukuba-refine": a reading letting the shared harness collect all four folders on an outer run. Owned and closed here: the bar no longer asks for that collection (Moves row 1), so no later spec takes the reading up |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | `task 1` (four-folder collection cannot be built) → (b): the station's bar, which the spec copied, was what was wrong; carried by move 2 and move 1, which name the product's two suites. `task 2` (depends on task 1) follows task 1 → (b): the proof test is carried as a reached-when clause on the open station (Moves row 1) |
| corrections owed | same unit, `tl_instruction.md` § Corrections owed while there | One *Owed outside this change's reach* line: `nfdr.md` § 10 equates the outer command with `pytest tests/`. Non-move: the collection did not change, and § 10 already names `pytest tests/e2e/` as the second suite (Considered row 1) |
| work handed on | same unit, `change_spec.md` § Out of Scope | "The PM can raise them as their own change": the two e2e SIGINT stop tests that failed alone under ignored SIGINT. They now pass alone (Considered row 3); nothing owed |

## Upstream

`git log --since=2026-10-29T09:34:27+01:00 --name-status -- products/tracker17/docs/` → empty: nothing
under the product's `docs/` changed since the seed was first committed. `ls products/tracker17/docs/ | grep open_issues`
→ empty: no live companion.

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: settled`, `pending: null`, so no product chain
is in flight. No change unit is open at the `tobiishi/` root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a station; modify a seed | `tracker17 · shukuba · 2026-10-29_start-tests-under-ignored-sigint`; `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint` (line 23) | Shape 6: the bar asked one root run to cover `unit`, `integration`, `e2e` and `architecture`, which the product's collection rule keeps apart and five shared basenames make impossible in one process; the product's own definition is two suites. The bar now names both suites under both launches, and keeps the proof test Task 2 deferred (a blocking finding) plus the 101-column reflow, so the station stays open. One re-aim on this station so far | `<a commit not in the public history>` (Task 1 blocked: 5 collection errors); `products/tracker17/docs/nfdr.md:L597-L601`; `flow_findings/development-implementation.md` blocking line; `git show 3b2c0dd28:products/tracker17/tests/conftest.py \| head -1 \| awk '{print length}'` → `101` | `26e7db24b` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `products/tracker17/docs/nfdr.md` § 10 | Not false: the outer run's collection did not change, and § 10 already names `pytest tests/e2e/` as the second suite the layer-5 rows need; no companion item | `products/tracker17/docs/nfdr.md:L597-L601`; `<a commit not in the public history>` ("not made false, because the outer command's collection did not change") |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already says no audit command exists and verifies QC-40 by review, as earlier refines here found; no companion owed | `security-report.md` (line 9); `products/tracker17/docs/nfdr.md:354`, `:664` |
| the two e2e SIGINT stop tests, handed on by the spec | They now pass alone under ignored SIGINT, so the order dependence is gone and nothing is owed | disposable clone at `3b2c0dd28`: `sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/e2e/test_first_project.py products/tracker17/tests/e2e/test_people.py -q'` → `19 passed` |
| close of `tracker17 · shukuba · 2026-10-29_start-tests-under-ignored-sigint` | Not reached: the suite half holds, the proof test does not exist | same clone: root run under trap and foreground → exit 0, `2651 passed` each; `tests/e2e/` under trap and foreground → exit 0, `121 passed` each; no test is named as the proof (`<a commit not in the public history>`, "Task 2 … not written") |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Its bar names "both suites", which this run's wording agrees with; nothing it rests on moved | `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (line 9); Upstream above |
| the owner's act on the open station | One re-aim by this run, none before: below the two that send a station to the owner | this report's Moves row 1; no earlier refine report beside the seed |

## Absent

None.
