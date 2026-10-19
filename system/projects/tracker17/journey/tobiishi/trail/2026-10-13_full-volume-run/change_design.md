# Change Design — Complete the timed run for comments and People assignees

**Date:** 2026-10-13
**Category:** nfdr
**Behaviour:** changing
**Publishes text:** yes — the timed run's console fixture reports and action timing rows

**Language resolution:** Python — project card `Languages:`; opened
`core/doctrine/engineering/languages/python/README.md` and its five sibling concerns plus
`core/doctrine/engineering/testing_python.md`, per the language resolution chain
(`core/doctrine/engineering/languages/README.md` § The resolution chain).

---

## 1. Change Summary

This design extends the timed harness and its integration tests for the comment add and the
People assignee add and remove, as specified by `tracker17 · tobiishi · 2026-10-13_full-volume-run`,
`change_spec.md` § Rules, CP-276–CP-292 (`change_spec.md:L23-L98`). It owns the harness seams,
saved-state verification, dependencies and test coverage for that extension.

Confine code changes to `products/tracker17/tests/timed_run.py` and
`products/tracker17/tests/integration/test_timed_run.py`. Preserve every existing action, fixture,
row, limit and assertion per CP-276, CP-277 and CP-289 (`change_spec.md:L23-L29`, `L87-L89`).
Use real saved files and the request path, with one independent full-volume fixture per new action,
per CP-277 and CP-278 (`change_spec.md:L24-L33`). Console wording is CP-285 and CP-286's;
the pages' completion lines are comparison inputs, with no page wording change
(`change_spec.md:L53-L58`, `L69-L80`).

Paths beginning `products/` or `system/` are relative to the change worktree. Paths beginning
`tests/`, `domain/`, `application/`, `persistence/` or `web/` are relative to
`products/tracker17/`, the project card's `Product path:` (`system/projects/tracker17/project.md:L3-L3`).
The output lives in this change's folder per `core/doctrine/setup/kensaiapp_structure.md` § 2,
`journey/tobiishi/<key>/` (`core/doctrine/setup/kensaiapp_structure.md:L2104-L2108`).

---

## 2. Blast Radius

The production parts table names `domain`, `application`, `persistence`, `web` and `main`, and
places `tests/` beside them in the package unit (`products/tracker17/docs/SDD.md` § 3,
“The parts” and “The units”, `L195-L217`). None of those parts owns test-fixture construction,
timing, harness result checks or harness console reporting. Place all four in `tests/timed_run.py`,
under the timed-run obligation of SDD TS-5 (`products/tracker17/docs/SDD.md:L462-L467`), and
place their regression checks in `tests/integration/test_timed_run.py`. Review note E1 records
the placement the parts table does not supply.

| Module | Status | What changes |
|---|---|---|
| `domain/` | Unchanged | CP-292 keeps entities, rules and exports unchanged (`change_spec.md:L98-L98`). |
| `application/` | Unchanged | CP-292 keeps action orchestration and saving/clock contracts unchanged (`change_spec.md:L98-L98`). |
| `persistence/` | Unchanged | CP-292 keeps the saved-data implementation and format unchanged (`change_spec.md:L98-L98`). |
| `web/` | Unchanged | CP-292 keeps routes, pages, escaping and request checks unchanged (`change_spec.md:L98-L98`). |
| `main.py` | Unchanged | CP-292 keeps product wiring unchanged (`change_spec.md:L98-L98`). |
| `errors.py` | Unchanged | CP-292 keeps the error surface unchanged (`change_spec.md:L98-L98`). |
| `tests/` — `timed_run.py` | Modified | Harness-owned fixture preparation, three measurements, exact saved-delta and landing checks, fixture reports and whole-run verdict integration; placement E1. |
| `tests/` — `integration/test_timed_run.py` | Modified | Harness-owned regression checks for the three measurements and their whole-run effects; extend only the three existing scripted timer inputs named by CP-289 (`change_spec.md:L89-L89`). |

