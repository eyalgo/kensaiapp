# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-10-29_uv-lock-and-pins-test` — the first change for station `2026-10-29_lock-and-pins-test` (seed `2026-10-29_the-suite-runs-on-uv`, item 1 of 3), derived from the station's reached-when, 2026-10-29. It replaces `tests/requirements.txt` with `uv.lock` beside `pyproject.toml`, rewrites `tests/architecture/test_pins.py` to check `uv.lock`, and rewords the `pyproject.toml` comment that names the old file. Sizing: one capability, one merge; the acceptance boundary is the station's four reached-when items. Scope boundary: no dependency version changes, no tracker code, no `docs/` record, no project card line; the README and the card's commands are the next two stations'. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present (ADR-0013, QC-39). Classified `nfdr` / `changing`: the pin test reports a different failure.
