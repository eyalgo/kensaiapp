# 宿場 Shukuba refine — `2026-10-12_browser-suite-every-run`

*Unit `2026-10-12_browser-suite-every-run`, sealed Tobiishi, reviewed 2026-10-12.
Station `browser-suite-every-run` (root). Seed `browser-suite-every-run`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 1 | recommendation 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `journey/tobiishi/trail/2026-10-12_browser-suite-every-run/flow_findings/development-specs.md` | 0 blocking, 2 change-local: I-1's collection claim was read, not run; 20 passes alone are weak evidence at the measured rate, and I-7 is what backs them up. Both are about the spec's own evidence and end with the unit. |
| flow findings | `…/flow_findings/development-design.md` | 0 blocking, 4 change-local: no continuity row for the 13 label/task waits, C5/C8 prescribe procedure, the probe was not quoted, a layout-plan fragment. All are about the design's own text. The negative check in the integrity report covers the first (14 failures, including 4 in labels and 2 in tasks). |
| flow findings | `…/flow_findings/development-plan.md` | 0 blocking, 3 change-local: the common gates name 2 modules and not 4, Task 3 has no C5 diagnostic, and the causal account is unbounded. All are about the plan's own text, and the marker `315e136f9` bounds the causes. |
| flow findings | `…/flow_findings/development-implementation.md` | 0 blocking, 3 skill-general: the re-close marker dropped the Step 1b block, the six-concern accounting and the review notes (kaizen `reclose-marker-drops-step-1b-and-notes`). 1 change-local: no `Skill-Version:`/`Reasoning-Effort:` on `315e136f9`. Skill-general findings are not the route's. |
| code-integrity report | `…/code-integrity-report.md` | `Integrity: pass`. I-1 to I-12 hold, I-3 passed 20 of 20, and the negative check gave 14 failed and 13 passed, all of them focus assertions. It surfaced nothing it could not fix. |
| developer's closing commit | `315e136f9` | Two causes. The autofocus race: `activeElement` was read before native focus settled. String-predicate `wait_for_function`: Playwright runs it through `eval`, which `script-src 'none'` refuses. It supersedes `7ba95e221`. |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` (`ls` of the unit folder) | — |
| the closing commit's `Deferred:` lines | absent — `315e136f9` has no line beginning `Deferred:`, and the integrity report agrees (§ Deferrals) | — |
| corrections owed | absent — `tl_instruction.md` has no § *Corrections owed while there* (`grep -n 'Corrections owed'` prints nothing) | — |
| work handed on | `…/change_spec.md:L58-L64` § Out of Scope | All five lines only fence work out: the ADR-0003 fallback (its condition did not occur, because the cause was test timing), RN-15's two open focus cases, new e2e coverage, the in-process suite, and Linux e2e runs. None hands work on. |

## Upstream

`git log --diff-filter=A --follow --format=%cI -- <seed>` gives `2026-10-12T12:03:35+02:00` (`b1ad03462`). Then `git -C products/tracker17 log --since=2026-10-12T12:03:35+02:00 --name-status -- docs/` prints one commit: `d4ea7c2be readme-status: tracker17 — Status says labels are built`, `M docs/what_left.md`. That file is not a source of this seed. `find products/tracker17/docs -name '*_open_issues.md' -not -path '*/trail/*'` prints nothing, so no companion is live.

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: "settled"` and `pending: null`, so no product chain is in flight. `journey/tobiishi/` holds only `trail/`, so no unit is open.

## Moves

None — no move was owed; see below.

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| tracker17 · shukuba · 2026-10-12_browser-suite-every-run | Its reached-when holds now, so the close is owed to the Scrum Master. 1: the causes are written in the closing commit's body. 2: no retry or rerun on added lines. 3: the whole folder exits 0 on 20 consecutive runs on an archive of `main`. | 1: `315e136f9` body, § Causes (I-7). 2: `git diff 530d0c214..HEAD -- products/tracker17 \| grep -E '^\+' \| grep -inE 'rerun\|flaky\|retry\|retries'` gives exit 1, no output. 3: `git archive 3db2c50ae products/tracker17` into `/private/tmp/t17-refine.h8Xk`, `git init`, the README's `.venv` (`README.md:L95-L98`), then 20 × `pytest -q -p no:cacheprovider products/tracker17/tests/e2e/`. `exits.log` shows 20 × `exit 0`, every run `27 passed`, and `EvalError\|SKIPPED\|XFAIL\|deselected` matches no log. |
| tracker17 · nemawashi · 2026-10-12_browser-suite-every-run | Its one station line is the station whose close is owed, so the seed is fully walked once that close lands. The retire is recommended, and the seed is not edited. Its prose ("fails at random", L5) records why it was cut and is not a stale current fact. | `seed.md:L13-L17` (one `- [ ]` line); row above |
| tracker17 · nemawashi · unpicked (all six) | None of them rests on this seed, none was cut from a document that moved, and none states the flaky suite as current. Each one's "both suites pass" bar is now reliably passable, and none needs a change for it. Shape 6 does not apply, because there is no next unticked station on the active seed. | `grep -rniE 'flak\|intermittent\|browser-suite' journey/nemawashi/unpicked` prints nothing; `seed.md` § Relation to existing work |
| products/tracker17/docs (any) | No document gap occurs. The fix changed only test observation in `tests/e2e/` (layer 5, NFDR § 9), and no document states something the unit made false. | `git diff --name-only 530d0c214..HEAD -- products/tracker17`: the four e2e modules only; integrity report § Placement |

## Absent

`deferred_decisions.md`, the `Deferred:` lines and § *Corrections owed while there*. The unit produced none of the three (see § Read). No live `*_open_issues.md` exists under `products/tracker17/docs`.
