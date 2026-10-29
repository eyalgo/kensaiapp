# 根回し Nemawashi refine — `2026-10-29_start-tests-under-ignored-sigint`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-10-29_start-tests-under-ignored-sigint` at `879300061`,
and the pool re-read behind it, 2026-10-29. The slug came from the caller: "answering the retired seed 2026-10-29_start-tests-under-ignored-sigint".*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | cut from the product's documents | Principal PM | `<CORE>/launchers/skill/launcher.sh seeds-from-product-docs tracker17` | — | `2026-10-29_the-start-is-stoppable-from-its-ready-line #2` |
| 2 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh nemawashi-pick tracker17` | 1 | the pool (`protect-saved-data`, plus what row 1 adds) |
| 3 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 2 | row 2 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 3 | row 3 |

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-10-29_start-tests-under-ignored-sigint` — Nothing to recommend. | read | none | The file carries no item. | `trail/2026-10-29_start-tests-under-ignored-sigint/2026-10-29_start-tests-under-ignored-sigint_recommendations.md:L8` |
| `2026-10-29_ignored-sigint-proof-test #1` — retire this seed once its station closes | ignored | none | Answered by the retire that already happened. | `879300061`; `fdfc8e4a8` closed the station |
| `2026-10-29_the-start-is-stoppable-from-its-ready-line #1` — the same retire | ignored | none | Follows the row above: the same ask, already answered by `879300061`. | `…_the-start-is-stoppable-from-its-ready-line_recommendations.md:L8-L13` |
| `2026-10-29_the-start-is-stoppable-from-its-ready-line #2` — move the suite to the uv environment | docs cut | named as next move 1 | The SDD and NFDR already state the move and no candidate carries it, so no document is owed a change. | `products/tracker17/docs/SDD.md:L2838-L2840` (the README's suite section and `tests/requirements.txt` "are the product's to move"); `products/tracker17/docs/nfdr.md:L355-L360` (QC-39 "starts unmet"); `products/tracker17/README.md:L95-L99` still `venv` + `pip`; `ls products/tracker17/uv.lock` → no such file |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-10-11_protect-saved-data` | modified | line pointer `main.py:L41-L48` → `main.py:L104-L113`, `3c56c7f07` | Still owed and still advances **Works**; only its pointer had drifted, as those lines now hold the `Serving` protocol. | `products/tracker17/main.py:L104-L113`; no `fcntl`/`flock` outside `docs/trail/`; no `UnreadableData` in `web/` or `application/`; SDD § 6 S-8 at `products/tracker17/docs/SDD.md:L1125` |

## The docs cut

Owed: the SDD § 4 RT-4 and NFDR QC-39 uv move is work the documents state and no candidate carries (`products/tracker17/docs/SDD.md:L2838-L2840`, `products/tracker17/docs/nfdr.md:L355-L360`).

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| A stale line pointer in a candidate | `journey/nemawashi/unpicked/2026-10-11_protect-saved-data.md:L7` | repaired at `3c56c7f07` | `products/tracker17/main.py:L104-L113` |

The journey-link check found no dead pointer. Its one malformed triple is a satellite triple in `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md`, which that finding already records.

## Held and refused

None. The definition chain ended `settled` (`system/logs/chain-tracker17-state.json`), and the product has no live companion.
