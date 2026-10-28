# Change Design — Summary counts open their filtered task lists

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the accessible names of the nine linked counts on a project's Summary

This blueprint owns the placement, interfaces and proof of the linked counts in
`tracker17 · tobiishi · 2026-10-28_linked-counts`.
Its requirements are the sibling `change_spec.md`, CP-513–CP-528; the request is the sibling
`change_request.md`, **Request**.
Product paths below are relative to `products/tracker17/` in this change's worktree, resolved by
`development_path.py resolve`: `product_path=products/tracker17`, `product_worktree` equals the
instance worktree.
The artifact's home is the change folder, per `<CORE>/doctrine/setup/kensaiapp_structure.md`
§ 2, `journey/tobiishi/<key>/`.

## 1. Change Summary

Turn the nine selected count cells into ordinary anchors in `web/pages.py`, with their accessible
names supplied as text and their target geometry styled in `web/style.css` (design decision for
`change_spec.md:24–48`, CP-513–CP-524).
The counts arrive through the existing `ProjectSummary`; both summary counts and list selection
already use the project filter (`domain/summary.py:94–120`, `application/tracker.py:259–288`).
The design therefore changes presentation and its validation harness, without adding a computation
or a request handler (placement decision against `docs/SDD.md` § 3, **The parts**, `web` row).

The rendered page keeps `summary_page(summary: ProjectSummary) -> str` as its entry point
(`web/pages.py:1479–1509`).
New link names belong on the anchors through `aria-label`; the anchors' text nodes contain only
the supplied numerals (design decision realizing `change_spec.md:26–42`, CP-515, CP-521–CP-522).
The page's other words, titles and navigation remain governed by CP-515, rather than new copy
in this blueprint (`change_spec.md:26–38`).

## 2. Blast Radius

The parts table assigns page building, addresses and styles to `web`, and count/filter/sort rules
to `domain` (`docs/SDD.md:198–235`, **The parts** and **The direction of dependence**).
All new product logic belongs to `web`: selecting which count receives an anchor, constructing its
one-choice address, formatting its accessible name, and styling its target (design placement).

| Module | Status | What changes |
|---|---|---|
| `domain/` | Unchanged | Keep summary, filtering, sorting and overdue computations; `ProjectSummary` and its row types are unchanged (`domain/summary.py:39–120`). |
| `application/` | Unchanged | Keep the summary and list reads, the injected clock and the existing exported types (`application/tracker.py:259–288`, `application/__init__.py`, exports). |
| `persistence/` | Unchanged | No saved field, format or saving-contract change (scope: `change_spec.md:38–45`, CP-520, CP-523). |
| `web/` | Modified | Owning part: `web`. `pages.py` attaches the nine count anchors and names using the supplied summary; `style.css` supplies their target geometry while retaining focus and reflow. Routes, listener and package exports stay unchanged (`web/__init__.py:1–8`, `web/routes.py:517–555`). |
| `main.py` | Unchanged | The composition interface and construction stay unchanged (`docs/SDD.md` § 3, `main` row). |
| `errors.py` | Unchanged | No refusal or exception is added (`change_spec.md:29–45`, CP-516–CP-523). |
| `tests/` | Modified | Supporting validation, outside the five runtime parts: page, route and browser assertions; `timed_run.py`'s count-cell reader and its independent tests. Existing affected sites are `tests/integration/test_summary_pages.py:74–150`, `tests/integration/test_pages.py:166–183`, `tests/e2e/test_summary.py:67–99`, `tests/timed_run.py:146,1218–1266`, and `tests/integration/test_timed_run.py:3693–3969`. |

No transitive production caller needs a change: the `web` exports and `summary_page` signature stay
the same, and `main` is the only other runtime part allowed to import `web`
(`web/__init__.py:1–8`, `web/pages.py:1479`, `docs/nfdr.md` § 1.2, QC-13–QC-19).
No new import edge is needed; `web` receives domain types through `application`, as QC-16 requires
(`docs/nfdr.md:161–165`, `web/pages.py:19–45`).

