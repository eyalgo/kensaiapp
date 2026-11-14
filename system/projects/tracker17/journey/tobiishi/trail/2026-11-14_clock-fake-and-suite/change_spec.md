# Change Spec — one verified `Clock` fake, its contract suite, and QC-64's walk

**Date:** 2026-11-14
**Category:** nfdr
**Behaviour:** preserving
**Request:** Give the `Clock` contract (`application/contracts.py`, method `now`) the one fake and the one contract suite NFDR QC-64 and SDD § 4 TS-6 ask for. Add the `Clock` fake to the test-support module `products/tracker17/tests/fakes.py`, beside the `Saver` fake: a class with a `now` method, written once. Add a layer-2 contract suite for `now` that runs twice: handed `main.SystemClock`, which reads the machine's clock and touches no file, and handed the fake. The suite holds at least one case that fails the fake when the fake is made to break the contract (a fake whose `now` returns a naive datetime fails the suite, because the contract is an aware UTC instant as `SystemClock` returns, while `SystemClock` still passes), shown by a test or a recorded mutation. Then move every test's own `now` stand-in onto the fake, in `tests/` and `tests/e2e/`. Before the change, `grep -rEn --include='*.py' '^\s+def now\(' tests` run from `products/tracker17` matches 25 lines in 24 files (measured 2026-11-14 at `a7c798a4a`). After it, the same command matches in exactly one file, `tests/fakes.py`, and `grep -rEln --include='*.py' '^\s+def now\(' tests | wc -l` prints `1`. A test that needed behaviour its own stand-in had (for example a fixed instant, one that advances, or one that records calls) gets that behaviour added to the fake, with its case in the suite; the fake is never loosened to make a test pass. The fake does not inherit from `Clock`, and `SystemClock` is not subclassed or patched (QC-3). The `Saver` fake and its suite stay as the previous change left them, except where a test needs a `Clock` case in a shared module. Production code under `application/`, `domain/`, `persistence/`, `web/` and `main.py` is unchanged, and if the contract needs a change it is raised, not made here: `git diff --stat <base>..HEAD -- products/tracker17 ':!products/tracker17/tests'` lists no file outside `tests/`. The whole suite passes: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` from the repository root, and `tests/e2e/` as the card's Test command also runs it. The layer-6 walk that keeps the whole shape is the seed's third item and is not built here.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened

---

## Change Summary

The `Clock` contract gets one fake, written once in the test-support module beside the `Saver`
fake, and one contract suite that runs at layer 2 handed `main.SystemClock` and handed the fake.
Every test-local `now` stand-in goes, and with both contracts done, QC-64's layer-6 walk lands so
the shape stays held. Only test code changes, and the product's behaviour and public interface stay
as they are.

All paths below are relative to the product root, which `project.md` `Product path:` names, unless a
command says it runs from the repository root.

---

## Invariants (characterization contract)

- **I-1: The existing suite still passes, and no test loses an assertion.** Both halves of the
  card's `Test command:` pass. Every test that exists at the base still exists, is not skipped, and
  keeps asserting the same facts. Only the object it hands the tracker as its clock changes, from
  its own stand-in to the fake (or, for the timed run, to the real clock, I-11), and the attribute
  it reads a count of reads from may change with it.
- **I-2: The public interface is identical.** No file outside `tests/` changes, so production code
  under `application/`, `domain/`, `persistence/`, `web/`, `main.py` and `errors.py`, and the Behave
  folder `.behave/`, stay as they are. The check is
  `git diff --stat <base>..HEAD -- products/tracker17 ':!products/tracker17/tests'`, run from the
  repository root, and it lists nothing. `<base>` is the change's merge base with `main`. If the
  `Clock` contract turns out to need a change, that change is raised and not made here.
- **I-3: One `Clock` fake, written once (NFDR QC-64; SDD § 4 TS-6).** `tests/fakes.py` defines
  exactly one class with a `now` method, the `Clock` fake, beside `FakeSaver`. The fake has no base
  class, so it does not inherit from `Clock`. It defines no `save`, and `FakeSaver` still defines no
  `now`.
- **I-4: One contract suite for `now`, run twice at layer 2 (NFDR QC-64; SDD § 4 TS-6; NFDR § 9
  level 2).** `pytest tests/` collects one contract suite for `now`. The suite states the contract's
  behaviour once, as cases written against the `Clock` contract alone. It runs twice, once handed
  `main.SystemClock` and once handed the fake, and every case in it runs in both runs. The
  `SystemClock` run reads the machine's clock and touches no file. Both runs are filed with layer
  2's tests. A fake that fails a case fails `pytest tests/`. At the least, the suite checks that
  `now` returns a `datetime` that is aware and whose UTC offset is zero, which is what the contract's
  docstring states and `SystemClock` returns. The full set of cases is development-design's call,
  beyond that one and the cases I-6 adds.
- **I-5: The suite catches a fake that breaks the contract.** Suppose the fake's `now` is changed
  so that it returns a naive datetime. Then the suite fails in the fake's run, and the `SystemClock`
  run still passes. This is shown either by a test or by a recorded mutation, and either way I-3,
  I-7 and I-8 still hold afterwards.
- **I-6: The fake grows, and is never loosened (NFDR QC-64; SDD § 4 TS-6).** Some tests use a
  behaviour their own stand-in gives them today. The fake gives each of those behaviours, and each
  one has its case in the suite. Every way a test configures the fake still keeps the contract: the
  contract cases of I-4 hold for the fake in each configuration the moved tests use, so a
  configured fake never returns an instant that is naive or off UTC. How the fake treats such an
  instant handed to it is development-design's call, within that. If a test fails on the fake, the
  fix is never to weaken the fake or the suite.
  **The domain is every behaviour that a stand-in being moved gives the test that uses it.** This
  spec does not fix the list. The base shows these, and they are candidates only:
  - one fixed instant, a default one or one the test gives (`FixedClock`, `_FixedClock`, `SeedClock`);
  - the instants it was given, one per read, then the last one again (`SequenceClock`);
  - the instants it was given, one per read, with no repeat (`ListClock`);
  - an instant a minute after the one before (`_SteppingClock` in `tests/integration/test_saved_data.py`);
  - an instant the test sets between reads (`MovableClock` in `tests/integration/test_task_routes.py`);
  - new instants handed out from a point on, with the read count back at zero (`restart` on
    `SequenceClock` in `test_sort_tracker.py` and `test_summary_tracker.py`);
  - counting the reads (`CountingClock`, `ReadCountingClock`, the `reads` of `SequenceClock` and
    `ListClock`).
- **I-7: No test-local `now` stand-in is left.** Run
  `grep -rEn --include='*.py' '^\s+def now\(' tests` from the product root. It matches in exactly
  one file, `tests/fakes.py`, and `grep -rEln --include='*.py' '^\s+def now\(' tests | wc -l` prints
  `1`. At the base it matches 25 lines in 24 files, 4 of them in `tests/e2e/`.
- **I-8: No test-local subclass of the fake stands in either (NFDR QC-64).** No class outside
  `tests/fakes.py` has a base class that module defines. Today `ReadCountingClock(MovableClock)` at
  `tests/integration/test_comment_routes.py:48` subclasses another test module's stand-in. After the
  change it must not become a subclass of the fake. The three modules that import `MovableClock`
  from `test_task_routes` (`test_comment_routes.py:24`, `test_failure_report.py:27`,
  `test_summary_routes.py:21`) import no clock from another test module after it.
- **I-9: Every contract is satisfied structurally, and nothing is patched.** This is the request's
  rule, and it reaches into `tests/` further than QC-3 does. The fake does not inherit from `Clock`.
  No test subclasses `SystemClock` or patches it. No test patches a name inside a product module,
  which NFDR QC-28 also requires and its existing layer-6 walk in `tests/architecture/test_reach.py`
  checks.
- **I-10: The `Saver` side stays as the previous change left it.** `FakeSaver` and the `save` contract
  suite are unchanged, except where a test needs a `Clock` case in a shared module.
  `grep -rEln --include='*.py' '^\s+def save\(' tests` still lists one file, `tests/fakes.py`.
- **I-11: The timed run keeps reading the machine's clock (SDD § 4 TS-5).** `tests/timed_run.py`
  defines no class with `now` after the change, and it is handed the real clock rather than the fake
  (Locked Answers, Gap 2). Run as TS-5 names it, from the product root through the suite's
  environment (`uv run --locked python tests/timed_run.py`), it exits 0, as it does at the base, and
  `tests/integration/test_timed_run.py` keeps passing under I-1.
- **I-12: QC-64's layer-6 walk lands, and passes (NFDR QC-64; NFDR § 9 layer 6).** A plain pytest
  module under `tests/architecture/`, run by `pytest tests/`, walks every module under `tests/`,
  `tests/e2e/` included. It reads the method names off the `Protocol` classes in
  `application/contracts.py`, `save` and `now` today, rather than from a list. It fails:
  - when it reads no method name;
  - on a class outside the test-support module that defines one of those methods;
  - on a class outside the test-support module whose base is a class that module defines;
  - when the test-support module is missing;
  - on a contract with no fake in that module;
  - on a contract with no suite run against both the real implementation and the fake;
  - when the directory it walks holds no module, as NFDR § 9 has every layer-6 walk do.

  Each failure is shown by a test or a recorded mutation. On the tree after this change it passes.
  It is the check QC-64's *verified by* names, and this change logs it under Locked Answers as (e),
  Gap 1.
- **I-13: The Ruff gates pass (NFDR QC-62).** From the product root, `uv run --locked ruff format
  --check .` and `uv run --locked ruff check .` both exit 0, as they do at the base, over the new
  and changed test code included. QC-62's mypy gate covers no part of `tests/` (Locked Answers,
  Gap 3).
- **I-14: Every new test module names what it checks (SDD § 4 TS-3; NFDR QC-11).** The contract
  suite's module and the walk's module each open with a docstring that names the requirements or
  acceptance criteria they check, and every path it names exists. The existing
  `tests/architecture/test_trace.py::test_every_test_module_names_a_requirement_or_acceptance_criterion`
  fails otherwise (Locked Answers, Gap 3).

---

## Structural Goal

- Each test's own stand-in for the clock becomes one verified fake. That fake lives beside
  `FakeSaver` in the test-support module, a contract suite checks it against `SystemClock`, and every
  test that needs a clock it controls uses it. QC-64's walk then holds the whole shape for both
  contracts.
- The fake's configuration surface, how a configured behaviour's case is stated, where the suite
  and the walk are filed, and how the walk tells that a contract's suite runs both ways are
  development-design's call, inside I-3 to I-12.

---

## Verified Claims

Run in the change worktree on 2026-11-14. Its base is `8c2f588bb`, and the product is unchanged
between it and `a7c798a4a`, the request's measure: `git diff --stat a7c798a4a 8c2f588bb --
products/tracker17` printed nothing.

| Claim | Verified by | What came back |
|---|---|---|
| I-7 base: 25 lines in 24 files, 4 in `tests/e2e/` | `grep -rEn … '^\s+def now\(' tests \| wc -l`; the same with `-ln`; the same with `-ln` over `tests/e2e` | `25`; `24`; `4` |
| I-7, I-8: every class under `tests/` that defines `save` or `now`, or subclasses a class `tests/fakes.py` defines | an `ast` walk of every module under `tests/` | 25 classes defining `now`, the 25 grep lines; none defining `save` outside `tests/fakes.py`; none subclassing `FakeSaver`; `ReadCountingClock(MovableClock)` at `test_comment_routes.py:48` |
| I-8: `MovableClock` imported across test modules | `grep -rn "import.*MovableClock" tests` | `test_comment_routes.py:24`, `test_failure_report.py:27`, `test_summary_routes.py:21`, from `test_task_routes` |
| I-6: every instant a test hands a stand-in is aware UTC | `grep -rnP 'tzinfo=(?!UTC)\|timezone\(\|ZoneInfo\|tzinfo=None\|\.replace\(tzinfo' tests` | none handed to a clock; the two hits are `_local_today()` in `timed_run.py:1394` and `test_timed_run.py:3805`, which read the machine's day |
| I-4, I-5: `SystemClock` returns an aware UTC instant, and has no base | `uv run --locked python -c` importing `main` and calling `SystemClock().now()` | `datetime`, tzinfo `UTC`, offset `0:00:00`; bases `(object,)` |
| I-12: the method names the walk reads | `vars(application.Clock)`; `application/contracts.py` | `now`; `Saver.save` and `Clock.now`, the two `Protocol` classes |
| I-12: no QC-64 walk yet | `grep -ln QC-64 tests/architecture/*.py` | none |
| I-12: after this change, the walk's only base findings are gone | the `ast` walk above | the base findings are the 25 `now` classes, which I-7 removes, and a `Clock` with no fake and no suite, which I-3 and I-4 add; the `Saver` contract has `TestSavedDataKeepsTheSaverContract` and `TestFakeSaverKeepsTheSaverContract` in `tests/integration/test_saver_contract.py` |
| I-1 base: the suite | `uv run --locked --project products/tracker17 pytest -q products/tracker17/tests/` from the repository root | 3383 passed, 2 skipped, exit 0, 6 min 39 s |
| I-1 base: the browser half | `uv run --locked --project products/tracker17 pytest -q products/tracker17/tests/e2e/` from the repository root | 122 passed |
| I-11 base: the timed run | `uv run --locked python tests/timed_run.py` from the product root | exit 0, 3 s |
| I-11, Gap 2: the timed run needs the machine's clock | in a disposable copy, `RealClock.now` changed to return 2026-10-11 12:00 UTC, the timed run run with the worktree's interpreter | exit 1; `open a project summary at 1000 tasks: … — refused or failed` |
| I-11: the timed run's clock is a copy of the real one | `tests/timed_run.py:341-343`; `main.py:81-85` | both return `datetime.now(UTC)` |
| I-13 base | `uv run --locked ruff format --check .`; `uv run --locked ruff check .` from the product root | exit 0 (374 files already formatted); exit 0 (All checks passed!) |
| I-14: the trace test reads every test module | `tests/architecture/test_trace.py:129-136` | fails on a module under test whose docstring names no requirement |
| I-9: QC-3 does not reach `tests/` | `docs/nfdr.md` QC-3 | it opens "Outside `tests/` and `.behave/`:" |
| No `now` stand-in in the Behave folder | `grep -rEn … '^\s+def now\(' .behave \| wc -l` | `0` |

---

## Out of Scope

- Any change to production code or to the `Clock` or `Saver` contract. A needed change is raised and
  not made here.
- Restructuring tests beyond swapping their clock: renaming, merging or moving test modules.
- The Behave folder, `.behave/`, which holds no `now` stand-in.
- A third contract. QC-64's walk reads the contracts off `application/contracts.py`, so one is bound
  the day it lands; none is added here.
- QC-64's dated counts ("64 classes across 26 modules") and its "starts unmet" reading. They are the
  NFDR's to update, and this seat edits no product record.

---

## Locked Answers (the divergence record — self-review 2026-11-14)

- **Gap 1 — QC-64's layer-6 walk is an invariant here, against the request's deferral (e):** The
  request says the walk "is the seed's third item and is not built here". QC-64's *verified by*
  names the walk. NFDR § 9 says layer 6 "is written … with the change that first builds the module
  it checks". RN-65 says that until a change moves the fakes and writes the suites, the walk fails,
  "so it lands with that change". The `Saver` change left the walk out because it would have failed
  on its tree: 25 `now` stand-ins, and a `Clock` with no fake. That reason does not hold here. This
  change removes the last stand-ins and adds the last fake and suite. On its tree, every case the
  walk fails on is gone (Verified Claims). So the check binds what this change adds, and it can
  pass. A check a record requires folds in even where the request defers it, and it does not make
  this two changes: it is the same QC-64 obligation, and the walk is that obligation's check.
- **Gap 2 — the timed run takes the real clock, not the fake:** The request moves "every test's own
  `now` stand-in onto the fake". `RealClock` in `tests/timed_run.py` is not a stand-in. It is a copy
  of `SystemClock`, and the timed run needs the machine's clock: it counts the Summary against the
  machine's own day (`tests/timed_run.py:1392-1394`). Handed a fixed instant, it fails (Verified
  Claims). A fake made to read the machine's clock would be the real clock under another name, and
  the suite could not tell the two apart. So the timed run is handed the real clock. That meets I-7
  and QC-64, because a real implementation does not stand in for itself. QC-2's "no module imports
  `main`" is scoped outside `tests/` (NFDR RN-70).
- **Gap 3 — the Ruff gates and the trace rule (e):** I-13 and I-14 are stated even though the request
  does not name them. QC-62's format and lint checks run over the whole tree, test code included,
  and SDD § 4 TS-3, held by QC-11, binds every test module. Both bind each line and module this
  change writes.
- **Gap 4 — "a folder the test makes" for the clock:** SDD § 4 TS-6 says the real implementation's
  run "works inside a folder the test makes". NFDR § 9 says the real clock's run "reads the machine's
  clock and touches no file". Both hold together: a run that touches no file stays inside any folder.
  So I-4 states the NFDR's wording, and nothing is raised.
- **Gap 5 — the citation behind the no-inheritance rule:** The request cites QC-3 for "the fake does
  not inherit from `Clock`" and "`SystemClock` is not subclassed or patched". QC-3 is scoped to code
  outside `tests/`. So I-9 rests on the request's own words, plus QC-28 for the part about patching.
  The rule is kept as the request states it.
