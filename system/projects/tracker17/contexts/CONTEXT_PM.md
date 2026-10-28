# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-10-28_delete-a-task` — the one change for station `2026-10-28_delete-a-task` (seed `2026-10-11_delete-and-rename`, item 1 of 3). Delete task on a task's page behind the in-place confirmation (`confirm_strip`), removing the task and its comments and landing on its project with a line naming it; the deleted address shows the not-found page; actions sent for it from another tab are refused with data unchanged (AC-12); its identity is never reissued (FR-15); the timed run gains a task delete (QC-48). Sizing: one capability, one merge. Scope boundary: no project rename or delete, no docstring bar, no moving tasks (FR-14). FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: adds a delete action and deleted-target refusals to the contract.
