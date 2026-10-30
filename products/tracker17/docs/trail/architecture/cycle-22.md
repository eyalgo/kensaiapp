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

> **No producing run wrote this file.** It was opened on 2026-10-30 by the PM, to carry § 3.
> `product-architecture` has no record of writing it.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-7's 200 for a form sent with method="get" does not hold on a start on unreadable data
- **Raised by:** PM — 2026-10-30
- **Which record:** `nfdr.md` § 1.1 QC-7
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. The universal clause reads false for one startup mode.
- **Where it shows:** `docs/nfdr.md:L73-L83` says a form sent with `method="get"` "is answered with its page, 200". On unreadable data the tracker answers every page address 503 with the one page (`web/routes.py`, `UnreadableSite.handle`; `tests/integration/test_start.py`, `test_an_unreadable_start_serves_one_page_and_announces_once`). `GET /style.css` still answers the stylesheet, and a marked same-origin POST is still sent to a page address. The clause wants scoping to the normal mode, with that answer named.
- **If a document has to be written:** none — `nfdr.md` itself, by `product-architecture`.
- **Answer:** Scope the 200 to a tracker serving its saved data, and name the other answer in QC-7. Its last sentence becomes: "While the tracker serves its saved data, a form sent with `method="get"` is answered with its page, 200, with no redirect. While the saved data is unreadable, a request QC-31 and QC-32 let through is answered at every address, whatever its query, with the one unreadable-data page, 503, `Cache-Control: no-store`, and a form sent with `method="get"` gets that answer. Two requests differ: `GET /style.css` answers the stylesheet, 200, and a `post` marked `same-origin` is sent to a page address, built by the same one function, with its body unread." QC-7's other sentences stand. *Verified by* gains `tests/integration/test_unreadable_routes.py`, `test_checked_unreadable_reads_share_one_representation`, `test_only_checked_get_serves_the_stylesheet` and `test_checked_post_always_redirects_without_decoding_or_acting`. The trace gains SDD § 4 EX-13, and it names 503 as the product's measured answer, because no upstream document names a status for that page (SDD RN-69). SDD RT-8 states the same 200 with no mode, and that change is the CTO's, on `products/tracker17/docs/SDD_open_issues.md` § 2.1. Reasoning: `products/tracker17/docs/trail/architecture/self_answer-26.md`.

### 3.2 QC-63's status rules do not hold on a start on unreadable data
- **Raised by:** PM — 2026-10-30
- **Which record:** `nfdr.md` § 1.1 QC-63
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. The clause is unconditional and one startup mode departs from it.
- **Where it shows:** `docs/nfdr.md:L91-L100` gives the address of a deleted task or project the not-found page, 404, and a confirmation page 202. On unreadable data those addresses answer 503 with the one page and look nothing up: the handler holds no tracker (`web/routes.py`, `UnreadableSite`). The rules want scoping to the normal mode.
- **If a document has to be written:** none — `nfdr.md` itself, by `product-architecture`.
- **Answer:** Scope all of QC-63 to a tracker serving its saved data, with a first sentence such as "While the tracker serves its saved data:", and add one closing sentence: "While the saved data is unreadable, no confirmation, outcome or not-found page exists, and these addresses answer as QC-7 says." QC-7 holds the one statement of the mode, so QC-63 repeats neither the 503 nor `no-store`. *Verified by* gains `tests/integration/test_unreadable_routes.py`, `test_checked_unreadable_reads_share_one_representation`, whose targets include `/tasks/1`, `/tasks/1/delete` and `/projects/1`. SDD RT-11 needs no change, because SDD RN-69 already reads its 404 as reached only while data is served. Reasoning: `products/tracker17/docs/trail/architecture/self_answer-26.md`.

