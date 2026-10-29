# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-10-29_project-card-commands` — the next change for station `2026-10-29_project-card-commands` (seed `2026-10-29_the-suite-runs-on-uv`, item 3 of 3), derived from the station's reached-when, 2026-10-29. It changes the project card's `Setup command:` (from `none` to a uv sync from `uv.lock`, naming `products/tracker17`) and `Test command:` (from a bare `pytest` to the whole suite run through uv), both run from the change worktree's root. Sizing: one capability, one merge; the two commands are one fact, and the acceptance boundary is the station's four reached-when items. Scope boundary: only those two card lines; no tracker code, test, pin, `uv.lock`, README or other card line; the suite is not narrowed. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `nfdr` / `changing`: the card's commands are what says pass or fail for every later change.
