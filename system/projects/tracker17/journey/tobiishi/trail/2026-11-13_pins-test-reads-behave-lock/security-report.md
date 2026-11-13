# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit. `docs/nfdr.md` QC-40's tail says "no audit command exists for this product: the Python packet names none and tracker17 installs none", and § 10 carries no audit row. Detailed under `## Dependency audit`. `osv-scanner` ran in its place for this review only and reported nothing; it is not the audit the NFDR owes.

## Dependency audit
Skipped — the NFDR names no dependency audit. Read in the change's worktree at `6723bcda4`: `docs/nfdr.md` § 2 QC-40, *verified by*, ends "No command can measure a window, and no audit command exists for this product: the Python packet names none and tracker17 installs none", RN-10 says the same, and § 10's verification map lists QC-40 among the review gates with no row. No command was invented in its place. The product's dependency sets were still scanned by `osv-scanner` (next section).

## Scanners
- osv-scanner: 2.7.0 — found nothing. Run in the change's worktree over the product's two lock files, `products/tracker17/uv.lock` (15 packages) and `products/tracker17/.behave/uv.lock` (16 packages), the two files that resolve the product's own dependencies (NFDR QC-39); exit 0; `normalise --from osv-scanner` returned an empty list.
- Semgrep CE: 1.182.0 — found nothing. `semgrep scan --config p/default --metrics=off` over `products/tracker17` and the five files the diff touches under `system/projects/tracker17/journey/tobiishi/2026-11-13_pins-test-reads-behave-lock/`; 270 paths scanned, 0 results, 0 errors, exit 0.
- gitleaks: 8.30.1 — found nothing. Six `gitleaks dir --redact` runs, one over `products/tracker17` (about 14 MB scanned) and one per touched journey file; each exit 0, each report empty.

## Advisories
| Advisory | Dependency | Reported by | Answer | What was done | Commit |
|---|---|---|---|---|---|
| none | — | — | — | neither the audit (not named) nor osv-scanner reported one | — |

## Exceptions and upkeep rows
none. The product has no exception record (`checks/deps/advisory_exceptions.toml` is absent, and the NFDR names no *Advisory exception record* line), and nothing called for one. `system/upkeep.md` exists with no rows and was not changed.

## Holes in the code
none.

The diff from `main` to `6723bcda4` touches one file inside the product, `products/tracker17/tests/architecture/test_pins.py`, and five records under the change's journey folder. No production module, manifest or lock file moves.

Threat lists applied: tracker17 is code that serves and stores input over loopback (NFDR § 2 B-1 to B-4), so the OWASP Top 10:2025 list was applied — A01/A07 access and authentication, A05 injection and path traversal, A04 cryptographic failures, A08 code run from data, A02/A09 secrets in output, A06/A10 fail-open paths. A03 is Half 1's. The agentic list does not apply: the product carries no skill, prompt or launcher.

Phase 1, context: the boundaries are the listener (QC-30 to QC-35), the saved data read as data (QC-37), typed text escaped (QC-36) and setup (QC-39 to QC-41). Phase 2, comparison: the change adds no entry point, no place where outside data arrives, and no departure from those patterns — it is layer-6 test code (`code-integrity-report.md` § Placement). Phase 3, assessment: data traced in `test_pins.py` enters from the product's own committed `.behave/pyproject.toml` and `.behave/uv.lock`, or from a copy of the product under pytest's `tmp_path` that each case writes itself, is parsed with `tomllib` (executes nothing) and compared as strings; the `product_copy` fixture copies the product tree into `tmp_path` with `.venv`, `.pytest_cache` and `__pycache__` left out, and no case writes into the product's own tree (CP-780, confirmed by the integrity review). No candidate reached the sceptical pass; Semgrep and gitleaks offered none. A file that only tests is also outside the lens by its own exclusion list.

## Not checked
- The NFDR's dependency audit, because the NFDR names none (above). Whether the pinned Chromium build `158.0.8127.18` carries an advisory is QC-40's `development-design` review and was not re-done here.
- The suite was not run by this step: nothing was fixed or bumped, so there was no change of this step's own to prove.
