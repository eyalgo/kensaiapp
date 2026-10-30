# 宿場 Shukuba refine — `2026-10-30_unreadable-data-page`

*Unit `2026-10-30_unreadable-data-page`, sealed Tobiishi, reviewed 2026-10-30.
Station `2026-10-30_unreadable-data-page` (root). Seed `2026-10-11_protect-saved-data`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | the companion items raised, Moves rows 3 to 6 |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-30_unreadable-data-page` | — | Considered row 1 |
| 3 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 2 | Considered row 1 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1, 2 | Moves row 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings, specs | `flow_findings/development-specs.md` | 0 blocking, 4 change-local (methods at the stylesheet, the 403 carve-out, altitude, evidence); Considered row 3; no work left |
| flow findings, design | `flow_findings/development-design.md` | 0 blocking, 4 change-local. Seven false records with no owner, carried by the plan's corrections and Moves rows 3 to 5. The rest concern that step's output |
| flow findings, plan | `flow_findings/development-plan.md` | 0 blocking, 2 change-local: task ordering and a cosmetic record; no work left |
| flow findings, content | `flow_findings/development-content.md` | 0 blocking, 1 change-local: "What the start prints" omits the third line; Moves row 1 |
| flow findings, implementation | `flow_findings/development-implementation.md` | 0 blocking, 6 change-local: five about that step's evidence, Considered row 4; the non-UTF-8 path, Moves row 6 |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`; three damaged-file kinds fixed in `persistence`. Six calls: call 6 is Moves row 6; calls 1 to 5 accepted, Considered row 5. Named pipe not tried, Considered row 6 |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM (lines 11, 12): no dependency audit named, and the package feed unchecked; the NFDR already states both, no companion owed, Considered row 7 |
| developer's closing commit | `<a commit not in the public history>` | Divergences recorded: `Answers` as a Protocol, the stylesheet read in the handler, one case not delivered. Ten corrections left to the PM, below |
| deferred decisions | `deferred_decisions.md` | Three entries, each owner none: the console line, Moves row 6; "no header", Moves row 5; the non-UTF-8 path, Moves row 6. Each now has an owner |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | Absent: no line begins `Deferred:` |
| corrections owed | `tl_instruction.md` § Corrections owed while there | Ten *Owed outside this change's reach* lines, each opened and still false: QC-7, QC-63, ADR-0011, ADR-0012, ADR-0005, Moves row 3; R-20, R-105, Moves row 4; EX-12, EX-13, Moves row 5; CONTENT Terminal messages, Moves row 6 |
| work handed on | `change_spec.md` § Out of Scope | The CONTENT example and rule, Moves row 6. Every other line fences |

## Upstream

`git log --since=2026-10-11T18:13:32+02:00 --name-status -- products/tracker17/docs/`: since the last refine, `CONTENT.md` to v18 at `759bc4110` and `nfdr.md` to v23 at `4a646aaf0`, both folds of items that refine raised, and neither touches this seed's sources. SDD § 6 S-8, SM-6, SD-5, AC-7 unmoved. No live `*_open_issues.md` before this run; four now, Moves rows 3 to 6.

## Held

