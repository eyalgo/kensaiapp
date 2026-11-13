# Change Design — a project's summary shows the due-on-date count

**Date:** 2026-11-13
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the label of the new row in the Summary page's "Due dates" group, the words before its date
<!-- Decided by the CP-438 test: does this change put text in front of a person to read? `yes` names each place, as the person knows it. Otherwise write `no`. The chain reads the first word, which must be exactly `yes` or `no`. -->
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with `toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md` and `<CORE>/doctrine/engineering/testing_python.md`

---

## 1. Change Summary

The Summary gains a `Due on {date}` row directly after `Overdue`. `domain/summary.py` works out the count and carries the date it was worked out on. `web/pages.py` shows the row. `ProjectSummary` gains two required fields: `due_today`, the count, and `today`, the summary's date. `summarize_project` sets `today` from the `today` it is handed, the same value every count of that summary uses. So the label's date and both counts come from one date by construction (CP-809). `application` already reads the clock once per summary and passes that date in (`Tracker.project_summary`), so it does not change. Paths are relative to the product root.

---

## 2. Blast Radius

New logic and its owning part (SDD § 3): **the due-on-date count** is a summary computation, so it belongs to `domain` ("the filter, sort and summary computations"). **The row and its label** are page building, so they belong to `web`. `web` "shows what `application` returns" and decides no count.

| Module | Status | What changes |
|---|---|---|
| `domain/` | Modified | `domain` part, summary computation: `ProjectSummary` gains `due_today: int` directly after `overdue`, and `today: date` directly after `project`, both required. `summarize_project` sets `today` to its `today` argument. It sets `due_today` to the number of the project's tasks with `due_date == today` and `status.is_open`. The module docstring adds the count to what it realizes (FR-38, AC-13) and adds the checking modules this change touches. |
| `web/` | Modified | `web` part, page building: `summary_page`'s "Due dates" rows become `Overdue` (linked, unchanged), then a plain `_SummaryRow` labelled with the words from `change_text.md` followed by `summary.today` as `YYYY-MM-DD` and counting `summary.due_today`, then `No due date` (unchanged). The function docstring's list of plain counts names the new one. |
| `application/` | Unchanged | It re-exports `ProjectSummary` by name (`application/__init__.py`), and the new fields travel with it. `Tracker.project_summary` already reads the clock once and hands that one date to `summarize_project`. |
| `persistence/` | Unchanged | — (nothing is saved: SRS RN-26) |
| `main.py`, `errors.py` | Unchanged | — |

Transitive check (NFDR § 1.2): `ProjectSummary`'s public interface changes, and the field order changes. Its importers are `application` (a by-name re-export, unchanged), `web/pages.py` (modified above) and the two test sites that build one directly: `tests/integration/test_pages.py:146` (positional) and `tests/integration/test_summary_pages.py` `make_summary` (keywords). Both are covered in § 5. The tests that call `summarize_project` are unaffected, because its signature stays as it is. No other module imports it.

---

## 3. Sub-jobs

### Sub-job A — `domain/`
**Scope:** the two fields on `ProjectSummary`, setting them in `summarize_project`, and the module docstring.
**Exposes:** `ProjectSummary(project, today, total, status_counts, priority_counts, overdue, due_today, no_due_date, assignee_counts)`. `today: date` is the date every count in the summary was worked out against. `due_today: int` is the number of the project's tasks whose due date equals `today` and whose status is open (`todo`, `in-progress`). `summarize_project(state, project_id, today)` keeps its signature and its `None` for an unknown project.
**Depends on:** none

### Sub-job B — `web/`
**Scope:** the new row in `summary_page`'s "Due dates" group, and its docstring.
**Exposes:** nothing new. The page's "Due dates" group reads, in this order: `Overdue` (a link), `<words> YYYY-MM-DD` (a bare numeral), `No due date` (a bare numeral).
**Depends on:** Sub-job A (reads `ProjectSummary.today` and `ProjectSummary.due_today`)

**Build sequence:**
```
Start: Sub-job A
After A: Sub-job B
```

