# Change Design — Distinguish an overtaken move press from a cancellation address

**Date:** 2026-10-21
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the move refusal beside a task's status on Project — Tasks and on the task's page, for an overtaken press and for a cancellation confirmation or back-out address

This document owns the structural delta for `tracker17 · tobiishi · 2026-10-21_out-of-date-move`.
Its behavioural input is that change's `change_spec.md`, CP-355–CP-370.
Product paths below are relative to `products/tracker17/`.

---

## 1. Change Summary

Keep the workflow and the request path that applies it. Change `web` to carry the context of a
refusal into page building: a refused submission, or a cancellation address that the saved workflow
no longer permits. Render the two lines from that context. For a refused submission, give the line
and the buttons the same ordered allowed-moves value. The line's title and status come from the task
being rendered, after the refusal. This implements CP-358–CP-364 without a second workflow table.

The existing seams support this placement: `Tracker.allowed_moves` delegates to the domain query
(`application/tracker.py:L184-L186`, `allowed_moves`), and both page builders already receive that
query (`web/pages.py:L852-L862`, `project_page`; `L1325-L1335`, `task_page`).

Exact new wording belongs to the change's text record. CP-361 fixes the address line; CP-359 fixes
what the submission line communicates. The existing other refusals, completion, failure and
confirmation words remain governed by CP-363.

---

## 2. Blast Radius

Placement follows `docs/SDD.md` § 3, **The parts**: `web` owns request interpretation and page
building; `domain` owns allowed moves; `application` exposes the computed answer.

| Module | Status | What changes |
|---|---|---|
| `domain/` | Unchanged | Keep the workflow and its sole ordered table in `domain/workflow.py`. Its existing feature docstring already names all test modules used below (`domain/workflow.py:L1-L23`, **Checked by**). |
| `application/` | Unchanged | Keep `Tracker.allowed_moves`, `move_task`, the refusal exports and the saving contracts. |
| `persistence/` | Unchanged | No saved field, file format, read or write path changes. |
| `web/` | Modified | Owning part: **web**. In `pages.py`, add a typed refusal context to `MoveOutcome`, distinguish the two lines and feed the same ordered moves to the line and buttons. In `routes.py`, mark only the refusal synthesized from a cancellation interaction address as address context. |
| `main.py` | Unchanged | No wiring or runtime dependency changes. |
| `errors.py` | Unchanged | No new exception or change to the error base. |
| `tests/` | Modified | Extend `integration/test_move_routes.py`, `integration/test_move_pages.py` and `e2e/test_moves.py`; preserve the other assertions CP-370 names. No new test module. |

The import graph is unchanged: `web` reaches workflow types and queries through `application`,
never through `domain` (`docs/nfdr.md` § 1.2, QC-13–QC-19). The changed contract is inside `web`:
`routes.py` constructs the page model declared in `pages.py` (`web/routes.py:L43-L44`, import of
`pages`; `L342-L366`, `_move_view`). `listener.py` consumes `Site` and `Response`
(`web/listener.py:L17`, imports), whose contracts stay unchanged. No other production part is
transitively affected.

No change to `web/style.css`, the route inventory, address grammar, outcome precedence, focus
ownership, confirmation strip, HTTP status/header machinery or `tests/timed_run.py` is designed
(CP-358, CP-360, CP-363, CP-365, CP-368).

---

## 3. Sub-jobs

There is one affected production part, `web`, with two internal seams: its page model/renderer in
`pages.py`, and its request interpretation in `routes.py`. The request interpretation consumes the
new page-model field, so A precedes B. This is the below-module decomposition permitted by the
skill; it does not introduce a new part.

### Sub-job A — `web/pages.py`: context and refusal rendering

**Scope:** Define the context value, extend the page model compatibly, render each refusal, and
share the ordered allowed moves between the submission line and its controls. This includes the
page-model and rendered-page assertions in § 5.

**Exposes:**

