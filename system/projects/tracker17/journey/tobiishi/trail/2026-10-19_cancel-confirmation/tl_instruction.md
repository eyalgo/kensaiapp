# Tech Lead instruction — cancel-confirmation: confirm the cancelled move in place

**Date:** 2026-10-20
**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — source and test paths below are relative to it; commands explicitly marked worktree-root use repository-relative paths.
**Scope:** Build the cancelled move's opening, confirmation, back-out and current-state outcomes on task rows and task pages, with browser proof of focus, geometry and history.

This instruction owns the task cut and verification scaffold for `tracker17 · tobiishi · 2026-10-19_cancel-confirmation`.
Read that change's `change_spec.md` CP-319–CP-342 and `change_design.md` §§ 2–5 for the binding contracts.
The artifact's home is the change arc, per `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2, `journey/tobiishi/<key>/`.

---

## Project layout

```text
products/tracker17/
  web/
    pages.py                              ← modified: interaction value, strip and one focus owner
    routes.py                             ← modified: opening/confirming intents, addresses and headers
    style.css                             ← modified: strip, trigger slot and focus treatment
  domain/
    workflow.py                           ← modified: opening feature trace only
  tests/
    integration/
      test_move_pages.py                    ← modified: rendered interaction and continuity
      test_move_routes.py                   ← modified: request/save/refusal/failure paths
      test_routes.py                        ← modified: route enumeration, policy and cache headers
      test_task_pages.py                    ← modified: the three CP-342 expectation updates
      test_comment_pages.py                 ← modified: the one CP-342 form-inventory update
    e2e/
      conftest.py                           ← modified only as needed for history-cache-enabled launch
      test_moves.py                         ← modified: existing three tests plus confirmation cases
    architecture/
      test_trace.py                         ← modified: complete workflow participation pointers
```

Create no directory, package or `__init__.py`. Keep public exports unchanged.
The full module set is `domain`, `application`, `persistence`, `web`, `main.py` and `errors.py` (`docs/nfdr.md` § 1.2, QC-13–QC-18).
All added runtime logic belongs to `web`; only the workflow entry docstring changes in `domain` (`docs/SDD.md:199–215`, § 3, “The parts”; `change_design.md:38–50`, § 2).
Use the graph in `docs/nfdr.md:127–164`, § 1.2: `web` may import `application` and `errors`, never `domain`, `persistence`, `main`, tests or third-party code; `domain` may import `errors` and the standard library, never another part.
Leave `application/`, `persistence/`, `main.py` and `errors.py` untouched (`change_design.md:42–45`, § 2).

Run gates in the product's locked test environment from `tests/requirements.txt`; do not move any pin.
The card's command is `pytest products/tracker17/tests/`, run at the change worktree root (`system/projects/tracker17/project.md:8–12`, “Test command”).
Run the whole browser folder separately, as `docs/nfdr.md` § 9, “Layer 5 runs on fewer systems”, and § 10 require.
Permit temporary loopback listeners and normal process interrupts in the gate environment.

## TL Review Notes

Decisions below are the Tech Lead's, 2026-10-20.

