# Tech Lead instruction — unreadable-data-page: serve safely when saved data cannot be read

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every path below is relative to it unless a command explicitly runs from the change worktree root.
**Scope:** Build the unreadable-data page, its listener and startup selection, the start-test replacements, and the two README passages required by CP-710–CP-735.

This document owns the implementation tasks for `tracker17 · tobiishi · 2026-10-30_unreadable-data-page`; its `change_spec.md` owns the rules and its `change_design.md` owns the structure. Its home is the active change arc in `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2, “the active Tobiishi”.

## Project layout

```text
products/tracker17/
  web/
    __init__.py                              ← modified: public re-exports only
    pages.py                                 ← modified: unreadable_data_page
    routes.py                                ← modified: UnreadableSite and shared checks/policy
    listener.py                              ← modified: listen_unreadable and shared transport
  main.py                                    ← modified: select mode and announce
  README.md                                  ← modified: the two CP-734 passages
  tests/
    integration/
      test_unreadable_pages.py                ← new
      test_unreadable_routes.py               ← new
      test_listener.py                       ← modified
      test_start.py                          ← modified
      test_start_stop.py                     ← modified
      test_single_tracker.py                 ← modified
    e2e/
      test_unreadable_data.py                 ← new
```

Create the three new test files in the existing directories. Create no package directory or `__init__.py`. The owning parts are `web` for rendering, request checks, routing and transport, and `main` for startup selection and console output (`docs/SDD.md:212-245`, § 3). Keep the module set and import graph in `docs/nfdr.md:166-197`, § 1.2: `web` may import `application`, `errors` and the standard library, and may not import `domain`, `persistence`, `main`, `tests` or third-party modules; `main` may import the four parts, `errors` and the standard library. No inner part gains an import of `web` or `main`.

All published text comes verbatim from this change's `change_text.md`, including the fixed CP-716 page words, alternate console line and README replacements. Do not invent replacement wording. Preserve the data model, normal screens, normal public interfaces, persistence signals and location lock (CP-727, CP-733; design § 2).

## Corrections owed while there

- Owed outside this change's reach: `docs/nfdr.md:73-83`, QC-7 — the universal GET-form 200 answer excludes unreadable mode; scope it to normal mode and retain unreadable 503 with the GET stylesheet exception and checked POST redirect (design § Records this change makes false).
- Owed outside this change's reach: `docs/nfdr.md:91-129`, QC-63 — unconditional confirmed-action and missing-identity status rules need a normal-mode qualification; unreadable mode answers 503 without a state lookup (design § Records this change makes false).
- Owed outside this change's reach: `docs/adr/0011-a-submission-is-a-post-form-and-its-outcome-travels-in-the-address.md`, § Decision — universal GET 200 and rendering from tracker state/address need the unreadable-mode exception supplied through SM-6, retaining the redirect/no-cookie/no-session decisions through append-only supersession (design § Records this change makes false).
- Owed outside this change's reach: `docs/adr/0012-pending-confirmation-answered-202-confirmed-action-pages-not-stored.md`, § Decision — the universal missing/deleted-identity 404 needs a normal-mode qualification through append-only supersession; no confirmation page is added (design § Records this change makes false).
- Owed outside this change's reach: `docs/fdr.md:98-100`, R-20 — replacement by the next save applies only to readable mode; unreadable mode has no save and remains until restart, retaining read-once (design § Records this change makes false).
- Owed outside this change's reach: `docs/adr/0005-state-in-memory-one-action-at-a-time.md:37-38`, § Consequences — qualify “overwritten by the next save” by readable mode through append-only supersession; an unreadable lifetime cannot overwrite an external repair (design § Records this change makes false).
- Owed outside this change's reach: `docs/fdr.md:326-327`, R-105 — not-found pages apply in normal mode; unreadable mode answers its one page under R-25, retaining R-105's identity (design § Records this change makes false).
- Owed outside this change's reach: `docs/SDD.md:693-697`, EX-12 — align “carries no header” with CP-717's product name as plain text and no navigation/links (design § Records this change makes false; existing deferred decision on the header wording).
- Owed outside this change's reach: `docs/SDD.md:698-699`, EX-13 — scope the not-found page to normal mode; unreadable mode takes precedence at every page address (design § Records this change makes false).
- Owed outside this change's reach: `docs/CONTENT.md:258-267`, Terminal messages — replace the failed-start example and extend its formula for a serving unreadable start with location, unchanged-data statement, URL and section pointer; this carries the existing deferred decision without creating another entry (design § Records this change makes false).

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git -C products/tracker17 ls-files returned 297 tracked product-relative paths. Reading that inventory found no CI, runner or build-service configuration; the two workflow-name matches are domain/workflow.py and tests/unit/test_workflow.py, both product Python modules. git ls-files .github returned no paths."
  },
  "decisions": {"override": null, "amd64": null},
  "candidates": [
    {
      "language": "python",
      "image": "docker.io/library/python",
      "image_source": {
        "root": "core",
        "file": "doctrine/engineering/languages/python/environment.md",
        "anchor": "Start a container from the official Python image, `docker.io/library/python`, tagged with CI's"
      }
    }
  ],
  "guest": null
}
```

