# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · 2026-10-27_project-list-sort` — sort one project's task list. **Date:** 2026-10-28.

## Deferrals

None. The closing marker `<a commit not in the public history>` carries no `Deferred:` line.

## What was reviewed

The 17 product paths the branch changed against merge base `614eca038`: `domain/sorting.py`,
`domain/__init__.py`, `application/tracker.py`, `application/__init__.py`, `web/routes.py`,
`web/pages.py`, `tests/timed_run.py`, and the ten test modules in `tl_instruction.md` § Project layout.

## The intent it was checked against

`tl_instruction.md` (Tasks 1–6 and their Behaviours to verify), `change_spec.md` CP-426–CP-458,
`change_design.md` §§ 2–5 and its Architect Review Notes (the zero-match count reading), and
`change_text.md` for the published strings. `docs/fdr.md` was read for context only.

## Placement

Walked against `docs/SDD.md` § 3 **The parts**. Nothing was moved, and there is no placement commit.

- Ordering, defaults, validation, refusal types, `count_requested` (`domain/sorting.py`) → `domain`, already there.
- The list read projecting the selection, one clock read (`application/tracker.py` `project_task_list`) → `application`, already there; it decides nothing.
- Address decoding, carrying, the pre-move check call (`web/routes.py` `_sort_input`, `_carried_sorts`, `_move_task`) → `web`, already there.
- Labels, options, reasons by type, count words, focus, hidden fields (`web/pages.py`) → `web`, already there. The default an unset select shows is its first offered option. That is presentation, not a sort rule.
- The timed sort and its independent order check (`tests/timed_run.py`) → the supporting measurement module the design lists, already there.

## Tests added or fixed

- **Added** `test_timed_sort_lists_and_counts_only_the_sorted_projects_tasks`
  (`tests/integration/test_timed_run.py`). CP-452 says `{N}` is "the number of the fixture's tasks
  in the project", and CP-454 says the landing lists "each of the `{N}` tasks". No test had a
  fixture with a second project. A changed check that sorted every task in the fixture passed the
  whole suite. The new test moves the three tasks that would sort first into project 2. It asserts
  that the fixture line counts 37, that the first-task lengths come from project 1, and that the
  landing check passes.
- **Fixed** `test_timed_sort_detects_saved_byte_changes_during_either_read`. Its interval part used
  `monkeypatch.setattr(harness, "_saved_bytes", …)`, which the Python testing rule forbids
  (`testing_python.md:31`). Yet `measure_task_sort` already takes `saved_data` as a keyword argument.
  A hand-written `_SlowSavedData` fake now goes in through that argument, and the assertions are
  unchanged. Moving any of the three byte reads into a timed interval still turns it red.

## Test evidence

- I deliberately broke the reviewed code, one change at a time, in a throwaway copy outside the
  repository, and ran the affected tests each time. There were 67 breaks, covering the sort rules,
  the defaults and the count, the refusals and their order, the read model, decoding, carrying, the
  pre-move check, the words, escaping, focus, the kept values, and the timed run's order check,
  count, headers, fixture line and byte checks. Two survived on the first pass:
  - The `{N}` scope break, closed by the added test above.
  - A swap of the Created time and Title options. A stale compiled file in the copy hid it, because
    the swap keeps the file the same size. Rerun with no compiled files, the existing test caught it.
- An earlier run of the test command exited 0 and printed `Environment: owners-mac — no CI`. It found 1845 passed, before the test changes.
- This run's suite (lines above): exit 0, 1846 passed.
- Python 3.11.15, in a scratch environment built from `tests/requirements.txt`:
  - `pytest products/tracker17/tests/e2e/` gave 85 passed.
  - `compileall -q domain application web tests` exited 0.
  - `mypy main.py errors.py domain application persistence web` found no issues in 26 files.
  - `python3 tests/timed_run.py` exited 0. Its last four lines are the CP-452 block, with `sort total at 1000 tasks: 14.1 ms`.
- `ruff format --check .` and `ruff check .` (ruff 0.16.10) both pass after the edit.

## The finding

No issues in the code. Every behaviour of the intent proved correct, and no code was changed. The
suite lacked one intent-derived test (added) and had one test off the packet's seam rule (fixed).

## Calls made

1. **Does a module the change wrote owe `__version__`?** (`conventions.md:148`; the developer left it
   for this step.) There were two readings. In the first, the packet binds and a marker is added: in
   `domain/__init__.py` under the package exception, or in `domain/sorting.py`. In the second, none is
   owed. **Took: none owed.** The clause says it is `versioning.md`'s marker, and `versioning.md`
   § *Whose artifacts — kensaiapp's, never a product's* says a product's `__version__` "is product
   content, set by whichever change needs to set it". Nothing in this change's intent needs one.
   **Owner:** the product's Architect (`docs/nfdr.md`). Ruled the other way, a later change would
   add one marker per product package.
2. **Can `test_timed_sort_failures_reach_main_verdict` stop patching `measure_task_sort`?**
   (`testing_python.md:31`.) There were two readings. In the first, `main` gains a measurement seam
   and the test hands a fake through it. In the second, the patch stays. **Took: it stays.**
   `change_design.md` § 3 D says "Keep the existing `main(directory, timer)` seam", and the filter's
   sibling test does the same. A new seam would change a stated interface, which is not this step's
   to make. **Owner:** the Architect (`change_design.md` § 3 D). Ruled the other way, `main` takes
   its measurements by keyword and both sibling tests pass fakes.

## Language resolution

Python — `project.md` `Languages:`, step 1 of the resolution chain. I opened the packet
`languages/python/README.md` and read Conventions (`conventions.md`), Quality gates
(`quality_gates.md`) and Testing (`testing_python.md`), plus Toolchain and Environment for the gate.
The product floor is Python 3.11 (`docs/nfdr.md` QC-60, ADR-0002), which outranks the packet's 3.13.
The checks above ran on 3.11.
