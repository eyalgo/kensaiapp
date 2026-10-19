# Change Spec — `caplog.get_records()` stops following the phase's records after `caplog.clear()`

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Request:** "Fix the issue below in the product, the repository that the project card's
`Product path:` names (`pytest-dev/pytest`). The repository stands at the commit before the issue was
fixed. Make the change the issue asks for, with tests of your own that show it, and leave the rest of
the product's behaviour as it is." The issue is `pytest-dev__pytest-10051`, quoted in full in this
folder's `change_request.md` § *The issue*. Its constraints are in that file's § *What must not be done*.

---

## Change Summary

After a test calls `caplog.clear()`, `caplog.get_records(when)` for the current phase stops
matching `caplog.records`. It keeps returning the records captured before the clear, and it never
picks up the ones logged afterwards. After this change, `get_records` for the phase in which
`clear()` was called returns what `caplog.records` holds. Everything else `caplog` reports stays as
it is.

The cause is a present defect. The list the phase's `get_records` returns is the list the phase
began with (`src/_pytest/logging.py` line 699), and `clear()` swaps in a new list rather than
emptying that one (`src/_pytest/logging.py` line 345). Both lines are at `base_commit`.

**Terms used below.** A **phase** is one of a test's three stages: `"setup"`, `"call"` or
`"teardown"`. These are the values `get_records(when)` accepts. "During a phase" covers the test
function body for `"call"`, and the fixture code that runs before its `yield` for `"setup"` and
after it for `"teardown"`. Two record lists are **equal** when they hold the same `LogRecord`
objects in the same order, the way Python's `==` compares them.

---

## Rules

### caplog — what `get_records` returns once `clear()` has been called

- **CP-9:** During any phase, `caplog.get_records(<that phase>)` equals `caplog.records` at every
  point: before any `caplog.clear()`, straight after one, and after more records are logged. This
  holds for any number of `clear()` calls in the phase. The issue's reproducer passes as written.
- **CP-10:** Once `caplog.clear()` has been called in a phase, `caplog.get_records(<that phase>)`
  returns only the records captured in that phase after the last `clear()` in it, in the order
  they were logged. This holds whether it is read during that phase or in a later phase of the same
  test, and it never returns a record captured before that `clear()`. For example, a fixture logs
  `s1` during setup, calls `caplog.clear()`, then logs `s2`. Read during call or during teardown,
  `get_records("setup")` holds only `s2`.
- **CP-11:** `caplog.clear()` changes only the records of the phase it is called in. A clear in
  a later phase does not change `get_records` for an earlier one: a clear during call leaves
  `get_records("setup")` exactly as it was. `get_records` for a phase that has not started yet
  returns `[]`, as it does today.

### caplog — what stays as it is

- **CP-12:** Nothing else that `caplog` and the test report show changes:
  - Straight after `caplog.clear()`, `caplog.records`, `caplog.record_tuples`, `caplog.messages`
    and `caplog.text` are empty. Each of them then shows the records logged after the clear.
  - A failing test's report section for the phase (`Captured log setup`, `Captured log call`,
    `Captured log teardown`) still shows every record of that phase, including the ones logged
    before the `clear()`.
  - In a test that never calls `clear()`, `caplog.records` and `caplog.get_records(when)` return
    what they return today for every phase.

### Proof

- **CP-13:** The change comes with tests of its own, and the card's `Test command:` runs them.
  Today that command runs only `testing/logging/test_fixture.py` (Verified Claims). The tests
  fail on the unchanged tree and pass with the change. Between them they cover at least:
  - the issue's reproducer (CP-9, during call);
  - a record logged after a `clear()` appearing in `get_records` for that phase (CP-9, CP-10);
  - a `clear()` during setup, with `get_records("setup")` read in a later phase (CP-10);
  - a `clear()` in one phase leaving `get_records` for an earlier phase unchanged (CP-11).
- **CP-14:** With the change in place, the card's `Test command:` exits 0 and no test it runs
  fails. The 15 tests it runs today still pass, alongside the change's own.

---

## Examples

"Today" is what `base_commit` does. It was run on 2026-10-11 (see Verified Claims). `s1`, `s2`,
`c1` and `c2` are the messages of records logged at INFO with `caplog.set_level(logging.INFO)`.

