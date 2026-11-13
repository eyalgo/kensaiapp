# Tech Lead instruction — saver-fake-and-suite: one verified `Saver` fake and its contract suite

**Category:** nfdr
**Behaviour:** preserving
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened; `conventions.md` § Constructs and `testing_python.md` § Rules read
**Product root:** `products/tracker17` — every path below is relative to it, except a command, which says where it runs from.
**Scope:** `tests/fakes.py` holds the one `Saver` fake; `tests/integration/test_saver_contract.py` holds the one contract suite for `save`, run against `SavedData` and against the fake; the 46 test-local stand-ins in 20 modules move onto the fake; no file outside `tests/` changes.

---

## Project layout

```
products/tracker17/
  application/ domain/ persistence/ web/ main.py errors.py   ← unchanged (I-2)
  tests/
    fakes.py                                    ← new: FakeSaver, and nothing else
    integration/
      test_saver_contract.py                    ← new: fake-only checks, then SaverContract + two subclasses
      test_<20 modules of Tasks 4–23>.py        ← modified: stand-ins replaced by FakeSaver
    conftest.py  e2e/  unit/  architecture/     ← unchanged
```

No creation notes: `tests/` has no `__init__.py`, and `tests/conftest.py` puts the product root on `sys.path`, so a test imports the fake as `from tests.fakes import FakeSaver`. No parts table covers test code (`docs/SDD.md` § 3 names five product parts), so placement follows `change_design.md §2`.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):
- **Task cut:** §3 lists 46 sites over 20 modules and no build sequence beyond "`fakes.py` first". Each module is its own task, because each swap is independently testable and a blocked one can be deferred alone. `test_routes.py` is one task: `RecordingSaver` is the base of `FailingAfterFirstSaver`, `SwitchedRecordingSaver` and both `OnlySaves`, so none of those can land without the others.
- **Order and dependencies:** the module tasks use only Task 1's `FakeSaver`, so each says `Task 1`. Tasks 4–23 are in a convenient order and carry no edge between them. Task 2 uses Task 1's fake; Task 3 uses both.
- **Task shapes:** Task 1 is test-first (the fake's checks fail at an import until the fake exists). Task 2 is the already-green shape: `SavedData` and the Task 1 fake already satisfy every case, so no case can be made to fail first, and the red it owes is Task 3's recorded mutation (I-5). Task 3 is review-verified: a mutation is a run recorded, not a test left in the suite, and a state-dropping class anywhere would break I-3, I-7 and I-8. Tasks 4–23 use the preserving shape without a relocation: they swap a stand-in under a green suite, add no test and change no assertion, which is that shape's `#### Invariant gate` and no-red body.
- **Behaviour added (Task 1):** `test_a_held_call_that_raises_is_not_held` — §3's order inside one `save` puts the raise before the hold, and no fake-only check pinned it. `test_a_hold_does_not_wait_once_release_is_set` — §3 row for the two `holding` modules says no later save waits after `release`. `test_the_fake_defines_no_now` — I-3. `test_the_fake_has_no_base_class` — I-9. The three pairs of `error` cases in §5's last row are listed as separate tests.
- **Held by review (Task 1):** the 10-second bound of a held call is not tested, because a test of it costs the full 10 seconds on every run.
- **Whole-change gate as a task (Task 24):** I-2, I-7, I-8 and I-10 are commands run on the branch. I-2 is true only while this change is built, so it is checked against the branch's merge base and not written into the suite. I-7, I-8 and I-10 persist, but the walk that would enforce them in the suite is the next station's (`change_spec.md` Locked Answers, Gap 3), so no test is written for them here.
- **Gate commands:** each task gates on its own module plus Ruff over `tests/`; the card's full `Test command:` runs once, at Task 24. A full run costs about 15 minutes (spec, Verified Claims), and one test in it fails under load at the base (I-1).

## Corrections owed while there

- Owed outside this change's reach: `docs/nfdr.md` QC-64 — its *form* sentence points at `testing_python.md` § 2, a section that file does not number; the sentence it quotes stands in its § Rules → the pointer names § Rules.

`change_design.md` § *Records this change makes false* is `None`, so no other line is owed.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {"finding": "none",
         "inventory": "git ls-files -- .github .gitlab-ci.yml .circleci Jenkinsfile azure-pipelines.yml .travis.yml .buildkite, run at the change worktree root, listed no file; git ls-files filtered for workflow, yml, yaml, pipeline and Jenkins names outside core, skills, system and .claude listed docs/findings/2026-09-16_the-chain-halts-where-the-workflow-halts.md, products/tracker17/domain/workflow.py and products/tracker17/tests/unit/test_workflow.py, none of which configures a build service"},
  "decisions": {"override": null, "amd64": null},
  "candidates": [],
  "guest": null
}
```

---

### Task 1: The `Saver` fake and its own checks (`tests/fakes.py`, `tests/integration/test_saver_contract.py`)

**Dependencies:** None

**What to build:** `FakeSaver` in `tests/fakes.py`, the only class in that module and the only class under `tests/` with a `save` after this change. It has no base class and no `now`. Its surface is `change_design.md §3`, *the fake's surface*, exactly: keyword-only constructor options `error`, `passes_to`, `only_save`; settable after construction `watch` and `hold_save`; records `saved`, `calls`, `seen`, `asked_for`, `entered`, `release`; and the order inside one `save` (count the call, call `watch`, raise `error` if set, hand on to `passes_to`, keep the state, hold if this is the held call). This task also creates `tests/integration/test_saver_contract.py` holding the fake-only checks as module-level functions; the contract suite is added to the same file by Task 2.

#### Behaviours to verify (developer adds tests to `tests/integration/test_saver_contract.py`)

- `test_saved_keeps_every_state_in_the_order_handed` — layer 1 — fakes: `FakeSaver` only — three saves leave `saved` holding the three states in order
- `test_calls_count_every_call_the_raised_ones_included` — layer 1 — fakes: `FakeSaver` only — with `error` set, `calls` grows and `saved` stays empty
- `test_the_error_set_is_the_error_raised` — layer 1 — fakes: `FakeSaver` only — the exact exception object is raised, including one assigned after construction
- `test_clearing_the_error_ends_the_raising` — layer 1 — fakes: `FakeSaver` only — after clearing, the next save is kept
- `test_watch_answer_lands_in_seen_at_each_save` — layer 1 — fakes: `FakeSaver` only — `seen` holds one answer per save, in order, and the answer is taken before the state is kept
- `test_the_held_call_keeps_its_state_and_waits_for_release` — layer 1 — fakes: `FakeSaver` only — the held save sets `entered`, has kept its state, and does not return until `release` is set
- `test_calls_other_than_the_held_one_are_not_held` — layer 1 — fakes: `FakeSaver` only — calls before and after the held number return at once
- `test_a_held_call_that_raises_is_not_held` — layer 1 — fakes: `FakeSaver` only — with `error` set on the held call, the error comes through at once and `entered` stays unset
- `test_a_hold_does_not_wait_once_release_is_set` — layer 1 — fakes: `FakeSaver` only — with `release` already set, the held call returns at once
- `test_passes_to_receives_each_save_before_the_fake_keeps_it` — layer 1 — fakes: a second `FakeSaver` as `passes_to`, handed in at construction — each state reaches the second saver, then the first keeps it
- `test_when_passes_to_raises_the_fake_keeps_nothing` — layer 1 — fakes: a second `FakeSaver` with `error` set as `passes_to` — the error comes through and `saved` stays empty
- `test_only_save_records_any_other_attribute_and_raises_assertion_error` — layer 1 — fakes: `FakeSaver(only_save=True)` — asking for `close` appends `"close"` to `asked_for` and raises `AssertionError` naming it, and a `getattr` with a default does not swallow it
- `test_without_only_save_a_missing_attribute_raises_attribute_error` — layer 1 — fakes: `FakeSaver()` — the same ask raises `AttributeError` and `asked_for` stays empty
- `test_the_fake_defines_no_now` — layer 1 — fakes: `FakeSaver()` — `now` is not an attribute (I-3)
- `test_the_fake_has_no_base_class` — layer 1 — fakes: none — `FakeSaver.__mro__` holds `FakeSaver` and `object` only (I-9)

#### Held by review

- The 10-second bound of a held call (`AssertionError` when `release` is not set in time) — covered by no test, because a test of it costs the full bound on every run. It is held by reading the diff: the wait is `release.wait(timeout=10)` asserted, as the five `HeldSaver`s it replaces carried.

#### Implement

Infer from failing tests.

# Hint: `only_save`'s refusal is a `__getattr__`, which Python reaches only for a name the instance lacks. Set every attribute the method reads in the constructor before anything can ask, or a lookup inside it recurses.

The new test file's module docstring must name an SRS requirement and name only paths that exist: `tests/architecture/test_trace.py` reads the docstring of every `test_*.py`. TS-6 serves NFR-10 and NFR-11.

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_saver_contract.py` from the repository root, then `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.

Pass criteria: the fake-only checks above pass; Ruff exits 0; no new failures elsewhere.

---

### Task 2: The contract suite for `save`, run against `SavedData` and the fake (`tests/integration/test_saver_contract.py`)

**Dependencies:** Task 1

**What to build:** `SaverContract` in the file Task 1 created: a plain base class (not `abc`, name not starting with `Test`) holding the `test_` cases below and four run hooks that each raise `NotImplementedError` in the base: `make(tmp_path, configuration)`, `kept(saver)`, `break_saves(saver)` and `mend_saves(saver)`, plus `release(saver)`. Two subclasses supply them, as `change_design.md §3`, *the suite's shape*, states: `TestSavedDataKeepsTheSaverContract` and `TestFakeSaverKeepsTheSaverContract`. The configurations are plain, `watch`, `passes_to` (to a second `FakeSaver`), `only_save` and held. The `SavedData` run writes only inside `tmp_path`.

#### Behaviours to verify (developer adds the cases to `SaverContract`; each runs in both subclasses)

- `test_nothing_is_kept_before_the_first_save` — layer 2 — fakes: none (the subject is handed in by the run) — `kept` is `None`
- `test_a_save_keeps_the_whole_state_it_was_handed` — layer 2 — fakes: none — `kept` equals a state with every field set: projects with descriptions, assignees, tasks with every field (labels, comments, due date), the operator name and both counters. This is I-4's minimum and the I-5 target
- `test_each_save_replaces_the_one_before_whole` — layer 2 — fakes: none — three distinct states saved in turn; after each, `kept` is that state
- `test_a_save_that_cannot_be_made_raises_and_keeps_nothing` — layer 2 — fakes: none — broken before any save: raises `OSError` and `kept` is `None`; broken after one kept save: raises `OSError` and `kept` is the first state
- `test_saves_are_kept_again_once_they_stop_failing` — layer 2 — fakes: none — break, a failed save, mend, a save: `kept` is the last state
- `test_a_held_save_has_kept_its_state_when_it_returns` — layer 2 — fakes: none — held configuration: save on another thread, `release`, join; the thread is done and `kept` is the state
- `test_a_configured_saver_keeps_the_whole_state_in_turn` — layer 2 — fakes: a second `FakeSaver` as `passes_to` (fake run only) — parametrized over `watch`, `passes_to` and `only_save`; the assertions of the two whole-state cases above, in that configuration

#### Implement

Tests cannot go red.

Reason: `SavedData` already keeps the whole state (`test_saved_data.py::test_save_then_load_round_trips` passes at the base) and the Task 1 fake keeps every state by construction, so no case can be made to fail first. The suite's failing side is shown by Task 3's recorded mutation (I-5).

# Hint: breaking a real save — put a directory at `persistence.saved_data.PARTIAL_FILE_NAME` inside the location, creating the location first. The save's `open` of that name then fails for any user, root included, which `chmod` does not. The kept `tracker.json` also stays readable through `load`. To mend, remove that directory. The real run hands plain `SavedData` to every configuration, since a real saver has no such controls (`change_design.md` Architect Review Notes, (b)).

The file's module docstring (Task 1) must stay true: it names an SRS requirement and only paths that exist.

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_saver_contract.py` from the repository root, then `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.

Pass criteria: both subclasses collect and every case passes in both; each case runs twice; Ruff exits 0; no new failures elsewhere.

---

### Task 3: Record the mutation that shows the suite catches a dropping fake (`tests/fakes.py`, nothing kept)

**Dependencies:** Task 1, Task 2

**What to build:** a recorded run, not a file. In `tests/fakes.py` change `FakeSaver.save` so that it keeps nothing — remove the step that appends to `saved`, and nothing else — run the suite, then restore the fake.

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- The mutation run — from the product root, `uv run --locked pytest tests/integration/test_saver_contract.py` — its command, and the pass and fail counts of each of the two runs, are in Developer Review Notes — a reader finds the command and four counts, one pair per run.
- The fake's run fails, at least in `test_a_save_keeps_the_whole_state_it_was_handed`, and the `SavedData` run passes every case — a reader sees both in the recorded counts.
- `tests/fakes.py` is restored — `git diff --quiet HEAD -- products/tracker17/tests/fakes.py` exits 0 in the change worktree, with Tasks 1 and 2 already committed.
- No state-dropping class or mode is left anywhere — `git grep -nE '^\s+def save\(' -- products/tracker17/tests` lists `tests/fakes.py` alone, once.

#### Implement

Verified by review — no test.

#### Verification gate

Run the restored suite: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_saver_contract.py` from the repository root.

