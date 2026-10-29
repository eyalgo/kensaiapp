# Security report

Security: reported

**Change:** tracker17 · tobiishi · 2026-10-29_uv-lock-and-pins-test
**Reviewed by:** Senior Engineer, 2026-10-29 · **Branch head read:** `568d4d5b4` (the code-integrity pass), merge base with `main` `c4777b8b7`.

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit (`products/tracker17/docs/nfdr.md` § 2 QC-40, *verified by*: "no audit command exists for this product: the Python packet names none and tracker17 installs none"), and the rules forbid running one the NFDR does not name. The advisory check the product does have is QC-40's review at `development-design`, which this change's design ran under CP-666; what this review could add is below under *Dependency audit*.

## Dependency audit
Skipped — the NFDR names no dependency audit. § 2 QC-40 states it in so many words (quoted above), and § 10 *Verification map* carries no audit row (its preamble names a dependency audit only as an example of scope). No command was invented and none ran. The product has no advisory exception record (`checks/` does not exist) and none was created, because no advisory was reported to except.

What was read instead, as supply-chain evidence for the PM: `uv.lock` holds 17 package records — the fifteen versions the deleted `tests/requirements.txt` fixed, `colorama 0.4.6` (Windows-only marker) and the product itself (`source = { virtual = "." }`). Every one of the 16 fetched packages resolves from `registry = "https://pypi.org/simple"` and carries sha256 hashes on its sdist and wheels (328 hash lines; the only record without one is the virtual workspace member). No git, URL, path or alternate-index source is in the lock. The one standing advisory the records know, the Chromium build of `playwright==1.63.0`, is under the owner's dated exception NFDR RN-33 to 2026-11-07, tracked by the existing row in `system/upkeep.md`.

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none — no audit ran | — | — | — | — |

## Exceptions and upkeep rows
none written. One existing row corrected in place (found while walking, clause 1): the `system/upkeep.md` row for RN-33 named `tests/requirements.txt` as where the `playwright==1.63.0` pin lives, and this change deletes that file; the row now names `pyproject.toml` and `uv.lock`. Its task, cadence, dates and reminder are unchanged. Carried in this report's commit.

## Holes in the code
none. The change's executable code is one test file, `tests/architecture/test_pins.py` (a file that only tests, excluded by the sceptical pass, and read anyway): it reads `uv.lock` with `tomllib`, a parser that executes nothing, compares names and versions as data, and takes no outside input beyond two committed files under the product root. The other touched files are `uv.lock` (data, read above), a comment block in `pyproject.toml`, the deleted pip lock file, and a wording edit to `docs/nfdr.md` QC-39 (a record, already recorded as a call in `code-integrity-report.md`). No runtime part (`domain`, `application`, `persistence`, `web`, `main.py`) is touched, so no trust boundary of NFDR § 2 (B-1 to B-3) or privilege entry of § 3 is reached; the change sits wholly at B-4, setup.

Lists applied: the product is code that serves and processes input (a loopback web tracker), so OWASP Top 10:2025 with Anthropic's five categories was the list over the diff — A01/A07, A05, A04, A08 (the lock's provenance and the test's parser), A02/A09, A06/A10. The product ships no skill, prompt or launcher, so the agentic list was not in scope. Phase 1 read NFDR § 2 and § 3 and the existing `test_pins.py` pattern (`tomllib` on `pyproject.toml`); phase 2 found no new entry point, no new place where outside data arrives, and no departure from the file's own pattern; phase 3 traced the two file reads to their assertions and found no use that matters beyond a pass/fail.

## Not checked
- No dependency audit, as above.
- No suite was run by this step: nothing was bumped and no hole was fixed, so there was no change to keep on a green run. The last gate run is the code-integrity report's (exit 0, 2698 passed, `Environment: owners-mac — no CI`), on the same branch head this review read.
- `tests/integration` and `tests/e2e`, and the Python 3.11 run, stay as the spec's *Out of Scope* leaves them.
