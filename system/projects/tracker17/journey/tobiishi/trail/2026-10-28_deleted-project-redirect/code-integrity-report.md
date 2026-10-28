# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-28_deleted-project-redirect` · **Date:** 2026-10-28 · **Mode:** workflow

## Deferrals

None. The closing marker (`<a commit not in the public history>`, the newest `— implementation complete` commit on the branch) carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

The branch's code commits `97e37d9d8`..`a7e53bc78` under `products/tracker17/`:

- `web/routes.py`: `Site._add_task`, `Site._rename_project`, `Site._project_page`.
- `web/pages.py`: `project_page`.
- The nine test modules named in `tl_instruction.md` § Project layout.

## The intent it was checked against

- `tl_instruction.md`: Tasks 1 and 2, their *Behaviours to verify* and *Held by review* items.
- `change_spec.md`: CP-594 to CP-608, the Examples table, § Out of Scope, and § Locked Answers Gap 6.
- `change_design.md` § 2 (*Response boundary*, *Renderer contract*) and § 5 rows T1 to T12.
- `docs/fdr.md` exists; nothing in it bore on a test beyond what the spec quotes.

## Language resolution

Python, chain step 1 (`project.md`, `Languages: Python`). Read `<CORE>/doctrine/engineering/languages/python/README.md` and the concerns it routes: `conventions.md`, `quality_gates.md`, `errors_logging.md` and `testing_python.md`. The production diff passes all four:

- Annotated, keyword-only `task_count: int`.
- `ProjectNotFound` caught by its type.
- No logging added.
- The action-time fake is a hand-written `Tracker` subclass passed to `Site(...)`, with no `monkeypatch`, as `testing_python.md` § Rules requires.

## Placement

The parts table is `docs/SDD.md` § 3, *The parts*. Two pieces of new logic were walked:

- **Redirect selection.** The readable-identity check and the bare `/projects/<n>` address in `Site._add_task` and `Site._rename_project` belong to `web`, which owns "the addresses of pages and actions". Already there.
- **The confirmation count.** The required `task_count` input of `pages.project_page`, and its supply from `listing.task_count` in `Site._project_page`, belong to `web`, which owns page building. The count itself still comes from `application`, so `web` does not decide "what a count is". Already there.

Nothing was moved, so there is no placement commit.

## Tests added or fixed

1. **`tests/integration/test_task_routes.py`, `state_of`: fixed.** It compared `project_tasks(2)`. The never-held matrix (`test_missing_project_add_redirects_without_saving`) runs in a world with only project 1, so its "tasks identical" clause compared two empty tuples, whatever happened to project 1. It now compares every project's tasks, which is what CP-594 asks: "its projects and its tasks are identical".
2. **`tests/integration/test_delete_project_pages.py`, `test_project_confirmation_counts_all_current_tasks`: strengthened.** The refused-filter (`filter_status=bogus`) and refused-sort (`sort_field=bogus`) queries now also assert that the page lists no row. Without this, nothing showed those queries reach a refused state. Now a 4-task sentence over 0 rows is proved, which is CP-600's "or refused" case.
3. **`tests/integration/test_rename_routes.py`, `test_deleted_project_rename_redirects_without_saving`: fixed.** This edit was found in the tree, uncommitted, made after the closing marker. It was reviewed and taken (Calls made, 1). The world held a project named `Gamma`, so the matrix's `valid` name (`Gamma`) was really a second in-use case, and a valid name was never sent to a deleted project. The world is now `Alpha`, `Beta`.

All three are green against the code as committed.

## The finding

No bug. The code does what CP-594 to CP-601 say.

Five deliberate breaks to the code, each run against the four touched route and page modules and then undone:

| Break | Result |
|---|---|
| Initial lookup answers the 404 directly | 62 failed |
| Action-time `ProjectNotFound` answers the 404 directly | 12 failed (T3) |
| Raw digits used in the address (`00` stays `00`) | 30 failed |
| Renderer counts `len(rows)` | 3 failed (T6) |
| Route hands `len(listing.rows)` | 1 failed (T5) |

Held-by-review checks, all passing:

- The redirects use `Site._redirect` with no flag or query.
- `git grep -n 'len(rows)' -- products/tracker17/web/pages.py` printed nothing and exited 1.
- The branch diff over `domain`, `application`, `persistence`, `main.py`, `errors.py` and `docs` is empty.
- No page wording changed in the `web/pages.py` diff.
- `project_page`'s docstring describes the explicit count.

## Calls made

1. **Take the uncommitted edit to `test_rename_routes.py`, or discard it?**
   - Readings: discard it as not this run's, or review it and take it.
   - Taken: take it. It corrects a case that misread the plan, which asks for a valid name and an in-use name as separate cases (`tl_instruction.md`, Task 1, `test_missing_project_rename_redirects_without_saving`, "a valid name … already-used names").
   - Owner: the Tech Lead's plan.
   - If reversed: the deleted-project Rename matrix again sends no valid name.
2. **The deleted-project matrices delete with `tracker.delete_project(1)` and not through the confirmation press. Is that what the plan asks?**
   - Taken: accepted. It is the same application call the press makes, and the code under test reads only `tracker.project(identity)`, so the state it meets is the same. The press itself is still exercised for both submissions by `test_deleted_project_submission_changes_nothing[add-task]` and `[rename]`.
   - Owner: the Tech Lead's plan.
   - If reversed: each matrix case sets up the deletion through `press(world, confirming=True)`.
3. **Should a test pin the initial missing-project check in `web`?**
   - Removing that check entirely leaves every test green. The real application reports `ProjectNotFound` before it refuses any form value, so the action-time redirect gives the same answer, and the behaviour CP-596 and CP-597 state still holds.
   - Taken: leave it held by review, as `tl_instruction.md` Task 1 *Held by review* places "keep the request checks first". Pinning it would need a fake application whose ordering the real one does not have.
   - Owner: the Tech Lead's plan.
   - If reversed: add a `Site` test with a tracker whose `project()` answers `None` and whose action refuses the form first.

## Test evidence

- The card's command, `pytest products/tracker17/tests/`, issued through `gate_suite.py run --gate code-integrity`, exited 0: `2629 passed in 273.11s`. This is the run the verdict rests on, and its line is the one above.
- `pytest products/tracker17/tests/e2e/` from the change worktree root, with the product's `.venv` interpreter, exited 0: `117 passed in 56.27s` (CP-604).
- From `products/tracker17/`, with `ruff 0.16.10` and `mypy 2.4.0` (the `pyproject.toml` pins), all three QC-62 gates exited 0 (CP-606):
  - `ruff format --check .`: "269 files already formatted".
  - `ruff check .`: "All checks passed!".
  - `mypy main.py errors.py domain application persistence web`: "no issues found in 27 source files".
