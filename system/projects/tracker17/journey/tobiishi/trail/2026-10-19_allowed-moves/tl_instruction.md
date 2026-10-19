# Tech Lead instruction — allowed-moves: moving a task along its allowed status moves

**Product root:** `products/tracker17` — every path below is relative to it.
**Scope:** `domain/workflow.py` (the allowed moves, the `MoveNotAllowed` refusal, the move rule), one `application` action and one query, and in `web` the move route, a seventh *moves* column, a status area on the task's page, the landing place and its line, and the move button's style. Category `feature`, Behaviour `changing` (copied from `change_design.md`). The design publishes text: every visible string, accessible name, reason and message comes from `change_text.md` verbatim, and none is written here or in a test by hand.

---

## Project layout

```
products/tracker17/
  domain/
    __init__.py              ← modified (re-exports allowed_moves, move_task, MoveNotAllowed)
    workflow.py              ← new
  application/
    __init__.py              ← modified (re-exports InvalidTaskStatus, MoveNotAllowed)
    tracker.py               ← modified (Tracker.move_task, Tracker.allowed_moves)
  web/
    routes.py                ← modified (POST /tasks/[0-9]+/move, outcome decoding)
    pages.py                 ← modified (moves column, status area, landing place and line)
    style.css                ← modified (move-button component)
  tests/
    architecture/
      test_trace.py          ← modified (E1)
      test_shapes.py         ← modified (E2)
    unit/
      test_workflow.py       ← new
    integration/
      test_move_tracker.py   ← new
      test_move_routes.py    ← new
      test_move_pages.py     ← new
      test_routes.py         ← modified (E3)
      test_task_pages.py     ← modified (E4, E5, E6)
      test_comment_pages.py  ← modified (E7)
    e2e/
      test_moves.py          ← new
```

`persistence/`, `main.py`, `errors.py`, `domain/tasks.py`, `domain/refusals.py`, `tests/timed_run.py` and `tests/integration/test_timed_run.py` are unchanged. No directory or `__init__.py` is created.

`docs/SDD.md` § 3 is read for placement. Each new piece of logic is in the task for its owning part's code, as the design places it.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Task split:** the design's one web sub-job C is cut into Task 3 (`web/style.css`), Task 4 (`web/routes.py`, `web/pages.py` and their tests) and Task 5 (the browser test). Style is a content change no test asserts, so it takes the review-verified shape; the browser test asserts what Task 4 delivers and cannot be red before it. The two atomic-landing edges of § 3 C (the route with E3, the moves column and status area with E4–E7) stay inside Task 4 — the route, the decoding and the pages are read by the same R and P tests and have no green point apart.
- **Atomic-landing edge kept:** `domain/workflow.py`, E1 and E2 are Task 1 together, as § 3 A says, because the file's existence fails the three architecture tests until they list `workflow` as landed.
- **Behaviour added:** `test_moving_a_task_keeps_every_task_in_its_place` (Task 1) — § 3 A says only that task's status differs; position in the task tuple is implied by "differs only in that task's `status`" but is not enumerated in § 5.
- **Behaviour added:** `test_list_press_lands_on_the_moved_tasks_own_project_page` (Task 4) — § 3 C resolves the place to "the task's project", and R1 uses one project only, so a second project would catch a handler that redirects to the wrong one.
- **Behaviour locked:** the design leaves implicit that `allowed_moves` is called on the status of the task as the state holds it at press time, not as the page showed (CP-308). Task 2 states it as a behaviour (`test_move_is_checked_against_the_current_state_not_a_stale_page`) so the layer-3 test does not rely on R3 alone.
- **Gate command:** `project.md` gives `pytest products/tracker17/tests/`, run from the worktree root. In this planning environment `pytest` is not installed (`command not found`, `python3 -m pytest` likewise), so the command was not run here; the design measured the identical invocation in a venv built from `tests/requirements.txt` (1091 passed with `tests/e2e` ignored). The command is kept as the card gives it; the runner is a prerequisite the developer's environment has to supply. Setup command on the card is `none`, so nothing builds it.
- **Hints carried:** the § 4 hints for sub-job A, the route, and the pages are carried into Tasks 1 and 4 as `# Hint:` blocks, trimmed to the approach. The hint for `web/style.css` is `None`; DESIGN.md gives every value, so Task 3 is review-verified.
- **Placement:** no placement was corrected. The design already puts the move rule in `domain`, the action and query in `application`, and the controls in `web`; `docs/SDD.md` § 3 agrees.
- **Not carried (set aside upstream):** the spec's CP-315 and its Example (a timed move in `tests/timed_run.py`) are set aside by `change_design.md` § Architect Review Notes R-1. No task touches the timed run.

