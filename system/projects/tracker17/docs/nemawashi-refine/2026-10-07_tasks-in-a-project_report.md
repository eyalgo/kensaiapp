# 根回し Nemawashi refine — `2026-10-07_tasks-in-a-project`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-10-07_tasks-in-a-project` at `ad8d6b151`, and the pool re-read behind it, 2026-10-12. The slug came from the caller: "invoke the nemawashi-refine skill for the tracker17 project, answering the retired seed 2026-10-07_tasks-in-a-project".*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh nemawashi-pick tracker17` | — | the pool of seven candidates; the seedbed root is empty |
| 2 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 1 | the pick |
| 3 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 2 | the route cut |

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-10-11_add-and-list-tasks #1` — cut a seed that makes the browser suite pass on every run | cut from an idea | `seeds-from-idea` wrote `tracker17 · nemawashi · 2026-10-12_browser-suite-every-run`, `b1ad03462` | This is test-reliability work owned by tracker17. No product document states it, and no candidate carries it. Re-measured at HEAD: 6 green runs of 8 | `…/2026-10-11_add-and-list-tasks_recommendations.md:L8-L13`; `grep -i 'flak\|determinis\|intermittent'` over `products/tracker17/docs` → nothing; 8 × `pytest products/tracker17/tests/e2e/` on a `git archive a041368b6` copy → 6 × `27 passed`, 2 failed runs |
| `2026-10-11_edit-task-fields #1` — the same cut | cut from an idea | Same seed, `b1ad03462` | Asks the same thing as `add-and-list-tasks #1`, so it gets the same answer | `…/2026-10-11_edit-task-fields_recommendations.md:L8-L13` |
| `2026-10-12_task-labels #2` — the same cut | cut from an idea | Same seed, `b1ad03462` | Asks the same thing as `add-and-list-tasks #1`, so it gets the same answer | `…/2026-10-12_task-labels_recommendations.md:L15-L20` |
| `2026-10-12_task-labels #1` — retire `tasks-in-a-project` once `task-labels` closes | ignored | none | It names this seed, so the retire at `ad8d6b151` already answered it | `…/2026-10-12_task-labels_recommendations.md:L8-L13`; `git log -1 --grep='^retire: nemawashi/2026-10-07_tasks'` → `ad8d6b151` |
| `2026-10-11_people-page-assignee-list` | — | none | Read. It says "Nothing to recommend." | `…/2026-10-11_people-page-assignee-list_recommendations.md:L8` |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-10-07_comment-on-a-task` | modified | Source line re-checked: the domain listing now includes the five files `tasks-in-a-project` added. `comments.py` is still missing. `a041368b6` | The listing was the one `first-project` left, so it was stale | `ls products/tracker17/domain`; `ls domain/comments.py` → no such file |
| `2026-10-07_status-moves` | modified | Same re-check. `workflow.py` is still missing. `a041368b6` | Same stale listing | `ls products/tracker17/domain/workflow.py` → no such file |
| `2026-10-11_narrow-and-sort` | kept | — | SDD S-5 is still owed. Its claim that `critical` comes from `tasks-in-a-project` holds | `domain/priorities.py:L29` `CRITICAL = "critical"`; `unpicked/2026-10-11_narrow-and-sort.md:L23` |
| `2026-10-11_project-summary` | kept | — | SDD S-6 is still owed, and `domain/summary.py` is missing | `unpicked/2026-10-11_project-summary.md:L13` |
| `2026-10-11_delete-and-rename` | kept | — | SDD S-7 is still owed. The walk added no rename or delete | `unpicked/2026-10-11_delete-and-rename.md:L13`; `products/tracker17/docs/what_left.md:L5-L10` |
| `2026-10-11_protect-saved-data` | kept | — | SDD S-8 is still owed. The `task-labels` review confirmed that this seed carries Gap 17 | `…/2026-10-12_task-labels_report.md:L49` |
| `2026-10-12_browser-suite-every-run` | kept | Cut in this run, `b1ad03462` | New this run | the recommendations above |

## The docs cut

Not owed. SDD § 6 has eight slices (`products/tracker17/docs/SDD.md:L648-L955`). S-1 and S-2 are in `trail/`, and S-3 to S-8 are each carried by a candidate above. No live `*_open_issues.md` asks for work (`find products/tracker17 -name '*_open_issues.md' -not -path '*/trail/*'` → nothing).

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| A stale domain listing in a candidate's Source line | `unpicked/2026-10-07_comment-on-a-task.md:L13`, `unpicked/2026-10-07_status-moves.md:L13` | repaired at `a041368b6` | `ls products/tracker17/domain` |

`check_journey_links.py`, run before and after: every pointer resolves. Its one malformed triple is in this instance's `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md`, which already records it.

## Held and refused

None. `system/logs/chain-tracker17-state.json` reads `"ended": "settled"`, so no chain is in flight.
