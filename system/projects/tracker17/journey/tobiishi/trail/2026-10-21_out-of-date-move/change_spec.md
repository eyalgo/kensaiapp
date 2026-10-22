# Change Spec — The move refusal for an overtaken press, and for one reached by an address

**Date:** 2026-10-21
**Category:** feature
**Behaviour:** changing
**Request:** Fix how the tracker refuses a move in two cases, both on the move refusal page. (1) When someone presses a move from a page whose task has since changed status, nothing is saved, and the page they land on says the status has changed, names the moves that page now shows (or none when the status is done or cancelled), and offers no reload; it is built after the refusal. (2) When the refusal is reached by an address with no press, it states the task's status as a fact about what that status allows, names the move the address asks for, and gives no action and no reload. Today's words, "the move you pressed" (`web/pages.py:760`), claim a press the tracker never saw, so they go, and the tests that quote them (`tests/integration/test_move_routes.py`, `tests/e2e/test_moves.py`) are changed to the new words rather than removed. The words come from CONTENT RN-26 and UX-I3/UX-F4. Saved data must be byte-identical before and after each refusal (AC-12), checked by a test that compares it. Both refusals are one capability: the same refusal page and the same words, so they are one merge. The workflow rule must stay written once in `domain/workflow.py`; the history mechanism and confirmation from the earlier units, `tests/timed_run.py`, the saved data format and every other refusal's words must not change, and no page script is added (ADR-0003). Done when `pytest products/tracker17/tests/integration/` and `pytest products/tracker17/tests/` both exit 0 from the repository root, and `grep -rn "the move you pressed" products/tracker17/web` prints nothing.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `core/doctrine/engineering/languages/python/README.md` opened and its concern files read for a line that fixes how a fact is rendered; no rule below renders a language-level fact

---

## Change Summary

A refused move stops saying "the move you pressed". A press that another tab overtook now says the task's status has changed and names the moves the page now offers, or that there are none. A refusal reached by opening an address, with no press, states the task's status and that it does not allow a move to `cancelled`. Neither offers a reload. Nothing else about either refusal changes: where it shows, what has focus, what is saved, and how the page is answered.

Paths below are relative to the product root, the directory `system/projects/tracker17/project.md` `Product path:` names. "The records" are that product's `docs/fdr.md`, `docs/SRS.md`, `docs/SDD.md`, `docs/nfdr.md`, `docs/UXD.md`, `docs/CONTENT.md` and `docs/adr/`.

---

## Rules

### Which refusal is which

