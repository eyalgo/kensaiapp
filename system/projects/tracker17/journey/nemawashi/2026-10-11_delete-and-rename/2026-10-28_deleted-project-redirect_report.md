# 宿場 Shukuba refine — `2026-10-28_deleted-project-redirect`

*Unit `2026-10-28_deleted-project-redirect`, sealed Tobiishi, reviewed 2026-10-28.
Station `deleted-project-redirect` (root). Seed `2026-10-11_delete-and-rename`.*

Key named by the caller; the project's PM context names the same key, `Status: Sealed`.

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-28_deleted-project-redirect` | — | Considered row 1 |
| 2 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 1 | Considered row 1 |
| 3 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1 | Considered row 2 |
| 4 | cut a seed | Principal PM | none — answered by `nemawashi-refine` after the seed's retire, which writes new product work onto the product's documents for `seeds-from-product-docs` to cut, and cuts work no document should state through `seeds-from-idea` | — | recommendation 1 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `flow_findings/development-specs.md` | 0 blocking; 3 change-local (mechanism anchors in rules, step named in CP-608, action-time path not mandated by CP-602); the integrity pass's 12-fail break on the action-time redirect covers the third |
| flow findings | `flow_findings/development-design.md` | Clean |
| flow findings | `flow_findings/development-plan.md` | 0 blocking; 3 change-local (gate cannot pass on a red base, overlong-text case unnamed, shared-builder clause held by review only); the base is now green, see Considered row 1 |
| flow findings | `flow_findings/development-implementation.md` | 0 blocking; 3 change-local (Step 1b count understates by one, the initial lookup check is held by review only, Language resolution quotes do not carry their verdicts); none leaves work unowned |
| code-integrity report | `code-integrity-report.md` | `Integrity: pass`; three tests tightened; five deliberate breaks each fail tests; nothing surfaced unfixed |
| security report | `security-report.md` | `Security: reported`, no hole. § Left for the PM: the dependency audit did not run because the NFDR names none — Considered row 4 |
| developer's closing commit | `<a commit not in the public history>` | Divergence notes: deleted-project matrices delete through the application call, not the press; mixed readable/unreadable tests split; e2e run via the product's pinned env; a stale design halt report left in the folder |
| deferred decisions | `deferred_decisions.md` | One entry, a route number too long to read as an identity answered 404 directly, `Owner: none` — no seed carries it; recommendation 1 |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — the body has no line beginning `Deferred:` (`git log -1 --format=%B <a commit not in the public history> \| grep -n '^Deferred:'` → nothing) |
| corrections owed | `tl_instruction.md` § Corrections owed while there | absent — the plan has no such section (`grep -n "Corrections owed" tl_instruction.md` → nothing) |
| work handed on | `change_spec.md` § Out of Scope | The unreadable-number line hands on to `deferred_decisions.md` (recommendation 1); Delete task's confirmation size is carried by `tracker17 · nemawashi · 2026-10-11_delete-and-rename` (line 21); the other lines only fence |
| halt report | `halt_report.md` | Stale: development-design halted on a refused PyPI read for QC-40; the design later landed at `5798235a1` with QC-40's review done through OSV (`change_design.md:173-190`). Nothing owed |

## Upstream

`git log --since=2026-10-11T18:13:32+02:00 --name-status -- products/tracker17/docs/` → 108 commits. Since the last refine on this seed (`958a36c7c`, 17:35): SDD v14 settled (`0ac110bab`), NFDR v18 settled (`66e29daa9`), `what_left.md` updated (`75eb81760`). Both folds are the deletion-test pointers the previous refine raised; neither moves a line the open station or the next one reads. No live `*_open_issues.md` under `products/tracker17/docs/` (`ls products/tracker17/docs/*open_issues*` → no matches).

## Held

None. `system/logs/chain-tracker17-state.json` has `ended: settled`, `pending: null`; `system/logs/chain-change-tracker17-state.json` is pending on this refine step for this key; no open unit at the `tobiishi/` root besides `trail/` and `drop/`.

## Moves

None — no move was owed; see below.

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-28_deleted-project-redirect` | Reached-when holds; its close is owed to the Scrum Master. Item 1 rests on the route tests at the HTTP layer; items 2–4 measured | fresh clone at `2600b3b5e` (= HEAD for `products/tracker17`): `pytest products/tracker17/tests/` → `2629 passed`, exit 0; `uv run pytest tests/e2e/` → `117 passed`, exit 0; `git grep -n 'len(rows)' -- products/tracker17/web/pages.py` → nothing, exit 1; `products/tracker17/web/routes.py:873-874`, `:904-905` redirect; tests at `test_task_routes.py:475`, `test_rename_routes.py:260`, `test_delete_project_pages.py:203`; red commit `97e37d9d8` |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename` (line 21), next station `task-delete-full-size-confirm` | Walkable where it stands: DESIGN's clause sizes Delete task's strip to `spacing.control`; the product passes `size=TRIGGER_SIZE` (`row-control`) and a `.strip-control` style already exists, so the work is the station's own; one re-aim (its creation), under two, so no owner's act | `products/tracker17/docs/DESIGN.md:457-466`; `products/tracker17/web/pages.py:765`, `:861`; `products/tracker17/web/style.css:316-325`, `:334-355` |
| `tracker17 · nemawashi · 2026-10-11_protect-saved-data` | Nothing the unit found or that moved upstream touches it | the seed's checklist (lines 17–19); Upstream above |
| `products/tracker17/docs/nfdr.md` QC-40, dependency audit | The NFDR already states no audit command exists; no companion item owed | `security-report.md` § Left for the PM; `products/tracker17/docs/nfdr.md:354-376` |
| `products/tracker17/docs/nfdr.md` QC-7, unreadable route number | The document is clear ("every submission is answered by sending the browser to a page address"); the product falls short of it, so this is work, not a document gap — recommendation 1 | `products/tracker17/docs/nfdr.md:73-77`; `products/tracker17/web/routes.py:869-871`, `:900-902`, `:937-938` |

## Absent

The closing commit's `Deferred:` lines and the plan's § Corrections owed while there — neither was written (Read rows above).
