# Change Design — a project's Summary view with plain counts

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the Tasks and Summary links beneath a project's name, both views' page titles, the Summary's group headings and count labels, its first-task invitation and link, and the timed run's Summary fixture and result lines

---

## 1. Change Summary

This blueprint places the Summary computation, its application read, its page and its proof for
`tracker17 · tobiishi · 2026-10-28_summary-page`. The sibling `change_spec.md` owns CP-490 to
CP-512 and the Examples; the sibling `change_request.md` owns the request. The design adds no
count links, cross-project summary, editing action or saved field.

The architectural decision is to add `domain/summary.py`, expose its immutable result through
`application`, and render it at `GET /projects/{id}/summary` through the existing `web` request
path. Summary rules belong to `domain`, page reads and the clock to `application`, and addresses
and HTML to `web` (products/tracker17/docs/SDD.md § 3, parts table and SM-1/SM-2:L198-L227).
All product-relative paths below are beneath `products/tracker17/` in the change worktree.

The artifact's home is the change-unit folder under the instance structure's § 2,
`journey/tobiishi/<key>/`, which names `change_design.md` in its change arc
(core/doctrine/setup/kensaiapp_structure.md:L2186-L2193).

## 2. Blast Radius

The owning parts are the SDD § 3 rows, rather than individual Python files; NFDR § 1.2 uses
the same import boundaries (docs/SDD.md § 3:L198-L233; docs/nfdr.md § 1.2:L145-L176).

| Module | Status | What changes |
|---|---|---|
| `domain/` | Modified | The `domain` part owns all Summary logic: project scope, every aggregate, zero rows, open-task membership, exact assignee identity and row order. Add `summary.py` and public re-exports in `__init__.py`. Reuse `filtering.py`, `due_dates.py`'s existing overdue decision through filtering, and `TaskStatus.is_open`; those existing implementations need no edits. |
| `application/` | Modified | The `application` part owns `Tracker.project_summary`, one local-date clock read per call, the current-state read and re-exporting the Summary values for `web`. No aggregate, ordering, HTML, cache or save is owned here. |
| `web/` | Modified | The `web` part owns the new GET route, its existing missing-project response, the Summary renderer, the shared project-view links, both project-view titles, escaping, and stylesheet rules for wrapping Summary groups and accessible links. Existing task-page rendering, move responses and list choices remain their existing contracts. |
| `persistence/` | Unchanged | The read adds no saved field, file access or format change. |
| `main.py` | Unchanged | The existing Tracker and Site wiring suffices; no new collaborator or clock is constructed. |
| `errors.py` | Unchanged | No new refusal or base error is needed. |
| `tests/timed_run.py` | Modified | Extend the existing test measurement with a final Summary block; this is test instrumentation, outside the SDD's production parts, per docs/nfdr.md § 9, “Outside the layers”. |
| `tests/` | Modified / new test modules | Add the § 5 proofs and update the explicitly released assertions from change_spec.md, Locked Answers (f-1) to (f-5). |

The transitive callers of `domain` are `application` and `persistence`; callers of `application`
include `web` and `main` (docs/SDD.md § 3, “The direction of dependence”:L233-L235).
The new interfaces are additive. No existing constructor, list method, entity, saver or clock
signature changes, so `persistence` and `main` need no call-site change. Every existing public
export remains available. No forbidden import edge is added.

## 3. Sub-jobs

### Sub-job A — `domain/`

**Scope:** Add the pure computation in `domain/summary.py` and its re-exports, with its layer-1
proof and the architecture assertions that admit this newly landed feature.

**Exposes:** `summarize_project(state: TrackerState, project_id: int, today: date) ->
ProjectSummary | None`. A missing project returns `None`, distinct from a present empty project.
The result includes its current `Project`, so a caller never has to join independently read
project metadata to the counts. It contains these frozen, tuple-backed values:

