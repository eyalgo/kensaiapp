# 宿場 Shukuba refine — `2026-11-13_walk-skips-by-name`

*Unit `2026-11-13_walk-skips-by-name`, sealed Tobiishi, reviewed 2026-11-13. Key named by the caller.
Station `walk-skips-by-name` (root). Seed `2026-11-13_the-source-walk-sees-the-behave-folder`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/product-docs/launcher.sh tracker17` | — | Moves row 1, the companion item raised |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-11-13_walk-skips-by-name` | — | Considered row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/walk/launcher.sh tracker17` | 1, 2 | Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-11-13_walk-skips-by-name`, `flow_findings/development-specs.md` | 0 blocking, 3 change-local (edge cases with no required test, mechanism in a rule, a step named as judge); each ended with the unit — the plan and code-integrity pass added the cases |
| flow findings | the same, `flow_findings/development-design.md` | 0 blocking, 1 change-local: which root each near-name row uses; ended with the unit |
| flow findings | the same, `flow_findings/development-plan.md` | 0 blocking, 2 change-local: a full-run timing failure of `test_real_start_stops_when_pytest_launch_ignores_sigint` recorded nowhere that outlives the change — recommendation 1; `.behave` below the root untested — closed by code-integrity's added test |
| flow findings | the same, `flow_findings/development-implementation.md` | 0 blocking, 3 change-local: `test-driven-development` not invoked, two `Language resolution:` wording gaps; process findings about this unit, ended with it |
| code-integrity report | the same, `code-integrity-report.md` | `Integrity: pass`; two tests added from spec words; both suites green ("3304 passed, 2 skipped", "122 passed"); names QC-1's stale sentence as owed to its owner — Moves row 1 |
| security report | the same, `security-report.md` | `Security: reported`, no hole. § Left for the PM: the dependency audit did not run, the NFDR names none — QC-40 already says so, no companion owed (Considered row 3) |
| developer's closing commit | `<a commit not in the public history>` | divergences: underscore rename of module internals, Python 3.11 floor over the packet's 3.13; both recorded with reasons |
| deferred decisions | the same, `deferred_decisions.md` | one entry, the layer-6 walk of `.behave/` (QC-19 second clause), owner "none — for shukuba-refine": owned by item 2 of `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder` (line 16) |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — `git log -1 --format=%B <a commit not in the public history> \| grep '^Deferred:'` prints nothing |
| corrections owed | the same, `tl_instruction.md` § Corrections owed while there | one *Owed outside this change's reach* line: NFDR QC-1's "The entry starts unmet in its test" goes false — Moves row 1 |
| work handed on | the same, `change_spec.md` § Out of Scope | the `.behave/` walk — carried by item 2 of the seed (line 16); QC-1's sentence — Moves row 1; the two other seeds and the rest only fence |

## Upstream

`git log --since=2026-11-13T02:37:24+01:00 --name-status -- products/tracker17/docs/` (the seed's first
commit, `c00b68e8a`): `39d50fd15` opened the architecture companion, `85b8a2017` answered it,
`a2e1f56c4` folded it into NFDR v29 (QC-39's Behave half met) and removed it. None touches QC-1 or
QC-19. No `*_open_issues.md` was live before this run; Moves row 1 opens the architecture one.

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: settled`, `pending: null`: no product-docs
chain in flight. `journey/tobiishi/` holds no open unit, only `trail/`.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1, on `nfdr.md` QC-1 | QC-1's *verified by* still says the entry starts unmet in its test, and the walk now skips by name with a test that fails on a code-holding dot-folder | `nfdr.md:L44-L46`; `tests/conftest.py:L129`; `tl_instruction.md` § Corrections owed while there of `tracker17 · tobiishi · 2026-11-13_walk-skips-by-name` | `9e5d92a3d` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-11-13_walk-skips-by-name` | Reached-when 1 to 4 hold now; the close is owed to the Scrum Master | 1: `grep -nF 'startswith(".")' products/tracker17/tests/conftest.py` → no match. 2, 3: `tests/architecture/test_source_walk.py:L48-L61`; disposable clone at `6a0f1fe6c`, `tests/architecture/` → "92 passed"; with `conftest.py` at `97603d4f3`, `test_source_walk.py` → "6 failed, 1 passed" (the named-folders case passes at both). 4: `code-integrity-report.md` § Test evidence, "3304 passed, 2 skipped" and "122 passed", and the seal `6a0f1fe6c` ran the suite after main's advance |
| `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder` (line 16), behave-import-walk | Can be walked where it stands (shape 6): QC-19's *verified by* asks a walk of `.behave/` failing on an import from `tests` and on no module while the folder exists, which is the station's own work; `.behave/features/` holds four modules today; re-aimed by no refine | `nfdr.md:L235-L240`; `ls products/tracker17/.behave/features/*.py` → 4 files |
| `products/tracker17/docs/nfdr.md` QC-40 | The security line asks the NFDR to state that no dependency audit exists, and QC-40 already says so | `security-report.md` § Left for the PM; `nfdr.md` QC-40 *verified by* — "no audit command exists for this product" |
| `products/tracker17/docs/nfdr.md` RN-66 | "That test change has not landed" is a dated revision note, left as written | `nfdr.md:L1851-L1858` |
| `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder` (line 5) | Its "skips every path piece that begins with a dot" is the cut-time reading, dated by its grep at `db8e9b81b`; item 1's tick records the change | the seed (line 5) |
| `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` | Independent of this unit: nothing it built or found touches QC-64's contracts | the seed's § Relation to existing work |

## Absent

None.
