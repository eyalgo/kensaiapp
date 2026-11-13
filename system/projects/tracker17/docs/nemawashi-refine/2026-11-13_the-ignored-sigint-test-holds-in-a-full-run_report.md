# 根回し Nemawashi refine — `2026-11-13_the-ignored-sigint-test-holds-in-a-full-run`

*The Principal PM's answer to the seed retired to `journey/nemawashi/trail/2026-11-13_the-ignored-sigint-test-holds-in-a-full-run` at `92de3a8db`,
and the pool re-read behind it, 2026-11-13. The slug came from the caller: "answering the retired seed 2026-11-13_the-ignored-sigint-test-holds-in-a-full-run".*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | cut from the product's documents | Principal PM | `<CORE>/launchers/skill/launcher.sh seeds-from-product-docs tracker17` | — | `2026-11-13_ignored-sigint-timing #2` |
| 2 | pick a seed | PM | `<CORE>/launchers/skill/launcher.sh seed-pick tracker17` | 1 | the pool |
| 3 | cut the route | PM | `<CORE>/launchers/skill/launcher.sh stations-from-seed tracker17` | 2 | row 2 |

The table stops at the route's cut: whether the next station is the chain's or the owner's turns on the pick. The pool holds `2026-11-13_the-srs-carries-the-due-today-count` (and its UXD, SDD and CONTENT siblings), whose one station is a companion fold — the owner's sweep — while `2026-11-13_the-summary-shows-the-due-today-count` is chain work.

## Recommendations

| Recommendation | Answer | What was done | Why | Source |
|---|---|---|---|---|
| `2026-11-13_ignored-sigint-timing #1` — retire this seed once its station is closed | ignored | none | The retire it asks for already landed. | `92de3a8db` `retire: nemawashi/2026-11-13_the-ignored-sigint-test-holds-in-a-full-run → trail/` |
| `2026-11-13_ignored-sigint-timing #2` — cut a security seed: move the Playwright pin off the affected Chromium build by 2026-12-11 | docs cut | named as next move 1 | A security line from a sealed unit, and the NFDR names the check it falls under: QC-40 states the 30-day window for the browser build `playwright==1.65.1` installs, and the two ways out (move the pin, or the owner's dated exception). No candidate carries it. | `products/tracker17/docs/nfdr.md:L475-L486`; `products/tracker17/pyproject.toml:L17`, `products/tracker17/.behave/pyproject.toml:L8`; `tracker17 · tobiishi · 2026-11-13_ignored-sigint-timing`, `change_design.md` L176-L184 |

## Candidates

| Candidate | Verdict | What changed | Why | Source |
|---|---|---|---|---|
| `2026-11-13_one-fake-and-one-contract-suite-per-contract` | kept | — | Still unmet NFDR QC-64 work toward **Simple to read**; the walk touched no fake or contract suite. | `tracker17 · shukuba · 2026-11-13_ignored-sigint-timing` refine report § Considered, not moved (diff touched the two sigint test modules only) |
| `2026-11-13_the-summary-shows-the-due-today-count` | kept | — | The build is still owed: `ProjectSummary` has `overdue` and `no_due_date`, no due-today field; its FDR wait was already removed at `7de9ac095`. | `products/tracker17/domain/summary.py:L81-L82` |
| `2026-11-13_the-srs-carries-the-due-today-count` | modified | divergence line: the work is on disk, wants a pick and a close — `2423eebea` | Its prose said the SRS stops at version 7 with no count; SRS v8 Settled carries it (15 hits) and its companion is gone. | `a3b3d39cd`; `grep -ciE 'due.today' products/tracker17/docs/SRS.md` → 15 |
| `2026-11-13_the-uxd-carries-the-due-today-count` | modified | the same — `2423eebea` | Its prose said the UXD lacks the count; UXD v12 Settled carries it (19 hits) and its companion is gone. | `59b5394da`; `grep -ciE 'due.today' products/tracker17/docs/UXD.md` → 19 |
| `2026-11-13_the-sdd-carries-the-due-today-count` | kept | — | Its divergence line already says SDD v23 carries the count and it wants a pick and a close. | the seed's last paragraph; `edd4235e1` |
| `2026-11-13_the-content-carries-the-due-today-count` | kept | — | Its divergence line already says CONTENT v22 carries the term and it wants a pick and a close. | the seed's last paragraph; `f3749d5bf` |

None of the four document seeds is dropped: their work ripened rather than being ruled out, and a ripened seed is retired after a pick and a close, not killed.

## The docs cut

Owed: the NFDR's QC-40 states work — moving the Playwright pin off Chromium 158.0.8127.18 within 30 days of the 2026-11-11 advisories — that no candidate carries (`products/tracker17/docs/nfdr.md:L475-L486`).

## Found while reading

| Defect | Where | What was done | Source |
|---|---|---|---|
| Two candidates stated a document gap that has since closed | `unpicked/2026-11-13_the-srs-carries-the-due-today-count.md`, `unpicked/2026-11-13_the-uxd-carries-the-due-today-count.md` | repaired at `2423eebea` | Candidates rows above |

The journey-link check found no dead pointer before the run (its one malformed triple, a satellite's, is already filed at `docs/findings/2026-10-03_a-satellite-triple-is-reported-malformed.md`), and the run moved nothing that could break one.

## Held and refused

None. `system/logs/chain-tracker17-state.json` reads `ended: settled`; no product companion is live (`ls products/tracker17/docs | grep -i open_issues` → nothing).