| Value | Fields and contract |
|---|---|
| `StatusCount` | `status: TaskStatus`, `count: int`. |
| `PriorityCount` | `priority: Priority`, `count: int`. |
| `AssigneeCount` | `assignee: str \| None`, `count: int`; `None` identifies the actual unassigned bucket, never a display string. |
| `ProjectSummary` | `project: Project`, `total: int`, `status_counts: tuple[StatusCount, ...]`, `priority_counts: tuple[PriorityCount, ...]`, `overdue: int`, `no_due_date: int`, `assignee_counts: tuple[AssigneeCount, ...]`. |

Every count is a nonnegative integer. The tuples carry the order CP-496/CP-500 require; the page
does not sort them. The computation explicitly enumerates statuses and priorities in their
required order and supplies zeros for absent values. Listed assignees retain `list_assignees`
order. Only unlisted names found on this project's open tasks are added, ordered by the pair
`(name.casefold(), name)`, followed by the `None` bucket. Exact-name equality determines bucket
identity; case folding is used only for ordering. These are architect decisions of 2026-10-28
to realize CP-496/CP-499/CP-500 by construction.

Reuse `filter_project_tasks` for the whole-project selection and the status, priority and
overdue selections. The public filter entry already takes `today`, narrows one project's tasks
and delegates overdue matching to `is_overdue` (domain/filtering.py, `filter_project_tasks` and
`_matches`:L149-L158,L280-L288). Use its returned counts rather than reimplementing those
predicates. The no-due-date and per-assignee aggregates use the whole-project selection; open
membership reuses `TaskStatus.is_open` (domain/tasks.py, `TaskStatus`:L54-L65). Never send an
unlisted assignee through the assignee filter: that filter refuses unlisted names
(domain/filtering.py, `_assignee`:L254-L257), while CP-499 requires counting them.

The domain carries identifiers and raw values, never the label `(unassigned)` or other page
wording. A real name spelled `(unassigned)` and the `None` bucket remain separate rows. No sort
rule for task lists is copied or changed. The Summary does not depend on task-list order.

The entry docstring names FR-38, the overdue and trace requirements, all participating
application/web modules and all checking test modules as they exist at completion. Register
`summary` in the trace test and replace the architecture assertion excluding `summary.py`
with a positive landed-feature assertion, as change_spec.md CP-504 and Locked Answer (f-5)
require. Participants are named only once their paths exist; the final trace covers every
participant. `__init__.py` contains only re-exports and initialization, per
core/doctrine/engineering/languages/python/layout.md § `__init__.py`.

**Depends on:** none; the filter, overdue, task and assignee surfaces already exist at the cited
entry points.

### Sub-job B — `application/`

**Scope:** Add `Tracker.project_summary(project_id: int) -> ProjectSummary | None` and expose
`ProjectSummary`, its row values and their existing enum/project types through the application
public surface. No separate application projection is needed.

**Exposes:** A read of current state with exactly one `Clock.now()` call, converted to the
machine's local date, passed to A. A repeat call recomputes from current state and the new call's
date. A missing identity returns `None`; a present empty project returns its zero result. The
method neither invokes `Saver` nor assigns state or stores a result between requests. This uses
the local-date convention of the existing Tracker list reads
(application/tracker.py, `project_tasks` and `_read_list`:L245-L255,L298-L309).

**Depends on:** A's result and pure function.

### Sub-job C — `web/`

