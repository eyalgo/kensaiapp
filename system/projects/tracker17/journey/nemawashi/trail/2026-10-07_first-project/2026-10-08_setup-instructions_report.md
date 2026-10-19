# 宿場 Shukuba refine — `2026-10-08_setup-instructions`

*Unit `2026-10-08_setup-instructions`, sealed Tobiishi, reviewed 2026-10-08. Key named by the caller.
Station `2026-10-08_setup-instructions` (root). Seed `2026-10-07_first-project`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves rows 2, 3 |
| 2 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1 | Moves row 1; Considered row 1 |

Row 2 waits on row 1 because the next change's `development-design` reads `nfdr.md` QC-40, which the sweep may move. From 2026-10-09 QC-40 blocks that review unless the owner answers the architecture companion's § 3.1.

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `journey/tobiishi/trail/2026-10-08_setup-instructions/flow_findings/development-content.md` | 1 blocking: "now" in section 6, banned by CONTENT § Grammar and mechanics. It landed at `README.md:79` → Moves row 1. 2 change-local: a 21-word sentence (landed at `README.md:23` → Moves row 1); the opening paragraph rewritten outside the design's `Publishes text:` places (ends with the unit) |
| flow findings | `…/flow_findings/development-design.md` | 0 blocking. 4 change-local: three about how the design stated its handed-down constraints (they end with the unit; the heading-reader one was fixed by integrity). The fourth notes that QC-40 blocks every `development-design` review from 2026-10-09 and asks that the PM read it → Moves row 2 |
| flow findings | `…/flow_findings/development-plan.md` | 0 blocking. 5 change-local: CP-62's copy is not a Git repository, three dropped sub-rules, the version check counted in section 2, the constant's owning task, an unresolved gate command. All end with the unit: the README states the non-Git case, and the card's gate ran (220 at baseline) |
| flow findings | `…/flow_findings/development-implementation.md` | 0 blocking. 4 change-local: Step 1b miscounted the reader case; the reader narrowing was not recorded; the `.venv` commands were never typed literally; the interpreter clause was unquoted. The `.venv` claim was measured here → Considered row 3. The rest are record defects that end with the unit |
| flow findings | `development-specs.md` | absent — the unit's `flow_findings/` holds no specs step file (`ls` lists content, design, implementation, plan) |
| code-integrity report | `journey/tobiishi/trail/2026-10-08_setup-instructions/code-integrity-report.md` | `Integrity: pass`. It fixed the heading reader, which had counted fenced `#` lines and seven-`#` runs (red `9026ef1a0`, green `a28d5617e`), and added a reader test. It surfaced nothing it could not fix. `pytest tests/e2e/` was not run on Linux (libglib) |
| developer's closing commit | `e75934a65` | `Suite: green`. Divergences: constants placed in Task 1's red commit; a pre-made venv at `/tmp/t17venv`; the e2e suite and the literal `.venv` commands not run; `mypy .` stops on `tests/conftest.py`, outside the gate |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | — |
| the closing commit's `Deferred:` lines | `e75934a65` | absent — no body line begins `Deferred:` (confirmed by the integrity report's § Deferrals) |
| corrections owed | `journey/tobiishi/trail/2026-10-08_setup-instructions/tl_instruction.md:35-39` | Line 1 rides Task 2 (the unit's own file). Two *Owed outside this change's reach* lines: QC-40's window → Moves row 2; SDD § 11 R-9 / Linux and the non-Git copy → Moves row 3 |
| work handed on | `journey/tobiishi/trail/2026-10-08_setup-instructions/change_spec.md` § Out of Scope | The unreadable-data page and the second-tracker refusal → slice `protect-saved-data` (the seed's § Out, not yet cut; already named there). Two facts the PM is to read: Linux libglib and the non-Git copy → Moves row 3. Everything else only fences (restoring set-aside data, listing failures, wording of other messages, Linux/Windows acceptance, publishing, later slices) |

## Upstream

`git log --diff-filter=A --follow --format=%cI -- <seed>/seed.md` → `2026-10-07T02:17:39+02:00`.
`git log --since=… -- products/tracker17/docs/` → 23 commits. The newest is `c0b823749`
(2026-10-07 15:04, NFDR v6). The previous refine read all of them, and nothing under `docs/` moved
during this unit: `git diff --stat 45c319d74^1 45c319d74 -- products/tracker17` touches only
`README.md`, `main.py` and `tests/integration/test_start.py`. Before this run there was no live
`*_open_issues.md` (`products/tracker17/docs/` held none). This run opened two: Moves rows 2 and 3.

## Held

None. `system/logs/chain-tracker17-state.json` reads `ended: settled`, `pending: null`, so no chain is
in flight. No open unit sits at `journey/tobiishi/`'s root (only `trail/`).

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a station | tracker17 · shukuba · 2026-10-08_setup-instructions, reached-when 8 added | The README landed with two breaches of CONTENT's checkable rules. One is "now", which the content audit marked blocking; the other is a 21-word sentence. No station on the route fixes either, and the README is this station's artifact | `README.md:79` ("Your saved data is now in…"); `README.md:23` (21 words); `docs/CONTENT.md:120`, `:126-127`; `flow_findings/development-content.md` findings 1–2; `grep -n -w -i -e today … -e recently README.md` → line 79 only | `d57c9681e` |
| raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1 (opened) | QC-40's 30-day window for the pinned Chromium build ends 2026-10-08. No newer Playwright exists, and no exception is recorded, so every design review from 2026-10-09 is blocked | `tl_instruction.md:38`; `change_design.md:137-138`; `tests/requirements.txt:12`; `docs/nfdr.md:291-308`; `curl https://pypi.org/pypi/playwright/json` → `1.63.0 2026-09-15T16:49:06` | `d253b6208` |
| raise a companion item | `products/tracker17/docs/SDD_open_issues.md` § 5.1 (opened) | R-9's settling run happened: on Linux the tracker and `pytest tests/` pass, but the e2e browser lacks a system library the prerequisites do not name. A non-Git copy also fails one test | `tl_instruction.md:39`; `docs/SDD.md:268-272`, `:655-660`, `:1170-1175`; this run, Debian 12 aarch64: `pytest tests/` 224 passed, `pytest tests/e2e/` "1 failed, 1 passed, 10 errors" (`libglib-2.0.so.0`); non-Git `git archive` copy: `1 failed, 223 passed` (`test_data_is_ignored_by_version_control`) | `5cbaf3a80` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| tracker17 · shukuba · 2026-10-08_setup-instructions | Not reached. 8 (added here) fails today. 1, 3, 4 and 6 hold. 7's `tests/` half holds, and its e2e half cannot run on this Linux machine; it last passed on the owner's macOS (12 passed, earlier refine). 5 is the reader walk the developer recorded (3 commands). It is walkable where it stands (shape 6): 8 is README wording, the station's own work, measured against `docs/CONTENT.md:120`, `:126-127`. One re-aim since the last owner's-act report (`2026-10-07_reverse-pointer-test_report.md` row 3), this run's `d57c9681e`, so no owner's act. No close owed | Disposable copy `/tmp/t17refine.ClF3` (git-initialised): `grep` 1 → headings at `README.md:56`, `:67`; grep 3 → exit 1, Status names `python3 main.py` (`:7`); unreadable `data/tracker.json` → exit 1, stderr ends `See Setting saved data aside in the setup instructions.`, sha1 unchanged; ready line `The tracker is running. Open http://127.0.0.1:<port> …` matches `README.md:43` except the location (port 8017 was held by another process on this machine, so it ran on port 0); `pytest tests/` 224 passed |
| QC-62 gates and README section 7 as written | They hold. The implementation audit's open `.venv` claim is measured true | Same copy, `python3 -m venv .venv`, `pip install -r tests/requirements.txt` inside it: `pytest tests/` 224 passed; `ruff format --check .` "110 files already formatted"; `ruff check .` "All checks passed!"; `mypy main.py errors.py domain application persistence web` "no issues found in 16 source files"; `git status --short` clean |
| README's opening paragraph rewrite | It was recorded in Wording decisions with reasons and broke no CONTENT rule this run measured. It is change-local and ends with the unit | `flow_findings/development-content.md` finding 3; `README.md:3` |
| tracker17 · nemawashi · 2026-10-07_first-project | Its last unticked line is the open station, which is not reached, so no retire is owed. No seed line needs to change: reached-when 8 belongs to the stretch being walked, and so lives in the station | `seed.md:25-26` |
| tracker17 · nemawashi · 2026-10-07_tasks-in-a-project, comment-on-a-task, status-moves | Nothing this unit found touches their scope, and no source under them moved. QC-40 bears on any of their design reviews, and Moves row 2 carries it | Upstream above |
| slice `protect-saved-data` (not cut) | It is still named in the seed's § Out and in the spec's Out of Scope. Cutting it is the Principal PM's at the seed's retire, which is not owed yet | `seed.md:30`, `:34` |

## Absent

`flow_findings/development-specs.md` — not in the unit's folder. `deferred_decisions.md` — none
written. `Deferred:` lines — none in `e75934a65`. Halt report — a sealed unit produces none.
`pytest tests/e2e/` — it cannot start its browser on this Linux machine (`libglib-2.0.so.0`), so its
verdict here is unknown, not failed. Reached-when 5's reader walk to the Projects page in a browser was
not re-run here, because no browser starts and port 8017 is held on this machine.
