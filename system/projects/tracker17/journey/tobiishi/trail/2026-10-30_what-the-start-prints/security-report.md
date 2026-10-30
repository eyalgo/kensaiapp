# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` § 2 QC-40 says in its own words "no audit command exists for this product: the Python packet names none and tracker17 installs none", and holds package advisories to a review at `development-design` with a Dependabot feed it records as down (2026-10-29; this change's `deferred_decisions.md` carries the same reading, made 2026-10-30). Detailed under *Dependency audit*.

## Dependency audit
skipped — the NFDR names no dependency audit. QC-40 (`products/tracker17/docs/nfdr.md` § 2) is verified by review, not by a command, and § 10's map says in so many words that QC-40 is a review gate with no row. No command was invented and none ran (`<CORE>/prompts/senior_engineer_repair_dependencies.md` § *The audit command is the product's, not yours*). The change moves no pin: `pyproject.toml` and `uv.lock` are untouched by the branch (`git diff --stat main...HEAD` lists only `products/tracker17/README.md` under the product).

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none — no audit ran | — | — | The one standing QC-40 exception (Chromium `153.0.8010.12` under `playwright==1.63.0`, RN-33) is read from `system/upkeep.md` line 10, not from an audit; its row stands with lapse 2026-11-07 and is not touched here | — |

## Exceptions and upkeep rows
none

## Holes in the code
none.

Artifact class and lists applied: the product is code that serves, stores and processes input, so the OWASP Top 10:2025 and Anthropic's five categories were the list; it ships no skill, prompt or launcher, so the agentic list does not apply. Boundaries read from the NFDR: B-1 the loopback listener, B-2 the saved data at start, B-3 typed text, B-4 setup; § 3 accepts any local program as a caller.

What the change adds and where its data comes from:

- `products/tracker17/README.md`, section `### What the start prints` — the only product file the diff touches (merge base `5e46e3a1a` to `20dcb471d`): four sentences of prose rewritten, no code, no test, no pin. Documentation: nothing loads it as instructions. The one thing in the product that reads the README is `tests/integration/test_start.py`, which reads its headings (`_headings`) and the first fenced command block under a named heading; this change adds no heading and no fenced block, and that file only tests, which the sceptical pass excludes. The section quotes the fixed console strings `main.py` already prints (`_unreadable_line`, lines 168–173; the refusals at lines 33 and 154) and introduces no new entry point, address, grant or data path.

Candidates scored and dropped: none arose — a prose edit with no path from any input to any use. Nothing scored 8 or above; nothing was fixed, so the suite was not run by this step. The code-integrity step's run on `<a commit not in the public history>` stands as the last green: exit 0, 2813 passed and 122 passed, `Environment: owners-mac — no CI`.

## Not checked
- The dependency audit: none is named (above).
- Nothing else — the one file the diff touches was read in full, with the three `main.py` sites it quotes.
