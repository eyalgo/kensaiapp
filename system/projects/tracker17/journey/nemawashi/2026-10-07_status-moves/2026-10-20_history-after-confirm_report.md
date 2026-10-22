# 宿場 Shukuba refine — `2026-10-20_history-after-confirm`

*Unit `2026-10-20_history-after-confirm`, sealed Tobiishi, reviewed 2026-10-20 (key named by the caller; `CONTEXT_PM.md` names the same, `Sealed`).
Station `2026-10-19_cancel-confirmation` (root). Seed `2026-10-07_status-moves`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves rows 2, 3 |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-19_cancel-confirmation` | — | Considered row 1 |
| 3 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 2 | Considered row 1 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1, 2 | Moves row 1; Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-10-20_history-after-confirm`, `flow_findings/development-specs.md` | 0 blocking; 4 change-local (rules anchored on lines, a downstream role named, an unrecorded fallback, headers read not captured) — end with the unit. |
| flow findings | same, `flow_findings/development-design.md` | 0 blocking; 4 change-local. "Record owed — CP-351" has no step that fills it → companion item (Moves row 2). Probe scripts kept only in a temp dir, blanket assertion reasons, the Chromium dependence — end with the unit. |
| flow findings | same, `flow_findings/development-plan.md` | 0 blocking; 3 change-local (red-at-baseline cases unmarked, review-only restrictions with no verifier, machine-specific paths) — end with the unit. |
| flow findings | same, `flow_findings/development-implementation.md` | 0 blocking; 3 change-local. The history matrix's docstring claims a stronger contract than it asserts (Considered row 4); the other two are about the run's own counts and end with it. |
| code-integrity report | same, `code-integrity-report.md` | `Integrity: pass`; no bug; one coverage gap closed in place (4 cases); card suite 1250 passed, browser folder 67 passed; surfaced no candidate seed. |
| developer's closing commit | `025a7406f` | Matrix relaxed: a later return may restore the 200 refusal page (recorded with reason); a fence breach caught and restored in task 3; previous change's fence and the assertion review pass; record owed handed to the plan's corrections. |
| deferred decisions | same, `deferred_decisions.md` | One record gap, **Owner: none**: a move refusal reached with no press keeps "the move you pressed" (`web/pages.py:760`) against CONTENT v12 RN-26 / UXD UX-I3 → now carried by seed item 3 (Moves row 1). |
| the closing commit's `Deferred:` lines | `025a7406f` | `Deferred: none`. |
| corrections owed | same, `tl_instruction.md` § Corrections owed while there | One *Owed outside this change's reach*: the history mechanism is absent from `docs/SDD.md` § 4 and `docs/adr/` → measured still absent; companion item § 5.1 (Moves row 2). |
| work handed on | same, `change_spec.md` § Out of Scope | No-press refusal words → seed item 3 (Moves row 1). Back while the move is still allowed, other pages restored from history, the out-of-date wording → seed item 3 `out-of-date-move`, already carrying them. Timed run → item 4. Delete confirmations → `tracker17 · nemawashi · 2026-10-11_delete-and-rename`. Writing the record → companion (Moves row 2). Screen-reader pass and browser pins only fence. |

## Upstream

`git log --since=2026-10-07T02:17:39+02:00 -- products/tracker17/docs/` (the seed's first commit). Since the previous refine of this seed, all 2026-10-20: CONTENT v12 (`fedb675ea`, RN-26: a refusal reached with no press), DESIGN v4 (`9d8c5d734`, the confirm-strip height), UXD v7 (`f90b692f9`, the no-press refusal kept as its own case) and UXD v8 (`afffd0d5e`, "no refusal offers a reload on a page built after it"). Each closed its companion. Live `*_open_issues.md` before this run: none (`find products/tracker17/docs -name '*open_issues*' -not -path '*/trail/*'` prints nothing). After it: `SDD_open_issues.md` (Moves rows 2, 3).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null`, so no product chain is in flight. `system/logs/chain-change-tracker17-state.json`: key `2026-10-20_history-after-confirm`, `pending: refine`, which is this run. No open unit at `journey/tobiishi/`'s root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a seed | `tracker17 · nemawashi · 2026-10-07_status-moves` (line 19) | Item 3 offered a reload that UXD v8 rules out, and the unit's handed-on no-press refusal had no owner; both are the same move refusal page, so item 3 carries both. | `products/tracker17/docs/UXD.md:384-387` (UX-I3), `:175-187` (UX-F4); `products/tracker17/docs/CONTENT.md:556` (RN-26); `products/tracker17/web/pages.py:760`; `deferred_decisions.md` | `2d3b30d33` |
| raise a companion item | `products/tracker17/docs/SDD.md` § 5.1 | No record names the 202 / `no-store` history policy, so a reader can undo it as an unexplained status code. | `products/tracker17/web/routes.py:72`, `:322-333`; `rg -n 'no-store\|Clear-Site-Data\|Cache-Control\|HTTP 202' docs/SDD.md docs/adr/` → exit 1, nothing; `tl_instruction.md` § Corrections owed while there | `8116aee1d` |
| raise a companion item | `products/tracker17/docs/SDD.md` § 5.2 | S-4's bar says an out-of-date move "offers a reload"; UXD v8 says none does. Two settled documents disagree. | `products/tracker17/docs/SDD.md:832`; `products/tracker17/docs/UXD.md:384-387` | `8116aee1d` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-19_cancel-confirmation` — close owed | Reached: all six reached-when items hold on `main`. Items 1, 3 and 4 are covered by the passing suites. | Fresh clone at `9b05680c7`: `pytest products/tracker17/tests/e2e/` → `67 passed`, no skips; `pytest products/tracker17/tests/` → `1250 passed`; `grep -n _WITHHELD_MOVES products/tracker17/web/pages.py` → exit 1 |
| `tracker17 · nemawashi · 2026-10-07_status-moves` (line 19) — shape 6 | Item 3, as amended, can be reached where it stands. Its bar is UX-I3 and AC-12's refusal with saved data unchanged, and its own work lands each part: the refusal page and `web/pages.py:760`'s words exist today. One re-aim (this run), so no owner's act. It reads SDD S-4, which the sweep may move, so the change waits on row 1. | `products/tracker17/docs/SRS.md:505-508` (AC-12); `products/tracker17/docs/UXD.md:370-394` (UX-I3) |
| `tracker17 · nemawashi · 2026-10-07_status-moves` (line 20) `move-timed-run` | Unchanged; nothing in this unit touches the timed run or NFDR QC-48. | `change_spec.md` § Out of Scope |
| `products/tracker17/tests/e2e/test_moves.py` history-matrix docstring | It claims every return is a fresh load, while the test accepts a later cache restore. The relaxation is recorded with its reason, and a stale test docstring is a fix rather than route work, so it is not cut as a seed. | `flow_findings/development-implementation.md`; `025a7406f` "Matrix refinement" |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename`, `…_narrow-and-sort`, `…_project-summary`, `…_protect-saved-data` | Nothing in this unit or the 2026-10-20 doc moves touches their sources. The confirmation they reuse is unchanged except its response status. | `git diff 61f97a0b2 025a7406f --stat -- products/tracker17` (routes.py and four test modules) |

## Absent

`halt_report.md`: a sealed unit has none.
