# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md`
  QC-40 says so in its own words — "no audit command exists for this product: the Python packet names
  none and tracker17 installs none" — so no advisory was answered on this branch. Detail under
  *Dependency audit*. The owner watches the pins by hand under QC-40 (Dependabot alerts and the
  browser-version comparison at each `development-design` review); the one dated exception in force,
  RN-33 for Chromium `153.0.8010.12`, lapses 2026-11-07 and already has its row in `system/upkeep.md`.

## Dependency audit
Skipped — the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` § 2 QC-40, *verified
by*: "No command can measure a window, and no audit command exists for this product: the Python packet
names none and tracker17 installs none". § 10's verification map carries no audit row. Nothing was run
in its place, and no command was invented. The product's pins (`pyproject.toml` dev group: mypy 2.4.0,
playwright 1.63.0, pytest 9.1.1, ruff 0.16.10) were not moved by this change.

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none | — | — | no audit ran (see above) | — |

## Exceptions and upkeep rows
none — no exception written, renewed or removed; no row added to `system/upkeep.md`.

## Holes in the code
none.

The product is a loopback HTTP service that stores and shows the operator's typed text, so the OWASP
Top 10:2025 list was applied; it ships no skill, prompt or launcher, so the agentic list does not
apply. The change's diff `main...2026-10-28_delete-a-project` under `products/tracker17/` was read in
full — `domain/projects.py`, `domain/tasks.py`, `domain/__init__.py`, `application/tracker.py`,
`application/__init__.py`, `web/routes.py`, `web/pages.py`, `web/style.css` — and traced through
the guards on `main` it passes through.

- **A01/A07, request origin (NFDR B-1, QC-31, QC-32):** the two new routes `POST /projects/<id>/delete`
  and `POST /projects/<id>/delete/confirm` are entered in `ROUTES` as `SUBMISSION`, so `Site.handle`
  refuses them before any code runs unless `Host` is the tracker's own and `Sec-Fetch-Site` is
  `same-origin`. The back-out is a GET that changes nothing. `handle` holds the one lock from the
  check to the response, so the lookup in `_delete_project` and `Tracker.delete_project` run under the
  same lock — no window between them.
- **A01, the target (CP-575, QC-38):** the project deleted is the one the path's `[0-9]+` names, read
  through `_identity` → `Tracker.project`; nothing from the form chooses it. The form's only values
  read are the filter and sort keys, through `_carried_filters` / `_carried_sorts`, which read a fixed
  key list. The domain refuses a missing project (`ProjectNotFound`) before any new state exists.
- **A05, header and address injection:** every redirect goes through `_address`, which `urlencode`s
  the query (the deleted project's name, the count, the carried values), so no newline or separator
  reaches the `Location` header. `missing` interpolates path digits only.
- **A03-adjacent XSS (B-3, QC-36):** the name shown on Projects (`_deleted_project_line`), the
  confirmation sentence and the failure line all pass through the one `_escape`; the hidden carried
  fields go through `_hidden`, which escapes name and value; `size` and `sentence_id` are escaped in
  `confirm_strip`. The e2e test `tests/e2e/test_delete_project.py` runs the whole path with the hostile
  name `<b>R&D "x"</b>`. `_without_focus` edits tags only (`_TAG` requires `<` followed by a letter;
  escaped text holds neither `<` nor a bare `"`), and its quoted-value alternation leaves attribute
  values intact, so a typed value can neither hide nor create an `autofocus`.
- **A10, exceptional conditions:** `_project_deletion` admits only an ASCII canonical decimal and
  catches the digit-limit `ValueError` (tested by the integrity step's added case); the save failure
  path goes through `_guarded`, the product's one catch site, and answers the failure page with the
  state unchanged.
- **A09, logging:** `_report_failure` writes the project's name and the error type to the console on a
  failed save — no secret, no credential, no personal data beyond what the operator typed on their own
  machine; QC-41 holds, the change reads and writes no secret.
- **A08:** no deserialization, `eval` or `exec` is added; persistence is unchanged.

Candidates read a second time and dropped below the floor: a crafted link that opens a project's
confirmation (`?project_delete_confirm`) or shows a completion line naming a project that was never
deleted — both are text on the operator's own page, escaped, change nothing, and follow the pattern the
task deletion already has on `main` (confidence 2); the console line on a failed save (no sensitive
data, excluded).

No fix was made, so the suite was not run by this step; the integrity step's run of the card's command
(2556 passed, `Environment: owners-mac — no CI`) stands as the branch's last green.

## Not checked
- The dependency audit, as above: the NFDR names none, so no advisory database was consulted and no
  advisory can be said to be absent.
- `products/tracker17/tests/`, `tests/timed_run.py` and the test fixtures: files that only test are
  outside the lens.