**Scope:** Add `GET /projects/[0-9]+/summary` as `PAGE` in `ROUTES`, dispatch it through
`Site.handle`'s existing checks and request lock, and add `pages.summary_page(summary:
ProjectSummary) -> str`. Add one shared project-view link renderer used by `project_page` and
`summary_page`; change only the project list's title to the Tasks form.

**Exposes:** `/projects/{id}` remains Tasks, `/projects/{id}/summary` becomes Summary, and both
links use these identity-based addresses without query or fragment. The Summary handler calls
B once, answers a present result as HTML 200, and maps `None` to the existing project not-found
page and 404. Reuse the existing digit-to-identity handling, including an identity too long for
Python to parse; no new request-refusal type is introduced (web/routes.py, `_identity` and
`_project_named_by`:L340-L350).

Place the pair immediately after the project heading, before its description or outcome line,
in every state `project_page` renders. This covers plain, empty, filtered, sorted, no-match,
refused, failed and move-confirmation Tasks pages without duplicating the pair in action
handlers. Tasks clears all choices by linking to the base project address. Preserve action
focus, accessible descriptions, 202/no-store move handling and existing completion/refusal
strings; the pair introduces no new autofocus. `summary_page` uses `_document` for the site
header, English language and escaped title (web/pages.py, `_document`:L400-L420).

Render `total` first, then all status rows, all priority rows, overdue and no-due-date, then the
ordered assignee rows. Group the rows using the existing design's wrapping, two-column Summary
sheets; no task-table horizontal-scroll exemption applies to this surface
(docs/DESIGN.md, “Summary”:L387-L388; docs/UXD.md UX-A7:L500-L504). Every count and row label is
plain text. The only links are the common header, the view pair and the empty Summary's Tasks
invitation. No form, script, polling, filter, sort, rename or delete control is added. The
renderer uses `total == 0` solely to choose the CP-502 presentation, never to derive a count.

All project/assignee names pass through `_escape`, including the title via `_document`; preserve
spaces in displayed name cells/headings with the existing wrapping convention
(web/pages.py, `_escape`:L380-L382; web/style.css, `.pre-wrap`:L80-L83). Existing DESIGN tokens
and CONTENT patterns govern presentation and wording; this design fixes no new token or copy.

Summary queries do not apply a filter, sort or move to the read: this address represents only
the project's complete Summary. The base links carry no such parameters. No request-dependent
data is retained in `web`.

**Depends on:** B's read result and re-exports. Its new page tests consume A's values through
`application`, never by importing `domain` into production `web`.

### Sub-job D — `tests/timed_run.py`

**Scope:** Append a Summary measurement and its harness proof after the existing sort block,
using a separate saved-data fixture at 1,000 tasks with 20 comments each and the existing timer
and verdict conventions (change_spec.md CP-509; docs/nfdr.md QC-48:L435-L442).

**Exposes:** `measure_project_summary(*, site, saved_data, timer) -> list[Timed]` returns one
measurement of the Summary GET. Its label and fixture description are published text; their
words belong in `change_text.md`, alongside the new page's words. The fixture description
appears immediately before that row; no earlier output label or position changes. The
fixture description names the actual task/comment volume and ordinary text lengths read from
the loaded fixture. `main` includes the result in its exit verdict.

Time the single GET from immediately before `Site.handle` until its response returns. Saved
bytes and independent expected counts are checked outside that interval. A passing result needs
HTML 200 for the exact target project's Summary, its project name and Summary title, every
expected count/assignee row, plain count markup, unchanged saved bytes, and elapsed time strictly
less than 1 second. A wrong page, incorrect/missing count, mutation, refusal, failed response or
time at/above the limit fails. Expectations are computed in the harness from its loaded fixture,
not by calling A or B as an oracle. This proof code adds no production rule.

Do not reuse `_measure_apply_and_reload` unchanged: its successful-Apply predicate requires
`id="filter-count"`, which a Summary must not need (tests/timed_run.py,
`_measure_apply_and_reload`:L960-L1008). No filtered-list marker or extra GET is added to make
the Summary fit that predicate.

**Depends on:** C's real route and B's read; it uses existing persistence only as a test fixture.

**Build sequence:** A → B → C → D, from the contracts each exposes. The trace's completed list
of checking paths follows those files' existence; this is not an additional production module.

**Atomic-landing edges:**

- A's module + its landed-feature/shape assertions — no green point with `summary.py` present
  while `test_shapes` still excludes it or the trace still treats it as unlanded
  (tests/architecture/test_shapes.py, `test_only_the_task_features_are_added_to_domain`:L175-L193;
  tests/architecture/test_trace.py, `LANDED_FEATURE_WORDS`:L22-L34).
- C's project-view links/titles + their released compatibility assertions — no green point with
  the new title/link while the old title or closed href set remains asserted (change_spec.md,
  Locked Answers (f-1)/(f-2):L139-L140).
- C's route + its route sample — no green point when the enumerated route set differs from
  `SAMPLE_ADDRESS` (tests/integration/test_routes.py,
  `test_every_route_leaves_state_and_headers_as_the_rules_say`:L302-L305).
- D's final block + the whole-run ordered labels and injected timer readings — no green point
  with the block appended and the old exact output/timer sequence still expected
  (tests/integration/test_timed_run.py, `_run_readings` and
  `test_timed_run_appends_exactly_three_ordered_action_blocks`:L2079-L2088,L2112-L2123).

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — Summary computation | Compose public project-filter selections for total/status/priority/overdue; aggregate open assignees from the whole-project selection so removed names remain countable. Keep bucket identity separate from its label, and return ordered immutable rows. |
| B — Tracker read and exports | None |
| C — route, page, shared navigation and CSS | Use one project-view link renderer at the shared project-page assembly point. Summary sheets wrap instead of inheriting the task-table minimum widths and scroll container. |
| D — timed Summary GET | Measure one read; check saved bytes and independently derived page expectations outside the interval. The existing filter Apply predicate is not a Summary predicate. |

No write to a repository outside the instance/product worktree is part of this design.

## 5. Test Additions

The row IDs below also supply the Example and rule-edge mapping. All new test modules name the
requirements or acceptance criteria they check, per change_spec.md CP-504. The existing layers
and tools are docs/nfdr.md § 9's; no new test dependency is proposed.

| Row / sub-job | Test file | What to add / modify |
|---|---|---|
| T01 / A | `tests/unit/test_summary.py` (new) | Layer 1: CP-507's one mixed Alpha/Beta fixture, with the five-task Example's exact total, all status/priority counts, overdue, undated and every assignee row/order asserted. Assert both sum identities and exclusion of Beta. No file or clock. CP-496–CP-499, CP-507. |
| T02 / A | `tests/unit/test_summary.py` | Empty project with listed names; empty project with an empty assignee list; populated project missing some statuses/priorities. Every required zero row remains present and `None` is last. A missing project returns `None`. CP-496, CP-499, CP-502. |
| T03 / A | `tests/unit/test_summary.py` | Listed insertion order deliberately differs from alphabetical order; unlisted `zed`, `Amy`, `amy` stored in another order; exact case and whitespace identity, repeated tasks of one name, names on only closed tasks or only Beta, and a listed literal `(unassigned)` alongside real unassigned tasks. Assert exact rows, counts and order, no accidental merging or omitted zero. CP-499–CP-500, Locked Answer (b-5). |
| T04 / A | `tests/unit/test_summary.py` | Fixed supplied date: due yesterday/open, due today/open, undated/open, and due yesterday in each closed status. Undated tasks in every status count toward no-due-date. Input state remains equal after the read, result/rows are frozen, and no displayed label is stored as unassigned identity. CP-497–CP-498, CP-506. |
| T05 / B | `tests/integration/test_summary_tracker.py` (new) | Layer 3: one injected clock read, local-date conversion (an offset instant with a different UTC date), different result after the clock advances, zero saver calls, unchanged current state and result recomputed after an existing task/assignee action. Missing versus empty projects and unchanged entity metadata are distinct. CP-493–CP-494, CP-497. |
| T06 / B+C | `tests/integration/test_summary_routes.py` (new) | CP-508's clock-injected agreement fixture: list marks only the open task due yesterday; overdue filter returns only that task; rendered Summary overdue is 1. Include open due today, closed `done` and `cancelled` due yesterday and an undated task. No product-module patch. CP-497, CP-505, CP-508. |
| T07 / C | `tests/integration/test_summary_routes.py` | GET Summary returns 200 HTML for the requested project; repeat/reload three times leaves all state and saves unchanged. Queries carrying filter/sort/move choices cannot narrow or mutate its complete counts. Missing and huge unparseable project identities use the existing 404/title. Before/after renamed-state fixtures with the same identity keep both addresses and show the new name, without adding a rename operation. CP-490, CP-493–CP-495. |
| T08 / C | `tests/integration/test_summary_pages.py` (new) | Layer 4: ordered complete count rows, numerals including 0, total first and assignees last, shared header, exactly one correct title, English language, no form/script/refresh, and exactly CP-503's allowed links. No row label or count is an anchor or other control. Empty Summary keeps zero rows and invitation linking to base Tasks. CP-491–CP-496, CP-502–CP-503, CP-512. |
| T09 / C | `tests/integration/test_summary_pages.py` | Project/assignee names containing `<`, `&`, `"`, spaces and long text remain exact text in heading, title and cells, with no inserted markup/attributes. A name `(unassigned)` and `None` render as two distinct rows. Check Summary/Tasks titles with surrounding spaces and task titles unchanged. CP-492, CP-501. |
| T10 / C | `tests/integration/test_summary_routes.py` | Matrix of plain, empty, filtered, sorted, combined choices, no match, filter refusal, sort refusal, add/move completion, add refusal/save failure, cancellation confirmation and backed-out/refused move pages: ordered view pair under the project heading, Tasks URL clears choices, correct Tasks title. Retain prior outcome strings, focus target, 202/no-store and ordinary response contracts. CP-491–CP-492. |
| T11 / C | `tests/integration/test_pages.py`; `tests/integration/test_task_pages.py` | Replace only the two old project title expectations named by Locked Answer (f-1). Expand the header test's href set for the new project Summary URL and include Summary among the page builders it checks. Retain exactly one title, exact header links, valid internal destinations, the empty Tasks invitation and no rename/delete text. Preserve task-page title assertions. CP-492, CP-502. |
| T12 / C | `tests/integration/test_routes.py`; `tests/integration/test_summary_routes.py` | Add Summary to `SAMPLE_ADDRESS` for the exact route-set test and preserve all existing assertions. Check no saves/cookies, common CSP including frame-ancestors and no-script/self-only rules, no CSP meta tag, and unchanged host/fetch-site gate for the new route (including none, absent, cross-site and same-site marks). Keep the existing outbound-connect audit over the enlarged route set. CP-510. |
| T13 / A | `tests/architecture/test_shapes.py`; `tests/architecture/test_trace.py`; existing import/reach walks | Change only the released `summary.py` absence assertion to positive presence and add `summary` to landed words. Retain exact saved-state fields, excluded later features where any remain, real path/requirement checks, and all import/reach/frozen walks. Add a Summary-entry assertion requiring FR-38 and its real participants/checkers, rather than relying only on generic path existence. CP-504–CP-506. |
| T14 / D | `tests/integration/test_timed_run.py` | Real Summary at 1,000 × 20 passes; injected timer below 1 passes, exactly 1 and above 1 fail. A wrong Tasks/project page, 404/forbidden/failed response, missing or wrong row, linked count, or changed saved bytes fails even when fast. Use supplied Site/timer/saver seams or a wrapper handed into the harness, never patch product-module names. CP-509. |
| T15 / D | `tests/integration/test_timed_run.py` | Append Summary fixture+measurement labels after every existing block, preserving all old labels/positions and statuses. Extend `_run_readings` and every whole-run caller to supply the Summary interval; include slow/failed Summary in exit status. The new fixture stays separate from every old fixture and product data. Report the loaded fixture's volume and text lengths. CP-509 and Locked Answer (f-4). |
| T16 / C | `tests/e2e/test_summary.py` (new) | Layer 5 through the existing started tracker/Chromium harness: Alpha Tasks → Summary → Tasks, both titles and pairs, all counts as plain numbers, no automatic data update, empty project zeros and first-task invitation; reload saves nothing. Navigate from a scrolled Tasks page and assert Summary starts at the top. CP-494, CP-511. |
| T17 / C | `tests/e2e/test_summary.py` | Drive typed special-character names and verify exact visible text/title with no markup injection. Keyboard Tab/Enter reaches and activates both view links with visible focus. At 1280 pixels and 400% browser zoom, Summary groups and long names reflow without page-level horizontal scrolling; verify link targets meet 24 × 24 CSS pixels or the named WCAG exception. Retain all existing browser tests. CP-501, CP-512. |

