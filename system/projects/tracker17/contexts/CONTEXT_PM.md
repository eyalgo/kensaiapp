# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-10-19_cancel-confirmation` — the only change unit expected for station `2026-10-19_cancel-confirmation` (seed `2026-10-07_status-moves`, item 2), opened for its reached-when 1 to 6. Adds the `cancelled` button to every list row and the task page where the workflow rule allows it, with the in-place confirmation a first press opens (sentence, confirming control, back-out control, focus per UX-I2; backing out restores the button and its focus; a stale first press opens none). Removes `_WITHHELD_MOVES` from `web/pages.py` so the offered moves come from `domain/workflow.py` alone. Runs the unrun `tests/e2e/test_moves.py` and adds the focus and double-press browser tests. Scope boundary: workflow table stays written once; no out-of-date-move handling, no `tests/timed_run.py` change, saved data format unchanged except status; no delete confirmations. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Product-fit: `domain/workflow.py` exists; `web/pages.py` withholds `cancelled` today. The browser folder cannot run on this Fedora machine (missing `libglib-2.0.so.0`), so its bar is checked where layer 5 runs. Classified `feature` / `changing`: it adds the `cancelled` button and confirmation behaviour.
