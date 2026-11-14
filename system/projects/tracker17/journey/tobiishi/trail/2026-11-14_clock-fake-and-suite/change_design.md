# Change Design — one verified `Clock` fake, its contract suite, and QC-64's walk

**Date:** 2026-11-14
**Category:** nfdr
**Behaviour:** preserving
**Publishes text:** no
<!-- A preserving change adds no words, so the line is always `no`. Moving existing text is placement, and placement is the Developer's. -->
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern file it routes and `testing_python.md`

---

## 1. Change Summary

Twenty-five test-local classes stand in for the `Clock` contract today, in 24 modules under `tests/`,
4 of them in `tests/e2e/` (I-7). This change replaces the 24 stand-ins with one fake, `FakeClock`,
written once in `tests/fakes.py` beside `FakeSaver`. The 25th class, `RealClock` in
`tests/timed_run.py`, goes too, and the timed run is handed `main.SystemClock` (I-11). The change adds
one contract suite for `now`, in `tests/integration/test_clock_contract.py`, which runs handed
`SystemClock` and handed the fake. It also adds QC-64's layer-6 walk, in
`tests/architecture/test_contract_fakes.py` (I-12). Only test code changes. No module outside
`tests/` changes, so every product import surface and every production signature stay as they are
(I-2). `FakeSaver` and the `save` suite do not change (I-10).

All paths are relative to the product root, `products/tracker17`.

---

## 2. Blast Radius

No transitive blast radius: public surfaces are unchanged, so no importing module is affected. No
product module is touched. Every module below is test code.

| Module | Status | What changes |
|---|---|---|
| `domain/`, `application/`, `persistence/`, `web/`, `main.py`, `errors.py`, `.behave/` | Unchanged | — |
| `tests/fakes.py` | Modified | Adds `FakeClock` beside `FakeSaver`. `FakeSaver` is untouched, and the module docstring names both fakes (I-3, I-10) |
| `tests/integration/test_clock_contract.py` | New | The contract suite for `now`, run twice at layer 2, and the fake-only checks of its configurations (§ 5) |
| `tests/architecture/test_contract_fakes.py` | New | QC-64's layer-6 walk, its failure tests, and its run over the product (I-12) |
| the 23 modules in § 3 that define a stand-in, other than `tests/timed_run.py` | Modified (test stand-in only) | The stand-in class goes. Each test hands the tracker a `FakeClock` configured as § 3 says, and reads `reads` and `instant` off the fake. Every test keeps its name and its assertions (I-1) |
| `tests/timed_run.py` | Modified | `RealClock` goes, and the two sites that built it build `main.SystemClock` (I-11) |
| `tests/integration/test_timed_run.py` | Modified | `harness.RealClock()` becomes `SystemClock()`, the real clock |
| `test_people_routes.py`, `test_failure_report.py`, `test_label_routes.py`, `test_summary_routes.py`, `test_task_pages.py` (all in `tests/integration/`) | Modified (import only) | They define no stand-in. They import `FixedClock` from `test_routes` or `MovableClock` from `test_task_routes`, and import `FakeClock` from `tests.fakes` instead (I-8, Architect Review Notes, (b)) |
| `test_filter_routes.py`, `test_move_routes.py`, `test_sort_routes.py` | Unchanged | They set `world.clock.instant`. `make_world` hands them a `FakeClock`, whose `instant` can be set |
| `tests/conftest.py`, `tests/e2e/conftest.py`, `tests/unit/`, the other modules under `tests/architecture/`, `test_saver_contract.py` | Unchanged | — |

---

## 3. Layout Plan

This change replaces stand-ins rather than relocating code. So this section states the fake's
surface, the suite's shape and the walk's rules, and maps each stand-in to the fake configuration
that replaces it. It does not map symbols to modules (Architect Review Notes, (d)).

### `tests/fakes.py` — `FakeClock`'s surface (interface contract)

All the sites below are written against this surface. The spec left it to this design (I-6,
Structural Goal).

`FakeClock` has no base class and satisfies `Clock` by having `now()` (I-3, I-9). It defines no
`save`. Every instant it gives is one a test handed it, or one built from those by `step`.

- **Constructor:** `FakeClock(first, *then, step=None, runs_out=False)`. `first` is required, so
  the fake has no instant of its own. `step` is a `timedelta` or `None`, and `runs_out` is a bool.
  Both are keyword-only.
