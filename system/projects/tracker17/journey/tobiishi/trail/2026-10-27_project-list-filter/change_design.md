# Change Design — filtering a project's task list

**Date:** 2026-10-27
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the project's filter controls and choices, match count, no-match state, field refusals, and move completion or failure lines above the list

This blueprint owns the boundaries, interfaces and test coverage for the filtering change in
`tracker17 · tobiishi · 2026-10-27_project-list-filter`. Its home is the change folder under
`<CORE>/doctrine/setup/kensaiapp_structure.md` § 2, “journey/tobiishi/<key>/”.
The behavioural authority is `change_spec.md` § Rules and § Examples in that change.

Paths below are relative to `products/tracker17/`, the product root returned by
`development_path.py resolve --project tracker17 --key 2026-10-27_project-list-filter`.
`docs/` means that product's documents. Design choices below are the Architect's, 2026-10-27.

---

## 1. Change Summary

Add a pure filtering entry module, a read-only application query, and filter controls on the existing
project page. Apply is a GET form to the project's address. Clear is a link to that address without
a query. Neither reaches the saver. The existing move submissions carry the choices through every
return to a project list. The timed run gains an independent filter fixture and measurement after
the move block. These boundaries implement `change_spec.md` CP-393–CP-425.

No new runtime dependency, saved field, route, composition-root collaborator or top-level part is
needed. Sorting, All tasks and Summary remain outside this delta, per `change_spec.md` § Out of Scope.
The seven controls use the layout and existing component contracts in `docs/DESIGN.md` § Layout and
§ Components. The words follow `docs/CONTENT.md`; this blueprint specifies their data and placement.

---

## 2. Blast Radius

Placement follows `docs/SDD.md` § 3, “The parts”, and NFDR § 1.2's six code units. The table's
`Lives in` cells are empty, but each part's `Owns` names its directory; those explicit directories
settle placement without inventing a new unit (`docs/SDD.md:L202-L209`).

| Module | Status | What changes |
|---|---|---|
| `domain/` | Modified; new `filtering.py` | The **domain** part owns raw-choice cardinality, filter validation, exact matching, date boundaries, AND, count, project label choices and deterministic label order. Reuse `tasks.list_project_tasks` for the established row order and `due_dates.is_overdue` for the overdue rule. Add filter refusal types to `refusals.py`; re-export contracts through `__init__.py`. |
| `application/` | Modified | The **application** part owns the query over current state, one local-date snapshot, and the read model carrying matching `TaskRow` values, full-project task count, match count, choices and typed problems. Re-export the domain contracts `web` consumes. No saver call or matching rule here. |
| `web/` | Modified | The **web** part owns query decoding/encoding, GET controls, raw retention, refusal-to-word mapping, rendered count and empty state, move return addresses, and focus. Change `routes.py`, `pages.py` and `style.css`; keep `listener.py` unchanged. No rule, count computation or clock read here. |
| `persistence/` | Unchanged | No saved format or saving contract changes. A real-file test proves filter requests leave bytes unchanged (CP-413). |
| `main.py` | Unchanged | Existing injected clock and saver suffice. |
| `errors.py` | Unchanged | New refusals derive from the existing domain refusal base. |
| `tests/` — support | Modified | Unit, application/UI and browser filter checks; architecture registrations; extend `timed_run.py` and its integration tests. This is the test unit named alongside the code parts by NFDR QC-1. |

Transitive check: `application` consumes the added `domain` surface; `web` consumes the added
`application` surface. Preserve the existing `Tracker.project_tasks(project_id)` and all mutator
signatures so their other consumers remain valid. `persistence` and `main` import the inner parts,
but no imported constructor or contract they use changes. The permitted edges remain
`web → application → domain → errors`, per `docs/nfdr.md` § 1.2 QC-13–QC-18.

---

## 3. Sub-jobs

### A — `domain/`: validate and select

