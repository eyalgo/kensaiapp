# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-29_the-start-is-stoppable-from-its-ready-line` — workflow mode, reviewed 2026-10-29 by the Senior Engineer.

## The deferrals

None. The closing marker (`<a commit not in the public history>`, the newest `implementation complete` commit on the branch) carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

The branch's code against its merge base `53ad18603`, under `products/tracker17/`:

- `main.py` — `StopRequests`, `Serving`, `SigintStopRequests`, `serve_until_stopped`, and `start` now handing its successful lifetime to `serve_until_stopped`.
- `web/listener.py` — `Listener.serve_until` and `IDLE_WAIT_SECONDS`.
- `tests/unit/test_start_lifecycle.py` (new), `tests/integration/test_start_stop.py` (new), `tests/integration/test_listener.py` (seven tests added).

## The intent it was checked against

- `tl_instruction.md` — Tasks 1 to 3, their *Behaviours to verify* and *Held by review* lists.
- `change_spec.md` — CP-644 to CP-656, the Examples and Out of Scope.
- `change_design.md` — sub-jobs A and B, test rows T1 to T10, the deterministic regression seam.
- `docs/fdr.md` — not needed beyond what the spec cites.

## The tests added or fixed

- **Added** `tests/unit/test_start_lifecycle.py::test_lifecycle_closes_once_and_propagates_unrelated_arming_failure`. Source: `change_design.md` sub-job B, "An unrelated failure still cleans up the listener and propagates", and the coordinator's own contract, "The listener is closed once". A stop collaborator whose `arm` raises must leave the listener closed once, unannounced, with the failure unchanged. The recording collaborator gained an `arming_failure` field for it, handed in as an argument like the other fakes.
- **Fixed:** none. Every existing and developer-written test asserts what the intent says.

## The finding

**One bug, fixed.** `serve_until_stopped` called `stops.arm()` before its `try`, so a failure while arming skipped the `finally` that closes the listener. The real adapter fails exactly this way when `start` runs off the main thread: `signal.signal` raises `ValueError`, and the bound socket stays open. The fix moves `stops.arm()` to the first line inside the `try`. Arming still comes before the announcement, so the protected span is unchanged. A SIGINT that lands before arming is before the ready line, which Out of Scope leaves as it is.

- Red commit `09552f157`: the new test fails, `['arm'] == ['arm', 'close']`; card suite 1 failed, 2697 passed.
- Green commit: `main.py` fix and this report; card suite 2698 passed.

**Checked and found sound:**

- **CP-649's proof is real.** In a disposable clone at `53ad1860336a69827e6cfe55ff0649f20addefa8` with only `test_start_stop.py` copied in, `test_real_start_stops_at_the_completed_ready_write` passed its observer check (ready write completed, signal injected once) and then failed with `assert -2 == 0`, standard error ending `KeyboardInterrupt`. It passes on the branch. The clone was removed.
- **The latch body** sets a boolean and does nothing else: no raise, print, lock, I/O, `shutdown` or `server_close` (Task 2 *Held by review*).
- **No early restoration.** No `finally` or context manager between `serve_until_stopped` returning and `start` returning restores a raising handler. `test_real_start_keeps_the_non_raising_handler_through_its_return` sees a callable disposition after return.
- **`serve_until`** uses the public `handle_request` with a scoped timeout, keeps threaded dispatch, never calls `shutdown`, and restores the timeout on both exits. A non-raising handler during the wait lets the `select` resume (PEP 475), so a stop is seen within one idle wait.
- **Discrimination.** The listener's idle test fails on a wait with no timeout, and its dispatch test fails on a sequential server. The timeout tests fail on a missing restore. The return-boundary test fails on a raising handler.
- **CP-646 and CP-647.** The ready-line words and both refusals are unchanged in `main.py`, and the tests pin them.
- **CP-648.** Change-only, held by Task 3 review. The diff of `test_start.py`, `test_sigint_launch.py`, `tests/e2e/` and `tests/conftest.py` against the merge base is empty, as the branch's file list shows.
- **CP-653.** From the product root, in the README's `.venv`: `ruff format --check .` (277 files already formatted), `ruff check .` (All checks passed!), `mypy main.py errors.py domain application persistence web` (no issues in 27 source files) and `python3 -m compileall -q main.py errors.py domain application persistence web tests` each exited 0 after the fix.
- **CP-652, partly re-run.** `python -m pytest products/tracker17/tests/e2e/ -q`, run once in the foreground after the fix, gave 121 passed. The two ignored-SIGINT runs were not repeated here. The developer's marker records all four exiting 0 before this one-line move.
- **CP-654.** The fix adds no construct. Everything the change added runs on Python 3.11: `Protocol`, `FrameType | None` under postponed annotations, and `signal.getsignal`.

**Test evidence:**

- An earlier run of the test command exited 1 and printed `Environment: owners-mac — no CI`.
- The run this verdict rests on exited 0: `2698 passed in 276.49s`.

## Calls made

- **Is a failure while arming an "unrelated failure" that must close the listener?** The weighed readings: (a) yes — sub-job B says "An unrelated failure still cleans up the listener and propagates", and arming is part of the coordinator's successful lifetime; (b) no — the TL's list names announcement and serving failures only, and the design says the adapter is for "the normal main-thread start". Taken: (a). The design's sentence is general, the coordinator owns the listener from the moment it is handed over, and the fix is one line moved and easy to reverse. It changes no upstream document's meaning and adds no support for starting off the main thread: `start` still raises there, now with the port released. **Owner:** the Architect (`change_design.md` sub-job B). If ruled (b), the fix and the test go, and an arming failure leaves the listener for the garbage collector.

## Placement

Walked against `docs/SDD.md` § 3, *The parts*:

- `Listener.serve_until`, `IDLE_WAIT_SECONDS` → `web`, which owns "listening on the loopback address". Already there.
- `SigintStopRequests`, `StopRequests`, `Serving`, `serve_until_stopped` → `main`, the composition root and start command. Already there.
- `announce` closure in `start` → `main`, which "writes the start messages to the console". Already there.

Nothing misplaced, no move, no placement commit.

## The language resolution

Python — chain step 1, `project.md` `Languages: Python`. Packet `<CORE>/doctrine/engineering/languages/python/README.md` opened; Conventions (`conventions.md`), Quality gates (`quality_gates.md`) and Testing (`<CORE>/doctrine/engineering/testing_python.md`) read as the review bar. The added test follows `testing_python.md`'s seam rule: a hand-written recorder handed in by argument, with no `monkeypatch.setattr` and no patch. The fix keeps `conventions.md`'s 100-column limit and the product's ruff configuration, and the format and lint gates pass.