Language resolution: Python from the project card's `Languages:` line; packet `<CORE>/doctrine/engineering/languages/python/README.md`. No container tag is supplied because the inventory names no CI version and `pyproject.toml:4` states only a minimum. The product decisions read were `docs/adr/`, `docs/nfdr.md` and `docs/SDD.md`; none names an environment override or amd64 requirement. Environment selection remains the gate tool's (`<CORE>/prompts/gate_suite.md`, Steps 3–4).

## TL Review Notes

Decisions made by the Tech Lead, 2026-10-30:

- **Task split:** split design sub-job A into renderer, request handler and listener tasks, so each responsibility has a direct test boundary and the listener uses an already-built handler. Tasks 1–3 preserve the design's additive interfaces and topology (design §§ 2–3).
- **Hint split:** distribute A's § 4 hint by responsibility across Tasks 1–3; each task retains the relevant approach without receiving a working implementation.
- **Ordering:** put the independent README placement before the startup switch so the operator-facing passages are ready when real-start/set-aside tests run. Task 4 uses no output of Tasks 1–3, so its dependencies are None (design § 3 C).
- **Atomic edge retained:** Task 5 includes startup selection and all CP-732 conflicting test rewrites because the design's B/test pair has no intervening green point (design § 3, Atomic-landing edge). Browser and real-start proofs belong here because they require the selected startup mode, rather than merely a constructed handler (design § 5 T6–T17).
- **Content task lane:** Task 4 uses review verification for wording, command referents and duplicate-conclusion removal; those are editorial deliverables, and tests would duplicate the approved text. The fixed-heading checks remain in Task 5 (CP-734; design § 5 T18).
- **Existing transport behaviours:** Task 3 adds unreadable-handler transport coverage; ordinary HEAD suppression, empty malformed-request errors and normal listener behavior remain regression checks, rather than separate tasks claiming to add those existing behaviours (`web/listener.py:34-61`, `_Handler`; design § 5 T5).
- **Baseline permission limit:** `uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`, invoked once from the change worktree root, exited 1: `70 failed, 2665 passed, 33 errors in 286.17s`. The listener setup traceback ended at `self.socket.bind(self.server_address)` with `PermissionError: [Errno 1] Operation not permitted`; a separate local bind check returned `loopback bind: PermissionError, errno=1, Operation not permitted`. The second command did not execute because the first failed. This establishes collection, not a clean product baseline, and does not establish that every failure has the same cause. Do not classify permission failures as an earlier change's deferred red tests or change the suite command to hide socket tests.

### Task 1: Render the unreadable-data page (`web/pages.py`)

**Dependencies:** None

