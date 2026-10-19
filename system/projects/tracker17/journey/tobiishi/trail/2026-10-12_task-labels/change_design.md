# Change Design — Labels on a task

**Date:** 2026-10-12
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the task page's label heading, label field, no-labels sentence, Add and Remove buttons and their accessible names, completion lines, refusal reasons, failed-action messages, and the console messages for failed label actions
**Language resolution:** Python — step 1, `system/projects/tracker17/project.md` `Languages:`; `core/doctrine/engineering/languages/python/README.md` and all six routed concerns read

## 1. Change Summary

This blueprint owns the boundaries, interfaces and test coverage for adding and removing a task's labels, including checking saved labels at start, as specified by `change_spec.md:L21-L106` in `tracker17 · tobiishi · 2026-10-12_task-labels`.

Code, test and `docs/` paths below are relative to `products/tracker17/` in the change worktree, resolved by `development_path.py resolve --format json --worktree .worktrees/2026-10-12_task-labels --project tracker17 --key 2026-10-12_task-labels` (exit 0; `product_path: products/tracker17`, `product_worktree` equal to that worktree).

The domain owns validation, exact membership, label order and whether an action changes anything; application owns saving and publishing the outcome; web owns forms, redirects, wording and focus, following `docs/SDD.md:L195-L205` and `change_spec.md:L68-L69`.

## 2. Blast Radius

Placement follows the five parts in `docs/SDD.md` § 3 (`L195-L205`); the module set and import edges come from `docs/nfdr.md` § 1.2 (`L121-L154`).

| Module | Status | What changes |
|---|---|---|
| `domain/` | Modified; new `labels.py` inside this part | Domain: label collection rules in `labels.py`; task state operations and saved-label validation call in `tasks.py`; typed refusals and label text-field identity in `refusals.py`; public re-exports in `__init__.py` (CP-187–CP-201). |
| `application/` | Modified | Application: two Tracker actions consume domain outcomes and save only a reported change; expose new outcomes and refusal types to web (CP-189, CP-200–CP-204; QC-5, QC-21). |
| `persistence/` | Modified at its test boundary only | Persistence: prove that its existing constructor call propagates the strengthened domain contract as whole-file unreadability; no production reader, writer or format change (`persistence/saved_data.py:L83-L98`, `L176-L202`; CP-197–CP-198). |
| `web/` | Modified | Web: two submission routes; separate label outcome address vocabulary; task-page label area, Add and Remove forms, reasons, completion/failure lines and focus targets; retain the list cell renderer (CP-182–CP-196). |
| `main.py` | Unchanged | Its existing unreadable-data exit handles new label breaks; startup tests exercise it without changing wiring or messages (`main.py:L39-L48`; CP-197). |
| `errors.py` | Unchanged | New domain refusals inherit through the existing `Refusal` base (`domain/refusals.py:L10-L24`; QC-4). |
| `tests/timed_run.py` | Modified | Measurement harness: add label-add and label-remove measurements and their landing reads at the specified volume (CP-208; `docs/SDD.md:L462-L465`). |

The transitive consumers of domain are application and persistence; web consumes application's re-exports, while main keeps its existing constructor contracts (`docs/nfdr.md:L128-L146`, `application/contracts.py:L13-L23`). All consumers appear above. No forbidden import edge or additional top-level part is needed.

## 3. Sub-jobs

### A — `domain/`

Scope: collection validation and transformation, task-level state changes, restoration integration, refusal definitions and re-exports (CP-187–CP-202).

Expose these contracts:

