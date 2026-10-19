# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-19_allowed-moves`, on the station `tracker17 · shukuba · 2026-10-19_allowed-moves`.
**Date:** 2026-10-19
**Reviewed at:** the developer's closing marker `0f395031a894326f11bfd24549e7f930a033baea` (`developer: 2026-10-19_allowed-moves — implementation complete`).

## Summary

The code does what its intent says. No code was wrong, and no logic sat outside its owning part.
The browser test, `tests/e2e/test_moves.py`, had two defects, and both are fixed here. Two of its
three tests waited for the landing address with its query in a fixed order that the route does not
produce, so they would have timed out. The third clicked a button that no longer exists on its
second pass. Two integration tests were tightened to the place the intent names, and one case the
intent states had no test, so one was added. The full card run is green, 1170 passed. The browser
tests still could not run on this machine, because Chromium does not start here (§ Not verified).

## Deferrals

**None.** The closing marker carries no `Deferred:` line, so there are no deferrals to check and none to leave alone.
The marker was read with `git -C <worktree> log -1 main..2026-10-19_allowed-moves --grep='2026-10-19_allowed-moves — implementation complete' --format=%B`.
The pause marker before it, `1439002bec57367c2203a1f43665abaca0222923`, carries none either.

## What was reviewed

Everything the change's code commits wrote under `products/tracker17/`, at `0f39503` against `main`. That is 17 files, 1444 lines added and 21 removed:

- `domain/workflow.py` (new) and `domain/__init__.py`;
- `application/tracker.py` and `application/__init__.py`;
- `web/routes.py`, `web/pages.py` and `web/style.css`;
- the new tests `tests/unit/test_workflow.py`, `tests/integration/test_move_tracker.py`,
  `tests/integration/test_move_routes.py`, `tests/integration/test_move_pages.py` and
  `tests/e2e/test_moves.py`;
- the edited tests E1 to E7 (`tests/architecture/test_trace.py`, `tests/architecture/test_shapes.py`,
  `tests/integration/test_routes.py`, `tests/integration/test_task_pages.py`,
  `tests/integration/test_comment_pages.py`).

## The intent it was checked against

- `tl_instruction.md`, Tasks 1 to 5 and their `#### Behaviours to verify`, the primary reference.
- `change_spec.md`, CP-293 to CP-318 and its Examples, behind it. CP-315 is set aside by the design.
- `change_design.md` § 3 to § 5 and § Architect Review Notes (R-1 to R-4, D-1 to D-14), which the
  plan carries.
- `change_text.md`, for every string the change publishes. Each string in `web/pages.py` and
  `web/routes.py` was compared with it word for word, and all of them match.
- `products/tracker17/docs/fdr.md` exists and was read as context through the spec's citations.
  `docs/SDD.md` § 3 is the parts table. `docs/DESIGN.md` gives the move button's values, which
  Task 3 checks by review.
- Every behaviour name the plan gives, 39 in all, is a test in the tree. The plan's E4 test was
  renamed to "seven columns", as the plan asks.

## Placement (Step 0)

Each piece of logic was walked against `docs/SDD.md` § 3. **Nothing was misplaced, and nothing was moved**, so there is no `… — placement` commit.

| Logic | Owning part | Where it is |
|---|---|---|
| The allowed moves per status, in the workflow's order (`_ALLOWED_MOVES`, `allowed_moves`) | `domain` ("every rule that accepts or refuses a change") | `domain/workflow.py`, already there |
| The refusal `MoveNotAllowed`, and refusing a non-status target and an unknown task | `domain` ("one typed refusal per refused condition") | `domain/workflow.py`, already there |
| Applying a move: one task's status, nothing else (`move_task`) | `domain` | `domain/workflow.py`, already there |
| The move action: apply, save, then publish (`Tracker.move_task`) | `application` ("each action is one call that applies a `domain` rule") | `application/tracker.py`, already there. It decides nothing. |
| Handing the allowed moves to the pages (`Tracker.allowed_moves`) | `application` ("answers what a page needs to show") | `application/tracker.py`, already there |
| The move route, reading the form and the place word, the redirects, and decoding the outcome (`_move_task`, `_move_outcome`) | `web` ("the addresses of pages and actions, reading form fields") | `web/routes.py`, already there |
| The move forms, the status area, the landing line, its words (`_move_forms`, `_status_section`, `_move_line`, `_REFUSAL_TAILS`) | `web` ("building each whole HTML page") | `web/pages.py`, already there. The wording is `web`'s, since `domain` must hold none. |
| Withholding `cancelled` from the offered controls (`_WITHHELD_MOVES`) | `web`, as the design places it (D-10: which controls a slice shows is page building, EX-12) | `web/pages.py`, already there. Which moves are allowed still comes only from `application`. |

