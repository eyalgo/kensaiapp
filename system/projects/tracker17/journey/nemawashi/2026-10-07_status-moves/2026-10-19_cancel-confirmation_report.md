# 宿場 Shukuba refine — `2026-10-19_cancel-confirmation`

*Unit `2026-10-19_cancel-confirmation`, sealed Tobiishi, reviewed 2026-10-20 (key named by the caller).
Station `2026-10-19_cancel-confirmation` (root). Seed `2026-10-07_status-moves`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves rows 2, 3 |
| 2 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1 | Moves row 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-10-19_cancel-confirmation`, `flow_findings/development-specs.md` | 0 blocking; 4 change-local (test lists miss rules, mechanism anchors in rules, unrun verified claims, a role named) — all about this unit's spec, none names unowned work. |
| flow findings | same, `flow_findings/development-design.md` | 0 blocking; 5 change-local. The response-header pair is a durable decision no record states → carried on the station (Moves row 1). No fallback if the eviction header fails → it failed; carried (Moves row 1). Three coverage/measurement gaps end with the unit. |
| flow findings | same, `flow_findings/development-plan.md` | 0 blocking; 2 change-local (an unrecorded `compileall` gate line; a prescribed fixture mechanism) — end with the unit. |
| flow findings | same, `flow_findings/development-content.md` | 0 blocking; 1 change-local: the refusal "…the move you pressed…" is shown where no press happened → companion item on `CONTENT.md` (Moves row 2). |
| flow findings | same, `flow_findings/development-implementation.md` | 1 blocking: `Suite: green` while the history case fails and CP-338 is unmet — accounted for: the station is not reached and carries the case (Moves row 1). 1 skill-general (the card's command cannot collect `tests/e2e/`) — machinery, not this route's; the station's reached-when 5 already runs that folder on its own. 7 change-local, the history-mechanism one carried (Moves row 1). |
| code-integrity report | same, `code-integrity-report.md` | `Integrity: pass` for task 2; tasks 1 and 3 deferred and real; the browser folder `1 failed, 56 passed`; "The change is not finished." Surfaced no candidate seed. |
| developer's closing commit | `1ab334527` | Task 2 landed; task 1's code on the branch but its history case fails on every run; three history alternatives rejected, the fix "not applied" pending an architect ruling. |
| deferred decisions | same, `deferred_decisions.md` | Three record gaps, each owned on the route: the out-of-date move → `tracker17 · nemawashi · 2026-10-07_status-moves` (line 19); the delete confirmations → `tracker17 · nemawashi · 2026-10-11_delete-and-rename` (line 17, line 19); the overdue agreement for `cancelled` (AC-13's third case) → `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` (line 19) and `tracker17 · nemawashi · 2026-10-11_project-summary` (line 18). |
| the closing commit's `Deferred:` lines | `1ab334527` | `task 1 — the Back-after-confirm history case … Clear-Site-Data "cache" does not evict …` → (b): the change's own design § 3 is what is wrong; the next change on the open station takes it (Moves row 1). `task 3 — depends on task 1` → follows task 1, (b) (Moves row 1). |
| corrections owed | same, `tl_instruction.md` § Corrections owed while there (line 63) | One *Owed outside this change's reach*: `DESIGN.md` confirm-strip height "elsewhere" vs the task-page move button → measured still false; companion item on `DESIGN.md` (Moves row 3). |
| work handed on | same, `change_spec.md` § Out of Scope | Out-of-date wording → seed item 3 `out-of-date-move`; delete confirmations → `tracker17 · nemawashi · 2026-10-11_delete-and-rename`; overdue views → `narrow-and-sort`, `project-summary`; timed run → seed item 4 `move-timed-run`. Undo, a screen-reader pass, a page script, the workflow rule and the data format only fence. |

## Upstream

`git log --since=2026-10-07T02:17:39+02:00 --name-status -- products/tracker17/docs/` (the seed's first commit, `5d9a6ce09`): since the previous refine of this seed (2026-10-19) only `docs/what_left.md` moved (`7c34e5726`, readme-status). Earlier: UXD v6 (UX-I3's refusal exception), CONTENT v10/v11, NFDR v11–v13, SDD v10, PRD v7, all already read by the stations-from-seed run of 2026-10-19 that cut this route. Live `*_open_issues.md` before this run: none (`ls products/tracker17/docs/*open_issues*` — no matches). After it: `CONTENT_open_issues.md`, `DESIGN_open_issues.md` (Moves rows 2, 3).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null` — no product chain in flight. `system/logs/chain-change-tracker17-state.json`: key `2026-10-19_cancel-confirmation`, `pending: refine` — this run. No open unit at `journey/tobiishi/`'s root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a station | `tracker17 · shukuba · 2026-10-19_cancel-confirmation` | The unit sealed with its history case failing, so the station's next change must carry that case with a mechanism other than the eviction header, then the deferred file-fence review, and list the history mechanism as a record owed; what it is amended, reached-when unchanged. | `1ab334527` `Deferred:` lines; `code-integrity-report.md` § The finding; `products/tracker17/web/routes.py:72-73`; `grep -rn "Clear-Site-Data\|no-store" products/tracker17/docs/` prints nothing; measured: `pytest tests/e2e/` in a fresh clone at `e0b0f245d` → `1 failed, 56 passed`, `test_moves.py:423` | `21e72e6e7` |
| raise a companion item | `products/tracker17/docs/CONTENT.md` § 3.1 | The refusal formula gives its reason as what the reader pressed, and a page load with no press shows that refusal. | `products/tracker17/web/routes.py:351-352`; `products/tracker17/web/pages.py:760`; `products/tracker17/docs/CONTENT.md:207-211`; `flow_findings/development-content.md` | `b8149c791` |
| raise a companion item | `products/tracker17/docs/DESIGN.md` § 3.1 | The confirm-strip clause gives the task page {spacing.control} while the move button it replaces is {spacing.row-control} there; the plan's correction owed, measured still false. | `products/tracker17/docs/DESIGN.md:452-461`; `products/tracker17/web/style.css:228-231`; `tl_instruction.md` (line 63) | `97501b518` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-19_cancel-confirmation` — close | Not reached: reached-when 5 fails. Items 1–3 and 6 hold as far as measured; item 2's grep prints nothing; item 6 passes. | Fresh clone at `e0b0f245d`: `pytest products/tracker17/tests/e2e/` → `1 failed, 56 passed`; `pytest products/tracker17/tests/` → `1220 passed`; `grep -n _WITHHELD_MOVES products/tracker17/web/pages.py` → exit 1 |
| `tracker17 · shukuba · 2026-10-19_cancel-confirmation` — shape 6 | Reachable where it stands: reached-when 5 is NFDR § 9's layer-5 run, which this Mac runs (56 cases pass); the one failing case is this station's own work, carried by the next change. No owner's act: one re-aim so far (the 2026-10-19 refine), none in this run. | `tracker17 · nemawashi · 2026-10-07_status-moves` (line 27); the e2e run above |
| `tracker17 · nemawashi · 2026-10-07_status-moves` | Its line for this station still states the bar; the deferred work is the station's own, so no seed edit; items 3–4 unchanged. | `tracker17 · nemawashi · 2026-10-07_status-moves` (line 18) |
| the history case as an `ADR-0003` gap | One mechanism failed, not the requirement; whether Back-after-confirm can be met with no page script is the next change's design call, so no companion on the ADR yet. | `1ab334527` Developer Review Notes, "Task 1 blocked" |
| `tracker17 · nemawashi · 2026-10-11_narrow-and-sort`, `tracker17 · nemawashi · 2026-10-11_project-summary`, `tracker17 · nemawashi · 2026-10-11_delete-and-rename`, `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Already carry the handed-on work (AC-13's three cases; the delete confirmations); nothing in this unit touches their sources. | `deferred_decisions.md`; the seed lines cited under Read |
| the card's `Test command:` skipping `tests/e2e/` | Skill-general (kaizen `test-command-excludes-e2e-gate`), not the route's; the station runs that folder on its own. | `flow_findings/development-implementation.md`; `products/tracker17/tests/conftest.py:7-9` |

## Absent

None — every artifact of a sealed Tobiishi was on disk. No `halt_report.md` (a sealed unit has none).