| Home | Interface | Contract |
|---|---|---|
| `labels.py` | `check_label(value)` | Accept the exact value or raise `EmptyLabel` / `TextTooLong(TextField.LABEL, SHORT_TEXT_MAX)`; no stripping, case folding or truncation (CP-188, CP-190–CP-191). |
| `labels.py` | `check_saved_labels(labels)` → label tuple | Validate each value and exact uniqueness within that task, preserving order; an exact repetition raises `RepeatedSavedLabel`; an empty collection is valid (CP-197). |
| `labels.py` | `add_label(labels, label)` → `(label tuple, changed)` | Validate and append a new exact value; an already-carried value returns the original collection and `changed=False` (CP-187–CP-189). |
| `labels.py` | `remove_label(labels, label)` → label tuple | Remove the exact value while retaining survivor order; a value not carried raises `LabelNotCarried` (CP-192–CP-193). |
| `tasks.py` | frozen `TaskLabelOutcome(task, changed)` | Plain task value and domain's change report; no wording or request metadata (QC-6; CP-189). |
| `tasks.py` | `add_task_label(state, task_id, label)` / `remove_task_label(state, task_id, label)` → `(state, TaskLabelOutcome)` | Resolve the task first or raise existing `TaskNotFound`; apply the collection rule against current labels; replace only that task's labels; keep all other tasks, fields and counters (CP-194, CP-199). |
| `tasks.py` | existing `restore_task(...)` | Keep its signature and apply `check_saved_labels` before constructing the Task; comment content and historical off-list assignees retain their existing treatment (CP-197, CP-209). |
| `refusals.py` | `EmptyLabel`, `LabelNotCarried`, `RepeatedSavedLabel`; `TextField.LABEL` | Distinct typed conditions under `Refusal`; use existing `TextTooLong` for the existing over-length condition; no published wording (CP-201; QC-5). |

The module `labels.py` owns collection rules without depending on the Task entity. `tasks.py` owns task lookup and replacement. Public package exports expose the task actions, outcome and new refusal types; the maximum remains the existing `domain/text.py` value (`domain/text.py:L12-L19`). This partition realizes CP-200 without a new part.

Dependencies: none.

### B — `application/`

Scope: Tracker label actions and re-exporting their plain values and refusal types (CP-200–CP-204).

Expose `Tracker.add_task_label(task_id, label)` and `Tracker.remove_task_label(task_id, label)`, each returning `TaskLabelOutcome`. A changed outcome is saved before the state becomes current. An unchanged outcome neither saves nor publishes a replacement state. Refusals and save failures propagate. The existing task lookup, edit context, list reads, `Saver.save(state)` and clock contract stay intact (`application/tracker.py:L105-L138`, `application/contracts.py:L13-L23`; QC-21, QC-49).

The application package re-exports `EmptyLabel`, `LabelNotCarried`, `TaskLabelOutcome` and existing `TextTooLong`, `TextField`, `TaskNotFound` and `SHORT_TEXT_MAX`. Web imports these only through application, per `docs/nfdr.md:L136-L141`.

Dependencies: A's task actions, outcome and refusal types.

### C — `web/`

Scope: routing and task-page presentation for labels, including failure presentation and browser proofs (CP-182–CP-196, CP-203, CP-206–CP-207).

Expose POST `/tasks/<id>/labels` to add and POST `/tasks/<id>/labels/remove` to remove. Both forms submit a field named `label`. Register both routes as submissions in `ROUTES` and run them under the existing request check and lock (`web/routes.py:L82-L93`, `L168-L190`; QC-7, QC-32, QC-53). Read values through the existing form decoder and newline normalization, with no trimming or other conversion (`web/routes.py:L114-L127`, `L156-L158`; ADR-0007 § Decision).

Every label action reached after request/body decoding redirects with status 303 through `_address`; following its GET changes nothing (`web/routes.py:L100-L107`, `L510-L511`; QC-7). `TaskNotFound` redirects to the task address, whose GET answers the existing task not-found page (CP-194). Request-check and malformed-body refusals retain their existing transport replies (`web/routes.py:L170-L195`).

The redirect protocol is label-specific: `label_added=<value>`, `label_removed=<value>`, `label_refused=<code>` with a retained `label` when permitted, or `label_failed=<add|remove>` with the retained label. Refusal codes are the closed set `empty`, `too-long`, `not-carried`. Query parsing uses presence, not truthiness, for values; only a recognized label outcome consumes retained label text. Unknown codes show the ordinary label area. No cookie, session, outcome cache or fragment is introduced (QC-8; `docs/adr/0006-last-action-travels-in-the-page-address.md` § Decision).