**Atomic-landing edge:** Sub-job B + the timed run's Summary check (`tests/timed_run.py` `_summary_expected`) + its harness test (`tests/integration/test_timed_run.py` `_summary_oracle` and its cell lists) + the "Due dates" rows assertion in `tests/integration/test_summary_pages.py` — no green point between them. Once the page shows the row, the harness refuses the real page until its expected rows include the row (spec, Verified Claims, Gap 6). Until the page shows the row, a harness that expects it refuses the page.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — `domain/` fields and count | Count over the `everything` selection `summarize_project` already takes, the way `no_due_date` is counted, with open membership from `TaskStatus.is_open`. Overdue is `due_date < today` and the new count is `due_date == today`, against the one `today`, so no task is in both counts. Do not add a filter field or a `due_dates.py` predicate. Nothing outside the summary uses this rule (OOS-17). |
| B — `web/` row | The row is a `_SummaryRow` with no link, so `_summary_cell` already writes a bare `<td>` with no `aria-label` (CP-812). The label goes through `_summary_group`'s `_escape` like every label (QC-36). The date part is `date.isoformat()`. The words come from `change_text.md`, and only `web` holds them (CP-819, QC-20). |

---

## 5. Test Additions

Every product test hands the date in: as a value at layers 1 and 4, through a clock the suite already has at layer 3 (CP-815, CP-818). No product name is patched (QC-28). No new class stands in for the clock or the saver.

