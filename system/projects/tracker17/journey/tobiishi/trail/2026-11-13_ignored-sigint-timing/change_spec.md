# Change Spec — the ignored-SIGINT proof test holds in a full run

**Date:** 2026-11-13
**Category:** bug
**Behaviour:** preserving
**Request:** The test that starts a pytest with SIGINT ignored and has it run one real-start case (`tests/integration/test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint`) failed in a full run of the card's suite and passed alone, twice. The start case it selects waits a fixed 30 seconds for the tracker to stop after a real SIGINT. Find the timing dependence that is left after the ready-line fix, add a measurement among the change's tests that makes the failure happen on demand (it fails on the base commit and passes after the change, with no full run needed to hit it by luck), and remove the dependence in the product. Name the cause in the commit body or a test docstring. Where the cause sits in the start's stop path (`main.py`'s `SigintStopRequests` and `serve_until_stopped`, `web/listener.py`'s `serve_until`) the fix goes there; where it sits in the test's own setup it goes there, and the product is not touched for the sake of it. The proof test must keep proving what it proves: a start launched with SIGINT ignored stops, exits 0 and writes nothing to standard error. The test passes alone, and both commands of the card's test command (`tests/` and `tests/e2e/`) pass in full from the change worktree root. No wait limit is raised (the 30-second waits at `tests/integration/test_start.py` and `tests/integration/test_sigint_launch.py` stay as they are or shrink), and no test is skipped, retried or marked expected-to-fail. Nothing the product's public names accept or return changes.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened

---

## Change Summary

The proof that a start launched under a pytest with SIGINT ignored still stops on a real SIGINT fails in a full run of the suite and passes alone; the request records two such runs. This change makes that failure reproducible on demand, names its cause, and removes the cause where it sits — the start's stop path or the test's own setup — so the proof holds in a full run. What a start does on SIGINT is unchanged.

Paths below are relative to the product, whose location is `system/projects/tracker17/project.md` `Product path:`.

---

## Invariants (characterization contract)

- **I-1 — The suite passes, in full.** Both commands of the card's `Test command:` exit 0, each run in full from the change worktree root. Every existing test keeps every assertion it makes. A test whose setup the change alters asserts no less than it did at the base.
- **I-2 — Public interface.** Nothing the product's public names accept or return changes: the names in the `__all__` of `domain/__init__.py`, `application/__init__.py`, `persistence/__init__.py` and `web/__init__.py`, and the top-level names of `main.py` (among them `start`, `serve_until_stopped`, `SigintStopRequests`, `StopRequests` and `Serving`).
- **I-3 — The proof keeps proving what it proves.** `tests/integration/test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint` still shows that a start launched with SIGINT ignored stops on a real SIGINT, exits 0 and writes nothing to standard error. The case it hands the second pytest still requires exit status 0 and empty standard error from the started tracker. The test still requires that second pytest to exit 0 and to report exactly one case passed. None of these is weakened, and the test passes when run alone.
- **I-4 — A measurement makes the failure happen on demand.** Among the change's tests, run by one of the two commands of `Test command:`, is a test that fails on the base commit `8c3f7e74d` and passes after the change, on every run, with no full run of the suite needed to hit it. The cause it shows is named in the change's commit body or in that test's docstring.
- **I-5 — No wait limit is raised, nothing is hidden.** No wait limit in the product's tests is raised: not `timeout=30` at `tests/integration/test_start.py:L708`, which the selected case waits on, and not `OUTER_DEADLINE_SECONDS = 120` at `tests/integration/test_sigint_launch.py:L38`. Each stays as it is or shrinks. No test is skipped, retried or marked expected-to-fail: `git diff 8c3f7e74d..HEAD -- products/tracker17 | grep -nE '^\+.*(mark\.(skip|skipif|xfail)|xfail|retry|flaky|reruns)'` prints nothing.
- **I-6 — A test patches no name inside a part** (SDD § 4 TS-2). Every test the change adds or alters, the measurement included, hands a part its collaborators and patches no name inside it.
- **I-7 — Every test module names what it checks** (NFDR QC-11; SDD § 4 TS-3). Every test module the change adds or alters names, in its opening docstring, the SRS requirements or acceptance criteria it checks, and the pointer test in `tests/architecture/test_trace.py` passes.
- **I-8 — One fake per contract** (SDD § 4 TS-6; NFDR QC-64). No test module the change adds or alters defines a class of its own that stands in for the clock or for the object that saves.
- **I-9 — The code gates pass** (NFDR QC-62). From the product root, `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web` each pass after the change, as they do at the base.
- **I-10 — Small and plain** (NFDR QC-12). The change adds no part that no requirement pays for. This is judged at `development-design`'s review, as QC-12 says; no command checks it.

---

## Structural Goal