- Add `MoveRefusalContext`, a closed enum with `SUBMISSION` and `CANCELLATION_ADDRESS`.
- Append `refusal_context` to `MoveOutcome`, with type `MoveRefusalContext` and default
  `SUBMISSION`. Keep the existing four fields, their order and defaults. Existing positional and
  keyword constructions retain their meaning (`web/pages.py:L171-L183`, `MoveOutcome`). The
  context is consulted only when the outcome has a refusal about the rendered task.
- `SUBMISSION` renders CP-359 for either existing refusal code. `CANCELLATION_ADDRESS` renders
  CP-361. Neither introduces a domain refusal type or changes `MoveRefusal`'s two URL codes.
- The private `_move_line` seam receives the rendered task's ordered allowed-moves tuple in
  addition to the outcome and task. Its result remains absent, or the existing kind/text pair.
  All call sites inside `pages.py` change together. Public `project_page` and `task_page`
  parameters and defaults stay as they are.
- Within each rendered row or task status area, resolve the supplied `allowed_moves` query for
  that task's saved status and use the resulting tuple for both `_move_forms` and the refusal
  line. An empty tuple selects the terminal-status wording. Format the nonempty tuple in its
  supplied order, with no sorting, filtering, enumeration of `TaskStatus`, or per-status move
  table in `web`. Outcome-presence checks must not require a second wording implementation.
- Both refusal lines continue through `_move_line_block` and `_status_word`, with the existing
  line identifier and one status focus. Titles pass through `_escape` once on their way into the
  line. The failure and completion branches keep their words.

**Depends on:** none. The allowed-moves callable is already a page input, as cited in § 1.

### Sub-job B — `web/routes.py`: mark an address refusal

**Scope:** Select A's context at the request seam and update the request/history assertions for
the address path. Keep the current workflow queries and submission handling.

**Exposes:**

- `Site._move_view` retains its result shape: a move outcome and an optional interaction, or
  not-found. Only its existing branch that finds the on-page task and finds that the workflow
  does not offer `cancelled` constructs a refusal with context `CANCELLATION_ADDRESS`
  (`web/routes.py:L342-L366`, `_move_view`).
- `_move_outcome` keeps the same recognized URL vocabulary and precedence, producing the
  default submission context. There is no new query parameter, outcome code or state between
  requests. Reopening a refused submission's landing address therefore keeps its submission
  line, as the spec's **Out of Scope** requires.
- `_move_task` keeps the existing type-based mappings and redirect addresses. A first refused
  `cancelled` press and a refused confirming POST both retain submission context. A missing or
  invalid status retains the same context and words as any other refused submission.
- Confirmation and back-out GETs still resolve task membership before the existing workflow
  query. Eligible tasks get their existing strip or restored trigger. Missing tasks, tasks on a
  different page, unknown interaction values, and recognized-outcome precedence keep their
  existing answers.
- Preserve `_pending_status` and `_stored_as_asked`: context selection changes neither the
  resolved interaction nor the response status/header decision (CP-365).

**Depends on:** A's `MoveRefusalContext` and appended `MoveOutcome.refusal_context` field.

**Build sequence:** A, then B. No separate cross-part contract is needed.

**Atomic-landing edges:**

- A's changed submission wording + its existing quoting assertions — no green point between
  them: CP-370's route, page and browser assertions quote the replaced text.
- B's address-context selection + the GET and history assertions that formerly shared the
  submission line — no green point between them: those assertions must now name the address
  line while the POST assertions continue to name the submission line.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — context and page rendering | Carry context on the existing immutable page value rather than encoding another URL outcome. Share the ordered tuple supplied by the existing query between the line and the controls; the tuple is the seam, not a second status-to-moves table. |
| B — request interpretation | None |

---

## 5. Test Additions

The rows below own the test delta. Expected new sentences are taken verbatim from the change's
text record, with CP-361's address sentence fixed by the spec. Exercise `Site.handle` with the
real `Tracker`, domain and `SavedData`, using the existing injected clock/saver and temporary
data directory (`tests/integration/test_move_routes.py` § module docstring and `world_with`).
Every refused-request case below compares saved bytes and save count before and after the request.
For a POST, the comparison also spans the landing GET, not merely the parsed state.

