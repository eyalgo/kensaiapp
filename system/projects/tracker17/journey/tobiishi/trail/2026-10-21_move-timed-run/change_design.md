# Change Design — time a status move at full volume

**Date:** 2026-10-21
**Category:** nfdr
**Behaviour:** changing
**Publishes text:** yes — the timed run’s move fixture report and its three timing rows

This blueprint owns the harness boundaries, callable contracts and coverage for the status-move
measurement. Its request and specification are `change_request.md` and `change_spec.md` in
`tracker17 · tobiishi · 2026-10-21_move-timed-run`; rule references below point into that specification.
Code and record paths below are relative to `products/tracker17/`.

---

## 1. Change Summary

Add a dedicated move measurement and fixture report to `tests/timed_run.py`, then append their output
to the whole run. Keep the change inside that script and `tests/integration/test_timed_run.py`, as
required by the specification’s “What does not change” and “Existing tests that change” sections
(`change_spec.md:L92-L154`).

Use the existing `Timed` result and `verdict` formatter, whose result flags, problem order, millisecond
format and strict limit check are already the required shape (`tests/timed_run.py:L108-L112`,
`tests/timed_run.py:L147-L162`, “Print each action with its time”).
No application-facing signature, data format or import edge changes.

---

## 2. Blast Radius

The SDD parts table assigns runtime responsibilities, but none owns test-harness measurement,
fixture reporting or assertions (`docs/SDD.md:L198-L222`, “The parts”). Architect placement decision,
2026-10-21: those three pieces of logic live under `tests/`, with measurement and reporting in
`tests/timed_run.py` and assertions in `tests/integration/test_timed_run.py`; see review note 1.

| Module | Status | What changes |
|---|---|---|
| `domain/` | Unchanged | Keep the rule core and its public exports. |
| `application/` | Unchanged | Keep actions, saving and clock contracts. |
| `persistence/` | Unchanged | Keep the saved-data implementation and format. |
| `web/` | Unchanged | Keep the move submission, redirects and completion page. |
| `main.py` | Unchanged | Keep runtime wiring. |
| `errors.py` | Unchanged | Keep error types. |
| `tests/` | Modified | Harness-owned move measurement, whole-state success check, loaded-fixture report, final output block and aggregate verdict in `tests/timed_run.py`; new coverage and the narrowly permitted existing-test input/output updates in `tests/integration/test_timed_run.py`. |

This enumerates the code set of NFDR § 1.1 QC-1 and § 1.2 QC-13–QC-19
(`docs/nfdr.md:L34-L38`, `docs/nfdr.md:L139-L170`, “Forbidden imports”).
There is no transitive runtime blast radius: the production interfaces stay unchanged and QC-19
forbids imports from `tests/` outside that tree (`docs/nfdr.md:L168-L170`).

---

## 3. Sub-jobs

The one affected module group, `tests/`, has two internal seams: independently callable measurement
and reporting, then whole-run orchestration. B consumes A’s callables. That ordering edge warrants a
cut below module granularity; each sub-job remains inside `tests/` (architect decision, 2026-10-21).

### Sub-job A — move measurement and fixture report

**Scope:** Add the following contracts to `tests/timed_run.py`, with focused tests in
`tests/integration/test_timed_run.py`.

**Exposes:**

- `MOVE_TASK_ID`, fixed to 4, identifies the task to move in both measurement and reporting.
  Architect decision, 2026-10-21: this identity is present in both the full fixture and the specified
  300-task variant, and the seed assigns it `todo` (`tests/timed_run.py:L169-L201`, “The number-th
  seeded task”; specification CP-371 and CP-386).
- `measure_task_move(*, site, saved_data, timer)` returns three existing `Timed` values, ordered
  POST, landing, total. The collaborators are required and handed in. The POST is exactly one
  request to `/tasks/4/move`, with URL-encoded fields `status=in-progress` and `place=list`, and
  the existing `FORM_HEADERS`. The page’s form carries those two fields and the route uses `place`
  to choose the project list (`web/pages.py:L713-L721`, “_move_form”;
  `web/routes.py:L737-L762`, “The status goes to the tracker as sent”).
