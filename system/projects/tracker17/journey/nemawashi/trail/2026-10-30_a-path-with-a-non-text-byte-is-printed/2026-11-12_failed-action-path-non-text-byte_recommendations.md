# 宿場 Shukuba refine — recommendations to the Principal PM — `2026-11-12_failed-action-path-non-text-byte`

*From the review of unit `2026-11-12_failed-action-path-non-text-byte`, 2026-11-13. The report beside this file carries what the run
did; this file carries what it could not do and no companion can carry.*

## To the Principal PM

### 1. Retire the non-text-path seed once its last station closes

- **Kind:** a seed to retire
- **Why:** Items 1 and 2 are ticked and item 3's station is reached now; once the Scrum Master closes it, every station of the seed is walked.
- **Source:** report Considered rows 1 and 2; `tracker17 · nemawashi · 2026-10-30_a-path-with-a-non-text-byte-is-printed` (lines 15-17)
- **Why no companion carries it:** it is a seed's retire, not what a document should state.

### 2. Cut a seed for NFDR QC-64 — one fake and one contract suite per contract

- **Kind:** a seed to cut
- **Why:** The product's own stated gate is unmet on main and no seed carries it; this unit's spec handed the work to "the change QC-64's walk lands with", which nothing on the route is.
- **Source:** `products/tracker17/docs/nfdr.md` QC-64 and RN-65 ("QC-64 starts unmet"); measured at `d6226071e`: `test -e products/tracker17/tests/fakes.py` → absent; `git grep -lP '^\s+def (save|now)\(' -- products/tracker17/tests | wc -l` → 26 modules, 69 definitions; `tracker17 · tobiishi · 2026-11-12_failed-action-path-non-text-byte` `change_spec.md` § Out of Scope
- **Why no companion carries it:** the NFDR already states the requirement; what is missing is the work, a seed.