**What to build:** `unreadable_data_page(location)` accepts absolute location text and returns a whole document with the approved title, one heading, body, product name and stylesheet, without navigation or data controls (design § 3 A; CP-716, CP-717, CP-723).

#### Behaviours to verify (developer adds tests to `tests/integration/test_unreadable_pages.py`)

- `test_unreadable_page_names_the_location_and_the_setup_section` — exact CP-716 title, sole h1 and body, one displayed absolute location, unchanged-data statement and words-only section pointer; use approved content (T1).
- `test_unreadable_page_offers_no_navigation_or_data_control` — product name is plain text; no `a`, `form`, `button`, `input`, `select`, `textarea` or `nav`; one stylesheet reference; no script or policy meta tag (T1; CP-717, CP-722).
- `test_unreadable_location_is_literal_text` — locations containing `<`, `&` and `"` round-trip as text, cannot create markup, and reveal no Python error text (T1; CP-723).

#### Held by review

- CP-733 / QC-36 — page building belongs in `web/pages.py` and dynamic location text enters through the existing escaping function; tests prove escaped output, while reading the diff holds the single-entry rule (`docs/nfdr.md:332-337`; design § 4 A).

#### Implement

Infer from failing tests.

# Hint:
Build the unreadable frame without normal navigation. Keep the existing stylesheet and use `pages._escape` for the location (design § 4 A).

#### Verification gate

From the change worktree root:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/
```

Pass: the new page tests pass, existing normal-page tests remain green, and both commands exit 0.

### Task 2: Answer unreadable-mode requests (`web/routes.py`, `web/__init__.py`)

**Dependencies:** Task 1 — its renderer.

**What to build:** Add and re-export `UnreadableSite(location, own_host)` with `handle(method, target, headers, body)` returning the existing `Response`. Keep only immutable startup configuration and no tracker, reader, saver or request outcome. Share checks and response policy without changing normal `Site`, `ROUTES` or its unknown-POST behavior (design § 3 A).

#### Behaviours to verify (developer adds tests to `tests/integration/test_unreadable_routes.py`)

- `test_checked_unreadable_reads_share_one_representation` — GET, HEAD, PUT, DELETE, PATCH and OPTIONS at root, `/people`, real action addresses and unknown paths, with varied queries and bodies, return identical representation bytes, 503, HTML UTF-8 type and `no-store`; no request value enters the page (T2; CP-718).
- `test_only_checked_get_serves_the_stylesheet` — GET `/style.css`, also with a query, returns existing CSS bytes, 200 and CSS UTF-8 type; HEAD there uses the unreadable representation (T3; CP-719).
- `test_checked_post_always_redirects_without_decoding_or_acting` — same-origin POST at known, unknown and stylesheet addresses returns empty 303 with `Location: /` even for malformed/non-text bodies; following the redirect gets the page (T3; CP-720).
- `test_request_refusals_precede_page_stylesheet_and_redirect` — each supported method refuses wrong/missing Host and cross-site/same-site marks with empty 403 and no disclosed location. Every POST lacking same-origin, including missing mark and `none`, is refused. Allowed non-POST with absent mark, `none` or same-origin gets its appropriate answer (T4; CP-721).
- `test_every_unreadable_response_has_policy_and_no_cookie` — 403, 303, 503 and CSS carry `PAGE_POLICY`, including frame protection, and set no cookie (T4; CP-722).
- `test_unreadable_handlers_keep_their_own_startup_location` — interleave distinct handlers and request values; each answer retains only its own configured location, independent of earlier requests (design § 3 A, fixed configuration; CP-718, CP-724).

#### Held by review

- CP-724, CP-725, CP-733 — read the handler's reach: it receives no application, saver or reader; no form decoding or normal action dispatch is reachable. Retain the normal request-check order at `web/routes.py:301-321`; unreadable POST checks must not widen normal unknown-POST checks (design § 3 A).

#### Implement

Infer from failing tests.

# Hint:
Use two handlers with the same request/response boundary and shared security checks and policy construction. Route unreadable POST before parsing fields. Keep the unreadable handler independent of the application so mutating requests have no path to a saver (design § 4 A).

#### Verification gate

From the change worktree root:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/
```

