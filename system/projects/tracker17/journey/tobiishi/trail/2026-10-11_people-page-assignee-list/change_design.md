# Change Design — The People page keeps the assignee list

**Date:** 2026-10-11
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the header's People link; the People page's title, headings, empty state, name field, Add button and Remove buttons with their accessible names; the add and remove completion lines, refusal reasons, reload link and failure messages; the console's add and remove failure messages

---

## 1. Change Summary

This blueprint owns the placement, interfaces and dependency order for the assignee-list change.
Its behavioural authority is `tracker17 · tobiishi · 2026-10-11_people-page-assignee-list`,
`change_spec.md` § Rules (CP-80 to CP-105) and § Locked Answers. References to CP rules and Examples
below point there; E1 to E26 mean its Examples in table order (`change_spec.md:L80-L105`). Product
paths below are relative to `products/tracker17/` in this change's worktree.

Add `domain/assignees.py` and extend the state, actions, saved-data adapter and browser interface.
Keep the existing five-part architecture: `docs/SDD.md` § 3, The parts, and the seams between them
(`products/tracker17/docs/SDD.md:L186-L223`). No new top-level part, task model, operator name,
migration, session or script belongs to this design; the scope is CP-85 and CP-105, with the spec's
§ Out of Scope left intact.

The page address is `/people`. Add submits to `/assignees`; Remove submits to `/assignees/remove`.
Both actions take the exact name in a form field, never as an identity embedded in a path. Every
action outcome redirects with status 303 to `/people` through the existing address-building seam,
with no fragment, under `docs/SDD.md` § 4 RT-8 and RT-9
(`products/tracker17/docs/SDD.md:L318-L337`). These address choices are this architect's decisions
of 2026-10-11; their reasons are in § Architect Review Notes.

## 2. Blast Radius

The parts table exists. Its `Lives in` cells are empty because the parts share the product-root
Python unit; its `Owns` cells name the directories that own the logic (`docs/SDD.md` § 3,
The parts and The units; `products/tracker17/docs/SDD.md:L190-L207`).

| Module | Status | What changes |
|---|---|---|
| `domain/` | Modified; new `assignees.py` within it | Owning part: `domain`. Exact-name validation, ordered immutable assignee state, add/remove/list rules and stale-remove refusal; restoration applies the same assignee rules. Extend `state.py`, `refusals.py` and `__init__.py`; retain `text.py`'s one length maximum. |
| `application/` | Modified | Owning part: `application`. Add and remove over current state, save before making it current, and a list query. Extend `tracker.py` and re-export the new refusal types from `__init__.py`. The saving and clock contracts keep their signatures. |
| `persistence/` | Modified | Owning part: `persistence`. Extend `saved_data.py`'s JSON shape with an ordered `assignees` array; read legacy missing-list data without writing; hand value validation to `domain.restore_state`. Keep the atomic whole-state save. |
| `web/` | Modified | Owning part: `web`. Extend `routes.py` with the page and two submissions, type-based outcome mapping and the shared failure boundary; extend `pages.py` with People and the shared header; extend `style.css` for the assignee sheet, wrapping row controls and focus on the new non-control targets. |
| `main.py` | Unchanged | Existing wiring accepts the enriched state through unchanged `SavedData.load`, `Tracker` and listener contracts (`main.py:L37-L51`, § start). |
| `errors.py` | Unchanged | New refusals inherit the existing `domain.refusals.Refusal`, which already derives from `AppError` (`domain/refusals.py:L11-L26`, § Refusal). |

Transitive callers are included: `application` and `persistence` consume the changed domain state;
`web` consumes application results and re-exported refusal types. No forbidden edge is needed
(`docs/nfdr.md` § 1.2 Forbidden imports, QC-13 to QC-18;
`products/tracker17/docs/nfdr.md:L128-L150`). `main` needs no call-site change because the added
state field has an empty default and the two-argument restoration call remains valid (§ 3 A).

Tests are in the blast radius alongside the production parts: new assignee unit, action, page,
request and browser tests; existing state, saved-data, startup, page, route-enumeration and trace
tests; and the not-found browser test. Their precise obligations and retired assertions are § 5.

