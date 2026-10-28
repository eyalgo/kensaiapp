# Change Design — Delete a task from its page

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the task page's Delete task control, confirmation and failure line; the project Tasks view's deletion completion line; the console's deletion failure message; the timed run's deletion report

---

## 1. Change Summary

This blueprint owns the structure, interfaces and test changes for task deletion in
`tracker17 · tobiishi · 2026-10-28_delete-a-task`.
It implements `change_spec.md` § Rules CP-529–CP-545 through the existing `domain`, `application`
and `web` parts, and extends the timed harness.
All product paths below are relative to `products/tracker17/` unless they start with `products/`.
The Architect chose the interfaces and mechanisms below on 2026-10-28.

Deletion is one immutable state transition, followed by one whole-state save before publication.
The removed task supplies the project and title for the success address.
The first press and Back out save nothing.
The existing confirmation renderer, typed missing-task refusal and unexpected-failure catch site
remain the mechanisms used by deletion.
Project deletion, project renaming and moving a task between projects are outside this blueprint.

## 2. Blast Radius

Placement follows `docs/SDD.md` § 3, *The parts*, and the permitted imports in `docs/nfdr.md`
§ 1.2, QC-13–QC-19.

| Module | Status | What changes |
|---|---|---|
| `domain/` | Modified | Owning part **domain**: add `delete_task` in `domain/tasks.py` and its public re-export in `domain/__init__.py`. The rule finds the current task or raises `TaskNotFound`, removes that task with its nested comments, preserves every other field and both counters, and returns the new state with the removed task. Update the Tasks entry docstring for this change's requirements, collaborators and tests (CP-545). |
| `application/` | Modified | Owning part **application**: add `Tracker.delete_task` in `application/tracker.py`. It applies the domain rule and saves before publishing, returning the removed task only after success. Existing reads supply the page's current task or not-found answer. |
| `web/` | Modified | Owning part **web**: add two POST routes, deletion address decoding, one task deletion area, the project completion line and failure presentation in `web/routes.py` and `web/pages.py`. Reuse `confirm_strip`, `StripForm`, `_address`, `_escape`, `_guarded` and the task not-found page. No stylesheet or listener change is required. |
| `persistence/` | Unchanged | Existing nested comments and persisted counters already fit deletion: `domain/tasks.py:L68-L81`, `Task`; `domain/state.py:L18-L33`, `TrackerState`; `persistence/saved_data.py:L110-L126`, `SavedData.save`. Exercise the real file without a schema or saver-contract change. |
| `main.py` | Unchanged | No new dependency needs wiring; `Tracker` continues to receive the same saver and clock (SDD § 3, SM-7). |
| `errors.py` | Unchanged | Reuse the existing `TaskNotFound`, already received by web through application (`application/__init__.py`, `TaskNotFound` export; `web/routes.py:L18-L50`, imports). |
| `tests/` | Modified | Add deletion rule, real-file restart, application/request, browser and harness coverage. Extend route-wide and no-outbound checks. Retire only the assertions explicitly released by the spec's Locked Answer Gap 12. |

No part is added and no forbidden import is needed.
The additions to domain and application are additive public interfaces.
Although persistence imports domain and main imports the affected parts, their named imports and
call sites need no change; deletion changes neither a constructor nor a saving contract.
Lists, filters, sorts and Summary continue to compute from the current state rather than acquire
separate removal logic (`application/tracker.py`, `project_task_list`, `all_task_list`,
`project_summary`). Their post-deletion behaviour is proved by T7 below.

## 3. Sub-jobs

### Sub-job A — `domain/`: remove one current task

**Scope:** the deletion rule, package export and Tasks feature trace.

**Exposes:** `delete_task(state, task_id) -> (new_state, removed_task)`, where the values are
`TrackerState` and `Task`. A missing identity raises the existing `TaskNotFound` before producing
any new state. Every saved status is deletable. The returned task is the one held at execution,
including its current title and project. The result omits only that task, preserves the order and
values of all survivors, and leaves both identity counters unchanged. Nested comments disappear
with their task; there is no second comment-removal operation.

**Depends on:** none.

### Sub-job B — `application/`: save and publish deletion

**Scope:** the new Tracker action only.

**Exposes:** `Tracker.delete_task(task_id) -> Task`. Apply A to the current state, use the existing
save-before-publication seam exactly once, then return the removed task. A typed refusal or saver
exception propagates without publishing the proposed state. No clock read, existence rule,
identity issuance or comment cascade is implemented here.

**Depends on:** A's deletion function and its package export.

### Sub-job C — `web/`: task confirmation, action and landing