| Row | Sub-job | Test file | What to add / modify |
|---|---|---|---|
| T1 | A | `tests/integration/test_move_routes.py` | Extend the stale-press cases to four saved statuses × row/task page. Actually load the earlier page, change the task through the real tracker, then send a previously offered move that is now refused. For the `todo` landing, load `in-progress`, change to `todo`, then press `done`. Assert latest status/title, unchanged bytes/count through redirect and GET, correct destination, one focused non-control status, its exact accessible description, no strip, and line move names matching the page's buttons in order. Final statuses have no moves. CP-355, CP-358, CP-359, CP-362, CP-366. |
| T2 | B | `tests/integration/test_move_routes.py` | Extend `test_stale_opening_and_confirmation_use_the_saved_workflow_answer`: first `cancelled` POST and confirming POST after the task becomes `done`, and retain its `cancelled` cases, for both places. Assert submission wording for both POST paths, no confirmation, unchanged bytes/count, focus and response contract. The back-out GET now asserts T3's address wording. CP-355, CP-358, CP-366, CP-370. |
| T3 | B | `tests/integration/test_move_routes.py` | Cover final status `done`/`cancelled` × confirmation/back-out GET × row/task page. Assert CP-361's exact line and current title, no strip or task move controls, status focus/described-by, no focus on the line, 200 and `Cache-Control: no-store`, no reload/link/control inside the reason, unchanged bytes/count. Extend `test_confirmation_and_back_out_reads_never_save` to snapshot again after the intervening saved move and compare after revisiting. CP-356, CP-360–CP-362, CP-365, CP-366. |
| T4 | A | `tests/integration/test_move_routes.py` | Keep all `finished`, missing, empty and `Done` cases in `test_a_non_status_or_missing_status_is_refused_and_answered_like_a_stale_press`; cover both places. Assert the same submission line, named moves, focus, unchanged bytes/count and destination. Preserve the existing two refusal codes. CP-357, CP-366. |
| T5 | A + B | `tests/integration/test_move_routes.py` | Parameterize both contexts and places with title `a < b & "c"`. For the submission case, use an overtaken loaded page; for the address case, use a final task. Assert the description's interpolated title is the saved title exactly once, parsed text is as typed, no injected element, no double-escaped entity, and unchanged bytes/count. Include a title changed in the other tab before refusal. CP-359, CP-361, CP-366. |
| T6 | A | `tests/integration/test_move_pages.py` | Add direct page-building coverage for the extended model: default context keeps existing construction valid; explicit address context selects the address line; `_move_line` receives allowed moves through both public page builders. Hand in an allowed-moves callable whose ordered result differs from today's workflow order and assert both buttons and named moves follow that same result. An empty result names no move. This pins data flow without patching a product name or copying the workflow table. CP-359, CP-364. |
| T7 | A + B | `tests/integration/test_move_pages.py` | Keep every non-word assertion in `test_a_landing_page_has_exactly_one_autofocus_on_a_non_control_status_element_that_names_the_line` and `test_back_out_restores_only_the_selected_trigger`. Give submission and address cases separate expectations. Extend refusal checks to absence of reload, links and controls in the line. Preserve outcome precedence, plain-page handling of invalid/foreign identities, per-row isolation and the existing `The status` prefix assertion in `test_move_query_collisions_select_one_interaction_and_focus_owner`. CP-358, CP-360, CP-362, CP-370. |
| T8 | B | `tests/integration/test_move_routes.py` | Retain `test_first_press_opens_confirmation_without_a_save`, `test_missing_confirmation_targets_answer_not_found_without_saving`, `test_other_moves_keep_their_first_press_outcomes` and the tests for failed saves. Cover both eligible statuses for confirmation and back-out GETs. Assert repeated final-status address loads remain read-only. Missing/not-on-page targets, unknown values, recognized-outcome precedence and plain pages retain their existing assertions. CP-356, CP-363, CP-365. |
| T9 | A + B | `tests/e2e/test_moves.py` | Split the old `DONE_REASON`/`CANCELLED_REASON` expectations by context. `test_stale_first_press_refuses_at_the_visible_current_status` gets submission wording; `test_real_history_traversal_revalidates_the_confirmation` and `test_history_matrix_revalidates_current_saved_status` get address wording. Keep every key, focus, geometry, view, fresh-load, cache-availability, Back/Forward and saved-bytes assertion. Cover escaping in the two refusal contexts through the existing browser harness, with `<`, `&`, `"` in the title. CP-363, CP-365, CP-369, CP-370; QC-36, QC-63. |
| T10 | A + B | `tests/integration/test_routes.py` | No assertion retired and no route added. Run the route enumeration test and all four QC-63 tests: `test_pending_confirmation_response_matches_the_rendered_page`, `test_non_confirmation_move_views_keep_their_response_contract`, `test_move_interaction_and_outcome_pages_are_not_stored`, `test_move_responses_do_not_clear_site_data`. Retain 202 for rendered pending confirmation, 200/no-store for refusals and the not-found exception. CP-365, CP-368. |
| T11 | A + B | Existing suite and static checks | Keep trace/import/shape checks unchanged, including `tests/architecture/test_trace.py`. Existing edited modules name the requirements they check; no new module means no new workflow docstring pointer. Run CP-368's `ruff format --check .`, `ruff check .`, `mypy main.py errors.py domain application persistence web` from the product root. Run CP-369's integration/full suites from the repository root and the separate browser suite where supported. CP-363–CP-365, CP-368–CP-370. |
| T12 | A | Source-text check | From the repository root, `grep -rn "the move you pressed" products/tracker17/web` prints nothing (grep's no-match exit is 1). Inspect the product diff for a second workflow table, scripts, unrelated wording changes, changed pins, saved-data changes or an edit to `tests/timed_run.py`. CP-362–CP-365. |
| T13 | A + B | Design review, recorded below | QC-5, QC-8, QC-12, QC-23, QC-27, QC-36, QC-40, QC-41 and QC-60 reviews are recorded under Architect Review Notes. CP-367. |

**Retired assertions and replacements.** CP-370's old `REFUSAL_FOR` sentences are replaced by
submission expectations in T1/T4/T7 and address expectations in T3/T7. The old assertion that two
POST refusals and the back-out GET have the same reason is retired: T2 and T3 prove their distinct
words while keeping the shared workflow decision and all unchanged-state/focus assertions.
`test_a_press_on_a_cancelled_task_is_refused_with_the_cancelled_reason` retains its test and bytes
assertion, with submission wording under T1. The browser constants' shared meaning is retired and
re-proved by T9's two contexts. No non-word assertion or underlying refusal clause is removed.

**Examples pass.** Numbering the spec's Examples rows in their existing order:
E1→T1; E2→T1; E3→T1; E4→T1; E5→T2; E6→T3; E7→T9;
E8→T3; E9→T8; E10→T4; E11→T5/T9; E12→T12; E13→T8/T11;
E14→T6/T12; E15→T1–T5; E16→T13; E17→T11; E18→T11; E19→T7/T9/T11.

**Rules pass.** CP-355→T1/T2; CP-356→T3/T8, including eligible, missing and foreign-page paths;
CP-357→T4; CP-358→T1/T2; CP-359→T1/T5/T6, including empty moves and changed title;
CP-360→T3; CP-361→T3/T5; CP-362→T1/T3/T7/T12; CP-363→T8/T11;
CP-364→T6/T12; CP-365→T9/T10/T12; CP-366→T1–T5; CP-367→T13;
CP-368→T10/T11; CP-369→T11; CP-370→T1/T2/T3/T7/T9 and the retirement paragraph.
An empty task list, an outcome naming another row or no row, and query collisions remain covered
by the existing page tests T7 retains; they create no context-bearing refusal for a missing row.

---

## Records this change makes false

None among `docs/adr/README.md`, Accepted ADR-0001–ADR-0010, `docs/nfdr.md`, `docs/fdr.md` and
`docs/SDD.md` § 3: their parts, import edges, refusal types, persistence and response contracts
remain the design's constraints. In particular, the context enum is a presentation value, not
another domain refused condition under QC-5.

One already-conflicting wording example remains owed outside this artifact: `docs/CONTENT.md`
§ Message patterns → Error → **A refusal**, fifth example, says **Reload the page to see it**.
After this change that example does not describe the overtaken-press line. Replace that example
with the settled no-reload submission variants, consistent with CP-359/CP-362 and UXD UX-F4/UX-I3.
The spec already records this disagreement in **Locked Answers**, Gap 4; this design edits no
foundation or content record. CONTENT RN-26's reopened-landing case stays in the existing
`deferred_decisions.md` record gap, with no new reading set aside.

---

## Architect Review Notes

Decisions in this section are the Architect's, 2026-10-21.

- **(b) Context is request-derived, not another URL code.** Add the typed field rather than
  broadening `MoveRefusal`. The existing enum is decoded by `_move_outcome` directly from a query
  (`web/routes.py:L378-L391`, `_move_outcome`). A new enum member there would also admit a new
  forged outcome word, which CP-356 does not ask for. Appending a defaulted context preserves the
  existing address grammar and constructions while separating the two presentations.
- **(b) Move-name agreement is explicit.** A row/status area gives its line and controls the same
  ordered tuple. This realizes CP-359/CP-364 by construction instead of copying today's four
  answers from `domain/workflow.py` § `_ALLOWED_MOVES` into a new wording table. T6 makes that
  dependency observable even if workflow order later changes.
- **(b) Retain the existing prefix contract.** The submission wording must continue to begin
  `The status`, because `tests/integration/test_move_pages.py:L437-L438`,
  `test_move_query_collisions_select_one_interaction_and_focus_owner`, asserts that prefix and
  CP-370 does not release that test. The rest of the submission wording remains the text record's.
- **(d) Two seams inside one part.** A owns the model the request seam B consumes. That real
  dependency, not a preference for file order, justifies § 3's below-module split.
- **QC-5 — pass.** Domain `MoveNotAllowed` and `InvalidTaskStatus` still reach `web` through
  `application`, and `_move_task` maps the exception classes, never messages
  (`web/routes.py:L22-L43`, imports; `L744-L755`, exception branches). The GET context is
  selected from the resolved interaction request and the existing allowed-moves query. No new
  domain condition, application refusal or message parsing is introduced.
- **QC-8, QC-23, QC-27 — pass.** The appended context lives on the per-request immutable page
  model; there is no last-action store. Allowed moves still come through `Tracker.allowed_moves`,
  and only `web` changes, preserving the boundary in `docs/SDD.md` § 3, **web**, and NFDR § 1.4,
  QC-27. No domain/application HTML, direct file access, cookie or session is designed.
- **QC-12 — pass.** The two contexts pay for one enum and one defaulted page-model field in the
  existing part. No new module, part, service, persistence record or generic refusal framework is
  needed for CP-355–CP-361.
- **QC-36 — pass.** Both variants remain in the existing line-building path, which already
  obtains the title through `_escape(task.title)` (`web/pages.py:L748-L756`, `_move_line`);
  `_escape` delegates to `html.escape` with quotes (`web/pages.py:L339-L341`, `_escape`). Keep
  the title as text through that function once, and do not escape the completed HTML line again.
  T5/T9 verify the typed characters in both contexts.
- **QC-40 — pass within the owner's dated browser exception, not a clean-browser verdict.**
  The unchanged direct pins are mypy 2.4.0, Playwright 1.63.0, pytest 9.1.1 and Ruff 0.16.10
  (`pyproject.toml` § dependency-groups; resolved packages in `tests/requirements.txt`). On
  2026-10-21, the four maintainers' advisory pages returned **There aren't any published security
  advisories**: [mypy](https://github.com/python/mypy/security/advisories),
  [Playwright](https://github.com/microsoft/playwright/security/advisories),
  [pytest](https://github.com/pytest-dev/pytest/security/advisories),
  [Ruff](https://github.com/astral-sh/ruff/security/advisories).
  The version-specific PyPI JSON endpoints for all 15 entries in `tests/requirements.txt` also
  returned `vulnerabilities: []` on 2026-10-21:
  [ast_serialize 0.12.1](https://pypi.org/pypi/ast_serialize/0.12.1/json),
  [greenlet 3.5.6](https://pypi.org/pypi/greenlet/3.5.6/json),
  [iniconfig 2.3.1](https://pypi.org/pypi/iniconfig/2.3.1/json),
  [librt 0.16.0](https://pypi.org/pypi/librt/0.16.0/json),
  [mypy 2.4.0](https://pypi.org/pypi/mypy/2.4.0/json),
  [mypy_extensions 1.1.0](https://pypi.org/pypi/mypy_extensions/1.1.0/json),
  [packaging 26.3](https://pypi.org/pypi/packaging/26.3/json),
  [pathspec 1.1.1](https://pypi.org/pypi/pathspec/1.1.1/json),
  [Playwright 1.63.0](https://pypi.org/pypi/playwright/1.63.0/json),
  [pluggy 1.6.0](https://pypi.org/pypi/pluggy/1.6.0/json),
  [pyee 13.0.1](https://pypi.org/pypi/pyee/13.0.1/json),
  [Pygments 2.21.0](https://pypi.org/pypi/Pygments/2.21.0/json),
  [pytest 9.1.1](https://pypi.org/pypi/pytest/9.1.1/json),
  [Ruff 0.16.10](https://pypi.org/pypi/ruff/0.16.10/json), and
  [typing_extensions 4.16.0](https://pypi.org/pypi/typing_extensions/4.16.0/json).
  This is a bounded advisory-metadata check, not proof that the resolved packages lack defects.
  The pinned browser expectation is 153.0.8010.12 (`tests/e2e/test_moves.py`, `PINNED_BROWSER`);
  [Google's October security release page](https://chromereleases.googleblog.com/2026/10/)
  lists Critical fixes in a newer browser, including CVE-2026-106347 and CVE-2026-106358 in its
  October 20 entry. Do not call the pinned build current or free of advisories. NFDR **RN-33**
  explicitly allows this exact unchanged build at reviews through 2026-11-07, including critical
  advisories against it. That existing dated exception is the reason the browser does not block
  this review; no pin move or renewed exception is designed.
- **QC-41 — pass.** The design adds request-local presentation context and words only; it adds
  no account, key, credential or secret, within NFDR QC-41's boundary.
- **QC-60 — pass for the chosen constructs.** A uses the same enum, immutable dataclass and
  ordered-tuple constructs already used at the seams (`web/pages.py:L164-L183`;
  `domain/workflow.py`, `allowed_moves`). No new language/library feature or runtime dependency
  is chosen. This review makes no claim to have run a Python 3.11 suite.
- **Other delegated reviews.** QC-20's no-wording half remains satisfied by the unchanged domain
  rule. QC-21, QC-22, QC-24–QC-26 and QC-46 do not acquire a new review case: application,
  persistence, main, saving contracts and saved fields are outside the delta. The relevant gate
  definitions are `docs/nfdr.md` §§ 1.3–1.4 and QC-46.
- **Cold read.** The design keeps all spec lines and takes no conflicting reading. Every new
  piece of logic has its owning part in § 2; A exposes everything B consumes; the import graph
  and response machinery stay fixed. § 5 walks all 19 Examples and CP-355–CP-370, including
  retired assertions and failure/empty paths. No write outside the instance/product worktree is
  part of this delta. No product suite or acceptance run was performed in this design stage.
