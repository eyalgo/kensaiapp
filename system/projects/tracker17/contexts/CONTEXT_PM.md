# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-10-30_unreadable-data-page` — the change for station `2026-10-30_unreadable-data-page` (seed `2026-10-11_protect-saved-data`, item 2 of 2), derived from the station's reached-when, 2026-10-30. A start on saved data that cannot be read stops exiting 1 and instead serves one unreadable-data page at every address, with a console line naming the data's location; the data is never touched. It carries the rewritten start-level tests, one test per SRS DR-6 break asserting unchanged bytes, and the README passage with its two wording faults mended. Sizing: one capability, one merge; the acceptance boundary is the station's reached-when (SM-6, SD-5, UX-F11, UX-S9, AC-7). Scope boundary: no control on the page that acts on data, no change to the second-tracker refusal or lock, the data model, other screens or address-taken behaviour; the `readme-status` sentence and `docs/what_left.md` are not here. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: a new observable start behaviour.