**Scope:** page values, presentation and request routing for deletion, plus the related route-wide
checks. Existing page entry points gain optional deletion arguments with neutral defaults, so
existing callers still build their ordinary pages.

**Exposes — page values:** a `DeleteArea` value with a closed mode vocabulary: ordinary,
confirmation, backed-out or failed. It carries presentation state only; the task page obtains its
title from the supplied current `TaskEditContext`. `task_page` accepts that area; `project_page`
accepts an optional deleted-task title. A neutral area or absent title adds no deletion outcome.
`confirm_strip`'s public contract remains unchanged (`web/pages.py:L701-L725`).

**Exposes — request contract:**

| Request | Result and saved effect |
|---|---|
| `POST /tasks/{id}/delete` | First press. Resolve the current task; if present, 303 to `/tasks/{id}?delete_confirm`. Never call the mutating Tracker action or the saver. |
| `GET /tasks/{id}?delete_confirm` | Current task page, the shared strip in the Delete task control's place. The current title supplies the sentence. |
| `GET /tasks/{id}?delete_back` | Back-out form's destination. Restore and focus Delete task with no line and no save. |
| `POST /tasks/{id}/delete/confirm` | Run B once. On success, 303 to `/projects/{removed.project_id}?deleted_task={encoded current title}`. No filter, sort or fragment is carried. |
| `GET /projects/{id}?deleted_task={title}` | Tasks view, one escaped completion line and focus at the project heading. Retain the line on reload and history navigation. An empty project retains its existing first-task invitation. |
| Failed confirming save | The existing `_guarded` site reports the deletion and error. 303 to `/tasks/{id}?delete_failed`; show the failure beside the restored Delete task control and focus it. No Python error text enters the address or page. |
| Either POST for a task no longer held | The existing missing-task path: 303 to `/tasks/{id}`, then the existing task not-found page, 404. No save. |
| Any GET for a missing task | Resolve task existence before every outcome or pending interaction. Return the existing task not-found page, 404, regardless of query. |

Both new POSTs are `SUBMISSION` routes under the existing origin checks and request lock.
The first is a submission that saves nothing; route classification does not imply a save.
Back out is a GET form to the task address, using the existing confirmation renderer's support for
that form shape (`web/pages.py:L737-L758`, `_cancellation_strip`).
The confirming target is fixed by its route, never selected from a submitted title, project or status.
Use the returned task's title for success, and the current task's title for confirmation and failure.
All new redirects use `_address`; every displayed title goes through `_escape`, with the strip
escaping its plain sentence itself (`web/routes.py:L133-L143`; `web/pages.py:L701-L725`).

**One focus and one outcome:** a resolved deletion area takes precedence over other task-page
outcomes. Within deletion, failure takes precedence over confirmation, then back-out.
With no recognized deletion state, the existing move/comment/label/edit precedence is unchanged.
An active deletion area suppresses other autofocus and outcome lines, including a move strip.
On the project page, the deletion completion takes precedence over other outcome/interaction
markers and focuses the heading, with that line as its description.
The Delete task control is a separate task-level control after the existing task content, outside
all comment items and existing forms. It appears in every status and in no list row.
The strip uses its sentence, confirming form and Back out form in that order; it uses the existing
trigger-size styling. The ordinary trigger and strip occupy the same spot.

**HTTP policy:** deletion's confirmation, back-out, failure and successful project landing are 200
with `Cache-Control: no-store`. A missing task remains 404 without that header, including when
queried for either kind of confirmation. No `Clear-Site-Data` is added.
Existing move-only 202 and caching rules are unchanged.
This choice does not promise fresh history restoration of a pending delete confirmation.

**Depends on:** B's action and returned `Task`; the application exports already used by web.

### Sub-job D — `tests/`: timed deletion and harness checks

**Scope:** extend `tests/timed_run.py` and `tests/integration/test_timed_run.py`.

**Exposes:** one deletion measurement appended after the existing Summary block, with POST, landing
GET and total durations, incorporated into the whole run's pass/fail result.
Use a fresh real-file fixture of 1,000 tasks with 20 comments each, reporting the ordinary text
lengths the fixture uses. Open the confirmation outside the timed interval.
Time the confirming POST and its landing GET separately and together.
Accept only an actual successful deletion: compare reloaded state with the independent expected
state containing exactly one fewer task and its comments, unchanged counters and all other values,
and require the completion line for the removed title on the intended project page.
Each interval and the total must be strictly below one second; equality fails.
A refusal, unexpected failure, wrong redirect, wrong page, wrong saved delta or missing line fails
the measurement and the whole run. Setup and readback/oracle work remain outside the interval.
Earlier actions and their verdicts remain in their original order.

