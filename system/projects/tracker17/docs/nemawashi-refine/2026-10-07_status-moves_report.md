# 根回し Nemawashi refine — `2026-10-07_status-moves`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-10-07_status-moves` at `4e6b3135c`, and the pool re-read behind it, 2026-10-27. The slug came from the caller: "answering the retired seed 2026-10-07_status-moves". Run in a `principal-pm:` session.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh nemawashi-pick tracker17` | — | Candidates (four in `unpicked/`, seedbed root empty) |
| 2 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 1 | row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 2 | row 2 |

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-10-19_allowed-moves` — "Nothing to recommend." | read | none | Carries no item. | `trail/2026-10-07_status-moves/2026-10-19_allowed-moves_recommendations.md:L8` |
| `2026-10-19_cancel-confirmation` — "Nothing to recommend." | read | none | Carries no item. | `trail/2026-10-07_status-moves/2026-10-19_cancel-confirmation_recommendations.md:L8` |
| `2026-10-20_history-after-confirm` — "Nothing to recommend." | read | none | Carries no item. | `trail/2026-10-07_status-moves/2026-10-20_history-after-confirm_recommendations.md:L8` |
| `2026-10-21_out-of-date-move` — "Nothing to recommend." | read | none | Carries no item. | `trail/2026-10-07_status-moves/2026-10-21_out-of-date-move_recommendations.md:L8` |
| `2026-10-21_move-timed-run #1` — retire this seed once its last station closes | ignored | none | The retire it asks for already happened, on this seed: all four stations are ticked and the seed is in `trail/`. | `trail/2026-10-07_status-moves/2026-10-21_move-timed-run_recommendations.md:L8-L13`; `trail/2026-10-07_status-moves/seed.md:L17-L20`; `4e6b3135c` |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-10-11_delete-and-rename` | modified | `5d7657923`: L9 now says both preferred predecessors are walked; L25's "if it is picked before `status-moves`" branch replaced by the confirmation it reuses | That branch can no longer happen, since `status-moves` is walked; SDD S-7 is still owed. | `products/tracker17/web/pages.py:L662` `def confirm_strip(`; `grep -rn -i "def .*delete\|def .*rename" products/tracker17/web products/tracker17/application` → no match |
| `2026-10-11_narrow-and-sort` | kept | — | SDD S-5 still owed; its dependency on `status-moves` is now met, and its text says nothing that the walk made false. | `ls products/tracker17/domain/filtering.py products/tracker17/domain/sorting.py` → both missing; `products/tracker17/domain/workflow.py` exists |
| `2026-10-11_project-summary` | modified | `5d7657923`: page-title pointer `web/pages.py:L630` → `L934` | The line moved as the moves slice grew the file; the claim (the title is the bare project name) still holds. | `products/tracker17/web/pages.py:L934` `_document(f"{project.name} - tracker17", body)`; `ls products/tracker17/domain/summary.py` → missing |
| `2026-10-11_protect-saved-data` | kept | — | SDD S-8 still owed; the cited start path is unchanged and no lock exists in code. | `products/tracker17/main.py:L41-L48`; `grep -rln 'fcntl\|flock' products/tracker17` → only `docs/trail/sdd/self_answer-2.md` |

## The docs cut

Not owed: the SDD's slices are S-1 to S-8 (`products/tracker17/docs/SDD.md:L698-L1042`); S-1 to S-4 are walked (`trail/2026-10-07_first-project`, `trail/2026-10-07_tasks-in-a-project`, `trail/2026-10-07_comment-on-a-task`, `trail/2026-10-07_status-moves`), S-5 to S-8 are each carried by one candidate above, and no companion item was written. Every entry in `products/tracker17/docs/what_left.md` falls under S-5, S-6 or S-7.

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| A branch for a pick order that can no longer happen | `unpicked/2026-10-11_delete-and-rename.md:L9`, `L25` | repaired at `5d7657923` | `trail/2026-10-07_status-moves/seed.md:L17-L20` (all ticked) |
| A stale line pointer | `unpicked/2026-10-11_project-summary.md:L20` | repaired at `5d7657923` | `products/tracker17/web/pages.py:L934` |

The journey-link check found no dead pointer before or after the edits; the one malformed triple it lists is in another project's finding and is that finding's own subject (`docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md`).

## Held and refused

None. The product chain is not in flight: its state reads `"ended": "settled"` (`system/logs/chain-tracker17-state.json`), and the product has no live `*_open_issues.md`.
