# 宿場 Shukuba refine — `2026-10-28_delete-a-task`

*Unit `2026-10-28_delete-a-task`, sealed Tobiishi, reviewed 2026-10-28. Key named by the caller.
Station `2026-10-28_delete-a-task` (root). Seed `2026-10-11_delete-and-rename`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-28_delete-a-task` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves rows 1, 2 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1, 3 | Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking · 6 change-local (non-duplication carried only as behaviour; no rule for existing pages; CP-544/545 name modules; Gap 12 prescribes test shape; CP-540 forward clause unrecorded; Verified Claims 3–7 read, not run) · 0 skill-general |
| flow findings | `flow_findings/development-design.md` | 0 blocking · 3 change-local (confirmation 200, not 202, reason covers only the 404; response policy settled only in the blueprint, "name a follow-up record owner"; T12 lacks a marker-plus-filter case). The first two → Moves row 1 |
| flow findings | `flow_findings/development-plan.md` | 0 blocking · 3 change-local (gate "exit 0" against a red recorded baseline; T8's browser half has no row; Tasks 1–2 gate without ruff/mypy) |
| flow findings | `flow_findings/development-content.md` | no findings; the Content Manager question it names → Moves row 2 |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking · 5 change-local (rule discrimination claimed by case name; no Task 3 discrimination line; "22 beyond" count not reproducible; no-CI exception cited from the wrong clause; two unquoted bore-on-nothing lines) · 0 skill-general |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`; no code bug; fixed four tests and added two controls; surfaced nothing it could not fix |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM: dependency audit did not run, NFDR names none — Considered row 4 |
| developer's closing commit | `<a commit not in the public history>` | divergence notes: delete trigger got its own class and a stylesheet line though the design said none; one monkeypatched test (replaced by code-integrity); e2e fixed and run, 100 passed — all change-local |
| deferred decisions | absent — no `deferred_decisions.md` in the unit folder | — |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — `git show -s --format=%B <a commit not in the public history> \| grep -c '^Deferred:'` → `0` |
| corrections owed | `tl_instruction.md` § TL Review Notes, *Local documentation corrections* | "No record correction is owed outside the task" — no *Owed outside this change's reach* line |
| work handed on | `change_spec.md` § Out of Scope | rename and delete of a project → seed lines 18–19; the docstring bar → seed line 19; HTTP caching of the delete confirmation and the deleted 404, handed to development-design, settled there only → Moves row 1; the other five lines only fence |

## Upstream

`git log --since=2026-10-11T18:13:32+02:00 -- products/tracker17/docs/` (seed first committed then): the moves the `2026-10-28_linked-counts` refine already read (SDD v8–v12, UXD v9–v11, CONTENT v13–v16, NFDR v15–v16 with ADR-0011, `what_left.md` status lines). None touches SDD § 6 S-7's bar, SRS FR-12/FR-13/FR-15/FR-17, UXD UX-F10 or NFDR QC-48's rule; SDD v11 added RT-11, whose deletion clause is Moves row 1. No live `*_open_issues.md` before this run (`ls products/tracker17/docs/*_open_issues.md` → no matches).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null`. `system/logs/chain-change-tracker17-state.json` is this refine's own walk (`pending: refine`, key `2026-10-28_delete-a-task`). No open unit under `journey/tobiishi/`'s root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| raise a companion item | `products/tracker17/docs/SDD_open_issues.md` § 5.1 (opened) | RT-11 hands the deleted task's 404 caching to this slice and S-7 says both confirmations behave as the move's, but the product answers the delete confirmation 200 with `no-store` and the 404 without it, and no settled section says so; `delete-a-project` builds the next confirmation against S-7 | `products/tracker17/web/routes.py:L433-L438`; `products/tracker17/docs/SDD.md:L438-L442`, `L1013`; `flow_findings/development-design.md` (findings 1–2); `change_design.md:L231-L236` | `0fe6aa906` |
| raise a companion item | `products/tracker17/docs/CONTENT_open_issues.md` § 3.1 (opened) | § Needs confirming counts "what goes with it", a task's comments go with it, and the task example names no count; the product follows the example, and the project deletion's sentence faces the same reading | `products/tracker17/web/pages.py:L782`; `products/tracker17/docs/CONTENT.md:L326-L333`; `products/tracker17/docs/SRS.md:L156`; `change_text.md:L160-L166` | `13c0e0d73` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-28_delete-a-task` | Reached-when holds on all five items; the close is the Scrum Master's. `README.md` has one `## Status` line and `docs/what_left.md` exists, so `readme-status` is owed after it | scratch clone at `e25e527b9`: `pytest products/tracker17/tests/` → `2273 passed`, exit 0 (items 2–4); `python3 products/tracker17/tests/timed_run.py` → exit 0, `delete a task at 1000 tasks: 24.0 ms` (item 5); `uv run --with playwright==1.63.0 python -m pytest tests/e2e/test_delete_task.py` → `7 passed` (item 1); `products/tracker17/tests/integration/test_delete_routes.py:L308-L376` (AC-12 refusals), `L411` (FR-15); `products/tracker17/tests/unit/test_tasks.py:L836` (FR-17) |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename` (line 18), `rename-a-project` | Walkable where it stands (shape 6): UX-F10, FR-12 and QC-48 are defined, the rename and its timing are the station's own work, and the timed run exists. One refine re-aim (2026-10-13, line 21), under two | `products/tracker17/docs/UXD.md:L329`; `products/tracker17/docs/SRS.md:L130`; `products/tracker17/docs/nfdr.md:L435-L442`; `grep -rn -i rename products/tracker17/web products/tracker17/application` → nothing |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename` (line 21) | Its QC-48 pointer `nfdr.md:L412-L414` now lands on other text (QC-48 is at `L435`); a dated divergence record, the identifier still resolves, so not amended | `products/tracker17/docs/nfdr.md:L435` |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already states there is no audit command, as earlier refines in this project found; no companion item owed | `security-report.md` § Left for the PM; `products/tracker17/docs/nfdr.md` QC-40 *verified by* |
| design T12, marker-plus-filter address | A missing test row, not a measured failure; no occurrence cited, so no carrier | `flow_findings/development-design.md` (finding 3) |
| the other change-local flow findings and the closing commit's notes | Each ends with this unit: wording, altitude, count and evidence notes about its own artifacts, corrected in its branch or by its audits; none names work that lost an owner | `flow_findings/*.md`; `code-integrity-report.md` § The finding |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Nothing in this unit touches its sources or route | upstream log above |

## Absent

`deferred_decisions.md`; the closing commit's `Deferred:` lines; an *Owed outside this change's reach* line; the halt report (a sealed unit produces none). No station in `shukuba/parked/`.