- Load the pre-state and resolve task 4 before opening the POST interval. Build the exact expected
  project-list address from that task’s loaded project identity and identity, in CP-377’s query order.
  Require both status 303 and exact `Location` equality before requesting a landing. Read back the
  saved state after closing the POST interval and before opening the GET interval. A correct redirect
  still gets its landing when the readback fails the saved-change check (CP-376–CP-379).
- Require task 4’s loaded pre-state status to be `todo` for a successful measurement. Construct the
  expected state from that pre-state, replacing only task 4’s status with `in-progress`, and compare
  the whole readback with that expected state. Do not use the workflow’s
  move function to produce the expectation: the harness must independently detect a wrong change.
  A missing saved state, unchanged status, wrong status, changed other task, changed other field,
  changed comments, changed project, changed counter, changed assignee list or changed operator name
  fails that comparison (CP-377).
- Check the GET’s 200 status and the exact CP-378 completion sentence with the loaded task title
  escaped as the page does. The page escapes the title before inserting it into that sentence
  (`web/pages.py:L790-L803`, “The one outcome to show”).
- On an invalid redirect response, return a failed landing of zero seconds and a failed total equal
  to the POST duration, without a GET or extra timer reads. Otherwise use four readings around only
  the POST and GET; the total is their durations added, and its success flag is the conjunction of
  the POST and landing flags (CP-376–CP-380).
- `move_fixture_report(state)` returns the exact CP-373 fixture line from a state loaded back from
  the fixture’s saved location. Use all loaded tasks for task and per-task comment counts, and task
  4 for title and first-comment lengths. Reuse `_volume_line` for the volume portion; it already
  derives the uniform comment count and total from the state (`tests/timed_run.py:L617-L628`,
  “read from the loaded fixture”). Use code-point lengths, as CP-374 requires.

The three timing labels and every printed character come from CP-373–CP-375, through the change’s
published-text artifact. The two callables expose values and do not print; `verdict` owns printing
timing rows, and orchestration owns printing the fixture line.

**Depends on:** none. Existing `Timed`, `verdict`, `_volume_line`, `open_task_volume`, `FORM_HEADERS`
and real `SavedData`/`Site` collaborators remain available without interface changes
(`tests/timed_run.py:L59-L63`, `L108-L162`, `L205-L215`, `L617-L628`).

### Sub-job B — whole-run integration and existing-test continuity

**Scope:** Add one final block in `tests/timed_run.py` after `_run_new_actions` returns. Open
`SavedData(directory / "move-volume")` through the unchanged `open_task_volume`, print the report
from its returned loaded state, measure the move with the handed timer, and combine the move verdict
with every existing verdict. Keep `main(directory=None, timer=...)` and every earlier action intact
(`tests/timed_run.py:L796-L827`, “main”; CP-372–CP-373, CP-381–CP-383).

**Exposes:** `main` retains its integer exit contract and appends exactly the four specified lines,
with no footer. The `move-volume` location is distinct from the existing locations and remains under
the same supplied temporary root (`tests/timed_run.py:L802-L856`, “Each prints its fixture line”).
The move consumes four additional handed-timer readings on the normal path, after all prior readings.
Update only the inputs and expected output CP-392 authorizes, preserving every previous test name,
case and assertion about the older actions.

**Depends on:** A’s `measure_task_move`, `move_fixture_report` and `MOVE_TASK_ID`.

**Build sequence:** A, then B. No dependency crosses a runtime module boundary.

**Atomic-landing edge:** B’s whole-run wiring + the finite timer-input and exact-output updates in
`tests/integration/test_timed_run.py` — no green point between them: the existing callers supply
finite readings and the order test asserts the entire label sequence
(`tests/integration/test_timed_run.py:L405-L417`, `L702-L714`, `L940-L952`, `L2045-L2083`).

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — move measurement and fixture report | A dedicated two-field measurement keeps the existing one-field `TimedAction` descriptor and its three consumers unchanged (`tests/timed_run.py:L558-L614`, “One form submission to time”). Use independent whole-state equality for success, exact response/address gating for the GET, and the existing `_volume_line` and `verdict` seams. |
| B — final output block and test-input continuity | None |

All implementation writes stay inside the resolved instance/product worktree. No write into a third
repository is part of this design.

---

## 5. Test Additions

