# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-11-12_failed-action-path-non-text-byte` — the change for station `2026-11-12_failed-action-path` (seed `2026-10-30_a-path-with-a-non-text-byte-is-printed`, item 3 of 3), derived from the station's reached-when, 2026-11-12. Adds the test that holds `CONTENT.md` RN-35: a failed action at a path with a non-text byte writes the plain sentence (no path), then the error kind and the path as `\udce9`, and the write raises nothing; the walker's mutation (rewrite to `\xe9`) must fail it. Production code changes only if the test shows a raise or a rewrite. Sizing: one capability, one merge; the acceptance boundary is the station's reached-when 1 to 4. Scope boundary: the start-level surfaces stay as landed; no document changes. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `bug` / `preserving`: an unpinned contract, behaviour fine.
