# Change Design — one verified `Saver` fake and its contract suite

**Date:** 2026-11-13
**Category:** nfdr
**Behaviour:** preserving
**Publishes text:** no
<!-- A preserving change adds no words, so the line is always `no`. Moving existing text is placement, and placement is the Developer's. -->
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern file it routes and `testing_python.md`

---

## 1. Change Summary

Forty-six test-local classes stand in for the `Saver` contract today, across 20 modules under
`tests/integration/`: the 44 that define `save` and the two `OnlySaves` subclasses (I-7, I-8). This change replaces all 46 with
one fake, `FakeSaver`, written once in a new test-support module, `tests/fakes.py`. It also adds one
contract suite for `save`, in `tests/integration/test_saver_contract.py`, which runs once handed
`SavedData` and once handed the fake. Only test code changes. No module outside `tests/` changes, so
every product import surface and every production signature stay as they are (I-2). No `now`
stand-in moves (I-10).

All paths are relative to the product root, `products/tracker17`.

---

## 2. Blast Radius

No transitive blast radius: public surfaces are unchanged, so no importing module is affected. No
product module is touched. The modules below are test code.

| Module | Status | What changes |
|---|---|---|
| `domain/`, `application/`, `persistence/`, `web/`, `main.py`, `errors.py` | Unchanged | — |
| `tests/fakes.py` | New | The test-support module. It holds `FakeSaver` and nothing else (I-3) |
| `tests/integration/test_saver_contract.py` | New | The contract suite for `save`, run twice at layer 2, plus the fake-only checks of its records and controls (§ 5) |
| the 20 modules in § 3's site list | Modified (test stand-in only) | Each test hands the tracker a `FakeSaver` in place of its own stand-in, and reads its facts from the fake's records. Every test keeps its name and its assertions (I-1) |
| `tests/conftest.py`, `tests/e2e/`, `tests/unit/`, `tests/architecture/` | Unchanged | — (no `save` stand-in there; the `now` stand-ins stay, I-10) |

---

## 3. Layout Plan

This change replaces stand-ins rather than relocating code, so this section maps each stand-in to the
fake configuration that replaces it. It does not map symbols to modules (Architect Review Notes, (d)).

### `tests/fakes.py` — the fake's surface (interface contract)

All 46 sites are written against this surface. The spec left the surface to this design (Structural
Goal).

`FakeSaver` has no base class and satisfies `Saver` by having `save(state)` (I-9). It defines no `now`
(I-3).

- **Constructor, keyword-only, every option optional.** With no options, the fake keeps every state it
  is given.
  - `error` (an exception or `None`, default `None`). While it is set, every `save` raises it and keeps
    nothing. It may also be assigned or cleared after the fake is built: assigning it is how a test
    throws the switch.
  - `passes_to` (a `Saver` or `None`, default `None`). Each `save` is handed on to this saver before the
    fake keeps the state. When that saver raises, the fake keeps nothing and lets the error through.
  - `only_save` (bool, default `False`). When true, asking the fake for any attribute it does not
    define appends the name to `asked_for` and fails with `AssertionError` naming that attribute.
- **Settable after construction** (a test builds the tracker after its saver):
  - `watch`: a no-argument callable, or `None`. It is called at the start of each `save`, and its
    answer is appended to `seen`.
  - `hold_save`: a call number, 1-based and counting every call, or `None`. The call with that number
    keeps its state, sets `entered`, then waits on `release` for at most 10 seconds, and fails with
    `AssertionError` if `release` was not set in that time. This is the bound the stand-ins carry today.
- **Records:** `saved`, every state kept, in order. `calls`, every call to `save`, the ones that raised
  included. `seen`. `asked_for`. `entered` and `release`, two `threading.Event`s.
- **Order inside one `save`:** count the call, call `watch`, raise `error` if set, hand on to
  `passes_to`, keep the state, and hold if this is the held call.

### `tests/integration/test_saver_contract.py` — the suite's shape

`SaverContract` is a plain base class: not `abc`, and its name does not start with `Test`
(`testing_python.md` § Rules). It holds the `test_` cases of § 5 and four run hooks, each raising
`NotImplementedError` in the base:

- `make(tmp_path, configuration)`: a fresh saver that has kept nothing.
- `kept(saver)`: the state the saver holds now, or `None`.
- `break_saves(saver)` and `mend_saves(saver)`: from now on, saves raise an `OSError` and keep nothing,
  or saves are kept again.
- `release(saver)`: let a held save return.

Two subclasses supply the hooks:

- `TestSavedDataKeepsTheSaverContract`: `make` gives `SavedData` on a location inside `tmp_path`, and
  ignores the configuration, because the real saver has none and the contract it must keep is the
  same. `kept` is a fresh `SavedData(location).load()`. Breaking and mending use real means (§ 4).
  `release` does nothing.