**Scope:** New `domain/filtering.py`, filter-specific refusals in `domain/refusals.py`, and public
re-exports. The entry module owns the rules of CP-396, CP-402–CP-404 and CP-412. It uses the existing
due-date parser but translates its invalid-date refusal into the appropriate filter-field type.

**Exposes:**

- `FilterField`: closed fields `status`, `priority`, `assignee`, `label`, `due_from`, `due_to`,
  `overdue`, in control order.
- Immutable `FilterInput`: one tuple of raw strings per field, default empty. An absent parameter
  becomes an empty tuple. Preserve duplicate values, empty values and spaces until domain validation.
  This is a plain value, with no request, URL or HTML knowledge.
- Immutable `TaskFilter`: validated optional status, priority, exact assignee and label, optional
  calendar-date ends and an overdue boolean. A singleton empty string means unset. The sole checked
  overdue value is `on`; absent or singleton empty means off. Repetition is invalid even when the
  repeated values are equal or empty.
- `InvalidFilterStatus`, `InvalidFilterPriority`, `FilterAssigneeNotListed`, `InvalidFilterDueFrom`,
  `InvalidFilterDueTo`, `ReversedFilterRange`, `InvalidFilterOverdue`, `RepeatedFilterValue`:
  distinct domain refusal types. Each carries its `FilterField`; the range names Due from.
  A repeated-value refusal carries the repeated field, so the same condition remains one type.
- `FilterRefused`: a domain refusal carrying the ordered tuple of field refusals and the original
  `FilterInput`. Domain raises the specific refusals during validation and collects them into this
  raised aggregate, allowing one page to show all bad fields. No messages carry operator wording.
  Check cardinality before parsing a field; check reversed range only when both dates parsed.
- `filter_project_tasks(state, project_id, fields, today)`: returns an immutable selection with
  validated choices, selected tasks in existing list order, match count, full-project task count,
  assignees and available project labels; raises `FilterRefused` on invalid choices. Assignees come
  from the current list in its existing order; labels are exact distinct values from **all** tasks
  in this project, explicitly sorted by code point. Never narrow available choices to the matches.
  A project with zero tasks returns its empty-project selection without validating filter choices,
  as CP-393 requires. No date or field is saved.
- `project_filter_options(state, project_id)`: returns immutable full-project task count,
  current assignee choices and exact project label choices in the orders above. Both successful
  selection and refusal-page projection use this domain contract.

An unknown single label remains a valid selected value, even when absent from the label choices.
The ordered input to matching is `tasks.list_project_tasks`; selection preserves that order.
Counts come from domain results rather than HTML row counting. The overdue predicate is
`due_dates.is_overdue` with the supplied `today`, never a second predicate.

**Depends on:** none. Existing task, assignee and overdue contracts remain intact.

### B — `application/`: one snapshot for the page

**Scope:** Add `Tracker.project_task_list(project_id, fields)` in `application/tracker.py` and the
corresponding public read model. Keep the existing unfiltered query as a compatible entry point.

**Exposes:** Immutable `ProjectTaskList` with full-project task count, ordered matching `TaskRow`
values, domain match count, validated choices when valid, original fields, ordered typed refusals,
and current assignee/label choices. On refusal, there are no result rows or result count. The
application catches only the domain aggregate to package the refused read model, preserving every
specific refusal type. Options needed on a refused page come from domain's project option query,
not an application set, sort or validation rule. That pure option query is also exported by A.

Read the injected clock once, convert its instant to the machine-local date, pass that date to
selection and to `is_overdue` when building every row. All date-dependent results on this page use
that same snapshot. Do not call `project_tasks` separately to build markers. Domain supplies the
empty-project distinction; the application performs only orchestration and projection. Neither the
successful query nor refusal handling calls `_save_then_publish` or the saver.

Expose the `FilterInput`, `FilterField`, filter refusals and `ProjectTaskList` through `application`
so `web` imports no `domain` names directly, per `docs/nfdr.md` QC-5 and QC-16.