All added or modified tests below live in `tests/integration/test_timed_run.py`. Pass recording sites,
saved-data wrappers and deterministic timers through the measurement’s collaborator arguments;
`Ticks`, `ScriptedSite` and `EventLog` already offer those seams
(`tests/integration/test_timed_run.py:L53-L80`, `L1276-L1316`, “Timer reads, requests and saved-data loads”).
Use real `SavedData` and the real product request path for the success and refusal cases.

| Row | Sub-job | Test file | What to add / modify |
|---|---|---|---|
| T1 | A | `tests/integration/test_timed_run.py` | Real full-volume success: record exactly one same-origin POST with the two required fields, to task 4, and one GET to the exact project-list redirect. Assert the pre-state has 1,000 tasks of 20 comments, task 4 is `todo`, only its status changes, and all three rows succeed. Covers CP-371, CP-372, CP-377, CP-378 and the “move is saved and lands” Example. |
| T2 | A | same | Real refusal: begin with task 4 already `in-progress` and submit the specified move. Assert only one POST, unchanged saved data, no GET, two timer reads, failed POST/landing/total flags, zero landing time and total equal to POST. Print through `verdict` and assert status 1. Covers CP-379, CP-381, CP-384 and the refusal Example. |
| T3 | A | same | Parameterize invalid POST answers: 403 (including a collaborator forwarding the submission without its same-origin mark), 500, 200 with an otherwise correct Location, missing Location, wrong project/task, missing/extra/reordered query or wrong destination. Assert no GET and failed three-row verdict, including when Location looks right but status is not 303. Covers CP-371, CP-377(a), CP-379 and the unmarked-submission Example. |
| T4 | A | same | Correct redirect with missing readback, unchanged saved state, wrong target status, second task changed, moved task’s other field/comment changed, project/counter/assignee/operator changed. Assert POST and total fail, but the exact redirected GET is still requested. Include populated assignee/operator values in the pre-state so their preservation is exercised. Covers CP-377(b) and the extra-task-change Example. |
| T5 | A | same | Real successful POST followed by a substituted landing: non-200 with the correct line, 200 without the line, title-only content, wrong task title or wrong destination status. Assert POST succeeds, landing and total fail, `verdict` returns 1. A title containing HTML-sensitive characters must pass only when the correct escaped completion line is present. Covers CP-378, CP-381, CP-385 and the missing-line Example. |
| T6 | A | same | Record the event sequence: setup and initial load before the first tick; only POST between ticks 1–2; saved-state readback between ticks 2–3; only GET between ticks 3–4. Use a large inter-interval gap and assert total equals POST plus GET rather than elapsed wall time. Covers CP-376. |
| T7 | A | same | Deterministic boundary matrix: parts and total below 1 s pass; total exactly 1 s and above 1 s fails with both parts below; POST exactly 1 s and 1.5 s fails itself and total; GET exactly 1 s and above fails itself and total. Verify raw durations select problems before one-decimal formatting, including a duration just below 1 s that rounds to `1000.0 ms`. Covers CP-375, CP-380 and both slow-row Examples. |
| T8 | A | same | Exact printed three-row strings: successful milliseconds to one decimal; refused POST taking exactly 1 s prints `refused or failed, at or over 1 s` in that order, zero failed landing and matching failed total. Covers CP-375, CP-379, CP-380 and the 1.5 s formatting case with T7. |
| T9 | A, B | same | Assert the complete fixture line on the loaded normal fixture and on a saved-and-reloaded 300-task/3-comment fixture. Retitle task 4 to `Plan 😀😀` and its first comment to `Note 😀`; require lengths 7 and 6 and total 900. Ensure task 4’s text lengths differ from the first task’s. Covers CP-374, CP-386 and the varied-fixture Example. |
| T10 | B | same | Whole-run success and exact complete output: retain the older labels in their places, then the four move lines in order, with no further line. Check the move’s fixture is `move-volume`, distinct from every older fixture, its saved delta is only the status, and product `data/` is absent or byte-identical before/after. Covers CP-372, CP-373, CP-381, CP-387 and the fast-run/after-run Examples. |
| T11 | B | same | Keep every CP-392 test under its existing name. Append four fast readings after the existing readings in the three explicitly named direct callers, the shared `_run_readings` source for both three-case families and the four `whole_run` consumers. Extend only the exact label expectation in `test_timed_run_appends_exactly_three_ordered_action_blocks` by the final four labels. Preserve every old assertion and parameter case. Covers CP-383, CP-388, CP-392 and the finite-readings Example. |
| T12 | B | same | Whole-run timer injection: make only the move total reach 1 s, then only its POST or GET reach/exceed 1 s while all older actions pass; require `main` returns 1 and the precise failing labels. Together T2/T5 verify refused and missing-result measurement verdicts feed the same integer aggregation. Covers CP-381, CP-382 and the slow-on-owner-machine Example. |