No production public interface or import edge changes. NFDR QC-13–QC-19 prohibit production
imports from `tests/`, so there is no transitive production blast radius
(`products/tracker17/docs/nfdr.md` § 1.2, `L131-L153`). The harness's consumer is its integration
test module, which imports it by path (`tests/integration/test_timed_run.py` `harness`, `L33-L43`).
No new module or dependency is required.

---

## 3. Sub-jobs

Only `tests/` is modified. Split below that module at its two file seams: the executable harness
and the integration checks that consume its measurement interfaces. The dependency is the new
measurement contract used by the checks. This is the single-module exception in the skill's
Step 3, recorded in review note D1.

### Sub-job A — `tests/timed_run.py`

**Scope:** Fixtures, measurement functions, saved-result predicates, fixture reports and the
three appended action blocks in `main`. Keep all existing callable signatures and result fields.
The existing result is `Timed(label, seconds, created)` (`tests/timed_run.py` `Timed`, `L103-L106`),
and `main(directory, timer)` is the whole-run seam (`tests/timed_run.py` `main`, `L525-L556`).

**Exposes:**

- Three measurement functions: `measure_comment_add`, `measure_assignee_add` and
  `measure_assignee_remove`. Each receives explicit keyword-only `site`, `saved_data` and `timer`
  collaborators and returns a list of three existing `Timed` values, in submission, landing,
  total order. The supplied site needs only `handle(method, target, headers, body)`.
- Three fixture openers: `open_comment_volume(saved_data)`, `open_assignee_add_volume(saved_data)`
  and `open_assignee_remove_volume(saved_data)`. Each returns the real site and the loaded
  pre-action `TrackerState`. Prepare the action-specific immutable fixture before saving and
  loading it. Preserve `seeded_state()` and `open_task_volume()` for all old callers.
- Fixture locations `comment-volume`, `assignee-add-volume` and `assignee-remove-volume`, each
  below the directory supplied to `main`. No new action reuses another action's location.
- Ordinary inputs `COMMENT_TASK_ID` = 250, `COMMENT_TEXT`, `COMMENT_OPERATOR_NAME` and
  `ASSIGNEE_NAME`. Use `Jordan Rivera` for the saved operator and `Avery Chen` for the assignee
  examples. These are fixture values, not new product constants. Choose comment text distinct
  from every seeded comment so the landing check proves the submitted text is shown.
- The comment fixture saves the operator name. The assignee-add fixture lacks the submitted
  name. The assignee-remove fixture carries it. All start with the existing 1,000 tasks and
  20 comments per task, as CP-277 requires (`change_spec.md:L24-L29`). Additional test variants
  may carry other assignee names and a task assigned to the removed name, to prove preservation.
- `comment_fixture_report(state)`, `assignee_add_fixture_report(state)` and
  `assignee_remove_fixture_report(state)` return CP-286's exact report shapes
  (`change_spec.md:L77-L80`). Read volume, each task's comment count, total comments, and title,
  seeded-comment and operator-name lengths from the loaded pre-action fixture. The comment
  report uses the selected task's title and one of its original comments. Read submitted-value
  lengths from the same ordinary values the corresponding request uses. No count is a copied
  volume or length literal.
- `main` preserves the old output prefix and then emits the three action blocks in CP-285's
  explicit order (`change_spec.md:L69-L75`). Each fixture report precedes its three result rows.
  Its return value aggregates all old and new verdicts, per CP-287 (`change_spec.md:L81-L81`).

**Measurement contract:**

1. Load the pre-action state outside the timed interval. Select the target task by identity.
   Build the expected redirect from that identity and the existing comment count, or from the
   submitted name encoded with the same query encoding as the request. CP-279–CP-281 fix these
   exact redirects (`change_spec.md:L37-L45`); the product builds them in
   `web/routes.py` `_add_comment`, `_add_assignee`, `_remove_assignee` (`L602-L661`, `L697-L709`).
