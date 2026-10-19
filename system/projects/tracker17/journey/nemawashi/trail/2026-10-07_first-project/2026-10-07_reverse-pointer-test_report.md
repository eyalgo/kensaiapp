# 宿場 Shukuba refine — `2026-10-07_reverse-pointer-test`

*Unit `2026-10-07_reverse-pointer-test`, sealed Tobiishi, reviewed 2026-10-07. Key named by the caller.
Station `2026-10-07_a-project-that-stays` (root). Seed `2026-10-07_first-project`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `~/.kensaiapp/pins/20261007T122327Z-v20q4n/core/launchers/chain-product/launcher.sh tracker17` | — | Moves row 1 |
| 2 | close the reached station | Scrum Master | `~/.kensaiapp/pins/20261007T122327Z-v20q4n/core/launchers/skill/launcher.sh shukuba-retire tracker17` | — | Considered row 1 |
| 3 | the owner's act | owner | none — is `setup-instructions` done as its bar now reads? | 2 | Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `journey/tobiishi/trail/2026-10-07_reverse-pointer-test/flow_findings/development-specs.md` | Clean |
| flow findings | `…/flow_findings/development-design.md` | Clean |
| flow findings | `…/flow_findings/development-plan.md` | 0 blocking; 3 change-local (CP-51 guard could not fail — corrected by integrity; test splits unlogged; eleven words restated in a test). End with the unit |
| flow findings | `…/flow_findings/development-implementation.md` | 0 blocking; 2 change-local (`conventions.md:80` verdict should read as a divergence; table-at-end-of-text edge untested — the real TS-3 table yields its eleven words, so no occurrence). End with the unit |
| code-integrity report | `journey/tobiishi/trail/2026-10-07_reverse-pointer-test/code-integrity-report.md` | `Integrity: pass`; one test added (column found by header), one corrected (CP-51 guard); 220 passed; names the two `nfdr.md` corrections as owed outside the change → Moves row 1 |
| developer's closing commit | `df7c793d3` | `Suite: green`; divergences: `FEATURE_WORDS` read at import; eleven-word guard list (`testing_python.md:57`); QC-11 tail and RN-21 left false |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | — |
| the closing commit's `Deferred:` lines | `df7c793d3` | absent — no body line begins `Deferred:` |
| corrections owed | `journey/tobiishi/trail/2026-10-07_reverse-pointer-test/tl_instruction.md:36-37` | Two *Owed outside this change's reach* lines, `nfdr.md` QC-11 tail and RN-21; both still false → one companion item, Moves row 1. Line 35 is the docstring the unit opened itself |
| work handed on | `journey/tobiishi/trail/2026-10-07_reverse-pointer-test/change_spec.md:94-100` | Station's final check of 1–7 → Considered row 1; README → `setup-instructions`; the rest only fences |

## Upstream

`git log --diff-filter=A --follow --format=%cI -- <seed>` → `2026-10-07T02:17:39+02:00`. Since the last
refine, `docs/` moved only by CONTENT v7 (`448a33a4a`, 14:10, folds the companion the last refine
raised), before this unit opened (`57b86b647`, 14:24). `git log 57b86b647..HEAD -- products/tracker17/docs/`
printed nothing before this run. No live `*_open_issues.md` before this run
(`find products/tracker17 -name '*_open_issues*' -not -path '*/trail/*'` → nothing).

## Held

None. `system/logs/chain-tracker17-state.json` reads `ended: settled`, `pending: null`;
`chain-change-tracker17-state.json`'s one pending step is this refine. No open unit under `journey/tobiishi/`.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1 (opened) | QC-11's *verified by* tail and RN-21 say the pointer test lacks its fourth check, which it now holds | `docs/nfdr.md:109-111`, `:765-767`; `tests/architecture/test_trace.py:223`, `:229`; `tl_instruction.md:36-37` | `91a545aa4` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| tracker17 · shukuba · 2026-10-07_a-project-that-stays | Reached: 1–8 hold now, so the close is owed to the Scrum Master (Next moves 2) | Disposable copy `/tmp/t17refine.sYMZ` (git-initialised): `python3 main.py` printed only "The tracker is running. Open http://127.0.0.1:8017 … Saved data is kept at …/data."; `pytest tests/` 220 passed (incl. `test_data_is_ignored_by_version_control`, reverse check `test_trace.py:223`); `pytest tests/e2e/` 12 passed (venv `/private/tmp/t17venv`); `ls` lists `domain/projects.py application persistence web`; named tests at `tests/e2e/test_first_project.py:95`, `:109`, `:151`, `tests/integration/test_pages.py:140`; 3 measured by the last refine and untouched since |
| tracker17 · nemawashi · 2026-10-07_first-project, line `setup-instructions` | Next to walk once the close lands; walkable where it stands (shape 6) — UX-S1's sections, § Status and the pointer in `main.py:43-44` are all its own work. Re-aimed twice (`9f2c40396` § Status, `6ce44a330` the pointer) and no earlier report put it to the owner, so the owner's act (Next moves 3) and no `walk the next change` row | `docs/UXD.md:307` UX-S1; `docs/CONTENT.md:161`, `:252`; seed `seed.md:17`, `:21` |
| `pytest tests/e2e/` back-to-back runs | All 6 full runs started within seconds of another failed one test each (`test_the_real_start_command_with_the_address_held`: "cannot hold 127.0.0.1:8017: [Errno 48]"; once the focus test, `assert '' == 'name'`); runs a minute apart pass 12/12, on `main` and on the pre-unit tree `a8e72dcdd^1`. I don't know the cause; not this unit's (it touched `test_trace.py` only) and not a stable failure, so no carrier | `/private/tmp/t17venv/bin/python -m pytest tests/e2e/ -q -rf` in `/tmp/t17refine.sYMZ` and `/tmp/t17refine.base.rsKC` |
| tracker17 · nemawashi · 2026-10-07_tasks-in-a-project, comment-on-a-task, status-moves | Nothing this unit found touches their scope; the reverse check they will meet is now in place | Upstream above; `test_trace.py:223` |

## Absent

`deferred_decisions.md` — none written. `Deferred:` lines — none in `df7c793d3`. Halt report — a sealed
unit produces none.
