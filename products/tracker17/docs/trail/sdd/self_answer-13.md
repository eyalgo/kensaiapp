# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-28
- **Sources re-read:** RFC 9110, HTTP Semantics (https://www.rfc-editor.org/rfc/rfc9110.html, read
  2026-10-28): § 15.5.5, "A 404 response is heuristically cacheable; i.e., unless otherwise
  indicated by the method definition or explicit cache controls"; § 15.1 lists the heuristically
  cacheable codes and says all others are not; § 15.3.3, "The 202 (Accepted) status code indicates
  that the request has been accepted for processing, but the processing has not been completed. The
  request might or might not eventually be acted upon, as it might be disallowed when processing
  actually takes place." RFC 9111, HTTP Caching (https://www.rfc-editor.org/rfc/rfc9111.html, read
  2026-10-28): § 4.2.2, a cache "MAY assign a heuristic expiration time when an explicit time is not
  specified", limited to heuristically cacheable status codes; § 3 and § 5.2.2.5, a cache "MUST NOT
  store any part of either the immediate request or the response" under `no-store`. Chromium,
  `net/http/http_response_headers.cc`, `GetFreshnessLifetimes`
  (https://raw.githubusercontent.com/chromium/chromium/main/net/http/http_response_headers.cc, read
  2026-10-28): the `Last-Modified` 10% heuristic runs only for `HTTP_OK`,
  `HTTP_NON_AUTHORITATIVE_INFORMATION` and `HTTP_PARTIAL_CONTENT` without `must-revalidate`;
  `HTTP_MULTIPLE_CHOICES`, `HTTP_MOVED_PERMANENTLY`, `HTTP_PERMANENT_REDIRECT` and `HTTP_GONE` get
  `base::TimeDelta::Max()`; every other status, 404 among them, gets "0 seconds, in accordance with
  common browser behaviour". The Chromium file read is `main`, not the pinned build's tag; the rule
  is old and the answer says so by stating it as the pinned browser's, as RT-11 does. Everything
  else is this repository's, read on disk: `SDD.md` whole, and § 4 RT-7, RT-8, RT-11, EX-4, EX-6,
  EX-13; § 6 S-7; § 7's `status-moves → delete-and-rename` edge; § 9 TO-8; § 11 R-12; § 12; RN-49;
  § Open Questions; the companion whole; `adr/0010-*.md` whole; `adr/README.md`; `nfdr.md` header
  and QC-63; SRS FR-17, NFR-3, NFR-13, DR-2; UXD § 4 ("Every page has its own address"), UX-F9,
  UX-F10, UX-I2, UX-S10; `web/routes.py:L79-L85`, `L317-L322`, `L370-L404` (`_task_page`),
  `L408-L416` (`_delete_area`), `L419-L430` (`_pending_status`), `L433-L438` (`_stored_as_asked`),
  `L554-L590` (`_project_page`), `L966-L999` (`_delete_task`); `web/pages.py:L783-L830`;
  `web/listener.py:L43-L50`; `tests/integration/test_delete_routes.py:L286-L306`, `L368-L380`,
  `L432-L449`, `L451-L478`; `tests/integration/test_routes.py:L355-L372`, `L1040-L1054`;
  `tests/e2e/test_delete_task.py:L151-L177`; `tests/e2e/test_moves.py:L430-L452`; the seed
  `2026-10-11_delete-and-rename`, its refine report and recommendations of 2026-10-28, and the
  sealed unit's `change_design.md` (§ HTTP policy, § Architect Review Notes "HTTP cache choice") and
  `flow_findings/development-design.md` — journey material read as input, cited nowhere in the
  answer. No suite was run: every claim about the product rests on code and tests read at `HEAD`,
  and this round changes no code.

The companion held one open item, § 5.1, `Seat: cto`, raised by the PM's `shukuba-refine` run after
the `delete-a-task` unit sealed; §§ 1 to 4 read None. The invocation listed no items, so this run
worked the one open item. It did not split: the item's clause about ADR-0010 and QC-63 is a
consequence of the one rule, carried to the records' own companion under check 1's second outcome,
not a second question with its own answer.

## Items worked