## Language resolution

- **Python**, from `project.md` `Languages: Python`, which is step 1 of the chain in `<CORE>/doctrine/engineering/languages/README.md` § The resolution chain.
  The developer's marker calls it "chain step 5", but the chain has four steps. That slip changes nothing in the code.
- **The packet opened** was `<CORE>/doctrine/engineering/languages/python/README.md`. The code was reviewed against:
  - `conventions.md`: line length, quotes, the future import, builtin generics, annotations, frozen
    dataclasses and `Enum`s, naming, comments, and collaborators handed in;
  - `quality_gates.md`: the suite, and the product's own Ruff and mypy;
  - `errors_logging.md`: narrow catches, `from None`, and the one catch site;
  - `layout.md`: file names, and `__init__.py` holding re-exports only;
  - `testing_python.md`: no `monkeypatch`, fakes passed to constructors, and the layer locations;
  - `environment.md`, through the gate tool.
- **One divergence from the packet stands**, the `__version__` marker. It is a call, recorded below.
- **The edited tests meet the bar:** `ruff format --check .`, `ruff check .` and
  `mypy main.py errors.py domain application persistence web` exit 0 from the product root after
  this run's edits.

## Tests added or fixed

**Fixed — `tests/e2e/test_moves.py`, two defects.** Both were found by reading the file and checking it against the route's real addresses. The file cannot run here (§ Not verified).

1. **The landing wait asserted a query order that nothing in the intent fixes, and the code does not produce.**
   - *The defect.* `test_tab_to_a_rows_move_button_and_press_space_lands_on_that_rows_status_element`
     and `test_the_same_move_from_the_task_page_with_enter_lands_on_the_status_area` waited for
     `re.compile(r"/projects/1\?move_task=1&moved=in-progress$")` and its `/tasks/1` twin. The route
     answers `/projects/1?moved=in-progress&move_task=1` and `/tasks/1?moved=in-progress&move_task=1`
     (probed through the real `Site`). The old pattern does not match that address, so each wait would
     have timed out.
   - *The fix.* The tests now wait with `landed_at(path)`. It checks the path, that there is no
     fragment (RT-9), and the query pairs `move_task=1` and `moved=in-progress`, in any order. It was
     checked against eight addresses: both query orders, the wrong page, a bare page, `?added`, a
     fragment, and a wrong status.
   - *Why the test, not the code.* See Calls made, 1.
2. **The 24-by-24 test clicked a button that was not there on its second pass.**
   - *The defect.* `test_every_move_button_is_at_least_24_by_24_pixels` pressed the `in-progress`
     move at the end of both passes. After the first press the task is `in-progress`, which offers
     `done` and `todo` and no `in-progress` button. So the second click would have waited for a
     button that does not exist, and failed.
   - *The fix.* The move is pressed once, between the `todo` pass (one button) and the `in-progress`
     pass (two buttons). That keeps what the plan asks for: every move button's box, on both pages,
     in both statuses that offer a move. The wait after the press now uses `landed_at` as well.

**Tightened — `tests/integration/test_move_routes.py`,
`test_a_non_status_or_missing_status_is_refused_and_answered_like_a_stale_press` (R5).**

- *The gap.* CP-309 says a non-status move "is answered as CP-308 answers", and CP-308 says "the page
  that answers is the page the button was on … at the task's row". R5 checked the reason and the
  focused word. It never checked where the answer landed, and the task's own page carries the same
  status word.
