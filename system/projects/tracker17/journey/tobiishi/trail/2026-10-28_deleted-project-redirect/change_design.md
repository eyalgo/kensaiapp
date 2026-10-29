# Change Design — deleted-project submissions redirect; confirmation counts come from the application

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing
**Publishes text:** no
**Inputs:** `change_spec.md` and `change_request.md` in `tracker17 · tobiishi · 2026-10-28_deleted-project-redirect`.
**Language resolution:** Python — `system/projects/tracker17/project.md`, `Languages:`; opened `<CORE>/doctrine/engineering/languages/python/README.md` and its seven concern destinations. Product decisions govern the Python 3.11 floor and the QC-62 tools, per `products/tracker17/docs/adr/0002-standard-library-only-no-web-framework.md` § Decision and `products/tracker17/docs/nfdr.md` QC-60/QC-62.

This document owns the structural delta and its test mapping. Rules and scope remain in the two inputs above.
Product paths below are relative to `products/tracker17/`, unless they begin with `products/` or `system/`.

---

## 1. Change Summary

Change only the browser part's production code: Add task and Rename redirect when a readable project
identity is missing, both at the initial lookup and when the action raises `ProjectNotFound`.
Make the project-page renderer require the whole-project task count supplied by its caller.
These are the response and count changes requested by `change_spec.md` § Rules, CP-594–CP-601.
No new wording is published: the landing page and confirmation sentences remain those required by
`change_spec.md` CP-599/CP-600 and § Out of Scope, “The wording of every page and line.”

---

## 2. Blast Radius

Placement follows `products/tracker17/docs/SDD.md:204-214`, § 3 “The parts”: `web` owns addresses,
reading form fields and page building; `application` answers what a page needs; `domain` owns the
computations. The existing count is already supplied on `ProjectTaskList.task_count`
(`products/tracker17/application/tracker.py:78-106`, `:354-391`, `_read_list`).

| Module | Status | What changes |
|---|---|---|
| `domain/` | Unchanged | No new entity rule, count computation, refusal type or feature-entry module. |
| `application/` | Unchanged | Keep the existing project lookup, actions, typed refusals and listing result. |
| `persistence/` | Unchanged | No format, save, load or locking change. |
| `web/` | Modified | **Owning part: web.** `routes.py`: distinguish an unreadable route number from a readable identity with no project; redirect the latter, and each action's `ProjectNotFound`, through the existing redirect builder. Pass the listing's whole-project count to the page. `pages.py`: make the count an explicit required input and remove row counting. |
| `main.py` | Unchanged | No wiring or exported `Site` constructor change. |
| `errors.py` | Unchanged | No new error or hierarchy change. |
| `tests/` | Modified | Extend existing route and page test modules; supply the required count in direct renderer callers named in T7. No new test module. |

The permitted import direction remains `web → application`, with no inward import of `web`
(`products/tracker17/docs/nfdr.md:175-197`, § 1.2 QC-13–QC-19).
No production caller outside `web` needs the changed renderer signature: the call-site search
`rg -n 'project_page\(' products/tracker17 --glob '*.py'` found the production renderer call in
`web/routes.py:636` and the direct test callers listed in T7.
The public `Site`/`Response` surface stays unchanged; there is no transitive production change.

**Response boundary.** Keep the current request checks before either action. Read the numeric
identity through `Site._identity`, independently of whether a project is found.
For an unreadable number, preserve the direct not-found answer.
For a readable identity, construct the bare project address from the parsed integer, without
carrying query values, and use `Site._redirect` for both missing-project exits.
Perform the missing-project check before interpreting form values, and catch `ProjectNotFound`
by type before form-refusal handling. These choices realize CP-594–CP-598 explicitly; the current
parser, lookup and shared redirect seam are at `products/tracker17/web/routes.py:402-411`,
`:860-915` and `:1312-1314` (`_identity`, `_project_named_by`, `_rename_project`, `_add_task`, `_redirect`).

