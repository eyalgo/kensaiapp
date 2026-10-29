# 宿場 Shukuba refine — `2026-10-29_ignored-sigint-proof-test`

*Unit `2026-10-29_ignored-sigint-proof-test`, sealed Tobiishi, reviewed 2026-10-29.
Station `2026-10-29_start-tests-under-ignored-sigint` (root). Seed `2026-10-29_start-tests-under-ignored-sigint`.
Key named by the caller.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-29_start-tests-under-ignored-sigint` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 1 | recommendation 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-10-29_ignored-sigint-proof-test`, `flow_findings/development-specs.md` | Clean: 0 findings |
| flow findings | same unit, `flow_findings/development-design.md` | 0 blocking, 1 change-local: who reaps the inner pytest on a failed proof was unstated. Answered in the unit: the test kills its process group on the outer timeout and in `finally` (`<a commit not in the public history>`); no route work |
| flow findings | same unit, `flow_findings/development-plan.md` | 0 blocking, 1 change-local: Task 2's gate measured line 1 only. At the tip line 1 is 97 and line 2 is 16 columns, so no harm landed; no route work |
| flow findings | same unit, `flow_findings/development-implementation.md` | 0 blocking, 3 change-local: the `1 passed` assertion has no failing evidence (the spec's one-test limit), and two citation slips in the closing commit (`toolchain.md:35` owner, a spliced `conventions.md:59` quote). Records of this unit; no route work |
| code-integrity report | same unit, `code-integrity-report.md` | `Integrity: pass`; no deferrals; `2652 passed`; a mutation run deleting the SIGINT fixture failed the proof on the inner 30 s stop timeout. Surfaced, not fixed: the new module's docstring glosses SRS NFR-11 loosely (Calls made, 3) — Considered row 3 |
| security report | same unit, `security-report.md` | `Security: reported`, no hole. § Left for the PM: the dependency audit did not run, the NFDR names none. No companion owed (Considered row 2) |
| developer's closing commit | `<a commit not in the public history>` | Two divergences (a test body that starts its own subprocess; constants without a leading underscore), both accepted by the integrity review; `-p no:cacheprovider` and a process-group kill added beyond the instruction |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | — |
| the closing commit's `Deferred:` lines | absent — `<a commit not in the public history>` carries no line beginning `Deferred:` | — |
| corrections owed | absent — `tl_instruction.md` has no § *Corrections owed while there* (`grep -n -i "corrections owed\|Owed outside"` → empty) | — |
| work handed on | same unit, `change_spec.md` § Out of Scope | Four lines, all fences: SIGINT behaviour of a running tracker, the product's other 90 lines over 100 columns, the collection rule, any change to an existing test. None hands work on (Considered row 4 for the long lines) |

## Upstream

`git log --since=2026-10-29T09:34:27+01:00 --name-status -- products/tracker17/docs/` → empty: nothing
under the product's `docs/` changed since the seed was first committed. `ls products/tracker17/docs | grep -i open_issues`
→ empty: no live companion.

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: settled`, `pending: null`, so no product chain
is in flight. `system/logs/chain-change-tracker17-state.json` is open only on this refine step for this
key. No change unit is open at the `tobiishi/` root.

## Moves

None — no move was owed; see below.

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| close of `tracker17 · shukuba · 2026-10-29_start-tests-under-ignored-sigint` | Reached: every clause of its reached-when holds on `main` now, so the close is owed to the Scrum Master | disposable clone at `a9e5d9108`, from the repository root: `python -m pytest products/tracker17/tests/ -q` → exit 0, `2652 passed`; the same under `sh -c 'trap "" INT; exec …'` → exit 0, `2652 passed`; `python -m pytest products/tracker17/tests/e2e/ -q` → exit 0, `121 passed`; the same under trap → exit 0, `121 passed`. Proof: `tests/integration/test_sigint_launch.py` from `a9e5d9108` placed on a clone at `970f6a4ca` → `1 failed in 34.61s`, exit 1; it passes at `a9e5d9108` inside the 2652 |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already says no audit command exists and verifies QC-40 by review, as the previous refine on this seed found; no companion owed | `security-report.md` (line 9); `products/tracker17/docs/nfdr.md:354`, `:664` |
| the NFR-11 gloss in `tests/integration/test_sigint_launch.py`'s docstring | The SRS ID is right and the trace pointer holds; a loose parenthetical in a test docstring is no failing gate and no Agari bar, and the integrity review took the call (Tech Lead's) | `code-integrity-report.md` § Calls made, 3; `products/tracker17/docs/SRS.md:371` |
| the product's other lines over 100 columns | Fenced by the spec, handed to nobody; the product's own gate `ruff check .` passes, so no measured failure carries it | `change_spec.md` § Out of Scope, line 2; `code-integrity-report.md` (`ruff check .` → `All checks passed!`) |
| the ignored-SIGINT e2e run's time | It passed, in 520 s against 110 s in the foreground, while other suites ran on the machine; no timeout, no failure, so nothing is owed | the clone runs in row 1 |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Its bar names "both suites", which this unit leaves true; nothing it rests on moved | `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (line 9); Upstream above |
| the owner's act on the open station | One re-aim on this station, by the previous refine, none by this run: below the two that send a station to the owner | `tracker17 · shukuba · 2026-10-29_start-tests-under-ignored-sigint` (line 20); `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint` (line 26) |

## Absent

`deferred_decisions.md`, the closing commit's `Deferred:` lines and the plan's § *Corrections owed while
there* — the unit produced none (Read above). No halt report — a sealed unit.