- `TestFakeSaverKeepsTheSaverContract`: `make` gives `FakeSaver` with the configuration applied.
  `kept` is the last of `saved`, or `None`. `break_saves` sets `error` to `PermissionError`, and
  `mend_saves` clears it. `release` sets `release`.

The configurations are plain, `watch`, `passes_to` (to a second `FakeSaver`), `only_save`, and held.

### Stand-in → fake configuration

| Stand-in | Sites | Behaviour it gives the test | Replaced by |
|---|---|---|---|
| `RecordingSaver` (keeps only) | `test_filter_tracker.py:54`, `test_sort_tracker.py:60`, `test_summary_tracker.py:44`, `test_routes.py:42` | keeps each state, in order | `FakeSaver()`; `saved` |
| `HandedSaver`, `NullSaver`, `Quiet` ×2 | `test_label_listener.py:31`, `test_listener.py:44`, `test_label_routes.py:270`, `test_comment_routes.py:362` | keeps, or ignores, each state | `FakeSaver()` |
| `RecordingSaver` that reads the tracker at each save | `test_assignee_tracker.py:39`, `test_comment_tracker.py:88`, `test_label_tracker.py:77`, `test_move_tracker.py:65`, `test_operator_name_tracker.py:43`, `test_rename_tracker.py:52`, `test_task_tracker.py:66`, `test_tracker.py:38` | keeps; reads the tracker at each save | `FakeSaver()` with `watch` set where `.tracker` was set; `*_during_save` → `seen` |
| `ObservingSaver` | `test_delete_project_tracker.py:35` | the same | the same |
| `_ReadingSaver(RecordingSaver)` | `test_task_tracker.py:483` | the same, with two reads at each save | one `watch` that answers both reads; each assertion reads its part of `seen` |
| `FailingSaver` ×9, `RaisingSaver` | `test_assignee_tracker.py:53`, `test_comment_tracker.py:102`, `test_delete_project_tracker.py:55`, `test_label_tracker.py:91`, `test_move_tracker.py:79`, `test_operator_name_tracker.py:57`, `test_rename_tracker.py:67`, `test_task_tracker.py:80`, `test_tracker.py:52`, `test_people_routes.py:277` | raises a given error on every save; counts calls | `FakeSaver(error=…)` with the same error; `calls` |
| `FailingAfterFirstSaver(RecordingSaver)` | `test_routes.py:50` | keeps the first save, raises after | `FakeSaver()`, with `error` assigned right after the test's first save (Architect Review Notes, (b)) |
| `SwitchedRecordingSaver(RecordingSaver)` | `test_routes.py:873` | keeps, or raises while switched to fail | `FakeSaver()`; `failing = True/False` → assign or clear `error` |
| `SwitchedSaver` | `test_task_routes.py:66` | passes on to `SavedData`, or raises while switched; counts kept saves | `FakeSaver(passes_to=…)`; `error` switch; `saves` → `len(saved)` |
| `CountingSaver` | `test_comment_pages.py:83` | passes on to `SavedData`; counts saves | `FakeSaver(passes_to=…)`; `saves` → `len(saved)` |
| `TeeSaver` | `test_rename_tracker.py:265` | keeps; passes on to `SavedData` | `FakeSaver(passes_to=…)`; `states` → `saved` |
| `HeldSaver` ×3 | `test_routes.py:409`, `:439`, `:708` | holds save 1 (or 3) until released | `FakeSaver()`, `hold_save = 1` (or `3`); the test's own `entered`, `release` and `states` → the fake's |
| `HeldSaver` with a `holding` switch ×2 | `test_comment_routes.py:459`, `test_label_routes.py:366` | holds every save once switched on | `hold_save` set to the next call number where `holding` was switched on. Once `release` is set, no later save waits, so the two are the same |
| `SaveOnlySaver`, `CallRecordingSaver` ×2 | `test_comment_tracker.py:111`, `test_delete_project_tracker.py:64`, `test_rename_tracker.py:76` | keeps or counts; records any other attribute asked for | `FakeSaver(only_save=True)`; `other_attributes_asked_for` / `other_access` → `asked_for`; `saves` → `calls` |
| `OnlySaves(RecordingSaver)` ×2 | `test_routes.py:743`, `:769` | keeps; fails on any other attribute | `FakeSaver(only_save=True)` (I-8: no subclass) |
| `RecordingEverything` ×3 | `test_routes.py:824`, `:848`, `:1189` | records saves and every other attribute; fails on the others | `FakeSaver(only_save=True)`. The names in the record → `asked_for` (others) and `len(saved)` (saves). `calls.clear()` → a count of `saved` taken at the same point |

