# Change Design — All tasks across every project

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the shared header, both not-found pages, and the All tasks heading, task table, empty state, controls, count, refusals and move outcomes

This blueprint owns the structure and interfaces for `tracker17 · tobiishi · 2026-10-28_all-tasks-list`.
Its behavioural source is that change's `change_spec.md`, CP-459–CP-489.
Product paths below are relative to `products/tracker17/` in the change worktree.

## 1. Change Summary

Add `GET /tasks` as the All tasks page, with the shared navigation and both not-found pages pointing
to it. Extend the scope of the existing filter and sort computations inside `domain`, project their
result through `application`, and reuse the controls, task-row presentation and move interactions in
`web`. This division follows `docs/SDD.md` § 3, “The parts”, and fulfils CP-461 and CP-480 without
another filter or sort implementation.

The address carries the same seven `filter_` keys and two `sort_` keys as a project's list
(`web/routes.py:179-220`, `_filter_input`, `_sort_input` and the carried-choice helpers).
Apply uses a GET form targeting `/tasks`; Clear links to `/tasks` with no query. Moves use the two
existing task move POST addresses, carrying a new closed destination value, `place=all_tasks`.
These are the architect's address decisions, 2026-10-28, within CP-461 and CP-475.

## 2. Blast Radius

Placement follows the owning parts in `docs/SDD.md` § 3; the complete module set and allowed import
edges are `docs/nfdr.md` § 1.2, QC-13–QC-19.

| Module | Status | What changes |
|---|---|---|
| `domain/` | Modified | **Rule core:** `filtering.py` gains whole-tracker scope and options; `sorting.py` applies the existing combined validation and ordering to that scope. Both project and All tasks entry points share the same validation, matching, options and ordering machinery. `__init__.py` re-exports the added entry points. Feature docstrings include FR-31 and the All tasks trace participants (CP-480, CP-481). |
| `application/` | Modified | **Actions and page data:** `tracker.py` adds `Tracker.all_task_list`, projecting the global selection through the existing `ProjectTaskList` and `TaskRow` values. Its one clock read supplies the selection and row markings. `__init__.py` remains the source of every type/refusal `web` uses (CP-480, CP-482; SDD § 3 SM-1, SM-2, SM-7). |
| `web/` | Modified | **Browser interface:** `routes.py` registers the page, dispatches the global read and carries the All tasks move destination through the existing move paths. `pages.py` builds the page, adds navigation and the project column, and shares controls, row and move rendering. `style.css` adds only the project-cell/layout hooks needed to apply DESIGN § Layout's wrapping and minimum-width rules to the extra column. No listener change (CP-459–CP-479). |
| `persistence/` | Unchanged | No saved-data field, format, saver contract or read-at-start change (CP-482). |
| `main.py` | Unchanged | The existing tracker, saver, clock and listener wiring serves the added read (SDD § 3 `main` row). |
| `errors.py` | Unchanged | Reuse the existing refusal hierarchy; no new refused condition (CP-474). |

The transitive consumers of `domain` include `application`, `persistence` and `main`, and of
`application` include `web` and `main` (NFDR § 1.2). The added entry points preserve the existing
project entry points, value fields and constructor contracts, so `persistence` and `main` need no
call-site change. `web` is included as a consumer of the added application read.

No new part, code module, saved field or dependency is introduced by this design.

## 3. Sub-jobs

### Sub-job A — `domain/`: one rule implementation, two list scopes

**Scope:** Extend `filtering.py` and `sorting.py`, with public exports in `domain/__init__.py`.
The project entry points retain their present argument and result contracts
(`domain/filtering.py:125-165`, `project_filter_options` and `filter_project_tasks`;
`domain/sorting.py:162-207`, `sort_project_tasks`).

**Exposes:**

