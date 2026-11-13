# Tech Lead instruction — summary-shows-due-today: a project's summary shows the due-on-date count

**Category:** feature
**Behaviour:** changing
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with `toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md` and `<CORE>/doctrine/engineering/testing_python.md`
**Product root:** `products/tracker17` — every path below is relative to it.
**Scope:** `ProjectSummary` gains `today` and `due_today`; `summary_page` shows a `Due on {date}` row directly after `Overdue`; the timed run's Summary check and its harness test hold the page to the row; the summary's trace names AC-13.

---

## Project layout

```
products/tracker17/
  domain/
    summary.py                              ← modified (two fields, the count, module docstring)
  web/
    pages.py                                ← modified (summary_page row and docstring)
  application/                              unchanged (re-exports ProjectSummary by name; one clock read per summary)
  persistence/                              unchanged
  tests/
    unit/test_summary.py                    ← modified (new tests, module docstring)
    integration/test_summary_tracker.py     ← modified (new tests, module docstring)
    integration/test_summary_pages.py       ← modified (make_summary keywords, rows assertion, new tests)
    integration/test_summary_routes.py      ← modified (new test, module docstring)
    integration/test_pages.py               ← modified (the ProjectSummary(...) call only)
    integration/test_timed_run.py           ← modified (_summary_oracle, OUTSIDE_THE_NINE and its label list)
    architecture/test_trace.py              ← modified (SUMMARY_REQUIREMENTS)
    timed_run.py                            ← modified (_summary_expected)
```

No new file, directory or `__init__.py`. `docs/SDD.md` § 3 is the parts table: `domain` owns the summary computations, `web` owns page building and decides no count. `tests/fakes.py` is not touched.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Atomic landing found beyond §3's edge:** both fields of `ProjectSummary` are required with no default (the design's own choice), so the moment `domain/summary.py` gains them, the two construction sites — `tests/integration/test_pages.py` (the positional call) and `make_summary` in `tests/integration/test_summary_pages.py` — fail to build a summary. They are in Task 1, not left to a later task, because no task boundary between them leaves the suite green. The design lists them in §5 under sub-job A and in its transitive check, so this places them and adds nothing.
- **Task cut from §3:** sub-job A is Task 1 and sub-job B is Task 2, in the design's build order, which `docs/nfdr.md` § 1.2 allows (`web` imports `application`, which re-exports `domain`'s value). §3's atomic-landing edge binds all of Task 2: the page row, the timed run's expected rows, its harness test and the rows assertion are one task.
- **Trace test goes with its docstring, in Task 1:** `tests/architecture/test_trace.py` gains `AC-13` in `SUMMARY_REQUIREMENTS` and `domain/summary.py`'s docstring names AC-13 in the same task, so the pointer test is red first (the docstring does not name AC-13) and green after.
- **Behaviour locked — what a due date equal to the date and a closed status means:** spec CP-810 covers `done` and `cancelled` due on the date. The plan makes every status outside `todo` and `in-progress` follow from `TaskStatus.is_open`, so no test names a third status, and none exists today. The membership is read from `is_open`, never from a list of status words in the new code.
- **Label words not in the plan:** the design says the label's words come from `change_text.md` (`Publishes text: yes`), written by the Content Editor between this plan and the implementation. The plan quotes them only as the spec's examples do (`Due on 2026-11-13`). The developer takes the words from `change_text.md` verbatim, in `web/pages.py` and in the expected strings the tests assert, and records any string that cannot be placed as written in Developer Review Notes.
- **Gate command checked:** the card's `Test command:` was run once under `--collect-only` at the base: the first command collects 3372 tests (the `e2e` folder included) and the second 122, so the gate runs tests. The spec's claims ran the same commands, so every `#### Verification gate` below carries the card's command and adds the checks CP-820 to CP-822 name.
- **No hint dropped, none rewritten.** §4's hints for A and B are carried as written, each cut to the approach.

## Corrections owed while there

- Owed outside this change's reach: `docs/what_left.md` — its entry for the project summary's due-on-date count will state a count the tracker lacks → the entry is gone once the count lands.