No build sequence. `tests/fakes.py` lands first in practice, because both the suite and the 20
modules import it. That is the only edge.

---

## 4. Code Strategy

| Module | Hint |
|---|---|
| `tests/fakes.py` | `only_save`'s refusal is a `__getattr__`, which Python reaches only for a name the instance lacks. Set every attribute the method reads in the constructor before anything can ask, or a lookup inside it recurses. |
| `tests/integration/test_saver_contract.py` | **Breaking a real save:** put a directory at `persistence.saved_data.PARTIAL_FILE_NAME` inside the location, creating the location first. The save's `open` of that name then fails for any user, root included, which `chmod` does not. The kept `tracker.json` also stays readable through `load`. To mend, remove that directory. The module docstring must name an SRS requirement and name only paths that exist: `tests/architecture/test_trace.py` reads the docstring of every `test_*.py`. TS-6 serves NFR-10 and NFR-11. |
| the 20 modules in § 3 | None |

---

## 5. Test Continuity

The existing suite is the characterization contract. Every test that exists at the base still exists,
is not skipped and asserts the same facts. Only the saver it hands in changes, and with it the
attribute it reads (I-1). The timed-run test is judged as at the base (I-1).

**New tests: the contract suite and the fake-only checks.** They test test code, not product
behaviour.

| Test | Layer | Fakes handed in | Asserts |
|---|---|---|---|
| `SaverContract.test_nothing_is_kept_before_the_first_save` | 2 — both runs | none (the subject) | `kept` is `None` |
| `…test_a_save_keeps_the_whole_state_it_was_handed` | 2 — both runs | none | `kept` equals a state with every field set: projects with descriptions, assignees, tasks with every field (labels, comments, due date), the operator name and both counters. This is I-4's minimum and the I-5 target |
| `…test_each_save_replaces_the_one_before_whole` | 2 — both runs | none | three distinct states, saved in turn; after each, `kept` is that state (order) |
| `…test_a_save_that_cannot_be_made_raises_and_keeps_nothing` | 2 — both runs | none | broken before any save: raises `OSError`, `kept` is `None`; broken after one kept save: raises `OSError`, `kept` is the first state (fails every save; fails after the first) |
| `…test_saves_are_kept_again_once_they_stop_failing` | 2 — both runs | none | break, failed save, mend, save: `kept` is the last state (switched) |
| `…test_a_held_save_has_kept_its_state_when_it_returns` | 2 — both runs | none | held configuration: save on another thread, `release`, join; the thread is done and `kept` is the state (held) |
| `…test_a_configured_saver_keeps_the_whole_state_in_turn` | 2 — both runs, parametrized over `watch`, `passes_to`, `only_save` | a second `FakeSaver` (`passes_to`, fake run) | the assertions of the two cases above it, in that configuration |
| fake-only checks, module-level functions beside the suite | 1 | `FakeSaver`s only | `saved` keeps every state in order. `calls` counts every call, raised ones included. The set `error` is the error raised, and clearing it ends the raising. `watch`'s answer at each save lands in `seen`. The held call keeps its state and sets `entered`, and does not return until `release` is set, while other calls are not held. `passes_to` receives each save, and when it raises the fake keeps nothing and the error comes through. With `only_save`, any other attribute is recorded in `asked_for` and raises `AssertionError`. Without it, a missing attribute raises `AttributeError` |

**I-5, the recorded mutation.** Change `FakeSaver.save` so that it keeps nothing: remove the step that
appends to `saved`, and nothing else. Run `uv run --locked pytest tests/integration/test_saver_contract.py`
from the product root. The fake run must fail, at least in "a save keeps the whole state it was
handed", and the `SavedData` run must pass. Then restore the fake. The command, both runs' counts and
the restore go into the change's Developer Review Notes. No state-dropping class is written anywhere,
so I-3, I-7 and I-8 still hold.

**What the change stops proving, and what proves it now:**

- **`assert release.wait(timeout=10)` inside the five `HeldSaver`s.** The fake's held call keeps it,
  and the fake-only check re-proves it.
- **`all(len(arguments) == 1 …)` and `isinstance(arguments[0], TrackerState)` in the three
  `RecordingEverything` tests.** These are re-proved by `saved` holding only `TrackerState`s, which
  each test asserts, and by `save` taking exactly one parameter. A call with any other number of
  arguments raises and keeps nothing, so the test's count of `saved` fails.
- **The `AttributeError` that `SaveOnlySaver` and `CallRecordingSaver` raised.** It becomes
  `AssertionError`, which is stricter: a `getattr` with a default can no longer swallow it. Each
  test's `asked_for == []` assertion stands.

