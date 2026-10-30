# Change Design — serve the unreadable-data page without reaching the saved data

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the unreadable-data page, the console line on an unreadable start, and the README passages on starting again and setting saved data aside

---

## 1. Change Summary

This document owns the structure, contracts and test placement for the unreadable-data start in
`tracker17 · tobiishi · 2026-10-30_unreadable-data-page`; its `change_spec.md` owns CP-710–CP-735.
The output belongs beside that spec under `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2,
“the active Tobiishi”, which names `change_design.md` in the change arc.

Use two request handlers behind the existing listener: the normal `Site`, and an `UnreadableSite`
with only the displayed location and its bound host. The latter receives no application object,
saver or saved-data reader. This is the architect's structural decision, 2026-10-30, to realize
CP-733 and the no-write contract CP-725 by construction. `main` selects the handler after the
single load and announces only after binding succeeds. Both modes use the existing stop lifetime.
The current load-and-exit branch and successful lifetime are in `products/tracker17/main.py:118-152`,
`_serve_claimed`; the ownership boundary is `products/tracker17/docs/SDD.md:214-240`, § 3.

All product paths below are relative to `products/tracker17/` unless prefixed with `products/` or
`<CORE>`. The request and spec refer to the change named above, independent of its journey position.

---

## 2. Blast Radius

Place logic by `docs/SDD.md:212-217`, § 3 “The parts”, and preserve the import graph in
`docs/nfdr.md:166-197`, § 1.2 “Forbidden imports”.

| Module | Status | What changes |
|---|---|---|
| `domain/` | Unchanged | No entity, constructor, data rule or feature entry point changes. |
| `application/` | Unchanged | No empty tracker, saver contract or action is added for unreadable mode. |
| `persistence/` | Unchanged | Keep `UnreadableData`, `SavedData.load`, and the existing location claim and rollback. |
| `web/` | Modified | Owning part: `web`. `pages.py` builds the one page and escapes its location; `routes.py` owns the unreadable handler, request checks, response policy, stylesheet exception and POST redirect; `listener.py` binds either handler and retains transport/stop behavior; `__init__.py` re-exports the added entry points. |
| `main.py` | Modified | Owning part: `main`. Choose the unreadable listener on the typed signal, pass the absolute location as text, bind before announcing, write the alternate stdout line, and retain claim/stop lifetimes. |
| `errors.py` | Unchanged | Reuse existing typed errors; add no exception. |

The new public surface is additive in `web`; `main` is its only affected production caller.
The inner parts have no allowed import of `web` or `main`, per `docs/nfdr.md:173-195`, QC-13–QC-18.
Keep the normal `listen(address, tracker)`, `Site(tracker, own_host)`, `Response`, `Listener`, and
`AddressTaken` contracts intact; their current exports are `web/__init__.py:6-9`, “browser-facing part”.
Thus no transitive production caller outside the table needs a change.

Other affected surfaces are `README.md` § “Starting the tracker again” and § “Setting saved data
aside”, plus the test modules in § 5. They implement CP-732 and CP-734. No write into another
repository is part of this design.

---

## 3. Sub-jobs

### Sub-job A — `web/`

**Scope:** page rendering, an unreadable request handler, and an additive listener entry point.
All three stay inside the browser-interface part; no new top-level part is introduced.

**Exposes:**

- `pages.unreadable_data_page(location)` takes the already absolute location as text and returns a
  whole HTML document as text. Use the title, heading and body fixed by CP-716. It uses the existing
  escaping boundary for the location, the existing stylesheet, and the product-name-only frame.
  There is one `h1`, no navigation or data control, and no policy tag (CP-716, CP-717, CP-723).
- `UnreadableSite(location, own_host)` exposes the same `handle(method, target, headers, body)`
  call and `Response` result as `Site.handle`. Its immutable startup configuration is not a
  request/session store. It accepts no tracker and performs no saved-data read or write (CP-724, CP-725,
  CP-733). Export it from `web` for the in-process tests.
- `listen_unreadable(address, location)` returns the same `Listener` as `listen`, after binding to
  the address and attaching an `UnreadableSite` configured with the actual bound host and port.
  Its `AddressTaken` signal and propagation of every other bind error are identical to `listen`.
  Export it from `web`; `main` supplies the absolute text location (CP-714, CP-733).
- Leave the normal `listen` and `Site` entry points and route enumeration unchanged. The new
  fallback is not appended to the finite normal `ROUTES` table (CP-727).

**Unreadable response contract, in precedence order:**

| Order | Condition | Result |
|---|---|---|
| 1 | Wrong or missing Host; `cross-site` or `same-site` mark; any POST without `same-origin` | Empty 403, using the existing response-policy helper. No location reaches it (CP-721). |
| 2 | Checked POST, any path/query/body, including `/style.css` and an unknown path | Empty 303 with `Location: /`, built through the existing address builder. Do not decode the form or dispatch any action (CP-720). |
| 3 | Checked GET whose path is `/style.css` | Existing stylesheet response, 200 and `text/css; charset=utf-8` (CP-719). |
| 4 | Every other checked request among GET, HEAD, PUT, DELETE, PATCH, OPTIONS | 503, `text/html; charset=utf-8`, `Cache-Control: no-store`, and the same UTF-8 page bytes independent of target/query/body (CP-718). |

Every row carries `PAGE_POLICY` as a response header, including `frame-ancestors 'none'`, and sets
no cookie (CP-722; `docs/nfdr.md:84-92`, QC-8). HEAD follows the existing listener convention: its
handler supplies the representation and headers; transport writes no body. Even HEAD on
`/style.css` takes row 4. The stylesheet address comparison ignores its query, as normal routing
does today (`web/routes.py:312-321`, `Site.handle`). Unknown listener methods and malformed messages
keep the listener's empty error answers, outside CP-718's method domain and the spec's scope.

Share request-check and response-policy machinery with the normal path without widening that
path's checks: normal `Site` still decides whether a route is a submission before applying its
submission check. In particular its unknown-POST response must not change. That order is the
existing contract at `web/routes.py:312-321`, `Site.handle`; the unreadable handler classifies every
POST before any route lookup, as CP-720 and CP-721 require.

**Depends on:** none. In-process and listener tests can supply a location without starting `main`.

### Sub-job B — `main.py`

**Scope:** select and announce the unreadable start, and place the approved console text.

**Exposes:** the existing `start(address, location)` entry point and return contract, with CP-710's
new successful lifetime. Claim first, call `SavedData.load` once, and choose normal mode only for
a readable result or no saved data. On `UnreadableData`, pass the same absolute displayed location
to `listen_unreadable` and to the console announcement. Do not create `Tracker`, `empty_state`, a
saver-backed application, or a second data-reading path in that branch (CP-710, CP-724, CP-733).

Binding in either mode precedes `claim.mark_started` and any stdout announcement. Proven location
contention keeps the existing refusal first. An occupied address gets only the existing stderr
address line and exit 1; any unrelated bind error propagates unchanged. An indeterminate claim goes
on to the chosen mode without a refusal (CP-713–CP-715). No exception message enters the announcement.

Use the bound listener's host/port for the URL, including when tests pass port zero. For unreadable
mode the announcement is exactly one flushed stdout line, with empty stderr, as CP-711 specifies.
Use `serve_until_stopped` with `SigintStopRequests`, retain the claim until after listener close,
and return 0 on Ctrl-C without further output (CP-712). The existing lifecycle is
`main.py:80-97`, `serve_until_stopped`, and `main.py:110-152`, `start` / `_serve_claimed`.

**Depends on:** A's `listen_unreadable` and its existing `Listener`/`AddressTaken` contracts.

### Sub-job C — `README.md`

**Scope:** place the approved text in the two CP-734 passages, preserving their heading names,
the set-aside commands and both conditions of the duplicate-conclusion passage. Keep the
second-tracker explanation. The words must describe the resulting start behavior and make the
referent of “the same commands” immediate. No other README passage or definition document changes.

**Exposes:** the unchanged `Setting saved data aside` heading referred to by the page and console,
and the operator's existing set-aside procedure (CP-716, CP-726, CP-734).

**Depends on:** none for its content contract; CP-734 defines the result independently of code.

**Build sequence:** A and C have no ordering dependency. B follows A's additive listener contract.
The real-start and browser checks require A + B; the set-aside/readme checks require B + C.

**Atomic-landing edge:** B + the CP-732 start-test rewrites — no green point exists between them:
the old assertions require exit 1 on a free unreadable start, while the new successful lifetime
serves until stopped. The conflicting assertions are in `tests/integration/test_start.py:57-93`,
“unreadable start”, `test_single_tracker.py:485-521`, “indeterminate acquisition”, and
`test_start_stop.py:533-565`, “refused start”. Retain their data-preservation clauses as § 5 states.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — `web/` | Two handlers with the same request/response boundary; share binding, security checks and policy construction. Build the unreadable frame without the normal navigation. Route unreadable POST before parsing fields; use `pages._escape` for the location. Keep the unreadable handler independent of the application, so mutating requests have no path to a saver. |
| B — `main.py` | None |
| C — `README.md` | None |

---

## 5. Test Additions

Every row below describes the required change to proof, not a claim that the tests have run.
The source contract is `change_spec.md` in `tracker17 · tobiishi · 2026-10-30_unreadable-data-page`,
§ Rules and § Examples. New test modules name the SRS requirements/acceptance criteria they check;
tests use collaborators or external-process observations rather than patching a product name
(CP-733; `docs/SDD.md:593-610`, TS-1–TS-4).

For every real unreadable start, observe bounded startup readiness and process exit: a child that
exits before announcing or fails to answer fails promptly, and cleanup always reaps it. Do not
call the newly serving `main.start` synchronously in an old exit test. The current direct calls
and held-address helpers are `tests/integration/test_start.py:57-93,471-491`, “unreadable start”.
Use test-owned paths/ports and a non-root identity for the permission-denial case, retaining that
case's existing root skip (`test_start.py:814-833`, “directory without read permission”).

| Row / sub-job | Test file | What to add / modify |
|---|---|---|
| T1 / A | `tests/integration/test_unreadable_pages.py` (new) | Build the page from an absolute location: exact CP-716 title, sole h1 and body, product name as plain text, one stylesheet, no `a`, `form`, `button`, `input`, `select`, `textarea`, `nav`, script or policy meta tag. Check `<`, `&`, `"` render as literal text, never markup, and no Python error appears. CP-716, CP-717, CP-723; Examples 2, 7. |
| T2 / A | `tests/integration/test_unreadable_routes.py` (new) | In-process handler: enumerate all CP-718 methods across `/`, `/people`, a missing address, real action paths, and varied queries/body bytes. Non-POST answers have identical page bytes, 503, HTML type and `no-store`; request values never appear. HEAD has the same representation headers, with its transport omission proved by T5. CP-718; Examples 2, 3. |
| T3 / A | Same as T2 | GET `/style.css`, including a query, yields the existing CSS bytes, type and 200. HEAD on that address follows the 503/HEAD contract; checked POST there and to known/unknown addresses returns empty 303 to `/` regardless of malformed or non-text form content. Following the redirect gets the page. CP-719, CP-720; Examples 4, 5. |
| T4 / A | Same as T2 | Each method with wrong/missing Host or `cross-site`/`same-site` yields empty 403 with no location; every POST with missing mark, `none`, or any mark other than `same-origin` is empty 403 even on unknown paths or `/style.css`. Allowed non-POST with no mark, `none` or `same-origin` opens its appropriate response. Assert policy with frame protection and no cookie for 403, 303, 503 and CSS. CP-721, CP-722; Example 6. |
| T5 / A | `tests/integration/test_listener.py` | Exercise `listen_unreadable` on a real ephemeral port: actual bound Host works; wrong Host refuses; every supported method follows T2–T4; HEAD writes no bytes and has the unreadable-page representation length, including HEAD `/style.css` as 503 rather than CSS. Requests write nothing to either stream. Unknown methods and malformed requests, including bad Content-Length, retain empty error bodies with policy and no Python text. Two listeners with distinct locations/ports do not share configuration. CP-718, CP-722, CP-727; Example 3 and listener-scope boundary. |
| T6 / B | `tests/integration/test_start.py` | Rewrite the first four unreadable-start tests and the closing-sentence/README-heading test named in CP-732: real start on truncated data stays alive; exact approved one-line stdout names absolute location, bound URL, unchanged data and the fixed heading; stderr empty. Root, `/people`, `/nothing?x=1` return the same 503 page with no controls; requests add no console output. Retain bytes, listing and no-traceback assertions. CP-710, CP-711, CP-729; Examples 1, 2. |
| T7 / B | Same as T6 | Seven independently collected start-level DR-6 cases: truncated read; unknown status; unknown priority; missing project for a task; duplicate project name; reused task identity; overlong saved field. Each must reach a real 503 page, leave the file byte-identical and preserve the full directory listing through stop. Every case fails promptly on the earlier exit-1 tree. CP-728; Example 16. |
| T8 / B | Same as T6 | Rewrite all other CP-732 data-rule cases: empty/non-UTF8/missing-key/wrong-shape files, invalid assignees, saved task-rule and label failures, invalid operator names, and invalid comment text/authors. Replace the held-address `_unreadable_start`/`_unreadable_comment` shortcut with free-port serving checks. Keep every prior invalid-value fixture, preservation assertion, persistence-signal check and heading check. CP-710, CP-732; Examples 12, 16 and FDR R-22 edges. |
| T9 / B | Same as T6 | A location that is itself a file, and an unreadable directory, each serve the page. Snapshot bytes/listing before restricting permissions, stop before restoring them for comparison, and assert unchanged data and no refusal line. CP-710, CP-725; Example 12. |
| T10 / A + B | `tests/integration/test_start_stop.py` | Add unreadable-mode real-process coverage at announcement, idle serving and close/return boundaries using the existing external signal-observation approach: Ctrl-C, separately delivered repeated Ctrl-C and quiet return 0, empty additional output, identical saved paths/bytes, then a fresh start on the released location/port. Keep normal-mode lifecycle tests. CP-712, CP-725; Example 8. |
| T11 / B | `tests/integration/test_single_tracker.py` | While the first tracker serves the unreadable page, the second gets the existing CP-693 refusal and exit 1, the first continues serving, data stays identical, and the claim lasts through listener close. Retain alias/kill-recovery checks; update only the CP-696 precedence wording. CP-713; Example 9. |
| T12 / B | `tests/integration/test_start.py`; `tests/integration/test_start_stop.py` | Rewrite unreadable-plus-held-address to the exact existing address stderr line, exit 1, no stdout/unreadable line, unchanged bytes/listing, and release for retry. In `test_refused_start_retains_its_message_and_saved_bytes`, remove the unreadable-only refusal case, retain `occupied-address`, and make `both` assert the address line. Also test an unrelated bind error on unreadable data propagates without either refusal line or an announcement. CP-714, CP-732; Example 10. |
| T13 / B | `tests/integration/test_single_tracker.py` | Extend its existing indeterminate-acquisition scenario matrix: unreadable/free address serves 503, unreadable/held address gets only the address refusal, readable cases retain their outcomes. Retain every acquisition-stage/error fixture, the evidence that injection fired, and bytes/listing checks. CP-715; Example 11. |
| T14 / A + B | `tests/integration/test_start.py` | Repair and, separately, remove the saved file while serving: the response stays byte-identical 503, POST still redirects without saving and output stays quiet. Stop and restart: repaired data serves 200 with the ready line; removed data starts empty. Keep this distinct from the app's existing read-once test. CP-724; Example 13. |
| T15 / A + B | Same as T14 | Across a successful unreadable lifetime, snapshot bytes and all saved paths before start, after root/known/unknown reads, after every supported method including checked and refused POST, and after stop. A local audit-hook observation fails on outbound `socket.connect` in the server process, without preventing the test client's local connection. CP-722, CP-725; Examples 5, 8, 16. |
| T16 / B + C | Same as T14 | After stop, execute the README's existing set-aside procedure in a test-owned copy/scratch home, then restart and observe the normal line, 200 and Projects first-run state. Assert the moved file's bytes are identical and its original contents were never replaced by the start. CP-726, CP-730; Example 14. |
| T17 / A + B | `tests/e2e/test_unreadable_data.py` (new) | Existing `trackers.start(location)` harness, browser root load: first console line, exact heading and path (also with `<&"`), no links/forms/navigation/data controls, stylesheet request succeeds, and no failed stylesheet load. Account for the deliberate 503 document response separately from resource failures. CP-731; Example 17. |
| T18 / C | `tests/integration/test_start.py` plus reading `README.md` | Keep both fixed-heading checks and the console's exact section reference. Read the two passages against CP-734: readable/unreadable starts, second-start refusal, immediate command referent, both set-aside conditions with their conclusion once. Keep excluded Status/content-rule wording untouched. CP-734; Example 20. |
| T19 / all | Existing normal `test_start.py`, `test_routes.py`, `test_single_tracker.py`, `test_saved_data.py`, `test_location_use.py`, `test_start_lifecycle.py`, and architecture suites | Retain readable/absent-data starts, held address on readable data, normal routes/screens, data-rule rejection at persistence level, lock behavior, shared lifecycle and capability/import checks. The new exports must not require loosening these gates. CP-727, CP-733; Examples 15, 19. |
| T20 / all | Full suite and `tests/e2e/`; NFDR quality commands | CP-735's two exact project-card commands exit 0. Run QC-62's Ruff format/lint and mypy commands through the locked project environment. Read all CP-732 sites and search test assertions/docstrings for the superseded unreadable stop/order; distinguish persistence's unchanged typed signal and real location/address refusals from the released exit-1 behavior. Examples 18, 19. |