**Depends on:** C's confirming route and landing contract.

**Build sequence:** A → B → C → D, following the exposed contracts.
Within C, renderer arguments and route wiring share the declared page-value contract.
The newly rendered Delete task form and the three full-page form/absence assertions released by
Gap 12 have no green point between them: one admits the control while the others prohibit it.
The timed deletion and the whole-run timer-reading expectations have no green point between them:
the additional readings otherwise exhaust or misalign the supplied timer stream.
These are atomic-landing edges within C and D respectively.

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — domain deletion | None |
| B — save and publish | None |
| C — deletion request and pages | Reuse the action-neutral `confirm_strip` with plain text and two `StripForm` values; route outcomes through `_address` and `_guarded`. Resolve one presentation outcome before building page regions so only its focus target survives. |
| D — timed harness | Use an isolated fixture and an independent expected full state. Place fixture setup and state readback outside the two request intervals; extend both whole-run timer sources and rejection probes. |

No write outside the instance/product worktree is part of this design.

## 5. Test Additions

The following rows name the test delta, not a replacement test strategy.
An Example number is its row order in the spec's Examples table.
New test modules must name their SRS requirements/acceptance criteria (CP-545).

| Row / sub-job | Test file | What to add / modify |
|---|---|---|
| T1 / A | `tests/unit/test_tasks.py` | Delete a task in each status, with zero and multiple comments. Assert a new state, original input unchanged, removed task returned exactly, survivor order/values unchanged, both counters unchanged, and missing identity raises `TaskNotFound`. Covers CP-529, CP-533, CP-539 and the rule's refusal edge. |
| T2 / B | `tests/integration/test_task_tracker.py` | Accepted deletion calls the saver once with the complete new state before publishing; the returned title/project come from the current task after an intervening edit. Missing target calls no saver. A failing saver leaves every application read on the old state. CP-533, CP-534, CP-536. |
| T3 / A+B | `tests/integration/test_saved_data.py` | With real files, delete the highest identity and read back no task/comments, all other state unchanged. Build a new Tracker from that saved data, add a task and assert an identity above every issued identity; also cover deletion of the last task and reload of an empty task collection. CP-539, CP-542; Example 13. |
| T4 / C | `tests/integration/test_delete_pages.py` (new) | Every status shows a separate task-level delete form; lists show none. First press is 303 then the in-place strip, sentence/confirm/back-out order, sentence as sole autofocus, current title, no save. Back out restores the trigger/focus without a line or save. CP-529–CP-532; Examples 1, 2, 5. |
| T5 / C | `tests/e2e/test_delete_task.py` (new) | Keyboard-only opening, sentence focus, two Tabs to confirm then Back out, keyboard activation and restored trigger focus. Actual double click never deletes; cover short and scrolled task pages. Confirm by keyboard and check project heading focus. Reload the completion, navigate away and use actual Back/Forward: the same completion line persists and saved bytes do not change. CP-531, CP-532, CP-534; Examples 2–6. |
| T6 / C | `tests/integration/test_delete_routes.py` (new) | Confirm deletes task plus comments, preserves all other state and both counters, redirects to the owning project unfiltered/unsorted with one line. Check project-start focus, reload and Back/Forward completion addresses without additional saves, and the last-task empty invitation. Use real saved bytes for delta assertions. CP-533, CP-534, CP-537; Examples 6–8. |
| T7 / C | `tests/integration/test_delete_routes.py` (new) | After deletion, read both lists, filtered/sorted variants and every Summary count. Include overdue and undated targets, all statuses/priorities, listed/unlisted/unassigned targets, other tasks/projects retained and zero counts after the last task. Assert no stale membership/counts or mutation by reads. CP-537; Examples 8, 11. |
| T8 / C | `tests/integration/test_delete_routes.py` (new); `tests/e2e/test_delete_task.py` (new) | Titles containing `<`, `&`, `"`, quotes and non-ASCII text round-trip through the completion address and appear as text in sentence/completion, never elements. Failure title is escaped too. CP-535; Example 9. |
| T9 / C | `tests/integration/test_delete_routes.py` (new) | Fail a real-file saver before replacement on confirm. Assert saved bytes, current state and all task/comment values displayed by reads unchanged; console names task deletion and error; redirect has failure code only; failed page focuses Delete task with one failure line, no completion and no exception/traceback. CP-536; Example 10. |
| T10 / C | `tests/integration/test_delete_routes.py` (new) | Separate layer-3 case per submission after genuine confirmed deletion: edit, label add, label remove, comment add, ordinary move, cancellation first press, cancellation confirm, delete first press, delete confirm. Each asserts 303 to the target task, then 404 with the existing heading, zero further saves and byte-for-byte saved data unchanged. Ordinary move covers each permitted target word from the former status. Include both repeated deletion and stale-tab sends. CP-540, CP-541; Example 14. |
| T11 / C | `tests/integration/test_delete_routes.py` (new) | Deleted-task GET is 404 with no `no-store` for no query, move confirmation, delete confirmation/back-out/failure and mixed/unknown queries. Existence wins over presentation. Assert the four live deletion landing modes are 200 with `no-store`, neither new POST bypasses origin checks, and no deletion response clears site data. Keep move-only response tests unchanged. CP-538; Example 12; HTTP choice below. |
| T12 / C | `tests/integration/test_delete_pages.py` (new) | Conflicting address presentation: deletion failure wins over confirmation/back-out; active deletion wins over move/comment/label/edit with exactly one focus and line. No deletion state leaves the existing precedence intact. Project completion wins over other outcome markers. Covers the conservative precedence decision below. |
| T13 / C | `tests/integration/test_task_pages.py`; `tests/integration/test_comment_pages.py` | Change only Gap 12's three named tests: include the separate delete form and stop prohibiting the word delete on the whole task page. Continue proving edit fields, existing forms and their order, no overdue, and no controls inside comment items, reply or edit-comment text. Their former no-task-delete clause is intentionally gone; T4 proves its replacement. |
| T14 / C | `tests/integration/test_routes.py` | Extend route samples and bodies for both new POSTs. Replace the universal one-save assertion with explicit expected save counts: delete first press 0, confirming deletion 1, every prior sample still 1. All POSTs retain 303; all reads retain unchanged state and response-policy/no-cookie assertions. Check first press's landing separately as a 200 pending delete view. Drive both delete presses and project landing inside the outbound audit window. CP-544; Example 16. |
| T15 / D | `tests/integration/test_timed_run.py`; `tests/timed_run.py` | Add the full-volume delete and append its block after Summary. Extend `_run_readings` and every fixed whole-run stream. Keep old block ordering, thresholds and verdicts; the old assertion that Summary is last is replaced by Summary-before-deletion. Prove under-limit success, each interval and total at/over limit failure, same-origin marking, setup/readback outside timing, exact-state comparison and all failure paths in D. Mutation probes must reject no deletion, comments retained, another task/field/counter changed, wrong title/project, missing completion and refused/failed actions. CP-543; Example 15. |
| T16 / A–D | `tests/architecture/test_trace.py`; touched/new modules' opening docstrings | Keep the pointer test passing. Update the Tasks entry docstring to include FR-17 and this change's collaborating source/test modules. New tests name FR-15, FR-17, FR-39, NFR-3, AC-12 and other SRS criteria they actually prove. No new feature word or architectural scanner is needed. CP-545; Example 17. |