- **CP-355:** The **overtaken press** is every move submission, for a task that exists, that names one of the four statuses and that the task's saved status does not allow when the submission is applied (fdr R-55, R-102). Its members are a press of any move button on a row or on the task's page, a first press of `cancelled`, and a press of the confirming control `Move to cancelled`. The tracker's own pages offer only the moves the saved status allowed when the page loaded, so on the interface every member comes from a page loaded before another tab changed the task's status (UXD UX-F4, failure and recovery, the first way).
- **CP-356:** The **address refusal** is the page a project's Tasks view or a task's page answers when its address asks to open the confirmation of a move to `cancelled`, or to back out of it, for a task on that page whose saved status is `done` or `cancelled` (UXD UX-F4, failure and recovery, the second way; SDD § 6 S-4 *Reached when*). For a task in `todo` or `in-progress` the same addresses show the confirmation, or the restored `cancelled` button, as they do today, with no refusal. An address naming a task that is not on that page, or that no task holds, answers as it does today.
- **CP-357:** A move submission that names anything other than one of the four statuses, or nothing, is refused, saves nothing, and is answered exactly as an overtaken press on the same task is, its words included (the allowed-moves change's CP-309, kept). See Locked Answers, Gap 1.

### The overtaken press

- **CP-358:** An overtaken press saves nothing: the saved data is byte-for-byte the same before and after (fdr R-100; SRS AC-12). It is answered with the page the button was on, built after the refusal from the saved data: the project's page at the task's row for a row, the task's page at its status for the task's page. That page shows the task's saved status and the moves it allows now. Keyboard focus is on the task's status in words, and the refusal's line is that element's accessible description and takes no focus. All of this is as today (SDD § 4 EX-4, EX-14; UXD UX-A3).
- **CP-359:** The overtaken press's line says the task's status has changed. For a saved status of `todo` or `in-progress`, it then names every move the landing page offers for that task, and no other, in the order the page shows them: `in-progress` and `cancelled` for `todo`; `done`, `cancelled` and `todo` for `in-progress`. For `done` or `cancelled`, it says the task can't be moved, so no move is left to name (UXD UX-I3, UX-F4; CONTENT.md § Message patterns, Error, *A refusal*). The task's title shows as saved and as typed (fdr R-112). The exact words are the content stage's, under CONTENT.md § Voice and *A refusal*. Today the line reads `The status of '<title>' is <status>, which doesn't allow the move you pressed.` and then a tail per status (`web/pages.py:740-763`).

### The address refusal

- **CP-360:** The address refusal saves nothing: the saved data is byte-for-byte the same before and after. No confirmation shows, and the task offers no move. Keyboard focus is on the task's status in words, beside which the refusal sits, and the line is that element's accessible description and takes no focus. All of this is as today (UXD UX-I3, UX-A3; SDD § 4 EX-4, EX-14).
- **CP-361:** The address refusal's line reads `The status of '<title>' is <status>, which doesn't allow a move to cancelled. A task in <status> can't be moved.`, where `<title>` is the task's title as saved and `<status>` is its saved status, `done` or `cancelled`. The same line serves both addresses, on the Tasks view and on the task's page (CONTENT.md § Message patterns, Error, *A refusal*, the rule for a refusal reached without a press and its seventh example; RN-26). A title holding `<`, `&` or `"` shows as typed (fdr R-112).

### What neither line says, and what stays

- **CP-362:** Neither line offers a reload: no sentence asks the reader to reload, and the line holds no link and no control (UXD UX-I3, RN-34). Neither line says "the move you pressed". After the change, `grep -rn "the move you pressed" products/tracker17/web`, run from the repository root, prints nothing. Today it prints `web/pages.py:760`.
- **CP-363:** Every other line the tracker shows keeps its words: every other refusal, the failed move's line, the completion line, and the confirmation's sentence and control labels.
- **CP-364:** The moves CP-359 names come from the one workflow rule. It stays written once, in `domain/workflow.py`, and no other module holds its own table of which moves a status allows (SDD § 3, `web` row, "it never works out which moves are allowed"). The workflow rule does not change.
- **CP-365:** How a move's pages are answered stays as it is. A page showing either refusal is answered 200 with `Cache-Control: no-store`, and a pending confirmation 202 (NFDR QC-63; ADR-0010). The four layer-3 tests and the two layer-5 tests QC-63 names pass. No page runs a script (ADR-0003; NFDR QC-34). The saved data format and `tests/timed_run.py` do not change.

### Checks the records above this change require

- **CP-366:** Tests at NFDR layer 3, through the tracker's request path, cover each refusal and assert, in each case, that the saved data is byte-for-byte the same before and after, and that the page shows that refusal's line as the focused status element's accessible description (SRS AC-12, "one per refusal", with NFR-3's refusal "tested … for a task that has changed"; NFDR QC-5, QC-38). Between them they cover:
  - the overtaken press landing on each of the four saved statuses, on a row and on the task's page, each asserting the moves the line names (CP-358, CP-359);
  - an overtaken first press of `cancelled`, and an overtaken press of `Move to cancelled`, for a task now `done` (CP-355);
  - the address refusal for `done` and for `cancelled`, through the confirmation's address and the back-out address, on the Tasks view and on the task's page (CP-360, CP-361);
  - a submission naming no status, answered as CP-357 says;
  - a title holding `<`, `&` and `"`, shown as typed in each line (CP-359, CP-361).
