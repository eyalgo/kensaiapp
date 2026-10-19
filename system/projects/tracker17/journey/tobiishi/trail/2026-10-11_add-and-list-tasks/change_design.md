# Change Design — Add a task and read the project's ordered list

**Date:** 2026-10-11
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the project's add-task form, first-task invitation, list headings and empty cells, overdue marking, add refusals and failure message; the task's page and completion line; the missing-task page; the console message for a failed add

---

## 1. Change Summary

Design for `tracker17 · tobiishi · 2026-10-11_add-and-list-tasks`, governed by adjacent `change_spec.md` § Rules (CP-106–CP-143, lines 26–87). Extend the immutable state with tasks and their counter, save that state through the existing whole-state contract, and expose task creation and read-back through application. Web gains a project form/list and a read-only task page. Validation, defaults, identity issuance, ordering and overdue decisions belong to domain; the parts table assigns those responsibilities there (`products/tracker17/docs/SDD.md` § 3, lines 200–204).

All choices labelled **Decision** below are this architect's decisions on 2026-10-11, within the choices left by the spec. Interface names describe the contract to implement; they are not claims that symbols already exist. Wording is supplied by this change's content artifact under `products/tracker17/docs/CONTENT.md`, as the spec requires (`change_spec.md` § Change Summary, lines 18–18).

---

## 2. Blast Radius

The owning parts and dependence direction are `products/tracker17/docs/SDD.md` § 3, lines 200–231; the module set and forbidden imports are `products/tracker17/docs/nfdr.md` § 1.2, QC-13–QC-19, lines 129–153. The following is the proposed delta against those boundaries.

| Module | Status | What changes / owning part |
|---|---|---|
| `domain/` | Modified | **Domain:** immutable Task and comment value shape, task counter, shared title bound, typed refusals, creation/defaults, restored-task validation, project-scoped due ordering, overdue predicate. Extend `state.py`, `refusals.py` and export-only `__init__.py`; add **new** `tasks.py`, `priorities.py`, `due_dates.py` (CP-135, CP-138). Existing project/assignee operations must retain tasks/counter when replacing state. No labels feature module. |
| `application/` | Modified | **Application:** `tracker.py` applies creation to current state, saves before publishing, returns saved task; prepares ordered task rows and supplies local today through the existing Clock. Re-export task values, choices and typed refusals through `__init__.py`; keep Saver and Clock protocols unchanged. |
| `persistence/` | Modified | **Persistence:** `saved_data.py` adds the task/counter representation, recognizes both older key sets, decodes the shape and calls domain restoration. Keep whole-file atomic replacement, unreadable-data handling and single-tracker lock. |
| `web/` | Modified | **Web:** `routes.py` adds POST creation, GET task lookup and missing-task dispatch, stateless redirected outcomes; `pages.py` renders form, list, task and missing-task pages, accessible focus/reasons, escaped values; extend the existing stylesheet as needed. Listener and public Site entry signature remain unchanged. |
| `main.py` | Unchanged | Existing Clock, Saver and Site wiring suffices; no new constructor argument or format knowledge. |
| `errors.py` | Unchanged | Existing common failure base suffices; domain owns new refusal types. |
| `tests/` | Modified | Contract tests, whole-path tests, browser escaping, trace registration, route-wide probes and timed-run volume; detailed rows in § 5. No product import from tests. |

Transitive impact is contained in application and persistence consuming domain, and web consuming application. Main receives no changed construction contract; errors receives no dependency. These are the permitted edges, not a new import exception (`products/tracker17/docs/nfdr.md` § 1.2, lines 129–153). No new responsibility lacks an owning part.

---

## 3. Sub-jobs

### A — `domain/`

**Scope:** task state and pure rules only (CP-111–CP-113, CP-116–CP-121, CP-130–CP-131, CP-135–CP-138; `change_spec.md` § Rules, lines 34–76).

**Exposes — Decision: immutable values and pure contracts.**

