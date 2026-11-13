# 根回し Nemawashi refine — `2026-10-30_a-path-with-a-non-text-byte-is-printed`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-10-30_a-path-with-a-non-text-byte-is-printed` at `ec2ddeff0`,
and the pool re-read behind it, 2026-11-13. The slug came from the caller: "answering the retired seed 2026-10-30_a-path-with-a-non-text-byte-is-printed".*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | cut from the product's documents | Principal PM | `<CORE>/launchers/skill/launcher.sh seeds-from-product-docs tracker17` | — | `2026-11-12_failed-action-path-non-text-byte #2`; the empty pool |
| 2 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh seed-pick tracker17` | 1 | row 1 |
| 3 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 2 | row 2 |

The table stops at the route cut: the pool is empty until row 1 lands, so whether the next station is
the chain's or the owner's turns on a seed that does not exist yet. The owner reads the route row 3
leaves and starts the walk, or walks the station.

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-10-30_ready-start-non-text-path` — Nothing to recommend. | read | none | The file carries no item. | `trail/2026-10-30_a-path-with-a-non-text-byte-is-printed/2026-10-30_ready-start-non-text-path_recommendations.md:L8` |
| `2026-10-30_unreadable-start-non-text-path` — Nothing to recommend. | read | none | The file carries no item. | `trail/2026-10-30_a-path-with-a-non-text-byte-is-printed/2026-10-30_unreadable-start-non-text-path_recommendations.md:L8` |
| `2026-11-12_failed-action-path-non-text-byte #1` — retire the non-text-path seed once its last station closes | ignored | none | It names this seed, and the retire it asks for has already happened. | `ec2ddeff0` (`retire: nemawashi/2026-10-30_a-path-with-a-non-text-byte-is-printed → trail/`); checklist all ticked, `trail/2026-10-30_a-path-with-a-non-text-byte-is-printed/seed.md:L17-L19` |
| `2026-11-12_failed-action-path-non-text-byte #2` — cut a seed for NFDR QC-64, one fake and one contract suite per contract | docs cut | named as next move 1 | The NFDR already states the work and says it starts unmet; no candidate carries it, and the pool is empty. It is product work a document states, so it is not cut from an idea here and no companion is owed. | `products/tracker17/docs/nfdr.md:L320-L340` (QC-64, "The entry starts unmet"); `test -e products/tracker17/tests/fakes.py` → absent; `git grep -lP '^\s+def (save\|now)\(' -- products/tracker17/tests \| wc -l` → 26 |

## Candidates

The pool is empty: `journey/nemawashi/unpicked/` holds no candidate, and the seedbed root holds none.

## The docs cut

Owed: the NFDR holds QC-64's work, which no candidate carries (`products/tracker17/docs/nfdr.md:L320-L340`), and the pool is empty after the retire.

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| None in this project. The journey-link check names one malformed triple, in a finding whose subject is that triple; it is a satellite pointer, already filed, and not tracker17's. | `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md` | none — already filed | `check_journey_links.py --repo <instance root>` → "every pointer … resolves"; "1 malformed triple(s) … not counted as dead" |

No product companion is live (`products/tracker17/docs/*_open_issues.md` → no match), so no sweep is owed.

## Held and refused

None. The product chain is not in flight: `system/logs/chain-tracker17-state.json` reads `"ended": "settled"`, "every spine document is settled".
