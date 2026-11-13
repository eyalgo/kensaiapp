# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `2026-11-13_summary-shows-due-today` — a project's summary shows the due-on-date count
**Mode:** workflow, on the change's branch at `6ce827a34`
**Outcome:** clean pass. The code already does what its intent says. One test was tightened to
prove a rule it skipped, and five docstring lines were corrected. No product code changed.

---

## Deferrals

None. The closing marker (`<a commit not in the public history>`, the only `implementation complete` commit on the branch)
carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

Everything the change's code commits added to `products/tracker17`:

- `domain/summary.py`: the `today` and `due_today` fields of `ProjectSummary`, the count in
  `summarize_project`, and the module docstring.
- `web/pages.py`: the `Due on {date}` row in `summary_page`, the label constant and the docstring.
- `tests/timed_run.py`: the due-on row in `_summary_expected`.
- The tests the change added or edited: `tests/unit/test_summary.py`,
  `tests/integration/test_summary_tracker.py`, `tests/integration/test_summary_pages.py`,
  `tests/integration/test_summary_routes.py`, `tests/integration/test_pages.py`,
  `tests/integration/test_delete_routes.py`, `tests/integration/test_timed_run.py` and
  `tests/architecture/test_trace.py`.

The `.behave/` scenarios are QA's and run at the close. They were not reviewed here.

## The intent it was checked against

- `tl_instruction.md`: Task 1, the summary carries its date and the count. Task 2, the page row and
  the timed run.
- `change_spec.md`: CP-808 to CP-822, the examples and the locked answers.
- `change_text.md`: the label `Due on {date}`.
- `docs/fdr.md` was not needed beyond what the spec quotes.

## Tests added or fixed

- **`test_summary_of_a_built_project_counts_due_on_the_date_and_excludes_the_rest`**
  (`tests/integration/test_summary_routes.py`). **Fixed.** CP-816 asks for a test on a built project
  that pins "the row in its CP-811 place". The test looked each row up by label, so a row in the
  wrong place would still pass it. It now checks the "Due dates" group's rows in order:
  `Overdue` 1, `Due on <date>` 2, `No due date` 1. To prove it catches the fault, I moved the row
  after `No due date` in `web/pages.py` for one run. The test failed, and the file was then restored
  from the commit.
- **`test_summary_entry_names_every_participant_and_check`** (`tests/architecture/test_trace.py`),
  docstring only. It said the entry names FR-38, FR-25, FR-35 and NFR-9. Its set now holds AC-13 as
  well, so the docstring now names AC-13 and CP-817.
- **Lines over 100 columns** (`conventions.md:17`, "Lines stay within 100 columns."). The change
  wrote four docstring lines past 100 columns. Ruff passed because its default rules do not check
  line length. The lines were reflowed with no word changed, in `tests/unit/test_summary.py`,
  `tests/integration/test_summary_routes.py` (two lines) and the module docstring of
  `tests/integration/test_timed_run.py`.

Every other test the instruction names was present, matched its behaviour, and was left as it was.
Two of them have a weakness that other tests cover:

- The layer-4 page tests date their summary 2026-11-13, which is also the real date of this run. So
  on their own they could not tell `summary.today` from a real clock read in `web`. The routes test
  can, because its clock stands at 2026-10-11 and its label must read that date.
- The tracker test across midnight fails if one summary reads the clock twice. That is CP-809's rule
  that one date serves both counts.

## The finding

**No issues in the code.** Every behaviour in the intent has a test, and every test now proves the
rule it names. Nothing was misplaced. The only fixes were the one test and the docstrings above.

The spec's own checks, run on the branch with the test fixes applied:

