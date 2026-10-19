# Change Design — `caplog.get_records()` stops following the phase's records after `caplog.clear()`

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Publishes text:** no

---

## 1. Change Summary

`caplog.clear()` stops replacing the capture handler's record list and empties it in place instead.
During a phase, the list stored for that phase (the one `get_records(<phase>)` returns) and
`caplog.records` are one list object. The handler binds that object when the phase starts
(`src/_pytest/logging.py`, `_runtest_for`, line 699). Today `clear()` goes through
`LogCaptureHandler.reset()`, which binds a new list (line 345). That splits the two names, so
`get_records` freezes on the pre-clear records. After the change, `clear()` keeps that object and
empties it. The two names stay one object for the whole phase, which gives CP-9 by construction.
The object stays stored under its phase once the next phase starts, which gives CP-10.

The phase-start reset is left exactly as it is: it still binds a **new** list at the start of each
phase. That is what keeps an earlier phase's stored list away from a later phase's clear (CP-11), and
what keeps `get_records` the same for tests that never call `clear()` (CP-12). The report section
comes from a separate handler instance (`report_handler`), which this change does not touch, so
`Captured log <phase>` keeps every record of the phase (CP-12).

One product module changes (`src/_pytest/logging.py`), plus one test file
(`testing/logging/test_fixture.py`). **Outward boundary:** the change stores nothing on a visitor's
device, collects nothing, and sends nothing to a third party. Nothing in it is published. The patch
stays in the local clone (`project.md`, `Manages: none`), and no other surface of the presence says
anything this change touches. The blast radius stops at this project's edge.

---

## 2. Blast Radius

The product has no `docs/` folder (`Definition: none`), so it has no `SDD.md` § 3 parts table, no
`nfdr.md` § 1.2 module set and no `adr/`. Placement and the module set come from the code itself,
read under the product worktree. With no parts table, the placement below goes by which class owns
the state the logic changes (logged as kind (e) in Architect Review Notes).

| Module | Status | What changes |
|---|---|---|
| `src/_pytest/logging.py` — `LogCaptureHandler` | Modified | New operation, `clear()`. It empties the handler's current record list **in place** (same object, now empty) and gives the handler a fresh text stream. `reset()` is **unchanged**: it still binds a new list and a new stream, and only the phase start calls it. The handler owns its record list and its stream, so the logic belongs here rather than in the fixture. |
| `src/_pytest/logging.py` — `LogCaptureFixture.clear` | Modified | Calls the handler's new `clear()` instead of `reset()`. Signature and docstring unchanged. |
| `src/_pytest/logging.py` — `LoggingPlugin._runtest_for` / `pytest_runtest_*` | Unchanged | They keep calling `caplog_handler.reset()` at each phase start and storing `caplog_handler.records` under the phase. That rebinding is what CP-10 and CP-11 rely on. |
| `src/_pytest/logging.py` — `report_handler`, `_LiveLoggingStreamHandler`, `_FileHandler` | Unchanged | Separate handler instances. `report_handler` feeds the `Captured log …` sections. `_LiveLoggingStreamHandler.reset()` (lines 681, 776) is a different class's method. |
| `src/pytest/__init__.py` | Unchanged | Exports `LogCaptureFixture` only. `LogCaptureHandler` is not exported, though `caplog.handler` reaches it. The new method is additive. |
| `testing/logging/test_fixture.py` | Modified | The change's own tests (§ 5). Existing tests unedited. |

Transitive blast radius: no public signature changes. `LogCaptureFixture.clear()` keeps its signature
and `get_records()` / `records` keep theirs. The only addition is the new handler method. No caller of
`reset()` outside the fixture is affected, because `reset()` does not change.

---

## 3. Sub-jobs

Omitted. One module changes, and its two edits (the handler's new operation and the fixture's call
to it) sit side by side in one file with no state between them that a separate landing could use.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `src/_pytest/logging.py` — handler `clear()` + fixture `clear()` | Mutate the existing list object (the list's own in-place emptying), never rebind `self.records`: identity between `handler.records` and the phase's stored list is the whole fix. Do **not** make `reset()` empty in place instead. The phase start calls `reset()` too, so an in-place `reset()` would empty the previous phase's stored list at every phase boundary: `get_records("setup")` would read `[]` during call, which breaks CP-11 and `test_caplog_captures_for_all_stages`. Replacing the stream with a fresh one, as `reset()` does, is fine, because nothing outside the handler holds the stream. |

---

## 5. Test Additions

All in `testing/logging/test_fixture.py`, the only file the card's `Test command:` runs (CP-13, Gap
5). `s1`/`s2`/`c1`/`c2`/`c3` are records logged at INFO under `caplog.set_level(logging.INFO)`.
Rows 1–4 fail on the unchanged tree and pass with the change (CP-13). Row 5 is a covered-by note. Rows 6–7 guard CP-12 and pass
both before and after.