- **`now()`** counts the read in `reads`. It gives the instants handed in, one per read, in order.
  Once it has given the last one, what the next read gives depends on the configuration:
  - by default, the last instant again;
  - with `step`, the instant before plus `step`, read after read;
  - with `runs_out`, nothing: the read fails with `AssertionError`, saying the clock was read more
    times than it was given instants.
- **`instant`** is a property. Reading it gives the instant the next read will give. Setting it
  makes the next read give that instant, and the instants after it stay queued.
- **`restart(first, *then)`** hands out these instants from now on, and sets `reads` back to 0.
- **`reads`** counts every read since the fake was built or last restarted.
- **The fake keeps the contract in every configuration (I-6).** The constructor, `restart` and the
  `instant` setter each refuse an instant that is not an aware `datetime` with a UTC offset of zero,
  raising `ValueError` that names it. The constructor also refuses `step` and `runs_out` together
  with `ValueError`, because the two cannot both decide what the read after the last instant gives.
  A `step` added to a UTC instant stays UTC, so no read can give an instant that is naive or off UTC.

### `tests/integration/test_clock_contract.py` — the suite's shape

`ClockContract` is a plain base class: not `abc`, and its name does not start with `Test`
(`testing_python.md` § Rules). It holds the contract cases of § 5 and one hook, `make(configuration)`,
which raises `NotImplementedError` in the base. Every case is parametrized over the configurations
below, reads `now()` three times, and asserts on each instant it reads.

Two subclasses supply the hook:

- `TestSystemClockKeepsTheClockContract`: `make` gives `main.SystemClock()` and ignores the
  configuration, because the real clock has none and the contract it must keep is the same. It reads
  the machine's clock and touches no file, so it takes no `tmp_path` (I-4).
- `TestFakeClockKeepsTheClockContract`: `make` gives a `FakeClock` in the named configuration.

The configurations are the behaviours the moved tests use (I-6):

| Configuration | The fake `make` gives |
|---|---|
| `fixed` | one instant |
| `sequence` | two instants, so the third read repeats the last |
| `runs_out` | three instants with `runs_out`, so the three reads stay within them |
| `step` | one instant with a one-minute `step` |
| `moved` | one instant, then `instant` set to another before the first read |
| `restarted` | one instant, read once, then `restart` with two others |

### `tests/architecture/test_contract_fakes.py` — the walk's rules

One function, given the product root and the product's source walk (the `walk_of` fixture's
`SourceWalk`), returns a list of findings. Its run over the product asserts that list is empty. It
reads:

- **The contract methods:** the method names, without a leading underscore, defined in each class in
  `application/contracts.py` whose base is `Protocol`. That is `save` and `now` today. A missing
  file, or one with no such method, is a finding.
- **The test modules:** every `.py` under `tests/`, `tests/e2e/` included, read as a syntax tree.
  `__pycache__` is skipped. No module is a finding.
- **The test-support module:** `tests/fakes.py`, and the classes it defines. A missing module is a
  finding.

It then finds, each with its module and line:

- a class outside `tests/fakes.py` that defines a contract method;
- a class outside `tests/fakes.py` whose base names a class `tests/fakes.py` defines, spelled as a
  bare name or as an attribute;
- a contract method that no class in `tests/fakes.py` defines (no fake);
- a contract method with no suite run both ways. A suite run both ways is a class under `tests/`
  that defines at least one `test_` method and has at least two subclasses under `tests/`. The body
  of one subclass names the method's fake. The body of another names a real implementation: a class
  in the source walk that defines the method and whose base is not `Protocol`. Today those are
  `SavedData` and `SystemClock`.

Its failure tests build a product tree in `tmp_path` whose contract is `Pinger`, with one method,
`ping` (§ 4).

### Stand-in → fake configuration

