# 根回し Nemawashi refine — `2026-10-07_first-project`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-10-07_first-project` at `bccbb22f5`,
and the pool re-read behind it, 2026-10-11. The slug came from the caller: "invoke the nemawashi-refine skill for the tracker17 project, answering the retired seed 2026-10-07_first-project". Run as the `principal-pm` run.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | cut from the product's documents | Principal PM | `<CORE>/launchers/skill/launcher.sh seeds-from-product-docs tracker17` | — | The docs cut, below: SDD S-5 to S-8 carried by no candidate |
| 2 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh nemawashi-pick tracker17` | 1 | Seedbed root empty; three candidates kept |
| 3 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 2 | The pick |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 3 | The route cut |

No companion sweep: this run wrote no companion item, `find products/tracker17/docs -name '*_open_issues.md'` lists none, and the product chain ended `settled` (`system/logs/chain-tracker17-state.json`, `"ended": "settled"`).

## Recommendations

Six files read as "Nothing to recommend.": `2026-10-07_a-not-found-page`, `2026-10-07_address-taken-start-message`, `2026-10-07_create-a-project-that-stays`, `2026-10-07_reverse-pointer-test`, `2026-10-08_setup-instructions`, `2026-10-10_readme-content-rules` (each `_recommendations.md:L8`).

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-10-11_readme-linux-setup-and-git #1` — retire `tracker17 · nemawashi · 2026-10-07_first-project` once its last station closes | ignored | none | It names this seed, and the retire it asks for already happened. | `trail/2026-10-07_first-project/2026-10-11_readme-linux-setup-and-git_recommendations.md:L8-L13`; `bccbb22f5` |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-10-07_tasks-in-a-project` | modified | § Source's product check refreshed to 2026-10-11: the four parts exist, none of the slice's five `domain/*.py` files does — `b9ae519be` | Its line said no `domain/`, `application/`, `persistence/` or `web/` exists. first-project built all four, so the line was false. The idea itself still stands: SDD S-2, Agari **Works**/**Simple to read**, Way `fit-to-publish`. | `unpicked/2026-10-07_tasks-in-a-project.md:L13`; `ls products/tracker17/domain` → `__init__.py projects.py refusals.py state.py text.py`; `system/michi.md:L32` |
| `2026-10-07_comment-on-a-task` | modified | § Source's product check refreshed to 2026-10-11; `domain/comments.py` still absent — `b9ae519be` | Its line said no `domain/` exists. That stopped being true when first-project landed. The slice (SDD S-3) is still owed. | `unpicked/2026-10-07_comment-on-a-task.md:L13`; same `ls` |
| `2026-10-07_status-moves` | modified | § Source's product check refreshed to 2026-10-11; `domain/workflow.py` still absent — `b9ae519be` | Its line said no `domain/` exists. That stopped being true when first-project landed. The slice (SDD S-4) is still owed. | `unpicked/2026-10-07_status-moves.md:L13`; same `ls` |

## The docs cut

Owed. The SDD sets four slices that no candidate carries: S-5 narrow-and-sort, S-6 project-summary, S-7 delete-and-rename and S-8 protect-saved-data (`products/tracker17/docs/SDD.md:L842`, `:L878`, `:L904`, `:L941`). `products/tracker17/docs/what_left.md:L35-L46` still lists their PRD features as missing. The PRD (`PRD.md:L137`) and SRS (`SRS.md:L720-L723`) now carry the `critical` priority, which was added after the candidates were cut. The FDR v4 settled it at `2c82d3efd`. The cut reads the pool and adds only what is missing.

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| Dead journey pointer to first-project's old root folder, broken by the retire | `docs/findings/2026-10-11_tracker17-ships-in-the-release-and-names-what-must-not-ship.md:L64` | repaired to the triple `tracker17 · nemawashi · 2026-10-07_first-project` at `b9ae519be`; re-check: "every pointer … resolves" | `check_journey_links.py` before and after |
| Three candidates' stale "Product checked" claims | `unpicked/*.md:L13` | modified at `b9ae519be` (Candidates, above) | `ls products/tracker17` |
| A malformed satellite triple, which the check does not count as dead | `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md` | left as it is. It is that finding's own subject and not a tracker17 pointer. | `check_journey_links.py` output |

## Held and refused

None.
