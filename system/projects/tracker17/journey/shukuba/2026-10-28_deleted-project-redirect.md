# 宿場 Shukuba — a deleted project's Add task and Rename are answered by a redirect, and the count comes only from the application

*Item 4 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-11_delete-and-rename`. Slug: `deleted-project-redirect`.*

## What it is

SDD § 4 RT-11 says a submission naming a deleted target is answered by a redirect to that target's address, which shows the not-found page, and saves nothing. A deleted task's submissions already do this; Add task and Rename sent for a deleted project answer the not-found page directly (`products/tracker17/web/routes.py`, `_rename_project` and `_add_task`, the `if project is None: return self._not_found_page()` lines, and the `except ProjectNotFound` in `rename`). This station makes both redirect to `/projects/<id>`, which then shows the 404. It also removes the one place `web` owns a count: `project_page` falls back to `len(rows)` when called without a listing (`products/tracker17/web/pages.py`, `task_count = listing.task_count if listing is not None else len(rows)`), against SDD § 3, so Delete project's confirmation takes its task count only from the application's answer. The count fix rides here because it is the same project-deletion code in `web`, and a one-line placement fix does not earn a merge of its own. One merge reaches it.

## Reached when

1. In the running app, an Add task submission and a Rename submission for a project that has been deleted (sent after the deletion, as from another tab) are each answered by a redirect to `/projects/<id>` of that project, and following it shows the not-found page (404); the saved data is unchanged.
2. A test per submission (Add task, Rename) asserts the redirect status and its location, and that the saved projects and tasks are identical before and after. Each test fails on `main` today, where both answer the not-found page directly.
3. `project_page` in `products/tracker17/web/pages.py` has no `len(rows)` fallback for the task count: `git grep -n 'len(rows)' -- products/tracker17/web/pages.py` prints no line inside `project_page`, and a test shows Delete project's confirmation sentence carries the count the application answered, not the count of rows shown.
4. `pytest products/tracker17/tests/` exits 0, and the end-to-end suite `pytest products/tracker17/tests/e2e/` exits 0 (the card's `Test command:` skips `tests/e2e/`, so it is run on its own).

## Guardrail

- A deleted task's submissions, the not-found page itself and its lack of a cache header (RT-11) stay as walked.
- No change to the wording of any page; the redirect lands on the existing not-found page.
- The count is read from the application's answer only; `web` gains no counting of its own, and `application` gains no new capability beyond handing the count over.
- No moving of tasks between projects (SRS FR-14) and no change of a project's description (UXD § 10).

- **Not here:** deleting a task, renaming a project and deleting a project, `tracker17 · nemawashi · 2026-10-11_delete-and-rename` items 1 to 3, already walked; Delete task's full-size confirmation, item 5.
