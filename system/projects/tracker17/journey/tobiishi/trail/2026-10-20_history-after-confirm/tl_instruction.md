# Tech Lead instruction — history-after-confirm: show saved state on history return

**Date:** 2026-10-20
**Category:** bug
**Behaviour:** changing
**Product root:** products/tracker17 — every product path below is relative to it.
**Scope:** Implement the response policy and browser proof in change_design.md §§ 1–5 for
change_spec.md CP-343–CP-354, then verify the file fence and assertion review.

This is the developer scaffold for `tracker17 · tobiishi · 2026-10-20_history-after-confirm`.
Read its change_spec.md and change_design.md alongside this instruction.
Commands labelled **worktree root** run at the instance change worktree; commands labelled
**product root** run at `products/tracker17` inside that worktree.
The gate environment must permit the local listener and browser and give the test process
normal SIGINT handling. In this Codex execution surface a terminal session (`tty: true`) has
that handler; a plain command session reports `SIGINT handler: 1`, equal to `SIG_IGN`, while
the terminal check reports `default_int_handler` (planning diagnostic, 2026-10-20).

## Project layout

```text
products/tracker17/
  web/
    routes.py                          ← modified
  tests/
    integration/
      test_routes.py                   ← modified
      test_move_routes.py              ← modified
      test_move_pages.py               ← modified
    e2e/
      test_moves.py                    ← modified
      conftest.py                      ← modified only if browser identity needs fixture support
```

Create no directory, package, test module or `__init__.py`.
The full part set and import permissions remain docs/nfdr.md § 1.2, QC-13–QC-19.
`web` owns the response policy under docs/SDD.md § 3, “The parts, and the seams between them”.
Its imports may reach `application`, `errors` and the standard library; they must not reach
`domain`, `persistence`, `main`, `tests` or third-party modules (docs/nfdr.md § 1.2, QC-16/QC-19).
No part or import edge is added.

## TL Review Notes

Decisions by the Tech Lead, 2026-10-20:

- **Task cut:** design § 2 gives one production delta and no atomic-landing edge, but has no
  numbered § 3 sub-job table. Task 1 owns that cohesive response policy and its new tests.
  Task 2 owns compatibility of the retained, already-failing history test. Task 3 owns the
  change-only review deliverables. This separates new tests from the existing red as required
  by development-plan § “The red-at-baseline shape”, without changing the design's topology.
- **Baseline red:** ran `/private/tmp/t17env/.venv/bin/python -m pytest -q
  products/tracker17/tests/e2e/test_moves.py::test_real_history_traversal_revalidates_the_confirmation`
  from the worktree root, with approval for the local server/browser: `1 failed in 6.59s`,
  at `test_moves.py:423`, expected strip count 0, actual 1. `git diff --stat main --
  products/tracker17` printed nothing. Commit `1ab3345271c03d60c9df2b9a86dd82b3e493c66a`
  records the earlier change's deferred task 1 and names that exact case. Task 2 therefore
  carries the existing red explicitly; Task 1's additional tests still require their own red.
- **Intermediate browser gate:** Task 1's gate names its new browser matrix, rather than
  claiming the whole browser folder green while Task 2 remains open. The original history
  test requires confirmation restoration at `tests/e2e/test_moves.py:L415-L416`, which the
  design explicitly retires in § 5 “Existing assertions retired, replaced or strengthened”.
  Task 2 replaces that witness with an ordinary-page restore and then requires the whole
  folder green. The order follows that proof's use of Task 1's response policy; it does not
  create a red solely to satisfy a lane.
- **Additional coverage:** Task 1 makes the existing repeated-query precedence cases assert
  exact response status as well as presentation, because `test_move_query_collisions_select_one_interaction_and_focus_owner`
  already covers the first-value/recognized-outcome rules at
  `tests/integration/test_move_pages.py:L408-L464`, and a status decision based on raw query
  presence would break the design's “actually rendered confirmation” contract.
- **Precision:** use the existing `HTTPStatus` and `MoveInteractionMode` vocabularies for the
  status and interaction decision; no new string discriminator is needed
  (`web/routes.py:L19-L21`, `web/pages.py:L186-L203`).
- **Review shape:** T10–T13 become Task 3 review deliverables, rather than tests of a fixed Git
  base or tests of the tests. The acceptance conditions apply to this change's diff, and
  CP-350 requires product-breaking counterexamples rather than assertions about test syntax.
- **Hint allocation:** carry design § 4's route, strict-helper and browser-recorder approaches
  in Task 1. Task 2 uses the required baseline-red marker and its Reason line; the same
  recorder approach applies to the retained proof through Task 1's helpers. No production
  implementation is supplied.
