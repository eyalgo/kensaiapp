# 宿場 Shukuba refine — `2026-10-29_project-card-commands`

*Unit `2026-10-29_project-card-commands`, sealed Tobiishi, reviewed 2026-10-30. Key named by the caller (the PM context names the same key, `Sealed`).
Station `2026-10-29_project-card-commands` (root). Seed `2026-10-29_the-suite-runs-on-uv`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-29_project-card-commands` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 1 | recommendation 1 |
| 4 | route across projects | Principal PM | none — a `principal-pm:` session, on that recommendation | — | recommendation 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking · 4 change-local (CP-689 exit semantics unrun in the spec; CP-690 tree state after full run unrecorded; CP-686 anchors core line numbers; browser readiness rests on one cache) |
| flow findings | `flow_findings/development-design.md` | 0 blocking · 1 change-local (`&&` short-circuit chosen without its trade-off logged) |
| flow findings | `flow_findings/development-plan.md` | 0 blocking · 2 change-local (gate clones HEAD without saying the edit is committed first; no stated outcome if T4 hits the loopback refusal) |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking · 1 change-local (`environment.md` line cites no no-CI default) |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`; T1–T8 re-run in fresh clones, `2698 passed` then `121 passed`; no fix; surfaced a refused Setup leaving `.venv` (ruled not a defect under CP-687) |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM (line 9): dependency audit did not run, the NFDR names none — QC-40 already says so, no companion owed (Considered row 4); line 10: nothing else |
| developer's closing commit | `<a commit not in the public history>` | re-close superseding `<a commit not in the public history>` once the gate carried Playwright's browser folder; divergences: checks ran in branch-head clones with the edited card, two scratch mutations discarded; § 10 NFDR correction left owed outside reach |
| deferred decisions | `deferred_decisions.md` | entry 1, NFDR § 10 preamble, `Owner: none` → folded since, NFDR v22 (Considered row 2); entry 2, QC-40 graph-reading moment, `Owner: none` → owned by QC-40's own every-review gate (Considered row 3) |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — `git log -1 --format=%B <a commit not in the public history> \| grep -n '^Deferred:'` → nothing |
| corrections owed | `tl_instruction.md` § Corrections owed while there (line 34) | one *Owed outside this change's reach*: NFDR § 10 preamble → already says what it asks (Considered row 2) |
| work handed on | `change_spec.md` § Out of Scope | NFDR § 10 → folded (Considered row 2); where worktree creation runs `Setup command:` vs the card template's comment → handed to nobody, recommendation 2; Playwright browser on a machine without Chromium v1243 → fence, does not occur (Considered row 5); pins, tests, other card lines, README, QC-40, QC-60, SDD prerequisites wording — fences only |

## Upstream

`git log --since=2026-10-29T19:20:28+01:00 --name-status -- products/tracker17/docs/` → `79a743286`, `5eb5ec557` (QC-39), `b50787bc4`/`d648214ab`/`01d3d925a` (SDD companion raised and folded, SDD v16), `f86543f50`/`1bfb63f7f`/`7ed698a82`/`f83e0f3f2`/`98a0a2497`/`1f1ed6101` (architecture companion raised and folded through NFDR v21), `870b7e70b`/`d0dae0269`/`1d11b7047` (§ 10 preamble companion raised and folded, NFDR v22 Settled). Every move closes over itself; none reaches the active seed's walked or unwalked lines. Live companions: none (`find products/tracker17/docs -name '*_open_issues.md' -not -path '*/trail/*'` → nothing).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null` — no definition chain in flight. `system/logs/chain-change-tracker17-state.json` carries this key with only `refine` pending — this run. No open unit at `journey/tobiishi/` root (`ls` → `trail` only).

## Moves

None — no move was owed; see below.

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-29_project-card-commands` | All four reached-when items hold on `main`; the close is the Scrum Master's, owed. It is the seed's last line, so the seed is fully walked | station (lines 13-16); at `84f95461e`, `grep -nE '^\*\*(Setup\|Test) command:\*\*' system/projects/tracker17/project.md` → Setup `uv sync --locked --project …`, Test `uv run --locked …` twice; fresh clone, no `.venv` before → card Setup via `/bin/sh` exit 0, `products/tracker17/.venv` made → card Test exit 0, `collected 2698` → `2698 passed`, `collected 121` → `121 passed`, unit/integration/architecture/e2e paths in the output, 0 deselected or collection errors; `git diff --stat 84f95461e^1 84f95461e -- products/tracker17` → nothing. `README.md` has one `## Status` line; `docs/what_left.md` present |
| `products/tracker17/docs/nfdr.md` § 10 preamble | Deferred entry 1 and the plan's owed correction are already folded: the preamble points at the card and says both suites run through `uv run` | `products/tracker17/docs/nfdr.md:633-637`; `1d11b7047` |
| `products/tracker17/docs/nfdr.md` QC-40, graph-reading moment | Deferred entry 2 has an owner: QC-40 itself keeps the moment owed at every `development-design` review until the graph is read, and the seed's § Out leaves it to the owner and the Principal Architect | `products/tracker17/docs/nfdr.md:385-398`; `7ed698a82`; `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv` (§ Out) |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already says no audit command exists; same as the two earlier refines on this seed | `security-report.md` (line 9); `products/tracker17/docs/nfdr.md:399` |
| route, Playwright browser on a machine lacking Chromium v1243 | Does not occur: every run of this product's suite, this one included, found the pinned browser | `change_spec.md` § Out of Scope; this run's fresh-clone Test → `121 passed` |
| flow findings, change-local (8) | Each ends with this unit; none names unowned work or a failing gate | `flow_findings/*.md`; integrity `Integrity: pass` |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Untouched by this unit; independent of the active seed; the pick after the retire is the Principal PM's refine to name | its § Relation to existing work |

## Absent

- The closing commit's `Deferred:` lines — none in `<a commit not in the public history>`.
- `journey/shukuba/parked/` — empty.
