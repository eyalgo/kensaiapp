# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` QC-40's *verified by* says in its own words "no audit command exists for this product: the Python packet names none and tracker17 installs none", so no advisory was answered (§ Dependency audit below). The standing dated exception for the browser build (QC-40, RN-33; upkeep row due 2026-11-07) was not re-examined here, since no audit reported it.

## Dependency audit
skipped — the NFDR names no dependency audit. QC-40 (`products/tracker17/docs/nfdr.md`, the `*verified by:*` tail ending "no audit command exists for this product: the Python packet names none and tracker17 installs none") makes the supply-chain check a review at `development-design`, with no command. No command was invented and none ran. Nothing in the change's diff adds, removes or moves a dependency: `pyproject.toml` and `uv.lock` are untouched (`git diff --stat main...HEAD` lists `products/tracker17/README.md` as the one product file).

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none | — | — | no audit ran (above) | — |

## Exceptions and upkeep rows
none

## Holes in the code
none. The change's whole product diff is `products/tracker17/README.md` (merge base `898e1ccf6` to `b5797647e`): the `### Running the tests` section, two `## How it's built` bullets and the `docs/adr/` line. No Python, no page, no route, no file or network path changed.

Threat lists applied, by artifact class: the product serves and stores input (NFDR § 2, boundaries B-1 to B-4), so the OWASP Top 10:2025 list (A01, A02, A04, A05, A06, A07, A08, A09, A10) was read against the diff; the agentic list (ASI01–ASI10) was read for whether the README is loaded anywhere as instructions. It is not: the one product file that reads it, `tests/integration/test_start.py`, reads its headings to assert the unreadable-data message names a real section (CP-67) — a test reading documentation, not an instruction path. The README's commands are typed by a person; `uv` is named as a prerequisite with the vendor's installation page and no installer recipe, as the spec requires (CP-668), and `uv sync --locked` installs only what `uv.lock` already fixes. No candidate reached the floor of 8.

## Not checked
- Dependency advisories, for the reason above.
- No suite was run: the run made no fix and no bump, so no green run was owed (SKILL.md § The suite runs only to keep one).