### 5.1 — No section states how a deletion's pages are answered, and S-7 says its confirmations behave as the move's

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** answered
- **Why:** The item carries no draft — it names two readings and leans to neither — so it is
  answered from scratch. It is a correction, not a widening: RT-11 itself hands this slice a
  question ("whether the HTTP cache may keep a 404 heuristically is `delete-and-rename`'s"), and the
  occurrence is on disk — the product answers a deletion's pages today and no settled sentence says
  how. The verdict is **answered**, and the rule is one boundary for every pending confirmation.

  *Seat (check 1).* The edit lands in § 4 RT-11 and S-7's *Command* half, both CTO rows of § *Who
  decides what*. It binds the document's agreement with the product and with its own TO-8 and
  EX-6, commits no person, party, money or risk, and I can name no ground I cannot see. Mine. The
  CDO's rows are not touched: S-7's *Behaviour* sentence stands as written, and the answer says why
  it needs no scoping — it names what the operator sees, EX-6's confirmation, and the HTTP status
  is not something the operator sees. The item's last clause, whether ADR-0010 or QC-63 owes a
  line, lands in `adr/` and `nfdr.md`, the Principal Architect's; it is carried there as
  `architecture_open_issues.md` § 2.1 (commit `5585e0b11`), opened on this run's judgment with the
  lean stated, as the cycle-8 answer did for RT-11 itself. Not a split: that clause has no answer
  of its own until the SDD's rule exists, and once it exists the clause is the rule's consequence
  on another document — check 1's second outcome, with the slot here saying where it is carried.

  *The question (check 2).* It is the right question and it hides one more, which the answer takes
  in the same slot: not only "what rule" but "200 or 202 for a deletion's confirmation", which the
  item names only as a reading of S-7. I was close to confirming the product as built — 200 with
  `no-store` on the confirmation, as the sealed unit's design chose, with S-7's sentence scoped to
  the operator-visible confirmation. What tipped it to 202 is the document itself: § 9 TO-8 states
  the boundary for "a page that shows a pending confirmation", with no move in its words, so the
  SDD already says it and the product contradicts the SDD's own trade-off; and § 7's edge reuses
  the `status-moves` confirmation "as built and tested", whose tests are the history tests. The
  design's reason for 200 covered only the 404, which its own audit found, and that 404 reasoning
  is taken whole into (e). The other way — narrowing TO-8 to moves and accepting a stale deletion
  confirmation on Back — would have been an answer too; it loses to one boundary because the
  benefit is identical (a fresh load after Back shows UX-S10's page, which is what a deleted
  address is supposed to show) and the price is the one line TO-8 already prices, while two
  boundaries for one mechanism is the shape that reopens with the project deletion.

  *Nothing settled moves (check 3), and the sources were re-read.* The 404's heuristic
  cacheability rests on RFC 9110 § 15.5.5 and RFC 9111 § 4.2.2, re-read at the source (above); the
  pinned browser's freshness rule rests on Chromium's `GetFreshnessLifetimes`, re-read at the
  source; the listener's headers rest on `web/listener.py` (`send_response_only`, which writes no
  `Date` or `Server`, unlike `send_response`). The 202's meaning rests on RFC 9110 § 15.3.3, whose
  second sentence — "might be disallowed when processing actually takes place" — describes the
  deleted-target refusal exactly. SRS NFR-3 holds: a page restored from history shows the data as it
  stood when loaded, and the answer does not claim otherwise; it chooses a fresh load for the one
  page that invites an action. NFR-13 bounds the rule to Chromium, as RT-11 and R-12 already do.
  UXD UX-I2 says nothing about history and is not widened; UX-S10 and EX-13 are what the fresh
  load shows. ADR-0008 and SRS DR-2 ("never reused, even after the task is deleted") are what make a
  kept 404 safe. RT-8's "the GET schedules, saves and records nothing" holds for the deletion's
  confirmation (`_delete_task` saves nothing on the first press; `SAVES_FOR` counts 0). My own
  earlier answers agree: `self_answer-10.md` § 5.1 chose the 202 for the confirmation and named the
  deleted-task 404 as this slice's; `self_answer-12.md` § 5.1's reading of RT-8 is untouched. ADR-0010
  and QC-63 are downstream and do not bind this document (§ 12: § 4 wins and the entry is
  re-derived), so their move-only wording is a consequence raised, not a contradiction answered.
  No slice's *Reached when* moves except S-7's *Command* half, which gains one clause; no fence,
  place or § 7 edge changes, so this is an added condition and not a re-cut under § 10.

  *Failure paths (check 4).* *Empty*: deleting a project's last task lands on the first-task
  invitation with the deletion line (`test_last_task_delete_keeps_the_first_task_invitation`), 200
  with `no-store` under (b). *Absent*: the save fails — `?delete_failed`, 200 with `no-store`, the
  task still held (`test_failed_confirm_keeps_saved_bytes_and_current_pages`); the Chromium source
  read is `main` rather than the pinned tag, named above and stated as the pinned browser's rule.
  *Stale*: a bookmark or a typed `?delete_confirm` after the deletion — 404 under (d), existence
  winning over presentation (`test_missing_task_wins_over_every_query`); a confirmation restored
  from history is the case the 202 removes. *Concurrent*: tab A holds the confirmation, tab B
  deletes; tab A's confirm, back-out or reload lands on the not-found page and saves nothing
  (`assert_refused_as_missing`, `test_deleted_target_refuses_delete_confirm_without_saving`, twice
  in a row). *Refused*: a cross-origin or mis-hosted POST is 403 with an empty body, saving nothing
  (`test_live_delete_views_have_their_response_policy`). *The project deletion*, not yet built: the
  same five under the same rule — `/projects/P?delete_confirm` 202, the landing on Projects 200
  with `no-store`, `/projects/P` and each of its tasks' addresses 404 bare, their identities never
  reissued. Named and not covered: a 404 for an identity not yet issued, typed by hand, kept by a
  cache outside NFR-13's bound; and the layer-5 history test for a deletion, which does not exist
  yet (`test_completion_survives_actual_reload_back_and_forward` never goes Back to the
  confirmation) and is named in the architecture item's *verified by*.

  *Noticed, not raised.* The document's header reads NFDR at version 15 and ADR-0001 to ADR-0010,
  and § 12 counts ten records; `adr/README.md` lists ADR-0011 (2026-10-27) and `nfdr.md` is at
  version 16. Both are the producing run's own lines about its inputs, rewritten by the fold this
  answer is owed, as the previous report judged the same lines; not worth a cycle of their own.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

- **products/tracker17/docs/architecture_open_issues.md** — **opened** — companion to `adr/` and
  `nfdr.md`, landed in commit `5585e0b11`

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
- **products/tracker17/docs/architecture_open_issues.md** — `<CORE>/launchers/companion-self-answer/launcher.sh tracker17 architecture`