| # | Test file | What to add / modify |
|---|---|---|
| 1 | `testing/logging/test_fixture.py` | New test: the issue's reproducer, verbatim in substance. Check `get_records("call") == caplog.records`, then `logging.warning("test")` and check again, then `caplog.clear()` and check again. (CP-9, Example row 1.) |
| 2 | `testing/logging/test_fixture.py` | New test, during call: log `c1`, clear, log `c2`, clear, log `c3`. After each step, assert `get_records("call") == caplog.records` and the expected contents: `[]`, `[c2]`, `[]`, `[c3]`. After `c2`, also assert `caplog.messages == ["c2"]`, the `record_tuples` entry, and that `caplog.text` holds `c2` and not `c1`. Straight after each clear, assert `records`, `record_tuples`, `messages` and `text` are empty. Read `get_records("teardown")` after a clear and assert `[]`. (CP-9, CP-10 in-phase, CP-11 not-started phase, CP-12 records/text rows; Example rows 2, 3, 4, 9, 10, 11.) |
| 3 | `testing/logging/test_fixture.py` | New fixture + test: setup logs `s1`, calls `caplog.clear()`, logs `s2`, and yields. In the test body, assert `get_records("setup")` holds only `s2`. In the fixture's teardown, assert it again. (CP-10 read in a later phase; Example rows 6, 7.) |
| 4 | `testing/logging/test_fixture.py` | New fixture + test: setup logs `s1` with no clear. The test body logs `c1`, calls `caplog.clear()`, logs `c2`, and asserts `get_records("setup")` is still `[s1]`. The fixture's teardown asserts `get_records("call")` holds only `c2` and `get_records("setup")` is still `[s1]`. (CP-10 call-read-in-teardown, CP-11 earlier phase untouched; Example rows 5, 8.) |
| 5 | `testing/logging/test_fixture.py` | Rows 1–4 together prove the "any number of clears" clause of CP-9 (row 2: two clears) and the "never returns a pre-clear record" clause of CP-10 (rows 2–4 assert exact contents). No separate test. |
| 6 | `testing/logging/test_fixture.py` | New `pytester` test: an inner test logs `before-clear`, calls `caplog.clear()`, logs `after-clear`, then fails. Assert the outer run's output under `Captured log call` shows both lines. Follow the shape of `test_log_report_captures_according_to_config_option_upon_failure`. (CP-12 report section, Gap 4; Example row 12.) |
| 7 | `testing/logging/test_fixture.py` | No addition. `test_caplog_captures_for_all_stages` and `test_clear` stay unedited and keep passing. They cover CP-12's "never calls `clear()`" clause and `clear()` emptying `records`/`text`. (Example row 13.) |

**Rule-implied edges:** a clear in a phase with no records before it is covered by row 1's first
check and row 2's second clear. A clear before the next phase starts is covered by rows 3 and 4. A
not-started phase reading `[]` is covered by row 2. CP-14 (the card's command exits 0 with the 15
present tests passing) is covered by row 7 together with the suite run itself.

**Retired assertions:** none. No existing assertion is edited or removed.

---

## Records this change makes false

None. The product has no `docs/` (no `adr/`, `nfdr.md`, `fdr.md` or `SDD.md`), so there is no record
to go false. Also read: the docstrings of `LogCaptureFixture.clear()` ("Reset the list of log records
and the captured log text") and `get_records()` ("The list of captured records at the given stage"),
and `doc/en/how-to/logging.rst` lines 132–163 as the spec cites them. Nothing in them goes false.

---

## Architect Review Notes

- **(b) CP-9/CP-10 realized by identity, not by syncing two lists:** the design keeps
  `handler.records` and the phase's stored list as **one object** for the whole phase, and `clear()`
  mutates it. The alternative was to rebind both names on every clear, which would mean `clear()`
  re-writing the stash entry for "the current phase". The fixture does not track which phase is
  current, so that would add phase state to the fixture just to keep two references in step. With
  identity, equality holds by construction at every point in the phase, for any number of clears,
  and the stored object carries its post-clear contents into later phases with no extra step.
- **(b) Gap 3 locked by the mechanism, and not pinned by a test:** emptying in place means a list a
  test obtained before a `clear()` (`old = caplog.records`, or `get_records(<current phase>)`) is
  emptied with it. The spec leaves this open (Out of Scope, Gap 3), and the probe shows the in-place
  outcome meets every rule. No test asserts it either way, so it does not become a contract the spec
  declined to make.
- **(b) `reset()` stays rebind-only, and a separate in-place operation is added:** an in-place
  `reset()` is the obvious one-line fix, but it is wrong. `_runtest_for` calls `reset()` at every
  phase start, so it would empty the previous phase's stored list (CP-11, CP-12 no-clear, and
  `test_caplog_captures_for_all_stages` all break). The design separates the two meanings: phase
  start gets a new list, and a user clear empties the current one. § 4 carries this as the hint so
  it reaches the developer.
- **(e) Placement without a parts table:** with no `SDD.md` § 3, the in-place emptying goes on
  `LogCaptureHandler`, the class that owns the record list and the stream. `LogCaptureFixture` keeps
  delegating to it, as it does today, rather than reaching into `handler.records` and
  `handler.stream`.
- **(d) Test row 6 passes on the unchanged tree:** CP-13 asks that the change's tests fail on the
  unchanged tree. The four coverage items it lists are rows 1–4, and they do. Row 6 is a regression
  guard for CP-12's report section, which Gap 4 states as a rule because a fix in this area could
  reach it. It passes before and after by design, and it is not one of CP-13's fail-on-base tests.
- **Delegated-gate sweep:** no `nfdr.md` or `adr/` exists, so no `verified by:` entry names a review
  at this stage. None performed.
- **No changelog fragment:** the spec leaves one not required (Out of Scope). The design adds none,
  which keeps `Publishes text: no`.
