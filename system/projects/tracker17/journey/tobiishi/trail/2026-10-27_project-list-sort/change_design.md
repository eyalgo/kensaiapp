# Change Design — a project's task list sorts by one field

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the project's task list: sort control labels and choices, sort refusal reasons and the count when only a sort is applied; the timed run's sort fixture and timing lines

This blueprint owns the module boundaries, contracts and coverage for the sort change in
`tracker17 · tobiishi · 2026-10-27_project-list-sort`. The sibling `change_spec.md` owns the
CP-426 to CP-458 requirements; the sibling `change_request.md` owns the requested scope.
Product paths below are relative to `products/tracker17/` in this change's worktree.

**Language resolution:** Python — step 1, the project's `project.md` **Languages** field;
opened `<CORE>/doctrine/engineering/languages/python/README.md` and its seven destinations.
The product's Python 3.11 floor and pinned tools govern this design (`docs/nfdr.md` § 8,
QC-59, QC-60 and QC-62; `docs/adr/0002-standard-library-only-no-web-framework.md` § Decision).

---

## 1. Change Summary

Add the sort entry in `domain/sorting.py`, extend the application's project-list read, and carry
two more choices through the existing web form, address and move landings. Add the independent
timed-sort fixture and measurements to `tests/timed_run.py`. The layer placement follows
`docs/SDD.md` § 3, **The parts**, rows `domain`, `application` and `web` (lines 204–207).
The behavior comes from the sibling spec's CP-426 to CP-458, with the zero-match reading recorded
in Architect Review Notes below.

---

## 2. Blast Radius

The table covers every part in `docs/nfdr.md` § 1.2, **Forbidden imports** (QC-13 to QC-19).
The owning parts come from `docs/SDD.md` § 3, **The parts**, rather than from the first caller.

| Module | Status | What changes |
|---|---|---|
| `domain/` | Modified; new `sorting.py` | The `domain` part owns sort defaults, validation, priority rank, Unicode title comparison, creation order and tie order. `sorting.py` also composes the existing filter selection with sorting and collects both kinds of typed refusal in control order. Add public re-exports in `__init__.py`. Keep the existing filter rules and default task-list function intact. |
| `application/` | Modified | The `application` part extends `tracker.py`'s project-list read model and read operation with raw and validated sort choices, result-count visibility and the combined typed problems. Its `__init__.py` hands the new plain values and refusal types to `web`. |
| `web/` | Modified | The `web` part adds address decoding and carrying in `routes.py`, and controls, typed reason mapping, retained values and count presentation in `pages.py`. Reuse the existing wrapping field styling in `style.css`; no stylesheet change is needed for another pair of native selects. |
| `persistence/` | Unchanged | No saved field, format, constructor or saver contract changes (CP-447). |
| `main.py` | Unchanged | No new wiring, clock or runtime dependency (CP-458). |
| `errors.py` | Unchanged | The new refusals inherit the existing domain refusal base, which already derives from the product error (`domain/refusals.py` § `Refusal`, lines 42–43). |
| `tests/timed_run.py` | Modified | Supporting measurement module: isolated loaded fixture, independent ordering oracle, two timed reads, exact four-line output and verdict propagation (CP-451 to CP-455). |

**Transitive impact.** `application` consumes the new domain contract, and `web` consumes the
extended application contract. Both are Modified above. `persistence` and `main.py` need no call-site
change: entity shapes and wiring signatures stay fixed. These edges follow `docs/nfdr.md` § 1.2,
QC-14 to QC-17. Keep the two-argument project-list call compatible with existing consumers
(`application/tracker.py:239-270`, `project_task_list`; `tests/integration/test_filter_tracker.py`,
`test_project_task_list_projects_domain_selection`). No new cross-part import is required.

---

## 3. Sub-jobs

The following contracts are architecture decisions by the Architect, 2026-10-28. Names identify the
seams; they are not production implementations.

### Sub-job A — `domain/`

**Scope:** implement `domain/sorting.py` and its public re-exports. Reuse `filter_project_tasks`
without changing its rules or signature (`domain/filtering.py:137-167`, `filter_project_tasks`).
The new entry composes selection and sorting so neither validation aggregation nor ordering leaks
into `application` or `web` (CP-443, CP-446).

**Exposes:**