- `Task` has `id`, `project_id`, `title`, `status`, `priority`, `assignee`, `labels`, `due_date`, `created_at`, `comments`. Identity/project identity are positive integers; title/assignee are exact strings; unassigned and undated are `None`; labels and comments are immutable ordered tuples; due date is a calendar `date`; creation time is an aware UTC instant. `Comment` is a value with `text`, `author`, `created_at`, held inside Task. These fields realize the existing entity shapes (`products/tracker17/docs/SDD.md` § 3, lines 240–254).
- `TaskStatus` exposes `todo`, `in-progress`, `done`, `cancelled` in `tasks.py`; `Priority` exposes `low`, `medium`, `high`, `critical` in `priorities.py`. Both are string-valued enums. `PRIORITY_CHOICES` is the immutable tuple of those four plain strings in that order. `TrackerState` adds `tasks=()` and `next_task_id=1` after its existing fields. Existing positional construction and restoration remain accepted; the present parameters are projects, project counter and optional assignees (`products/tracker17/domain/state.py:L20-L34`).
- `add_task(state, project_id, title, priority, assignee, due_date, created_at)` returns the new state and Task, or a typed refusal, without I/O. Priority, assignee and due date enter as form strings, with absent values passed as empty strings. Domain alone applies medium/unassigned/undated defaults and todo, checks the current project/list, issues the saved task counter, and creates empty labels/comments. The original state is never changed (CP-111–CP-113, CP-116; `change_spec.md:L34-L39`).
- `restore_task(id, project_id, title, status, priority, assignee, labels, due_date, created_at, comments)` returns a Task or a typed refusal. Status/priority arrive as strings; due date arrives as `None` or its calendar-date string; instants arrive as decoded aware UTC datetimes. Domain validates title, enum values, optional assignee and calendar date through the same value checks used by creation. Unlike form defaults, a saved empty/unknown priority or a saved empty due-date string is invalid. Restoration permits an assignee absent from the current People list (CP-137; `change_spec.md:L72-L72`).
- `restore_state` retains its first three parameters and gains keyword-only `tasks=()` and `next_task_id=1`. It accepts restored Task values, checks positive task identities/counter, project references, duplicate identities and every identity below the counter, and returns all state or refuses it all. Comment/label containers carry their structural values without adding their deferred semantic rules (`change_spec.md` § What is saved, lines 70–72).
- `find_task(state, task_id)` returns Task or `None`. `list_project_tasks(state, project_id)` returns all tasks for that project, explicitly sorted by dated before undated, ascending calendar date, then ascending task identity. Identity is the recorded creation-order field, independently of time (`products/tracker17/docs/SDD.md:L242-L245`); tuple insertion order is not the contract.
- `due_dates.py` exposes calendar-date validation and `is_overdue(due_date, status, today)`, returning a boolean, with all arguments supplied. It owns the before-today/status/no-date rule; it reads no clock (CP-131; `change_spec.md:L63-L63`). Date validation requires exactly a valid `YYYY-MM-DD` calendar date, rather than a week date, timestamp or compact form.
- New refusals are `BlankTitle`, `ProjectNotFound`, `AssigneeNotListed` carrying the submitted name, `InvalidPriority`, `InvalidDueDate`, `InvalidTaskStatus`. Add `TextField.TITLE` to the shared `TextTooLong` contract. Reuse `IdentityReused` for invalid task identity reuse. Refusals carry structured facts, never operator wording; their ownership/re-export seam is NFDR QC-5 (`products/tracker17/docs/nfdr.md:L56-L67`).

**Decision: refusal precedence.** Check project existence, title length, title blankness, priority, current assignee membership, then due date. Thus 201 spaces receives the mandated too-long reason, and every unknown project receives not-found. The spec requires those two results but does not order mixed invalid fields (`change_spec.md:L44-L47`). A refused add consumes no identity.

**Depends on:** none. Domain takes created instant and today as values, using no application or persistence contract.

### B — `persistence/`

**Scope:** additive saved-file representation and compatibility, using A's restoration contracts (CP-134–CP-137; `change_spec.md:L69-L72`).

**Exposes — Decision: one full saved shape.** Keep the existing project and assignee encoding; add `next_task_id` and `tasks` to the current top-level keys. Every save writes exactly `next_project_id`, `projects`, `assignees`, `next_task_id`, `tasks`. A task object has exactly A's ten field names; enums are strings, absent assignee/due date are JSON null, labels/comments are arrays, due date is `YYYY-MM-DD`, and `created_at` is an ISO-8601 UTC instant. A comment object has exactly `text`, `author`, `created_at`. The People list remains an ordered array of exact names (CP-136; `change_spec.md:L71-L71`).

