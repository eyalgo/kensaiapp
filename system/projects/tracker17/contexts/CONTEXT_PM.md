# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-10-28_delete-a-project` — the one change for station `2026-10-28_delete-a-project` (seed `2026-10-11_delete-and-rename`, item 3 of 3, the last). Delete project on a project's Tasks view behind a confirmation naming the project and its task count, built on the existing confirmation and holding below a scrolled list; confirming deletes the project with its tasks and comments and lands on Projects with a line naming it; its address then shows the not-found page and a late action for it is refused with data unchanged (AC-12). Also lands SDD v13 / ADR-0012: both deletions' pending confirmations answer 202 (a task deletion's answers 200 today), every deletion page carries `Cache-Control: no-store`, Back to a confirmation after confirming is a fresh load (RT-11); the opening docstrings of `domain/projects.py` and `domain/tasks.py` name the slice's tests; the timed run gains a project deletion (QC-48). Sizing: one capability, one merge. Scope boundary: no moving tasks (FR-14), no description change (UXD § 10), no page-script cache workaround. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: adds a delete action and its refusals and changes a task deletion's confirmation status.