| Rule | Scenario | Today | Expected behavior |
|---|---|---|---|
| CP-9 | The issue's reproducer: `logging.warning("test")`, then `caplog.clear()`, then `assert caplog.get_records("call") == caplog.records` | fails: `[<LogRecord … "test">] == []` | passes |
| CP-9 | During call: log `c1`, `caplog.clear()`. Read `get_records("call")` | `[c1]` | `[]` (equal to `caplog.records`) |
| CP-9, CP-10 | During call: log `c1`, `caplog.clear()`, log `c2`. Read `get_records("call")` during call | `[c1]` | `[c2]` (equal to `caplog.records`) |
| CP-9 | During call: log `c1`, clear, log `c2`, clear, log `c3`. Read `get_records("call")` after each step | `[c1]` after every step from the first clear on | `[]`, `[c2]`, `[]`, `[c3]` (equal to `caplog.records` each time) |
| CP-10 | Same call as above. Read `get_records("call")` during teardown | `[c1]` | `[c2]` |
| CP-10 | A setup fixture logs `s1`, calls `caplog.clear()`, logs `s2`. Read `get_records("setup")` during call | `[s1]` | `[s2]` |
| CP-10 | Same fixture. Read `get_records("setup")` during teardown | `[s1]` | `[s2]` |
| CP-11 | Setup logs `s1` with no clear. During call, `caplog.clear()`. Read `get_records("setup")` after it | `[s1]` | `[s1]` |
| CP-11 | During call, after a `clear()`, read `get_records("teardown")` | `[]` | `[]` |
| CP-12 | During call: log `c1`, `caplog.clear()`. Read `caplog.records` and `caplog.text` | `[]` and `''` | `[]` and `''` |
| CP-12 | Same, then log `c2`. Read `caplog.records`, `caplog.messages`, `caplog.record_tuples` and `caplog.text` | `[c2]`, `["c2"]`, `[("p", 20, "c2")]`, and text holding only `c2` | unchanged |
| CP-12 | A failing test logs `before-clear`, calls `caplog.clear()`, logs `after-clear` | `Captured log call` shows both lines | `Captured log call` shows both lines |
| CP-12 | `test_caplog_captures_for_all_stages` (no `clear()` anywhere) | passes | passes, unedited |
| CP-13 | The change's own tests, run on the unchanged tree | — | they fail |
| CP-13 | The change's own tests, run with the change | — | they pass |
| CP-14 | The card's `Test command:` run with the change | exit 0, `15 passed` | exit 0, no failure, the 15 present tests among those passing |

---

## Verified Claims

Every claim was run on 2026-10-11 against the product's change worktree for this key. That worktree
was opened from the repository the card's `Product path:` names, at `base_commit` (`aa55975`), with
no change applied. The card's interpreter (`/home/kensai/issue-venv/bin/python`) imports `_pytest`
from that worktree's `src/`. The probe tests were scratch files in a folder outside the repository,
and `git status --short` in the worktree was empty after every run. Nothing outside the repository
was consulted: no upstream history, no pull request, no benchmark copy, and none of the issue's
links were followed.

| Claim | Verified by | What came back |
|---|---|---|
| The issue reproduces at `base_commit` | ran the issue's reproducer, verbatim, as a scratch test | failed on the third `verify_consistency()`: `assert [<LogRecord: ..., 11, "test">] == []` |
| Today's values in the Examples' *Today* column (CP-9, CP-10, CP-11, the `records`/`text` rows of CP-12) | ran a scratch test with a setup fixture that logs `s1`, clears and logs `s2`, a call body that logs `c1`, clears and logs `c2`, and a teardown that reads both phases. It printed each read | call reads `get_records("setup")` = `['s1']`. After the call's clear: `records` = `[]`, `get_records("call")` = `['c1']`. After `c2`: `records` = `['c2']`, `get_records("call")` = `['c1']`. `get_records("teardown")` during call = `[]`. Teardown reads `get_records("call")` = `['c1']` and `get_records("setup")` = `['s1']`. `caplog.text` after `c2` held only the `c2` line |
| Two clears in one phase, and `messages`/`record_tuples` after a clear (the CP-9 two-clear row, CP-12) | ran a scratch test during call: log `c1`, clear, log `c2`, clear, log `c3` (logger `p`), printing `get_records("call")` and `records` after each step. Ran it at base and under the probe below | base: `get_records("call")` = `['c1']` at every step from the first clear on. `records` = `[]`, `['c2']`, `[]`, `['c3']`. `messages` = `['c3']`, `record_tuples` = `[('p', 20, 'c3')]`. Probe: `get_records("call")` = `[]`, `['c2']`, `[]`, `['c3']`, equal to `records` each time |
| A failing test's `Captured log call` section shows records logged before a `clear()` (CP-12) | ran a scratch test that logs `before-clear`, clears, logs `after-clear`, then fails | the section listed both `before-clear` and `after-clear` |
| The card's `Test command:` passes today with 15 tests, and runs only `testing/logging/test_fixture.py` | read `/home/kensai/issue-test.sh` and the suite script it calls (`python -m pytest -rfE -p no:cacheprovider testing/logging/test_fixture.py`). Ran `/home/kensai/issue-test.sh` from the product worktree root | `15 passed in 0.27s`, exit 0. The baseline file `/home/kensai/issue-baseline.txt` is empty |
| The rules can all be met together, and meeting them does not break the present suite | scratch probe, not a design: a plugin outside the tree, loaded with `-p`, that makes `caplog.clear()` empty the phase's existing record list instead of replacing it. Re-ran the scratch tests above and `testing/logging/test_fixture.py` under it | the issue's reproducer passed. `get_records("call")` = `[]` after the clear and `['c2']` after `c2`, in call and in teardown. `get_records("setup")` = `['s2']` in call and in teardown. `Captured log call` still listed both lines. `test_fixture.py`: `15 passed` |
| `test_caplog_captures_for_all_stages` and `test_clear` are present tests covering the no-clear stages and `clear()` emptying `records`/`text` | read `testing/logging/test_fixture.py` lines 144–172 | confirmed. Neither calls `get_records` after a `clear()` |
| The cause lines cited in the Change Summary | read `src/_pytest/logging.py` lines 344–346 (`LogCaptureHandler.reset`) and 688–702 (`_runtest_for`), and `LogCaptureFixture.clear` at line 441 | line 699 sets the phase's `get_records` list to the handler's list at the phase's start. Line 345 replaces that handler's list with a new one, and `clear()` calls it |
| The user docs do not state how `get_records` relates to `clear()` | read `doc/en/how-to/logging.rst` lines 132–163 | they describe `clear()` resetting the captured records and `get_records(when)` reading other stages. Neither says what `get_records` returns after a `clear()` |

