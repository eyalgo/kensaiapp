# 宿場 Shukuba refine — `2026-10-29_readme-on-uv`

*Unit `2026-10-29_readme-on-uv`, sealed Tobiishi, reviewed 2026-10-29. Key named by the caller (the PM context names the same key, `Sealed`).
Station `readme-on-uv` (root). Seed `2026-10-29_the-suite-runs-on-uv`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves rows 1, 2 |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-29_readme-on-uv` | — | Considered row 1 |
| 3 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 2 | Considered row 1 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1, 2 | Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking · 1 change-local (three Verified Claims rows rest on reading source, not a run) |
| flow findings | `flow_findings/development-design.md` | 0 blocking · 1 change-local (§ 5 lead-in says V1–V13 cover every Example; CP-684 is V14's) |
| flow findings | `flow_findings/development-content.md` | 0 blocking · 2 change-local (network sentence's "only" overclaims; "these commands" referent loosened) |
| flow findings | `flow_findings/development-plan.md` | 0 blocking · 2 change-local (no verbatim compare in the gate; regression pass condition vs listener-error baseline) |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking · 2 change-local (closing gate ran the card's bare `pytest`, `toolchain.md:85`; V13 split after exit 144 not logged as a divergence) |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`; README-only diff, every rule met; no fix, nothing surfaced |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM (line 9): dependency audit did not run, the NFDR names none — QC-40 already says so, no companion owed (Considered row 4) |
| developer's closing commit | `<a commit not in the public history>` | "No divergence"; environment.md container rule diverged (owner's Mac, no CI); V13 rerun separately after exit 144, all passed |
| deferred decisions | `deferred_decisions.md` | entry 1, uv in the prerequisites (SDD S-1 vs RT-4), `Owner: none` → companion SDD 5.1 (Moves row 1); entry 2, QC-40 dependency graph unreadable, Owner Principal Architect, unreached → companion architecture 3.1 (Moves row 2) |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — `git log -1 --format=%B <a commit not in the public history> \| grep -n '^Deferred:'` → nothing |
| corrections owed | `tl_instruction.md` | absent — `grep -n 'Corrections owed' tl_instruction.md` → nothing |
| work handed on | `change_spec.md` § Out of Scope | prerequisites section → SDD 5.1 (Moves row 1); card Setup/Test commands → `project-card-commands` (seed line 19); README `## Status` → `readme-status` (Next move 3); Python 3.11 run → seed § Out; Linux run, uv install recipe, other sections, `docs/` records — fences only |

## Upstream

`git log --since=2026-10-29T19:20:28+01:00 --name-status -- products/tracker17/docs/` → `79a743286`, `5eb5ec557`, both `M products/tracker17/docs/nfdr.md` (QC-39, the previous unit's; already read by its refine). Live companions before this run: none (`find products/tracker17/docs -name '*_open_issues.md' -not -path '*/trail/*'` → nothing). After it: `SDD_open_issues.md` and `architecture_open_issues.md`, this run's.

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null` — no definition chain in flight. `system/logs/chain-change-tracker17-state.json` carries this key with only `refine` pending — this run. No open unit at `journey/tobiishi/` root (`ls` → `trail` only).

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| raise a companion item | `products/tracker17/docs/SDD.md` → `SDD_open_issues.md` § 5.1 | Two settled SDD sentences disagree on whether the prerequisites section names uv, and the README can meet only one; the deferral had no owner | `products/tracker17/docs/SDD.md:302-305` vs `:832-834`; `products/tracker17/README.md:17-29` (no uv), `:91`; `deferred_decisions.md` entry 1 | `b50787bc4` |
| raise a companion item | `products/tracker17/docs/nfdr.md` QC-40 → `architecture_open_issues.md` § 3.1 | QC-40's first-review dependency-graph check came due with this unit and could not run; the NFDR's channel to the Principal Architect is its companion, not a unit's deferred file | `products/tracker17/docs/nfdr.md:386-390`; `deferred_decisions.md` entry 2 (`gh api …/dependency-graph/sbom` → HTTP 404, exit 1) | `f86543f50` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-29_readme-on-uv` | All four reached-when items hold on `main`; the close is the Scrum Master's, owed | station (lines 13-16); at `products/tracker17` on `main` after `a71d23637`: item 1 grep → nothing, exit 1; item 2 → each of the four commands found (`README.md:97`, `:91`/`:93`, `:99`, `:100`), install-uv-first with URL at `:91`; item 3 → two lines; item 4 → nothing, exit 1. `README.md` has one `## Status` line; `docs/what_left.md` present |
| `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv` (line 19), `project-card-commands` | Next unticked station, walkable where it stands: it needs `uv.lock` (on `main`) and edits to the card's two commands, its own work; no refine has re-aimed it. Waits on the SDD sweep because RT-4 states where `uv sync --locked` is typed | `products/tracker17/docs/SDD.md:299-306` (RT-4: `uv sync --locked` typed from the product root); `system/projects/tracker17/project.md` Setup `none`, Test `pytest products/tracker17/tests/` |
| implementation finding: the closing gate ran the card's bare `pytest` | Already the next station's work — its bar runs the suite through uv from the card | `flow_findings/development-implementation.md` (line 8); `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv` (line 19) |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already says no audit command exists; same as the previous refine | `security-report.md` (line 9); `products/tracker17/docs/nfdr.md:390-391` |
| flow findings, change-local (8) | Each ends with this unit; none names unowned work or a failing gate | `flow_findings/*.md`; integrity `Integrity: pass` |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Untouched by this unit; independent of the active seed | its § Relation to existing work |

## Absent

- The closing commit's `Deferred:` lines — none in `<a commit not in the public history>`.
- `tl_instruction.md` § Corrections owed while there — not in the plan.
- `journey/shukuba/parked/` — empty.
