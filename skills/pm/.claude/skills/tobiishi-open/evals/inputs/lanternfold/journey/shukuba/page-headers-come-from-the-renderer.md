# 宿場 Shukuba — the page header set comes from the renderer

*Item 1 on the active 根回し Nemawashi `pages-own-their-headers`. Slug: `page-headers-come-from-the-renderer`.*

## What it is

Move the page-level header set out of the HTTP edge and into the renderer, so each view carries its
own headers, as NFDR QC-4 asks. The edge keeps writing exactly the headers it writes today.

## Reached when

- `grep -n "PAGE_HEADERS" src/lanternfold/host/application.py` returns no line. It returns one today.
- `render_welcome` and `render_goodbye` in `src/lanternfold/screens/renderer.py` each return a value
  carrying the rendered body **and** the header set, of a type defined under
  `src/lanternfold/screens/`. Both return a bare `str` today.
- `pytest tests/` exits 0.

## Guardrail

- Every page response carries byte-identical headers, in the same order, before and after.
- **Not here:** `a-view-marks-itself-not-storable`.
