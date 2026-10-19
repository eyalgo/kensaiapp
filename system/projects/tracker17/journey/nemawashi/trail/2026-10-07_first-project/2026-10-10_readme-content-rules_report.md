# 宿場 Shukuba refine — `2026-10-10_readme-content-rules`

*Unit `2026-10-10_readme-content-rules`, sealed Tobiishi, reviewed 2026-10-11. Key named by the caller.
Station `2026-10-08_setup-instructions` (root). Seed `2026-10-07_first-project`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves rows 2, 3 |
| 2 | the owner's act | owner | none — is `setup-instructions` done as its bar now reads? | — | Moves row 1 |

Row 2 does not wait on row 1. The station reads SDD § 6 S-1 / § 4 RT-4 and `CONTENT.md:120`, `:126-127`; the two items the sweep folds are about the priority set (`SRS.md:231`, `CONTENT.md:150`) and touch neither.

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `journey/tobiishi/trail/2026-10-10_readme-content-rules/flow_findings/development-specs.md` | 1 blocking: the e2e invariant against a red baseline (port 8017 held) with no disposition; it ended with the unit, whose re-run found the port free and 12 passed (integrity C8). 1 change-local (e2e counts differ), 1 skill-general (kaizen, not mine) |
| flow findings | `…/flow_findings/development-plan.md` | 1 blocking: the same red-baseline gate, which caused the halt (`22b681de4`); ended with the unit as above. 2 change-local record defects (e2e count, C1 not a command); end with the unit |
| flow findings | `…/flow_findings/development-design.md` | 0 blocking. 1 skill-general (`Publishes text: no` on a prose repair; kaizen). 1 change-local (held address not said to be halt or exception); ends with the unit |
| flow findings | `…/flow_findings/development-implementation.md` | 0 blocking. 2 change-local: the `.venv` and Ruff line-length packet quotes. Record defects; end with the unit |
| code-integrity report | `journey/tobiishi/trail/2026-10-10_readme-content-rules/code-integrity-report.md` | `Integrity: pass`. C1–C8 run by hand; e2e 12 passed. It surfaced the earlier Codex-run timeout of `test_a_created_project_is_listed_after_a_stop_and_a_start` with no cause → Considered row 2. Its call not to add a content-rule test → Considered row 3 |
| developer's closing commit | `39cff98eb` | `Suite: green`. "No divergence from the instruction"; the inherited halt re-checked, not relied on; the *Owed outside this change's reach* line left untouched |
| deferred decisions | absent — the unit wrote no `deferred_decisions.md` | — |
| the closing commit's `Deferred:` lines | `39cff98eb` | absent — no body line begins `Deferred:` (integrity § Deferrals agrees) |
| corrections owed | `journey/tobiishi/trail/2026-10-10_readme-content-rules/tl_instruction.md:63-67` | One *Owed outside this change's reach* line: `README.md:87-107` lacks RT-4's Linux setup and suite boundary. `README.md` has no companion template, and the README is this station's artifact, so it is carried by move 2 → Moves row 1 |
| work handed on | `journey/tobiishi/trail/2026-10-10_readme-content-rules/change_spec.md` § Out of Scope | Fences only: README text outside the span, setup steps and platforms, code/tests/docs, a general rewrite. Nothing handed on |

## Upstream