Read exactly three supported top-level key sets: legacy projects/counter; projects/counter/assignees; the new full five-key form. Missing tasks in either older form restore to no tasks and counter 1; missing assignees in the oldest restore to no names. Reading never saves or rewrites. A partial new task form, missing/extra fields, wrong primitive/container types (including boolean identities), or undecodable instants are unreadable shape failures. Domain decides positivity, task content rules and cross-record invariants. Report either failure through the existing unreadable-data path with its location and unchanged bytes (CP-136–CP-137; `change_spec.md:L71-L72`).

Save remains the same full-state operation and atomic second-file replacement. Preserve the old state and original file on failure, including tasks and counter, under ADR-0004 § Decision and the spec's CP-122 (`products/tracker17/docs/adr/0004-whole-state-saved-atomically-on-every-change.md` § Decision; `change_spec.md:L48-L48`). Neither format strings nor JSON key names become application/domain knowledge.

**Depends on:** A's Task/Comment values, `restore_task` and extended `restore_state`. Saver's `save(state)` contract stays unchanged.

### C — `application/`

**Scope:** actions and read projections over the current state, using the handed-in saver/clock (SDD owning part: `products/tracker17/docs/SDD.md:L201-L201`).

**Exposes — Decision:** `Tracker.add_task(project_id, title, priority="", assignee="", due_date="")` returns the saved Task; `Tracker.task(task_id)` returns Task or `None`; `Tracker.project_tasks(project_id)` returns an immutable tuple of `TaskRow(task, overdue)` values. Export these values, `PRIORITY_CHOICES`, `SHORT_TEXT_MAX` and the new domain refusal classes through application for web. Existing project and People methods keep their signatures.

For add, obtain one creation instant through Clock, apply A to current state, call the existing save-then-publish seam, then return Task. A refusal calls no saver; any saver failure publishes no candidate state. The current save-before-publication seam is `products/tracker17/application/tracker.py:L65-L67`. For a project read, obtain one Clock instant, derive the machine-local calendar date with its local-time conversion, ask domain for ordering and overdue booleans, and return all rows. No clock read or business predicate belongs in web. Injected clocks supply the instant for boundary tests (CP-131, CP-140; `change_spec.md:L63-L63`, `L84-L84`).

**Depends on:** A's pure actions/lookups/overdue contracts. B is not an import or interface dependency: the existing Saver accepts state. Real persisted-path checks require B's codec.

### D — `web/`

**Scope:** requests, addresses, stateless outcomes, accessible pages and one stylesheet (SDD owning part: `products/tracker17/docs/SDD.md:L203-L203`).

**Exposes — Decision: addresses.** Add `POST /projects/<digit-id>/tasks` and `GET /tasks/<digit-id>`, with digit IDs matched by `[0-9]+`; issued identities are positive. Use the existing route declaration, same-origin guard and Site-wide request lock. A successful add returns 303 to `/tasks/<id>?added`; its GET fetches the saved title for the quoted completion line. Plain task GET has no completion line. Both GET forms, reload and history reads call no saver (CP-113–CP-115, CP-123–CP-125; `change_spec.md:L36-L38`, `L49-L54`). Numeric task-shaped addresses with no matching task, zero included, receive the new task-specific 404; all other unknown addresses keep the existing project-specific 404. An unrepresentable numeric address is also missing, rather than an unexpected add/read failure; no web-specific task-count limit is introduced.

**Decision: form transport and outcomes.** Fields are `title`, `priority`, `assignee`, `due_date`; none/unassigned is an empty assignee option value. Use existing UTF-8 form/query codecs and line-feed normalization. Refusals/failures return 303 to the project's existing GET address with a task-scoped outcome code and retained fields encoded as query values; store no pending form, outcome, cookie or session. Unknown project returns the existing not-found page without saving. Put all unexpected add failures through the one existing guarded failure/logging site; the console names the add action before its error (`products/tracker17/docs/nfdr.md` QC-8, QC-23, lines 79–84, 182–186; CP-117–CP-123 in `change_spec.md:L43-L49`).

Outcome page contracts:

