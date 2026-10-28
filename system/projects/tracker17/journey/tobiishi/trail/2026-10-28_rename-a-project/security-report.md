# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit (`products/tracker17/docs/nfdr.md` QC-40, *verified by*: "no audit command exists for this product: the Python packet names none and tracker17 installs none"). No advisory was answered on this branch; the dependency floor stays the `development-design` review QC-40 names. Detail under *Dependency audit*.

## Dependency audit
Skipped — the NFDR names no dependency audit. QC-40 (`docs/nfdr.md` § 2, B-4) is a review gate, verified at `development-design`, and its text states that no audit command exists for the product; § 10's verification map gives it no row. Under the rules (`senior_engineer_repair_dependencies.md` § *The audit command is the product's, not yours*) no command was invented and none ran. The pins (`pyproject.toml` `[dependency-groups] dev`, `tests/requirements.txt`) are unchanged by this change. The owner's dated exception RN-33 (Chromium `153.0.8010.12`, to 2026-11-07) stands in the NFDR and in `system/upkeep.md` as before; it is QC-40's, not an audit's, and this run neither renewed nor removed it.

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none — no audit ran | — | — | — | — |

## Exceptions and upkeep rows
none

## Holes in the code
none.

Artifact class: code that serves and processes input (a loopback web tracker) — the OWASP Top 10:2025 list was applied over the diff `main...HEAD` under `products/tracker17/` (`domain/projects.py`, `domain/__init__.py`, `application/tracker.py`, `application/__init__.py`, `web/pages.py`, `web/routes.py`), against the NFDR's boundaries B-1 (listener), B-2 (saved data) and B-3 (typed text shown back). No skill, prompt or launcher is in the change, so the agentic list did not apply.

Traced, and found to keep the product's own patterns:

- **A01 / A07, the new entry point** `POST /projects/{id}/rename` (`web/routes.py:135`, `:321`): in `ROUTES` as a `SUBMISSION`, so `Site.handle` (`:292`–`:308`) refuses a wrong `Host` and any `Sec-Fetch-Site` other than `same-origin` before `_submit` runs (QC-31, QC-32). The target project is fixed by the route's `[0-9]+`, read through `_identity` → `tracker.project`; a missing one answers the 404 page. `test_routes.py:311` enumerates `ROUTES` against `SAMPLE_ADDRESS`, which carries the rename route (`:279`), so the header and state assertions of QC-7 cover it.
- **A05, the typed name**: `_first(form, "name")` → `_line_feeds` → `Tracker.rename_project` → `domain.rename_project` (`domain/projects.py:88`), which applies `check_project_values` and `_check_name_available` — the same rules creation applies — before any state changes (QC-38). No path, command or query is built from it. The redirect carries it only through `_address` → `urlencode` (`web/routes.py:160`), which percent-encodes CR and LF, so the `Location` header cannot be split.
- **B-3 / XSS, the five new query keys** `rename_typed`, `rename_refused`, `rename_saved`, `rename_from`, `rename_failed` (`web/routes.py:756`–`:768`): `rename_refused` goes through `_closed(ProjectNameRefusal, …)` and an unknown code is `None`; `rename_failed` is compared to a constant; the three free-text values reach the page only through `_escape` (`html.escape(quote=True)`, `web/pages.py:442`) — in the field's `value="…"` (`:1781`), the completion line (`:1771`), the failure line (`:1768`) and `_name_reason`'s in-use reason (`:488`) — one function, as QC-36 requires.
- **A08 / A10**: `_takes_focus` (`web/pages.py:1726`) reads the page's own markup, never a request value; `_guarded` (`:1193`) catches the unexpected failure, leaves state as it was and answers the failure redirect, so the error path keeps the request check and the refusals the normal path keeps.
- **A02 / A09**: the one console write on failure (`_report_failure`) prints the typed project name and the error — no secret, credential or personal data (QC-41 holds: the change reads and writes none).
- **A04**: no cryptography, randomness or secret enters the change.

Sceptical pass: no candidate reached the floor of 8. Two were read and dropped under the exclusions — a backtracking regex in `_takes_focus` (denial of service, excluded) and the typed name on the console (log spoofing, excluded).

## Not checked
- The dependency audit — skipped, as above: the NFDR names none, so none ran.
- The suite was not run by this step: no bump was taken and no hole was fixed, so there was nothing to keep on a green run. The code-integrity step's run on this same head (`code-integrity-report.md`, 2384 passed) is the last recorded.
