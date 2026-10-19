# 宿場 Shukuba refine — `2026-10-13_full-volume-run`

*Unit `2026-10-13_full-volume-run`, sealed Tobiishi, reviewed 2026-10-13. Key named by the caller; `contexts/CONTEXT_PM.md` names the same key, `**Status:** Sealed`.
Station `2026-10-13_full-volume-run` (root). Seed `2026-10-07_comment-on-a-task`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves row 2 |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17` | — | Considered row 1 |
| 3 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 2 | Considered row 1 |
| 4 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 2 | recommendation 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-10-13_full-volume-run`, `flow_findings/` — `development-specs.md`, `development-design.md`, `development-plan.md`, `development-content.md`, `development-implementation.md` | 1 blocking, 12 non-blocking, all change-local, 0 skill-general. The blocking one (content) says `CONTENT.md` § Scope does not settle whether the timed run's rows are governed, and they carry an em dash, a semicolon and "failed" → Moves row 2. The rest are coverage, divergence-record and evidence notes on this unit's own records (Considered rows 4–5) |
| code-integrity report | `…/code-integrity-report.md` | `Integrity: pass`; no code changed; seven test cases added, each mutation-proved (comment position, readback before landing, printed failing rows); suite 1084 → 1091; nothing surfaced unfixed |
| developer's closing commit | `eef4f062c` | Review Notes: `FixtureShapeError` added beyond the plan; `_open_volume` shared; the label actions left off the new `_measure_action` core under CP-276, named as a follow-up; width repair `6ec824065`; two clone directories left under `/private/tmp` |
| deferred decisions | absent — the unit folder holds no `deferred_decisions.md` (`ls` of the folder) | — |
| the closing commit's `Deferred:` lines | absent — `eef4f062c` carries none (`code-integrity-report.md` § Deferrals: `grep -E '^(Deferred\|Failing):'` printed nothing) | — |
| corrections owed | absent — `tl_instruction.md` has no § Corrections owed while there (`grep -c "Corrections owed"` → `0`) | — |
| work handed on | `change_spec.md` § Out of Scope | NFR-1 actions not yet built, each left "to the station that builds it": moving → `tracker17 · nemawashi · 2026-10-07_status-moves` (line 19); filtering and sorting → `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` (line 19); summary → `tracker17 · nemawashi · 2026-10-11_project-summary` (line 18); deleting a project → `tracker17 · nemawashi · 2026-10-11_delete-and-rename` (line 19); deleting a task and renaming a project → carried by none, now placed (Moves row 1). Delete with comments and unreadable-data pages are already on their seeds; the rest only fence |

## Upstream

`git log --since=2026-10-07T02:17:39+02:00 --name-status -- products/tracker17/docs/` since the seed's first commit; the moves since the previous refine on this seed: `architecture_open_issues.md` opened `7f9532d83`, answered `c6f8b0f65`, folded into NFDR v13 `5e68bc569` (RN-15); PRD v7 `faf9430a4` (the not-public assumption); `what_left.md` `9db6b9bbf`. None touches QC-48, NFR-1 or TS-5, the sources of the open station. Live `*_open_issues.md` before this run: none (`find products/tracker17/docs -name '*_open_issues.md' -not -path '*/trail/*'` printed nothing). This run opened `CONTENT_open_issues.md` (Moves row 2).

## Held

None. `system/logs/chain-tracker17-state.json`: `"ended": "settled"`, `"pending": null`, so no chain is in flight. `system/logs/chain-change-tracker17-state.json` carries this key with `pending` set to `refine`, which is this run. `journey/tobiishi/` holds only `trail/`, so no open unit walks a seed or station.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a seed | `tracker17 · nemawashi · 2026-10-11_delete-and-rename`, items `delete-a-task` and `rename-a-project` | The unit handed deleting a task and renaming a project to the stations that build them, QC-48 has each such change add its action to the timed run, and only `delete-a-project` carried a timing | `change_spec.md` § Out of Scope, first line; `products/tracker17/docs/nfdr.md:L412-L414` (QC-48); `products/tracker17/docs/SRS.md:L307-L309` (NFR-1, "creating, editing, moving, deleting") | `c33fa45dc` |
| raise a companion item | `products/tracker17/docs/CONTENT_open_issues.md` § 3.1, on `CONTENT.md` § Scope | Scope covers what the tracker prints in its terminal and excludes comments and test names, and it says nothing about a developer check's output. The timed run prints a banned em dash, semicolon and "failed" there, and the content audit left this blocking with no owner | `products/tracker17/tests/timed_run.py:153`, `:158`, `:691`, `:783`; `CONTENT.md` § Scope; `flow_findings/development-content.md`, the blocking finding; `change_text.md` § Findings for the Content Manager | `b5265e673` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| 1. `tracker17 · shukuba · 2026-10-13_full-volume-run` | Reached-when 1–4 hold now. The close is the Scrum Master's | Fresh clone of the instance at `5eee9ce3f`: from `products/tracker17`, `python3 tests/timed_run.py` → exit 0, 80 lines, no `over` or `refused`, comment 42.9 / 0.2 / 43.0 ms, assignee add 44.9 / 0.1 / 45.0 ms, assignee remove 46.4 / 0.1 / 46.5 ms, each fixture line `1000 tasks, 20 comments each` with its text lengths (items 1, 3); `tests/integration/test_timed_run.py` holds `test_timed_{comment,assignee_add,assignee_remove}_refusal_or_wrong_redirect_never_requests_landing` and `…_landing_requires_…` for each action (item 2); `pytest products/tracker17/tests/` (pytest 9.1.1, from the unchanged `tests/requirements.txt`) → `1091 passed`, exit 0, and every `def test_` at merge base `e5e1cbbae` is still present (item 4) |
| 2. `tracker17 · nemawashi · 2026-10-07_comment-on-a-task` | Station 3 is its last item, and once that station closes every item is ticked. The retire is the Scrum Master's, recommended | `seed.md` § Stations; recommendation 1 |
| 3. `tracker17 · nemawashi · 2026-10-07_status-moves`, `…2026-10-11_narrow-and-sort`, `…2026-10-11_project-summary` | Each already carries the timing for the NFR-1 action it builds | `tracker17 · nemawashi · 2026-10-07_status-moves` (line 19); `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` (line 19); `tracker17 · nemawashi · 2026-10-11_project-summary` (line 18) |
| 4. Two lines at 101 columns in `tests/integration/test_timed_run.py` (implementation audit) | A convention slip with no failing gate. Ruff passes, and the next change that edits the file repairs it under the found-while-walking rule. It needs no station | `awk 'length>100'` → `:2200: 101`, `:2250: 101`; `flow_findings/development-implementation.md`, placement-of-record finding |
| 5. Remaining change-local findings (specs coverage of slow rows; plan whole-run refusal and untracked-file checks; design `Publishes text:` note; implementation evidence wording) | About this unit's own records, and the integrity pass closed the redirect and printed-row gaps. None names work left without an owner | `flow_findings/*.md`; `code-integrity-report.md` § Tests added |
| 6. Developer's follow-up: route the label actions through `_measure_action` | A refactor of harness code that CP-276 fenced. No gate fails and no product document asks for it, so this run cites no occurrence and carries nothing | `eef4f062c` Review Notes; `pytest` above, exit 0 |

## Absent

Halt report — not produced by a sealed unit. `deferred_decisions.md`, the `Deferred:` lines and § Corrections owed while there are absent, as the Read table says.