## 3. Sub-jobs

Each sub-job owns one production part and its associated test delta. Contracts below are design
interfaces, not implementations. No sub-job crosses two production parts.

### Sub-job A — `domain/`

**Scope:** Add the Assignees entry module, integrate its rules into restoration and publish its
surface from `domain`. Keep project values and identity issuance unchanged. Update the landed-feature
trace declaration with this module, not later: the reverse trace check requires that pairing
(`tests/architecture/test_trace.py` § test_each_feature_word_with_its_domain_module_is_listed_as_landed,
`products/tracker17/tests/architecture/test_trace.py:L24-L24` for the current landed declaration and `L223-L226` for the reverse test).

**Exposes:**

| Interface | Contract |
|---|---|
| `TrackerState.assignees` | Immutable `tuple[str, ...]`, default `()`. Preserve the two existing constructor arguments and all other state fields. |
| `restore_state(projects, next_project_id, assignees=()) -> TrackerState` | Existing arguments and return type remain; the optional third argument takes a sequence of names, validates all names and exact uniqueness, and retains their order. A refusal restores no partial state. |
| `check_assignee_names(names) -> tuple[str, ...]` | Shared domain validation for restoration and action candidates; applies CP-101's value rules, with length before blank. No sorting, case folding, trimming or wording. |
| `add_assignee(state, name) -> TrackerState` | Return a new state with the accepted name appended, or raise the condition's refusal. |
| `remove_assignee(state, name) -> TrackerState` | Return a new state with the exact matching name removed, or raise `AssigneeNotFound`. Preserve the order of every survivor. |
| `list_assignees(state) -> tuple[str, ...]` | Return the state's declared assignee order. |
| `AssigneeNameInUse`, `AssigneeNotFound` | New refusal types in `refusals.py`, deriving from `Refusal`, with no operator-facing wording. |
| `BlankName`, `TextTooLong`, `TextField.NAME`, `SHORT_TEXT_MAX` | Reuse these existing conditions and the name-field maximum. `NameInUse` keeps its project-specific meaning (`domain/refusals.py:L26-L40`; `domain/text.py:L10-L19`). |

Appending to an ordered tuple, removing only the matching member, and restoring the array in its
given order realize CP-82 by construction. There is no separate ordering counter or assignee ID.
Creating a project on a state with assignees must preserve that field, and an assignee action must
preserve every project and the counter (CP-100, CP-105; `domain/projects.py:L55-L61`, § create_project,
already replaces the existing state).

**Depends on:** none.

### Sub-job B — `application/`

**Scope:** Apply A's rules to the current state, save the candidate, then publish it as current;
propagate refusals and save failures. No field validation or duplicate search belongs here, per
`docs/SDD.md` § 3 application (`products/tracker17/docs/SDD.md:L193-L193`).

**Exposes:** `Tracker.assignees() -> tuple[str, ...]`,
`Tracker.add_assignee(name: str) -> str` and `Tracker.remove_assignee(name: str) -> str`.
An action returns the exact accepted/removed name only after the save succeeds. A refusal or save
failure leaves the current state unchanged. Re-export `AssigneeNameInUse` and `AssigneeNotFound`
alongside the existing refusal and maximum exports so `web` never imports `domain` directly.
`Saver.save(state)` and the constructor's `(state, saver, clock)` stay as they are
(`application/contracts.py:L14-L17`, § Saver; `application/tracker.py:L17-L27`, § Tracker).

**Depends on:** A's state, action functions, list function and refusal types. B uses the saving
protocol, not C's concrete class.

### Sub-job C — `persistence/`

**Scope:** Read and write the enriched whole state in `saved_data.py`. Keep the project records,
counter, location, temporary-file and replace procedure unchanged; the latter is the existing
`SavedData.save` seam (`persistence/saved_data.py:L57-L73`, § save).