**Retired assertions and their replacement:** T6–T9 replace unreadable-start exit 1, stderr-only,
no-URL and no-response assertions with serving/announcement assertions while retaining their bytes,
listing, location, exact heading and no-traceback clauses. T12 replaces unreadable-before-address
with the address-only contract. T13 replaces the same unreadable stop/order inside the unclaimed
start matrix. T10 and T14 replace the failed-start release proof with stop/close/restart release
proof, retaining repaired-data 200. Persistence's `UnreadableData` assertions remain unchanged.
This covers the complete CP-732 list, including every user of its two named helpers.

**Rule-edge sweep:** CP-710's empty/encoding/shape/unreadable-location edges are T7–T9; CP-711's
first-output/quiet-request edges are T6 and T5; CP-712–CP-715 are T10–T13. CP-716–CP-723 map to
T1–T5, T15 and T17, including unmarked POST and unknown routes. CP-724's repaired/removed-file
paths are T14; CP-725 spans T7–T16; CP-726 is T16; CP-727 is T19. CP-728–CP-731 are T7, T6/T4,
T16 and T17 respectively. CP-732 is the retirement mapping above; CP-733 is T19/T20 and the
review below; CP-734 is T18; CP-735 is T20. No Example or rule-implied failure path is deferred.

---

## Records this change makes false