**Renderer contract.** Add a required keyword-only integer input named `task_count` to
`pages.project_page`. It is the whole-project count answered by the application, irrespective of
the supplied rows or optional listing. Keep the existing rows, assignees and optional listing
inputs for their present rendering responsibilities. `Site._project_page` supplies
`listing.task_count` from the same listing it already reads, without another application call.
The renderer passes that input to the deletion section without deriving, defaulting or replacing
it from rows. This removes the fallback at `products/tracker17/web/pages.py:2037-2039` while
retaining the existing application/page seam at `products/tracker17/web/routes.py:614-656`.

Only `web` is affected in production, so there is one delta and no § 3 sub-job split.
The renderer signature and its route/test callers must land together: there is no green point
with the required input missing from a caller. There is no ordering dependency between the
redirect correction and the count correction.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| Single `web/` delta — redirects and explicit count input | Use the existing identity parser to distinguish unreadable digits from a missing entity before constructing a canonical address. Both initial absence and the action's typed absence use the shared `_redirect`/`_address` seam with no flags or query. The explicit count input needs no algorithm. |

---

## 5. Test Additions

Tests belong in existing modules. Each row names the contract it proves; the three old direct-404
assertions named by `change_spec.md` § Locked Answers, “Gap 6”, are replaced only as detailed below.

| Row / delta | Test file | What to add / modify |
|---|---|---|
| T1 — deleted-project submissions | `tests/integration/test_delete_project_routes.py` | Update `test_deleted_project_submission_changes_nothing`: its `add-task` and `rename` cases must each assert 303 and exact bare `Location: /projects/1` after deletion through confirmation. Snapshot saved bytes, save calls, projects and tasks **after deletion, before the stale submission**, and assert equality afterwards, including the surviving project's data. These two cases are CP-602's regression tests and must each fail against the pre-change implementation. Keep the other deletion cases' assertions. CP-594–CP-596, CP-602. |
| T2 — never-held identities and invalid fields | `tests/integration/test_task_routes.py`, `tests/integration/test_rename_routes.py` | Split the readable and unreadable cases of `test_a_missing_project_post_gets_project_not_found_and_saves_nothing` and `test_a_missing_rename_project_answers_404_without_saving`. Readable cases cover 99, 0, 00 and 00099 for both submissions. Exercise all CP-597 form refusals against a deleted project as well as never-held identities: the in-use Rename name, blank/overlong names and titles, invalid priority, unlisted assignee and invalid date. Assert 303, the exact canonical location with no query, unchanged saved bytes/state and no save. Retain the 5,000-digit case's original direct-404, no-Location and unchanged-data assertions. CP-594/CP-595, CP-597/CP-598 and § Out of Scope. |
| T3 — missing only when the action runs | `tests/integration/test_task_routes.py`, `tests/integration/test_rename_routes.py` | Inject a tracker collaborator into the real `Site` that permits the project lookup but reports the existing `ProjectNotFound` type at the selected action. Exercise both submissions with valid and invalid form values. Assert 303, the bare canonical project location with no refusal/failure/typed values, no save and no action-side state mutation. Do not simulate concurrent requests by changing the production lock or patching product globals. CP-596/CP-597. |
| T4 — the redirect landing | `tests/integration/test_delete_project_routes.py` | Follow T1's locations and assert the existing project not-found page, 404 and no `Cache-Control`. Keep `test_project_delete_response_policy_matches_rendered_state` and `test_deleted_child_submission_changes_nothing` unchanged as regression checks for the not-found policy and deleted-task submissions. CP-599 and § Out of Scope. |
| T5 — application count through the real page | `tests/integration/test_delete_project_pages.py` | Extend `test_project_confirmation_counts_all_current_tasks`: explicitly read the application's count, assert the filtered page shows fewer rows, and assert the confirmation uses that count. Cover four tasks, one per status, with `filter_status=done`, plus zero matching rows, unfiltered, sorted, refused-filter and refused-sort views. Keep zero/one/many sentence assertions and unchanged wording. CP-600/CP-603. |
| T6 — renderer count without a listing | `tests/integration/test_delete_project_pages.py` | Add a direct renderer test with an application-supplied whole-project count and no listing, with confirmation open. Assert the exact sentence uses the supplied count. Include zero with empty rows, and one/many counts with fewer rows than the project holds. This proves the modified signature's count contract independently of the route's already-supplied listing and fails if counting rows is restored. CP-600/CP-601. |
| T7 — renderer callers retain their assertions | `tests/integration/test_pages.py`, `tests/integration/test_task_pages.py`, `tests/integration/test_move_pages.py`, `tests/integration/test_rename_pages.py`, `tests/integration/test_summary_pages.py` | Supply the required count at every direct `pages.project_page` call, using the application's answer for worlds with a tracker and the fixture's explicit whole-project count for page-only fixtures. Keep every existing page, focus, escaping, move, rename and navigation assertion. No assertion is retired by this signature change. |
| T8 — every submission shares the redirect builder | `tests/integration/test_routes.py` | Retain `test_every_route_leaves_state_and_headers_as_the_rules_say`, including its state and cookie checks; T1–T3 cover the newly changed exits while this test checks the route set. CP-605; NFDR QC-7/QC-8. |
| T9 — no row-count fallback | Source check, no new test module | Run `git grep -n 'len(rows)' -- products/tracker17/web/pages.py` from the change worktree and inspect any match: none may lie inside `project_page`. T5/T6 prove the count behaviour; this check proves CP-601's structural clause. |
| T10 — requirement pointers | `tests/architecture/test_trace.py` | Keep the pointer suite green. Update touched test docstrings with their SRS requirements/acceptance criteria and CP identifiers. No new module is planned; if one becomes necessary, CP-607 also requires adding its pointer to `domain/projects.py`'s opening docstring. |
| T11 — required suites | Existing suites | From the change worktree, both `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` must exit 0. CP-604. |
| T12 — product quality gates | Existing tools | From `products/tracker17/`, `ruff format --check .`, `ruff check .`, and `mypy main.py errors.py domain application persistence web` must each exit 0 using the product's pinned tools. CP-606; NFDR QC-62. |