| Stand-in | Sites | Behaviour it gives the test | Replaced by |
|---|---|---|---|
| `FixedClock`, `_FixedClock`, `SeedClock` (one instant, fixed in the body) | `e2e/test_delete_project.py:46`, `e2e/test_filters.py:30`, `e2e/test_sorting.py:31`, `e2e/test_summary.py:62`, `test_delete_project_tracker.py:31`, `test_label_listener.py:27`, `test_label_tracker.py:36`, `test_listener.py:40`, `test_routes.py:36`, `test_saved_data.py:63`, `test_tracker.py:34` | one fixed instant | `FakeClock(<that instant>)`, the module's own constant where it has one |
| `FixedClock` with an instant handed in | `test_move_tracker.py:38` | one fixed instant, `CREATED` or the one handed in | `FakeClock(<the instant>)` |
| `CountingClock` | `test_assignee_tracker.py:31`, `test_comment_pages.py:75`, `test_operator_name_tracker.py:35`, `test_rename_tracker.py:44` | one fixed instant; counts reads | `FakeClock(<that instant>)`; `reads` |
| `SequenceClock` | `test_filter_tracker.py:41`, `test_task_tracker.py:48` | each instant given, then the last again; counts reads | `FakeClock(*instants)`. With none given, the module's default (`CREATED`), passed explicitly; `reads` |
| `SequenceClock` with `restart` | `test_sort_tracker.py:42`, `test_summary_tracker.py:30` | the same, and `restart` | the same, default `CREATED` or `NOON`; `restart` |
| `ListClock` | `test_comment_tracker.py:44` | each instant given once, no repeat; counts reads | `FakeClock(*instants, runs_out=True)`; `reads` |
| `_SteppingClock` | `test_saved_data.py:1279` | `NOW`, then a minute after the one before | `FakeClock(NOW, step=timedelta(minutes=1))` |
| `MovableClock` | `test_task_routes.py:58` | an instant the test sets between reads, default `NOON` | `FakeClock(NOON)` or `FakeClock(<the instant>)`; `instant` |
| `ReadCountingClock(MovableClock)` | `test_comment_routes.py:48` | the same, default `WRITTEN`; counts reads | `FakeClock(WRITTEN)`; `reads`; `isinstance(world.clock, FakeClock)` (I-8: no subclass) |
| `RealClock` | `tests/timed_run.py:341` | the machine's clock | `main.SystemClock()`: the real clock, not the fake (I-11) |

Where a stand-in was built with no argument, the site passes the instant its default was, so every
test reads the same instants as at the base. A type annotation naming a stand-in names `FakeClock`.

No build sequence. `FakeClock` lands first in practice, because the suite, the walk's run over the
product and every site import it. That is the only edge.

---

## 4. Code Strategy

| Module | Hint |
|---|---|
| `tests/fakes.py` | Hold the instants still to come as one list whose head is `instant`. A read takes the head and drops it while more than one is left. With one left, it keeps it (default), replaces it with itself plus `step`, or empties the list (`runs_out`). An empty list fails the read. `instant` is the head, and setting it replaces the head. The UTC check is one private function that the constructor, `restart` and the setter all call. |
| `tests/integration/test_clock_contract.py` | The contract cases state the contract against the instant read: `isinstance(x, datetime)`, `x.utcoffset() is not None`, `x.utcoffset() == timedelta(0)`. Do not import the fake's own check, or I-5's mutation would reach both runs. The module docstring must name an SRS requirement and only paths that exist, because `tests/architecture/test_trace.py` reads it. TS-6 serves NFR-10 and NFR-11. |
| `tests/architecture/test_contract_fakes.py` | **No fixture line may start with whitespace then `def now(` or `def save(`.** I-7 and I-10 grep every line under `tests/`, string literals included. That is why the fixture contract is `Pinger.ping`. It also shows the walk reads its method names off the contracts file. Name a class in a subclass body by any `ast.Name` id or `ast.Attribute` attr in that class's subtree. The docstring follows the same trace rule as the suite's. |
| `tests/timed_run.py` | `PRODUCT_ROOT` is already on `sys.path` (`:77`), so `from main import SystemClock` resolves. `main` starts nothing on import (its entry is under `if __name__ == "__main__":`, `main.py:202`). |
| the other modules in § 2 | None |

---

## 5. Test Continuity

The existing suite is the characterization contract. Every test that exists at the base still exists,
is not skipped and asserts the same facts. Only the clock it hands in changes, and with it the
attribute it reads (I-1). The timed run and its test are judged as at the base (I-11).

**New tests: the contract suite, the fake-only checks and the walk.** They test test code, not
product behaviour.

