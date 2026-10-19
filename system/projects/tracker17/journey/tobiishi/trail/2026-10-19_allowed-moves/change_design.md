# Change Design — Moving a task along its allowed status moves

**Date:** 2026-10-19
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the move buttons on every project-list row and on the task's page (their visible labels and their accessible names), the heading of the new moves column in a project's task list, the status area on the task's page, the one-line confirmation after a move, the reason shown when a move is refused, and the message when a move fails, on the page and on the console

---

## 1. Change Summary

The operator can move a task along the moves the status workflow allows, by pressing a button on any
row of a project's task list or on the task's own page. Three parts change, in dependence order.
`domain` gains the Status workflow feature's entry module, `domain/workflow.py`. It holds the allowed
moves per status, a new typed refusal for a move the workflow refuses, and the rule that applies a
move to the tracker state. `application` gains one action that applies that rule and saves, and one
query that hands the allowed moves to `web`. `web` gains the move route, a seventh *moves* column in
the task list, a status-and-moves area on the task's page, the landing place and its line after a
move, and the move button's style. `persistence` and `main` do not change, and nor does the saved
data's format. The `cancelled` move stays allowed by the rule but is offered by no page. The timed
run does not change here: the spec's CP-315 is set aside (§ Architect Review Notes, R-1).

Paths below are relative to the product root, `products/tracker17/`.

---

## 2. Blast Radius

Placement by `docs/SDD.md` § 3. Each new piece of logic and its owning part:

- **The allowed moves per status, in CP-293's order** — `domain` ("every rule that accepts or
  refuses a change").
- **Refusing every other move, a target that is not a status, and a task that does not exist** —
  `domain` ("one typed refusal per refused condition"). The workflow refusal is new. The other two
  reuse `InvalidTaskStatus` and `TaskNotFound`.
- **Applying an accepted move to the state: the one task's status, nothing else** — `domain`
  ("every function … returns a new value").
- **The move action: apply the rule to the current state, save, then make it current** —
  `application` ("each action is one call that applies a `domain` rule").