2. Time only the single `site.handle` POST between two timer readings. Send the one form field
   and the existing `FORM_HEADERS`, per CP-278 (`change_spec.md:L30-L33`;
   `tests/timed_run.py` `FORM_HEADERS`, `L54-L58`). Fixture construction, save, load, request
   encoding and saved-state validation are outside this interval.
3. A successful submission needs both the exact `303` redirect and a fresh saved-state readback
   from that measurement's `saved_data`. For a comment, require exactly one new final comment
   on the selected task, preserving every old comment and every other state field. Compare its
   text and author against the submitted text and the pre-action operator name. Exclude only
   the newly added comment's `created_at` from the expected-delta comparison. For assignee add
   and remove, compare the whole readback with the pre-state changed only by that one list
   operation. Do not call the product action being checked to compute the expected result.
4. With any status other than `303`, missing location, refusal/failure redirect or wrong
   location, send no GET. Return the measured failed submission, a failed zero-duration landing,
   and a failed total carrying the submission duration, per CP-282 (`change_spec.md:L46-L52`).
5. With an exact `303`, time a GET to that exact location, using the tracker's host. Perform the
   saved-state check before the landing interval. The landing requires `200` and CP-283's
   action-specific line with typed values escaped. The comment also requires the distinct
   submitted text (`change_spec.md:L53-L58`; `web/pages.py` `_comment_outcome`, `_comment_item`,
   `L924-L953`, and assignee outcome, `L1169-L1178`). A plausible redirect with an invalid saved
   delta may still request its landing, but its submission and total remain failed.
6. The total duration is the sum of the two measured intervals, excluding the gap between them.
   Its `created` flag is submission-success AND landing-success. Feed all three values through
   the existing `verdict` and unchanged `LIMIT_SECONDS` for CP-284–CP-287
   (`change_spec.md:L62-L81`; `tests/timed_run.py` `verdict`, `L138-L153`).

**Depends on:** none. Product routes and the `SavedData`, `Tracker`, `Site` and immutable state
contracts are unchanged inputs to this sub-job, as required by CP-292 (`change_spec.md:L98-L98`).

### Sub-job B — `tests/integration/test_timed_run.py`

**Scope:** Add the checks in § 5 and extend the three CP-289 timer scripts without removing,
skipping or relaxing any existing assertion (`change_spec.md:L89-L89`). Update this test module's
trace docstring to include the new harness rules, NFR-1 and AC-15.

**Exposes:** Tests of A's measurement and whole-run contracts, using real saved data in
`tmp_path`, a handed-in recording/intercepting site, and the existing `Ticks` fake. The existing
`Intercept` records method, target, headers and body without changing the wrapped module
(`tests/integration/test_timed_run.py` `Intercept`, `L194-L209`).

**Depends on:** A's named openers, ordinary inputs, measurement result ordering, report functions,
fixture locations and `main` contract. Expected deltas, redirects and output strings in tests
come independently from CP-279–CP-286, rather than from the harness's predicates or completion
templates (`change_spec.md:L37-L80`).

**Build sequence:** Prefer B's backwards-compatible CP-289 timer-input extension first, then
A's harness extension, then B's new consumer checks. The reason for that first placement is
compatibility with the old whole-run tests; A's measurement/reporting contract remains the
interface prerequisite for B's new checks. The three action measurements have no dependency
on one another's saved state. There is no additional atomic-landing edge: unused extra readings
do not fail `Ticks`, which returns values only when called
(`tests/integration/test_timed_run.py` `Ticks`, `L46-L54`).

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — fixtures, measurement and reporting | Compare immutable whole-state values, allowing only the intended delta; mask only the new comment's timestamp. Keep pre/post saved-data reads outside timer spans. Query-encode expected names and HTML-escape expected landing values. Derive fixture counts from the loaded pre-state. |
| B — harness regression checks | Use a recording wrapper around a real site for request and landing cases, and a scripted responder that can write an independently constructed wrong saved state for false-success cases. Supply both as collaborators; patch no module name. |

---

## 5. Test Additions