Records remain unedited here. The following corrections qualify universal clauses by startup mode;
they do not weaken readable-mode contracts.

- `docs/nfdr.md:73-83`, § 1.1 QC-7 — “a form sent with method=get is answered with its page, 200”
  becomes false in unreadable mode. Qualify it by normal mode and name the unreadable 503 response
  (with the GET stylesheet exception); checked POST still redirects.
- `docs/nfdr.md:91-129`, § 1.1 QC-63 — the unconditional 404 for a missing/deleted task or project
  becomes false on an unreadable start. Scope confirmed-action and not-found status rules to normal
  mode; unreadable mode uses CP-718's 503, never 202 or a data lookup.
- `docs/adr/0011-a-submission-is-a-post-form-and-its-outcome-travels-in-the-address.md`, § Decision,
  “A form sent with method=get is a read” — its universal 200 answer needs the unreadable-mode
  exception. Its “What a page shows is a function of the tracker state and the page's address”
  also needs the startup-failure page supplied through SM-6, without a tracker state. Preserve
  no-session, no-cookie and redirect decisions; record the exception through the append-only ADR
  process rather than editing this Accepted record.
- `docs/adr/0012-pending-confirmation-answered-202-confirmed-action-pages-not-stored.md`, § Decision,
  “The address of a deleted task or project” — the unconditional 404 needs the same normal-mode
  qualification through the append-only ADR process. This change adds no confirmation page.
