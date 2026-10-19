# 宿場 Shukuba refine — `2026-10-07_address-taken-start-message`

*Unit `2026-10-07_address-taken-start-message`, sealed Tobiishi, reviewed 2026-10-07. Key named by the caller.
Station `2026-10-07_a-project-that-stays` (root). Seed `2026-10-07_first-project`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `~/.kensaiapp/pins/20261007T110759Z-adq171/core/launchers/chain-product/launcher.sh tracker17` | — | Moves row 2 |
| 2 | walk the next change | owner | `~/.kensaiapp/pins/20261007T110759Z-adq171/core/launchers/chain-change/launcher.sh tracker17` | — | Considered row 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `journey/tobiishi/trail/2026-10-07_address-taken-start-message/flow_findings/development-specs.md` | 0 blocking; 3 change-local (CP-46 suites not run in a real worktree; implementation anchors in rules; trailing newline unstated). End with the unit |
| flow findings | `…/flow_findings/development-design.md` | Clean; QC-40 "Pass today, failing tomorrow" noted as an observation |
| flow findings | `…/flow_findings/development-plan.md` | 0 blocking; 2 change-local (plan fixed the words; no start-level other-cause case, added by integrity), 1 skill-general (plan before content → kaizen `plan-before-content-words-input`, not the route's) |
| flow findings | `…/flow_findings/development-content.md` | Clean |
| flow findings | `…/flow_findings/development-implementation.md` | 0 blocking; 2 change-local (task 1's second rule has no revert proof; Toolchain line omits the venv run). End with the unit |
| code-integrity report | `journey/tobiishi/trail/2026-10-07_address-taken-start-message/code-integrity-report.md` | `Integrity: pass`; one start-level test added (CP-42), two tightened; one call (CP-42 option 1) recorded with its owner, the Product Owner; nothing left unfixed |
| developer's closing commit | `af3439893` (supersedes `6c778da38`) | `Suite: green`; divergences: no `__version__`, no `error: ` prefix; notes `CONTENT.md:250` shows 127.0.0.1:8000 against 8017 → Moves row 2 |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | — |
| the closing commit's `Deferred:` lines | `af3439893` | absent — no body line begins `Deferred:` |
| corrections owed | `journey/tobiishi/trail/2026-10-07_address-taken-start-message/tl_instruction.md:42-45` | Two lines, both files the unit opened itself ("Rides Task"); no *Owed outside this change's reach* line |
| work handed on | `journey/tobiishi/trail/2026-10-07_address-taken-start-message/change_spec.md` § Out of Scope | R-5 second tracker and unreadable-data page → slice `protect-saved-data` (seed § Out, not yet cut); README → `setup-instructions`; reverse pointer test and whole check → open station's reached-when 8 and later units; unreadable-message pointer left unadded → Moves row 1; the rest only fences |

## Upstream

`git log --diff-filter=A --follow --format=%cI -- <seed>` → `2026-10-07T02:17:39+02:00`.
`git log --since=… -- products/tracker17/docs/`: new since the last refine is CONTENT v6
(`db19799c8`, 13:12, folds companion cycle 5), before this unit opened (`e21a54119`, 13:14). Nothing
under `docs/` moved during the unit. No live `*_open_issues.md` before this run
(`ls products/tracker17/docs/*_open_issues.md` → no matches).

## Held

None. `system/logs/chain-tracker17-state.json` reads `ended: settled`, `pending: null`;
`chain-change-tracker17-state.json`'s one pending step is this refine. No open unit under `journey/tobiishi/`.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a seed | tracker17 · nemawashi · 2026-10-07_first-project, line `setup-instructions` | The unreadable-data start message says what is wrong and not what to do; its action points to a README section that first exists on `setup-instructions`, so that station carries it | `docs/UXD.md:308` UX-S2 "each saying what is wrong and what to do"; `main.py:43-44`; `docs/CONTENT.md:252`; `docs/CONTENT.md:161` | `6ce44a330` |
| raise a companion item | `products/tracker17/docs/CONTENT_open_issues.md` § 3.1 (opened) | The terminal examples name 127.0.0.1:8000 while the tracker's address is 127.0.0.1:8017, and the setup instructions quote what the start prints | `docs/CONTENT.md:250`, `:278`; `docs/SDD.md:286`; `main.py:20`; closing commit `af3439893` Review Notes | `c34e10e15` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| tracker17 · shukuba · 2026-10-07_a-project-that-stays | Not reached: 3 now holds, 8 does not; 8 is walkable where it stands (shape 6) — TS-4's fourth check reads TS-3's table and `domain/projects.py`, both present. One re-aim (`af3c6e57e`), none this run, so no owner's act | Disposable copy `/tmp/t17refine.D1Rn`: `python3 main.py` with 127.0.0.1:8017 held → exit 1, stdout empty, stderr the CONTENT line, no `data/`; `grep -n 'def test_' tests/architecture/test_trace.py` → no reverse check; `docs/SDD.md:430-435`; `docs/nfdr.md:100-110` |
| QC-62 and the suites on `main` | Gates green; no work owed | Same copy: `ruff check .` "All checks passed!", `ruff format --check .` "106 files already formatted", `mypy main.py errors.py domain application persistence web` "no issues found in 16 source files" (venv `/private/tmp/t17venv`, ruff 0.16.10, mypy 2.4.0); `pytest tests/` 208 passed, 1 failed (`test_data_is_ignored_by_version_control`, exit 128 — the copy is no git repo) |
| CP-42 other bind failures (integrity's option 1) | Spec fences it as unchanged; no failing run and no owner owed it | `change_spec.md` § Out of Scope line 1; `code-integrity-report.md` § Calls made |
| SRS NFR-8 underlying error line | Not a start failure: NFR-8 covers an action's failure, told in the browser | `docs/SRS.md:342-346` |
| tracker17 · nemawashi · 2026-10-07_tasks-in-a-project, comment-on-a-task, status-moves | Nothing this unit found touches their scope; no source moved under them | Upstream above |

## Absent

`deferred_decisions.md` — none written. `Deferred:` lines — none in `af3439893`. Halt report — a sealed
unit produces none. `pytest tests/e2e/` not re-run here; recorded 12 passed in `code-integrity-report.md`.
