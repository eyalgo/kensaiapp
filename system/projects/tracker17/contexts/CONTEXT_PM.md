# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-10-30_unreadable-start-non-text-path` — the change for station `2026-10-30_unreadable-start` (seed `2026-10-30_a-path-with-a-non-text-byte-is-printed`, item 2 of 3), derived from the station's reached-when, 2026-10-30. A start on unreadable saved data at a path holding a byte that is not text prints the unreadable line and serves the unreadable-data page, each with the byte as `\xe9` (the form `CONTENT.md` § *A path the tracker prints* fixes), instead of raising `UnicodeEncodeError`; a test per surface fails on `main` and passes after. Sizing: one capability, one merge (line and page are one behaviour, SDD § 6 S-8); the acceptance boundary is the station's reached-when 1 to 6. Scope boundary: the failed-action console message is item 3 of the seed and stays out; no document changes; no change to where the saved data lives, the claim or the lock. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: a start that fails today now prints a line and serves.
