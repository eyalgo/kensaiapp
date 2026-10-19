# Code integrity report — 2026-10-11_pytest-10051

Integrity: pass

**Reviewed on:** 2026-10-11, by the Senior Engineer (`development-code-integrity`, workflow mode).
**Product commits reviewed:** `f666c96` (task 1 red), `aba2a66` (task 1 green), `43c6e46` (task 2),
in the product worktree `<the issue's clone>/.worktrees/2026-10-11_pytest-10051`.
**Product commit this review added:** `a3860d0` (tests only).

## Deferrals

None. The closing marker `8ce4cf5` (`developer: 2026-10-11_pytest-10051 — implementation complete`)
carries no `Deferred:` line, and no `Failing:` line. The suite was green when the review opened
(23 passed).

## What was reviewed

- `src/_pytest/logging.py`: the new `LogCaptureHandler.clear()` (empties `self.records` in place
  and gives the handler a fresh `StringIO`), and `LogCaptureFixture.clear()` now calling it in place
  of `reset()`. `reset()`, `_runtest_for` and the `pytest_runtest_*` hooks are unchanged, as the
  instruction requires.
- `testing/logging/test_fixture.py`: the eight tests the developer added (seven for Task 1, one for
  Task 2), and the 15 tests that were already there, unedited.

## The intent it was checked against

- `tl_instruction.md`: Task 1 and Task 2, including their *Behaviours to verify*, the hint and
  *Held by review* (Gap 3).
- `change_spec.md`: rules CP-9 to CP-14, the Examples table and Locked Answers Gaps 1 to 5.
- `change_request.md`: the issue's reproducer.
- `docs/fdr.md`: none. The card reads `Definition: none` and the product has no `docs/`. This is
  the normal case, not a gap.

## Tests added or fixed

Added two tests, in `a3860d0`. Both are written from the spec, not from the code:

- `test_get_records_equals_records_after_clear_during_setup`: a fixture logs `s1`, clears, then
  logs `s2`, all during setup. After each step it checks `get_records("setup") == caplog.records`
  and that the messages are `["s1"]`, `[]` and `["s2"]`.
- `test_get_records_equals_records_after_clear_during_teardown`: the same steps (`t1`, clear,
  `t2`) in a fixture's teardown, checked against `get_records("teardown")`.

**Why.** CP-9 says the equality holds "during any phase … at every point". Every equality check
the developer wrote runs during call. Setup records were read only from later phases, never
compared with `caplog.records` while setup ran, and no test called `clear()` during teardown. So
a fix that worked during call but broke in setup or teardown would have kept the suite green.

**They catch the bug.** I ran them against `base_commit`'s `src/` in a disposable copy (made with
`git archive main`, then deleted). Both new tests failed, along with the developer's five Task 1
tests that go red on base. With the change applied, all of them pass.

Fixed: none. Each existing test reads as a correct statement of the spec row it names. None
asserts the old behaviour, and none holds a list across a `clear()`, so Gap 3 stays untested as
the instruction requires (checked by reading the diff).

Considered and not added: a report-section test for setup and teardown. `report_handler` is one
instance shared across all three phases, and `clear()` never touches it, so the call-phase test
(`test_report_section_keeps_records_logged_before_clear`) already exercises that mechanism.
Its `fnmatch_lines` pattern looks for both messages after the `Captured log call` header. The only
later output is the short summary, which does not repeat them, so a dropped record would fail it.

## The finding

**No issues in the code.** The fix is correct as written. The only finding was the coverage gap
above, now closed by tests.

Mutation checks, run in the same disposable copy, to see whether the suite would still pass if
the code were wrong:

- **Making `reset()` empty in place as well** (the wrong fix the hint warns about): 3 failed and
  2 errors, among them `test_caplog_captures_for_all_stages` and
  `test_call_clear_leaves_setup_records_and_is_seen_in_teardown`.
- **Dropping the fresh `StringIO` from `clear()`:** 2 failed, `test_clear` and
  `test_clear_empties_records_tuples_messages_text`.

**Gate:** `/home/kensai/issue-test.sh`, run from the product worktree, exited 0 with 25 passed.
`python -m compileall -q testing/logging/test_fixture.py` exited 0.

## Calls made

1. **Must every new test fail at base, or only the coverage CP-13 lists?**
   - *The question.* `tl_instruction.md` Task 1 says "All of these fail on the unchanged tree
     (CP-13)". But two of its listed tests pass at base: `test_clear_empties_records_tuples_messages_text`
     and `test_clear_leaves_not_started_phase_empty`. The developer kept them as written and
     flagged this.
   - *The readings.* (a) Every test the change adds must go red on base. (b) CP-13's four listed
     behaviours must be covered by tests that go red on base. A test that pins a row whose
     Expected value equals Today (CP-11's "not started reads `[]`", CP-12's empty-after-clear rows)
     is allowed to pass on base.
   - *Taken: (b).* CP-13 says "between them they cover at least" four behaviours, and every one
     of those has a test that goes red on base. The spec's own Examples give today's value as the
     expected one for those two rows, so no honest test of them can go red. Reshaping them to force
     a red would make them test something the spec doesn't say.
   - *Whose call it is.* The **Tech Lead** (`tl_instruction.md`, Task 1's closing sentence).
   - *If they rule (a).* The two tests stay. They would be relabelled as already-green guards in
     Task 2's shape. No code changes.

## Placement

No parts table. The product has no `docs/SDD.md` (it has no `docs/` at all; `Definition: none`),
so Step 0 had nothing to place against and did not run. No logic was moved, and there is no
placement commit. For the record, the new logic sits in `LogCaptureHandler`, the class that owns
`records` and `stream`, as `change_design.md` § 2 places it.

## Language resolution

- **Language:** Python, declared in `project.md` `Languages:` (step 1 of the resolution chain).
- **Packet opened:** `<CORE>/doctrine/engineering/languages/python/README.md`, with Conventions
  (`conventions.md`), Quality gates (`quality_gates.md`) and Testing (`testing_python.md`, through
  the router) read for this review. Toolchain, Layout and Errors and logging were checked through
  the router and found to bear on nothing this review wrote.
- **Applied to the tests added:**
  - Test functions are unannotated, as `conventions.md:58` says a test function is. The one
    helper, `_verify_phase_follows_records`, is annotated `-> None`, matching the file's existing
    inner helpers.
  - Double quotes are used throughout.
  - The added lines are within 88 columns. Four lines in the file are longer (42, 47, 275, 277),
    but they are pytest's own and were left alone.
  - There is no `monkeypatch`, and the tests use the real `caplog` handlers.
- **Quality gates:** Compile, `compileall` exit 0. Suite, the card's test command exit 0.
- **Where the packet and the product disagree:** the same as the developer recorded on the
  marker. The tests live in `testing/logging/`, not beside their subject (`layout.md:29`). The
  interpreter is the card's Python 3.9.25, below the packet's 3.11 floor (`toolchain.md:17`).
  There is no `__version__` or `from __future__ import annotations` in pytest's own files. The
  product's existing layout and the card's interpreter are fixed by `tl_instruction.md` and
  `project.md`, so the packet's house-tool clauses give way here.
