# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-10-29_the-start-is-stoppable-from-its-ready-line` — a further change for station `2026-10-29_start-tests-under-ignored-sigint` (seed `2026-10-29_start-tests-under-ignored-sigint`, item 1 of 1), opened by hand in the owner's session, 2026-10-29. The station's close stopped on the proof test failing once under load; the cause is `main.py`'s `start`, which prints its ready line before entering the `try` that catches Ctrl-C. This change closes that gap and proves it with a test that fails on `main` every time. Sizing: one capability, one merge; the acceptance boundary is the station's reached-when plus the request's proof. Scope boundary: the ready line's words, the refusals and Ctrl-C's quiet stop unchanged; no test deleted, skipped, retried or marked expected-to-fail; no deadline lengthened. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `bug` / `changing`: a Ctrl-C right after the ready line ends the tracker with a traceback, a wrong observable.