No other record states the count as absent: `change_design.md` § *Records this change makes false* reads `None`, and the walk found no stale sentence in a file a task opens.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {"finding": "none",
         "inventory": "git ls-files filtered for CI configuration paths (.github/, .gitlab-ci, .circleci/, azure-pipelines, Jenkinsfile, .travis, bitbucket-pipelines, .drone, .buildkite/, .woodpecker, cloudbuild) returned nothing: 0 files"},
  "decisions": {"override": null, "amd64": null},
  "candidates": [],
  "guest": null
}
```

The product records no environment entry in § 8 of `docs/nfdr.md` (no `environment:` field is in the file), and no CI configuration is tracked, so no tag has a source to quote and no candidate is written.

---

### Task 1: The summary carries its date and its due-on-date count (`domain/summary.py`)

**Dependencies:** None

**What to build:** `ProjectSummary` gains `today: date`, directly after `project`, and `due_today: int`, directly after `overdue`, both required, so its fields read `project, today, total, status_counts, priority_counts, overdue, due_today, no_due_date, assignee_counts`. `summarize_project` keeps its signature and its `None` for an unknown project; it sets `today` to the `today` it was handed and `due_today` to the number of the project's tasks whose due date equals `today` and whose status is open. The module docstring names AC-13 and the new rules among what it realizes, and its list of checking modules stays true. The two sites that build a `ProjectSummary` move to the new field order in this same task (TL Review Notes, first entry): the positional call in `tests/integration/test_pages.py` carries `today` and `due_today` in their new positions with no assertion changed, and `make_summary` in `tests/integration/test_summary_pages.py` gains `due_today` (default 0) and `today` (a fixed default date) keywords so every existing call stays as it is. `tests/architecture/test_trace.py`'s `SUMMARY_REQUIREMENTS` gains `AC-13`.

#### Behaviours to verify (developer adds tests to `tests/unit/test_summary.py` and `tests/integration/test_summary_tracker.py`)

- `test_an_open_task_due_today_is_counted_and_not_overdue` — layer 1 Unit — fakes: none, the state and the date are values — today 2026-10-06; A `todo` due 10-06, B `cancelled` due 10-06, C `in-progress` due 10-05 → `due_today` 1 and `overdue` 1 (FDR Example 1; CP-808, CP-810).
- `test_in_progress_due_today_counts_and_done_due_today_does_not` — layer 1 Unit — fakes: none — an `in-progress` task and a `done` task both due on the date → `due_today` 1, `overdue` 0 (CP-810).
- `test_tasks_due_tomorrow_or_undated_are_not_due_today` — layer 1 Unit — fakes: none — a `todo` due the day after and a `todo` with no due date → `due_today` 0, `overdue` 0, `no_due_date` 1 (CP-808).
- `test_another_projects_task_due_today_is_not_counted` — layer 1 Unit — fakes: none — an open task of another project due on the date → this project's `due_today` 0 (CP-808).
- `test_an_empty_project_has_zero_due_today_and_carries_the_date` — layer 1 Unit — fakes: none — a project with no tasks → `due_today` 0 and `today` equal to the date handed in (CP-809, CP-813).
- `test_summary_due_today_side_of_ac13_through_a_handed_in_clock` — layer 3 Application — fakes: `FakeSaver` from `tests/fakes.py` handed to `Tracker`, and the module's existing `SequenceClock` handed to `Tracker`, at `NOON` in `utc_zone` — an open task due 2026-10-27 is in `due_today` and not in `overdue`; a `done` and a `cancelled` task due that day are in neither (CP-815).
- `test_one_summary_uses_one_date_for_both_counts_across_midnight` — layer 3 Application — fakes: `FakeSaver`, `SequenceClock(NOON, NEXT_NOON)` — an open task due 2026-10-27: the first summary gives `today` 2026-10-27, `due_today` 1, `overdue` 0; the second gives `today` 2026-10-28, `due_today` 0, `overdue` 1 (FDR Example 6; CP-809).
- `test_due_today_uses_the_machine_local_calendar_day` — layer 3 Application — fakes: `FakeSaver`, `SequenceClock` at `NOON`, in `local_zone` — `NOON` is 2026-10-28 at UTC+14, so `today` is 2026-10-28 and a task due 2026-10-28 is in `due_today` (CP-809).
- `test_summary_trace_names_ac13` — layer 6 Architecture — fakes: none — `SUMMARY_REQUIREMENTS` holds `AC-13`, and `tests/architecture/test_trace.py` passes only while `domain/summary.py`'s opening docstring names it (CP-817). The `test_pages.py` call and `make_summary` carry no test of their own: every existing test that builds a summary through them must still pass unchanged.

Every new test hands the date in as a value or through the suite's existing clock, patches no name inside a product module, and adds no class that stands in for the clock or the saver (CP-815, CP-818). The two test modules' own docstrings name AC-13 and the new CP rules (CP-817).

#### Implement

Infer from failing tests.

# Hint: count over the `everything` selection `summarize_project` already takes, the way `no_due_date` is counted, with open membership from `TaskStatus.is_open`. Overdue is `due_date < today` and the new count is `due_date == today`, against the one `today`, so no task is in both counts. Do not add a filter field or a `due_dates.py` predicate; nothing outside the summary uses this rule (OOS-17).

#### Verification gate

Run the card's `Test command:` from the worktree root: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`.

Pass criteria: this task's tests pass; the existing Overdue tests (`test_summary_overdue_uses_the_supplied_date`, `test_overdue_mark_filter_and_summary_agree`, `test_overdue_filter_and_row_marking_agree`) pass unchanged; no new failures elsewhere, `tests/architecture/test_trace.py` and `tests/architecture/test_shapes.py` included.

---

### Task 2: The Summary page shows `Due on {date}` and the timed run holds the page to it (`web/pages.py`, `tests/timed_run.py`, `tests/integration/test_timed_run.py`, `tests/integration/test_summary_pages.py`, `tests/integration/test_summary_routes.py`)

