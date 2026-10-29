# Change Spec — a proof test for the ignored-SIGINT launch, and the shared test file's line 1 reflowed

**Date:** 2026-10-29
**Category:** bug
**Behaviour:** preserving
**Request:** Add the proof test the first unit on this station deferred, and finish that unit's leftover line. The suite already passes whether it is launched in the foreground or with SIGINT ignored, because a session fixture in `products/tracker17/tests/conftest.py` gives the suite's own children default SIGINT. But nothing in the suite would catch that fixture being lost: no test fails when the suite is launched with SIGINT ignored and the fixture is missing. Add one test, named by this change, that passes in the foreground at the commit under test and fails in the foreground on `970f6a4ca`, the commit where the start tests' SIGINT did not stop a tracker under an ignored-SIGINT launch. The test should show the fixture's effect directly (the test process, and so a tracker it starts, gets a SIGINT that stops it even when the launch ignored SIGINT), and should drive the real start in a child process as the existing start tests do. Also reflow line 1 of `products/tracker17/tests/conftest.py`, which is 101 columns against the Python packet's 100 (`conventions.md:17`). Both of the product's suites (`python -m pytest products/tracker17/tests/ -q` and `python -m pytest products/tracker17/tests/e2e/ -q`) must still exit 0 in the foreground and under `sh -c 'trap "" INT; exec <command>'`, with the proof test passing in both launches at the commit under test; run it all in a disposable clone of that commit. Ctrl-C at a terminal must keep stopping the tracker for an operator; no test may be deleted, skipped or marked expected-to-fail; the start tests must keep exercising the real start in a child process; and no product document is edited unless a sentence this change makes false requires it.
**Language resolution:** Python — step 1 (`project.md` `Languages:`) — `<CORE>/doctrine/engineering/languages/python/README.md` opened, every routed concern read

---

## Change Summary

The suite passes under an ignored-SIGINT launch only because of one session fixture in the shared test file, and no test fails if that fixture is lost. This change adds the one test that does, and rewraps that file's 101-column first line. The tracker's behaviour does not change.

---

## Invariants (characterization contract)

- **The existing test suite passes unchanged.** Every existing test keeps every assertion it makes today, and none is deleted, skipped or marked expected-to-fail. Typed from the repository root, each of these four launches exits 0, at the branch point and after the change:
  - `python -m pytest products/tracker17/tests/ -q`
  - `sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/ -q'`
  - `python -m pytest products/tracker17/tests/e2e/ -q`
  - `sh -c 'trap "" INT; exec python -m pytest products/tracker17/tests/e2e/ -q'`
- **Public interface:** `main.start(address, location)` and `main.main(argv=None)` keep their signatures and return values. Nothing else the product exposes changes.
- **Ctrl-C at a terminal keeps stopping the tracker for an operator.** A tracker started with SIGINT at its default disposition stops on SIGINT, exits 0 and writes nothing to standard error.
- **The start tests keep exercising the real start in a child process.** Each existing case that calls `_run_real_start` (`tests/integration/test_start.py:516`) still starts the product's own `main.start` in a separate process and stops it with SIGINT. Each still asserts exit status 0, an empty standard error, and saved data and a file listing left as they were.
- **No product document is edited** unless this change makes one of its sentences false. Where that happens, only that sentence changes. None is expected to (Verified Claims).
- **The test module that holds the proof test names the requirements or acceptance criteria it checks** (nfdr.md QC-11; SDD § 4 TS-3). The pointer test in `tests/architecture/test_trace.py` checks this, and it runs in the first suite above.
- **The proof test hands each part its collaborators and never patches a name inside it** (SDD § 4 TS-2).
- **The code passes `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web`, each with exit 0, typed from the product root** (nfdr.md QC-62). All three pass at the branch point (Verified Claims).

---

## Structural Goal

