# SDD open issues — tracker17

> Companion to `SDD.md`. The CTO wrote the SDD; this file holds what that run could not settle from
> its inputs (the PRD, the SRS, the UXD, and any context or constraints), and the calls that are the
> CPO's or the CDO's to make. An item whose call is the CPO's or the CDO's carries that seat's
> `Seat:`; an item whose call is the CTO's carries `cto` or no `Seat:` field.
>
> **Answer inline** — fill each **Answer** / **Confirm or override** / **Keep or re-cut** /
> **Your call** slot — **commit this file**, then re-run `product-sdd`. It folds your answers into
> the SDD and drops the resolved items. When nothing is left open, `product-sdd` **deletes this
> file**: no file = the SDD is done.
>
> Your answers are never thrown away. Each time `product-sdd` folds them in, it first copies this
> file whole to `docs/trail/sdd/` — so what you decided, and why, stays readable and citable for good.
>
> **An item may name the seat that answers it.** Any item in any section carries an optional
> `- **Seat:** <seat>` field beside its other fields. Its value is the name of the agent whose posture
> answers the item — `cto`, `cpo` or `cdo`. An item with no usable value, whether the field is absent,
> empty or still the `<seat>` placeholder, is answered in the seat of the skill that produced this file.
> The field names the *answering* seat. It is not the seat that raised the item (`Raised by:` /
> `Held by:`), and it is not the document an answer belongs to.
>
> **An item in §§ 1–3 names the seat that raised it.** An item the CPO raised is a product call and
> an item the CTO raised is a technical one, and the answer that settles one does not settle the
> other. **§ 4 names two seats and no raiser** — a
> disagreement is not something one seat asked, it is two positions held by different seats, and the
> answer that settles it picks between them.
>
> **§ 5 names a raiser from outside the SDD's lanes entirely.** §§ 1–4 are all the SDD's own three
> lane seats; § 5 is a seat that never held a lane in it, reading it long after it settled and

> **No producing run wrote this file.** The PM opened it on 2026-10-20, in a route review, to carry
> items § 5.1 and § 5.2. `product-sdd` has no record of writing it. It exists because no record names
> the response policy a move's pages follow in the browser's history, and because § 6 S-4's bar still
> has an out-of-date move offer a reload that UX-I3 now rules out.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — a best-effort answer was drafted; confirm or override

### 2.1 § 11 R-2 and the first Open Question still call the confirmation case unverified; its tests have run and passed
- **Raised by:** CTO
- **Seat:** cto
- **Drafted into the SDD:** nothing — this run writes no document. The draft it hands: § 11 R-2's "Two cases stay unverified. The confirmation case: focus on the confirmation's sentence, the double press that never confirms, and back-out returning focus to the restored button (§ 4 EX-6), which `status-moves` tests" becomes a verified case, in the form R-2 gives the two already verified: `tests/e2e/test_moves.py`, `test_keyboard_opening_focuses_the_visible_sentence` (the sentence alone has focus, in view), `test_keyboard_confirming_and_back_out_use_their_own_intents` (backing out returns visible focus to the trigger), `test_double_click_never_confirms_at_the_original_trigger_coordinates` and `test_keyboard_opening_on_a_far_row_focuses_the_visible_sentence` (row 40 of 60, the list scrolled part-way), 67 passed in a fresh clone at `9b05680c7` with the pinned library and Chromium 153.0.8010.12, and no product code moved since (`git diff --stat 9b05680c7 HEAD -- products/tracker17 ':!products/tracker17/docs'` printed nothing on 2026-10-20). The first item of § Open Questions closes, as RN-36 and RN-41 closed the other two cases, and the second item stays. § 7's `validates` row for `status-moves` describes what the tests show and stays. R-2 keeps the four tests among its triggers, as it keeps `first-project`'s and `tasks-in-a-project`'s, and the assistive-technology case stays open with its VoiceOver settling path.

  > **No producing run wrote this item.** A `companion-self-answer` run raised it on 2026-10-20 while answering §§ 5.1 and 5.2, from reading § 11 R-2 and § Open Questions whole against `tests/e2e/test_moves.py` and the station `tracker17 · shukuba · 2026-10-19_cancel-confirmation`, whose refine found every reached-when item holding on `main`. `product-sdd` has no record of writing it. It exists because a fact the document states is now false.
