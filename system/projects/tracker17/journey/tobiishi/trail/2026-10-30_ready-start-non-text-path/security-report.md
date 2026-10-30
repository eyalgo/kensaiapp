# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` QC-40 says so in its own words — "no audit command exists for this product: the Python packet names none and tracker17 installs none" — and § 10 lists QC-40 as a review gate with no row. No advisory was answered. Detailed under *Dependency audit* and *Not checked*.

## Dependency audit
Skipped — the NFDR names no dependency audit. The one supply-chain entry, QC-40 (`docs/nfdr.md` § 2, B-4), is verified by review at `development-design`, not by a command, and its `verified by:` tail states that no audit command exists for this product. The `uv.lock` of QC-39 fixes the test dependencies only; the running tracker has no third-party dependency (QC-19). Nothing was run, and no command was invented in its place.

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none | — | — | the NFDR names no audit, so none was reported | — |

## Exceptions and upkeep rows
none. The existing QC-40 exception for the browser build (RN-33, lapse 2026-11-07) and its row in `system/upkeep.md` were not touched: it is a review-gate exception, not one an audit reads, and this change moves no pin.

## Holes in the code
none.

The change's diff from `main` (`a7d507b23`) to the branch head is one product file, `products/tracker17/main.py`: three constants, the new `_shown_location`, and `_ready_line` calling it. The two other files are tests (`tests/unit/test_start_message.py`, `tests/integration/test_ready_start.py`), which the lens excludes.

- **Threat lists applied.** The product serves, stores and processes input, so the OWASP Top 10:2025 list was applied against the NFDR's four boundaries (B-1 the listener, B-2 the saved data at start, B-3 typed text shown back, B-4 setup). It holds no skills, prompts or launchers, so the agentic list does not apply.
- **Context.** The product's patterns: one escaping function in `web` for every value put into a page (QC-36), values checked by `domain` rules before state changes (QC-38), only `persistence` writes files and only under `data/` (QC-42), only `main.py` and one site in `web/` write to the console (QC-45), and the saved-data location is worked out from where the code is, never from an argument or the working directory (QC-42; `main.main` reads no argument).
- **Comparison.** The change adds no entry point, no place where outside data arrives, no file write, no socket, and no page. It changes one string written to standard output.
- **Assessment.** The one data path: `location` (the `Path` the claim, load and saves already use) → `str(location)` → `_shown_location`, which rewrites each lone low surrogate U+DC80–U+DCFF as `\xNN` and leaves every other character as it is → `_ready_line` → `print(..., flush=True)` on standard output. The display form reaches nothing else: `_shown_location` has one caller, `_ready_line`, and the original `Path` is what `SavedData`, the claim and `listen` are handed, which `test_readable_start_keeps_the_original_path_for_the_file_system` holds. The path is the operator's own machine location, not attacker-controlled (QC-42; at the trust level of an environment variable, which the lens excludes), and the output is a console line, not HTML, a query, a command or a path. No candidate reached the confidence floor; the one considered — a control byte in a folder name reaching the terminal — is ASCII the change does not touch, was already on `main`, needs control of the operator's own file system, and scores well below 8.
- **Already on `main`, out of the change's trace.** `_unreadable_line` and `web.UnreadableSite` still take the raw `str(location)`; the change's spec names them Out of Scope (the seed's next item, `unreadable-start`), and the trace of this change's code does not pass through them, so they are not holes of this review.

No fix was made, so the suite was not run by this step; the code-integrity step's green run through the gate tool (`code-integrity-report.md`, *Test evidence*) stands as the branch's last suite result.

## Not checked
- The dependency audit: skipped, the NFDR names none (above).
- The QC-40 package-advisory review of the pins `uv.lock` fixes: a `development-design` review gate, not this step's; the design step's reading of the feed is recorded in `deferred_decisions.md` on this change.
