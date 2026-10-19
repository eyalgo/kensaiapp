# 宿場 Shukuba refine — `2026-10-12_operator-name`

*Unit `2026-10-12_operator-name`, sealed Tobiishi, reviewed 2026-10-12.
Station `2026-10-12_operator-name` (root). Seed `2026-10-07_comment-on-a-task`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves rows 3, 4 |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17` | — | Considered row 1 |
| 3 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 2 | Considered row 1 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1, 2 | Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `journey/tobiishi/trail/2026-10-12_operator-name/flow_findings/` — `development-specs.md`, `development-design.md`, `development-plan.md`, `development-content.md`, `development-implementation.md` | 0 blocking, 11 change-local (specs 4, design 2, plan 1, implementation 4, content 0), 0 skill-general. Coverage and evidence notes on this unit's own records; none names unowned work (Considered rows 3–5) |
| code-integrity report | `…/code-integrity-report.md` | `Integrity: pass` at `9036cc6ed`; 35 of 36 mutations killed (the survivor equivalent); three packet fixes made in place; calls 2–4 (sibling bare `Enum`s, sibling timer defaults, no product `__version__`) left to the Tech Lead — code conventions, not route work |
| developer's closing commit | `9036cc6ed` | `Suite: green`; divergences: future import after docstring, bare `Enum` for the new refusal (both corrected by integrity), tests under `unit/integration/e2e`; corrections owed outside reach left as they stand |
| deferred decisions | `…/deferred_decisions.md` | 1. unreadable-data pages (FDR R-25, R-26) → owned: `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (line 19). 2. comments (R-71–R-75) → owned: this seed's `comments-on-the-page`. 3. timing the assignee add and remove (QC-48) → unowned; carried, Moves row 2. 4. CP-239 clone reading → now the contract's own rule; Moves rows 1, 4 |
| the closing commit's `Deferred:` lines | `9036cc6ed` | absent — `git log -1 --format=%B 9036cc6ed \| grep '^Deferred:'` → nothing |
| corrections owed | `…/tl_instruction.md` § Corrections owed while there | 1. SDD § 3 application row → SDD companion § 5.1 (Moves row 3). 2. NFDR QC-21 → architecture companion § 3.1 (Moves row 4). 3. NFDR QC-47, RN-28 → architecture companion § 3.2 (Moves row 4). 4. station Reached when item 5 → Moves row 1 |
| work handed on | `…/change_spec.md` § Out of Scope | comment form, no-name notice, earlier-name rule → `comments-on-the-page` (`seed.md:L18`); comment timing → `full-volume-run` (`seed.md:L19`); `domain/comments.py` → `comments-on-the-page`; unreadable-data pages → `protect-saved-data`; assignee timing → Moves row 2; maximum sentence, Assignees behaviour, wording → fences only |

## Upstream

