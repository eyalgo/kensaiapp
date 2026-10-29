# 根回し Nemawashi refine — `2026-10-11_delete-and-rename`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-10-11_delete-and-rename` at `7dc28c5f4`,
and the pool re-read behind it, 2026-10-29. The slug came from the caller: "answering the retired seed 2026-10-11_delete-and-rename". The run was a `principal-pm:` session invoking the skill, not the launched subagent.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | cut from the product's documents | Principal PM | `<CORE>/launchers/skill/launcher.sh seeds-from-product-docs tracker17` | — | `2026-10-28_deleted-project-redirect #1` |
| 2 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh nemawashi-pick tracker17` | 1 | the pool |
| 3 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 2 | row 2 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 3 | row 3 |

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-10-28_delete-a-task` — "Nothing to recommend." | — | read | Nothing to answer. | `trail/2026-10-11_delete-and-rename/2026-10-28_delete-a-task_recommendations.md:L9` |
| `2026-10-28_rename-a-project #1` — an operator name holding a curly brace breaks the People page | cut from an idea | `tracker17 · nemawashi · 2026-10-29_operator-name-with-a-brace` cut, `9a83b1b8b`; the cut's report carries all three ask lines | A code defect in a walked feature for one kind of input; no document states braces, so a docs cut would not draw it, and no candidate carries People. Still present: `.format` over a line holding the escaped name. | `products/tracker17/web/pages.py:L2819-L2829`; `system/projects/tracker17/docs/seeds-from-idea/2026-10-29_operator-name-with-a-brace_report.md` |
| `2026-10-28_delete-a-project` — "Nothing to recommend." | — | read | Nothing to answer. | `trail/2026-10-11_delete-and-rename/2026-10-28_delete-a-project_recommendations.md:L9` |
| `2026-10-28_deleted-project-redirect #1` — a submission whose route number cannot be read as an identity is answered by a redirect | docs cut | named as next move 1 | NFDR QC-7 already states the rule ("every submission is answered by sending the browser to a page address"); Add task and Rename still answer the not-found page directly. No candidate carries it. | `products/tracker17/docs/nfdr.md:L73-L77`; `products/tracker17/web/routes.py:L869-L871`, `:L900-L902` |
| `2026-10-28_task-delete-full-size-confirm #1` — retire `delete-and-rename` once its last station closes | ignored | none | Answered by the retire that already happened. | `7dc28c5f4` |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-10-11_protect-saved-data` | kept | — | Still unbuilt and still advances **Works** for the PRD's failure states; the walk touched nothing it says. Its cited stop is still at the lines it names, and its one journey pointer is already a triple. | `products/tracker17/main.py:L41-L48`; `grep -rn 'fcntl\|flock' products/tracker17` matches only `docs/` |
| `2026-10-29_operator-name-with-a-brace` | kept | — | Cut by this run. | `9a83b1b8b` |

## The docs cut

Owed: NFDR QC-7 states the redirect for every submission and no candidate carries the routes that still answer 404 directly (`products/tracker17/docs/nfdr.md:L73-L77`, `products/tracker17/web/routes.py:L869-L871`). The SDD's slices other than S-8 are walked, and S-8 is carried by `protect-saved-data`.

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| The rename recommendation cites `pages.py:L2673-L2684`; the code has since moved to L2819-L2829 | `trail/2026-10-11_delete-and-rename/2026-10-28_rename-a-project_recommendations.md:L12` | Not edited (`trail/` is never written); the new seed and its brief cite the current lines | `grep -n 'paragraph.format' products/tracker17/web/pages.py` |

No dead journey pointer: `check_journey_links.py` reported every pointer resolving, before and after the cut. Its one malformed triple is a satellite's, in `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md`, already filed.

## Held and refused

None. The product chain is not in flight (`system/logs/chain-tracker17-state.json`: `"ended": "settled"`), and no `*_open_issues.md` companion is live in `products/tracker17/docs/`.