- `SortInput`: an immutable plain value with `field` and `direction`, each a tuple of every raw
  string sent. An absent key is an empty tuple; one empty string is an unset choice. Keep repeated
  and unknown values intact until domain validation.
- `SortKey`: the four values `due_date`, `priority`, `created_time`, `title`.
  `SortDirection`: `ascending`, `descending`. `SortControl`: `field`, `direction`, in that order.
  These enums carry identifiers only, with no operator-facing wording.
- `TaskSort`: the immutable validated key and direction, defaulting under CP-428, plus whether a
  nonempty raw sort choice was supplied. An explicit default is still a supplied choice (CP-435).
- `SortFieldRefusal`, deriving from `Refusal`, carries its `SortControl`. Its concrete conditions
  are `InvalidSortField` and `InvalidSortDirection`, each carrying the raw value, and
  `RepeatedSortValue`, carrying the control and number of values. Equal repeats and empty repeats
  are repeats. A repeated field receives its repeated-value refusal instead of extra invalid-value
  refusals for the same field (CP-441 to CP-443).
- `sort_project_tasks(state, project_id, fields, sort_fields, today)` returns an immutable
  `SortedSelection`: the full-project task count, ordered matching tasks, match count, validated
  filter, validated sort, full-project assignee and label options, and `count_requested`.
  The filter options and membership retain the existing filter contract (CP-434).
- `ProjectListRefused` carries the raw filter and sort inputs and the combined typed field
  refusals. Check both inputs independently so an invalid filter cannot hide an invalid sort.
  Report the filter's existing problem order, followed by Sort by and Direction (CP-442).

**Result conditions:**

- Sort the matches explicitly under CP-428 to CP-433. The result must be independent of the
  state tuple's order and of recorded creation timestamps.
- With at least one project task, validate a sort even when the valid filter selects no tasks.
  On any refusal, expose no selection result. On a project with no tasks, return the existing
  empty-project state without validating either input, preserving CP-426 and the empty-filter
  contract (`tests/integration/test_filter_pages.py:124-136`,
  `test_empty_project_retains_first_task_page_without_filters`).
- `count_requested` is false for refusals, empty projects, zero matches and a request with no
  nonempty filter or sort choice. Otherwise it is true. The zero-match exception is the reading
  below. Counts themselves are domain results; words are the web part's.
- A selection changes neither the state nor its task objects and reads no clock or file (CP-447).

**Depends on:** none. Existing domain filtering, tasks, priorities and refusals are inputs.

### Sub-job B — `application/`

**Scope:** adapt `Tracker.project_task_list` and `ProjectTaskList` in `application/tracker.py`,
and extend the facade in `application/__init__.py` (CP-443, CP-446, CP-447).

**Exposes:** `Tracker.project_task_list(project_id, fields, *, sort_fields=SortInput())` continues
to return `ProjectTaskList`. Preserve its existing members and their filter-only meanings:
`task_count`, `rows`, `match_count`, `filter`, `fields`, `problems`, `assignees`, `labels` and
`narrowed`. Add `sort_fields`, `sorting` and `count_requested`. `problems` can hold either the
existing filter refusal types or the new sort refusal types, in the order A supplies. A refusal
has no rows, zero internal match count, no validated selection and no displayed result count.
The application facade re-exports all sort values and concrete refusal types `web` consumes.

Use one injected clock reading for both the selection's date and every row's overdue flag, as
the existing method does (`application/tracker.py:239-270`, `project_task_list`). The operation
calls A and projects its answer. It performs no validation, sorting, ranking or state comparison,
and never calls the saver (CP-446, CP-447).

**Depends on:** A's selection and typed-refusal contracts.

### Sub-job C — `web/`

**Scope:** extend `web/routes.py` and `web/pages.py`. Reuse the native select, escaped option,
field-reason and wrapping-row shapes (`web/pages.py:542-544`, `_option`; lines 1163–1209,
`_filter_field` and `_filter_area`; `web/style.css`, **The filter controls** block).

**Exposes:**

- Two GET keys: `sort_field` carries a `SortKey` value and `sort_direction` carries a
  `SortDirection` value. Decode all values with blanks preserved into `SortInput`; do not take
  only the first value, normalize tokens, or accept aliases. Existing filter key names stay fixed.
