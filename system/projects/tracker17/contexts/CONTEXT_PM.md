# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-10-30_what-the-start-prints` — the change for station `2026-10-30_what-the-start-prints` (seed `2026-10-11_protect-saved-data`, item 3 of 3), derived from the station's reached-when, 2026-10-30. The README section "What the start prints" names the third line a start can print, the one starting `The tracker couldn't read`, beside the ready line and `The tracker didn't start`, and says the tracker is still running when it shows, pointing on to "Setting saved data aside". The quoted wording is the program's own (`_unreadable_line` in `main.py`). Sizing: one capability, one merge; the acceptance boundary is the station's reached-when 1 to 4. Scope boundary: no change to `main.py`, the page, the lock or any test beyond what a README test already reads; the passage under the starting instructions stays as it is. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: a new statement in the setup instructions that a reader acts on.
