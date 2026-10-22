# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-19_cancel-confirmation`, on the station `tracker17 · shukuba · 2026-10-19_cancel-confirmation`.
**Date:** 2026-10-20
**Reviewed at:** the developer's closing marker `1ab334527` (`developer: 2026-10-19_cancel-confirmation — implementation complete`).

## Summary

Task 2, the one task that landed, does what its intent says. Its test proves the intent and fails when
the docstring is wrong. Nothing was added, corrected or moved. Tasks 1 and 3 are deferred. Both
deferrals pass all four checks, and nothing inside them was touched. The card's command is green,
1220 passed. The browser folder, run on its own in the locked environment, has one failure:
`test_real_history_traversal_revalidates_the_confirmation`. That case belongs to deferred task 1, so
it is not a finding here. The change is not done: task 1's history case is still open and waits on
the architect (§ Deferrals).

## Deferrals

The marker was read with `git -C <worktree> log -1 main..2026-10-19_cancel-confirmation --grep='2026-10-19_cancel-confirmation — implementation complete' --format=%B`.

1. `Deferred: task 1 — the Back-after-confirm history case (tests/e2e/test_moves.py::test_real_history_traversal_revalidates_the_confirmation): Clear-Site-Data "cache" does not evict the old confirmation from the pinned browser's live history cache — system/projects/tracker17/journey/tobiishi/2026-10-19_cancel-confirmation/change_design.md § 3`
   - **The task exists:** pass. `### Task 1: The cancelled confirmation capability` is in `tl_instruction.md`.
   - **No landing commit:** pass. Task 1's commits are `8d2e52512` (`— red`), `6b4df74aa` (`— deferred`) and `c7b040d0c` (`— in-progress`). None is a landing subject. The task does not meet its completion check now either: the case still fails on the current tree (below).
   - **Case in the tree:** pass. The test is at `tests/e2e/test_moves.py:392`, with the assertions the instruction states (reload, back and forward save nothing; Back after confirming shows the refusal and no strip; a second tab's ordinary move invalidates an old confirmation). Nothing in `test_moves.py`, `tests/e2e/conftest.py`, `tests/conftest.py` or `pyproject.toml` skips it, deselects it or marks it expected to fail. Its fixture `history_browser` (`tests/e2e/conftest.py:149`) keeps the history cache on, as design § 3 A.3 requires. In the locked environment the folder ran `1 failed, 56 passed`, failing at `test_moves.py:423`, `Locator expected to have count '0'`, `Actual value: 1`, which is what the marker reports.
   - **Record exists:** pass. `change_design.md` is on the branch and has its § 3.
2. `Deferred: task 3 — depends on task 1 — system/projects/tracker17/journey/tobiishi/2026-10-19_cancel-confirmation/change_design.md § 3`
   - **The task exists:** pass. `### Task 3: Review the change's file fence and retained assertions` is in `tl_instruction.md`.
   - **No landing commit:** pass. The branch has no commit for task 3.
   - **Dependency deferred:** pass. Task 1 is named by the `Deferred:` line above.
   - **Record exists:** pass, as above.

Both deferrals are real. Whether they were right is not this step's call.

## What was reviewed

Task 2's commits, `1e433eb91` (red) and `c7b53bed7` (green), against the merge base `127719e6d`:

- `products/tracker17/domain/workflow.py`: only the opening docstring changes. Everything after it is unchanged in the diff.
- `products/tracker17/tests/architecture/test_trace.py`: one new test, `test_workflow_entry_names_every_participating_module_and_check`, with its three constants.

Task 1's code and tests (`web/pages.py`, `web/routes.py`, `web/style.css`, and the integration and
browser tests) and task 3's review were left alone, as deferred work.

## The intent it was checked against

- `tl_instruction.md` § Task 2, *What to build* and *Behaviours to verify*.
- `change_spec.md` CP-340.
- `change_design.md` § 3 Sub-job B and § 5 T16.
- `docs/fdr.md` was not needed for this task.

## Tests added or fixed

