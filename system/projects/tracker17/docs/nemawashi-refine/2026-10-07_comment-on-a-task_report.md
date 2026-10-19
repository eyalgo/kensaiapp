# 根回し Nemawashi refine — `2026-10-07_comment-on-a-task`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-10-07_comment-on-a-task`, and the pool re-read behind it, 2026-10-19. No retire commit is in this clone's history: the seed reaches `trail/` in `e77c12b` ("KensaiApp 0.1.0"), the one commit that touches the trail (`git log -- system/projects/tracker17/journey/nemawashi/trail/`). The slug came from the caller: "answering the retired seed 2026-10-07_comment-on-a-task". Run in a `principal-pm:` session.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh nemawashi-pick tracker17` | — | Candidates (five in `unpicked/`, seedbed root empty) |
| 2 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 1 | row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 2 | row 2 |

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-10-12_operator-name` — "Nothing to recommend." | read | none | Carries no item. | `trail/2026-10-07_comment-on-a-task/2026-10-12_operator-name_recommendations.md:L8` |
| `2026-10-12_comments-on-the-page` — "Nothing to recommend." | read | none | Carries no item. | `trail/2026-10-07_comment-on-a-task/2026-10-12_comments-on-the-page_recommendations.md:L8` |
| `2026-10-13_full-volume-run #1` — retire this seed once its last station closes | ignored | none | The retire it asks for already happened, on this seed: all three stations are ticked and the seed is in `trail/`. | `trail/2026-10-07_comment-on-a-task/2026-10-13_full-volume-run_recommendations.md:L8-L13`; `trail/2026-10-07_comment-on-a-task/seed.md:L17-L19` |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-10-07_status-moves` | kept | — | SDD S-4 still owed; the walk added comments, not the workflow. | `ls products/tracker17/domain/workflow.py` → missing |
| `2026-10-11_delete-and-rename` | kept | — | SDD S-7 still owed. Its preference to follow `comment-on-a-task` is now met, which its text already allows for. | `grep -rn -i "def .*delete\|rename" products/tracker17/web products/tracker17/application` → no match; `unpicked/2026-10-11_delete-and-rename.md:L9`, `L25` |
| `2026-10-11_narrow-and-sort` | kept | — | SDD S-5 still owed. | `ls products/tracker17/domain/filtering.py products/tracker17/domain/sorting.py` → both missing |
| `2026-10-11_project-summary` | modified | page-title pointer `web/pages.py:L541` → `L630`, `db99277` | The cited line moved as the comments slice grew the file; the claim (title is the bare project name) still holds. | `products/tracker17/web/pages.py:L630` `_document(f"{project.name} - tracker17", body)`; `ls products/tracker17/domain/summary.py` → missing |
| `2026-10-11_protect-saved-data` | kept | — | SDD S-8 still owed; the cited start path is unchanged and no lock exists in code. | `products/tracker17/main.py:L41-L48`; `grep -rln 'fcntl\|flock' products/tracker17` → only `docs/trail/sdd/self_answer-2.md` |

All five are read on the Agari alone: `system/michi.md` is still the placeholder (`system/michi.md:L11-L14`), the one case the Michi check is skipped (`<CORE>/prompts/principal_pm_cut_seeds.md` § *The Michi is checked on every seed, and a seed says which Way it serves*). Each still moves the Agari's **Works** bar (`system/projects/tracker17/agari.md:L22-L24`).

## The docs cut

Not owed: the SDD's eight slices are S-1 to S-8 (`products/tracker17/docs/SDD.md:L648-L955`); S-1, S-2 and S-3 are walked (`trail/2026-10-07_first-project`, `trail/2026-10-07_tasks-in-a-project`, `trail/2026-10-07_comment-on-a-task`), S-4 to S-8 are each carried by one candidate above, and no companion item was written.

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| Moved line pointer | `unpicked/2026-10-11_project-summary.md:L20` | repaired at `db99277` | `products/tracker17/web/pages.py:L630` |
| Every candidate names the Way `fit-to-publish`, and four rank it under a "Way 5", but this instance's Michi declares no Way | `unpicked/*.md:L5` | filed in `docs/findings/` at `6b28746` | `system/michi.md:L11-L14`; `2026-10-07_first-project_report.md:L29` cites the Ways at a `michi.md:L32` this clone does not have |

The journey-link check found no dead pointer before the moves or after them (`check_journey_links.py --repo .` → "every pointer in the live seedbeds, docs/findings/ and product docs/ resolves").

## Held and refused

None. No `system/logs/chain-tracker17-state.json` exists, so no chain is in flight; `find products/tracker17/docs -name '*_open_issues.md'` finds no live companion.
