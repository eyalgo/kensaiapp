# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-20
- **Sources re-read:** three, each at the source on 2026-10-20. Chromium,
  `content/browser/back_forward_cache/back_forward_cache_impl.cc`, `PopulateReasonsForMainDocument`:
  "Only store documents that have successful http status code." then
  `if (rfh->last_http_status_code() != net::HTTP_OK)` → `kHTTPStatusNotOK` — exactly 200 is admitted,
  not any 2xx. RFC 9110 § 15.3.3: 202 "indicates that the request has been accepted for processing,
  but the processing has not been completed", "intentionally noncommittal", no sentence on caching;
  § 15.1's heuristically cacheable codes are "200, 203, 204, 206, 300, 301, 308, 404, 405, 410, 414,
  and 501" — 202 is not among them. developer.chrome.com, "bfcache-ccns": a `Cache-Control: no-store`
  page can be restored from the back/forward cache (rolled out to all users by April 2025), "Chrome
  will evict a page from the bfcache on changes to cookies, or other authorization methods", and its
  timeout there is 3 minutes. `web.dev/articles/bfcache` was read too and names no status-code rule.
  Read in-repo besides `SDD.md` whole and the companion: `UXD.md` § 4, UX-F4, UX-I3, UX-I9, RN-32 to
  RN-34; `SRS.md` NFR-3, NFR-4, NFR-13, FR-18, FR-19, AC-12; `adr/README.md`, ADR-0003, ADR-0006;
  `nfdr.md` QC-7, QC-8, QC-12, QC-34, RN-15, RN-41, § 4; `fdr.md` R-106; `CONTENT.md` RN-26;
  `web/routes.py:60-80, 118-119, 300-392, 440-492, 713-760`; `web/pages.py:740-770`;
  `tests/integration/test_routes.py:900-1080`; `tests/e2e/test_moves.py:1-30, 174-215, 321-330,
  391-605`; the change record `system/projects/tracker17/journey/tobiishi/trail/2026-10-20_history-after-confirm/change_design.md`
  § 1 and § *Records this change makes false*; the seed `2026-10-07_status-moves`, its refine report
  `2026-10-20_history-after-confirm_report.md` and the open station `2026-10-19_cancel-confirmation.md`;
  `trail/sdd/self_answer-9.md` and `cycle-7.md`. Measured: `git diff --stat 9b05680c7 HEAD --
  products/tracker17 ':!products/tracker17/docs'` printed nothing at `ca2f9e98a`; `grep -rn -i
  'no-store\|Clear-Site-Data\|Cache-Control\|202\|history cache' docs/SDD.md docs/adr/ docs/nfdr.md
  docs/fdr.md` printed nothing. No suite was run: the items are about what the code and the records
  say, the refine recorded 67 end-to-end and 1250 suite passes in a fresh clone at `9b05680c7`, no
  code moved since, and this round changes no code.

The companion held two open items, §§ 5.1 and 5.2, both `Seat: cto`, and the invocation listed none,
so this run worked both, in order. Neither widens the document without an occurrence: 5.1 asks a
record for a mechanism the product runs today, and 5.2 corrects a statement found false against the
UXD. Neither split: each is one question with one seat.

## Items worked