| Test | Layer | Fakes handed in | Asserts |
|---|---|---|---|
| `ClockContract.test_now_gives_a_datetime` | 2 — both runs, every configuration | none (the subject) | each of three reads is a `datetime` |
| `ClockContract.test_now_gives_an_aware_instant_at_utc` | 2 — both runs, every configuration | none | each of three reads is aware and its UTC offset is zero. This is I-4's minimum and the I-5 target |
| fake-only checks, module-level functions beside the suite | 1 | `FakeClock`s only | Fixed: every read gives the one instant. Sequence: each instant in order, then the last again. `runs_out`: each once, then a read fails with `AssertionError`. `step`: the reads after the last are each one step later. `instant`: reading it gives the next read's instant, and setting it makes the next read give it. `restart`: the new instants in order, with `reads` back at 0. `reads` counts every read. A naive instant and an instant at `+02:00` are each refused with `ValueError` by the constructor (as `first` and in `then`), by `restart` and by the `instant` setter. `step` with `runs_out` is refused with `ValueError`. `FakeClock` has no base class and defines no `save` |
| `test_contract_fakes.py`, the run over the product | 6 | none | the walk's findings over the product root are `[]` |
| `test_contract_fakes.py`, one failure test per I-12 case | 6 | none (a tree in `tmp_path`) | One `Pinger` tree that passes, and from it, one finding each for: a contracts file with no method; a class outside the support module that defines `ping`; a class outside it whose base is the fake; no support module; no fake for `ping`; a suite with only the fake's subclass; a `tests/` with no module |

**I-5, the recorded mutation.** Change `FakeClock.now` so that it gives its instant with the time zone
removed (`replace(tzinfo=None)` on the return), and nothing else. Run
`uv run --locked pytest tests/integration/test_clock_contract.py` from the product root. The fake run
must fail `test_now_gives_an_aware_instant_at_utc` in every configuration, and the `SystemClock` run
must pass. Then restore the fake. The command, both runs' counts and the restore go into the
change's Developer Review Notes. No naive-giving class is written anywhere, so I-3, I-7 and I-8 still
hold.

**What the change stops proving, and what proves it now:**

- **`ListClock`'s `IndexError` on a read past its instants.** It becomes `runs_out`'s
  `AssertionError`. The read still fails, and a fake-only check proves it.
- **The defaults of the no-argument stand-ins** (`SequenceClock()`, `MovableClock()`,
  `ReadCountingClock()`, `FixedClock()` in `test_move_tracker.py`). Each site passes the instant
  explicitly, so no assertion that reads one moves.
- **`RealClock` in the timed run.** `SystemClock` is the code it copied (`tests/timed_run.py:341-343`,
  `main.py:81-85`), so the timed run and `test_timed_run.py` read the same clock.

No other assertion is retired.

**The gates after the change:** I-7's grep lists `tests/fakes.py` alone, and its `-l` count prints
`1`. I-10's `save` grep lists `tests/fakes.py` alone. No class outside it bases on a class it defines
(I-8). A syntax-tree read of every import under `tests/` finds no clock imported from a test module
other than `tests.fakes`, multi-line imports included (I-8). The I-2 diff from
`8c2f588bb` lists nothing outside `tests/`. `ruff format --check .` and `ruff check .` exit 0 (I-13).
`uv run --locked python tests/timed_run.py` exits 0 (I-11). Both halves of the card's
`Test command:` pass (I-1).

---

## Records this change makes false

- `docs/nfdr.md` QC-64, *verified by* — "The entry starts unmet: at `373ecc8a8` neither the
  test-support module nor a contract suite exists, and 64 classes … stand in for the clock or the
  saver" reads as the entry's state, and it goes false: both fakes and both suites exist, no stand-in
  is left, and the walk runs → the entry is met. It should name `tests/fakes.py`,
  `tests/integration/test_saver_contract.py`, `tests/integration/test_clock_contract.py` and
  `tests/architecture/test_contract_fakes.py` with its run over the product. It should keep the
  dated start as "started unmet at `373ecc8a8`", in the form QC-39 uses.

Read and holding: `docs/adr/` (0001 to 0016), `docs/nfdr.md` (QC-3, QC-12, QC-28, QC-40, QC-41,
QC-60, QC-62, QC-64, § 9, § 10, RN-65, RN-70), `docs/fdr.md`, and `docs/SDD.md` § 3 and § 4 TS-6.

---

## Architect Review Notes

- **(d) The Layout Plan is a replacement map:** the template's shape, symbols moved behind
  `__init__.py` re-exports, has nothing to place. No symbol moves and no import surface changes. § 3
  instead maps each stand-in to the fake configuration that replaces it. It also states the fake's
  surface, the suite's hook and the walk's rules, which the spec left to this design. This is the
  shape the `Saver` change's design took.
- **(e) Test code has no owning part:** SDD § 3's `Owns` column covers the five product parts, and
  `tests/` is none of them. The fake goes in `tests/fakes.py`, which QC-64 names. The suite sits in
  `tests/integration/`, filed with layer 2's tests beside `test_saver_contract.py` (NFDR § 9,
  level 2). The walk sits in `tests/architecture/` (layer 6).
