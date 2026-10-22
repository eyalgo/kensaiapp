# Change Design — revalidate a confirmation on every history return

**Date:** 2026-10-20
**Category:** bug
**Behaviour:** changing
**Publishes text:** no

## 1. Change Summary

Serve an actual pending confirmation as HTTP 202, with the existing `Cache-Control: no-store`.
Remove successful moves' `Clear-Site-Data` header. Keep the existing page, address, workflow
check and focus rules. This blueprint owns that response-policy choice and its proof boundary;
requirements remain in the adjacent change_spec CP-343–CP-354.

Product paths below are relative to `products/tracker17/`. The blueprint's home follows
core/doctrine/setup/kensaiapp_structure.md § 2, the active Tobiishi's change arc.

### Response contract

| Response | Design decision |
|---|---|
| GET actually displaying a pending confirmation on the task's page or a project row | HTTP 202, unchanged HTML and address, with `Cache-Control: no-store` and the existing page policy. |
| GET at the same address after the saved status disallows the move | Existing HTTP 200 refusal, saved status, no confirming controls, status focus and description; keep no-store. |
| GET with only a back-out interaction, an outcome, an unknown interaction, a missing/foreign task or a higher-precedence outcome | Preserve the existing response status and page selection. Keep the existing no-store scope. |
| Ordinary or confirming move submission | Existing redirect, Location and save/refusal/failure handling; no `Clear-Site-Data` on success or failure. |
| All responses | No `Set-Cookie`; retain the existing Content-Security-Policy and all request checks. |

Select 202 from the **resolved presentation**, not merely the presence of `move_confirm` in
the query. Reuse `_move_view`'s saved-status check and outcome precedence. A confirmation
about another project's task does not render on this page and must not select 202. Do not
reproduce the workflow table or inspect HTML to decide the response status
(`web/routes.py:L328-L359`, `L435-L455`; `web/pages.py`, `project_page` and `task_page`).

**HTTP meaning — architect's choice.** Treat 202 as the response for the requested move intent
awaiting the person's confirmation. It reports no completed move, schedules nothing, creates no
pending server record, and changes no saved data. A GET still only displays the intent carried
by the address. This uses the noncommittal pending meaning of 202; the HTTP standard defines it
as accepted processing that is incomplete and may ultimately be disallowed
([RFC 9110 § 15.3.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-15.3.3)).
The interpretation is explicit because the GET's page representation is complete even though
the displayed move intent is not. Do not present this as a background job or a promise to move.