Pass criteria: every criterion above is met on reading the diff and the Developer Review Notes; the suite has no new failures.

---

### Task 4: Move `test_filter_tracker.py` onto `FakeSaver` (`tests/integration/test_filter_tracker.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `RecordingSaver` (`:54`), keeps each state → `FakeSaver()`; reads `saved`. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_filter_tracker.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_filter_tracker.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_filter_tracker.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 5: Move `test_sort_tracker.py` onto `FakeSaver` (`tests/integration/test_sort_tracker.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `RecordingSaver` (`:60`), keeps each state → `FakeSaver()`; reads `saved`. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_sort_tracker.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_sort_tracker.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_sort_tracker.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 6: Move `test_summary_tracker.py` onto `FakeSaver` (`tests/integration/test_summary_tracker.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `RecordingSaver` (`:44`), keeps each state → `FakeSaver()`; reads `saved`. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_summary_tracker.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_summary_tracker.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_summary_tracker.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 7: Move `test_label_listener.py` onto `FakeSaver` (`tests/integration/test_label_listener.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `HandedSaver` (`:31`), keeps each state → `FakeSaver()`. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_label_listener.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_label_listener.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_label_listener.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 8: Move `test_listener.py` onto `FakeSaver` (`tests/integration/test_listener.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `NullSaver` (`:44`), ignores each state → `FakeSaver()`. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_listener.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_listener.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_listener.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 9: Move `test_label_routes.py` onto `FakeSaver` (`tests/integration/test_label_routes.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `Quiet` (`:270`) → `FakeSaver()`. `HeldSaver` with a `holding` switch (`:366`), holds every save once switched on → `FakeSaver()` with `hold_save` set to the next call number where `holding` was switched on; the test's own `entered` and `release` → the fake's. Once `release` is set no later save waits, so the two are the same. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_label_routes.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_label_routes.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_label_routes.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 10: Move `test_comment_routes.py` onto `FakeSaver` (`tests/integration/test_comment_routes.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `Quiet` (`:362`) → `FakeSaver()`. `HeldSaver` with a `holding` switch (`:459`) → `FakeSaver()` with `hold_save` set to the next call number where `holding` was switched on; the test's own `entered` and `release` → the fake's. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_comment_routes.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_comment_routes.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_comment_routes.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 11: Move `test_people_routes.py` onto `FakeSaver` (`tests/integration/test_people_routes.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `RaisingSaver` (`:277`), raises a given error on every save → `FakeSaver(error=…)` with the same error; `calls`. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_people_routes.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_people_routes.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_people_routes.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 12: Move `test_comment_pages.py` onto `FakeSaver` (`tests/integration/test_comment_pages.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `CountingSaver` (`:83`), passes each save on to `SavedData` and counts saves → `FakeSaver(passes_to=…)` handed the same `SavedData`; `saves` → `len(saved)`. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_comment_pages.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_comment_pages.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_comment_pages.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 13: Move `test_task_routes.py` onto `FakeSaver` (`tests/integration/test_task_routes.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `SwitchedSaver` (`:66`), passes on to `SavedData`, raises while switched to fail, counts kept saves → `FakeSaver(passes_to=…)`; `failing = True/False` → assign or clear `error` (the same `PermissionError`); `saves` → `len(saved)`. Annotations that name the removed class (the `World` dataclass) follow. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_task_routes.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_task_routes.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_task_routes.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 14: Move `test_assignee_tracker.py` onto `FakeSaver` (`tests/integration/test_assignee_tracker.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `RecordingSaver` that reads the tracker at each save (`:39`) → `FakeSaver()` with `watch` set where the stand-in's `.tracker` was set; each `*_during_save` list → `seen`. `FailingSaver` (`:53`), raises a given error on every save and counts calls → `FakeSaver(error=…)` with the same error; the count → `calls` Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_assignee_tracker.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_assignee_tracker.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_assignee_tracker.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 15: Move `test_label_tracker.py` onto `FakeSaver` (`tests/integration/test_label_tracker.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `RecordingSaver` that reads the tracker at each save (`:77`) → `FakeSaver()` with `watch` set where the stand-in's `.tracker` was set; each `*_during_save` list → `seen`. `FailingSaver` (`:91`), raises a given error on every save and counts calls → `FakeSaver(error=…)` with the same error; the count → `calls` Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_label_tracker.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_label_tracker.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_label_tracker.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 16: Move `test_move_tracker.py` onto `FakeSaver` (`tests/integration/test_move_tracker.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `RecordingSaver` that reads the tracker at each save (`:65`) → `FakeSaver()` with `watch` set where the stand-in's `.tracker` was set; each `*_during_save` list → `seen`. `FailingSaver` (`:79`), raises a given error on every save and counts calls → `FakeSaver(error=…)` with the same error; the count → `calls` Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_move_tracker.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_move_tracker.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_move_tracker.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 17: Move `test_operator_name_tracker.py` onto `FakeSaver` (`tests/integration/test_operator_name_tracker.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `RecordingSaver` that reads the tracker at each save (`:43`) → `FakeSaver()` with `watch` set where the stand-in's `.tracker` was set; each `*_during_save` list → `seen`. `FailingSaver` (`:57`), raises a given error on every save and counts calls → `FakeSaver(error=…)` with the same error; the count → `calls` Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_operator_name_tracker.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_operator_name_tracker.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_operator_name_tracker.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 18: Move `test_tracker.py` onto `FakeSaver` (`tests/integration/test_tracker.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `RecordingSaver` that reads the tracker at each save (`:38`) → `FakeSaver()` with `watch` set where the stand-in's `.tracker` was set; each `*_during_save` list → `seen`. `FailingSaver` (`:52`), raises a given error on every save and counts calls → `FakeSaver(error=…)` with the same error; the count → `calls` Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_tracker.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_tracker.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_tracker.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 19: Move `test_delete_project_tracker.py` onto `FakeSaver` (`tests/integration/test_delete_project_tracker.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `ObservingSaver` (`:35`), keeps and reads the tracker at each save → `FakeSaver()` with `watch`; `FailingSaver` (`:55`) → `FakeSaver(error=…)`; `CallRecordingSaver` (`:64`), counts saves and records any other attribute asked for → `FakeSaver(only_save=True)`; `other_access` → `asked_for`; `saves` → `calls`. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_delete_project_tracker.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_delete_project_tracker.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_delete_project_tracker.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 20: Move `test_comment_tracker.py` onto `FakeSaver` (`tests/integration/test_comment_tracker.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `RecordingSaver` that reads the tracker at each save (`:88`) → `FakeSaver()` with `watch` set where the stand-in's `.tracker` was set; each `*_during_save` list → `seen`. `FailingSaver` (`:102`), raises a given error on every save and counts calls → `FakeSaver(error=…)` with the same error; the count → `calls`. `SaveOnlySaver` (`:111`), keeps or counts and records any other attribute asked for → `FakeSaver(only_save=True)`; `other_attributes_asked_for` → `asked_for`; `saves` → `calls`. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_comment_tracker.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_comment_tracker.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_comment_tracker.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 21: Move `test_rename_tracker.py` onto `FakeSaver` (`tests/integration/test_rename_tracker.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `RecordingSaver` that reads the tracker at each save (`:52`) → `FakeSaver()` with `watch` set where the stand-in's `.tracker` was set; each `*_during_save` list → `seen`. `FailingSaver` (`:67`), raises a given error on every save and counts calls → `FakeSaver(error=…)` with the same error; the count → `calls`. `CallRecordingSaver` (`:76`) → `FakeSaver(only_save=True)`; `other_access` → `asked_for`; `saves` → `calls`. `TeeSaver` (`:265`), keeps and passes on to `SavedData` → `FakeSaver(passes_to=…)`; `states` → `saved`. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_rename_tracker.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_rename_tracker.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_rename_tracker.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 22: Move `test_task_tracker.py` onto `FakeSaver` (`tests/integration/test_task_tracker.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `RecordingSaver` that reads the tracker at each save (`:66`) → `FakeSaver()` with `watch` set where the stand-in's `.tracker` was set; each `*_during_save` list → `seen`. `FailingSaver` (`:80`), raises a given error on every save and counts calls → `FakeSaver(error=…)` with the same error; the count → `calls`. `_ReadingSaver(RecordingSaver)` (`:483`), two reads of the tracker at each save → one `watch` that answers both reads; each assertion reads its part of `seen`. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_task_tracker.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_task_tracker.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_task_tracker.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 23: Move `test_routes.py` onto `FakeSaver` (`tests/integration/test_routes.py`)