| Entry point | Arguments | Result and refusal contract |
|---|---|---|
| `all_filter_options` | tracker state | `FilterOptions` for all tasks: total count, current assignees in their existing order, and exact distinct labels in code-point order from all tasks before filtering (CP-468). |
| `filter_all_tasks` | tracker state, `FilterInput`, supplied local date | `FilterSelection` across all tasks; the same `FilterRefused` and field refusal types as the project entry point (CP-469, CP-474). |
| `sort_all_tasks` | tracker state, `FilterInput`, `SortInput`, supplied local date | `SortedSelection` across all tasks; reuse `ProjectListRefused` as the combined refusal envelope, retaining both raw inputs and every problem in control order (CP-469, CP-474). |

Use shared scope-independent helpers within the two existing feature modules. Scope determines the
input task collection and options; it does not select a second validator, matcher or ordering rule.
Do not concatenate independently sorted project lists: CP-465 and CP-469 require one order across
projects. The existing `_ordered` explicitly establishes ascending task identity before
stable field sorting and partitions undated tasks last (`domain/sorting.py:235-252`); the global entry point uses that same
ordering operation. Created-time descending reverses identity order, rather than comparing recorded
timestamps (CP-469; ADR-0008 § Decision).

An empty global scope returns the default empty selection before either input is validated,
matching CP-466. A nonempty scope validates the filter and sort independently even when the filter
has problems or matches nothing, as `sort_project_tasks` does under its “checked independently”
contract (`domain/sorting.py:170-190`). Counts and count visibility remain domain results (CP-470, CP-471).

**Depends on:** none.

### Sub-job B — `application/`: the global page read

**Scope:** Add the read and share projection of a sorted selection or combined refusal with the
project read. Keep HTML, query keys and destination values outside this part (SDD § 3 SM-1).

**Exposes:** `Tracker.all_task_list(fields, *, sort_fields=NO_SORT)` returns `ProjectTaskList`.
The value retains every field defined by `application/tracker.py:67-90` (`ProjectTaskList`): whole-scope
`task_count`, ordered `rows`, `match_count`, validated filter and sort or `None`, both raw inputs,
ordered typed `problems`, assignees, labels and `count_requested`. Its existing name remains usable;
its documentation describes the scope supplied by the read rather than promising one project.

Each `TaskRow` remains a task plus its overdue flag. Resolve project display names through the
existing `Tracker.projects()` values and each task's `project_id`; no project name is saved or
copied into a task. One clock instant supplies one local date for selection and every row marking,
as `Tracker.project_task_list`'s current contract requires
(`application/tracker.py:249-262`; CP-479, CP-480).

A refusal is a page-read result with no rows, no count and no validated choices, retaining the raw
values and the unfiltered whole-scope options. A read never calls `_save_then_publish` or the saver
(CP-474, CP-482). `Tracker.move_task` and its save-before-publish contract stay unchanged.

**Depends on:** A's global selection, options and existing typed refusal envelope.

### Sub-job C — `web/`: page, navigation and move destination

**Scope:** Route and render All tasks and extend the shared presentation seams without changing the
project/task destinations. Use B's ordered rows and counts as given (CP-475, CP-478, CP-480).

**Exposes:**

- `GET /tasks` is a `PAGE` route answered directly with HTML. `/tasks/`, malformed task paths and
  every other unknown address retain their existing not-found handling (CP-460, CP-461).
- `pages.all_tasks_page` consumes the list read model, project values, existing allowed-moves
  callback, move outcome/interaction and any off-list task. It returns the whole document.
  Shared helper extensions default to the existing project behaviour so other callers retain
  their contracts (CP-462, CP-478).
- `place=all_tasks` is a destination discriminator, never a supplied return URL. It selects `/tasks`
  for a move, confirmation, back out, refusal and failure. The existing list discriminator still
  selects the task's project; the task/default case keeps its current landing. Both move POST
  routes retain their current paths (CP-475, CP-478).
- Retain `filter_status`, `filter_priority`, `filter_assignee`, `filter_label`, `filter_due_from`,
  `filter_due_to`, `filter_overdue`, `sort_field` and `sort_direction` using the existing request
  readers and carried-pair helpers. Preserve duplicate and empty values so domain validation sees
  exactly what was sent. Ordinary Apply/Clear carry no move-outcome state (CP-472–CP-475).