`git log --since=2026-10-07T02:17:39+02:00 --name-status -- products/tracker17/docs/` (seed first
committed then): SDD v8 → v9 (`c2e7d0e7e`, `33ad1a2a7`), NFDR v10 → v11 (`ceac03d4b`, `df8ac27ea`),
CONTENT v9 → v10 (`64431490b`, `78b41c07e`), UXD v5 → v6 (`7634a24bd`, `5d32fb74e`), `what_left.md`
(`2010c559e`, `8df0e5156`, `d4ea7c2be`); every companion folded and moved to `docs/trail/`. None
moves this seed's sources: SDD § 3 entities, § 4 and § 6 S-3 stand. No live `*_open_issues.md`
before this run (`ls products/tracker17/docs/*_open_issues.md` → no matches); this run opened two
(Moves rows 3, 4).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null` — no product chain
in flight. `system/logs/chain-change-tracker17-state.json` is in flight on this unit's own refine
step, with no `spine`. No open unit at `journey/tobiishi/`'s root (`ls` → `trail` only).

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| 1. modify a station | `tracker17 · shukuba · 2026-10-12_operator-name`, Reached when item 5 | Shape 6: the bar ran the suite on a `git archive` copy, which cannot exit 0, and the cross-role contract now requires a fresh clone at the tested commit; re-aimed to the clone (re-aim 1 of this station) | archive copy at `2866e76de`: `pytest products/tracker17/tests/` → `1 failed, 936 passed` (`test_data_is_ignored_by_version_control`, `fatal: not a git repository`); clone at `2866e76de` → `937 passed`; `core/roles/CROSS_ROLE.md:L14-L19`; `tl_instruction.md` Corrections owed, line 4 | `11394222c` |
| 2. modify a seed | `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`, `full-volume-run` | Deferred entry 3 has no owner: QC-48 has a change that adds a listed action add it to the run, and the timed run has no assignee action; the timed-run station carries it, divergence logged | `products/tracker17/tests/timed_run.py:L525-L555` (`main` times tasks, edit, labels, name); `products/tracker17/docs/nfdr.md:L404-L408`; `deferred_decisions.md` § Timing the assignee add and remove | `11394222c` |
| 5. raise a companion item | `products/tracker17/docs/SDD_open_issues.md` § 5.1 (opened) | Correction owed 1: SDD § 3 says every report compares with the value the page showed; the operator name compares with the saved name | `products/tracker17/docs/SDD.md:L202`; `products/tracker17/domain/operator_name.py:L59-L62`; `products/tracker17/tests/integration/test_people_routes.py:L520-L533` | `4db8c9d5c` |
| 5. raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1, § 3.2 (opened) | Corrections owed 2 and 3: QC-21 carries the same comparison sentence; QC-47 and RN-28 name an archive copy the contract no longer uses | `products/tracker17/docs/nfdr.md:L171-L173`, `L396-L397`, `L908`; `core/roles/CROSS_ROLE.md:L14-L19`; the measurement in row 1 | `15b201d62` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| 1. `tracker17 · shukuba · 2026-10-12_operator-name` | Reached as amended: close owed to the Scrum Master. Item 1–3: the tests exist and pass. Item 4: the e2e test exists; its run is the integrity pass's (machine pytest here has no `playwright`). Item 5: clone run passes | `test_people_pages.py:L511`, `test_people_routes.py:L483`, `L537`, `L558`, `L838`, `e2e/test_people.py:L261`; clone `pytest products/tracker17/tests/` → `937 passed`; `code-integrity-report.md` § The finding (`e2e/` 29 passed at `fc2b2f24c`) |
| 2. `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`, `comments-on-the-page` (next unticked) | Shape 6: can be met where it stands. The saved operator name it writes under now exists; `domain/comments.py`, the form, notice, refusals, AC-20's test and SD-5's start check are its own work. Re-aimed once by a refine (2026-10-11), so no owner's act | `products/tracker17/domain/operator_name.py`; `products/tracker17/docs/SDD.md` § 6 S-3; `seed.md` dated line 2026-10-11 |
| 3. CP-229's task-page half (design and plan findings) | No test shows the task page unchanged after a name is saved; the next station replaces that page's comment area, so the claim expires there | `flow_findings/development-design.md:L25`; `flow_findings/development-plan.md:L45` |
| 4. e2e history-navigation assertion (implementation finding) | The route test covers repeated landing GETs never saving; a change-local evidence note on the developer's record, not route work | `flow_findings/development-implementation.md:L33`; `tests/integration/test_people_routes.py` `test_name_landing_gets_never_repeat_save` |
| 5. spec findings (CP-223 origin test, CP-216/217/219/224 cases, CP-227 evidence, CP-238 altitude) | CP-223's test was added by the plan; the rest are change-local notes on the spec's own altitude and coverage | `flow_findings/development-specs.md:L56-L59`; `tl_instruction.md` Task 4 `test_operator_name_submission_origin_checks_run_before_action` |
| 6. `products/tracker17/docs/fdr.md` R-25, R-26 | Owned by `protect-saved-data`'s `unreadable-data-page` | `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (line 19) |
| 7. the other unpicked seeds | No source moved and no finding lands on them | Upstream above |

## Absent

The closing commit's `Deferred:` lines (none). A product test environment in the main checkout
(`products/tracker17/.venv` absent; machine `pytest` used, without `playwright`, so the e2e layer
was not re-run here).