## Corrections owed while there

- Owed outside this change's reach: `docs/nfdr.md` § 5 QC-48 — says a change that adds a listed action adds it to the timed run, and this change adds moving without adding it to `tests/timed_run.py` → it reads true again once the later station `move-timed-run` adds the timed move; if that station is dropped it needs a dated note in its Review Notes naming moving as the action the run does not time, and why.
- Owed outside this change's reach: `docs/SDD.md` § 4 TS-5 — says a timed run covers every action SRS NFR-1 lists that exists so far, and a slice that adds a listed action adds it to the run → false for the same reason as QC-48, and restored the same way.

---

### Task 1: Status workflow (`domain/workflow.py`, `domain/__init__.py`, `tests/unit/test_workflow.py`, `tests/architecture/test_trace.py`, `tests/architecture/test_shapes.py`)

**Dependencies:** None

**What to build:** The Status workflow feature's entry module, `domain/workflow.py` (SRS FR-18, FR-19). It holds three public names, all re-exported from `domain/__init__.py`:

- `allowed_moves(status: TaskStatus) -> tuple[TaskStatus, ...]` — the moves allowed from `status`, in this order: `todo` gives (`in-progress`, `cancelled`); `in-progress` gives (`done`, `cancelled`, `todo`); `done` and `cancelled` give `()`.
- `move_task(state: TrackerState, task_id: int, target: str) -> tuple[TrackerState, Task]` — the state with that one task's status set to `target`, and the moved task. It checks against the state it is handed, in this order: no task with that identity raises `TaskNotFound`; a `target` that is not exactly one of the four status words (the empty string included) raises `InvalidTaskStatus`; a `target` not in `allowed_moves(current status)` raises `MoveNotAllowed`, a same-status move among them. The returned state differs from the one handed in only in that task's `status`.
- `MoveNotAllowed` — a `Refusal` subclass that carries no message, defined in this module.

The module's opening docstring names SRS FR-18 and FR-19, every taking-part module (`application/tracker.py`, `web/routes.py`, `web/pages.py`) and every test module that checks it (`tests/unit/test_workflow.py`, `tests/integration/test_move_tracker.py`, `tests/integration/test_move_routes.py`, `tests/integration/test_move_pages.py`, `tests/e2e/test_moves.py`) (CP-313). It imports only `domain` siblings, `errors` and the standard library (NFDR QC-13), and every value it defines is immutable (QC-6). `domain/tasks.py` and `domain/refusals.py` are not edited.

The same task makes the two existing architecture tests agree with the module's existence: `tests/architecture/test_trace.py` lists `workflow` in `LANDED_FEATURE_WORDS` (E1), and `tests/architecture/test_shapes.py::test_only_the_task_features_are_added_to_domain` moves `workflow` from the not-yet-landed list to the landed list (E2), keeping its assertions that `filtering`, `sorting` and `summary` do not exist and its `TrackerState` field-set assertion, and adding the CP numbers to its docstring. Nothing else in those two files changes.

#### Behaviours to verify (developer adds tests to `tests/unit/test_workflow.py`; E1 and E2 are edits to the two architecture tests)

- `test_allowed_moves_for_each_status_give_exactly_the_workflow_tuple_in_order` — U1; the four statuses give the four tuples above, in order.
- `test_every_one_of_sixteen_pairs_has_its_outcome` — U2, parametrized with each pair named with its expected outcome as the case id. The 5 allowed moves each assert the moved task's status and that the returned state equals the one handed in except for that task's status. The 11 refused pairs (the four same-status moves, `todo`→`done`, and every move out of `done` or `cancelled` to another status) each assert `MoveNotAllowed` and the state unchanged.
- `test_a_target_that_is_not_a_status_raises_invalid_task_status_and_changes_nothing` — U3; `finished`, the empty string and `Done` raise `InvalidTaskStatus`.
- `test_an_unknown_task_raises_task_not_found_even_with_a_non_status_target` — U4; the check order.
- `test_move_not_allowed_is_a_refusal_and_carries_no_message` — U5.
- `test_allowed_moves_returns_a_tuple_and_the_table_cannot_be_assigned_through` — U6.
- `test_moving_a_task_keeps_every_task_in_its_place` — the moved task keeps its position among the state's tasks; no other task, project, assignee or counter differs.
- E1 — `test_each_feature_word_with_its_domain_module_is_listed_as_landed` and `test_no_excluded_feature_entry_exists` pass with `workflow` listed as landed.
- E2 — `test_only_the_task_features_are_added_to_domain` passes with `workflow` among the landed modules and `filtering`, `sorting`, `summary` still absent.

