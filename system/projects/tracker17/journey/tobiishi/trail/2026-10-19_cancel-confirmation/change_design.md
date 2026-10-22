# Change Design — The cancelled move and its in-place confirmation

**Date:** 2026-10-20
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the cancelled buttons on task rows and task pages, the confirmation sentence and its two controls, the move completion line, the refusal and failure messages beside the task's status, and the console's move failure message

This document owns the structural delta for `tracker17 · tobiishi · 2026-10-19_cancel-confirmation`.
The request and `change_spec.md` in that change own scope and CP-319–CP-342.
Product paths below are relative to `products/tracker17/` in this change's worktree.

---

## 1. Change Summary

Add the confirmation entirely inside `web`: the ordinary move submission opens it without saving,
a distinct confirming submission performs the existing move, and backing out returns to the same
page without saving. Remove the page's withholding of allowed moves. These are design decisions
implementing `change_spec.md` CP-319, CP-321, CP-327, CP-329 and CP-330.

Use the existing workflow and application surfaces unchanged. `domain/workflow.py`, `allowed_moves`
and `move_task`, already own the ordered moves and current-state validation;
`application/tracker.py`, `Tracker.move_task` and `_save_then_publish`, already save before publishing
the new state. The only domain edit is the feature-entry docstring required by CP-340.

The confirmation is a page-load state carried in the address, with one selected task and one focus
target. It is not a new saved field or a session. This follows `docs/SDD.md` § 4 RT-7–RT-9 and
`docs/adr/0006-last-action-travels-in-the-page-address.md` § Decision.

---

## 2. Blast Radius

`docs/SDD.md` § 3, “The parts”, assigns page building, addresses, requests and the stylesheet to
`web`. Its `Lives in` cells name the shared root unit; the `Owns` cells name each part's directory
(`docs/SDD.md:199–215`). Place every added runtime responsibility in that existing `web/` part.

| Module | Status | What changes |
|---|---|---|
| `web/` | Modified | Owning part: `web`. `pages.py` owns the reusable confirmation markup, selection of the one focus target, button restoration and insertion of the confirmation into the ordered moves. `routes.py` owns the address state, read-only opening/back-out, the separate confirming submission, current-state lookups, response headers and existing typed refusal/failure routing. `style.css` owns the strip, sentence geometry, focus ring and the confirming/back-out button styles. |
| `domain/` | Modified — documentation only | `workflow.py`'s opening feature trace names every participating module and checking test under CP-340. No rule, type, value, signature, export or workflow order changes. |
| `application/` | Unchanged | Reuse `Tracker.task`, `allowed_moves`, `move_task`, `project_tasks` and their present return values (`application/tracker.py`, those named methods). |
| `persistence/` | Unchanged | Reuse the save contract; add no field or format change (CP-327 and CP-334). |
| `main.py` | Unchanged | Keep the existing wiring and clock injection (CP-328 and CP-341). |
| `errors.py` | Unchanged | Reuse the existing error hierarchy and move refusal types (CP-331–CP-334). |

Transitive review: `docs/nfdr.md` § 1.2 QC-13–QC-18 permits the current dependency graph. The domain
edit changes no public surface, and no module imports a new `web` contract from outside `web`.
Consequently no importing production part needs a change. Keep all new page/route types internal to
`web`; keep `web/__init__.py`'s exports unchanged. No import exemption or new top-level part is needed.

Tests are in § 5. No change reaches `tests/timed_run.py` or another repository (request, Guardrail).

---

## 3. Sub-jobs

### Sub-job A — `web/`: one confirmation carried through requests and pages

**Scope:** `web/pages.py`, `web/routes.py`, `web/style.css` and the checking tests named in § 5.
The route and page changes form one browser capability; the two files are not independently
activated features. This sub-job remains within the `web` part of `docs/SDD.md` § 3.

**Exposes:** the following internal page/route contract and browser request contract. These are the
architect's choices on 2026-10-20, realizing CP-321–CP-335.

#### A.1 Address state and request contract