- `docs/fdr.md:98-100`, § Saved data R-20 — “the tracker's next save replaces it” applies only to
  a readable-mode tracker. State the unreadable start has no save and keeps showing its page until
  restart; the read-once clause stays intact.
- `docs/adr/0005-state-in-memory-one-action-at-a-time.md:37-38`, § Consequences, “overwritten by
  the next save” — qualify this consequence by readable mode through the append-only ADR process.
  The unreadable lifetime has no save and does not overwrite an external repair.
- `docs/fdr.md:326-327`, § Refusals, stale pages and failures R-105 — missing project/task addresses show not-found
  only in normal mode; unreadable mode answers its one page under R-25. Keep the existing rule ID.
- `docs/SDD.md:693-697`, § 4 EX-12 — “carries no header” must agree with CP-717 and
  `docs/DESIGN.md:426-427`, “On UX-S9”: product name as plain text, no area navigation or links.
- `docs/SDD.md:698-699`, § 4 EX-13 — qualify the not-found page by normal mode; the unreadable
  page takes precedence at every page address.
- `docs/CONTENT.md:258-267`, § Terminal messages, third example — the failed-start example for
  unreadable data becomes false. Add the serving unreadable-start message pattern with location,
  unchanged-data statement, URL and section pointer. This is the same correction already named by
  the spec's `deferred_decisions.md`; do not add a duplicate entry.

