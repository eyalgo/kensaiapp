# 宿場 Shukuba refine — `2026-10-28_delete-a-project`

*Unit `2026-10-28_delete-a-project`, sealed Tobiishi, reviewed 2026-10-28. Key named by the caller.
Station `2026-10-28_delete-a-project` (root). Seed `2026-10-11_delete-and-rename`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves rows 3 and 4 |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-28_delete-a-project` | — | Considered row 1 |
| 3 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 2 | Considered row 1 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1, 2 | Moves rows 1 and 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking, 3 change-local (evidence read from source, three rule-implied cases unexampled, test-shape altitude); all ended with the unit |
| flow findings | `flow_findings/development-design.md` | 0 blocking, 3 change-local divergence-record and citation notes; ended with the unit |
| flow findings | `flow_findings/development-plan.md` | 0 blocking, 1 change-local (no e2e gate before Task 6); ended with the unit |
| flow findings | `flow_findings/development-content.md` | clean |
| flow findings | `flow_findings/development-implementation.md` | 1 blocking: `project_page` counts `len(rows)` when called without a listing, `web` owning a count against SDD § 3 — still on main, carried by Moves row 2; 4 change-local evidence and language-resolution notes, ended with the unit; 1 skill-general (card's `Test command:` skips `tests/e2e/`), not the route's |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`, one boundary case added (5,000-digit count); judged the count fallback unreachable from the live route, which the audit's blocking line does not dispute; nothing surfaced unfixed |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM: the dependency audit did not run because the NFDR names none — Considered row 5 |
| developer's closing commit | `<a commit not in the public history>` | tasks 1–6 landed; Task 4 reopened when the e2e suite broke at Task 6; `testing_python.md` divergence (monkeypatch, no seam) noted |
| deferred decisions | `deferred_decisions.md` | 2 entries, both `Owner: none`: RT-11's redirect for a deleted project's submissions → Moves row 1; DESIGN confirm-strip size for Delete task → Moves row 1 |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — `git show -s --format=%B <a commit not in the public history> \| grep '^Deferred:'` printed nothing |
| corrections owed | `tl_instruction.md` § Corrections owed while there | 3 *Owed outside this change's reach* lines: NFDR QC-63's unmet line → Moves row 4; SDD RT-11's test list → Moves row 3; SDD R-12's "once it exists" → Moves row 3 |
| work handed on | `change_spec.md` § Out of Scope | RT-11 redirect gap → Moves row 1; records brought up to the built product (RT-11, R-12, QC-63) → Moves rows 3 and 4; the rest fence only (FR-14, UXD § 10, undo, other pages, task deletion, wording, placement) |

## Upstream

`git log --since=2026-10-11T18:13:32+02:00 -- products/tracker17/docs/` (seed first committed at `<a commit not in the public history>`): SDD v12 and v13, ADR-0011 and ADR-0012, NFDR v16 and v17, UXD v9–v11, CONTENT v13–v17. The latest, `d459f69d9` (ADR-0012, NFDR v17) and `cb9ef1445` (SDD v13), were already read into the open station by the previous refine (`tracker17 · nemawashi · 2026-10-11_delete-and-rename` (line 27)); nothing under `docs/` moved after that refine's report at `8aade4042`. No live `*_open_issues.md` before this run (`find products/tracker17/docs -name '*_open_issues.md' -not -path '*/trail/*'` printed nothing); this run opened two.

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: settled`, `pending: null` — no product chain in flight. `system/logs/chain-change-tracker17-state.json` carries this unit with `pending: refine`, which is this run. No unit is open at `journey/tobiishi/`'s root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| 1. modify a seed (two stations added) and modify a station | `tracker17 · nemawashi · 2026-10-11_delete-and-rename`; `tracker17 · shukuba · 2026-10-28_delete-a-project` | Two record gaps the unit handed on with no owner are this slice's work, so the seed gains `deleted-project-redirect` (SDD RT-11's redirect for Add task and Rename on a deleted project) and `task-delete-full-size-confirm` (DESIGN sizes Delete task's strip to `spacing.control`); the open station's two lines saying it closes the seed now name items 4 and 5 | `deferred_decisions.md`; `products/tracker17/docs/SDD.md:L448-L452`; `products/tracker17/web/routes.py:L869-L870`, `:L898-L899` (404 directly; a deleted task's submissions redirect, `:L946-L947`); `products/tracker17/docs/DESIGN.md:L457-L466`; `products/tracker17/web/pages.py:L861`, `products/tracker17/web/style.css:L316-L325` | `18b7b40ed` |
| 2. modify a seed | `tracker17 · nemawashi · 2026-10-11_delete-and-rename` | The implementation audit's blocking finding still stands on main and no station carried it; it rides `deleted-project-redirect`, the same project-deletion code in `web` | `flow_findings/development-implementation.md`; `products/tracker17/web/pages.py:L2037` | `7126209d9` |
| 3. raise a companion item | `products/tracker17/docs/SDD_open_issues.md` § 5.1 | RT-11's test list and R-12's trigger wait on a deletion history test that now exists, and RT-11 names no project-deletion response test | `tl_instruction.md` § Corrections owed; `products/tracker17/docs/SDD.md:L470-L474`, `:L1564-L1565`; `tests/e2e/test_delete_task.py:L182`, `tests/e2e/test_delete_project.py:L290`, `tests/integration/test_delete_project_routes.py:L268` | `ceefcf7b3` |
| 4. raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1 | QC-63 still says the task deletion's 202 is unmet and the project deletion's pages are bound when they land; both now hold | `products/tracker17/docs/nfdr.md:L113-L118`; `tests/integration/test_delete_routes.py:L455` asserts 202; card suite 2556 passed (Considered row 1) | `79119f680` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-28_delete-a-project` | Reached-when holds; its close is owed to the Scrum Master. Items 4, 6, 7, 8 measured; items 1, 2, 3, 5 rest on tests in the suite and the integrity run's e2e pass | fresh clone at `ac09e56af`: `pytest products/tracker17/tests/` → `2556 passed`, exit 0; `python3 products/tracker17/tests/timed_run.py` → exit 0, "delete a project at 1000 tasks: 6.2 ms"; `test_delete_routes.py:L455` asserts `?delete_confirm` 202; docstrings of `domain/projects.py` and `domain/tasks.py` name 12 and 15 tests; `code-integrity-report.md`: `pytest tests/e2e/` 117 passed |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename`, re-aims of the next station | `deleted-project-redirect` has one re-aim (its creation here, extended in Moves row 2 by the same run); under two, so no owner's act | this report, Moves rows 1–2 |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Not touched by anything the unit found or that moved upstream | `system/projects/tracker17/journey/nemawashi/unpicked/` listing |
| `products/tracker17/docs/fdr.md` | No call needed it, by the integrity report and every flow finding | `code-integrity-report.md` § The intent |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already states that no audit command exists; no companion item owed | `security-report.md` § Left for the PM; `products/tracker17/docs/nfdr.md` QC-40 *verified by* |
| card's `Test command:` skips `tests/e2e/` | skill-general flow finding, about the machinery, not this route | `flow_findings/development-implementation.md` |

## Absent

- The closing commit's `Deferred:` lines: none on `<a commit not in the public history>`.
- Halt report: not produced for a sealed unit.
