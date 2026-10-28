# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit. QC-40 states it in so many
  words — "no audit command exists for this product: the Python packet names none and tracker17 installs
  none" (`products/tracker17/docs/nfdr.md` § 2, QC-40's *verified by*). QC-40 holds advisories to a
  `development-design` review and the owner's Dependabot feed instead, so no advisory was answered here
  and none could be. Detail under *Dependency audit* below.

Nothing else is left: no hole was found, no exception was written.

## Dependency audit
Skipped — the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` § 2 QC-40, *verified by*:
"No command can measure a window, and no audit command exists for this product: the Python packet names
none and tracker17 installs none." Per the shared rules, no command was invented and no tool reached for.
The pins on the branch are unchanged from `main`: the diff touches neither `products/tracker17/pyproject.toml`
nor its lock file (`git -C <code_worktree> diff --stat main...HEAD` lists no dependency file).

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none | — | — | the audit did not run (none named) | — |

## Exceptions and upkeep rows
none

## Holes in the code
none.

The product is **code that serves and processes input** (a loopback HTTP tracker, NFDR § 2 boundaries
B-1 to B-4); § 3 declares identity and authorization not applicable (one operator, loopback only). The
list applied was the OWASP Top 10:2025 through Anthropic's five categories: A01/A07 access and
authentication, A05 injection and path traversal, A04 cryptographic failures, A08 data integrity
(unsafe deserialization, `eval`), A02/A09 secrets and data in logs, A06/A10 fail-open checks. No
skill, prompt or launcher is in the change, so the agentic list did not apply.

Phases over the change's diff (`main...HEAD`, the non-test files `domain/summary.py`,
`domain/__init__.py`, `application/tracker.py`, `application/__init__.py`, `web/routes.py`,
`web/pages.py`, `web/style.css`):

- **Context.** The patterns the code keeps: every request passes `Site.handle`'s `Host` and
  `Sec-Fetch-Site` checks before routing (`web/routes.py:262-282`, QC-31/QC-32); every response carries
  the CSP header through `_respond` (`web/routes.py:129-130`, QC-33/QC-34); one function, `_escape`
  (`web/pages.py:381-383`), puts typed text into a page (QC-36); the clock is injected (QC-44).
- **Comparison.** The change adds one entry point — `GET /projects/[0-9]+/summary` in `ROUTES` and
  `SUMMARY_PATTERN` (`web/routes.py:71,110,336-338`). It reaches the tracker only through
  `_summary_page`, which goes through the same `handle` → `_route` → `_page` path as every page, so the
  request check and the CSP header apply with no new code. No new place where outside data arrives:
  the route reads the digits of the path only and ignores the query. No tool grant, no file, no socket,
  no secret.
- **Assessment.** Traced data: (1) the path digits → `_identity` (`web/routes.py:346-351`, an
  oversized value becomes `None` → the existing 404) → `Tracker.project_summary` → `summarize_project`,
  a pure read; (2) typed text shown back — the project name goes through `_escape` in the `<h1>` and
  through `_document`'s `_escape(title)` (`web/pages.py:401-407`), every row label (assignee names, the
  only typed text in the rows) goes through `_escape` in `_summary_group` (`web/pages.py:1463-1466`);
  status and priority labels are enum values and counts are integers; the two link addresses are built
  from the integer project id. `domain/summary.py` reads no clock, opens nothing, executes nothing
  (`git grep` for `pickle|marshal|shelve|eval(|exec(|subprocess|os.system` over the touched modules:
  no hit).

Sceptical pass: no candidate reached the floor of 8. The one hole already on `main` that this trace
passes through is none: the shared path (`handle`, `_respond`, `_escape`, `_identity`) keeps every guard
on the new route.

## Not checked
- The dependency audit — skipped, as above: the NFDR names none, so no advisory data exists for this run.
- The suite was not run by this step: nothing was fixed or bumped, so no run was owed (the skill runs the
  suite only to keep a major bump or a hole fix). The code-integrity step's run stands as the last one on
  the branch (`code-integrity-report.md`: `Integrity: pass`, 2046 passed).
