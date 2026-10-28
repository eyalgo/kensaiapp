# 根回し Nemawashi refine — `2026-10-11_narrow-and-sort`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-10-11_narrow-and-sort` at `1e057fb03`, and the pool re-read behind it, 2026-10-28. The slug came from the caller: "answering the retired seed 2026-10-11_narrow-and-sort". Run in a `principal-pm:` session.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | cut from the product's documents | Principal PM | `<CORE>/launchers/skill/launcher.sh seeds-from-product-docs tracker17` | — | `2026-10-28_all-tasks-list #2` |
| 2 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh nemawashi-pick tracker17` | 1 | Candidates (three in `unpicked/`, seedbed root empty) |
| 3 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 2 | row 2 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 3 | row 3 |

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-10-27_project-list-filter` — "Nothing to recommend." | read | none | Carries no item. | `trail/2026-10-11_narrow-and-sort/2026-10-27_project-list-filter_recommendations.md:L8` |
| `2026-10-27_project-list-sort` — "Nothing to recommend." | read | none | Carries no item. | `trail/2026-10-11_narrow-and-sort/2026-10-27_project-list-sort_recommendations.md:L8` |
| `2026-10-28_all-tasks-list #1` — retire this seed once its last station closes | ignored | none | The retire it asks for already happened, on this seed: all three stations are ticked and the seed is in `trail/`. | `trail/2026-10-11_narrow-and-sort/2026-10-28_all-tasks-list_recommendations.md:L8-L14`; `trail/2026-10-11_narrow-and-sort/seed.md:L17-L19`; `1e057fb03` |
| `2026-10-28_all-tasks-list #2` — cut a seed: the out-of-date refusal on a project's list and the task page states the status and claims no change | docs cut | none here; row 1 names the cut | The SDD already states the work: S-4's bar has the refusal state the current status and its moves and claim no change. The product's line on a project's list and the task page still says "has changed to", and no candidate carries it. Nothing is owed to a document, so no companion. | `products/tracker17/docs/SDD.md:L907-L911`; `products/tracker17/docs/CONTENT.md:L213`; `products/tracker17/web/pages.py:L804-L809` (`_CHANGED`); `grep -rn -i 'has changed to' system/projects/tracker17/journey/nemawashi/unpicked` → no match |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-10-11_delete-and-rename` | modified | `9b1080528`: `confirm_strip` pointer `web/pages.py:L662` → `L699` | The line moved as the narrow-and-sort slice grew the file. SDD S-7 is still owed, and nothing else the candidate says changed. | `products/tracker17/web/pages.py:L699` `def confirm_strip(`; `grep -rn -i "def .*delete\|def .*rename" products/tracker17/web products/tracker17/application` → no match |
| `2026-10-11_project-summary` | modified | `9b1080528`: page-title pointer `web/pages.py:L934` → `L1506`; CONTENT's page-title rule `L354-L357` → `L378-L381`; the relation line now says narrow-and-sort is walked | Both lines moved. Its one dependency is now met, so the filtered lists its counts link into exist. SDD S-6 is still owed. | `products/tracker17/web/pages.py:L1506`; `products/tracker17/docs/CONTENT.md:L378-L381`; `ls products/tracker17/domain/summary.py` → missing |
| `2026-10-11_protect-saved-data` | kept | — | SDD S-8 is still owed. The cited start path is unchanged, and the code still has no lock. | `products/tracker17/main.py:L41-L48`; `grep -rln 'fcntl\|flock' products/tracker17` → only `docs/trail/sdd/self_answer-2.md` |

## The docs cut

Owed. The SDD states work that no candidate carries: S-4's out-of-date refusal claims no change (`products/tracker17/docs/SDD.md:L907-L911`), but on a project's list and the task page the product still says "has changed to" (`products/tracker17/web/pages.py:L804-L809`). SDD slices S-1 to S-5 are walked, and S-6 to S-8 each have one candidate above.

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| A stale line pointer | `unpicked/2026-10-11_delete-and-rename.md:L25` | repaired at `9b1080528` | `products/tracker17/web/pages.py:L699` |
| Two stale line pointers | `unpicked/2026-10-11_project-summary.md:L20` | repaired at `9b1080528` | `products/tracker17/web/pages.py:L1506`; `products/tracker17/docs/CONTENT.md:L378-L381` |

The journey-link check found no dead pointer. The one malformed triple it lists is in another project's finding, and that triple is the finding's own subject (`docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md`).

## Held and refused

None. The product chain is not in flight: its state reads `"ended": "settled"` (`system/logs/chain-tracker17-state.json`), and the product has no live `*_open_issues.md`.
