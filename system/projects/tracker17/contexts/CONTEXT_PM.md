# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Sealed

`2026-10-29_readme-on-uv` — the next change for station `2026-10-29_readme-on-uv` (seed `2026-10-29_the-suite-runs-on-uv`, item 2 of 3), derived from the station's reached-when, 2026-10-29. It rewrites the README's "Running the tests" section and the "How it's built" test line to the uv path (`uv sync --locked`, `uv run playwright install chromium`, `uv run pytest tests/`, `uv run pytest tests/e2e/`), with uv installed first. Sizing: one capability, one merge; the acceptance boundary is the station's four reached-when items. Scope boundary: the tracker's own setup text and start path stay as they are; no tracker code, test, `docs/` record or project card line; the card's commands are the next station's. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present (SDD § 4 RT-4, ADR-0013, QC-39). Classified `nfdr` / `changing`: the README now tells the reader to install and use uv.