#### Implement

Infer from failing tests.

# Hint: hold the allowed moves as a module-private immutable mapping (a `types.MappingProxyType` over a literal) from each `TaskStatus` to a tuple. The order of each tuple is the workflow's order, realized by construction and never derived from the enum's member order. Parse the target with the enum's value constructor, turning its `ValueError` into `InvalidTaskStatus` the way `domain/tasks.py`'s `_parse_status` does. Build the new state with `dataclasses.replace` on the one task, then on the state's task tuple, the shape `_with_labels` already uses. `workflow.py` imports `domain.tasks` at module level and `TrackerState` under `TYPE_CHECKING`; `domain/tasks.py` must never import `workflow`, or the two form an import cycle.

#### Verification gate

Run `pytest products/tracker17/tests/` from the worktree root (`tests/e2e` needs Playwright's Chromium and is not part of this task's check; the other layers are).

Pass criteria: `tests/unit/test_workflow.py` and the two architecture tests pass; no new failures elsewhere.

---

### Task 2: Move action and allowed-moves query (`application/tracker.py`, `application/__init__.py`, `tests/integration/test_move_tracker.py`)

**Dependencies:** Task 1 (`move_task`, `allowed_moves`, `MoveNotAllowed`)

**What to build:** `Tracker.move_task(task_id: int, status: str) -> Task`, which applies `domain`'s `move_task` to the current state, saves the new state, makes it current only after the save returns, and returns the moved task (SDD § 4 SD-2). A refusal (`TaskNotFound`, `InvalidTaskStatus`, `MoveNotAllowed`) or a saver failure propagates and the current state stays as it was. It compares nothing and decides nothing (QC-21). `Tracker.allowed_moves(status: TaskStatus) -> tuple[TaskStatus, ...]` is `domain`'s `allowed_moves`, unchanged. `application/__init__.py` re-exports `InvalidTaskStatus` and `MoveNotAllowed` for `web` (QC-5, QC-16; `TaskStatus` is already re-exported). `TaskRow` and `contracts.py` are unchanged: `TaskRow` gains no moves field.

#### Behaviours to verify (developer adds tests to `tests/integration/test_move_tracker.py`; names FR-18, AC-9, AC-13, AC-18)

- `test_the_move_is_saved_before_it_becomes_current` — T1; a recording saver receives the new state, then `tracker.task(id)` shows it. A refused move reaches no save and leaves the state.
- `test_a_moved_task_survives_a_restart_and_only_its_status_differs_in_the_saved_file` — T2; `Write it`, with its fields, is moved to `done` through a real `SavedData`; loading the file again shows `done`, and the saved JSON differs from the pre-move JSON only in that task's `status` value.
- `test_a_failing_saver_raises_and_leaves_the_current_state_as_it_was` — T3.
- `test_allowed_moves_gives_the_domain_tuples` — T4.
- `test_a_task_due_yesterday_moved_to_done_is_not_overdue_and_moved_to_todo_still_is` — T5; a clock handed in at 2026-10-19, a task due 2026-10-18; `overdue` is False in `project_tasks` after `done` and True after `todo`. The test patches no name (QC-28).
- `test_move_is_checked_against_the_current_state_not_a_stale_page` — a task moved to `in-progress` by one call, then the same `todo`→`in-progress` move asked again, raises `MoveNotAllowed` and saves nothing.

#### Implement

Infer from failing tests.

#### Verification gate

Run `pytest products/tracker17/tests/` from the worktree root.

Pass criteria: this task's tests pass; no new failures elsewhere.

---

### Task 3: Move-button style (`web/style.css`)

**Dependencies:** None

