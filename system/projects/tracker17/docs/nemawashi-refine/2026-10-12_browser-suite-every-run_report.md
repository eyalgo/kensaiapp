# 根回し Nemawashi refine — `2026-10-12_browser-suite-every-run`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-10-12_browser-suite-every-run` at `3ae47114c`,
and the pool re-read behind it, 2026-10-12. The slug came from the caller: "answering the retired seed 2026-10-12_browser-suite-every-run". Run as the launched `principal-pm` agent.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh nemawashi-pick tracker17` | — | Candidates (six in `unpicked/`, seedbed root empty) |
| 2 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 1 | row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 2 | row 2 |

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-10-12_browser-suite-every-run #1` — retire this seed once its one station closes | ignored | none | The retire it asks for already happened, on this seed. | `trail/2026-10-12_browser-suite-every-run/2026-10-12_browser-suite-every-run_recommendations.md:L8-L13`; `3ae47114c` |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-10-07_comment-on-a-task` | kept | — | SDD S-3 still owed; the walk changed only e2e test observation. | `ls products/tracker17/domain` has no `comments.py`; walk diff = four e2e modules (`trail/…/2026-10-12_browser-suite-every-run_report.md:L48`) |
| `2026-10-07_status-moves` | kept | — | SDD S-4 still owed. | `ls products/tracker17/domain` has no `workflow.py` |
| `2026-10-11_delete-and-rename` | kept | — | SDD S-7 still owed; the grep's only hit is the HTTP method dispatcher, not a rename or delete action. | `grep -rn -i "rename\|delete" web application` → `web/listener.py:53` (`do_DELETE = … _serve`) only |
| `2026-10-11_narrow-and-sort` | kept | — | SDD S-5 still owed. | `ls domain/filtering.py domain/sorting.py` → both missing |
| `2026-10-11_project-summary` | modified | page-title pointer `web/pages.py:L467` → `L541`, `fdf999812` | The cited line moved; the claim (title is the bare project name) still holds. | `products/tracker17/web/pages.py:L541` `_document(f"{project.name} - tracker17", body)` |
| `2026-10-11_protect-saved-data` | kept | — | SDD S-8 still owed; the cited start path is unchanged. | `products/tracker17/main.py:L41-L48`; `grep -rln 'fcntl\|flock'` → only `docs/trail/sdd/self_answer-2.md` |

## The docs cut

Not owed: the SDD's eight slices are S-1 to S-8 (`products/tracker17/docs/SDD.md:L648-L955`), S-1 and S-2 are walked (`trail/2026-10-07_first-project`, `trail/2026-10-07_tasks-in-a-project`), and S-3 to S-8 are each carried by one candidate above; no companion item was written.

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| Moved line pointer | `unpicked/2026-10-11_project-summary.md:L20` | repaired at `fdf999812` | `web/pages.py:L541` |
| Malformed satellite triple reported by the link check | `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md` | none — it is that finding's own subject, already filed | `check_journey_links.py --repo .` → 0 dead, 1 malformed |

## Held and refused

None. `system/logs/chain-tracker17-state.json` reads `ended: "settled"`, `pending: null`; no live `*_open_issues.md` under `products/tracker17/docs`.
