# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-10-30_second-tracker-refusal` — the change for station `2026-10-30_second-tracker-refusal` (seed `2026-10-11_protect-saved-data`, item 1 of 2), derived from the station's reached-when, 2026-10-30. It adds the one Unix lock of ADR-0009 (SDD `SM-5`) so a second start on a saved-data location in use prints one plain message and exits while the first tracker carries on and the saved data is unchanged, and a start after a kill succeeds; two tests (both halves of SRS AC-16) and a README passage. Sizing: one capability, one merge; the acceptance boundary is AC-16 / NFR-3. Scope boundary: no unreadable-data page, no change to unreadable-data exit-1, address-taken behaviour, screens or data model; no Windows path. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: a new observable refusal and kill-recovery.
