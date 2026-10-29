# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

Clean pass. The one test the change adds proves what the spec asks of it, the reflow keeps every
word, and nothing was added, fixed or moved.

## Deferrals

None. The closing marker (`<a commit not in the public history>`, `developer: 2026-10-29_ignored-sigint-proof-test —
implementation complete`) carries no `Deferred:` line.

## What was reviewed

The product diff against `main` at `efad30bd8`, in `products/tracker17/`:

- `tests/integration/test_sigint_launch.py` — new, one test,
  `test_real_start_stops_when_pytest_launch_ignores_sigint`.
- `tests/conftest.py` — lines 1 and 2 of the module docstring rewrapped.

No other product path differs.

## The intent it was checked against

- `tl_instruction.md` — Task 1's Behaviours to verify and Held by review; Task 2's Deliverables
  verified by review.
- `change_spec.md` — § Invariants and § Structural Goal, properties 1–5 of the proof test and the
  reflow.
- `docs/fdr.md` — context only.

## Tests added or fixed

None. The spec fixes the change at exactly one added test (§ Structural Goal; § Out of Scope, *Any
change to an existing test*), so a second test is outside the intent (Calls made, 1).

How the existing test holds against each behaviour it owes:

- **Ignored-INT launch of one explicit node under the current interpreter.** `/bin/sh -c 'trap ""
  INT; exec "$@"'` with `sys.executable -m pytest` and `SELECTED_CASE` passed positionally. `exec`
  keeps the ignored disposition, and Python leaves an ignored SIGINT ignored at start, so the inner
  pytest arrives exactly as a background launch does.
- **The real start, stopped by a real SIGINT.** The selected case calls `_run_real_start`
  (`tests/integration/test_start.py:516-535`), which runs `main.start` in a child and sends it
  SIGINT. The proof itself patches nothing and imports no fixture.
- **Child exit 0 and exactly one case passed.** Both asserted, with the `1 passed` pattern
  anchored to the line start so `11 passed` cannot match it.
- **Both output channels in a failed assertion; an outer deadline past 30 s; children reaped.**
  `report` carries both channels, the deadline is 120 s, and the process group is killed on the
  outer timeout and in `finally`. The inner helper reaps its own tracker on failure.
- **The test fails when the fixture is lost (property 4).** Checked independently here, as a
  mutation run in place of the historical checkout: a disposable clone of `efad30bd8` with the
  `_interruptible_test_session` fixture deleted from `tests/conftest.py` (23 lines, nothing else),
  and `pytest -q -p no:cacheprovider tests/integration/test_sigint_launch.py` from the product root.
  The proof failed, `1 failed in 34.40s`, on `assert launch.returncode == 0`, and its message
  carried the inner report: `subprocess.TimeoutExpired … timed out after 30 seconds` on the
  `main.start` child, `1 failed in 34.24s`. That is the stop that does not happen, not an import or
  collection failure. The developer's run at `970f6a4ca` recorded the same failure.

Task 2 reviewed against its deliverables: line 1 is now 97 columns; the docstring's
whitespace-split words equal the merge base's, 258 in order; only lines 1 and 2 differ and the file
stays 157 lines.

## The finding

No issues. Every behaviour the intent names has a test or a review check that holds, the full card
suite passed, and nothing was misplaced.

- The card suite, through the gate tool: exit 0, `2652 passed in 279.84s`, the proof module
  collected once and passing.
- `ruff format --check .` (`270 files already formatted`), `ruff check .` (`All checks passed!`),
  `compileall -q` on the two changed files and `ruff check --select E501` on them all exit 0, from
  the product root.
- Not re-run here: mypy, the ignored-INT launches and both end-to-end suites. The developer
  recorded them as exit 0 in a fresh clone of `efad30bd8`, and this review changed no file.

## Calls made

1. **Whether to add a test for the `1 passed` assertion.** No case makes the child exit 0 without
   passing its one case, so that assertion is not proven to discriminate. Readings: add a second
   test that drives a skipped or deselected node, or leave it. Taken: leave it, because the spec
   fixes exactly one added test and forbids changing existing ones, and a skipped node would need
   one. Owner: the Product Owner (`change_spec.md` § Structural Goal). If reversed, a second test
   or a fixture-free skipped case would be added.
2. **Whether `-p no:cacheprovider` and `start_new_session=True` stay.** The plan names neither.
   Taken: both stay. The first keeps the inner run from writing `.pytest_cache` into the tree. The
   second is what lets the `finally` reach the grandchild tracker, which the plan's "children are
   reaped on failure" needs. Neither changes the signal disposition the test depends on, and the
   mutation run shows the test still fails without the fixture. Owner: the Tech Lead
   (`tl_instruction.md` Task 1). If reversed, the flag and the session would be dropped and the
   reaping would reach the shell only.
3. **Whether to correct the docstring's gloss of NFR-11.** The module docstring reads "SRS NFR-11
   (the automated suite has an integration layer that drives the real start)". `docs/SRS.md:371`
   says the suite has three layers, unit, integration and end-to-end; "drives the real start" is
   not in it. The ID is right, so QC-11's pointer holds. Taken: leave it, the smaller and more
   easily reversed fix, since no behaviour rests on the gloss. Owner: the Tech Lead. If reversed,
   the parenthetical becomes "(the automated suite has an integration layer)", with the suite
   re-run for the pointer test in `tests/architecture/test_trace.py`.

## Placement

No new logic. The change adds one test module and a docstring rewrap, and no production code.
`tests/` sits at the product root, the one unit `docs/SDD.md` § 3 lists ("Its language frame
places `main.py`, `errors.py`, `pyproject.toml` and `tests/` there"), and the module is in
`tests/integration/`, beside the start tests it drives. No `… — placement` commit.

## Language resolution

Python, from step 1 of the chain (`project.md` `Languages: Python`). Packet read:
`<CORE>/doctrine/engineering/languages/python/README.md`, with `conventions.md`,
`quality_gates.md` and `testing_python.md` for Conventions, Quality gates and Testing. The code
meets them: lines within 100 columns, `from __future__ import annotations` first, `pathlib.Path`
only, the test function left unannotated (`conventions.md:59`), and no `monkeypatch.setattr` on a
part (`testing_python.md`, *The seam is a hand-written fake*). The developer recorded two
divergences, a body that starts its own subprocess and constants without a leading underscore.
Both are accepted: the subprocess boundary is what the test proves (`change_design.md` § 3), and
the constants follow the sibling test modules in a module that exports nothing.
