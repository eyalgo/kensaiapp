# 宿場 Shukuba refine — `2026-10-21_out-of-date-move`

*Unit `2026-10-21_out-of-date-move`, sealed Tobiishi, reviewed 2026-10-21 (key named by the caller; `CONTEXT_PM.md` names the same, `Sealed`).
Station `2026-10-21_out-of-date-move` (root). Seed `2026-10-07_status-moves`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | sweep the product's companions | owner | `<CORE>/launchers/chain-product/launcher.sh tracker17` | — | Moves rows 2, 3 |
| 2 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-10-21_out-of-date-move` | — | Considered row 1 |
| 3 | readme-status | Content Editor | `<CORE>/launchers/skill/launcher.sh readme-status tracker17` | 2 | Considered row 1 |
| 4 | walk the next change | owner | `<CORE>/launchers/chain-change/launcher.sh tracker17` | 2 | Considered row 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-10-21_out-of-date-move`, `flow_findings/development-specs.md` | 0 blocking; 3 change-local (a downstream review named, a press for a missing task uncovered, pinned words beside the content stage) — end with the unit. |
| flow findings | same, `flow_findings/development-design.md` | 0 blocking; 1 change-local (build order stated in the design) — ends with the unit. |
| flow findings | same, `flow_findings/development-plan.md` | 0 blocking; 3 change-local. The CONTENT fifth-example correction had no durable home → companion item (Moves row 2). The other two (an unowned test constant, Task 3's verdict home) end with the unit. |
| flow findings | same, `flow_findings/development-content.md` | 0 blocking; 1 change-local: the "offers one move" string has no reachable case (Considered row 4). |
| flow findings | same, `flow_findings/development-implementation.md` | 0 blocking; 2 change-local, both about the closing commit's own quotes (`__version__`, Toolchain) — end with the unit. |
| code-integrity report | same, `code-integrity-report.md` | `Integrity: pass`; no bug; one coverage gap closed in place (a title that forms markup, 6 integration + 4 browser cases); 1316 passed; surfaced no candidate seed. |
| developer's closing commit | `61b380e78` | No divergence from the instruction; two cases added beyond it; CONTENT fifth example left as owed outside reach; one open deferred record gap left for this run. |
| deferred decisions | same, `deferred_decisions.md` | One record gap, **Owner: none**: a refused press's landing page reopened by reload, Back or bookmark (CONTENT RN-26) → companion item § 3.2 (Moves row 3). |
| the closing commit's `Deferred:` lines | `61b380e78` | Absent — the body carries no line beginning `Deferred:` (`git show -s --format=%B 61b380e78 \| grep -n "Deferred:"` prints nothing). |
| corrections owed | same, `tl_instruction.md` § Corrections owed while there | One *Owed outside this change's reach*: `docs/CONTENT.md` fifth refusal example offers a reload → measured still there (`docs/CONTENT.md:219`); companion item § 3.1 (Moves row 2). |
| work handed on | same, `change_spec.md` § Out of Scope | Reopened landing page → companion § 3.2 (Moves row 3). Timed run → seed item 4 `move-timed-run`, already carrying it. CONTENT fifth example → companion § 3.1. Workflow, data format, confirmation, history and page script only fence. |

## Upstream

`git log --since=2026-10-07T02:17:39+02:00 -- products/tracker17/docs/` (the seed's first commit, `5d9a6ce09`). Since the previous refine of this seed, all 2026-10-21: SDD v11 (`9c7db2266`, § 6 `status-moves` offers no reload and names the no-press refusal; § 4 RT-11), ADR-0010 and NFDR v14 (`b4810919c`, the 202 history boundary as QC-63) and NFDR v15 (`5982d98c3`). Each closed its companion. Live `*_open_issues.md` before this run: none (`find products/tracker17/docs -name '*open_issues*' -not -path '*/trail/*'` prints nothing). After it: `CONTENT_open_issues.md` (Moves rows 2, 3).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended: settled`, `pending: null`, so no product chain is in flight. `system/logs/chain-change-tracker17-state.json`: key `2026-10-21_out-of-date-move`, `pending: refine`, which is this run. No open unit at `journey/tobiishi/`'s root.

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a seed; modify a station | `tracker17 · nemawashi · 2026-10-07_status-moves` (line 29); `tracker17 · shukuba · 2026-10-21_out-of-date-move` (Guardrail, last bullet) | Both still called the SDD S-4 reload wording owed on a companion; SDD v11 folded it, so the fact is repaired everywhere it is stated. Not a re-aim: no reached-when changed. | `products/tracker17/docs/SDD.md:882-885`; `9c7db2266` | `72ff07ae0` |
| raise a companion item | `products/tracker17/docs/CONTENT.md` § 3.1 | The refusal formula's fifth example still says "Reload the page to see it", which UXD v8, SDD v11 and the shipped words all rule out. | `products/tracker17/docs/CONTENT.md:219`; `products/tracker17/web/pages.py:752-757`; `tl_instruction.md` § Corrections owed while there | `43aecc578` |
| raise a companion item | `products/tracker17/docs/CONTENT.md` § 3.2 | RN-26 waits for a reloaded-press occurrence that now exists, and cites `web/pages.py:760` "the move you pressed", which no longer does; the reopened landing page has no rule to be written against. | `products/tracker17/docs/CONTENT.md:556`; `products/tracker17/web/routes.py:384-392`; `products/tracker17/web/pages.py:752`; `grep -rn "the move you pressed" products/tracker17/web` → exit 1; `deferred_decisions.md` | `43aecc578` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-10-21_out-of-date-move` — close owed | Reached: all four reached-when items hold on `main`. Items 1–3 are the tests the integrity report maps to CP-355/359, CP-356/361 and CP-366, all passing. | Fresh clone at `774fe17c2`: `pytest products/tracker17/tests/integration/` → `995 passed`; `pytest products/tracker17/tests/` → `1316 passed`; `grep -rn "the move you pressed" products/tracker17/web` → exit 1; `code-integrity-report.md` § Checked against that intent |
| `tracker17 · nemawashi · 2026-10-07_status-moves` (line 20) `move-timed-run` — shape 6 | Reachable where it stands: QC-48 asks every SRS NFR-1 action timed at 1,000 tasks × 20 comments by `tests/timed_run.py`, and "a change that adds a listed action adds it to the run". The harness, its fixture (`TASK_VOLUME = 1000`, `COMMENTS_PER_TASK = 20`) and `tests/integration/test_timed_run.py` exist; the move path exists; timing a move is this station's own work. Re-aimed 0 times, so no owner's act. It reads no CONTENT rule, so it does not wait on the sweep. | `products/tracker17/docs/nfdr.md:429-436` (QC-48); `products/tracker17/tests/timed_run.py:57-67`; `ls products/tracker17/tests/timed_run.py products/tracker17/tests/integration/test_timed_run.py` |
| `tracker17 · nemawashi · 2026-10-07_status-moves` (line 7) | Its prose bar is SDD S-4 and AC-12; still current after SDD v11. | `products/tracker17/docs/SDD.md:878-892` |
| `products/tracker17/web/pages.py:754` "can be moved to {0}." | The one-move string has no reachable case: no status offers exactly one move. Unreachable copy is a code fix, not route work, and no behaviour is wrong. | `products/tracker17/domain/workflow.py:47-52`; `flow_findings/development-content.md` |
| `tracker17 · nemawashi · 2026-10-11_delete-and-rename`, `…_narrow-and-sort`, `…_project-summary`, `…_protect-saved-data` | Nothing in this unit or the 2026-10-21 doc moves touches their sources; the unit changed only the move refusal words and their context. | `code-integrity-report.md` § What was reviewed (`web/pages.py`, `web/routes.py`, three test modules) |

## Absent

`halt_report.md`: a sealed unit has none. The closing commit's `Deferred:` lines: none written.