- Extend the one existing GET form, with Sort by and Direction after its seven filter controls.
  Default selections display Due date and Ascending even when their keys are absent or empty.
  The existing Apply and Clear serve the whole form (CP-426 to CP-428, CP-436, CP-438).
- Retain invalid raw values in escaped options and show repeated raw values beside the control,
  using the filter's retained-attempt pattern. Each refusal maps by concrete type, never exception
  text. The first refused control alone receives focus and its reason as its accessible description
  (CP-441 to CP-443).
- Render rows exactly in B's order. Use B's count and `count_requested`; use the existing filter
  count words when a filter narrows the result, and the sort-only count words otherwise. Keep the
  filter's zero-match sentence and Clear, with no table or separate count, under the reading below.
  Applying a sort produces no completion message (CP-427, CP-435).
- Carry only the sort keys actually present, alongside the filter keys, through row move hidden
  fields, cancellation confirmation, Back out, and every move outcome address. Preserve every
  repeated/blank value during carrying. Missing sort keys stay missing. Validate the combined
  list choices through B before a move can save or open a confirmation (CP-439, CP-440).
- Apply, reload and Clear answer 200 pages with no redirect. Move POSTs keep the existing redirect
  mechanism; their landing status and no-store policy follow the page actually rendered (CP-437,
  CP-439; `docs/adr/0010-pending-confirmation-answered-202-move-pages-not-stored.md` § Decision).
  A move whose row leaves a status filter retains the existing off-list line and focus (CP-408).
- Clear's link is the bare project address. Unknown projects still take the not-found path before
  list validation. A sort adds no route, script, cookie or retained server state (CP-437, CP-444).

The labels, options, reasons and sort-only count words belong to the text artifact; this blueprint
fixes their places and meaning. The timed run's four lines are already fixed by CP-452.

**Depends on:** B's read model and application exports. C never imports `domain` directly.

### Sub-job D — `tests/timed_run.py`

**Scope:** add the sort measurement, fixture reporting and main-verdict integration in this module.

**Exposes:** a keyword-injected measurement seam, `measure_task_sort(site, saved_data, timer)`,
returning the existing three `Timed` rows; `sort_fixture_report(state)` returns CP-452's fixture
line; the final sort block in `main` prints that line and passes the rows through `verdict`.
Keep the existing `main(directory, timer)` seam and `LIMIT_SECONDS` (CP-451 to CP-456).

Use a separate `sort-volume` location under the run's temporary directory and load its own fixture.
Apply chooses Priority descending without a filter and marks each GET same-origin. The second
read opens that sorted address. The oracle compares exact task-link identities, once each and in
order, and the count against the loaded fixture. It derives priority rank and ascending identity
independently of production sorting. Fixture shape and saved-byte checks sit outside the measured
intervals. Apply failure suppresses the second request and returns the zero-time failed row
(CP-451 to CP-454).

**Depends on:** C's GET address, count and row contracts. Printed labels and fixture fields are
CP-452's, and timing/verdict semantics are CP-453 to CP-455's.

**Build sequence:** A → B → C → D. Each edge consumes the contract named above.
The supporting architecture checks accompany A, and each sub-job carries its § 5 tests.

**Atomic-landing edges:**

- A's `sorting.py` + the landed-word and shape-test updates — no green point between them:
  the architecture suite rejects a sorting module still excluded or omitted from the landed set
  (`tests/architecture/test_shapes.py:175-194`, `test_only_the_task_features_are_added_to_domain`;
  `tests/architecture/test_trace.py`, `test_each_feature_word_with_its_domain_module_is_listed_as_landed`).
- D's activation in `main` + CP-456's timer-stream and whole-output expectations — no green point
  between them: the new measurement consumes extra supplied readings and appends four lines.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — domain sorting and combined validation | Establish ascending task identity explicitly as the tie baseline; apply a stable primary-field ordering in the requested direction. Due-date ordering keeps dated and undated partitions separate so descending reverses neither null placement nor ties. Created time orders identities in the requested direction. Use Unicode case folding for the title key and an explicit priority rank. The selection wrapper gathers filter and sort refusals independently before exposing any result. |