**Dependencies:** Task 1

**What to build:** in `summary_page`, the "Due dates" rows become `Overdue` (linked, unchanged), then a plain `_SummaryRow` whose label is the words from `change_text.md` followed by `summary.today` as `YYYY-MM-DD` and whose count is `summary.due_today`, then `No due date` (unchanged). The row carries no link and no accessible name of its own, so the Summary's count links stay the nine they are. The label's words are held in `web` only, and the function docstring's list of plain counts names the new one. Because the page then shows a row the timed run does not expect, the same task changes `tests/timed_run.py`'s `_summary_expected` to add `Due on <day>` between `Overdue` and `No due date`, counted by plain comparison of each task for the day being tried; `_summary_oracle` in `tests/integration/test_timed_run.py` gains the same row, its `Due on` cell joins `OUTSIDE_THE_NINE` and its label joins the "Due dates" label list; and the "Due dates" rows assertion in `test_summary_has_all_ordered_plain_rows_and_only_allowed_links` becomes `Overdue`, `Due on <date>`, `No due date`, keeping every other row, the nine linked rows, the headings and the no-form, no-script assertions.

#### Behaviours to verify (developer adds tests to `tests/integration/test_summary_pages.py`, `tests/integration/test_summary_routes.py` and `tests/integration/test_timed_run.py`)

- `test_summary_has_all_ordered_plain_rows_and_only_allowed_links` (modified, not renamed) — layer 4 UI — fakes: none, the summary is built by `make_summary` — the "Due dates" rows read `Overdue`, `Due on <date>`, `No due date`; every other assertion in it is unchanged (Gap 6 (1)).
- `test_empty_summary_shows_due_on_zero_among_all_zero_rows` — layer 4 UI — fakes: none — a no-tasks summary dated 2026-11-13 → "Due dates" reads `Overdue` 0, `Due on 2026-11-13` 0, `No due date` 0, and the invitation to add a first task shows (CP-811, CP-813, CP-816).
- `test_due_on_cell_is_a_bare_numeral_with_no_link_or_name` — layer 4 UI — fakes: none — the `Due on` cell holds no `a` and no `aria-label`; the page holds nine count links, as before; no text on the page matches `today` as a whole word, in any case (CP-811, CP-812).
- `test_summary_of_a_built_project_counts_due_on_the_date_and_excludes_the_rest` — layer 3 Application — fakes: the existing `MovableClock` handed to the `Tracker`, with the real `Site` and `SavedData` — open tasks due today in `todo` and in `in-progress`, tasks due today in `done` and in `cancelled`, one task due yesterday, one due tomorrow, one undated, and another project's open task due today; GET the Summary → the "Due dates" rows are exactly `Overdue` 1, `Due on <the clock's date>` 2, `No due date` 1 (CP-816).
- `test_timed_summary_check_holds_the_page_to_the_due_on_row` — layer 3 Application, the module's own layer — fakes: none beyond what `tests/integration/test_timed_run.py` already hands the harness — the real page, with its `Due on` row, passes the harness check; a page with the row dropped fails it; an anchored count or label on the `Due on` row fails the measurement (CP-812, CP-821).
- `test_timed_summary_oracle_reads_the_real_page_as_the_fixture_says` (modified, not renamed) — layer 3 Application — fakes: as above — the oracle's rows, now with the `Due on` row between `Overdue` and `No due date`, equal the real page's rows for the fixture (CP-821).

Every test hands the date in as a value, or through `MovableClock`; no product name is patched and no stand-in class is added (CP-815, CP-818). The two modules' own docstrings name the requirements they check (CP-817).

#### Implement

Infer from failing tests.

# Hint: the row is a `_SummaryRow` with no link, so `_summary_cell` already writes a bare `<td>` with no `aria-label`. The label goes through `_summary_group`'s `_escape` like every label, and its date part is `date.isoformat()`. The words come from `change_text.md`, and only `web` holds them (CP-819, QC-20). `SUMMARY_LINKED_ROWS` already allows an anchor only at the group's first row, so the new row is held to a bare cell with no change there.

#### Verification gate

Run the card's `Test command:` from the worktree root: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`.

Then, from the product root, run `python3 tests/timed_run.py`, and `uv run --locked ruff format --check .`, `uv run --locked ruff check .` and `uv run --locked mypy main.py errors.py domain application persistence web` (NFDR QC-62).

Pass criteria: this task's tests pass; both pytest commands pass; the timed run exits 0 and its Summary check holds the page to every row, the `Due on` row among them (CP-821); the three QC-62 gates pass (CP-820); `grep -rniE 'due.today|due_today' domain application web --include='*.py' --include='*.html'` run from the product root prints the field's line in `domain/summary.py` and at least one line where it is used (CP-822); `git grep -n 'Due on' -- domain` prints nothing (CP-819); no text on the Summary page reads "Due today" or "Today" (CP-811).