**What to build:** The move-button component and the side-by-side moves in a table cell, with the values `docs/DESIGN.md` gives (EX-10): `{components.button-move}`, `{spacing.row-control}` tall with the secondary button's edge, its hover state `button-move-hover`, and the moves in one cell sitting `{spacing.sm}` apart. A move button's pointer target is at least 24 by 24 CSS pixels (UXD UX-A6). The class names the pages use for these are the ones Task 4 writes and this task defines; both take them from DESIGN.md's component names.

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- `web/style.css` move-button rule — its height is DESIGN.md's `row-control` value (28px) and it carries the secondary button's edge, read against DESIGN.md `button-move` (lines 144–151) and § Components.
- `web/style.css` hover rule — matches DESIGN.md `button-move-hover`.
- `web/style.css` moves-in-a-cell rule — controls in one cell sit side by side with `spacing.sm` between them, read against DESIGN.md § Cells.
- `web/style.css` — no other rule changes; `git diff "$(git merge-base main HEAD)" -- products/tracker17/web/style.css` shows additions only.

#### Implement

Verified by review — no test.

#### Verification gate

Run `pytest products/tracker17/tests/` from the worktree root.

Pass criteria: every criterion above is met on reading the diff; the full suite has no new failures.

---

### Task 4: Move route, moves column, status area and landing (`web/routes.py`, `web/pages.py`, `tests/integration/test_move_routes.py`, `tests/integration/test_move_pages.py`, `tests/integration/test_routes.py`, `tests/integration/test_task_pages.py`, `tests/integration/test_comment_pages.py`)

**Dependencies:** Task 2 (`Tracker.move_task`, `Tracker.allowed_moves`, the re-exported `MoveNotAllowed` and `InvalidTaskStatus`)

**What to build:** The route, the pages and the landing that let the operator press a move. All visible words (the moves column header, the status area, the completion line, the two refusal reasons, the failure line, the console message) come from `change_text.md` verbatim.

