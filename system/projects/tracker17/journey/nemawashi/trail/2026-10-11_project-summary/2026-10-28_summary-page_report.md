# 宿場 Shukuba refine — `2026-10-28_summary-page`

*Unit `2026-10-28_summary-page`, sealed Tobiishi, reviewed 2026-10-28. Key named by the caller.
Station `2026-10-28_summary-page` (root). Seed `2026-10-11_project-summary`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-28_summary-page` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1 | Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking · 4 change-local (unrun Verified Claims; spec altitude; e-1/e-2 widen the request without the sizing line saying so; CP-499 edges with no example) · 0 skill-general |
| flow findings | `flow_findings/development-design.md` | 0 blocking · 4 change-local (a "project list" wording slip; build order prescribed; T13 unrecorded; "strictly less than 1 second" vs "within 1 second") |
| flow findings | `flow_findings/development-plan.md` | 0 blocking · 2 change-local (shape-test change not a named behaviour; CP-512 words-not-colour unasserted) |
| flow findings | `flow_findings/development-content.md` | no findings |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking · 3 change-local (`__version__` divergence reason; rules not mutation-proven; `Suite: green` covers less than the card) · 1 skill-general (`implementation-rule-discrimination-unproven`, raised as kaizen, not the route's) |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`; added one cross-project overdue test, fixed none, surfaced nothing it could not fix |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM: dependency audit did not run, NFDR names none — Considered row 5 |
| developer's closing commit | `<a commit not in the public history>` | `Suite: green`; divergence on `conventions.md:148` (no `__version__` in `domain/summary.py`) — change-local |
| deferred decisions | `deferred_decisions.md` | (1) counts as links — owned by `tracker17 · nemawashi · 2026-10-11_project-summary` (line 18), Considered row 3; (2) unreadable-data page — owned by `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (line 19), Considered row 4 |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — `git show -s --format=%B <a commit not in the public history> \| grep '^Deferred:'` prints nothing |
| corrections owed | `tl_instruction.md` | absent — no § Corrections owed while there (`grep -n 'Corrections owed' tl_instruction.md` prints nothing) |
| work handed on | `change_spec.md` § Out of Scope | counts as links → `linked-counts` (Considered row 3); unreadable-data page → `protect-saved-data` (Considered row 4); the other four lines only fence |

## Upstream

`git log --since=2026-10-11T18:13:32+02:00 -- products/tracker17/docs/` (seed first committed then): SDD v8–v12, CONTENT v16, UXD v10–v11, NFDR v16 with ADR-0011, `what_left.md` status lines. None touches SDD § 6 S-6, SRS AC-13/AC-14, UXD UX-F6/UX-S5 or CONTENT's number-link name (`products/tracker17/docs/UXD.md:L248`, `L366`; `products/tracker17/docs/CONTENT.md:L373-L374`). No live `*_open_issues.md` under `products/tracker17/docs/` (glob matches nothing).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null`. No open unit under `journey/tobiishi/`'s root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a seed | `tracker17 · nemawashi · 2026-10-11_project-summary` (line 18) | The AC-13 agreement test and the timed summary landed with this unit, so `linked-counts` keeps them as checks that must still pass, not as new work | `change_spec.md` Locked Answers e-1, e-2; `products/tracker17/tests/integration/test_summary_routes.py:L76`; `products/tracker17/tests/timed_run.py:L140-L145` | `ffe34b859` |
| modify a station | `tracker17 · shukuba · 2026-10-28_summary-page` (lines 20, 22) | Repair-everywhere: its guardrail and **Not here** still gave the timed run and AC-13 test to the next station | same as above | `ffe34b859` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-28_summary-page` | Reached-when holds on all four items; the close is the Scrum Master's. `README.md` has one `## Status` line and `docs/what_left.md` exists, so `readme-status` is owed after it | scratch clone at `599dd0fbe`: `pytest products/tracker17/tests/` → `2046 passed`; `ls domain/summary.py` present; `tests/integration/test_summary_pages.py:L81`, `L127`; `tests/integration/test_task_pages.py:L145`; `tests/e2e/test_summary.py:L75-L92`; `web/pages.py:L1454` |
| `tracker17 · nemawashi · 2026-10-11_project-summary` item 2, `linked-counts` | Walkable where it stands (shape 6): the status, priority and overdue filters it links into exist, AC-14 is its own work, and the AC-13 test and timed run already pass. Re-aimed once by a refine (this run), under the owner's-act threshold | `products/tracker17/domain/filtering.py:L56-L74`; `products/tracker17/docs/SRS.md:L509-L513`; `python3 products/tracker17/tests/timed_run.py` → exit 0, `open a project summary at 1000 tasks: 3.3 ms` |
| deferred decision 1, counts as links | Still owned: `linked-counts` carries it | `tracker17 · nemawashi · 2026-10-11_project-summary` (line 18) |
| deferred decision 2, unreadable-data page | Still owned: the `unreadable-data-page` station carries it | `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (line 19) |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already states there is no audit command, as the earlier refines in this project found; no companion item owed | `security-report.md` § Left for the PM; `products/tracker17/docs/nfdr.md` QC-40 *verified by* |
| the change-local flow findings | Each ends with this unit: wording, altitude and evidence notes about its own artifacts, none naming work that has lost an owner. The CP-499 edges (specs) are untested cases with no measured failure, so they owe no carrier | `flow_findings/*.md`, lines 8–11 |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename`, `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Nothing in this unit touches their sources or routes | `git log --since=2026-10-11 -- products/tracker17/docs/` above |

## Absent

The closing commit's `Deferred:` lines; `tl_instruction.md` § Corrections owed while there; the halt report (a sealed unit produces none). No live companion under `products/tracker17/docs/`.
