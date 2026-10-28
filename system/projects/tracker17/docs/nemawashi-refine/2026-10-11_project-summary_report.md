# 根回し Nemawashi refine — `2026-10-11_project-summary`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-10-11_project-summary` at `5da66b7c7`,
and the pool re-read behind it, 2026-10-28. The slug came from the caller: "invoke the nemawashi-refine skill for the tracker17 project, answering the retired seed 2026-10-11_project-summary". Run in a `principal-pm:` session.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh nemawashi-pick tracker17` | — | Candidates: `delete-and-rename`, `protect-saved-data` |
| 2 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 1 | row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 2 | row 2 |

No companion sweep: no companion item was written and none is live. No docs cut: see below. Whichever
candidate is picked, its first station is product work the chain walks, so the walk row stands for
either.

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-10-28_linked-counts #1` — retire `project-summary` once its last station closes | ignored | none | Already answered: the Scrum Master's retire filed this seed in `trail/` | `2026-10-28_linked-counts_recommendations.md:L8-L13`; retire commit `5da66b7c7` |
| `2026-10-28_summary-page` — "Nothing to recommend." | read | none | Contributes no item | `2026-10-28_summary-page_recommendations.md:L8` |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-10-11_delete-and-rename` | modified | `confirm_strip` pointer `web/pages.py:L699` → `L701`, at `833ecdc5d` | Still SDD § 6 S-7, still unbuilt, still advances **Works**; only the line it cited moved | `products/tracker17/web/pages.py:L701`; `products/tracker17/docs/what_left.md:L5-L10`; `grep -rn -i 'def .*rename\|def .*delete' web application` → nothing |
| `2026-10-11_protect-saved-data` | kept | — | Still SDD § 6 S-8 and unbuilt; its code pointer still holds; the walk's deferred unreadable-data page for the Summary is already its `unreadable-data-page` station's "every address" | `products/tracker17/main.py:L41-L48`; `grep -rln 'fcntl\|flock'` → only `docs/trail/sdd/self_answer-2.md`; `2026-10-28_linked-counts_report.md:L49` |

## The docs cut

Not owed: the SDD has eight slices, S-1 to S-6 are walked and in `trail/`, and S-7 and S-8 are the two
candidates, so the pool carries the documents' remaining work; no companion was written
(`products/tracker17/docs/SDD.md:L724-L1040`; `journey/nemawashi/trail/` listing).

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| Stale line pointer | `unpicked/2026-10-11_delete-and-rename.md:L25` | repaired at `833ecdc5d` | `grep -n 'def confirm_strip' web/pages.py` → `701` |

The journey-link check found no dead pointer before or after the run; its one malformed-triple note is
an existing finding (`docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md`), not this
project's.

## Held and refused

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null`; no live
`*_open_issues.md` under `products/tracker17/docs/`.