All T1–T12 rows belong to sub-job B and live in `tests/integration/test_timed_run.py`. The
measurement enters `Site.handle` in process and verifies rendered responses, matching the
product's layer-3/layer-4 arrangement (`products/tracker17/docs/nfdr.md` § 9, `L516-L530`).
Use real saved files and deterministic handed-in timers. Do not add a collected wall-clock
performance threshold: the real-clock command remains the separate QC-48 check
(`products/tracker17/docs/nfdr.md` § 9, “Outside the layers”, `L539-L543`).

| Row / sub-job | Test file | What to add / modify |
|---|---|---|
| T1 / B | `tests/integration/test_timed_run.py` | Whole-run coverage and ordering: every old fixture/action label remains in its old order; exactly the three CP-285 blocks follow, each report before its three rows; no extra timed action. The before-change Example is the baseline at input commit `f411afe7a867a6d81683783b7e78d2d672e324c7`; its old prefix is the characterization retained by this test, while the post-change assertion requires the appended blocks. CP-276, CP-285, CP-287. |
| T2 / B | `tests/integration/test_timed_run.py` | Fixture isolation: inspect each loaded pre-state for 1,000 tasks and 20 comments on every task, required operator/list conditions and an independent real location under the supplied temporary directory. Acting on one leaves the other fixtures unchanged. Keep the name-save fixture unnamed. Compare product `data/` presence and, where present, its entries/bytes before and after without writing to it. CP-277. |
| T3 / B | `tests/integration/test_timed_run.py` | For each action record exactly one POST to its prescribed route, then the exact redirected GET. Assert host, same-origin mark and decoded body containing only `text` or only `name`. Assert success and the three result labels. CP-278–CP-281. |
| T4 / B | `tests/integration/test_timed_run.py` | Comment saved delta: task 250 gains exactly one final comment, preserving its preceding 20 and every other field/task; text matches the submission and author matches the fixture's saved operator. Use whole-state equality excluding only the new timestamp. CP-279. |
| T5 / B | `tests/integration/test_timed_run.py` | Assignee deltas: add exactly the requested name and remove exactly that name with every other state field intact. Include an unrelated listed name and a task already carrying the removed name so preservation is non-vacuous. CP-280, CP-281. |
| T6 / B | `tests/integration/test_timed_run.py` | Refusal/failure/address matrix for all three actions: real no-name comment refusal, duplicate-assignee add refusal and unlisted remove refusal; scripted failure redirect, `500`, another non-303 status, a non-303 carrying an otherwise correct Location, missing Location, wrong task/name/count, plain redirect and unrelated address. Assert failed submission/landing/total, no GET, measured request retained, zero landing duration and verdict 1. CP-282, CP-288. |
| T7 / B | `tests/integration/test_timed_run.py` | Exact-looking success with false saved delta: no write, missing saved state, wrong comment text/author/target/order/count, changes to earlier comments or unrelated fields; assignee unchanged, wrong name, extra name removal, task-assignee clearing or another unrelated change. Build valid wrong states independently through the supplied saver. Assert failed submission and total and verdict 1 even if the correct-address landing is plausible. CP-279–CP-282. |
| T8 / B | `tests/integration/test_timed_run.py` | After each real POST, substitute landing `404`/`500`, no completion line, another action's line, wrong task title or wrong assignee name; for comments also correct line without the new text and new text without the line. Assert submission done, landing/total failed, verdict 1. Include a correct replacement page as a passing control. CP-283, CP-288. |
| T9 / B | `tests/integration/test_timed_run.py` | For each action, deterministic intervals: 0.4 + 0.5 passes; 0.5 + 0.5 fails only total; total above 1 fails; POST exactly 1 fails POST and total; landing exactly 1 fails landing and total. Assert exact result order, approximate duration sum, unchanged 1.0 limit, problem wording and verdict. CP-284, CP-285. |
| T10 / B | `tests/integration/test_timed_run.py` | Whole-run verdict propagation: scripted readings make each new action's total alone hit 1.0 while all other actions pass; also exercise slow POST and slow landing for each action with their corresponding slow total. Assert the precise failing labels and main return 1. Include the Example with only assignee-remove total slow. CP-287. |
| T11 / B | `tests/integration/test_timed_run.py` | One whole-run fixture-report test checks all three CP-286 literal shapes against each loaded pre-action fixture and the actual submitted values, every task's 20 comments, summed 20,000 comments and actual code-point lengths. Check output order and no `over` or `refused` in the passing report. Add report-function checks using alternate valid pre-states with different task/comment counts and title/comment/operator text, including an astral character, while keeping submitted ordinary inputs unchanged. This detects copied counts and byte/UTF-16 length substitution without patching a module name. CP-285, CP-286, CP-288. |
| T12 / B | `tests/integration/test_timed_run.py` | Keep all existing tests. Change only the supplied timer values in `test_timed_run_fails_when_only_the_edit_fails`, `test_timed_run_fails_when_only_a_label_action_fails` and `test_full_timed_run_fails_when_only_name_measurement_fails`: append four under-limit readings per new action, 12 total. All existing assertions and slow-action choices remain exact. CP-289. |
| V1 / A + B | Existing script and full suite | At the resulting code commit, in a fresh clone checked out at that commit, `python3 tests/timed_run.py` from `products/tracker17` exits 0 and prints the required successful blocks; `pytest products/tracker17/tests/` from the clone root exits 0. Covers the fresh-clone Example and CP-290 (`change_spec.md:L93-L93`). |
| V2 / A + B | Existing quality checks | `ruff format --check .` and `ruff check .` from the clone's product root, at locked versions, each exit 0. Covers the Ruff Example and CP-291 (`change_spec.md:L94-L94`). |
| V3 / A + B | Change diff | Compare the resulting product diff against the change input commit: only the two scoped Python files change; no production part, dependency, threshold or product document changes. Covers the diff Example and CP-292 (`change_spec.md:L98-L98`). |

