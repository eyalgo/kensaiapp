# Change Spec — the real-start tests pass when the suite is launched with SIGINT ignored

**Date:** 2026-10-29
**Category:** bug
**Behaviour:** preserving
**Request:** The tests that start the real tracker in a child process and stop it with SIGINT (the four callers of `_run_real_start` in `products/tracker17/tests/integration/test_start.py`, some parametrized) should pass the same way whether the suite is launched in the foreground or as a background job with SIGINT ignored. Today, when SIGINT is ignored, the child inherits that and never stops, so the 30-second wait times out; the refine's full-suite run counted 12 failures. After this change both `sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/ -q'` and `python -m pytest products/tracker17/tests/ -q` exit 0 from the repository root, covering the `unit`, `integration`, `e2e` and `architecture` folders, with no `test_start.py` failure or timeout. The new proof is one test run under ignored SIGINT that fails on the starting commit. Where the fix sits (the tests or the start they drive) is for the spec and design to decide, but what Ctrl-C does for an operator at a terminal must not change, no test may be deleted, skipped or marked expected-to-fail, the start tests must keep exercising the real start in a child process, and no product document is edited unless a sentence this change makes false requires it.
**Language resolution:** Python — step 1 (`project.md` `Languages:`) — `<CORE>/doctrine/engineering/languages/python/README.md` opened, every routed concern read

---

## Change Summary

The 12 collected cases of the four `_run_real_start` callers time out when the suite is launched with SIGINT ignored, because the tracker they start inherits the ignored SIGINT and never stops. This change makes them stop and pass under that launch too, without changing what the tracker itself does on SIGINT.

---

## Invariants (characterization contract)

- **The existing test suite passes unchanged.** Every existing test keeps every assertion it makes today. None is deleted, skipped or marked expected-to-fail. `python -m pytest products/tracker17/tests/ -q` from the repository root keeps exiting 0, and it covers the `unit`, `integration`, `e2e` and `architecture` folders.
- **Public interface:** `main.start(address, location)` and `main.main(argv=None)` keep their signatures and return values. Nothing else the product exposes changes.
- **The start tests keep exercising the real start in a child process.** Each of the 12 cases still starts the product's own `main.start` in a separate process and stops it with SIGINT, as Ctrl-C does. Each still asserts that the stopped tracker exited with status 0, wrote nothing to standard error, and left the saved data's bytes and the location's file listing as they were.
- **What SIGINT does to a running tracker does not change, under either disposition the tracker can inherit.** Started with SIGINT at its default disposition (an operator at a terminal pressing Ctrl-C), the tracker stops, exits 0 and writes nothing to standard error. Started with SIGINT already ignored by whatever launched it, the tracker keeps running when SIGINT arrives, as it does today. This change is a change to the tests, not to the start (Locked Answers, Gap 1).
- **No product document is edited** unless this change makes one of its sentences false. Where that happens, only that sentence changes.
- **A test module this change adds names the requirements or acceptance criteria it checks** (nfdr.md QC-11; SDD § 4 TS-3). The pointer test in `tests/architecture/test_trace.py` holds this, and it runs in the suite.
- **A test this change adds or alters hands each part its collaborators and never patches a name inside it** (SDD § 4 TS-2).
- **The code passes `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web`, each with exit 0, typed from the product root** (nfdr.md QC-62). All three pass on the starting commit (Verified Claims).

---

## Structural Goal

- **Target.** Each of the 12 cases stops on the SIGINT its test sends, whatever SIGINT disposition the suite was launched with. So `sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/ -q'`, typed from the repository root, exits 0 with no `test_start.py` failure or timeout. The foreground command in § Invariants keeps exiting 0 too.
- **Where the fix sits.** In the test side, which decides the conditions the real start runs under. The product's start is unchanged (Invariants, the SIGINT line). Which test file, helper or fixture carries the fix is development-design's call.
- **The proof.** At least one test runs the real start with SIGINT ignored by what launched it, and requires that the test's SIGINT stops it with the outcome the 12 cases assert. That test fails on the starting commit, `970f6a4ca`, and passes after the change. How it sets the launch up is development-design's call.

---

## Verified Claims