None. `system/logs/chain-tracker17-state.json`: `ended` is `settled`, `pending` null. `system/logs/chain-change-tracker17-state.json` has `pending` `refine`: that is this review, of this sealed unit. No unit is open at the Tobiishi root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| Modify a seed | `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Adds `what-the-start-prints`: the section a new operator reads first stays silent on a line the start now prints, the unit was fenced from it, and nothing carries it | `products/tracker17/README.md:L50`; `change_text.md` § Wording decisions (line 108); `flow_findings/development-content.md` | `00bc6057c` |
| Modify a seed and a station | `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (line 7); `tracker17 · shukuba · 2026-10-30_unreadable-data-page` (line 7) | Both stated the exit-1 stop as current; the reached-when is unchanged | `products/tracker17/main.py:L126-L128` | `00bc6057c` |
| Raise a companion item | `products/tracker17/docs/architecture_open_issues.md` §§ 3.1-3.5 | QC-7, QC-63, ADR-0011, ADR-0012, ADR-0005 are universal and one startup mode departs from each | `tl_instruction.md` lines 39-44; `products/tracker17/docs/nfdr.md:L73-L83`, `:L91-L100`; `products/tracker17/web/routes.py:L1343-L1345` | `12499fcbe` |
| Raise a companion item | `products/tracker17/docs/fdr_open_issues.md` §§ 3.1-3.2 | R-20's next save and R-105's not-found page do not reach that mode | `products/tracker17/docs/fdr.md:L98-L100`, `:L326-L327` | `5c011fcbf` |
| Raise a companion item | `products/tracker17/docs/SDD_open_issues.md` §§ 5.1-5.2 | EX-12 disagrees with DESIGN.md on the header; EX-13 wants scoping | `products/tracker17/docs/SDD.md:L693-L699`; `products/tracker17/docs/DESIGN.md:L426-L427` | `55e6bb6cb` |
| Raise a companion item | `products/tracker17/docs/CONTENT_open_issues.md` §§ 3.1-3.2 | The third terminal example describes nothing, the new line has no rule, and no rule shows a path with no faithful text | `products/tracker17/docs/CONTENT.md:L258-L267`; `products/tracker17/main.py:L170`; `web.UnreadableSite(os.fsdecode(b'/tmp/caf\xe9/data'), '127.0.0.1:8017')` raised `UnicodeEncodeError`, and so did printing that text | `d9f583de0` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-30_unreadable-data-page` | All seven bars hold now; the close is the Scrum Master's. Bars 1-3: named tests; bar 4: seven cases fail on the opened tree; bar 5: read; bar 7: the passage read | Clone at `cc37b1bde`: `pytest tests/` 2813 passed, `tests/e2e/` 122 passed. `tests/integration/test_start.py` copied onto `4762c2633`: `-k test_each_dr6_break_serves` 7 failed. `products/tracker17/tests/integration/test_start.py:L242`, `:L607`, `:L1094`; `products/tracker17/README.md:L103` |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data`, `what-the-start-prints` | Reachable where it stands: UX-S2 and the README's section ask only for words this station writes, and the line it names already exists. No re-aim yet | `products/tracker17/README.md:L42-L52`; `products/tracker17/main.py:L170` |
| `products/tracker17/docs/SDD.md`, the 403 carve-out and the stylesheet from "every address" | A reading the spec recorded and the page's documents permit: no other site learns the location, and the stylesheet is not a page. Nothing false to fold | `change_spec.md` Locked Answers, Gaps 4-6 |
| `tests/integration/test_listener.py`, a case no mutation turned red | About that step's evidence; the per-call handler it guards is unchanged code, and no failure is measured, so no carrier | `flow_findings/development-implementation.md` (line 10) |
| `products/tracker17/persistence/saved_data.py`, the edit outside the plan's boundary | Recorded with its reason, and DR-6 already says "cannot read all of it", so the document asks nothing new | `code-integrity-report.md` § Calls made, calls 1, 2; `products/tracker17/docs/SRS.md:L425-L431` |
| A saved file that is a named pipe | The form does not occur: no run has shown it, and it waits as it did before this unit | `code-integrity-report.md` § Test evidence, *Not tried* |
| `products/tracker17/docs/nfdr.md` QC-40, audit and package feed | The NFDR already says no audit command exists and the feed is down; the exception's date is tracked in upkeep, so an item would ask it to state what it states | `security-report.md` (lines 11, 12); `system/upkeep.md:L10` |
| `products/tracker17/docs/CONTENT.md` § Terminology, "quotes its heading exactly" | Its own examples carry no marks and the string follows them, so nothing is false | `change_text.md` § Findings for the Content Manager (line 117) |
| `products/tracker17/docs/what_left.md` | Its empty marker holds: the new station is a sentence of setup text, which the file does not list. The README's status sentence is `readme-status`'s | `products/tracker17/docs/what_left.md`; `products/tracker17/README.md:L11` |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data`, a retire | The added station leaves the seed not fully walked | `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (line 21) |

## Absent

The closing commit's `Deferred:` lines, as in Read. The halt report: a sealed unit produces none. `<CORE>/launchers/chain-product/launcher.sh` was not run here, so whether the sweep's items need the owner's answer is the sweep's to say.
