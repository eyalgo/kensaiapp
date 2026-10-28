# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit (`products/tracker17/docs/nfdr.md` QC-40, "no audit command exists for this product: the Python packet names none and tracker17 installs none"). Detailed under *Dependency audit*.

## Dependency audit
Skipped — the NFDR names no dependency audit. QC-40 (`products/tracker17/docs/nfdr.md` § 2, the *verified by* tail) states that no audit command exists for this product and places the advisory check at the `development-design` review and on the owner's Dependabot feed. No command was invented and no advisory was answered. The pins this branch ships are unchanged from `main` (`pyproject.toml` `[dependency-groups] dev`, `tests/requirements.txt` — neither is in the branch's diff). The one dated exception in force, Chromium `153.0.8010.12` under QC-40 / RN-33 (upkeep row, lapse 2026-11-07), was not touched: no audit reported it to this run.

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none | — | — | no audit ran | — |

## Exceptions and upkeep rows
none

## Holes in the code
none. The product serves and processes input on a loopback listener (NFDR § 2 B-1, B-3; § 3 not applicable — one operator), so the OWASP Top 10:2025 list was applied, with A01/A07, A05, A04, A08, A02/A09 and A06/A10 as the corners; the agentic list does not apply (no skills, prompts or launchers in the product). Traced, from the diff `main...HEAD`:

- **Two new address keys** `sort_field` and `sort_direction` (`web/routes.py` `_sort_input`, `_carried_sorts`): read only by their fixed names from `parse_qs(keep_blank_values=True)`; every value is kept raw and handed to `domain/sorting.py`, where `_validated_sort` admits only the closed `SortKey` / `SortDirection` vocabularies and refuses the rest typed (A05, A06 — no path to a query, a command, a path or a decision other than the sort order).
- **Reflection of a refused value** (`web/pages.py` `_sort_select`, `_sort_reason`, `_sort_attempt`): an unknown value is shown back as the selected option, inside the reason and in the attempt list; each passes through `_option` → `_escape` or `_escape` directly, the one escaping function QC-36 names. Proved by `tests/integration/test_sort_pages.py::test_titles_and_refused_tokens_are_escaped` (`<b>boom</b>` as both a single and a repeated value) (A03-style XSS, not a hole).
- **Hidden fields of the move forms** (`_carried_pairs` → `_hidden`): name and value both escaped; the names are fixed prefixes plus enum values.
- **Redirect after a move on a sorted list** (`routes.py` `_move`, `_redirect` → `_address`): the carried sort values go through `urlencode(doseq=True)`, so a value cannot break the `Location` header (no CRLF injection) and only the fixed carried keys are forwarded.
- **Ordering** (`domain/sorting.py` `_ordered`): keys are task fields of domain types (`Priority` rank table, `date`, `casefold` title, `id`); nothing user-supplied reaches a key function; no `eval`, deserialization, file, socket or clock (A08, QC-37, QC-43, QC-44 untouched).
- **`tests/timed_run.py`**: a test harness; excluded by the lens (a file that only runs tests).

Nothing already on `main` that the trace passes through (`_escape`, `_option`, `_hidden`, `_address`, the request check) was found open.

## Not checked
- The dependency audit — skipped as above.
- The suite was not run by this review: it made no fix and no bump, so there was nothing a run would be proving; the branch's last suite evidence is `code-integrity-report.md` (1846 passed).