| B — project-list read and exports | None |
| C — request, page and move carrying | Carry raw value tuples symmetrically through address decoding, row forms and the shared address builder. Reuse existing escaped fields and native select styling; page focus follows the combined domain problem order. |
| D — timed sort | The oracle compares the full ordered identity sequence, rather than set membership. Keep fixture reads and byte comparisons outside both timed intervals. The filter measurement's two-GET shape is the seam, while CP-454's exact ordering check is specific to sorting. |

No sub-job writes into another repository.

---

## 5. Test Additions

Rows identify the coverage obligations, not test implementations. Every new test module's opening
docstring names its SRS requirements or acceptance criteria (CP-446).

| Row / sub-job | Test file | What to add / modify |
|---|---|---|
| T1 / A | `tests/unit/test_sorting.py` (new) | CP-428 to CP-433, CP-448: each of four fields in both directions; dated versus undated, including all-undated; all four priorities; `beta`, `Alpha`, `alpha` both ways; Unicode case-fold ties `Straße`/`STRASSE`; code-point ordering and `Task 10` before `Task 2`. Tie groups retain ascending identity in either direction. Deliberately shuffle state storage order so creation order is proved independently of it. |
| T2 / A | `tests/unit/test_sorting.py` | CP-432, CP-433: created time ascending/descending over equal and reversed recorded timestamps, with gaps in task numbers; empty and singleton selections; repeated reads have identical order. CP-428: absent and singleton-empty inputs, field only, direction only, explicit defaults. No input state or task mutation. |
| T3 / A | `tests/unit/test_sorting.py` | CP-434, CP-441 to CP-443: unchanged membership under each existing filter kind and combinations; zero matches still validate sort. Invalid field, invalid direction, repeated field and repeated direction, including equal, blank and mixed repeats and spaced/case-altered tokens; each concrete refusal type and field. Combined filter/sort refusals collect all reasons in control order. Empty project ignores valid and malformed inputs. |
| T4 / B | `tests/integration/test_sort_tracker.py` (new) | CP-434, CP-435, CP-447, CP-449: project isolation, ordered rows, full-project options and counts, raw choices, validated defaults, sort-only count visibility, two-argument compatibility, combined refusal data and zero matches. One handed clock reading serves overdue selection and row marking; the handed recording saver receives no call on valid, invalid, reload-equivalent or clear-equivalent reads. |
| T5 / C | `tests/integration/test_sort_pages.py` (new) | CP-426 to CP-428, CP-435, CP-436, CP-449: nine labelled controls in order before the single Apply and Clear; the exact offered choices and defaults; no controls on an empty project, even with malformed sort choices; no default count, explicit-default and direction-only count, sort-only count for one and several tasks without filter wording; selected choices persist; no applied message. |
| T6 / C | `tests/integration/test_sort_routes.py` (new) | CP-429 to CP-438, CP-449: every field and direction through the real Site, ordered task-link identities, count and retained controls; no direction and no field; status filter plus descending priority and other membership combinations; same address twice, reload/bookmark-like reopening, then Clear. Clear removes all choices/count and restores due ascending with identity ties. A filter yielding zero matches, with and without sorting, keeps the existing empty state under the reading below. Blank-only choices do not request a count. |
| T7 / C | `tests/integration/test_sort_pages.py`; `tests/integration/test_sort_routes.py` | CP-440 to CP-444, CP-449: one case per refusal kind and repeated control, asserting its reason, retained raw values, single focus, accessible description, no result/count and unchanged saved bytes. Combine reversed Due from/Due to with invalid Direction: both reasons, focus Due from. Both sort fields refused: focus Sort by. Unknown project, with valid or invalid sort, remains 404. |
| T8 / C | `tests/integration/test_sort_move_routes.py` (new) | CP-439, CP-440: ordinary move, opening cancellation confirmation, Back out, confirming, workflow refusal, saver failure, stale/forged confirmation addresses and off-list outcome after a status-filtered move; use filter plus sort and sort alone. Assert retained choices in hidden fields and every address, expected sorted order against the resulting saved data, 202 only for a rendered confirmation, 200 for other move pages and no-store throughout. Invalid/repeated sort choices on ordinary and confirming POSTs save nothing and open no confirmation. Requests with no sort keys gain none. Keep CP-408/CP-409 assertions represented by the unchanged filter-move tests. |
| T9 / C | `tests/integration/test_sort_pages.py`; `tests/e2e/test_sorting.py` (new) | CP-445: title `<b>&"x"` displays literally and sorts by its text; unknown sort tokens containing markup are escaped. Browser keys alone choose and apply sort, reload, traverse Back/Forward and Clear with scripting off. First refused field owns focus and its visible reason; Clear stays in view. Reuse the wrapping layout and check reflow at 400% zoom without clipping the new controls. |
| T10 / B, C | `tests/integration/test_routes.py` | CP-437, CP-447, CP-450: extend the named Apply/reload/Clear route check with sort values and assert 200, no redirect, no saved changes and no Set-Cookie; add a sorted Apply to the audit-hook no-outbound action walk and recording-saver action walk. Keep every existing route/action assertion. |
| T11 / A | `tests/architecture/test_trace.py`; `tests/architecture/test_shapes.py` | CP-446, CP-456: list `sorting` as landed; check its entry docstring's FR-36, every participating application/web module and checking test path. In the named shape test, replace sorting's absence assertion with its presence; retain summary's absence, every other landed module and every TrackerState field. Run the existing import, reach, immutability and error walks over the added code. |
| T12 / D | `tests/integration/test_timed_run.py` | CP-451 to CP-455: separate saved location, loaded volume 1,000/20/20,000, ordinary text lengths, same-origin GET Apply and reload; exactly four appended lines, final total last. The fixture report must also work from a different loaded fixture with different counts, first sorted task and code-point lengths. Product data and fixture saved bytes stay unchanged. |
| T13 / D | `tests/integration/test_timed_run.py` | CP-453 to CP-455: handed timer proves Apply, landing and sum; slow Apply, slow landing, and a total exactly 1.0 with both parts below it each fail the appropriate row and main verdict. A refused/failed Apply suppresses the next request and gives the exact zero-time failed landing and Apply-only failed total. Refusal, failure status, swapped tasks, missing/duplicate/extra identities, incorrect count and changed saved bytes each fail the sort and main verdict. Expected ordering is independent of production sorting. |
| T14 / D | `tests/integration/test_timed_run.py` | CP-456: adapt exactly the named 21 fixed timer streams and 7 whole-run users to the sort's readings and fixture. The two named whole-output assertions include the new final four lines after the unchanged filter block. Every old action, assertion beyond that extension, threshold, failure probe and test name remains. |
| T15 / all | Product gate commands | CP-457, CP-458: the complete project suite, separate end-to-end suite, timed run and the three pinned Ruff/mypy checks named in CP-457 all exit 0. The Python compile gate also covers the changed modules. Run checks in the change worktree or the disposable Git clone the spec requires, with temporary test data; preserve the Python 3.11 syntax/library floor. These are implementation checks, not results claimed by this design. |

