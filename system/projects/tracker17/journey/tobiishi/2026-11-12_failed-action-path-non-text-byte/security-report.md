# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` QC-40, *verified by:* "no audit command exists for this product: the Python packet names none and tracker17 installs none". Detailed under `## Dependency audit`.

Nothing else is left: every scanner ran, `osv-scanner` reported no advisory against either lock file, no exception was written, and no hole was found.

## Dependency audit
skipped — the NFDR names no dependency audit. QC-40 is a review gate (`## 10. Verification map`: "QC-12, QC-25, QC-26, QC-27, QC-40, QC-41 and QC-60 are review gates and have no row"), and its text says no audit command exists for this product. No command was invented in its place; `osv-scanner` ran on this skill's own rule, beside the absent audit and not as it (below).

## Scanners
- osv-scanner: 2.7.0 — found nothing
- Semgrep CE: 1.182.0 — found nothing
- gitleaks: 8.30.1 — found nothing

How each ran, in the change's worktree at `dc586f47c`:

- `osv-scanner scan source --format json --lockfile <file>`, once for each lock file that resolves the product's own dependencies: `products/tracker17/uv.lock` (15 packages) and `products/tracker17/.behave/uv.lock` (16 packages) — the two sets QC-39 names. Both scans exited 0 and `normalise --from osv-scanner` printed an empty list for each. No other lock file or manifest under the product path.
- `semgrep scan --config p/default --metrics=off --json` over `products/tracker17` and the five files the diff touches outside it (the change's `change_design.md`, `change_spec.md`, `changelog-report.md`, `code-integrity-report.md`, `tl_instruction.md`): exit 0, 291 rules on 268 files, 0 findings, 0 errors.
- `gitleaks dir <path> --redact --no-banner --report-format json`, once for the product path and once for each of those five files: six runs, each exit 0, "no leaks found", empty report.

## Advisories
| Advisory | Dependency | Reported by | Answer | What was done | Commit |
|---|---|---|---|---|---|
| none | — | — | — | neither the audit (which did not run) nor osv-scanner reported one | — |

## Exceptions and upkeep rows
none written. No advisory to except; the product has no exception record (`checks/deps/advisory_exceptions.toml` is absent) and none was created.

One row was **removed** from `system/upkeep.md` in this run's report commit, under the boy-scout rule: the register's only row, "tracker17: end the browser exception by moving the `playwright==1.63.0` pin … to a release whose Chromium is `153.0.8010.36` or later", a task that has ended. NFDR RN-72 records the pin at `playwright==1.65.1` (Chromium 158.0.8127.18) in both manifests and both lock files, and RN-33's exception ended on 2026-11-07. The register's own rule is that a task that ends is removed and the commit says why. Not a security exception; noted here because the file is this report's to commit.

## Holes in the code
none.

The diff from `main` to `dc586f47c` adds one file of product code, `products/tracker17/tests/integration/test_failure_report.py` — a test module, which the sceptical pass excludes ("a file that only tests") — and five records under the change's journey folder. No production file changed.

Threat lists applied: the product is code that serves and stores input on a loopback listener (NFDR § 2, boundaries B-1 to B-4), so the OWASP Top 10:2025 list, with Anthropic's five categories as its corners. It holds no skills, prompts or launchers, so the agentic list did not apply.

Trace through the unchanged code the test exercises, marked *already on `main`*: `Site._guarded` (`web/routes.py`, QC-56's one catch site) catches an unexpected exception from an action, hands it to `Site._report_failure`, and answers the action's failure redirect. `_report_failure` writes the action's fixed sentence and then `type(error).__name__: str(error)` to `sys.stderr`. Candidates weighed and dropped:

- A09 — error text written to the console. The stream is the operator's own terminal on the operator's machine; the text is the system's error (a path, an errno), never a secret, a password or personal data. Nothing in `str(error)` reaches a page or a response. Confidence it is exploitable: 1.
- A05 — the typed comment carried back in the failure redirect's query. Already on `main`, built through `urlencode` by `_address`; the test's `FAILURE_REDIRECT` asserts the encoded form. No injection path. Confidence: 1.
- A10 — the catch site fails closed: the state is left as it was and the action answers its failure page; the write to `stderr` is the last thing before the answer, and a write that raised would propagate out of `_guarded`, not skip a guard. The change's intent (CONTENT RN-35) and the code-integrity report's mutation table cover the write. Confidence: 1.

Semgrep and gitleaks supplied no candidate.

## Not checked
- The dependency audit, because the NFDR names none (above). `osv-scanner` covered the two lock files in its place on this skill's own rule, but that is not the product's audit.
- No suite was run by this step: it made no dependency bump and no hole fix, and the suite is run only to keep one of those. The code-integrity step's run at `a18618545` stands (`code-integrity-report.md`: 3276 passed, 2 skipped; 122 passed).
