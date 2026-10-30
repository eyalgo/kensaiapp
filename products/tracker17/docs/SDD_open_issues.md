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

None.

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
- **Answer:**

### 5.2 EX-13's not-found page does not hold while the unreadable-data page shows
- **Raised by:** PM — 2026-10-30
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. The exception wants scoping to the normal mode.
- **Where it shows:** `docs/SDD.md:L698-L699`. On unreadable data the one page takes precedence at every page address (`tests/integration/test_start.py`, `test_an_unreadable_start_serves_one_page_and_announces_once`).
- **If a document has to be written:** none — `SDD.md` itself, by `product-sdd`.
- **Answer:**

**How it closes.** `product-sdd` folds it on its next run like every other item in this file, and the trail copy and the delete-when-empty behaviour are unchanged.
