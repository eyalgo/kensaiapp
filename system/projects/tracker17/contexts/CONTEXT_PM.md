# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-10-28_task-delete-full-size-confirm` — the one change for station `2026-10-28_task-delete-full-size-confirm` (seed `2026-10-11_delete-and-rename`, item 5 of 5, the slice's last). Delete task's confirmation takes `spacing.control` (36px) like the full-size first press it replaces, instead of `row-control` (28px) (DESIGN `components.confirm-strip`); `_delete_strip` takes the sizing Delete project's strip already uses. A new e2e test measures the confirming button against the first press and fails on `main`; the e2e assertion pinning 28px is corrected; both suites pass. Sizing: one capability, one merge. Scope boundary: status-move strips stay `row-control`; no wording, focus, part-order or Delete project strip change; task deletion otherwise as walked; moving tasks (FR-14) and description change (UXD § 10) are out. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: changes what `/tasks/<id>?delete_confirm` renders where the suite pins 28px.
