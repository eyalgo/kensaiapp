# Change Spec — a start on unreadable saved data serves one plain page

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing
**Request:** Right now, if the tracker is started and its saved data cannot be read, it prints one message and exits with status 1. Change that: the tracker should start anyway, say on the console that the data could not be read and where it is, and then answer every address with one plain "unreadable data" page. The page says where the data is, says nothing was changed, has no navigation and no control that acts on the data, and points to the README's section on setting saved data aside (SDD § 7 `supersedes`, SM-6, SD-5; UXD UX-F11, UX-S9). After the operator sets the data aside as the README says, a restart starts empty and the set-aside file still holds the earlier work. The start-level tests that assert the old exit-1 stop are rewritten, in `tests/integration/test_start.py` and `tests/integration/test_single_tracker.py` (the location-in-use order and the unclaimed-start scenarios). There is one start-level test per kind of break SRS DR-6 names (a value longer than its field's maximum among them), each asserting the saved data's bytes are unchanged (AC-7). The README says what a start does in both cases, and its two wording faults are mended in the passages this change edits anyway: "the same commands" in "Starting the tracker again" with no commands before it in that sentence, and the one conclusion stated twice in "Setting saved data aside". What must not be weakened: saved data is never written, replaced or deleted by a start on unreadable data or by serving the page (SD-4); the page carries no control that sets data aside or repairs it; the second-tracker refusal and the lock stay as landed; the data model, the other screens and the address-taken behaviour stay unchanged. Not in this change: the README's `readme-status` sentence and `docs/what_left.md`, and the word the README publishes for a missing content rule.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `core/doctrine/engineering/languages/python/README.md`

---

## Change Summary

A start on saved data it cannot read no longer stops. It serves one plain page at every address and says so on the console, and it leaves the data as it found it, so the operator can set the data aside and start fresh. Sizing: one capability, one merge. The acceptance boundary is SDD § 6 S-8's unreadable-data behaviour with SRS DR-6 and AC-7. The page, the console line, the tests and the README passage are that capability and its proof.

---

## Rules

### The start