- **Gate environment:** language resolution is Python, step 1 (`system/projects/tracker17/project.md`,
  “Languages”). Opened core/doctrine/engineering/languages/python/README.md and all seven
  destinations. The product's Python 3.11 floor, standard-library runtime and exact test pins
  take precedence (docs/adr/0002-standard-library-only-no-web-framework.md § Decision;
  docs/nfdr.md QC-39/QC-59/QC-60). Use an environment installed from tests/requirements.txt;
  change no pin. The available locked environment for this run is `/private/tmp/t17env/.venv`;
  `/private/tmp/t17env/.venv/bin/python -m pytest --version` returned `pytest 9.1.1`.
  An importlib.metadata comparison of every tests/requirements.txt pin returned
  `lock mismatches: []`.
- **Execution correction:** the first card run in the restricted command session returned
  `20 failed, 1170 passed, 30 errors in 85.19s`; listener setup reported
  `PermissionError: [Errno 1] Operation not permitted`. A standalone loopback bind reproduced
  that permission error. An approved locked-environment run could bind, but its shutdown
  checks inherited ignored SIGINT. Restoring the normal handler before running
  `test_every_supported_saved_form_keeps_all_existing_values` returned `4 passed in 0.32s`.
  Gate permissions and the normal signal handler are environment prerequisites, not new
  product fixes or baseline-red task entries.
  The approved terminal run of `/private/tmp/t17env/.venv/bin/python -m pytest -q
  products/tracker17/tests/` returned `1220 passed in 117.21s (0:01:57)`.
- **Suite scope:** retain the card's `pytest products/tracker17/tests/` and separately require
  `pytest products/tracker17/tests/e2e/`; the card command deliberately excludes the browser
  folder (`tests/conftest.py`, “The collection rule”, L6–L9 and L45–L51).
  Do not replace either gate with the other.
- **Scope boundary:** retain the no-press refusal wording as it stands; change_spec.md
  “Out of Scope” leaves that wording for other work. History assertions must check that the
  accessible reason describes the saved status, without creating a new wording requirement.

## Corrections owed while there