- **Handing `web` the allowed moves for a status** — `application` ("answers what a page needs to
  show").
- **The move address, reading the form, answering with a redirect, building the buttons, the landing
  place and its line, and withholding the `cancelled` control in this slice** — `web` ("the addresses
  of pages and actions, reading form fields … building each whole HTML page and the one
  stylesheet").

| Module | Status | What changes |
|---|---|---|
| `domain/` | Modified | **New `domain/workflow.py`**, the Status workflow entry (SDD § 4 TS-3). It holds the `domain` part's new logic: the immutable table of allowed moves per status, the query for one status's moves, the new refusal `MoveNotAllowed`, and the move rule `move_task`. `domain/__init__.py` re-exports the three public names. `domain/tasks.py`, `domain/refusals.py` and the other modules are unchanged. |
| `application/` | Modified | `application/tracker.py`: `Tracker` gains the move action (the `application` part's "one call that applies a `domain` rule") and the allowed-moves query. `application/__init__.py` re-exports `InvalidTaskStatus` and `MoveNotAllowed` for `web` (NFDR QC-5, QC-16). `TaskRow` and `contracts.py` are unchanged. |
| `web/` | Modified | `web/routes.py`: one submission route, `POST /tasks/[0-9]+/move`, and its handler. It also passes the allowed moves and the move outcome read from the address to the two page builders. `web/pages.py`: the seventh moves column, the move forms, the status area on the task's page, and the landing place, line, reason and failure. `web/style.css`: the move-button component and the side-by-side moves in a cell, from `docs/DESIGN.md`. |
| `persistence/` | Unchanged | — (the saved data is unchanged: a status is already saved as its word, `persistence/saved_data.py:138`) |
| `main.py` | Unchanged | — |
| `errors.py` | Unchanged | — |
| `tests/` | Modified | New: `tests/unit/test_workflow.py`, `tests/integration/test_move_tracker.py`, `tests/integration/test_move_routes.py`, `tests/integration/test_move_pages.py`, `tests/e2e/test_moves.py`. Changed: seven existing tests, listed in § 5. `tests/timed_run.py` and `tests/integration/test_timed_run.py` are unchanged. |

**Transitive check (`docs/nfdr.md` § 1.2).** `domain`'s public surface gains names and changes none,
so `persistence` (QC-15), which imports `domain`, is not affected. `application`'s surface gains two
re-exports and two `Tracker` methods and changes none, so nothing else that imports it is affected
beyond `web`, which is in the table. `main.py` builds `Tracker` and `Site` with unchanged signatures.
No new import crosses a part boundary. `web` reaches the moves only through `application`, and
`domain/workflow.py` imports only `domain` siblings, `errors` and the standard library (QC-13).

---

## 3. Sub-jobs

### Sub-job A — `domain/`
**Scope:** the new module `domain/workflow.py` and its re-exports in `domain/__init__.py`. Its
opening docstring names SRS FR-18 and FR-19, every taking-part module (`application/tracker.py`,
`web/routes.py`, `web/pages.py`), and every test module that checks it (the five new modules of § 5)
(CP-313). Also the two existing architecture tests that the module's existence decides (§ 5, rows
E1 and E2).
**Exposes:**
- `allowed_moves(status: TaskStatus) -> tuple[TaskStatus, ...]` gives the moves allowed from
  `status`, in CP-293's order. `todo` gives (`in-progress`, `cancelled`), and `in-progress` gives
  (`done`, `cancelled`, `todo`). `done` and `cancelled` give `()`.
- `move_task(state: TrackerState, task_id: int, target: str) -> tuple[TrackerState, Task]` gives the
  state with that one task's status set to `target`, and the moved task. It checks against the state
  it is handed, never against what a page showed (CP-308), in this order. No task with that identity
  raises `TaskNotFound`. A `target` that is not exactly one of the four status words raises
  `InvalidTaskStatus`, and that includes the empty string. A `target` not in
  `allowed_moves(current status)` raises `MoveNotAllowed`. A same-status move is one of those. Every
  accepted move changes the state, so there is no "no change" outcome. The returned state differs
  from the one handed in only in that task's `status` (CP-295).
- `MoveNotAllowed`, a `Refusal` subclass that carries no message, defined in `domain/workflow.py`.
- All three are re-exported from `domain`.
**Depends on:** none.
**Atomic-landing edge:** `domain/workflow.py` + `tests/architecture/test_trace.py` (E1) +
`tests/architecture/test_shapes.py` (E2). No green point lies between them. The file's existence
fails `test_each_feature_word_with_its_domain_module_is_listed_as_landed`,
`test_no_excluded_feature_entry_exists` and `test_only_the_task_features_are_added_to_domain` until
those two test modules list `workflow` as landed (measured; § Architect Review Notes, the evidence
note).

### Sub-job B — `application/`
**Scope:** `Tracker.move_task` and `Tracker.allowed_moves` in `application/tracker.py`, and the
two re-exports in `application/__init__.py`.
**Exposes:**
- `Tracker.move_task(task_id: int, status: str) -> Task` applies sub-job A's `move_task` to the
  current state, saves the new state, makes it current only after the save returns, and returns the
  moved task (SDD § 4 SD-2). A refusal (`TaskNotFound`, `InvalidTaskStatus`, `MoveNotAllowed`) or a
  saver failure propagates, and the current state stays as it was. It compares nothing and decides
  nothing (QC-21).
- `Tracker.allowed_moves(status: TaskStatus) -> tuple[TaskStatus, ...]` is sub-job A's
  `allowed_moves`, unchanged.
- `application` re-exports `InvalidTaskStatus` and `MoveNotAllowed`. `TaskStatus` is already
  re-exported.
- `TaskRow` is **unchanged**: it gains no moves field (§ Architect Review Notes, D-9).
**Depends on:** Sub-job A (`move_task`, `allowed_moves`, `MoveNotAllowed`).

### Sub-job C — `web/`
**Scope:** `web/routes.py`, `web/pages.py` and `web/style.css`, plus the four existing tests the new
route and the new page content decide (§ 5, rows E3 to E7, except E1 and E2). One sub-job, not cut
below the module. The route, the pages and the style change for one reason, the moves, and none has a
green point of its own against the existing page tests.
**Exposes (to the browser; no other part consumes `web`):**
- **The route.** `POST /tasks/[0-9]+/move`, kind *submission*. It sits behind the existing request
  check, so only a `same-origin` submission is applied (CP-314). Its form fields are the target
  status and the *place* the button was on, which is a closed vocabulary of two: the project's list,
  or the task's page. The handler reads both, does no check of its own on either beyond reading the
  place word (QC-38), and makes one `Tracker.move_task` call. Its answers:
  - An identity too long to read: the task-not-found page, as the other task actions answer.
  - `TaskNotFound`: a redirect to the task's address, which answers with the not-found page (CP-310).
  - `MoveNotAllowed` or `InvalidTaskStatus`: a redirect to the place, carrying the task identity and
    one refusal code per type. The two codes are a closed vocabulary in `pages`, mapped by type
    (QC-5).
  - Success: a redirect to the place, carrying the task identity and the status the task moved to.
  - Any other failure goes through `_guarded`, the one catch site. The console gets a line naming the
    move and the error, and the browser gets a redirect to the place carrying the task identity and a
    failure marker with the status the move named (CP-311).
  - The place resolves to the project's page `/projects/<the task's project>` or to `/tasks/<id>`. A
    missing or unknown place word answers at the task's page. Every address is built by `_address`
    and carries no fragment (RT-8, RT-9).
- **The outcome read back from an address.** It is read with the existing closed-vocabulary
  decoding. A task identity that is not a row on that page, an unknown code, or a status word that is
  not one of the four yields no outcome, and the page renders plain.
- **The project's page.** The task table gains a seventh column, *moves*, last in the row, with a
  header word from the content stage. Each row's moves cell holds one form per move the row's status
  allows, except `cancelled`, in the order `application` gives (CP-297, CP-301). A `done` or
  `cancelled` row's moves cell is empty. Each form posts to the move route with the target status and
  the place, and holds one `<button type="submit">`. The button's visible label is the status word.
  Its accessible name is `Move '<title>' to <status>`, with the title passed through `_escape`
  (CP-298). The status cell's text stays exactly the status word.
- **The task's page.** It gains a status area of its own, a sheet placed after the edit form and
  before the labels (UXD UX-S6's order). It shows the current status word in an element of its own,
  then one form per allowed move except `cancelled`, in the same shape as a row's (CP-297, CP-299). A
  `done` or `cancelled` task shows its status and no button. The area holds no `table` and adds no
  `dt`, so the page's one `dl` still holds only Project.
- **The landing place, on both pages, for a success, a refusal or a failure** (CP-303, CP-304,
  CP-308, CP-311). The element that takes focus is the moved task's *status word element*: in the
  row's status cell, or in the task page's status area. It carries `tabindex="-1"`, `autofocus` and
  `aria-describedby`, pointing at the one line. The line is placed beside the moves: in that row's
  moves cell, or in the status area. It takes no focus and has no `tabindex` (EX-14).
  - The completion line names the task's title as the state holds it now, through `_escape`, and the
    status from the address (CP-305).
  - The refusal line is the reason for the code.
  - The failure line says the move did not happen and nothing changed.
  - All three are worded by the content stage.
  - A page shows at most one such line. A move outcome takes precedence over every other outcome the
    same address carries (`created`, the add-task form's, the edit form's, the label area's and the
    comment area's), so exactly one element takes focus.
- **The stylesheet.** It gains DESIGN.md's `{components.button-move}`, `{spacing.row-control}` tall
  with the secondary button's edge, and its hover state. The moves in one cell sit side by side,
  `{spacing.sm}` apart. The values are DESIGN.md's (EX-10). A move button's pointer target is at least
  24 by 24 CSS pixels (UXD UX-A6).
**Depends on:** Sub-job B (`Tracker.move_task`, `Tracker.allowed_moves`, the re-exported
`MoveNotAllowed` and `InvalidTaskStatus`).
**Atomic-landing edges:**
- The move route + `tests/integration/test_routes.py`'s sample (E3). No green point lies between
  them, because the route test fails on a route without a sample address (Verified Claims in the
  spec).
- The moves column and the status area + E4, E5, E6 and E7. No green point lies between them,
  because each of those tests pins a page these change (measured).

**Build sequence:**
```
Sub-job A  (domain)
  → Sub-job B  (application)    needs A's move_task, allowed_moves, MoveNotAllowed
    → Sub-job C  (web)          needs B's Tracker.move_task, Tracker.allowed_moves and the re-exports
```
The chain is strictly sequential, following the import graph: `web` → `application` → `domain`
(NFDR QC-14, QC-16).

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — `domain/workflow.py` | Hold the allowed moves as a module-private immutable mapping (a `types.MappingProxyType` over a literal) from each `TaskStatus` to a tuple. The order of each tuple *is* CP-293's order, so the order is realized by construction, never derived from the enum's member order. Parse the target with the enum's value constructor, turning its `ValueError` into `InvalidTaskStatus` as `domain/tasks.py`'s `_parse_status` does. Build the new state with `dataclasses.replace` on the one task, then on the state's task tuple, the shape `_with_labels` already uses. `workflow.py` imports `domain.tasks` at module level and `TrackerState` under `TYPE_CHECKING`. `domain/tasks.py` must never import `workflow`, or the two form an import cycle. |
| A — `domain/__init__.py` re-exports | None |
| B — `Tracker.move_task`, `Tracker.allowed_moves`, re-exports | None |
| C — `web/routes.py` move route and outcome decoding | Follow the label actions' shape (`_add_label`): the identity read, a nested `act` passed to `_guarded`, one `except` per refusal type, and `_redirect` through `_address`. Read the task once before acting, as `_edit_task` does, so a refusal or a failure on a row can name `/projects/<project>` and the console line can name the title. Decode the outcome with `_closed` over closed vocabularies (`TaskStatus` and the new refusal enum) and `_position` for the identity. |
| C — `web/pages.py` moves, status area, landing | The focus target is the non-control pattern `_label_row` already uses: `tabindex="-1"`, `autofocus` and `aria-describedby`. Withhold `cancelled` in the one helper that renders a task's move forms, so both pages share it. |
| C — `web/style.css` | None — DESIGN.md's `button-move` entry and its cell rule give every value |

---

## 5. Test Additions

### New tests

| Sub-job | Test file | What to add |
|---|---|---|
| A | `tests/unit/test_workflow.py` (new; layer 1; names FR-18, FR-19, AC-12) | **U1.** `allowed_moves` for each of the four statuses gives exactly CP-293's tuple, in order (Examples 1–3). **U2.** CP-296's 16 cases, parametrized, each pair named with its expected outcome as the case id. The 5 allowed moves each assert the moved task's status and that the returned state equals the one handed in except that task's status. The 11 refused pairs each assert `MoveNotAllowed` and the state unchanged (Examples 4–8). **U3.** A target that is not a status (`finished`, empty, `Done`) raises `InvalidTaskStatus` and changes nothing (CP-309). **U4.** An unknown task identity raises `TaskNotFound`, even with a non-status target (check order). **U5.** `MoveNotAllowed` is a `Refusal` and carries no message (QC-5, QC-20). **U6.** `allowed_moves` returns a tuple, and the module's table cannot be assigned through (QC-6). |
| B | `tests/integration/test_move_tracker.py` (new; layer 3; names FR-18, AC-9, AC-13, AC-18) | **T1.** The move is saved before it becomes current: a recording saver receives the new state, then `tracker.task(id)` shows it. A refusal reaches no save and leaves the state (QC-21, SD-2). **T2.** The CP-295 Example: `Write it`, with its fields, is moved to `done` through a real `SavedData`. Load the saved file again: the task is `done`, and the saved JSON differs from the pre-move JSON only in that task's `status` value (the restart). **T3.** A failing saver: the move raises, the current state is the old one. **T4.** `Tracker.allowed_moves` gives domain's tuples. **T5.** CP-307 at the tracker: with a clock handed in at 2026-10-19, a task due 2026-10-18 moved to `done` has `overdue` False in `project_tasks`, and one moved to `todo` keeps it True. The test patches no name (QC-28). |
| C | `tests/integration/test_move_routes.py` (new; layer 3; names FR-18, FR-19, NFR-3, NFR-4, AC-10, AC-12, AC-13, AC-18) | **R1.** A row press: `Set up CI` in `todo`, press `in-progress` with the place set to the list. The answer is a redirect to `/projects/1?…` with no `#`, and the saver received one save. The landing page has `Set up CI`'s status element focused, reading `in-progress`, the row's buttons `done`, `todo`, and the description `You moved 'Set up CI' to in-progress.` (Example 15). **R2.** A task-page press of `done`: the redirect is to `/tasks/<id>?…`, and the landing shows status `done`, no buttons, and the line describing the focused status element (Example 16). **R3.** The stale tab, CP-312: the page showed `todo`, another tab moved the task to `in-progress`, then `in-progress` is pressed. The saved file's bytes are equal before and after, and the page answered shows the refusal reason as the focused element's description (Example 21). **R4.** In-progress shown, then moved to `done` elsewhere, then `todo` pressed: refused, still `done` (Example 22). **R5.** Status `finished`, and no status field: refused, nothing saved, answered as R3 (Example 23). **R6.** Task 999, and an identity of more digits than an int reads: the not-found page, nothing saved (Example 24). **R7.** The saver fails: stderr's first line names the move, the next names the error. The landing page's failure line describes the focused element and holds no exception text or traceback, and the state and saved file are unchanged (Example 25; QC-56, QC-57). **R8.** A move submission marked `none`, `same-site` or unmarked is refused, and a GET to `/tasks/1/move` changes nothing (Example 26). **R9.** Reload the landing address twice: the same line each time, and no save (Example 18; CP-306). **R10.** CP-307 on the row, the request's named test: today 2026-10-19 by the clock handed in. A, due 2026-10-18 and `in-progress`, shows `Overdue` and then, after `done` is pressed, no `Overdue`. B, the same, after `todo` still shows `Overdue` (Examples 19–20). **R11.** A missing or unknown place answers at the task's page. |
| C | `tests/integration/test_move_pages.py` (new; layers 3–4; names FR-19, AC-12, NFR-12, UX-A6) | **P1.** One project with tasks in all four statuses: the `todo` row has `in-progress`, the `in-progress` row has `done` then `todo`, and the `done` and `cancelled` rows have empty moves cells. No element anywhere on the page or on any task page has the text, value or name of a `cancelled` move, and no page has a confirmation (Example 10; CP-301). **P2.** The task page in `in-progress`: status `in-progress` in words, the buttons `done` then `todo`. The task page in `done` shows `done` and no button (Examples 11–12). **P3.** The `done` button's accessible name on `Set up CI`'s row is `Move 'Set up CI' to done`, and the same on the task page (Example 13). **P4.** Every move control is a `<button type="submit">` alone in a `<form method="post">`, with no `tabindex`, no `accesskey` and no `disabled`. This is the structural half of CP-300, the browser's own keys (Example 14, with E2E1). **P5.** The landing line for `a < b & c` reads `You moved 'a < b & c' to in-progress.` exactly, and the button's name holds the title once-escaped (Example 17; QC-36). **P6.** Exactly one `autofocus` element on a landing page. It is not a form control, has `tabindex="-1"`, sits inside the moved row (or the status area), and its `aria-describedby` names the line. The line has no `autofocus` or `tabindex`, and the page holds exactly one completion line (CP-303–CP-305; EX-14). **P7.** Precedence: an address carrying a move outcome together with `created`, a label outcome or a comment outcome still has exactly one focus, the move's. **P8.** Forged outcomes: an unknown refusal code, a non-status `moved` word, or a task identity not on that page renders the page plain. |
| C | `tests/e2e/test_moves.py` (new; layer 5; names NFR-12, UX-A6, AC-13) | **E2E1.** In Chromium, from the project page, Tab until a row's `in-progress` button has focus and press Space. The page lands with that row's status element focused, in the viewport, `tabIndex` −1, and its computed accessible description is the completion line. On the task page the same, with Enter. Every move button's bounding box is at least 24×24 (Example 14; CP-300, CP-303; SDD § 11 R-2, the risk that `autofocus` in a table cell misbehaves). |

### Existing tests that change

Each changes only at the assertions that pin what this change removes, and keeps every other
assertion as it is.

| Sub-job | Test | What to modify |
|---|---|---|
| A | **E1.** `tests/architecture/test_trace.py` — `LANDED_FEATURE_WORDS` | Add `workflow` (CP-313; NFDR QC-11). Both `test_each_feature_word_with_its_domain_module_is_listed_as_landed` and `test_no_excluded_feature_entry_exists` then pass. Nothing else changes (Example 27). |
| A | **E2.** `tests/architecture/test_shapes.py::test_only_the_task_features_are_added_to_domain` | Move `workflow` from the not-yet-landed list to the landed list. Keep its assertion that `filtering`, `sorting` and `summary` do not exist and its `TrackerState` field-set assertion. Add the CP numbers to its docstring. |
| C | **E3.** `tests/integration/test_routes.py` — `SAMPLE_ADDRESS` and `SUBMITTED_BODY` | Add `/tasks/[0-9]+/move` → `/tasks/1/move`, with a body naming a move the seed task allows from its status, and a place. `test_every_route_leaves_state_and_headers_as_the_rules_say` then covers the move as accepted, saved once, redirected, with no cookie and with the page policy header (CP-314; QC-7, QC-8, QC-33, QC-34). The QC-35 audit test reads the same samples. |
| C | **E4.** `tests/integration/test_task_pages.py::test_project_list_shows_every_own_task_in_six_columns` | Headers become the six plus the moves column's header word, last, and every row has seven cells. The first six cells keep every value assertion. Add: the `in-progress` row's moves cell holds `done`, `todo`, the `todo` row's holds `in-progress`, and a `done` bulk row's is empty. Rename it to say seven columns (spec Gap 12; § Architect Review Notes, D-14). |
| C | **E5.** `tests/integration/test_task_pages.py::test_task_page_shows_the_four_fields_in_the_one_authorized_form` | The main area's form-action list admits the one move form each `todo` task offers, after the edit form and before the label form. The absent-word list drops `status` and `todo` and keeps `overdue` and `delete`. Every other assertion stays, the `dt == ["Project"]` included. |
| C | **E6.** `tests/integration/test_task_pages.py::test_task_page_opens_edit_form_from_saved_values` | Each status's form-action list admits that status's move forms after the edit form: one for `todo`, two for `in-progress`, none for `done` and `cancelled`. `focused(root) == []` stays: a plain page has no move outcome. |
| C | **E7.** `tests/integration/test_comment_pages.py::test_written_comments_offer_no_edit_delete_or_reply_control` | The form-action list admits the one move form its `todo` task offers, after `/tasks/1`. The checks that a written comment holds no control, and the remover values, stay. |

### What this change stops proving

Each retired assertion, and where its clause goes:

- **E2** stops proving "`domain/workflow.py` does not exist". The clause itself is gone: the feature
  has landed, and E1 proves the reverse.
- **E5** stops proving "the task page shows no `status` and no `todo`". That clause is gone too,
  because CP-299 reverses it, and P2 proves the status is shown. The form-action list goes on proving
  that only the authorized forms exist, now with the move forms named.
- **E4, E6 and E7** each stop proving an exact form or cell count without moves. In each, the same
  count is re-proved with the moves named. P1 proves which moves those are.
- **E1** stops listing `workflow` as not landed. The clause is gone, and the pointer test checks the
  reverse.

No other assertion is retired.

### Example and rule coverage

| Spec Example / rule | Covered by |
|---|---|
| Examples 1–8 (the rule, its 16 cases) | U1, U2 (CP-293, CP-294, CP-296) |
| Example 9 (`Write it` to `done`, restart) | T2 |
| Examples 10–14 | P1, P2, P3, P4 + E2E1 |
| Examples 15–17 | R1, R2, P5, P6 |
| Example 18 (reload) | R9 |
| Examples 19–20 (overdue) | R10 (page), T5 (tracker) |
| Examples 21–23 (stale tab, non-status) | R3, R4, R5, U3 |
| Example 24 (task 999) | R6, U4 |
| Example 25 (save fails) | R7, T3 |
| Example 26 (GET, not `same-origin`) | E3, R8 |
| Example 27 (pointer test) | E1 |
| Example 28 (`python3 tests/timed_run.py` times a move) | **Not carried: CP-315 is set aside** (§ Architect Review Notes, R-1; `deferred_decisions.md`) |
| Example 29 (layer-6 walks, ruff, mypy) | the existing layer-6 walks (QC-6, QC-13–QC-16, QC-28) over the new module, and the three QC-62 commands; no new test |
| Example 30 (`pytest products/tracker17/tests/` exits 0) | the whole suite, with E1–E7 the only existing tests changed (§ Architect Review Notes, R-2) |

Rule-implied edges:

- CP-294 says the state is unchanged after a refusal: U2 and R3.
- CP-303 says the address carries no fragment: R1 and R2.
- CP-305 says the page shows exactly one line: P6.
- CP-308 says a refused move is checked against the saved status, not the shown one: R3 and R4.
- CP-309 says a missing status is refused: R5 and U3.
- CP-310 says an unreadable identity gets the not-found page: R6.
- CP-311 says no Python text reaches a page: R7.
- A forged outcome renders the page plain: P8.
- Outcome precedence keeps exactly one focus: P7.
- An unknown place answers at the task's page: R11.
- CP-307 says no test patches a name: the QC-28 layer-6 walk, over T5 and R10.

---

## Records this change makes false

- `docs/nfdr.md` § 5 QC-48 says "a change that adds a listed action adds it to the run". SRS NFR-1
  lists "moving". This change adds moving and, with CP-315 set aside, does not add it to
  `tests/timed_run.py`. From this landing, the run that QC-48's `verified by:` names no longer covers
  every listed action that exists, and this change is one that did not add its action. → The wording
  needs no edit if the station `move-timed-run` adds the timed move. It goes true again then. If that
  station is dropped, QC-48 needs a dated note in its Review Notes naming moving as the action the run
  does not time, and why.
- `docs/SDD.md` § 4 TS-5 says "A timed run covers every action SRS NFR-1 lists that exists so far …
  A slice that adds a listed action adds it to the run." That goes false for the same reason and is
  restored the same way. It is § 4, not § 3, and is listed because it goes false with QC-48.

Read and found still true: `adr/` 0001–0009 (ADR-0006's "the last action travels in the page
address" is how the landing is built); `fdr.md` R-52 to R-56, R-68 and R-102; `R-56` says the tracker
"offers only the moves allowed", which withholding `cancelled` keeps true; `nfdr.md` §§ 1–3 and § 4
(QC-46: no saved field is added); `SDD.md` § 3, all five rows and the seams. The UXD sentence this
change leaves unmet, UX-I1's "offers exactly the moves allowed", is already handed on by
development-specs in `deferred_decisions.md`.

---

## Architect Review Notes

### Readings taken where the spec conflicts with the request or the tree (Step 7)

- **R-1 — CP-315 (the timed run) and its Example are set aside (a).**
  - *The conflict.* CP-315 adds a timed move to `tests/timed_run.py`. The request says "no change to
    `tests/timed_run.py`" and sizes the timed run into the later station `move-timed-run`. The tree
    pins the run too. `tests/integration/test_timed_run.py::test_timed_run_appends_exactly_three_ordered_action_blocks`
    asserts the run's printed labels are exactly the old ones plus three blocks, "no more". The
    module's `whole_run` fixture also feeds `main` an exact count of timer readings. Neither test is
    named as changing in CP-318.
  - *The readings.* Carrying CP-315 breaks those existing tests and does what the request forbids.
    Setting it aside keeps every existing test and delivers everything the request asks. That is the
    reading taken.
  - *What it leaves unmet.* QC-48 and TS-5, listed under § Records this change makes false, and
    handed on in `deferred_decisions.md`. The spec's line "How the run's new part is itself checked is
    development-design's to decide" is moot.
- **R-2 — CP-318's list of the tests that change is extended from three to seven (a).**
  - *What was found.* A prototype of this design was run against the existing suite in a disposable
    clone at `c01872b`, and eight tests failed. They were the three CP-318 names (the two pointer
    tests count as one change, E1) and four more: E2, E5, E6 and E7.
  - *Why each fails.* Each of the four pins exactly what the request asks to change. E2 asserts
    `domain/workflow.py` does not exist (CP-293 and the request create it). E5 asserts the task page
    shows neither `status` nor `todo` (CP-299 shows the status in words). E5, E6 and E7 assert the
    task page's exact form list (CP-297 adds the move forms).
  - *Why no other reading works.* A reading that kept those assertions would drop the task page's
    moves or the workflow module, both of which the request asks for. Moving the buttons into the
    edit form with `formaction` still breaks E5's status words and its one-button assertion, and would
    make Enter in an edit field able to trigger a move. It was rejected.
  - *The reading taken.* CP-293, CP-297 and CP-299 release exactly those assertions, the way the
    spec's Gap 12 released the six-column test, and every other assertion in the four tests stays.
    Only CP-318's "except the three named as changing" is not carried. Handed on in
    `deferred_decisions.md`.
- **R-3 — CP-316's first sentence is read as NFDR QC-13, the rule it cites (a).**
  - *The two readings.* "The workflow module imports only `errors` and the standard library" can be
    read literally, as no `domain` sibling either, or as QC-13's part-level allowance.
  - *Why the literal reading fails.* It forces three things. The move rule would move into
    `domain/tasks.py`. The new refusal would move into `domain/refusals.py`, or be defined from
    `AppError` and so outside the `Refusal` family that `domain/refusals.py` and the existing
    per-refusal tests treat as every refusal's base. The table would have to work in bare strings.
    The first two edit files the request says "stay as they are".
  - *The reading taken.* The QC-13 reading keeps both files untouched and keeps every QC-13 walk
    green. `workflow.py` imports `domain.tasks` and `domain.refusals` (domain siblings), `errors`
    through them, and the standard library, and no other part. Handed on in `deferred_decisions.md`.
- **R-4 — the request's file fence (a), extending the spec's Gap 1.** The spec already reads the
  fence by intent, for `application/`. This design also changes `domain/__init__.py` (re-exports,
  the import convention `application` follows) and `web/style.css`. The stylesheet is the `web`
  part's "one stylesheet", and DESIGN.md's `button-move` and moves-cell rules have no other home
  (EX-10). Both read as "the pages and routes that offer the moves". `domain/tasks.py`,
  `domain/refusals.py`, `persistence/` and `main.py` stay as they are.

### Decisions the spec left implicit (b)

- **D-1 — The moves column is a seventh column, last in the row.** This is DESIGN.md's column order,
  "title, status, priority, assignee, labels, due date and moves". It keeps the status cell's text
  exactly the status word, and keeps every existing cell index. `tests/e2e/test_labels.py:168` reads
  cell 4, and the page tests read cells 0, 3, 4 and 5. This settles the choice the spec's Gap 12 left
  to design.
- **D-2 — The status area on the task page is a sheet of its own, between the edit form and the
  labels.** That is UX-S6's order. It is not a `dt` in the existing `dl`, so E5's
  `dt == ["Project"]` stays, and it uses no `table`, so E5's no-table check stays.
- **D-3 — The focus target is the moved task's status word element**, for a success, a refusal and a
  failure alike, on both pages. EX-4 asks for "the control that was used", but after a refusal or a
  move that control may no longer exist, because the offered buttons follow the saved status. The
  status element always exists, and CP-303 and CP-308 ask for "an element within that row" and "the
  task's status and moves".
- **D-4 — The line sits beside the moves**: in the moved row's moves cell, or in the status area.
  That keeps it in view with the row (EX-5) and adds no table row, which would change the row counts
  the page tests assert.
- **D-5 — The completion line takes the title from the state now and the status from the address.**
  This follows the existing precedent: "You saved changes to '…'" and the label lines read the title
  from the task as it stands, and a label line takes the label from the address. A reload after
  another tab renamed the task shows the new title. The status named stays the one the press moved
  to, which is CP-306's "same completion line".
- **D-6 — Two refusal codes, one per type** (`MoveNotAllowed`, `InvalidTaskStatus`). CP-309 asks
  that a non-status be "answered as CP-308 answers", meaning the same place, focus and reason shape.
  The words for each code are the content stage's, and may be the same.
- **D-7 — The move outcome takes precedence** over every other outcome an address can carry, on both
  pages. That keeps exactly one focus target. The task page already orders its outcomes this way:
  comment over label over the edit form.
- **D-8 — The place is a hidden form field from a closed vocabulary of two.** A missing or unknown
  value answers at the task's page, which exists for as long as the task does. This keeps one route
  (CP-314's "the move submission is one of the routes").
- **D-9 — The moves reach the pages through a query, `Tracker.allowed_moves`, not a new field on
  `TaskRow`.** `tests/integration/test_task_tracker.py:211`, `:212` and `:360` compare `TaskRow`
  values by equality. A moves field would make those comparisons false, and those tests are not
  released.
- **D-10 — `cancelled` is withheld in `web`'s page building, in one helper.** Which controls a
  page shows in a slice is page building (EX-12). The allowed set itself still comes only from
  `domain` (EX-7; the `web` row's "never works out which moves are allowed").
- **D-11 — `MoveNotAllowed` is defined in `domain/workflow.py`, beside its rule, and derives from
  `Refusal`.** The request names `workflow.py` as the home of "for any other move, a refusal", and
  `domain/refusals.py` stays untouched (R-3, R-4).
- **D-12 — The domain checks run in the order task found, target a status, move allowed.** This
  follows the existing "the task is found first" order.
- **D-13 — One end-to-end test is added** (`tests/e2e/test_moves.py`). The spec allows one. CP-300's
  "pressed with Enter or Space" and the 24×24 floor, and RT-9's `autofocus` on an element inside a
  table cell (SDD § 11 R-2), are each settled only by a real browser. The existing label and comment
  focus tests are the precedent.
- **D-14 — E4 is renamed** to say seven columns. A name that says six over an assertion of seven
  misleads the next reader. The spec names it by its old identifier.

### Noted for the later station `cancel-confirmation` (b)

**A hand-built `cancelled` submission is accepted.**

- *Why.* CP-309 ("If it names one of the four statuses, CP-293 or CP-294 decides") and the request's
  "the workflow rule itself keeps every move" mean a `same-origin` submission naming `cancelled` for
  a `todo` or `in-progress` task is saved with no confirmation.
- *Why it is carried here.* No tracker page builds that submission (CP-301), and the request check
  admits only `same-origin` submissions (SEC-2). So no path the tracker offers saves an unconfirmed
  `cancelled`, which keeps the request's "a move to `cancelled` must never save unconfirmed". A local
  program can send one, which NFDR § 3 already accepts as inside the boundary. Carried as written.
- *What it means for the later station.* Its confirmation must be enforced by the server, so that a
  move to `cancelled` without the confirming press is refused. Otherwise the confirmation will be a
  page-only guard over a route that already accepts the move. No test here asserts that a hand-built
  `cancelled` is accepted, so that station inherits no test to unpin.

### Reviews the records delegate to `development-design` (swept from `nfdr.md` and `adr/`)

| Obligation | Verdict |
|---|---|
| **QC-5** (by type; `application` defines no refusal) | Pass. One new refusal, `MoveNotAllowed`, is defined in `domain`. `application` re-exports it and `InvalidTaskStatus` and defines none. `web` maps each to its own code by `except` type (§ 3 C). No message is read. |
| **QC-8** (`web` keeps nothing between requests) | Pass. The outcome travels in the address only. No module-level value is added to `web`. |
| **QC-12** (no part no requirement pays for) | Pass. One module, one action, one query and one route, each paid for by FR-18, FR-19, EX-5 and EX-7. No new part or layer. |
| **QC-20** (`domain` holds no wording) | Pass. `MoveNotAllowed` carries no message, and the table holds enum members, not page text. |
| **QC-21** (`application` holds no rule) | Pass. `move_task` applies the rule and saves, and `allowed_moves` passes it through. Neither compares nor filters. |
| **QC-22, QC-25, QC-26** (`persistence`, format, saving contract) | Not touched. Nothing to review. |
| **QC-23** (`web` holds no rule) | Pass, with D-10 noted: withholding `cancelled` decides which controls a page shows, not which moves are allowed. The status value is not checked in `web` (QC-38). |
| **QC-24** (`main`) | Not touched. |
| **QC-27** (a change to `web` touches only `web` and `main`'s wiring) | Not a replacement of the interface. `application` and `domain` change for the rule, not for `web`. |
| **QC-36** (one escaping function) | Pass, as designed. The title in the accessible name and in the completion line goes through `_escape` (P5). No text field is added, so no new layer-5 escaping test is owed. |
| **QC-40** (pins and browser build against advisories, every review) | Pass. All 15 pins in `tests/requirements.txt` were queried against OSV (`api.osv.dev/v1/querybatch`, 2026-10-19), with 0 advisories each. The Chromium build `playwright==1.63.0` installs is inside the owner's dated exception, RN-33, to 2026-11-07, so it does not block this review. |
| **QC-41** (no secret) | Pass. None introduced. |
| **QC-46** (no saved field added) | Pass. Only the existing status value changes. |
| **QC-60** (Python 3.11) | Pass. The design names only 3.11-available features: `types.MappingProxyType`, `dataclasses.replace` and `str`-valued `Enum`. |

### Evidence note

**What the prototype measured.** The blast radius of § 5's existing tests (R-2, and the atomic-landing
edges in § 3) was measured, not inferred. The steps:

- A fresh clone of the instance at `c01872b`, in `mktemp -d`, with a venv from
  `tests/requirements.txt` (pytest 9.1.1).
- Baseline: `pytest products/tracker17/tests/ --ignore=products/tracker17/tests/e2e` gave 1091
  passed.
- A throwaway prototype of this design was then applied: the workflow module, the action, the route,
  the seventh column, and the status area. The run gave **8 failed, 1083 passed**:
  - `test_trace.py` ×2
  - `test_shapes.py::test_only_the_task_features_are_added_to_domain`
  - `test_routes.py::test_every_route_leaves_state_and_headers_as_the_rules_say`
  - `test_task_pages.py::test_project_list_shows_every_own_task_in_six_columns`
  - `test_task_pages.py::test_task_page_shows_the_four_fields_in_the_one_authorized_form`
  - `test_task_pages.py::test_task_page_opens_edit_form_from_saved_values`
  - `test_comment_pages.py::test_written_comments_offer_no_edit_delete_or_reply_control`
- The clone and the prototype were then removed.

**What the prototype did not measure.**

- **The browser tests.** `tests/e2e/` was not run, because Chromium is not installed here. By reading:
  the Tab sequences in `tests/e2e/test_labels.py` and `tests/e2e/test_comments.py` stay inside the
  label and comment areas, and `test_labels.py:168` reads cell 4. D-1 and D-2 leave both untouched.
- **The timed run.** The prototype did not touch the timed run. R-1 rests on reading
  `tests/integration/test_timed_run.py`.