**Exposes:** `SavedData.load() -> TrackerState | None` and `SavedData.save(state) -> None` keep
their signatures. New writes contain exactly `next_project_id`, `projects`, and `assignees`, the
last an array of strings in state order. A legacy document with exactly the first two keys loads
with `assignees=()`; a missing required project/counter key or an unrelated key remains unreadable.
An explicitly present `assignees` must be a list of strings: `null`, a scalar, a mapping or a list
containing non-text is not the missing-list case. The adapter checks JSON shape/types and delegates
blank, duplicate and length rules to A. Its existing conversion of `Refusal` to `UnreadableData`
must cover the new refusals, retaining the saved file bytes (CP-100, CP-101;
`persistence/saved_data.py:L42-L55`, § load).

No read rewrites the file. The next successful state-changing save, including a project create,
writes the full current shape. A refused remove from an empty legacy list saves nothing; CP-100
does not grant a refusal permission to write, because CP-96 pins unchanged saved data.

**Depends on:** A's enriched state and compatible restoration contract. No dependency on B.

### Sub-job D — `web/`

**Scope:** Page and action routing, typed outcome mapping, all published text placement, semantic
HTML and the stylesheet. Preserve the current host/fetch-site check and request lock around check,
application action, save and response (`web/routes.py:L97-L117`, § Site.handle). The shared page
document gains People after Projects; the order of existing areas is `docs/DESIGN.md` § Layout,
Header (`products/tracker17/docs/DESIGN.md:L350-L352`), with absent areas omitted under CP-85.

**Exposes:** Add `GET /people`, `POST /assignees`, `POST /assignees/remove` to the declared `ROUTES`.
Each submission reads `name` using the existing strict UTF-8 form decoder and line-feed normalization,
calls one B action, and answers with a 303 Location made by `_address`. Wrong origin/host checks
remain first; invalid UTF-8 remains a 400 with no mutation, as on the existing create route
(`web/routes.py:L176-L187`, § _create). GET only queries the list and builds a page.

Outcome-address contract:

| Outcome | Query on `/people` | Page focus / description target |
|---|---|---|
| Plain list | none | No action autofocus or outcome line. |
| Added | `added=<exact name>` | The matching name's non-control span in its row. |
| Removed | `removed=<exact name>` | The Assignees sheet's `h2`, `id="assignees-heading"`. |
| Blank add / duplicate add | `refused=blank-name` / `refused=assignee-name-in-use`, plus `name` | Add name input, with the field reason as description. |
| Too-long add | `refused=too-long` only | Add name input with its reason; ignore any supplied name/outcome payload, carrying and rendering no submitted text. |
| Stale remove | `refused=assignee-not-found`, plus `name` | Assignees heading with the refusal as description and a link to plain `/people` for reload. |
| Failed add | `failed=add`, plus `name` | Add button with the failure as description; retain the field value. |
| Failed remove | `failed=remove`, plus `name` | Matching row's Remove button with the failure as description. |

The page-building interface is `people_page(assignees, *, added=None, removed=None, refusal=None,
failed=None, name="") -> str`: an immutable string sequence, optional string outcome values, and
retained field text. It builds one whole document and keeps no state. Map each domain refusal by its type at the action boundary; query codes
are presentation identifiers, never exception messages. Recognize only the above outcomes, with
refusal before failure before success (added before removed) if a hand-built query combines them. Unknown codes show the
plain page. On a later GET whose added/failed-remove subject is no longer listed, keep the outcome
line and use the sheet heading as its description target; the history address changes no state.
These query-resolution decisions are recorded in the review notes.

Use per-render ordinal element IDs for rows, separate from names. After add, apply `tabindex="-1"`,
`autofocus`, and `aria-describedby` to the matching name span. Its Remove button is the next control
in reading order. After removal/stale removal use those same focus attributes on the Assignees
heading. Never put focus on the message paragraph; only one outcome target receives autofocus.
Whitespace in displayed names must survive, including around the value (CP-82, CP-87, CP-94).
For each Remove, the accessible wording names the exact value and a distinct row ordinal so even
names differing only in repeated spaces have distinct accessible names. Its visible word and
accessible wording are authored to CP-83, not invented here.