**The gates after the change:** I-7's grep lists `tests/fakes.py` alone. No class outside it bases
on a class it defines (I-8). I-10's grep prints 25 lines in 24 files. `ruff format --check .` and
`ruff check .` exit 0 (I-11). Both halves of the card's `Test command:` pass (I-1).

---

## Records this change makes false

None. Read: `docs/adr/` (0001 to 0016), `docs/nfdr.md` (QC-3, QC-28, QC-29, QC-53, QC-54, QC-62,
QC-64, § 9, § 10, RN-65), `docs/fdr.md`, and `docs/SDD.md` § 3 and § 4 TS-6. QC-64's "starts unmet"
line is dated and stays true while the `Clock` half is unmet. Nothing in these records goes false.

---

## Architect Review Notes

- **(d) The Layout Plan is a replacement map:** the template's shape, symbols moved behind
  `__init__.py` re-exports, has nothing to place. No symbol moves and no import surface changes. § 3
  instead maps each stand-in to the fake configuration that replaces it, and states the fake's surface
  and the suite's hooks, which the spec left to this design.
- **(e) Test code has no owning part:** SDD § 3's `Owns` column covers the five product parts, and
  `tests/` is none of them. `tests/fakes.py` follows QC-64's example name. The suite sits in
  `tests/integration/`, with layer 2's tests, beside `test_saved_data.py` (NFDR § 9, level 2).
- **(b) How a configured behaviour runs handed `SavedData`:** a configuration that changes what a save
  does, failing, is reached in the real run by real means (§ 4). A configuration that does not change
  it is `watch`, held, `passes_to` or `only_save`. The real run hands that case plain `SavedData`,
  because a real saver has no such controls and the contract they must keep is the same. Every case
  runs in both runs (I-4). Rejected: running the real side through the fake with `passes_to` set to
  `SavedData`. That would make the `SavedData` run depend on the fake, and I-5's mutation would fail
  that run too. The effect of each control has no real counterpart, so the fake-only checks prove it
  (§ 5), outside the two-run suite.
- **(b) Failing after the first save is the switch, thrown after that save:** the one
  `FailingAfterFirstSaver` test assigns `error` after its first post. A separate counter option would
  add surface, and the suite could reach it in the real run only through a wrapper.
- **(b) One refusal for three shapes:** `only_save` raises `AssertionError` and records the name.
  That covers `OnlySaves`, `RecordingEverything`, `SaveOnlySaver` and `CallRecordingSaver`. For the
  last two it is stricter, never looser (I-6).
- **Packet check, no conflict:** the suite's real run writes only under `tmp_path`. It breaks a save
  with a directory rather than `chmod`, so it does not depend on who runs it (`testing_doctrine.md`
  § A test reads nothing of the machine it runs on). The fake-only checks touch no real resource.
  Nothing is patched (QC-28). `passes_to` defaults to no saver at all, never to a real one, so the
  hidden real collaborator that `conventions.md` § Constructs forbids cannot arrive. No production
  module is edited.
- **QC-12 review, pass:** the change adds two test modules and removes 46 classes. TS-6 and QC-64 pay
  for both.
- **QC-60 review, pass:** only Python 3.11 standard library (`threading.Event`) and pytest 9.1.1
  features.
- **QC-41 review, pass:** no secret is read, held or written.
- **QC-25, QC-26, QC-27 and the other `development-design` reviews tied to a part:** not triggered.
  No part's code, the saving contract or a dependency changes.
- **QC-40 review, every-review moment, packages: met.** All 27 pinned packages in `uv.lock` and
  `.behave/uv.lock` were checked against OSV's PyPI advisories on 2026-11-13, and none has one. No
  dependency is added or moved.
- **QC-40 review, every-review moment, browser build: not blocking, owed by 2026-12-11.** The pinned
  build is Chromium 158.0.8127.18. The vendor's feed, read 2026-11-13, holds the Stable Channel Update
  for Desktop of 2026-11-11 (157.0.8103.78), which fixes the Critical CVE-2026-126885,
  CVE-2026-126895, CVE-2026-126879, CVE-2026-126846 and CVE-2026-126911. Nothing newer carries a
  Critical. The vendor does not say whether 158.0.8127.18 carries those fixes, so this review reads
  it as affected. The advisories are 2 days old, inside the 30-day window. The fix is owed within 30
  days of 2026-11-11.
- **QC-40 review, package feed: down, moment still owed.** The checking account has admin on the
  repository that holds tracker17. The Dependabot alerts endpoint answered "Dependabot alerts are
  disabled for this repository." (403), and the SBOM export answered 404. By QC-40's words that is a
  feed that is down, and no discrepancy is raised.
- **Found while walking, left as the spec placed it:** QC-64's pointer "`testing_python.md` § 2"
  names a section that file does not number. The spec's Out of Scope already records it, and this
  seat edits no product record.
