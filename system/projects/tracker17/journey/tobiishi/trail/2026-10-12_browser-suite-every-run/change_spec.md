# Change Spec — the end-to-end suite passes on every run

**Date:** 2026-10-12
**Category:** nfdr
**Behaviour:** preserving
**Request:** Find why the focus tests in `products/tracker17/tests/e2e/test_first_project.py` and `tests/e2e/test_people.py` fail on some runs of `main` and pass on others, and fix it in the tests or in what they measure, so `pytest products/tracker17/tests/e2e/` (the whole folder as it stands on `main`) exits 0 run after run. Name the cause in the closing commit's body: which tests, what raced or varied, and why the fix removes it. A retry or rerun plugin or option is not a fix and must not be added. The focus checks must still assert focus, and no test may be deleted, skipped or loosened so that it cannot fail. No new end-to-end tests, and no behaviour change the fix does not need. Diagnosis and fix are one change: a named cause with no fix leaves the suite as flaky as before.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened

---

## Change Summary

The end-to-end suite (`<Product path>/tests/e2e/`, `Product path:` per `project.md`) gives a different verdict on different runs of the same tree. Focus assertions read no focused element on some runs and the expected one on others (§ *Verified Claims*, row 2). This change finds what varies, removes it at its source, and names it in the commit that lands the fix. What the tracker does for its user stays the same.

---

## Invariants (characterization contract)

- **I-1 — The in-process suite passes, with its tests unchanged.** The project card's `Test command:` (`pytest products/tracker17/tests/`, run from the worktree root) collects everything under `tests/` except `tests/e2e/` (`<Product path>/tests/conftest.py:L7-L9`). It exits 0, and no test module it collects is modified. This suite is the contract for every page the tracker builds, its `autofocus` attributes included: layer 4, NFDR § 9.
- **I-2 — The public import surface is identical.** `__all__` in `application/__init__.py`, `domain/__init__.py`, `persistence/__init__.py` and `web/__init__.py` names the same symbols. `main.start` keeps the call the harness makes: `main.start((host, port), location)`, which `<Product path>/tests/e2e/conftest.py` `START_PROGRAM` uses.
- **I-3 — The whole end-to-end folder exits 0 on 20 consecutive runs.** Take a `git archive <HEAD SHA> products/tracker17` copy, `git init` it, and set up the README's `.venv` there. In that copy, `pytest products/tracker17/tests/e2e/` exits 0 on 20 consecutive runs, and the run log shows 20 exit codes of 0. The command runs the whole folder as it stands, never a subset (station reached-when 3).
- **I-4 — The same tests, still able to fail.** Every test function under `<Product path>/tests/e2e/` at station open is still there under the same name: 27 functions across five modules (§ *Verified Claims*, row 3). Each one runs. None is skipped, marked expected-to-fail, deselected or ignored by any configuration. None is weakened so that it can no longer fail. No new end-to-end test function is added.
- **I-5 — Focus checks still assert focus, on the same element.** Every assertion that reads the focused element keeps asserting the element it asserts today. In `test_first_project.py` those are `name`, `description` and `H1`. In `test_people.py` they are `assignee-<n>`, `remove-<n>`, `assignee-name`, `assignees-heading`, `INPUT` and the Tab stops. Each assertion fails when focus is anywhere else, the document body included.
- **I-6 — No retry or rerun plugin or option.** `git diff <station-open SHA>..HEAD -- products/tracker17 | grep -inE 'rerun|flaky|retry|retries'` prints nothing on added lines. The station opened at `530d0c214`. The grep reads every added line under the product, comments included. So the cause is written in the commit body, which the grep does not read, and never in a code comment that uses one of those words (station reached-when 2).
- **I-7 — The cause is named in the commit that lands the fix.** That commit's body says which tests failed, what raced or varied, and why the fix removes it (station reached-when 1).
- **I-8 — The ADR-0003 focus tests stay as regression triggers (NFDR RN-15, `nfdr.md:L725-L737`).** `test_added_markup_name_has_browser_focus_and_accessible_description` and `test_people_keyboard_refusals_and_removal_keep_focus_at_the_action` keep asserting what RN-15 says they verify. That is Chromium focusing a form control, and focusing an element that is not a control, made focusable with `tabindex="-1"`.
- **I-9 — The code gates pass (NFDR QC-62, `nfdr.md:L480-L486`).** `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web` each exit 0 from the product root.
- **I-10 — A test hands a part its collaborators and never patches a name inside it (SDD § 4 TS-2, `SDD.md:L448-L450`).** This binds every test the fix edits.
- **I-11 — Each test module names what it checks, and the pointer test passes (SDD § 4 TS-3 and TS-4, `SDD.md:L451-L461`).** A test module the fix edits keeps its opening docstring naming the requirements, rules and NFDR entries its tests check. TS-4's pointer test runs in I-1's suite and passes.
- **I-12 — A test dependency, if one is added or moved, is pinned and locked (NFDR QC-39, `nfdr.md:L298-L302`; QC-40, `nfdr.md:L303`).** It is declared in `pyproject.toml` with `==` and locked in `tests/requirements.txt`. The version it picks clears QC-40's advisory rule. This applies only where the fix touches a test dependency. I-6 still forbids a retry or rerun one.

---

## Structural Goal

