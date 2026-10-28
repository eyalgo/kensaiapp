# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-28
- **Sources re-read:**
  - RFC 9110, from `https://www.rfc-editor.org/rfc/rfc9110.txt`, read 2026-10-28. § 15.3.3: "the
    request has been accepted for processing, but the processing has not been completed. The request
    might or might not eventually be acted upon, as it might be disallowed when processing actually
    takes place." § 15.5.5: "A 404 response is heuristically cacheable". § 15.1 lists 200, 203, 204,
    206, 300, 301, 308, 404, 405, 410, 414 and 501 as heuristically cacheable, "all other status
    codes are not". 202 is not among them. All three match what the item and SDD RT-11 cite.
  - Chromium `content/browser/back_forward_cache/back_forward_cache_impl.cc`, main branch, read
    2026-10-28. `PopulateReasonsForMainDocument` still has
    `if (rfh->last_http_status_code() != net::HTTP_OK)` →
    `NotRestoredReason::kHTTPStatusNotOK`. That means exactly 200, and a 202 deletion confirmation is
    kept out of the history cache the same way a move's is.
  - Not re-read: Chromium's `GetFreshnessLifetimes`. My answer does not rest on it. It bears only
    on whether the pinned browser keeps a 404, which the item's draft and SDD RT-11 already cite
    from today's reading, and the answer is unchanged either way, because a kept 404 for a deleted
    address stays true (SRS DR-2, ADR-0008).

## Items worked