All dynamic names entering HTML, including input values, hidden Remove values, messages and
accessible names, pass through `_escape`; names never become element IDs. Keep all links/actions
local and use the existing page policy (CP-82, CP-98; `web/pages.py:L32-L34`, § _escape;
`web/routes.py:L25-L25`, § PAGE_POLICY). Take visible and accessible wording from this change's
text record to `docs/CONTENT.md`; take visual values from `docs/DESIGN.md`. Add the stylesheet's
focus treatment to the new name spans and heading, not only to controls (CP-87; `web/style.css`,
§ Focus currently ends with `h1:focus`, `products/tracker17/web/style.css:L201-L209`).

Keep one unexpected-failure catch site for project create, assignee add and assignee remove, plus
one console-report site. The boundary uses action kind and name to select the outcome address and
content-record console message; it never branches on exception text. Expected refusal handling
stays separate. Preserve create's existing redirects, fields, messages and diagnostic lines while
sharing the failure boundary (`docs/nfdr.md` QC-45, QC-56, QC-57;
`products/tracker17/docs/nfdr.md:L362-L366`, `L442-L448`).

**Depends on:** B's list/actions/refusal exports. D's browser proof also needs C's saved-data shape
through `main`; C is not a direct web import.

**Build sequence:** A first; B and C may follow independently; D's in-process page/action work follows
B, and its whole-process browser proof follows B and C. This is contract order; it specifies no
implementation tasks or red/green sequence.

**Atomic-landing edges:**

- A's `assignees.py` + the landed-feature declaration — no green point between them: the reverse
  trace test fails with an existing entry module absent from its landed list (`tests/architecture/test_trace.py`,
  § test_each_feature_word_with_its_domain_module_is_listed_as_landed, `tests/architecture/test_trace.py:L223-L226`).
- C's new saved shape + the exact-key test update — no green point between them: that assertion
  currently permits only the two legacy keys (`tests/integration/test_saved_data.py:L282-L290`,
  § test_the_saved_file_holds_only_its_keys).
- D's shared header + the existing exact-navigation assertions — no green point between them:
  those tests require one link and forbid People (`tests/integration/test_pages.py:L155-L173`,
  § test_every_page_has_a_header_with_one_link_to_projects; `tests/e2e/test_first_project.py:L180-L193`,
  § test_an_address_with_no_project_shows_the_not_found_page).

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — assignee rules and restored state | Preserve the projects module's separation between runtime state construction and type-only state references; a mutual runtime import between `state.py` and `assignees.py` would create a cycle. |
| B — assignee actions | None |
| C — saved-data shape | Distinguish a missing optional legacy field from an explicitly malformed field; reuse domain construction for value rules and the existing atomic replacement for saves. |
| D — page, actions and failure boundary | Outcome information travels only in the redirect query. Native `autofocus` on a `tabindex="-1"` name span/heading gives the required non-Tab target; use ordinal IDs rather than embedding names. Keep unexpected action failures at one shared boundary. |

## 5. Test Additions

Each row identifies its owning sub-job and proof obligation. The paths follow the existing test
layout; layers are `docs/nfdr.md` § 9 (`products/tracker17/docs/nfdr.md:L491-L505`). New test module
docstrings name the SRS identifiers they check, in addition to CP rules (CP-102).

