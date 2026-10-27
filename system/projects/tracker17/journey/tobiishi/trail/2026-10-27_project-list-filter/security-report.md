# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the product's NFDR names no dependency audit. QC-40 states it in so many words — "no audit command exists for this product: the Python packet names none and tracker17 installs none" (`products/tracker17/docs/nfdr.md` § 2, QC-40's *verified by*). No advisory was answered on this branch, so the pins in `tests/requirements.txt` stand as the owner's two feeds (Dependabot and the browser comparison at `development-design`) last left them. Detailed under *Dependency audit*.
- Nothing else. No hole was found at the confidence floor, no exception was written, no fix was made.

## Dependency audit
skipped — the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` § 2 QC-40 holds the supply-chain obligation and verifies it by "review at `development-design`", adding that "No command can measure a window, and no audit command exists for this product: the Python packet names none and tracker17 installs none". § 10's verification map projects the same row. Per the shared rules, no command was invented and none was run. The product's test dependencies are `mypy==2.4.0`, `playwright==1.63.0`, `pytest==9.1.1`, `ruff==0.16.10` (`pyproject.toml`), locked with everything they pull in by `tests/requirements.txt`. The change moved no pin and added no dependency.

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none | — | — | the audit did not run | — |

The one dated exception already in force — QC-40's browser exception for Chromium `153.0.8010.12` (NFDR RN-33), tracked in `system/upkeep.md` with a lapse date of 2026-11-07 — is the design review's, not this audit's; it was not touched.

## Exceptions and upkeep rows
none

## Holes in the code
none. The product is code that serves, stores and processes input (a loopback HTTP tracker — NFDR § 2 boundaries B-1 to B-4, § 3), so the OWASP Top 10:2025 list was applied, with Anthropic's five categories as its corners. The agentic list does not apply: the change adds no skill, prompt or launcher.

What was read: `git diff main...HEAD` over the product, then every touched module in full — `domain/filtering.py` (new), `domain/refusals.py`, `application/tracker.py`, `web/routes.py`, `web/pages.py`, `web/style.css`, `tests/timed_run.py` — and the paths traced from the new entry point: `parse_qs(keep_blank_values=True)` → `_filter_input` / `_carried_filters` → `filter_project_tasks` → `ProjectTaskList` → the page builders, and the redirect built by `_address(..., doseq=True)`.

Candidates examined and dropped, with the score:

- **B-3, typed values shown back (A05 / XSS).** Every raw filter value that reaches a page goes through the one `_escape` (`pages.py:363`): the select options via `_option` (`:544`, value and label both escaped, including a sent value no option offers), the date inputs (`:1137`), the retained attempts (`:1152`), every reason that echoes a value (`:1058–1077`), and the hidden carried pairs in every move form via `_hidden` (`:668`). The checkbox emits no raw value. The reversed-range reason prints parsed `date.isoformat()`. QC-36's one-function pattern is kept. Score 1 — not a hole.
- **Header injection through the redirect (A05).** `_redirect` builds `Location` with `urlencode(query, doseq=True)`, which percent-encodes CR and LF, so a carried filter value cannot break the header. The CSP header still rides every `_respond`, redirects included (QC-33/34). Score 1.
- **Cross-project read through `_move_view` (A01).** The move lookup now reaches any task by identity, but `_project_task` returns it only when `task.project_id == project.id` (`routes.py` diff, `_project_task`); a task of another project resolves to no interaction. The product has one operator on loopback (§ 3), so even the shown fields are the operator's own. Score 1.
- **State change on a malformed filter (A10, fail-open).** A list move whose carried filter is refused is redirected before any save or confirmation (`routes.py` `_move`, CP-405), and `project_task_list` saves nothing. Already covered by layer-3 tests asserting unchanged saved data. Not a hole.
- **Unbounded repeated keys / query size.** `parse_qs` carries no `max_num_fields`; a request may repeat a key many times. Denial of service and resource exhaustion are excluded by the lens. Dropped.
- **Label filter accepts any string.** It is compared, never executed or stored, and a non-matching label yields the empty state. No security impact; dropped.
- `tests/timed_run.py` only runs the product; excluded as test harness.

Nothing already on `main` that the trace passed through — the request check (QC-31/32), `_escape`, `_respond`, `_form` — showed a hole.

## Not checked
- The dependency audit: skipped, for the reason above. No advisory database was consulted and no pin was checked against one; QC-40 places that at the `development-design` review and in the owner's feeds.
- The suite was not run by this step: it is owed only to keep a major bump or a hole fix, and there was neither. The branch's last suite evidence is the code-integrity report's — 1,575 passed, `Environment: owners-mac — no CI`.
- `web/style.css` was read for completeness; a stylesheet carries no input path and was not assessed further.
