# 宿場 Shukuba refine — `2026-10-28_linked-counts`

*Unit `2026-10-28_linked-counts`, sealed Tobiishi, reviewed 2026-10-28. Key named by the caller.
Station `2026-10-28_linked-counts` (root). Seed `2026-10-11_project-summary`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-28_linked-counts` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 1 | recommendation 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking · 4 change-local (e2e claim read, not run; Fixture A has no zero against CP-525; Locked Answers f-1–f-4 at design altitude; CP-522 widening unrecorded in b-5) · 0 skill-general |
| flow findings | `flow_findings/development-design.md` | 0 blocking · 1 change-local (CP-517 match line named by no test row) — closed in code: `products/tracker17/tests/integration/test_summary_routes.py:L201-L202`, `L223-L224` assert it per link |
| flow findings | `flow_findings/development-plan.md` | 0 blocking · 2 change-local (gate "every command exits 0" against a listener-limited baseline; Beta's due date unfixed) |
| flow findings | `flow_findings/development-content.md` | no findings |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking · 3 change-local (not-delivered count was 3, not 0; e2e not re-run at the close; uncited no-CI exception) · 1 skill-general (`implementation-step1b-count-by-assertion`, raised as kaizen, not the route's) |
| code-integrity report | `code-integrity-report.md` | no issues in the code; tightened three instruction-named tests; e2e re-run, 93 passed; surfaced nothing it could not fix |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM: dependency audit did not run, NFDR names none — Considered row 4 |
| developer's closing commit | `<a commit not in the public history>` | divergence notes on the e2e count and the no-CI environment, both corrected by the implementation audit — change-local |
| deferred decisions | `deferred_decisions.md` | (1) unreadable-data page for the Summary and its lists — owned by `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (line 19), Considered row 3; (2) CP-525 fixture placement — a reading the unit settled and landed, no owner needed, Considered row 5 |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — `git show -s --format=%B <a commit not in the public history> \| grep -c '^Deferred:'` → `0` |
| corrections owed | `tl_instruction.md` | absent — no § Corrections owed while there (`grep -n 'Corrections owed' tl_instruction.md` prints nothing) |
| work handed on | `change_spec.md` § Out of Scope | unreadable-data page → `protect-saved-data` (Considered row 3); the other five lines only fence |

## Upstream

`git log --since=2026-10-11T18:13:32+02:00 -- products/tracker17/docs/` (seed first committed then): the moves the `2026-10-28_summary-page` refine already read (SDD v8–v12, CONTENT v16, UXD v10–v11, NFDR v16 with ADR-0011), plus one since, `4791167d6`, a `what_left.md` status line. None touches SDD § 6 S-6, SRS AC-13/AC-14, UXD UX-F6/UX-S5 or CONTENT's number-link name. No live `*_open_issues.md` under `products/tracker17/docs/` (find matches nothing).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null`. `system/logs/chain-change-tracker17-state.json` is this refine's own walk (`pending: refine`, key `2026-10-28_linked-counts`). No open unit under `journey/tobiishi/`'s root.

## Moves

None — no move was owed; see below.

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-28_linked-counts` | Reached-when holds on all five items; the close is the Scrum Master's. `README.md` has one `## Status` line and `docs/what_left.md` exists, so `readme-status` is owed after it | scratch clone at `54e7bcf44`: `pytest products/tracker17/tests/` → `2090 passed`, exit 0; `python3 products/tracker17/tests/timed_run.py` → exit 0, `open a project summary at 1000 tasks: 3.4 ms`; `products/tracker17/tests/integration/test_summary_routes.py:L205-L224` (items 1, 4), `L260`, `L290` (item 3), `L360` (AC-13, item 5); `products/tracker17/tests/integration/test_summary_pages.py:L131`, `L239` (items 1, 2); `products/tracker17/web/pages.py:L1499-L1519` |
| `tracker17 · nemawashi · 2026-10-11_project-summary` | Both station lines are walked once the close lands (line 17 ticked, line 18 this station), so the seed is fully walked; its retire is recommended, not made | `tracker17 · nemawashi · 2026-10-11_project-summary` (lines 17–18) |
| deferred decision 1, unreadable-data page | Still owned: the `unreadable-data-page` station's "every address shows the page" covers the Summary and the lists its counts open | `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (line 19) |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already states there is no audit command, as the earlier refines in this project found; no companion item owed | `security-report.md` § Left for the PM; `products/tracker17/docs/nfdr.md` QC-40 *verified by* |
| deferred decision 2 and the change-local flow findings | Each ends with this unit: fixture, wording, altitude and evidence notes about its own artifacts, corrected in its own branch or by its audits, none naming work that lost an owner | `flow_findings/*.md`; `code-integrity-report.md` § The finding |
| e2e suite not runnable in this run | `playwright` is not installed here, so the e2e layer was not re-measured; the station's bar does not name it, and code-integrity recorded 93 passed on the branch | scratch clone: `pytest products/tracker17/tests/e2e` → `ModuleNotFoundError: No module named 'playwright'`; `code-integrity-report.md` |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename`, `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Nothing in this unit touches their sources or routes | `git log --since=2026-10-11 -- products/tracker17/docs/` above |

## Absent

The closing commit's `Deferred:` lines; `tl_instruction.md` § Corrections owed while there; the halt report (a sealed unit produces none). No station in `shukuba/parked/`. No live companion under `products/tracker17/docs/`.
