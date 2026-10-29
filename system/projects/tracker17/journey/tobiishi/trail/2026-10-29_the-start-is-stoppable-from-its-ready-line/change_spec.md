# Change Spec — the start is stoppable from its ready line

**Date:** 2026-10-29
**Category:** bug
**Behaviour:** changing
**Request:** Make the tracker stop cleanly on Ctrl-C from the moment it prints its ready line until `start` returns. Today `start` in `products/tracker17/main.py` prints "The tracker is running. Open http://… in your browser." and only then enters the `try` whose `except KeyboardInterrupt` stops it quietly (`main.py:L59-L72`). A Ctrl-C that lands between the two ends the tracker with a traceback on standard error and a non-zero exit instead of exit 0 and nothing written. The start tests send SIGINT as soon as they read the ready line (`tests/integration/test_start.py:L528-L530`), so on a loaded machine they land in that gap: the run closing `tracker17 · shukuba · 2026-10-29_start-tests-under-ignored-sigint` on 2026-10-29 saw `test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint` fail once in a full foreground run that took 782 s (`2651 passed, 1 failed`), and pass alone and in a second full run (`2652 passed`). An operator who presses Ctrl-C right after starting hits the same gap. — with the request's *Measured*, *The span ends when `start` returns*, *What must not be weakened* and *Proof* paragraphs, in this folder's `change_request.md`.
**Language resolution:** Python — step 1 (`project.md` `Languages:`) — `<CORE>/doctrine/engineering/languages/python/README.md` opened, every concern it routes read

---

## Change Summary

A Ctrl-C that reaches the tracker after its ready line but outside the stretch where it is serving — before serving begins, or while it closes down — ends it with a traceback and a non-zero exit. From the moment the ready line is written until `start` returns, every Ctrl-C must be the quiet stop the operator already gets while the tracker is serving: exit 0 and nothing written.

---

## Rules

Numbering starts at CP-644. CP-631 to CP-643 were given out by this change's first walk, whose branch was removed after its plan halted; they are not reused.

### Stopping from the ready line

- **CP-644:** From the moment the ready line has been written to standard output until `start` returns, every SIGINT the tracker receives — Ctrl-C in the terminal it runs in, or the signal sent to its process — stops it quietly: `start` returns 0, the process the start command runs exits with status 0, and nothing is written to standard error — no traceback and no message. This holds at every point in that span, whatever the tracker is doing: before it has begun answering requests, while it waits for one, while it applies one, and while it closes down after serving ends; and it holds for a further SIGINT that arrives while the tracker is already stopping on an earlier one. Today it does not, at two places: the ready line is printed at `products/tracker17/main.py:61-65`, before the `try` at `:66` whose `except KeyboardInterrupt` at `:68-69` gives the quiet stop, and a SIGINT that lands between them ends the process killed by SIGINT with a traceback ending `KeyboardInterrupt`; and a SIGINT that lands while `finally:` at `:70-71` closes the listener ends it the same way (both reproduced, § Verified Claims).
- **CP-645:** The stop in CP-644 writes nothing to standard output after the ready line. When no action is being applied as the SIGINT arrives, the stop leaves the saved-data location exactly as it was: the same files, with the same bytes.

### What stays as it is