**Examples pass.** Numbering the Examples by their displayed order, excluding the heading:

| Example numbers / scenarios | Coverage |
|---|---|
| 1 before-change run; 2 whole run after | T1 |
| 3 absent `data/`; 4 comment fixture; 5 unnamed name fixture | T2 |
| 6 comment submission | T3 |
| 7 comment saved at position 21 | T3, T4 |
| 8 no-name refusal | T6 |
| 9 correct redirect without save; 10 wrong author | T7 |
| 11 assignee add | T3, T5, T8 passing control |
| 12 duplicate add | T6 |
| 13 assignee remove | T3, T5, T8 passing control |
| 14 absent remove; 15 failure redirect or 500 | T6 |
| 16 comment landing lacks completion | T8 |
| 17 total 0.9; 18 total 1.0; 19 submission 1.0 | T9 |
| 20 passing row; 21 passing whole report; 22 assignee fixture line | T9, T11 |
| 23 only assignee-remove total slow | T10 |
| 24 refusal and wrong landing per action | T6, T8 |
| 25 fixture-report test | T11 |
| 26 old label failure test | T12 |
| 27 fresh clone; 28 Ruff; 29 diff | V1, V2, V3 |

The Example source is `change_spec.md` § Examples (`L103-L131`).

**Rules pass.** CP-276 → T1; CP-277 → T2, including data absent/present, fixture independence and
the unchanged name-save precondition; CP-278 → T3; CP-279 → T4/T7; CP-280–CP-281 → T5/T7,
including tasks retaining removed names; CP-282 → T6/T7, including missing/wrong redirects,
non-303 answers and plausible redirects with invalid readback; CP-283 → T8, including both
missing-comment-text and missing-line cases; CP-284 → T9/T10; CP-285 → T1/T9/T11; CP-286 → T11;
CP-287 → T6–T10 and whole-run T10; CP-288 → T6/T8/T11; CP-289 → T12; CP-290–CP-292 → V1–V3
(`change_spec.md` § Rules, `L23-L98`).

No existing assertion is retired. T12 re-proves the same three existing full-run failure clauses
with longer input streams. Preserve their assertions about the exact failing labels and verdict
(`tests/integration/test_timed_run.py` named tests, `L398-L408`, `L693-L705`, `L929-L941`).

