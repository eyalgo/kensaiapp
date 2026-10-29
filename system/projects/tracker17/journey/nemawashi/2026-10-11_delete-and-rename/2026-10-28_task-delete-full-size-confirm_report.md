# 宿場 Shukuba refine — `2026-10-28_task-delete-full-size-confirm`

*Unit `2026-10-28_task-delete-full-size-confirm`, sealed Tobiishi, reviewed 2026-10-29.
Station `task-delete-full-size-confirm` (root). Seed `2026-10-11_delete-and-rename`.*

Key named by the caller; the project's PM context names the same key, `Status: Sealed`.

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-28_task-delete-full-size-confirm` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 1 | recommendation 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking; 2 change-local (code anchors in CP-609/CP-610, CP-614 not naming the Back-out and failed-save forms); the forms got tests anyway (integrity report table) |
| flow findings | `flow_findings/development-design.md` | 0 blocking; 2 change-local (36px equality is two literals guarded only by T1, stylesheet clean-up unrecorded); `git grep delete-button` over the product is empty, so nothing is left unowned |
| flow findings | `flow_findings/development-plan.md` | 0 blocking; 2 change-local (red-before-green has no observation point, gate unreachable if the listener cannot bind); the integrity pass ran the tests against the old code and they failed, and the bind error did not recur |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking; 1 change-local (the environment clause's no-CI verdict not quoted from its source); about the record, no route work |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`; no tests added; all five geometry cases fail on the old `web/` files; nothing surfaced unfixed |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM: (1) the dependency audit did not run because the NFDR names none — Considered row 3; (2) RN-33's exception lapsing 2026-11-07 is the owner's and has its upkeep row — Considered row 4 |
| developer's closing commit | `<a commit not in the public history>` | Divergence notes: two green commits (second adds the secondary-look check after a revert showed the class rule undetected); `CONTROL_HEIGHT`/`box_of` imported from the sibling test; a git-ignored `.venv` made for Playwright |
| deferred decisions | `deferred_decisions.md` | absent — the unit wrote none (`ls` → No such file) |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — no line of the body begins `Deferred:` (`git log -1 --format=%B <a commit not in the public history>`) |
| corrections owed | `tl_instruction.md` § Corrections owed while there | absent — the plan has no such section (`grep -n "Corrections owed" tl_instruction.md` → nothing) |
| work handed on | `change_spec.md` § Out of Scope | Every line only fences; moving tasks (SRS FR-14) and description change (UXD § 10) are excluded by those documents and sit in the seed's Out |

## Upstream

`git log --since=2026-10-11T18:13:32+02:00 --name-status -- products/tracker17/docs/` → the same set the previous refine on this seed read; nothing under `docs/` changed after `75eb81760` (2026-10-28 18:10), which predates this station's opening (`785bc87b8`). DESIGN `components.confirm-strip` still sizes Delete task's strip to `spacing.control` (`products/tracker17/docs/DESIGN.md:457-466`). No live `*_open_issues.md` under `products/tracker17/docs/` (`find products/tracker17/docs -name '*_open_issues.md' -not -path '*/trail/*'` → nothing).

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: settled`, `pending: null`; `system/logs/chain-change-tracker17-state.json` is pending on this refine step for this key; no open unit at the `tobiishi/` root besides `trail/`.

## Moves

None — no move was owed; see below.

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-28_task-delete-full-size-confirm` | Reached-when holds; its close is owed to the Scrum Master. Items 1 and 4 rest on the e2e measurements; item 2 on the integrity pass's run against the old code; items 3 and 5 measured | fresh clone at `b8777bee0`: `pytest products/tracker17/tests/` → `2629 passed`, exit 0; `pytest tests/e2e/` → `121 passed`; `-k full_size` → `4 passed`; `git grep -n ROW_CONTROL_HEIGHT -- products/tracker17/tests/e2e/test_delete_project.py` → only `:39` (constant) and `:218` (`move_confirm`); `products/tracker17/web/pages.py:861` `size=FULL_SIZE`; `code-integrity-report.md` § Tests added or fixed |
| `tracker17 · shukuba · 2026-10-28_task-delete-full-size-confirm` (line 12) | Item 2's reason ("the first press 36px") was false — the first press was 28px too; the spec corrected it (Locked Answers Gap 1) and the test still failed on `main`. The bar is met; amending a station about to close would be a re-aim for nothing | `change_spec.md` § Locked Answers, Gap 1; `code-integrity-report.md` § Tests added or fixed |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already states that no audit command exists; no companion item owed | `security-report.md` § Left for the PM; `products/tracker17/docs/nfdr.md:354-376` |
| RN-33, the Chromium exception lapsing 2026-11-07 | The owner's, already on the upkeep list; not route work | `system/upkeep.md:10` |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename` | Once the close lands, every station line is ticked; the retire is owed (recommendation 1), so no pick, route cut or next change is named | the seed's checklist, lines 17–21 |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Nothing the unit found or that moved upstream touches it | the seed's checklist (lines 17–19); Upstream above |

## Absent

The unit's `deferred_decisions.md`, the closing commit's `Deferred:` lines and the plan's § Corrections owed while there — none was written (Read rows above).