### Examples → proof rows

The twenty Examples are identified by their order in the sibling `change_spec.md` Examples
table; the short labels below locate each scenario without duplicating its expected values.

| Example | Proof |
|---|---|
| 1 — Alpha Tasks | T10, T11, T16 |
| 2 — Tasks clears the todo filter | T10, T16 |
| 3 — follow Summary | T07, T08, T16 |
| 4 — padded project name | T09, T11 |
| 5 — unchanged task page | T09, T11 and existing task-page assertions |
| 6 — renamed Alpha | T05, T07 |
| 7 — reload three times | T07 |
| 8 — missing project | T07 |
| 9 — mixed five-task Alpha/Beta fixture | T01 |
| 10 — both total identities | T01 |
| 11 — Amy/amy/zed order | T03 |
| 12 — overdue agreement | T04, T06 |
| 13 — typed markup characters | T09, T17 |
| 14 — empty Gamma | T02, T08, T16 |
| 15 — existing empty Tasks invitation | T11 |
| 16 — no linked counts/labels | T08, T14, T16 |
| 17 — suite, module and pointer | T13 plus the suite gate below |
| 18 — single overdue decision | T06 and A's composition through the public filter |
| 19 — appended timed output | T14, T15 plus the timed command below |
| 20 — 400% zoom | T17 |