| Row / sub-job | Test file | What to add / modify; Example coverage |
|---|---|---|
| T1 / A | `tests/unit/test_assignees.py` (new) | Empty list; add Dana/Ari/Bo; exact case and spaces; remove/re-add moves to end; survivor order; immutability and other-state preservation. CP-82, CP-86, CP-88, CP-95. E3, E4, E6, E13. |
| T2 / A | `tests/unit/test_assignees.py` | Blank empty/whitespace, exact duplicate, 200 accepted/201 refused, 201 spaces length precedence, non-BMP code points; absent remove refused and remove-after-re-add accepted. Domain tests take only values, no file/clock. CP-89 to CP-92, CP-96. E7 to E11, E14, E15. |
| T3 / A | `tests/unit/test_state.py` | Existing two-argument restore and constructor default; restore ordered exact names and apply all list value rules; retain all project checks; a project create retains assignees. CP-100, CP-101, CP-105. E20 to E22. |
| T4 / A | `tests/architecture/test_trace.py` | Add `assignees` to landed words alongside its entry module; assert the new entry docstring names FR-20, FR-22, FR-39, FR-40, DR-4, NFR-9 and all participating application/web/test modules; retain both trace directions and all projects checks. CP-102. E23. |
| T5 / B | `tests/integration/test_assignee_tracker.py` (new) | Real Tracker plus handed recording/failing savers: query/actions, current-state duplicate/stale checks, candidate saved before current publication, failures leave old current state, project create preserves list and list actions preserve projects/counter. Cover empty and nonempty starting state. CP-86, CP-92, CP-96, CP-97. E11, E14 to E17. |
| T6 / C | `tests/integration/test_saved_data.py` | Full real-file round trip with names in order and exact spaces, remove/re-add and an empty list. Assert exactly three permitted top-level keys and unchanged project record keys/counter; no unknown key accepted. CP-99, CP-100, CP-105. E19, E20. |
| T7 / C | `tests/integration/test_saved_data.py` | Legacy two-key data loads empty list without changing bytes/location; first successful add saves enriched shape; a refused remove saves nothing. Malformed present list: duplicate, empty/whitespace name, overlong name, number member, mixed text/non-text, null, scalar or mapping -> UnreadableData, no partial state and identical bytes. CP-100, CP-101. E20 to E22. |
| T8 / C + D proof | `tests/integration/test_start.py`; `tests/integration/test_people_routes.py` (new) | Exercise actual startup refusal on each CP-101 break with location/plain console message and unchanged bytes; restart an application/site wired with real SavedData after add/remove and assert ordered list. Legacy startup keeps every project and file bytes. CP-99 to CP-101. E19 to E22. |
| T9 / D | `tests/integration/test_people_pages.py` (new); `tests/integration/test_pages.py` | People GET empty/populated, title, Add form, maxlength, exact text including spaces and markup, one Remove per row, distinct accessible names including repeated-whitespace-only differences, no operator name/comment or unavailable control. All HTML pages have one header and exactly Projects/People links. CP-80 to CP-85, CP-91. E1 to E4, E6, E9. |
| T10 / D | `tests/integration/test_people_routes.py` | Add/remove succeed once and answer 303; following/reloading/history outcome GETs never call save, with/without data. Exact matching, remove/re-add order, stale add and both stale-remove sequences against one shared live Site; empty after removing the last name retains Add and empty text. CP-82, CP-86, CP-92 to CP-96. E3 to E6, E11 to E15. |
| T11 / D | `tests/integration/test_people_routes.py`; `tests/integration/test_people_pages.py` | Blank/duplicate reason and retained input; absent name field is blank; 200 Unicode code points accepted; overlong/overlong-blank refusal wins and emits no submitted text in Location or page. Follow too-long URL with hand-added payload and verify ignored text. Strict invalid UTF-8 returns 400; submitted CRLF/CR normalizes to LF without trimming. CP-88 to CP-91. E6 to E10. |
| T12 / D | `tests/integration/test_people_routes.py`; `tests/integration/test_routes.py` | Failed add/remove with handed failing saver, on empty and populated state as applicable: no state/file change, retained typed value or row, correct autofocus/description markup, plain failure page and action then diagnostic on stderr. Preserve the existing failed-create coverage at the single shared catch/report boundary. CP-97. E16, E17. |
| T13 / D | `tests/integration/test_people_routes.py`; `tests/integration/test_routes.py` | Both submissions: cross-site, same-site, none, missing and other non-same-origin marks refused; same-origin accepted; wrong/missing Host refused. Extend exhaustive route samples with meaningful setup for remove; compare assignees and projects plus saves for all GETs, assert policy/no cookies for each response, extend no-outbound audit coverage to both new actions. CP-80, CP-98; QC-7, QC-8, QC-31 to QC-35, QC-53. E1, E18. |
| T14 / D | `tests/e2e/test_people.py` (new) | Chromium via the existing main-start harness: add exactly `<b>A&B</b>`, assert literal text/no injected element, added name focused, in viewport, completion line quoted and its accessible description; next Tab focuses its Remove. Reload/back/forward change no saved bytes. Repeat with a name including a quote to cover QC-36. CP-82, CP-86, CP-87, CP-103. E5, E24. |
| T15 / D | `tests/e2e/test_people.py` | Keyboard-only add/refusal/remove: blank/duplicate name input focus and description, remove-last and stale-remove sheet-heading focus/description, failed-add button and failed-remove control markup covered by T12; assert message itself is never focused, name not in sequential Tab order, no page script and visible focus on non-control targets. Verify long names and narrow-page reflow against DESIGN. CP-83, CP-87, CP-89, CP-90, CP-94, CP-96. E7, E8, E12, E14. |
| T16 / D | `tests/integration/test_pages.py`; `tests/e2e/test_first_project.py` | Replace single-header-link/no-People/all-links-to-root expectations with exact Projects/People header checks. Keep the not-found main's single Projects link and unchanged wording, 404, no forms, hostile-address absence and no writes. CP-80; spec § Out of Scope, not-found body. E1. |
| T18 / D | `tests/integration/test_people_routes.py`; `tests/integration/test_people_pages.py` | Unknown and combined outcome queries follow the declared precedence; absent success/failure subject uses the sheet heading and retains the line; synthetic outcome GETs never call save. Include too-long refusal with added, removed and failed payloads and prove all payload text omitted. |
| T17 / A to D | `tests/architecture/test_shapes.py`, `test_imports.py`, `test_reach.py`, `test_trace.py`; existing suite; `tests/timed_run.py` | Existing whole-tree architecture checks cover new code; assert no forbidden future feature module and no task/operator-name state field added. Full project-card suite collects unit/integration/e2e/architecture; existing timed run still exits 0, without adding assignee timings. CP-102 to CP-105. E23, E25, E26. |

