# Change Design — Edit a task's four fields from its page

**Date:** 2026-10-12
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the task page's field labels and Save button, project label, left-the-list assignee notice, saved-change completion line, refusal reasons and reload link, failed-save message, and the console's failed-edit action message

This blueprint owns the edit's module boundaries, interfaces, build dependencies and test delta. Its behavioural input is `change_spec.md` in `tracker17 · tobiishi · 2026-10-11_edit-task-fields`; CP identifiers below name that spec's Rules. The artifact belongs beside that spec under the per-project change arc, per `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2, “Holds the change arc” (L2097-L2101).

Paths below beginning `domain/`, `application/`, `web/` or `tests/` are relative to `products/tracker17/`. Design decisions are the architect's, 2026-10-12; § Architect Review Notes gives their reasons.

---

## 1. Change Summary

Add an immutable domain edit operation, an application action that saves its result, and a task-page form posting to the task's own address. The domain compares submitted fields with the values the form originally showed and applies only that change set to the current task. The form and refusal/failure redirect carry both sets of values, so a retry retains the original comparison baseline. This realizes CP-151, CP-152 and CP-166 by construction (`change_spec.md:L37-L39,L55-L55`). The project name is plain text, without a link, under CP-149's delegated choice (`change_spec.md:L32-L32`).

The edit leaves the task entity and saved schema intact, under CP-170 and CP-171 (`change_spec.md:L62-L63`). The existing parsers and title check supply the value rules (`products/tracker17/domain/tasks.py:L85-L89`; `products/tracker17/domain/priorities.py:L36-L41`; `products/tracker17/domain/due_dates.py:L27-L41`). Add and restore keep their existing contracts; editing does not acquire creation defaults.

## 2. Blast Radius

Placement follows `products/tracker17/docs/SDD.md` § 3, “The parts” (L194-L204), and imports follow `products/tracker17/docs/nfdr.md` § 1.2 (L129-L150).

| Module | Status | What changes |
|---|---|---|
| `domain/` | Modified | The **domain part** owns exact changed-field comparison, validation order, membership checks against current People, atomic immutable replacement, the no-change result, and missing-task refusal. `tasks.py` holds the edit values, result and task-edit context; `refusals.py` adds `TaskNotFound`; `__init__.py` re-exports the new public contract. The context also computes selectable assignees and whether the current assignee has left the list, so neither outer part owns this rule. CP-151–CP-165, CP-167, CP-172 (`change_spec.md:L37-L56,L67-L68`). |
| `application/` | Modified | The **application part** adds `Tracker.edit_task` and `Tracker.task_edit_context`, delegates both to domain, and saves/publishes only an outcome domain marks changed. `__init__.py` hands web the edit values, context, outcome and refusal types. CP-157, CP-168, CP-172 (`change_spec.md:L43-L45,L57-L57,L67-L68`). |
| `web/` | Modified | The **web part** owns the POST route, presence-preserving field extraction and newline normalization, the form and hidden shown values, typed outcome-to-address mapping, retry reconstruction, escaping and focus. `routes.py` and `pages.py` change; `style.css` may reuse or extend form/reason/failure styling. `listener.py` and the package export remain unchanged. CP-144–CP-150, CP-155–CP-156, CP-161–CP-169 (`change_spec.md:L27-L33,L41-L57`). |
| `persistence/` | Unchanged | The edit passes the same immutable state and entity shapes to the existing whole-state saver. No constructor signature, schema or saving protocol changes. CP-170 (`change_spec.md:L62-L62`; existing boundary: `products/tracker17/docs/SDD.md:L223-L224`). |
| `main.py` | Unchanged | No new collaborator, clock or wiring is required; the same Tracker and Site serve the edit. Existing wiring ownership: `products/tracker17/docs/SDD.md` § 3, `main` row (L204-L204). |
| `errors.py` | Unchanged | `TaskNotFound` derives from the existing domain `Refusal`, which already derives from `AppError` (`products/tracker17/domain/refusals.py:L12-L24`). |
| `tests/` | Modified | Extend the feature's unit, application, page, route and browser tests; extend every-action checks and the timed harness. CP-173 and CP-175–CP-181 (`change_spec.md:L68-L83`). |

Transitive impact is bounded by additive domain/application exports: persistence keeps its constructor imports and main keeps its wiring. The changed task-page renderer's callers in `web/routes.py` and page tests are included in C and D below; its existing signature is `task_page(task, *, added=False)` (`products/tracker17/web/pages.py:L470-L493`; caller: `products/tracker17/web/routes.py:L196-L201`; direct tests: `products/tracker17/tests/integration/test_task_pages.py:L284-L305`). No import edge needs permission beyond NFDR § 1.2.

## 3. Sub-jobs

The two web sub-jobs sit below the `web` part: page rendering consumes a new context and outcome carrier, and routing supplies them while exposing the POST action. Their shared renderer signature has an atomic-landing edge. This cut preserves each file's boundary; the decision is recorded in § Architect Review Notes.

### A — `domain/`: edit rule and task-edit context

**Scope:** `domain/tasks.py`, `domain/refusals.py`, and domain public re-exports. Extend the tasks entry docstring with FR-16 and the participating modules/tests under CP-173 (`change_spec.md:L68-L68`).

**Exposes:**

| Contract | Meaning |
|---|---|
| `TaskFields` | Frozen value with `title`, `priority`, `assignee`, `due_date`, each a string or `None`. `None` means the field is absent; empty string means a carried empty value. It is used separately for submitted and shown values. |
| `TaskEditOutcome` | Frozen value holding the resulting `Task` and a `changed` boolean. The boolean answers whether any supplied pair differed, even if the submitted value equals the task's current saved value. |
| `edit_task(state, task_id, submitted, shown)` | Returns the resulting `TrackerState` and `TaskEditOutcome`, or raises a typed refusal. Both field sets contain normalized plain strings, not request objects. |
| `TaskEditContext` | Frozen value holding the current `Task`, its `Project`, all four saved field strings, ordered assignee choices, and an `assignee_unlisted` boolean. Saved unassigned/undated values are empty strings; saved priority is its word and due date its ISO calendar date. |
| `task_edit_context(state, task_id)` | Returns the context, or `None` when no task has that identity. Choices are empty string for none, then listed names in their saved order, then the carried unlisted name if present. No name occurs twice. |
| `TaskNotFound` | New domain refusal raised by the edit for a missing task. |

The edit finds the current task before considering a no-change result. A field is eligible only when both its submitted and shown values are present and differ exactly. Validate that set in CP-165's explicit order: title length, title blankness, priority, assignee, due date (`change_spec.md:L37-L39,L54-L56`). A changed empty priority is invalid, rather than creation's medium default; a changed empty assignee or due date clears the field under CP-153 (`change_spec.md:L39-L39`).

Validate every eligible field before returning a replacement state. Replace only those four eligible fields on the current task and preserve its tuple position and every other task/state value, under CP-160 and CP-171 (`change_spec.md:L49-L49,L63-L63`). Do not rebuild the task through `restore_task`: its check of every title and assignee belongs to restoration (`products/tracker17/domain/tasks.py:L143-L175`), whereas CP-158 checks only changed fields (`change_spec.md:L44-L44`). When no field is eligible, return the original state and current task with `changed=false`.

Refusals are `TextTooLong` for title, `BlankTitle`, `InvalidPriority`, `AssigneeNotListed` carrying the rejected name, `InvalidDueDate`, and `TaskNotFound`. The first five already exist (`products/tracker17/domain/refusals.py:L43-L77`); widen `AssigneeNotListed`'s creation-only docstring to cover a changed assignment. Reuse the refusal type because the rejected condition is the same; the edit-specific stale explanation is web's mapping.

**Depends on:** none.

### B — `application/`: action and page values

**Scope:** `application/tracker.py` and application public re-exports.

**Exposes:** `Tracker.edit_task(task_id, submitted, shown)` returns `TaskEditOutcome`; `Tracker.task_edit_context(task_id)` returns `TaskEditContext` or `None`. Web imports those values and all six refusal types through `application`, under NFDR QC-5 and QC-16 (`products/tracker17/docs/nfdr.md:L56-L67,L138-L143`).

The action calls domain once with the current state. When domain marks the outcome changed, save the returned whole state and publish it only after the saver returns; propagate a failure without publishing. When domain reports no change, make no saver call. The action reads no clock, computes no comparison, checks no membership and decides no refusal. The existing save/publish seam is `Tracker._save_then_publish` (`products/tracker17/application/tracker.py:L115-L117`); CP-157 and CP-168 determine the two outcomes (`change_spec.md:L43-L43,L57-L57`). The page query delegates to domain; it does not add an application membership rule.

**Depends on:** A's edit, context, outcome and refusal exports.

### C — `web/pages.py`: task page and edit carrier

**Scope:** the task-page renderer, its page-local form carrier and relevant stylesheet rules.

**Exposes:** `task_page(context, *, form=None, added=False, saved=False)` renders `TaskEditContext`; the context is required. A frozen `TaskEditForm` holds retained `TaskFields`, original shown `TaskFields`, a closed edit refusal code or none, and a failure flag. Keep the add-task `TaskForm` and add-page contract separate.

On a normal page, show context's saved field values and hidden shown values named `shown_title`, `shown_priority`, `shown_assignee`, `shown_due_date`. Submitted visible names remain `title`, `priority`, `assignee`, `due_date`. The single form posts to `/tasks/<id>`; the project name is an escaped, non-editable text fact. Retained refusal/failure values override the visible controls but their original shown values override the hidden controls. The too-long outcome discards the retained carrier entirely and opens from context's saved fields. These are transport decisions implementing CP-145, CP-149 and CP-166 (`change_spec.md:L28-L32,L55-L55`).

Render the four priority words, assignee choices, unlisted notice and native date field under CP-145–CP-148 (`change_spec.md:L28-L31`). In an out-of-date refusal, a rejected assignee may be echoed as the failed selection; that echo is not a new eligible name. Its next submitted change is still checked by domain. Retained invalid strings from a hand-built request remain in the carrier; rendering does not accept, trim or validate them. Use the application-exported title maximum for `maxlength` under CP-146 (`change_spec.md:L29-L29`). Every operator value, including hidden attributes, option values, project name, heading and quoted outcome values, passes through `_escape`, the existing single escape function (`products/tracker17/web/pages.py:L111-L113`).

Blank/too-long title refusals focus the title field; priority, assignee and due-date refusals focus their control. Associate one reason by `aria-describedby`; the reason does not take focus. A failure focuses the edit form, with the failed-save message as its accessible description. A changed successful save focuses the task heading, described by one saved-change line; a no-change save has no completion line. Retain the existing added outcome and its focus behavior, under CP-156 and CP-161–CP-168 (`change_spec.md:L42-L57`; added rendering: `products/tracker17/web/pages.py:L475-L481`). No redirect address has a fragment. Published words are supplied by this change's text record under `products/tracker17/docs/CONTENT.md` § Message patterns, Completed (L290-L301), per the spec's wording boundary (`change_spec.md:L17-L19`).

**Depends on:** B's context, field values, refusal exports and maximum/priority exports.

### D — `web/routes.py`: edit request and outcome addresses

**Scope:** the POST `/tasks/[0-9]+` route, task GET context retrieval, edit-field extraction and typed outcome mapping.

**Exposes:** the route in `ROUTES`, a same-origin POST returning a 303 task-page address, and the GET building C's context/form contract. The existing request gate and request lock enclose the edit (`products/tracker17/web/routes.py:L146-L166`), under CP-169 (`change_spec.md:L58-L58`). Use `_identity` for addresses with too many digits; an identity it cannot read answers the existing task not-found page, under CP-167 (`products/tracker17/web/routes.py:L208-L214`; `change_spec.md:L56-L56`).

Extract both field sets without collapsing absent keys to empty strings; normalize every present value with `_line_feeds`. `_first` currently defaults absent values to empty strings (`products/tracker17/web/routes.py:L105-L107`), so using that default alone would lose CP-151's absent-versus-empty distinction (`change_spec.md:L37-L37`). Routes do not compare either set with the current task.

Map each domain refusal by its type, not message text. Carry edit outcomes separately from add outcomes: `edit_refused`, `edit_failed`, and the successful `saved` flag. For retained refusals/failures, put the present visible and shown values in the redirect query, preserving absence. GET reconstructs both sets only for a recognized retained edit outcome. A too-long redirect carries only the refusal code and task address: no submitted or shown fields. A normal, added, saved or no-change GET reads a fresh context baseline. The missing-task refusal redirects to the task address, whose GET returns the existing task not-found page. These transport decisions realize CP-155–CP-168 with ADR-0006's redirect contract (`change_spec.md:L41-L57`; `products/tracker17/docs/adr/0006-last-action-travels-in-the-page-address.md` § Decision, L19-L24).

Issue the `saved` flag only from a changed outcome returned after saving. A no-change result redirects to the plain task address. Use the existing `_redirect`/`_address` pair for all paths and `_guarded` for unexpected failures, preserving the one console site (`products/tracker17/web/routes.py:L96-L102,L404-L429`). The failure address retains the original baseline as well as entered values; no Python exception text reaches it.

**Depends on:** B's action and C's renderer/carrier.

### E — `tests/timed_run.py`: field-edit measurement

**Scope:** the executable timed harness and `tests/integration/test_timed_run.py`.

**Exposes:** an additional field-edit measurement and its landing-page measurement, reported and judged separately at the existing 1,000-task/20-comment fixture under CP-179 (`change_spec.md:L81-L81`). Keep the existing add and add-landing measurements, whose contract is `measure_task_volume` (`products/tracker17/tests/timed_run.py:L195-L225`).

Load the edit form before timing, submit its shown fields and one changed title through Site with the same-origin header, and fetch the returned address as a separate measurement. Count success only when the redirect is a successful edit and saved data contains exactly the expected field delta; the landing must show the edited title. The fixture's other tasks, comments and counters stay identical. Any refusal, failure, incorrect save, wrong page or duration at least 1 second produces a failed verdict. Declare the edited title's text length in the report.

**Depends on:** D's POST/GET contract.

**Build sequence:** A → B → C → D → E. The ordering follows the domain/application/web import contracts. C defines the renderer contract consumed by D; E needs the served form and completed action.

**Atomic-landing edges:**

- **C + D — no green point between them:** C changes a required renderer argument, while the task GET in D supplies it. The existing GET and direct-renderer tests call the former signature (`products/tracker17/web/routes.py:L196-L201`; `products/tracker17/tests/integration/test_task_pages.py:L284-L305`). The new POST also needs an accepted route sample in the existing every-route test (`products/tracker17/tests/integration/test_routes.py:L273-L306`).

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — domain edit/context | Build the change set from submitted/shown pairs, validate it completely in the explicit refusal order, then replace only those fields on the current immutable task. A changed-to-current value still has a changed outcome. |
| B — application action | None |
| C — task-page rendering | Two separate field sets: visible retained values and hidden original values. The too-long outcome resets both from the current context. Use the single escape function at every text/attribute insertion. |
| D — request/redirect transport | Preserve absent versus present-empty through extraction and URL encoding. Keep both sets on retained outcomes, neither on too-long outcomes; reuse the existing redirect builder and failure boundary. |
| E — timed harness | Measure edit and landing separately; prove the saved field delta and preserved fixture before reporting success. |

## 5. Test Additions

Each row has a local identifier so the coverage walk can name the exact proof. Integration means the real Site, Tracker and domain in one process, with real SavedData for saved-byte assertions; the product's layer mapping is `products/tracker17/docs/nfdr.md` § 9 (L498-L509). Collaborators arrive through existing seams, never by patching a product name, under CP-175 (`change_spec.md:L77-L77`).

| Row | Sub-job | Test file | What to add / modify |
|---|---|---|---|
| T1 | A | `tests/unit/test_tasks.py` | Edit all four fields, each one alone, and each optional clear; exact title spacing; each of the four priorities; valid/leap calendar dates. Original state remains immutable. Compare supplied pairs, including missing submitted or shown value, present-empty and normalized strings. Changed-to-current is still changed. CP-151–CP-154. |
| T2 | A | `tests/unit/test_tasks.py` | No-change returns current task/state; unchanged invalid/unlisted supplied pairs are not validated. Listed/unassigned/unlisted context choices preserve exact names and list order, with no duplicate when the carried name is listed. Unlisted assignee unchanged, replaced with listed/none, and refused when restored while off-list. CP-147–CP-159. |
| T3 | A | `tests/unit/test_tasks.py` | Empty, ASCII and Unicode-whitespace title; 200 accepted versus 201 refused, including 201 spaces; empty/unknown/case-varied priority; unlisted changed assignee; malformed/impossible date. Parametrize competing invalid fields to prove the complete CP-165 precedence, not only blank-title before priority. All refusals leave state unchanged; missing-task refusal wins even with no changed pair. CP-160–CP-165, CP-167. |
| T4 | A, B | `tests/unit/test_tasks.py`; `tests/integration/test_task_tracker.py` | Edit tasks in all four statuses. Preserve identity, project, status, labels, comments, created instant, both counters, other tasks/projects/People and task tuple positions. Current stale-field replacement and untouched-current fields; no edit clock call. CP-144, CP-152, CP-154, CP-170–CP-171. |
| T5 | B | `tests/integration/test_task_tracker.py` | Recording saver sees exactly one whole-state save for a changed outcome, none for a no-change or refusal. A failing saver leaves the in-memory state/current task unchanged. The action passes typed refusals through application exports; only saver calls, no rereads. CP-157, CP-168, CP-177. |
| T6 | C, D | `tests/integration/test_task_pages.py`; `tests/integration/test_task_routes.py` | Opening form for listed, none, empty People, and carried unlisted assignee, in every task status. Exact title and shown hidden values, four priority choices, selected values, empty/native date and domain maximum. Unlisted notice beside the control, absent for listed/none; project plain text; one Save form, no out-of-scope controls, no script; repeated GET leaves saved bytes unchanged. CP-144–CP-150, CP-174. |
| T7 | C, D | `tests/integration/test_task_routes.py` | Four-field save with ` Ship it `, critical/Ari/date; each one-field edit and optional clears. Submit unchanged title plus changed priority, and missing shown/submitted keys including a body with no fields. Compare saved bytes/current task and redirected form. Changed-to-current gets saved completion; no-change gets none and no save. CP-151–CP-157. |
| T8 | C, D | `tests/integration/test_task_routes.py` | Load a real form, submit a second tab's different title, then submit the first form's changed title: accepted overwrite. Repeat with low → high → medium priority. Change only title from a form whose priority another tab changed: that priority survives. Use hidden fields read from the page. CP-152, CP-154. |
| T9 | C, D | `tests/integration/test_task_routes.py` | Remove carried Dana, edit only title and retain Dana; replace with Ari and separately none, verify Dana and notice disappear; then a hand-built changed Dana fails. Load form, remove Ari, submit changed Ari: stale reason and reload link, assignee focus, other three entered values retained, saved bytes unchanged. CP-148, CP-158–CP-159, CP-163. |
| T10 | C, D | `tests/integration/test_task_routes.py`; `tests/integration/test_task_pages.py` | Separate test per blank, too-long, invalid priority, unlisted assignee, invalid date and missing-task refusal. Assert exact supplied content reason and identical before/after saved bytes. Blank plus accepted other edits saves none. For 201 characters and 201 spaces, neither entered nor shown submission text appears in address/page; controls and hidden baseline reset to saved. Multi-invalid requests prove one reason and focus at the first refused field. Also cover nonexistent, zero and oversized-digit task addresses. CP-160–CP-165, CP-167, CP-176. |
| T11 | C, D | `tests/integration/test_task_routes.py` | Refusal retry saves the retained low priority after fixing a blank title. Retry from a refused stale form keeps another tab's newer untouched priority. Repeat baseline carry-over after assignee refusal, invalid-value refusal and disk failure; follow too-long refusal with a save using the new saved baseline. Assert hidden baseline survived redirects, including missing pairs in a hand-built request. CP-166. |
| T12 | C, D | `tests/integration/test_task_routes.py` | Inject saver failure during a multi-field edit: saved bytes and current state unchanged; typed values and original baseline retained; form focused and described; console action then error; neither Python message nor traceback in page/address. Healthy retry succeeds. CP-168. |
| T13 | D | `tests/integration/test_task_routes.py`; `tests/integration/test_routes.py` | Each cross-site, same-site, none, absent or other non-same-origin mark and incorrect Host prevents an edit, without a saver call or changed bytes. Add accepted edit body to the dynamically enumerated route samples: 303, exactly one save, policy header, no cookie. Drive edit in no-outbound-connection and recording-saver action sequences. Keep request-lock serialization coverage; exercise two edits against a held saver. CP-169, CP-177. |
| T14 | B, D | `tests/integration/test_task_routes.py`; `tests/integration/test_saved_data.py` | Read pre-change saved task data without migration. Edit title/due date then reopen from real saved data; assert same JSON keys and protected task fields. List explicitly recomputes due-date/identity order and overdue flag from edited task, including undated and equal-date ties. CP-170–CP-171. |
| T15 | C, D | `tests/integration/test_task_pages.py`; `tests/integration/test_task_routes.py` | Successful edit line names current saved title; one heading-focused accessible description, not focused line. GET/reload/back/forward after edit never saves again; plain/no-change GET has no completion. Preserve added line behavior. Escape markup in title, project, listed/unlisted names, visible/hidden fields and retained outcomes. CP-155–CP-156, CP-175. |
| T16 | C, D | `tests/e2e/test_tasks.py` | Edit title to `<b>A&B</b> "Q"`; task heading, form and project's list/link show exact text. Exercise title maxlength, native date set/clear, keyboard Save, success heading focus/description, blank-refusal field focus. CP-146, CP-156, CP-161, CP-178. |
| T17 | E | `tests/integration/test_timed_run.py`; `tests/timed_run.py` | Report edit and edit-landing at 1,000 tasks with 20 comments each and declared text lengths. An injected timer proves each must be strictly below 1 second. Scripted request-path replies prove refused/failed edit, successful-looking redirect with incorrect/no delta, bad landing or wrong title produce a failed verdict. Retain every add-harness proof. CP-179. |
| T18 | A–E | `tests/architecture/test_trace.py`, existing architecture suite, and suite/gate commands | Run the trace check with FR-16 and every participating module/test in the tasks docstring; keep landed feature words unchanged. Architecture checks cover the new types/exports and unchanged import graph. In a git-archive HEAD copy initialized as a Git repository, both `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` and the timed run exit 0. From product root: Ruff format/check and mypy over main/errors/four packages exit 0; compile changed Python as the packet requires. CP-172–CP-173, CP-175, CP-180–CP-181. |

**Examples pass:** every example in `change_spec.md` maps to these rows: CP-144 → T4/T6; CP-145 → T6; CP-146 → T16; CP-147–CP-150 → T6/T9; CP-151 → T1/T7; CP-152 → T7/T8; CP-153 → T7; CP-154 → T8; CP-155–CP-156 → T15; CP-157 → T5/T7; CP-158–CP-159 → T9; CP-160–CP-162 → T10; CP-163 → T9/T10; CP-164–CP-165 → T10; both CP-166 examples → T11; CP-167 → T10; CP-168 → T12; CP-169 → T13; CP-170–CP-171 → T14; CP-172–CP-173 → T18; CP-174 → T6; CP-175–CP-176 → T1–T12/T18; CP-177 → T5/T13; CP-178 → T16; CP-179 → T17; CP-180–CP-181 → T18 (`change_spec.md:L93-L138`).

**Rules pass:** edges not singled out by an Example are placed too: absent submitted values and present-empty pairs → T1/T7/T11; all statuses including cancelled → T4/T6; no listed People with a carried name → T2/T6; changed-to-current versus no-change → T1/T5/T7; normalization on both field sets and exact spaced/case-sensitive names → T1/T2/T9; every competing-refusal pair → T3/T10; retained baseline after every retaining outcome and reset after too-long → T11/T12; all protected fields and unrelated entities/counters → T4/T14; no read mutation after reload/history → T6/T15; identity too large for the address parser → T10; false-positive timed success and the 1-second boundary → T17 (rules: `change_spec.md:L27-L83`).

**Assertions superseded:** `test_task_page_is_read_only_and_shows_only_four_fields` prohibits forms/inputs/selects/buttons, the word edit and any main-area link (`products/tracker17/tests/integration/test_task_pages.py:L250-L273`). CP-144 replaces the no-form/control clause and CP-149 adds project text; T6 replaces those assertions with exactly the authorized form and no additional controls (`change_spec.md:L27-L33,L184-L184`). Keep its exact title/page-title, saved priority/assignee/date, header navigation, no-status/no-label/no-comment/no-overdue and no-script/table proofs; T6/T15 re-prove the changed renderer call sites. No other assertion is retired or weakened. The added-outcome browser test and direct escape tests keep their existing assertions with context-aware fixtures (`products/tracker17/tests/e2e/test_tasks.py:L58-L83`; `products/tracker17/tests/integration/test_task_pages.py:L284-L305`).

## Records this change makes false

- `products/tracker17/docs/SDD.md` § 3, application row (L201-L201), says each action saves the new state, and `products/tracker17/docs/nfdr.md` § 1.3 QC-21 (L167-L174) says the same. The no-change edit skips saving to realize CP-157, so the unconditional wording becomes false. Correction: a state-changing action saves before publishing; an edit whose domain outcome marks no changed field returns the current task without a save or publication. The no-change branch is an action result, not an application rule (`change_spec.md:L43-L44`).
- `products/tracker17/docs/adr/0001-rule-core-behind-server-rendered-pages.md` § Decision, application bullet (L26-L28), also says each action saves its result. The same no-change qualification is owed. Keep the Accepted record append-only; a clarification beside QC-21 should explain that the save-before-publication decision applies when a domain operation reports a change. No new part or import edge is proposed.
- No other foundation sentence changes on this reading of the design: ADR-0001–ADR-0009, the ADR index, FDR, NFDR and SDD § 3 have been read. In particular ADR-0004's “on every change” still holds because the no-change edit changes nothing (`products/tracker17/docs/adr/0004-whole-state-saved-atomically-on-every-change.md` § Decision, L18-L24). The saved shape and import graph remain the recorded ones. The foundation records are not edited by this artifact.

## Architect Review Notes

### Language resolution

Python — resolution step 1, the project card's `Languages:` (`system/projects/tracker17/project.md:L12-L12`). Opened `<CORE>/doctrine/engineering/languages/python/README.md` and its five routed files plus `testing_python.md`; the product's locked records govern this design.

### Design decisions — architect, 2026-10-12

- **(b) Comparison by construction:** use distinct optional-string field values and a domain-owned outcome flag. The flag means a submitted/shown difference, not state inequality, so a stale form setting a field to its current saved value still follows CP-155's changed-save path. Original shown values travel through every retaining redirect; too-long resets them. This locks the mechanism CP-151 and CP-166 leave open (`change_spec.md:L37-L41,L55-L55`).
- **Delegated project-link choice:** show the project name as plain text without a link. CP-149 and Locked Answers Gap 6 explicitly leave the link to this stage; text meets the contract and adds no navigation contract (`change_spec.md:L32-L32,L180-L180`).
- **(b) Ordered assignee choices:** the domain context appends a carried unlisted name after none and the listed names. This keeps list order exact, introduces no duplicate, and supplies the notice flag as data. A failed submitted name is only an echo in a refused form, never permission to assign it. This fixes the presentation ordering not specified by CP-148 while preserving CP-147 and CP-163 (`change_spec.md:L30-L31,L52-L52`).
- **(d) Web cut below the part:** C and D are separate because the renderer's required context is D's dependency and there is no green point between their signature/caller changes. The cut states an interface and an atomic-landing property, not task or commit instructions (`products/tracker17/web/pages.py:L470-L493`; `products/tracker17/web/routes.py:L196-L201`).
- **(a) No-change orchestration wording:** CP-157/FDR R-116's no-change result controls the edit; narrow SDD § 3's and QC-21's unconditional saving language and record ADR-0001's matching qualification through the correction listed above. The domain decides whether a field changed and the application only follows that outcome (`change_spec.md:L43-L44`; `products/tracker17/docs/fdr.md:L164-L171`).

### Delegated record reviews

The sweep was `rg -n 'development-design' products/tracker17/docs/nfdr.md products/tracker17/docs/adr/`; it returned the NFDR gates recorded here and no ADR-specific stage gate. Verdicts below assess the design contracts, not implementation or a suite run.

| Gate | Verdict and grounds |
|---|---|
| QC-5 — by-type refusal mapping; application defines no refusal | **Pass.** A defines TaskNotFound and reuses five domain refusal types; B re-exports them; D handles them by type, with edit-specific outward codes. No exception-message branch. Gate source: `products/tracker17/docs/nfdr.md:L56-L67`. |
| QC-8 — web keeps no request state | **Pass.** Both field sets and last outcomes are request/form/query values, not a cache, cookie, session or module-level mutable store. Gate source: `products/tracker17/docs/nfdr.md:L79-L84`. |
| QC-12 — every part pays for a requirement | **Pass.** No top-level part or production file is added; A's three immutable values carry the comparison, page context and outcome required across the existing seams. Gate source: `products/tracker17/docs/nfdr.md:L115-L120`. |
| QC-20, QC-21, QC-23 — domain wording, application rules, web rules | **Pass, with the QC-21 wording correction listed above.** A holds comparison, validation, membership and choice computations without published words. B only queries/applies/saves/publishes. C/D transport values and render typed outcomes; web performs no changed-field or membership decision. Gate sources: `products/tracker17/docs/nfdr.md:L160-L174,L182-L186`. |
| QC-27 — browser interface replaceable | **Pass.** No request/HTML/address object crosses B; the saver and clock contracts do not change. Gate source: `products/tracker17/docs/nfdr.md:L203-L208`. |
| QC-36 — one escape function | **Pass.** C routes each operator value through the existing `_escape`, including both field carriers, attributes and outcome text. Gate/source: `products/tracker17/docs/nfdr.md:L268-L275`; `products/tracker17/web/pages.py:L111-L113`. |
| QC-41 — no secret introduced | **Pass.** No credential, account, new saved fact or external service belongs to A–E. Gate source: `products/tracker17/docs/nfdr.md:L320-L324`. |
| QC-60 — Python 3.11 surface | **Pass at design review.** A–E reuse the existing frozen dataclass, replacement, enum, date-parser and URL-encoding approaches; no new language/library requirement or pin is introduced. The floor is `products/tracker17/pyproject.toml:L1-L4`; the gate's separate unverified-runtime limitation remains `products/tracker17/docs/nfdr.md:L462-L467`. |
| QC-22, QC-24–QC-26, QC-46 | **Not triggered.** No persistence or main source, saving contract, file format or saved field changes. Their triggers are `products/tracker17/docs/nfdr.md:L175-L202,L379-L383`. |

### QC-40 dependency and browser review — 2026-10-12

The fixed test set is `products/tracker17/tests/requirements.txt:L4-L18`; this design adds no dependency and moves no pin. The repository-feed check `gh api --paginate repos/<instance-repo>/dependabot/alerts …` executed and returned HTTP 403, “Dependabot alerts are disabled for this repository.” The ongoing feed named by QC-40 is therefore unavailable at this review (`products/tracker17/docs/nfdr.md:L301-L317`). Do not treat that refusal as an empty alert set.

The alternative published-advisory check executed on 2026-10-12:

```sh
gh api --method GET --paginate advisories \
  -f ecosystem=pip -f severity=critical -f is_withdrawn=false \
  -f affects='ast_serialize@0.12.1,greenlet@3.5.6,iniconfig@2.3.1,librt@0.16.0,mypy@2.4.0,mypy_extensions@1.1.0,packaging@26.3,pathspec@1.1.1,playwright@1.63.0,pluggy@1.6.0,pyee@13.0.1,Pygments@2.21.0,pytest@9.1.1,ruff@0.16.10,typing_extensions@4.16.0' \
  --jq '[.[] | {id: .ghsa_id, severity, published_at, packages: .vulnerabilities}]'
```

It exited 0 with `[]`: no matching non-withdrawn critical GitHub-reviewed advisory in that query. This is a dated query result, not a guarantee of no vulnerability or an enabled ongoing feed; the endpoint's filtering contract is https://docs.github.com/en/rest/security-advisories/global-advisories?apiVersion=2022-11-28.

The installed browser's `CFBundleShortVersionString` is `153.0.8010.12` (command: Python `plistlib.loads(Path('~/Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/Info.plist').read_bytes())['CFBundleShortVersionString']`; actual output: `153.0.8010.12`). Google's 2026-09-15 release publishes critical fixes in `153.0.8010.47/.48` for CVE-2026-91726, CVE-2026-91721 and CVE-2026-91749 (https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0541751186.html). Google's 2026-10-01 release publishes a critical WebGL fix in `154.0.8037.97/.98` (https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop.html). On that comparison, the installed build is behind these critical fixes.

**QC-40 verdict: pass under the existing dated browser exception, with the repository-feed limitation recorded.** NFDR RN-33 names precisely `153.0.8010.12` and explicitly permits development-design reviews through 2026-11-07 (`products/tracker17/docs/nfdr.md:L968-L976`, “The exception names the build, not the advisories”). The review does not extend that date, move a pin or enable a repository setting.
