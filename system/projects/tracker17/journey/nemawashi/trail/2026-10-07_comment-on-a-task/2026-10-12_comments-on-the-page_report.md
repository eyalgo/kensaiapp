# 宿場 Shukuba refine — `2026-10-12_comments-on-the-page`

*Unit `2026-10-12_comments-on-the-page`, sealed Tobiishi, reviewed 2026-10-12. Key named by the caller; `contexts/CONTEXT_PM.md` names the same key, `**Status:** Sealed`.
Station `2026-10-12_comments-on-the-page` (root). Seed `2026-10-07_comment-on-a-task`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves row 1 |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17` | — | Considered row 1 |
| 3 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 2 | Considered row 1 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 1, 2 | Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `journey/tobiishi/trail/2026-10-12_comments-on-the-page/flow_findings/` — `development-specs.md`, `development-design.md`, `development-plan.md`, `development-content.md`, `development-implementation.md` | 0 blocking, 15 change-local (specs 6, design 4, plan 2, content 0, implementation 3), 0 skill-general. The specs finding on CP-273 asks this review to confirm the request's timed-run boundary (Considered row 3); the plan finding on RN-15 and the test command is Considered rows 4–5; the rest are coverage, altitude and evidence notes on this unit's own records, naming no unowned work (Considered row 6) |
| code-integrity report | `…/code-integrity-report.md` | `Integrity: pass` at `560c28c62`; one test added (title escaping in the comment lines), mutation-proved; calls 1 (`__version__` in product code, the owner's) and 2 (`comment_added=02`, the Architect's) are code calls, not route work |
| developer's closing commit | `560c28c62` | Review Notes: width repair `5d3955761`, a facts clause asserted `4c9d8513b`, the `__version__` question raised not settled; rule discrimination for `_comment_outcome` and `_add_comment` shown by case design, not mutation |
| deferred decisions | `…/deferred_decisions.md` | Four entries, each with an owner on the route: delete with comments → `tracker17 · nemawashi · 2026-10-11_delete-and-rename`; unreadable-data pages → `tracker17 · nemawashi · 2026-10-11_protect-saved-data`; status on the task page → `tracker17 · nemawashi · 2026-10-07_status-moves`; CP-273's timed comment add → item 3 `full-volume-run` on this seed (Considered rows 2–3, 7) |
| the closing commit's `Deferred:` lines | `560c28c62` | absent — `git log -1 --format=%B 560c28c62 \| grep -n '^Deferred:'` printed nothing, exit 1 |
| corrections owed | `tl_instruction.md` § Corrections owed while there | One *Owed outside this change's reach* line: `docs/nfdr.md` RN-15's "no product code has moved since" → companion item § 3.1 (Moves row 1) |
| work handed on | `change_spec.md` § Out of Scope | Assignee timing → `full-volume-run` already carries it; delete with comments, unreadable-data pages, status on the task page → the three seeds above; the rest only fence (threaded replies, edit/delete a comment, wording, Your name) |

## Upstream

`git log --since=2026-10-07T02:17:39+02:00 --name-status -- products/tracker17/docs/` since the seed's first commit, the moves since the previous refine: SDD v10 settled `376226bc5` (§ 3 `application` row names what each reporting action compares); NFDR v12 settled `1e9f21d7e` (QC-21 compares per action, QC-47 names the fresh clone); UXD v6 `5d32fb74e`; CONTENT v10 `78b41c07e`; `what_left.md` `d4ea7c2be`. No seed or station outside `trail/` cites QC-21, QC-47 or `git archive` except the open station's item 8, which already names the fresh clone (`grep -rn -i 'git archive\|QC-21\|QC-47' system/projects/tracker17/journey`, excluding trail, drop and refine records → `tracker17 · shukuba · 2026-10-12_comments-on-the-page` (line 18) only). Live `*_open_issues.md` before this run: none (`find products/tracker17/docs -name '*_open_issues.md' -not -path '*/trail/*'` printed nothing). This run opened `architecture_open_issues.md` (Moves row 1).

## Held

None. `system/logs/chain-tracker17-state.json`: `"ended": "settled"`, `"pending": null`, so no chain is in flight. `journey/tobiishi/` holds only `trail/`, so no open unit walks a seed or station.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| raise a companion item | `products/tracker17/docs/architecture_open_issues.md` § 3.1, on `nfdr.md` RN-15 | RN-15 says no product code has moved since the People focus run at `641bb58b5`, and it has, so the recorded Chromium verdict no longer names the tree it describes | `nfdr.md:L736-L738`; `git diff --stat 641bb58b5 4f6f59752 -- products/tracker17/web products/tracker17/domain` → `12 files changed, 2350 insertions(+), 26 deletions(-)`; `tl_instruction.md` § Corrections owed while there | `7f9532d83` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| 1. `tracker17 · shukuba · 2026-10-12_comments-on-the-page` | Reached-when 1–8 hold now; the close is the Scrum Master's | Fresh clone at `4f6f59752`, under a pty, pinned venv: `pytest products/tracker17/tests/` → `1047 passed`, exit 0; `pytest products/tracker17/tests/e2e/` → `33 passed`, exit 0. Items 1–4: `tests/integration/test_comment_pages.py:L200-L282`, `:L296-L335`, `:L427`, plus `test_comment_routes.py` and `test_comment_tracker.py`; item 5: `tests/e2e/test_comments.py:L89`, `:L127`; item 6: `tests/integration/test_saved_data.py:L1305`; item 7: `ls products/tracker17/domain/comments.py` lists it |
| 2. `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`, item 3 `full-volume-run` | Reachable where it stands (shape 6): QC-48 asks every NFR-1 action timed at 1,000 tasks × 20 comments, same-origin, failing on a refusal; the comment add route and both assignee routes exist now, the 1,000 × 20 fixture is seeded, and the timing is the station's own work. Re-aimed once by a refine (the operator-name refine's dated line), so no owner's act | `nfdr.md:L412-L419` (QC-48); `SDD.md:L462-L465` (TS-5); `web/routes.py:L95-L96`, `:L104`; `tests/timed_run.py:L11`, `:L157`; `seed.md` dated line "2026-10-12, shukuba-refine after `tracker17` unit `operator-name`" |
| 3. CP-273's timed comment add (specs audit asked for confirmation) | Confirmed: the request's must-not held — both timed-run files are byte-identical — and the work has its owner, item 3 `full-volume-run`, whose line already names "its comment add and that add's landing page" | `code-integrity-report.md` § Verification (`git diff --exit-code 3b5746f91 -- …timed_run.py …test_timed_run.py` exit 0); `seed.md` § Stations, item 3 |
| 4. Project card `Test command:` omits `tests/e2e/` (plan finding) | Not a defect: NFDR § 10 states the card's command is `pytest tests/` and names `pytest tests/e2e/` beside it as the second suite; the station bar runs both | `nfdr.md:L553-L557`; `tl_instruction.md:L68` |
| 5. SDD § 3 `web` row vs `_comment_outcome`'s position bound (implementation finding) | The row forbids rules about moves, overdue and counts and any state kept; a bound on an address value the design assigned to the route is none of these, so no document gap | `SDD.md:L204`; `flow_findings/development-implementation.md:L10` |
| 6. Remaining change-local findings (specs coverage/altitude, design divergence-record and coverage, plan CP-263 restart through the page, implementation evidence) | About this unit's own records; none names work left without an owner | `flow_findings/*.md` |
| 7. `tracker17 · nemawashi · 2026-10-11_delete-and-rename`, `…2026-10-11_protect-saved-data`, `…2026-10-07_status-moves` | Each already carries the deferred entry handed to it | `tracker17 · nemawashi · 2026-10-11_delete-and-rename` (line 7), `:L19`; `tracker17 · nemawashi · 2026-10-11_protect-saved-data` (line 9), `:L19`; `tracker17 · nemawashi · 2026-10-07_status-moves` (line 5) |
| 8. `seed.md` § Source, "`domain/comments.py` does not exist … The work is still owed" | A dated re-check ("Product re-checked on 2026-10-12"), a record of what held then; the route's remaining item still owes work, so it is left as written | `seed.md` § Source |

## Absent

Halt report — not produced by a sealed unit. Every other row of the unit's shape was read.
