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

Nothing else is left: no hole was found, no exception was written, no fix was made.

## Dependency audit
Skipped — the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` § 2 QC-40, *verified by*:
"No command can measure a window, and no audit command exists for this product: the Python packet names
none and tracker17 installs none." Per the shared rules, no command was invented and no tool reached for.
The pins on the branch are unchanged from `main`: the diff touches neither `products/tracker17/pyproject.toml`
nor a lock file (`git -C <code_worktree> diff --stat main...HEAD` lists no dependency file; the 22 files it
lists are five product modules, one stylesheet, eleven test files and five change records).

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

What was traced, file by file, from where data enters to where it is used:

- `web/routes.py` — two new `POST` routes, `/tasks/<id>/delete` and `/tasks/<id>/delete/confirm`,
  both registered as `SUBMISSION` in `ROUTES`, so `Site.handle` refuses them before any handler runs
  unless `Host` is the tracker's own and `Sec-Fetch-Site` is `same-origin` (`routes.py:270-289`,
  QC-31/QC-32). The target task comes from the path digits only, through `_identity`, which answers
  404 on digits Python cannot read as an int; nothing in the form body chooses the task
  (`_delete_task`, `routes.py:966-998`). The opening press reads the task and saves nothing; the
  confirming press runs `Tracker.delete_task` inside `_guarded`, so a saver failure leaves the state
  as it was (QC-56) and the error goes to the console through the one reporting site (OB-3). The
  removed task's title travels in the landing redirect's query through `_address`, which `urlencode`s
  every value (`routes.py:141-150`, RT-8). The page reads `deleted_task`, `delete_confirm`,
  `delete_failed` and `delete_back` from the query by presence or first value only.
- `web/pages.py` — every value the change puts into a page goes through `_escape` (`html.escape`,
  `quote=True`, SEC-4): the confirmation sentence via `confirm_strip`, which escapes its sentence
  once (`pages.py:741`); the failure line and the deleted line via `_escape` directly
  (`pages.py:820`, `pages.py:1737`); the form actions carry only `task.id`, an int. No new HTML
  escape hatch, no attribute built from a typed value.
- `domain/tasks.py` and `application/tracker.py` — pure state transforms: `delete_task` refuses a
  task no state holds before any new state exists, filters the tuple, and keeps both counters so the
  identity is never reissued; the application saves before publishing, so the on-disk state is
  never ahead of or behind the shown one. No file, socket, clock or console reached (QC-42 to
  QC-45 hold; the change adds no import).

Candidates read a second time and dropped below the floor of 8:

- The deleted line's title is read back from the landing address (`?deleted_task=<title>`), so any
  same-origin page request can show "You deleted '<text>'" for text no deletion produced. The value
  is escaped as text, the page policy runs no script (QC-34), a cross-site or same-site navigation
  is refused before the page builds (QC-32), and no state changes. A reflected, escaped string with
  no state effect on a loopback-only single-operator product: confidence 2, not a hole.
- The removed task's title is written to the console in `_guarded`'s failure message. A task title is
  the operator's own data on their own machine, not a secret or a credential (QC-41); logging that
  exposes nothing sensitive is an exclusion. Not a hole.
- A `POST /tasks/<id>/delete/confirm` from a local program that forges `Host` and `Sec-Fetch-Site`
  deletes the task without a confirmation page. NFDR § 3 states this caller is already inside the
  machine and accepts it by design; it is the product's declared boundary, not the change's hole.

## Not checked
- The dependency audit: none is named (above).
- The browser-level end-to-end tests (`tests/e2e/test_delete_task.py`) were not run by this step;
  no fix was made, so no suite run was owed (the integrity step's run stands as the branch's last
  green: 2273 passed, `code-integrity-report.md`).