### Rule-implied edges and retired assertions

Every CP-490–CP-512 rule is covered by T01–T17: T07/T10 cover 490 and 493/495; T08–T11/T16
cover 491/492/494; T01–T04/T06 cover 496–500; T09/T17 cover 501; T02/T08/T11/T16 cover 502;
T08/T14/T16 cover 503; T13 covers 504/506; T06 covers 505/508; T01 covers 507;
T14/T15 cover 509; T12 covers 510; T16 covers 511; T08/T17 cover 512.
The no-task/no-name state, listed-zero state, only-closed removed names, other-project-only names,
case ties, literal `(unassigned)`, missing/oversized identity, midnight date change, stale rendered
data and all Tasks outcome pages have explicit rows above. No Example-only coverage assumption is
needed.

T11 re-proves both retired project-title clauses and the widened internal-link clause. T12
re-proves exact route enumeration. T15 re-proves exact ordered output and failure propagation.
T13 re-proves the positive feature set and saved-state shape after retiring only the absence of
the newly requested module. No other existing assertion or contract is retired; these releases
are exactly change_spec.md Locked Answers (f-1)–(f-5):L139-L143.

The completed change's gates are `pytest products/tracker17/tests/` from the instance worktree
(project.md, `Test command`), `python3 tests/timed_run.py` from the product root (CP-509), and
NFDR QC-62's product-root commands: `ruff format --check .`, `ruff check .`, and
`mypy main.py errors.py domain application persistence web` (docs/nfdr.md QC-62:L509-L522).
No suite or acceptance run is performed by this design stage.

