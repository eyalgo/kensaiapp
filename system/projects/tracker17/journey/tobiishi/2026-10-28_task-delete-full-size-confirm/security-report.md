# Security report

Security: reported

**Change:** `tracker17 · tobiishi · 2026-10-28_task-delete-full-size-confirm` — Delete task's first press and its confirmation take the full-size height.
**Reviewed at:** `ef7c9b377` (the code-integrity pass), diff `main...HEAD` over `products/tracker17/`.

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit — `products/tracker17/docs/nfdr.md` QC-40, *verified by:* "no audit command exists for this product: the Python packet names none and tracker17 installs none". No advisory was answered on this branch. Detail under *Dependency audit*.
- The one dated exception in force (RN-33, the Chromium build under QC-40, lapsing 2026-11-07) is the owner's and already has its row in `system/upkeep.md`; this run neither wrote nor renewed it, since no audit reported anything to answer.

## Dependency audit
Skipped — the NFDR names no dependency audit. QC-40 (`products/tracker17/docs/nfdr.md` § 2, *verified by:*) states it outright: "No command can measure a window, and no audit command exists for this product: the Python packet names none and tracker17 installs none." QC-40's check is a review at `development-design`, which this change passed before the plan. No command was invented and none ran.

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none | — | — | no audit ran | — |

## Exceptions and upkeep rows
none

## Holes in the code
none.

**Threat lists applied.** The product serves and processes input from a browser (`web`, a loopback HTTP listener), so the OWASP Top 10:2025 list was applied, through the NFDR's four boundaries (B-1 the listener, B-2 saved data, B-3 typed text shown back, B-4 setup). The product carries no skills, prompts or launchers, so the agentic list does not apply.

**Phase 1 — context.** Pages are built by one escaping function (QC-36): `confirm_strip` escapes `size`, `sentence_id` and `sentence` itself (`web/pages.py:797`, "Every value is escaped here, once"; `:801–803`), and `_escape` is the one function. Every response carries a CSP with no script (QC-33, QC-34). Request origin is checked before any route runs (QC-31, QC-32).

**Phase 2 — comparison.** The production diff is two lines in `web/pages.py` and the stylesheet:
- `_delete_strip` (`web/pages.py:861`): `size=TRIGGER_SIZE` → `size=FULL_SIZE`. Both are module constants (`"row-control"`, `"control"`) and reach the page through `_escape(size)` into a class name. No new entry point, no new place where outside data arrives.
- `_delete_section` (`web/pages.py:890`): the first press's class `delete-button` → `button-secondary`, a literal in the template. The button's label stays `_escape(DELETE_LABEL)`, a constant.
- `web/style.css`: the `button.delete-button` selector and its hover rule removed; comments re-worded. No `url()`, no `@import`, nothing that loads.
No departure from the patterns the rest of `web` keeps.

**Phase 3 — assessment.** Data traced through the two touched functions: `task.id` is `int` (`domain/tasks.py:81`) and lands in `DELETE_ADDRESS.format(...)` and `DELETE_CONFIRM_ADDRESS.format(...)`; `task.title` (B-3, typed text) reaches the page only through `_escape` — in `confirm_strip` for the sentence (`:803`) and in `_delete_section` for the failure line (`:881`). Both paths are already on `main` and the change passes through them unaltered. Nothing in the diff reads a request value, opens a file, runs a command, or builds HTML from a typed value outside `_escape`.

**Sceptical pass.** No candidate reached the floor. The test files (`tests/e2e/test_delete_task.py`, `test_delete_project.py`) drive a browser with fixed JS and a fixed literal title; a file that only tests is excluded by the lens.

## Not checked
- The dependency set: no audit is named by the NFDR, so no advisory check ran (above).
- The suite was not re-run by this step: no bump and no hole fix was made, so there was nothing to keep on a green run. The code-integrity pass at `ef7c9b377` holds (card suite 2629 passed, e2e 121 passed).