- The end-to-end suite's verdict on a given tree no longer varies from run to run. The fix removes the cause where it lives, either in how the tests observe the page or in what they observe. It never adds a repeat attempt.
- The fix reaches every end-to-end test that varies, whichever module it sits in. Where the cause is shared, it is removed once, for all of them.
- Where and how the fix is made is development-design's decision.

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| 1. I-1's suite passes today. | `pytest -q products/tracker17/tests/` run in a `git archive 5148e0366 products/tracker17` copy under `/private/tmp`, `git init`-ed, with the README's `.venv` installed from `tests/requirements.txt` and `python -m playwright install chromium`. Run on macOS. | `813 passed in 42.03s`, exit 0 |
| 2. The end-to-end suite fails on some runs and passes on others today, and focus assertions are what fail. | `pytest -q -p no:cacheprovider products/tracker17/tests/e2e/`, 8 runs in a row, in the same copy under the same conditions. `-p no:cacheprovider` only stops the run writing `.pytest_cache`. | Runs 1 and 3 to 8: `27 passed`, exit 0. Run 2: exit 1, `3 failed, 24 passed`. The failures were `test_first_project.py:166` (`assert '' == 'name'`), `test_first_project.py:177` (`assert '' == 'description'`) and `test_people.py:157` (`assert '' == 'assignees-heading'`). Each read an empty focused-element id. |
| 3. The end-to-end folder holds 27 test functions. | `git grep -c -E '^def test_' 5148e0366 -- products/tracker17/tests/e2e/` | `test_first_project.py` 11, `test_labels.py` 4, `test_people.py` 6, `test_start_command.py` 1, `test_tasks.py` 5. That is 27, matching row 2's `27 passed`. |
| 4. I-6's grep prints nothing before the work, so it fails only if the fix adds a match. | `git diff 530d0c214 5148e0366 -- products/tracker17 \| grep -inE 'rerun\|flaky\|retry\|retries'` | No output, grep exit 1 |
| 5. The tree already holds the word `retry`, in lines the diff will not touch. | `git grep -inE 'rerun\|flaky\|retry\|retries' 5148e0366 -- products/tracker17/pyproject.toml products/tracker17/tests/` | Matches only in `tests/integration/test_task_routes.py` (`retry = edit(...)`, L826, L899 and others). There is none in `pyproject.toml` or `tests/requirements.txt`, which carries no retry or rerun package. |
| 6. I-9's gates pass today. | `ruff format --check .`, `ruff check .`, `mypy main.py errors.py domain application persistence web`, run from the product root of the row-1 copy | `168 files already formatted` · `All checks passed!` · `Success: no issues found in 21 source files` |
| 7. RN-15 names the two `test_people.py` functions, and both exist. | Read `nfdr.md:L725-L728` and `tests/e2e/test_people.py:L70`, `:L90` | Both names appear in RN-15 and are defined at those lines. |
| 8. I-2's surface. | Read the four `__init__.py` files, and `tests/e2e/conftest.py` `START_PROGRAM` | `__all__` is present in all four. The harness calls `main.start((sys.argv[1], int(sys.argv[2])), Path(sys.argv[3]))`. |
| 9. `pytest tests/` leaves out `tests/e2e/`. | Read `tests/conftest.py:L7-L9`, and row 1's count against row 2's | The docstring states the collection rule. Row 1 collected 813 tests and row 2 collected 27, so the two runs did not overlap. |

---

## Out of Scope

- **ADR-0003's fallback, and any record superseding it.** Undoing the no-script model inside `web` is not this change, and neither is any change to which element a page focuses. Suppose the diagnosis finds that Chromium does not focus the `autofocus` element at all, as opposed to a test reading focus at a moment when the outcome varies. Then the fix is a behaviour change, and it goes back for reclassification under NFDR RN-15 and ADR-0003 § *Dependence*.
- **The two focus cases RN-15 leaves open**: the EX-6 confirmation, and assistive technology speaking the EX-14 description.
- **New end-to-end coverage**, and any change to what an end-to-end test checks beyond what removing the variation needs.
- **The in-process suite (I-1), `tests/timed_run.py` and the layer-6 tests.** They are not edited.
- **Linux runs of the end-to-end layer.** I-3's proof runs on the machine the change is built on. NFDR § 9's Linux bound is unchanged.

---

## Locked Answers (the divergence record — self-review 2026-10-12)

- **Gap 1 — QC-62's gates as an invariant (I-9):** stated, though the request does not name them. (e): NFDR QC-62 gates every change at the suite. A fix to Python test code is checked by `ruff format --check .` and `ruff check .`, both of which reach `tests/`.
- **Gap 2 — SDD TS-2 as an invariant (I-10):** stated. (e): TS-2 binds every test. A fix that patches a name inside a part to control timing would break it.
- **Gap 3 — SDD TS-3 and TS-4 as an invariant (I-11):** stated. (e): TS-3 requires every test module to name what it checks, and TS-4's pointer test fails on a docstring path that does not exist. An edited e2e module is held to both.
- **Gap 4 — QC-39 and QC-40, conditionally (I-12):** stated. (e): a fix might add or move a test dependency, and those two entries bind any change that does. I-6 already rules out a retry or rerun dependency, whatever its pin.
- **Gap 5 — RN-15's focus tests, by name (I-4, I-8):** stated. (e): RN-15 keeps the passing ADR-0003 focus tests as regression triggers and cites two of them by function name, so renaming one breaks a pointer in the NFDR. That is why I-4 says "under the same name", which goes further than the request's "no test may be deleted".
