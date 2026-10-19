# 宿場 Shukuba refine — `2026-10-19_allowed-moves`

*Unit `2026-10-19_allowed-moves`, sealed Tobiishi, reviewed 2026-10-19.
Station `allowed-moves` (root). Seed `2026-10-07_status-moves`.*

The key was the caller's; `tracker17`'s PM context names the same unit as `Sealed`.

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-19_allowed-moves` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1 | Moves row 1; Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-10-19_allowed-moves`, `flow_findings/development-specs.md` | 0 blocking, 4 change-local (unit-level reason narrowed, no task-page stale example, mechanism in rules, timed-run fence reversed and set aside) — all ended with the unit; the timed-run question is answered in Considered row 5 |
| flow findings | same unit, `flow_findings/development-design.md` | 0 blocking, 3 change-local (P7 coverage, CP-313 check, hand-off count) — ended with the unit |
| flow findings | same unit, `flow_findings/development-plan.md` | 0 blocking, 3 change-local (class names, e2e gate wording, lint gates in task 4 only) — ended with the unit |
| flow findings | same unit, `flow_findings/development-content.md` | clean |
| flow findings | same unit, `flow_findings/development-implementation.md` | 0 blocking, 5 change-local: `_WITHHELD_MOVES` lets `web` filter the offered set (→ Moves row 1); red-by-rule notes, a paraphrased quote, the unrun e2e layer (→ Moves row 1), the `__version__` reason (→ Considered row 6) |
| code-integrity report | same unit, `code-integrity-report.md` | `Integrity: pass`, 1170 passed; fixed two defects in `tests/e2e/test_moves.py` by reading only; § Not verified: that file has never run, Chromium would not start (→ Moves row 1) |
| developer's closing commit | `0f39503` | Divergences: `__version__` not added to product modules (upheld by integrity, Calls made 2); e2e not run; no other |
| deferred decisions | same unit, `deferred_decisions.md` | 6 entries. `cancelled` button + confirmation → owned by seed line `cancel-confirmation`; out-of-date refusal → `out-of-date-move`; overdue on filter/summary/All tasks → `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` (line 18, 19) and `tracker17 · nemawashi · 2026-10-11_project-summary` (line 18); CP-315 timed run → `move-timed-run`; CP-318 and CP-316 readings → consumed by the design, nothing owed. Every entry has an owner |
| the closing commit's `Deferred:` lines | `0f39503` | absent — `git log -1 --format=%B 0f39503 \| grep -n '^Deferred:'` prints nothing; integrity report § Deferrals agrees |
| corrections owed | same unit, `tl_instruction.md` § Corrections owed while there | Two *Owed outside this change's reach* lines, NFDR QC-48 and SDD TS-5 → non-move, Considered row 4 |
| work handed on | same unit, `change_spec.md` § Out of Scope | `cancelled` + confirmation → `cancel-confirmation`; out-of-date wording → `out-of-date-move`; filter/summary/All tasks → `narrow-and-sort`, `project-summary`; delete confirmations → `tracker17 · nemawashi · 2026-10-11_delete-and-rename`; e2e tests for moves, saved-data rule, undo → fences, nothing handed on |

## Upstream

`git log --since=2026-10-19T09:29:47+02:00 --name-status -- products/tracker17/docs/` (the seed's first commit, `e77c12b`) lists only `e77c12b`, the instance import that added every file. Nothing under `docs/` moved since. `find products/tracker17/docs -name '*_open_issues.md'` prints nothing: no live companion.

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: settled`, `pending: null`, so no product chain is in flight. `system/logs/chain-change-tracker17-state.json` is pending only on `refine` for this unit, which is this run. No change unit is open under the tobiishi root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| 1. modify a seed | `tracker17 · nemawashi · 2026-10-07_status-moves` (line 18, line 27) | Two things the unit left have no owner: the pages' filter that withholds `cancelled` must go once the button exists, or `web` keeps a second rule about the offered moves; and `tests/e2e/test_moves.py` has never run. `cancel-confirmation` is the station that builds the button and writes the next browser tests, so it carries both. Re-aim 1 of this station | `products/tracker17/web/pages.py:603-609`; implementation flow finding 1; code-integrity report § Not verified; this run: `pytest products/tracker17/tests/e2e/` in a clone at `2117033` → `2 passed, 34 errors`, `libglib-2.0.so.0: cannot open shared object file` | `aa5df9e` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-19_allowed-moves` | Reached-when holds now, all five items; the close is owed to the Scrum Master. Item 2 reads the typed refusal `MoveNotAllowed` as the domain's reason, since `domain` holds no wording and the words are tested per saved status at the route | 1: `ls products/tracker17/domain` lists `workflow.py`. 2: `tests/unit/test_workflow.py:91-106`, 16 parametrized pairs. 3: `tests/integration/test_move_pages.py:57`, `tests/integration/test_move_routes.py:94`, `:113`. 4: `tests/integration/test_move_tracker.py:196`, `tests/integration/test_move_routes.py:255`; filter and summary do not exist yet. 5: clone at `2117033`, `pytest -q products/tracker17/tests/` → `1170 passed`, exit 0 |
| `tracker17 · nemawashi · 2026-10-07_status-moves`, next station `cancel-confirmation` (shape 6) | Can be walked where it stands: the button, confirmation, focus and double-press work are its own; the e2e harness exists; layer 5 is defined to run only on macOS or the listed Debian/Ubuntu releases, so its browser bar is checked there, not on this Fedora machine | `products/tracker17/docs/SDD.md:822-839` (S-4 Reached when, Command); `products/tracker17/docs/nfdr.md:533-538`; `ls products/tracker17/tests/e2e` |
| This machine's browser libraries | The browser suite errors here before any test runs. NFDR already states this is a missing prerequisite on other Linux, so no document is wrong and no seed is owed; it is the owner's call where layer 5 runs, and the station close in Next moves row 1 and the later `cancel-confirmation` close need that run | this run: `2 passed, 34 errors`, `libglib-2.0.so.0` missing; `products/tracker17/docs/nfdr.md:533-538`; code-integrity report § Calls made 3 |
| `products/tracker17/docs/nfdr.md` QC-48, `products/tracker17/docs/SDD.md` TS-5 | No companion item: both state a rule that stays right; what is false is the run's coverage, which the seed's `move-timed-run` line restores. The correction line asks for a record change only if that station is dropped, and it is not | `tl_instruction.md` § Corrections owed while there; `tracker17 · nemawashi · 2026-10-07_status-moves` (line 20) |
| `move-timed-run` vs this unit (spec audit's double-count question) | Not double-counted: the design set CP-315 aside and the unit left the timed run untouched | `git diff --stat 2117033^1 2117033 -- products/tracker17/tests/timed_run.py products/tracker17/tests/integration/test_timed_run.py` prints nothing; `deferred_decisions.md`, CP-315 entry |
| `__version__` divergence (implementation finding 5) | About the shared Python packet's scope, not this product's route; integrity upheld it against `versioning.md` | code-integrity report § Calls made 2 |
| `tracker17 · nemawashi · 2026-10-11_narrow-and-sort`, `…_project-summary`, `…_delete-and-rename`, `…_protect-saved-data` | Already carry what this unit handed on to them; nothing upstream moved under them | Read table, deferred decisions and work handed on rows |

## Absent

Halt report — not produced by a sealed unit. `Deferred:` lines — none in `0f39503`. No live `*_open_issues.md` in the product.
