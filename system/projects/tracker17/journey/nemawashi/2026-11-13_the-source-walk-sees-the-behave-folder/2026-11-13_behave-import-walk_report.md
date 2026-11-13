# 宿場 Shukuba refine — `2026-11-13_behave-import-walk`

*Unit `2026-11-13_behave-import-walk`, sealed Tobiishi, reviewed 2026-11-13. Key named by the caller.
Station `behave-import-walk` (root). Seed `2026-11-13_the-source-walk-sees-the-behave-folder`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/product-docs/launcher.sh tracker17` | — | Moves row 2, the companion item raised |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-11-13_behave-import-walk` | — | Considered row 1 |
| 3 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 2 | recommendation 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-11-13_behave-import-walk`, `flow_findings/development-specs.md` | 0 blocking, 3 change-local: an unrun Verified Claim, an unparseable `.py` under `.behave/` left unstated (Considered row 4), test shape in two rules; each ended with the unit |
| flow findings | the same, `flow_findings/development-design.md` | 0 blocking, 1 change-local: the same unparseable-file edge (Considered row 4) |
| flow findings | the same, `flow_findings/development-plan.md` | 0 blocking, 2 change-local: sorted order unasserted — closed by code-integrity's `test_modules_come_back_sorted_by_path_from_any_depth`; two gate commands — ended with the unit |
| flow findings | the same, `flow_findings/development-implementation.md` | 0 blocking, 4 change-local: environment wording, a skipped observable, a missed dangling-link edge (repaired by code-integrity), and a found-while-walking warning with no owner (Considered row 5) |
| code-integrity report | the same, `code-integrity-report.md` | `Integrity: pass`; two bugs found and fixed in `BehaveWalk` (dangling link, folder named `*.py`), three tests added; nothing surfaced unfixed |
| security report | the same, `security-report.md` | `Security: reported`, no hole. § Left for the PM: the dependency audit did not run, the NFDR names none — QC-40 already says so, no companion owed (Considered row 6) |
| developer's closing commit | `<a commit not in the public history>` | divergences: `tests_imports` rename and an `isinstance` swap, each with its reason; one found-while-walking line (Considered row 5) |
| deferred decisions | the same, `deferred_decisions.md` | absent — the unit wrote none: `ls` → no such file |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — `git log -1 --format=%B <a commit not in the public history> \| grep '^Deferred:'` prints nothing; code-integrity § Deferrals says the same |
| corrections owed | the same, `tl_instruction.md` § Corrections owed while there | two *Owed outside this change's reach* lines, NFDR § 1.2 preamble and QC-1's *verified by* — both still false at `nfdr.md:L201-L203` and `:L42`, Moves row 2; one in-reach docstring line, the unit's own |
| work handed on | the same, `change_spec.md` § Out of Scope | "QC-19's *verified by* tail, whose wording is the Principal Architect's to update once this lands" — Moves row 2; the rest only fences |

## Upstream

`git log --since=2026-11-13T02:37:24+01:00 --name-status -- products/tracker17/docs/` (the seed's
first commit, `c00b68e8a`): `39d50fd15`, `85b8a2017`, `a2e1f56c4` (NFDR v29, QC-39), and
`9e5d92a3d`, `d91a081f4`, `d09fb068c` (NFDR v30: QC-1's tail says the entry is met, the companion
removed). None touches QC-19 or the § 1.2 preamble. No `*_open_issues.md` was live before this run;
Moves row 2 opens the architecture one.

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: settled`, `pending: null`: no product-docs
chain in flight. `system/logs/chain-walk-tracker17-state.json` is this run's own walk (`pending`
step `refine`). `journey/tobiishi/` holds no open unit, only `trail/`.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a station | `tracker17 · shukuba · 2026-11-13_behave-import-walk` (line 7) | It stated as current that no test reads `.behave/` and that the walk reuses `SourceWalk`; the walk landed as its own class and a test reads the folder. Prose only, reached-when unchanged, not a re-aim | `products/tracker17/tests/conftest.py:L139`, `:L171`; `change_spec.md` § Locked Answers Gap 1 of `tracker17 · tobiishi · 2026-11-13_behave-import-walk` | `c1e40bc49` |
| raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1, on `nfdr.md` § 1.2 preamble, QC-1 and QC-19 | The preamble's "one layer-6 test" and QC-1's "share" go false with a second, separate walk, and QC-19's tail still asks for a walk that exists and passes | `nfdr.md:L42`, `:L201-L203`, `:L242-L246`; `tl_instruction.md` § Corrections owed while there and `change_spec.md` § Out of Scope of `tracker17 · tobiishi · 2026-11-13_behave-import-walk` | `b1d6fea45` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-11-13_behave-import-walk` | Reached-when 1 to 4 hold now; the close is owed to the Scrum Master | Disposable clone at `69265afe1`: 1, `ls products/tracker17/.behave/features/*.py \| wc -l` → 4, `tests/architecture/` → "120 passed"; 2, with `import tests.conftest` appended to `.behave/features/command_way_in.py` → "1 failed, 119 passed", the failure `test_the_real_behave_folder_passes_and_is_present`; 3, `test_behave_imports.py` holds the empty-folder and absent-folder cases (code-integrity § The finding, CP-797 to CP-799); 4, `tests/` → "3335 passed, 2 skipped", `tests/e2e/` → "122 passed" |
| `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder` (line 16) | Its last unticked line, and its station is the one whose close is owed above; once closed the seed is fully walked — recommendation 1 | the seed (lines 15-16) |
| `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder` (line 7) | "a walk of that folder, which does not exist" is the cut-time reading, dated by its grep at `db8e9b81b`; the tick will record the change | the seed (line 7) |
| `nfdr.md` QC-19, an unparseable `.py` under `.behave/` | The spec and design findings ask its outcome be stated; the form does not occur — every module there parses | `tests/architecture/` → "120 passed" in the clone above, which parses every `.behave/` module through `BehaveWalk` |
| the found-while-walking PytestWarning | Not tracker17's: the warned folder `test_steps_names_a_directory_t1` is left in the machine's shared pytest temp folder by a test this repository does not hold | `git grep -n "steps_names_a_directory"` → no match; the clone run's warning names `<pytest temp root>/garbage-…/test_steps_names_a_directory_t1`, outside the clone |
| `products/tracker17/docs/nfdr.md` QC-40 | The security line asks the NFDR to state that no dependency audit exists, and QC-40 already says so | `security-report.md` § Left for the PM; `nfdr.md` QC-40 *verified by* — "no audit command exists for this product" |
| `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` | Independent of this unit: nothing it built or found touches QC-64's contracts | the seed's § Relation to existing work |

## Absent

- `deferred_decisions.md` — the unit wrote none.
- The closing commit's `Deferred:` lines — none.
- Halt report — a sealed unit produces none.
