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
> finding something only the SDD can fix. Its `Raised by:` therefore takes a wider set than §§ 1–3's,
> which stay fixed to the three lane seats on purpose.

> **No producing run wrote this file.** The PM opened it on 2026-10-28, after reading the product's
> task deletion against § 4 RT-11 and § 6 S-7, to carry § 5.1. `product-sdd` has no record of writing it.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — a best-effort answer was drafted; confirm or override

None.

## 3. Cut calls to confirm — where the slicing could reasonably have gone another way

None.

---

## 4. Disagreements — two seats hold different positions and neither yields

None.

## 5. Raised from downstream — an item from a seat that did not write the SDD

### 5.1 No section states how a deletion's pages are answered, and S-7 says its confirmations behave as the move's
- **Raised by:** PM — 2026-10-28
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_delete-and-rename`
- **What it blocks:** nothing is blocked. The project deletion still to be built has two readings of
  how its confirmation is answered.
- **Where it shows:** § 4 RT-11 is move-only (202 for a pending move to `cancelled`, 200 and
  `no-store` for the other move pages) and leaves "whether the HTTP cache may keep a 404
  heuristically" to `delete-and-rename` (`docs/SDD.md:L438-L442`). § 6 S-7 says "Both confirmations
  behave as the one in `status-moves` does" (`docs/SDD.md:L1013`). The product now answers the task
  deletion's confirmation and outcome pages 200 with `no-store`, not 202, and a deleted task's
  address 404 with no `no-store` (`web/routes.py:L433-L438`). ADR-0010 and NFDR QC-63 stay move-only
  (`docs/nfdr.md:L91`). No settled section states the deletion's response rule, so the 404 question
  RT-11 hands to this slice has no answer on record, and S-7's "behave as" reads as 202 for a
  confirmation the product answers 200. The SDD should state the rule a deletion's pages follow, for
  a task and for a project, or scope S-7's sentence to what the operator sees; whether ADR-0010 or
  QC-63 then owes a line is the Principal Architect's.
- **If a document has to be written:** `SDD.md` itself, by `product-sdd`.
- **Answer:** One boundary for every pending confirmation EX-6 names, and a deletion's other pages
  follow a move's. Stated in § 4, the CTO's: RT-11 widens from "a move to `cancelled`" to every
  action EX-6 confirms — a move to `cancelled`, a task deletion, a project deletion. (a) A page that
  shows a pending confirmation is answered 202, read off the page as built, so a `delete_confirm`
  address for a task no task holds is 404, never 202. (b) Every other page a confirmed action's
  interaction or outcome lands on — a deletion's back-out, its failure, and the landing that names
  the deleted task or project — is 200. (c) Every page under (a) and (b) carries `Cache-Control:
  no-store`. (d) The address of a deleted task or project, with any query, answers the not-found
  page, 404, with no cache header (EX-13; UXD UX-S10), and a submission naming a deleted target is
  answered by a redirect to that address and saves nothing (S-7's deleted-target refusals). (e) The
  case RT-11 handed to this slice closes: the standard lets a cache keep a 404 heuristically (RFC
  9110 § 15.5.5, "A 404 response is heuristically cacheable", read at the source on 2026-10-28), and
  the tracker lets it, because an identity is never reused after its task is deleted (SRS DR-2;
  ADR-0008), so a kept 404 for a deleted address stays true for good; under the pinned browser none
  is kept — Chromium computes a heuristic lifetime only for 200, 203 and 206 with a `Last-Modified`,
  treats 300, 301, 308 and 410 as fresh for ever, and gives every other status zero freshness
  (`net/http/http_response_headers.cc`, `GetFreshnessLifetimes`, read at the source on 2026-10-28),
  and the listener sends neither `Date` nor `Last-Modified` (`web/listener.py`, `_write`,
  `send_response_only`), so a 404 is revalidated on every use. Named and left: a 404 for an
  identity not yet issued, reached only by a typed address, kept by a cache outside SRS NFR-13's
  bound. **Why 202 for a deletion's confirmation, which the product answers 200 today.** The
  boundary RT-11 states is the confirmation's, not the move's: § 9 TO-8 already states it for "a
  page that shows a pending confirmation" with no move in its words; EX-6 defines the three
  confirmations as one mechanism, and § 7's `status-moves → delete-and-rename` edge reuses that
  confirmation "as built and tested", the history tests included; and what the 202 buys is the
  same — Back from "You deleted 'X'" to the confirmation's address is a fresh load that shows
  UX-S10's not-found page, not a page restored from the history cache that shows the deleted task as
  held and offers to delete it again. Every press on that restored page is refused and changes
  nothing (the deleted-target refusals), so the ghost costs confusion, not data; the 202 costs the
  one line TO-8 already prices. The meaning of 202 fits a deletion intent as it fits a move's: a
  request accepted and not complete, which "might or might not eventually be acted upon, as it
  might be disallowed when processing actually takes place" (RFC 9110 § 15.3.3, read 2026-10-28).
  **What moves.** § 4 RT-11 widens as above and its last sentence, the case handed to this slice,
  closes with (d) and (e). § 9 TO-8 and § 11 R-12 keep their words; R-12's trigger gains the
  deletion history test once it exists. § 6 S-7's *Behaviour* sentence is the CDO's and stands: it
  names what the operator sees, EX-6's confirmation, and the status is § 4's; its *Command* half
  gains "and that a return through Back to a deletion's confirmation, after confirming, is a fresh
  load (§ 4 RT-11)". **What the product does.** It meets (b), (c) and (d) (`web/routes.py`,
  `_stored_as_asked`, L433-L438; `tests/integration/test_delete_routes.py`,
  `test_live_delete_views_have_their_response_policy`, `test_missing_task_wins_over_every_query`)
  and diverges on (a): a task deletion's confirmation is 200, because `web/routes.py:L378-L385`
  passes no interaction to `_pending_status` for a deletion page. That is an occurrence for the PM to
  carry, and the project deletion is built to this rule. ADR-0010 and QC-63 owe a deletion's pages a
  line; that is carried at `products/tracker17/docs/architecture_open_issues.md` § 2.1, opened by
  this run at `5585e0b11`, with the lean that QC-63 is revised in place and ADR-0010 superseded.
  Reasoning: `products/tracker17/docs/trail/sdd/self_answer-13.md` § 5.1.

**How it closes.** `product-sdd` folds it on its next run like every other item in this file, and
the trail copy and the delete-when-empty behaviour are unchanged.
