# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` § 2, QC-40's *verified by:* says "no audit command exists for this product: the Python packet names none and tracker17 installs none" — the advisories are watched by the owner through Dependabot and the browser vendor's releases, and checked by review at `development-design`. So no advisory was answered on this branch. Detail under *Dependency audit*.
- Nothing else: no hole was found and no exception was written.

## Dependency audit
Skipped — the NFDR names no dependency audit. QC-40 (`products/tracker17/docs/nfdr.md` § 2 *Security*, B-4) states the obligation and its *verified by:* names review, not a command: "No command can measure a window, and no audit command exists for this product: the Python packet names none and tracker17 installs none". No command was invented and none run. The one exception in force is QC-40's dated exception for Chromium `153.0.8010.12` (RN-33), tracked as the tracker17 row of `system/upkeep.md`, next due 2026-11-07; this change moves no pin (`pyproject.toml` and `tests/requirements.txt` are untouched by `main...HEAD`), so nothing about that exception changes here.

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none — no audit ran | — | — | — | — |

## Exceptions and upkeep rows
none

## Holes in the code
none.

Scope read: the change's product diff from the merge base to the branch head is one file, `products/tracker17/tests/conftest.py` — a new session-scoped autouse fixture `_interruptible_test_session` (lines 62–83) and the module docstring. The fixture reads the incoming SIGINT handler, installs `signal.default_int_handler` in the main thread only, and restores the saved handler in `finally`. The trace from it: it reaches `tests/integration/test_start.py` `_run_real_start` (line 516), which starts the tracker with `subprocess.Popen` on a fixed argument list and sends it `signal.SIGINT` (line 529). No argument of that call comes from outside the test, the product's own modules (`main.py`, `web/`, `application/`) are untouched and install no signal handler of their own, and no production file changed.

Threat lists applied: the product serves and processes input, so the OWASP Top 10:2025 list was applied over the NFDR's four boundaries (B-1 listener, B-2 saved data at start, B-3 typed text shown back, B-4 setup). The change crosses none of them: it adds no entry point, reads no outside data, grants no tool, and departs from no pattern the rest of the code keeps. The agentic list (ASI01–ASI10) does not apply — the product holds no skill, prompt or launcher, and the change touches none. The one candidate considered — a handler restored to a value the suite inherited — is the test process's own, is also a file that only runs tests (an exclusion of the sceptical pass), and has no path for an attacker's data; it is below the floor and is not a hole.

## Not checked
- The dependency audit, because the NFDR names none (above).
- The suite was not run by this step: no fix and no bump was made, so there was nothing to keep on a green run. The code-integrity run's result stands: `2651 passed`, `Environment: owners-mac — no CI`, recorded in `code-integrity-report.md` beside this file.