T8's combined proof belongs to D for the request path and C for startup/persistence; it creates no
production sub-job spanning parts. Hand failures through the saver seam, never by patching a product
name (QC-28/QC-29, `products/tracker17/docs/nfdr.md:L208-L218`). Browser tests use the existing real
process harness, not a mocked page (CP-103; `tests/e2e/conftest.py:L73-L105`, § TrackerFactory).

**Rule-edge pass:** CP-80/81's read-only links and GETs -> T9/T13; CP-82/83's exact whitespace,
markup, order and accessible-name uniqueness -> T1/T9/T14; CP-84's initially empty and remove-last
states -> T9/T10/T15; CP-85/105's unavailable features -> T9/T17; CP-86/93's history and reload
non-repetition -> T10/T14; CP-87's next-Tab/non-Tab/viewport/no-script targets -> T14/T15;
CP-88/89/90/91's case, spaces, empty, boundary, refusal precedence and payload omission -> T2/T11;
CP-92/96's stale checks and removed-then-readded case -> T5/T10; CP-94's missing subject and
CP-97's failures -> T12/T15; CP-98's full refused-mark set -> T13; CP-99/100/101's restart,
legacy missing field, malformed present field, unchanged bytes and console -> T6/T7/T8;
CP-102/103/104's trace and proof layers -> T4/T14/T17. The design's additional query-resolution edges -> T18. No Example or rule-implied path is deferred.

**Assertions retired and re-proved:**

- T6 replaces the literal two-key set in `tests/integration/test_saved_data.py:L282-L290`
  (§ test_the_saved_file_holds_only_its_keys) with an exact three-key set and explicit empty-list
  assertion; the no-extra-fields clause and unchanged project fields/counter remain proved. T7
  separately preserves the legacy-read contract.
- T9/T16 replace the one-link, People-forbidden and all-links-to-root assertions in
  `tests/integration/test_pages.py:L155-L173`, `L342-L350` and
  `tests/e2e/test_first_project.py:L180-L193` with exact full-header expectations and an exact
  main-body Projects-only link assertion. Unavailable All tasks/rename/delete remain forbidden on
  existing pages. These are changed-feature expectations, not removed checks.