---

## Records this change makes false

None — read `products/tracker17/docs/adr/README.md` and Accepted ADR-0001–ADR-0009,
`products/tracker17/docs/nfdr.md`, `products/tracker17/docs/fdr.md` and `products/tracker17/docs/SDD.md`
§ 3. On this design, the change extends verification of existing actions under NFDR QC-48 and
SDD TS-5, without changing a part, seam, field, product rule, import or dependency
(`products/tracker17/docs/nfdr.md:L412-L419`; `products/tracker17/docs/SDD.md:L462-L467`;
`change_spec.md:L98-L98`). No sentence in those records needs a correction for this delta.

---

## Architect Review Notes

The architecture decisions below are the Architect's calls on 2026-10-13.

- **E1 — logic outside the production parts table (kind e):** Place fixture preparation,
  timing, completion verification and console reporting in the harness, and their tests in its
  existing integration file. The SDD § 3 table assigns runtime responsibilities to five parts
  (`products/tracker17/docs/SDD.md:L195-L217`); TS-5 places the timed run in `tests/timed_run.py`
  (`products/tracker17/docs/SDD.md:L462-L467`). No production part owns harness logic and no
  forbidden import is needed. This keeps CP-292's production-code fence intact.
- **D1 — sub-module split (kind d):** Cut the two existing files under `tests/` into A and B.
  Their reasons for changing differ, and B consumes A's three measurement contracts. The split
  makes that contract dependency explicit without adding a package or runtime part.
- **B1 — completion by construction (kind b):** Use exact redirect equality and independent
  whole-state expected-delta comparisons. Normalize only the newly added comment's timestamp
  for equality. This realizes CP-279–CP-282's “nothing else differs” requirement without
  assuming a correct redirect proves a save (`change_spec.md:L37-L50`). With a correct redirect
  but bad saved state, retain CP-283's independently checked landing and fail the total; CP-282
  suppresses the GET only for a status/redirect mismatch (`change_spec.md:L52-L58`).
- **B2 — ordering, measurement and fixture reporting by construction (kind b):** Append the
  three blocks explicitly in CP-285's order; bracket POST and GET separately; sum their measured
  durations; read reports from the same loaded pre-action fixtures. This realizes CP-284–CP-286
  without relying on dictionary iteration, fixture constants or an elapsed interval that
  includes setup/readback (`change_spec.md:L62-L80`). Use actual selected-task lengths rather
  than a different task's title length. Use distinct comment text so the landing check cannot
  pass on one of the fixture's old comments.
- **B3 — new seams use handed-in collaborators (kind b):** The three new measurement functions
  take explicit keyword-only collaborators, while old signatures stay unchanged. Tests hand in
  site wrappers and timers and compute expected deltas independently. This realizes CP-288's
  no-patching requirement (`change_spec.md:L85-L87`) and Python's constructor/collaborator
  convention (`core/doctrine/engineering/languages/python/conventions.md` § Constructs,
  “Several collaborators arrive keyword-only, and none carries a default”).
- **B4 — compatibility before whole-run consumption (kind b):** Prefer the CP-289 timer-input
  extension before wiring the new measurements into `main`. Extra unused readings are compatible
  with the old run because `Ticks` advances only on a call (`tests/integration/test_timed_run.py`
  `Ticks`, `L46-L54`); this gives the old failure assertions a green compatibility point and
  avoids inventing an atomic-landing constraint.
- **QC-12 — simplicity review: pass.** Two existing files, three action measurements and their
  checks serve the requested coverage; no generic action framework, new production part,
  runtime dependency or persistence optimization is introduced. This meets the review question
  in `products/tracker17/docs/nfdr.md` § 1.1, QC-12 (`L115-L120`).
- **QC-28 — replaceability review: pass.** The new tests use collaborators passed to the harness
  and patch no product-module name, as CP-288 requires (`change_spec.md:L87-L87`;
  `products/tracker17/docs/nfdr.md:L224-L229`).
