# 宿場 Shukuba refine — `2026-10-21_move-timed-run`

*Unit `2026-10-21_move-timed-run`, sealed Tobiishi, reviewed 2026-10-21. Key named by the caller; `contexts/CONTEXT_PM.md` names the same key, `**Status:** Sealed`.
Station `2026-10-21_move-timed-run` (root). Seed `2026-10-07_status-moves`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-21_move-timed-run` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 1 | recommendation 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-10-21_move-timed-run`, `flow_findings/` — `development-specs.md`, `development-design.md`, `development-plan.md`, `development-content.md`, `development-implementation.md` | 0 blocking, 12 non-blocking, all change-local, 0 skill-general. Plan and content clean. Specs: a wrong CP-383 → CP-391 pointer, examples with no named test, two claims read rather than run, CP-392 prescribing edit shape. Design: the `todo` pre-state guard had no isolating case — answered by `test_timed_move_requires_todo_even_with_plausible_success`, which the integrity pass mutation-proved. Implementation: four evidence notes on the closing commit's own record (Considered row 2) |
| code-integrity report | `…/code-integrity-report.md`, commit `0f4226e25` | `Integrity: pass`, owner's Mac, no CI; no test added; three spot mutations each turned a named test red; eight new over-100-column lines rewrapped, one dead helper removed; 1370 passed. Surfaced, left: nine older over-100-column lines (Considered row 3) and a Tech Lead call on the CP-372 location check, taken as (a) |
| developer's closing commit | `9141daa6e` | Implementation complete, 4 tasks delivered, 0 not delivered; the Python 3.11 floor (NFDR QC-60) kept over the packet's 3.13 |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | — |
| the closing commit's `Deferred:` lines | `9141daa6e` — none: `git show -s --format=%B 9141daa6e \| grep '^Deferred:'` prints nothing | — |
| corrections owed | absent — `tl_instruction.md` has no § Corrections owed while there (`grep -i 'corrections owed'` finds nothing) | — |
| work handed on | `change_spec.md` § Out of Scope | The NFR-1 actions not yet built (delete, filter, sort, summary) are handed to their slices, and each is already on a station line: `tracker17 · nemawashi · 2026-10-11_delete-and-rename` (lines 17–19), `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` (line 19), `tracker17 · nemawashi · 2026-10-11_project-summary` (line 18). The `cancelled` move, a move from the task page, the other plain moves, the product code and the limit, and unequal-comment fixtures are fences that hand nothing on |

## Upstream

`git -C products/tracker17 log --since=2026-10-07T02:17:39+02:00 --name-status -- docs/` — SDD v11, ADR-0010 and NFDR v14–v15, UXD v7–v9, CONTENT v12–v15 and DESIGN v4 all settled by 2026-10-21 12:39. None of them moves this station: NFDR QC-48 (`products/tracker17/docs/nfdr.md:429-436`) still asks for every listed action in the timed run, a same-origin mark and a failure on a refused action; SDD § 6 S-4 *Command* (`products/tracker17/docs/SDD.md:891-897`) still ends "`python3 tests/timed_run.py` exits 0 and covers a move". No live companion: `find products/tracker17/docs -name '*open_issues*' -not -path '*/trail/*' -not -name '*template*'` prints nothing.

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: settled`, `pending: null`. `system/logs/chain-change-tracker17-state.json` carries this unit with `pending.refine` — this run itself. No unit is open at `journey/tobiishi/`'s root (only `trail/`).

## Moves

None — no move was owed; see below.

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-21_move-timed-run` | All four reached-when items hold now, so the close is owed to the Scrum Master; never re-aimed by a refine, so no owner's act | Fresh clone at `a5a78755d`: from `products/tracker17`, `python3 tests/timed_run.py` exit 0, printing "move fixture: 1000 tasks, 20 comments each (20000 in all); title of 46 characters, comment of 58 characters", "move a task at 1000 tasks: 24.7 ms", "move landing page at 1000 tasks: 2.9 ms", "move total at 1000 tasks: 27.7 ms" (items 1, 3); `pytest products/tracker17/tests/` → `1370 passed`; `pytest tests/integration/test_timed_run.py` → `128 passed`, with `test_timed_move_refusal_never_requests_landing` and `test_timed_move_landing_requires_200_and_completion` (item 2); `pytest tests/e2e/` in the README's venv → `75 passed` (item 4) |
| `tracker17 · nemawashi · 2026-10-07_status-moves` | Its last item is the station above; once closed, every item is ticked and the seed is walked — recommendation 1, not a seed edit | `tracker17 · nemawashi · 2026-10-07_status-moves` (lines 17–20) |
| the closing commit's record (`9141daa6e`) | The four implementation evidence notes and the specs notes are about this unit's own records; the code they describe was checked and holds, so no route work follows | `flow_findings/development-implementation.md`, `flow_findings/development-specs.md`; the integrity report's rewrap and the 1370-pass run above |
| `products/tracker17/tests/timed_run.py`, `tests/integration/test_timed_run.py` | Nine lines older than this change still pass 100 columns. A packet style point with no gate failing and no product behaviour behind it — left to the next change that edits those files under the boy-scout rule, not carried on a seed | `awk 'length>100'` on the clone: `timed_run.py` 326, 329, 330; `test_timed_run.py` 298, 359, 387, 424, 2207, 2257; `ruff check .` exits 0 (integrity report § The finding) |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename`, `…_narrow-and-sort`, `…_project-summary`, `…_protect-saved-data` | Their sources did not move under them in a way they miss; the timed-run work handed on is already on their lines | Upstream above; work handed on row in § Read |

## Absent

`deferred_decisions.md` (not written by the unit); `tl_instruction.md` § Corrections owed while there (not written); `Deferred:` lines (none in `9141daa6e`); live companions (none). The browser suite first failed with `ModuleNotFoundError: No module named 'playwright'` under the system Python — the README runs it in a venv from `tests/requirements.txt`, and it passed there.
