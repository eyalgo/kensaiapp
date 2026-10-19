# 宿場 Shukuba refine — `2026-10-11_readme-linux-setup-and-git`

*Unit `2026-10-11_readme-linux-setup-and-git`, sealed Tobiishi, reviewed 2026-10-11. Key named by the caller.
Station `2026-10-08_setup-instructions` (root). Seed `2026-10-07_first-project`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves row 1 |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17` | — | Considered row 1 |
| 3 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 2 | Considered row 1 |
| 4 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 1, 2 | recommendation 1 |

Row 4 also waits on row 1 so the Principal PM's `nemawashi-refine` after the retire reads an SRS that has folded the second purpose.

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `journey/tobiishi/trail/2026-10-11_readme-linux-setup-and-git/flow_findings/development-specs.md` | 0 blocking. 1 change-local: "the full suite" is not a README term; the README's last paragraph says "For every test to pass", so it ended with the unit |
| flow findings | `…/flow_findings/development-design.md` | 0 blocking. 1 change-local: no `## 3` heading. Record defect; ends with the unit |
| flow findings | `…/flow_findings/development-plan.md` | 0 blocking. 1 change-local: V-4 does not bar naming the test's file; `README.md:109` names neither, so nothing is owed |
| flow findings | `…/flow_findings/development-implementation.md` | 0 blocking. 2 change-local packet-quote defects in `439add9e2`'s language block; end with the unit |
| flow findings | `…/flow_findings/development-content.md` | Clean |
| code-integrity report | `journey/tobiishi/trail/2026-10-11_readme-linux-setup-and-git/code-integrity-report.md` | `Integrity: pass`. V-1 to V-9 hold; `pytest products/tracker17/tests/` 224 passed. Surfaced nothing it could not fix |
| developer's closing commit | `439add9e2` | `Suite: green`. "Nothing diverged"; 0 cases added, 0 not delivered |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | — |
| the closing commit's `Deferred:` lines | `439add9e2` | absent — no body line begins `Deferred:` (integrity § Deferrals agrees) |
| corrections owed | absent — `tl_instruction.md` has no § Corrections owed while there (`grep -n -i 'corrections owed'` printed nothing) | — |
| work handed on | `journey/tobiishi/trail/2026-10-11_readme-linux-setup-and-git/change_spec.md:80-89` | Fences only. Linux verification is handed to SDD § 11 R-9, a standing risk the README's "checked on macOS only" states; it hands no work to the route |

## Upstream

Seed first committed `2026-10-07T02:17:39+02:00`. Since the previous refine (`c373ad4c5`), `git log --since=2026-10-11T16:47 -- products/tracker17/docs/` lists: SRS v5 `083aa6d92`, FDR v3–v4 `1d67fd17d` and `2c82d3efd`, and CONTENT v8 `8d2050237`. Together they fold `critical` (the previous refine's two companions are now folded) and add FDR R-119 and R-120, which match reached-when 9. PRD v6 `cafd1cb92` adds a second purpose and "A reader learns both purposes from the first thing they read" (`PRD.md:23-29`), and `what_left.md` records the want at `20f9076c5` → Moves row 1. SDD changed only machine paths (`878d25dac`). Before this run, `ls products/tracker17/docs/*_open_issues.md` matched nothing; this run opened one.

## Held

None. `system/logs/chain-tracker17-state.json` reads `ended: settled`, `pending: null`, so no chain is in flight. `chain-change-tracker17-state.json` carries this key with `pending.refine`, which is this run. No open unit sits at `journey/tobiishi/`'s root (only `trail/`).

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| raise a companion item | `products/tracker17/docs/SRS_open_issues.md` § 3.1 (opened) | PRD v6 wants the first thing a reader reads to name tracker17's second purpose. The SRS states neither the purpose nor the want, and RN-18 still drops PRD § Purpose as intent, so no slice can be cut for it | `PRD.md:23-29`; `SRS.md:30-38`, `:620-621`; occurrence `README.md:3`: `grep -n -i 'testing ground' products/tracker17/README.md` → exit 1 | `b1c92352a` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| tracker17 · shukuba · 2026-10-08_setup-instructions | Reached: 1–9 hold now, so the close is owed to the Scrum Master (Next moves 2). No re-aim since the owner's act in `2026-10-10_readme-content-rules_report.md` row 2, and none here, so no owner's-act row | Disposable copy `/tmp/t17refine2.5cj1` (git-initialised). 1: headings at `README.md:58`, `:69`. 2: `:15-28` gives Python 3.11, `python3 --version`, what to do when it is lower, macOS and Linux checked on macOS only, Windows unsupported, and network once for the tests. 3: grep → exit 1, `python3 main.py` at `:7`. 4: unreadable `data/tracker.json` → exit 1, stderr ends `See Setting saved data aside in the setup instructions.`, file unchanged. 5–6: the README's 2 commands print `The tracker is running. Open http://127.0.0.1:8017 … Saved data is kept at …/data.` as `:45` shows, and the page title is `Projects - tracker17`. 7: `pytest tests/` 224 passed, `pytest tests/e2e/` 12 passed. 8: the time-word grep → exit 1, and the longest sentence from `## Status` to `## How it's built` is 20 words. 9: `--with-deps` and `Debian 12` on `:91`. `git status --short` is empty |
| tracker17 · nemawashi · 2026-10-07_first-project | Its last unticked line is the station above, whose close is owed, so it is fully walked → recommendation 1. Its prose quotes the README's old purpose wording (`seed.md:5`). That is not edited, because the seed is leaving the root | `seed.md:25-26` |
| README's opening, the second purpose | Not carried on the open station: its subject is S-1's setup artifact, and no settled document below the PRD asks for it yet. The companion carries it | Moves row 1 |
| tracker17 · nemawashi · 2026-10-07_tasks-in-a-project, comment-on-a-task, status-moves | Nothing the unit found or upstream moved makes their text false. The priority set is now folded through the SRS, FDR and CONTENT | `grep -n -i -e critical -e linux -e 'testing ground' unpicked/*.md` → no match on those terms |
| Port 8017 held by a leftover tracker | The previous refine left a tracker running from its scratch copy (PID 5766, cwd `/private/tmp/t17refine.ngOD/products/tracker17`, started 16:47:51). It failed `test_the_real_start_command_with_the_address_held` here (`Address already in use`). This run stopped it with SIGTERM and stopped its own. Environment, not product: no carrier | `lsof -nP -iTCP:8017 -sTCP:LISTEN`, before and after |

## Absent

`deferred_decisions.md` — none written. `Deferred:` lines — none in `439add9e2`. Corrections owed — the plan has no such section. Halt report — not produced by a sealed unit. I don't know whether the earlier `pkill -f "python3 main.py"` in this run matched any other process. PID 5766 survived it, and no other tracker was listening afterwards.