- T13 extends `tests/integration/test_routes.py` § SAMPLE_ADDRESS and
  § test_every_route_leaves_state_and_headers_as_the_rules_say: exhaustive route equality stays,
  and the read-only assertion includes the new state field. No existing failure, escaping, format,
  startup or project assertion is dropped.

## Records this change makes false

- `products/tracker17/docs/adr/0003-no-script-in-any-page.md` § Consequences, Dependence
  (`products/tracker17/docs/adr/0003-no-script-in-any-page.md:L45-L50`) and `products/tracker17/docs/SDD.md` § 11 R-2 and § Open Questions — on a passing
  CP-103 proof, the statement that non-control focus/description is wholly unverified needs to
  distinguish the added-name span now checked from confirmations and assistive-technology speech
  that this browser assertion does not check. The correction should record that narrower evidence,
  retain the untested cases and keep the no-script decision. This is conditional on that proof;
  this design records no test success and closes no foundation question.
- None in `products/tracker17/docs/fdr.md`, `products/tracker17/docs/nfdr.md`,
  `products/tracker17/docs/SDD.md` § 3, or the other Accepted ADR-0001 to ADR-0009 decisions goes
  false: these already place assignee rules/list state in the existing parts (SDD § 3, DR-4;
  `products/tracker17/docs/SDD.md:L240-L240`), require whole-state saving (ADR-0004 § Decision) and permit the existing import
  edges (NFDR § 1.2). No record is edited here.

## Architect Review Notes

Architect decisions below were made on 2026-10-11. They settle structure left open by the spec;
they introduce no additional operator capability.

- **(b) Addresses and exact removal:** Choose `/people`, `/assignees` and `/assignees/remove`,
  passing names in the form/query rather than interpolating them into paths. CP-81 delegates the
  page address; CP-88/95 require exact names, including spaces and markup. This keeps addressing
  separate from matching and needs no stored assignee identity.
- **(b) Ordering and compatibility by construction:** Use an ordered immutable tuple in state and
  an array on disk, with append/remove operations preserving the sequence. CP-82 is then an
  explicit state invariant. Give the new state/restore arguments empty defaults to preserve the
  existing constructor and restore callers (`domain/state.py:L13-L25`), while CP-100 authorizes
  only the missing-list read case and CP-101 rejects malformed present lists. A successful project
  create also writes the complete state; no migration or write during load is introduced.
- **(b) Removal focus and stale history:** Choose the Assignees sheet's heading as CP-94's target;
  it exists for populated and empty lists, so removing the last name and stale removal have a
  stable target. Use that heading also when a later outcome GET can no longer find the named row,
  retaining the historical line without changing data (SDD § 4 RT-7/RT-8,
  `products/tracker17/docs/SDD.md:L309-L329`). Recognized outcome precedence is refusal, failure,
  then success (added before removed if both are present); unknown codes stay plain, extending the existing query-handling shape
  (`web/routes.py:L153-L174`, § _projects_page).
- **(b) Accessible-name uniqueness:** Include the row ordinal in Remove's accessible wording as
  well as the exact name. CP-88 allows distinct values differing only in repeated spaces, while
  CP-83 requires distinct accessible names. The ordinal makes uniqueness explicit regardless of
  whitespace folding by an accessibility consumer. Ordinal IDs and wording are per render; they
  are never saved identities. The wording remains the text record's to author.
- **(a) Existing assertion changes:** CP-104 forbids weakening tests, but CP-80 and the enriched
  saved form invalidate the old exact one-link/two-key expectations. § 5 names each replacement
  and the clause it continues proving, with stronger full-header/current-shape checks and the
  unchanged not-found body/legacy-read assertions. Leaving those literal expectations intact
  would contradict the same spec's new feature; removing their contracts is not the resolution.