The page has the eight columns required by CP-462, with Project directly after Title. Each project
name links to `/projects/<id>` without choices. Reuse the common row, controls and move renderers,
parameterizing the page destination and optional project cell rather than copying their bodies.
The zero-task branch precedes controls and shows only its empty-state invitation under the heading;
the nonempty branches distinguish refused choices, no matches and a result with any owed count
(CP-464, CP-466, CP-470, CP-471, CP-474).

Before either move POST can open a confirmation or reach `Tracker.move_task`, validate the carried
choices through `all_task_list` for this destination. Typed problems redirect back to `/tasks` with
the raw choices and no pending confirmation. Reuse `_address` for every submission redirect
(CP-477; ADR-0011 § Decision).

For the landing page, reuse `_move_view` against the current task and then restrict confirmations
to the selected row identities. Derive 202 only from a confirmation actually rendered; the other
move pages are 200, all with `no-store`. Missing tasks retain the existing redirect/not-found
handling, including 404 without `no-store` for a missing confirmation target (CP-475, CP-478;
NFDR QC-63). Off-list outcomes use the existing outcome precedence and current task lookup,
testing membership in the selected identity set rather than repeating a filter predicate
(`routes.py::_off_list_task`; CP-476, CP-480).

For a visible row, use the existing status focus, in-place confirmation and restored-button focus.
For an off-list outcome, focus the results section and make the line its accessible description,
including the no-match state. A choice refusal owns the first refused field's focus and suppresses
list results. No line itself takes focus (CP-474–CP-476; SDD § 4 EX-4–EX-6, EX-14).

All published words come from the change's text artifact. Apply `docs/DESIGN.md` § Layout to the
header, wrapping controls, eight-column table and scroll container. Typed values pass through
`pages.py::_escape`, including project names in cells, titles and accessible descriptions
(CP-479; NFDR QC-36).

**Depends on:** B's global page read and existing application exports.

**Build sequence:** A → B → C, because each consumes the preceding interface. Additive entry points
and default-preserving presentation extensions leave a green landing point between these sub-jobs;
there is no atomic-landing edge. Extend the existing test modules listed below, so trace docstrings
can name real paths throughout the sequence.

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — shared filter/sort over two scopes | Select the scope once, then run the same validation/matching/ordering machinery. Reuse the explicit identity baseline and undated partition in `sorting.py::_ordered`; never merge per-project ordered results. |
| B — page read | None |
| C — page and moves | A closed destination discriminator feeds both move redirects and cancellation back-out forms. Apply the rendered-row visibility gate before choosing the confirmation response status. |

## 5. Test Additions

Each row below states the delta to existing test files; paths are product-relative. E1–E43 index
the spec's Examples in their existing order. CP-483 is covered collectively by T1–T15 and T19;
the other rule-implied edges are stated in the rows rather than limited to those Examples.