| Outcome | Retention and focus decision |
|---|---|
| Blank title | All four fields retained; focus title with adjacent reason as accessible description. |
| Too-long title | Outcome code only, no submitted fields in address or rendered page; fresh defaults; focus title. This discard rule also governs a crafted GET carrying fields beside the too-long code. |
| Assignee no longer listed | Retain title/priority/due date; rebuild choices from current saved People order, select none; name the removed assignee in the adjacent reason, focus assignee and offer an ordinary reload link. No unlisted option is inserted. |
| Invalid priority or date | Focus the concerned control with adjacent described reason; preserve other valid form fields. Reset the rejected priority to medium, or rejected date to empty, so the controls continue to offer valid native choices. |
| Unexpected failure | Retain all four fields; focus the Add form itself with `tabindex="-1"`, `autofocus` and its failure message as accessible description; expose no Python error on the page. |

The retention required in the first, second, third and fifth rows is CP-117–CP-119/CP-122; restoring an invalid hand-built value is not specified in CP-120 (`change_spec.md:L43-L48`). Fresh priority choices are low, medium, high, critical in that order; fresh assignee choices are none followed by current exact names. Title maxlength comes through application from the shared domain bound. Due date uses `input type="date"` with no script. The form remains visible for both empty and populated projects (CP-106–CP-110; `change_spec.md:L26-L30`).

**Decision: page construction.** Extend `project_page` to receive project, ordered TaskRows, current assignees, priority choices and a web-only outcome/form value. Use a semantic six-column table when rows exist; otherwise render the invitation and no empty table. Rendering never filters, sorts or decides overdue. Task rows include all labels as text, without label controls; list due dates are ISO calendar dates and overdue word placement consumes the supplied boolean. New task pages show only title/priority/assignee/due date, plus navigation and the success line when requested. On success, focus the title heading with `tabindex="-1"`, `autofocus`, and `aria-describedby` pointing to the unfocused completion line. Add a distinct `task_not_found_page` to leave the project not-found renderer intact (CP-115, CP-124–CP-133, CP-139; `change_spec.md:L38-L38`, `L53-L65`, `L77-L77`).

Escape every supplied title/name/label/form value at the existing web escaping seam, including attributes, completion text and document title. The content artifact decides the empty-label/undated words, labels and all new messages; this design specifies their data, location, meaning and accessible relationship only (CP-128–CP-129, CP-133; `change_spec.md:L60-L65`).

**Depends on:** C's methods, rows, choices/bound and re-exported types/refusals. No direct domain, persistence or clock access.

### E — `tests/`

**Scope:** § 5's tests, trace table and timed script; exports no production contract.

**Depends on:** A–D for the corresponding public contracts; full-path/browser/timed checks need all four. No production module depends on E.

**Build sequence:** A first; B and C may follow in parallel; D follows C; E's complete persisted request-path checks follow B and D. Domain tests depend only on A, and application tests only on A/C. These edges follow the contract consumers above, rather than a preferred execution order.

**Atomic-landing edges:** A + E's trace registration — no green point with the new domain feature modules present but their feature words absent (CP-138; `change_spec.md:L76-L76`). B + E's saved-shape assertions — no green point with the five-key writer and the exact three-key assertions. D + E's project-page, first-project browser and route-inventory assertions — no green point with the new form/routes and assertions forbidding them (source assertions named in § 5).

---

## 4. Code Strategy

| Sub-job | Hint |
|---|---|
| A — domain | Explicit due-date/identity sort key; shared value checks for creation and restoration, with current assignee membership required only for a new add. Keep the state/type cycle out of runtime imports. |
| B — persistence | Recognize complete key sets, then shape-decode and delegate data validity; preserve the existing atomic full-file save. |
| C — application | Convert one injected aware instant to machine-local today per project page, and pass it to the domain predicate. |
| D — web | Use stateless POST/303/GET outcomes; the too-long outcome carries no submitted text. Rebuild People choices on each GET. |
| E — tests | Seed volume through immutable domain values/restoration in a disposable location; time the real same-origin request and its landing GET separately. |

---

## 5. Test Additions

All paths below are under `products/tracker17/`. Every Example is mapped by its row's source line in adjacent `change_spec.md` § Examples (lines 97–138); a range in the coverage column means every row in that range. The Rules pass follows the table.

