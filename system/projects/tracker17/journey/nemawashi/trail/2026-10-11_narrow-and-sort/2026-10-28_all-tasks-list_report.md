# 宿場 Shukuba refine — `2026-10-28_all-tasks-list`

*Unit `2026-10-28_all-tasks-list`, sealed Tobiishi, reviewed 2026-10-28; key named by the caller.
Station `all-tasks-list` (root). Seed `2026-10-11_narrow-and-sort`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-28_all-tasks-list` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves rows 1, 2 |
| 4 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 1 | recommendation 1 |
| 5 | cut a seed | Principal PM | none — answered by `nemawashi-refine` after the seed's retire, which writes new product work onto the product's documents for `seeds-from-product-docs` to cut, and cuts work no document should state through `seeds-from-idea` | 4 | recommendation 2 |

## Read

All under `tracker17 · tobiishi · 2026-10-28_all-tasks-list`.

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking; 4 change-local (Verified Claims read not run; the request's grep done-when unrecorded; CP-469's created-time clause against its example; CP-483/487 at test altitude); 0 skill-general |
| flow findings | `flow_findings/development-design.md` | clean |
| flow findings | `flow_findings/development-plan.md` | 0 blocking; 4 change-local (CP-470 open-at-start and CP-473 Clear defaults unasserted; shown choices unnamed; gate baseline unstated; docs-unchanged gate unrecorded) |
| flow findings | `flow_findings/development-content.md` | 0 blocking; 2 change-local: the in-row refusal reads "is" on All tasks and "has changed to" on a project's list (recommendation 2); the move buttons' accessible name collides for same-titled tasks (Moves row 2) |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking; 5 change-local, all about the closing commit's own evidence wording (gate environment, `__version__`, an undercount, rule discrimination for tasks 1, 2, 4, gates re-run on the final tree) |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`, 1964 passed; four tests added, no code changed; three calls (FR-31 test shape, CP-481 "adds", CP-459's unreadable-data page) — Considered rows 6, 7 |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM: (1) dependency audit did not run, NFDR names none — Considered row 5; (2) RN-33's browser-build exception lapses 2026-11-07 and already has its `system/upkeep.md` row — Considered row 5 |
| developer's closing commit | `<a commit not in the public history>` | divergences: Python 3.11 against the packet's 3.13 floor; `list_all_tasks` added to `domain/tasks.py`; the two refusal wordings by destination; four instruction cases not delivered (400% zoom not run, no unreadable-data page, T17 samples routed elsewhere, no new cases in five files) |
| deferred decisions | `deferred_decisions.md` | (1) the project summary and its links — owned by `tracker17 · nemawashi · 2026-10-11_project-summary`, Considered row 3; (2) CP-475's row location for an excluded final task, set aside — the UXD states no place for it, Moves row 1 |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — `git show -s --format=%B <a commit not in the public history> \| grep '^Deferred:'` prints nothing |
| corrections owed | `tl_instruction.md` § Corrections owed while there | absent — `grep -n -i 'corrections owed\|Owed outside' tl_instruction.md` prints nothing |
| work handed on | `change_spec.md` § Out of Scope | the summary and its links → `tracker17 · nemawashi · 2026-10-11_project-summary` (lines 17, 18); renaming and deleting → `tracker17 · nemawashi · 2026-10-11_delete-and-rename`; the address form, wording and looks went to this unit's own design and content stages; the rest only fences (summary across projects, add-task on All tasks, multi-value filters, filter and sort rules, remembering choices, timed actions) |

## Upstream

`git log --since=2026-10-11T18:13:32+02:00 --name-status -- products/tracker17/docs/` (the seed's first
commit). Since the previous refine on this seed (`tracker17 · nemawashi · 2026-10-11_narrow-and-sort`,
report for `2026-10-27_project-list-sort`), one commit: `a23407d94`, `docs/what_left.md` (README status).
No definition document moved.

Live companions before this run: none (`find products/tracker17/docs -name '*_open_issues.md' -not -path '*/trail/*'` printed nothing). This run opened two — Moves rows 1, 2.

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null` — no product chain in
flight. `chain-change-tracker17-state.json` is pending only on this refine step. No unit open at
`journey/tobiishi/`'s root (`ls` shows only `trail/`).

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| raise a companion item | `products/tracker17/docs/UXD_open_issues.md` § 3.1 | UX-S4 puts a refusal reached by an address in the task's row, and a status or Overdue filter can leave that final task with no row; the product shows it above the results, which the UXD never describes | `products/tracker17/docs/UXD.md:L186-L193,L337,L340`; `products/tracker17/web/pages.py:L896-L914`; `tests/integration/test_filter_move_routes.py:L755`; `deferred_decisions.md` entry 2 | `3a4de0b27` |
| raise a companion item | `products/tracker17/docs/CONTENT_open_issues.md` § 3.1 | § Accessibility of text names a task by its title in a control's accessible name, titles need not be unique, so two move buttons for different tasks share one name | `products/tracker17/docs/CONTENT.md:L336-L342`; `products/tracker17/docs/fdr.md:L148` (R-40); `products/tracker17/web/pages.py:L676,L769,L979`; `flow_findings/development-content.md` finding 2 | `f7ee9a5f2` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-28_all-tasks-list` | Reached-when holds on all six lines now; the close is the Scrum Master's, owed. It is the seed's last line, so the seed is fully walked once it closes | fresh clone at `9f74b3d50`: `grep -rn -i 'all tasks' products/tracker17/web` matches `web/pages.py:L413` (header link); `pytest products/tracker17/tests/` → `1964 passed`, exit 0; `python3 products/tracker17/tests/timed_run.py` → `filter total at 1000 tasks: 6.9 ms`, `sort total at 1000 tasks: 14.6 ms`, exit 0; lines 1–5 by `tests/integration/test_pages.py:L388` (both not-found forms), `tests/integration/test_sort_pages.py:L418` (empty state), `tests/integration/test_filter_move_routes.py:L471,L707` (moves return to All tasks; a moved task leaves a filtered selection), `tests/unit/test_filtering.py:L703`, `tests/e2e/test_filters.py:L253`; empty-state text at `web/pages.py:L1510` |
| `tracker17 · nemawashi · 2026-10-11_narrow-and-sort` | Every station line is ticked or is the station whose close is owed; no `Deferred:` line to carry, so no line is added. Retire recommended | the seed's checklist (lines 17–19); recommendation 1 |
| `tracker17 · nemawashi · 2026-10-11_project-summary` (lines 17, 18) | Deferred entry 1 and Out of Scope's summary line keep their owner | `deferred_decisions.md` entry 1; `change_spec.md` § Out of Scope |
| `products/tracker17/web/pages.py` `_CHANGED`, a project's list and the task page | The in-row refusal still says "has changed to", which `CONTENT.md` RN-26 and RN-27 say the product's line must not; CONTENT already states the rule, so this is work, not a document gap — recommendation 2 | `products/tracker17/web/pages.py:L804-L808`; `products/tracker17/docs/CONTENT.md:L558-L559`; `change_text.md` § Wording decisions, first entry |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit; RN-33 exception | The NFDR already states there is no audit command (as the two previous refines on this seed found); the exception has its upkeep row and nothing is owed before it lapses | `security-report.md` § Left for the PM, lines 1, 2; `products/tracker17/docs/nfdr.md` QC-40 |
| CP-459's unreadable-data page header | No such page exists; SDD § 6 S-8's page is carried by `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (line 19) | `code-integrity-report.md` § Calls made, 3; `products/tracker17/main.py:L39-L46` |
| code-integrity calls 1, 2 (FR-31 test shape, CP-481 "adds") | The Product Owner's readings of this unit's own spec; each names its fallback; nothing failing | `code-integrity-report.md` § Calls made, 1, 2 |
| plan finding on CP-473's Clear defaults and CP-470's open-at-start | Change-local coverage notes; no failure measured, and the station's Clear line is pinned by the suite this run ran green | `flow_findings/development-plan.md` findings 1, 2; this run's suite (`1964 passed`) |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename`, `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Nothing in the unit or upstream touches their stations | `grep -n -i 'all tasks\|filter\|sort' ` on both seeds' checklists matches nothing |
| remaining specs and implementation flow findings | Change-local, about this unit's own records; they end with it and name no unowned work | the flow findings files above |

## Absent

The closing commit's `Deferred:` lines and the plan's corrections owed — see ## Read. The halt report:
not produced for a sealed unit.