Pass: every method/path/check combination above passes, existing normal routes retain their outcomes, architecture tests pass without loosening their rules, and both commands exit 0.

### Task 3: Bind an unreadable handler through the shared listener (`web/listener.py`, `web/__init__.py`)

**Dependencies:** Task 2 — `UnreadableSite` and its response contract.

**What to build:** Add and re-export `listen_unreadable(address, location)`, returning the existing `Listener` and binding the handler to the actual bound host/port. Preserve normal `listen(address, tracker)`, `AddressTaken`, other bind failures, quiet transport, empty library errors and the existing stop lifetime (design § 3 A).

#### Behaviours to verify (developer extends `tests/integration/test_listener.py`)

- `test_unreadable_listener_uses_its_actual_bound_host` — an ephemeral-port listener accepts its own Host and refuses a wrong/missing Host without exposing the location (T5; CP-721).
- `test_unreadable_listener_transports_the_method_contract` — all seven supported methods over real HTTP satisfy Tasks 1–2, including CSS GET, checked POST and empty security refusals (T5; CP-718–CP-722).
- `test_unreadable_head_omits_the_representation_body` — real HEAD has no bytes, the same representation headers/length as the page, and 503 even at `/style.css` (T5; CP-718, CP-719).
- `test_unreadable_listener_errors_are_empty_and_quiet` — unknown methods and malformed requests, including bad Content-Length, retain empty policy-bearing transport errors and no Python text or console output; valid requests are quiet too (T5; CP-722, CP-727).
- `test_unreadable_listeners_do_not_share_configuration` — two live listeners with distinct ports/locations answer with their own settings (T5).
- `test_unreadable_listener_retains_bind_failure_identity` — occupied address raises existing `AddressTaken`; unrelated bind failure propagates unchanged; normal listener behavior remains covered (design § 3 A; CP-714).

#### Held by review

- CP-733 — binding, transport and their shared checks stay in `web`; `main` builds no page or request dispatcher. Keep `__init__.py` re-export-only (design §§ 2–3).

#### Implement

Infer from failing tests.

# Hint:
Share binding and the existing transport between handlers with the same request/response boundary. Preserve per-listener configuration and existing security-policy construction (design § 4 A).

#### Verification gate

From the change worktree root:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/
```

Pass: real listener tests pass on permitted local sockets, normal listener/lifecycle tests remain green, and both commands exit 0.

### Task 4: Place the approved operator instructions (`README.md`)

**Dependencies:** None

**What to build:** Place `change_text.md`'s approved replacements in “Starting the tracker again” and “Setting saved data aside”, as CP-734 and design sub-job C require.

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- The two passages describe readable starts and unreadable starts, the alternate console line, the page at every address and unchanged data; they keep the second-tracker explanation (CP-734; T18).
- Both heading names and the existing set-aside commands remain exact. “the same commands” has the commands it means in the same sentence or the immediately preceding sentence (CP-734; T18).
- Both conditions formerly beginning “If `mv` says” and “If the new directory is empty” remain, with their shared conclusion stated once. The unreadable-start passage no longer says that start failed (CP-734; T18).
- The approved words match `change_text.md` verbatim. Review `git diff "$(git merge-base main HEAD)" -- products/tracker17/README.md` from the change worktree root: only the two named passages change. The Status sentence, missing-content-rule wording and every other passage remain unchanged. This check ends with the change; it is no suite test (CP-734; spec § Out of Scope).

#### Implement

Verified by review — no test.

#### Verification gate

From the change worktree root:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/
git diff "$(git merge-base main HEAD)" -- products/tracker17/README.md
```

