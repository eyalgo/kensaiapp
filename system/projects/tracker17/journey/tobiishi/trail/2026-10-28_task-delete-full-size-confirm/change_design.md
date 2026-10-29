# Change Design — Full-size Delete task controls

**Date:** 2026-10-29
**Category:** feature
**Behaviour:** changing
**Publishes text:** no

---

## 1. Change Summary

This blueprint owns the rendering changes and regression coverage for `tracker17 · tobiishi · 2026-10-28_task-delete-full-size-confirm`.
Its scope is the change spec's CP-609–CP-618, including the first press as well as its confirmation.
All product paths below are relative to `products/tracker17/`.

Use the existing full-size secondary-button styling for Delete task's first press and the existing full-size strip context for its confirmation.
The first-press rendering belongs in `_delete_section`, which builds the ordinary, backed-out and failed forms of that control (`web/pages.py:866-894`, `_delete_section`).
The strip context belongs in `_delete_strip`, which calls the shared renderer (`web/pages.py:855-863`, `_delete_strip`).
The full-size stylesheet contracts already exist (`web/style.css:334-337`, `.strip-control .confirm-sentence`; `:345-357`, `.strip-control button.button-confirm`; `:360-373`, `button.button-secondary`).

Retain the shared strip's arguments, output structure, sentence focus and form destinations.
Keep task deletion's data flow, response policy and copy unchanged, as the spec's Out of Scope requires.
The change publishes no words: the spec's Out of Scope explicitly preserves every page's wording.

---

## 2. Blast Radius

The owning part is **web**, whose SDD § 3 row owns whole-page building and the stylesheet (`docs/SDD.md:206-220`, “The parts”).
Place both the first-press component selection and the task strip's size selection in that part.
The module set below is NFDR § 1.2's (`docs/nfdr.md:166-197`, “Forbidden imports”).

| Module | Status | What changes |
|---|---|---|
| `domain/` | Unchanged | No task rule, state shape, feature-entry pointer or public surface changes. |
| `application/` | Unchanged | No action, save contract, clock contract or page-value changes. |
| `persistence/` | Unchanged | No saved-data or save-failure behavior changes. |
| `web/` | Modified | **web** owns the presentation choice: `_delete_section` uses the full-size secondary component for every restored/ordinary first press; `_delete_strip` selects the existing full-size strip context. Retire the obsolete task-delete selector from the row-control stylesheet rules and correct the associated comments. |
| `main.py` | Unchanged | No wiring or start changes. |
| `errors.py` | Unchanged | No error types or handling changes. |

Test support changes are confined to additions in `tests/e2e/test_delete_task.py` and the corrected assertion in `tests/e2e/test_delete_project.py`.
The latter's description of unchanged task contexts must also be brought into agreement with its corrected assertion (`tests/e2e/test_delete_project.py:192-220`, `test_project_strip_uses_full_size_controls`).

No transitive caller changes are needed: this design changes neither a Python signature nor the public exports (`web/__init__.py:6-9`, export list; `web/pages.py:783-807`, `confirm_strip`).
No new import edge is needed under NFDR QC-13–QC-19 (`docs/nfdr.md:166-197`, “Forbidden imports”).
The existing size vocabulary remains `row-control` for status moves and `control` for full-size controls (`web/pages.py:765-765`, `TRIGGER_SIZE`; `:897-897`, `FULL_SIZE`).

Only one production module is affected, with no new interface or internal ordering dependency, so this is one delta rather than separate sub-jobs.
The full-size stylesheet rules are already available to the page builder (`web/style.css:334-373`, full-size strip and secondary-button rules).

**Atomic-landing edge:** the task strip's size selection + T4's corrected assertion have no green point between them in the e2e suite.
The current assertion requires 28px (`tests/e2e/test_delete_project.py:218-220`, `task_confirm`), while the full-size context sets 36px (`web/style.css:345-353`, `.strip-control button.button-confirm`).
Changing either alone leaves those two contracts disagreeing.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `web/` — task first press, confirmation context and stylesheet cleanup | None |

The equality contract is realized by selecting the two existing 36px components, rather than by globally changing the shared strip's default geometry.
All three non-confirmation modes must share the full-size first-press rendering, preserving `_delete_section`'s existing focus and failure-description branches (`web/pages.py:866-894`, `_delete_section`).

---

## 5. Test Additions

Add the browser checks to the existing task-deletion module, retaining its current tests.
Its opening docstring already names SRS FR-17, NFR-12, NFR-3 and AC-12 (`tests/e2e/test_delete_task.py:1-8`, opening docstring).
The Tasks feature entry already names that module (`domain/tasks.py:17-31`, “Checked by”).
No new test module or feature-entry edit is needed for CP-618.