| Check | Result |
|---|---|
| The card's `Test command:`, through the gate tool (CP-820) | exit 0: `3383 passed, 2 skipped`, then `122 passed` |
| `uv run --locked ruff format --check .`, from the product root (CP-820) | `374 files already formatted` |
| `uv run --locked ruff check .` (CP-820) | `All checks passed!` |
| `uv run --locked mypy main.py errors.py domain application persistence web` (CP-820) | `Success: no issues found in 28 source files` |
| `python3 tests/timed_run.py`, from the product root (CP-821) | exit 0, with `open a project summary at 1000 tasks: 3.4 ms` |
| `grep -rniE 'due.today\|due_today' domain application web --include='*.py' --include='*.html'` (CP-822) | the field at `domain/summary.py:86`, the count at `:113`, and its use at `web/pages.py:1828` |
| `git grep -n 'Due on' -- domain` (CP-819) | no output, exit 1 |

Test evidence:

- An earlier run of the test command exited 1 and printed `Environment: owners-mac — no CI`.
  Its 57 failures, in `test_summary_pages.py`, `test_summary_routes.py` and `test_timed_run.py`,
  all showed the due-on row after `No due date`. The cause was the review's own fault check, not
  the code. The temporary edit and the restore of `web/pages.py` were the same size and landed in
  the same second, so Python's cached bytecode still matched the restored file and served the
  edited one. With that cache file removed, the source unchanged, the next run passed. That run is
  the one this verdict rests on.

## Calls made

- **The timed-run tests read the real clock.** `tests/integration/test_timed_run.py` works out the
  expected day with `_local_today()` against a site the harness builds on its real clock. The new
  test `test_timed_summary_check_holds_the_page_to_the_due_on_row` does the same. A run that crosses
  local midnight between building the page and reading the day could fail.
  - Readings weighed: hand the harness a clock now, or keep the module's existing pattern.
  - Taken: keep it. The module used this pattern before this change. These are layer-3 tests of a
    script that times the real program. `testing_doctrine.md` forbids the real clock in a layer-1
    unit test, and these are not unit tests. Giving the harness a clock seam would change
    `tests/timed_run.py`'s design, which is beyond this change.
  - Owner: the Tech Lead, whose plan placed these tests. If reversed: the harness takes a clock as
    a parameter, and every timed-run test hands it one.
- **No separate `test_summary_trace_names_ac13`.** The instruction names that test. The developer
  added `AC-13` to `SUMMARY_REQUIREMENTS` instead. The existing
  `test_summary_entry_names_every_participant_and_check` asserts every member of that set is named in
  `domain/summary.py`'s docstring (`tests/architecture/test_trace.py:624`), so it fails while AC-13
  is missing.
  - Taken: accepted. A second test would assert the same line.
  - Owner: the Tech Lead. If reversed: a one-line test that asserts `"AC-13"` is in the set, which
    adds no proof.
- **The 100-column rule over the file's own habit.** The module docstring of `test_timed_run.py`
  already had a line past 100 columns before this change, and the change lengthened another. The
  whole paragraph was reflowed, as `languages/README.md` § *Precedence* says ("the packet wins and
  the run records that it diverged from the file").
  - Owner: the packet. If reversed: nothing in behaviour changes.

## Placement

The parts table is `products/tracker17/docs/SDD.md` § 3.

| Logic | Owning part | Where it is |
|---|---|---|
| `ProjectSummary.today` and `due_today`, and the count in `summarize_project` | `domain` (owns "the filter, sort and summary computations") | already there |
| The `Due on {date}` label and its row in `summary_page` | `web` (owns building each page, and `domain` must not own "any wording shown to the operator") | already there |
| The due-on row of `_summary_expected` in `tests/timed_run.py` | no owning part (test harness) | stays in `tests/` |

Nothing was moved, so there is no placement commit.

## Language resolution

- Python, answered by step 1 of the chain: `project.md`'s `Languages:` line.
- Packet read: `languages/python/README.md`, with every concern file it routes: `toolchain.md`,
  `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`, and
  `testing_python.md` outside the folder.
- Also read: `arch_defaults.md` and `testing_doctrine.md`.
- The code builds none of its own collaborators. `summarize_project` is handed `today`, and
  `Tracker.project_summary` reads the clock it was given. The new unit tests hand in values and
  touch nothing real. The layer-3 tests hand in `FakeSaver`, `SequenceClock` and `MovableClock`
  through the Tracker's constructor, and no product name is patched.
- One divergence from the surrounding file: the 100-column reflow above.