| Row / sub-job | Test file | What to add / modify | Example coverage |
|---|---|---|---|
| T1 / A | `tests/unit/test_tasks.py`, `test_priorities.py`, `test_due_dates.py`, existing `test_state.py` | Pure creation/defaults; exact surrounding whitespace and duplicate titles; all priorities; missing/blank title, length 200/201 and 201 spaces precedence; invalid priority/date; absent project; stale assignee; no consumed counter on refusal; global IDs across projects and restored counter. Restore all four statuses, off-list assignee and each CP-137 value/invariant break. Date order uses explicitly shuffled stored tuples, equal instants and reverse timestamps; ties/undated sort by ID. Overdue matrix all statuses × yesterday/today/tomorrow/none, and no clock/file. | 103–107, 109–113, 122–125, 130–131 |
| T2 / C | `tests/integration/test_task_tracker.py` | Saver spy/failure: save once before publication, exception leaves Task tuple and counter unchanged, later successful add uses unconsumed identity. Current-state People removal is seen by subsequent add. Project/People operations retain all tasks and counter. Clock injection tests local date across midnight/UTC boundary and renewed date on a later page build. Project lookup/task lookup/rows use public contracts. | 107, 111, 114, 124–125 |
| T3 / B | `tests/integration/test_saved_data.py`, `tests/integration/test_start.py` | Round-trip all ten task fields plus counter; newly created empty labels/comments; two projects; all enum statuses; optional values; UTC instant, label/comment container preservation without new semantic rules. Restart preserves identity/order/fields. Both legacy forms load with exact original bytes and migrate only on first successful save; project/People changes also save the full form. Each CP-137 break is individually unreadable with location/unchanged bytes, including ID equal to/above counter, unknown status, whitespace/overlong assignee and title. Off-list assignee loads. Exercise malformed new shapes, nonpositive/boolean IDs/counters and timestamps; atomic interrupted/failed save preserves old file and tasks. | 107, 127–131 |
| T4 / D | `tests/integration/test_task_pages.py`, `tests/integration/test_task_routes.py` | Real Site + Tracker + SavedData, no socket: four-field form both empty/populated; exact ordered priorities/default, People exact saved order/default, empty People + link, maxlength from shared bound, native date/no scripts. Full-fields/title-only adds and success 303/GET, heading focus/description, quoted completion, plain task GET without completion. Title duplicates and spaces; repeat landing GET/history GET never saves. Missing project POST and missing numeric task GET, including zero and an unrepresentable digit sequence; other unknown paths keep old 404. | 97–109, 113, 116–119 |
| T5 / D | `tests/integration/test_task_routes.py`, `test_task_pages.py` | All refusal/failure outcomes through real Site: blank/whitespace titles with all four retained and described focus; 201 characters and 201 spaces expose none of any submitted fields in Location/body; crafted too-long GET cannot restore them. Two-tab removal refuses, retains other three, fresh choices and reload link. Invalid enum/calendar input focuses relevant control. Inject saver failure: original file/state unchanged, all fields retained, form focus/description, plain page message, action/error at single console site. Same-origin guard covers cross-site, same-site, none and absent mark before action/saver. Every refusal followed by GET still has no task/invitation as appropriate. | 109–115 |
| T6 / D | `tests/integration/test_task_routes.py`, `test_task_pages.py` | Project isolation and all rows/no limit; exact six-column order/link/status/priority/assignee/labels/date; empty→populated invitation transition; dated/undated order and ties before/after restart; yesterday/today marking via injected Clock; literal title/assignee/labels and form values with HTML characters. Read-only task page has correct document title/four fields/unassigned/undated, no status or action controls. Missing-task page offers only Projects. Reject excluded modules/routes/controls. | 116–127, 131, 133–134 |
| T7 / E | `tests/architecture/test_trace.py`, existing architecture suite | Add tasks/priorities/due_dates to landed words; trace docstrings name SRS requirements, application/web participants and checking test modules; new test docstrings trace CP/SRS. Check no `labels.py` or other excluded feature entry. Preserve import/capability/gate coverage. | 132–135 |
| T8 / E | `tests/integration/test_routes.py` and existing route-wide security probes | Extend SAMPLE_ADDRESS and SUBMITTED_BODY for new routes with valid project/task fixtures; exercise accepted task POST, rejected submissions and all task GETs. Keep assertions for unchanged state on reads, no cookies, headers/CSP and no external egress. Include tasks/counter in state comparison. | 108, 115–117 |
| T9 / E | `tests/e2e/test_tasks.py` | Browser enters 200 characters and cannot add a 201st via ordinary typing; native date field; complete add and heading accessibility. Enter `<b>A&B</b> "Q"` title, follow task→project list and assert literal text/exact link/title with no injected bold node. Cover new empty invitation through existing first-project journey. | 98, 102–103, 126, 137 |
| T10 / E | `tests/timed_run.py` | Keep existing project-create checks. Add ordinary-length fixture of 1,000 tasks with 20 comments per task, stored through real SavedData in its own temporary location, per QC-48. Report fixture volume and actual text lengths. Time add POST and landing GET independently, each strictly below one second; verify successful task identity/state and landing content, fail on refusal/failure/bound. Keep maximum-length project checks as additional existing checks, not the ordinary-volume substitute. No comment/label action is introduced. | 138 |
| T11 / E | Existing suite and gate commands | In a disposable `git archive HEAD` copy followed by `git init`, require `pytest products/tracker17/tests/`, separate `pytest products/tracker17/tests/e2e/`, and `python3 products/tracker17/tests/timed_run.py` each exit 0. Apply the configured Ruff format/lint and mypy gates, without exemptions. No claim of their results is made by this design. | 135–136 |

