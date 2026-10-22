# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-20_history-after-confirm`, on the station `tracker17 · shukuba · 2026-10-19_cancel-confirmation`.
**Date:** 2026-10-20
**Reviewed at:** the developer's newest closing marker `025a7406f` (`developer: 2026-10-20_history-after-confirm — implementation complete`), which supersedes `c7dacd5fd`.

## Summary

The code does what its intent says. A confirmation that the page actually shows is answered with
202, every other page keeps its 200 or 404, and the `Clear-Site-Data` header is gone. Back to a
confirmation's address now shows the saved status, on the task's page and at the task's row. No bug
was found. One gap was closed: the card's suite does not collect the browser folder, so it had no
check of what the confirmation's address shows once the task is `done`. A test now covers that, for
both pages and both final statuses. Two over-long lines in the same test file were wrapped. Nothing
was moved. The card's suite passed 1250 through the gate tool. The browser folder passed 67, with
nothing skipped.

## Deferrals

The marker was read with `git -C <worktree> log -1 main..2026-10-20_history-after-confirm --grep='2026-10-20_history-after-confirm — implementation complete' --format=%B`.

**None.** The marker reads `Deferred: none`, so there is nothing to check and no task is held out of this review.

## What was reviewed

The product diff from the merge base `61f97a0b2` to `025a7406f`, under `products/tracker17`:
`web/routes.py`, `tests/integration/test_routes.py`, `test_move_routes.py`, `test_move_pages.py`
and `tests/e2e/test_moves.py`. That is 5 files, 399 lines added and 72 removed. The one production
delta is `Site._pending_status` (`web/routes.py:322-333`) and its two call sites in `_task_page` and
`_project_page`, plus the removal of `CACHE_EVICTION` from a successful move's redirect.

## The intent it was checked against

- `tl_instruction.md`: Tasks 1–3, their *Behaviours to verify*, *Held by review*, and the TL Review Notes.
- `change_spec.md`: CP-343 to CP-354, the Examples and the Locked Answers.
- `change_design.md`: § 1's response contract ("Select 202 from the **resolved presentation**, not merely the presence of `move_confirm` in the query"), § 2, § 4, and § 5's T1–T15 with its retired assertions.
- `docs/fdr.md` was not needed: the spec names the rules it rests on.

Checked against the code. `_move_view` returns an interaction only after outcome precedence, task
membership on this page, and the saved workflow's answer (`web/routes.py:340-366`). `pages.py` draws
the strip exactly when that interaction is `CONFIRM` (`web/pages.py:729`, `:874-878`, `:1354-1360`).
So "202 ⇔ a strip is shown" holds by construction. No HTML is inspected and no workflow table is
repeated. `no-store` keeps its scope (`_stored_as_asked`, unchanged). No script, cookie, session,
interception or cache-disabling flag was added. The fixture is unchanged, and the matrix asserts
browser `153.0.8010.12`.

## The tests added or fixed

- **Added:** `tests/integration/test_move_routes.py::test_confirmation_address_at_a_final_status_shows_the_saved_status`,
  4 cases: list and task page × `done` and `cancelled`. CP-343: once the saved status disallows the
  move, the confirmation's address (what Back now reaches) answers 200 and shows no strip, no
  sentence and no move form for the task. The status word holds the one focus, and its description
  names the saved status. Nothing is saved. It does not pin the refusal's words, as CP-343 and the
  TL's scope boundary require. **Why:** the existing integration checks cover this address only at
  `cancelled` (`test_confirmation_and_back_out_reads_never_save`). `test_non_confirmation_move_views_keep_their_response_contract`
  asserts only "no strip, at most one focus owner", which a page with no focus would also pass. The
  `done` case was proved only in the browser folder, which the card's command does not collect.
  **Can it fail?** Yes. In a scratch copy with the saved-status check in `_move_view` disabled, all 4
  cases failed. The copy was then removed.
- **Fixed (found while walking, behaviour unchanged):** two lines in the same file that were already
  over the packet's 100 columns at the base. The docstring of
  `test_a_submission_not_marked_same_origin_is_refused_and_a_get_changes_nothing` was wrapped. The
  signature of `test_confirming_an_overdue_task_clears_the_row_marker` was split, and its
  `# noqa: F811` moved to the `utc_zone` parameter line, where ruff reports F811. The module
  docstring line this change extended was rewrapped too.
- **No test was corrected for asserting the wrong behaviour.** The developer's new and changed tests
  all come from the intent. Each exact 202 is confined to a known confirmation caller, and
  `test_routes.page` still defaults to exactly 200.

## The finding

**No bugs.** One coverage gap was closed (above). Nothing was misplaced.

The assertion review CP-350 asks for (`tests/e2e/test_moves.py`) was read again here, and it holds.
`fresh_load` waits for an explicit recorder entry and requires exactly `[False]`, so a restored
confirmation would read `[False, True]` and fail. The positive restore witness is on an ordinary
200 page (`page.wait_for_function(RESTORED)` with the URL asserted). `locator_box` lost only its
object-literal non-null check. The two fence verdicts (CP-349, CP-352) were re-run. The current
fence command printed nothing, before and after this run's edit.

## Calls made