- **CP-646:** The ready line keeps its words and its moment: it is the first thing the console shows, it appears once the tracker is ready, and it reads `The tracker is running. Open http://{host}:{port} in your browser. Saved data is kept at {location}.` (FDR R-2; NFDR QC-55, verified at layer 5 by the end-to-end harness asserting the first console lines).
- **CP-647:** The two refusals `start` prints before it listens are unchanged — unreadable saved data, and the address held by something else — each one plain message on standard error, exit status 1, no ready line, nothing written to the saved data, and the unreadable-data message the one shown when both are true (FDR R-4, R-24; NFDR QC-51 and QC-58, verified by the layer 2 tests of each refused start asserting the message and the saved data's bytes).
- **CP-648:** The existing start tests keep starting the real start in a child process and stopping it with a real SIGINT. No test is deleted, skipped, retried or marked expected-to-fail, and no test's deadline is lengthened.

### Proof

- **CP-649:** The suite holds a test that fails on the code before this change on every run and passes after it. It shows that a SIGINT landing at any point of CP-644's span — before serving begins and while closing down included — stops the tracker with exit status 0 and nothing on standard error. Its verdict does not depend on how fast or how loaded the machine is: a test that is red only when a signal happens to land in the gap is not this proof.
- **CP-650:** The test CP-649 adds hands each part its collaborators and patches no name inside a part; the layer-6 walk that fails on `monkeypatch.setattr` or `unittest.mock.patch` aimed at a product module passes (SDD § 4 TS-2; NFDR QC-28).
- **CP-651:** Every test module this change adds or edits names, in its docstring, the requirements or acceptance criteria it checks, and every path and requirement identifier it names exists — the pointer test of SDD § 4 TS-4 passes (NFDR QC-11; SDD § 4 TS-3, TS-4).
- **CP-652:** `python -m pytest products/tracker17/tests/ -q` and `python -m pytest products/tracker17/tests/e2e/ -q` each exit 0, run in the product's test environment as the written setup instructions make it, both in the foreground and when launched with SIGINT ignored, leaving all three of SDD § 4 TS-1's layers passing.
- **CP-653:** The code passes NFDR QC-62's three gates, each exiting 0 from the product root: `ruff format --check .`, `ruff check .`, and `mypy main.py errors.py domain application persistence web`, at the versions `pyproject.toml` pins (NFDR QC-62). The compile gate NFDR § 9 *Outside the layers* applies, `python3 -m compileall -q` over the product, exits 0.
- **CP-654:** The code this change adds runs on Python 3.11, checked by review at `development-design` (NFDR QC-60).
- **CP-655:** The change adds no part that no requirement pays for, checked by review at `development-design` (NFDR QC-12).
- **CP-656:** Where this change alters `main.py`, `main.py` still holds no rule, no page and no file format, checked by review at `development-design`; the layer-6 half, QC-42 and QC-43 over `main.py`, passes in the suite (NFDR QC-24).

---

## Examples

| Scenario | Expected behavior |
|---|---|
| CP-644: the operator starts the tracker and presses Ctrl-C the instant the ready line appears, before the tracker has begun serving | The tracker stops; the shell sees exit status 0; nothing appears on standard error. |
| CP-644: Ctrl-C while the tracker sits idle, serving | Exit status 0, nothing on standard error — as today. |
| CP-644: Ctrl-C while a request is being answered | Exit status 0, nothing on standard error. What the saved data holds afterwards is FDR R-19's (see Out of Scope). |
| CP-644: Ctrl-C while the tracker is closing down after serving ends, before `start` returns | Exit status 0, nothing on standard error. |
| CP-644: Ctrl-C, then Ctrl-C again while the tracker is still stopping, before `start` returns | Exit status 0, nothing on standard error. |
| CP-645: Ctrl-C with no action under way, saved data present | Standard output holds the ready line and nothing after it; the saved-data location's files and bytes are as they were before the SIGINT. |
| CP-645: Ctrl-C with no action under way, no saved data yet | Standard output holds the ready line and nothing after it; the saved-data location is still empty. |
| CP-646: a normal start | The console's first line is `The tracker is running. Open http://127.0.0.1:8017 in your browser. Saved data is kept at /Users/sam/tracker17/data.` and nothing comes before it. |
| CP-647: saved data cannot be read | One line on standard error naming the location and the *Setting saved data aside* section, exit status 1, no ready line, saved data unchanged — as today. |
| CP-647: something else holds the address | One line on standard error naming the address, exit status 1, no ready line, saved data unchanged — as today. |
| CP-648: the start tests in `tests/integration/test_start.py` and the end-to-end harness | Still start the real start in a child process and stop it with a real SIGINT; same count of tests, none skipped or marked expected-to-fail, deadlines as they are. |
| CP-649: the new test, run against the code before this change, on an unloaded machine | Fails, on every run. |
| CP-649: the new test, run after the change | Passes, on every run. |
| CP-650: the new test's source | Hands its parts their collaborators; replaces no name inside `main` or any other part. |
| CP-651: the new or edited test module's docstring | Names the requirements it checks; the pointer test passes. |
| CP-652: both suites, run in the foreground and again launched with SIGINT ignored | Exit 0 all four times. |
| CP-653: the three QC-62 commands and the compile gate | Each exits 0. |
| CP-654, CP-655, CP-656 | No example row — each is a review at `development-design`, not an observable the product shows; CP-656's layer-6 half is a suite test already counted under CP-652. |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| The ready line is printed before the `try` whose `except KeyboardInterrupt` gives the quiet stop, and the listener is closed in a `finally` after it (CP-644) | Read `products/tracker17/main.py` at `53ad18603` | The ready line's `print` is `main.py:61-65`; `try:` `:66`, `listener.serve_forever()` `:67`, `except KeyboardInterrupt: pass` `:68-69`, `finally: listener.server_close()` `:70-71`, `return 0` `:72`. |
| A SIGINT after the ready line ends the process quietly while serving, and with a traceback and a non-zero exit before serving begins and while closing down (CP-644, CP-645) | In a disposable clone of the instance at `53ad18603`, with Python 3.15.0, from `products/tracker17`: started `main.start(('127.0.0.1', 0), <empty dir>)` in a child `python3`, read the first line of standard output, sent a real SIGINT, collected exit status, the rest of standard output, standard error and the location's listing. Three runs: the code as it is; `time.sleep(1)` added between the ready print and the `try`, to hold the first gap open; `time.sleep(2)` added in the `finally` before `server_close()`, with a second real SIGINT sent 0.5 s after the first. Real start, real socket, real signals | As it is: status 0, stdout after the ready line `b''`, stderr empty, location empty before and after. First gap held open: status -2 (killed by signal 2), stderr's last line `KeyboardInterrupt`, stdout after the ready line `b''`, location empty. Closing-down gap held open: status -2, stderr's last line `KeyboardInterrupt`, stdout after the ready line `b''`, location empty. The clone was removed. |
| The start tests send SIGINT as soon as they read the ready line, and the end-to-end harness stops its tracker with SIGINT (CP-648) | Read `tests/integration/test_start.py:455-458` and `:516-535`, and `tests/e2e/conftest.py:27-32` and `:54-62` at `53ad18603` | `RUN_START` runs `sys.exit(main.start(('127.0.0.1', 0), Path(sys.argv[1])))`; `_run_real_start` reads one line (`:527`), asserts it starts `The tracker is running. Open http://127.0.0.1:`, sends `signal.SIGINT` (`:529`) and waits 30 s; the e2e `START_PROGRAM` raises `SystemExit(main.start(...))`, and `stop()` sends SIGINT and returns the exit status and standard error. |
| No existing test has to change for CP-644 and CP-645 to hold (Step 6, *Rules against the existing tests*) | Searched `products/tracker17/tests/` for `KeyboardInterrupt`, `serve_forever`, `default_int_handler`, `main.start` and `SIGINT` at `53ad18603` | The tests that stop a real start (`test_start.py`'s `_run_real_start`, `test_sigint_launch.py`, the e2e `stop()`) assert or return exit 0 and empty standard error after SIGINT, which these rules keep; the in-process `main.start` calls in `test_start.py` are refused starts or a bind failure that raises; the `serve_forever` hits start a listener in a thread. None asserts the gap. |
| The operator is told to stop the tracker with Ctrl-C | Read `products/tracker17/README.md:52` | "The tracker keeps running in that terminal until you stop it. To stop it, press Ctrl-C in that terminal." |
| QC-62's three gates and the compile gate pass on the code before this change (CP-653) | In the same disposable clone, from `products/tracker17`, on the unmodified code: `uvx --offline ruff@0.16.10 format --check . --no-cache`; `uvx --offline ruff@0.16.10 check . --no-cache`; `uvx --offline mypy@2.4.0 main.py errors.py domain application persistence web`; `python3 -m compileall -q .` | Exit 0 each: `275 files already formatted`; `All checks passed!`; `Success: no issues found in 27 source files`; compile silent. |
| The written setup instructions make the test environment with `venv` and `pip`, no `uv.lock` is tracked, and the pin test reads `tests/requirements.txt` (Out of Scope, record gap) | Read `products/tracker17/README.md:95-102`; `git ls-files products/tracker17` filtered for `uv.lock`, `pyproject` and `requirements`; read `tests/architecture/test_pins.py:39-40`, at `53ad18603` | README: `python3 -m venv .venv` (`:97`), `python -m pip install -r tests/requirements.txt` (`:99`), `pytest tests/` and `pytest tests/e2e/` (`:101-102`). Tracked: `pyproject.toml` and `tests/requirements.txt`; no `uv.lock`. `test_the_lock_file_exists_and_every_line_is_exact` reads `PRODUCT_ROOT / "tests" / "requirements.txt"`. |
| Language rendering — no rule pins output that renders a language-level fact | Step 6 walk of CP-644 to CP-656 | The exit status, the empty standard error, the empty standard output after the ready line and the ready line's words are outputs the product chooses; no rendering row is owed. |

---

## Out of Scope

- A SIGINT that arrives before the ready line has been written — while the saved data is read, the address is taken or the ready line is being printed. What the tracker does then stays as it is.
- A SIGINT that arrives after `start` has returned. The request: "After that the tracker has stopped, and what a Ctrl-C does while Python itself shuts down is the interpreter's, not the product's". CP-644's exit status 0 is the one a stop inside the span gives; this change makes no claim about a further SIGINT that lands after `start` returns.
- A tracker whose process starts with SIGINT already ignored, as a background job started by a non-interactive shell does. This change does not alter how such a tracker responds to SIGINT.
- What the saved data holds after a stop that lands while an action is being saved. That is FDR R-19 and NFDR QC-49 to QC-51, unchanged; CP-644 binds only the exit status and standard error of that stop.
- Stopping the tracker by any signal other than SIGINT, or by closing its terminal.
- The ready line's words, the refusal messages and the README's instructions for stopping the tracker — none changes.
- SDD § 4 RT-4's test environment made by uv, and NFDR QC-39's `uv.lock` and § 10's suite commands typed through `uv run`. The product does otherwise today: the written setup instructions make the environment with `venv` and `pip` from `tests/requirements.txt` (`products/tracker17/README.md:97-99`), no `uv.lock` is tracked, and the pin test reads `tests/requirements.txt` (`tests/architecture/test_pins.py:40`). QC-39 itself says it "starts unmet" and that "The change that moves the product to SDD § 4 RT-4 moves the test with the file"; this change adds and moves no test dependency, so it is not that change, and it runs the suites in the environment the instructions make today, as the request asks. The move to uv is parked in `deferred_decisions.md` as a record gap.

---

## Locked Answers (the divergence record — self-review 2026-10-29)

- **Gap 1 — the span includes closing down and a second Ctrl-C (b):** CP-644 names every point from the ready line until `start` returns — closing the listener after serving ends included, and a further SIGINT while already stopping — not only the gap before the `try` the request diagnosed. CP-649's proof covers the closing-down point as well. — The request asks for a quiet stop "from the moment it prints its ready line until `start` returns" and a proof for "a Ctrl-C at any point" of it; closing down is inside that span and fails today the same way (§ Verified Claims), and an operator who sees nothing happen at once presses Ctrl-C again. The pick is additive and reversible.
- **Gap 2 — the span starts once the ready line has been written (b):** CP-644's span opens when the ready line is on standard output, not while it is being printed. — That is the moment the operator and the start tests can see the line and act on it; a SIGINT before it is the pre-ready case Out of Scope keeps as it is.
- **Gap 3 — "nothing written" read as standard error, plus nothing more on standard output and an untouched saved-data location (b):** CP-644 pins standard error empty; CP-645 adds that the stop writes nothing further to standard output and, with no action under way, leaves the saved data's files and bytes as they were. — The request's "exit 0 and nothing written" names the stream the start tests assert on, standard error; the other two are what an operator sees of a quiet stop today (reproduced, § Verified Claims), and pinning them keeps the fix from adding a farewell line or a save on the way out.
- **Gap 4 — the records' checks folded in (e):** CP-650 (SDD § 4 TS-2; NFDR QC-28), CP-651 (NFDR QC-11; SDD § 4 TS-3, TS-4), CP-653 (NFDR QC-62 and the compile gate of NFDR § 9), CP-654 (NFDR QC-60), CP-655 (NFDR QC-12) and CP-656 (NFDR QC-24) are stated as rules though the request names none of them. — Each is a test or check the product's records require of a change that alters the start's code or adds a test, and this one does both; the request itself places the defect in `main.py`, which QC-24 binds.
- **Gap 5 — CP-646 and CP-647 cite their records (e):** the request protects the ready line and the two refusals in its own words; the rules add FDR R-2 / NFDR QC-55 and FDR R-4, R-24 / NFDR QC-51, QC-58 as the checks that already guard them. — The records name the tests that verify them, so the rules point at those checks rather than leaving the protection as prose.
