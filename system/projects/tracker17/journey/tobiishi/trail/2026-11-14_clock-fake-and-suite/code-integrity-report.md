# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `2026-11-14_clock-fake-and-suite` (tracker17) — one verified `Clock` fake, its contract
suite, and QC-64's layer-6 walk.
**Outcome:** clean pass. Every test added here went green on the code as the developer left it, so
there is no red commit and no code fix. Five tests were added where a wrong fake or a wrong walk
would still have passed the suite, and one docstring line was shortened to the packet's 100 columns.

All paths are relative to the product root, `products/tracker17`, unless they begin `system/`.

---

## Deferrals

**None.** The newest closing marker, `<a commit not in the public history>` (`developer: 2026-11-14_clock-fake-and-suite —
implementation complete`), carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

Every file the change's code commits touched against its merge base `8c2f588bb`: 33 files under
`tests/`, all test code.

- `tests/fakes.py` — `FakeClock` and its check `_aware_utc`, beside the unchanged `FakeSaver`.
- `tests/integration/test_clock_contract.py` — 13 checks of the fake on its own, then `ClockContract`
  and its two runs.
- `tests/architecture/test_contract_fakes.py` — QC-64's walk, its run over the product, and its
  failure cases.
- The 28 modules whose stand-in or clock import moved onto `FakeClock` (Tasks 3 to 10), and
  `tests/timed_run.py` with `tests/integration/test_timed_run.py`, which now build `main.SystemClock`
  (Task 11). Each removed stand-in was compared with the configuration that replaced it: fixed,
  sequence, `restart`, `runs_out` for `ListClock`, `step` for `_SteppingClock`, `instant` for
  `MovableClock`, and `reads` for every counting stand-in. Every default a no-argument stand-in had is
  passed explicitly. Only two assertion lines changed in the whole move: `isinstance(world.clock,
  ReadCountingClock)` became `isinstance(world.clock, FakeClock)`, and one `FixedClock()` inside an
  assertion became `FakeClock(CREATED)`, its default.

## The intent it was checked against

- `system/projects/tracker17/journey/tobiishi/2026-11-14_clock-fake-and-suite/tl_instruction.md` —
  Tasks 1 to 13, primary.
- `change_spec.md` in the same folder — invariants I-1 to I-14, and Locked Answers Gaps 1 to 5.
- `change_design.md` in the same folder — § 3, the fake's surface, the suite's shape and the walk's
  rules, which the spec left to the design.
- `docs/fdr.md` exists and was not needed: the change is test code and adds no product behaviour.

## Tests added or fixed

No test was wrong. Five were missing.

1. `tests/integration/test_clock_contract.py::test_a_refused_instant_is_named_in_the_error`
   (layer 1). Task 1 and design § 3 say every refusal is a `ValueError` "naming it", that is, naming
   the refused instant. The existing refusal tests matched only `naive|aware` or `UTC`, so an error
   that dropped the instant would have passed them. The new test checks the instant's `repr` is in
   the message from the constructor, `restart` and the `instant` setter, for a naive instant and one
   at `+02:00`.
2. `tests/architecture/test_contract_fakes.py::test_a_contract_with_a_suite_run_only_against_the_real_one_is_a_finding`
   (layer 6). I-12 fails a contract "with no suite run against both the real implementation and the
   fake". Only the fake-only side had a test. A walk that checked only for a real side would have
   passed the whole file.
3. `...::test_a_suite_whose_one_subclass_names_both_sides_is_a_finding` (layer 6). Task 12 and
   design § 3 ask for at least two subclasses, "one whose body names the method's fake and one whose
   body names a real implementation". Without this test, the walk could drop its check that the two
   are different subclasses and stay green.
4. `...::test_a_base_with_no_test_method_is_no_suite` (layer 6). The same definition says the suite
   is a class "that defines at least one `test_` method". Nothing checked that.
5. `...::test_a_subclass_that_names_only_the_contract_is_no_real_side` (layer 6). A real
   implementation is "a class in the source walk that defines the method and whose base is not
   `Protocol`". A subclass that names only the contract `Pinger` must not count as the real side.
   The developer's notes judged this edge out of scope because "the passing Pinger tree would fail
   with a finding if it did not". It would not: with the `Protocol` exclusion deleted, every earlier
   test of the file still passed (mutation M4 below).

Each one was shown to catch its fault by a recorded mutation, put back afterwards (`cmp` against a
copy taken first; `git diff -- tests/fakes.py` empty):

| Mutation | Test that went red |
|---|---|
| M1: `_aware_utc`'s message drops `{instant!r}` | test 1 |
| M2: `runs_both_ways` accepts `with_fake and with_real` without asking for two subclasses | test 3 |
| M3: the `test_`-method filter in `runs_both_ways` removed | test 4 |
| M4: `and PROTOCOL not in base_names(node)` removed from `real_implementations` | test 5 |
| M5: `runs_both_ways` accepts `with_real` alone | test 2, and test 3 |

**I-5 re-checked, not taken from the notes.** `FakeClock.now` changed to return
`instant.replace(tzinfo=None)`, then `pytest tests/integration/test_clock_contract.py -k
KeepsTheClockContract`: `test_now_gives_an_aware_instant_at_utc` failed in all six configurations of
the fake's run, and every `SystemClock` case passed (6 failed, 18 passed). The fake was restored, and
`git diff -- tests/fakes.py` against `HEAD` is empty.

## The finding