**Rule-edge pass:** CP-529's final statuses and absence on rows → T1/T4;
CP-530's current title/no-save → T2/T4; CP-531's focus/keyboard/double press → T5;
CP-532's back-out/no-line → T4/T5; CP-533's empty comments/other state/counters → T1/T3/T6;
CP-534's last task, completion history and different-page focus → T5/T6;
CP-535's escaping → T8; CP-536's failed save → T2/T9;
CP-537's empty/filtered/sorted/count cases → T7; CP-538's query variants → T11;
CP-539's highest/last identity and restart → T3; CP-540–CP-541's complete submission domain → T10;
CP-542's real-file cascade → T3; CP-543's false success and exact one-second boundary → T15;
CP-544's route/security/outbound coverage → T14; CP-545's trace → T16.

Only the clauses named in T13–T15 are retired. No other existing assertion is released.

## Records this change makes false

None — reviewed `docs/adr/README.md` and ADR-0001–ADR-0011 (ADR-0006 is superseded),
`docs/nfdr.md` §§ 1–10 and RN-33, `docs/fdr.md` Rules/Product decisions/Out of scope,
and `docs/SDD.md` § 3 plus § 4 RT-11. The deletion fits the existing parts, data shape,
identity rule and behavioural contract. RT-11's delegation of the delete-cache choice is settled
below without changing its move-only rule.

## Architect Review Notes

- **Construction of removal (b), Architect, 2026-10-28:** remove the task as a whole from the state,
  with comments nested in it, and preserve both counters explicitly. This realizes CP-533/CP-539
  without a separate cascade or identity recomputation (`domain/tasks.py:L68-L81`, `Task`;
  `domain/state.py:L18-L33`, `TrackerState`; ADR-0008 § Decision).