1. **Must every return to a confirmation's address show the pageshow sequence `[False]`, or may a later return be a cache restore of the refusal page?**
   - **Readings:** (a) the plan's words, "explicit false on confirmation returns", applied to every
     return; (b) the developer's refinement, recorded in its marker. The first return after the
     status changed must be `[False]`. A later return may be `[False, True]`: a cache restore of the
     200 refusal page that the first return loaded.
   - **Taken:** (b). CP-343 asks that the page show the saved status and no confirmation. A restored
     refusal page shows exactly that, because the status cannot move again from `done` or
     `cancelled`. CP-347 asks only that the run prove the cache is live, which the ordinary-page
     witness does. Reading (a) cannot be met without a forced reload or a cache-disabling flag, and
     the plan forbids both. It would also make a 200 refusal page uncacheable, which no rule asks
     for. The confirmation itself still has to be a fresh load every time it shows.
   - **Whose document:** the Tech Lead's (`tl_instruction.md` Task 1, *Behaviours to verify*).
   - **If ruled the other way:** the response policy would also have to keep the refusal page out
     of the history cache (a non-200 status or similar), which is a design change for the architect.
2. **Does the packet's "A test function is not [annotated]" forbid annotating a test?**
   - **Readings:** (a) a prohibition; (b) a statement that a test is not required to be annotated.
   - **Taken:** (b). The bullet gives its reason, that fixture names already say what they are, and
     sets no gate. The product annotates every test it has, and its mypy gate leaves out `tests`.
     The added test follows the file and carries `-> None`.
   - **Whose document:** core's Python packet (`conventions.md:57-61`).
   - **If ruled the other way:** strip the annotations from the added test. Nothing else in this
     run depends on them.

## Placement

Parts table: `products/tracker17/docs/SDD.md` § 3.

- **Response-status choice for a resolved confirmation** (`Site._pending_status`, `web/routes.py:322-333`): owning part **web**, which owns "building each whole HTML page" and the addresses of pages and actions. It was already there. Not moved.
- **Removal of the successful-move `Clear-Site-Data` header** (`web/routes.py`, `_move_task`): removes logic and adds none.
- The test-side helpers (`site_with_two_tasks`, `fresh_load`, `acted_on_scope`, `expect_saved_status_at`, `move_in_other_tab`) are test code under `tests/` and own no product logic.

No `— placement` commit.

## Language resolution

- **Python**, from `project.md` `Languages:` (chain step 1).
- **Packet:** `core/doctrine/engineering/languages/python/README.md`. Read for this review:
  `conventions.md`, `quality_gates.md`, `testing_python.md` and `environment.md`.
- **Lines within 100 columns** (`conventions.md:17`): followed after repair. The three lines in
  `test_move_routes.py` noted above were wrapped. `awk 'length > 100'` over the file now prints
  nothing.
- **f-string interpolation, double quotes, `from __future__ import annotations` first**
  (`conventions.md:21-48`): followed in the added test.
- **A test function's annotation** (`conventions.md:57-61`): see *Calls made* 2.
- **Quality gates** (`quality_gates.md:14`, `:33`, `:66`, `:76`), run from the product root, all
  exit 0:
  - `python3 -m compileall -q main.py errors.py domain application persistence web tests`
  - `ruff format --check .`: 199 files already formatted
  - `ruff check .`: all checks passed
  - `mypy main.py errors.py domain application persistence web`: no issues in 24 source files
- **Layer 5 lives in `tests/e2e/`, run separately** (`testing_python.md:29`): followed. The added
  test is layer 3.
- **The seam is a hand-written fake, not `monkeypatch.setattr`** (`testing_python.md:31`): followed.
  The added test drives the real `Site` with the existing `RecordingSaver` world.
- **Gate environment** (`environment.md:16`): no CI exists, so the gate tool chose the owner's Mac
  (`languages/README.md`, a product with no CI runs its gates on the owner's Mac).
- **Python 3.13 floor** (`toolchain.md`): the product's own records take precedence (`requires-python
  = ">=3.11"`, NFDR QC-59 and QC-60).

## Test evidence

- An earlier run of the test command exited 0 and printed `Environment: owners-mac — no CI`.
- An earlier run of the test command exited 0 and printed `Environment: owners-mac — no CI`.
- An earlier run of the test command exited 0 and printed `Environment: owners-mac — no CI`.
- An earlier run of the test command exited 0 and printed `Environment: owners-mac — no CI`.
- The run the verdict rests on is the last full-card run, issued by `core/tools/gate_suite.py run --gate code-integrity` from the instance change worktree with the locked environment `/private/tmp/t17env/.venv/bin` first on `PATH`. It exited 0: `1250 passed in 117.09s`. That is 1246 at the marker plus the 4 added cases.
- The evidence the tool was given: no CI. The inventory over the worktree's tracked files found no
  build-service, pipeline or runner configuration. The product's tracked files outside
  `.py/.md/.css/.json/.txt/.toml` are `.gitignore` and `tests/e2e/.gitkeep`. No product decision
  names a gate environment or amd64. `KENSAIAPP_GATE_OWNERS_MAC` was unset.
- The browser folder (CP-348; the card's command does not collect it):
  `/private/tmp/t17env/.venv/bin/python -m pytest -q -rsxX products/tracker17/tests/e2e/`, from the
  worktree root, gave `67 passed in 30.68s`, with no skip, deselection or xfail. It ran before this
  run's test edit, which touched only `tests/integration/test_move_routes.py`, a file outside that
  folder.
- The new test against a scratch copy with the saved-status check disabled: `4 failed`.