---

## Out of Scope

- **A list a test got before a `clear()`.** The rules bind what a call made after the `clear()`
  returns. Whether a list object obtained earlier (`old = caplog.records`, or
  `old = caplog.get_records("call")`) keeps its records or is emptied is not fixed here, and either
  outcome meets this spec. See Locked Answers, Gap 3.
- **Clearing a phase other than the current one.** No new API is added. `clear()` keeps its
  signature and acts on the current phase only (CP-11).
- **The report and live-log output.** The `Captured log …` report sections, `log_cli`, `log_file`
  and the report handler are unchanged (CP-12).
- **Documentation and changelog.** The request asks for neither. `doc/en/how-to/logging.rst` does not
  state the relation this change fixes (checked above). The docstrings of `clear()` ("Reset the list
  of log records and the captured log text") and `get_records()` ("The list of captured records at
  the given stage") stay true. Whether to add a changelog fragment is not required by this spec.
  Other surfaces were not looked at: the API reference pages outside `how-to/logging.rst`, and
  `CHANGELOG.rst`.
- **Other failing tests.** None fail before the change (`15 passed`). The request forbids fixing
  unrelated ones.
- **Anything outside the local clone.** The patch is not pushed (`project.md`, `Manages: none`), and
  nothing is published. Per the request, no record, grade or benchmark file is produced.

---

## Locked Answers (the divergence record — self-review 2026-10-11)

- **Gap 1 — a `clear()` acts on its own phase only (CP-11).** The issue speaks only of the phase in
  which `clear()` is called. The spec keeps earlier phases' `get_records` untouched. The user docs
  say `caplog.records` "contains records from the current stage only", and `clear()` resets that
  list. Reaching into another phase would lose records the test never asked to drop. This is the
  conservative, non-destructive pick, and it matches what a clear during call does to `"setup"`
  today (`[s1]` stays `[s1]`).
- **Gap 2 — a later phase sees a phase's records as they stood after its last clear (CP-10).** The
  issue's reproducer reads within one phase only. The spec extends CP-9 to reads made later. The
  docs' own example reads `get_records("setup")` and `("call")` during teardown to check a test's
  warnings. A test that cleared expected noise in setup should not see it again from teardown. The
  alternative, a later phase seeing the records from before the clear, would make the same call
  return different lists depending on when it is read.
- **Gap 3 — a list obtained before a `clear()` is left open (Out of Scope).** The request and the
  issue speak of what `get_records()` and `caplog.records` return. Neither speaks of a list a test
  held on to across a clear. Today such a list keeps its records. Pinning either outcome would pick
  the mechanism of the fix rather than an observable the issue asks for. The docs and docstrings
  present both as values read, and promise neither a snapshot nor a live view. No present test
  depends on it (`test_fixture.py` read in full). The probe shows that emptying in place meets every
  rule. A fix that keeps the old list's contents could meet them as well.
- **Gap 4 — the captured-log report section keeps the pre-clear records (CP-12).** The request says
  to leave the rest as it is. The report section is what a person reads when a test fails, and today
  it keeps records logged before a `clear()`. A `clear()` is how a test reshapes what it asserts on,
  not what the report shows. This is stated as a rule because a fix in this area could reach it.
- **Gap 5 — the change's tests are ones the card's `Test command:` runs (CP-13, CP-14).** The
  request asks for "tests of your own" and does not say where they run. The card's command runs only
  `testing/logging/test_fixture.py`. A test outside it shows nothing at the change's gate. This is
  stated as a property of the result. Where the tests go is development-design's decision.