### 2.1 — Widen the history-admission boundary to every pending confirmation and to a deletion's pages — QC-63 revised in place, ADR-0010 superseded

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft is right. ADR-0012 supersedes ADR-0010, and QC-63 is widened in place to
  every pending confirmation SDD § 4 EX-6 names. I added three things. The draft left one call
  open: how to carry an obligation the product does not yet meet. Its `Clear-Site-Data` clause
  was wider than the SDD. And it did not carry the one case RT-11 names and leaves.
  - **Seat: mine, and the decision is already made.** The edit lands in `adr/` and `nfdr.md`. The
    decision under it is the CTO's, and the CTO has now made it. SDD version 13 (commit
    `cb9ef1445`, 2026-10-28) widens § 4 RT-11 to "a move to `cancelled`, a task deletion, a project
    deletion", 202 on the confirmation and 200 with `no-store` on every other page, with the
    deleted address a 404 with no cache header (`SDD.md:414-482`, RN-56 at `:2553`). The draft was
    written ahead of that fold and said it would land after it. The fold matches the draft's
    decision word for word, so the records follow a settled design and decide nothing. No answer
    binds a person, money or a risk the owner carries, so the item is not left for the owner.
  - **Supersession, not an added record: confirmed, for the draft's reason.** An added
    "deletions follow ADR-0010" record would leave two Accepted records stating one mechanism.
    ADR-0010's title, "store no move page", would still read as the whole rule. EX-6 defines the
    three confirmations as one mechanism, and TO-8 states the boundary with no move in its words,
    so one current record is what the log owes. Changing a decision's words is recorded by
    supersession, as ADR-0011 took ADR-0006 (`adr/README.md`; `0006-*.md` reads
    "Superseded by ADR-0011"). Widening QC-63 in place, not adding a second QC, keeps one
    obligation per mechanism, and the NFDR header says it is updated in place.
  - **Addition 1, the open call: the unmet clause is carried in QC-63 and a Review Note, never in
    ADR-0012.** I checked the product at `035b97cd1`, the newest commit to `web/` and `tests/`.
    `web/routes.py` `_task_page` sets `move_interaction` to `None` on any active deletion state
    (`:384-386`), and `_pending_status(None)` returns 200 (`:420-430`). So the task deletion's
    confirmation is 200 with `no-store` today. The draft's citation `:L378-L385` has drifted a
    few lines, but the behaviour is as it says. `test_live_delete_views_have_their_response_policy`
    (`tests/integration/test_delete_routes.py:451-458`) asserts `status == 200` for `?delete_confirm`.
    Under the widened QC-63 that test asserts the breach. The NFDR's header says an entry needs a
    verifier that fails when the obligation is broken, and that test passes on the breach, so it
    cannot be named as the 202 clause's verifier. The tail must name each clause with the tests
    that verify it today:
    - the move clauses: the four layer-3 and two layer-5 tests QC-63 names now.
    - the deletion's `no-store` on its four pages, its 200 on back-out, failure and landing, and no
      `Clear-Site-Data`: `test_live_delete_views_have_their_response_policy`.
    - the 404 with no cache header: `test_missing_task_wins_over_every_query` and
      `test_a_never_held_task_answers_the_same` (`:432-449`).

    The tail then says the task deletion's 202 is unmet. Its verifiers are that test's
    `?delete_confirm` row flipped to 202 and the layer-5 deletion history test beside
    `tests/e2e/test_delete_task.py` `test_completion_survives_actual_reload_back_and_forward`
    (`:151`), which today goes Back only to the landing. Both land with the change that aligns
    the product. A Review Note records the divergence and the commit it was measured at, and says
    the aligning change is the PM's to carry, as SDD RN-56 already notes. This follows RN-15 and
    RN-42, which tie a verification state to a commit and claim nothing past it. ADR-0012 states
    no product state. It is written once, and a dated "the product answers 200" in it would read
    false after the aligning change, which is exactly when a reader would open it. The NFDR is
    revised in place, so the Note can close when the code moves.
  - **Addition 2: the `Clear-Site-Data` clause is scoped to the three actions, not the product.**
    The draft says "no response carries `Clear-Site-Data`". That binds every page the tracker
    serves. RT-11 says only that the earlier header on the confirming redirect "is gone", and
    ADR-0010 and QC-63 scoped the clause to "move response". Widening it to every page would be an
    obligation no upstream section states, which this seat does not write. So the scope is the one
    RT-11 widens to: no response of an action EX-6 confirms carries it, neither its submissions nor
    its confirmation, back-out, failure or outcome pages. The delete-route tests reach the deletion
    half (`test_delete_routes.py:79`, `:438`, `:458`, `:472-477`). If the CTO wants a product-wide
    ban, that is an SDD line first. I came close to confirming the draft's wording, because no page
    sends the header today. What stopped me is that "true of the product" and "required by the
    design" are different grounds, and only the second makes an obligation.
  - **Addition 3, the failure paths.**
    - **Stale:** RT-11 names one case and leaves it (`SDD.md:461-463`). A 404 for an identity not
      yet issued, reached only by a typed address and kept by a cache outside NFR-13's bound, goes
      stale once that identity is issued. A kept 404 for a *deleted* identity stays true for good
      (DR-2, ADR-0008). This not-yet-issued case does not, so ADR-0012's *Consequences* names it
      as a cost the decision accepts.
    - **Absent:** the project deletion is not built (`docs/what_left.md`, "deletes a project along
      with all of its tasks", missing at `<a commit not in the public history>`). Its pages fall under the obligation when they
      land, and its verifiers are the layer-3 and layer-5 tests `delete-and-rename`'s project half
      adds (SDD S-7 *Command*, `SDD.md:1066-1072`).
    - **Concurrent:** a confirmation address reached after another tab deleted the task is the 404
      (`test_missing_task_wins_over_every_query` covers `?delete_confirm` on a deleted task). The
      202 only ever goes out on a page that actually shows the confirmation.
    - **Refused:** a confirmed deletion that fails lands on the failure page, 200 and `no-store`,
      covered by the policy test.
    - **Empty:** a project with no tasks changes nothing here.
  - **What would have tipped it.** If SDD version 13 had not folded RT-11's widening, the item would
    have had to wait on the SDD, and confirming it would have written records ahead of their
    source. The fold is at `cb9ef1445`, so it did not have to wait.
  - **Not raised on this document.** The NFDR header reads SDD version 12 and UXD version 9, and
    both have moved (SDD 13, UXD 11). That is the catch-up `product-architecture` does on its fold
    whenever it reads upstream. It is not a separate change this run must raise.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