## Records this change makes false

None — read `docs/adr/README.md`, ADR-0001 through ADR-0011, `docs/nfdr.md`, `docs/fdr.md` and
`docs/SDD.md` § 3. The summary computation and application/web seams fit the already declared
parts; the new GET changes no import restriction or saved-state sentence (SDD § 3:L198-L258;
NFDR § 1.2:L145-L176). ADR-0006 is superseded, not an active decision
(docs/adr/0006-last-action-travels-in-the-page-address.md, Status:L3).

The pre-existing linked-count and unreadable-data gaps remain the sibling
`deferred_decisions.md`'s entries. SDD § 6 S-6's count-link requirement is still undelivered,
not a changed architectural decision (docs/SDD.md § 6 S-6:L977-L1000; change_spec.md,
Out of Scope:L118-L126). This design changes no record or deferred entry.

## Architect Review Notes

Architect decisions and reviews below are dated 2026-10-28.

- **(b) Stable page address and read result:** Choose `/projects/{id}/summary` and a result
  containing its `Project`, with `None` for no such identity. The spec leaves the address and
  internal read shape open (CP-490); one state snapshot supplies both metadata and counts without
  a second read or cached projection. Existing Tasks addresses and all old signatures remain.
- **(b) Ordering and identity by construction:** Return ordered status/priority/assignee tuples;
  explicitly sort only removed names with case-folded/exact-text tie keys. Keep unassigned as
  `None`. This realizes CP-496/CP-500 and Locked Answer (b-5) without relying on task storage order
  or conflating a real name with its displayed bucket label.
