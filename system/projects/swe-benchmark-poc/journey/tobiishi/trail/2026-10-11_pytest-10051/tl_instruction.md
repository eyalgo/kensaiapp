# Tech Lead instruction — pytest-10051: `caplog.get_records()` follows the phase's records after `caplog.clear()`

**Category:** bug
**Behaviour:** changing
**Product root:** <the issue's clone>/.worktrees/2026-10-11_pytest-10051 — every path below is relative to it.
**Scope:** `caplog.clear()` empties the capture handler's current record list in place, so `get_records(<phase>)` and `caplog.records` stay one list for the whole phase. One production file, one test file. Nothing is published, stored on a device or sent anywhere; the patch stays in the local clone.

---

## Project layout

```
<product-root>/
  src/_pytest/logging.py          ← modified (LogCaptureHandler gains clear(); LogCaptureFixture.clear calls it)
  testing/logging/test_fixture.py ← modified (new tests only; existing tests unedited)
```

No parts table — placement follows change_design.md §2. The product has no `docs/` (`Definition: none`), so there is no `nfdr.md` module set or `adr/` to check against. The card's `Test command:` (`/home/kensai/issue-test.sh`) runs only `testing/logging/test_fixture.py`, so every new test goes in that file.

**What a task may bring in:** no new third-party origin, no device storage, no new dependency. Only the standard library already imported in each file.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Task split by lane:** design §5 rows 1–4 and row 6 sit in one test file under one change. Rows 1–4 fail on the unchanged tree. Row 6 (report section keeps pre-clear records) passes before and after, because `report_handler` is a separate instance this change does not touch. In one test-first task, row 6 would have no red to watch. It gets its own task in the already-green shape (Task 2), with a `Reason:` line. No behaviour was dropped.
- **Behaviour added:** Task 1 also asserts that `caplog.record_tuples` is empty straight after each clear. Design row 2 lists it. It is written out in the Task 1 behaviours so it is not lost.
- **Behaviour added (edge):** a `clear()` straight after phase start, before anything was logged in it, leaves `get_records(<phase>) == caplog.records == []` and a record logged afterwards appears in both. This is implied by CP-9 ("at every point") and row 2's first clear. It is stated as its own behaviour so the empty-list case is pinned.
- **Hint carried:** design §4's hint is carried into Task 1 as written in substance. It was not vague and was not code, so no rewrite.
- **No Corrections owed section:** `change_design.md` § *Records this change makes false* is `None`, and the walk found nothing else.
- **Gap 3 stays untested, deliberately:** the design locks, by mechanism, that a list obtained before a `clear()` is emptied along with it. The spec leaves that open, so no test asserts it either way. Task 1 carries it under *Held by review* so the developer does not add such a test.

### Task 1: `LogCaptureHandler.clear()` and `LogCaptureFixture.clear` (`src/_pytest/logging.py`, `testing/logging/test_fixture.py`)

**Dependencies:** None

**What to build:** `LogCaptureHandler` gains a `clear()` operation that empties its current record list in place (the same list object, now empty) and gives the handler a fresh text stream. `LogCaptureFixture.clear()` calls it instead of `reset()`, with signature and docstring unchanged. `reset()` is **unchanged**, and `LoggingPlugin._runtest_for` / `pytest_runtest_*` are untouched.

#### Behaviours to verify (developer adds tests to `testing/logging/test_fixture.py`; use the `caplog` fixture and `caplog.set_level(logging.INFO)`)

- `test_get_records_equals_records_after_clear` — the issue's reproducer: assert `caplog.get_records("call") == caplog.records` at the start, after `logging.warning("test")`, and after `caplog.clear()`.
- `test_clear_in_empty_phase_then_log` — `caplog.clear()` before anything was logged in the phase leaves `get_records("call") == caplog.records == []`. A record logged after it shows in both.
- `test_get_records_tracks_records_across_several_clears` — during call: log `c1`, clear, log `c2`, clear, log `c3`. After each step `get_records("call") == caplog.records`, with contents `[]`, `[c2]`, `[]`, `[c3]` after the first clear, `c2`, the second clear and `c3` respectively.
- `test_clear_empties_records_tuples_messages_text` — straight after each clear in the test above, `records`, `record_tuples`, `messages` and `text` are all empty. After `c2`, `messages == ["c2"]`, `record_tuples` holds the one `c2` tuple, and `text` holds `c2` and not `c1`.
- `test_clear_leaves_not_started_phase_empty` — during call, after a clear, `get_records("teardown") == []`.
- `test_setup_clear_is_seen_from_later_phases` — a fixture logs `s1`, calls `caplog.clear()`, logs `s2` and yields. In the test body, `get_records("setup")` holds only `s2`. Asserted again in the fixture's teardown.
- `test_call_clear_leaves_setup_records_and_is_seen_in_teardown` — a fixture logs `s1` with no clear. The test body logs `c1`, clears, logs `c2`, and asserts `get_records("setup")` is still `[s1]`. In the fixture's teardown, `get_records("call")` holds only `c2` and `get_records("setup")` is still `[s1]`.

Assert on message contents (for example `[r.getMessage() for r in ...]`) alongside the equality checks, so a test cannot pass by comparing two equally wrong lists. All of these fail on the unchanged tree (CP-13). Run them red first.

#### Held by review

- Gap 3 (a list obtained before a `clear()`, such as `old = caplog.records`) — covered by no test, deliberately. The spec leaves open whether the old list keeps its records or is emptied. The in-place mechanism empties it. Write no test that asserts either outcome. The diff is read to confirm none was added.

#### Implement

Infer from failing tests.

# Hint: Empty the existing list object in the list's own in-place way. Never rebind `self.records`, because identity between `handler.records` and the list stored for the phase is the whole fix. Do **not** make `reset()` empty in place instead. `_runtest_for` calls `reset()` at every phase start, so an in-place `reset()` would empty the previous phase's stored list and break `get_records("setup")` during call. Giving the handler a fresh text stream, as `reset()` does, is fine, because nothing outside the handler holds the stream.

#### Verification gate

Run `/home/kensai/issue-test.sh` from the product root.

Pass criteria: exit 0; the new tests pass; the 15 tests present before the change still pass; no new failures.

### Task 2: Report section keeps records logged before `clear()` (`testing/logging/test_fixture.py`)

**Dependencies:** None

**What to build:** one `pytester` guard test for CP-12's report-section rule. No production change.

#### Behaviours to verify (developer adds the test to `testing/logging/test_fixture.py`)

- `test_report_section_keeps_records_logged_before_clear` — an inner test logs `before-clear`, calls `caplog.clear()`, logs `after-clear`, then fails. The outer run's output under `Captured log call` shows both lines. Follow the shape of `test_log_report_captures_according_to_config_option_upon_failure`.

#### Implement

Tests cannot go red.

Reason: the `Captured log …` sections come from `report_handler`, a separate handler instance that `clear()` never touches, so the behaviour holds on the unchanged tree and after Task 1. The spec's own verified claims show the section listing both lines at base.

#### Verification gate

Run `/home/kensai/issue-test.sh` from the product root.

Pass criteria: exit 0; the new test passes; no new failures elsewhere.
