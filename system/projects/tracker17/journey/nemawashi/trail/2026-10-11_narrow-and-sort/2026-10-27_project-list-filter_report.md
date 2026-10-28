# 宿場 Shukuba refine — `2026-10-27_project-list-filter`

*Unit `2026-10-27_project-list-filter`, sealed Tobiishi, reviewed 2026-10-27.
Station `project-list-filter` (root). Seed `2026-10-11_narrow-and-sort`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves rows 1, 2 |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-27_project-list-filter` | — | Considered row 1 |
| 3 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 2 | Considered row 1 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1, 2 | Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking; 4 change-local (rule altitude, test shape in rules, blank "no value" unstated, CP-423 probe narrow); 0 skill-general |
| flow findings | `flow_findings/development-design.md` | 0 blocking; 4 change-local: GET Apply not set against ADR-0006/QC-7 (became Moves rows 1–2), empty Overdue accepted, two untested spec branches, no bound on carried address size (Considered row 5) |
| flow findings | `flow_findings/development-plan.md` | 0 blocking; 4 change-local (T11 unmapped, owner-added confirmation requirement, unnamed test file, task headers name `domain/filtering.py`) |
| flow findings | `flow_findings/development-content.md` | 0 blocking; 1 change-local: "Clear" used with no Wording decision (Considered row 7) |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking; 4 change-local evidence findings on the closing notes (rule discrimination, four renamed cases, mypy clause, garbled Step 1b count) |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`, 1,575 green; added one test, strengthened one; three calls made, none left unfixed (call 1 is Considered row 6) |
| security report | `security-report.md` | `Security: reported`. § Left for the PM: (1) dependency audit did not run, NFDR names none — Considered row 8; (2) "Nothing else" |
| developer's closing commit | `<a commit not in the public history>` | divergences: Python 3.11 against the packet's 3.13 floor, and `tests/e2e/test_moves.py` outside the layout, both with reasons |
| deferred decisions | `deferred_decisions.md` | three record gaps, each "Owner: none — for shukuba-refine": sorting, All tasks, the summary's overdue agreement and links — all carried (Considered rows 3, 4) |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — `git show -s --format=%B <a commit not in the public history> \| grep '^Deferred:'` prints nothing |
| corrections owed | `tl_instruction.md` | absent — no § Corrections owed while there (`grep -n -i 'Corrections owed'` prints nothing) |
| work handed on | `change_spec.md` § Out of Scope | sorting → seed line 2; All tasks → seed line 3; summary agreement and links → `tracker17 · nemawashi · 2026-10-11_project-summary` (line 18); the rest only fences (multi-value fields, add-form answers, remembering choices, wording, looks) |

## Upstream

`git log --since=2026-10-11T18:13:32+02:00 -- products/tracker17/docs/` lists 30+ commits, 2026-10-20 to
2026-10-21: UXD v7–v9, CONTENT v12–v15, DESIGN v4, SDD v11, ADR-0010 and NFDR v14–v15 — the move-refusal,
confirmation and history-admission work of `tracker17 · nemawashi · 2026-10-07_status-moves`. Searched
those diffs for filter, sort, S-5, UX-F5, FR-36, R-89 to R-93: the only filter-bearing change is UXD
UX-S4's added "A refusal reached by an address and no control sits beside the task's status in its row
(UX-F4)" (`<a commit not in the public history>`), which the sealed unit was built after. No seed or station source moved against
the route.

Live companions before this run: none (`ls products/tracker17/docs/*_open_issues.md` matches nothing).
After it: `SDD_open_issues.md` and `architecture_open_issues.md`, each one item (Moves rows 1, 2).

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: settled`, `pending: null` — no product chain in
flight. No unit is open at `journey/tobiishi/`'s root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| raise a companion item | `products/tracker17/docs/SDD_open_issues.md` § 5.1 (opened) | RT-8 says every submission is answered by a redirect, and the project page's GET filter form is answered with the page; RT-8 never says a GET form is not a submission, and sort and All tasks add more such forms | `products/tracker17/docs/SDD.md:L330-L332`; `products/tracker17/web/pages.py:L1189` (`<form method="get"`); `products/tracker17/tests/integration/test_routes.py:L1090-L1093`; design flow finding 1 | `66837fe34` |
| raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1 (opened) | ADR-0006 and NFDR QC-7 carry the same sentence, QC-7's *verified by* asserting a redirect for each submission | `products/tracker17/docs/adr/0006-last-action-travels-in-the-page-address.md:L19-L20`; `products/tracker17/docs/nfdr.md:L73-L78`; the same product site | `632123a1c` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-27_project-list-filter` | Reached-when holds now on all six lines; the close is the Scrum Master's, owed | `ls products/tracker17/domain/filtering.py` → present; fresh clone at `819f5b37b`: `pytest products/tracker17/tests/` → `1575 passed`, exit 0; `python3 products/tracker17/tests/timed_run.py` → `filter total at 1000 tasks: 6.5 ms`, exit 0; lines 2–4 by `test_filter_routes.py:L48,L56,L67`, `test_filter_pages.py:L162`, `test_filter_move_routes.py:L193,L227`, `test_filter_tracker.py:L169` |
| `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` (line 18), `project-list-sort` | Next unticked station, reachable where it stands (shape 6): every thing its bar requires exists now or is its own work | SRS FR-36 and AC-14 (`products/tracker17/docs/SRS.md:L240-L243,L513-L518`), FDR R-89 to R-93 (`products/tracker17/docs/fdr.md:L283-L293`): creation time exists (`products/tracker17/domain/tasks.py:L80`, `created_at`); `domain/sorting.py` missing, the station's own; Apply, Clear and the address landed by this unit; no refine has re-aimed it |
| `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` (lines 18, 19) | Deferred sorting and All tasks keep their owners: the seed's own next two lines | `deferred_decisions.md` entries 1, 2; `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` (line 18), (line 19) |
| `tracker17 · nemawashi · 2026-10-11_project-summary` (line 18) | Deferred summary overdue agreement and links already carried by `linked-counts` | `deferred_decisions.md` entry 3; `tracker17 · nemawashi · 2026-10-11_project-summary` (line 18) |
| `products/tracker17/docs/adr/0006-last-action-travels-in-the-page-address.md` (L53), size bound on carried filter values | Non-occurrence: no request over the 65,536-byte line limit was measured; the form could occur and does not | design flow finding 4; the unit's record and this run's suite (`1575 passed`) show no failing case |
| `products/tracker17/docs/SRS.md` / `change_spec.md` CP-409 example | Integrity call 1 (off-list confirmation shows nothing) is change-local and the rules and design are met as written; no failure measured | `code-integrity-report.md` § Calls made, 1 |
| `products/tracker17/docs/CONTENT.md` § Terminology, "Clear" | CONTENT.md's own § Empty example fixes "Clear" for resetting a filter; no fact is false, a row would be improvement only | `flow_findings/development-content.md` finding 1 |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already states there is no audit command, so no companion item is owed | `security-report.md` § Left for the PM, line 1; `products/tracker17/docs/nfdr.md` QC-40 *verified by* |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename`, `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Nothing in the unit or upstream touches their stations | `grep -n -i 'filter\|sort'` on both seeds matches nothing on a station line |
| remaining specs, plan and implementation flow findings | Change-local, about this unit's own artifacts; they end with it and name no unowned work | the flow findings files above |

## Absent

The closing commit's `Deferred:` lines and `tl_instruction.md` § Corrections owed while there — see
## Read. The halt report, not produced by a sealed unit.
