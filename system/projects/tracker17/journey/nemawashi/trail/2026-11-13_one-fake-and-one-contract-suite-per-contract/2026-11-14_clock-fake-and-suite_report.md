# 宿場 Shukuba refine — `2026-11-14_clock-fake-and-suite`

*Unit `2026-11-14_clock-fake-and-suite`, sealed Tobiishi, reviewed 2026-11-14. Key named by the caller; the
project's PM context names the same unit, `Sealed`.
Station `clock-fake-and-suite` (root). Seed `2026-11-13_one-fake-and-one-contract-suite-per-contract`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/product-docs/launcher.sh tracker17` | — | Moves row 2, the companion item raised |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-11-13_clock-fake-and-suite` | — | Considered row 1 |
| 3 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 2 | recommendation 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-11-14_clock-fake-and-suite`, `flow_findings/development-specs.md` | 0 blocking, 3 change-local, 1 skill-general (kaizen, not the route's). Gap 1 folded QC-64's walk into the unit past the request's sizing, which is why the seed's item 3 is now moot (Moves row 1) |
| flow findings | the same, `flow_findings/development-design.md` | 0 blocking, 3 change-local: two walk edges with no failure test (code-integrity added the real-only one), I-8's cross-module import held only by a one-off gate (Considered row 3), the mutation record's home prescribed |
| flow findings | the same, `flow_findings/development-plan.md` | 0 blocking, 3 change-local: Tasks 3 and 5 narrowed gates missed importers (the full run caught nothing), walk rules without a failure test, FakeClock edges left to inference |
| flow findings | the same, `flow_findings/development-implementation.md` | 0 blocking, 5 change-local: three mis-cited language lines, the Step 1b count (closed by code-integrity's test 1), five walk rules with no recorded single-rule revert (Considered row 4) |
| code-integrity report | the same, `code-integrity-report.md` | `Integrity: pass`; added five missing tests, each shown by a mutation; shortened one line to 100 columns; surfaced nothing it could not fix; two calls left to Tech Lead and Architect on the unit's own test code |
| security report | the same, `security-report.md` | `Security: reported`, no hole. § Left for the PM: the dependency audit did not run, the NFDR names none. QC-40 already says so, so no companion item is owed (Considered row 5) |
| developer's closing commit | `<a commit not in the public history>` | Task 2's I-5 mutation recorded (fake run failed in all 6 configurations, `SystemClock` run passed); the walk's per-rule reverts run for the added edge only |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | — |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` — absent, no line begins `Deferred:` | — |
| corrections owed | `tl_instruction.md` § Corrections owed while there | one *Owed outside this change's reach* line: QC-64's "starts unmet" tail is false once the change lands → companion item (Moves row 2) |
| work handed on | `change_spec.md` § Out of Scope | QC-64's dated counts and "starts unmet" reading, handed to the NFDR → Moves row 2. Production code, restructuring, `.behave/`, a third contract: fences, nothing handed on |

## Upstream

`git log --since=2026-11-13T02:37:24+01:00 --name-status -- products/tracker17/docs/`: FDR v8, SDD v23,
CONTENT v22 (the due-today count, as the previous refine read them); NFDR v32 (`e1c521d02`), which folded
the previous refine's companion item: QC-64 now names `testing_python.md` § Rules. `what_left.md`
(`6ce827a34`). No obligation QC-64 states moved. No live `*_open_issues.md` before this run; this run opened
`architecture_open_issues.md`.

## Held

None. `system/logs/chain-tracker17-state.json`: `ended` `settled`, `pending` null, so no docs chain is in
flight. `system/logs/chain-walk-tracker17-state.json` carries this unit with `pending` `refine`, which is
this run. No open unit at `journey/tobiishi/`'s root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a seed; modify a station | `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` (line 16, 20, 24); `tracker17 · shukuba · 2026-11-13_clock-fake-and-suite` (line 7, 17, 25) | The unit landed QC-64's walk with the fake, and every case item 3 named has its test on `main`, so item 3 is folded into item 2 and the open station gains the walk as reached-when 5. A station of its own would spend a change on nothing. This is the station's first re-aim. | `change_spec.md` § Locked Answers Gap 1; `products/tracker17/tests/architecture/test_contract_fakes.py:159`, `:238`, `:266`, `:277`, `:290`, `:297`, `:308`, `:319`; merge `4f4be9413` | `60f9842ef` |
| raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1, on `nfdr.md` QC-64 | QC-64's *verified by* still ends "The entry starts unmet …", and the tree now meets it. | `tl_instruction.md` § Corrections owed while there; `products/tracker17/docs/nfdr.md:356-358`; `grep -rEln --include='*.py' '^\s+def (now\|save)\(' tests` → `tests/fakes.py` only | `9a72cffe7` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-11-13_clock-fake-and-suite` | Reached-when 1 to 5 hold on `main`. The close is the Scrum Master's, and it is owed. | 1: `products/tracker17/tests/fakes.py:77` `FakeClock`, `:99` `now`; `tests/integration/test_clock_contract.py:183`, `:188`, the two runs. 2: `<a commit not in the public history>` body, the I-5 mutation (`now` returns a naive instant: the fake run failed in all 6 configurations, `SystemClock` passed). 3: `grep -rEln --include='*.py' '^\s+def now\(' tests` → `tests/fakes.py`, count `1`. 4: `code-integrity-report.md` § Test evidence, 3436 passed, 2 skipped, e2e 122 passed; `git diff --stat 8c2f588bb..4f4be9413 -- products/tracker17 ':!products/tracker17/tests'` in a fresh clone → empty. 5: the walk, clock and saver files in a fresh clone at `4f4be9413` → `87 passed` |
| the same seed, fully walked once the close lands | Item 1 is ticked and item 2 is the station whose close this run records as owed, so the retire is owed after the close. | `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` (line 15, 16) |
| design finding: I-8's cross-module clock import is held only by a one-off gate | Does not occur: every clock class sits in `tests/fakes.py`, and an imported clock would need a defining class that the walk already fails. | `grep -rEln --include='*.py' '^\s+def now\(' tests` → `tests/fakes.py` only |
| implementation finding: five walk rules with no recorded single-rule revert | No occurrence cited. Each rule has a named failure test on `main` and no revert was measured green, so no carrier is owed. | `products/tracker17/tests/architecture/test_contract_fakes.py:238-372` |
| `products/tracker17/docs/nfdr.md` QC-40 | The security line asks the NFDR to say no dependency audit exists, and QC-40 already says so. | `security-report.md` § Left for the PM; `nfdr.md` QC-40 *verified by*: "no audit command exists for this product" |
| unpicked seeds | None in the pool. | `ls system/projects/tracker17/journey/nemawashi/unpicked` → empty |

## Absent

`deferred_decisions.md`: the unit wrote none. `Deferred:` lines: none in `<a commit not in the public history>`. No halt report, because the unit is sealed. No station in `parked/`.