`git log --diff-filter=A --follow --format=%cI -- <seed>/seed.md` → `2026-10-07T02:17:39+02:00` (previous refine). Since that refine, `git log --since=2026-10-08T00:00 -- products/tracker17/docs/` lists: SDD v7 `4156e81b2` (RT-4 Linux libraries and suite bound; S-1 *Artifact* holds them and the Git prerequisite) → Moves row 1; NFDR v7–v9 `332311003`, `1f536001f`, `24aa9ecd8` (QC-40's dated browser exception to 2026-11-07; architecture companion folded and removed) → Considered row 5; `5cc999d06` readme-status (README § Status); PRD v5 `29352d2fc` (`critical` priority) → Moves rows 2, 3; `878d25dac` (machine paths removed from live files). `SDD_open_issues.md` folded in v7. Before this run no `*_open_issues.md` was live (`find products/tracker17/docs -name '*_open_issues.md'` printed nothing); this run opened two.

## Held

None. `system/logs/chain-tracker17-state.json` reads `ended: settled`, `pending: null`, so no chain is in flight. `chain-change-tracker17-state.json` carries this key with `pending.refine` — this run. No open unit sits at `journey/tobiishi/`'s root (only `trail/`).

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a station | tracker17 · shukuba · 2026-10-08_setup-instructions, reached-when 9 added | SDD v7 put RT-4's Linux line and the Git prerequisite into S-1 *Artifact*, the station's subject, and the README carries neither. This is the station's second re-aim since the owner was last asked (`2026-10-07_reverse-pointer-test_report.md` row 3): `d57c9681e` (reached-when 8) and this one → Next moves 2 | `docs/SDD.md:281-301`, `:672-686`; `tl_instruction.md:65`; `grep -n -F -e '--with-deps' -e 'Debian 12' products/tracker17/README.md` → exit 1 | `ef4137927` |
| raise a companion item | `products/tracker17/docs/SRS_open_issues.md` § 3.1 (opened) | The PRD now states four priorities and the SRS three, with nothing stating where `critical` sorts | `PRD.md:128`; `SRS.md:231`, `:647-648`; `fdr.md:175`, `:278-279` | `78b2a4c5b` |
| raise a companion item | `products/tracker17/docs/CONTENT_open_issues.md` § 3.1 (opened) | The terminology lists `critical` as a word not to use for priority, which the PRD now names | `CONTENT.md:150`; `PRD.md:128` | `fe1033d35` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| tracker17 · shukuba · 2026-10-08_setup-instructions | Not reached: 9 (added here) fails. 1–8 hold as measured. Walkable where it stands (shape 6): 9 is README wording, the station's own work, against SDD RT-4 and S-1 *Artifact* as they stand, and it still binds 8's 20-word limit. No close owed | Disposable copy `/tmp/t17refine.ngOD` (git-initialised): grep 1 → headings `README.md:58`, `:69`; grep 3 → exit 1, Status names `python3 main.py` (`:7`); grep 8 → exit 1; unreadable `data/tracker.json` → exit 1, stderr ends `See Setting saved data aside in the setup instructions.`, file unchanged; start prints `The tracker is running. Open http://127.0.0.1:8017 …`, matching `README.md:45` but the location, and the page title is `Projects - tracker17`, reached by the README's 2 commands; `pytest tests/` 224 passed; `pytest tests/e2e/` 12 passed ×3; `git status --short` empty |
| `test_a_created_project_is_listed_after_a_stop_and_a_start` timeout | Recorded twice on Codex runs (`halt_report.md`, `7325cabb1`) with no cause; passed on the integrity run and 3 of 3 here, so no occurrence now and no carrier | `code-integrity-report.md` § The finding; e2e ×3 above |
| No lasting test for the README's content rules | The integrity seat's call, held by the spec's continuity invariant; reached-when 8 is a grep a fresh session runs, so nothing is unowned | `code-integrity-report.md` § Calls made |
| tracker17 · nemawashi · 2026-10-07_first-project | Its last unticked line is the open station, not reached, so no retire. Its line needs no edit: reached-when 9 belongs to the stretch being walked | `seed.md:26` |
| `docs/nfdr.md` QC-40 | The previous refine's companion is folded: a dated exception runs to 2026-11-07, so design reviews are not blocked until then | `24aa9ecd8` |
| tracker17 · nemawashi · 2026-10-07_tasks-in-a-project | It says "a priority" without naming the set and rests on SDD S-2, which follows the SRS; the SRS and CONTENT items carry the change, so the seed's text is not stale | `unpicked/2026-10-07_tasks-in-a-project.md:5-7` |
| tracker17 · nemawashi · 2026-10-07_comment-on-a-task, status-moves | Nothing the unit found or upstream moved touches their scope | Upstream above |

## Absent

`deferred_decisions.md` — none written. `Deferred:` lines — none in `39cff98eb`. Halt report — present from the unit's first implementation run (`22b681de4`), superseded by the landed run; a sealed unit's halt report is read as history. I don't know whether the sweep carries the SRS's priority fold on into `fdr.md` R-51 and R-90 and SDD S-2 without their own companion items; the SRS item names those lines so the fold can see them.