| Request or address state | Contract |
|---|---|
| Existing `POST /tasks/<id>/move`, `status=cancelled`, existing `place` | An opening request only. Never call the mutating tracker method on this branch, even if extra form fields claim confirmation. Resolve the saved task and consult its allowed-moves tuple under the request lock. If cancelled is allowed, answer with a 303 to its project or task page carrying `move_task=<id>&move_confirm=cancelled`; otherwise redirect to the current-status refusal landing. If the target is gone, use the existing not-found landing. |
| Project/task page with `move_confirm=cancelled&move_task=<id>` | Read the target and the workflow's allowed moves afresh under the existing request lock. If cancelled is in the returned tuple, render one confirmation. Otherwise render the current status with the existing not-allowed refusal code and its reason, no confirmation. An absent target answers not found. A project page never renders a target from another project. |
| New `POST /tasks/<id>/move/confirm`, existing `place` | The confirming intent for this capability. The target is fixed to cancelled; a submitted `status`, shown status or confirmation flag does not select another operation. Call the existing `Tracker.move_task` once. Map `MoveNotAllowed` and `TaskNotFound` through their existing outcomes; unexpected failure stays inside `Site._guarded`. Every recognized submission answers 303. |
| Back-out control | A native submit button in its own GET form targeting the originating project/task page. Carry `move_task=<id>&move_back=cancelled`, without a confirmation or outcome key. This is a read-only page request, so Enter and Space work without a script or a new action route. |
| Page with `move_back=cancelled&move_task=<id>` | Render the ordinary moves and put the sole focus on the restored cancelled button. Render no completion line or confirmation. If the current workflow no longer offers that button, use the current-status refusal landing rather than fabricate a disallowed button. |
| Other `POST /tasks/<id>/move` targets | Preserve existing first-press saving, invalid-target refusals, place fallback and failure behavior (CP-330; `web/routes.py`, `Site._move_task`). |

Use `_address` for every newly built page address and form target carrying query values. Keep the
existing `place=list` versus task-page fallback. Derive a list landing's project from the saved task,
not a submitted project identity. These choices preserve `web/routes.py`, `_address` and
`Site._move_task`, and realize CP-321, CP-327 and CP-331 without a second routing rule.

The presence of a confirming endpoint is an intent distinction, not proof that a browser previously
opened the strip. Add no token, cookie or server-side pending state. The existing Host and
Sec-Fetch-Site checks remain the request boundary (`docs/nfdr.md` QC-31, QC-32; `web/routes.py`,
`Site.handle`). GETs to the confirming action do not call an action and retain the 404 fallback.

#### A.2 Page model and reusable confirmation

Extend the existing page inputs with `MoveInteraction`, an immutable value with `task_id` (one task
identity) and `mode` (a `MoveInteractionMode` member, `CONFIRM` or `BACK_OUT`). The optional page
keyword is `move_interaction`, defaulting to `None`. Keep it separate from `MoveOutcome`, whose refusal,
failure and completion cases retain their current meaning (`web/pages.py`, `MoveOutcome`).
`project_page` and `task_page` receive that keyword, preserving existing callers. No new application
method or domain preview is needed.

The route resolves target existence, page membership and allowed moves from the saved state.
It passes either the selected interaction or the existing refusal outcome to the page. Membership
in `Tracker.allowed_moves(task.status)` consumes the rule's answer; neither a status-to-moves table
nor a list of allowed source statuses belongs in routes or pages (CP-319, CP-331).

Define one reusable strip builder inside `web/pages.py`. Its input is plain text for the sentence
and both controls, the confirming POST destination and hidden fields, the back-out GET destination
and hidden fields, a unique sentence identity, the trigger-size context, and whether the sentence
owns focus. Its output is the sentence followed by two separate native button forms in that order.
It knows no task type, cancelled status, workflow or tracker action. The move-specific caller supplies
those values. This is the reuse boundary for CP-335; no deletion control or unused deletion-specific
branch is added.

Render every workflow tuple in its returned order. Replace only the selected task's cancelled
button with the strip. Retain the other move forms and all other rows/forms. The normal cancelled
button uses the existing move endpoint and existing two hidden fields; its restored version may
add autofocus, never a positive tabindex (CP-319–CP-321, CP-329).

The selected move interaction owns focus before any unrelated outcome. Normalize conflicting move
query modes to one interaction: recognized refusal, failure, completion, opening, then backing out,
in that precedence order. Emit only one autofocus attribute, suppressing other focus/outcome decorations without removing
the ordinary forms. Unknown interaction codes or an interaction for another task on a task page
have no interaction effect. This extends the existing outcome precedence in `web/pages.py`,
`project_page` and `task_page`, to realize CP-324 and CP-326 by construction.

The sentence is a noninteractive element with `tabindex=-1` and autofocus, without a form ancestor
that could submit on Enter. Confirm and Back out immediately follow it in DOM/tab order. The sentence
has an unconditional focus ring on `:focus`. Only the confirmed save uses the existing status-word
focus and accessible-description completion mechanism (CP-324, CP-327).