- **CP-710:** A start on saved data that counts as unreadable does not exit. It serves until it is stopped. Unreadable is FDR R-21 and R-22 and SRS DR-6, whatever the cause: the tracker cannot read all of the data, or the data breaks a data rule. So a truncated file, an empty file, bytes that are not text, the wrong shape, a location that is a file and a location the tracker has no permission to read all take this path. No part of the data is loaded (FDR R-23), and no empty tracker is presented (FDR R-25).
- **CP-711:** Once the tracker answers requests, the console's first output is one line on standard output, and standard error stays empty (FDR R-2, R-24; UXD UX-S2; SDD OB-2; NFDR QC-55). The line says that the tracker couldn't read its saved data, gives the data's location as an absolute path, says nothing in it was changed, gives the address to open as `http://<host>:<port>`, and names the section `Setting saved data aside` exactly. It does not begin "The tracker didn't start" and is not the normal ready line. Its exact words are written at the content step, to `CONTENT.md`, which uses "couldn't read" and none of its banned words for saved data (`docs/CONTENT.md:186`). A request writes nothing further to the console.
- **CP-712:** Ctrl-C stops a tracker serving the page with status 0 and nothing more written, however many times it is pressed (SRS FR-1). The location is free for the next start.
- **CP-713:** A second start on a location whose tracker is serving the page gets the existing refusal: the CP-693 line, status 1, and the first tracker still answers. Where several apply, the first that applies decides the one line: another tracker on the location, then the address taken.
- **CP-714:** A start on unreadable data whose address is taken shows today's address-taken line on standard error and exits 1, with no unreadable-data message, and the file's bytes and the location's listing are unchanged (FDR R-4, NFDR QC-58). A bind that fails for another reason fails as it does on readable data, and is not told the address is taken.
- **CP-715:** A start on unreadable data where it cannot be determined whether another tracker is on the location serves the page as in CP-710 (CP-702's class of causes; SDD SM-5).

### The page

- **CP-716:** The page's words are `CONTENT.md`'s (`docs/CONTENT.md:251-256`, `:388`). Its title is `The saved data can't be read - tracker17`. Its one `h1` is `The saved data can't be read`. Its body is `The tracker couldn't read its saved data, which is kept at <location>. Nothing in it was changed or overwritten. To start fresh on purpose, follow Setting saved data aside in the setup instructions.` `<location>` is the same absolute path as the CP-711 line.
- **CP-717:** The page has no `a`, `form`, `button`, `input`, `select`, `textarea` or `nav` element (FDR R-26; UXD UX-S9, RN-18; SDD EX-12). The product name `tracker17` stands at the top as plain text with no nav links (`docs/DESIGN.md:427`). The pointer to the section is words only. The one stylesheet reference is allowed (SDD EX-10).
- **CP-718:** Every request that passes CP-721 gets the same page, byte for byte, whatever its address and query, real or unknown, with one method exception in CP-720 and one address exception in CP-719 (UXD § 4, UX-F11). The domain of methods is all those the listener answers: GET, HEAD, POST, PUT, DELETE, PATCH and OPTIONS. The answer is status 503, `Content-Type: text/html; charset=utf-8` and `Cache-Control: no-store`. HEAD carries the same status and headers and no body. Nothing from the address reaches the page.
- **CP-719:** `GET /style.css` still answers the stylesheet, status 200, as `text/css; charset=utf-8`, so the page is styled like every other (SDD EX-10; `docs/DESIGN.md:427`). It reveals nothing about the saved data.
- **CP-720:** A POST marked `Sec-Fetch-Site: same-origin`, to any address and with any body, changes nothing and is answered 303 with `Location: /`, where the browser gets the page (NFDR QC-7, ADR-0011). Any other POST that passes the host check is refused under CP-721.
- **CP-721:** The request check still runs first (SDD SEC-2; NFDR QC-31, QC-32). A request whose `Host` does not name the tracker's own address, a request marked `cross-site` or `same-site`, and a POST not marked `same-origin` each get today's empty 403. None of them shows the page, so no other site learns the location.
- **CP-722:** Every response in this mode carries the page policy as a `Content-Security-Policy` header with `frame-ancestors 'none'`, and no page carries it as a tag (NFDR QC-33, QC-34; SDD SEC-3). The tracker opens no outbound connection (NFDR QC-35).
- **CP-723:** The location is shown as text, escaped like every value put into a page: a location holding `<`, `&` or `"` shows those characters literally (NFDR QC-36). No page shows Python's error text, and neither does the console line (NFDR QC-57).

### The saved data

- **CP-724:** The saved data is read once, at start (FDR R-20; NFDR QC-54). A file repaired or removed while the page is being served does not change the answer. The next start reads it afresh, and on readable data prints the normal ready line and serves.
- **CP-725:** From the start through every request, a POST included, to the stop, the saved file's bytes and the location's listing are unchanged: nothing written, replaced, deleted or added beside it (FDR R-27; SDD SD-4; NFDR QC-51).
- **CP-726:** After the operator stops the tracker and sets the data aside with the README's commands, the next start prints the normal ready line, `GET /` answers 200 with the Projects page's first-run state, and the set-aside file's bytes are what they were (FDR R-28; SRS AC-8).

### What stays as it is

- **CP-727:** A start on readable data or on no saved data, a start whose address is taken on readable data, and a second start on a running tracker's location each behave as they do today, and the data model and every other screen are untouched.

### The proof

- **CP-728:** There is one start-level test per kind of break SRS DR-6 names: cannot read all of it, an unknown status, an unknown priority, a task whose project does not exist, two projects with one name, a reused task identity, and a value longer than its field's maximum (SRS AC-7; NFDR QC-22, QC-51). DR-6 says such breaks "include" these, so this list is the floor. Each test starts a tracker on data with that break, asserts the page is answered, and asserts the file's bytes and the listing are identical before and after. Each fails on the tree before this change, because that tree exits 1, and it fails rather than hangs.
- **CP-729:** A test starts a real tracker process on unreadable data and asserts CP-710, CP-711, CP-716, CP-717 and CP-718 at the root, at one real route and at one unknown address. A test asserts CP-721 and CP-722 per refused request on this path.
- **CP-730:** A test moves unreadable data aside as the README's commands do, starts a tracker, and asserts CP-726.
- **CP-731:** A layer-5 test starts a tracker on unreadable data, opens the root in the browser, and asserts the CP-711 first console line, the page's `h1`, no link, no form and no failed stylesheet load (NFDR QC-55). It runs under the existing `tests/e2e/` harness.
- **CP-732:** These existing tests change, and each keeps asserting the location is named, the bytes and listing are unchanged, and no traceback appears. In `tests/integration/test_start.py`: `test_an_unreadable_start_returns_non_zero_with_one_message_naming_the_location`, `test_an_unreadable_start_changes_nothing_in_the_location`, `test_other_unreadable_files_are_refused_the_same_way`, `test_an_unreadable_start_writes_exactly_the_one_line_with_the_closing_sentence`, `test_invalid_assignees_stop_start_with_the_existing_plain_message`, `test_the_message_closing_sentence_quotes_a_heading_the_readme_has` (still asserts the heading exists), `test_unreadable_saved_data_wins_over_a_held_address` (now asserts CP-714), `test_a_saved_task_that_breaks_a_task_rule_stops_start_with_the_plain_message`, `test_invalid_saved_labels_stop_start_with_existing_message`, every test using `_unreadable_start` or `_unreadable_comment` (a held address no longer proves the data was refused), `test_a_location_that_is_a_file_keeps_the_unreadable_start`, `test_a_directory_without_read_permission_keeps_the_unreadable_start` and `test_failed_start_on_unreadable_data_releases_its_location_for_retry` (still ends in repaired data serving 200). In `tests/integration/test_single_tracker.py`: `test_indeterminate_acquisition_keeps_existing_start_behavior` (the `unreadable` scenario serves the page; `unreadable-and-address-held` shows the address line) and `test_location_in_use_wins_over_other_start_refusals` (keeps its assertions; its stated order loses the unreadable step). In `tests/integration/test_start_stop.py`: `test_refused_start_retains_its_message_and_saved_bytes` (the `unreadable-data` case leaves it; `both` asserts the address line; `occupied-address` stays). After this, no test asserts that a start on unreadable data exits 1 or serves nothing. These rules replace CP-7, CP-43, CP-65, CP-101, CP-137, CP-647, CP-696's middle step and CP-700 where those say otherwise.
- **CP-733:** `main` chooses between the normal tracker and the page and writes the console line, and holds no page (NFDR QC-24, QC-45; SDD SM-6). `web` is given the fact and the location across SM-6, builds the page and answers, with no reach to the saved data (NFDR QC-23). `persistence` keeps its signal and decides nothing about what happens then (NFDR QC-22; SDD SM-5). Nothing beyond the standard library is added at run time (NFDR QC-19). Each new test module names what it checks (NFDR QC-11), no test patches a name inside a part (SDD TS-2), a path a docstring names exists (SDD TS-4), and the code passes the NFDR QC-62 format, lint and type checks.
- **CP-734:** `products/tracker17/README.md` changes in the passages "Starting the tracker again" and "Setting saved data aside", in words the content step writes (SDD § 6 S-8; FDR R-8). It says a start on saved data that can't be read gives a console line and a page at every address, that nothing is changed, and it keeps saying what a second tracker's start does. "the same commands" stands with the commands it means, in that sentence or the one directly before it. The sentences beginning "If `mv` says" and "If the new directory is empty" keep both conditions and state their conclusion once. The sentence saying "the tracker didn't start because it couldn't read its saved data" no longer says the tracker didn't start. Both headings keep their exact names.
- **CP-735:** `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/` both exit 0.

---

## Examples

| Scenario | Expected behavior | Rules |
|---|---|---|
| Truncated `tracker.json`, address free | Keeps running. One stdout line with the location and the address; stderr empty | CP-710, CP-711 |
| Same, `GET /`, `GET /people`, `GET /nothing?x=1` | Identical page, 503, `no-store`; `h1` and body as CP-716; no link, form or nav; `tracker17` as plain text | CP-716, CP-717, CP-718 |
| Same, `HEAD /people` and `PUT /projects` | 503 and the page's headers; HEAD has no body | CP-718 |
| Same, `GET /style.css` | 200 stylesheet | CP-719 |
| Same, POST to `/projects` marked `same-origin` | 303 to `/`; data unchanged | CP-720, CP-725 |
| Same, POST with no mark, wrong `Host`, or `cross-site` | Empty 403 with the policy header; no location shown | CP-721, CP-722 |
| Location holding `<&"` | Those characters shown literally; no Python error text | CP-723 |
| Ctrl-C while the page is served | Status 0, nothing more written, bytes and listing unchanged | CP-712, CP-725 |
| Second start while the page is served | CP-693 line, exit 1; the first still answers | CP-713 |
| Unreadable data and a held address | Address-taken line only, exit 1, nothing changed | CP-714 |
| Unreadable data, and the lock call fails with no other tracker | The page is served; no refusal line | CP-715 |
| Location is a file, or has no read permission | The page is served; nothing changed | CP-710, CP-725 |
| File repaired while the page is served | Still the page; after Ctrl-C and a new start, the normal ready line and 200 | CP-724 |
| Stop, run the README's commands, start again | Ready line, Projects first-run state; the set-aside file's bytes unchanged | CP-726, CP-730 |
| Readable data; no data; address taken on readable data | As today | CP-727 |
| Each DR-6 break in turn | Page answered; bytes and listing identical; fails on the earlier tree | CP-728, CP-729 |
| Browser opens the root on unreadable data | `h1` shown, stylesheet loaded, no link and no form | CP-731 |
| The test suites after the change | No test asserts the old stop; both suite commands exit 0 | CP-732, CP-735 |
| Reading the code's reach | `main` chooses, `web` builds the page, `persistence` only signals | CP-733 |
| Reading the README's two passages | Both cases described; "the same commands" has its commands; the conclusion stands once | CP-734 |

---

## Verified Claims

Base commit for every run below: `ae37deac2`.

| Claim | Verified by | What came back |
|---|---|---|
| Rendering: no rule pins output that renders a language-level fact | Walked the rules. The location, the address and the status are product-chosen values, so no rendering row is owed | `none — no rule pins a language-level rendering`; the Python packet was read in full and decides no rule |
| A start on damaged data exits 1 today, so every CP-728 test fails on the earlier tree | A real `main.start` on a free port on a truncated `tracker.json` in a scratch location, driven by a throwaway script | Exit 1, nothing on stdout, one stderr message naming the location |
| CP-726 holds at the base once the data is moved | Same scratch location, moved with the README's `mkdir -p` and `mv` under a scratch home, then a real start and `GET /`, then SIGINT | Ready line; 200; first-run words present; exit 0; stderr empty; the moved file's checksum identical |
| CP-714: the address-taken behaviour stays | `test_start.py::test_a_start_with_a_held_address_prints_the_one_line_and_changes_nothing`, `::test_a_held_address_leaves_existing_saved_data_untouched`, `::test_a_start_refused_the_address_for_another_reason_is_not_told_it_is_taken` | `ae37deac2`, passed |
| CP-713: the second-tracker refusal stays | `test_single_tracker.py::test_second_tracker_is_refused_without_changing_the_first`, `::test_location_in_use_wins_over_other_start_refusals` | `ae37deac2`, passed |
| CP-712, CP-727: a stop and a kill recovery behave as stated | `test_start_stop.py::test_real_start_stops_at_the_completed_ready_write`, `::test_idle_stop_preserves_every_saved_path_and_byte`, `test_single_tracker.py::test_tracker_starts_after_the_owner_is_killed` | `ae37deac2`, passed |
| CP-721: today's refusals are empty 403s | `test_routes.py::test_a_wrong_host_is_refused`, `::test_a_get_is_refused_only_when_marked_from_another_site`, `::test_a_submission_not_marked_same_origin_is_refused`; read `web/routes.py:301-321` | `ae37deac2`, passed; `handle` answers 403 before routing |
| CP-734: both README headings exist | `test_start.py::test_the_readme_has_both_fixed_headings` | `ae37deac2`, passed |
| CP-732: the named tests assert the old stop | Read each at its lines; grepped `tests/` for the old line and for damaged data handed to a start | The named set; `test_saved_data.py` and `test_location_use.py` assert the persistence signal and do not change |
| CP-717: the page frame today carries the nav links | Read `web/pages.py:474-492`: `_document` writes `<nav>` on every page | So this page cannot use that frame unchanged |
| CP-719: the stylesheet is a route today | Read `web/routes.py:154` and `:379-380` | `GET /style.css`, 200, `text/css; charset=utf-8` |
| CP-731: the layer-5 harness can start on any location | Read `tests/e2e/conftest.py:78-96` | `TrackerFactory.start(location)` takes a location and reads the first stdout line |
| CP-734: the README's sentences as quoted | Read `README.md:79`, `:83`, `:95` | Present as the request and this rule quote them |

---

## Out of Scope

- The README's `readme-status` sentence and `docs/what_left.md`, which the request excludes.
- The word the README publishes for a missing content rule, which the request excludes.
- Any control in the tracker that sets data aside or repairs it (UXD RN-18; SDD § 6 S-8).
- Unreadable data found while the tracker runs (FDR OOS-16).
- A malformed request the listener itself answers, such as a bad `Content-Length`, which keeps today's status-only answer.
- Editing `CONTENT.md` or any other definition document. Its unreadable-start example at `docs/CONTENT.md:267` goes false with this change, and it holds no rule for this console line. Both are parked in `deferred_decisions.md` for the document's owner.

---

## Locked Answers (the divergence record — self-review 2026-10-30)

- **Gap 1 — Unreadable data and a held address (b):** the address-taken line, exit 1. The page cannot be served without the address, and the request keeps the address-taken behaviour unchanged. The next start, once the address is free, shows the page. This reverses CP-43's "unreadable data wins", and SDD SM-6 already gives this outcome only one outward signal for it.
- **Gap 2 — Console stream and content (b):** one line on standard output, carrying the address too. The request says only "the console". This line takes the ready line's place on the same stream, and FDR R-2 and UXD UX-F11 need the operator to learn the address to open. Reversible.
- **Gap 3 — Status and caching (b):** 503 with `no-store`. No record fixes these. 503 says the tracker cannot do what was asked until the operator acts, and `no-store` keeps a browser from showing the page after a set-aside and restart has made it false. The operator sees the same page whatever the status. Reversible.
- **Gap 4 — "Every address" and the stylesheet (a):** `GET /style.css` still answers the stylesheet. Read literally the request would leave the page unstyled, against SDD EX-10 and `docs/DESIGN.md:427`. It shows no data and no navigation.
- **Gap 5 — Methods and POST (b, e):** every method gets the page except POST, which is answered 303 to `/` when marked `same-origin`. Reloading then asks no resubmission, and it meets NFDR QC-7's "every submission is answered by sending the browser to a page address". The request names addresses and not methods, so this closes the method domain.
- **Gap 6 — Checks the request left out (e):** CP-721, CP-722, CP-723 and CP-731 state NFDR QC-7, QC-31 to QC-36, QC-55 and QC-57, and CP-733 states QC-11, QC-19, QC-22 to QC-24, QC-45, QC-62 and SDD TS-2 and TS-4, because they bind this page and this console line.
- **Gap 7 — "No header" and the product name (a):** the product name stands as plain text with no nav links. SDD EX-12 says this page "carries no header and no navigation", and `docs/DESIGN.md:427` says its header "shows the product name and no nav links". EX-12's header is the "one header with the areas that exist", so the two agree on what matters: no areas and no links. How the page looks is the design document's to say. The difference in wording is parked for the owners.
- **Gap 8 — Tests the request did not name (f):** `test_start_stop.py::test_refused_start_retains_its_message_and_saved_bytes` asserts the old stop and the old order, so it changes too. What it keeps is in CP-732.
- **Gap 9 — Which words are fixed here (b):** the page's words are pinned because `CONTENT.md` already has them. The console line and the README are stated as what they must say, because their words are the content step's to write and no record holds them yet.
- **Gap 10 — The breaks counted (b):** "an unknown status or priority" counts as two kinds, so the conservative list holds seven tests. More tests cost little, and a missed kind would leave AC-7 unproved.

