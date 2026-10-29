# Security report

Security: reported

**Change:** `tracker17 · tobiishi · 2026-10-29_the-start-is-stoppable-from-its-ready-line` — reviewed 2026-10-29 by the Senior Engineer, on the branch at `12e48a9f7`, against its merge base `53ad18603`. Lens: `development-security/prompts/rich.md` with `<CORE>/prompts/senior_engineer_repair_dependencies.md`.

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` § 2 QC-40's `verified by:` says it in its own words — "No command can measure a window, and no audit command exists for this product: the Python packet names none and tracker17 installs none" — and § 10 lists QC-40 among the review gates with no row. No advisory was answered on this branch. Detail: § *Dependency audit*.

## Dependency audit
skipped — the NFDR names no dependency audit. QC-40 (`docs/nfdr.md` § 2, B-4) is verified by review at `development-design`, not by a command; its advisory watch is the owner's two feeds (Dependabot on the repository, and the browser build compared with the vendor's security releases at each design review). No command was invented and none ran (`senior_engineer_repair_dependencies.md` § *The audit command is the product's, not yours*). The change adds no dependency and moves no pin: `pyproject.toml` and `tests/requirements.txt` are not in `git diff --stat main...HEAD`. For the PM's awareness, not this run's to answer: the one dated exception in force is QC-40's for Chromium `153.0.8010.12` (`docs/nfdr.md` RN-33), 2026-10-10 to 2026-11-07, already tracked by the one row of `system/upkeep.md`.

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none | — | — | no audit ran | — |

## Exceptions and upkeep rows
none

## Holes in the code
none found.

**Threat classes applied.** The product is a local web server — code that serves and processes input — so the OWASP Top 10:2025 was the list, over the NFDR's four trust boundaries (§ 2 B-1 to B-4) and its § 3 privilege entries QC-42 to QC-45. The agentic list does not apply: the product holds no skill, prompt or launcher.

**What was traced.** The change's product diff is `main.py` (`StopRequests`, `Serving`, `SigintStopRequests`, `serve_until_stopped`, and `start` handing its lifetime to it) and `web/listener.py` (`Listener.serve_until`, `IDLE_WAIT_SECONDS`); the three test files are excluded as test-only. Data entering the changed code:

- **SIGINT** → `SigintStopRequests.latch` → a boolean set, read by `serve_until`. The signal comes from the operator's terminal or the OS, trusted like a command-line flag; the handler raises, prints, locks and writes nothing, so a repeated signal only re-sets the flag. `arm` leaves `SIG_IGN` as found, and arming off the main thread raises `ValueError`, which the `try`/`finally` closes the listener on (the code-integrity fix) and propagates.
- **HTTP requests** → `Listener.handle_request` → `_Handler._serve` → `Site.handle`. `serve_until` changes only how often the accept loop looks at the flag (a half-second `timeout` on the server, restored in `finally`); the request path, the `Host` and `Sec-Fetch-Site` refusals (QC-31, QC-32), the response policy headers (QC-33, QC-34) and the `domain` checks (QC-38) are untouched. No new entry point, no new place where outside data arrives, no new write, socket or console use (QC-42, QC-43, QC-45 hold — `signal` is imported in `main.py`, the composition root, only).
- **Exceptional conditions (A10).** The old `except KeyboardInterrupt: pass` is gone; with the latch installed no `KeyboardInterrupt` can arise after the ready line, which is the change's point, and before arming the pre-ready case stays as it was (spec Out of Scope). A request already accepted when the stop lands is answered on its own thread; `ThreadingMixIn.server_close` joins those threads before the port is released.

**Sceptical pass.** No candidate reached the floor of 8. Considered and dropped: a stop that waits up to `IDLE_WAIT_SECONDS` plus the join of in-flight request threads (availability, excluded); a signal arriving mid-`handle_request` (PEP 475 resumes the `select`; the flag is read at the next loop head — no integrity effect).

## Not checked
- The dependency audit — none exists to run (above).
- The suite was not run by this step: it fixed no hole and took no bump, and the suite is owed only to keep one of those (`SKILL.md` § *The suite*). The verdict it rests on is the code-integrity report's: `2698 passed in 276.49s` at `12e48a9f7`, `Environment: owners-mac — no CI`.
- Nothing else: every file the change touches was read in full on the branch.
