# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit. `docs/nfdr.md` § 2, QC-40, *verified by*, says in its own words "no audit command exists for this product: the Python packet names none and tracker17 installs none", and § 10's row for QC-40 reads "review gates and have no row". Detailed under `## Dependency audit`.
- Nothing else. No hole, no advisory, no exception, every scanner ran.

## Dependency audit
Skipped — the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` § 2 *Security*, QC-40 (B-4, setup), holds the product's one supply-chain obligation, and its *verified by* is a review at `development-design`, not a command: "No command can measure a window, and no audit command exists for this product: the Python packet names none and tracker17 installs none". § 10 *Verification map* lists QC-40 among the entries that "are review gates and have no row". No command was invented in its place. `osv-scanner` ran over the product's dependency sets as this skill's own run (below), and found nothing to answer.

## Scanners
- osv-scanner: 2.7.0 — found nothing
- Semgrep CE: 1.182.0 — found nothing
- gitleaks: 8.30.1 — found nothing

`osv-scanner` read the product's two dependency sets, the ones QC-39 names: `products/tracker17/uv.lock` (15 packages) and `products/tracker17/.behave/uv.lock` (16 packages), each by `--lockfile`, in the change's worktree. Exit 0; `normalise` returned an empty list. Semgrep CE ran with `p/default` over the product path and the change's one touched folder outside it, `system/projects/tracker17/journey/tobiishi/2026-11-13_walk-skips-by-name/`: 0 results, 0 errors, exit 0. `gitleaks` ran once over each of those two paths with redaction on: "no leaks found" for both, exit 0.

## Advisories
| Advisory | Dependency | Reported by | Answer | What was done | Commit |
|---|---|---|---|---|---|
| none | — | — | — | neither the audit (none named) nor osv-scanner reported one | — |

## Exceptions and upkeep rows
none. `system/upkeep.md` exists in the instance and holds no row; none was added.

## Holes in the code
none.

The change is two files of test code and nothing else: `products/tracker17/tests/conftest.py` (`SourceWalk._all` and its two skip constants, plus two docstrings) and the new `products/tracker17/tests/architecture/test_source_walk.py` (`git diff main...HEAD -- products/tracker17/`). No product module under `domain/`, `application/`, `persistence/`, `web/`, `main.py` or `errors.py` changes, and no file under `.behave/`.

Threat lists applied. tracker17 is code that serves, stores and processes input (a loopback web tracker, NFDR § 2 boundaries B-1 to B-4; § 3 names no identity or authorization), so the OWASP Top 10:2025 list was applied, with Anthropic's five categories as its corners. The agentic list (ASI01–ASI10) does not apply: the product holds no skill, prompt or launcher, and the change adds none.

Phase 1, context: the product's security model is QC-30 to QC-45 — loopback only, `Host` and `Sec-Fetch-Site` checks, writes confined to `persistence/` under `data/`, sockets only in `web/`, no secrets (QC-41). Phase 2, comparison: the change adds no entry point, no place where outside data arrives, no tool grant and no departure from a pattern the code keeps; it narrows what the layer-6 walk leaves out, so the architecture tests now see more of the tree, never less. Phase 3, assessment: `SourceWalk._all` takes a root path from the test (`tmp_path` or the product root), lists `*.py` under it with `rglob`, and parses each as a syntax tree; it runs no file, writes nothing and reads nothing outside the root it was handed. The data it reads is the product's own committed source or files the test itself wrote. No path from attacker data to a query, a command, a path, a decision or a model instruction exists in the diff.

Sceptical pass: the one candidate class — "a file that only tests, or only runs tests" — is an exclusion the prompt keeps, and nothing in the diff reaches the floor of 8. Semgrep and `gitleaks` handed over no candidates.

## Not checked
none. The dependency audit was skipped because the NFDR names none, as `## Dependency audit` says; that is the item left for the PM, not a check this run could not make. No suite run was owed: no bump was taken and no hole was fixed.