**Depends on:** A's input, selection, option query and refusal contracts.

### C — `web/`: addresses, controls and move context

**Scope:** Existing project GET rendering and list-row move paths in `routes.py`; the project page,
filter area and list move forms in `pages.py`; filter layout in the one stylesheet. No new route.

**Exposes — address contract:**

| Field | Query key | Form |
|---|---|---|
| Status | `filter_status` | single select, empty choice plus four statuses |
| Priority | `filter_priority` | single select, empty choice plus four priorities |
| Assignee | `filter_assignee` | single select, empty choice plus current names |
| Label | `filter_label` | single select, empty choice plus exact project labels |
| Due from | `filter_due_from` | native date control |
| Due to | `filter_due_to` | native date control |
| Overdue | `filter_overdue` | checkbox with checked value `on` |

Use a separate GET form targeting `/projects/{project_id}` with no fragment. Apply sends only its
seven controls, replacing any prior action-outcome query. Preserve every decoded value for the
seven keys when constructing `FilterInput`; do not use `_first` for filters. The `filter_` namespace
keeps filter choices apart from the add-task form's existing `priority` and `assignee` values
(`web/routes.py` `_task_form`). Clear is `/projects/{project_id}` with no query.

Successful addresses may contain singleton empty values from the GET form; those are unset by A.
A valid active filter shows the domain match count, including zero. Empty-only fields show neither
a filter count nor an applied message. No unknown parameter becomes an extra filter field.

**Exposes — page contract:**

- Distinguish no project tasks, no matches, refused filter and matching list from `ProjectTaskList`.
  Never infer empty-project state from the filtered rows. Preserve the existing empty-project
  invitation and add form without controls, even for malformed choices.
- A filter area contains raw choices, offered choices and by-type field problems. Add a retained
  selected option for a valid unmatched label or invalid enum/name. Keep every malformed date,
  invalid overdue token and repeated attempted value visibly in its labelled field area alongside
  the correction control and refusal; never silently retain only the first or erase a bad token.
  The correction controls retain their normal single-value shapes. Applying the correction sends
  one value. The retained raw input remains available to render each value exactly, escaped.
- Reasons sit at their fields. Exactly the first refused field in control order gets `autofocus`
  and `aria-describedby` naming its reason. All refused fields expose their reason; no result table,
  result count or no-match line appears. Use `novalidate` so native browser validation cannot prevent
  the specified server refusal path. A valid Apply opens at the page start.
- Reuse the single `_escape` function for option values, labels, retained raw values, hidden values,
  query-bearing attributes and task names. Percent-encode addresses before HTML escaping them.
  Filter layout follows `docs/DESIGN.md` § Layout, “The filter controls”, and its focus/reflow rules.

**Exposes — move return contract:**

Carry only the seven allowlisted filter keys through list-row move forms, cancellation confirmation,
back-out links, confirm submissions and all outcome redirects. Preserve repeated raw values where
present. Extend the one `_address` builder to accept repeated query pairs without changing its
existing callers. No arbitrary return URL or session is introduced. Task-page moves retain their
existing address behavior. Add-task submissions retain the behavior excluded from this change by
`change_spec.md` § Out of Scope.

Before a list move can save, validate carried filters through B; a malformed filter returns its
field refusal without moving a task (CP-405). Successful move, refused move and save failure all
return to the same filter choices. Rebuild the landing from current state after the move.

Find the outcome's task among the project's full task set as well as the visible rows. A task that
still appears keeps its current row line and focus. An outcome whose task belongs to this project
but is no longer visible gets one line above the results, with focus on the list section described
by that line, never on the line itself. The completion's task name and new status come from the
move outcome/current task. Membership comes from B's selected identities; `web` does not retest
status, dates or overdue. The line remains above a no-match state. A missing task or an outcome
for another project retains the existing not-found/ignore behavior.

