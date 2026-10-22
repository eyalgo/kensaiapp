# Architecture open issues — tracker17

> Companion to `adr/` and `nfdr.md`. The Principal Architect authored both records
> non-interactively; this file holds what the run could not settle from its inputs — the SRS, the SDD
> and the FDR.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-architecture`. It folds your answers into the records and drops the resolved items.
> When nothing is left open, `product-architecture` **deletes this file**: no file = the records are
> done.
>
> Your answers are never thrown away. Each time the Principal Architect folds them in, it first copies
> this file whole to `docs/trail/architecture/` — so what you decided, and why, stays readable and
> citable for good.
>
> **§ 3 is raised, not asked.** These records bind every later change, so the seats that live under
> them find gaps the authoring run could not. § 3 is where such a seat says so, against both records
> — an ADR's binding and an NFDR obligation reach the same file.

> **No producing run wrote this file.** A `companion-self-answer` run opened it on 2026-10-20, in the
> CTO's seat, while answering `products/tracker17/docs/SDD_open_issues.md` § 5.1, to carry item
> § 2.1. `product-architecture` has no record of writing it. It exists because the product answers a
> page that shows a pending confirmation with HTTP 202 and sends `Cache-Control: no-store` on every
> move interaction and outcome page, on a rule of the pinned browser, and no record in `adr/` and no
> obligation in `nfdr.md` names either (`grep -rn 'no-store\|Clear-Site-Data\|Cache-Control\|202'
> docs/adr/ docs/nfdr.md` printed nothing on 2026-10-20). The SDD states the condition on its fold of
> that item; the decision record and the obligation that binds it are these records' to write.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

### 2.1 Record the history-admission boundary — 202 for a page that shows a pending confirmation, `no-store` on every move page — as an ADR, and bind it with an NFDR obligation
- **Lands in:** both — a new `adr/0010-<slug>.md` and an `nfdr.md` QC-n under § 2, with a row in § 10.
- **Drafted into the records:** nothing — the run that raised this writes no record. What it hands
  the Principal Architect, to write after `product-sdd` folds `SDD_open_issues.md` § 5.1 (which puts
  the condition in SDD § 4 as RT-11, surfaces it in § 9 as TO-8 and names the browser dependence in
  § 11 as R-12): **the decision** — `web` answers a page that shows a pending confirmation of a move
  to `cancelled` with HTTP 202 and every other move interaction or outcome page with 200, each with
  `Cache-Control: no-store`; the status is read off the page as built, after outcome precedence, task
  membership and the workflow's answer against the saved state (`web/routes.py:L323-L333`,
  `_pending_status`; `L340-L367`, `_move_view`); the 202 is the history-admission boundary and
  `no-store` is HTTP-cache protection, two purposes; the meaning taken for 202 is the standard's, a
  request accepted for processing that is not complete, here a move intent awaiting the operator,
  with nothing scheduled, saved or recorded. **Alternatives ruled out** — a page script (ADR-0003);
  a cookie or session (ADR-0006); `Clear-Site-Data: "cache"` on the confirming redirect, measured not
  to evict the page from the pinned browser's history cache (the change design of
  `tracker17 · tobiishi · 2026-10-20_history-after-confirm`, § 1, "Feasibility evidence");
  `no-store` alone, which Chrome documents as no bar to a history-cache restore. **Consequences** — a
  return through Back or Forward to a confirmation's address is a fresh load of the saved status
  (UXD UX-F4's no-press refusal once the task is final); a reader meets a 202 on a GET and this record
  says why. **Dependence** — Chromium admits a main document to its back/forward cache only when its
  status is exactly 200 (`content/browser/back_forward_cache/back_forward_cache_impl.cc`,
  `PopulateReasonsForMainDocument`: `if (rfh->last_http_status_code() != net::HTTP_OK)` →
  `kHTTPStatusNotOK`, read 2026-10-20), and 202 is not a status the HTTP standard lets a cache store
  heuristically (RFC 9110 § 15.1). A release that changes the rule shows up as the two end-to-end
  tests below failing. **The obligation** — QC-n: a page that shows a pending confirmation is answered
  202, every other move interaction or outcome page 200, each with `Cache-Control: no-store`, and no
  response carries `Clear-Site-Data`; *verified by:* layer 3, `tests/integration/test_routes.py`
  (`test_pending_confirmation_response_matches_the_rendered_page`,
  `test_non_confirmation_move_views_keep_their_response_contract`,
  `test_move_interaction_and_outcome_pages_are_not_stored`), and layer 5,
  `tests/e2e/test_moves.py` (`test_history_matrix_revalidates_current_saved_status`,
  `test_real_history_traversal_revalidates_the_confirmation`); 67 passed in a fresh clone at
  `9b05680c7`, and no product code has moved since at `ca2f9e98a`. *Traces to:* SDD § 4 RT-11, § 9
  TO-8, § 11 R-12 as the fold writes them; SRS NFR-3, NFR-13; UXD § 4, UX-F4, UX-I3. *Binds:* the new
  QC-n.
- **Rationale:** the decision has every mark the nine records already carry — rejected alternatives
  that were measured, a dependence on one vendor's rule, and a shape a reader would "simplify" away
  (a 202 on a GET read as a mistake and set back to 200 brings a stale confirmation back on Back).
  The SDD surfaces it in § 9 and its Review Notes, which is where § 12 says the Principal Architect
  reads, and this item is raised as well so the record does not wait on a run nobody schedules: the
  product has run on the decision since `9b05680c7`, and today no obligation a `development-design`
  review checks names it. The CTO judged the record worth writing in
  `products/tracker17/docs/trail/sdd/self_answer-10.md` § 5.1.
- **If overridden:** with "no ADR; the SDD's RT-11 and TO-8 suffice", the decision stays surfaced in
  the SDD only — a browser-rule change then has no superseding-record path, and no obligation binds
  the status and the header, so a change can drop the 202 and only the end-to-end layer catches it,
  on a machine where layer 5 runs. With "an obligation, no ADR", QC-n binds the behaviour and the
  reason lives in SDD § 9 TO-8 alone.
- **Confirm or override:** confirm, with three additions. The record and the obligation are both
  owed, and SDD version 11 now carries § 4 RT-11, § 9 TO-8 and § 11 R-12, so nothing waits on the
  SDD. First, the record prices undoing the *decision*, not the line. TO-8 puts undoing the 202 at
  "one line in `web`", and RN-13 and RN-22 refused a record to one-line decisions. This one passes
  that gate because the guarantee it buys has no other mechanism left. Undoing it needs a page
  script (a record superseding ADR-0003), a cookie or session (a record superseding ADR-0006), or
  giving up UXD UX-F4's no-press refusal on Back. A Review Note says so, so the record does not read
  as contradicting RN-13. The record's *Dependence* also keeps R-12's bound: the end-to-end tests
  prove the pinned Chromium build, 153.0.8010.12 under `playwright==1.63.0`, and not the operator's
  current stable Chrome. Second, the obligation goes in § 1.1, beside QC-7 and QC-8, as QC-63, and
  not in § 2. § 2's preamble has every entry name the trust boundary it guards, and this one guards
  none of B-1 to B-4. Its § 10 row is `pytest tests/` · layer 3 and `pytest tests/e2e/` · layer 5,
  over the tree, gated at the suite. Third, the obligation keeps two bounds RT-11 states. A
  confirmation address whose task no task holds answers the not-found page, 404, with no
  `no-store`, and that page is outside the obligation. The `Clear-Site-Data` clause covers a move's
  responses: every move submission's response, and the confirmation and back-out pages. That is
  what its check reaches, `tests/integration/test_routes.py`,
  `test_move_responses_do_not_clear_site_data`, and the *verified by:* tail names that test, which
  the drafted list leaves out. Reasoning: `products/tracker17/docs/trail/architecture/self_answer-16.md` § 2.1

### 2.2 RN-15 and RN-42 still call the EX-6 confirmation open, and SDD version 11 counts it verified

> A `companion-self-answer` run raised this item on 2026-10-21, in the Principal Architect's seat,
> while answering § 2.1 of this file. No producing run wrote it. It came from reading `nfdr.md`
> version 13 against SDD version 11. Its reasoning is
> `products/tracker17/docs/trail/architecture/self_answer-16.md` § *Raised on this document*.

- **Lands in:** `nfdr.md` RN-15, recorded by a new Review Note. RN-42 is a dated record and is not
  edited. `adr/0003-no-script-in-any-page.md` is not edited.
- **Drafted into the records:** nothing. This run writes no record. What the fold is handed: RN-15
  says the EX-6 confirmation is verified. Its three parts are the sentence alone holding focus, the
  double press that never confirms, and back-out returning focus. SDD § 11 R-2 at version 11 names
  the four tests in `tests/e2e/test_moves.py` that verify them, and records that all four passed in
  a fresh clone at `9b05680c7`, 67 passed, with `playwright==1.63.0` and Chromium 153.0.8010.12.
  Assistive-technology speech for EX-14 stays as the one open case, which one VoiceOver pass
  settles, as SDD § Open Questions now holds it alone. The result is tied to its commit, by RN-42's
  own rule. ADR-0003 is neither edited nor superseded, because its decision did not move and its
  *Dependence* was true on its date.
- **Rationale:** `nfdr.md` RN-15 reads "What stays open is two cases. The first is the confirmation
  of SDD § 4 EX-6", and RN-42 reads "so both stay: the EX-6 confirmation, which SDD § 6
  `status-moves` settles". SDD version 11 (`9c7db2266`) settled it: § 11 R-2 counts the
  confirmation case verified, and § Open Questions keeps only the assistive-technology case. A
  `development-design` review that reads RN-15 meets a case as open that the SDD has closed.
- **If overridden:** with "leave it", RN-15 keeps counting two open cases where the SDD holds one,
  and a reader following ADR-0003's `## Binds` line through QC-34 to RN-15 is told a verified case is
  unsettled.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

## 3. Raised from downstream — an item from a seat that did not write these records

None.