- **Task cut:** Keep sub-job A in Task 1 because the page contract, first-press adapter and thirteen continuity changes form one capability; extracting the button alone would expose the immediate-save route that `change_spec.md` CP-330 forbids (`change_design.md:58–76`, § 3 A; `web/routes.py:631–675`, `Site._move_task`). Task 2 is independently testable trace work, as the design's B declares (`change_design.md:154–170`, § 3 B). Neither task consumes the other's output, so both say `Dependencies: None`.
- **History harness specificity:** Add `tests/e2e/conftest.py` to Task 1's test-support scope so the history case can satisfy the design's requirement that browser history caching remain available (`change_design.md:143–150`, § 3 A.3, and § 5 T14). The fixture delegates its launch arguments to Playwright (`tests/e2e/conftest.py:132–136`, `browser`), whose vendor source lists a default `--disable-back-forward-cache` ([Playwright Chromium switches](https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/server/chromium/chromiumSwitches.ts)). Inspect the installed pinned driver's actual arguments and exclude only cache-disabling defaults that apply to the history proof, using the vendor's argument-filter seam ([BrowserType.launch, ignore_default_args](https://playwright.dev/python/docs/api/class-browsertype#browser-type-launch-option-ignore-default-args)). Preserve the existing browser, tracker factory, origin and dependency pins; this is test scaffolding for T14, not a new product mechanism.
- **Review-only checks:** Put the source-symbol check from design T1, no-deletion diff from T11, unchanged-file fence and existing-assertion continuity from CP-342 in Task 3's review lane. They check this change's construction and diff, not an enduring behavior; a test tied to this branch's base would burden later work (`<CORE>/../skills/tech-lead/.claude/skills/development-plan/SKILL.md`, Step 3, “A check that holds only for this change”). Task 1 still tests exact workflow-derived offered moves.
- **Edge coverage:** Add same-origin direct confirmation without prior opening, repeated confirming POST after cancellation, repeated/unknown interaction query values, no cache eviction after a refused/failed save, and a long markup-bearing title in browser geometry checks. The first two follow the stateless distinct-intent contract (`change_design.md:71–86`, § 3 A.1); the query cases sharpen its one-interaction rule (`:115–120`, A.2); the header cases bound “successful” (`:136–141`, A.3); the title case combines CP-322's typed-text contract with CP-325's full trigger-rectangle condition.
- **Red remains test-first:** Task 1 changes the offered moves and ordinary cancelled POST; those subjects do not already satisfy the new contract (`web/pages.py:603–620`, `_move_forms`; `web/routes.py:631–675`, `Site._move_task`). Task 2 adds a real completeness assertion for pointers missing from the workflow entry (`domain/workflow.py:8–18`, “Taking part” / “Checked by”). Do not manufacture a red phase for Task 3's review deliverables.
- **Gate environment:** At `18f46c5d9ce778155129abbb54afb7ddb66c69a0`, the planning run of `pytest products/tracker17/tests/` returned `1170 passed in 91.87s` with approved local sockets and a terminal. The restricted, nonterminal run returned `20 failed, 1120 passed, 30 errors`; the isolated listener reproduction ended at `socket.bind` with `PermissionError: [Errno 1] Operation not permitted`. The nonterminal command `python3 -c 'import signal; print("SIGINT disposition:", signal.getsignal(signal.SIGINT))'` returned `SIGINT disposition: 1`, whereas the terminal probe returned `SIGINT disposition: <built-in function default_int_handler>`. Preserve both environment preconditions: `_run_real_start` sends SIGINT and waits for exit (`tests/integration/test_start.py:515–537`). These failures do not establish deferred product reds. The passing run reported pytest 9.0.3; `tests/requirements.txt:14` pins 9.1.1, so the planning measurement is not a locked-environment acceptance verdict. Keep the card's command and require the locked environment for delivery gates.

## Corrections owed while there

- Owed outside this change's reach: `docs/DESIGN.md` § Components, `{components.confirm-strip}` (`:456–464`) — its location shorthand assigns `{spacing.control}` everywhere except a task row, while the task-page move trigger uses row-control height (`web/style.css`, `button.move-button`; `web/pages.py`, `_status_section`) → state that the sentence and confirming button follow the actual trigger height, with row and task-page move examples. Preserve CP-323's height continuity. This carries `change_design.md` § Records this change makes false; this change does not edit the record.

### Task 1: The cancelled confirmation capability (`web/pages.py`, `web/routes.py`, `web/style.css`, `tests/integration/test_move_pages.py`, `tests/integration/test_move_routes.py`, `tests/integration/test_routes.py`, `tests/integration/test_task_pages.py`, `tests/integration/test_comment_pages.py`, `tests/e2e/test_moves.py`, `tests/e2e/conftest.py`)

**Dependencies:** None

**What to build:** The complete web-owned capability in design § 3 A, including the existing-test expectation changes in design § 5, “Existing assertions retired and re-proved”.

- In `pages.py`, add immutable `MoveInteraction(task_id, mode)` and the closed `MoveInteractionMode` enum with `CONFIRM` and `BACK_OUT`. Add the optional `move_interaction=None` page keyword without removing an existing signature or export. Keep `MoveOutcome`'s meaning distinct. Build one reusable strip from plain wording, destinations, fields, sentence identity, trigger-size context and focus ownership. The strip owns no task type, workflow lookup or action. Replace only the selected cancelled button, preserving the workflow tuple's explicit order (`change_design.md` § 3 A.2).
- In `routes.py`, make ordinary `POST /tasks/<id>/move` with `status=cancelled` read-only opening. Add fixed-target `POST /tasks/<id>/move/confirm`. Retain all other move behavior. Resolve tasks, membership and allowed moves afresh inside the existing request lock; consume `Tracker.allowed_moves` rather than copying its table. Use `_address` for newly built query-bearing destinations. Keep `place=list` and task-page fallback, derive a list's project from the saved task, and route typed refusals and unexpected failures through the existing boundaries (`change_design.md` § 3 A.1).
- Preserve the address contract `move_task=<id>&move_confirm=cancelled` for opening and `move_task=<id>&move_back=cancelled` for the native GET back-out form. Normalize recognized move states in refusal, failure, completion, confirmation, back-out order; ignore unknown codes and a different task on a task page. Show at most one strip and one autofocus, ahead of unrelated outcomes. A now-disallowed back-out lands on the current status/reason instead of inventing a button (`change_design.md` § 3 A.1–A.2).
- In `style.css`, realize `confirm-strip`, `button-confirm` and `button-secondary` from `docs/DESIGN.md` § Components. Keep the whole old trigger rectangle occupied by the sentence, with controls below it, and retain trigger-height continuity on both pages. Give the focused sentence the control focus ring. Do not use product script (`change_design.md` § 3 A.2; `change_spec.md` CP-323–CP-325, CP-338).
- Add `Cache-Control: no-store` on move-interaction/outcome pages and `Clear-Site-Data: "cache"` on successful move responses, ordinary moves included. Clear neither cookies, storage nor execution contexts. Keep the history proof's launch free of cache-disabling arguments, with any fixture adjustment confined to that requirement (`change_design.md` § 3 A.3).
- Place published wording verbatim from this change's `change_text.md`, including accessible names and console failure text. Do not invent fallback copy; CP-322 and CP-327 remain the text acceptance criteria (`change_spec.md` CP-322, CP-327; `<CORE>/roles/CROSS_ROLE.md` § 2).

#### Behaviours to verify

Use the real Site, Tracker and SavedData with handed-in clock/saver for layers 3 and 4; use the main-started Chromium harness for layer 5 (`docs/nfdr.md` § 9). Add the following tests to the named files; parameterize both originating places and each allowed source state where stated. Add no dependency or second workflow table. Every checking module names the SRS requirement or acceptance criterion it checks (CP-340).

In `tests/integration/test_move_pages.py`:

- `test_each_saved_status_offers_the_workflow_moves_in_order` — every status on rows and task pages offers exactly `Tracker.allowed_moves(saved_status)` in returned order, with one native button per move and no initial strip; cancelled has the saved-title accessible name and visible label CP-319 requires. Retain the existing status words, Status heading and ordinary-form assertions (T1/T3; CP-319–CP-320).
- `test_opening_replaces_only_the_selected_cancelled_button` — both places and eligible source states retain all other moves, rows and forms; sentence, confirming POST form and back-out GET form appear in that order, with the prescribed text and no completion (T2; CP-321–CP-322).
- `test_confirmation_titles_are_shown_as_text_once` — `<`, `&`, double quotes and apostrophes survive as typed in the sentence and accessible names, without injected markup or double escaping (T2; CP-322).
- `test_confirmation_sentence_alone_owns_focus_and_is_not_a_tab_stop` — sentence outside either submitting form, `tabindex=-1`, sole autofocus; following controls are native, enabled and lack positive tabindex or shortcuts. Check the strip and size-context classes; actual dimensions and key behavior belong to the browser cases below (T3; CP-320, CP-323–CP-324).
- `test_move_query_collisions_select_one_interaction_and_focus_owner` — recognized refusal > failure > completion > confirm > back-out, no unrelated completion/focus, one strip at most; unknown codes, invalid task values and another task on a task page have no interaction effect. Include repeated query keys without multiplying strips or focus targets (T3; CP-324, CP-326; TL edge addition).
- `test_back_out_restores_only_the_selected_trigger` — no strip/completion, one restored cancelled button with sole autofocus, other forms retained; a now-disallowed move uses current-status refusal instead (T6; CP-329, CP-331).
- `test_plain_confirmation_strip_is_reusable_without_a_move_subject` — plain fixture text/destinations/hidden fields and the cancellation caller share the same sentence/forms/order/focus contract; no task, workflow or tracker collaborator is needed to render the plain strip (T11; CP-335).

In `tests/integration/test_move_routes.py`:

- `test_first_press_opens_confirmation_without_a_save` — both places and eligible source states return 303 to their own page's confirmation address; disk bytes, in-memory state and save count remain identical, no completion. Preserve list/task fallback and saved-task-derived project landing (T2/T4; CP-321).
- `test_confirmation_and_back_out_reads_never_save` — direct GET, reload, repeated reads and history-address reads retain bytes/state/save count; an eligible confirmation refocuses its sentence, a back-out restores its trigger without a line, and a revisited confirmation after cancellation shows the current refusal (T4/T6; CP-326, CP-329).
- `test_confirming_saves_once_and_only_the_status_changes` — both places from each eligible source state change only the task's serialized status value, preserve every other serialized field, and land on cancelled with no moves/strip, one focused non-Tab-stop status and one accessible-description completion. Completion reload saves nothing (T4; CP-327).
- `test_confirming_an_overdue_task_clears_the_row_marker` — injected local date makes the due date overdue before confirmation and unmarked after, with no patched product name (T5; CP-328).
- `test_ordinary_cancelled_submission_cannot_claim_confirmation` — ordinary endpoint with cancelled, including forged confirmation/shown-status fields, opens or refuses without saving. The confirming endpoint fixes its target to cancelled despite submitted fields selecting another status (T7; CP-330).
- `test_confirming_intent_needs_no_remembered_pending_state` — a same-origin confirming POST can apply a currently allowed cancelled move without a prior opening request; a second confirming POST after cancellation refuses without saving (TL edge addition; design § 3 A.1).
- `test_other_moves_keep_their_first_press_outcomes` — retain ordinary successful moves, invalid/missing targets, task-not-found behavior and place fallback; no confirmation for another target (T7; CP-330).
- `test_stale_opening_and_confirmation_use_the_saved_workflow_answer` — both places: after todo becomes in-progress, opening remains allowed and confirming saves; after done or cancelled, both intents refuse with no strip and unchanged bytes/state/save count. One focused current-status element has its saved-status reason as accessible description. Back-out after a disallowing concurrent move has the same landing (T6/T8; CP-331–CP-332).
- `test_missing_confirmation_targets_answer_not_found_without_saving` — unknown and unreadable identities on opening, confirming and confirmation-address reads; no other project's task can be rendered through a list's interaction query (T9; CP-333).
- `test_failed_confirming_save_preserves_data_and_reports_the_action` — handed-in failing saver leaves disk and memory unchanged; console names action/error, browser gives the failure beside the sole focused status without Python exception text or success completion (T10; CP-334).

In `tests/integration/test_routes.py`:

- Extend `test_every_route_leaves_state_and_headers_as_the_rules_say` with the new confirming POST's enumerated pattern, sample destination and accepted body. Keep every existing route assertion. GET to the action address is nonmutating 404; accepted same-origin confirmation redirects. All responses retain CSP and no cookie (T15; CP-339).
- `test_confirming_route_checks_origin_before_applying_the_move` — wrong Host and cross-site, same-site, none and absent submission marks refuse with identical saved data/state/save count; same-origin is accepted; no script or meta policy is introduced (T15; CP-339).
- `test_move_interaction_and_outcome_pages_are_not_stored` — opening, back-out and move outcome pages carry no-store while preserving policy/no-cookie headers (T15; design § 3 A.3).
- `test_only_successful_moves_evict_cached_confirmations` — successful ordinary and confirming POSTs carry exactly the cache eviction directive; opening, refusal and failing save do not claim a successful-move eviction and do not clear cookies/storage/execution contexts (T15; TL edge addition).

In `tests/e2e/test_moves.py`:

- Retain and update all three CP-342-named existing tests: row Space and task-page Enter still land on a focused, visible, non-Tab-stop status with its accessible description; target tests compare offered buttons with the workflow answer, including cancelled, without fixed counts or a copied table (T17; CP-342).
- `test_keyboard_opening_focuses_the_visible_sentence` — row and task page, Enter and Space after Tab navigation; sentence alone focused/in view with visible ring, not in Tab order; repeated Enter and Space leave the strip and disk unchanged; next two Tabs reach confirm then back-out. Include the far-down scrolled row (T12; CP-320, CP-324, CP-337).
- `test_keyboard_confirming_and_back_out_use_their_own_intents` — confirm by Enter and Space saves and focuses visible cancelled status described by one line; back-out by either key saves nothing, restores the trigger with visible focus, no completion/strip, and subsequent traversal has no sentence stop (T12; CP-327, CP-329, CP-337).
- `test_confirmation_preserves_trigger_geometry_and_target_sizes` — measure original trigger before opening; sentence covers its whole rectangle and is at least as tall, confirming control retains trigger height, and all three buttons meet 24 by 24 CSS pixels on both places. Include a long markup-bearing title shown as typed (T12; CP-320, CP-322–CP-323; TL edge addition).
- `test_double_click_never_confirms_at_the_original_trigger_coordinates` — short list row, task page and row 40 of 60 at a nonzero partial scroll; drive a real double click at interior and far-edge points. Also deliver a second click at the original coordinate after the new document arrives, proving the coordinate hits the sentence instead of merely losing the second event to navigation. Strip stays and saved status/data do not change (T13; CP-325, CP-337).
- `test_stale_first_press_refuses_at_the_visible_current_status` — two tabs: eligible button becomes stale after the other tab reaches a final status; first press saves nothing and shows no strip, with focused/in-view current status described by the reason (T14; CP-331, CP-337).
- `test_real_history_traversal_revalidates_the_confirmation` — reload/back/forward before confirmation never save; after confirming, back to the old confirmation renders the saved-status refusal, no strip/save. Include successful ordinary move in a second tab invalidating the old confirmation. Run with history caching available and no test interception or launch option disabling it; address reads alone do not prove this case (T14; CP-326).

#### Held by review

- The reusable builder owns no task/workflow policy, runtime rule remains stated only in `domain/workflow.py`, new dynamic text passes the existing `_escape` boundary once, and failures remain mapped by type at the existing catch site — fixture tests cover examples but cannot prove these ownership and single-site properties. Read the production diff against `docs/SDD.md` § 3 and `docs/nfdr.md` QC-5, QC-8, QC-23, QC-36, QC-56.
- The browser history case has caching available on the actual pinned driver, with no cache-disabling default left active. Inspect its launch arguments; an ordinary navigation pass alone is insufficient (`change_design.md` § 3 A.3, § 5 T14).

#### Implement

Infer from failing tests.

# Hint:
Keep opening/back-out as address-only reads and saving behind the distinct POST intent. Reuse `Site.handle`'s lock and `Site._guarded`; never perform a trial mutation to validate opening. Use one plain strip builder and a stable trigger slot, with the focused sentence outside either button's form. Pair no-store on interaction/outcome pages with cache eviction after successful moves for history revalidation. Browser tests decide focus and old-click-coordinate behavior.

#### Verification gate

From the change worktree root, in the locked test environment with temporary local sockets and normal SIGINT handling:

```sh
pytest products/tracker17/tests/integration/test_move_pages.py products/tracker17/tests/integration/test_move_routes.py products/tracker17/tests/integration/test_routes.py products/tracker17/tests/integration/test_task_pages.py products/tracker17/tests/integration/test_comment_pages.py
pytest products/tracker17/tests/e2e/
pytest products/tracker17/tests/
```

From the product root, in the same environment:

```sh
python3 -m compileall -q main.py errors.py domain application persistence web tests
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: every command exits 0, both suites collect and run their intended tests, all Task 1 behaviors pass, the three original browser move tests remain covered and there are no unrelated regressions. Missing browser/system libraries or dependencies are prerequisites, not a passing browser verdict; a failing focus/geometry/history experience condition is reported without weakening tests, adding script or reversing ADR-0003 (CP-338, CP-341–CP-342).

### Task 2: Complete the workflow feature trace (`domain/workflow.py`, `tests/architecture/test_trace.py`)

**Dependencies:** None

**What to build:** Complete only the workflow entry's opening docstring and add its specific completeness assertion, retaining workflow implementation and public API unchanged (`change_design.md` § 3 B, § 5 T16; CP-340).

#### Behaviours to verify

In `tests/architecture/test_trace.py`:

- `test_workflow_entry_names_every_participating_module_and_check` — the workflow entry names FR-18 and FR-19, `application/tracker.py`, `web/routes.py`, `web/pages.py`, `web/style.css`, and all participating checking modules: `tests/unit/test_workflow.py`, `tests/integration/test_move_tracker.py`, `tests/integration/test_move_pages.py`, `tests/integration/test_move_routes.py`, `tests/integration/test_routes.py`, `tests/integration/test_task_pages.py`, `tests/integration/test_comment_pages.py`, `tests/e2e/test_moves.py`, `tests/architecture/test_trace.py` and `tests/architecture/test_shapes.py`. Every path exists, every checking module names a real SRS requirement or acceptance criterion and no named requirement is unknown. Keep the existing trace walks and their nonempty/reverse checks (T16; CP-340).

#### Implement

Infer from failing tests.

#### Verification gate

From the change worktree root in the locked environment:

```sh
pytest products/tracker17/tests/architecture/test_trace.py
pytest products/tracker17/tests/
```

From the product root:

```sh
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: the new completeness check and all existing trace checks pass, every command exits 0 and no unrelated test fails. The workflow implementation-byte check is Task 3's review deliverable, not a permanent architecture test against a fixed base.

### Task 3: Review the change's file fence and retained assertions (`web/pages.py`, `web/routes.py`, `web/style.css`, `domain/workflow.py`, `tests/`)

**Dependencies:** Tasks 1 and 2 — reviews the implementation, checking tests and completed feature trace they produce.

**What to build:** A verdict for each one-change deliverable below against this branch's merge base, recorded in Developer Review Notes; add no suite test and change no product record (`change_spec.md` CP-335, CP-342 and Request; `change_design.md` § Records this change makes false).

#### Deliverables verified by review

- `web/pages.py` no longer contains `_WITHHELD_MOVES` — worktree-root `grep -n "_WITHHELD_MOVES" products/tracker17/web/pages.py` prints nothing and exits 1; reading the move-rendering diff confirms no replacement withholding rule (`change_spec.md` CP-319).
- Product files outside the named scope are unchanged — run the following worktree-root command; it must print nothing. This includes the timed run, application, persistence, composition, errors, exports, dependency pins and all product records (`change_spec.md` Request and Out of Scope; `change_design.md` § 2):

  ```sh
  git diff --name-only "$(git merge-base main HEAD)" -- products/tracker17 ':!products/tracker17/web/pages.py' ':!products/tracker17/web/routes.py' ':!products/tracker17/web/style.css' ':!products/tracker17/domain/workflow.py' ':!products/tracker17/tests/integration/test_move_pages.py' ':!products/tracker17/tests/integration/test_move_routes.py' ':!products/tracker17/tests/integration/test_routes.py' ':!products/tracker17/tests/integration/test_task_pages.py' ':!products/tracker17/tests/integration/test_comment_pages.py' ':!products/tracker17/tests/e2e/test_moves.py' ':!products/tracker17/tests/e2e/conftest.py' ':!products/tracker17/tests/architecture/test_trace.py'
  ```

- `domain/workflow.py` changes only its opening docstring — worktree-root `git diff "$(git merge-base main HEAD)" -- products/tracker17/domain/workflow.py` must show identical bytes after the closing docstring (`change_design.md` § 3 B).
- Existing tests retain every assertion except the thirteen named tests' obsolete move expectations — worktree-root `git diff "$(git merge-base main HEAD)" -- products/tracker17/tests` must preserve the assertions listed in `change_design.md` § 5, “Existing assertions retired and re-proved”, and every other existing assertion. Additions and requirement-docstring updates are allowed; removing unrelated coverage is not (CP-342).
- No delete control/confirmation, stale-page reload offer, session, cookie, product script or saved-data field is added — read worktree-root `git diff "$(git merge-base main HEAD)" -- products/tracker17/web products/tracker17/domain/workflow.py` against `change_spec.md` Out of Scope and design § 3 A. The plain strip remains usable without cancellation policy. Do not turn this change's absence of deletion UI into a permanent test (CP-335).
- `docs/DESIGN.md`'s trigger-height correction stays explicitly owed above and the product record itself is untouched; all pre-existing exclusions remain those of `change_spec.md` Out of Scope. Do not claim the browser risk closed from a plan or an address-only test (`change_design.md` § Records this change makes false).

#### Implement

Verified by review — no test.

#### Verification gate

Run every review command above from the worktree root and record one falsifiable verdict per deliverable. Then, in the locked environment:

```sh
pytest products/tracker17/tests/e2e/
pytest products/tracker17/tests/
```

Pass: every review criterion holds against the branch's own merge base, both suites collect their intended tests and exit 0, and there are no new failures. This task has no tests of its own. Keep the CP-338 prerequisite/failure distinction; no skipped browser run or system-pytest-only result substitutes for these gates.