Keep `_move_view`'s outcome precedence and saved-workflow check. A pending confirmation is rendered
only for a visible row. Derive 202 versus 200 from the interaction actually rendered, and keep
`Cache-Control: no-store` on all move interaction/outcome landings, including off-list lines.
The absent-target 404 exception remains as in `docs/nfdr.md` QC-63.

**Depends on:** B's read model and re-exported contracts. No new inward import edge.

### D — `tests/`: timed filter measurement

**Scope:** Extend `tests/timed_run.py` and `tests/integration/test_timed_run.py`; no production part.

**Exposes:** A measurement using the injected timer, a fixture opener, a fixture-report function and
an appended runner block, with the same callable seams as the existing move measurement
(`tests/timed_run.py` `measure_task_move`, `move_fixture_report`, `_run_move`).

Use a distinct temporary saved-data location. Send GET Apply using C's keys and same-origin marks.
Time that request, then a second GET of the same address for the reload landing. A redirect, if
ever supplied by the seam, is followed as CP-420 specifies. Accept Apply only when its response is
successful and is a result, not a refused or failed page. Check the landing's task-link identities
as an exact set **and** exact row count against the loaded fixture's matching identities, plus its
displayed count. Duplicate rows, extra rows and missing rows fail. Check saved bytes before/after.

Print the four lines of CP-419 verbatim in their specified order after the existing move total.
Derive fixture counts and text lengths from the loaded fixture; the first matching row is determined
by list order, not the fixture's storage order. The matcher used for the harness's expected Status
set is an independent fixture inspection, not the production filtering function. Propagate a
refused Apply, zero skipped-landing time, any bad landing, byte change or limit breach into the
existing verdict mechanism. Exactly 1.0 second fails each relevant row.

**Depends on:** C's GET keys, page result/count contract and unchanged row title-link identities.

**Build sequence:** A, then B, then C, then D. Rule contracts precede the page query; the timed action
needs the real page it measures. Within A, adding `domain/filtering.py`, registering `filtering` in
the trace test and replacing the shape test's filtering-absence assertion have an **atomic-landing
edge**: no green point exists with the feature file present but either architecture expectation
still describing its absence (`tests/architecture/test_trace.py`, `LANDED_FEATURE_WORDS`;
`tests/architecture/test_shapes.py`, `test_only_the_task_features_are_added_to_domain`). The
entry docstring names checking files only when they exist; each added participant updates the trace.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — domain filtering | Preserve multi-values until cardinality validation; aggregate typed field refusals to show simultaneous errors. Filter the existing explicitly ordered list; reuse the one overdue predicate. |
| B — application read model | One clock snapshot serves selection and row markers; a refused selection is projected with its typed problems and domain-supplied options. |
| C — web | GET form plus the existing address builder, extended for repeated pairs. Carry allowlisted choices through every list move path; render off-list outcomes at the list section. |
| D — timed run | Independent loaded fixture readback and exact task identities guard the measurement; four timer reads cover Apply and reload. |

All changed files are in the resolved instance/product worktree. No write into another repository
is part of this delta.

---

## 5. Test Additions

Row identifiers below are coverage references, not proposed test names. New test modules name their
SRS requirements/acceptance criteria in their opening docstrings (CP-412).

