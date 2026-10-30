# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit (`products/tracker17/docs/nfdr.md` § 2 QC-40: "no audit command exists for this product: the Python packet names none and tracker17 installs none"). No advisory was answered on this branch — see *Dependency audit*.
- Nothing else: no hole was found and no fix was needed.

## Dependency audit
Skipped — the NFDR names no dependency audit. QC-40's `verified by:` names a review at `development-design`, not a command (`products/tracker17/docs/nfdr.md` § 2 QC-40), and its package feed is recorded there as down. The design step's two QC-40 reviews for this change stand in `change_design.md` § Architect Review Notes 7 and 8, and the owed graph-reading moment is already handed on in `deferred_decisions.md`. No command was invented in its place.

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none | — | — | the audit did not run | — |

## Exceptions and upkeep rows
none written. The one exception in force, QC-40's dated exception for Chromium `153.0.8010.12` (NFDR RN-33), is the owner's by hand and sits within its window: it lapses 2026-11-07, with its row already in `system/upkeep.md`.

## Holes in the code
none. The change's diff is two values on `system/projects/tracker17/project.md` and this change's own records; nothing under `products/tracker17/` changed. The card's values are run through `/bin/sh` by the chain's tools — the worktree creation runs `Setup command:` and the suite gate runs `Test command:` — so the agentic list was applied to them (ASI05 Unexpected Code Execution, ASI02 Tool Misuse, ASI03 Identity & Privilege Abuse); the web list does not apply, since no product code that serves, stores or processes input changed. Traced:

- `Setup command:` holds a command substitution, `$(git rev-parse --show-toplevel)`. Its only input is git's own answer for the worktree the chain made, double-quoted, so a path with spaces stays one argument. The card is a tracked instance file the chain trusts the way it trusts a command-line flag, and no outside content reaches the value. Confidence it is exploitable: 2 of 10 — below the floor.
- `Test command:` runs the two suites under `uv run --locked` and nothing else; a file that only runs tests is excluded by the sceptical pass. The `--locked` flag means neither command can rewrite `uv.lock`, which the code-integrity report proved (its T2 and T7).
- Neither value introduces a secret, an outbound fetch or a new tool grant (QC-41 and QC-35 unchanged; the design's review sweep, `change_design.md` § Architect Review Notes 5).

## Not checked
- The dependency audit, because the NFDR names none.
- The suite was not re-run by this step: no advisory fix and no hole fix was made, so there was nothing to keep on a green run. The last green run is the code-integrity report's (2698 passed, then 121 passed, `Environment: owners-mac — no CI`).
