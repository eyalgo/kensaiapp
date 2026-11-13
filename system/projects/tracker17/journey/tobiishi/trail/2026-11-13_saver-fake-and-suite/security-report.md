# Security report

Security: reported

**Change:** `2026-11-13_saver-fake-and-suite` (tracker17) · **Reviewed at:** `752d28c98`, the code-integrity
pass, on the change's branch. The product is inside the instance, so the code worktree and the pipeline
worktree are one.

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit. `docs/nfdr.md` QC-40 says so in
  its own words — "no audit command exists for this product: the Python packet names none and tracker17
  installs none" — and no `verified by:` tail in § 2 or § 10 names one. `osv-scanner` ran over both lock
  files in its place (§ Scanners) and reported no advisory, but it is not the NFDR's audit, and the
  NFDR still names none.

Nothing else is left: no hole, no advisory, no exception, no scanner that did not run.

## Dependency audit
skipped — the NFDR names no dependency audit. `docs/nfdr.md` § 2 QC-40, *verified by:* tail: "No
command can measure a window, and no audit command exists for this product: the Python packet names
none and tracker17 installs none". QC-40 keeps the advisory watch as a review at `development-design`
and names the Dependabot feed as down (2026-10-29). No command was invented in its place.

## Scanners
- osv-scanner: 2.7.0 — found nothing
- Semgrep CE: 1.182.0 — found nothing
- gitleaks: 8.30.1 — found nothing

osv-scanner read the product's two dependency sets, the ones NFDR QC-39 names: `products/tracker17/uv.lock`
(15 packages) and `products/tracker17/.behave/uv.lock` (16 packages), each passed as its own `--lockfile`
from the code worktree; exit 0, and `normalise --from osv-scanner` printed an empty list. Semgrep CE
(`p/default`, metrics off) read the product path and the five pipeline files the diff touches outside it
(`change_design.md`, `change_spec.md`, `changelog-report.md`, `code-integrity-report.md`,
`tl_instruction.md`): 288 paths scanned, 0 results, 0 errors, exit 0. gitleaks ran once over the product
path and once over each of those five files, redaction on: six runs, each "no leaks found", exit 0.

## Advisories
| Advisory | Dependency | Reported by | Answer | What was done | Commit |
|---|---|---|---|---|---|
| none | — | — | — | neither the audit (not named) nor osv-scanner reported one | — |

## Exceptions and upkeep rows
none. The product has no exception record (`checks/deps/` is absent) and none was needed; the NFDR
names no *Advisory exception record* line. `system/upkeep.md` exists in the instance and gained no row.

## Holes in the code
none.

**Scope read.** `git diff main...HEAD` touches 35 files under `products/tracker17/tests/` and the five
pipeline records. `git diff --stat main...HEAD -- . ':!products/tracker17/tests' ':!system/projects'`
lists nothing: no file under `application/`, `domain/`, `persistence/`, `web/`, `main.py` or `errors.py`
changes (spec I-2). Nothing under `tests/e2e/` changes.

**Threat lists applied.** tracker17 is code that serves, stores and processes input (a loopback HTTP
tracker), so the OWASP Top 10:2025 list was applied, through the NFDR's four boundaries — B-1 the
listener, B-2 the saved data at start, B-3 typed text shown back, B-4 setup. The product holds no
skill, prompt or launcher, so the agentic list does not apply.

**Phases.** *Context:* the request check (QC-31, QC-32), the one escaping function (QC-36), the
data-only reader (QC-37), the domain-rule gate on every request value (QC-38), the write capability held
to `persistence` inside `data/` (QC-42), and no outbound connection (QC-35). *Comparison:* the change
adds no entry point, no place where outside data arrives, no file write, no socket and no new library;
it adds `tests/fakes.py` (the one `Saver` fake) and `tests/integration/test_saver_contract.py`, and
moves 33 test modules' own `save` stand-ins onto the fake. *Assessment:* every touched file is a test
or test support, which is a listed exclusion ("a file that only tests, or only runs tests"). Checked
all the same: no module outside `tests/` imports `tests` (`grep -rn '^\s*\(from\|import\)\s*tests'` over
the six production paths: nothing), so the fake cannot reach a running tracker; `fakes.py` opens no
file, no socket and no process and calls no `eval`/`exec`/`pickle`; its held save waits on a bounded
event (10 s) inside a test; the real-saver run of the contract suite writes only under `tmp_path`.

**Candidates considered and dropped.** `FakeSaver.__getattr__` raising `AssertionError` on an
unexpected attribute (test-only, no data path, score 1). `test_failure_report.py`'s non-UTF-8 `PATH`
constant (pre-existing, test-only, drives the stderr-encoding case the test exists for, score 1). No
candidate reached the floor of 8.

## Not checked
- The NFDR's dependency audit: none is named, so none ran (§ Dependency audit). osv-scanner is not a
  substitute the NFDR recognises.
- No suite was run by this step: it made no fix and no bump, so there was nothing a suite run would
  have had to keep. The code-integrity report at `752d28c98` records the full card command green
  (3370 passed, 2 skipped; 122 passed), `Environment: owners-mac — no CI`.
- Everything else was read.