**Rules pass:** CP-106–CP-110 are covered by T4/T9; CP-111–CP-113 by T1/T2/T3/T4; CP-114–CP-115 by T4/T8/T9; CP-116–CP-123 by T1/T2/T4/T5/T8; CP-124–CP-129 by T4/T6; CP-130–CP-133 by T1/T2/T3/T6/T9; CP-134–CP-137 by T1/T3/T6; CP-138–CP-139 by T6/T7; CP-140 by T1–T6; CP-141 by T11; CP-142 by T9; CP-143 by T10. Boundary paths explicitly include empty/all-undated/failed-only project lists, date leap-day validity and malformed/non-calendar forms, all four overdue statuses, counter continuity after failure/restart, exact duplicate task titles, late People removal and readable historical assignees. These are required tests, not a statement that they have run (`change_spec.md` § Rules, lines 26–87).

**Assertions retired and clauses re-proved:**

- `tests/integration/test_pages.py:L206-L217` asserts no form/input/textarea/button/select and no first-task invitation on a project page. Those absence clauses are replaced by CP-106/CP-126; T4/T6 prove the exact add form/invitation and still forbid excluded controls. Retain its project heading, exact name/description and project document-title checks.
- `tests/e2e/test_first_project.py:L68-L70` expects the old no-task sentence and no form/button/input/textarea. T9 re-proves an accessible no-task message plus invitation and exactly the specified add form, using the content artifact; retain the journey's creation, heading focus and read-back assertions.
- `tests/integration/test_saved_data.py:L319-L326`, `L383-L388` asserts exactly three top-level keys. T3 replaces that with exactly the new five keys, preserving all original project/counter/People shape/order checks and adding empty tasks/counter plus legacy byte-preservation tests. No malformed legacy fixture becomes readable because the new form exists.
- `tests/integration/test_routes.py:L262-L280` fixes the old route inventory. T8 extends its sample/body maps rather than dropping the inventory equality or skipping a route. All existing security probes continue to visit every declared route.

These replacements re-prove the original remaining clauses and the specified new contracts; they do not remove tests or relax validity/security assertions. The no-form/three-key clauses themselves are superseded by the feature, while CP-141 requires the existing coverage to remain (`change_spec.md:L26-L26`, `L70-L71`, `L85-L85`).

---

## Records this change makes false

None — read `products/tracker17/docs/adr/` (index and Accepted records 0001–0009), `docs/fdr.md`, `docs/nfdr.md` and `docs/SDD.md` § 3. The delta uses the already-declared Task/counter and existing parts graph; it adds feature entry files within domain, not a new architectural part (`products/tracker17/docs/SDD.md` § 3, lines 200–254; `products/tracker17/docs/nfdr.md` § 1.2, lines 129–153). Their final-product task/edit/comment requirements are not descriptions of today's implemented slice. No foundation record is edited here.

