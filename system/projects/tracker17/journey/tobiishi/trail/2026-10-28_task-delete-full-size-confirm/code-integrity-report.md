# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-28_task-delete-full-size-confirm` — Delete task's first press and its confirmation take the full-size height.
**Reviewed at:** `<a commit not in the public history>` (the developer's closing marker), against merge base `62123a148`.

## Deferrals

None — the closing marker (`<a commit not in the public history>`) carries no `Deferred:` line.

## What was reviewed

- `products/tracker17/web/pages.py` — `_delete_strip` (`size=FULL_SIZE`) and `_delete_section` (first press `class="button-secondary"`).
- `products/tracker17/web/style.css` — `button.delete-button` and its hover rule removed from the row-control rules; the move-button and full-size strip comments aligned.
- `products/tracker17/tests/e2e/test_delete_task.py` — four new cases (three tests, one parameterised) and the opening docstring.
- `products/tracker17/tests/e2e/test_delete_project.py` — the one corrected `task_confirm` assertion and its docstring.

`git grep "delete-button"` over the product returns nothing, so no rule or test still names the retired selector. The diff over `domain`, `application`, `persistence`, `main.py`, `errors.py`, `web/routes.py`, `web/listener.py` and `web/__init__.py` is empty.

## The intent it was checked against

`tl_instruction.md` Task 1 (`#### Behaviours to verify`, `#### Held by review`) and `change_spec.md` CP-609–CP-618, with `change_design.md` § 5 T1–T8. `docs/fdr.md` was not needed.

## Tests added or fixed

None. Each behaviour in the intent already has a test that would fail if the code were wrong:

| Intent | Test |
|---|---|
| CP-609, ordinary page; CP-610–CP-612; CP-611 "whole spot" on both axes, short and scrolled page | `test_delete_task_confirmation_matches_full_size_trigger[short-page]`, `[scrolled-page]` |
| CP-609 "is the {components.button-secondary}" (not only 36px) | the `secondary_look` assertion in the same test |
| CP-609, after Back out | `test_delete_task_back_out_restores_full_size_trigger` |
| CP-609, after a failed save | `test_delete_task_save_failure_restores_full_size_trigger` |
| CP-613, CP-615 | `test_project_strip_uses_full_size_controls` (task 36px, move still 28px) |
| CP-618 | `tests/architecture/test_trace.py`, in the card suite |

**Checked: the tests fail on the old code (CP-614).** In a separate clone of the branch tip with `web/pages.py` and `web/style.css` set back to `62123a148`, all five geometry cases failed on height: "the first press is 28px tall" (both T1 variants), "the restored first press is 28px tall", "the first press after a failed save is 28px tall", and `test_project_strip_uses_full_size_controls` at `:221`. The developer's revert checks, recorded on the marker, cover each production rule separately.

**Checked: CP-615 changed only what it allows.** Compared with the merge base, `test_delete_task.py` has only additions plus a reworded opening description. `test_delete_project.py` changes only the `task_confirm` constant and its docstring. The existing T5 tests are unchanged.

## The finding

No issues. Every intended behaviour had a correct test, nothing was misplaced, and every check passed.

## Calls made

- **Question:** CP-609 / T3 says to check that "the task remains available" after a failed save. Does that need its own check, beyond the saved bytes?
  **Readings weighed:** (a) a separate visit to the task's address; (b) what the test already shows: the page at `/tasks/1?delete_failed` renders task 1 with its Delete task button, the saved bytes are unchanged, and they still hold the task's title.
  **Taken:** (b). The page shown after the failure is the task's own page, so the task is still available. A second visit would add nothing to the proof.
  **Whose document:** the Tech Lead's (`tl_instruction.md` Task 1). **If reversed:** add one `page.goto("/tasks/1")` check to that test. The code would not change.

## Placement

The parts table is `docs/SDD.md` § 3. **web** owns "building each whole HTML page and the one stylesheet".

- First-press component selection (`_delete_section`) → **web**, already there.
- Strip size selection (`_delete_strip`) → **web**, already there.
- Removing the retired selector (`style.css`) → **web**, already there.

Nothing was moved, so there is no placement commit.

## Language resolution

Python, from step 1 (`project.md` `Languages:`). Read `<CORE>/doctrine/engineering/languages/python/README.md`, `conventions.md`, `quality_gates.md` and `<CORE>/doctrine/engineering/testing_python.md`. The product's QC-62 commands outrank the packet's no-linter default (`quality_gates.md` § What a product installs). The new code breaks no packet rule: lines are within 100 columns, it uses `Path`, nothing is monkeypatched, the failing save is a real directory at the saver's partial-file path, and the browser tests live in `tests/e2e/` and run on their own.

## Test evidence

- Card suite through `gate_suite.py --gate code-integrity`: exit 0, `2629 passed in 261.21s`. This is the run the verdict rests on, and its `Environment:` line is the one above.
- `pytest products/tracker17/tests/e2e/` (CP-616, run on its own): `121 passed in 53.17s`.
- From the product root (CP-617, QC-62): `compileall` exit 0; `ruff format --check .` (ruff 0.16.10) "269 files already formatted"; `ruff check .` "All checks passed!"; `mypy main.py errors.py domain application persistence web` (mypy 2.4.0) "Success: no issues found in 27 source files".
- Every command ran with `products/tracker17/.venv/bin` first on `PATH`, holding the versions `tests/requirements.txt` pins.
