# 根回し Nemawashi refine — `2026-11-13_the-summary-shows-the-due-today-count`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-11-13_the-summary-shows-the-due-today-count` at `1654893c8`,
and the pool re-read behind it, 2026-11-14. The slug came from the caller: "answering the retired seed 2026-11-13_the-summary-shows-the-due-today-count".*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | cut from the product's documents | Principal PM | `<CORE>/launchers/skill/launcher.sh seeds-from-product-docs tracker17` | — | The docs cut, below (NFDR QC-40) |
| 2 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh seed-pick tracker17` | 1 | the pool |
| 3 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 2 | row 2 |
| 4 | walk the next change | owner | `<CORE>/launchers/walk/launcher.sh tracker17` | 3 | row 3 |

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-11-13_summary-shows-due-today #1` — retire this seed once its station is closed | ignored | none | The retire it asks for already landed. | `1654893c8` `retire: nemawashi/2026-11-13_the-summary-shows-the-due-today-count → trail/` |
| `2026-11-13_summary-shows-due-today #2` — decide the four due-today fold seeds: their work is on disk | drop | four drops: `73f8af8de` (SRS), `a81f7a2b4` (UXD), `fcd48033d` (SDD), `ae88081f0` (CONTENT) | Each seed's one station asks for a fold that has happened: all four documents are Settled and carry the count, no companion is live, and the count is built. A drop, not a retire: none was picked or walked. | `products/tracker17/docs/SRS.md:L3-L5`, `UXD.md:L3-L5`, `SDD.md:L3-L5`, `CONTENT.md:L10-L12` (all Settled; versions 8, 12, 23, 22); `CONTENT.md:L166`; `ls products/tracker17/docs \| grep -i open_issues` → nothing; `products/tracker17/docs/what_left.md:L5` "Nothing is left to build." |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-11-13_the-srs-carries-the-due-today-count` | dropped | moved to `drop/`, `73f8af8de` | SRS version 8 carries the count at FR-38 and AC-13; its station is done without it. | recommendation #2; `products/tracker17/docs/SRS.md:L5` |
| `2026-11-13_the-uxd-carries-the-due-today-count` | dropped | moved to `drop/`, `a81f7a2b4` | UXD version 12 carries it at UX-F6 and UX-S5. | recommendation #2; `products/tracker17/docs/UXD.md:L5`, `L381` |
| `2026-11-13_the-sdd-carries-the-due-today-count` | dropped | moved to `drop/`, `fcd48033d` | SDD version 23 carries it as a re-cut of S-6 (§ 10 RC-7). | recommendation #2; `products/tracker17/docs/SDD.md:L5` |
| `2026-11-13_the-content-carries-the-due-today-count` | dropped | moved to `drop/`, `ae88081f0` | CONTENT version 22 carries the term "Due on {date}". | recommendation #2; `products/tracker17/docs/CONTENT.md:L12`, `L166` |
| `2026-11-13_one-fake-and-one-contract-suite-per-contract` | kept | — | Independent of the count; NFDR QC-64 still states it unmet; its parked station `tracker17 · shukuba · 2026-11-13_clock-fake-and-suite` stands on unmoved ground. | the seed's § Relation to existing work; the walked unit's refine report, § Considered, not moved, rows 5–6 |

## The docs cut

Owed: NFDR QC-40 states work no candidate carries — moving the Playwright pin off Chromium 158.0.8127.18 within 30 days of the 2026-11-11 advisories, named owed by the previous refine and not cut since; both pins still read `playwright==1.65.1` (`products/tracker17/docs/nfdr.md:L475-L486`; `products/tracker17/pyproject.toml:L17`, `products/tracker17/.behave/pyproject.toml:L8`; no `seeds-from-product-docs` commit under `system/projects/tracker17` since 2026-11-13).

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| A malformed satellite triple | `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md` | none — it is the subject of that finding, already filed; not a dead pointer | `check_journey_links.py`, before and after the drops: every pointer resolves, 1 malformed triple |

## Held and refused

None. The project's chain state reads `ended: settled`, `pending: null`; no product companion is live.