## 3. Sub-jobs

### Sub-job A — `web/`: count anchors and their presentation

**Scope:** the Summary rendering in `pages.py`, its internal group renderer, and count-link styling
in `style.css`; associated page, route and browser proof is listed in § 5.

**Exposes:** the unchanged `summary_page` entry point, with the following HTML contract:

- Each selected count cell contains exactly one anchor whose visible text is the supplied decimal
  count; its accessible name contains that numeral first and identifies the row's meaning
  (`change_spec.md:24–26,41–42`, CP-513, CP-515, CP-521–CP-522).
- The anchor target is the project's base Tasks address plus exactly one existing status, priority
  or overdue query pair; it carries no copied query string, sort key, fragment or outcome flag
  (`change_spec.md:29–35`, CP-516–CP-517).
  The exact targets are `/projects/{id}?filter_status={status}`,
  `/projects/{id}?filter_priority={priority}` and `/projects/{id}?filter_overdue=on`, with the
  summary's project id and the row's status/priority value (`change_spec.md:29–34`, CP-516).
- Selection is based on the group and typed row identity, never a label-wide lookup; an assignee
  named `todo`, `high` or `Overdue` still has a plain count (design choice enforcing
  `change_spec.md:25`, CP-514).
- The total and all remaining count cells are plain numeric cells, and every label remains a row
  header outside an anchor (`change_spec.md:25–26`, CP-514–CP-515).
- Names use the count and category values from this render, with singular/plural forms and every
  published string supplied by the change's text artifact; no name or URL stores a selected filter
  between requests (design choice for CP-519, CP-521–CP-522 and NFDR QC-8).
- Native anchors provide activation; styling provides at least 24 by 24 CSS pixels for every count
  link, preserves visible keyboard focus and fits the Summary at 320 CSS pixels wide (design choice
  realizing `change_spec.md:48`, CP-524, using the non-exception target-size path).

**Depends on:** B's count-cell reader accepting the new cell shape, because the timed-summary checks
are part of the suite (`change_spec.md:58`, CP-527).

### Sub-job B — `tests/`: the timed Summary's count-cell reader

**Scope:** `tests/timed_run.py` and its independent verification in
`tests/integration/test_timed_run.py`; no measured action, label, timer or fixture-volume change.

**Exposes:** the unchanged `measure_project_summary(*, site, saved_data, timer) -> list[Timed]`
contract: one Summary GET, and one timing result, with response validation outside the measured
interval (`tests/timed_run.py:1241–1266`).
The Summary checker projects ordered group/label/numeral rows from both plain count cells and the
allowed anchored count cells, preserving the existing title, heading, group, value and saved-byte
checks (design decision for CP-527 and `tests/timed_run.py:1218–1266`).
An anchor in a total, no-due-date or assignee cell, or any linked row label, remains invalid; accepting
link markup in selected cells must not erase those distinctions (CP-514;
`tests/integration/test_timed_run.py:3865–3881`, existing linked-total and linked-label refusals).
The checker establishes count validity, while § 5's page/list tests establish the exact navigation
contract; it does not follow count links or add timed actions (CP-525, CP-527).

**Depends on:** none; the HTML boundary is specified above, and the old plain-count page remains
acceptable to this measurement checker while A supplies the final link contract (design decision).

