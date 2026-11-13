# 根回し Nemawashi refine — `2026-11-13_the-pins-test-reads-the-behave-lock`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-11-13_the-pins-test-reads-the-behave-lock` at `3c6a56cda`,
and the pool re-read behind it, 2026-11-13. The slug came from the caller: "invoke the nemawashi-refine skill for the tracker17 project, answering the retired seed 2026-11-13_the-pins-test-reads-the-behave-lock". Run in a `principal-pm:` session.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh seed-pick tracker17` | — | the seedbed root is empty; Candidates, both kept |
| 2 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 1 | row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/walk/launcher.sh tracker17` | 2 | row 2 — every station of both candidates is test code the chain walks |

No sweep is owed: this run wrote no companion item, and no product companion is live. No docs cut is owed (§ *The docs cut*).

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-11-13_pins-test-reads-behave-lock #1` — retire this seed once its one station closes | ignored | none | The retire it asks for has already happened: the station closed at `c0d970db5` and the seed was retired at `3c6a56cda`. | `trail/2026-11-13_the-pins-test-reads-the-behave-lock/2026-11-13_pins-test-reads-behave-lock_recommendations.md:L8-L13`; `git log -2` → `3c6a56cda retire: nemawashi/2026-11-13_the-pins-test-reads-the-behave-lock → trail/`, `c0d970db5 close shukuba: 2026-11-13_pins-over-behave → trail/, item 1 ticked` |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-11-13_one-fake-and-one-contract-suite-per-contract` | kept | — | QC-64 is still unmet, and the counts the seed gives still hold: 64 classes in 26 modules. The walk changed only `test_pins.py` and the NFDR's QC-39, neither of which this seed reads. Its link to the retired seed is a triple, so it still resolves. | `products/tracker17/docs/nfdr.md:L335`; `grep -rEn "^\s*class \w*(Clock\|Saver)\w*" tests --include='*.py' \| wc -l` → 64, `-l` → 26 (from `products/tracker17`, at `3c6a56cda`); `git diff --stat db8e9b81b HEAD -- products/tracker17/` → `nfdr.md`, two trail files, `test_pins.py` |
| `2026-11-13_the-source-walk-sees-the-behave-folder` | kept | — | QC-1 still starts unmet in its test. `SourceWalk._all` still skips every dot-folder at the lines the seed cites, and the walk did not touch `conftest.py` or `test_shapes.py`. | `products/tracker17/docs/nfdr.md:L44`; `products/tracker17/tests/conftest.py:L138-L146`; the same `git diff --stat` |

## The docs cut

Not owed. The documents still hold two unmet entries, QC-1/QC-19 and QC-64, and each is carried by a kept candidate. QC-39 is now met (`products/tracker17/docs/nfdr.md:L436-L438`, NFDR v29 at `a2e1f56c4`). `products/tracker17/docs/what_left.md:L5` reads "Nothing is left to build." The other "unmet" lines that `grep -n -i unmet` finds in `nfdr.md` and `SDD.md` are dated Review Notes, already answered (for example RN-52, `nfdr.md:L1559-L1560`).

## Found while reading

None. `check_journey_links.py` found every pointer resolving. The one malformed triple it reports, in `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md`, is that finding's own subject: it is already filed, and it is not a dead pointer.

## Held and refused

None. `system/logs/chain-tracker17-state.json` → `ended: settled`, so no chain is in flight. No product companion is live: `find products/tracker17/docs -name '*_open_issues.md' -not -path '*/trail/*'` → nothing. The walk's one companion item (`39d50fd15`) was answered at `85b8a2017` and folded at `a2e1f56c4`.