Route handling maps `EmptyLabel`, `TextTooLong` and `LabelNotCarried` by type. Over-long redirects carry no submitted text; parsing a too-long outcome also discards a forged retained label beside that code. Repeated adds redirect to the plain task address without an outcome. Both actions use the existing `_guarded` failure boundary; the page reports a failure without publishing the attempted change (`web/routes.py:L495-L519`; QC-49, QC-56–QC-57).

Extend `task_page(context, ...)` with an optional label presentation value, separate from `TaskEditForm`. The value carries retained label input, refusal/failure code, and added/removed label identity, all plain values; it does not contain rule decisions. Keep existing add-task and edit-task callers valid (`web/pages.py:L659-L695`; CP-199).

The label area follows the edit form as a separate section, with sibling forms rather than nested forms. Each carried label is a text element with its own Remove form; Add is its own labelled text field and submit button. `maxlength` is supplied through application from `SHORT_TEXT_MAX`; the field has no maximum-length note (CP-182–CP-186).

| Outcome | Focus target and accessible description |
|---|---|
| Added | The text element for the exact added label, with `tabindex="-1"`, `autofocus` and the completion line's ID in `aria-describedby` (CP-187). |
| Removed | Task heading at the top of the sheet, described by the removal completion line (CP-192). |
| Empty / too-long add refusal | Add's label field, described by its adjacent reason; too-long input is absent (CP-190–CP-191). |
| Remove-not-carried refusal | Label section, focusable without entering the Tab order, described by its reason (CP-193). |
| Save failure | The relevant Add form or label section for Remove, described by its failed-action line (QC-49, QC-56; SDD EX-4). |
| Plain page / repeated add | No label outcome or label autofocus (CP-189). |

Label outcomes have one focus target. A label refusal/failure takes precedence over label completion flags; a recognized label outcome suppresses task-added/task-saved completion flags on the same address. Keep ordinary edit-form outcome behavior for addresses without a label outcome. Every typed insertion, including hidden values, accessible names and reasons, passes through the existing `_escape` seam (`web/pages.py:L1-L8`; QC-36). Preserve whitespace on label text elements; target IDs are page-local positions, not raw labels.

Dependencies: B's actions and re-exports.

### D — `persistence/` boundary tests

Scope: real-file restoration, startup refusal, restart and saved-shape proofs. Production persistence stays as it is because `SavedData.load` already catches `Refusal`, and `_decode_task` already calls `restore_task` (`persistence/saved_data.py:L83-L98`, `L176-L202`).

Expose no new production interface or schema. The strengthened constructor remains the single label validator at this boundary (CP-197–CP-198; QC-22, QC-37).

Dependencies: A's restoration contract; restart after a label action also needs B.

### E — `tests/timed_run.py`

Scope: label measurements and harness self-tests (CP-208).

Expose label-add and label-remove measurements in the run's report and exit verdict. Each starts with 1,000 tasks and 20 comments per task at ordinary stated text lengths; each measures its submission and landing GET. Success requires the expected redirect, the intended saved-label delta and the landing page showing the result. Report both intervals and their sum; the action's result must appear in less than 1 second across submission plus landing, with fixture setup and saved-delta inspection outside those intervals (CP-208). Refusal, failed save, missing/wrong landing or a total at or above the bound fails the run. The existing harness exposes request and landing measurements separately (`tests/timed_run.py:L188-L237`, `L270-L302`).

Dependencies: C's routes and page protocol; existing real SavedData.

Build sequence: A first; B and D's restoration/start proofs can then proceed independently; C follows B; D's action/restart proofs follow B; E follows C. These edges name consumed contracts, not a preferred order.

Atomic-landing edges:

- `domain/labels.py` + its architecture listing/assertions + test paths named in its entry docstring — no green point between them: existing architecture checks forbid the module and the pointer check requires every named path to exist (`tests/architecture/test_shapes.py:L175-L183`, `tests/architecture/test_trace.py:L96-L107`, `L328-L332`; CP-200, CP-209).
- A's `restore_task` contract + D's CP-209 label fixtures and their dependent round-trip expectation — no green point between them: the historical fixture loads invalid labels, and the all-fields fixture and assertion require an exact repetition (`tests/integration/test_saved_data.py:L560-L604`, `L834-L845`).