**Dependencies:** Task 1

**What to move:** every test-local `save` stand-in in this module is replaced by `FakeSaver` from `tests.fakes`, and its class is deleted. `RecordingSaver` (`:42`) → `FakeSaver()`; `saved`, and `restart` reads `saved[-1]`. `FailingAfterFirstSaver(RecordingSaver)` (`:50`), keeps the first save and raises after → `FakeSaver()` with `error` assigned right after the test's first save. `SwitchedRecordingSaver(RecordingSaver)` (`:873`), keeps or raises while switched → `FakeSaver()`; `failing = True/False` → assign or clear `error`. `HeldSaver` ×3 (`:409`, `:439`, `:708`), holds save 1 (or 3) until released → `FakeSaver()` with `hold_save = 1` (or `3`); the test's own `entered`, `release` and `states` → the fake's. `OnlySaves(RecordingSaver)` ×2 (`:743`, `:769`) → `FakeSaver(only_save=True)`, no subclass (I-8). `RecordingEverything` ×3 (`:824`, `:848`, `:1189`), records saves and every other attribute and fails on the others → `FakeSaver(only_save=True)`; the names it recorded → `asked_for` (others) and `len(saved)` (saves); `calls.clear()` → a count of `saved` taken at the same point. This is one task because `RecordingSaver` is the base of three of the classes above: it can be deleted only when all are replaced. Each test keeps its name and its assertions; only the saver it hands in, and the attribute it reads its facts from, change (I-1). No `now` stand-in moves, and nothing outside `tests/` is touched.

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- The module's tests all pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_routes.py` from the repository root.
- Every test in the module keeps its name, is not skipped, and asserts the same facts.
- No `def save(` is left in the module, and no class in it has a class from `tests/fakes.py` as a base: `git grep -nE '^\s+def save\(' -- products/tracker17/tests/integration/test_routes.py` lists nothing.
- Ruff passes: `uv run --locked --project products/tracker17 ruff format --check products/tracker17/tests && uv run --locked --project products/tracker17 ruff check products/tracker17/tests`.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan, the stand-in row for this module; no test file moves. **No new tests — TDD under green** (baseline green → restructure → green; no red phase).

