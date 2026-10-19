# 宿場 Shukuba refine — `2026-10-07_a-not-found-page`

*Unit `2026-10-07_a-not-found-page`, sealed Tobiishi, reviewed 2026-10-07. Key named by the caller.
Station `2026-10-07_a-project-that-stays` (root). Seed `2026-10-07_first-project`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `~/.kensaiapp/pins/20261007T100109Z-tvtxvt/core/launchers/chain-product/launcher.sh tracker17` | — | Moves row 2 |
| 2 | walk the next change | owner | `~/.kensaiapp/pins/20261007T100109Z-tvtxvt/core/launchers/chain-change/launcher.sh tracker17` | 1 | Moves row 1 · Considered row 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `journey/tobiishi/trail/2026-10-07_a-not-found-page/flow_findings/development-specs.md` | 0 blocking; 1 change-local (no wrong-`Host` run in Verified Claims; the existing test covers it). Ends with the unit |
| flow findings | `…/flow_findings/development-design.md` | 0 blocking; 3 change-local: CP-33's no-cause check, the title row, QC-40's browser verdict "Pass today, failing tomorrow" (Considered row 3) |
| flow findings | `…/flow_findings/development-plan.md` | 0 blocking; 2 change-local (plan wrote the words; CP-35 Python-error case), 1 skill-general (plan ran before content → kaizen `plan-states-no-words-for-unwritten-text`, not the route's) |
| flow findings | `…/flow_findings/development-content.md` | Clean |
| flow findings | `…/flow_findings/development-implementation.md` | 0 blocking; 1 change-local: QC-62's red gate left as a note, not a `Deferred:` line; repaired by integrity in `2ac931bc2` |
| code-integrity report | `journey/tobiishi/trail/2026-10-07_a-not-found-page/code-integrity-report.md` | `Integrity: pass`; one structure test added; QC-62 (8 Ruff, 3 mypy) repaired in `2ac931bc2`; nothing left unfixed |
| developer's closing commit | `06cd9a17a` (supersedes `cc2205854`) | `Suite: green`; words taken from `change_text.md` over the plan's; QC-62 left for another seat (since repaired) |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | — |
| the closing commit's `Deferred:` lines | `06cd9a17a` | absent — no body line begins `Deferred:` |
| corrections owed | `journey/tobiishi/trail/2026-10-07_a-not-found-page/tl_instruction.md:42-46` | Three lines, all test docstrings the unit opened itself ("Rides Task"); no *Owed outside this change's reach* line |
| work handed on | `journey/tobiishi/trail/2026-10-07_a-not-found-page/change_spec.md` § Out of Scope | Address-taken message (R-4) → open station's reached-when 3; README → `setup-instructions`; the rest only fences |
| content findings | `journey/tobiishi/trail/2026-10-07_a-not-found-page/change_text.md` § Findings for the Content Manager | Two standard gaps; no step routes them (`core/roles/loaders/content_manager_global.md:174-175`) → Moves row 2 |

## Upstream

`git log --diff-filter=A --follow --format=%cI -- <seed>` → `2026-10-07T02:17:39+02:00`.
`git -C products/tracker17 log --since=… -- docs/` lists SDD v6 (`4e290298d`: TS-4 both directions,
RT-5 address), NFDR v4/v5 (`1a9c8fb86`, `07c88929b`: QC-11 both directions, QC-62 Ruff/mypy gates),
CONTENT v4/v5 (`37f75b825`, `ed49dc486`) — all before this unit opened (`9e915896e`, 12:19);
`git log 9e915896e^..HEAD -- products/tracker17/docs/` printed nothing before this run. No live
`*_open_issues.md` before this run (`ls products/tracker17/docs/`).

## Held

None. `system/logs/chain-tracker17-state.json` reads `ended: settled`, `pending: null`;
`chain-change-tracker17-state.json`'s one pending step is this refine. No open unit under `journey/tobiishi/`.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a station + modify a seed | tracker17 · shukuba · 2026-10-07_a-project-that-stays (reached-when 8) · tracker17 · nemawashi · 2026-10-07_first-project (its line) | TS-4 and QC-11 now state a reverse pointer check the code lacks, and no station lands it before `tasks-in-a-project` adds the next feature module (shape 3/4) | `products/tracker17/docs/SDD.md` RN-34 ("TS-4 states one check the code is owed"); `docs/nfdr.md:100-108`; `tests/architecture/test_trace.py:87-90` forward only | `af3c6e57e` |
| raise a companion item | `products/tracker17/docs/CONTENT_open_issues.md` § 3.1–3.2 (opened) | The address pattern names two places where the page can show one; the accessible-name rule doesn't say whether same-label, same-destination links repeat | `docs/CONTENT.md:225-230`, `:323-325`; `web/pages.py:53`, `:209-210` | `c2161226e` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| tracker17 · shukuba · 2026-10-07_a-project-that-stays | Not reached: 3 (address-taken message, SDD S-1 *Behaviour* last sentence) and 8 are its own later work; walkable where it stands (shape 6). One re-aim (this run), so no owner's act | `docs/SDD.md:628-641`; `change_spec.md` § Out of Scope |
| QC-62 on `main` | Gate green, no work owed | `git archive HEAD` copy in `/tmp/t17refine.fwrg`: `ruff check .` "All checks passed!", `ruff format --check .` "103 files already formatted", mypy "no issues found in 16 source files"; `pytest tests/` 197 passed, 1 failed (`test_data_is_ignored_by_version_control`, exit 128 — the copy is no git repo, as last refine measured) |
| QC-40 browser advisory | No measured failure today; QC-40's own review re-runs at the next unit's `development-design` | `docs/nfdr.md:289-300`; `flow_findings/development-design.md` third finding |
| tracker17 · nemawashi · 2026-10-07_tasks-in-a-project, comment-on-a-task, status-moves | Nothing this unit found touches their scope; TS-4's reverse check lands before them via Moves row 1 | Upstream above |
| `setup-instructions` line | Still carries README § Status and UX-S1; nothing moved under it | seed `## Stations` line 2 |

## Absent

`deferred_decisions.md` — none written. `Deferred:` lines — none in `06cd9a17a`. Halt report — a sealed
unit produces none. `pytest tests/e2e/` not re-run here (Playwright outside the worktree); recorded
11 passed in `code-integrity-report.md`.
