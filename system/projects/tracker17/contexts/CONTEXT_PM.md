# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-10-30_ready-start-non-text-path` — the change for station `2026-10-30_ready-start` (seed `2026-10-30_a-path-with-a-non-text-byte-is-printed`, item 1 of 2), derived from the station's reached-when, 2026-10-30. A start on readable saved data at a path holding a byte that is not text prints the ready line with the byte as `\xe9` (the form `CONTENT.md` § *A path the tracker prints* fixes) and serves its page, instead of raising `UnicodeEncodeError`; a test fails on `main` and passes after. Sizing: one capability, one merge; the acceptance boundary is the station's reached-when 1 to 4. Scope boundary: the unreadable start (line and page) is item 2 of the seed and stays out; no document changes; no change to where the saved data lives, the claim or the lock. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: a start that fails today now prints a line and serves.