| Row / sub-job | Test file | What to add / modify |
|---|---|---|
| T1 / A | `tests/unit/test_filtering.py` | Each field alone; all-field AND with an almost-matching task for each predicate; no choices and singleton-empty choices; project isolation; exact label/name case and surrounding spaces; unknown label returns no matches; inclusive lower, upper, both and equal range ends; undated task excluded for every nonempty range shape. CP-396, CP-402, CP-414. |
| T2 / A | `tests/unit/test_filtering.py` | Every distinct refusal type: status, priority, unlisted assignee, invalid lower date, invalid upper date, reversed range, overdue token and repetition in **each** field including Label, equal duplicate values and blank duplicates. Multiple invalid fields collect every refusal in control order; malformed date prevents a spurious reversed-range reason. Every input state is unchanged. CP-402–CP-406, CP-414. |
| T3 / A | `tests/unit/test_filtering.py` | Deliberately shuffled storage, due ties and undated ties preserve explicit date/identity order; labels `ui`, `Bug`, `bug` and duplicates across project tasks yield `Bug`, `bug`, `ui`; another project's labels absent; assignees remain earliest-added first. Filtered-out labels remain choices. CP-394, CP-397. |
| T4 / B | `tests/integration/test_filter_tracker.py` | Inject clock and recording saver. AC-13: yesterday/open, today/open, yesterday/done and yesterday/cancelled; marking and selection agree. A clock whose next read crosses local midnight proves one snapshot per page; later query recomputes. No save on valid, refused, clear or repeated query. Preserve old `project_tasks` signature and results. CP-399, CP-413, CP-415. |
| T5 / C | `tests/integration/test_filter_pages.py` | Three-task project controls, labels and choices; count only for active filters, no Apply/Clear success message; plain empty project still one add form and no filters, with valid **and invalid** query choices; nonempty project with no matches shows Clear, retained unknown label and no table/first-task invitation. CP-393–CP-395, CP-398, CP-401. |
| T6 / C | `tests/integration/test_filter_routes.py` | Every field via GET, all-field AND and every range shape; count, choices and stable date/identity link order; same address on reload/bookmark/Back; Clear's bare address returns all tasks and unset controls. Test removed assignee still held on a task is refused. Missing project plus invalid choices is 404. CP-396–CP-400, CP-403, CP-410, CP-416. |
| T7 / C | `tests/integration/test_filter_routes.py`, `tests/integration/test_filter_pages.py` | One case per T2 refusal through `web`, saved bytes/state unchanged, no result/count/no-match state, Clear present, field reason/described-by and exactly one autofocus. Reversed range plus bad Status focuses Status. Invalid dates and all repeated raw values remain visible, escaped, without silently taking the first. CP-402–CP-406. |
| T8 / C | `tests/integration/test_filter_move_routes.py` | Parameterize list move, open cancellation, back out, confirm, workflow refusal and saver failure with retained choices and appropriate 303/GET landing contract. Priority `high` retains its row after a move; status `todo` loses it; only matching row lost shows completion above no-match; overdue to **both** done and cancelled leaves; stale other-tab refusal and failure about an off-list task appears above results. Assert 202 only for rendered pending confirmation, otherwise 200, no-store, no Clear-Site-Data. Keep missing-target 404 and unfiltered/task-page behavior. CP-407–CP-409. |
| T9 / C | `tests/integration/test_filter_pages.py`, `tests/e2e/test_filters.py` | Labels and names with `<`, `&`, quotes and surrounding spaces round-trip exactly through options, URLs, hidden move fields and rendering. Use keyboard alone to Apply and Clear with scripting disabled. Verify actual focus/viewport on field refusal and off-list completion, count/no-match appearance, and filter row reflow at 400% with table-only horizontal scrolling. CP-405, CP-408, CP-411. |
| T10 / A, C | `tests/architecture/test_trace.py`, `tests/architecture/test_shapes.py` | Add `filtering` to landed words and check its requirements/participants; replace only filtering's forbidden-file assertion with presence. Preserve `sorting`, `summary` absences and `TrackerState` shape checks. CP-412, CP-423. |
| T11 / C | `tests/integration/test_routes.py`, `tests/integration/test_listener.py`, `tests/integration/test_tracker.py` | Extend existing route enumeration, page-policy/no-cookie, outbound audit and recording-saver action coverage to Apply/reload/Clear. Apply GET is read-only; no new route registration needed. Keep same-origin move-submission checks with carried choices. CP-417; NFDR QC-7, QC-8, QC-34, QC-35, QC-54. |
| T12 / D | `tests/integration/test_timed_run.py` | Success on independent fixture, same-origin GET Apply and reload, exact four appended lines and old prefix unchanged, loaded rather than constant fixture counts/lengths; refused/failed Apply skips landing at zero ms, non-200 landing, extra/missing/duplicate identities, wrong count, saved-byte change, slow Apply, slow landing and total exactly 1.0 with parts below it all fail. Check failures propagate to main's nonzero verdict. CP-418–CP-422. |
| T13 / D | `tests/integration/test_timed_run.py` | Extend the 21 existing finite-timer/whole-run cases identified in `change_spec.md` § Verified Claims with four extra readings. The two whole-output assertions now prove the exact existing prefix **and** four-line filter suffix. Keep all other assertions, failure thresholds, fixture-independence and product-data checks. CP-423. |
| T14 / all | Existing product gate commands | CP-424's suite, separate browser suite, timed run, Ruff format/lint and mypy commands remain acceptance gates. Add compile verification under the Python packet. Exercise new code on Python 3.11 for CP-425; no dependency pin moves. |