- **(b) Six modules import a clock from another test module, not the spec's three:** I-8 names the
  three that import `MovableClock` on one line. A syntax-tree read of every import also finds
  `test_label_routes.py:19` and `test_task_pages.py:20`, multi-line imports of `MovableClock`, and
  `test_people_routes.py:25`, a multi-line import of `FixedClock` from `test_routes`. I-8's rule,
  "import no clock from another test module", covers all six, and the stand-ins they import are gone
  anyway. So the design moves all six onto `tests.fakes`, and sets no spec line aside.
- **(b) The fake refuses an instant off the contract:** I-6 left it to this design how the fake treats
  a naive or off-UTC instant handed to it. It refuses with `ValueError` wherever it takes an
  instant. That is stricter than any stand-in, never looser. The spec's Verified Claims found no
  instant handed to a clock that is not UTC, so no moved test meets the refusal.
- **(b) The fake has no instant of its own:** `first` is required. A default would be one more
  instant a reader has to know. The stand-ins' defaults differed (`CREATED`, `NOON`, `WRITTEN`), so
  each site passes its own and keeps reading the same instants.
- **(b) `runs_out` keeps `ListClock`'s guard:** without it, a third read in a `ListClock` test would
  give the last instant again instead of failing. That would loosen the fake for that test, which I-6
  forbids.
- **(b) How the walk tells a suite runs both ways:** by structure, not by name. The suite is a base
  class with `test_` methods. It needs one subclass whose body names the fake and one whose body names
  a class in product code that defines the method. A suite whose real side is missing therefore fails
  the walk, whatever the classes are called. Rejected: matching `<Contract>Contract` and `Test…`
  names, which a renamed suite would slip past.
- **(b) The contract cases are two:** a `datetime`, and aware at UTC. That is all the contract's
  docstring states. Rejected: a case that successive reads never go back. The contract does not say
  so, the machine's clock can step back, and `restart` and `instant` let a test go back on purpose.
- **The walk is built here, as the spec's Gap 1 decided:** the request defers it to the seed's third
  item. The spec folds it in on QC-64's *verified by*, NFDR § 9 and RN-65, and the design follows
  the spec. It is test code, so the change stays preserving.
- **Packet check, no conflict:** the `SystemClock` run reads the machine's clock and touches no file,
  which NFDR § 9 level 2 allows for the real clock. The fake-only checks touch no real resource. The
  walk's failure tests write only under `tmp_path`. Nothing is patched (QC-28). The walk is given the
  root and the source walk, rather than reaching for them. No production module is edited.
- **QC-12 review, pass:** the change adds two test modules and one fake, and removes 25 classes.
  TS-6 and QC-64 pay for each.
- **QC-60 review, pass:** only Python 3.11 standard library (`datetime.UTC`, `timedelta`, `property`,
  `ast`) and pytest 9.1.1 features.
- **QC-41 review, pass:** no secret is read, held or written.
- **QC-25, QC-26, QC-27 and the other `development-design` reviews tied to a part:** not triggered.
  No part's code, no contract and no dependency changes, and nothing under `.behave/` moves.
- **QC-40 review, every-review moment, packages: met.** All 27 pinned packages in `uv.lock` and
  `.behave/uv.lock` were checked against OSV's PyPI advisories on 2026-11-14 (`/v1/querybatch`), and
  none has one. No dependency is added or moved.
- **QC-40 review, every-review moment, browser build: not blocking, owed by 2026-12-11.** The pinned
  build is Chromium 158.0.8127.18. The vendor's release feed, read 2026-11-14, holds nothing newer
  with a Critical than the Stable Channel Update for Desktop of 2026-11-11 (157.0.8103.78):
  CVE-2026-126846, CVE-2026-126879, CVE-2026-126885, CVE-2026-126895 and CVE-2026-126911. The Early
  Stable Update of 2026-11-12 (158.0.8127.36) names no security fix. The vendor does not say whether
  158.0.8127.18 carries the 2026-11-11 fixes, so this review treats the build as affected. The
  advisories are 3 days old, inside the 30-day window.
- **QC-40 review, package feed: down, moment still owed.** The checking account has admin on the
  repository that holds tracker17. The Dependabot alerts endpoint answered "Dependabot alerts are
  disabled for this repository." (403), and the SBOM export answered 404. By QC-40's words the feed is
  down, so no discrepancy is raised.
