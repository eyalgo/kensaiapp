# CONTEXT_PM — per-project PM context for project tracker17

## Current change — PM view

**Status:** Open

`2026-10-28_deleted-project-redirect` — the one change for station `2026-10-28_deleted-project-redirect` (seed `2026-10-11_delete-and-rename`, item 4 of 5). Add task and Rename sent for a deleted project answer a redirect to `/projects/<id>` (which shows the 404) and save nothing, instead of the not-found page directly (SDD § 4 RT-11); `project_page` loses its `len(rows)` task-count fallback so Delete project's confirmation takes its count only from the application (SDD § 3). A test per submission asserts the redirect and unchanged data; a test pins the count's source; both suites pass. Sizing: one capability, one merge. Scope boundary: a deleted task's submissions, the not-found page and its lack of a cache header stay as walked; no wording change; no counting in `web`; Delete task's full-size confirmation (item 5), moving tasks (FR-14) and description change (UXD § 10) are out. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present. Classified `feature` / `changing`: changes what two public routes return for a deleted project.