**Build sequence:** B, then A. B can have a green landing against the existing page; A consumes B's
broader count-cell reader. The old reader matches only `<td>` followed directly by digits, so A
without B breaks the measurement (`tests/timed_run.py:146,1232`).
There is no atomic-landing edge between A and B: B's dual-shape reader provides the green point.
When A lands, both the measurement reader and the independent parser/mutation helpers must understand
linked cells; leaving either direct-digit-only loses the row checks or the mutations they target
(`tests/integration/test_timed_run.py:3693,3730–3757,3857–3863,3921–3969`).

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — `web/` | Carry optional link target/name metadata alongside the existing count within the Summary renderer; keep the decision at the typed row/group boundary. Reuse the existing filter field vocabulary through `application` and the page's filter-prefix convention (`web/pages.py:1058,1427–1439`). Ordinary anchor markup and `aria-label` keep the visible numeral unchanged. All dynamic text and attribute values pass through `_escape`, not raw HTML supplied as a row value (`web/pages.py:381–383`). |
| B — `tests/` | Use structural count-cell parsing, scoped by Summary group and row position/identity, with the standard library's HTML parser. Do not strip all tags and then accept the remaining digits: that admits linked labels or forbidden linked counts. Keep the test oracle and edited-response helpers independent of the harness reader; mutations must locate real cells and assert the edited body differs from the real response. |

No sub-job writes outside the instance/product worktree (design scope).

## 5. Test Additions

Use existing test modules, so no new runtime module or test dependency is needed (design decision).
Each added test names CP rules and SRS criteria in its docstring, retaining the existing feature
trace (`docs/nfdr.md` QC-11; `domain/summary.py:15–23`).
`tests/unit/test_summary.py::test_summary_counts_only_the_requested_project` remains the domain
AC-14 proof; extend AC-14 at the real page/list boundary in `tests/integration/test_summary_routes.py`
rather than replacing that unit coverage (`change_spec.md`, Locked Answer b-3).

