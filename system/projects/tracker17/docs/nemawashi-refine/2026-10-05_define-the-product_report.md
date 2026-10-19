# 根回し Nemawashi refine — `2026-10-05_define-the-product`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-10-05_define-the-product`
at `084b7f614`, and the pool re-read behind it, 2026-10-07. The slug came from the caller: "answering
the retired seed 2026-10-05_define-the-product". The run was a `principal-pm:` session.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | cut from the product's documents | Principal PM | `core/launchers/skill/launcher.sh seeds-from-product-docs tracker17` | — | The docs cut |
| 2 | pick a seed | PM | `core/launchers/skill/launcher.sh nemawashi-pick tracker17` | 1 | the empty pool |
| 3 | cut the route | PM | `core/launchers/skill/launcher.sh stations-from-seed tracker17` | 2 | row 2 |
| 4 | walk the next change | owner | `core/launchers/chain-change/launcher.sh tracker17` | 3 | row 3 |

## Recommendations

The retired seed is a file, `trail/2026-10-05_define-the-product.md`. No `shukuba-refine` run wrote into
it, so it carries no recommendations.

## Candidates

`unpicked/` holds only `.gitkeep`, so there is no candidate to keep, modify or drop. The seedbed root is
empty too (`ls journey/nemawashi/`: `README.md drop trail unpicked`).

## The docs cut

**Owed.** The pool is empty, and the documents hold the whole build. The SDD, FDR and NFDR read
`**Status:** Settled` (`products/tracker17/docs/SDD.md:L3`, `fdr.md:L3`, `nfdr.md:L3`), nine ADRs sit in
`docs/adr/`, and `products/tracker17/` holds no code yet. No live `*_open_issues.md` remains, so no
companion sweep is owed. The foundation seed the retired seed promised
(`trail/2026-10-05_define-the-product.md`, § *This seed ends at the SDD*) is not owed either: the product
chain already authored the FDR, the ADRs and the NFDR on its spine (`system/logs/chain-tracker17-state.json`,
`"ended": "settled"`).

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| `product-card` has not run after the foundation step, and the refine's next-move list has no row that names it | `system/projects/tracker17/project.md:L12` (`**Languages:** <blank>`); no `products/tracker17/README.md` | filed in `docs/findings/` at `31e270c58`. The Principal PM's `core/launchers/product-card/launcher.sh tracker17` (which runs `product-skeleton` after it) belongs before row 4. | `core/doctrine/setup/kensaiapp_structure.md:L522-L529` |
| A malformed triple in a finding | `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md` | none. It is that finding's own example, and it is not a dead pointer. | `check_journey_links.py`: "every pointer … resolves", "1 malformed triple(s)" |

## Held and refused

None. The product chain ended `settled` and the change chain ended `halted` with nothing pending
(`system/logs/chain-tracker17-state.json`, `chain-change-tracker17-state.json`), so no chain is in flight.
