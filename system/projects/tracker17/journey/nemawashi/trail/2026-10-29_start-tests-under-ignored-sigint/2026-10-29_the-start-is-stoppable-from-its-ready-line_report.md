# 宿場 Shukuba refine — `2026-10-29_the-start-is-stoppable-from-its-ready-line`

*Unit `2026-10-29_the-start-is-stoppable-from-its-ready-line`, sealed Tobiishi, reviewed 2026-10-29.
Station `2026-10-29_start-tests-under-ignored-sigint` (root). Seed `2026-10-29_start-tests-under-ignored-sigint`.
Key named by the caller.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-29_start-tests-under-ignored-sigint` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 1 | recommendation 1 |
| 4 | cut a seed | Principal PM | none — answered by `nemawashi-refine` after the seed's retire | 3 | recommendation 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-10-29_the-start-is-stoppable-from-its-ready-line`, `flow_findings/development-specs.md` | 0 blocking, 4 change-local: mechanism in CP-644, reproduction on Python 3.15 not 3.11, no mid-request SIGINT run, CP-654–656 naming a downstream step. Records of this unit; no route work |
| flow findings | same unit, `flow_findings/development-design.md` | 0 blocking, 2 change-local: the QC-40 package-advisory review left incomplete with no owner (Considered row 4); a stop during the announcement promised with no T2 row — the integrity pass's arming test and the ready-write proof cover the span; no route work |
| flow findings | same unit, `flow_findings/development-plan.md` | 0 blocking, 4 change-local: gate wording, the sandbox `bind` baseline, a T2 assertion moved to the integration layer, activation order. Records of this unit; no route work |
| flow findings | same unit, `flow_findings/development-implementation.md` | 0 blocking, 2 change-local (`conventions.md:129` and `environment.md:16` verdicts read as followed on an unquoted clause), 1 skill-general (kaizen candidate `language-resolution-verdict-rests-on-unquoted-clause`, the machinery's). No route work |
| code-integrity report | same unit, `code-integrity-report.md` | `Integrity: pass`, `2698 passed`; one bug fixed (an arming failure skipped the listener's close, `09552f157` red → `12e48a9f7` green); CP-649's proof fails at `53ad18603`. Calls made 1, reading (a), is the Architect's to rule; nothing surfaced unfixed |
| security report | same unit, `security-report.md` | `Security: reported`, no hole. § Left for the PM, one line: the dependency audit did not run, the NFDR names none — the NFDR already says so (Considered row 3) |
| developer's closing commit | `<a commit not in the public history>` | Divergences: `toolchain.md:35` (3.11 constructs, suite on 3.15), `layout.md:52` test names, `conventions.md:148` no `__version__`; QC-40 package review left incomplete as the design records |
| deferred decisions | same unit, `deferred_decisions.md` | One entry, a record gap with **Owner: none**: SDD § 4 RT-4 / NFDR QC-39 — the suite's environment made by uv. Nothing on the route carries it → recommendation 2 (Considered row 2) |
| the closing commit's `Deferred:` lines | absent — `git show -s --format=%B <a commit not in the public history> \| grep -n '^Deferred:'` prints nothing | — |
| corrections owed | absent — `tl_instruction.md` has no § *Corrections owed while there* (`grep -n -i "corrections owed\|Owed outside"` → empty) | — |
| work handed on | same unit, `change_spec.md` § Out of Scope | Seven lines. Six fence (pre-ready SIGINT, after-return SIGINT, a tracker launched with SIGINT ignored, saved data mid-stop, other signals, the words). The seventh, RT-4's uv move, is the deferred entry above — recommendation 2 |

## Upstream

`git log --since=2026-10-29T09:34:27+01:00 --name-status -- products/tracker17/docs/` → five commits:
`ca9de2cce` opens `SDD_open_issues.md` (uv); `3266cb262` SDD v15 settled, § 4 RT-4 moves the suite to uv,
companion removed; `566d7903d` opens `architecture_open_issues.md`; `909fc536c` NFDR v19 settled,
ADR-0013 supersedes ADR-0002, QC-39 names `uv.lock` and `uv lock --check` and "starts unmet", companion
removed; `53ad18603` NFDR QC-26's review-gate tail. `ls products/tracker17/docs | grep -i open_issues` →
empty: no live companion. The uv move is settled in the documents and not in the product (Considered row 2).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null` — no product chain in
flight. `system/logs/chain-change-tracker17-state.json` is open only on this refine step for this key. No
change unit is open at the `tobiishi/` root.

## Moves

None — no move was owed; see below.

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| close of `tracker17 · shukuba · 2026-10-29_start-tests-under-ignored-sigint` | Reached: every clause of its reached-when holds on `main` now, so the close is owed to the Scrum Master. This unit closed the gap that made the proof fail once under load | disposable clone at `5768d462e`, README environment, from the repository root: `python -m pytest products/tracker17/tests/ -q` → exit 0, `2698 passed in 314.60s`; under `sh -c 'trap "" INT; exec …'` → exit 0, `2698 passed in 323.01s`; `python -m pytest products/tracker17/tests/e2e/ -q` → exit 0, `121 passed in 56.06s`; under trap → exit 0, `121 passed in 65.04s`. Proof: `tests/integration/test_sigint_launch.py` from `5768d462e` placed on the clone at `970f6a4ca` → `1 failed in 30.42s`. Station clause: `tracker17 · shukuba · 2026-10-29_start-tests-under-ignored-sigint` (line 18) |
| SDD § 4 RT-4 / NFDR QC-39, the suite's environment made by uv | Settled in both documents, absent in the product, and on no seed or station: work no seed carries, outside this seed's scope (SIGINT launch), so a seed to cut — recommendation 2. No companion: the documents already state it | `products/tracker17/docs/SDD.md:2838-2840` ("which unit carries that is the PM's"); `products/tracker17/docs/nfdr.md:358`; `products/tracker17/README.md:97-99` (`python3 -m venv`, `pip install -r tests/requirements.txt`); clone at `5768d462e`: `uv lock --check` → `error: Unable to find lockfile at uv.lock`, exit 2; `grep -rn -i 'RT-4\|uv.lock\|QC-39\|uv sync'` over this project's live seeds and stations → empty |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already says no audit command exists and verifies QC-40 by review; no companion owed, as earlier refines on this seed found | `security-report.md` (line 9); `products/tracker17/docs/nfdr.md:362-380`, `:683` |
| QC-40's every-review package check, left incomplete at this unit's design | Not a product hole and not a document gap: the lookup of the pins was refused by the run's approval review as sending dependency metadata outward without authorization. The change moved no pin, and the owner's Dependabot feed is QC-40's standing watch. Authorizing that lookup in a run is the owner's call, not route work | `change_design.md` (lines 237-243); `flow_findings/development-design.md` finding 1; `products/tracker17/docs/nfdr.md:362-380` |
| integrity Calls made 1 — an arming failure closes the listener | Reading (a) taken, one line, reversible; the ruling is the Architect's on `change_design.md` sub-job B, not the route's | `code-integrity-report.md` § Calls made |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Its bar is SDD § 6 S-8, which RT-4's move leaves unchanged; "both suites pass" stays true however the environment is made | `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (line 9); `products/tracker17/docs/SDD.md:2836-2837` ("no slice's *Reached when* fails as written") |
| the owner's act on the open station | One re-aim on this station, by the first refine; none by the second or this run — below the two that send a station to the owner | `tracker17 · shukuba · 2026-10-29_start-tests-under-ignored-sigint` (line 20); `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint` (line 26) |

## Absent

The closing commit's `Deferred:` lines and the plan's § *Corrections owed while there* — the unit produced
none (Read above). No halt report — a sealed unit.