- **QC-41 — secrets review: pass.** The design uses synthetic fixture names and ordinary text
  only and introduces no secret, account, key or credential, meeting the review boundary in
  `products/tracker17/docs/nfdr.md` § 2, QC-41 (`L336-L339`).
- **QC-60 — Python floor review: pass for the proposed constructs.** The design adds no
  language/library feature beyond immutable replacements, query encoding, escaping and injected
  callables already used by the harness (`tests/timed_run.py` imports, `L22-L47`,
  `_measure_label_action`, `L391-L438`). The unchecked Python-3.11 suite remains the explicitly
  recorded gap in NFDR QC-60 (`products/tracker17/docs/nfdr.md:L479-L483`); this design claims
  no interpreter-floor execution result.
- **QC-40 — dependencies and browser review: pass under the recorded dated exception.** The
  15 locked package versions are `tests/requirements.txt:L5-L19`. The table below records
  each version-specific PyPI advisory response from this review.
  Playwright 1.63.0's release lists Chromium 153.0.8010.12
  (https://github.com/microsoft/playwright/releases/tag/v1.63.0, “Browser Versions”). Running
  `'~/Library/Caches/ms-playwright/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing' --version`
  returned `Google Chrome for Testing 153.0.8010.12`. On version comparison, that build predates
  Google's 2026-09-08 desktop update to 153.0.8010.36/.37, which lists critical security fixes
  (https://chromereleases.googleblog.com/2026/?amp=1, “Stable Channel Update for Desktop”,
  2026-09-08). NFDR RN-33 grants that exact build an exception through 2026-11-07
  (`products/tracker17/docs/nfdr.md:L993-L1006`), so it does not block this 2026-10-13 review.
  The design changes no pin, lock format or browser choice.

| Version-specific advisory source checked on 2026-10-13 | Actual returned field |
|---|---|
| https://pypi.org/pypi/ast_serialize/0.12.1/json | `vulnerabilities: []` |
| https://pypi.org/pypi/greenlet/3.5.6/json | `vulnerabilities: []` |
| https://pypi.org/pypi/iniconfig/2.3.1/json | `vulnerabilities: []` |
| https://pypi.org/pypi/librt/0.16.0/json | `vulnerabilities: []` |
| https://pypi.org/pypi/mypy/2.4.0/json | `vulnerabilities: []` |
| https://pypi.org/pypi/mypy_extensions/1.1.0/json | `vulnerabilities: []` |
| https://pypi.org/pypi/packaging/26.3/json | `vulnerabilities: []` |
| https://pypi.org/pypi/pathspec/1.1.1/json | `vulnerabilities: []` |
| https://pypi.org/pypi/playwright/1.63.0/json | `vulnerabilities: []` |
| https://pypi.org/pypi/pluggy/1.6.0/json | `vulnerabilities: []` |
| https://pypi.org/pypi/pyee/13.0.1/json | `vulnerabilities: []` |
| https://pypi.org/pypi/Pygments/2.21.0/json | `vulnerabilities: []` |
| https://pypi.org/pypi/pytest/9.1.1/json | `vulnerabilities: []` |
| https://pypi.org/pypi/ruff/0.16.10/json | `vulnerabilities: []` |
| https://pypi.org/pypi/typing_extensions/4.16.0/json | `vulnerabilities: []` |

The delegated gate sweep used `rg -n 'development-design' products/tracker17/docs/nfdr.md
products/tracker17/docs/adr/*.md`. Its matches identify QC-5, QC-8, QC-12, QC-20–QC-27,
QC-36, QC-40, QC-41, QC-46 and QC-60 in the NFDR and no ADR entry delegating another gate.
QC-5/QC-8/QC-20–QC-27/QC-36/QC-46's conditional production changes are absent from this design
under CP-292 (`change_spec.md:L98-L98`); QC-12/QC-40/QC-41 and the proposed-construct QC-60
review are recorded above. No delegated review touched by this delta is left unrecorded.