- **(b) Shared-rule reuse without changing the assignee filter:** Use the public project filter
  for scope/status/priority/overdue, and existing `is_open` for assignee aggregation. Counting a
  removed name cannot use the validated assignee filter, whose refusal remains required outside
  this Summary (domain/filtering.py, `_assignee`:L254-L257; change_spec.md CP-499/CP-505).
- **(b) Read-only Summary and rename continuity:** Ignore list/action choices on the Summary
  address and retain no web state. Prove new names with successive same-identity state fixtures;
  add no rename endpoint. These choices realize CP-493/CP-494 without enlarging product scope.
- **(b) One timed read:** CP-509 adds an opening operation, not an Apply interaction. Use one
  GET and its own success predicate/fixture+measurement block, preserving every old timed line.
  Carry CP-509 as specified, including the already recorded override in change_spec.md Locked
  Answer (e-2); no additional reading of the request is set aside here.
- **(e) Measurement code placement:** No SDD production part owns test measurement. Keep D in
  the existing `tests/timed_run.py`, which NFDR § 9 explicitly places outside the layers, rather
  than adding a production timer or instrumentation part (docs/nfdr.md § 9:L561-L566).
- **QC-5 review — pass:** No new refusal is introduced. Missing projects reuse absence and the
  existing not-found response; existing typed refusal paths and application exports are retained.
  No branch on a refusal's message is proposed (docs/nfdr.md QC-5:L58-L67).
- **QC-8, QC-20, QC-21 and QC-23 review — pass:** A owns every aggregate and membership/order
  decision, accepts today and returns immutable values. B only reads its current state and clock.
  C formats those results, reaches no clock/file and stores no query/result between requests.
  The application returns a domain value through its exports; production web imports no domain
  code (docs/nfdr.md § 1.2 and § 1.3:L145-L224).
- **QC-12 and QC-27 review — pass:** One required feature entry and one renderer add no new
  production part, generic reporting framework, cache or persistence seam. Shared navigation
  stays inside web, and no HTML leaks into the inner parts (docs/nfdr.md QC-12:L137-L143;
  QC-27:L240-L245; SDD § 3:L198-L233).
- **QC-36 review — pass:** Every typed name enters the existing `_escape`; `_document` escapes
  the composed title. No raw-name interpolation into markup or address is introduced, and
  identity-only links need no typed-name encoding (web/pages.py:L380-L382,L400-L420;
  docs/nfdr.md QC-36:L307-L315).