- **The proof test.** The change adds exactly one test, and the change's own record names it so that a later stage can run it by name. The test:
  1. is collected by `python -m pytest products/tracker17/tests/ -q`, the project card's suite (Locked Answers, Gap 1);
  2. passes in the foreground at the commit under test;
  3. passes at the commit under test when the suite is launched with SIGINT ignored (`sh -c 'trap "" INT; exec …'`);
  4. fails in the foreground when it is added to the tree at `970f6a4ca`, where the shared test file has no SIGINT session fixture. The failure has to be the one the fixture prevents: a SIGINT the test sends does not stop a tracker that was started under an ignored-SIGINT launch, so the wait times out or the tracker is still running. A failure for any other reason does not count, such as an import error, a missing name, a collection error, or an assertion about something other than whether the tracker stopped (Locked Answers, Gap 2);
  5. starts the product's real `main.start` in a child process and stops it with a real SIGINT, as `_run_real_start` does. Starting under a launch that ignored SIGINT, that tracker must stop on the test's SIGINT. This is the fixture's effect, shown directly.

  How the test sets up the ignored-SIGINT launch, which module holds it and what it is called are development-design's call.
- **The reflow.** Line 1 of `products/tracker17/tests/conftest.py` fits within 100 columns. The module docstring keeps every word and the order of its words; only its line breaks move. No other line of the product is rewrapped (Out of Scope).
- **Where the change sits.** Only in `products/tracker17/tests/`. No module outside `tests/` changes, and neither do the shared test file's fixtures or collection rule (Locked Answers, Gap 3).

---

## Verified Claims

The runs were made in a disposable clone of the repository at `812786063`, with a fresh virtual environment built from `products/tracker17/tests/requirements.txt` on Python 3.15.0. They ran under the conditions the request fixes: commands typed from the repository root, the real `main.start` in a child process, and a real SIGINT. This change branches from `<a commit not in the public history>`, and neither `products/tracker17/` nor `system/projects/tracker17/` differs between the two commits (first row).

| Claim | Verified by | What came back |
|---|---|---|
| The product and project trees at the branch point are the ones the runs below used. | `git diff --stat 812786063 <a commit not in the public history> -- products/tracker17 system/projects/tracker17` | empty, exit 0. The only commits between them touch `core/tools/`'s test-isolation check |
| The first suite passes in the foreground. | `python -m pytest products/tracker17/tests/ -q`, repository root | exit 0; `2651 passed in 276.01s` |
| The first suite passes when launched with SIGINT ignored. | `sh -c "trap '' INT; exec python -m pytest products/tracker17/tests/ -q"`, repository root | exit 0; `2651 passed in 282.00s` |
| The end-to-end suite passes in the foreground. | `python -m pytest products/tracker17/tests/e2e/ -q`, repository root | exit 0; `121 passed in 59.13s` |
| The end-to-end suite passes when launched with SIGINT ignored. | `sh -c "trap '' INT; exec python -m pytest products/tracker17/tests/e2e/ -q"`, repository root | exit 0; `121 passed in 57.07s` |
| The SIGINT session fixture is in the shared test file at the branch point and absent at `970f6a4ca`. | read `tests/conftest.py`; `grep -c _interruptible_test_session` at `970f6a4ca` | present at `:62-82`: it sets `signal.default_int_handler` in the main thread and restores the incoming handler. Count `0` at `970f6a4ca` |
| A proof test with the five properties in § Structural Goal can be written. This is a check that the target can be met, not the design. | a throwaway test, made in the clone and then deleted. It runs one real-start case (`test_start_reads_each_legacy_form_with_every_existing_value[projects-only]`) in a child pytest whose SIGINT is set to ignored before it starts, and requires exit 0. It was run in the foreground at `812786063`, under `sh -c "trap '' INT; exec …"` at `812786063`, and in the foreground in a checkout of `970f6a4ca` with the same file added | `1 passed in 0.28s`, exit 0; `1 passed in 0.25s`, exit 0; `1 failed in 30.35s`, exit 1. The inner run raised `subprocess.TimeoutExpired` after 30 s, because the tracker did not stop on SIGINT, which is the failure property 4 requires |
| `_run_real_start` starts the real start in a child and stops it with SIGINT; its callers assert exit 0, an empty standard error and unchanged data. | read `tests/integration/test_start.py` | `:516-535`: `Popen([sys.executable, "-c", RUN_START, …])`, where `RUN_START` (`:455-458`) calls `main.start(('127.0.0.1', 0), …)`; then `send_signal(signal.SIGINT)` and `communicate(timeout=30)`. A caller at `:560-563` asserts `(status, errors) == (0, b"")` and the saved bytes and listing unchanged |
| Ctrl-C at the default disposition stops the tracker with exit 0 and an empty standard error. | the foreground first-suite run above, in which every `_run_real_start` case passes while asserting exactly that | exit 0, no failure |
| Line 1 of the shared test file is 101 columns, against a limit of 100. | `awk 'length($0)>100'` over `tests/conftest.py`; `ruff check --select E501 tests/conftest.py`; `pyproject.toml` `[tool.ruff] line-length = 100`; `conventions.md:17` | line 1 only, length 101; `E501 Line too long (101 > 100)` at `tests/conftest.py:1:101`; `line-length = 100`; `conventions.md:17` reads "**Lines stay within 100 columns.**" |
| The 101-column line does not fail QC-62, and it is not the product's only over-long line. | `ruff check .` and `ruff check --select E501 .`, product root | `All checks passed!`, exit 0, because the configured rule set does not include E501; with E501 selected, `Found 91 errors` across the product |
| The three QC-62 gates pass at the branch point. | `ruff format --check .`, `ruff check .`, `mypy main.py errors.py domain application persistence web`, product root, pinned tools | exit 0 each: `269 files already formatted`, `All checks passed!`, `Success: no issues found in 27 source files` |
| No product document has a sentence this change makes false. | `grep -n SIGINT` over `docs/*.md` and `README.md` outside `docs/trail/`; read the `conftest` mentions | no SIGINT hit. `nfdr.md:540` ("stops on the two `conftest.py` files") stays true, because the change adds no conftest and removes none |

