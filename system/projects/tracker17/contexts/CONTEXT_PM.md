# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-10-29_operator-name-with-a-brace` — the one change for station `2026-10-29_operator-name-with-a-brace` (seed `2026-10-29_operator-name-with-a-brace`, item 1 of 1). `_your_name_section` stops calling `.format` over an outcome line that already holds the escaped name, so a saved name such as `{x}`, `}` or `{0}` shows as typed on the saved and failed outcomes instead of raising. Tests: saved and failed outcomes one each, failing on the starting commit; blank and too-long refusals one each as guards with `{x}` already saved; full suite passes. Sizing: one capability (the Your name section's outcome rendering), one merge. Scope boundary: outcome wording, classes, ids and focus unchanged; no other page's text building touched; no document edited. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `bug` / `changing`: the page returns where it raises today.