- *The change.* It now asserts that the redirect goes to `/projects/1?…`, with no `#`, and that the
  focused element sits in that row's status cell.

**Tightened — `tests/integration/test_move_pages.py`,
`test_a_landing_page_has_exactly_one_autofocus_on_a_non_control_status_element_that_names_the_line`
(P6).**

- *The gap.* The plan and the design put the focused status word "in the row's status cell" and the
  line "in that row's moves cell" (Task 4; design D-3 and D-4). P6 checked only that both sat
  somewhere in the row.
- *The change.* On the list it now asserts the status cell and the moves cell. On the task page it
  asserts the status area, as before.

**Added — `tests/integration/test_move_pages.py`,
`test_a_move_outcome_about_a_real_task_of_another_page_renders_the_page_plain`.**

- *The gap.* The plan says "a task identity that is not a row on that page … yields no outcome, and
  the page renders plain". P8 proves this only with `move_task=999`, a task that does not exist. That
  case cannot tell "is a row of this page" from "exists at all".
- *The test.* It uses two projects, with task 2 in the second. An outcome about task 2 must leave
  project 1's page and task 1's page byte-for-byte equal to the plain pages, with no focus.

**Left as they are.** Every other test, new or edited, matches its intent:

- U1 to U6 and the place test;
- T1 to T5 and the stale-state test;
- R1 to R4, R6 to R11, the two-project test and the `cancelled` reason test;
- P1 to P5, P7, P8 and the other-rows test;
- E1 to E7.

Each asserts the intent's own values: the workflow tuples, the sixteen pairs, `change_text.md`'s
strings, the saved bytes, and the console lines. None asserts a value read off the code.

## The finding

**No code defect.** Every behaviour of the intent has a test, and every test that runs here is green against the code as the developer left it.
No code was changed in this run, and there was no misplacement.

**Two test defects were fixed**, both in `tests/e2e/test_moves.py`, a file the card's suite does not
collect. As the file stood, two of its three tests would have timed out on the landing wait, and the
third would have failed on its second pass, wherever Chromium runs. The developer's marker already
named the URL waits as the thing "most likely to need a fix". **Two tests were tightened and one
was added**, as listed above.

## Calls made

1. **The browser test's landing address: the test was wrong, not the code.**
   - *The question.* Should the route's redirect put `move_task` before `moved`, as the test expected,
     or is the order free?
   - *The readings.* (a) The order is part of the landing contract, so the code changes to suit the
     test. (b) The intent fixes no order, so the test changes.
   - *Taken: (b).* CP-303 and SDD RT-9 require that the address carries no fragment and lands on the
     place. RT-8 builds every address through `_address`. Nothing in the spec, the design, the plan or
     `change_text.md` orders the query, and the integration tests, R1 and R2, assert only the path
     and the absence of `#`. Changing the code to suit an over-specified test is the one thing this
     review exists to refuse.
   - *Whose document.* `tl_instruction.md` Task 5, the Tech Lead's.
   - *If ruled the other way.* The `_redirect` call in `web/routes.py` `_move_task` changes its
     keyword order, a one-line change, and `landed_at` could then require the order.
2. **No `__version__` marker on product modules. The developer's divergence is upheld.**
   - *The question.* `conventions.md` § Naming says "Every non-test module carries
     `__version__ = "X.Y.Z"`", and the packet binds over the file's own style.
   - *The readings.* (a) Add the marker to `domain/workflow.py`, `web/pages.py` and `web/routes.py`.
     (b) The rule does not reach a product's own modules.
   - *Taken: (b).* The bullet names itself "`versioning.md`'s marker for a script", and its measured
     set is the house's own tools. `<CORE>/doctrine/governance/versioning.md` says "A product's
     artifacts version by the product's rules, not the instance's" (lines 158–160). This product
     versions in `pyproject.toml` (`version = "0.0.0"`), and none of its modules carries a marker.
     Adding one to three files would also create a pattern nothing else in the product follows.
   - *Whose document.* The Python packet's, `<CORE>/doctrine/engineering/languages/python/conventions.md`,
     which the owner keeps. Its scope could say so in words.
   - *If ruled the other way.* Every non-test module of `products/tracker17` would gain a marker. That
     is a product-wide change, larger than this one.