Read `docs/adr/README.md` and ADR-0001–ADR-0013, `docs/nfdr.md` §§ 1–10, `docs/fdr.md` and
`docs/SDD.md` § 3 and affected § 4 clauses. No module-set or forbidden-import correction is needed.
SDD § 6 S-1's stop and § 7's supersession reason describe the earlier slice's boundary; § 6 S-8
already owns its replacement, so they do not need rewriting.

---

## Architect Review Notes

All structural choices below are the architect's decisions of 2026-10-30.

- **Realize CP-725 by construction (b):** choose a separate unreadable handler rather than an
  optional tracker inside normal route dispatch. Requests cannot accidentally reach a valid action
  or a saver. This adds no product behavior; CP-733 already requires the mode/location seam.
- **Realize CP-718 and CP-724 by construction (b):** the unreadable renderer receives only the
  fixed location and no address, query, body or exception. The handler has no reader to discover
  an external repair. Do not cache request outcomes; deterministic rendering makes the byte
  identity independent of request order.
- **Preserve existing normal contracts (b):** the additive entry point leaves normal `Site` and
  `listen` callers valid. Preserve the route-dependent normal POST check while checking every
  unreadable POST; otherwise extracting one shared gate could silently change the unknown-POST
  404 at `web/routes.py:312-321`, `Site.handle`. No spec line is set aside by this design.
