# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-21
- **Sources re-read:** three, each read at its source on 2026-10-21.
  - Chromium, `content/browser/back_forward_cache/back_forward_cache_impl.cc` on `main`
    (chromium.googlesource.com). In `PopulateReasonsForMainDocument` it reads "Only store documents
    that have successful http status code", then `if (rfh->last_http_status_code() != net::HTTP_OK)`
    → `kHTTPStatusNotOK`. That is exactly 200 and not any 2xx, as the item states.
  - RFC 9110 § 15.1 (rfc-editor.org). The heuristically cacheable codes are "200, 203, 204, 206,
    300, 301, 308, 404, 405, 410, 414, and 501", and "all other status codes are not heuristically
    cacheable". 202 is not among them. § 15.3.3 defines 202 as "accepted for processing, but the
    processing has not been completed".
  - developer.chrome.com, "bfcache-ccns". Chrome allows bfcache for `Cache-Control: no-store` pages,
    rolled out to 100% of users over March and April 2025, and evicts them on a cookie change. So
    `no-store` alone is no bar, as the item states.

## Items worked

### 2.1 — Record the history-admission boundary — 202 for a page that shows a pending confirmation, `no-store` on every move page — as an ADR, and bind it with an NFDR obligation

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The record and the obligation are both owed. I confirmed the draft's conclusion and added
  three things it lacked. One of them is a reason the draft never gave and that the confirmation
  rests on.

  *Check 1, the seat.* The change lands in `adr/` and `nfdr.md`, the documents this companion
  belongs to. It binds only their consistency with the settled SDD, so it is this seat's to answer.
  The decision itself was the CTO's, settled in SDD version 11 (`9c7db2266`): § 4 RT-11, § 9 TO-8
  and § 11 R-12. The draft wanted to wait until `product-sdd` folded `SDD_open_issues.md` § 5.1.
  That fold has landed (`SDD.md:5`, `:386`, `:1158`, `:1423`).

  *Check 2, the draft.* The draft argues from significance: alternatives that were measured and
  ruled out, a dependence on one vendor's rule, and a 202 a reader would "fix" back to 200. It says
  nothing on reversibility, which is the gate this NFDR has used to refuse records before. RN-13
  refused one to SEC-2 and SEC-3 because each "lives in one function each in `web`". RN-22 refused
  one to QC-62 because "dropping a gate is a one-line change". SDD TO-8 prices undoing this decision
  at "one line in `web` and the two history tests". Read alone, the draft's record fails the gate
  its own document applies. It passes for a reason the draft does not give. Undoing the line is
  cheap. Undoing the decision is not, because nothing else is left to keep UXD UX-F4's promise: a
  return through Back or Forward loads the saved status afresh. A page script would need a record
  superseding ADR-0003. A cookie or session would need a record superseding ADR-0006.
  `Clear-Site-Data: "cache"` was measured not to evict the page, and `no-store` is documented as no
  bar. Reversing the 202 therefore reverses another Accepted record or gives up the UXD promise.
  That is a hard reversal. The loader's *Dependence* lens also asks for the record on its own: the
  decision stays decided only as long as Chromium keeps its exact-200 rule. So addition one is
  that the record states this reversal cost, and a Review Note says why it passes where RN-13's
  cases did not. Without that, the new record and RN-13 read as contradicting each other.

  *Check 3, the settled record.* Two things the draft says do not survive it. First, it places the
  obligation "under § 2". § 2's preamble says "every entry below names the one it guards", meaning
  trust boundaries B-1 to B-4. This obligation protects the freshness of a move page, and no
  boundary covers that. Its neighbours are QC-7 (only submissions change state, answered by a
  redirect) and QC-8 (no cookie), both in § 1.1 and both tracing to ADR-0006. So addition two is
  that the entry goes in § 1.1 as QC-63, the next free ID (`grep -c QC-63 nfdr.md` gives 0; IDs are
  never renumbered, so it sits out of numeric order there). Its § 10 row runs `pytest tests/` at
  layer 3 and `pytest tests/e2e/` at layer 5, over the tree, gated at the suite. Second, the draft's
  QC claims "no response carries `Clear-Site-Data`". Its named tests do not check that, and the one
  test that does, `test_move_responses_do_not_clear_site_data`
  (`tests/integration/test_routes.py:L1005-L1058`), is missing from the draft's list. It covers
  move submissions (success, confirming, refused, invalid, missing task, failed save, rejected
  origin) and the confirmation and back-out GETs. It does not cover every response. So part of
  addition three is that the clause covers a move's responses and the tail names that test. I
  checked every locator the draft gives at `HEAD`. `web/routes.py` `_pending_status` is at
  L323-L333, and `_stored_as_asked` sets `no-store` when `move_task` is in the query. All five tests
  the draft names exist. `git diff --stat 9b05680c7 HEAD -- products/tracker17
  ':!products/tracker17/docs'` lists only `README.md`. I ran no suite.

  *Check 4, the failure paths.* *Absent*: a confirmation address whose task another tab deleted
  answers the not-found page, 404, with no `no-store` (SDD RT-11). The test's 404 rows at
  `test_routes.py:L950-L951` assert the body and no header. The drafted QC's "every other move
  interaction or outcome page 200, each with `no-store`" could be read to cover that page, and the
  code would then break it. So the rest of addition three is that the QC excludes it, as RT-11
  does. *Stale*: the two end-to-end tests prove the pinned build, Chromium 153.0.8010.12 under
  `playwright==1.63.0`. The operator runs current stable Chrome (SRS NFR-13), which can change the
  rule before the pin moves. SDD R-12 states that bound, and the draft's *Dependence* drops it
  ("A release that changes the rule shows up as the two end-to-end tests below failing"). The record
  keeps it. *Concurrent*: another tab confirms first and this tab goes Back. That is a fresh load
  that meets the no-press refusal, which `test_history_matrix_revalidates_current_saved_status`
  drives. *Empty* and *refused* reach nothing new: no task means no confirmation page, and a refused
  move answers 200 with `no-store`, which `NOT_STORED_ADDRESSES` lists.

  *What would have tipped it.* I was close to *overridden* on the placement alone. It stays a
  confirmation because the draft's decision, alternatives, dependence and tests all hold. What
  moves is where the entry sits and how far two of its clauses reach.