Pass: each editorial criterion holds on reading the diff, existing fixed-heading checks pass, and both suite commands exit 0 with no new failures.

### Task 5: Select the serving mode and replace the old startup proof (`main.py`, `tests/integration/test_start.py`, `tests/integration/test_start_stop.py`, `tests/integration/test_single_tracker.py`, `tests/e2e/test_unreadable_data.py`)

**Dependencies:** Task 3 — `listen_unreadable` and its `Listener`/`AddressTaken` contracts.

**What to build:** Keep the location claim, load once and select the unreadable listener on `UnreadableData`; readable/absent data uses the normal tracker. Bind before marking started and announcing. Place the approved single flushed stdout line with the absolute location, bound URL and exact section name. Retain `serve_until_stopped`, `SigintStopRequests` and claim ownership through listener close. Replace all conflicting CP-732 assertions and their helper callers together with this startup change (design § 3 B, Atomic-landing edge).

Every real start uses a child process, test-owned paths/ports, bounded announcement/HTTP waits and an early-exit check that fails promptly on the earlier exit-1 behavior. Always stop/kill and reap children on failure. Do not call a newly serving start synchronously in a retired exit test (design § 5 preamble). Use the existing external signal and acquisition-error observation facilities; patch no product name (CP-733).

#### Behaviours to verify (developer extends the three named integration modules and adds `tests/e2e/test_unreadable_data.py`)

- `test_unreadable_start_serves_and_announces_once` — real start stays alive, first stdout is the exact approved one-line announcement, stderr is empty, and `/`, `/people`, `/nothing?x=1` share the 503 page with no controls. Location is absolute and identical on console/page; port-zero startup announces the actual port. Requests add no console output (T6; CP-710, CP-711, CP-729).
- `test_each_dr6_break_serves_without_changing_saved_data` — seven separately collected cases: truncated data; unknown status; unknown priority; task without its project; duplicate project name; reused task identity; overlong saved field. Each reaches a real 503 and preserves exact bytes and the recursive directory listing through stop. Each fails promptly on the old exit-1 tree (T7; CP-728).
- `test_other_invalid_saved_values_serve_without_changing_data` — retain every invalid-file, assignee, task-rule, label, operator-name and comment text/author fixture; include empty/non-UTF8/missing-key/wrong-shape documents. Replace `_unreadable_start` and `_unreadable_comment` held-address shortcuts with free-port serving checks. Retain independent `SavedData.load`/`UnreadableData` assertions and fixed-heading checks (T8; CP-710, CP-732).
- `test_unreadable_location_serves_without_touching_it` — a location that is a file and a directory without read permission both serve. Snapshot before permission restriction, stop before restoring permissions for comparison, retain the real-root skip, and preserve bytes/listing/no-refusal checks (T9; CP-710, CP-725).
- `test_unreadable_start_stops_quietly_and_releases_its_location` — at announcement, idle serving, close and return boundaries, Ctrl-C and separately delivered repeated Ctrl-C return 0 with no additional output and unchanged saved paths/bytes. A subsequent start can use the released location and port (T10; CP-712, CP-725).
- `test_second_tracker_is_refused_while_unreadable_page_serves` — second start gets the exact CP-693 line and exit 1, first tracker keeps answering 503, data remains identical and the claim lasts through listener close. Retain alias and kill-recovery cases (T11; CP-713).
- `test_held_address_wins_on_an_unreadable_start` — exact existing address line on stderr, exit 1, no stdout or unreadable line, unchanged bytes/listing and release for retry. An unrelated bind error propagates with neither refusal line nor announcement (T12; CP-714).
- `test_indeterminate_claim_preserves_selected_start_mode` — retain every mkdir/open/flock failure fixture and its fired marker; unreadable/free serves 503, unreadable/held emits only the address refusal, readable cases retain outcomes, and snapshots remain identical (T13; CP-715).
- `test_external_repair_does_not_change_the_running_unreadable_page` — repair and separately remove the saved file while serving; responses stay byte-identical 503, checked POST redirects without saving, output stays quiet. After stop/restart repaired data serves 200 with the normal line, removed data starts empty (T14; CP-724).
- `test_unreadable_lifetime_preserves_all_saved_paths_and_bytes` — snapshot before start, after root/known/unknown reads, after every supported method with checked/refused POST, and after stop; no file/path is added, replaced or removed. Observe server-process outbound `socket.connect` through a local audit hook while permitting the separate test client's connection (T15; CP-722, CP-725).
- `test_set_aside_then_restart_preserves_the_earlier_work` — after stopping, execute the README's existing set-aside commands in a test-owned copy and scratch home. Restart answers 200 with Projects first-run state and normal ready line; moved bytes are identical (T16; CP-726, CP-730).
- `test_browser_opens_the_unreadable_page_without_controls` — use existing `trackers.start(location)`, assert the first console line, exact heading/location including `<&"`, no links/forms/navigation/data controls and a successful stylesheet load. Treat intentional document 503 separately from a failed resource load (T17; CP-731).
- Keep existing readable/absent-data starts, normal routes/screens, address refusal on readable data, persistence-rule rejection, lock/alias/kill recovery, normal lifecycle and architecture checks without weakening assertions (T19; CP-727, CP-733).