- **The route.** `POST /tasks/[0-9]+/move`, kind *submission*, behind the existing request check so only a `same-origin` submission is applied (CP-314). Its form fields are the target status and the *place* the button was on, a closed vocabulary of two: the project's list, or the task's page. The handler reads both, does no check of its own on either beyond reading the place word (QC-38), and makes one `Tracker.move_task` call. Its answers: an identity too long to read → the task-not-found page, as the other task actions answer; `TaskNotFound` → a redirect to the task's address, which answers with the not-found page; `MoveNotAllowed` or `InvalidTaskStatus` → a redirect to the place carrying the task identity and one refusal code per type (a closed vocabulary in `pages`, mapped by type, QC-5); success → a redirect to the place carrying the task identity and the status moved to; any other failure goes through `_guarded`, the one catch site, giving the console a line naming the move and the error and the browser a redirect to the place carrying the task identity and a failure marker with the status the move named. The place resolves to `/projects/<the task's project>` or `/tasks/<id>`; a missing or unknown place word answers at the task's page. Every address is built by `_address` and carries no fragment (RT-8, RT-9).
- **The outcome read back from an address.** Decoded with the existing closed-vocabulary decoding. A task identity that is not a row on that page, an unknown code, or a status word that is not one of the four yields no outcome, and the page renders plain.
- **The project's page.** The task table gains a seventh column, *moves*, last in the row. Each row's moves cell holds one form per move the row's status allows except `cancelled`, in the order `application` gives. A `done` or `cancelled` row's cell is empty. Each form posts to the move route with the target status and the place and holds one `<button type="submit">` whose visible label is the status word and whose accessible name is `Move '<title>' to <status>` with the title passed through `_escape`. The status cell's text stays exactly the status word.
- **The task's page.** A status area of its own, a sheet placed after the edit form and before the labels. It shows the current status word in an element of its own, then one form per allowed move except `cancelled`, in the same shape as a row's. A `done` or `cancelled` task shows its status and no button. The area holds no `table` and adds no `dt`, so the page's one `dl` still holds only Project.
- **The landing place, on both pages, for a success, a refusal and a failure.** The element that takes focus is the moved task's *status word element*, in the row's status cell or the task page's status area. It carries `tabindex="-1"`, `autofocus` and `aria-describedby` pointing at the one line. The line is placed beside the moves — in that row's moves cell, or in the status area — and takes no focus and has no `tabindex`. The completion line names the task's title as the state holds it now, through `_escape`, and the status from the address. A page shows at most one such line. A move outcome takes precedence over every other outcome the same address carries (`created`, the add-task form's, the edit form's, the label area's and the comment area's), so exactly one element takes focus.
- **`cancelled` is withheld in one helper** that renders a task's move forms, shared by both pages. Which moves are allowed still comes only from `application`; `web` never works it out.

The seven existing tests the change releases are edited only at the assertions that pin what it removes:

- E3 `tests/integration/test_routes.py` — `SAMPLE_ADDRESS` and `SUBMITTED_BODY` gain `/tasks/[0-9]+/move` → `/tasks/1/move`, with a body naming a move the seed task allows from its status, and a place.
- E4 `tests/integration/test_task_pages.py::test_project_list_shows_every_own_task_in_six_columns` — headers become the six plus the moves header, last, and every row has seven cells; the first six cells keep every value assertion; add that the `in-progress` row's moves cell holds `done`, `todo`, the `todo` row's holds `in-progress`, and a `done` row's is empty; rename the test to say seven columns.
- E5 `…::test_task_page_shows_the_four_fields_in_the_one_authorized_form` — the main area's form-action list admits the one move form a `todo` task offers, after the edit form and before the label form; the absent-word list drops `status` and `todo` and keeps `overdue` and `delete`; every other assertion stays, `dt == ["Project"]` included.
- E6 `…::test_task_page_opens_edit_form_from_saved_values` — each status's form-action list admits that status's move forms after the edit form (one for `todo`, two for `in-progress`, none for `done` and `cancelled`); `focused(root) == []` stays.
- E7 `tests/integration/test_comment_pages.py::test_written_comments_offer_no_edit_delete_or_reply_control` — the form-action list admits the one move form its `todo` task offers, after `/tasks/1`; the no-control and remover checks stay.

#### Behaviours to verify (developer adds tests to `tests/integration/test_move_routes.py` and `tests/integration/test_move_pages.py`; E3–E7 above are edits to existing tests)

Routes (`test_move_routes.py`; names FR-18, FR-19, NFR-3, NFR-4, AC-10, AC-12, AC-13, AC-18):

- `test_a_row_press_saves_and_lands_on_the_project_page_at_the_rows_status` — R1; `Set up CI` in `todo`, `in-progress` pressed with the place set to the list: a redirect to `/projects/1?…` with no `#`, one save, and the landing page has that task's status element focused, reading `in-progress`, the row's buttons `done`, `todo`, and the completion line as its description.
- `test_a_task_page_press_saves_and_lands_on_the_task_page_with_no_buttons_at_done` — R2; redirect to `/tasks/<id>?…`, status `done`, no buttons, the line describing the focused status element.
- `test_a_stale_press_is_refused_against_the_saved_status_and_saves_nothing` — R3; the page showed `todo`, another tab moved the task to `in-progress`, then `in-progress` is pressed: the saved file's bytes are equal before and after, and the page shows the refusal reason as the focused element's description.
- `test_a_stale_todo_press_after_done_is_refused_and_the_task_stays_done` — R4.
- `test_a_non_status_or_missing_status_is_refused_and_answered_like_a_stale_press` — R5; `finished` and no status field, nothing saved.
- `test_an_unknown_task_and_an_unreadable_identity_get_the_not_found_page_and_nothing_is_saved` — R6; task 999, and an identity of more digits than an int reads.
- `test_a_failing_saver_reports_on_the_console_and_the_page_without_exception_text` — R7; stderr's first line names the move and the next names the error; the landing page's failure line describes the focused element and holds no exception text or traceback; state and saved file unchanged (QC-56, QC-57).
- `test_a_submission_not_marked_same_origin_is_refused_and_a_get_changes_nothing` — R8; `none`, `same-site` and unmarked submissions, and a GET to `/tasks/1/move`.
- `test_reloading_the_landing_address_shows_the_same_line_and_saves_nothing` — R9; twice.
- `test_overdue_clears_on_done_and_stays_on_todo_on_the_row` — R10; today 2026-10-19 by the clock handed in: A due 2026-10-18 and `in-progress` shows `Overdue`, then after `done` is pressed no `Overdue`; B, the same, after `todo` still shows `Overdue`.
- `test_a_missing_or_unknown_place_answers_at_the_tasks_page` — R11.
- `test_list_press_lands_on_the_moved_tasks_own_project_page` — with tasks in two projects, a list press on the second project's task redirects to that project's page, not the first's.

