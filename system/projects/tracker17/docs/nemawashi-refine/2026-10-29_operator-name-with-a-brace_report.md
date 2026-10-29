# 根回し Nemawashi refine — `2026-10-29_operator-name-with-a-brace`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-10-29_operator-name-with-a-brace` at `418f71e31`,
and the pool re-read behind it, 2026-10-29. The slug came from the caller: "answering the retired seed 2026-10-29_operator-name-with-a-brace". The run was the launched `principal-pm` subagent.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | cut from the product's documents | Principal PM | `<CORE>/launchers/skill/launcher.sh seeds-from-product-docs tracker17` | — | The docs cut |
| 2 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh nemawashi-pick tracker17` | 1 | the pool |
| 3 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 2 | row 2 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 3 | row 3 |

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-10-29_operator-name-with-a-brace #1` — retire this seed once its station closes | ignored | none | Answered by the retire that already happened. | `418f71e31` |
| `2026-10-29_operator-name-with-a-brace #2` — the start tests fail when the suite is launched with SIGINT ignored | cut from an idea | `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint` cut, `4d129a071`; the cut's report carries all three ask lines | Test-harness work no product document should state, and no candidate carries it. Re-measured: one case passes in the foreground, times out in the background. | `trail/2026-10-29_operator-name-with-a-brace/2026-10-29_operator-name-with-a-brace_recommendations.md:L15-L20`; `system/projects/tracker17/docs/seeds-from-idea/2026-10-29_start-tests-under-ignored-sigint_report.md`; clone at `418f71e31`: `3 passed in 0.87s` foreground, `1 failed in 30.17s` background |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-10-11_protect-saved-data` | kept | — | Still unbuilt and still advances **Works** for the PRD's failure states; the walk touched nothing it says, and its cited stop is still at its lines. | `products/tracker17/main.py:L41-L48`; `grep -rn 'fcntl\|flock' products/tracker17` matches only `docs/` |
| `2026-10-29_start-tests-under-ignored-sigint` | kept | — | Cut by this run. | `4d129a071` |

## The docs cut

Owed: the previous refine named it for NFDR QC-7 ("every submission is answered by sending the browser to a page address") and it has not run since (last `seeds-from-product-docs` commit is `<a commit not in the public history>`, 2026-10-11). Add task and Rename still answer the not-found page directly, and no candidate carries them (`products/tracker17/docs/nfdr.md:L73-L77`; `products/tracker17/web/routes.py:L869-L871`, `:L900-L902`).

## Found while reading

None. `check_journey_links.py` found no dead pointer before or after; its one malformed triple is the subject of an existing finding, `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md`.

## Held and refused

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null`; the change chain ended `sealed` on this unit.
