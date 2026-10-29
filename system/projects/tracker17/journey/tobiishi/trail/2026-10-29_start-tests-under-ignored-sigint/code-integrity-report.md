# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-29_start-tests-under-ignored-sigint` · reviewed 2026-10-29
by the Senior Engineer (`development-code-integrity`, workflow mode).

**Read this pass for what it is.** Both of the plan's tasks are declared deferred, and both deferrals
are real. So nothing in this change sits outside a deferral, and this skill may add, fix or turn green
nothing inside one. The pass says the deferrals are real and the suite is green. It does not say the
change is delivered: the four-folder collection and the new proof test are still unbuilt.

## Deferrals

The closing marker is `<a commit not in the public history>`, `developer: 2026-10-29_start-tests-under-ignored-sigint —
implementation complete`, the only marker on the branch.

```
Deferred: task 1 — the outer whole-directory collection of all four folders cannot be built: the unit and e2e folders hold five files with one basename each and no __init__.py, so one pytest process cannot collect both — system/projects/tracker17/journey/tobiishi/2026-10-29_start-tests-under-ignored-sigint/change_spec.md § Invariants
```

1. **The task exists** — holds. `### Task 1` is at `tl_instruction.md:66`.
2. **No delivered task is deferred** — holds. Task 1's only commit is `edd526be6`, `developer: task 1
   repair shared pytest launch conditions — deferred`. Its suffix is `deferred`, which does not count
   as a landing. No other commit on `main..HEAD` names task 1. The marker's Developer Review Notes say
   which half landed (the signal fixture) and which did not (the outer collection rule). The tree
   agrees: `pytest_ignore_collect` and `_command_line_names_end_to_end` are unchanged from `970f6a4ca`.
3. **The case is in the tree** — holds. Task 1 is a preserving task in the "No new tests" lane, so
   its blocked case is a verification-gate check, not a test. Nothing that states it was deleted,
   weakened, skipped or marked expected to fail. The branch's only product change is
   `tests/conftest.py`, and `tests/integration/` is untouched (`git diff --stat main...HEAD --
   products/tracker17/tests/integration/` is empty).
4. **The record exists** — holds. `change_spec.md` is on the branch, and `§ Invariants` is its line 17.

```
Deferred: task 2 — depends on task 1 — system/projects/tracker17/journey/tobiishi/2026-10-29_start-tests-under-ignored-sigint/change_spec.md § Invariants
```

1. **The task exists** — holds. `### Task 2` is at `tl_instruction.md:128`.
2. **No delivered task is deferred** — holds. No commit on `main..HEAD` has a task 2 subject.
3. **The dependency is itself deferred** — holds. Task 1 is named by the `Deferred:` line above.
4. **The record exists** — holds, as above.

Both deferrals are real. Whether they were right is not this skill's call. The marker's own evidence
is for the PM and `shukuba-refine`: the five colliding basenames and the `--import-mode=importlib`
attempt. The open reading is in `deferred_decisions.md`.

## What was reviewed

The branch's product diff against the merge base `970f6a4ca` is one file,
`products/tracker17/tests/conftest.py`:

- `_interruptible_test_session`, a new session autouse fixture. It saves the incoming SIGINT handler,
  sets `signal.default_int_handler` in the main thread only, and restores the saved handler in a
  `finally`.
- The module docstring's duties paragraph, rewritten to describe the fixture and to call the
  collection rule "product-local".

Both are inside deferred Task 1. They were reviewed against the intent and left as written.

## The intent it was checked against

`tl_instruction.md` (Tasks 1 and 2, TL Review Notes), `change_spec.md` (§ Invariants, § Structural
Goal, § Verified Claims), `change_design.md` (§ 3 Signal boundary, Collection boundary, Regression
boundary; § 5 T1–T7) and `deferred_decisions.md`. `docs/fdr.md` was not opened, because the spec
quotes what it binds.

## Placement

- The SIGINT session fixture is pytest lifecycle, so it is test support. **No owning part** in
  `docs/SDD.md` § 3, The parts, because that table assigns pytest lifecycle to no product part. This
  agrees with `change_design.md` § 2 and its Test-support placement note. It already sits in the
  test-support unit, `tests/conftest.py`. No move, no placement commit.
- Task 2 wrote no logic.

## Tests added or fixed

None. Every behaviour this change's intent names belongs to Task 1 or Task 2, and both are real
deferrals. Here are the cases the plan wants and why each is left:

- The outer whole-directory collection invariant (Task 1) — deferred. It is the blocked case.
- `test_real_start_stops_when_pytest_inherits_ignored_sigint` (Task 2) — deferred. It asserts that
  collection.
- The twelve real-start cases are existing tests. They are unchanged and kept every assertion. No
  test was read off the code.

## Test evidence

- **The card's suite, through the gate tool** (`--gate code-integrity`, the evidence recorded in the
  plan's § Gate environment inputs, re-inventoried this run): exit 0, `2651 passed in 271.25s`. This
  is the run the verdict rests on, and its `Environment:` line is the one under the verdict. As the
  developer noted, 2651 is unit, integration and architecture only: the card's command collects no
  `e2e` node, which is Task 1's deferred case.
- **The signal half, checked independently** (not a full-card run):
  `sh -c 'trap "" INT; exec pytest products/tracker17/tests/integration/test_start.py -q'` from the
  change worktree root gave `57 passed`, exit 0. The spec measured 12 timeouts here on `970f6a4ca`.
  This confirms the developer's lane-(a) baseline note, that the fixture turns the four named families
  green under ignored SIGINT.
- `ruff format --check tests/conftest.py` and `ruff check tests/conftest.py` (product `.venv`): exit 0.

## The finding

**No issues outside the deferrals.** No test was missing or wrong, no case failed, and nothing was
misplaced.

**One defect inside deferred Task 1, recorded and not fixed.** This change rewrote line 1 of
`tests/conftest.py`, and it is 101 columns. The Python packet says: `conventions.md:17` —
"**Lines stay within 100 columns.**". Ruff does not catch it, because the product's ruff config sets
`line-length = 100` but does not select the line-length rule. The marker's language block says
`conventions.md:17` was "followed at conftest.py:63-83". That is true of the fixture but not of the
docstring line the same commit wrote. The docstring correction rides Task 1 (`tl_instruction.md`,
Task 1 § Held by review), and § *Deferrals* forbids fixing code inside a deferred task, so this run
leaves it. Whoever reopens Task 1 reflows it.

**Reviewed and sound, inside the deferral:**

- The fixture handles the three edges the plan names. A handler of `None` (installed outside Python)
  is not restored, because it cannot be. A thread other than the main one yields without touching
  the handler. A failing session restores in `finally`, which is the Held-by-review item.
- The fix is sound. A Python-level handler is reset to the default across `exec`, so a tracker
  started by a test gets default SIGINT and installs its own interrupt handler. A tracker an operator
  starts outside pytest is untouched, which keeps the spec's SIGINT invariant. No production file
  changed.

## Calls made

None.

## Language resolution

- **Language:** Python, from step 1 of the chain: `system/projects/tracker17/project.md`,
  `Languages: Python`.
- **Packet read:** `<CORE>/doctrine/engineering/languages/python/README.md` and its seven routed
  concerns: `toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`,
  `testing_python.md` (outside the folder) and `environment.md`.
- **Bearing on this review:** `conventions.md:17` (100 columns) is breached at `conftest.py:1`, inside
  the deferral, as recorded above. `environment.md` was applied through the gate tool, and with no
  CI it resolved to the owner's Mac. The rest bore on nothing this review changed, because this
  review changed no code.