| Row | Sub-job | Test file | What to add / modify |
|---|---|---|---|
| T01 | A | `tests/integration/test_summary_pages.py` | Replace the pair-only expectations in `test_summary_has_all_ordered_plain_rows_and_only_allowed_links` and `test_empty_summary_invites_first_task_beside_all_zero_rows` with the pair/invitation plus exactly nine count links. Retain every existing title, heading, group, header, row value/order, escaping and no-control/no-refresh assertion; assert no anchors in labels or forbidden count cells. CP-513–CP-515; Examples Alpha Summary and Gamma Summary. |
| T02 | A | `tests/integration/test_summary_routes.py` | AC-14 extension: seed Fixture A from the spec, with Alpha in all statuses and priorities, listed and removed names, and Beta's independent task. For all nine Alpha anchors assert the exact target, numeral, and target's exact task identities and count. Use the fixture's explicit expected membership, not the product filter/summary to calculate expectations. Cover Alpha todo, in-progress, critical and overdue Examples, then the remaining status/priority rows. CP-516–CP-517, CP-523, CP-525. |
| T03 | A | `tests/integration/test_summary_routes.py` | On every T02 destination assert only the intended control is selected, all other filter controls are empty, sort controls show the existing default, and task rows follow that default. Include an added sort-discriminating fixture where creation order differs from due-date order and equal due dates retain their existing tie order. Verify seven filter fields remain. CP-516–CP-517, CP-523; Example “The filter after the change”. |
| T04 | A | `tests/integration/test_summary_routes.py` | Follow every zero status, priority and overdue link on populated Beta, including its done 0 link; require 200, the selected control, the existing no-match text, and no task row. CP-513, CP-518, CP-525; Example Beta done 0. |
| T05 | A | `tests/integration/test_summary_routes.py` | Empty Gamma: all nine links remain, each opens 200 and the existing no-tasks invitation, and none opens no-match or not-found. Keep the Summary invitation and its base Tasks target. CP-513, CP-515, CP-518; Example Gamma Summary. |
| T06 | A | `tests/integration/test_summary_pages.py`; `tests/e2e/test_summary.py` | Check names for 0, 1 and plural values in every category: numeral first, visible text an unbroken prefix, noun agreement and category meaning. Pin the two fixed CONTENT examples with counts 12 and 3. In the browser assert the computed accessible names, not just an attribute's existence. Across all Summary links, equal names imply equal destinations, including Gamma's allowed pair of Tasks links. CP-521–CP-522; Examples linked-count names and overdue 3. Exact new words come from the text artifact. |
| T07 | A | `tests/integration/test_summary_routes.py` | Capture the Summary's todo 2 link, change T1 through the real Tracker to in-progress, and follow the captured target: only T5 matches and the old Summary HTML remains unchanged. Independently advance the injected clock across local midnight after capturing the overdue link; the followed list uses the new local date. CP-519; both stale-state Examples. |
| T08 | A | `tests/integration/test_summary_routes.py`; `tests/e2e/test_summary.py` | For count GETs and reloads assert unchanged Tracker state, save-call count and saved bytes. In the browser follow, reload and go back; assert unchanged saved bytes and Summary navigation. CP-520; Example follow/reload/back. |
| T09 | A | `tests/integration/test_summary_routes.py` | Keep `test_overdue_mark_filter_and_summary_agree` intact, using its handed-in clock: yesterday/open counted, today/open not counted, final statuses not counted. Follow the Summary overdue anchor in that same world and prove the same membership. CP-526, CP-523; overdue Example. |
| T10 | A | `tests/integration/test_pages.py` | Repair only the internal-address check in `test_every_page_has_a_header_with_the_projects_and_people_links`: accept the exact one-choice project URLs for supported status/priority/overdue values. Keep the three header-link assertions on every page, existing base addresses, and no rename/delete. CP-515–CP-516; Locked Answer f-1. |
| T11 | A | `tests/e2e/test_summary.py` | Repair `test_browser_can_open_summary_and_return_to_tasks`'s main-link list; retain its title, pair, counts, empty-project invitation, no-controls and round-trip checks. Follow a count link through the real listener with scripts disabled and verify the selected filter and list; follow zero on a populated project as the key empty-result path. CP-518, CP-520, CP-528; Locked Answer f-4. |
| T12 | A | `tests/e2e/test_summary.py` | Extend keyboard proof to all nine count links, including zero. Locate by their distinct accessible names, Tab to each, assert visible focus, activate with Enter and assert its exact destination. Check each target's bounding box meets both 24-pixel dimensions. Keep the existing two-view-link proof. CP-524; Tab Example. |
| T13 | A | `tests/e2e/test_summary.py` | Retain and extend `test_summary_names_and_groups_reflow_at_four_hundred_percent`: at 320 CSS pixels, long hostile names and all new links stay within the viewport, all four groups fit, and no horizontal page scrolling occurs. CP-524; 400% Example. |
| T14 | B | `tests/integration/test_timed_run.py` | Update the independent row reader, `_summary_row`/edited-response helpers, swap-count tests and midnight mutation to handle actual linked cells. Positive checks accept the real linked Summary and a correct bare-count projection. Keep every current wrong-count, missing-row, swapped-category, assignee-case/order, wrong-title/heading/status/media-type, changed-bytes and midnight-boundary rejection. Every mutation must change the response before its rejection is asserted. CP-527; Locked Answer f-3. |
| T15 | B | `tests/integration/test_timed_run.py` | Preserve the “a linked count” rejection: it links Total, which CP-514 still forbids. Preserve “a linked label”. Add equivalent forbidden no-due-date and assignee-cell anchors, including assignees named like status/priority/Overdue labels; keep exact row/value agreement rather than accepting any text containing a numeral. CP-514, CP-527. |
| T16 | B | `tests/integration/test_timed_run.py` | Keep strict one-second boundary, one same-origin Summary GET, 1000 tasks × 20 comments, saved-byte invariance, measurement readbacks outside the interval, every existing run label/order and Summary last. Run `python3 tests/timed_run.py` from the product root; add no timed request or line. CP-527; timed-run Example. |
| T17 | A + B, separately scoped | Existing suite commands | `pytest products/tracker17/tests/` and separately `pytest products/tracker17/tests/e2e/`, from the instance worktree; from the product root, `ruff format --check .`, `ruff check .`, `mypy main.py errors.py domain application persistence web`. These are the CP-528 Examples and NFDR QC-62 gates, not a claim they ran during design. |
| T18 | A | `tests/integration/test_summary_pages.py` | Place listed/unlisted assignees named `todo`, `low`, `Overdue`, and `(unassigned)` beside the real categories/unassigned bucket; all assignee counts remain plain. Preserve hostile project/assignee text escaping, padding and long-name checks. CP-514–CP-515, NFDR QC-36; rule-implied identity/escaping edges. |