**Browser dependence.** Chromium's admission check excludes a main document whose response
status differs from 200
([Chromium eligibility check, `PopulateReasonsForMainDocument`](https://raw.githubusercontent.com/chromium/chromium/main/content/browser/back_forward_cache/back_forward_cache_impl.cc#L987-L991)).
No-store separately prevents reuse from the HTTP cache; Chrome can admit a no-store page to
its history cache, so the header alone is insufficient
([Chrome's no-store explanation](https://developer.chrome.com/docs/web-platform/bfcache-ccns)).
The design therefore prevents confirmation admission, rather than trying to invalidate it
later. That also covers a confirmation left open while another tab moves the task, then
cached only after that move: it cannot enter the history cache in the first place.

### Feasibility evidence and its limit

An isolated synthetic server and the installed pinned browser compared only response policies;
no product source changed and no product acceptance suite ran. The command
`/private/tmp/t17env/.venv/bin/python /private/tmp/tracker17-status-probe.py` returned:

```text
browser: 153.0.8010.12
confirmation status: 200 ordinary-page restore: True confirmation before: True after: True cookies: 0
confirmation status: 202 ordinary-page restore: True confirmation before: False after: False cookies: 0
```

The probe used script-free served pages, the product's page policy, no-store confirmations,
303 after a form submission, a fresh empty-cookie context, and the driver's full Chromium
channel with only its disable-history-cache default removed. Its test-owned pageshow recorder
observed the values above. This establishes the admission behavior, not saved-status refusal,
product focus or the complete browser case; § 5 requires those product proofs.

A separate synthetic comparison using the same pinned browser returned `after: True` for
no clearing header, `Clear-Site-Data: "cache"`, and `Clear-Site-Data: "cookies"` on the
303 (`/private/tmp/t17env/.venv/bin/python /private/tmp/tracker17-header-probe.py`, exit 0).
Do not use cookie clearing as a substitute. Apart from that failed probe, its host-scoped
deletion reaches beyond one loopback port
([Chromium cookie filter](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/content/browser/browsing_data/clear_site_data_utils.cc#76)).

## 2. Blast Radius

Placement follows `docs/SDD.md` § 3: `web` owns browser requests and responses; `domain` owns
which moves are allowed. The table accounts for the complete NFDR § 1.2 module set.

| Module | Status | What changes |
|---|---|---|
| `domain/` | Unchanged | Workflow rule, exports, data and entry docstring remain unchanged; no test module is added. |
| `application/` | Unchanged | Existing action and allowed-moves contracts. |
| `persistence/` | Unchanged | Existing saves and data format. |
| `web/` | Modified | Owning part: **web**. `routes.py` owns response-status selection for the resolved confirmation on both pages and removal of the successful-move clearing directive. Page builders, stylesheet, listener and public exports remain unchanged. |
| `main.py` | Unchanged | Existing composition. |
| `errors.py` | Unchanged | No new refusal or error type. |
| `tests/` | Modified | Existing `integration/test_routes.py`, `integration/test_move_routes.py`, `integration/test_move_pages.py` and `e2e/test_moves.py`. `e2e/conftest.py` only if identity checks need fixture support; its cache-enabled launch stays intact. |

No production signature or export changes: `Response`, `Site` and `listen` keep their surfaces
(`web/__init__.py:L7-L10`). The listener already forwards status and headers
(`web/listener.py:L43-L51`), so the `main` importer needs no edit. NFDR § 1.2's import graph
requires no new edge. The response-status **value** for pending confirmations intentionally
changes; its test expectations are retired explicitly in § 5.

One production module changes, without independent internal seams requiring a sub-job split.
This is a single delta, with no inter-module interface contract or atomic-landing edge.

## 4. Code Strategy

| Change | Hint |
|---|---|
| `web/routes.py` — response policy | Derive 202 from the resolved, actually rendered confirmation after outcome precedence, task membership and the saved workflow answer. Keep no-store as HTTP-cache protection; remove the clearing header and its obsolete eviction claims. The non-200 admission boundary is the browser-specific approach, not a new page action. |
| Integration tests — status and body contracts | Keep the shared `test_routes.page` helper strict at 200 by default; permit an explicitly supplied expected status for known confirmation cases. Update confirmation callers in `test_move_routes.py` and `test_move_pages.py`. Never replace exact expectations with a blanket successful-status range. |
| Browser tests — history and assertion review | Put the same-run positive pageshow witness on an ordinary 200 page. Await explicit true/false recorder observations as well as the expected DOM; missing instrumentation does not prove a fresh load. |
| Browser fixture, if needed | None |

## 5. Test Additions

Rows T1–T15 map the Examples in their stated order. Keep additions in existing files so the
workflow trace needs no new module entry (CP-352, CP-353).

| Row | Test file / check | What to add / modify |
|---|---|---|
| T1 | `tests/e2e/test_moves.py::test_real_history_traversal_revalidates_the_confirmation` | Task-page Back after this tab confirms: assert the confirmation address, saved cancelled status, no strip/sentence/confirm/back-out/move controls, status focus, viewport visibility and its saved-status description. Compare saved bytes before and after each traversal. |
| T2 | Same file, row variant | Cover the same case from the project's task row. Scope focus, description, status and controls to the acted-on task; keep both places. |
| T3 | Same history proof | Confirm, Back, Back again, then Forward to the confirmation address. On each return assert the address, refusal state, focus, description and unchanged bytes. Cover task page and row. |
| T4 | Same history proof, second-tab variants | Tab 2's ordinary moves end at done; Back in tab 1 shows the current refusal and unchanged bytes. Cover both places, another tab confirming to cancelled, Forward to the final-state address, and the edge where the confirmation is still active when tab 2 moves, then tab 1 leaves and returns (CP-343). |
| T5 | Same history proof | Before confirming, reload, Back and Forward each save nothing; reload/Forward focus the confirmation sentence when still allowed. The confirmation now reloads instead of restoring. Keep a same-run positive restore witness using an ordinary 200 page; do not remove the cache-availability proof (CP-344, CP-347). |
| T6 | `tests/integration/test_routes.py`, move response matrix | Cover both pages, both allowed starting statuses, final statuses, back-out, competing outcomes, malformed/unknown interaction and a task from another project. Assert exactly 202 only when a confirmation renders; otherwise the existing 200/404 and content/focus contract. Inspect HTML for script elements, handler attributes and script URLs, with the existing page policy and no cookie (CP-345). |
| T7 | `tests/integration/test_routes.py::test_only_successful_moves_evict_cached_confirmations` and T1–T4 | Retire the exact cache-clearing directive assertion and rename/restate the test as no site-data clearing on any move response. Retain ordinary/confirming success, opening, refusal, invalid/missing task and failed-save coverage, including redirect and no-Set-Cookie checks. T1–T4 prove the replacement mechanism (CP-346). |
| T8 | History proof / `tests/e2e/conftest.py` if needed | Assert browser 153.0.8010.12. Retain full Chromium and the existing removal of the driver's disable-cache default. No interception or other cache-disabling flags. An ordinary page must report persisted true in the same run; confirmations must report explicit false. |
| T9 | `pytest products/tracker17/tests/e2e/` from the instance worktree | Entire folder exits 0 on a supported machine, including the named history case; no skip, deselection or xfail (CP-348). This is an execution gate, not a new test. |
| T10 | Previous-change fence review | The commands and verdict below discharge CP-349; do not add a test duplicating a frozen Git comparison. |
| T11 | `tests/e2e/test_moves.py`, all assertions | Apply the findings below. Review each new assertion by its product-breaking counterexample and record any additional removal/repair with the clause it proved (CP-350). |
| T12 | Change-folder record review | The owed record below names the mechanism, retained header, removed header, purposes and browser dependence; no product record changes (CP-351). |
| T13 | Current-change file fence | Compare the product diff against this change's merge base, including uncommitted paths before the closing commit. Allow only the actual paths in § 2; require no diff in workflow, saving, dependencies, timed run or product docs (CP-352). |
| T14 | Existing route enumeration, architecture suite and quality gates | Retain every route's non-saving GET, redirect POST, same-site rejection, no cookie and page-policy checks. Keep `test_trace.py` unchanged. Product-root `ruff format --check .`, `ruff check .` and `mypy main.py errors.py domain application persistence web` each exit 0 (CP-353). |
| T15 | `pytest products/tracker17/tests/` from the instance worktree | Entire card suite exits 0. Only the named mechanism exceptions below and recorded CP-350 findings alter existing assertions (CP-354). |

**Rule-implied edges:** T6 covers outcome precedence, unrelated rows, terminal tasks and missing
targets without inventing a second workflow rule. T7 covers successful and failed saves on both
submission paths, plus malformed input, GET, back-out and rejected origins including same-site;
assert state/save count unchanged for non-saving paths. T1–T5 snapshot saved bytes separately
around each traversal. No test forces a post-Back reload to manufacture revalidation. The
out-of-scope case where another tab leaves the move still allowed acquires no new experience
rule; existing confirming revalidation stays in place.

### Existing assertions retired, replaced or strengthened

The review covers every assertion and helper in `tests/e2e/test_moves.py` at this handoff.
It is a source counterexample review, not a mutation-test or product-browser pass.

- Remove `locator_box`'s `assert box is not None` (`L250-L258`). Its script returns an object
  literal whenever evaluation completes; an absent locator fails before that assertion.
  Keep callers' coordinate, height, width and pointer-target assertions.
- Replace the history test's confirmation-specific positive restore assertion (`L416`) with
  T5/T8's ordinary-page positive witness. Preserve the reload/Forward confirmation, focus
  and saved-byte assertions surrounding it. The proof remains non-vacuous with caching on.
- Strengthen `window.__restored is not True` (`L424`, `L448`) to an awaited explicit false
  observation. Those checks reject true but also accept missing instrumentation; T1/T4
  keep the fresh-load clause without accepting absence.
- Retain the remaining assertions. A broken focus/text/description/visibility, missing or
  extra control, wrong geometry, reachable sentence, wrong click target, extra save or
  incorrect stored status defeats the corresponding check. The geometry and status checks
  depend on rendered or saved product values, unlike the object-literal non-null assertion
  (`tests/e2e/test_moves.py:L28-L475`).

Two integration contracts change under CP-354's mechanism exception:

1. `test_move_interaction_and_outcome_pages_are_not_stored`'s unconditional status 200 at
   `tests/integration/test_routes.py:L885` becomes the explicit T6 status matrix. Keep its
   exact no-store, policy and no-cookie checks. Confirmation callers of `test_routes.page`
   opt into expected 202; every other caller keeps the exact 200 default and all body checks.
2. `test_only_successful_moves_evict_cached_confirmations`'s `"cache"` expectation at
   `tests/integration/test_routes.py:L901` becomes absence of Clear-Site-Data (T7).
   Keep the negative save/outcome matrix and no-cookie checks.

No spec line is set aside: CP-347 requires a restored page within the run, not a restored
confirmation; Locked Answers Gap 4 expressly permits moving that witness.

### Previous-change fence verdict

Ran `git -C <instance-worktree> diff --name-only e97b021f0 e0b0f245d -- products/tracker17`:
its twelve paths are exactly the CP-349 allowance. Ran
`git -C <instance-worktree> diff e97b021f0 e0b0f245d -- products/tracker17/domain/workflow.py`:
the only hunk, `@@ -7,14 +7,18 @@`, is inside the opening docstring. The allow-list comparison
printed `Previous-change file fence: PASS; no paths outside CP-349 list`; an AST-delimited
body comparison printed `Workflow body comparison: PASS; bytes after opening docstring match`.
Verdict: the previous change respects its fence; undo nothing.

## Records this change makes false

None — read `docs/adr/README.md`, ADR-0001–ADR-0009, `docs/nfdr.md`, `docs/fdr.md` and
`docs/SDD.md` § 3; no part, import permission, accepted decision or behavioural rule becomes
false. Response-status choice is an added mechanism, not a reversal of the no-script decision.

**Record owed — CP-351:** the CTO's SDD § 4 runtime conditions or a Principal Architect ADR
must name 202 on actually rendered pending confirmations as the chosen history-admission
boundary; name `Cache-Control: no-store` on move interaction/outcome pages as HTTP-cache
protection. State why both are needed, the pending-intent meaning, no script/cookie/session,
revalidation through the existing saved-status GET path, and service of RT-7, EX-6 and CP-343.
Record removal of Clear-Site-Data, the Chromium dependence and the product proof's measured
outcome. The handoff's record search for `no-store|Clear-Site-Data|Cache-Control` under product
`docs/` returned no matches. Write no product record in this change.

## Architect Review Notes

- **Mechanism choice (b), CP-346/QC-12:** select 202 only for an actual pending confirmation.
  The HTTP interpretation, vendor admission rule and synthetic pinned-browser result are
  stated in § 1. Remove cache clearing: the request rejects it as the mechanism and no other
  requirement pays for it. Cookie clearing is rejected by the measured comparison and its
  wider deletion scope. Add no script, cookie, session, endpoint, browser flag or auto-refresh.
- **Realize CP-343 by construction (b):** prevent every rendered confirmation from entering
  history cache, including one active during another tab's save. Every return then uses
  no-store plus the existing GET revalidation. Select the response from the resolved view,
  preserving outcome precedence and task membership; a query flag alone is insufficient.
  Product T1–T8 must prove the entire contract; the synthetic probe proves only admission.
- **QC-8, QC-23 and QC-27 — pass:** only request-local status/header choices change. No rule,
  stored outcome, page script or inner-part dependency is added. `Site` retains its tracker,
  host and lock (`web/routes.py:L202-L232`); response forwarding already exists
  (`web/listener.py:L43-L51`). No cookie is set, retained or cleared by this design.
- **QC-12 — pass:** the response choice serves CP-343 without an extra production part.
  The one browser-specific boundary is explicit and pinned proof is mandatory; a header's
  presence cannot substitute for the history test. Preserve CP-348's failing-case rule.
- **Delegated-gate sweep:** checked every development-design tail in NFDR and ADRs. QC-5 and
  QC-36 acquire no new refusal mapping or escaping: page builders remain unchanged. The
  unchanged domain/action/persistence/composition/save-contract/saved-field parts introduce
  no new QC-20/21/22/24/25/26/46 obligation. QC-41 passes: no secret is added. QC-60 passes
  on the proposed delta: the existing Python 3.11 HTTPStatus and Playwright seams suffice.
- **QC-40 — browser exception applies:** the lock keeps `playwright==1.63.0`
  (`tests/requirements.txt:L12`); the synthetic run reports Chromium 153.0.8010.12.
  Google's September 15 update lists critical fixes in .47/.48
  ([vendor release](https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0541751186.html)).
  NFDR RN-33's exception for .12 runs through 2026-11-07 and covers this review date.
  This design moves no dependency pin, grants no exception and claims no clean advisory scan.
- **Language resolution:** Python — step 1, the project card's Languages field; opened
  `core/doctrine/engineering/languages/python/README.md` and its seven destinations.
  Product NFDR QC-39/QC-59/QC-60/QC-62 retain the product's floor, pins and gates.
- **Published words:** the spec's Out of Scope entry leaves refusal wording alone. No label,
  message or prose is added to a product surface; Publishes text is no.
- **Cold-read:** every module, changed response path, Example and rule-implied edge has a
  placement or proof row. Named old assertions have replacements; no public production
  signature, import edge, cross-repository write or spec reading is left implicit.