**Examples pass:** The Examples table maps in order to T5, T5, T3/T5, T5, T1/T6, T1/T5,
T1/T6, T4, T6, T6, T2/T7, T1/T6, T2/T6/T7, T2/T7, T7, T2, T8, T8, T8/T9,
T8, T8, T8, T6, T9, T9, T10, T4/T11, T1/T2, T11, T5–T9, T12, T12, T10/T13,
T14 and T14. Each of the 35 Examples has a row.

**Rules pass:** CP-393–CP-395 → T3/T5; CP-396–CP-401 → T1/T3–T6;
CP-402–CP-406 → T2/T6/T7; CP-407–CP-409 → T8/T9; CP-410 → T6;
CP-411 → T9; CP-412 → T10; CP-413 → T4/T11; CP-414 → T1–T3;
CP-415 → T4; CP-416 → T5–T9; CP-417 → T11; CP-418–CP-422 → T12;
CP-423 → T10/T13; CP-424–CP-425 → T14. Rule-implied edges include empty project with invalid
address, empty fields, unmatched retained label, removed-name task, equal range ends, undated tasks,
multiple simultaneous refusals, repeated blanks, final cancelled overdue task, last matching row
leaving, failed off-list move and exact timing boundaries; their rows above explicitly name them.

**Retired assertions:** Only the filtering-absence assertion is retired, replaced by T10's feature
presence and trace. Existing finite timer lengths are extended, not relaxed. T13 replaces “nothing
after move total” with “exactly the filter suffix after move total”, retaining all prefix checks.
No other assertion or behavioural clause is retired (CP-423).

---

## Records this change makes false

None — read `docs/adr/README.md` and Accepted ADR-0001–ADR-0010 (their Decision sections),
`docs/nfdr.md` §§ 1–10 and RN-33, `docs/fdr.md` § Rules, and `docs/SDD.md` § 3. The new entry
module sits inside the existing domain part; no import, persistence, clock or interface boundary
changes. Filtering realizes existing records. Sorting, All tasks and Summary gaps remain in the
existing `deferred_decisions.md`; this design sets aside no spec line.

---

## Architect Review Notes

- **GET Apply and namespaced keys (b):** Architect, 2026-10-27. CP-420 and Locked Answer 9 leave
  the method open. GET directly realizes the reloadable address without a write or action marker.
  The namespace avoids collision with the existing add-task refusal fields in `web/routes.py`
  `_task_form`. No new endpoint is needed.
- **Order and overdue by construction (b):** Architect, 2026-10-27. Selection takes the existing
  explicit `_due_then_identity` order (`domain/tasks.py:L372-L380`), not storage order. The
  application's one snapshot feeds `domain/due_dates.py` `is_overdue` for both filtering and
  markers. These choices realize CP-397 and CP-415 even with shuffled state or a midnight boundary.