| Row / sub-job | Test file(s) | What to add / modify |
|---|---|---|
| T1 / C | `tests/integration/test_pages.py`, `tests/integration/test_people_pages.py`, `tests/integration/test_task_pages.py`, `tests/integration/test_people_routes.py` | CP-459, CP-487; E1–E2: shared header order on every page kind including All tasks, both not-found forms, confirmations/refusals/failures, and no header on unreadable data. Retain unrelated assertions. |
| T2 / C | `tests/integration/test_pages.py`, `tests/integration/test_task_routes.py`; `tests/e2e/test_first_project.py` | CP-460–CP-461, CP-487; E3–E6: both 404 forms keep one heading, one following paragraph with Projects then All tasks, no forms; header/total link counts adjusted. Only `/tasks` leaves the unknown-path cases; `/tasks/` and all other cases remain. Browser clicks Projects by name. Header link opens `/tasks`, 200 without redirect/save. |
| T3 / B, C | `tests/integration/test_sort_tracker.py`, `tests/integration/test_sort_pages.py`, `tests/integration/test_sort_routes.py` | CP-462–CP-465; E7, E9: two interleaved projects, every task once, exact default order 2,1,4,3, title/h1, eight column positions, project names and unfiltered project links, all existing task attributes/markers/allowed moves, no add/rename/delete/summary controls. |
| T4 / A, B, C | `tests/unit/test_filtering.py`, `tests/unit/test_sorting.py`; `tests/integration/test_filter_tracker.py`, `tests/integration/test_filter_pages.py`, `tests/integration/test_sort_routes.py` | CP-466; E10: no projects and only empty projects, each with absent, valid, invalid and repeated filter/sort inputs. Empty state has Projects link and no controls, refusal, table, count or filter wording. No saver call. |
| T5 / A, B, C | `tests/unit/test_filtering.py`; `tests/integration/test_filter_tracker.py`, `tests/integration/test_filter_pages.py` | CP-467–CP-468; E11–E12: nine labelled controls in order, one Apply and Clear, no Apply message; assignees in current-list order, exact distinct labels sorted by code point from every project before matching, including duplicates, case differences and labels only on excluded tasks. |
| T6 / A, B, C | `tests/unit/test_filtering.py`; `tests/integration/test_filter_tracker.py`, `tests/integration/test_filter_routes.py` | CP-469, CP-483; E13: each filter field alone, AND across fields, exact label/assignee matches, either/both range endpoints including equal inclusive endpoints, undated tasks against every range shape, AC-13 overdue cases with injected date, marking/filter agreement. Fixtures span at least two projects. |
| T7 / A, B, C | `tests/unit/test_sorting.py`; `tests/integration/test_sort_tracker.py`, `tests/integration/test_sort_pages.py`, `tests/integration/test_sort_routes.py` | CP-465, CP-469, CP-483; E7, E14–E15: every field in both directions, priority rank, case-insensitive titles, undated last in both directions, cross-project ties on every field, identical recorded timestamps and created-time ordering. Supply task tuples out of identity order to prove explicit ordering. Check a sort neither adds nor drops matches and filter+sort compose. |
| T8 / B, C | `tests/integration/test_sort_pages.py`, `tests/integration/test_filter_pages.py`, `tests/integration/test_sort_routes.py` | CP-470–CP-471; E16–E17, E23: filter, sort-only and combined counts, sort-only wording without a filter claim, explicit default sort still requesting a count, no count with no choice. Unknown single label yields no matches, not refusal. No-match state retains choices/Clear, no table/count/blank placeholder or global empty wording. |
| T9 / B, C | `tests/integration/test_sort_routes.py`, `tests/integration/test_filter_routes.py`, `tests/integration/test_filter_tracker.py` | CP-472–CP-473, CP-482; E18–E20, E36: exact address reload/bookmark/Back-equivalent GET, fresh link and Clear, 200 without redirect, unchanged state and no saver call. Re-read after a task change and injected local-date change to prove current-data/date recomputation rather than remembered choices. |
| T10 / A, B, C | `tests/unit/test_filtering.py`, `tests/unit/test_sorting.py`; `tests/integration/test_filter_routes.py`, `tests/integration/test_sort_routes.py`, `tests/integration/test_sort_pages.py` | CP-474; E21–E22: one case per existing refusal kind — reversed dates, unlisted assignee, unknown status/priority/overdue, invalid from/to dates, repeated value for each of seven filter fields and both sort controls, invalid sort field/direction. Preserve blanks/repeats/spacing; combine filter+sort failures to check complete control-order reasons, raw choices, first-field focus/description, Clear and no list/count/save. Validate sort even when a valid filter matches nothing. |
| T11 / C | `tests/integration/test_sort_move_routes.py`, `tests/integration/test_filter_move_routes.py`, `tests/integration/test_move_pages.py` | CP-475; E24–E27: with no choices, filter only, sort only and both, press every offered move, open cancellation, back out, confirm, stale/refused move and failed save. Check All tasks destination and all carried values, current status, one line, correct focus, 202 only for a rendered confirmation and otherwise 200, `no-store`, no `Clear-Site-Data`. Failure retains state and uses the existing console site without Python error text in HTML. Reload completed/failed/refused addresses saves nothing. |
| T12 / C | `tests/integration/test_filter_move_routes.py`, `tests/integration/test_sort_move_routes.py`, `tests/integration/test_move_pages.py` | CP-475–CP-476; E28–E29: task leaves a status filter; `done` and `cancelled` leave Overdue; include final matching task and other matches left. One off-list completion precedes table or no-match state, results section owns focus/description. Confirmation/back-out replay with a final task visible shows its status refusal; filtered-out final target shows the off-list refusal and no invented row/confirmation (review note below). Hidden or choice-refused rows never produce a pending confirmation. |
| T13 / C | `tests/integration/test_sort_move_routes.py`, `tests/integration/test_filter_move_routes.py` | CP-477; E30: invalid/repeated filter or sort on both initial and confirming move POSTs, including simultaneous problems. No save, status change or confirmation; All tasks renders ordered field reasons and retains the rejected choices. |
| T14 / C | `tests/integration/test_move_routes.py`, `tests/integration/test_sort_move_routes.py`, `tests/integration/test_filter_move_routes.py` | CP-478; E31–E32: project-list and task-page destinations unchanged; deleted All tasks move target follows the existing task-not-found path. Missing confirmation/back-out target gives 404 without move cache headers. |
| T15 / C | `tests/integration/test_filter_pages.py`, `tests/integration/test_sort_pages.py` | CP-479; E8: `<`, `&`, quotes in project names, task titles, labels and assignees remain text in cells, links, options, hidden carried values and accessible names. No script, and All tasks table uses the established wrapping/scroll classes. |
| T16 / A, B, C | `tests/architecture/test_trace.py`, existing import/shape tests | CP-480–CP-481; E34–E35: retain the pointer/import/shape assertions; update feature docstrings with FR-31, `application/tracker.py`, `application/__init__.py`, the participating web files and all test modules extended here that check the feature. All named paths exist. Review both list paths reaching the same validators, matcher, sort and overdue rule. |
| T17 / B, C | `tests/integration/test_routes.py`, `tests/integration/test_tracker.py` | CP-482, CP-485; E36, E39: route samples gain `GET /tasks`; retain the existing move samples and add cases exercising `place=all_tasks` beside them. Route-set equality remains. Exercise open/Apply/reload/Clear/refused choice: 200, no redirect/save/cookie, unchanged state, policy header. Audit-hook action sequence includes All tasks Apply and move; recording saver sees no reads and no saves for the global read. |
| T18 / C | `tests/e2e/test_filters.py`, `tests/e2e/test_sorting.py`, `tests/e2e/test_moves.py` | CP-479, CP-484; E33, E38: keyboard-only from a project's header to All tasks, apply a filter/sort and press a row move with scripting disabled. Verify retained choices and landing/focus; extend the existing pinned-browser confirmation history coverage to All tasks. |
| T19 / all | Existing files named by CP-487 | E41: change only the assertions CP-487 releases; re-prove three header links, two not-found main links, new navigation positions and the added route in T1–T2/T17. Retain the “rename”/“delete” prohibitions and People main-content “all tasks” prohibition. No other assertion is retired. |
| T20 / all | Existing full suite, `tests/timed_run.py` | CP-483, CP-486, CP-488–CP-489; E37, E40, E42–E43: the full suite and separate browser suite, unchanged timed run and its unchanged limit/row order, Ruff format/lint and mypy gates in CP-488, and Python 3.11 compatibility. No new timed row or dependency. A run outside the change worktree uses a fresh clone at the commit under test, as CP-488 requires. |