- **Stylesheet/query reading (b):** `/style.css` is the path exception even with a query, following
  the current path/query split at `web/routes.py:312-321`. HEAD on that path is still the unreadable
  representation, because CP-719 grants the exception only to GET. T3 and T5 pin both boundaries.
- **Delegated review — QC-5, QC-20–QC-24:** pass. Add no domain refusal or data rule; catch the
  existing `UnreadableData` type in `main`. `web` renders/dispatches, `main` selects/announces,
  and persistence continues only to signal. The parts table covers every new piece of logic, so
  no placement exception or forbidden import is needed (`docs/nfdr.md:55-67,201-249`, §§ 1.1/1.3).
- **Delegated review — QC-8:** pass on the reading that startup configuration is not session or
  request state. `Site` already retains its bound host (`web/routes.py:294-298`, constructor), and
  SM-6 explicitly passes the unreadable fact/location (`docs/SDD.md:240`, § 3). The added handler
  keeps only that immutable configuration and no request-derived value; no cookies or cached
  action outcomes are introduced (`docs/nfdr.md:84-92`, QC-8).
- **Delegated review — QC-12 and QC-27:** pass. Add one handler and one renderer inside `web`,
  with the existing listener, stylesheet and start lifetime. No new top-level part, framework,
  session store or inner-part coupling is needed (`docs/nfdr.md:159-164,263-267`, §§ 1.1/1.4).
  QC-25, QC-26 and QC-46 are not triggered: neither persistence, the saving contract nor a saved
  field changes (`docs/nfdr.md:251-262,466-472`, §§ 1.4/4).