All runs were made in a disposable clone of the repository at `970f6a4ca` (this change's branch point), with a fresh virtual environment built from `products/tracker17/tests/requirements.txt` on Python 3.15.0. The conditions are the ones the request fixes: the real `main.start` in a child process, a real SIGINT, and the full suite typed from the repository root.

| Claim | Verified by | What came back |
|---|---|---|
| The foreground suite passes on the starting commit. | `python -m pytest products/tracker17/tests/ -q`, from the repository root | exit 0; `2651 passed in 265.25s`; no skips |
| The suite launched with SIGINT ignored fails, on exactly the 12 cases of the four `_run_real_start` callers, each by timing out. | `sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/ -q'`, from the repository root | exit 1; `12 failed, 2639 passed`. The failures are `test_start_reads_each_legacy_form_with_every_existing_value` (3), `test_start_reads_valid_unset_boundary_and_surrounded_name` (3), `test_saved_comment_boundaries_and_historical_authors_load` (2) and `test_every_supported_saved_form_keeps_all_existing_values` (4), each raising `subprocess.TimeoutExpired … timed out after 30 seconds` at the `communicate(timeout=30)` in `_run_real_start` (`tests/integration/test_start.py:530`) |
| `_run_real_start` has four callers. | read `tests/integration/test_start.py` | callers at `:560`, `:585`, `:708` and `:756`; the parametrizations give 3 + 3 + 2 + 4 = 12 cases |
| Started with SIGINT at its default disposition, the tracker stops on SIGINT with exit 0 and an empty standard error. | a child running `main.start(('127.0.0.1', 0), <temp dir>)` from the product root, launched by Python with no change to its signal disposition; SIGINT sent after the ready line | `stopped exit= 0 stderr= b''` |
| Started with SIGINT ignored, the tracker keeps running after SIGINT. | the same child, launched with SIGINT set to ignored before it starts; SIGINT sent after the ready line | `still running 10s after SIGINT` |
| The three QC-62 gates pass on the starting commit. | `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web`, run from the product root with the pinned tools | exit 0 each: `269 files already formatted`, `All checks passed!`, `Success: no issues found in 27 source files` |
| The two end-to-end tests that also stop a tracker with SIGINT pass in the full run with SIGINT ignored, but fail when run on their own under it. | `sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/e2e/test_first_project.py products/tracker17/tests/e2e/test_people.py -q'` | exit 1; `2 failed, 17 passed`. The failures are `test_a_created_project_is_listed_after_a_stop_and_a_start` and `test_the_list_is_there_after_a_stop_and_a_start`, the callers of `RunningTracker.stop` (`tests/e2e/conftest.py:54`). In the full run above, both passed |

---

## Out of Scope

- **What Ctrl-C does to the tracker, under either disposition.** The start's response to SIGINT stays as it is (Invariants).
- **The two end-to-end tests that stop a tracker with SIGINT** — `test_a_created_project_is_listed_after_a_stop_and_a_start` (`tests/e2e/test_first_project.py:92`) and `test_the_list_is_there_after_a_stop_and_a_start` (`tests/e2e/test_people.py:203`). The request names the four `_run_real_start` callers, and both pass in the full run under ignored SIGINT, which is what the reached-when measures. They fail when only they run under ignored SIGINT (Verified Claims), so whether they pass depends on what ran before them. This change does not have to make them pass alone. A fix that also covers them is not excluded, and the suite invariant still requires them to pass in the full run. The PM can raise them as their own change.
- Any test besides the 12 cases and the new proof, any fixed timeout, and any part of the product outside its tests.

---

## Locked Answers (the divergence record — self-review 2026-10-29)

- **Gap 1 — the fix sits in the tests, not the start:** the request left the choice to the spec and design. The spec takes it here, because a fix in the start changes what Ctrl-C does for an operator in one case. A tracker launched with SIGINT ignored (for example, started with `&` from a script that is then run at a terminal) keeps running today when the operator presses Ctrl-C in that terminal (Verified Claims). A start that put SIGINT back to its default would stop in that case. That falls under the request's guardrail ("what Ctrl-C does for an operator at a terminal must not change") and the classification's note that a fix altering what the start does "goes back to the PM".
- **Gap 2 — the end-to-end stop tests are named, not taken on:** they are the same kind of test the request describes, but the request lists only the four `_run_real_start` callers, and its reached-when is already met for them in the full run. Taking them on would widen the change past the request. They are named under Out of Scope so the PM sees them.
- **Gap 3 (e) — record checks stated as Invariants:** the request does not name nfdr.md QC-11, QC-62 or SDD § 4 TS-2 and TS-3. A record above the change requires each of them of any test code this change adds or alters, so each is an Invariant that cites its record.