**None.** The task 2 test already asserts each item the instruction lists: FR-18 and FR-19; the four
modules that take part; the ten checking modules; that every named path exists; that each checking
module names a requirement and names no unknown one; and that the docstring names no unknown
requirement. The existing trace tests are all still there.

To check that the test means something, it was run against four broken docstrings in a throwaway
clone at `1ab334527`. It failed each time:

- `tests/integration/test_comment_pages.py` renamed → `AssertionError: tests/integration/test_comment_pages.py`;
- `tests/integration/test_routes.py` removed → `AssertionError: tests/integration/test_routes.py`;
- `FR-19` changed to `FR-9` → `assert {'FR-18', 'FR-19'} <= {'FR-18', 'FR-9'}`;
- `application/tracker.py` removed → `AssertionError: application/tracker.py`.

The developer's red commit `1e433eb91` already showed it failing on the missing `web/style.css`.

## The finding

**No issues** in the work that landed. Nothing was misplaced, every behaviour of task 2 already had a
correct test, and every case outside the deferrals passes.

Two things for the seal and the PM to know:

- **The card's command does not run the browser folder.** `tests/conftest.py:7-9` and its
  `pytest_ignore_collect` at `:42` keep `pytest tests/` from collecting `tests/e2e/`. The gate run
  collected 1220 items and none of them are browser tests. That is why the marker's `Suite: green` is
  true even though the history case fails. It also answers the open point in the developer's
  closing-run note: the browser folder did not run in the gate tool's run. The browser folder's
  result is the separate run above (`1 failed, 56 passed`).
- **The change is not finished.** CP-338 needs `pytest products/tracker17/tests/e2e/` to exit 0, and
  it does not, because of task 1's history case. The developer proposed a fix that was not applied: the
  architect either names another way to handle CP-326's Back-after-confirm, or rules on how this
  browser behaves.

## Calls made

**None.**

## Placement

**No new logic** outside the deferred tasks. Task 2 added a docstring and an architecture test. The
docstring stays in its owning entry, `domain/workflow.py` (`docs/SDD.md` § 3, `domain`), and the test
sits with the other entry checks in `tests/architecture/test_trace.py`. A deferred task has no code
to walk (§ Deferrals), so task 1's web code was not walked here. No `… — placement` commit.

## Language resolution

- **Python**, from `system/projects/tracker17/project.md` `Languages:` (step 1 of the chain in `<CORE>/doctrine/engineering/languages/README.md`).
- Packet read: `languages/python/README.md`, which routes the seven concerns to `toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `testing_python.md` (outside the folder) and `environment.md`.
- What applied to task 2: `conventions.md` § Comments and docstrings (the module docstring carries reasoning about the whole file; the new docstring lines say what takes part and what checks it, which is the entry's job). The 100-column and double-quote rules are covered by `ruff format --check` and `ruff check` on both files: `2 files already formatted`, `All checks passed!`. `quality_gates.md`: `compileall` over `domain` and `tests/architecture` exits 0, and `mypy main.py errors.py domain application persistence web` gives `Success: no issues found in 24 source files`. `testing_python.md` § Layer 6: the new test is a layer-6 architecture check that reads files and needs no seam.
- `environment.md` sends Python gates to a container at CI's version. The product has no CI, so the gate tool chose the owner's Mac (the `Environment:` line above).

## Test evidence

- The card's command `pytest products/tracker17/tests/`, run through `gate_suite.py --gate code-integrity`, exited 0: `1220 passed in 91.36s`. It ran under Python 3.14.7 and pytest 9.0.3, the tool's choice for the owner's Mac. The CI inventory found no CI: no tracked file configures a build service, pipeline, runner or workflow.
- `pytest products/tracker17/tests/e2e/`, run on its own as `docs/nfdr.md` § 9 says, in a fresh venv from `tests/requirements.txt` (Python 3.11.9, pytest 9.1.1, playwright 1.63.0): `1 failed, 56 passed in 31.36s`. The one failure is task 1's deferred history case.
