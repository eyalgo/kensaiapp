# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-28_all-tasks-list`, the All tasks list. Workflow mode, in-repo product (`products/tracker17`): one worktree takes both the code and the report.

## Deferrals

None. The closing marker `<a commit not in the public history>` (`developer: 2026-10-28_all-tasks-list — implementation complete`) carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

The product code the change wrote, `git diff main...2026-10-28_all-tasks-list -- products/tracker17`: `domain/filtering.py`, `domain/sorting.py`, `domain/tasks.py`, `domain/__init__.py`, `application/tracker.py`, `web/pages.py`, `web/routes.py` and `web/style.css`. Also every test the change added or edited (20 test files).

## The intent it was checked against

`tl_instruction.md` (tasks 1 to 5, each task's *Behaviours to verify* and *Held by review*), `change_spec.md` (CP-459 to CP-489 and the Examples), `change_design.md` (§ 3 interfaces, § 5 T1–T20, Architect Review Notes), `change_text.md` (every published string, and its Wording decisions) and `deferred_decisions.md` (the CP-475 reading set aside). `docs/fdr.md` was read as context.

## Language resolution

Python. It comes from chain step 1, the `project.md` `Languages:` line. I read the packet `<CORE>/doctrine/engineering/languages/python/README.md`, which routes seven concerns: Toolchain, Layout, Quality gates, Conventions, Errors and logging, Testing (`testing_python.md`) and Gate environment. The review bar applied:

- `conventions.md:17`, lines within 100 columns, and `:49`, builtin generics with PEP 604 unions.
- `testing_python.md:31`, the seam is a hand-written fake and not `monkeypatch.setattr`. The four tests added here use the real `Site`, `Tracker`, injected clock and saver, and they patch nothing.
- `quality_gates.md`, ruff format and ruff check. Both are clean on the four changed test files, at the pinned ruff 0.16.10.
- Toolchain: the product's ADR-0002 and NFDR QC-59/QC-60 put it on Python 3.11, which outranks the packet's 3.13 floor. The four changed test modules pass on 3.11.9.

## Placement

The parts table is `docs/SDD.md` § 3. Every piece of new logic is already in the part that owns it, so no placement commit was made.

- `all_filter_options`, `filter_all_tasks`, `_options` and `_select` are in `domain/filtering.py`, owned by `domain` (the filter computation). They were already there.
- `sort_all_tasks` and `_sorted_selection` are in `domain/sorting.py`, owned by `domain` (the sort computation). They were already there.
- `list_all_tasks` is in `domain/tasks.py`, owned by `domain` (list order). It was already there.
- `Tracker.all_task_list` and `_read_list` are in `application/tracker.py`, owned by `application` (it calls the rule and projects the page data). They were already there.
- `MovePlace`, `_back_out_address`, `_Scope`, `_project_cell`, `all_tasks_page`, `_STANDING_LINES` and `_all_sort_count_line` are in `web/pages.py`, owned by `web` (presentation and words). They were already there.
- The `GET /tasks` dispatch, `_all_tasks_page`, the `place` decoding in `_move_task` and the `find` parameter of `_off_list_task` are in `web/routes.py`, owned by `web` (addresses and request decoding). They were already there. Off-list membership is a test against the selected row identities, not a copy of a filter rule.
- The `.project-cell` and minimum-width rule is in `web/style.css`, owned by `web` (the stylesheet). It was already there.

## The tests added or fixed

No existing test was wrong. I added four tests, seven cases in all. Each comes from the intent, and each was shown to fail when the code it guards was deliberately broken, then restored.

1. **`tests/integration/test_filter_move_routes.py::test_global_in_row_refusal_states_the_status_without_claiming_a_change`** (3 cases). The intent is `change_text.md`, "In the task's row, when the task is listed", and its first Wording decision. The test checks the exact All tasks line for each move count the workflow can reach: two moves (todo), three moves (in-progress) and none (done). It also checks that the same press on a project's list keeps "has changed to" (CP-478). Before this, only the two-move form was pinned exactly; the three-move form was not pinned at all, and the no-move form only by fragments. Break check: making All tasks use the project's wording turned all 3 cases red.
2. **`tests/integration/test_pages.py::test_both_not_found_forms_offer_both_destinations`** (2 cases). The intent is CP-460 and the change text's "Both not-found pages". For each of the two forms, the test checks: one heading, then one paragraph reading exactly "Open Projects or All tasks." with Projects linked before All tasks, the three header links, five links in all, and no form. Before this, the task form's paragraph and its structure were unchecked. Break check: restoring the old one-link paragraph on the task form turned it red.
3. **`tests/integration/test_sort_pages.py::test_project_links_carry_no_choice_while_choices_are_applied`**. The intent is CP-463, "a link to that project's page with no filter or sort choice in its address". Before this, the Project link was checked only on a page with no choices applied. Break check: appending a choice to the link turned it red.
4. **`tests/architecture/test_trace.py::test_list_entries_name_fr31_and_every_all_tasks_participant`**. The intent is CP-481. The test checks that the filtering docstring names FR-31, and that both list docstrings name `application/tracker.py`, `application/__init__.py`, `web/routes.py` and `web/pages.py`. The existing trace tests check FR-32 to FR-35 only, so dropping FR-31 would have stayed green. Break check: removing FR-31 turned it red.

## The finding

No issues. The code already did what its intent says on every behaviour I tested: the four tests above passed against the developer's code unchanged. Nothing was misplaced, and no code was changed. The gap was in the tests: four requirements had no test that would fail if the code were wrong, and each now has one.

These requirements are checked by reading the code, not by a test:

- **CP-480:** both list scopes reach one validator, matcher, label computation, sort validator and `_ordered`. There is no second copy in `application` or `web`.
- **CP-479:** `web/style.css` matches `docs/DESIGN.md` § Layout. The title, project, assignee and labels cells each keep `min-width: 6rem`, and the table sits in the `.table-scroll` container. The 400% zoom and long-value browser inspection was not run, as the developer's marker also records.
- **CP-482:** nothing under `persistence/`, `main.py`, `errors.py` or `pyproject.toml` changed.
- **CP-486:** the timed-run files are unchanged.

## Calls made

1. **Should the FR-31 check extend the existing filtering trace test, or be a new test?** The two readings: add FR-31 to `FILTERING_REQUIREMENTS` in the existing test, or add a new test function. I took the new test function. CP-487 says "No other existing test is changed to fit", and a new function meets that under either reading of "changed". The call is the Product Owner's (`change_spec.md`). If they rule the other way, FR-31 moves into `FILTERING_REQUIREMENTS` and the new test folds into it.
2. **Does CP-481's "every test module this change adds" bind anything?** The change adds no test module; it extends existing ones. So the clause binds nothing, and test 4 checks only the requirement and the participants. The call is the Product Owner's. If they read "adds" as "extends", both docstrings would also have to name `tests/integration/test_sort_pages.py`, `test_sort_routes.py`, `test_move_pages.py`, `tests/e2e/test_moves.py` and others, and test 4 would grow to match.
3. **Does CP-459's "The page for saved data that can't be read keeps having no header" need a test?** No such page exists. `main.py:39-46` prints to the console and returns 1 when the saved data can't be read, and `web/` has no page for it (SDD § 6 S-8 is not built). So the clause holds with no page to check, and no test is owed. This agrees with the developer's marker. The call belongs to the Architect (SDD S-8). If a page is built later, its header test belongs to that change.

## Test evidence

- The run the verdict rests on is the full card command through the gate tool (`--gate code-integrity`, using the plan's gate-environment inputs: no CI). It exited 0 with `1964 passed in 144.29s`, which is the developer's 1957 plus these 7 cases.
- No earlier full-card run was made.
- Targeted runs, which were not full-card runs:
  - The 7 new cases passed on Python 3.15.
  - The four changed modules passed on Python 3.11.9 (116 passed).
  - Each break check above turned its own test red and left the others green.
  - `ruff format --check` and `ruff check` were clean on the four changed files.
- Not re-run here: the browser suite (`tests/e2e/`, which the card's command does not collect), mypy and the timed run. No production code and no browser test changed in this step, so the developer's task-5 results stand: e2e 88 passed on 3.11.15, the timed run exited 0, and mypy exited 0.
