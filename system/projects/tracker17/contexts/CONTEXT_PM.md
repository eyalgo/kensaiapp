# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-10-21_move-timed-run` — the one change for station `2026-10-21_move-timed-run` (seed `2026-10-07_status-moves`, item 4). Reaches all four reached-when items: `tests/timed_run.py` prints a timed POST, landing GET and total for a status move, each under `LIMIT_SECONDS` (1.0); the run fails when the saved status is not the one moved to or the landing page does not show the result; it prints the move's fixture (1,000 tasks, 20 comments each, text lengths); both suites exit 0. Sizing: one capability (the timed run covers a move), one merge. Scope boundary: no product code under `domain/`, `application/`, `persistence/` or `web/` changes; the limit and every existing timed action stay as they are; the move to `cancelled` with confirmation is not timed unless its press path is the plain move's; no action beyond the move is added. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `nfdr` / `changing`: NFDR QC-48 drives it, and the enforcement command reports a new timed action, a new failure verdict and a new fixture report.