- The cause sits where the measurement shows it. When it sits in the start's stop path (`SigintStopRequests` and `serve_until_stopped` in `main.py`, `Listener.serve_until` in `web/listener.py`), the stop path is changed so a real SIGINT after the ready line ends the start whatever else the full run has done. When it sits in the test's own setup, the setup is changed and the product's code is not touched.
- The fix removes the dependence. It does not wait it out.
- Where the measurement lives, and how it is built, is `development-design`'s decision.

---

## Verified Claims

All rows were checked in the change worktree at the base commit `8c3f7e74d`. Each command ran through `uv run --locked` on the product's own locked environment, with a real child process and a real signal wherever the test sends one.

| Claim | Verified by | What came back |
|---|---|---|
| I-3: the proof test passes alone at the base | `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint`, from the worktree root | `1 passed in 1.26s` |
| I-3: what the proof test asserts | read `tests/integration/test_sigint_launch.py:L29-L32`, `L80-L81` | it selects `tests/integration/test_start.py::test_start_reads_each_legacy_form_with_every_existing_value[projects-only]`, and asserts `launch.returncode == 0` and one line matching `^1 passed(, \d+ warnings?)? in ` |
| I-3: what the selected case asserts | read `tests/integration/test_start.py:L694-L713`, `L740` | `_run_real_start` reads the ready line, sends `signal.SIGINT`, waits `communicate(timeout=30)`; the case asserts `(status, errors) == (0, b"")` |
| I-5: the two wait limits | read `tests/integration/test_start.py:L707-L708`, `tests/integration/test_sigint_launch.py:L36-L38` | `child.send_signal(signal.SIGINT)` then `child.communicate(timeout=30)`; `OUTER_DEADLINE_SECONDS = 120`, its comment saying it is longer than the selected case's 30 seconds |
| Structural Goal: the stop-path names exist | read `main.py:L57-L103`, `web/listener.py:L80-L93` | `SigintStopRequests` (`arm`, `latch`, `stop_requested`), `serve_until_stopped`, and `Listener.serve_until`, which calls `handle_request` with a 0.5-second idle wait until `stop_requested()` is true |
| I-7: the pointer test exists | `ls tests/architecture/test_trace.py` | present |
| I-9: the code gates pass at the base | `uv run --locked ruff format --check .`; `uv run --locked ruff check .`; `uv run --locked mypy main.py errors.py domain application persistence web` — from the product root | `355 files already formatted`; `All checks passed!`; `Success: no issues found in 28 source files` |
| Out of Scope: an ignored SIGINT stays ignored | `uv run --locked --project products/tracker17 pytest products/tracker17/tests/integration/test_start_stop.py::test_arming_preserves_an_inherited_ignored_sigint`, from the worktree root; read `main.py:L69-L71` | `1 passed, 6 warnings in 0.63s`; `arm` returns without installing its handler when SIGINT is already `SIG_IGN` |

The full-run failure itself was not reproduced here. It is the request's evidence, and making it reproducible is I-4's work.

---

## Out of Scope

- What a start does on SIGINT, as an operator sees it: the ready line, exit status 0, nothing on standard error, and the saved data left as it is.
- A tracker whose own process began with SIGINT ignored keeps it ignored once armed (`main.py:L69-L71`; asserted by `tests/integration/test_start_stop.py::test_arming_preserves_an_inherited_ignored_sigint`). A fix that makes such a tracker catch SIGINT changes behaviour, and is not this change.
- The ready-line gap that `tracker17 · tobiishi · 2026-10-29_the-start-is-stoppable-from-its-ready-line` closed. It stays closed and is not reopened here.
- The fakes and contract suites, which `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` owns.
- The Behave scenarios under `.behave/`, which `Test command:` does not run.

---

## Locked Answers (the divergence record — self-review 2026-11-13)

- **Gap 1 — the second "30-second wait" is 120 seconds:** the request names 30-second waits in both `tests/integration/test_start.py` and `tests/integration/test_sigint_launch.py`. The 30-second wait is `test_start.py:L708`. The limit in `test_sigint_launch.py` is `OUTER_DEADLINE_SECONDS = 120` at `L38`, and the 30 seconds its comment names is the selected case's. I-5 holds both limits by their values on disk — neither is raised — which is what the request's "stay as they are or shrink" asks of each.
- **Gap 2 — (e) the checks the records require of a test change:** the request does not name SDD § 4 TS-2, NFDR QC-11 with SDD § 4 TS-3, SDD § 4 TS-6 with NFDR QC-64, NFDR QC-62 or NFDR QC-12. Each binds every change that adds or alters a test or code, and this change adds at least one test. They are stated as I-6 to I-10, each citing its record.
- **Gap 3 — the inherited ignored SIGINT is named as a boundary:** the request does not mention it. It sits right beside the stop path the request names, and a fix that overrides an inherited `SIG_IGN` would pass the proof test while changing what the product does. It is named under Out of Scope, with the test that already asserts it, so the change cannot make the proof pass that way.
