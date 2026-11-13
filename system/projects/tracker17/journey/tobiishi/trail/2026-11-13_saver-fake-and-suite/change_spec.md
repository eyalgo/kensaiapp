# Change Spec — one verified `Saver` fake and its contract suite

**Date:** 2026-11-13
**Category:** nfdr
**Behaviour:** preserving
**Request:** Give the `Saver` contract (`application/contracts.py`, method `save`) the one fake and the one contract suite NFDR QC-64 and SDD § 4 TS-6 ask for. Create one test-support module under `products/tracker17/tests/` (QC-64's example name is `tests/fakes.py`) that defines the `Saver` fake, a class with a `save` method that keeps the state it is given, written once. Add a layer-2 contract suite for `save` that runs twice: handed `persistence`'s `SavedData`, working in a folder the test makes (`tmp_path`), and handed the fake. The suite holds at least one case that fails the fake when the fake is made to break the contract (a `save` that drops the state fails the suite while `SavedData` still passes), shown by a test or a recorded mutation. Then move every test's own `save` stand-in onto the fake, in `tests/` and `tests/e2e/`, the ones under other names (`Quiet`, `RecordingEverything`) included. Before the change, `grep -rEln --include='*.py' '^\s+def save\(' tests` run from `products/tracker17` lists 20 files (44 lines, measured 2026-11-13 at `22365380e`). After it, the same command lists exactly one file, the test-support module. A test that needed behaviour its own stand-in had (for example one that records calls, or one that raises) gets that behaviour added to the fake, with its case in the suite; the fake is never loosened to make a test pass. The fake does not inherit from `Saver` and `SavedData` is not subclassed or patched (QC-3). No `Clock` stand-in moves: `now` stand-ins stay where they are. Production code under `application/`, `domain/`, `persistence/`, `web/` and `main.py` is unchanged, and if the contract needs a change it is raised, not made here. The whole suite passes: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` from the repository root, and `tests/e2e/` as the card's Test command also runs it.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened

---

## Change Summary

The `Saver` contract gets one fake, written once in one test-support module under `tests/`, and one
contract suite that runs at layer 2 handed `SavedData` and handed the fake. Every test-local `save`
stand-in moves onto that fake. Only test code changes, and the product's behaviour and public
interface stay as they are.

All paths below are relative to the product root, which `project.md` `Product path:` names, unless a
command says it runs from the repository root.

---

## Invariants (characterization contract)

- **I-1: The existing suite still passes, and no test loses an assertion.** Both halves of the
  card's `Test command:` pass. Every test that exists at the base still exists, is not skipped, and
  keeps asserting the same facts. Only the object it hands the tracker as its saver changes, from its
  own stand-in to the fake, and the attribute it reads those facts from may change with it. At the
  base, one test fails in a full run and passes alone. That test is
  `tests/integration/test_timed_run.py::test_timed_run_exercises_and_reports_task_volume`, and it is
  judged after the change as it is at the base (Verified Claims; Locked Answers, Gap 6).
- **I-2: The public interface is identical.** No file outside `tests/` changes, so production code
  under `application/`, `domain/`, `persistence/`, `web/`, `main.py` and `errors.py` stays as it is.
  The check is `git diff --stat <base>..HEAD -- . ':!tests'`, run from the product root, and it lists
  nothing. `<base>` is the change's merge base with `main`. If the `Saver` contract turns out to need
  a change, that change is raised and not made here.
- **I-3: One fake, written once (NFDR QC-64; SDD § 4 TS-6).** One test-support module exists under
  `tests/`. It defines exactly one class with a `save` method, and that class is the `Saver` fake.
  The fake keeps the state it is given. It does not define `now`, because the `Clock` fake belongs
  to the next station.
- **I-4: One contract suite, run twice at layer 2 (NFDR QC-64; SDD § 4 TS-6; NFDR § 9 level 2).**
  `pytest tests/` collects one contract suite for `save`. The suite states the contract's behaviour
  once, as cases written against the `Saver` contract alone. It runs twice, once handed `SavedData`
  and once handed the fake, and every case in it runs in both runs. The `SavedData` run writes only
  inside a folder the test makes (`tmp_path`). Both runs are filed with layer 2's tests. A fake that
  fails a case fails `pytest tests/`. At the least, the suite checks that the state a `save` keeps is
  the whole state it was handed. The full set of cases is development-design's call, beyond that one
  and the cases I-6 adds.
- **I-5: The suite catches a fake that breaks the contract.** Suppose the fake's `save` is changed
  so that it drops the state. Then the suite fails in the fake's run, and the `SavedData` run still
  passes. This is shown either by a test or by a recorded mutation, and either way I-3, I-7 and I-8
  still hold afterwards (Locked Answers, Gap 4).
- **I-6: The fake grows, and is never loosened (NFDR QC-64; SDD § 4 TS-6).** Some tests use a
  behaviour that their own stand-in gives them today. The fake gives each of those behaviours, and
  each one has its case in the suite, running both ways as I-4 requires. If a test fails on the
  fake, the fix is never to weaken the fake or the suite.
  **The domain is every behaviour that a stand-in being moved gives the test that uses it.** This
  spec does not fix the list. The base shows these, and they are candidates only:
  - keeping each state in the order it was handed;
  - raising a given error on every save, after the first save, or while switched to fail;
  - counting saves;
  - holding a save open until released (`HeldSaver`);
  - reading the tracker at the moment of a save (`_ReadingSaver` and the `*_during_save` observers);
  - passing each save on to another saver (`TeeSaver`, `SwitchedSaver` over `SavedData`);
  - failing a test that asks the saver for anything other than `save` (the QC-54 tests, `OnlySaves`
    and `RecordingEverything` in `tests/integration/test_routes.py`).
- **I-7: No test-local `save` stand-in is left.** Run
  `grep -rEln --include='*.py' '^\s+def save\(' tests` from the product root. It lists exactly one
  file, the test-support module, and `… | wc -l` prints `1`. At the base it lists 20 files, 44 lines,
  and none of them is in `tests/e2e/`.
- **I-8: No test-local subclass of the fake stands in either (NFDR QC-64).** No class outside the
  test-support module has a base class that the module defines. Today, `OnlySaves(RecordingSaver)`
  at `tests/integration/test_routes.py:743` and `:769` defines no `save`, so I-7's grep cannot see it.
  After the change it must not become `OnlySaves(<the fake>)` (Locked Answers, Gap 1).
- **I-9: Every contract is satisfied structurally, and nothing is patched.** This is the request's
  rule, and it reaches into `tests/` further than QC-3 does (Locked Answers, Gap 5). The fake does
  not inherit from `Saver`. No test subclasses `SavedData`. No test patches a name inside a product
  module, which NFDR QC-28 also requires and its existing layer-6 walk checks.
- **I-10: No `Clock` stand-in moves.** Run `grep -rEn --include='*.py' '^\s+def now\(' tests` from
  the product root. It prints 25 lines in 24 files, the same as at the base.
- **I-11: The Ruff gates pass (NFDR QC-62).** From the product root, `ruff format --check .` and
  `ruff check .` both exit 0, as they do at the base, over the new and changed test code included.
  QC-62's mypy gate covers no part of `tests/`, so this change cannot affect it (Locked Answers,
  Gap 2).

---

## Structural Goal

- Each test's own stand-in for the object that saves becomes one verified fake. That fake lives in
  one test-support module, a contract suite checks it against `SavedData`, and every test that needs
  a saver uses it.
- The module's name and the place where the suite is filed are development-design's call, inside
  I-3 and I-4. The record gives `tests/fakes.py` only as an example. The same goes for the fake's
  configuration surface, how each run reads back what a save kept, and how a case for a configured
  behaviour also runs handed `SavedData`.

---

## Verified Claims

Run in the change worktree on 2026-11-13. Its base is `61a5b1ecc`, and the product is unchanged
between it and `22365380e`: `git diff --stat 22365380e 61a5b1ecc -- products/tracker17` printed
nothing.

| Claim | Verified by | What came back |
|---|---|---|
| I-7 base: 20 files, 44 lines, none in `tests/e2e/` | `grep -rEln … '^\s+def save\(' tests \| wc -l`; the same with `-n`; the same over `tests/e2e` | `20`; `44`; `0` |
| I-7: the stand-ins named in the request are among them | `grep -rEn -B12 '^\s+def save\(' tests \| grep 'class '` | `Quiet` at `test_label_routes.py:270` and `test_comment_routes.py:362`; `RecordingEverything` at `test_routes.py:824`, `:848`, `:1189`; the rest of the 44 classes in `tests/integration/` |
| I-8: a stand-in the grep cannot see | `grep -rnE 'class \w+\((\w*Saver\|…)' tests` | `OnlySaves(RecordingSaver)` at `test_routes.py:743` and `:769`, with no `save` of its own |
| I-3: no test-support module yet | `ls tests/fakes.py` | no such file |
| I-10 base, and no class defines both methods | `grep -rEn … '^\s+def now\(' tests \| wc -l`, the same with `-ln`; an `ast` walk of `tests/` for classes defining `save` and `now` | `25`; `24`; none |
| I-1 base: the suite | `uv run --locked --project products/tracker17 pytest -q products/tracker17/tests/` from the repository root | 3335 passed, 2 skipped, 1 failed (`test_timed_run_exercises_and_reports_task_volume`), 15 min 23 s |
| I-1 base: the failure is about load | the same test run alone | 1 passed, 55 s |
| I-1 base: the browser half | `uv run --locked --project products/tracker17 pytest -q products/tracker17/tests/e2e/` | 122 passed; the first command collects no `tests/e2e/` test (`--collect-only`: 0) |
| I-4: `SavedData` keeps the whole state handed to it | `test_saved_data.py::test_save_then_load_round_trips` and `::test_tasks_and_counter_round_trip_every_field` | 2 passed |
| I-11 base | `uv run --locked ruff format --check .`; `uv run --locked ruff check .` from the product root | exit 0 (368 files already formatted); exit 0 (All checks passed) |
| I-9: QC-3 does not reach `tests/` | `docs/nfdr.md` QC-3 | it opens "Outside `tests/` and `.behave/`:" |
| No `save` stand-in in the Behave folder | `grep -rEn … '^\s+def save\(' .behave` | `0` |

---

## Out of Scope

- The `Clock` fake, its contract suite, and moving the `now` stand-ins belong to the next station:
  `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract`, item 2.
- QC-64's layer-6 walk, which this change does not owe (Locked Answers, Gap 3). It is item 3 of the
  same seed.
- Any change to production code or to the `Saver` contract. A needed change is raised and not made
  here.
- The timed-run test's failure in a full run under load (I-1). It exists at the base, and this
  change neither causes it nor repairs it.
- Restructuring tests beyond swapping their stand-in: renaming, merging or moving test modules.
- QC-64's pointer to "`testing_python.md` § 2". That file has no numbered § 2, and the sentence QC-64
  quotes stands in its § Rules. Repairing a product record is not this seat's job.

---

## Locked Answers (the divergence record — self-review 2026-11-13)

- **Gap 1 — a subclass of the fake counts as a stand-in (e):** I-8 is stated as an invariant. The
  request's grep sees only classes that define `save`. QC-64, however, forbids "a class outside it
  whose base is a class that module defines", and the base already has two such classes. Without I-8,
  they would pass the grep as `OnlySaves(<the fake>)`.
- **Gap 2 — the Ruff gates (e):** I-11 is stated as an invariant, even though the request does not
  name it. QC-62's format and lint checks run over the whole tree, test code included, so they bind
  every line this change writes.
- **Gap 3 — QC-64's layer-6 walk is not an invariant here:** That walk reads `save` and `now` and
  fails "on a contract with no fake" and on any stand-in for either method outside the module. On
  this change's tree it would fail on 25 `now` stand-ins and on a `Clock` with no fake. It checks the
  whole entry, not something this change adds, and NFDR RN-65 says it "lands with that change", the
  one that moves those fakes and writes the suites. This change still holds every requirement QC-64
  places on `save`, through I-3 to I-8.
- **Gap 4 — how the mutation is shown:** Suppose a test defined a state-dropping class outside the
  module. It would break I-7 and I-8. And a dropping mode inside the fake would loosen it, against
  I-6. So the form has to keep I-3, I-7 and I-8 true. A recorded mutation does this, as the request
  allows. Here that means changing the fake's `save` to drop the state, running the suite, and
  recording that the fake's run fails and the `SavedData` run passes.
- **Gap 5 — the citation behind the no-inheritance rule:** The request cites QC-3 for "the fake does
  not inherit from `Saver`" and "`SavedData` is not subclassed or patched". QC-3 is scoped to code
  outside `tests/`, so I-9 rests on the request's own words, plus QC-28 for the part about patching.
  The rule is kept exactly as the request states it.
- **Gap 6 — what "the whole suite passes" means here:** At the base, the full run is already not
  green: one timing test fails under load and passes alone. I-1 therefore asks two things. Every test
  that passes at the base must pass after. That one test must pass when run alone, as it does at the
  base. Asking for a fully green full run would make this change own a failure it did not cause.