---

## Architect Review Notes

### Decisions beyond the spec — architect, 2026-10-11

- **(b) Addresses and identity ordering:** global `/tasks/<id>` plus project-scoped POST makes task address ownership explicit; digit-shaped missing addresses, zero and unrepresentable numbers included, receive task not-found so the address shape consistently selects the missing-object wording. The saved monotonically issued identity is the final ordering tie-breaker, even when storage order/timestamps disagree. CP-113 leaves the address form open, CP-125 selects task wording for missing task-shaped addresses, and SDD fixes identity as creation order (`change_spec.md:L36-L36`, `change_spec.md:L54-L54`; `products/tracker17/docs/SDD.md:L242-L245`).
- **(b) Value/schema contracts:** enums, immutable Task/Comment tuples, positive counters, full five-key JSON form, UTC instant encoding and the additive restoration signature are the chosen realization of CP-135–CP-137; no new label/comment business rule is inferred. They allow the timed fixture to carry comments without adding an action (`change_spec.md:L70-L72`; `products/tracker17/docs/SDD.md:L246-L253`).
- **(b) Order of options and mixed invalid fields:** low→medium→high→critical makes the ascending urgency choices explicit; CP-108 delegates their order. The precedence in A resolves otherwise unspecified simultaneous invalid fields while keeping too-long-before-blank and unknown-project handling (`change_spec.md:L28-L28`, `L44-L47`).
- **(b) Stateless recovery and malformed values:** task-scoped query outcomes keep the existing no-session boundary; too-long drops every submitted field. A stale assignee returns to none with a named reason, keeping the current list as the sole options source; malformed priority/date reset only the invalid control, retaining valid others. Invalid date strings must match calendar ISO form. The specified retention and native controls constrain these choices; invalid-control restoration is left implicit (`change_spec.md:L29-L30`, `L43-L48`; `products/tracker17/docs/nfdr.md` QC-8, lines 79–84).
- **(b) Failure focus:** focus the form container with described failure text, rather than add a new focusable message, to realize CP-122's Add-form focus; success uses the specified heading/description pattern (`change_spec.md:L38-L38`, `L48-L48`).
- **(a) Existing assertions versus CP-141:** the assertion replacements in § 5 keep every applicable old clause proved; old no-form and exact-three-key results cannot coexist with CP-106/CP-135. Retaining the tests with precise replacement assertions is the interpretation of “no existing test is weakened or removed,” rather than suppressing these tests (`change_spec.md:L26-L26`, `L70-L71`, `L85-L85`).
- **Owner-set scope:** include browser escaping and the task timed run. The previous station exclusion does not override the later locked owner answer; no renewed decision is needed (`change_spec.md` § Locked Answers, Gap 14, line 185).

### Delegated architectural reviews — architect verdicts, 2026-10-11

| Gate | Verdict and design evidence |
|---|---|
| QC-5, QC-20–QC-24 | **Pass for this design.** A owns typed validation/ordering/overdue without wording; C owns apply/save/publish and Clock conversion without rules; B only owns file shape/codec and delegates validity; D owns request/display without business rules; main is unchanged. This reviews the respective no-rule/no-wording obligations (`products/tracker17/docs/nfdr.md:L56-L67`, `L160-L190`). |
| QC-8, QC-12 | **Pass for this design.** Four affected product parts retain the existing seams; no session/outcome store, framework, generic migration layer or unpaid part is proposed. New entry modules are required by CP-138, not an extra framework (`products/tracker17/docs/nfdr.md:L79-L84`, `L115-L120`; `change_spec.md:L76-L76`). |
| QC-25–QC-27 | **Pass for this design.** B alone owns JSON representations; Saver remains full-state. Browser/form/outcome knowledge stays in D, with the existing main wiring. QC-26's saving-contract replacement trigger does not apply (`products/tracker17/docs/nfdr.md:L194-L208`). |
| QC-36, QC-41, QC-46 | **Pass for this design.** One escaping seam covers all rendered values with T9's real-browser proof; no secret/account/credential is added; only the specified Task fields/counter are persisted (`products/tracker17/docs/nfdr.md:L270-L276`, `L320-L324`, `L378-L383`; `change_spec.md:L70-L70`, `L86-L86`). |
| QC-60, QC-62 | **Pass for this design.** Only Python 3.11 standard-library product contracts are proposed; no dependency/pin/config changes. T11 retains the configured format/lint/type gates. This verdict does not claim implementation or command results (`products/tracker17/docs/nfdr.md:L462-L485`). |
| QC-40 | **Pass with the existing browser exception; review evidence and limits below.** No pin moves are proposed. The dated exception is in force on this review date (`products/tracker17/docs/nfdr.md:L968-L980`). |

