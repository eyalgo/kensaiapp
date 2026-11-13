# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit (`products/tracker17/docs/nfdr.md` QC-40, "no audit command exists for this product: the Python packet names none and tracker17 installs none"). Detailed in `## Dependency audit`.

## Dependency audit
skipped — the NFDR names no dependency audit. QC-40's *verified by* places the advisory check at the `development-design` review and says in its own words that no audit command exists for this product. No command was invented in its place; `osv-scanner` ran beside it as this skill requires (below), and reported no advisory against either lock file.

## Scanners
- osv-scanner: 2.7.0 — found nothing
- Semgrep CE: 1.182.0 — found nothing
- gitleaks: 8.30.1 — found nothing

Where each one ran. `osv-scanner` read the two lock files that resolve the product's own dependencies, `uv.lock` (15 packages) and `.behave/uv.lock` (16 packages), both under the product path, as `--lockfile` targets; the manifests beside them, `pyproject.toml` and `.behave/pyproject.toml`, declare what those lock files fix. Semgrep CE read the product path (274 files, 36 of them Python) and the five records the diff touches under the change's own folder; its default ignore list skips a folder named `tests/`, so the two files this change writes, `tests/conftest.py` and `tests/architecture/test_behave_imports.py`, were read in a second run that named them as explicit targets, and both came back with no finding and no error. `gitleaks` ran once over the product path and once over each of the five touched records, with redaction on; each run exited 0 with an empty report.

## Advisories
| Advisory | Dependency | Reported by | Answer | What was done | Commit |
|---|---|---|---|---|---|
| none | — | — | — | neither the audit (not named) nor osv-scanner reported one | — |

## Exceptions and upkeep rows
none. The product has no exception record (`checks/deps/advisory_exceptions.toml` is absent) and none was needed; the NFDR names no *Advisory exception record* line, so a first one would have gone to the default path under the default window.

## Holes in the code
none.

Threat lists applied. The NFDR § 2 names four trust boundaries, B-1 the listener, B-2 the saved data at start, B-3 typed text shown back and B-4 setup, and the product's artifact class is code that serves input, so the OWASP Top 10:2025 list was the lens. The change's diff touches two files under `tests/`: `tests/conftest.py` gains `BehaveWalk`, a walk of the product root's `.behave/` folder, and `tests/architecture/test_behave_imports.py` is new. Trace: each module under `.behave/` is read with `Path.read_text` and parsed with `ast.parse`, never imported or executed; the only inputs are the product's own committed files and the `tmp_path` fixtures the tests plant; the walk follows a symlink named `.behave` only to list `.py` files for parsing, and a dangling one fails the walk. No serving code (`web`, `main`, `application`, `persistence`, `domain`) changes, so B-1, B-2 and B-3 are untouched, and B-4 is untouched because no pin or lock file moves. Every candidate falls under the sceptical pass's exclusion "a file that only tests, or only runs tests", and none reached the confidence floor of 8. Semgrep and gitleaks offered no candidate.

## Not checked
- The dependency audit: the NFDR names none, so none ran (above).
- The agentic list (OWASP Top 10 for Agentic Applications 2026) was not applied: the product holds no skill, prompt or launcher.
