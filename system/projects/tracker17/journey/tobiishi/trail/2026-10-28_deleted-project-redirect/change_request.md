# Change request — 2026-10-28_deleted-project-redirect

---

**Request:** Make a submission for a deleted project answer the way a deleted task's submissions already do. When an Add task or a Rename is sent for a project that has been deleted (as from another tab after the deletion), the application redirects to that project's address, `/projects/<id>`, which shows the not-found page (404), and saves nothing; today both answer the not-found page directly (SDD § 4 RT-11). This covers both the case where the project is already gone when the form arrives and the case where it disappears between the check and the save. Also remove the one place `web` owns a count: `project_page` in `products/tracker17/web/pages.py` falls back to `len(rows)` when called without a listing, so Delete project's confirmation takes its task count only from the application's answer (SDD § 3). Tests: one per submission (Add task, Rename) asserting the redirect status and its location and that the saved projects and tasks are identical before and after, each failing on `main` today; and one showing Delete project's confirmation sentence carries the count the application answered, not the count of rows shown. `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` must both exit 0. A deleted task's submissions, the not-found page itself and its lack of a cache header (RT-11) must stay as walked; no page's wording changes; `web` gains no counting of its own and `application` gains nothing beyond handing the count over. Deleting a task's confirmation size, moving tasks between projects (SRS FR-14) and changing a project's description (UXD § 10) are not part of this change.

**Category:** feature
**Behaviour:** changing
**Classified because:** the station's reached-when changes what Add task and Rename return for a deleted project, from the not-found page to a redirect, which alters what a public route returns (SDD § 4 RT-11).

---

*Sizing: one capability, answering a submission for a deleted project by redirect to its address, with the count placement fix riding as the same project-deletion code in `web`; acceptance is the station's four reached-when items (both redirects with unchanged data, the test per submission, no `len(rows)` fallback with its test, both suites); one flow, one merge. Source: SDD § 4 RT-11 and § 3, the station `2026-10-28_deleted-project-redirect`, item 4 of 5 on seed `2026-10-11_delete-and-rename`. FDR fit: in-scope; `docs/SDD.md`, `docs/fdr.md`, `docs/nfdr.md` and `docs/adr/` are present.*

**Sealed:** 2026-10-28 — accepted; merged to `main` via `--no-ff`.
Environment: owners-mac — no CI