## 4. Code Strategy

| Sub-job | Hint |
|---|---|
| A — `domain/` | Keep collection rules independent of Task so `restore_task` can share validation without an import cycle. Use an ordered tuple for labels and exact membership for changes; any set used to detect saved repetitions is auxiliary, never the returned order (CP-182, CP-188, CP-197). |
| B — `application/` | None |
| C — `web/` | Carry label outcomes through the shared URL builder; use fragment-free native autofocus on one focusable target with the outcome as its accessible description, following ADR-0003/0006 and SDD RT-9. |
| D — persistence boundary tests | None |
| E — timed harness | Measure actual actions and their landing reads against the real saver, and validate the saved delta outside the timing interval; a redirect alone does not prove success (QC-48). |

## 5. Test Additions

Row IDs below identify coverage, not test implementation names. Every new test module names the SRS requirements or acceptance criteria it checks, per CP-200 and `docs/SDD.md:L451-L460`.

| Row | Sub-job | Test file | Add / modify and coverage |
|---|---|---|---|
| T1 | A | `tests/unit/test_labels.py` | Empty and 201-code-point refusals; 200-code-point boundary including a non-BMP character; spaces-only and surrounding-space values; exact case-sensitive comparison; append after prior labels; duplicate add unchanged; remove-middle survivor order; removal of absent, empty or case-mismatched value; empty collection and remove-last result (CP-182, CP-187–CP-193, CP-202). |
| T2 | A | `tests/unit/test_tasks.py` | Task label actions preserve all non-label fields, other tasks and counters; outcome changed flags; missing-task precedence for both actions; no mutation of input on success or refusal; `restore_task` rejects all three saved breaks and accepts empty/valid label collections (CP-194, CP-197, CP-199, CP-201). Add assertions without retiring the edit's existing assertions. |
| T3 | B | `tests/integration/test_label_tracker.py` | Add/remove save exactly once before publication; repeated add sends the saver nothing; every refusal sends nothing; saver failure for each changed action leaves current state unchanged; list/read-back and non-label fields remain correct (CP-187–CP-194, CP-199, CP-204; QC-49). |
| T4 | C | `tests/integration/test_label_pages.py` | Labels in order with Remove and Add, label-less sentence, exact Add/Remove words and accessible names containing label and task; maximum sourced through application without adjacent note; no nested forms; literal/whitespace text and hidden values; one focus target and description for each outcome; old edit form intact (CP-182–CP-186, CP-199, CP-203). Assert wording from the change's published-text artifact. |
| T5 | C | `tests/integration/test_label_routes.py` | Through real Site/application/domain with clock and recording saver: add, surrounding spaces, spaces-only, 200 code points including non-BMP via a crafted request, duplicate no-save/no-message, case-different add, remove-middle and remove-last; empty refusal with retained field; over-long refusal with no input in redirect or page; stale removal; missing task for each action; redirect and read-back for every case, with unchanged saved state on refusal (CP-187–CP-194, CP-203). |
| T6 | C | `tests/integration/test_label_routes.py` | Real SavedData saver for representative success and each domain refusal: compare file bytes on refusal and prove restart read-back on success; project list Labels cell remains its existing comma join and `none` rendering (CP-196, CP-198–CP-199). Save failures use an injected failing saver and assert page/console failure, no success line, retained permitted input and no Python error text (QC-49, QC-56–QC-57). |
| T7 | C | `tests/integration/test_label_routes.py` | New routes retain Host/fetch checks, 303, no cookie, response policy and serialized request handling. GET/reload/back-equivalent reads never repeat writes; unknown label codes consume no retained text; mixed outcome flags yield one description/focus target. Shared saved state is used after a stale page (QC-7–QC-8, QC-31–QC-34, QC-53; CP-189, CP-193). |
| T8 | C | `tests/integration/test_label_listener.py` | Real loopback listener with application/domain and handed-in saver/clock: read populated/empty area, submit add, duplicate, remove, each add refusal and stale remove, follow redirects and read the list. Send `same-origin` marks for submissions (request's real-server proof; CP-203). |
| T9 | D | `tests/integration/test_saved_data.py` | A real file containing each saved-label break raises UnreadableData and returns no partial state; include a valid task before the invalid task. Accept no labels, spaces-only, exactly 200 code points including non-BMP, case-distinct labels and the same label on two different tasks. Compare bytes and directory listing (CP-197, CP-205; QC-37, QC-51). |
| T10 | D | `tests/integration/test_start.py` | Separate empty, 201-code-point and repeated-label cases call real `main.start`; nonzero result, exactly the existing unreadable-data console line naming location, no ready line/listener, untouched file bytes/listing (CP-197, CP-205). Keep the existing exact-message assertion intact. |
| T11 | D | `tests/integration/test_saved_data.py` | Add label, reload, remove label, reload; assert exact saved keys, People list, counters and every other task field. Valid-label fixture replaces the repeated fixture, and its label-only round-trip expectation follows that fixture (CP-198–CP-199, CP-209). |
| T12 | A | `tests/architecture/test_shapes.py`, `tests/architecture/test_trace.py` | Replace only the CP-209 no-label module assertions with labels-present assertions; add `labels` to the landed words. Re-prove feature-set containment, state field set, existing feature entries and excluded features. Check the label entry's FR-23/FR-40, all participating modules and all checking test paths (CP-200–CP-201, CP-209; QC-11). Existing import/reach/frozen checks cover new modules. |
| T13 | C | `tests/integration/test_routes.py` | Extend QC-7's route samples with accepted add/remove setup; keep accepted-save and policy assertions. Extend `test_no_socket_connection_is_made` with both actions and a recording-saver test with both actions and subsequent reads, receiving only saves (CP-206; QC-35, QC-54). |
| T14 | C | `tests/e2e/test_labels.py` | From real main in Chromium, keyboard-only Add focuses the added label text element in the viewport, outside ordinary Tab stops, with the completion line as computed accessible description; keyboard-only Remove works and focuses the heading with its description. Verify field/section focus and computed descriptions for empty/stale refusals (CP-187, CP-190, CP-192–CP-195, CP-207). |
| T15 | C | `tests/e2e/test_labels.py` | Enter a label containing `<`, `&` and `"` through the native field; task page and project's Labels cell show it literally. Include surrounding spaces and exact accessible naming; native `maxlength` remains the domain maximum (CP-185–CP-188, CP-196, CP-207; QC-36). |
| T16 | E | `tests/integration/test_timed_run.py` | Run report includes add/remove at 1,000 tasks, 20 comments each, and stated ordinary label lengths. Prove same-origin requests, intended saved delta, unchanged other fields, correct landing, failing verdict for refusal/failure/false success/wrong landing, and the strict one-second bound for submission plus landing for both actions, including two individually short intervals whose sum exceeds the bound (CP-208; QC-48). |
| T17 | A, D | `tests/integration/test_saved_data.py` | Retire the historical test's invalid-label acceptance; keep historical off-list assignee and unrestricted comment assertions. T9/T10 re-prove the invalid-label clauses as refusal/start rejection; T11 re-proves all-fields round-trip with a valid unique-label fixture (CP-209). |
| T18 | All | CP-210 commands; no new test file | On a disposable `git archive HEAD` copy initialized as a Git repo, both specified pytest invocations pass. Product-root Ruff format/lint and mypy commands pass; timed run passes. These are execution checks owed by the change, not results claimed by this design (CP-210). |

Example coverage, in the order of the spec's table (`change_spec.md:L114-L144`):

| Example | Rows |
|---|---|
| Populated area and accessible Remove; empty area; Add/Remove words; field maximum | T4, T8, T15 |
| Add `ui`; surrounding spaces; spaces-only; 200 code points including emoji | T1, T3, T5, T14–T15 |
| Repeated `bug`; case-distinct `Bug` | T1, T3, T5 |
| Empty refusal; 201-code-point refusal | T1, T5, T8, T14 |
| Remove `ui` among survivors; stale-tab removal | T1, T5, T8, T14 |
| Missing task; keyboard-only add/remove | T2, T5, T14 |
| Labels cell with labels and with none | T6, T8, T15 |
| Each invalid saved-label case; same label on different tasks; spaces-only/exact boundary load | T9–T10 |
| Restart preserving keys; non-label fields/edit unchanged | T2–T4, T6, T11 |
| Feature entry/pointers; typed refusals | T1–T5, T9, T12 |
| Required suites/tests; browser proofs; timing; four old assertions; command gates | T1–T18 |

Rule-implied edges beyond those examples: remove-last then read the empty area (T1/T5/T8), missing task for Remove as well as Add (T2/T5), empty saved collection (T9), valid entries before a later invalid one (T9), failed saver for each action (T3/T6), GET replay and forged outcome flags (T7), escaped hidden/accessible values (T4/T15), and current-state checks after stale input (T5/T7). No assertion is dropped without a replacement row.

## Records this change makes false

None — read `docs/adr/README.md`, Accepted ADR-0001–0009, `docs/nfdr.md` §§ 1–10 and applicable Review Notes, `docs/fdr.md` and `docs/SDD.md` § 3; this delta changes no part, edge, schema or standing rule in those records.

The startup-page discrepancy in FDR R-25/R-26 and SDD § 3's main/SM-6 rows is an existing gap explicitly excluded by `change_spec.md:L176-L198`; it is not made false by adding label validation. CP-197 uses the existing nonzero startup refusal and does not add unreadable-data pages.

## Architect Review Notes

- **(b) Order and uniqueness by construction:** label collections stay tuples; adds append and removes retain survivor order; saved repetition checks do not return a set. This realizes CP-182/CP-187/CP-192/CP-197 regardless of incidental state ordering (`change_spec.md:L21-L59`).
- **(b) Domain outcome:** `TaskLabelOutcome.changed` carries the domain's exact-membership verdict; application does not infer it by comparing states. This implements CP-189 and QC-21 while retaining the existing edit contract (`application/tracker.py:L105-L114`; `docs/nfdr.md:L167-L182`).
- **(b) Stateless presentation:** the route/query vocabulary, separate label presentation value and focus targets in C settle how the page realizes CP-187–CP-194. A single recognized label outcome prevents competing autofocus targets; opaque positional IDs avoid putting typed labels into identifiers. ADR-0003/0006 and `docs/SDD.md:L339-L346` require native focus and fragment-free redirects.
- **(b) Native maximum and rule boundary:** the 200-code-point case containing a non-BMP character is proved at the domain and crafted-request boundaries, not by forcing extra characters through the native field. SDD RT-10 explicitly permits the browser's UTF-16 count to be stricter (`docs/SDD.md:L347-L365`); T1/T5 prove the rule and T4/T15 prove the field maximum.
- **(b) Timing through the result:** E enforces the sum of submission and landing intervals. CP-208 requires the result within one second; two individually passing intervals can exceed that bound together, so independent interval checks alone do not prove it (`change_spec.md:L96`; `tests/timed_run.py:L199-L236`).
- **(b) Missing-task and removal checks:** resolve the task before the label rule. An absent Remove value, including an empty or over-long forged value, is `LabelNotCarried`, not an add-validation error. CP-193/CP-194 distinguish these conditions; no new observable refusal is needed (`change_spec.md:L40-L44`).
- **(a) CP-209's fixture and its dependent assertion:** `_state_holding_every_field` is named for correction, but `test_tasks_and_counter_round_trip_every_field` independently expects its repeated labels at `tests/integration/test_saved_data.py:L604`. Change that label-only expectation with the named fixture. Keeping it would contradict the required unique-label fixture. T11/T17 preserve all other assertions and replace invalid-label acceptance with rejection coverage; this is the only dependent old expectation added to CP-209's named sites.
- **(e) Harness ownership:** SDD § 3 places production logic, while SDD TS-5 owns the measurement requirement (`docs/SDD.md:L195-L205`, `L462-L465`). E belongs in the existing test harness, not a production part; production placement in A–C is fully covered by the parts table.
- **QC-5 — pass:** refusals are defined/raised in domain, passed through application and mapped by type in C; no exception-message parsing or application-defined refusal is part of the contracts (A–C; `docs/nfdr.md:L57-L67`).
- **QC-8/QC-23/QC-27 — pass:** C keeps outcome state in addresses and rendering arguments, extends the existing request lock and shared URL builder, and calls application for every label decision; no session, new browser framework or script is required (C; `docs/nfdr.md:L80-L85`, `L191-L195`, `L212-L216`).
- **QC-12 — pass:** the sole new production module is the feature entry CP-200 requires; one outcome joins the rule result to save/no-save. No new top-level part, adapter or saving abstraction is added (A–C; `docs/nfdr.md:L115-L119`).
- **QC-20/QC-21 — pass:** A holds rules and typed values without I/O or operator wording; B branches only on the domain report and uses its injected saver. All published strings belong to the text artifact named by the header (A–C; `docs/nfdr.md:L162-L182`).
- **QC-22/QC-25 — pass:** D retains the existing file reader and format; validation belongs in the constructor. A future format-only replacement remains inside persistence because the label contracts expose no file shape (A/D; `docs/nfdr.md:L183-L190`, `L201-L205`). QC-26's saving-contract gate and QC-46's added-field gate are not triggered: neither contract nor saved fields change (CP-198).
- **QC-24 — not triggered:** main has no source change; startup behavior is checked in T10 (`main.py:L39-L48`).
- **QC-36 — pass:** all new typed insertions, including hidden fields and accessible names, use `_escape`; the existing Labels cell stays as it is. T15 proves browser read-back rather than source spelling (C; `docs/nfdr.md:L277-L285`, `web/pages.py:L438-L456`).
- **QC-40 — pass for this review, with feed limitation recorded:** the locked packages are the 15 entries in `tests/requirements.txt:L4-L18`. The public GitHub advisory query below returned `[]`, exit 0, on 2026-10-12. It checks GitHub-reviewed critical advisories affecting those exact pins; it does not assert absence of all vulnerabilities. No pin or dependency format changes.

  `gh api 'advisories?ecosystem=pip&severity=critical&affects=ast_serialize@0.12.1,greenlet@3.5.6,iniconfig@2.3.1,librt@0.16.0,mypy@2.4.0,mypy_extensions@1.1.0,packaging@26.3,pathspec@1.1.1,playwright@1.63.0,pluggy@1.6.0,pyee@13.0.1,Pygments@2.21.0,pytest@9.1.1,ruff@0.16.10,typing_extensions@4.16.0&per_page=100' --jq '[.[] | {id: .ghsa_id, severity, published: .published_at, withdrawn: .withdrawn_at, url: .html_url}]'` → `[]`.

  The repository-specific alerts check returned HTTP 403, `Dependabot alerts are disabled for this repository`, from `gh api 'repos/<instance-repo>/dependabot/alerts?state=open&per_page=100'`; the public advisory query supplies this review's package evidence. Repository alert monitoring remains an operational gap against `docs/nfdr.md:L312-L317`; no repository setting or authentication scope is changed by this design.

  The installed cached browser's Info.plist reports `CFBundleShortVersionString=153.0.8010.12` at `~/Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/Info.plist` (read with Python plistlib). Google's [2026-10-06 desktop release](https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_086471744.html?hl=de) lists newer 155.0.8059.39/.40 builds and critical fixes. The pinned browser has no claim of being current or vulnerability-free; `docs/nfdr.md:L976-L989` RN-33 explicitly permits that build through 2026-11-07, so the dated exception applies on this review date.
- **QC-41 — pass:** the design uses task labels and existing local state only; no secret, credential, account or login is introduced (A–C; `docs/nfdr.md:L328-L332`).
- **QC-60 — pass at design scope:** the contracts require existing Python 3.11-compatible tuples, frozen dataclasses, enums and standard URL/HTML helpers; no newer runtime feature or new library is required. No Python 3.11 execution result is claimed (`docs/nfdr.md:L470-L475`; ADR-0002 § Decision).

Cold-read: owning parts and all transitive consumers accounted for; interfaces and dependency edges settled; every Example and rule-implied edge mapped in § 5; explicit order/no-save/focus mechanisms and their decisions recorded; records reviewed; `Publishes text` settled. This is a design review, with no product suite executed.
