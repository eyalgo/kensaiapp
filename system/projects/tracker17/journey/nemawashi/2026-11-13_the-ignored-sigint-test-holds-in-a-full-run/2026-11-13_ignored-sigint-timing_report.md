# 宿場 Shukuba refine — `2026-11-13_ignored-sigint-timing`

*Unit `2026-11-13_ignored-sigint-timing`, sealed Tobiishi, reviewed 2026-11-13. Key named by the caller.
Station `the-ignored-sigint-cause` (root). Seed `2026-11-13_the-ignored-sigint-test-holds-in-a-full-run`.*

## Next moves

| # | Move | Whose | Command | After | From |
|---|---|---|---|---|---|
| 1 | close the reached station | Scrum Master | `<CORE>/launchers/skill/launcher.sh shukuba-retire tracker17 2026-11-13_the-ignored-sigint-cause` | — | Considered row 1 |
| 2 | retire a seed | Scrum Master | `<CORE>/launchers/skill/launcher.sh nemawashi-retire tracker17` | 1 | recommendation 1 |
| 3 | cut a seed | Principal PM | none — answered by `nemawashi-refine` after the seed's retire, which writes new product work onto the product's documents for `seeds-from-product-docs` to cut, and cuts work no document should state through `seeds-from-idea` | 2 | recommendation 2 |

## Read

| Artifact | Where | What it said, in a line |
|---|---|---|
| flow findings | `tracker17 · tobiishi · 2026-11-13_ignored-sigint-timing`, `flow_findings/development-specs.md` | 0 blocking, 2 change-local (I-5's grep could trip on a docstring; base line anchors not marked as the base's); both end with the unit — the diff grep printed nothing |
| flow findings | the same, `flow_findings/development-design.md` | 0 blocking, 1 change-local: the QC-40 browser-build fix owed by 2026-12-11 sits only in the design notes with no owner — work nothing carries, recommendation 2 |
| flow findings | the same, `flow_findings/development-plan.md` | 0 blocking, 1 change-local: the proof module's docstring was not held by review; the integrity pass read both docstrings (I-7), ends with the unit |
| flow findings | the same, `flow_findings/development-implementation.md` | 0 blocking, 1 change-local: the gate-environment line quotes the wrong clause; a record defect of the unit, ends with it |
| code-integrity report | the same, `code-integrity-report.md` | `Integrity: pass`, clean; no test added, nothing surfaced unfixed; corrects the developer's "most likely to bite" (the listing assertion still turns red at the base) |
| security report | the same, `security-report.md` | `Security: reported`, no hole. § Left for the PM: the dependency audit did not run, the NFDR names none — QC-40 already says so, no companion owed (Considered row 3) |
| developer's closing commit | `<a commit not in the public history>` | cause is a launched pytest with no base folder cleaning the shared temp root; fix gives it `--basetemp` under `tmp_path`; the earlier halt (builder refused the red) did not recur; no divergence beyond naming NFDR QC-11 in the docstring |
| deferred decisions | absent — the unit wrote none | — |
| the closing commit's `Deferred:` lines | `<a commit not in the public history>` | absent — no line begins `Deferred:` |
| corrections owed | the same, `tl_instruction.md` | absent — the plan has no § Corrections owed while there |
| work handed on | the same, `change_spec.md` § Out of Scope | fences only: the inherited ignored SIGINT stays ignored, held by `test_arming_preserves_an_inherited_ignored_sigint`; nothing handed on |

## Upstream

`git log --since=2026-11-13T13:51:17+01:00 --name-status -- products/tracker17/docs/` → FDR v7 then v8 Settled (`2f52b5ac5`, `023af2b2e`, `243f1f6f6`, due-today count at R-129 to R-131, companion moved to `docs/trail/fdr/cycle-5.md`); SDD v23 Settled (`a7d393293`, `edd4235e1`, S-6 re-cut carries the count, companion moved to trail). None is a source of this seed or its station. No live `*_open_issues.md` under `products/tracker17/docs/` (`ls products/tracker17/docs` → none).

## Held

None. `system/logs/chain-tracker17-state.json`: `ended` = `settled`, so no docs chain is in flight. No change unit is open at `journey/tobiishi/`'s root (`ls` → `trail` only).

