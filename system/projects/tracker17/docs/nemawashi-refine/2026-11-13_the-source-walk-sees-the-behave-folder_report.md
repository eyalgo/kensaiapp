# 根回し Nemawashi refine — `2026-11-13_the-source-walk-sees-the-behave-folder`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-11-13_the-source-walk-sees-the-behave-folder` at `b42ec1825`,
and the pool re-read behind it, 2026-11-13. The slug came from the caller: "answering the retired seed 2026-11-13_the-source-walk-sees-the-behave-folder". Run in a Principal PM session.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh seed-pick tracker17` | — | Candidates: two in the pool, the root empty |
| 2 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 1 | row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/walk/launcher.sh tracker17` | 2 | row 2; neither candidate holds a station only the owner walks |

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-11-13_behave-import-walk #1` — retire this seed once its last station closes | ignored | none | The retire it asks for already happened | `b42ec1825` `retire: nemawashi/2026-11-13_the-source-walk-sees-the-behave-folder → trail/` |
| `2026-11-13_walk-skips-by-name #1` — cut a seed for the full-run timing failure of the ignored-SIGINT test | cut from an idea | `seeds-from-idea` wrote `tracker17 · nemawashi · 2026-11-13_the-ignored-sigint-test-holds-in-a-full-run`, at `f7a00f87f`; its report carries every ask line, nothing left for a later cut | A defect in the product's own gate that no document should state (NFR-11's quiet stop is already stated; its proof fails under load), and no seed carried it | `trail/2026-11-13_the-source-walk-sees-the-behave-folder/2026-11-13_walk-skips-by-name_recommendations.md:L8-L13`; `system/projects/tracker17/docs/seeds-from-idea/2026-11-13_the-ignored-sigint-test-fails-in-a-full-run_report.md` |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-11-13_one-fake-and-one-contract-suite-per-contract` | kept | — | Nothing the walk built touches QC-64's contracts, and its counts still hold | both refine reports' Considered rows; `ls tests/fakes.py` → no such file; the class grep → 64 (run from `products/tracker17`, today) |
| `2026-11-13_the-ignored-sigint-test-holds-in-a-full-run` | kept | — (cut by this run, `f7a00f87f`) | New; it carries recommendation `walk-skips-by-name #1` | `f7a00f87f` |

## The docs cut

Not owed: the NFDR's only entry still unmet is QC-64, which the kept candidate carries, and `what_left.md` reads "Nothing is left to build." (`products/tracker17/docs/nfdr.md:L356`, `:L1863`; `products/tracker17/docs/what_left.md:L5`).

## Found while reading

None. The journey-link check found no dead pointer before or after the cut; its one malformed triple is the satellite pointer already filed in `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md`.

## Held and refused

None. `system/logs/chain-tracker17-state.json` has `ended: settled`, `pending: null`, and no `*_open_issues.md` is live under `products/tracker17/docs/`.
