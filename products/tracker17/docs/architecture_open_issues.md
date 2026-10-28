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

> **No producing run wrote this file.** A `companion-self-answer` run opened it on 2026-10-28, in the
> CTO's seat, while answering `products/tracker17/docs/SDD_open_issues.md` § 5.1, to carry item
> § 2.1. `product-architecture` has no record of writing it. It exists because that answer widens SDD
> § 4 RT-11 from a move to `cancelled` to every pending confirmation EX-6 names and states the rule a
> deletion's pages follow, while ADR-0010 § Decision and NFDR QC-63 are worded for a move only and
> name no deletion page at all (`grep -n -i delet docs/adr/0010-*.md` and the same over QC-63's lines,
> `docs/nfdr.md:L91-L110`, both printed nothing on 2026-10-28). The SDD states the condition on its
> fold of that item; the record and the obligation are these records' to write.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

### 2.1 Widen the history-admission boundary to every pending confirmation and to a deletion's pages — QC-63 revised in place, ADR-0010 superseded
- **Lands in:** both — `nfdr.md` QC-63, revised in place, and a new `adr/0012-<slug>.md` that
  supersedes ADR-0010.
- **Drafted into the records:** nothing — the run that raised this writes no record. What it hands
  the Principal Architect, to write after `product-sdd` folds `SDD_open_issues.md` § 5.1 (which
  widens § 4 RT-11 and closes the case RT-11 handed to `delete-and-rename`): **the decision** —
  `web` answers a page that shows a pending confirmation of any action SDD § 4 EX-6 confirms — a
  move to `cancelled`, a task deletion, a project deletion — with HTTP 202, read off the page as
  built, and every other page a confirmed action's interaction or outcome lands on — a move's
  outcome, a deletion's back-out, its failure and the landing that names what was deleted — with
  200; each carries `Cache-Control: no-store`; the address of a deleted task or project, with any
  query, answers the not-found page, 404, with no cache header, and is outside the obligation; no
  response carries `Clear-Site-Data`. **The 404 and the HTTP cache** — the standard lets a cache
  keep a 404 heuristically (RFC 9110 § 15.5.5, "A 404 response is heuristically cacheable", read at
  the source on 2026-10-28), and the tracker lets it, because an identity is never reused after its
  task is deleted (SRS DR-2; ADR-0008), so a kept 404 for a deleted address stays true; the pinned
  browser never keeps one anyway — Chromium computes a heuristic lifetime only for 200, 203 and 206
  with a `Last-Modified`, treats 300, 301, 308 and 410 as fresh for ever, and gives every other
  status zero freshness (`net/http/http_response_headers.cc`, `GetFreshnessLifetimes`, read at the
  source on 2026-10-28), and the listener sends neither `Date` nor `Last-Modified`
  (`web/listener.py`, `_write`, `send_response_only`). **Why one boundary** — SDD § 9 TO-8 already
  states it for "a page that shows a pending confirmation" with no move in its words; EX-6 defines
  the three confirmations as one mechanism, reused by § 7's `status-moves → delete-and-rename` edge
  "as built and tested"; and what the 202 buys is the same: Back from "You deleted 'X'" to the
  confirmation's address is a fresh load that shows the not-found page (UXD UX-S10), not a page
  restored from the history cache that shows the deleted task as held and offers to delete it
  again. **The obligation** — QC-63 widened to those words; *verified by:* its four layer-3 tests
  and its two layer-5 tests as today, plus `tests/integration/test_delete_routes.py`,
  `test_live_delete_views_have_their_response_policy` (the deletion's four live pages carry
  `no-store`; it asserts 200 on `?delete_confirm` today and flips to 202 with the code),
  `test_missing_task_wins_over_every_query` and `test_a_never_held_task_answers_the_same` (404 with
  no cache header), and a layer-5 deletion history test, to be added beside
  `tests/e2e/test_delete_task.py` `test_completion_survives_actual_reload_back_and_forward`, which
  today never goes Back to the confirmation. *Traces to:* SDD § 4 RT-11, EX-6, EX-13; § 9 TO-8;
  § 11 R-12, as the fold writes them; SRS NFR-3, NFR-13, DR-2; UXD UX-I2, UX-S10.
- **Rationale:** ADR-0010 § Decision held to its words — "a pending confirmation of a move to
  `cancelled`", "every other page a move's interaction or outcome lands on" — excludes a deletion's
  pages, and QC-63 binds nothing on them, while the product has sent `no-store` on every one of
  them since the task deletion landed (`web/routes.py`, `_stored_as_asked`, `deleting`) and the SDD's
  rule now covers them. A change of a decision's words is recorded by supersession and never by
  edit, which is how ADR-0011 took ADR-0006 (`trail/architecture/cycle-14.md` § 3.1). The obligation
  is revised in place because the NFDR is updated in place (its header). One thing the Principal
  Architect decides that this run cannot: the product answers the task deletion's confirmation 200
  today (`web/routes.py:L378-L385` passes no interaction to `_pending_status` for a deletion page),
  so the widened obligation binds from the change that aligns the product, and the records say how
  an obligation the product does not yet meet is carried, as RN-15 and RN-42 carried the EX-6
  confirmation.
- **If overridden:** with "QC-63 only, no new ADR", the reason a deletion's confirmation is a 202
  GET lives in SDD § 9 TO-8 alone and ADR-0010, held to its words, reads as contradicting the product
  on every deletion page. With "a separate QC for deletion", two obligations state one mechanism's
  rule and drift apart. With "keep the records move-only", a deletion's confirmation stays 200, Back
  after confirming restores the deleted task's page from history on the pinned browser, and SDD
  § 9 TO-8's words stay false of the product; that is the SDD's call first, raised on its companion,
  and these records follow it.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

## 3. Raised from downstream — an item from a seat that did not write these records

None.