**Coverage walk:** CP-513 → T01, T04–T05; CP-514 → T01, T15, T18; CP-515 → T01, T05,
T10–T11; CP-516 → T02–T04, T10; CP-517 → T02–T03; CP-518 → T04–T05, T11;
CP-519 → T07; CP-520 → T08, T11; CP-521–CP-522 → T06;
CP-523 → T02–T03, T09; CP-524 → T12–T13; CP-525 → T01–T06;
CP-526 → T09; CP-527 → T14–T16; CP-528 → T17.
Every Example in `change_spec.md`, **Examples**, is identified in the rows above.
Zero/nonzero, singular/plural, same-numeral names, empty/populated projects, stale data/day,
forbidden links and category-like assignee names have explicit rows rather than implied coverage.

**Assertions retired:** only the prohibition on links in the nine selected count cells and the
pair-only main-link inventories are withdrawn, as `change_spec.md`, Locked Answers f-2, f-4 and
f-5 authorize; T01, T06 and T11 replace them with exact selected-link and plain-cell assertions.
The direct-digit-only readers and literal row-edit helpers are replaced by T14's structural
checks; their count, ordering and rejection clauses remain proved by T14–T16.
The linked-Total rejection is retained by T15, not retired merely because its case name says
“a linked count” (`tests/integration/test_timed_run.py:3865–3872`).

## Records this change makes false

None — read `docs/adr/README.md` and ADR-0001–ADR-0011 (ADR-0006 is superseded),
`docs/nfdr.md` §§ 1–2, 5, 8–9 and RN-33, `docs/fdr.md`'s Rules and Product decisions, and
`docs/SDD.md` § 3 and S-6; the design adds no part, import, saved field or rule that makes a
sentence in those records false.
The plain-count constraint being replaced is the prior change's CP-503, explicitly withdrawn by
this spec's Locked Answer f-5; the existing unreadable-data gap remains in `deferred_decisions.md`
rather than being newly caused by this design.

## Architect Review Notes

- **(a) CP-525's fixture contradiction:** `change_spec.md:51` requires tasks in every status and
  priority, while `change_spec.md:56` requires a zero in at least one of those buckets on that
  project. Take the multi-project reading: keep Alpha's full membership fixture, and prove zero
  navigation on populated Beta, exactly as the spec's Beta done 0 Example does. Dropping one Alpha
  category to create a zero would lose the full-membership exercise; requiring both simultaneously
  is impossible. Gamma remains the separate no-tasks case. Only the same-project placement of the
  zero case is set aside, recorded in `deferred_decisions.md`; no product behaviour is changed.
- **(b) Explicit URL and cell ownership:** construct targets from the summary's project identity
  and category identity, with one query pair, rather than retaining the Summary request's query
  string. Classify cells by group/typed row, never visible labels. These choices realize CP-514,
  CP-516 and CP-523 by construction and handle assignee names matching category words.
- **(b) Accessible-name placement and target sizing:** use `aria-label` and a count-link style
  satisfying the 24-by-24 floor, rather than an exception. This keeps the visible number exact
  while giving the browser the contextual name CP-521 requires. Wording remains the text
  artifact's; this design fixes its placement and inputs only (CP-515, CP-521–CP-524).