Use a stable trigger slot within the moves container. The sentence occupies its full width and at
least its height; the controls follow below that occupied rectangle. Size the confirming control
from that same trigger context. Avoid content-driven flex redistribution that puts a confirming
button under any part of the old trigger. On the task page retain the existing move-control height
as the trigger height; the record wording owed for this choice is listed below. Scrolled geometry
remains a browser-proved condition, not a claim inferred from DOM order (CP-323, CP-325, CP-338).

#### A.3 Reload and history

Send `Cache-Control: no-store` on pages carrying the move interaction or its outcome. A successful
move response also sends `Clear-Site-Data: "cache"` to evict prior confirmation documents from the
origin's browser history cache. Apply this on successful ordinary moves as well as confirmed ones,
so another tab's move to done cannot leave an eligible cached confirmation behind. Keep cookies,
storage and execution-context clearing out of the header. These are response decisions implementing
CP-326 and the Examples row “confirmed … then goes back”.

Do not rely on no-store alone: Chrome permits eligible no-store documents in its history cache
([Chrome, “Enabling bfcache for Cache-Control: no-store”](https://developer.chrome.com/docs/web-platform/bfcache-ccns)).
Chromium's documented cache-removal behavior includes eviction of matching history-cache entries
([Chromium, “Clear BFCache during browsing data removal”](https://groups.google.com/a/chromium.org/g/blink-dev/c/1jIrhBN0XTU)).
The loopback origin is potentially trustworthy under the Secure Contexts algorithm
([W3C, § 3.1](https://www.w3.org/TR/secure-contexts/#is-origin-trustworthy)). Require the browser
history test in § 5 to demonstrate this header combination on the pinned browser without disabling
its history cache; no product script or weakened history expectation is an alternative.

**Depends on:** none. Reuses the application interfaces already present.

### Sub-job B — `domain/`: finish the workflow feature trace

**Scope:** only the opening docstring of `domain/workflow.py` and its trace assertion.
Name the changed checking modules, including the route-policy, task-page and comment-page checks
that also inspect the workflow controls. Keep all workflow implementation bytes unchanged (CP-340).

**Exposes:** the completed feature-to-module/test pointers, using existing files only.

**Depends on:** none. The test paths in § 5 already exist, so the docstring can name them before
their new assertions are added (`tests/architecture/test_trace.py`, `missing_paths`).

**Build sequence:** A and B have no dependency on one another and can start independently. No
atomic-landing edge exists between these two sub-jobs: the docstring-only change has its own green
point against the existing files.

Within A, the button, renderer and request adapter are one confirmation capability. Its internal
page/route interface is A.2; it adds no cross-part ordering edge.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — `web/` | Keep opening/back-out as address-only reads and saving behind the distinct POST intent. Reuse `Site.handle`'s lock and `Site._guarded`; never perform a trial mutation to validate opening. Use one plain strip builder and a stable trigger slot, with the focused sentence outside either button's form. Pair no-store on interaction/outcome pages with cache eviction after successful moves for history revalidation. Browser tests decide focus and old-click-coordinate behavior. |
| B — `domain/` feature trace | None |

No write outside the instance/product worktree is part of this design.

---

## 5. Test Additions

Use the real Site, Tracker and SavedData with an injected clock/saver at layers 3 and 4, and the
existing main-started Chromium harness at layer 5, as `docs/nfdr.md` § 9 specifies. Extend existing
modules; add no test dependency. Each added test names its SRS requirement or acceptance criterion
(CP-340). Assertions about offered moves derive the expected tuple through the workflow's public
answer; they never restate its table (request, Guardrail).

E1–E32 below mean the `change_spec.md` Examples rows in their existing order, from “A project's list”
through the full-suite row. The mapping is explicit so both example and rule coverage can be read.

| Row | Sub-job | Test file | What to add / modify |
|---|---|---|---|
| T1 | A | `tests/integration/test_move_pages.py` | E1–E3: every saved status on row and task page offers exactly the workflow tuple in order, with no initial strip; cancelled has the specified visible/accessibility labels. Assert the withholding symbol is absent from `web/pages.py`. CP-319. |
| T2 | A | `tests/integration/test_move_pages.py` | E5–E7: both places and both allowed source states; first press leaves disk bytes/state/save count unchanged, replaces only the selected button, keeps other moves/rows/forms, emits no completion, and orders sentence/confirm/back-out. Escape `<`, `&`, double and single quotes exactly once in sentence and accessible names. CP-321–CP-322, CP-336. |
| T3 | A | `tests/integration/test_move_pages.py` | E4, E8–E9: structural half of native buttons/forms, no shortcut/disabled/positive tabindex; sentence is outside a submitting form, is the only autofocus, tabindex -1; confirm/back-out follow in DOM order. Query collisions choose one focus/one strip, no unrelated completion. CP-320, CP-323–CP-324, CP-326. |
| T4 | A | `tests/integration/test_move_routes.py` | E11–E13, E22: opening, reload, repeated GET, back/forward-address reads never save; confirm on each place from each allowed source state saves once, changes only the status value in the entire serialized state, and lands with one status focus/one described completion/no moves/strip. Completion reload saves nothing. Revisited confirmation after cancellation gives the current refusal, not a strip. CP-321, CP-326–CP-327. |
| T5 | A | `tests/integration/test_move_routes.py` | E14: overdue row before confirmation, none after; clock handed in fixes the date and no module name is patched. CP-328. |
| T6 | A | `tests/integration/test_move_pages.py` and `tests/integration/test_move_routes.py` | E15: Back out on both places restores only the selected cancelled button with the sole autofocus; no completion/strip and identical disk/state/save count, including reload. If another tab removes that move, no disallowed button is fabricated; focus/reason describe current status. CP-329 with CP-319/CP-331. |
| T7 | A | `tests/integration/test_move_routes.py` | E16–E17: an ordinary cancelled submission, including one carrying forged confirmation/status fields, cannot save. Other move targets retain first-press success and present invalid/missing-target refusals. A confirming submission cannot select a different target with a field. CP-330. |
| T8 | A | `tests/integration/test_move_routes.py` | E18–E21: first and confirming presses after another tab moves todo to in-progress are accepted appropriately; after a move to done or cancelled both are refused. Cover both places. Every refusal proves byte-for-byte identical saved data, unchanged in-memory state/save count and the saved-status reason as the sole focused status's description. CP-331–CP-332, CP-336. |
| T9 | A | `tests/integration/test_move_routes.py` | E23: first/confirming press and confirmation-address read for an unknown or unreadable task identity answer not found and save nothing; list requests cannot display another project's task. CP-333. |
| T10 | A | `tests/integration/test_move_routes.py` | E24: confirming save fails through the handed-in saver; state/disk unchanged, console names action and error, page gives failure without exception text, one focused status described by it, no success line. CP-334. |
| T11 | A | `tests/integration/test_move_pages.py` | E25: exercise the strip builder with plain fixture text/destinations as well as the real cancellation caller, proving it depends on no task/workflow. Check sentence/forms/order/focus contract through the same helper. Verify the diff adds no deletion UI; add no permanent assertion requiring deletion UI to remain absent. CP-335. |
| T12 | A | `tests/e2e/test_moves.py` | E4, E8–E9, E15: row and task page, Tab/Space/Enter open the strip; focused sentence visible, tabindex -1 and visible ring; repeated Enter and Space save nothing; subsequent Tabs reach confirm then Back out. Confirm works by Enter and Space and saves the move; Back out works by both keys, restores visible focused trigger, and a later Tab traversal skips the sentence. Measure all three button targets against the 24px floor and compare sentence/confirm heights to the trigger. CP-320, CP-323–CP-324, CP-329, CP-337. |
| T13 | A | `tests/e2e/test_moves.py` | E10: short row, task page and row 40 in 60 rows with nonzero partial scroll. Drive a real double click at the original trigger's interior, including near its far edge; second click never activates confirm, strip remains, disk/status/save evidence shows no move. Include a second click at the original coordinate after the new document arrives so pre-navigation event delivery cannot give a vacuous pass. CP-325, CP-337. |
| T14 | A | `tests/e2e/test_moves.py` | E11, E18, E22: two tabs make a first press stale; no strip/save, visible focused current status/reason. Real reload/back/forward before and after confirming preserve data; after save, returning to confirmation shows current refusal. Run history case with browser history caching available, not disabled by harness launch flags. CP-326, CP-331, CP-337. |
| T15 | A | `tests/integration/test_routes.py` | E29: extend the enumerated route fixture for the confirming POST. Keep every existing route assertion. GET/action-address access leaves state unchanged; same-origin submission redirects; cross-site, same-site, none and absent marks refuse without saving. Assert policy/no cookies on every response and no new script/meta policy. Assert interaction/outcome no-store headers and cache-eviction header after successful moves. CP-339. |
| T16 | B | `tests/architecture/test_trace.py` | E30: extend workflow-entry trace coverage for all participating modules/checks named here; every path exists, requirements are real and every checking module names one. Existing architecture walks remain required. CP-340. |
| T17 | A + B | Existing architecture, lint/type and full-suite commands | E26–E28, E31–E32: run the whole browser folder and full project suite separately as CP-338/CP-342 specify; retain the three existing browser move tests with the updates below. Run the CP-341 Ruff format/lint and mypy commands from product root. Missing browser libraries are a prerequisite failure, not a passed/skipped browser verdict. No alteration to a failing experience condition or script fallback. |

Rules pass: CP-319 maps to T1; CP-320 to T3/T12; CP-321–CP-322 to T2/T4;
CP-323–CP-324 to T3/T12; CP-325 to T13; CP-326 to T3/T4/T14; CP-327 to T4;
CP-328 to T5; CP-329 to T6/T12; CP-330 to T7; CP-331–CP-332 to T8/T14;
CP-333 to T9; CP-334 to T10; CP-335 to T11; CP-336 to T1–T10;
CP-337 to T12–T14; CP-338 to T17; CP-339 to T15; CP-340 to T16;
CP-341–CP-342 to T17 and the continuity changes below.

### Existing assertions retired and re-proved

Only the thirteen existing tests CP-342 names change their established expectations. The following
table identifies the retired clauses and their replacement; every other assertion stays.

| Existing file / tests | Retired assertion → replacement |
|---|---|
| `tests/integration/test_move_pages.py`: `test_each_status_row_offers_exactly_its_allowed_moves_except_cancelled`, `test_task_page_shows_the_status_in_words_and_its_moves`, `test_every_move_control_is_a_lone_submit_button_in_a_post_form_with_no_tabindex_accesskey_or_disabled` | Withheld cancelled and fixed old button counts → T1's exact workflow tuple and T3's native-form checks. Retain status words, headings, order, accessible names and each ordinary move's lone-button POST form with status/place fields. Initial pages still show no confirmation. |
| `tests/integration/test_move_routes.py`: `test_a_row_press_saves_and_lands_on_the_project_page_at_the_rows_status`, `test_a_stale_press_is_refused_against_the_saved_status_and_saves_nothing`, `test_a_failing_saver_reports_on_the_console_and_the_page_without_exception_text` | Old offered-button lists after the same outcomes → T1. Keep every original save, failure/refusal, focus, description and landing assertion. T4/T8/T10 add the cancelled paths; they do not replace the ordinary move paths. |
| `tests/integration/test_task_pages.py`: `test_project_list_shows_every_own_task_in_seven_columns`, `test_task_page_shows_the_four_fields_in_the_one_authorized_form`, `test_task_page_opens_edit_form_from_saved_values` | Old move-cell content/form-action inventory → T1 includes cancelled's ordinary move form. Keep seven column names, all other cells, edit fields/saved values and order of existing edit/label/comment forms. |
| `tests/integration/test_comment_pages.py`: `test_written_comments_offer_no_edit_delete_or_reply_control` | Old surrounding form inventory → add the cancelled move form. Keep no-edit/delete/reply checks for comments and all comment content assertions. |
| `tests/e2e/test_moves.py`: `test_tab_to_a_rows_move_button_and_press_space_lands_on_that_rows_status_element`, `test_the_same_move_from_the_task_page_with_enter_lands_on_the_status_area`, `test_every_move_button_is_at_least_24_by_24_pixels` | Old withheld move lists/counts → compare to allowed moves supplied through the rule, including cancelled. Retain both original key presses, status focus/viewport/tabindex/description assertions and target-size floor. T12–T14 supplement them with the confirmation paths. |

No existing production signature is removed. The new optional page keyword leaves absent-interaction
calls working, so no signature assertion is retired.

---

## Records this change makes false

- `docs/DESIGN.md` § Components, `confirm-strip`, “That height is … row-control in a task row and …
  control elsewhere” (`:456–463`) needs a clarification for the task-page move: the strip sentence
  and confirming button follow the actual trigger height, including a move button using row-control
  height on the task page. The existing task-page moves use that height (`web/style.css`,
  `button.move-button`, and `web/pages.py`, `_status_section`); CP-323 requires height continuity.
  This design keeps it, rather than resize the existing move controls. The correction should state
  the trigger-height rule, with context examples, rather than infer height solely from page location.
- None of the architectural records becomes false: read `docs/adr/README.md` and Accepted
  ADR-0001–ADR-0009, `docs/nfdr.md` §§ 1–10 and RN-15/RN-33, `docs/fdr.md` Rules/Product decisions,
  and `docs/SDD.md` § 3. The graph, parts, save contract, workflow and no-script/session decisions
  stay valid. The already-unbuilt record obligations stay in the existing `deferred_decisions.md`;
  no fresh browser-test result or closure of SDD R-2 is claimed by this design.

---

## Architect Review Notes

Decisions below are the architect's, 2026-10-20. None sets a line of `change_spec.md` aside.

- **Intent boundary (b):** A separate fixed-target POST distinguishes confirming from opening.
  A boolean field on the ordinary move form was not chosen because CP-330 requires that ordinary
  submission to remain non-mutating for cancelled. No remembered pending state is needed.
- **Reuse (b), CP-335 — pass:** The strip builder has only wording, destinations, fields, size and
  focus inputs. Move validation and saving stay in the move adapter. Future deletions can supply
  different inputs without restating the strip's behavior. No generic action dispatcher, protocol,
  registry, new part or deletion implementation is justified.
- **Focus and geometry (b):** A selected interaction owns exactly one autofocus. Sentence-first
  markup alone cannot establish the old button's covered rectangle, so the stable slot and T13's
  old-coordinate press are both required by CP-324–CP-325. CP-323's trigger-height continuity takes
  precedence over DESIGN's location shorthand; the owed clarification is listed above.
- **Back-out after a concurrent move (b):** CP-329's restored-button landing applies where the
  workflow still offers that button. Otherwise CP-319's no-disallowed-control contract and
  CP-331's current-status refusal determine the landing. This fills the concurrent back-out case
  the spec does not separately enumerate; it adds no stale-page reload offer.
- **History revalidation (b):** Address-only state guarantees reads do not save, but fresh server
  validation alone cannot determine a restored browser document. A successful move therefore
  invalidates cached confirmation documents, with T14 checking actual history traversal. This is
  the construction for CP-326's post-confirmation Back example, not a change to stale-page wording.
- **NFDR delegated reviews — pass for this design:** QC-5 uses existing typed refusals and never
  branches on exception text. QC-8 keeps no pending state/cookie. QC-12 introduces no part beyond
  the requirement-paid strip helper. QC-20 changes domain trace text only, with no displayed wording.
  QC-21/QC-22/QC-24 leave application, persistence and main untouched. QC-23 consumes the workflow
  answer and keeps rules out of web. QC-27 keeps the entire browser mechanism in web. QC-36 routes
  every dynamic title, sentence value and attribute through the existing `_escape` boundary, exactly
  once. QC-41 adds no secret. QC-46 adds no saved field. QC-60 requires no language feature beyond
  the existing Python 3.11 shapes. These are reviews against `docs/nfdr.md` §§ 1–4 and 8, not claims
  about an implementation that does not yet exist. QC-25/QC-26's triggers do not fire because neither
  persistence nor the saving contract changes.
- **QC-40 dependency/browser review — pass under the existing exception:** On 2026-10-20, a read-only
  Python query parsed every `name==version` in `tests/requirements.txt` and POSTed those 15 exact
  PyPI pairs to `https://api.osv.dev/v1/querybatch`; output was `[]` for every pair. This reports
  that query's result, not an absence-of-all-vulnerabilities guarantee. Reading the installed
  `chromium-1243` app's `Contents/Info.plist` with `plistlib` returned
  `CFBundleShortVersionString: 153.0.8010.12`. Google's October 1 bulletin lists Critical
  CVE-2026-103628 in a later release
  ([Chrome release bulletin](https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop.html)).
  The older installed build therefore relies on the owner's exact-build exception through
  2026-11-07 (`docs/nfdr.md:993–1004`, RN-33), which covers this review date. No dependency pin or
  browser build is changed here. No browser acceptance run was performed in the design stage.
- **Cold read:** All six modules of the import graph appear in § 2; all added runtime logic has
  the web owner. § 3 fixes internal inputs and browser requests before the build sequence.
  § 5 maps all 32 Examples and every CP rule, including missing targets, refused/failed saves,
  reload/history, escaping and concurrent status changes. The publication verdict and record debt
  are settled above. No external-repository write or unresolved spec reading remains.