**Retired assertions:** none. The exact-output assertion gains the final four lines; its old-prefix,
ordering, no-problem and successful-exit clauses remain proved by T10/T11. The old three-block coverage
is retained under its existing test name (`tests/integration/test_timed_run.py:L2077-L2083`,
“every old line keeps its label and place”).

**Example pass:** the “run today, before the change” Example is a baseline description, not a desired
post-change output; T10/T11 retain its complete older prefix. The real-command Examples map to the
following acceptance checks rather than tests of a command-name string. The Python 3.11 Example maps
to review note 4, as that row explicitly specifies a review instead of a test. All remaining Examples
map to T1–T12 above (specification “Examples”, `change_spec.md:L159-L179`).

**Rule pass:** CP-371–CP-381 map to T1–T10/T12, including absent data, invalid redirects, a skipped
landing, saved collateral changes, missing or failed landing, exact-boundary totals and combined
problems. CP-382–CP-383 map to the two-file scope, T10–T12 and the final diff check. CP-384–CP-386 map
to T2/T5/T9. CP-387–CP-390 map to the checks below. CP-391 maps to review note 4. CP-392 maps to T11.
No new product behavior or invalid-fixture policy is introduced.

Acceptance checks, not architect-stage test executions:

- CP-387: `python3 tests/timed_run.py` from the product root of a fresh clone at the commit under
  test, requiring exit 0, all four final lines and all three move durations strictly below 1 s.
- CP-388/CP-389: `pytest products/tracker17/tests/` from the checkout root and
  `pytest products/tracker17/tests/e2e/` where NFDR § 9 supports layer 5.
- CP-390: from the product root, in its pinned virtual environment, `ruff format --check .`,
  `ruff check .`, and `mypy main.py errors.py domain application persistence web`; all exit 0.
- Python packet compile gate: `python3 -m compileall -q tests/timed_run.py tests/integration/test_timed_run.py`
  from the product root; exit 0 (`<CORE>/doctrine/engineering/languages/python/quality_gates.md`,
  “The two gates”, L12–L24).
- CP-382/CP-383: inspect the product diff for only the two authorized test files; no production
  optimization, limit change, older action change or dependency change belongs in this delta.

---

## Records this change makes false

None — read `docs/adr/README.md` and Accepted ADR-0001 through ADR-0010, `docs/nfdr.md` §§ 1–10,
`docs/fdr.md` Rules/Product decisions/Out of scope/Examples, and `docs/SDD.md` § 3. This delta supplies
the move measurement QC-48 already requires without changing any recorded runtime part, seam, rule,
quality limit or dependency (`docs/nfdr.md:L429-L436`, “Performance & capacity”;
`docs/SDD.md:L198-L243`, “The parts, and the seams between them”).

---

## Architect Review Notes

1. **Harness placement — kind (e), architect decision, 2026-10-21.** No runtime part’s `Owns` covers
   measurement or test assertions in the SDD parts table (`docs/SDD.md:L198-L222`, “The parts”).
   Place them in the existing test harness and its checker, outside the runtime parts, rather than
   give runtime code a test responsibility. No forbidden import needs changing.
2. **Dedicated measurement and explicit checks — kind (b), architect decision, 2026-10-21.** Keep
   `TimedAction` and `_measure_action` unchanged: their form contract is one `field`/`value` pair
   (`tests/timed_run.py:L558-L594`, “One form submission to time”). The move needs two fields
   (`web/pages.py:L713-L721`, “_move_form”). The dedicated helper, identity 4, exact redirect
   comparison, independent expected whole state, escaped completion check, duration sum and final
   append make CP-371–CP-381 hold explicitly. Do not infer success from a plausible redirect or title
   alone. Identity 4 avoids relying on a task position or finding a particular status by accident.
