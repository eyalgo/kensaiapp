# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

Change `2026-10-21_move-timed-run`, project `tracker17`, workflow mode. Clean pass: no bug found,
no test read off the implementation, no placement move. The tidy-ups below change no behaviour.

## Deferrals

None. The closing marker (`developer: 2026-10-21_move-timed-run — implementation complete`, the
newest on the branch) carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

The product diff `main...2026-10-21_move-timed-run` under `products/tracker17/`, two files:

- `tests/timed_run.py` — `MOVE_*` constants, `_move_redirect`, `_saved_the_move`,
  `measure_task_move`, `move_fixture_report`, `_run_move` and `main`'s fold of the move status.
- `tests/integration/test_timed_run.py` — the 18 new move tests and the CP-392 updates to existing
  callers.

## The intent it was checked against

`tl_instruction.md` (Tasks 1–4 and their *Behaviours to verify*), `change_spec.md` (CP-371 to
CP-392, Examples, Locked Answers), `change_design.md` §§ 2–5 (T1–T12) and `change_text.md` (the four
lines). `docs/fdr.md` added nothing for a harness-only change.

Each rule against its test:

- CP-371 (one marked two-field POST, no other submission): T1 test; unmarked-submission test.
- CP-372 (own fixture, product `data/` untouched): `test_timed_move_fixture_is_independent_and_product_data_unchanged`.
- CP-373–CP-375 (the four lines, formats, problem order): T8, T10 and the full-volume report tests.
- CP-376 (intervals exclude setup, readback and gap; total is a sum): T6.
- CP-377 (a) exact 303 address: 14 bad-answer cases; (b) whole-state delta: 13 saved-delta cases;
  the `todo` precondition: `test_timed_move_requires_todo_even_with_plausible_success`.
- CP-378 (200 and escaped completion line): T5 landing cases and the escaping test, on the real page.
- CP-379 (no landing, zero row, total = POST): refusal and bad-answer tests.
- CP-380 (each row and the total held to 1.0 s, raw before rounding): T7 matrix, T12 whole-run tests.
- CP-381 (exit 1 on any move problem): T7, T8, T12.
- CP-383/CP-392 (old tests kept): every old test name present. The removed lines are only the docstring, the import,
  the readings tuples, `_run_readings`' order and the exact-label assertion, which became a
  superset of the old one.

## Tests added or fixed

None added, none corrected. Every behaviour the intent names already has a test that says what the
intent says. Three spot mutations of `tests/timed_run.py`, each restored, turned a named test red:

- dropping the `todo` precondition → `test_timed_move_requires_todo_even_with_plausible_success` failed;
- escaping the title with `quote=False` → `test_timed_move_completion_escapes_loaded_title` failed;
- reporting the first task instead of task 4 → `test_move_fixture_report_uses_varied_loaded_counts_and_code_points` failed.

Tidy-ups made in this commit (no behaviour change, the suite green before and after):

- Eight lines this change added ran past 100 columns. The marker said that rule was "followed", but it was not: the
  test module docstring (162 columns), five test docstrings, one `# type: ignore` line, and
  `main`'s docstring in `tests/timed_run.py`. All rewrapped (packet `python/conventions.md:17`).
- Removed `_page_change`, a helper the change added and nothing calls.
- `test_timed_move_uses_loaded_task_identity_and_project`: `replace(x)` with no changes became
  `find_task(...)`, which says what the line means.

## The finding

No issues. Nothing misplaced, every behaviour has a correct test, and the card's suite passed:
1370 passed. The QC-62 commands and the compile gate also exit 0 on Python 3.11.9 with the pinned
`ruff==0.16.10` and `mypy==2.4.0`: `ruff format --check .` (216 files already formatted),
`ruff check .` (All checks passed!), `mypy main.py errors.py domain application persistence web`
(no issues in 24 source files), and `python3 -m compileall -q` on both files.

## Calls made

- **Is the CP-372 location check strong enough?** In
  `test_timed_move_fixture_is_independent_and_product_data_unchanged`, `moved.location.parent ==
  directory` and the distinct-from-earlier check compare paths the test builds itself. Two readings:
  (a) the proof is the load. `SavedData(directory / "move-volume").load()` returning exactly the
  fixture with task 4 moved shows the run saved there, inside the supplied root, and no other
  action touched it. (b) Add a listing of the run directory. I took (a): a run that saved the move
  anywhere else fails that load, so (b) would add nothing the intent asks for. This is the Tech
  Lead's call (`tl_instruction.md` Task 3). If they rule (b), add one assertion over
  `sorted(directory.iterdir())`.
- **Over-long lines older than this change.** Nine lines that `main` already holds are also past 100 columns
  (`test_timed_run.py` 298, 359, 387, 424, 2207, 2257; `timed_run.py` 326, 329, 330). I left them, because
  they are outside this change's diff. This is the Developer's call for a later tidy. If they rule
  otherwise, rewrap those nine lines.

## Placement

- `measure_task_move`, `_move_redirect`, `_saved_the_move`, `move_fixture_report`, `_run_move`,
  the `MOVE_*` constants → `tests/timed_run.py`. The test helpers → `tests/integration/test_timed_run.py`.
  Already in place. `docs/SDD.md` § 3 gives no runtime part harness measurement, and its one unit's
  language frame puts `tests/` at the product root (`change_design.md` § 2, Architect note 1).
  `_saved_the_move` builds its expectation by field replacement, not by the workflow rule, as the
  design requires. That is test independence, not a duplicated domain rule. Nothing moved, so there is no
  placement commit.

## Language resolution

- Python. Declared in `project.md` `Languages: Python`, chain step 1.
- Packet `languages/python/README.md`, with its concern files read: `conventions.md`,
  `quality_gates.md`, `environment.md`, and `testing_python.md` outside the folder.
- `conventions.md:17` "Lines stay within 100 columns" was broken by the new lines and has been fixed (above).
  `testing_python.md` "The seam is a hand-written fake passed to the constructor": followed. Every
  new test hands the harness a real or wrapped site, saved data or timer, and nothing is
  monkeypatched. `quality_gates.md` Compile and Suite gates: both exit 0.
- Divergence kept: the product's Python 3.11 floor (`docs/nfdr.md` QC-60) outranks the packet's
  3.13 floor. The new code uses nothing newer than 3.11, and the edited test file passed (128) on 3.11.9.

## Test evidence

- The gate tool's evidence: no CI. `git ls-files` finds no build-service configuration, and no
  product decision names a gate environment. The tool picked the owner's Mac, exit 0,
  `1370 passed in 111.16s`.
