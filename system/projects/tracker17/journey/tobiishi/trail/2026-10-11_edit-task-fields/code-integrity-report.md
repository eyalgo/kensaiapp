# Code integrity report — 2026-10-11_edit-task-fields

Integrity: pass

**Reviewer:** Senior Engineer, `development-code-integrity`, 2026-10-12 · **Outcome:** clean pass.
The code needed no fix. Three tests were strengthened and two added, and all of them pass against the
code as the developer left it.

## Deferrals

None. The closing marker `7ada48cae` (`developer: 2026-10-11_edit-task-fields — implementation
complete`) carries no `Deferred:` line and no `Failing:` line, and reads `Suite: green`.

## What was reviewed

Everything the change put under `products/tracker17/` in `main..7ada48cae`:

- `domain/` — `tasks.py`, `refusals.py` and `__init__.py`.
- `application/` — `tracker.py` and `__init__.py`.
- `web/` — `pages.py`, `routes.py` and `style.css`.
- `tests/timed_run.py`, and the eight test files the change modified.

## The intent it was checked against

- `tl_instruction.md` — Tasks 1 to 5, each task's *Behaviours to verify* and *Held by review*.
- `change_spec.md` — CP-144 to CP-181 and its Examples.
- `change_design.md` — sections 2 to 5.
- `change_text.md` — every published string. Each string in `web/pages.py` and the console line in
  `web/routes.py` matches it word for word.
- `docs/fdr.md` exists and was not needed: the spec cites each R-number it rests on.

## Method

All 63 test names the instruction lists are each defined once under `products/tracker17/tests/`.
Then 34 deliberate breaches of the intent were applied to a `git archive HEAD` copy, one at a time,
and the suite was run against each. A breach the suite does not catch marks a sentence of the intent
that no test proves. 27 were caught as the developer left the suite. The 7 that were not:

| Breach | Intent | Result |
|---|---|---|
| Shown values not line-break normalized | CP-151; Task 4 "CR LF/lone CR normalize in submitted and shown strings" | Test strengthened (below) |
| Added line still shown beside a refusal | CP-161, CP-165, CP-168 (one focused control) | Test strengthened (below) |
| Retained form shows the saved value, not the original shown one, for a field the request did not send | CP-166; Task 4 "retaining missing pairs" | Test added (below) |
| The run's exit status ignores the edit's verdict | CP-179 "the run fails when the edit is refused or fails" | Test added (below) |
| No echo of a refused assignee name | `change_design.md` § 3 C says it "may be echoed" | Optional by design; no test owed |
| Completion line uses the typed title | CP-156 | No observable effect: a saved page carries no form fields |
| Edit verdict skips the 303 check | CP-179 | No observable effect: only a 303 carries the `Location` it also checks |

## The tests added or fixed

- **Fixed** `tests/integration/test_task_routes.py::test_task_edit_normalizes_both_field_sets`. It
  sent carriage returns only in the submitted value, so it passed when shown values were never
  normalized. Two cases added: CR LF and a lone CR in the shown value against LF submitted, each a
  plain redirect with no save.
- **Fixed** `tests/integration/test_task_pages.py::test_task_edit_completion_line_is_not_shown_with_a_refusal_or_failure`.
  It covered a refusal with the saved line only, although its name promises a failure too. It is now
  parametrized over the added and saved lines, and checks a failed form as well: no completion line,
  and focus on the form alone.
- **Added** `tests/integration/test_task_routes.py::test_task_edit_retry_keeps_a_field_the_request_did_not_send`,
  parametrized over a refusal and a failed save. A request shows priority `high` and sends none
  while another tab has saved `medium`. The retained form is loaded, then a third save sets
  `critical`, and the retry must leave `critical` in place (CP-166).
- **Added** `tests/integration/test_timed_run.py::test_timed_run_fails_when_only_the_edit_fails`.
  `main` is given a timer under which only the edit takes 1.5 s. The run must report only the edit
  as over the limit and return 1 (CP-179).

Each one was rerun against its breach and catches it.

## The finding

No issues in the code. It already does what its intent says. The gaps were in the tests and are
closed above. Nothing was misplaced.

Suite: `pytest products/tracker17/tests/` 696 passed (692 before), in the change worktree and again
in a `git archive HEAD` copy, `git init`-ed, carrying the three edited test files. From that copy's
product root, the pinned `ruff format --check .`, `ruff check .` (0.16.10) and
`mypy main.py errors.py domain application persistence web` (2.4.0) each exit 0, and so does
`python3 -m compileall -q tests`. The e2e suite and `timed_run.py` were not rerun: no product code
and no e2e file changed since the developer's archive verification at `02e3b35c9`.

## Calls made

- **Is the assignee echo, or the 303 check, owed a test?** The readings weighed were "test every
  line of the code" and "test what the intent says". The intent was taken. The design makes the echo
  optional, and the 303 check is unobservable on its own. Owner: the Architect, `change_design.md`
  § 3 C. If the echo is ruled required, it is owed a test asserting the refused name is the chosen
  option after a CP-163 refusal.
- **Extend the developer's completion-line test, or add a new one?** It was extended: its name
  already claims the failure case it did not test. Owner: the Tech Lead, `tl_instruction.md` Task 4.
  Splitting it would change no assertion.

## Placement

The parts table is `docs/SDD.md` § 3.

- `TaskFields`, `TaskEditOutcome`, `TaskEditContext`, `edit_task`, `task_edit_context`,
  `_changed_value`, `_parse_optional_date` and `TaskNotFound` hold the comparison, validation order,
  membership, choices and the unlisted flag. Their owning part is `domain`, and they were already
  there.
- `Tracker.edit_task` and `Tracker.task_edit_context` delegate to domain and branch only on
  `outcome.changed`, as design B prescribes. Their owning part is `application`, and they were
  already there.
- `TaskEditRefusal`, `TaskEditForm`, `_edit_form`, `task_page`, `_optional`, `_fields`,
  `_carried`, `Site._edit_task`, `Site._task_page` and `Site._edit_form` hold extraction,
  transport, rendering and the refused-name echo. Their owning part is `web`, they were already
  there, and none decides a rule.
- `measure_task_edit` and its helpers sit under `tests/`, a harness and not a part.

No move, so no `— placement` commit.

## Language resolution

Python, from step 1 of the chain: `project.md` `Languages:`. Read `<CORE>/doctrine/engineering/languages/python/README.md`
and the concerns that bear on test code: `conventions.md` (100 columns, `:17`), `quality_gates.md`
and `testing_python.md` (`:31`, a hand-written fake through the constructor, never
`monkeypatch.setattr`). The added tests use the world's `SwitchedSaver` and the harness's `Ticks`,
and patch no name. Ruff and mypy at the pinned versions pass, as recorded above.