**Example coverage, in table order from `change_spec.md` § Examples:** 1 → T1 Add task;
2 → T1 Rename; 3 → T4; 4 → T3; 5–8 → T2; 9–11 → T5 (also T6 for sentence forms);
12 → T9; 13 → T11; 14 → T8; 15 → T12; 16 → T10.
CP-608's reviews are recorded below.

**Rule-implied edges:** CP-594/CP-595's no-save and any-form clauses → T1–T3;
CP-596's two absence points → T1/T2 and T3;
CP-597's missing-target precedence and absence of carried form values → T2/T3;
CP-598's zero and canonical decimal identities → T2;
CP-599's following read and cache policy → T4;
CP-600's unfiltered, filtered, sorted, no-match, refused, empty and singular/plural states → T5/T6;
CP-601's no-listing path and absence of the fallback → T6/T9.
The remaining rules map directly to T1, T5 and T8–T12.

**Assertions retired:** only the readable-identity Add task/Rename direct-404 assertions in T1/T2,
which the spec expressly releases in § Locked Answers, “Gap 6”. Their no-save clauses remain in
T1/T2; the not-found page and its cache policy remain proved in T4.
The unreadable-identity direct-404 assertions remain in T2.

---

## Records this change makes false

None — read `products/tracker17/docs/adr/README.md` and ADR-0001–ADR-0012 (ADR-0006/ADR-0010
are superseded), `products/tracker17/docs/nfdr.md` § 1.1–§ 1.4 and its delegated review clauses,
`products/tracker17/docs/fdr.md` § Rules, and `products/tracker17/docs/SDD.md` § 3 and § 4 RT-11.
The delta realizes the address and count boundaries already stated in SDD § 3/RT-11,
NFDR QC-7/QC-23, FDR R-105 and ADR-0011/ADR-0012; it adds no part, import edge or saving contract.
The unreadable-number gap against QC-7/ADR-0011 remains outside scope, as already collected in
`deferred_decisions.md` § “A submission naming a number too long to read as an identity is answered
by a redirect”; this design adds no conflicting reading or new deferral.

---

## Architect Review Notes

Decisions below are the architect's, 2026-10-28.

- **Canonical address by construction (kind b):** distinguish failed numeric parsing from a missing
  project, and derive every readable-identity redirect from the parsed integer. Reusing the raw
  digits would violate CP-598 for `00`; treating all failed lookups alike would change the
  unreadable-number contract which § Out of Scope preserves. Both action-level typed refusals use
  the same bare-address path, so CP-596 does not depend on the initial lookup catching absence.