**Example coverage:** the sibling spec's 36 Examples rows, numbered in their printed order, map as
follows: 1–3 → T5; 4–5 → T2/T6; 6–10 → T1/T6; 11 → T2; 12–13 → T1/T2/T6;
14–17 → T6; 18–20 → T8; 21–23 → T3/T7; 24 → T7; 25–26 → T9; 27 → T11;
28 → T4/T10; 29 → T1–T3; 30 → T5–T9; 31 → T10; 32 → T12/T15;
33 → T13; 34 → T11/T14; 35–36 → T15.

**Rule-implied edges:** empty project and empty choices → T2/T3/T5; empty filtered result → T3/T6;
all-undated and descending ties → T1; mixed invalid/repeated controls → T3/T7;
missing project → T7; malformed sort on confirming moves and post-move off-list rows → T8;
read-only, no cookie/outbound/save → T4/T10; timing equality, suppressed landing and byte changes →
T12/T13. CP-426 to CP-458 are covered by the rows that name them, including the CP-435 exception below.

**Assertions retired:** sorting's absence is replaced by its presence in T11; the clause itself is
released by CP-446/CP-456. The whole-run terminal-filter assertion and fixed timer-stream lengths
are replaced by T12/T14's unchanged prefix plus sort suffix; the old-action clauses are re-proved
by the retained assertions. No other existing assertion is dropped.

---

## Records this change makes false

