# 宿場 Shukuba — a project can be deleted with its tasks, and the slice's deletions are never replayed

*Item 3 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-11_delete-and-rename`. Slug: `delete-a-project`.*

## What it is

A project's Tasks view offers Delete project. It opens a confirmation naming the project and its number of tasks; confirming deletes the project with its tasks and their comments and lands on Projects with a line naming the deleted project (UXD; SDD § 6 S-7; SRS FR-13, FR-17). The confirmation behaves as the one in `status-moves` does and holds below a list long enough to scroll (SDD § 4 EX-6). The project's address then shows the not-found page, and an action sent from another tab for it is refused and changes nothing (AC-12). This station also lands what SDD v13 and ADR-0012 widened onto the slice's last station: both deletions' pending confirmations answer 202 (a task deletion's answers 200 today), every page of either deletion carries `Cache-Control: no-store`, and Back to a deletion's confirmation after confirming is a fresh load (S-7 *Command*, RT-11). Last, the opening docstrings of `domain/projects.py` and `domain/tasks.py` name the tests the whole slice added (S-7 *Artifact*). One merge closes the seed.

## Reached when

1. In the running app, Delete project on a project's Tasks view opens a confirmation whose sentence names that project and its task count; confirming lands on Projects with a line naming the deleted project, and the project is in no list.
2. The deleted project's tasks appear in no list and no task of it or comment on one can be read at any address (FR-13, FR-17); its own address shows the not-found page (404).
3. An action for that project sent after it was deleted, as from another tab, is refused and the saved data is unchanged (AC-12).
4. A page showing a pending confirmation of a project deletion, and one of a task deletion, each answer 202; the other pages of either deletion answer 200 and the deleted address 404; each page that shows a deletion's confirmation or outcome carries `Cache-Control: no-store`, and the not-found page for a deleted address carries none (RT-11). A test asserts the task deletion's confirmation answers 202 (today a test asserts 200, `products/tracker17/tests/integration/test_delete_routes.py`).
5. An end-to-end test shows Delete project's confirmation below a list long enough to scroll opening in view with keyboard focus on its sentence, and a double press on its first button not confirming; another shows that Back to a deletion's confirmation after confirming is a fresh load (S-7 *Command*).
6. The opening docstrings of `products/tracker17/domain/projects.py` and `products/tracker17/domain/tasks.py` each name the tests this slice added (S-7 *Artifact*).
7. `pytest products/tracker17/tests/` exits 0, including a test that a deleted project's tasks and comments are gone and one per deleted-target refusal of item 3 asserting unchanged saved data.
8. `python3 products/tracker17/tests/timed_run.py` exits 0 and its listed actions include a deletion (QC-48).

## Guardrail

- Reuse the confirmation of `status-moves` and the existing delete-a-task and rename code paths; no second confirmation scheme and no cache workaround such as a page script (ADR-0012 chose the 202).
- The task deletion's behaviour otherwise stays as walked: only its confirmation status and cache header move to RT-11's.
- The docstrings name tests and nothing else; no new feature module (S-7 *Artifact*).
- No moving of tasks between projects (SRS FR-14) and no change of a project's description (UXD § 10).

- **Not here:** deleting a task, `tracker17 · nemawashi · 2026-10-11_delete-and-rename` item 1, and renaming a project, item 2, both already walked; the seed's retirement after this station closes is the Scrum Master's.
