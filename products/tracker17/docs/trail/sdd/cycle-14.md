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

> **No producing run wrote this file.** It was opened on 2026-10-30 by the PM, to carry § 5.
> `product-sdd` has no record of writing it.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — a best-effort answer was drafted; confirm or override

### 2.1 The header still reads the NFDR at version 19 and the architecture companion as one item on QC-40
- **Raised by:** CTO
- **Seat:** cto
- **Drafted into the SDD:** nothing yet — the lean is this: the header's *Inputs read* reads NFDR
  version 23, and `products/tracker17/docs/architecture_open_issues.md` live with five items, §§ 3.1
  to 3.5, raised by the PM on 2026-10-30 against QC-7, QC-63, ADR-0011, ADR-0012 and ADR-0005,
  unanswered and the Principal Architect's. The records run to ADR-0013 as the header already
  says, and § 12's count of thirteen stands.
- **Rationale:** two facts in the header are false on disk. `SDD.md:6` says "NFDR Settled (version
  19 …" and that the companion was "opened on 2026-10-29 by the PM at `f86543f50` with one item,
  § 3.1 on QC-40, unanswered". `nfdr.md`'s header reads version 23 (`4a646aaf0`), whose fold of
  cycle 21 answered QC-40's item and removed that companion; the PM opened it again on 2026-10-30
  (`12499fcbe`) with §§ 3.1 to 3.5, none of them on QC-40. What those five ask is the Principal
  Architect's, carried on that companion, not this document's: each is the same startup-mode
  qualification §§ 5.1 and 5.2 make here, read against the records, and § 12 says § 4 wins where
  the two disagree.
- **If overridden:** nothing moves in any slice, fence or edge. The two lines stay false, and a
  reader is sent to a companion item that was folded four versions ago.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

> **No producing run wrote this item.** A `companion-self-answer` run raised it on 2026-10-30 while
> answering §§ 5.1 and 5.2, after reading the header against `nfdr.md`'s header and
> `architecture_open_issues.md`. `product-sdd` has no record of writing it. The fold's own input
> catch-up may reach the same lines unprompted, as it did for cycle 11's § 2.1 (RN-60) and cycle
> 13's (RN-66); the item is here so that it is not missed.

## 3. Cut calls to confirm — where the slicing could reasonably have gone another way

None.

## 4. Disagreements — two seats hold different positions and neither yields

None.

## 5. Raised from downstream — an item from a seat that did not write the SDD

### 5.1 EX-12 says the unreadable-data page carries no header, and DESIGN.md gives it one
- **Raised by:** PM — 2026-10-30
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. Two settled documents word one page differently.
- **Where it shows:** `docs/SDD.md:L693-L697`, "carries no header and no navigation", against `docs/DESIGN.md:L426-L427`, "the header shows the product name and no nav links". The page follows the design document: the product name as plain text and no links (`web/pages.py`, `unreadable_data_page`). Both agree there is no navigation.
- **If a document has to be written:** none — `SDD.md` itself, by `product-sdd`.
- **Answer:** EX-12 follows the UXD and the design language: one header sits on every page, the
  unreadable-data page included. On that page the header shows the product name and no area link,
  and the page carries no navigation and no control that acts on the data (UXD § 4, "one header
  that sits on every page"; UX-S9, "no navigation into the tracker"; `DESIGN.md` § Components,
  {components.header}, "On UX-S9, the unreadable-data page, the header shows the product name and
  no nav links"). The clause "carries no header" goes, and "every page but one" becomes every page,
  with the exception narrowed to the area links: the UXD never states "no header", the design
  language states the opposite, and the page as built renders the header with the product name
  and an empty navigation (`web/pages.py`, `_framed`, which `unreadable_data_page` calls with no
  navigation). The rule that the header shows only the areas that exist so far stands. Nothing
  else moves: § 6 S-8's "no navigation and no control that acts on the data", the station's bar
  and FDR R-26 already say only that. Answered in the CTO's seat because the input settles it, as
  RN-31, RN-54 and RN-57 read a UXD change; cycle-1 § 2.4's addition (2), which put "no header"
  in, over-read UX-S9. Reasoning in `products/tracker17/docs/trail/sdd/self_answer-17.md`.

### 5.2 EX-13's not-found page does not hold while the unreadable-data page shows
- **Raised by:** PM — 2026-10-30
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. The exception wants scoping to the normal mode.
- **Where it shows:** `docs/SDD.md:L698-L699`. On unreadable data the one page takes precedence at every page address (`tests/integration/test_start.py`, `test_an_unreadable_start_serves_one_page_and_announces_once`).
- **If a document has to be written:** none — `SDD.md` itself, by `product-sdd`.
- **Answer:** EX-13 is scoped to a tracker serving its saved data: while the tracker serves the
  saved data, an address for a project or task that does not exist shows the not-found page
  (UX-S10); while the saved data cannot be read, every address shows the unreadable-data page and
  no other, the not-found page included (EX-12; UXD § 4, "One page replaces all of them when the
  saved data cannot be read (UX-S9): every address shows that page";
  `tests/integration/test_start.py`, `test_an_unreadable_start_serves_one_page_and_announces_once`,
  which asks an unknown address among the three). The mode is fixed at start (§ 4 SD-1; § 9 TO-4),
  so which page an address shows does not change while the tracker runs, and a repair made while
  the page shows is read at the next start. The UXD already states the precedence, so this is a
  correction of EX-13's words and not a change to the experience, and no CDO item is raised. § 4
  RT-11's 404 and § 6 S-7's not-found line speak of a deleted task or project, which exists only
  while the tracker serves its data, and stand as written. Reasoning in
  `products/tracker17/docs/trail/sdd/self_answer-17.md`.

**How it closes.** `product-sdd` folds it on its next run like every other item in this file, and the trail copy and the delete-when-empty behaviour are unchanged.