### QC-40 dependency and browser review — 2026-10-11

The reviewed lock contains the following exact pins (`products/tracker17/tests/requirements.txt:L4-L18`). Each linked maintainer advisory page displayed no published advisory in the returned page; that is the bounded review result, not a claim that vulnerabilities cannot exist.

| Reviewed pin | Maintainer advisory source |
|---|---|
| ast_serialize 0.12.1 | [mypyc/ast_serialize](https://github.com/mypyc/ast_serialize/security/advisories) |
| greenlet 3.5.6 | [python-greenlet/greenlet](https://github.com/python-greenlet/greenlet/security/advisories) |
| iniconfig 2.3.1 | [pytest-dev/iniconfig](https://github.com/pytest-dev/iniconfig/security/advisories) |
| librt 0.16.0 | [mypyc/librt](https://github.com/mypyc/librt/security/advisories) |
| mypy 2.4.0 | [python/mypy](https://github.com/python/mypy/security/advisories) |
| mypy_extensions 1.1.0 | [python/mypy_extensions](https://github.com/python/mypy_extensions/security/advisories) |
| packaging 26.3 | [pypa/packaging](https://github.com/pypa/packaging/security/advisories) |
| pathspec 1.1.1 | [cpburnz/python-pathspec](https://github.com/cpburnz/python-pathspec/security/advisories) |
| playwright 1.63.0 | [microsoft/playwright](https://github.com/microsoft/playwright/security/advisories) |
| pluggy 1.6.0 | [pytest-dev/pluggy](https://github.com/pytest-dev/pluggy/security/advisories) |
| pyee 13.0.1 | [jfhbrook/pyee](https://github.com/jfhbrook/pyee/security/advisories) |
| Pygments 2.21.0 | [pygments/pygments](https://github.com/pygments/pygments/security/advisories) |
| pytest 9.1.1 | [pytest-dev/pytest](https://github.com/pytest-dev/pytest/security/advisories) |
| ruff 0.16.10 | [astral-sh/ruff](https://github.com/astral-sh/ruff/security/advisories) |
| typing_extensions 4.16.0 | [python/typing_extensions](https://github.com/python/typing_extensions/security/advisories) |

Installed browser identification: reading `CFBundleShortVersionString` with Python `plistlib` from `~/Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/Info.plist` returned `Cached Chromium CFBundleShortVersionString: 153.0.8010.12`. The vendor's September 8 desktop release fixes Chrome 153 at 153.0.8010.36/.37 and lists critical WebGL/Cast issues, including CVE-2026-87464 and CVE-2026-87527 ([Chrome Releases, September 8 entry](https://chromereleases.googleblog.com/2026/?amp=1)). The installed build precedes that fix release; treating it as subject to that release's critical-advisory window is an inference from those version numbers. September 8 to October 11 is 33 days, past QC-40's 30 days. **Accepted under the owner's existing build-specific exception through 2026-11-07**, not a new exception or a claim that the build is fixed (`products/tracker17/docs/nfdr.md` RN-33, lines 968–980).

Review limit: the attempted Python HTTPS query to `api.osv.dev/v1/querybatch` failed with DNS output `[Errno 8] nodename nor servname provided, or not known`; it supplied no package verdict. The review above uses the fetched maintainer pages and vendor release search result. Some GitHub pages also displayed a loading-error banner while returning the advisory section; no exhaustive database scan is claimed. No critical package advisory was identified in those sources. The owner's recorded reason about the newest PyPI Playwright is cited as the dated record's reason, not reasserted as today's index fact (`products/tracker17/docs/nfdr.md:L970-L978`).