- **QC-41/QC-46 and conditional reviews — pass / not triggered:** The design adds no credential,
  saved field, saver-contract change, file format, startup choice or runtime/test dependency.
  QC-22/QC-24/QC-25/QC-26's conditional persistence/main/saver reviews therefore require no
  changed implementation (docs/nfdr.md § 1.3–1.4:L213-L245; QC-41:L357-L362;
  QC-46:L415-L421).
- **QC-60 review — pass at design:** The contracts require only existing enums, frozen
  dataclasses, tuples, dates and case folding; no language/library feature beyond the declared
  Python 3.11 floor is needed (docs/nfdr.md QC-59/QC-60:L498-L506). This is a design review,
  not a claim that a 3.11 suite ran.
- **Language resolution:** Python — resolution step 1, `system/projects/tracker17/project.md`,
  `Languages: Python`. Opened `core/doctrine/engineering/languages/python/README.md`, its layout,
  conventions and quality-gates answers, and the routed `testing_python.md`; product decisions
  remain the narrower owner (core/doctrine/engineering/languages/README.md, “Precedence”).
- **QC-40 review — pass under the existing dated browser exception:** On 2026-10-28,
  version-specific PyPI JSON requests for all fifteen pins in `tests/requirements.txt` returned
  `vulnerabilities: []` at each primary endpoint in the evidence table below. This states the
  returned advisory metadata, not a guarantee of no vulnerability. The installed Chromium 1243
  app's metadata read returned `153.0.8010.12` (command and output below), matching the pin's
  browser described by https://pypi.org/pypi/playwright/1.63.0/json. Google's September release page publishes critical
  browser fixes, so this review does not treat that build as clean
  (https://chromereleases.googleblog.com/2026/09/, “Stable Channel Update for Desktop”,
  2026-09-22). NFDR RN-33's owner's exception covers that exact build through 2026-11-07 and
  explicitly permits reviews on/before that date (docs/nfdr.md, RN-33:L1028-L1036). No pin or
  exception is changed by this design. The dated verdict relies on the inspected September
  notices and the build-specific exception; it makes no claim of a complete advisory inventory.

### QC-40 evidence read on 2026-10-28

Every endpoint below returned `vulnerabilities: []` in the version-specific JSON response.

| Locked pin | Primary endpoint |
|---|---|
| `ast_serialize==0.12.1` | https://pypi.org/pypi/ast-serialize/0.12.1/json |
| `greenlet==3.5.6` | https://pypi.org/pypi/greenlet/3.5.6/json |
| `iniconfig==2.3.1` | https://pypi.org/pypi/iniconfig/2.3.1/json |
| `librt==0.16.0` | https://pypi.org/pypi/librt/0.16.0/json |
| `mypy==2.4.0` | https://pypi.org/pypi/mypy/2.4.0/json |
| `mypy_extensions==1.1.0` | https://pypi.org/pypi/mypy-extensions/1.1.0/json |
| `packaging==26.3` | https://pypi.org/pypi/packaging/26.3/json |
| `pathspec==1.1.1` | https://pypi.org/pypi/pathspec/1.1.1/json |
| `playwright==1.63.0` | https://pypi.org/pypi/playwright/1.63.0/json |
| `pluggy==1.6.0` | https://pypi.org/pypi/pluggy/1.6.0/json |
| `pyee==13.0.1` | https://pypi.org/pypi/pyee/13.0.1/json |
| `Pygments==2.21.0` | https://pypi.org/pypi/Pygments/2.21.0/json |
| `pytest==9.1.1` | https://pypi.org/pypi/pytest/9.1.1/json |
| `ruff==0.16.10` | https://pypi.org/pypi/ruff/0.16.10/json |
| `typing_extensions==4.16.0` | https://pypi.org/pypi/typing-extensions/4.16.0/json |

The installed browser metadata command and its actual output were:

```text
/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' '<a path on Eyal's machine> Chrome for Testing.app/Contents/Info.plist'
153.0.8010.12
```