## Left for the owner

None this run.

## Skipped

None this run.

## Raised on this document

### 2.2 — RN-15 and RN-42 still call the EX-6 confirmation open, and SDD version 11 counts it verified

- **What the document is owed:** RN-15 restated so that the EX-6 confirmation is verified, by the
  four `tests/e2e/test_moves.py` tests SDD § 11 R-2 names, tied to `9b05680c7`, and so that
  assistive-technology speech for EX-14 is the one case still open. A new Review Note records the
  change. RN-42 and ADR-0003 are not edited.
- **Why it is worth a cycle:** *A fact in it is now false*, and *something upstream moved and it
  has not seen it* (`prompts/rich.md` § The items are not the whole of what a document is owed).
  `nfdr.md:746` reads "What stays open is two cases. The first is the confirmation of SDD § 4 EX-6",
  and `nfdr.md:1161-1162` reads "both stay: the EX-6 confirmation, which SDD § 6 `status-moves`
  settles". SDD version 11 (`9c7db2266`) closed that case. `SDD.md:1325-1333` names the four tests
  and their pass in a fresh clone at `9b05680c7`. `SDD.md:2332` § Open Questions holds only the
  VoiceOver case. A review reaching RN-15 through ADR-0003's `## Binds` and QC-34 is told a verified
  case is open. Item 2.1 already owes `product-architecture` a fold, so this rides the same round.
  It is raised as its own item and not left to that fold because no answer here would carry it, and
  a fold reads the items it is given.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