None — read `docs/adr/README.md` and ADR-0001 through ADR-0011, `docs/nfdr.md` §§ 1–9 including
QC-40/RN-33, `docs/fdr.md` Rules and Product decisions, and `docs/SDD.md` § 3 **The parts, and the
seams between them**. Sorting is already assigned to domain, the import graph permits its callers,
and the sort changes neither entities nor saved state. ADR-0006 remains superseded by ADR-0011.
The scope exclusions already recorded in the sibling `deferred_decisions.md` remain there.

---

## Architect Review Notes

All decisions in this section are the Architect's, 2026-10-28.

- **Realize the order explicitly (b):** use the identity baseline, stable primary ordering and
  separate undated partition in § 4. Storage order, lexical priority and a reversal of the entire
  result cannot substitute for CP-429 to CP-433. This realizes the rules by construction and
  preserves ascending tie order even under descending primary order.
- **Wire vocabulary and compatible reads (b):** choose `sort_field`/`sort_direction` and the enum
  tokens in A/C; add a keyword-only optional sort input to the existing read. These are the
  concrete cross-module contracts the spec leaves unstated. Retain every raw value because
  CP-441 cannot be proved after discarding repeats.
- **Combine validation in the owning part (b):** `sorting.py` composes the existing filter and
  collects both refusal sets before returning. This preserves filter rules while satisfying
  CP-442's simultaneous-refusal requirement without a rule in the application coordinator.
- **Zero-match count reading (a):** CP-435's universal count wording conflicts with the existing
  no-count empty state (`tests/integration/test_filter_pages.py:162-176`,
  `test_no_matches_keeps_choices_and_clear_without_an_empty_project_message`;
  `web/pages.py:1210-1215`, `_filtered_list`). Take the reading that retains that empty-state
  sentence and Clear without a separate count, including when sorting accompanies the filter.
  Counts for nonempty filtered or sorted results remain CP-435's. A reading that adds a numeric
  zero count changes filter behavior outside the request's guardrail; a reading that removes or
  rewrites the existing empty-state test also violates CP-456. Set aside only CP-435's separate
  count for a valid zero-match filter, and record it in `deferred_decisions.md`. No Example asks
  for that zero count, and T6 covers the preserved edge.
- **Empty-project validation (b):** bypass sort validation with filter validation on an empty
  project. CP-426 preserves that page, and the existing test includes malformed choices
  (`tests/integration/test_filter_pages.py:124-136`,
  `test_empty_project_retains_first_task_page_without_filters`). Validate sort when tasks exist
  but a filter finds none; those two empty cases have different existing contracts.
- **Delegated NFDR reviews — pass:** QC-5 maps each new refusal by its type through application;
  QC-8 keeps choices in request-local values and addresses; QC-12 adds only the required sorting
  entry and measurement helpers; QC-20/21/23 keep rules and count decisions in domain; QC-27
  carries only plain values across the replaceable browser seam; QC-36 reuses `_escape` for
  every typed value (`web/pages.py:363-365`, `_escape`); QC-41 introduces no secret; QC-60 uses
  only Python 3.11 constructs and standard-library operations. QC-22/24/25/26/46's conditional
  reviews are untouched: neither persistence, main, the saving contract nor saved fields change.
  The review obligations are `docs/nfdr.md` §§ 1.1, 1.3, 1.4, 2, 4 and 8, each named QC above.
- **QC-40 advisory review — pass under the dated browser exception:** the 15 exact package/version
  pairs in `tests/requirements.txt` were submitted to `https://api.osv.dev/v1/querybatch` on
  2026-10-28 (Europe/Berlin). The read-only curl command exited 0 with
  `{"results":[{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}]}`: no matching published advisories in
  that database, not a claim that none can exist elsewhere. The pinned Playwright's vendor
  manifest names Chromium 153.0.8010.12
  (`https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/packages/playwright-core/browsers.json`,
  `chromium` and `chromium-headless-shell`). Google's 2026-09-08 desktop release lists critical
  fixes in 153.0.8010.36/.37
  (`https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0808145027.html`).
  That fixed release is newer than the pinned build and its publication is more than 30 days
  before this review. `docs/nfdr.md` **RN-33**, lines 1025–1039, expressly exempts this build through
  2026-11-07, so it does not block this design. No pin or dependency changes are proposed.

**Cold-read result:** blast radius, owning parts, interface dependencies, atomic edges, every
Example and rule edge, explicit order realization, divergences, record impact and the text verdict
have been checked against this design. The change writes only inside its own repository.

change_design: clean.