Pages (`test_move_pages.py`; names FR-19, AC-12, NFR-12, UX-A6):

- `test_each_status_row_offers_exactly_its_allowed_moves_except_cancelled` — P1; one project with tasks in all four statuses: the `todo` row has `in-progress`, the `in-progress` row has `done` then `todo`, the `done` and `cancelled` rows have empty moves cells. No element anywhere on the project page or on any task page has the text, value or name of a `cancelled` move, and no page has a confirmation.
- `test_task_page_shows_the_status_in_words_and_its_moves` — P2; `in-progress`: status in words, buttons `done` then `todo`; `done`: the status and no button.
- `test_the_done_button_name_is_move_title_to_done_on_the_row_and_the_task_page` — P3; `Move 'Set up CI' to done`.
- `test_every_move_control_is_a_lone_submit_button_in_a_post_form_with_no_tabindex_accesskey_or_disabled` — P4.
- `test_the_completion_line_and_button_name_escape_the_title_once` — P5; the line for `a < b & c` reads `You moved 'a < b & c' to in-progress.` exactly as `change_text.md` words it, and the button's name holds the title once-escaped (QC-36).
- `test_a_landing_page_has_exactly_one_autofocus_on_a_non_control_status_element_that_names_the_line` — P6; `tabindex="-1"`, inside the moved row (or the status area), `aria-describedby` naming the line; the line has no `autofocus` or `tabindex`; exactly one completion line.
- `test_a_move_outcome_wins_over_created_label_and_comment_outcomes` — P7; exactly one focus, the move's.
- `test_forged_outcomes_render_the_page_plain` — P8; an unknown refusal code, a non-status `moved` word, or a task identity not on that page.

#### Implement

Infer from failing tests.

# Hint: follow the label actions' shape (`_add_label`) for the route — the identity read, a nested `act` passed to `_guarded`, one `except` per refusal type, and `_redirect` through `_address`. Read the task once before acting, as `_edit_task` does, so a refusal or a failure on a row can name `/projects/<project>` and the console line can name the title. Decode the outcome with `_closed` over closed vocabularies (`TaskStatus` and the new refusal enum) and `_position` for the identity. For the pages, the focus target is the non-control pattern `_label_row` already uses (`tabindex="-1"`, `autofocus`, `aria-describedby`); withhold `cancelled` in the one helper that renders a task's move forms so both pages share it.

#### Verification gate

Run `pytest products/tracker17/tests/` from the worktree root, then from the product root `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web` (NFDR QC-62).

Pass criteria: this task's tests and the edited E3–E7 pass; the three QC-62 commands exit 0; no new failures elsewhere.

---

### Task 5: Browser test of the moves (`tests/e2e/test_moves.py`)

**Dependencies:** Task 3, Task 4

**What to build:** One end-to-end test module, layer 5, naming NFR-12, UX-A6 and AC-13, that drives the moves in a real browser. It settles what only a browser settles: Space and Enter pressing a move button (CP-300), the 24 by 24 pointer floor, and `autofocus` on an element inside a table cell (SDD § 11 R-2). The existing `tests/e2e/test_labels.py` and `tests/e2e/test_comments.py` are the precedent for the fixture and the Tab sequences.

#### Behaviours to verify (developer adds tests to `tests/e2e/test_moves.py`)

- `test_tab_to_a_rows_move_button_and_press_space_lands_on_that_rows_status_element` — E2E1; in Chromium, from the project page, Tab until a row's `in-progress` button has focus and press Space. The page lands with that row's status element focused, in the viewport, `tabIndex` −1, and its computed accessible description is the completion line.
- `test_the_same_move_from_the_task_page_with_enter_lands_on_the_status_area` — E2E1, the task page with Enter.
- `test_every_move_button_is_at_least_24_by_24_pixels` — every move button's bounding box on both pages.

#### Implement

Tests cannot go red.

Reason: the behaviour these tests assert, the moves on rows and the task's page and their landing, is built by Task 4 (and styled by Task 3); the browser test is written after it and checks it, so no failing version of it exists to commit first.

#### Verification gate

Run `pytest products/tracker17/tests/` from the worktree root. `tests/e2e` needs Playwright's Chromium (SDD § 4 RT-4); it was not installed where the design was measured, so these tests could not run there.

Pass criteria: `tests/e2e/test_moves.py` passes where Chromium is installed; no new failures elsewhere.
