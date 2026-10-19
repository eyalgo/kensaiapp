# Code integrity report — tracker17 · tobiishi · 2026-10-13_full-volume-run

Integrity: pass

This report records the Senior Engineer's integrity review of the timed-run extension for the comment
add and the People assignee add and remove. It was written by `development-code-integrity` on
2026-10-13. The code already did what its intent says. Three behaviours of the intent had no test that
would fail if the code were wrong, and this pass adds seven test cases that close them. No code changed.

## Deferrals

None. The closing marker `eef4f062c` (`developer: 2026-10-13_full-volume-run — implementation complete`)
carries no `Deferred:` line and no `Failing:` line (`git log -1 eef4f062c --format=%B | grep -E '^(Deferred|Failing):'`
printed nothing).

## What was reviewed

- `products/tracker17/tests/timed_run.py`. The three openers, `TimedAction` and `_measure_action`, the
  three saved-state and landing predicates, the three fixture reports, `_volume_line`,
  `FixtureShapeError`, and `_run_new_actions` as `main` calls it.
- `products/tracker17/tests/integration/test_timed_run.py`. The developer added 37 cases: the file collects
  74 after this pass, 30 at merge base `e5e1cbbae`, and 7 are this pass's (`pytest --collect-only`).
  The three CP-289 timer streams were also reviewed.

The branch's whole diff against merge base `e5e1cbbae` touches only these two files
(`git diff --stat e5e1cbbae HEAD -- products/` → `2 files changed, 1534 insertions(+), 20 deletions(-)`).

## The intent it was checked against

- `system/projects/tracker17/journey/tobiishi/2026-10-13_full-volume-run/tl_instruction.md`, Tasks 1–6.
- `system/projects/tracker17/journey/tobiishi/2026-10-13_full-volume-run/change_spec.md` § Rules,
  CP-276 to CP-292, and § Examples.
- `system/projects/tracker17/journey/tobiishi/2026-10-13_full-volume-run/change_design.md` § 3,
  "Measurement contract", which the plan's interval tests cite as "points 1–5".
- `system/projects/tracker17/journey/tobiishi/2026-10-13_full-volume-run/change_text.md`, for the
  printed row forms.
- `products/tracker17/docs/fdr.md` exists and was read only for R-57 and R-61, the assignee list rules.

## Tests added

Each test was written from the rule it names. Each was proven to discriminate: the harness was mutated
in a scratch edit, the test went red, and the file was restored byte for byte
(`git diff --quiet -- products/tracker17/tests/timed_run.py` exit 0). M1 and M2 below were also run
against the developer's 67 cases with the new ones deselected, and all 67 passed. That result is the
gap each new test closes.

1. `test_timed_comment_redirect_counts_the_tasks_own_comments`. CP-279 says `{n}` is "the added
   comment's one-based place among that task's comments". Every earlier comment test runs on a 20-comment
   task. Mutation M1, a harness that hard-codes `position = 21`, passed all 67 developer cases and fails
   this test. The test uses a uniform fixture of 3 comments per task and expects the GET to
   `/tasks/250?comment_added=4`, with all three rows done.
2. `test_new_timed_action_reads_the_saved_state_back_before_the_landing_interval`, run once for each of
   the three actions. Design § 3 point 5 says "Perform the saved-state check before the landing
   interval". The developer's interval tests check only that a load comes somewhere after the POST.
   Mutation M2 moves the readback after the landing GET. M2 passed all 67 developer cases and fails all
   three cases of this test.
3. `test_new_timed_action_refusal_prints_each_rows_problems`, run once for each of the three actions.
   CP-285 and `change_text.md` fix the printed form of a failing row: ` — `, then its problems joined by
   `, `. They also fix the landing that was never requested at `0.0` ms. No new test checked the printed
   `refused or failed` text of any of the nine new rows. Each case uses the real refusal: no saved name,
   a name already listed, a name not listed. Each times the POST at 1.0 s and asserts all three printed
   lines exactly. A mutation that gives the unrequested landing the POST's duration fails all three cases.

## The finding

No bug was found and no logic was misplaced. The harness meets CP-276 to CP-287 as written.

- Card suite at pytest 9.1.1, from the change worktree root, `pytest products/tracker17/tests/`: before
  this pass `1084 passed`, after it `1091 passed`.
- `ruff format --check .` and `ruff check .` at Ruff 0.16.10, from `products/tracker17`:
  `183 files already formatted`, `All checks passed!`.
- CP-289 holds. The only removed lines in the test file are the module docstring, two imports widened,
  and the three timer streams. Each of those streams gained `*NEW_ACTIONS_QUICK` and nothing else
  (`git diff e5e1cbbae HEAD -- products/tracker17/tests/integration/test_timed_run.py | grep -E '^-[^-]'`).

Observed, not acted on: `FixtureShapeError` refuses a fixture whose tasks hold unequal comment counts.
The developer added it beyond the plan and recorded it in the marker's Developer Review Notes. It never
fires on the run's own fixtures, and CP-286 is the ground the developer gave for it.

## Calls made

None.

## Placement

The parts table in `products/tracker17/docs/SDD.md` § 3, "The parts, and the seams between them", gives
no runtime part ownership of test fixtures, timing, harness checks or console reporting. Its units table
places `tests/` in the one package unit at the product root. `change_design.md` § Architect Review
Notes, "E1", records that the harness owns this logic.

| Logic the change added | Owning part | Result |
|---|---|---|
| Openers, `TimedAction`, `_measure_action`, the saved-state and landing predicates, the fixture reports, `_volume_line`, `FixtureShapeError` | the harness, `tests/timed_run.py` (SDD § 4 TS-5) | already there |
| `_run_new_actions` and its call from `main` | the harness, `tests/timed_run.py` | already there |
| The regression checks | `tests/integration/test_timed_run.py` | already there |

Nothing was moved, so this pass made no placement commit.

## Language resolution

Python, read from `system/projects/tracker17/project.md` `Languages:`, step 1 of the chain in
`core/doctrine/engineering/languages/README.md`. The packet is
`core/doctrine/engineering/languages/python/README.md`, which routes to `toolchain.md`, `layout.md`,
`quality_gates.md`, `conventions.md` and `errors_logging.md`, and to
`core/doctrine/engineering/testing_python.md`.

- `conventions.md`, "Lines stay within 100 columns." Both Ruff gates pass, and the added tests stay within
  100 columns.
- `conventions.md`, "`from __future__ import annotations` is the first statement." Both files already
  open with it.
- `testing_python.md`, "The seam is a hand-written fake passed to the constructor — not
  `monkeypatch.setattr` on the module under test." The added tests hand the harness `Intercept`,
  `EventLog` and `Ticks`, and they patch no name.
- `quality_gates.md` and `toolchain.md`. Every gate ran in a venv built from the unchanged
  `products/tracker17/tests/requirements.txt`.