- Owed outside this change's reach: `docs/SDD.md` § 4 runtime conditions or `docs/adr/` — the
  history mechanism is absent from the product records (`rg -n
  'no-store|Clear-Site-Data|Cache-Control' products/tracker17/docs` returned no matches).
  The added record must describe HTTP 202 for an actually rendered pending confirmation as
  the history-admission boundary, and `Cache-Control: no-store` on move interaction/outcome
  pages as HTTP-cache protection. It must describe both purposes, the pending-intent
  interpretation, unchanged saved-status GET revalidation, no page script/cookie/session,
  removal of Clear-Site-Data, the Chromium dependence, the product proof's measured outcome,
  and service of RT-7, EX-6 and CP-343. This carries design “Record owed — CP-351”; no file
  under product `docs/` changes here. The admission check is vendor-specific
  ([Chromium, PopulateReasonsForMainDocument](https://raw.githubusercontent.com/chromium/chromium/main/content/browser/back_forward_cache/back_forward_cache_impl.cc#L987-L991));
  no-store alone does not exclude a page from Chrome's history cache
  ([Chrome's explanation](https://developer.chrome.com/docs/web-platform/bfcache-ccns)).

### Task 1: Resolved confirmation response policy (`web/routes.py`, `tests/integration/test_routes.py`, `tests/integration/test_move_routes.py`, `tests/integration/test_move_pages.py`, `tests/e2e/test_moves.py`, optionally `tests/e2e/conftest.py`)

**Dependencies:** None

**What to build:** Apply design § 1's response table in the owning `web/routes.py`, with new
response and history-matrix tests. Serve 202 exactly when this page actually renders a pending
confirmation; keep the existing response/body/address for every other resolved presentation.
Keep no-store's existing scope and all submission outcomes; remove Clear-Site-Data entirely.
Update the existing integration callers' explicit expected statuses with the policy.
Keep the original `test_real_history_traversal_revalidates_the_confirmation` for Task 2;
add the broader browser matrix as a separate test in the same module.

#### Behaviours to verify

In `tests/integration/test_routes.py`, with existing move/page helpers and cases in
`test_move_routes.py` and `test_move_pages.py`:

- `test_pending_confirmation_response_matches_the_rendered_page` — for task and project-row
  pages, from both allowed starting statuses, exact 202 accompanies the one confirmation.
  The sentence alone owns focus, and other rows keep their ordinary controls. Saved bytes,
  tracker state and save count do not change on the read.
- `test_non_confirmation_move_views_keep_their_response_contract` — back-out, terminal saved
  statuses, recognized refusal/failure/completion winning over confirmation, unknown or empty
  interaction values, absent/malformed/unknown task identity, and a real task from another
  project retain the existing exact 200/404 and body/focus contract. A different task on a
  task page stays plain. Repeated query values preserve their existing precedence.
- `test_move_interaction_and_outcome_pages_are_not_stored` — replace the unconditional 200
  with explicit expected statuses; keep exact no-store, policy and no-cookie assertions,
  including plain pages without the interaction query as the unchanged no-store-scope control.
- `test_move_responses_do_not_clear_site_data` — replace the former eviction test while
  retaining ordinary/confirming successes, first press, refused move, invalid status,
  missing task, failed save on both submission paths, GET, back-out and rejected origins.
  Every response lacks Clear-Site-Data and Set-Cookie. Preserve exact redirects and Locations;
  non-saving paths preserve bytes/state/save count and successful saves retain their outcomes.
- `test_move_pages_contain_no_executable_script` — inspect the served page structure for script
  elements, event-handler attributes and script URLs; every relevant response retains the
  exact Content-Security-Policy, including script refusal and `frame-ancestors 'none'`.
- Existing `test_every_route_leaves_state_and_headers_as_the_rules_say` remains effective:
  non-submissions never save and submissions redirect, with the request checks, policy and
  no-cookie guarantees intact.
- Existing integration confirmation tests retain all body, focus, save and refusal assertions;
  only known pending-confirmation callers opt into exact expected 202. The shared page
  helper's default stays exactly 200, including ordinary `follow` callers.

In `tests/e2e/test_moves.py`:

- `test_history_matrix_revalidates_current_saved_status` — cover both page locations and both
  history directions after final state. Include this tab confirming to cancelled; Back,
  Back again, Forward to the confirmation address; another tab's ordinary moves ending at
  done; another tab confirming to cancelled; and the confirmation remaining active during
  the other tab's save before this tab leaves and returns. On every return to the
  confirmation address, assert that exact address, saved status, absence of strip/sentence/
  confirming/back-out/move controls, status focus, viewport visibility and accessible
  saved-status reason. Scope the row assertions to the acted-on task, with another row as
  a control. Compare saved bytes separately around every traversal, after the deliberate save.
  Before confirming, reload, Back and Forward each preserve bytes; reload/Forward show the
  still-allowed confirmation with sentence focus. Each parameter run observes a positive
  ordinary-page cache restore and explicit false on confirmation returns. Assert browser
  version 153.0.8010.12 and keep the existing cache-enabled full-Chromium launch.

#### Held by review

- No second workflow table, production HTML inspection to choose status, page script,
  retained request state, cookie, session, endpoint, interception, cache-disabling flag or
  forced reload after history traversal. Read the production and harness diff against
  design §§ 1–2; a green DOM assertion alone cannot prove these restrictions.
- Remove the obsolete successful-move eviction explanation from `web/routes.py` as the
  header is removed. Remove `locator_box`'s object-literal non-null assertion while opening
  `test_moves.py`, retaining the browser-derived geometry and hit-target checks; design § 5
  identifies these exact corrections at `web/routes.py:L700-L701` and
  `tests/e2e/test_moves.py:L250-L258`.

#### Implement

Infer from failing tests.

# Hint:
Derive 202 from the resolved, actually rendered confirmation after outcome precedence, task
membership and the saved workflow answer. Keep no-store as HTTP-cache protection; remove the
clearing header and its obsolete eviction claims. The non-200 admission boundary is the
browser-specific approach, not a new page action.
Keep the shared `test_routes.page` helper strict at 200 by default; permit an explicitly
supplied expected status for known confirmation cases. Update confirmation callers in
`test_move_routes.py` and `test_move_pages.py`. Never replace exact expectations with a blanket
successful-status range.
Put the same-run positive pageshow witness on an ordinary 200 page. Await explicit true/false
recorder observations as well as the expected DOM; missing instrumentation does not prove
a fresh load.

#### Verification gate

With the locked test environment active, from the **worktree root**:

```sh
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/test_moves.py::test_history_matrix_revalidates_current_saved_status
```

Pass: the card suite and every new browser parameter pass. The retained baseline history
test remains Task 2's obligation; no other known failure is accepted. Run the whole browser
folder in Task 2 without exclusions.

From the **product root**, each command must exit 0:

```sh
python3 -m compileall -q main.py errors.py domain application persistence web tests
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

### Task 2: Restore the retained history proof (`tests/e2e/test_moves.py`)

**Dependencies:** Task 1 — uses its response policy and history-observation helpers.

**What to build:** Make the existing history proof compatible with the response policy while
retaining every saved-byte, confirmation, focus and description assertion permitted by
change_spec.md CP-354. Move its positive restore witness to an ordinary page, await explicit
false for confirmation returns and compare saved bytes around each traversal. Keep its
existing test name. Add no test or parameter here; Task 1 carries additional scenario coverage.

#### Behaviours to verify

- Red at baseline: `tests/e2e/test_moves.py::test_real_history_traversal_revalidates_the_confirmation`

#### Implement

Tests are red at baseline.

Reason: `tracker17 · tobiishi · 2026-10-19_cancel-confirmation` deferred task 1 in closing
commit `1ab3345271c03d60c9df2b9a86dd82b3e493c66a`; the exact existing case failed this planning
run at L423 with strip count 1 instead of 0. Task 1 supplies the production mechanism; this
task adapts only the design's named obsolete cache witness and strengthens the two permissive
false observations in that retained case. Its existing red is observed, not newly created.

#### Verification gate

From the **worktree root**, with the locked test environment active:

```sh
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/
```

Pass: both complete folders exit 0; the original named history case and the new matrix pass.
No browser test is skipped, deselected or marked xfail. No post-Back reload, interception,
pin change or cache-disabled browser substitutes for the proof. A failing history case remains
a failed condition under CP-348, with no weakening of the experience or ADR-0003.

From the **product root**, each command must also exit 0:

```sh
python3 -m compileall -q main.py errors.py domain application persistence web tests
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

### Task 3: Verify the fences and assertion verdicts (`web/routes.py`, `tests/e2e/test_moves.py` — diff review only)

**Dependencies:** Tasks 1 and 2 — reviews their final product diff and browser assertions.

**What to build:** Record the change-specific review verdicts for design T10–T13 and CP-349–CP-352
in Developer Review Notes, including the commands and measured outputs. No suite test encodes
a Git base, a file fence or the shape of another test.

#### Deliverables verified by review

- Previous-change fence, from the **worktree root**:
  `git diff --name-only e97b021f0 e0b0f245d -- products/tracker17` must name precisely CP-349's
  twelve allowed files. `git diff e97b021f0 e0b0f245d -- products/tracker17/domain/workflow.py`
  must touch the opening docstring only. Planning re-ran both: twelve allowed paths;
  the sole workflow hunk is `@@ -7,14 +7,18 @@`, wholly inside that docstring. Verdict: PASS;
  undo nothing from the previous change.
- Every assertion and helper in `tests/e2e/test_moves.py` has a product-breaking counterexample,
  or is removed/repaired and named with its original purpose and disposition. Review the whole
  file, including old move, keyboard, geometry, double-click, stale-first-press and new history
  checks. Retain real `bounding_box()` non-null assertions; those can fail on an unrendered
  element. Confirm Task 1 removed only the object-literal `locator_box` check, and Task 2
  replaced the positive confirmation witness and permissive false checks. State why the rest
  still check product behavior; additional findings are individually named, never silently cut.
- Current-change fence, from the **worktree root**: the following command must print nothing.
  Its merge base belongs to this branch, and its diff includes uncommitted tracked edits.

  ```sh
  git diff --name-only "$(git merge-base main HEAD)" -- products/tracker17 ':!products/tracker17/web/routes.py' ':!products/tracker17/tests/integration/test_routes.py' ':!products/tracker17/tests/integration/test_move_routes.py' ':!products/tracker17/tests/integration/test_move_pages.py' ':!products/tracker17/tests/e2e/test_moves.py' ':!products/tracker17/tests/e2e/conftest.py'
  git ls-files --others --exclude-standard -- products/tracker17
  ```

  Both listings must be empty. No new file is in design § 2. In particular workflow.py's
  docstring and body, pages/style/listener, public exports, other tests, inner parts, main,
  errors, timed run, dependencies, pyproject and all product docs stay byte-identical to base.
- The “Corrections owed while there” entry in this instruction carries CP-351's complete
  mechanism record obligation. Record the final measured browser result beside the review
  verdicts; do not claim the synthetic probe proves product focus or saved-state behavior.

#### Implement

Verified by review — no test.

#### Verification gate

Run both fence commands above and read the two historical diffs. Pass: the old fence is met,
the current fence prints nothing, and every assertion disposition has its falsifiable reason.

From the **worktree root**, with the locked test environment active:

```sh
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/
```

From the **product root**:

```sh
python3 -m compileall -q main.py errors.py domain application persistence web tests
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: all commands exit 0, no browser skip/deselection/xfail, no new failures anywhere;
`tests/architecture/test_trace.py` remains unchanged and passes as part of the card suite.
