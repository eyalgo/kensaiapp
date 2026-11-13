# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the product's NFDR names no dependency audit — `docs/nfdr.md` QC-40 says "no audit command exists for this product: the Python packet names none and tracker17 installs none" (RN-10). Detailed under `## Dependency audit`. `osv-scanner` ran in its place on every lockfile and reported nothing, but it is not the audit the NFDR names.

## Dependency audit
Skipped — the NFDR names no dependency audit. `docs/nfdr.md` § 2 QC-40 states it in so many words ("no audit command exists for this product: the Python packet names none and tracker17 installs none"), and RN-10 records why: the Python packet's quality gates name no audit command and no scanner, and installing one is a toolchain decision the NFDR does not make. No command was invented in its place, per the shared rules.

## Scanners
- osv-scanner: 2.7.0 — found nothing. Two dependency sets resolve the product's own dependencies, both scanned, each with its own `--lockfile`: `uv.lock` (15 packages) and `.behave/uv.lock` (16 packages), the two sets QC-39 names. Both exited 0, and `normalise` read each as an empty list.
- Semgrep CE: 1.182.0 — found nothing. `semgrep scan --config p/default` over the product path and the six records the change touches outside it (the change's `change_spec.md`, `change_design.md`, `tl_instruction.md`, `halt_report.md`, `changelog-report.md` and `code-integrity-report.md`): 291 rules over 277 git-tracked files, 0 findings, 0 errors, exit 0.
- gitleaks: 8.30.1 — found nothing. Seven runs of `gitleaks dir --redact`: one over the product path, one over each of the six touched records. Each exited 0 with an empty report.

## Advisories
| Advisory | Dependency | Reported by | Answer | What was done | Commit |
|---|---|---|---|---|---|
| none | — | — | — | neither the audit (not named) nor osv-scanner reported one | — |

## Exceptions and upkeep rows
none. The product has no exception record (`checks/deps/advisory_exceptions.toml` is absent) and none was needed; `system/upkeep.md` exists in the instance and gained no row.

## Holes in the code
none.

The change's diff against `main` touches two files under the product, both test code at layer 2: `tests/integration/test_sigint_launch.py` (modified — the launched pytest gets `--basetemp` under the test's `tmp_path`, and the module docstring names the cause) and `tests/integration/test_sigint_launch_temp_root.py` (new — the measurement). No product module changed. Both files were read in full and their paths traced.

Threat classes applied, read off the NFDR § 2's four boundaries and the product's artifact class (a loopback web tool with a Python test suite):

- B-1 (the listener), B-2 (saved data), B-3 (typed text shown back): the change does not reach them — no code under `web/`, `persistence/`, `domain/`, `application/` or `main.py` changed.
- B-4 (setup / supply chain): no manifest or lock file moved; both lockfiles scanned clean above.
- OWASP A03 injection / A05 misconfiguration, as the sharpest corners for test code that starts processes: the only `/bin/sh -c` runs a constant string (`trap "" INT; exec "$@"`) with every argument passed positionally, never interpolated; both `subprocess.Popen` calls take list commands with no `shell=True`; every path handed to a child is pytest's own `tmp_path`; the one environment variable set (`PYTEST_DEBUG_TEMPROOT`) is test-controlled and trusted by the lens's exclusions; `os.killpg` targets only the session the test itself started (`start_new_session=True`). No untrusted input reaches either file.
- The agentic list (ASI) does not apply: the product holds no prompt, skill or tool grant.
- Semgrep and gitleaks produced no candidates for the sceptical pass.

The lens's own exclusion — "a file that only tests, or only runs tests" — also covers both files; the trace above was made regardless so that "none" reads as looked-at rather than skipped.

## Not checked
- The NFDR's dependency audit — it names none, so none ran (above).
- `uv lock --check --project .behave`, which QC-39 assigns to the `development-design` review of a change to `.behave/`; the change touches nothing under `.behave/`, so it was not owed here.
- Nothing else: both scanners ran to completion over every file in scope, and the suite was not run because no bump or hole fix needed proving.
