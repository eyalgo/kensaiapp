# 宿場 Shukuba refine — recommendations to the Principal PM — `2026-11-13_ignored-sigint-timing`

*From the review of unit `2026-11-13_ignored-sigint-timing`, 2026-11-13. The report beside this file carries what the run
did; this file carries what it could not do and no companion can carry.*

## To the Principal PM

### 1. Retire `tracker17 · nemawashi · 2026-11-13_the-ignored-sigint-test-holds-in-a-full-run` once its station is closed

- **Kind:** a seed to retire
- **Why:** Its only station's reached-when holds on `main`; after the Scrum Master's close the checklist is fully walked.
- **Source:** report § Considered, not moved, row 1 — proof test alone `2 passed`; `tests/` `3336 passed, 2 skipped`; `tests/e2e/` `122 passed`; the skip/retry grep over the diff prints nothing.
- **Why no companion carries it:** it is a seed's retire, not what a document should state.

### 2. Cut a security seed: move the Playwright pin off the affected Chromium build by 2026-12-11

- **Kind:** a seed to cut
- **Why:** Both dependency sets pin `playwright==1.65.1`, which installs Chromium 158.0.8127.18; the design review read it as affected by five Critical advisories fixed in the vendor's 2026-11-11 stable update, and NFDR QC-40 gives 30 days from publication. No seed or station carries the fix. The owner's question beside it: move the pin, or record a dated exception in an NFDR Review Note (QC-40's alternative).
- **Source:** `products/tracker17/pyproject.toml` L17 and `products/tracker17/.behave/pyproject.toml` L8 (`playwright==1.65.1`); `tracker17 · tobiishi · 2026-11-13_ignored-sigint-timing`, `change_design.md` L176-L184; `flow_findings/development-design.md` (the item has "no owner or route out of the change folder"); `products/tracker17/docs/nfdr.md` L475-L486.
- **Why no companion carries it:** QC-40 already states the rule and the window; what is owed is a pin move in the product, which is work.