### 5.1 — No record names how a move's pages behave in the browser's history

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** confirmed with addition
- **Why:** The item leaves the home open ("an ADR, if the CTO judges the rejected alternatives worth
  a decision record; otherwise a § 4 runtime line") and hands the record's content as a list, so I
  read the list as the draft and the home as the question. The draft holds and is taken; the home is
  both, and four things are added.

  *Seat (check 1).* The edit lands in § 4, a CTO row in § *Who decides what*, and binds this
  document's agreement with the product; nothing it decides is a person's, a party's or a risk the
  owner carries, and I can name no ground I cannot see. Mine. The ADR half lands in `adr/` and
  `nfdr.md`, the Principal Architect's: the loader puts the SDD run's job at surfacing and theirs at
  recording, and § 12 says the same. So the SDD states and surfaces the decision (RT-11, TO-8, R-12,
  a Review Note), and the record is raised on `architecture_open_issues.md` § 2.1, committed at
  `b52bdedf1` before this slot was written. I was unsure whether to open that companion at all — the
  Principal Architect reads each SDD version's change (NFDR RN-30, RN-41) and would meet TO-8 on the
  next round — and raised it with the doubt stated in the item: the product has run on the decision
  since `9b05680c7`, no obligation a `development-design` review checks names it, and nothing
  schedules that round; a double is one item folded twice, a lost record is a 202 a reader sets back
  to 200.

  *The draft holds (check 2).* Every citation is as stated: `NOT_STORED` at `web/routes.py:72`,
  `_pending_status` at `:323-333` returning `ACCEPTED` only when the resolved interaction is a shown
  confirmation, `_stored_as_asked` sending `no-store` on every page whose address carries
  `move_task`, `_move_view` reading the saved state first; the integration matrix asserts exactly
  202 on a rendered confirmation and 200 or 404 on twenty other addresses, `no-store` on seven move
  pages and no `Clear-Site-Data` on any move response; the two end-to-end tests do what their
  docstrings say. The draft's one imprecision is the item's own hedge "the behaviour depends on
  Chromium not admitting a non-200 main document", which is right and was not a hedge: the source
  reads exactly 200. **Addition one** states that, with the RFC's heuristic list, which shows why
  `no-store` is for the 200 outcome pages and the 202 needs no header to stay out of the HTTP cache,
  and Chrome's own page on why `no-store` alone is no history-cache bar. I judged the ADR worth
  writing by the marks the nine records carry: measured rejected alternatives, a vendor dependence
  with a regression signal, and a shape a reader would undo. **Addition two** is the consequence of
  that judgment inside this document: § 12 names three surfacing places and no fourth, and a
  decision stated only in § 4 is surfaced in none of them, so § 9 gains TO-8 and § 11 gains R-12 in
  the form R-2 uses for the same browser. **Addition three** scopes RT-8's last sentence, which a
  reader of the history tests would otherwise find false: a confirmation's address names a pending
  step, and what a return to it shows is RT-7 applied. **Addition four** names the case the answer
  does not reach.

  *Nothing settled moves (check 3).* SRS NFR-3's "checked against the saved data at the moment it
  is applied" is what the fresh load serves; NFR-4 and SEC-2 are untouched, a GET still changes
  nothing (RT-8, FDR R-106, QC-7); NFR-13 bounds the browser rule to Chromium-based browsers, where
  the source was read. UXD § 4's "back, forward and reload buttons work on every one" holds — they
  work, and show the saved status. ADR-0003 and ADR-0006 stand: no script, no cookie, no session,
  every submission answered by an address; ADR-0006's Consequences gloss "shows the same page" is
  read as its Decision reads it, a function of state and address, and is not raised. My answer to
  5.2 was decided after this one and rests on the same saved-state read; the two agree. The record's
  content already in the change design (§ *Record owed — CP-351*) is what the item carried, and the
  answer adds to it rather than departing from it.

  *Failure paths (check 4).* *Empty*: a tracker with one task — the confirmation renders and is 202;
  the control row the matrix adds only proves the other row keeps its buttons. *Absent*: the task
  gone — 404, named in addition four and left to `delete-and-rename`. *Stale*: the case itself; the
  matrix covers this tab and another tab, done and cancelled, before and after leaving. *Concurrent*:
  § 4 RT-6 applies one request at a time, and a confirming submission after another tab moved the
  task is checked against the saved state and refused (NFR-3; `_move_task`'s `MoveNotAllowed`).
  *Refused*: a refusal page is 200 with `no-store`. *Failed*: a save failure on confirming redirects
  to a `move_failed` page, 200 with `no-store`. *The browser*: a release that changes the exact-200
  rule is R-12, and the operator's current Chrome against the pinned Chromium is the bound R-2
  already states. I was close to a plain *confirmed* and the source read tipped it: the item said
  "non-200" where the code says `!= HTTP_OK`, and a record that says "non-200" invites a 204 or a
  201 later as "also fine", which the rule would reject too — right by accident is the hole addition
  one closes.

### 5.2 — § 6 S-4's bar has an out-of-date move offer a reload; UX-I3 now says it offers none

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** confirmed with addition
- **Why:** The item hands the clause ("says the status has changed and names the moves the page now
  shows, or none, with no reload") and offers the second case as a could; I read the clause as the
  draft and took it, took the second case, and added two things. One question, one seat: both cases
  are UX-F4's two ways a move refusal arises, restated in a line whose source is the UXD.

  *Seat (check 1).* The edit lands in S-4's behaviour line and § 4 EX-4, CDO rows in § *Who decides
  what* — but a row the CDO decides through the UXD, which is the CDO's own document and has already
  decided it: § 4's preamble says "The UXD entry is the source, and where the two differ the UXD is
  right", and RN-31 folded UXD version 4 into three behaviour lines without an item for the same
  reason. The answer binds only this document's agreement with its source. Mine, in the owner's seat,
  with the CDO's call already made at UXD RN-33 and RN-34.

  *The draft holds (check 2).* `SDD.md:832` reads "offers a reload (UX-I3)"; UXD version 8's UX-I3
  reads "Each lands on a page built after the refusal, so none of them offers a reload", and UX-F4's
  first failure case says the same with the reason. The draft's clause is UX-F4's wording and is
  taken. **The second case** is taken rather than answered "not until it occurs": the rule for a
  raised-from-downstream item is that an occurrence is read from the item, and this item cites the
  UXD, not the product — but the occurrence is on this same companion, cited by the same raiser in
  § 5.1 for the same page: `_move_view` answers the confirmation's address from the saved state and
  the history matrix shows the refusal beside the status. I did not search the product for it beyond
  what the companion named; I say so because the bar is strict and the call was close. What tipped
  it: the document's own rule makes the UXD right where they differ, UX-F4 now states the case, and
  seed item 3 is already re-aimed to build its words — a bar that omits it would let the slice read
  reached while its last station builds a case the bar never named. **Addition one** is that case.
  **Addition two** is EX-4: it restates UX-I3's first sentence, "beside the control that was used",
  and the no-press refusal used none; the UXD resolves that to the task's status, and EX-4 should say
  so where a builder reads it. **Addition three** is § 10: the SDD's own rule writes a re-cut record
  when the UXD changed upstream, RC-2 did so for version 4, and RN-48's judgment that version 6 moved
  no line does not reach versions 7 and 8, which move this one.

  *Nothing settled moves (check 3).* SRS NFR-3's "The operator reloads the page to see the current
  state" is about seeing another tab's change (UX-I9), not about a refusal offering one, and the
  refusal still lands on a page built after it; AC-12 asks reason and unchanged data, which stand;
  FR-18 and FR-19 are untouched. The CONTENT refusal line on `web/pages.py:758-761` offers no reload
  today, and its "the move you pressed" is RN-26's finding carried by seed item 3, not this
  document's. S-2's assignee line states no reload and is not touched. My answer to 5.1 states the
  same saved-state read for the same address; the two were decided in that order and agree.

  *Failure paths (check 4).* *Empty*: a task with no allowed move left — the refusal names none,
  which the clause says. *Absent*: the task deleted — UX-S10 and EX-6's "shows UX-S10 when its
  target is gone", unchanged. *Stale*: the case itself, both ways in. *Concurrent*: a press and
  another tab's move in the same moment are serialized by RT-6, and whichever is second is refused.
  *Refused*: the refusal is the subject; it changes nothing (AC-12). *Failed*: a failed move is
  UX-I5's line, not this clause. I was close to answering the second case "not until it occurs";
  the paragraph above says what moved me and what a reader who disagrees would hold against it.

## Left for the owner

None this run.

## Skipped

None this run.

## Raised on this document

### 2.1 — § 11 R-2 and the first Open Question still call the confirmation case unverified; its tests have run and passed

- **What the document is owed:** R-2's "Two cases stay unverified. The confirmation case …" and the
  first item of § Open Questions become a verified case naming its four tests, as RN-36 and RN-41 did
  for the other two.
- **Why it is worth a cycle:** the first ground, *a fact in it is now false*. The tests R-2 names as
  what settles the case exist in `tests/e2e/test_moves.py` (lines 174, 208, 321 and 606) and passed,
  67 of 67, in a fresh clone at `9b05680c7` (the refine report of `2026-10-20_history-after-confirm`,
  "Considered, not moved", first row), and no product code moved since. The sentence sends a reader
  to run a check that has run. The slot is left at its placeholder; the fold decides.

## Companions opened

- **products/tracker17/docs/architecture_open_issues.md** — **opened** — companion to `adr/` and
  `nfdr.md`, landed in commit `b52bdedf1`

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
- **products/tracker17/docs/architecture_open_issues.md** — `<CORE>/launchers/companion-self-answer/launcher.sh tracker17 architecture`