#### Held by review

- **Retired assertion sweep:** account for every CP-732 named test and all callers of `_unreadable_start` / `_unreadable_comment`, retaining invalid fixtures, exact heading references, location, preservation and no-traceback assertions. In `test_start_stop.py::test_refused_start_retains_its_message_and_saved_bytes`, remove only unreadable-only from the refusal cases; retain occupied-address and make both assert the address line. Update `test_single_tracker.py::test_location_in_use_wins_over_other_start_refusals`'s ordering description, and update the indeterminate-acquisition matrix's unreadable cases (T6–T13, T18, T20; CP-732).
- **Read-only structure:** `main` selects and announces but holds no page; the unreadable branch creates no `Tracker`, `empty_state`, saver-backed application or second reader. `persistence` continues only to signal. Read the touched source docstrings and helpers and replace stale stop/precedence descriptions in their own task's files (design § 3 B; `main.py:101-130`; `tests/integration/test_start.py:1-54`; CP-733).
- **Change-only boundaries:** from the change worktree root, review `git diff "$(git merge-base main HEAD)" -- products/tracker17/domain products/tracker17/application products/tracker17/persistence products/tracker17/errors.py products/tracker17/docs products/tracker17/pyproject.toml products/tracker17/uv.lock`. Expect no diff. Do not persist this branch comparison as a suite test (design § 2; CP-727, CP-733; spec § Out of Scope).

#### Implement

Infer from failing tests.

#### Verification gate

From the change worktree root:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/
rg -n 'unreadable|UNREADABLE|_unreadable_start|_unreadable_comment|couldn.t read|stops start|stop_start' products/tracker17/tests/integration/test_start.py products/tracker17/tests/integration/test_single_tracker.py products/tracker17/tests/integration/test_start_stop.py
git diff "$(git merge-base main HEAD)" -- products/tracker17/domain products/tracker17/application products/tracker17/persistence products/tracker17/errors.py products/tracker17/docs products/tracker17/pyproject.toml products/tracker17/uv.lock
```

From the product root, run QC-62 and the locked-manifest check (`docs/nfdr.md:566-580`, QC-62; § 10):

```sh
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy main.py errors.py domain application persistence web
uv lock --check
```

Pass: all new behaviors and retained regression tests pass; both exact suite commands and each quality command exit 0. Read each search hit: no free-address unreadable start asserts exit 1 or no service; real location/address refusals and persistence's typed signal remain. Every DR-6 case is separately collected and asserts bytes/listing preservation. All review-held criteria pass, no excluded path changes, and the README's two edited passages match the approved text.