### 3.3 ADR-0011's decision has no exception for the unreadable-data page
- **Raised by:** PM — 2026-10-30
- **Which record:** ADR-0011, `adr/0011-a-submission-is-a-post-form-and-its-outcome-travels-in-the-address.md`
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. An Accepted record states as universal what one startup mode does not do.
- **Where it shows:** § Decision says a form sent with `method="get"` is a read answered 200, and "What a page shows is a function of the tracker state and the page's address" (line 27). The unreadable-data page has no tracker state and is the same at every address (SDD SM-6). The no-session, no-cookie and redirect decisions hold, so the exception goes through this log's append-only process.
- **If a document has to be written:** a superseding ADR, by `product-architecture`.
- **Answer:** Write a superseding record, one for ADR-0011 alone, carrying its decision, alternatives and consequences whole. It qualifies two things: "What a page shows is a function of the tracker state and the page's address" and the `get` form's 200 hold while the tracker serves its saved data. While the saved data is unreadable there is no tracker state, the page is fixed by the location given at start and is the same at every address, and a `get` form's address gets that page, 503, as QC-7 says. The no-session, no-cookie, `post`-only and redirect decisions stand word for word. It records one new alternative: one shared record for the mode, which lost because a log of one decision per file has no status for a partial narrowing and ADR-0011 would stay Accepted and read as universal. It binds QC-7 and QC-8, and QC-8 does not move: the location is fixed at start as the host already is, and it is nothing a request brings. Reasoning: `products/tracker17/docs/trail/architecture/self_answer-26.md`.

### 3.4 ADR-0012's 404 for a missing identity does not hold on a start on unreadable data
- **Raised by:** PM — 2026-10-30
- **Which record:** ADR-0012, `adr/0012-pending-confirmation-answered-202-confirmed-action-pages-not-stored.md`
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. The decision needs a qualification for one startup mode.
- **Where it shows:** lines 40-42 answer a deleted or never-issued identity with the not-found page, 404. On unreadable data the same address answers 503 with the one page, as 3.2 shows. No confirmation page is added, so the qualification is all that moves, through this log's append-only process.
- **If a document has to be written:** a superseding ADR, by `product-architecture`.
- **Answer:** Write a superseding record, one for ADR-0012 alone, carrying it whole. Its one qualification: the 202, 200, `no-store` and 404 rules hold while the tracker serves its saved data, and on unreadable data those addresses answer as the record that follows ADR-0011 says. No confirmation page is added, and the Chromium dependence does not move. It records one new alternative: leaving ADR-0012 as it stands and relying on SDD § 12, which lost because the delivery tier reads an Accepted record as fixed. It binds QC-63. Reasoning: `products/tracker17/docs/trail/architecture/self_answer-26.md`.

### 3.5 ADR-0005's "overwritten by the next save" does not reach a tracker that never saves
- **Raised by:** PM — 2026-10-30
- **Which record:** ADR-0005, `adr/0005-state-in-memory-one-action-at-a-time.md`
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. § Consequences reads wider than it holds.
- **Where it shows:** lines 37-38 say a change made by hand while the tracker runs "is overwritten by the next save". A tracker showing the unreadable-data page has no save, so a repair made while it runs is kept and is not read until the next start (`products/tracker17/README.md`, "The tracker keeps showing the page until you stop it, even if you repair the saved data."). The qualification goes through this log's append-only process.
- **If a document has to be written:** a superseding ADR, by `product-architecture`.
- **Answer:** Write a superseding record, one for ADR-0005 alone, carrying it whole, with two sentences qualified to agree with SDD § 9 TO-4. § Consequences reads: while the tracker serves its saved data, a change made to the file by hand is overwritten by the next save; while the saved data cannot be read, it holds no state and makes no save, so the change stays and the next start reads it. § Decision's "`application` holds the current state" becomes "a readable state", because no `application` is built on unreadable data, as TO-4 now reads. The read-once and one-tracker sentences hold in both modes and do not move. It binds QC-3, QC-52, QC-53 and QC-54, whose traces re-point to it. Reasoning: `products/tracker17/docs/trail/architecture/self_answer-26.md`.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
