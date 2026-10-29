# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit (`products/tracker17/docs/nfdr.md` § 2, QC-40: "no audit command exists for this product: the Python packet names none and tracker17 installs none"). No advisory was answered on this branch; the pins stand as the last `development-design` review left them. Detailed under *Dependency audit*.
- Nothing else. No hole was found in the change's code, and no exception was written.

## Dependency audit
Skipped — the NFDR names no dependency audit. QC-40 (`products/tracker17/docs/nfdr.md` § 2) puts the dependency check at `development-design` review, by hand against published advisories, and states in so many words that no audit command exists for this product. Under `senior_engineer_repair_dependencies.md` § *The audit command is the product's, not yours*, no command was invented and none ran. The resolved set is `products/tracker17/tests/requirements.txt` (15 pins); none was touched by this change. The one standing exception, QC-40's dated exception for Chromium `153.0.8010.12` (RN-33, lapse 2026-11-07), is already a row in `system/upkeep.md`; with no audit output to read it against, nothing was done to it.

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none | — | — | no audit ran (NFDR names none) | — |

## Exceptions and upkeep rows
none

## Holes in the code
none.

What was read: the diff `main...HEAD` in `products/tracker17/`, two files — `tests/integration/test_sigint_launch.py` (new, one test) and `tests/conftest.py` (lines 1–2 of the docstring rewrapped, no code change) — and the paths the new test's trace passes through on `main`: `tests/integration/test_start.py` `_run_real_start` (lines 516–535), `tests/conftest.py` `_interruptible_test_session` (lines 62–82) and `main.py` `start`.

Threat lists applied: the product is a loopback web service in Python, so the OWASP Top 10:2025 list through Anthropic's five categories (access control / authentication, injection incl. command and path, cryptographic failures, code run from data, secrets in logs, fail-open error paths). The NFDR's boundaries B-1 to B-4 were read first; the change touches none of them — it adds no entry point, no place where outside data arrives, and no production code.

Candidates considered and dropped in the sceptical pass:
- `/bin/sh -c 'trap "" INT; exec "$@"'` in the new test (command execution, A05/ASI05): the script string is a module constant, every argument is a constant or `sys.executable`, and the selected node is a fixed literal; nothing read from a file, an environment variable or an argument reaches the shell. Confidence it is exploitable: 1. Dropped — and the file only tests, an exclusion on its own.
- `os.killpg(launch.pid, SIGKILL)` on the outer-timeout and `finally` paths: the group is the one `start_new_session=True` made for this launch, so the signal cannot reach a process the test did not start. Confidence: 1. Dropped.
- `PRODUCT_ROOT = Path(__file__).resolve().parent.parent.parent` as `cwd`: derived from the module's own location, not from the working directory or input. No traversal path. Dropped.
- Already on `main`, passed through by the trace: `_run_real_start` runs `sys.executable -c RUN_START <location>` with a `tmp_path` location; `main.start` reads the saved data through `SavedData.load`, which QC-37 holds to a reader that executes nothing. No outside data enters along this path in the test. Nothing to fix or report.

## Not checked
- The dependency audit: not run — the NFDR names none (above).
- The suite was not run by this step: it fixed nothing and bumped nothing, so there was no change to prove green. No `Environment:` line is copied here, because none was printed by a run this step made. The code-integrity step's run of the card suite (`code-integrity-report.md`: exit 0, `2652 passed`) stands as the last run on this branch.
- The end-to-end suite and the ignored-INT launches: not re-run here, for the same reason; the developer recorded them as exit 0 and this step changed no file in the product.
