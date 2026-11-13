# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** tracker17 · tobiishi · 2026-11-13_ignored-sigint-timing — clean pass. The code matches its
intent, every behaviour the intent names has a test that proves it, and no test or code was changed by
this review.

## Deferrals

None. The closing marker (`developer: 2026-11-13_ignored-sigint-timing — implementation complete`)
carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

The branch's diff against its merge base `8c3f7e74d`, under `products/tracker17`:

- `tests/integration/test_sigint_launch.py` — modified: the proof test takes `tmp_path` and hands the
  pytest it launches `--basetemp <tmp_path>/launched-base`; the module docstring gains the cause.
- `tests/integration/test_sigint_launch_temp_root.py` — new: the measurement,
  `test_launched_pytest_leaves_the_shared_temp_root_alone`.

No product module changed.

## The intent it was checked against

`tl_instruction.md` (Task 1's behaviours and hint, Task 2's review-verified deliverables) and
`change_spec.md` (invariants I-1 to I-10). The product's `docs/fdr.md` exists and was not needed:
the change touches only test code, and the spec states every behaviour it is held to.

## Test evidence

Each check below was run by this review, not taken from the marker.

- **I-4, the measurement shows the cause on demand.** In a disposable clone at the branch head:
  the measurement and the proof test, `2 passed`. Then with only `test_sigint_launch.py` put back to
  the merge base: the measurement failed twice in two runs, both on its listing assertion
  (`At index 1 diff: 'pytest-of-<user>/pytest-5' != 'pytest-of-<user>/pytest-1'`; `Left contains 3
  more items, first extra item: 'pytest-of-<user>/pytest-6/…'`) — the leftover session deleted and a
  new numbered one made. Red on the assertion, not on an import.
- **I-3, the proof keeps proving what it proves.** The proof test passes alone at the head. The
  diff removes no line matching `assert`, `SELECTED_CASE`, `IGNORE_INTERRUPT_THEN_RUN`,
  `ONE_CASE_PASSED` or `returncode`.
- **I-2.** `git diff 8c3f7e74d --name-only -- products/tracker17` lists exactly the two test modules.
- **I-5.** The diff of `tests/integration/test_start.py` is empty; no `OUTER_DEADLINE_SECONDS =` or
  `timeout=` line changes in the proof test; the skip/xfail/retry grep over the added lines prints
  nothing.
- **I-6, I-8.** `grep -nE 'monkeypatch|mock|patch\(|^class '` over the measurement prints nothing.
- **I-7.** Both modules' opening docstrings name SRS NFR-11, SDD § 4 TS-2 and NFDR QC-11;
  `tests/architecture/test_trace.py` passes, with `test_arming_preserves_an_inherited_ignored_sigint`
  (`35 passed`).
- **I-9.** From the product root: `ruff format --check .` — `356 files already formatted`;
  `ruff check .` — `All checks passed!`; `mypy main.py errors.py domain application persistence web`
  — `Success: no issues found in 28 source files`. No line of either module exceeds 100 columns.
- **I-1, the full card.** Both commands of `Test command:`, through the gate tool, gate
  `code-integrity`, exit 0: `3336 passed, 2 skipped` and `122 passed`. One run; its `Environment:` line
  is the one under the verdict.

## Tests added or fixed

None. Each behaviour Task 1 lists already has a test that asserts it as the intent states it, and the
measurement was shown red at the base and green at the head above.

## The finding

No issues. No bug, no wrong test, nothing misplaced.

One correction to the Developer's handoff, which changes nothing on the branch: its "most likely to
bite" — that a later pytest which stopped cleaning old session folders would turn the measurement
green at the base — does not hold. The measurement compares the whole private root's listing, so the
new numbered folder and its `pytest-current` link a base-folder-less pytest makes would still turn it
red; the base run above shows those extra entries.

## Calls made

1. **The launch-and-wait block is written twice, once in each module.** Readings weighed: extract a
   shared helper (the floor's "DRY — no duplicated logic"), or keep the measurement self-standing.
   Taken: keep it. The plan's hint (5) has the measurement import only names the proof test already
   has at the base, so that the measurement, run against the base, fails on its assertion rather than
   on an import — which is what makes it the proof I-4 asks for. A helper added to the proof test, or
   to a new support module, would not exist at the base. Owner: the **Tech Lead** (the plan). If
   reversed: the helper lands in `test_sigint_launch.py`, both modules call it, and the base run of the
   measurement fails by `ImportError` instead of showing the cause.
2. **`getpass.getuser()` in the measurement, against the testing doctrine's "who runs it".** Readings
   weighed: the test depends on the user, or it does not. Taken: it does not. The name is used only to
   plant the leftover where pytest would look; the assertion compares the whole private root, so with a
   name pytest spells differently the base run still makes a new folder there and fails, and the fixed
   run still leaves it untouched. Owner: the **Tech Lead**. If reversed: the leftover is planted without
   the user's name, by reading the folder pytest makes, at the cost of a second nested run.

## Placement

The parts table (`docs/SDD.md` § 3) names five parts — `domain`, `application`, `persistence`, `web`,
`main` — and `tests/` is none of them. Walked: the proof test's setup change and the measurement, both
test code under `tests/integration/` → no owning part, no new logic in a product part. Nothing moved;
no `— placement` commit.

## Language resolution

- Python — `project.md` `Languages:`, chain step 1.
- Packet opened: `languages/python/README.md` and every concern it routes — `toolchain.md`,
  `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md` and
  `testing_python.md` — with the floor `languages/developer_standards.md`, and `arch_defaults.md` and
  `testing_doctrine.md` read beside them.
- Held against the change: both tests are layer 2 under `tests/integration/`, start only the suite's own
  interpreter, write only under `tmp_path`, patch nothing and define no class (`testing_doctrine.md`
  § *A unit test hands its unit fakes and touches nothing real* and § *A test reads nothing of the
  machine it runs on*; `testing_python.md` § Rules). The environment reaches each process as a
  `Popen` argument (`conventions.md`, "A module is given its collaborators"). Lines stay within 100
  columns; `from __future__ import annotations` opens each module after its docstring; the
  measurement's constants are named (`developer_standards.md`, "No magic numbers or strings"). No
  collaborator is built inside a unit and no unit test touches a real resource: nothing to repair.
- Gate environment: chosen by the gate tool, not this run. The product has no CI (a filter of the
  tracked files for CI configuration paths returned 0) and no environment decision in `docs/nfdr.md`
  or `docs/adr/`, so the tool printed `Environment: owners-mac — no CI`.