- **(d/e) Supporting harness sub-job:** the SDD parts table covers runtime parts, not a measurement
  harness. B belongs in the existing `tests/` boundary, not a sixth runtime part, because CP-527
  explicitly requires that harness to accept the rendered count cells. A and B are separate
  sub-jobs; B-first's dual-shape projection provides a green point. B includes both
  its checker and independent oracle/mutation helpers, whose existing direct-digit shape is
  visible at `tests/timed_run.py:146` and `tests/integration/test_timed_run.py:3693,3730`.
- **Delegated NFDR review — QC-8, QC-12, QC-23, QC-27: pass.** Anchor metadata is local to one
  page build; no request state, new part, count rule, clock or file access is introduced.
  Domain/application contracts stay unchanged, so the interface remains replaceable as required
  (`docs/nfdr.md:84–90,138–143,221–246`; SDD § 3 placement above).
- **Delegated NFDR review — QC-36: pass.** `_escape` remains the single escaping boundary for
  dynamic labels, names and attribute values; row rendering receives structured count/link data,
  not arbitrary trusted HTML. Targets contain project identities and supported category values,
  never a project or assignee name (`web/pages.py:381–383,1442–1509`; T01, T18).
- **Delegated NFDR review — QC-41, QC-60: pass for this design.** No account, key, credential,
  dependency or saved field is introduced. Native anchors, CSS, `aria-label` and standard-library
  HTML parsing require no Python feature beyond the declared 3.11 floor
  (`docs/nfdr.md:358–362,498–506`; `pyproject.toml:1–4`).
- **Delegated NFDR review — conditional gates:** QC-5's refusal-handling review, QC-20–QC-22's
  inner-part reviews, QC-24's wiring review, QC-25–QC-26's saving reviews and QC-46's saved-field
  review have no changed subject in this design; the reviewed `web` work is confined to page
  building and styles (`docs/nfdr.md` §§ 1.1, 1.3–1.4, 4; § 2 blast radius above).
- **Delegated NFDR review — QC-40, checked 2026-10-28:** the cached browser's Info.plist reports
  `153.0.8010.12` (`plutil -extract CFBundleShortVersionString raw` against
  `~/Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/Info.plist`
  → `153.0.8010.12`). Google's October releases list newer critical fixes
  ([vendor releases](https://chromereleases.googleblog.com/2026/10/)). The owner's exception covers
  this exact build through 2026-11-07, so the browser does not block this review
  (`docs/nfdr.md:1028–1040`, RN-33). Do not treat that exception as covering another build.
- **QC-40 package-review evidence and limit:** reviewed the pins in `tests/requirements.txt:5–19`,
  their PyPI release metadata, and the maintainers' advisory pages for
  [Playwright](https://github.com/microsoft/playwright/security/advisories),
  [Playwright Python](https://github.com/microsoft/playwright-python/security/advisories),
  [mypy](https://github.com/python/mypy/security/advisories),
  [pytest](https://github.com/pytest-dev/pytest/security/advisories),
  [Ruff](https://github.com/astral-sh/ruff/security/advisories),
  [Pygments](https://github.com/pygments/pygments/security/advisories),
  [greenlet](https://github.com/python-greenlet/greenlet/security/advisories) and
  [packaging](https://github.com/pypa/packaging/security/advisories).
  No blocking package advisory was identified in the linked vendor feeds and searches against all
  names in `tests/requirements.txt:5–19`. This is a bounded published-source
  review, not an automated clean audit: the web-rendered release JSON did not expose all advisory
  arrays, and the local metadata fetch reported DNS errors. No pin or lock-format change is
  proposed; the dated browser exception is the applicable known-advisory verdict.
- **Language resolution:** Python, step 1, `project.md` **Languages**; opened
  `<CORE>/doctrine/engineering/languages/python/README.md` and the testing doctrine it routes.
- **Cold-read:** the nine design checks were walked: placement/imports, interfaces/order,
  Examples and rule edges, explicit target construction, divergence capture, records, settled
  text verdict and write scope are accounted for in §§ 2–5 and these notes. Product suites and
  timed acceptance were not run in this design stage.