- **Delegated review — QC-36 and QC-41:** pass. The location passes through `pages._escape`, the
  existing value-entry function (`web/pages.py:451-453`, “one place a value enters a page”). Add
  no raw-value HTML path, secret, account or credential (`docs/nfdr.md:332-337,409-413`, § 2).
- **Delegated review — QC-60:** pass for the design. Use existing standard-library facilities and
  the existing listener/lifecycle interfaces, with no post-3.11 feature required. This is a
  structural review, not a claim that a 3.11 suite was executed; that run remains the recorded
  verification gap (`docs/nfdr.md:553-560`, § 8 QC-60).
- **Delegated review — QC-40, packages:** no applicable critical advisory found in this review's
  GitHub-reviewed list. Downloaded all nine pages with `gh api --method GET /advisories --raw-field
  ecosystem=pip --raw-field severity=critical --field per_page=100 --paginate`; local `--jq`
  comparison by the sixteen external names in `uv.lock` returned eight pages of 100 and one of
  33. The only name match was `GHSA-fff8-4w9p-7v76`, Pygments `>= 1.2.2, < 2.1`, fixed in 2.1;
  the lock pins 2.21.0 (`uv.lock:412-413`). Evidence:
  `https://github.com/advisories/GHSA-fff8-4w9p-7v76` and the command output above. The request
  sent only ecosystem, severity and page size; dependency names were compared locally. No
  dependency, lock format or pin moves in this change.
- **Delegated review — QC-40, browser:** the installed driver's
  `.venv/lib/python3.14/site-packages/playwright/driver/package/browsers.json`, chromium and
  chromium-headless-shell entries, declares revision 1243 / version 153.0.8010.12. Google's
  2026-09-22 security release lists critical fixes in 154.0.8037.57/.58, including
  CVE-2026-95350 and CVE-2026-95357:
  `https://chromereleases.googleblog.com/2026/09/stable-channel-update-for-desktop_0856730748.html`.
  The installed build is older than that fixed release; this review treats it as covered by
  the owner's dated build-specific exception, valid through 2026-11-07 (`docs/nfdr.md:1090-1101`,
  RN-33). Verdict: allowed under that exception on 2026-10-30, not a claim of a fixed browser.
- **Delegated review — QC-40, package feed:** down; graph verification remains owed, as the entry
  permits for this exact outcome (`docs/nfdr.md:387-403`, QC-40). Command evidence:
  `gh api repos/kensaiapp/<the instance KensaiApp is developed in> --jq '{admin:.permissions.admin,security_and_analysis:.security_and_analysis}'`
  returned `{"admin":true,"security_and_analysis":null}`;
  `gh api repos/kensaiapp/<the instance KensaiApp is developed in>/dependabot/alerts` returned 403, “Dependabot alerts are
  disabled for this repository”; `gh api -X POST repos/kensaiapp/<the instance KensaiApp is developed in>/dependency-graph/sbom/exports`
  returned 404. This does not establish that the dependency graph lists the lock's packages.
- **Cold-read result:** the mode decision, owning parts, additive seam, ordering and atomic edge,
  every Example and rule-implied edge, retired assertions, published-text places and false records
  are accounted for above. No conflicting spec reading was needed and no deferred entry is added.
  This design changes no product source and reports no suite verdict.