| Row | Sub-job | Test file | What to add / modify |
|---|---|---|---|
| T1 | `web/` | `tests/e2e/test_delete_task.py` | Add a Chromium geometry test using the real tracker fixtures. Measure the ordinary first press at `/tasks/1`, then the sentence, confirming button and Back out at `/tasks/1?delete_confirm`. Assert first press and confirm are each 36px ±0.5, their height difference is ≤0.5px, sentence height is ≥35.5px and at least the measured trigger height within 0.5px, and Back out is 36px ±0.5. Compare rectangles in document coordinates across page loads and assert the sentence covers the entire original first-press rectangle on both axes. Cover a normal page and the scrolled page-bottom case. CP-609–CP-612, CP-614; Examples 1, 4, 6 and 7. |
| T2 | `web/` | `tests/e2e/test_delete_task.py` | Add a browser check that opens confirmation and uses Back out, reaches `delete_back`, and measures the restored first press at 36px ±0.5. Retain the existing focus and no-save checks. CP-609; Example 2. |
| T3 | `web/` | `tests/e2e/test_delete_task.py` | Add a browser check that opens confirmation, makes the next save fail in the test's own temporary data location, presses the confirming control, and measures the restored first press at 36px ±0.5 on `delete_failed`. Assert the failure line is present and the task and saved bytes remain. Use a deterministic filesystem obstruction at the saver's partial-file destination, removed after the check, rather than a permission-bit assumption or patching product names. The save opens that destination before replacing the saved file (`persistence/saved_data.py:124-130`, save's partial-file write). CP-609; Example 3. |
| T4 | `web/` | `tests/e2e/test_delete_project.py` | In `test_project_strip_uses_full_size_controls`, replace only the task-confirmation height expectation with `CONTROL_HEIGHT`. Keep the status-move assertion at `ROW_CONTROL_HEIGHT`, all project-strip measurements, and the existing tolerance. Align the same test's descriptive docstring with that corrected expectation. CP-613, CP-615; Examples 5 and 8. |
| T5 | `web/` | `tests/e2e/test_delete_task.py`, existing tests | Keep the keyboard, real double-click/third-click, completion history, fresh confirmation history and escaped-title tests unchanged. They remain the regression fence for the spec's unchanged focus, part order, no accidental confirmation, copy, redirects and deletion behavior (`tests/e2e/test_delete_task.py`, `test_delete_confirmation_is_keyboard_operable`, `test_double_press_never_confirms_deletion`, `test_completion_survives_actual_reload_back_and_forward`, `test_confirmation_is_loaded_afresh_after_confirming`, `test_deletion_titles_stay_text_in_the_browser`). |
| T6 | `web/` | `tests/architecture/test_trace.py`, existing tests | Keep the trace checks unchanged and retain a compliant opening docstring in the module receiving T1–T3. The existing `test_every_test_module_names_a_requirement_or_acceptance_criterion` rejects a module with no requirement reference (`tests/architecture/test_trace.py:129-136`, that test). CP-618; Example 11, including its negative condition. |
| T7 | `web/` | Both product suites | `pytest products/tracker17/tests/` and, separately, `pytest products/tracker17/tests/e2e/`, from the change worktree root, must each exit 0. CP-616; Example 9. The first suite excludes e2e (`tests/conftest.py:1-9`, collection-rule docstring). |
| T8 | `web/` | Product quality gates | From the product root, `ruff format --check .`, `ruff check .`, and `mypy main.py errors.py domain application persistence web` must each exit 0 at the locked versions. CP-617; Example 10; `docs/nfdr.md:532-545`, QC-62. |

**Baseline and retirement.** T1 must fail against the pre-change rendering, including commit `0c92d8dec1b773b7584b588cc4e149b37522a939`, before the implementation lands.
That revision gives the task first press `delete-button`, whose stylesheet height is 28px, and the task strip `TRIGGER_SIZE`, whose confirming button height is 28px (`web/pages.py:855-890`, task deletion builders; `web/style.css:228-244`, row controls; `:314-324`, row-control confirmation).
The sole retired assertion is the task confirmation's 28px expectation in T4.
Its clause is replaced by T1's absolute 36px and relative equality checks and T4's 36px assertion.
The status-move 28px clause is retained by T4, not retired (`tests/e2e/test_delete_project.py:215-220`, move and task comparisons).

**Rule pass.** CP-609's three page forms are covered by T1–T3; CP-610–CP-612 by T1; CP-613 by T4; CP-614 by T1's baseline failure and post-change pass; CP-615 by T4; CP-616–CP-618 by T7, T8 and T6 respectively.
The full-rectangle coverage and scrolled-page variant in T1 protect CP-611's “whole spot” clause rather than relying on height equality alone.
T5 retains the existing real-click protection.
No other existing assertion is weakened or removed.

---

## Records this change makes false

None — read `docs/adr/README.md` and the Accepted ADR-0001–ADR-0005, ADR-0007–ADR-0009, ADR-0011 and ADR-0012; `docs/nfdr.md`; `docs/fdr.md`; and `docs/SDD.md` § 3.
On this design, no decision, obligation, behavioral rule or parts-table sentence changes truth: the change stays inside web's existing page/stylesheet ownership and introduces no new seam.
The size contract is already stated by `docs/DESIGN.md:450-466`, “Components”, `components.button-secondary` and `components.confirm-strip`.

---

## Architect Review Notes

All decisions below are the Architect's, 2026-10-29.

- **Realize the size contract by construction (kind b).** Choose the existing secondary component and full-size strip context, instead of enlarging the shared row-control token. The reason is CP-613's preserved move height, with `_cancellation_strip` and `_delete_strip` currently sharing `TRIGGER_SIZE` (`web/pages.py:819-863`, those two builders).
- **Conservative placement of test additions (kind b).** Add T1–T3 to the existing task-deletion module. This satisfies CP-618 without a new feature pointer or test module (`domain/tasks.py:17-31`, “Checked by”; `tests/e2e/test_delete_task.py:1-8`, opening docstring).
- **Failure-path proof (kind b).** T3 drives an actual failing confirming submission. A temporary obstruction at the partial-file destination exercises the real saver before replacement (`persistence/saved_data.py:124-130`, partial-file write). This locks the test approach, not a new failure behavior, and avoids assuming permission bits fail under every test account.
- **Correct the changed test's description (kind b).** CP-615 changes one assertion in `test_project_strip_uses_full_size_controls`; that test's docstring says existing task contexts are not resized (`tests/e2e/test_delete_project.py:195-196`). Correct that description alongside the named assertion so it does not contradict the new expectation. No other existing test body changes.
- **Delegated NFDR reviews — pass.** QC-8 and QC-23: the delta selects presentation classes and size contexts, with no per-request state stored and no domain decision added (`docs/nfdr.md:85-91`, QC-8; `:241-245`, QC-23; `web/pages.py:855-894`, task deletion builders). QC-12: no additional production part, abstraction or dependency is needed (`docs/nfdr.md:158-164`, QC-12; § 2 of this design). QC-27: no HTML or request detail crosses into another part (`docs/nfdr.md:262-267`, QC-27; § 2). QC-36: retain `_escape` and the shared renderer's escaping paths for sentence and form values (`docs/nfdr.md:329-335`, QC-36; `web/pages.py:775-807`, `_strip_form` and `confirm_strip`). QC-41: no secret or credential is introduced by the rendering selections or tests (`docs/nfdr.md:379-383`, QC-41; §§ 2 and 5).
- **Other conditional architect gates — not triggered.** The delta adds no refusal, modifies no application, persistence, saving or main contract, adds no saved field, and requires no new Python/library feature (`docs/nfdr.md`, QC-5, QC-20–QC-22, QC-24–QC-26, QC-46 and QC-60; §§ 2 and 4 of this design). The sweep `rg -n 'development-design' products/tracker17/docs/adr products/tracker17/docs/nfdr.md` returned delegated entries in NFDR and none in the ADRs.
- **QC-40 package advisory review — pass within the query's coverage.** On 2026-10-29, queried `https://api.osv.dev/v1/querybatch` for each exact PyPI name/version in `tests/requirements.txt:4-18`, including transitive dependencies. The command exited 0 and returned `{}` for each of the 15 entries, so it reported no matching advisory. This is a recorded database result, not a claim that every possible vulnerability is absent.
- **QC-40 browser review — pass under the owner's existing exception.** The suite's pinned Chromium is `153.0.8010.12` (`tests/e2e/test_moves.py:515-515`, `PINNED_BROWSER`). Google's 2026-09-15 desktop release names critical fixes in `153.0.8010.47/.48` ([Chrome Releases](https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0541751186.html)). The older pinned build is covered through 2026-11-07 by the owner's dated exception, which explicitly permits a design review before that date (`docs/nfdr.md:1049-1057`, RN-33). This design moves no pin and claims no browser-security fix.
