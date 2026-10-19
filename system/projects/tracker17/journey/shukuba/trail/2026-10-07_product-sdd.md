# 宿場 Shukuba — tracker17's SDD settled, written from a settled SRS and UXD

*Item 7 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-05_define-the-product`. Slug: `product-sdd`.*

## What it is

The CTO's SDD for tracker17, authored in rounds by `product-sdd` from the settled PRD, SRS and UXD. On disk at open it already reads Settled (v5, 759ab7f5e), written after the UXD v4 closed its companion, so this station closes with no change unit.

## Reached when

- `products/tracker17/docs/SDD.md` line 3 reads `**Status:** Settled`.
- No `SDD_open_issues.md` exists under `products/tracker17/docs/` (`find products/tracker17 -name 'SDD_open_issues.md'` prints nothing).
- Its `**Inputs read:**` line (line 6) records `SRS Settled` and `UXD Settled`, and when the SDD was last committed, neither `SRS_open_issues.md` nor `UXD_open_issues.md` existed: `git ls-tree --name-only $(git log -1 --format=%h -- products/tracker17/docs/SDD.md) products/tracker17/docs/ | grep -E 'SRS_open_issues|UXD_open_issues'` prints nothing.

## Guardrail

- **Not here:** the owner's design run — its own station on `tracker17 · nemawashi · 2026-10-05_define-the-product`; the foundation step and the Delivery Plan — not on this seed.
- `products/tracker17/docs/SDD.md` is left byte-identical by the open and the close.