- **Rationale:** R-2 names the confirmation tests as what settles the case, and they exist and pass; a risk that calls its own settled case unverified sends a reader to run a check that has run. The source is the station's refine (`system/projects/tracker17/journey/nemawashi/2026-10-07_status-moves/2026-10-20_history-after-confirm_report.md`, "Considered, not moved", first row) and the tests on disk; no upstream document moves. `nfdr.md` RN-15 carries the same "stays open" sentence and is the Principal Architect's, read from this document as § 12 says.
- **If overridden:** nothing moves but the sentence: R-2's triggers, response and fallback stand either way, and no slice, fence or edge depends on which cases R-2 calls verified.
- **Confirm or override:** confirm, with four additions. The draft is taken as written: R-2's "Two cases stay unverified. The confirmation case: …" becomes a verified case naming its four tests, the first item of § Open Questions closes and the second stays, § 7's `validates` row for `status-moves` stays, and the four tests stay among R-2's triggers. **Addition one, the result is a count at the commit it names, and the tree was re-measured today.** 67 passed at `9b05680c7`, in a fresh clone on the owner's Mac, is what the record says (`system/projects/tracker17/journey/nemawashi/2026-10-07_status-moves/2026-10-20_history-after-confirm_report.md`, "Considered, not moved", first row; the unit's `code-integrity-report.md`, "The browser folder", `67 passed in 30.68s`, no skip). The draft's "printed nothing on 2026-10-20" was true at `ca2f9e98a` and is dated: at `72d80bffa` on 2026-10-21 the same `git diff --stat` lists one line of `products/tracker17/README.md` (commit `819818875`, the Status paragraph) and no code; no heading changed, and the only test that reads the README (`tests/integration/test_start.py`, headings) is layer 3, outside the browser folder. R-2 states the result in the form it already uses for `first-project` and `tasks-in-a-project`, a dated diff and the commit the count was taken at, which is the form `nfdr.md` RN-15 settled on (`trail/architecture/cycle-11.md` § 3.1: tie each result to its commit, claim nothing about the tree after it). **Addition two, the browser build is asserted by the run, not inferred from the pin.** `tests/e2e/test_moves.py:452` sets `PINNED_BROWSER = "153.0.8010.12"` and `:541`, inside `test_history_matrix_revalidates_current_saved_status`, asserts `browser.version == PINNED_BROWSER` — one of the 67. Precisely: the four focus tests drive the headless shell the pinned library installs (`tests/e2e/conftest.py`, the `browser` fixture, `chromium.launch()`), and the build number is asserted in the same run on the full Chromium of the same install (the `history_browser` fixture, `channel="chromium"`); both come from `playwright==1.63.0` (`pyproject.toml:14`). R-2 says that, as RN-41 said `tabindex="-1"`, so the sentence claims no more than the tests show. **Addition three, this is a correction and not a re-cut under § 10**, as RN-41's was: no slice's *Reached when*, fence or place moves and no edge in § 7 changes; S-4's *Why here in the order* and § 9 TO-2 state why the confirmation was ordered fourth and stand as written. **Addition four, what stays open downstream and why no item is raised there.** `nfdr.md` RN-15 and ADR-0003's *Dependence* still count the confirmation case open, and both are the Principal Architect's. They read this document (§ 12), and the precedent is NFDR RN-23: when version 6 closed two of the three questions RN-15 counted, the Principal Architect caught it by reading the SDD's change, with no companion item. Until this item is folded the NFDR's sentence is true, and `products/tracker17/docs/architecture_open_issues.md` is live and owed a round that reads the SDD as it then stands, so nothing is appended there. Nothing settled moves: SRS NFR-13, UXD UX-I2, § 4 EX-6, § 9 TO-2 and ADR-0003 stand; the assistive-technology case keeps its VoiceOver settling path. Reasoning: `products/tracker17/docs/trail/sdd/self_answer-11.md` § 2.1.

## 3. Cut calls to confirm — where the slicing could reasonably have gone another way

None.

---

## 4. Disagreements — two seats hold different positions and neither yields

None.

## 5. Raised from downstream — an item from a seat that did not write the SDD

### 5.1 No record names how a move's pages behave in the browser's history
- **Raised by:** PM — 2026-10-20
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_status-moves`
- **What it blocks:** nothing is blocked. The product answers a page that shows a pending
  confirmation with HTTP 202 and every other move page with 200, and sends `Cache-Control: no-store`
  on move interaction and outcome pages; no line of the SDD or an ADR says so or why. A reader
  tracing UX-F4's Back case to its code finds a status code chosen for a browser rule nothing names,
  and could "simplify" it back to 200, which brings a stale confirmation back on Back.
- **Where it shows:** `web/routes.py:L72` (`NOT_STORED`) and `web/routes.py:L322-L333`
  (`Site._pending_status`, `HTTPStatus.ACCEPTED if pending else HTTPStatus.OK`);
  `rg -n 'no-store|Clear-Site-Data|Cache-Control|HTTP 202' docs/SDD.md docs/adr/` prints nothing. The
  record the change asked for, in § 4 runtime conditions or as an ADR, states: 202 for a page that
  actually shows a pending confirmation is the history-admission boundary, so Back to that address
  loads it fresh from the saved status; `no-store` on move interaction and outcome pages protects
  against the HTTP cache, which is a separate purpose; a saved-status GET is still revalidated as
  before; no page script, cookie or session is used (ADR-0003, RT-7); the earlier
  `Clear-Site-Data: "cache"` header is gone because it did not evict the page from the pinned
  browser's history cache; the behaviour depends on Chromium not admitting a non-200 main document to
  its back/forward cache, and the pinned browser's end-to-end run passes on it
  (`tests/e2e/test_moves.py::test_history_matrix_revalidates_current_saved_status` and
  `::test_real_history_traversal_revalidates_the_confirmation`, 67 passed); it serves RT-7, EX-6 and
  UX-F4's second refusal path.
- **If a document has to be written:** an ADR, if the CTO judges the rejected alternatives (a page
  script, a cache-clearing header) worth a decision record; otherwise a § 4 runtime line. Either is
  `product-sdd`'s or `product-architecture`'s to write.
- **Answer:** Confirm the record as the item lists it, with four additions, written in this document; the decision record and the obligation that binds it are the Principal Architect's, raised at `products/tracker17/docs/architecture_open_issues.md` § 2.1 (commit `b52bdedf1`). **§ 4, a new runtime condition, RT-11:** A page that shows a pending confirmation of a move to `cancelled` is answered with HTTP status 202, and every other page a move's interaction or outcome lands on with 200; each of them, the confirmation included, carries `Cache-Control: no-store`. The status is read off the page as built, after outcome precedence, task membership and the workflow's answer against the saved state (`web/routes.py:L323-L333`, `_pending_status`; `L340-L367`, `_move_view`), so an address that asks for a confirmation the page does not show is 200, and one naming a task no task holds is 404. The 202 is the history-admission boundary: the pinned browser admits only a main document answered 200 to its back/forward cache, so a return to a confirmation's address through Back or Forward is loaded afresh from the saved status and, once the task is in a final status, shows UX-F4's no-press refusal and never a stale confirmation. `no-store` serves a separate purpose, keeping the HTTP cache from reusing a move's interaction or outcome page, and does not by itself keep a page out of the browser's history cache. The meaning taken for 202 is the standard's, a request accepted for processing that is not complete, here a move intent awaiting the operator's confirmation; the GET schedules, saves and records nothing (RT-8), and no page script, cookie or session is used (RT-7; ADR-0003, ADR-0006). The earlier `Clear-Site-Data: "cache"` header on the confirming redirect was measured not to evict the page from the pinned browser's history cache and is gone (`tests/integration/test_routes.py:L1057` asserts its absence). Serves RT-7, EX-6 and UX-F4's second refusal path. Tests: `tests/integration/test_routes.py`, `test_pending_confirmation_response_matches_the_rendered_page`, `test_non_confirmation_move_views_keep_their_response_contract` and `test_move_interaction_and_outcome_pages_are_not_stored`; `tests/e2e/test_moves.py`, `test_history_matrix_revalidates_current_saved_status` and `test_real_history_traversal_revalidates_the_confirmation` — 67 passed in a fresh clone at `9b05680c7`, and `git diff --stat 9b05680c7 HEAD -- products/tracker17 ':!products/tracker17/docs'` printed nothing on 2026-10-20, so the code they ran against is the code on `main`. **Addition one, the dependence is exact and was re-read at its source.** Chromium admits a main document to its back/forward cache only when `rfh->last_http_status_code() != net::HTTP_OK` is false — exactly 200, not any 2xx (`content/browser/back_forward_cache/back_forward_cache_impl.cc`, `PopulateReasonsForMainDocument`, read 2026-10-20) — and 202 is not among the status codes the HTTP standard lets a cache store heuristically (RFC 9110 § 15.1 lists 200, 203, 204, 206, 300, 301, 308, 404, 405, 410, 414 and 501), so the HTTP cache cannot keep the confirmation even without the header, and `no-store` is what protects the 200 outcome pages. Chrome's own documentation says a `no-store` page can be restored from the history cache and is evicted on a cookie change (developer.chrome.com, "bfcache-ccns", read 2026-10-20), which is why the header alone was not enough. RT-11 states the rule as the pinned browser's, as RT-9 and § 11 R-2 do for `autofocus`, and SRS NFR-13 bounds the product to Chromium-based browsers. **Addition two, where the decision is surfaced for the Principal Architect.** § 12 surfaces an architecturally significant decision in § 2, § 9 and the Review Notes and nowhere else, so § 9 gains TO-8: the design gives up the plain reading of a status line, a 202 on a GET that completes nothing — *buys* a confirmation that cannot be restored from the history cache without a script, a cookie or a session (TO-2, TO-7) and a return through Back that shows the saved status — *undoing it costs* one line in `web` and the two history tests, after which Back after confirming shows a stale confirmation on the pinned browser, which `test_real_history_traversal_revalidates_the_confirmation` failed on before the change. § 11 gains R-12: a browser release that admits a non-200 main document to its history cache — *shows up as* the two end-to-end tests above failing, a return to a confirmation's address restored instead of loaded — *response* both run on every slice (TS-1), and the fallback is TO-2's reversal confined to `web`, as R-2's. **Addition three, RT-8's last sentence is scoped.** "A reload of that page, or a return to it through back, shows the same line at the same place" holds for a page whose address names a finished outcome, a completion line, a refusal or a failure; a page whose address asks for a pending step is built from the saved state on every load (RT-7) and shows what the state now allows, which RT-11 and UX-F4 state. **Addition four, one case named and left where it occurs.** A confirmation address whose task another tab has deleted answers the not-found page, 404, with no `no-store` (`web/routes.py:L303-L304`, `L453-L454`); the same exact-200 rule keeps it out of the history cache, and whether the HTTP cache may keep a 404 heuristically is `delete-and-rename`'s, where a task first becomes deletable. Nothing settled moves: SRS NFR-3, NFR-4 and NFR-13, UXD § 4 ("the browser's back, forward and reload buttons work on every one"), UX-F4 and UX-I3, § 4 EX-2, EX-6 and SEC-3 and § 9 TO-2 stand; no slice's *Reached when*, fence or place moves and no edge in § 7 changes, so this is an added condition and not a re-cut under § 10. Reasoning: `products/tracker17/docs/trail/sdd/self_answer-10.md` § 5.1.

### 5.2 § 6 S-4's bar has an out-of-date move offer a reload; UX-I3 now says it offers none
- **Raised by:** PM — 2026-10-20
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_status-moves`
- **What it blocks:** nothing yet. The slice's last unwalked stations are cut against S-4's
  *Reached when*, and a station built to it would add a reload offer UX-I3 forbids.
- **Where it shows:** `SDD.md:L832` (§ 6 S-4, *Reached when*) — "A move made from a page that is out
  of date is refused, says the status has changed, and offers a reload (UX-I3)". `UXD.md:L384-L387`
  (UX-I3, version 8) — "The overtaken move names the moves the page now shows, or none for a final
  status … Each lands on a page built after the refusal, so none of them offers a reload", and
  `UXD.md:L175-L181` (UX-F4) says the same. The change asked: S-4's clause says the refusal says the
  status has changed and names the moves the page now shows, or none, with no reload. The same bar
  could also name UX-I3's second case, a refusal reached by an address with no press, which S-4 does
  not mention.
- **If a document has to be written:** none. `SDD.md` changes through `product-sdd`.
- **Answer:** Confirm the change as asked, with three additions. **§ 6 S-4, *Reached when*, behaviour**, replacing "A move made from a page that is out of date is refused, says the status has changed, and offers a reload (UX-I3)": A move pressed after another tab moved the task is refused, says the task's status has changed and names the moves the page now shows, or none for a final status, and offers no reload, because the list or the task's page it lands on is built after the refusal and already shows the current status and the moves it allows (UXD UX-I3, UX-F4). **Addition one, the second case, in the same clause:** a move refusal reached by an address and no press — the address that shows the confirmation of a move to `cancelled`, or the one that backs out of it, opened again by a reload, by Back or from a bookmark once the task is in `done` or `cancelled`, on a project's Tasks view and on the task's page alike — shows where the confirmation would have been, beside the task's status, says what is true now, names no action and offers no reload (UXD UX-F4, UX-I3). Its occurrence is the one § 5.1 of this file cites: `web/routes.py:L340-L367` answers the address from the saved state and `tests/e2e/test_moves.py::test_history_matrix_revalidates_current_saved_status` shows the refusal at the status; the words the page carries today ("the move you pressed", `web/pages.py:L758-L761`) are CONTENT RN-26's finding and seed item 3's, not this document's. **Addition two, EX-4.** § 4 EX-4 gains one sentence: a refusal reached by an address and no control sits beside the task's status (UXD UX-I3), so a reader building the no-press case does not look for a control that was not used. **Addition three, this is an upstream change, so § 10 records it.** The UXD moved after version 10 read it at version 6: version 7 (commit `f90b692f9`) keeps the no-press refusal as a case of its own (UXD RN-33), and version 8 (`afffd0d5e`) has no refusal offer a reload on a page built after it (UXD RN-34). RC-4 records it with the CDO's ground moved, retains every slice, slug, *Delivers*, fence, order and § 7 edge, and changes S-4's behaviour line and EX-4; the header's *Inputs read* names version 8. The command half stands: "the out-of-date move of AC-12" still names the test, and SRS AC-12 asks only that the refusal shows its reason and the saved data is unchanged. S-2's assignee refused "as out of date" states no reload and does not move; whether the product's two assignee refusal lines still offer one is a change to those strings (UXD RN-34), not to this document. Reasoning: `products/tracker17/docs/trail/sdd/self_answer-10.md` § 5.2.