- **All refusals and raw retention (b):** Architect, 2026-10-27. Aggregate typed problems allow
  CP-405's simultaneous field errors. A labelled field area retains repeated attempted values while
  its correction control emits one value. Malformed dates and invalid overdue tokens remain visible
  in the labelled area too. These render choices retain the whole attempt without adding another
  editable field; no validation is delegated to `web` or the browser.
- **Off-list outcomes (b):** Architect, 2026-10-27. Use selected identity membership and the full
  project task lookup to place lines. Focus belongs to the list section described by the line.
  This realizes CP-408/CP-409 and SDD EX-14 without reconstructing filter rules in `web`.
- **Delegated NFDR review — pass, QC-5:** The § 3 A refusal set is defined and raised in domain,
  passed through application and mapped by type in web. No branch reads exception text.
- **Delegated NFDR review — pass, QC-8, QC-20, QC-21, QC-23, QC-27:** The § 3 contracts keep all
  transient choices in the request/read model, all matching/validation/counts in domain, and all
  wording/HTML in web. Application retains only current tracker state and uses its existing clock.
  The interface could be replaced without changing rule or saved-data contracts.
- **Delegated NFDR review — pass, QC-12, QC-41, QC-60:** The new domain module is expressly
  required by CP-412; no extra production part or generic filtering framework is added. No secret
  is introduced. The proposed dataclasses, enums, tuple values, date handling and URL/form machinery
  are already present in the product; no feature beyond its Python 3.11 floor is required
  (`pyproject.toml` `requires-python`; `domain/due_dates.py`; `application/tracker.py`; `web/routes.py`).
- **Delegated NFDR review — pass, QC-36:** All new dynamic rendering uses `web/pages.py` `_escape`.
  Address encoding and HTML escaping remain separate operations. T9 covers typed special characters
  at each new place they appear.
- **Delegated NFDR review — pass within the dated exception, QC-40 (2026-10-27):** Read all 15
  exact pins in `tests/requirements.txt`. A read-only query of each
  `https://pypi.org/pypi/<name>/<version>/json` returned `vulnerabilities: []` for
  `ast_serialize 0.12.1`, `greenlet 3.5.6`, `iniconfig 2.3.1`, `librt 0.16.0`, `mypy 2.4.0`,
  `mypy_extensions 1.1.0`, `packaging 26.3`, `pathspec 1.1.1`, `playwright 1.63.0`, `pluggy 1.6.0`,
  `pyee 13.0.1`, `Pygments 2.21.0`, `pytest 9.1.1`, `ruff 0.16.10` and
  `typing_extensions 4.16.0`. This is a check of that advisory feed, not a claim that no vulnerability
  exists. The installed Chromium plist reports `153.0.8010.12`. Google's
  [2026-09-15 security release](https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0541751186.html)
  fixes critical issues in later 153 builds. `docs/nfdr.md` RN-33 expressly permits this build
  through 2026-11-07; this review uses that existing exception and does not extend it. No pin moves.
- **Delegated reviews not triggered:** QC-22/QC-25 concern persistence; QC-26 the saving contract;
  QC-24 the composition root; QC-46 a saved field. None is changed by this blueprint (§ 2).
- **Cold-read:** The nine changing-mode checks pass on this document: every owning part is named,
  dependent contracts precede their consumers, ordering matches the import graph, § 5 covers Examples
  and Rules, row order and overdue agreement are explicit, choices are logged here, records have
  their mandatory section, the text verdict is settled, and no other-repository write is proposed.
  No acceptance suite was run in this architect step.
- **Language resolution:** Python, step 1 (`system/projects/tracker17/project.md`, `Languages:`).
  Opened `<CORE>/doctrine/engineering/languages/python/README.md` and all seven routed concerns.
  The product's NFDR/ADR runtime and tool contracts take precedence over the generic packet.
