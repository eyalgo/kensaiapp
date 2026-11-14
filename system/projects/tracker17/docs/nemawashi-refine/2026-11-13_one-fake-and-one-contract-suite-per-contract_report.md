# 根回し Nemawashi refine — `2026-11-13_one-fake-and-one-contract-suite-per-contract`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-11-13_one-fake-and-one-contract-suite-per-contract` at `a2acd6045`,
and the pool re-read behind it, 2026-11-14. The slug came from the caller: "answering the retired seed 2026-11-13_one-fake-and-one-contract-suite-per-contract".*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | cut from the product's documents | Principal PM | `<CORE>/launchers/skill/launcher.sh seeds-from-product-docs tracker17` | — | The docs cut, below (NFDR QC-40) |
| 2 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh seed-pick tracker17` | 1 | the pool, empty until row 1 fills it |
| 3 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 2 | row 2 |
| 4 | walk the next change | owner | `<CORE>/launchers/walk/launcher.sh tracker17` | 3 | row 3 |

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-11-13_saver-fake-and-suite` — read | — | none | The file reads "Nothing to recommend." | `trail/2026-11-13_one-fake-and-one-contract-suite-per-contract/2026-11-13_saver-fake-and-suite_recommendations.md:L8` |
| `2026-11-14_clock-fake-and-suite #1` — retire this seed once its last station closes | ignored | none | The retire it asks for already landed, after the station's close at `45adbaead`. | `a2acd6045` `retire: nemawashi/2026-11-13_one-fake-and-one-contract-suite-per-contract → trail/` |

## Candidates

The pool is empty: `unpicked/` holds only `.gitkeep`, and the seedbed root holds no seed.

## The docs cut

Owed: the pool is empty, and NFDR QC-40 states work no candidate carries. That work is moving the Playwright pin off Chromium 158.0.8127.18 within 30 days of the 2026-11-11 advisories. The previous refine named this cut, and it has not run since. Both pins still read `playwright==1.65.1` (`products/tracker17/docs/nfdr.md:L485-L493`; `products/tracker17/pyproject.toml:L17`, `products/tracker17/.behave/pyproject.toml:L8`; `tracker17 · docs · nemawashi-refine · 2026-11-13_the-summary-shows-the-due-today-count_report.md`, § The docs cut; no `seeds-from-product-docs` commit under `system/projects/tracker17`). QC-64, the work of the seed just retired, now reads as met at NFDR version 33 (`nfdr.md:L5`), so the cut owes nothing for it. `what_left.md` reads "Nothing is left to build." (`L5`). It records what the code does against the finish line and the PRD, and it does not cover the NFDR's standing obligations.

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| A dead journey pointer: the three-part key named <another product built with KensaiApp>'s change, which lives in `<another instance of Eyal's>` | `docs/findings/2026-11-09_a-raised-item-is-not-carried-when-main-has-no-companion.md:L5-L6` | repaired to the four-part key at `<a commit not in the public history>` | `check_journey_links.py` before, 2 dead; the unit sits in that instance's `journey/tobiishi/trail/` |
| The same, for the QA finding | `docs/findings/2026-11-14_qa-is-sent-a-check-only-change-no-way-in-can-reach.md:L5-L6` | repaired to the four-part key at `<a commit not in the public history>` | the same check; the unit sits at that instance's `journey/tobiishi/` root |
| Two malformed triples (the check does not count them as dead) | `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md`; `product-development · nemawashi · 2026-11-03_shukuba-open-is-given-its-collaborators` | none: the first is the subject of that finding, which is already filed. The second is in another project's picked seed, and this run repairs only dead pointers there | `check_journey_links.py` after the repair: every pointer resolves, 2 malformed |

## Held and refused

None. The project's chain state reads `ended: settled` and the walk chain reads `ended: sealed`. No product companion is live (`ls products/tracker17/docs` shows no `*_open_issues.md`; NFDR version 33 removed the last one).