3. **Sub-module cut — kind (d), architect decision, 2026-10-21.** A’s returned values are the contract
   B consumes. Keeping these seams explicit gives the measurement an independent landing point;
   enabling the whole-run block also changes finite-timer callers and the exact-output expectation
   (`tests/integration/test_timed_run.py:L2045-L2083`, “The timer readings of one whole run”).
4. **Language and QC-60 review — pass for this design, 2026-10-21.** Language resolution: Python,
   step 1, `project.md` Languages, opened `<CORE>/doctrine/engineering/languages/python/README.md`
   and all seven routed concerns. Keep this product’s Python 3.11 floor, which outranks the packet’s
   default floor (`docs/nfdr.md:L492-L500`, QC-59/QC-60; `docs/adr/0002-standard-library-only-no-web-framework.md:L15-L27`,
   “Decision”; `<CORE>/doctrine/engineering/languages/README.md`, “Precedence”). The design uses
   existing dataclasses, URL encoding, HTML escaping, path handling and callable-timer seams
   (`tests/timed_run.py:L26-L37`, `L169-L215`, `L579-L628`). Add no newer syntax or library API,
   dependency or pin. This is compatibility review, not a claim of a Python 3.11 suite run.
5. **QC-12 simplicity and QC-41 secrets review — pass for this design, 2026-10-21.** The two-file
   test-only delta adds no runtime part, service, account, key or saved field. It reuses the product’s
   existing full-volume setup and output model (`tests/timed_run.py:L205-L215`, `L802-L856`), as
   required by `docs/nfdr.md:L132-L137` (QC-12) and `L352-L356` (QC-41). Runtime-specific design
   reviews QC-5/QC-8/QC-20–QC-27/QC-36/QC-46 are inapplicable to unchanged runtime code and data
   schema (`docs/nfdr.md`, §§ 1–4).
6. **QC-40 dependency and browser review — pass under the recorded browser exception, 2026-10-21.**
   Compare the 15 pins in `tests/requirements.txt:L4-L18` locally against the public PyPA advisory
   database at commit `9a8aa073f2b8fbb331c6bb22b30929f16bef23ed`
   (https://github.com/pypa/advisory-database/tree/9a8aa073f2b8fbb331c6bb22b30929f16bef23ed/vulns).
   The downloaded database has six records for those package names: five for Pygments, whose newest
   fixed boundary is 2.20.0, and one for pytest, fixed at 9.0.3; the lock pins 2.21.0 and 9.1.1,
   respectively (`tests/requirements.txt:L15-L16`; the database’s `vulns/pygments/` and
   `vulns/pytest/PYSEC-2026-1845.yaml` at that commit). All six fixed boundaries precede their pins;
   this review finds no affected locked package in that database. This is a dated database review,
   not a guarantee about unpublished vulnerabilities.

   The browser contract pins Chromium `153.0.8010.12`
   (`tests/e2e/test_moves.py:L510-L510`, `L599-L599`, “PINNED_BROWSER”). Google’s 2026-09-08 release
   fixes critical issues in `153.0.8010.36/.37`
   (https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0808145027.html).
   Treat the earlier build as exposed; do not declare it vulnerability-free. NFDR RN-33 expressly
   permits that build at a design review through 2026-11-07, so the dated exception applies on this
   review date (`docs/nfdr.md:L1022-L1035`, “Dated exception to QC-40”). No pin or exception moves.
   The browser package is absent from this process’s Python environment (`python3` with
   `importlib.util.find_spec('playwright')` returned `None`); no installed-browser version is claimed.

   The package-specific PyPI metadata request was denied before execution by automatic approval
   review because it would disclose local dependency names and versions. The permitted alternative
   downloaded the public PyPA database without sending those names and compared it locally. The
   archive’s SHA-256 is `aaa3495bd3e5897f5c7f0f212292f58c5e14ea746d8b8ce534a2968e52654e56`;
   its tar header identifies the database commit above. The incomplete GitHub API pagination is not
   evidence for the verdict.

**Cold-read:** checked all nine changing-mode checks: module coverage and placement; callable
contracts; A-before-B ordering and the atomic edge; every Example and rule edge in § 5; explicit
success, duration and append contracts; recorded architectural decisions; the records zero form;
settled published-text header; and no third-repository write. No spec reading is set aside by this
design. The review does not claim a product suite or timed acceptance run; those checks belong to
the implementation of the delta.