- **Delegated reviews — pass:** QC-5 (typed refusal mapping), QC-8 (no web outcome store), QC-12
  (no unpaid part), QC-20/21/22/23 (no wording in domain and no rules in outer parts), QC-25/27
  (format and interface replacement remain separated), QC-36 (one escaping function), QC-41
  (no account/key/secret), QC-46 (only DR-4 names added) and QC-60 (Python 3.11 design floor)
  are satisfied by the placements/contracts above, against `docs/nfdr.md` § 1.1, § 1.3/1.4,
  § 2, § 4 and § 8 (`L55-L67`, `L79-L85`, `L114-L120`, `L160-L207`, `L270-L275`,
  `L319-L324`, `L378-L383`, `L463-L467`). QC-24 and QC-26 are not triggered: neither main nor
  the saving protocol changes. No new language/library feature or dependency is needed.
- **QC-40 — pass with the existing dated browser exception:** Read all 15 locked package/version
  pairs from `tests/requirements.txt:L4-L18`; the per-version sources and actual output field from
  the 2026-10-11 check are in the table below. This is the scope of that check,
  not a claim that no advisory can exist elsewhere. No pin or lock format changes. The cached
  Chromium build was read with `plutil -extract CFBundleShortVersionString raw
  '~/Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for
  Testing.app/Contents/Info.plist'`, output `153.0.8010.12`. Google's desktop security release of
  2026-09-15 lists critical fixes in 153.0.8010.47/.48
  (https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0541751186.html).
  On this comparison the cached build predates those fixes; NFDR RN-33's owner-recorded
  2026-10-10 to 2026-11-07 exception covers this exact build, so it does not block this review
  (`products/tracker17/docs/nfdr.md:L952-L964`, § RN-33). The project has no local installed
  Playwright on `python3`'s path (`importlib.util.find_spec('playwright')` returned `None`), so no
  browser was launched and no installed-library/build pairing or browser test success is claimed.
  The dependency proof here is the unchanged pin review plus the observed cached build/exception.

QC-40 package review evidence, read 2026-10-11:

| Locked pin | Per-version source | Output field |
|---|---|---|
| `ast_serialize==0.12.1` | https://pypi.org/pypi/ast_serialize/0.12.1/json | `vulnerabilities: []` |
| `greenlet==3.5.6` | https://pypi.org/pypi/greenlet/3.5.6/json | `vulnerabilities: []` |
| `iniconfig==2.3.1` | https://pypi.org/pypi/iniconfig/2.3.1/json | `vulnerabilities: []` |
| `librt==0.16.0` | https://pypi.org/pypi/librt/0.16.0/json | `vulnerabilities: []` |
| `mypy==2.4.0` | https://pypi.org/pypi/mypy/2.4.0/json | `vulnerabilities: []` |
| `mypy_extensions==1.1.0` | https://pypi.org/pypi/mypy_extensions/1.1.0/json | `vulnerabilities: []` |
| `packaging==26.3` | https://pypi.org/pypi/packaging/26.3/json | `vulnerabilities: []` |
| `pathspec==1.1.1` | https://pypi.org/pypi/pathspec/1.1.1/json | `vulnerabilities: []` |
| `playwright==1.63.0` | https://pypi.org/pypi/playwright/1.63.0/json | `vulnerabilities: []` |
| `pluggy==1.6.0` | https://pypi.org/pypi/pluggy/1.6.0/json | `vulnerabilities: []` |
| `pyee==13.0.1` | https://pypi.org/pypi/pyee/13.0.1/json | `vulnerabilities: []` |
| `Pygments==2.21.0` | https://pypi.org/pypi/Pygments/2.21.0/json | `vulnerabilities: []` |
| `pytest==9.1.1` | https://pypi.org/pypi/pytest/9.1.1/json | `vulnerabilities: []` |
| `ruff==0.16.10` | https://pypi.org/pypi/ruff/0.16.10/json | `vulnerabilities: []` |
| `typing_extensions==4.16.0` | https://pypi.org/pypi/typing_extensions/4.16.0/json | `vulnerabilities: []` |

## Cold-read result

change_design: clean.

Placement and transitive impact are covered by § 2; the contracts and their dependency order are
§ 3; § 5 maps E1 to E26 and the rule-edge pass, including assertions re-proved; each sub-job has a
§ 4 strategy row. Observable choices and delegated reviews are recorded above. The records section
retains its conditional proof boundary, and `Publishes text:` is settled. This is the architect's
document review of 2026-10-11, not a suite or browser verdict.
