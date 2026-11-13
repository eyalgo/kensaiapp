# 宿場 Shukuba refine — `2026-11-13_pins-test-reads-behave-lock`

*Unit `2026-11-13_pins-test-reads-behave-lock`, sealed Tobiishi, reviewed 2026-11-13. Key named by the caller.
Station `pins-over-behave` (root). Seed `2026-11-13_the-pins-test-reads-the-behave-lock`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/product-docs/launcher.sh tracker17` | — | Moves row 1, the companion item raised |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-11-13_pins-over-behave` | — | Considered row 1 |
| 3 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 2 | recommendation 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-11-13_pins-test-reads-behave-lock`, `flow_findings/development-specs.md` | 0 blocking, 3 change-local (test coverage of TOML and name-folding edges, multi-version lock records, an unrun claim); each ended with the unit — the plan and code-integrity pass added the cases |
| flow findings | the same, `flow_findings/development-design.md` | 0 blocking, 1 change-local: the QC-39 correction has no named owner — owned now by Moves row 1 |
| flow findings | the same, `flow_findings/development-plan.md` | 0 blocking, 2 change-local: red-first note wrong for two guard tests; the QC-39 correction unowned — owned now by Moves row 1 |
| flow findings | the same, `flow_findings/development-implementation.md` | 0 blocking, 1 change-local: the gate-environment line cites the wrong clause; a record defect of the unit, ends with it |
| code-integrity report | the same, `code-integrity-report.md` | `Integrity: pass`; added two tests (a name the lock does not hold, a separator run); surfaced nothing unfixed; § For the PM repeats the QC-39 correction |
| security report | the same, `security-report.md` | `Security: reported`, no hole. § Left for the PM: the dependency audit did not run, the NFDR names none — QC-40 already says so, no companion owed (Considered row 3) |
| developer's closing commit | `<a commit not in the public history>` | DRY helper `pinned_pair` replaces root-test parsing; mutation-checked rule discrimination; one timing failure in `test_timed_run` passed alone and in every later run (Considered row 4); the QC-39 correction owed |
| deferred decisions | absent — the integrity report says no packet departure arose, so none was written | — |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — no line begins `Deferred:` |
| corrections owed | the same, `tl_instruction.md` § Corrections owed while there | one *Owed outside this change's reach* line, NFDR QC-39 *verified by* — became the companion item (Moves row 1) |
| work handed on | the same, `change_spec.md` § Out of Scope | fences only: `uv lock --check --project .behave` stays a review bar, `requires-python`, production code, Behave runs. The contract-suite and source-walk work is carried by `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` and `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder` |

## Upstream

`git log --since=2026-11-13T02:37:24+01:00 --name-status -- products/tracker17/docs/` → nothing. No live
`*_open_issues.md` under `products/tracker17/docs/` before this run (`find … -name '*_open_issues.md' -not -path '*/trail/*'` → nothing).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended` = `settled`, so no docs chain is in flight. No
change unit is open at `journey/tobiishi/`'s root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1 (opened from `architecture_open_issues_template.md`) | QC-39's *verified by* still says the entry starts unmet in its test, and the pins test now reads both pairs. | `products/tracker17/docs/nfdr.md:L435-L438`; `products/tracker17/tests/architecture/test_pins.py:L83-L101`; `tl_instruction.md` § Corrections owed while there of `tracker17 · tobiishi · 2026-11-13_pins-test-reads-behave-lock` | `39d50fd15` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-11-13_pins-over-behave` | Its reached-when holds now; the close is the Scrum Master's. | Disposable clone at `789255723`, from `products/tracker17`: (1) `grep -n -i -c behave tests/architecture/test_pins.py` → 42; (2) red commits `91caa3d2a`, `071fc5120` before their greens; (3) `playwright==1.65.0` in `.behave/pyproject.toml` → `4 failed, 21 passed`, reverted → `25 passed`; (4) `pytest tests/ -q` → `3297 passed, 2 skipped`, `pytest tests/e2e/ -q` → `122 passed`; `git status --short` empty after |
| `tracker17 · nemawashi · 2026-11-13_the-pins-test-reads-the-behave-lock` | Its only station line is the one whose close is owed, so the seed is fully walked; the retire is recommended. | `tracker17 · nemawashi · 2026-11-13_the-pins-test-reads-the-behave-lock` (line 15) |
| `products/tracker17/docs/nfdr.md` QC-40 | The security line asks the NFDR to state that no dependency audit exists, and QC-40 already says so. | `security-report.md` § Left for the PM; `products/tracker17/docs/nfdr.md` QC-40 *verified by* — "no audit command exists for this product" |
| `tests/integration/test_timed_run.py::test_timed_run_reports_label_add_and_remove_at_volume` | One timing failure in one run, not reproduced: it passed alone and in every later full run, and in this run's. | `<a commit not in the public history>`; this run's `pytest tests/ -q` → `3297 passed, 2 skipped` |
| `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract`, `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder` | The unit touched one test file and nothing upstream moved, so neither seed's sources changed. | `git log --since=2026-11-13T02:37:24+01:00 -- products/tracker17/docs/` → nothing |

## Absent

`deferred_decisions.md` — not written by the unit (no packet departure). No `Deferred:` lines in the
closing commit. No halt report — the unit sealed.
