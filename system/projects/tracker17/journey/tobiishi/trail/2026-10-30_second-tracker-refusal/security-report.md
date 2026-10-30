# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` § 2 QC-40 says in its own words "no audit command exists for this product: the Python packet names none and tracker17 installs none", and holds package advisories to a review at `development-design` with a Dependabot feed it records as down (2026-10-29). Detailed under *Dependency audit*.

## Dependency audit
skipped — the NFDR names no dependency audit. QC-40 (`products/tracker17/docs/nfdr.md` § 2) is verified by review, not by a command; § 10's map carries no audit row. No command was invented and none ran (`<CORE>/prompts/senior_engineer_repair_dependencies.md` § *The audit command is the product's, not yours*). The change moves no pin: `pyproject.toml` and `uv.lock` are untouched by the branch (`git diff --stat main...HEAD` lists neither).

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none — no audit ran | — | — | The one standing QC-40 exception (Chromium `153.0.8010.12` under `playwright==1.63.0`, RN-33) is read from `system/upkeep.md`, not from an audit; its row stands with lapse 2026-11-07 and is not touched here | — |

## Exceptions and upkeep rows
none

## Holes in the code
none.

Artifact class and lists applied: the product is code that serves, stores and processes input, so the OWASP Top 10:2025 and Anthropic's five categories were the list; it ships no skill, prompt or launcher, so the agentic list does not apply. Boundaries read from the NFDR: B-1 the loopback listener, B-2 the saved data at start, B-3 typed text, B-4 setup; § 3 accepts any local program as a caller.

What the change adds and where its data comes from:

- `persistence/location_use.py` (new) — the `flock` claim on the saved-data directory. Its one input, `location`, is `DEFAULT_LOCATION`, derived from the module's own path (`persistence/saved_data.py:25`) and handed in by `main.py:157`; `main(argv)` reads no argument. No request, file content, environment variable or typed value reaches it, so there is no untrusted path into `os.mkdir`, `os.open`, `fcntl.flock`, `os.stat` or `os.rmdir`. The writes stay inside the location (QC-42); the directory removal is guarded to the directory this attempt created, still empty, and still the live inode. A local process holding the lock, or a directory swapped under the claim, needs a caller already on the operator's machine, which § 3 accepts, and the effect is a refused or unclaimed start — availability, which the sceptical pass excludes.
- `main.py` — prints the fixed `ANOTHER_TRACKER_LINE` on `LocationInUse`, not the exception's text, so no path reaches the console beyond what the unreadable line already showed; the claim is released after the listener is closed. No new entry point, no new address, no new grant.
- `persistence/__init__.py` — exports only.
- `README.md` — documentation; nothing loads it as instructions.
- `tests/` — files that only test; excluded.

Candidates scored and dropped: lock-starvation and the 100-attempt bound (denial of service, excluded); a symlinked `data/` pointing outside the product root (needs local file-system control, below the floor; the lock then follows the symlink's target, which is also where the saved data already lives). Nothing scored 8 or above; nothing was fixed, so the suite was not run by this step.

## Not checked
- The dependency audit: none is named (above).
- Nothing else — every file the diff touches was read.