#### Verification gate

Run `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_routes.py` from the repository root. Pass: every test in the module passes unchanged in name and assertion, the `def save(` listing above is empty, and Ruff exits 0.

---

### Task 24: The whole-change gates (no file written)

**Dependencies:** Task 1, Task 2, Task 3, Tasks 4 to 23

**What to build:** nothing. This task runs the change's closing checks on the finished branch and records each result in Developer Review Notes.

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- I-7 — from the product root, `grep -rEln --include='*.py' '^\s+def save\(' tests` lists `tests/fakes.py` alone, and `… | wc -l` prints `1` — a reader reads the listing.
- I-8 — no class outside `tests/fakes.py` has a base class that module defines: `grep -rnE 'class \w+\(.*FakeSaver' tests` lists nothing, and `FakeSaver` is never passed as a base anywhere else — a reader reads the listing.
- I-10 — from the product root, `grep -rEn --include='*.py' '^\s+def now\(' tests` prints 25 lines, and the same with `-ln` prints 24 files — a reader reads the counts.
- I-2 — `git diff --stat "$(git merge-base main HEAD)"..HEAD -- products/tracker17 ':!products/tracker17/tests'` lists nothing — a reader reads the empty output. The command is checked against the branch's merge base, never a pinned SHA.
- I-9 — no `tests/` module patches a name inside a product module and none subclasses `SavedData`: `git grep -nE 'class \w+\(SavedData\)|monkeypatch\.setattr|mock\.patch' -- products/tracker17/tests` lists nothing that is new on this branch — a reader compares with the merge base.
- I-11 — from the product root, `ruff format --check .` and `ruff check .` exit 0: `uv run --locked --project products/tracker17 ruff format --check products/tracker17` and `uv run --locked --project products/tracker17 ruff check products/tracker17` — a reader reads both exit statuses.

#### Implement

Verified by review — no test.

#### Verification gate

Run the card's full `Test command:` from the repository root: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`. The first half takes about 15 minutes.

Pass criteria: every criterion above is met; the suite passes as at the base — every test that passes at the base passes, and `tests/integration/test_timed_run.py::test_timed_run_exercises_and_reports_task_volume`, which fails in a full run under load at the base, is judged as it is there: it must pass when run alone (I-1, Locked Answers, Gap 6); the `tests/e2e/` half passes.