---

## Out of Scope

- **What SIGINT does to a running tracker, under either disposition it can inherit.** The start is not changed (Structural Goal, *Where the change sits*).
- **The product's other 90 lines over 100 columns** (Verified Claims, the E501 row). Only line 1 of `tests/conftest.py` is reflowed, which is what the request asks.
- **The shared test file's collection rule** (`pytest_ignore_collect`, `tests/conftest.py:53-59`) and a single run collecting all four test folders. The station's bar now names the product's two suites instead.
- **Any change to an existing test.** No existing test body or assertion changes. The proof test is the only test added.

---

## Locked Answers (the divergence record — self-review 2026-10-29)

- **Gap 1 — the proof test runs in the card's suite:** the request asks for "one test" and requires both suites to pass, but does not say which suite holds the test. It is placed in `python -m pytest products/tracker17/tests/ -q`, because that is the project card's `Test command:` and the suite each delivery stage and the seal end on. A test there guards the fixture at every gate; a test only in the end-to-end suite would guard it only where the browser is installed.
- **Gap 2 — the failure on `970f6a4ca` must be the stop that does not happen:** the request names the cause ("the commit where the start tests' SIGINT did not stop a tracker under an ignored-SIGINT launch") but does not rule out failing there for another reason. A test that failed on `970f6a4ca` only because a name it imports is missing would meet the request's words and prove nothing about the fixture. So property 4 counts only the failure the fixture prevents.
- **Gap 3 — tests only:** both things the request asks for are in `tests/`, and the station's guardrail puts any change to what Ctrl-C does for an operator out. So the spec fences the change to `tests/` and leaves the shared file's fixtures and collection rule unchanged. A proof that needed a change outside `tests/`, or a change to the fixture it proves, would no longer be the change the request describes.
- **Gap 4 (e) — record checks stated as Invariants:** the request does not name nfdr.md QC-11, QC-62 or SDD § 4 TS-2 and TS-3. A record above the change requires each of them of the test code this change adds, so each is an Invariant that cites its record.