| Sub-job | Test file | Layer | Fakes handed in | What to add / modify |
|---|---|---|---|---|
| A | `tests/unit/test_summary.py` | 1 — Unit | none — the state and the date are values | New: FDR Example 1. Today 2026-10-06: A `todo` due 10-06, B `cancelled` due 10-06, C `in-progress` due 10-05 → `overdue` 1, `due_today` 1 (CP-808, CP-810). |
| A | `tests/unit/test_summary.py` | 1 — Unit | none | New: `in-progress` due today and `done` due today → `due_today` 1, `overdue` 0 (CP-810). |
| A | `tests/unit/test_summary.py` | 1 — Unit | none | New: `todo` due tomorrow and `todo` with no due date → `due_today` 0, `overdue` 0, `no_due_date` 1 (CP-808). |
| A | `tests/unit/test_summary.py` | 1 — Unit | none | New: another project's open task due today → this project's `due_today` 0 (CP-808). |
| A | `tests/unit/test_summary.py` | 1 — Unit | none | New: a project with no tasks → `due_today` 0 and `today` equal to the date handed in (CP-809, CP-813). |
| A | `tests/unit/test_summary.py` | 1 — Unit | none | Module docstring names AC-13 and the new CP rules. |
| A | `tests/integration/test_summary_tracker.py` | 3 — Application | `FakeSaver` (`tests/fakes.py`) and the module's existing `SequenceClock`, handed to `Tracker` | New, AC-13's due-today side through a handed-in clock (CP-815): clock at `NOON` in `utc_zone`. An open task due 2026-10-27 is in `due_today` and not in `overdue`. A `done` task and a `cancelled` task due that day are in neither. |
| A | `tests/integration/test_summary_tracker.py` | 3 — Application | the same | New, FDR Example 6 (CP-809): `SequenceClock(NOON, NEXT_NOON)`, an open task due 2026-10-27. The first summary reads the clock once and gives `today` 2026-10-27, `due_today` 1, `overdue` 0. The second gives `today` 2026-10-28, `due_today` 0, `overdue` 1. |
| A | `tests/integration/test_summary_tracker.py` | 3 — Application | the same, in `local_zone` | New (CP-809, the machine's local date): at `NOON`, which is 2026-10-28 at UTC+14, `today` is 2026-10-28, and a task due 2026-10-28 is in `due_today`. Module docstring names AC-13. |
| A | `tests/integration/test_pages.py` | 4 — UI | none | Modify only the `ProjectSummary(...)` call at :146 to carry `today` and `due_today` in their new positions. No assertion changes. |
| A | `tests/integration/test_summary_pages.py` | 4 — UI | none | `make_summary` gains `due_today` (default 0) and `today` (a fixed default date) keywords. Every existing call stays as it is, so the all-zero assertion of `test_empty_summary_invites_first_task_beside_all_zero_rows` keeps passing unchanged. |
| B | `tests/integration/test_summary_pages.py` | 4 — UI | none | Modify `test_summary_has_all_ordered_plain_rows_and_only_allowed_links`: its "Due dates" rows become `Overdue`, `Due on <date>`, `No due date`. Its nine linked rows, headings, and no-form, no-script assertions are unchanged (Gap 6 (1)). |
| B | `tests/integration/test_summary_pages.py` | 4 — UI | none | New: a no-tasks summary page dated 2026-11-13 → "Due dates" reads `Overdue` 0, `Due on 2026-11-13` 0, `No due date` 0, and the invitation shows (CP-811, CP-813, CP-816). |
| B | `tests/integration/test_summary_pages.py` | 4 — UI | none | New: the `Due on` cell is a bare numeral with no `a` and no `aria-label`. The page holds nine count links, unchanged. No text on the page matches `today` as a whole word in any case (CP-811, CP-812). |
| B | `tests/integration/test_summary_routes.py` | 3 — Application | the existing `MovableClock`, handed to the `Tracker`, with the real `Site` and `SavedData` | New, a built project (CP-816): open tasks due today in `todo` and `in-progress`, and tasks due today in `done` and `cancelled`. Also one due yesterday, one due tomorrow, one undated, and another project's open task due today. GET the Summary. The "Due dates" rows are exactly `Overdue` 1, `Due on <clock's date>` 2, `No due date` 1. Module docstring names the new CP rules. |
| B | `tests/timed_run.py` | the timed run (SDD § 4 TS-5, NFDR QC-48) | — | `_summary_expected` adds `Due on <day>` between `Overdue` and `No due date`, counted by plain comparison of each task for the day being tried, so the existing two-day tolerance covers the label too (CP-821, Gap 6 (2)). `SUMMARY_LINKED_ROWS` already allows an anchor only at the group's first row, so the new row is held to a bare cell with no change there. |
| B | `tests/integration/test_timed_run.py` | 3 — Application (the module's own layer) | none beyond what the module already hands the harness | `_summary_oracle` gains the same row. The `Due on` cell joins `OUTSIDE_THE_NINE`, and its label joins the label list. So an anchored count or label on that row fails the measurement. A page with the `Due on` row dropped fails it too (CP-812, CP-821). |
| A | `tests/architecture/test_trace.py` | 6 — Architecture | none | `SUMMARY_REQUIREMENTS` gains `AC-13`, so the pointer test fails if the entry docstring stops naming it (CP-817). |

**Coverage of the spec's Examples:** 1 → the first unit row; 2 → the second; 3 → the third; 4 → the fourth; 5 → the no-tasks unit row and the no-tasks page row; 6 → the `SequenceClock(NOON, NEXT_NOON)` row; 7 → the bare-cell page row plus the unchanged nine-link assertions; 8 → the card's two test commands, the QC-62 gates and the timed run, which CP-820 and CP-821 hold as commands; 9 → the CP-822 grep, run by hand before and after. It is an acceptance command, not a test.

**Rule-implied edges:** no due date → the third unit row. Due after the date → the third unit row and the routes row. Due before the date → the first unit row. Another project → the fourth unit row and the routes row. An empty project → the no-tasks rows. The date changing mid-summary → the `SequenceClock` row. A local date that differs from UTC → the `local_zone` row. CP-814 (Overdue unchanged) is covered by the existing `test_summary_overdue_uses_the_supplied_date`, `test_overdue_mark_filter_and_summary_agree`, `test_overdue_filter_and_row_marking_agree` and the browser `test_browser_can_open_summary_and_return_to_tasks`, all unchanged. CP-818 and CP-819 are covered by design (no stand-in added; words only in `web`) and the QC-20 review below. CP-820 is covered by the three QC-62 gates.

**What stops being proved:** nothing. The two rows-list assertions Gap 6 names keep every row they assert today and add one. The `test_pages.py` call changes its arguments only.

---

## Testing the change from outside the code

- The `Due on {date}` row, its place, its count, its plain cell and the empty project's 0 are reached through the browser, the way in NFDR § 9 records (`**Behave way in:** browser`). QA's scenarios in `.behave/features/summary_due_on_date.feature` add tasks through the tracker's own pages, open the Summary, and read the "Due dates" group's rows and cells. This design meets them as written: the label is the words then the `YYYY-MM-DD` date, and the cell is a bare numeral with no link and no name. The midnight case cannot be driven through the browser. The `SequenceClock` row in § 5 covers it.

---

## Records this change makes false

None — read `docs/adr/` (0001–0016 and its README), `docs/nfdr.md` (version 32), `docs/fdr.md` (version 8, R-129 to R-131, OOS-17) and `docs/SDD.md` § 3 and § 6 S-6. Each already states the due-on-date count as wanted, and none says the product lacks it. `docs/what_left.md`'s entry for this count is removed by the change's `changelog-line` step, not by this design.

---

## Architect Review Notes

- **(b) The date travels on the summary:** `ProjectSummary` carries `today`, and the page's label reads it from there. CP-809 asks that the label's date be the one both counts used. Carrying the date on the value that holds the counts makes that true by construction. A second clock read or a date passed to `summary_page` separately could drift from the counts. `summary_page`'s signature stays as it is.
- **(b) Both new fields are required, with no default:** a defaulted `today` or `due_today` would let a builder leave out the date or the count without anyone noticing. So the two test construction sites (§ 5) change, and the test helper `make_summary` carries the defaults instead.
- **(b) Field placement:** `due_today` sits directly after `overdue`, matching the page order the class docstring promises. `today` sits after `project` because it is not a count. The positional call in `test_pages.py` follows.
- **(b) The count is inline in `summary.py`, with no `due_dates.py` predicate:** the overdue rule sits in `due_dates.py` because the list marking, the filter and the summary all share it. The due-on-date count has one user, the summary (OOS-17: no marker, no filter). This also keeps QC-12's "no part no requirement pays for".
- **(e) Test code has no owning part:** the new tests sit in the summary's existing test modules, which `domain/summary.py`'s docstring already names, so the trace test needs no new path.
- **Packet check, no conflict:** `domain` reads no clock and gets `today` as an argument (`conventions.md` § Constructs, the four layers). The new fields are on a frozen dataclass (QC-6). No collaborator is built inside a unit. Unit and page tests touch nothing real. The layer-3 tests reuse `SequenceClock` and `MovableClock`, which sit outside `tests/fakes.py` against `testing_python.md` § Rules. NFDR QC-64 and RN-65 already record that state as unmet until the change that moves them, and spec Gap 7 keeps that change separate. This change adds no stand-in, so no packet departure is handed on.
- **QC-20 review (no wording in `domain`), pass:** the words `Due on` and the date's text form live only in `web`, and `domain` holds the field names `today` and `due_today`.
- **QC-23 review (`web` owns no rule), pass:** `web` writes the date as text and decides no count and no membership.
- **QC-8 review (`web` keeps nothing between requests), pass:** no module-level value is added. The words are a constant.
- **QC-36 review (one escaping function), pass:** the label goes through `_summary_group`'s `_escape`, like every Summary label.
- **QC-27 review, pass:** the browser interface is not replaced. `domain`, `application` and `persistence` change no wiring.
- **QC-12 review, pass:** two fields, one row and their tests. FR-38 and AC-13 pay for each.
- **QC-60 review, pass:** only Python 3.11 standard library (`date.isoformat`, equality on `date`).
- **QC-41 review, pass:** no secret is read, held or written.
- **QC-46 review, not triggered:** no saved field is added (SRS RN-26).
- **QC-5, QC-21, QC-22, QC-24, QC-25, QC-26 and QC-39's `.behave` lock check, not triggered:** this design adds no refusal and changes no code in `application`, `persistence` or `main`. It leaves the saving contract alone. QA's red changed no `.behave/pyproject.toml` or `.behave/uv.lock` (diff from the base commit to the branch head).
- **QC-40 review, every-review moment, packages: met.** All 27 pinned packages in `uv.lock` and `.behave/uv.lock` were checked against OSV's PyPI advisories on 2026-11-13, and none has one. No dependency is added or moved.
- **QC-40 review, every-review moment, browser build: not blocking, owed by 2026-12-11.** The pinned build is Chromium 158.0.8127.18. The vendor's release feed was read on 2026-11-13. Its newest Critical advisories are in the Stable Channel Update for Desktop of 2026-11-11 (157.0.8103.78): CVE-2026-126885, CVE-2026-126895, CVE-2026-126879, CVE-2026-126846 and CVE-2026-126911. The Early Stable Update of 2026-11-12 (158.0.8127.36/.37) names no security fixes. The vendor does not say whether 158.0.8127.18 carries the 2026-11-11 fixes, so this review treats the build as affected. The advisories are 2 days old, inside the 30-day window.
- **QC-40 review, package feed: down, moment still owed.** The checking account has admin on the repository that holds tracker17. The Dependabot alerts endpoint answered "Dependabot alerts are disabled for this repository." (403), and the SBOM export answered 404. By QC-40's words the feed is down, so no discrepancy is raised.