**No bug.** The fake, the suite and the walk do what the intent says, and the moves keep every test
reading the instants it read at the base.

- **Five gaps in the tests**, listed above. Each is a case the intent states and no test checked,
  now closed. None of them found wrong code.
- **One packet departure, fixed.** The first line of `tests/integration/test_clock_contract.py`'s
  docstring was 106 columns. `conventions.md` § *Surface style* holds lines to 100. Ruff's default rule
  set does not include E501, so Ruff passed it. It is now 100 columns, and the wording still names what
  the module checks for `tests/architecture/test_trace.py`. It was the only line the change added
  over 100 columns. The longer lines left in the touched modules are all lines the base already held.
- **One note in the developer's record is wrong**, as item 5 above says. Test 5 now covers that edge.

Invariants held by review, checked again on the branch:

- I-2: `git diff --stat 8c2f588bb -- . ':!tests'` from the product root lists nothing.
- I-3: `tests/fakes.py` defines `FakeSaver` and `FakeClock`. `FakeClock.__bases__ == (object,)`, it
  defines no `save`, and `FakeSaver` defines no `now`.
- I-7: `grep -rEn --include='*.py' '^\s+def now\(' tests` matches only `tests/fakes.py:99`, and the
  `-l` count prints `1`.
- I-8: a syntax-tree read of every module under `tests/` finds no clock imported from a test module
  other than `tests.fakes`, and no class outside `tests/fakes.py` based on a class it defines.
- I-9: no class under `tests/` subclasses `SystemClock`, and nothing patches it.
- I-10: `def save(` is defined only in `tests/fakes.py`, and `git diff --stat 8c2f588bb --
  tests/integration/test_saver_contract.py` is empty.
- I-11: `uv run --locked python tests/timed_run.py` from the product root exits 0.
- I-13: `uv run --locked ruff format --check .` reports 376 files already formatted, and `uv run
  --locked ruff check .` reports all checks passed, both run with this run's edits in place.

## Test evidence

- The full card `Test command:`, issued through the gate tool with gate `code-integrity`, exited 0.
  First half: 3436 passed, 2 skipped, in 396 s. Second half, `tests/e2e/`: 122 passed. The base had
  3383 passed and 2 skipped, the developer's closing run 3431 passed, and the five tests above make
  3436. No skip beyond the base's two.
- Before it, the two changed modules ran on their own: `pytest tests/integration/test_clock_contract.py
  tests/architecture/` gave 173 passed, and Ruff format and check over both files exited 0.
- pytest warned that it could not remove old temporary folders. The warning comes from a test outside
  this change, the developer's record notes the same, and it moved no result.

## Calls made

1. **What "`ValueError` naming it" asks of the message.** The readings: the message names the
   refused instant itself, or only says what kind of instant was refused. Taken: the first, checked as
   the instant's `repr` in the message, because "naming it" names the instant and the fake already
   writes it that way. Owner: the Tech Lead (Task 1) and the Architect (design § 3). If they rule the
   other way, test 1 is cut back to the type of the error and nothing else changes.
2. **Whether "one subclass … and one subclass" means two different subclasses.** The readings: two
   different subclasses, or any subclasses, so that one subclass naming both sides is enough. Taken:
   two different ones, because the design says "at least two subclasses" just before it, and because
   one subclass hands in one implementation per run, which is not a suite run both ways. The walk
   already reads it this way, so this is a test of existing behaviour, not a change. Owner: the
   Architect (design § 3). If they rule the other way, test 3 goes, and the walk's `one is not other`
   check with it.

No other question was left open by the intent.

## Placement

Step 0 ran against `docs/SDD.md` § 3. The parts table lists the five product parts (`domain`,
`application`, `persistence`, `web`, `main`), and none of them owns test code (design, Architect
Review Notes (e)). Each piece of new logic was walked:

- `FakeClock` and `_aware_utc`, in `tests/fakes.py` — **no owning part**. It sits where QC-64 and
  design § 2 put it.
- `ClockContract` and its two `Test…` subclasses, in `tests/integration/test_clock_contract.py` —
  **no owning part**. They are filed with layer 2's tests beside `test_saver_contract.py`.
- `contract_findings` and its helpers, in `tests/architecture/test_contract_fakes.py` — **no owning
  part**. They are filed with layer 6's tests.
- Tasks 3 to 11 add **no new logic**. They swap a clock and change imports.

Nothing was moved, so there is no `… — placement` commit.

## Language resolution

- Python, from step 1 of the chain, `project.md` `Languages:`.
- The packet read: `languages/python/README.md`, with every concern file it routes. Those are
  `toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`,
  `environment.md` and `testing_python.md`. Also read: the floor, `languages/developer_standards.md`,
  and beside them `arch_defaults.md` and `testing_doctrine.md`.
- What bore on this change:
  - `conventions.md` § *Surface style*, on the 100-column line, fixed above.
  - `testing_doctrine.md` § *A fake is verified against its port's contract*, with `testing_python.md`
    § Rules on its Python form: one fake in the test-support module, a plain non-`abc` base whose name
    does not start with `Test`, and two `Test…` subclasses filed with layer 2. All hold.
  - `testing_python.md` § *Layer 6*, "Enumerate from disk, never from a list": the walk reads the
    contract methods and the test modules off disk. This holds.
- No collaborator is built by code under test, and no layer-1 check touches a real resource. The
  fake-only checks hand nothing real in, and the walk's failure cases write only under `tmp_path`.
