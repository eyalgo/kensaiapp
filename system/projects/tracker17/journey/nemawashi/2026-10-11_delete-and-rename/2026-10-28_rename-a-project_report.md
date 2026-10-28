# 宿場 Shukuba refine — `2026-10-28_rename-a-project`

*Unit `2026-10-28_rename-a-project`, sealed Tobiishi, reviewed 2026-10-28. Key named by the caller.
Station `2026-10-28_rename-a-project` (root). Seed `2026-10-11_delete-and-rename`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-28_rename-a-project` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1 | Considered row 2 |
| 4 | cut a seed | Principal PM | none — answered by `nemawashi-refine` after the seed's retire, which writes new product work onto the product's documents for `seeds-from-product-docs` to cut, and cuts work no document should state through `seeds-from-idea` | — | recommendation 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking · 5 change-local (verified claims read not run; beyond-request rules lack Locked Answers; CP-557/CP-559 have no named check; placement anchors in rules; work assigned to design) · 0 skill-general |
| flow findings | `flow_findings/development-design.md` | 0 blocking · 2 change-local (`rename_from` contract left conditional; no case-only collision row) |
| flow findings | `flow_findings/development-plan.md` | 0 blocking · 1 change-local (gates measured against an unrecorded red baseline) |
| flow findings | `flow_findings/development-content.md` | 0 blocking · 2 change-local (the "no heading" call omits UX-F10's reading; a typo) |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking · 2 change-local (layout.md:52 scoped to "this run"; tasks 1 and 3 have no per-rule discrimination) · 1 skill-general (`rule-discrimination-claim-unrun`, not the route's) |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`; added one normalized-length test, mutant-checked; 2384 passed. Observed: `_takes_focus` would miss `autofocus=""` — Considered row 6 |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM: dependency audit did not run, NFDR names none — Considered row 4 |
| developer's closing commit | `<a commit not in the public history>` | divergences: one monkeypatched harness test (kept by code-integrity, Calls made 1); a test renamed; harness escapes names not the sentence. Notes the People page's Your name section `.format` breaks on braces, "a follow-up for whoever owns People" — measured, recommendation 1 |
| deferred decisions | `deferred_decisions.md` | Deleting a project, and the slice's docstring bar, both "Owner: none — for shukuba-refine": both carried by `tracker17 · nemawashi · 2026-10-11_delete-and-rename` (line 19) |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — `git show -s --format=%B <a commit not in the public history> \| grep -c '^Deferred:'` → `0` |
| corrections owed | `tl_instruction.md` § TL Review Notes, *Corrections ride their file* | the timed run's docstrings, inside the change; no *Owed outside this change's reach* line |
| work handed on | `change_spec.md` § Out of Scope | deleting a project and the docstring bar → seed line 19; the other six lines only fence |

## Upstream

`git log --since=2026-10-28T00:00 --format='%h %s' -- products/tracker17/docs/` (the earlier moves since the seed's first commit, 2026-10-11T18:13:32+02:00, were read by the `2026-10-28_delete-a-task` refine): CONTENT v17 (`952932972`), SDD v13 (`cb9ef1445`), ADR-0012 and NFDR v17 (`d459f69d9`) — the folds of that refine's two companions. SDD v13 widens § 4 RT-11 to every pending confirmation (202, `no-store`) and adds S-7 *Command*'s deletion history clause (`products/tracker17/docs/SDD.md:L1064-L1071`) → Moves row 1. No live `*_open_issues.md` (`ls products/tracker17/docs/*_open_issues.md` → no matches).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null`. No open unit under `journey/tobiishi/`'s root (`ls` → `trail` only).

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a seed | `tracker17 · nemawashi · 2026-10-11_delete-and-rename` (line 19, divergence line 25) | S-7's sources moved after `delete-a-task` was walked: RT-11 now answers both deletions' pending confirmations 202 and S-7 asks for a deletion history test, and the product's task deletion confirmation still answers 200; `delete-a-project` is the slice's last station and builds the second confirmation through the same status | `products/tracker17/docs/SDD.md:L1064-L1071`; `products/tracker17/docs/adr/0012-pending-confirmation-answered-202-confirmed-action-pages-not-stored.md:L1-L9`; `products/tracker17/web/routes.py:L404-L426`, `L446-L455` (`_pending_status(None)` → 200 for a deletion state); `products/tracker17/tests/integration/test_delete_routes.py:L457` (asserts 200) | `a14511e42` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-28_rename-a-project` | Reached-when holds on all five items; the close is the Scrum Master's. `README.md` has one `## Status` line and `docs/what_left.md` exists, so `readme-status` is owed after it | scratch clone at `1eecb6c0e`, Python 3.11.9: `pytest products/tracker17/tests/` → `2384 passed`, exit 0 (items 2–4, e2e included); `pytest tests/e2e/test_rename_project.py` → `2 passed` (item 1); `python3 products/tracker17/tests/timed_run.py` → exit 0, `rename a project at 1000 tasks: 300.7 ms` (item 5); `tests/integration/test_rename_tracker.py` `test_rename_preserves_tasks_and_survives_restart` (FR-12); `grep -c '^## Status' products/tracker17/README.md` → `1` |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename` (line 19), `delete-a-project` | Walkable where it stands (shape 6): S-7's bar (`SDD.md:L1055-L1073`), EX-6, EX-13, RT-11, FR-13, FR-17 and AC-12 are defined; the project deletion, its confirmation, its tests, the 202 and the docstrings are the station's own work, on the existing confirmation (`web/pages.py` `confirm_strip`) and timed run. One refine re-aim (this run), under two | `products/tracker17/docs/SDD.md:L1055-L1073`; `grep -rn "def test.*delete_project\|delete_project" products/tracker17/web` → nothing yet |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename` (line 21) | Its QC-48 pointer `nfdr.md:L412-L414` lands on other text; a dated divergence record whose identifier still resolves, as the last refine found | `tracker17 · nemawashi · 2026-10-11_delete-and-rename` (line 21) |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already states there is no audit command; no companion item owed | `security-report.md` § Left for the PM; `products/tracker17/docs/nfdr.md` QC-40 *verified by* |
| the change-local flow findings and code-integrity's Calls made | Each ends with this unit — evidence, wording and coverage notes about its own artifacts; the monkeypatched harness test has an owner (the Tech Lead) and an "if reversed" in the report | `flow_findings/*.md`; `code-integrity-report.md` § Calls made |
| `_takes_focus` and `autofocus=""` | Form does not occur: no page writes it | `grep -rn 'autofocus=""' products/tracker17/web \| wc -l` → `0` |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Nothing in this unit or upstream touches its sources (SDD § 6 S-8) or route | upstream log above |

## Absent

The closing commit's `Deferred:` lines; an *Owed outside this change's reach* line; the halt report (a sealed unit produces none). No station in `shukuba/parked/`.