- **Current success metadata (b), Architect, 2026-10-28:** return the removed task through A/B.
  Build the landing from that returned value only after saving. This realizes CP-534's title at
  execution rather than the earlier page's title, and retains metadata after removal.
- **First press is POST (b), Architect, 2026-10-28:** use the same submission/redirect shape as
  cancellation, with no save on the first press. This settles Gap 12's delegated choice and follows
  ADR-0011 § Decision. The broader statement that every submission saves once is released only for
  this first-press sample, as T14 states; the first-press control is never the confirming endpoint.
- **Control placement and measurement order (b), Architect, 2026-10-28:** put the delete area
  after the task content, outside comments and all other forms, to preserve the existing controls'
  relative order. Append the timed deletion after Summary so every earlier timing block keeps
  its order. These choices settle positions the spec leaves implicit.
- **Query collisions (b), Architect, 2026-10-28:** use the explicit precedence in C. A plain address
  has only its requested mode, but mixed markers must still produce one focus target. Deletion
  does not alter existing precedence when no deletion marker is recognized.
- **HTTP cache choice (b), Architect, 2026-10-28:** keep deletion's live interaction/outcome pages
  200 with `no-store`, and keep missing-task 404 answers without it. CP-539 permanently retires an
  issued identity, so retaining that deleted identity's 404 cannot hide a later replacement.
  Do not extend the move-only 202 decision of ADR-0010 § Decision and NFDR QC-63 to deletion.
  The spec's Out of Scope and Locked Answer Gap 6 release pending-delete history restoration;
  `no-store` here is not a history guarantee (SDD § 4 RT-11). No spec line is set aside.
- **QC-5/8/12/20/21/23/27/36/38/41/46/60 review — pass for this blueprint:** the parts table places
  every new rule and presentation decision. No new part, refusal, cookie/session, saved field,
  secret or dependency is introduced. The domain has no UI wording; application only orchestrates
  the existing save; web maps `TaskNotFound` by type through application, uses the one escape
  function and retains the one failure site (`web/routes.py:L1041-L1067`). The persistence-format,
  saving-contract and composition-root review triggers QC-22/24/25/26 are untouched. The chosen
  mechanisms need no language feature beyond the product's Python 3.11 floor; this is a design
  review, not a claim that the suite was run under 3.11.
- **Language resolution:** Python, step 1, the project's `Languages:` field;
  `<CORE>/doctrine/engineering/languages/python/README.md` opened.
- **QC-40 review, Architect, 2026-10-28 — pass under the existing browser exception:** a read of
  each of the 15 exact versions in `tests/requirements.txt` through
  `https://pypi.org/pypi/<name>/<version>/json` returned `vulnerabilities: []` for every package.
  This is the published PyPI metadata check, not a claim that no vulnerability exists.
  The versioned endpoints are listed below. Google's
  [2026-09-08 release notice](https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0808145027.html)
  lists critical fixes in 153.0.8010.36/.37, beyond the pinned test build 153.0.8010.12.
  NFDR RN-33 explicitly permits that exact build through 2026-11-07; this review is on 2026-10-28.
  No exception is renewed or pin moved by this design.

  PyPI endpoints checked: [ast_serialize 0.12.1](https://pypi.org/pypi/ast_serialize/0.12.1/json),
  [greenlet 3.5.6](https://pypi.org/pypi/greenlet/3.5.6/json),
  [iniconfig 2.3.1](https://pypi.org/pypi/iniconfig/2.3.1/json),
  [librt 0.16.0](https://pypi.org/pypi/librt/0.16.0/json),
  [mypy 2.4.0](https://pypi.org/pypi/mypy/2.4.0/json),
  [mypy_extensions 1.1.0](https://pypi.org/pypi/mypy_extensions/1.1.0/json),
  [packaging 26.3](https://pypi.org/pypi/packaging/26.3/json),
  [pathspec 1.1.1](https://pypi.org/pypi/pathspec/1.1.1/json),
  [playwright 1.63.0](https://pypi.org/pypi/playwright/1.63.0/json),
  [pluggy 1.6.0](https://pypi.org/pypi/pluggy/1.6.0/json),
  [pyee 13.0.1](https://pypi.org/pypi/pyee/13.0.1/json),
  [Pygments 2.21.0](https://pypi.org/pypi/Pygments/2.21.0/json),
  [pytest 9.1.1](https://pypi.org/pypi/pytest/9.1.1/json),
  [ruff 0.16.10](https://pypi.org/pypi/ruff/0.16.10/json), and
  [typing_extensions 4.16.0](https://pypi.org/pypi/typing_extensions/4.16.0/json).