## Moves

| Move | On | Why | Source | Commit |
|---|---|---|---|---|
| modify a seed | `tracker17 · nemawashi · 2026-11-13_the-summary-shows-the-due-today-count` | Its § Relation still said it waits on the FDR, which omitted the count at version 6; the FDR now states it, so the wait is removed and a divergence line logged | `products/tracker17/docs/fdr.md` L332-L337 (R-129 to R-131), Status Settled, version 8; `243f1f6f6` | `7de9ac095` |
| modify a seed | `tracker17 · nemawashi · 2026-11-13_the-sdd-carries-the-due-today-count` | Its prose states the SDD lacks the count as current; SDD v23 Settled carries it and the companion is gone, so a divergence line says the seed wants a pick and a close | `grep -ciE 'due.today' products/tracker17/docs/SDD.md` → 28; `edd4235e1` | `7de9ac095` |
| modify a seed | `tracker17 · nemawashi · 2026-11-13_the-content-carries-the-due-today-count` | The same for CONTENT: v22 Settled has the "Due on {date}" term row and no companion | `products/tracker17/docs/CONTENT.md` L166; `f3749d5bf` | `7de9ac095` |

## Considered, not moved

| Seed, station or document | Why it stays | Source |
|---|---|---|
| `tracker17 · shukuba · 2026-11-13_the-ignored-sigint-cause` | All four reached-when items hold on `main` now; the close is the Scrum Master's (Next moves 1) | disposable clone at `243f1f6f6`: (1) `test_sigint_launch_temp_root.py` present, shown red at base `8c3f7e74d` by the integrity report § Test evidence; (2) the proof test alone and the measurement → `2 passed`; (3) `pytest products/tracker17/tests/` → `3336 passed, 2 skipped`, exit 0; `pytest products/tracker17/tests/e2e/` → `122 passed`, exit 0; (4) `git diff 8c3f7e74d 2b06c9afd^2 -- products/tracker17 \| grep -nE '^\+.*(mark\.(skip\|skipif\|xfail)\|xfail\|retry\|flaky\|reruns)'` → nothing, and the diff of `test_start.py` is empty |
| `tracker17 · nemawashi · 2026-11-13_the-ignored-sigint-test-holds-in-a-full-run` | Its one station is reached, so once the close lands it is fully walked; the retire is recommended (recommendation 1), not made | `tracker17 · nemawashi · 2026-11-13_the-ignored-sigint-test-holds-in-a-full-run` (line 15) — the only station line |
| `products/tracker17/docs/nfdr.md` QC-40 | The security line asks the NFDR to state that no dependency audit exists, and QC-40 already says so | `security-report.md` § Left for the PM; `nfdr.md` QC-40 *verified by* — "no audit command exists for this product" |
| `products/tracker17/docs/nfdr.md` QC-40, browser build | No companion: QC-40 already states the 30-day window and the two ways out (move the pin, or the owner's dated exception); what is owed is work, not a document change | `products/tracker17/docs/nfdr.md` L475-L486 |
| `tracker17 · nemawashi · 2026-11-13_the-srs-carries-the-due-today-count`, `tracker17 · nemawashi · 2026-11-13_the-uxd-carries-the-due-today-count` | Already say their work is on disk and they want a pick and a close; nothing stale | each seed's § Relation to existing work |
| `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract` | The unit touched no fake or contract suite; nothing it carries moved | `git diff --stat 8c3f7e74d 2b06c9afd^2 -- products/tracker17/tests` → the two sigint test modules only |
| shape 6 | No unticked station is left on the active seed after the reached one, so no next bar to measure | `tracker17 · nemawashi · 2026-11-13_the-ignored-sigint-test-holds-in-a-full-run` (line 15) |

## Absent

`deferred_decisions.md` (the unit wrote none); `Deferred:` lines (none in `<a commit not in the public history>`); § Corrections owed while there (not in `tl_instruction.md`). The unit's `halt_report.md` is a leftover from the developer's earlier halted run, whose cause did not recur (`<a commit not in the public history>` Developer Review Notes); read, owes nothing.
