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
- **Answer:**

### 3.2 QC-63's status rules do not hold on a start on unreadable data
- **Raised by:** PM — 2026-10-30
- **Which record:** `nfdr.md` § 1.1 QC-63
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. The clause is unconditional and one startup mode departs from it.
- **Where it shows:** `docs/nfdr.md:L91-L100` gives the address of a deleted task or project the not-found page, 404, and a confirmation page 202. On unreadable data those addresses answer 503 with the one page and look nothing up: the handler holds no tracker (`web/routes.py`, `UnreadableSite`). The rules want scoping to the normal mode.
- **If a document has to be written:** none — `nfdr.md` itself, by `product-architecture`.
- **Answer:**

### 3.3 ADR-0011's decision has no exception for the unreadable-data page
- **Raised by:** PM — 2026-10-30
- **Which record:** ADR-0011, `adr/0011-a-submission-is-a-post-form-and-its-outcome-travels-in-the-address.md`
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. An Accepted record states as universal what one startup mode does not do.
- **Where it shows:** § Decision says a form sent with `method="get"` is a read answered 200, and "What a page shows is a function of the tracker state and the page's address" (line 27). The unreadable-data page has no tracker state and is the same at every address (SDD SM-6). The no-session, no-cookie and redirect decisions hold, so the exception goes through this log's append-only process.
- **If a document has to be written:** a superseding ADR, by `product-architecture`.
- **Answer:**

### 3.4 ADR-0012's 404 for a missing identity does not hold on a start on unreadable data
- **Raised by:** PM — 2026-10-30
- **Which record:** ADR-0012, `adr/0012-pending-confirmation-answered-202-confirmed-action-pages-not-stored.md`
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. The decision needs a qualification for one startup mode.
- **Where it shows:** lines 40-42 answer a deleted or never-issued identity with the not-found page, 404. On unreadable data the same address answers 503 with the one page, as 3.2 shows. No confirmation page is added, so the qualification is all that moves, through this log's append-only process.
- **If a document has to be written:** a superseding ADR, by `product-architecture`.
- **Answer:**

### 3.5 ADR-0005's "overwritten by the next save" does not reach a tracker that never saves
- **Raised by:** PM — 2026-10-30
- **Which record:** ADR-0005, `adr/0005-state-in-memory-one-action-at-a-time.md`
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. § Consequences reads wider than it holds.
- **Where it shows:** lines 37-38 say a change made by hand while the tracker runs "is overwritten by the next save". A tracker showing the unreadable-data page has no save, so a repair made while it runs is kept and is not read until the next start (`products/tracker17/README.md`, "The tracker keeps showing the page until you stop it, even if you repair the saved data."). The qualification goes through this log's append-only process.
- **If a document has to be written:** a superseding ADR, by `product-architecture`.
- **Answer:**

**How it closes.** `product-architecture` folds it on its next run like any other item here.