## Records this change makes false

None — read `docs/adr/README.md` and ADR-0001–ADR-0011 (ADR-0006 is superseded by ADR-0011),
`docs/nfdr.md` §§ 1–10, `docs/fdr.md` Rules and Out of scope, and `docs/SDD.md` § 3 and the S-5
contracts. The design adds the all-project list those records describe, within the existing parts,
imports, saved schema and runtime decisions. No record needs a correction because of this delta.

## Architect Review Notes

The architect made the following decisions on 2026-10-28.

- **Address and destination (b):** `/tasks` and `place=all_tasks` settle CP-461's open address and
  CP-475's return context. They extend the existing task-address family and closed destination
  handling in `web/routes.py::_move_task`; they add no arbitrary return address or new POST route.
- **Ordering by construction (b):** A single whole-scope selection reaches the explicit identity
  baseline in `domain/sorting.py::_ordered`. This implements CP-465/CP-469 across projects without
  depending on state tuple order, project enumeration or timestamps.
- **Replay when a final task is filtered out (a):** Read CP-475's “refusal beside the task's status
  in its row” as applying when that row is listed. For a final task excluded by the choices, keep
  the selected rows and use the existing off-list refusal above results. `web/routes.py:394-426` (`_move_view`) and `web/routes.py:508-560`
  (`_project_page`, `_off_list_task`) already combine row visibility with that outcome presentation.
  The unconditional-row reading would either show a nonmatching task against CP-469 or discard the
  choices against CP-475. The reading taken preserves both and gives the request the same moves
  and landings as a project's list. The set-aside absolute location is recorded in
  `deferred_decisions.md`; T12 proves both visible and excluded final-task cases.
