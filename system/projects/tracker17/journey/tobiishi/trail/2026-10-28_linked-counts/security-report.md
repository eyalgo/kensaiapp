# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit. Its QC-40 says so in its own words — "no audit command exists for this product: the Python packet names none and tracker17 installs none" — and its § 10 map carries QC-40 as a review gate with no row. No advisory was answered on this branch; the pins in `products/tracker17/pyproject.toml` and `tests/requirements.txt` stand as `main` left them, under the owner's watch QC-40 describes (Dependabot and the browser-version comparison at `development-design`). Detailed under *Dependency audit*.

## Dependency audit
Skipped — the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` § 2 QC-40, *verified by:* "review at `development-design` … No command can measure a window, and no audit command exists for this product: the Python packet names none and tracker17 installs none"; § 10 *Verification map*, closing line: "QC-12, QC-25, QC-26, QC-27, QC-40, QC-41 and QC-60 are review gates and have no row." No command was invented in its place. The product has no exception record (`products/tracker17/checks/` does not exist) and the NFDR names no *Advisory exception record* line; none was created, since no advisory was read. The one dated exception in force, QC-40's browser exception (NFDR RN-33; `system/upkeep.md`, due 2026-11-07), is the owner's by-hand record and was not touched.

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none — no audit ran | — | — | — | — |

## Exceptions and upkeep rows
none

## Holes in the code
none.

**Scope read.** `git diff main...HEAD` on the change's branch: `products/tracker17/web/pages.py`, `web/style.css`, `tests/timed_run.py`, and the five test files (`tests/e2e/test_summary.py`, `tests/integration/test_pages.py`, `test_summary_pages.py`, `test_summary_routes.py`, `test_timed_run.py`). The test files, `tests/timed_run.py` among them (a harness under `tests/`), are the lens's "a file that only tests" exclusion and were read for what they prove, not for holes. `style.css` is static text with no value in it.

**Threat lists applied.** The product is a loopback web service that serves and processes input (NFDR § 2, boundaries B-1 to B-4; § 3, one operator, no identity). The OWASP Top 10:2025 list was applied with Anthropic's five categories as its corners: A01/A07 access control and authentication (not applicable — NFDR § 3, no user, role or login; the loopback and `Host`/`Sec-Fetch-Site` checks of QC-30 to QC-32 run before any code the change touched); A05 injection, path traversal; A04 cryptographic failures (no secret, QC-41); A08 code run from data; A02/A09 secrets or personal data in output or logs; A06/A10 a check that fails open. The product has no skills, prompts or launchers, so the agentic list does not apply.

**Phase 1, context.** One escape function puts every value into a page, `web/pages.py:382` `_escape` → `html.escape(value, quote=True)` (QC-36, SEC-4). Every value a request carries is handed as sent to a `domain` rule before use (QC-38): `web/routes.py:183` `_filter_input` keeps each `filter_*` value as a tuple of strings and `routes.py:519` passes it to `project_task_list`, which `domain/filtering.py` checks. The page policy of QC-34 allows no script.

**Phase 2, comparison.** The change adds no entry point, no route, no form, no request field and no query key: each new link is a GET of the project's existing Tasks address with one of the existing `filter_status`, `filter_priority` or `filter_overdue` keys (`pages.py` `_summary_cell`). The pattern the rest of the page keeps — a value enters only through `_escape` — is kept: both the `href` and the `aria-label` go through it.

**Phase 3, assessment — data traced into the new markup.** The `href` is built from `_project_address(project)` (`pages.py:1445`, `/projects/{project.id}`, and `Project.id` is `int`, `domain/projects.py:31`), a `FilterField` enum value, and either a `TaskStatus`/`Priority` enum value or the constant `OVERDUE_VALUE = "on"`; no typed text reaches it. The `aria-label` is a `_CountName` constant formatted with the `int` count. The visible text is the `int` count. The label cell is the pre-existing `_escape(row.label)`, unchanged for assignee names, the one typed value on the page. What the link's target does with its value is the existing filter path above, where an invalid value is refused by `domain` and changes nothing (QC-38), and where a zero count opens the list's no-match state (proved by the suite's `test_zero_links_on_populated_project_show_no_match` and the e2e click-through in `tests/e2e/test_summary.py`).

**Sceptical pass.** Candidates considered and scored: a value injected into the `href` or the `aria-label` — no attacker-controlled input reaches either (score 1); a new page state reachable from a count link that the request check would not cover — the link is a same-origin page navigation to an address the product already serves, and QC-31/QC-32 run before routing (score 1); a count link leaking typed data into a URL — only integers and enum constants are carried (score 1). Nothing reached the floor of 8, so nothing is fixed or reported. No hole already on `main` was met along the trace.

## Not checked
- The dependency audit, as above: the NFDR names none, so no advisory against the pinned test dependencies or the browser build was read by this run.
- The suite was not run by this step: no bump and no hole fix was made, and the suite is run only to keep one. The code-integrity step's run on this branch (`code-integrity-report.md`, 2090 passed) is the last recorded green.