3. **The verdict rests on the card's suite, with the browser tests recorded as not run.**
   - *The question.* Task 5's tests could not run here. Is that a pass, or a stop?
   - *The readings.* (a) Stop, because a test the change wrote has never run. (b) Pass on the card's
     command, and record the browser tests as not verified.
   - *Taken: (b).* The card's `Test command:` is the gate, and it does not collect `tests/e2e`
     (`tests/conftest.py`; `testing_python.md`, "Layer 5 runs separately"). Task 5's own pass
     criterion reads "passes where Chromium is installed". SDD § 4 RT-4 pins the browser library as
     a setup prerequisite, and NFDR § 9 says layer 5 "runs where the pinned browser-driving library
     does". None of this skill's STOP conditions covers a layer the card does not run. The browser test was still corrected here as far as reading and probing allow.
   - *Whose call.* The Tech Lead's for Task 5's gate, and the owner's for where layer 5 runs.
   - *If ruled the other way.* This change waits for a run of
     `pytest products/tracker17/tests/e2e/test_moves.py` on a machine where Chromium starts, such as
     the owner's Mac.

## Not verified

- **`tests/e2e/test_moves.py` has not run, before or after this review's fixes.**
  - *Why.* Playwright's Chromium does not start on this machine. A launch exits 127, the same missing
    system libraries the developer reported, and there is no way to install them here.
  - *What was checked instead.*
    - The file collects (3 tests) and passes Ruff.
    - Its landing predicate was run against the real route's addresses.
    - Its open-task and Tab steps follow `tests/e2e/test_labels.py`.
    - Clicking at (1, 1) lands in the body's 24px padding, which holds no control.
  - *What only a browser settles.*
    - The Tab count to each button.
    - Space and Enter pressing a button.
    - The 24-by-24 boxes.
    - The computed accessible description of a focused `span` inside a table cell (SDD § 11 R-2).
  - *The command to run, where Chromium works:* `pytest products/tracker17/tests/e2e/test_moves.py`.

## Test evidence

- An earlier run of the test command exited 127 and printed `Environment: owners-mac — no CI`.
  - That was the first call through `gate_suite.py`. It reported `sh: 1: pytest: not found`, because
    pytest is not installed on the host.
  - The packet says pytest is installed before the suite runs (`environment.md` § Provisioning).
    The venv the developer built from `tests/requirements.txt`, at `/tmp/venv17`, was checked against
    the pins: `pip freeze` equals the file's 15 pins exactly. It was then put on the tool call's
    `PATH`.
- An earlier run of the test command exited 0 and printed `Environment: owners-mac — no CI`.
  - That was the baseline, before any test was changed: 1169 passed.
- **The run the verdict rests on** exited 0, and its first line is the `Environment:` line above.
  - That run was made after this review's test changes: 1170 passed, in 113.33s.
- The evidence file gave no CI, with its inventory:
  - `git ls-files` holds no build-service, pipeline or runner file, and no `*.yml` or `*.yaml` file;
  - the tracked `Containerfile` builds the instance's sandbox image;
  - `.claude/workflows/` holds Claude workflow scripts.

  It gave no recorded gate decision. ADR-0009 and SDD RT-3 are about where the tracker runs, not
  where its gates run. It gave a Python candidate with no tag, because no file states CI's version.
- From the product root: `ruff format --check .` printed "191 files already formatted", `ruff check .`
  printed "All checks passed!", and `mypy main.py errors.py domain application persistence web`
  printed "Success: no issues found in 24 source files".
- Probe of the landing address: a temporary test, written to `tests/integration/` and removed in the
  same command, printed `LIST: /projects/1?moved=in-progress&move_task=1` and
  `TASK: /tasks/1?moved=in-progress&move_task=1`. The old pattern does not match the first address.
