# 根回し Nemawashi refine — `2026-10-11_protect-saved-data`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-10-11_protect-saved-data` at `4f686e56c`,
and the pool re-read behind it, 2026-10-30. The slug came from the caller: "answering the retired seed 2026-10-11_protect-saved-data".*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | cut from the product's documents | Principal PM | `<CORE>/launchers/skill/launcher.sh seeds-from-product-docs tracker17` | — | § The docs cut |
| 2 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh nemawashi-pick tracker17` | 1 | row 1 |
| 3 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 2 | row 2 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 3 | row 3 |

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-10-30_second-tracker-refusal` — Nothing to recommend. | read | none | The file carries no item. | `trail/2026-10-11_protect-saved-data/2026-10-30_second-tracker-refusal_recommendations.md:L8` |
| `2026-10-30_unreadable-data-page` — Nothing to recommend. | read | none | The file carries no item. | `trail/2026-10-11_protect-saved-data/2026-10-30_unreadable-data-page_recommendations.md:L8` |
| `2026-10-30_what-the-start-prints #1` — retire this seed once its last station closes | ignored | none | Answered by the retire that already happened. | `4f686e56c` (`retire: nemawashi/2026-10-11_protect-saved-data → trail/`); all three stations ticked, `trail/2026-10-11_protect-saved-data/seed.md:L19-L21` |

## Candidates

The pool is empty: `journey/nemawashi/unpicked/` holds only `.gitkeep`, and the seedbed root holds no seed.

## The docs cut

Owed: S-8 was walked before CONTENT gained its rule for a path holding a byte that is not text (`products/tracker17/docs/CONTENT.md:L135-L139`, `6effdff29`), so on such a location the start cannot write the console line or the page S-8 requires (`products/tracker17/docs/SDD.md:L1171-L1173`), and no candidate carries the repair. The rest of the documents' slices are walked; the pool is empty.

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| On a location holding a non-UTF-8 byte, the unreadable-data page raises instead of serving, and the start's lines cannot be encoded; no test covers it | `products/tracker17/web/routes.py:L1346`; `products/tracker17/main.py:L161-L173` | Named as the docs cut, next move 1; a defect in the product against a settled rule, so no document is owed a change | `web.UnreadableSite(os.fsdecode(b'/tmp/caf\xe9/data'), '127.0.0.1:8017')` raised `UnicodeEncodeError`; `main._unreadable_line` on that path gave text whose `.encode('utf-8')` raised the same; `git grep xe9 -- products/tracker17/tests` printed nothing |

The journey-link check found no dead pointer; its one malformed triple is the satellite triple `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md` already records.

## Held and refused

None. The definition chain ended `settled` and the change chain `sealed` (`system/logs/chain-tracker17-state.json`, `system/logs/chain-change-tracker17-state.json`), and the product has no live companion.
