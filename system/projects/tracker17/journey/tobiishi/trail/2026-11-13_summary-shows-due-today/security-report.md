# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` § 2, QC-40, *verified by*, says in its own words "no audit command exists for this product: the Python packet names none and tracker17 installs none", and § 10 lists QC-40 among the entries that "are review gates and have no row". Detailed under `## Dependency audit`.
- Nothing else. No hole, no advisory, no exception; every scanner ran.

## Dependency audit
Skipped — the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` § 2 *Security*, QC-40 (B-4, setup), is the product's one supply-chain obligation, and its *verified by* is a review at `development-design`, not a command. No command was invented in its place. `osv-scanner` ran over the product's dependency sets as this skill's own run (below) and found nothing to answer.

## Scanners
- osv-scanner: 2.7.0 — found nothing
- Semgrep CE: 1.182.0 — found nothing
- gitleaks: 8.30.1 — found nothing

`osv-scanner` read the product's two dependency sets, the ones QC-39 names: `products/tracker17/uv.lock` (15 packages) and `products/tracker17/.behave/uv.lock` (16 packages), each by `--lockfile`, in the change's worktree at `817313a73`. Both exits 0; `normalise` returned an empty list for each. Semgrep CE ran with `p/default` over the product path and the change's one touched folder outside it, `system/projects/tracker17/journey/tobiishi/2026-11-13_summary-shows-due-today/`: 0 results, 0 errors, exit 0. `gitleaks` ran once over each of those two paths with redaction on: "no leaks found" for both, exit 0.

## Advisories
| Advisory | Dependency | Reported by | Answer | What was done | Commit |
|---|---|---|---|---|---|
| none | — | — | — | neither the audit (none named) nor osv-scanner reported one | — |

## Exceptions and upkeep rows
none. `system/upkeep.md` exists in the instance and holds no row; none was added.

## Holes in the code
none.

The change's product code is two files: `products/tracker17/domain/summary.py` (two fields on `ProjectSummary`, `today` and `due_today`, and the count in `summarize_project`) and `products/tracker17/web/pages.py` (the `Due on {date}` row in `summary_page`, with its label constant). The rest is test code — `tests/timed_run.py`'s expected rows, eight test modules under `tests/`, and QA's `.behave/` scenario, steps and two helpers (`tracker_program.py`, `browser_way_in.py`) — and the change's records under the journey.

Threat lists applied. tracker17 is code that serves, stores and processes input (a loopback web tracker, NFDR § 2 boundaries B-1 to B-4; § 3 names no identity or authorization), so the OWASP Top 10:2025 list was applied, with Anthropic's five categories as its corners. The agentic list (ASI01–ASI10) does not apply: the product holds no skill, prompt or launcher, and the change adds none.

Phase 1, context: the product's security model is QC-30 to QC-45 — loopback only, `Host` and `Sec-Fetch-Site` checks before any other `web` code, every value put into a page through `web/pages.py`'s one `_escape`, writes confined to `persistence/` under `data/`, sockets only in `web/`, no clock read outside `main.py`, no secrets (QC-41). Phase 2, comparison: the change adds no entry point, no place where outside data arrives, no file or socket use in product code, and no departure from a pattern the code keeps — the new row goes through the same `_SummaryRow` and `_summary_group` as the two rows beside it. Phase 3, assessment: the one new value shown on a page is the summary's date. It enters as `today`, read once from the clock `main.py` hands in (`application/tracker.py` `project_summary`), is carried on `ProjectSummary.today`, and is written into the label with `date.isoformat()` — ten fixed characters of digits and hyphens, never typed text — and the label is then escaped like every row header (`web/pages.py` `_summary_group`, `_escape(row.label)`). The count is an integer. No request data, saved data or typed text reaches either. The summary route and its request checks are unchanged (`web/routes.py` `_summary_page`). In the test code, `tracker_program.py` starts the tracker as a fixed command (`sys.executable main.py`) from a copy the test itself makes under `mktemp`, with no value from outside it; the Behave steps read dates from the machine's clock and fill them into the tracker's own form fields through a browser.

Sceptical pass: the only candidate classes — "a file that only tests, or only runs tests" for the `.behave/` and `tests/` changes, and an attack needing control of the machine's clock, which is the operator's environment — are exclusions the prompt keeps, and nothing in the diff reaches the floor of 8. Semgrep and `gitleaks` handed over no candidates.

## Not checked
none. The dependency audit was skipped because the NFDR names none, as `## Dependency audit` says; that is the item left for the PM, not a check this run could not make. No suite run was owed: no bump was taken and no hole was fixed.