- **Shared read value (b):** Reuse `ProjectTaskList` with scope-neutral documentation instead of a
  second projection type. Its fields already carry everything needed for CP-466–CP-474
  (`application/tracker.py:67-90`, `ProjectTaskList`). Project values reach the renderer separately, so
  no saved schema or existing constructor changes.
- **Delegated reviews — pass:** NFDR QC-5's by-type review uses the existing domain refusal classes
  and application re-exports, with no message inspection or application-defined refusal.
  QC-8, QC-20, QC-21 and QC-23 pass: only current state is retained, domain owns options/matching/
  ordering/counts, application only calls/projects, and web owns request decoding and presentation.
  QC-12 and QC-27 pass: three existing parts absorb this capability, with no new abstraction for
  an unreplaced interface. QC-36 passes: new project text uses the same `_escape` entry as other
  typed text. QC-41 passes: no secret, account or credential enters the design. These verdicts
  apply to the boundaries in §§ 2–3, against the named clauses in `docs/nfdr.md`.
- **Conditional delegated reviews:** NFDR QC-22, QC-24–QC-26 and QC-46 have no changed persistence,
  composition, save-contract or saved-field surface in § 2. QC-60 passes the design review:
  it requires no construct newer than the existing Python 3.11 floor; actual execution remains
  T20's check, not a result claimed here (`docs/adr/0002-standard-library-only-no-web-framework.md`
  § Decision; `pyproject.toml` `requires-python`). Language resolution is Python, step 1 from
  `system/projects/tracker17/project.md` `Languages:`; the packet opened is
  `<CORE>/doctrine/engineering/languages/python/README.md` and its seven concern destinations.
- **QC-40 — pass under the dated browser exception:** On 2026-10-28, the version-specific PyPI
  JSON endpoints returned `vulnerabilities: []` for all 15 exact entries of
  `tests/requirements.txt:4-18`:
  [ast_serialize 0.12.1](https://pypi.org/pypi/ast_serialize/0.12.1/json),
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
  [ruff 0.16.10](https://pypi.org/pypi/ruff/0.16.10/json) and
  [typing_extensions 4.16.0](https://pypi.org/pypi/typing_extensions/4.16.0/json).
  This is the index's advisory report, not a claim
  that unreported vulnerabilities do not exist. Microsoft's pinned browser manifest names
  Chromium and headless-shell 153.0.8010.12, revision 1243
  (https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/packages/playwright-core/browsers.json).
  Google's 2026-09-08 release publishes critical fixes in 153.0.8010.36/.37, including
  CVE-2026-87464 (https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0808145027.html).
  The browser therefore uses the owner's build-specific exception through 2026-11-07 in
  `docs/nfdr.md:1027-1041`, RN-33, “Dated exception to QC-40”. No pin, lock format or exception is changed.
- **Cold read:** All nine changing-mode checks hold for this blueprint: § 2 places every logic
  addition and covers consumers; § 3 gives interfaces before dependency order; § 5 maps all 43
  Examples and the rule-implied edges; the choices above account for divergences; the records
  section and text verdict are present. This change requires no write outside the instance and
  product worktrees. No implementation or acceptance suite was run by this architecture step.