- **CP-367:** development-design reviews, for this change to `web`'s handling of a refusal and to page building: that `web` tells the two refusals apart by type or by the request, never by reading a message (NFDR QC-5, the by-type half); that the change adds no part no requirement pays for (QC-12); and that the title reaches each line through the one function that escapes values (QC-36, the one-function half).
- **CP-368:** Every test module this change adds names the requirements or acceptance criteria it checks, and the opening docstring of `domain/workflow.py` names it among the modules that check the Status workflow feature. `tests/architecture/test_trace.py` passes (NFDR QC-11). `web` imports only `application` and `errors` (QC-16). A route this change adds, if any, is one that `tests/integration/test_routes.py::test_every_route_leaves_state_and_headers_as_the_rules_say` sends (QC-7, QC-8). These three commands, run from the product root, each exit 0: `ruff format --check .`, `ruff check .`, and `mypy main.py errors.py domain application persistence web` (QC-62).
- **CP-369:** `pytest products/tracker17/tests/integration/` and `pytest products/tracker17/tests/` each exit 0 from the repository root (the request; `project.md` `Test command:`). `pytest products/tracker17/tests/e2e/` exits 0 on a machine where layer 5 runs (SDD § 6 S-4 *Command*, "Both suites pass"; NFDR QC-63's layer-5 tests; NFDR § 9). `pytest products/tracker17/tests/` does not collect `tests/e2e/` (`tests/conftest.py:7-9`), so the request's two commands alone do not run it.
- **CP-370:** Every existing test passes unchanged, except the ones below. Each pins today's line, and each is changed to the new words, not removed, and keeps every other assertion it makes (see Locked Answers, Gap 7):
  - `tests/integration/test_move_routes.py`: the `REFUSAL_FOR` words, and `test_a_stale_press_is_refused_against_the_saved_status_and_saves_nothing`, `test_a_stale_todo_press_after_done_is_refused_and_the_task_stays_done`, `test_a_non_status_or_missing_status_is_refused_and_answered_like_a_stale_press`, `test_a_press_on_a_cancelled_task_is_refused_with_the_cancelled_reason`, `test_confirmation_and_back_out_reads_never_save`, `test_stale_opening_and_confirmation_use_the_saved_workflow_answer`;
  - `tests/integration/test_move_pages.py`: `test_a_landing_page_has_exactly_one_autofocus_on_a_non_control_status_element_that_names_the_line`, `test_back_out_restores_only_the_selected_trigger`;
  - `tests/e2e/test_moves.py`: the `DONE_REASON` and `CANCELLED_REASON` words, and `test_stale_first_press_refuses_at_the_visible_current_status`, `test_real_history_traversal_revalidates_the_confirmation`, `test_history_matrix_revalidates_current_saved_status`.

---

## Examples

| Scenario | Expected behavior |
|---|---|
| Tab 1 shows `Set up CI` in `todo`. Tab 2 moves it to `in-progress`. Tab 1 presses `in-progress` on its row | Nothing is saved, and the saved data is byte-for-byte unchanged. The project's page opens at the row, which shows `in-progress` with `done`, `cancelled`, `todo`. Focus is on the status word. Its description says the status has changed and names `done`, `cancelled` and `todo`, in that order. No reload is offered. (CP-355, CP-358, CP-359, CP-362) |
| Tab 1 shows `Set up CI` in `in-progress`. Tab 2 moves it to `todo`. Tab 1 presses `done` on the task's page | Nothing is saved. The task's page opens at its status, `todo`, with `in-progress`, `cancelled`. The line says the status has changed and names `in-progress` and `cancelled`. (CP-358, CP-359) |
| Tab 1 shows `Set up CI` in `in-progress`. Tab 2 moves it to `done`. Tab 1 presses `todo` | Nothing is saved. The landing shows `done` and no move button. The line says the status has changed and that the task can't be moved. (CP-359) |
| Tab 1 shows `Set up CI` in `todo`. Tab 2 cancels it. Tab 1 presses `in-progress` | As above, for `cancelled`. (CP-359) |
| Tab 1 shows `Set up CI` in `todo`. Tab 2 moves it to `in-progress`, then `done`. Tab 1 presses `cancelled`, or presses `Move to cancelled` on a confirmation it opened earlier | No confirmation shows and nothing is saved. The line is the overtaken press's, for `done`. (CP-355, CP-359) |
| `Set up CI` is `done`. The operator opens `/projects/1?move_task=1&move_confirm=cancelled` from a bookmark | No confirmation shows and nothing is saved. Focus is on the status word `done`, described by "The status of 'Set up CI' is done, which doesn't allow a move to cancelled. A task in done can't be moved." The page is answered 200 with `Cache-Control: no-store`. (CP-356, CP-360, CP-361, CP-365) |
| The operator confirms `Set up CI` to `cancelled` on its task's page, then presses Back to the confirmation's address | Nothing is saved. The line reads "The status of 'Set up CI' is cancelled, which doesn't allow a move to cancelled. A task in cancelled can't be moved." (CP-356, CP-361) |
| The back-out address for a task in `done`, on the Tasks view | The same line as the confirmation's address gives, for `done`. (CP-356, CP-361) |
| The confirmation's address for a task in `todo` | The confirmation opens, as today. No refusal. (CP-356) |
| A same-origin move submission naming `finished` for a task in `todo` | Refused, nothing saved, answered as an overtaken press on a `todo` task: the line names `in-progress` and `cancelled`. (CP-357) |
| A task titled `a < b & "c"`, overtaken press and address refusal | Each line shows the title exactly as typed, once. (CP-359, CP-361) |
| `grep -rn "the move you pressed" products/tracker17/web` after the change | Prints nothing. (CP-362) |
| A label refusal, a failed move, a completed move, the confirmation | Each shows the same words it shows today. (CP-363) |
| The modules outside `domain/workflow.py` after the change | None holds a table of which moves a status allows. The landing's named moves and its buttons agree for every status. (CP-364) |
| The layer-3 tests for the two refusals | Cover CP-366's cases, each comparing the saved bytes before and after. (CP-366) |
| design review of the change | Records the QC-5, QC-12 and QC-36 reviews. (CP-367) |
| `tests/architecture/test_trace.py`, `ruff` and `mypy` | Pass. (CP-368) |
| `pytest products/tracker17/tests/integration/`, `pytest products/tracker17/tests/`, and `pytest products/tracker17/tests/e2e/` on a machine where layer 5 runs | Each exits 0. (CP-369) |
| The suite after the change | Every existing test passes, except the ones CP-370 names, each changed to the new words and keeping its other assertions. (CP-370) |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| The project's highest rule number in use is CP-354 | `grep -rhoE "CP-[0-9]+"` over `products/tracker17` and `system/projects/tracker17`, sorted numerically | `CP-354`. This spec starts at CP-355 |
| Today `grep -rn "the move you pressed" products/tracker17/web` prints one line (CP-362) | Ran it from the change worktree's root at `06d6aea1a` | `products/tracker17/web/pages.py:760` |
| Today the overtaken press, the address refusal and a submission naming no status show one and the same line (CP-355 to CP-357, CP-359) | Read `web/pages.py:740-763` (`_REFUSAL_TAILS` and `_move_line`, which give one line for any refusal code), `web/routes.py:365` (the address answers `NOT_ALLOWED`), `:741` and `:748-751` (a refused press is sent on with `not-allowed`), `:752-755` (no status, `not-a-status`); and `tests/integration/test_move_routes.py::test_stale_opening_and_confirmation_use_the_saved_workflow_answer`, which asserts one reason for the press, the confirming press and the back-out address | As stated |
| The address refusal arises only for `done` and `cancelled` (CP-356) | Read `web/routes.py:364-365` (it answers the refusal only where the saved status does not allow `cancelled`) and `domain/workflow.py:47-54` (only `todo` and `in-progress` allow it) | As stated |
| `pytest products/tracker17/tests/` does not collect `tests/e2e/` (CP-369) | Read `tests/conftest.py:7-9`; ran the suite with and without `--ignore=products/tracker17/tests/e2e` | Both runs collect 1250 tests |
| The tree passes today (CP-368, CP-369) | In a fresh clone of the instance at `06d6aea1a`, macOS, with a venv from `tests/requirements.txt` (pytest 9.1.1, playwright 1.63.0, the pinned Chromium build): `pytest -q products/tracker17/tests/` from the repository root; `pytest -q products/tracker17/tests/e2e/test_moves.py`, which starts the tracker through `main`; then `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web` from the product root | `1250 passed`; `34 passed`; "207 files already formatted", "All checks passed!", "Success: no issues found in 24 source files" |
| Exactly the tests CP-370 names pin today's line (CP-370, Gap 7) | In the same clone, a prototype that gave the address refusal its own code, chosen at `web/routes.py:365`, and gave the overtaken press, the address refusal and a submission naming no status the new kinds of line. Then `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/`, both from the repository root | `17 failed, 1233 passed`: the eight integration functions CP-370 names, and nothing else. `13 failed, 54 passed`: the three `test_moves.py` functions CP-370 names, and nothing else. Each failure is on the line's words. `test_confirmation_address_at_a_final_status_shows_the_saved_status` passed, because it checks only `is <status>,`, which CP-361's line holds. The prototype was thrown away |
| No rule pins output that renders a language-level fact (Step 6, *Language rendering*) | Walked CP-355 to CP-370. The status words, the move names and the lines are the product's own (CONTENT.md) | No rendering rows |

---

## Out of Scope

- **The overtaken press's landing address, opened again without a press.** Reloading the page a refused press landed on, or reaching it by Back or a bookmark, shows the overtaken press's line again, as it shows today's (`web/routes.py:378-391` reads the outcome from the address; fdr R-106, PD-11). CONTENT.md RN-26 says such a refusal "has the same property" as the address refusal and "waits until one occurs". No rule here changes it. Handed on as a record gap in `deferred_decisions.md`.
- **The timed run.** `tests/timed_run.py` does not change. This change adds no action SRS NFR-1 lists (NFDR QC-48). The timed move is the `move-timed-run` station's.
- **The workflow rule, the saved data format, the confirmation and the history mechanism.** None changes (CP-363 to CP-365).
- **A script in any page** (ADR-0003; CP-365).
- **CONTENT.md's own example of an out-of-date refusal.** § Message patterns, Error, *A refusal*, the fifth example, still reads "Reload the page to see it." See Locked Answers, Gap 4. Editing a record is not this change's.

---

## Locked Answers (the divergence record — self-review 2026-10-21)

- **Gap 1 — a submission naming no status keeps the overtaken press's answer (b):** CP-357 keeps the allowed-moves change's CP-309, which answers it "as CP-308 answers", the overtaken press. *Because* the request names two refusals and says every other refusal's words stay. This one shares today's line, so the grep forces its words to change, and keeping its tie to the press is the smallest change that does that. The tracker's own pages never send such a submission, so the line's "has changed" can read wrongly only for a request built by hand. A hand-built submission naming a refused status reads the same way, and the tracker cannot tell either from an overtaken press. Reversible: a later change can give it its own line.
- **Gap 2 — the address refusal's words are pinned (b):** CP-361 states the line. *Because* CONTENT.md gives it, for exactly this refusal, as the seventh example of *A refusal*, and says "The same formula serves a task in `done` and a task in `cancelled`." A spec that left it open would hand design a choice the record has already made. The content stage still writes it in its text record.
- **Gap 3 — the overtaken press names every move the page offers, in the page's order (b):** CP-359. *Because* UX-F4 says it "names the moves the page now shows", and naming them in the order of the buttons beside the line lets a test check the line against the page. The words around the names are left to the content stage. CONTENT.md has no example for this case that UXD version 8 still allows (Gap 4).
- **Gap 4 — no reload, against CONTENT.md's fifth example (b):** CP-362 has no line offer a reload. *Because* UXD UX-I3 and UX-F4 (version 8, RN-34) and SDD § 6 S-4 *Reached when* say the overtaken press "offers no reload", and the request says the same. Whether a refusal offers a reload is the UXD's to state. CONTENT.md says its examples illustrate a rule "and specify no screen", and its fifth example ("Reload the page to see it") predates UXD version 8. The disagreement is for the Content Manager's seat.
- **Gap 5 — the browser suite runs (e):** CP-369 requires `pytest products/tracker17/tests/e2e/` to exit 0 where layer 5 runs. The request's done-when names two commands, and neither collects `tests/e2e/`. *Because* SDD § 6 S-4 *Command* says "Both suites pass", and NFDR QC-63 is verified by two layer-5 tests in `tests/e2e/test_moves.py` that pin today's line. The request already asks for that file's quoting tests to be changed, and only running it shows the change worked.
- **Gap 6 — the structural checks and reviews (e):** CP-366's per-refusal cases, and CP-367 and CP-368, state checks the request does not name: SRS AC-12; NFDR QC-5, QC-7, QC-8, QC-11, QC-12, QC-16, QC-36, QC-38 and QC-62. *Because* each binds a change to a refusal's handling or to page building, and the suite and the gates run over this change whether or not the spec names them. The overtaken press is tested at all four landing statuses rather than one final and one other, because its line differs by status.
- **Gap 7 — the tests that change (f):** CP-370 names them. The request names `tests/integration/test_move_routes.py` and `tests/e2e/test_moves.py`. `tests/integration/test_move_pages.py` imports `REFUSAL_FOR` from the first and pins it in two tests, so it changes too. *Because* CP-359 and CP-361 change the words, which the request asks for, none of them can pass unchanged (Verified Claims, the prototype row). Each keeps every other assertion:
  - the `test_move_routes.py` six keep their unchanged saved bytes and save counts, their landing addresses, their single focus on the status word, the buttons each landing shows, and their absence of a confirmation strip. `test_stale_opening_and_confirmation_use_the_saved_workflow_answer` no longer asserts one reason for the presses and the back-out address. It asserts the overtaken press's line for the two presses and the address refusal's line for the back-out;
  - the `test_move_pages.py` two keep their one autofocus on a non-control status element, where the line sits, and the restored trigger and its accessible name;
  - the `test_moves.py` three keep their focus, view, history, fresh-load and saved-bytes assertions. `test_stale_first_press_refuses_at_the_visible_current_status` takes the overtaken press's line for `done`. The two history tests take the address refusal's line.

  Design names the final set, measured against its own design.
