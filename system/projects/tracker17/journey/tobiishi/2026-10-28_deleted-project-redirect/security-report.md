# Security report

Security: reported

## Why the run stopped
none

## Left for the PM
- The dependency audit did not run: the NFDR names no dependency audit (QC-40, *verified by:* "no audit command exists for this product: the Python packet names none and tracker17 installs none"), so no advisory was answered on this branch. Detailed under *Dependency audit*.

## Dependency audit
skipped — the NFDR names no dependency audit. `products/tracker17/docs/nfdr.md` QC-40 (§ 2 Security) holds the product's only supply-chain obligation, verified by review at `development-design`, and § 10 lists QC-40 among the review gates with no command row. No command was invented, nothing ran, and the exception record and upkeep register were not touched. The one standing exception the product carries — QC-40's dated exception for Chromium `153.0.8010.12` (RN-33; `system/upkeep.md`, lapse 2026-11-07) — is the owner's by hand, outside any audit, and this run neither reads nor renews it.

## Advisories
| Advisory | Dependency | Answer | What was done | Commit |
|---|---|---|---|---|
| none | — | — | the audit did not run | — |

## Exceptions and upkeep rows
none

## Holes in the code
none. The product serves and processes input over loopback (NFDR § 2, boundaries B-1 to B-4; § 3 "not applicable" for identity), so the OWASP Top 10:2025 was applied, with Anthropic's five categories, over the change's diff (`git diff main...HEAD` — `web/routes.py` `Site._add_task`, `Site._rename_project`, `Site._project_page`; `web/pages.py` `project_page`; nine test modules) and the paths traced from it.

- **Phase 1, context.** The request check (`Host`, `Sec-Fetch-Site`, QC-31/QC-32) runs before any route code; identities are read by `Site._identity` (`web/routes.py:402-407`, `int(digits)` or `None`); every redirect goes through `Site._redirect` → `_address` (`:1318-1319`), the one address builder (RT-8).
- **Phase 2, comparison.** The change replaces `_project_named_by` with `_identity` + `self._tracker.project(identity)` in the two submissions and answers a missing project with `_redirect(f"/projects/{identity}")` — the same guard and builder the deleted-task submissions and Delete project's presses already use. `project_page` gains a required keyword `task_count`, supplied from `listing.task_count` (the application's count); its one caller is `Site._project_page` (`:636`).
- **Phase 3, assessment.** The only outside data reaching the new code is the route's `<id>`, admitted by `[0-9]+` (`:70-74`, `:141-142`) and reduced to an `int` before it is written into `Location`, so no header or path injection is possible and the redirect is same-origin and relative (A01, A03, A10 — no path). Form values on a missing project never reach the application (CP-597) and nothing is saved (proved by the branch's redirect matrices). The count is an application integer rendered by the existing page code; no new HTML is built from typed text (A03/QC-36 unchanged).
- **Sceptical pass.** Candidates considered and dropped: open redirect (Location is a fixed-shape relative path from an int — not reachable, confidence of exploit 1); an action-time race between `project()` and the action (both answers are the same redirect, nothing saved — not a hole). Nothing scored 8 or above.

## Not checked
- The dependency audit: not run, the NFDR names none (above).
- The suite was not re-run by this step: nothing was fixed or bumped, so no fix needed proving. The code-integrity run of the same branch (`bdd24089d`) carries `Environment: owners-mac — no CI` and `2629 passed`.