- **Count dependency is explicit (kind b):** choose a required keyword-only count rather than
  making a listing mandatory or keeping a numeric default. Existing direct callers deliberately
  render plain rows with no listing (`tests/integration/test_task_pages.py:248-268`,
  `tests/integration/test_move_pages.py:328`, `project_html`); the existing listing parameter is
  optional (`products/tracker17/web/pages.py:1941-1956`, `project_page`). The explicit count retains
  that rendering seam while removing every route to inferring the count from rows. It requires
  caller updates but no new application capability. T6 proves the no-listing case.
- **Action-time absence without concurrency changes:** ADR-0005 § Decision serializes actions.
  CP-596 still requires handling the action's typed absence; T3 exercises that boundary with an
  injected collaborator, without introducing a new concurrent execution model.

### Delegated record reviews

The sweep `rg -n 'development-design' products/tracker17/docs/nfdr.md products/tracker17/docs/adr/`
identified the following applicable gates and the conditional gates listed afterwards.

| Gate | Verdict and reason |
|---|---|
| QC-5 — refusal handling by type | Pass for this design: retain the existing `ProjectNotFound` catches and form-refusal types; no message inspection or new refusal type (`web/routes.py:874-883`, `:907-915`). |
| QC-8 — nothing retained between requests | Pass: all new identity/address/count values are request or render inputs. No cookie, session or new retained field. The baseline request-local seams are `web/routes.py:614-656`, `:860-915`. |
| QC-12 — every added part paid for | Pass: no new production part or test module. Both changes fit the existing `web` part in SDD § 3 and CP-594–CP-601. |
| QC-23 — web owns no rule, including no count | Pass: web selects addresses from lookup/action outcomes and displays a supplied count; it neither counts rows nor adds a domain refusal rule. The count remains the existing `application/tracker.py:354-391` answer. |
| QC-27 — browser interface remains replaceable | Pass: all production edits remain in `web`; `application`/`domain` contracts and wiring are unchanged. This follows the existing import boundary in NFDR § 1.2 QC-14/QC-16. |
| QC-36 — one escaping function | Pass: retain the existing `_project_delete_section` → `project_delete_sentence`/`confirm_strip` rendering path (`web/pages.py:928-955`). Only the source of the numeric argument changes; no new text interpolation or escaping path. |
| QC-41 — no secret | Pass: the new inputs are a numeric project identity and count. No credential, account, secret read or saved field is introduced. |
| QC-60 — Python floor | Pass for the design's constructs: ordinary keyword-only arguments, integers and existing typed exception handling add no language/library feature beyond the product's Python 3.11 baseline (ADR-0002 § Decision). No interpreter compatibility run is claimed. |
| QC-40 — dependency/browser advisory review | Pass for this review date under the existing browser exception; evidence follows. No dependency or browser pin changes. |

**QC-40 evidence, checked 2026-10-28:** POST `https://api.osv.dev/v1/querybatch` with the 15 exact
package/version pairs in `products/tracker17/tests/requirements.txt` returned
`{"results":[{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}]}`: no matching advisory was returned for
those pins. This is the query result, not a claim that the database contains every advisory.
The installed cached Chromium's `CFBundleShortVersionString`, read with
`/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' '<the Playwright cache>/chromium-1243/chrome-mac-arm64/Google Chrome for Testing.app/Contents/Info.plist'`,
printed `153.0.8010.12`.
Google's [September 8 security release](https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0808145027.html)
lists critical fixes in the later 153.0.8010.36/.37 builds; the browser is not judged current.
`products/tracker17/docs/nfdr.md:1049-1058`, RN-33, explicitly permits this exact build through
2026-11-07, so it does not block the 2026-10-28 design review. No new exception is created.

**Conditional gates not triggered:** QC-20 (domain wording), QC-21 (application rules),
QC-22/QC-25 (persistence), QC-24 (composition), QC-26 (saving contract) and QC-46 (saved fields):
the blast radius changes none of those parts or contracts. The dependency-selection half of
QC-40 is likewise not triggered; its every-review half is recorded above.

**Cold-read result:** the single-module boundary, parsed-identity response contract, explicit count
input, caller coupling, example/rule coverage, retired assertions, record disposition and text
verdict have been checked against this design. No write into another repository is planned.
