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

> **No producing run wrote this file.** The PM opened it on 2026-10-27, after reading the product's
> filter form against § 4 RT-8, to carry § 5.1. `product-sdd` has no record of writing it.

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

### 5.1 RT-8 says every submission is answered by a redirect; the filter form is answered with a page
- **Raised by:** PM — 2026-10-27
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_narrow-and-sort`
- **What it blocks:** nothing is blocked. RT-8 reads "Every submission is answered by sending the
  browser to a page address" (`SDD.md:L330-L332`). The project page now carries a filter form sent
  with `method="get"` (`web/pages.py:L1189`), and Apply, its reload and Clear are answered with the
  project page itself, 200, saving nothing (`tests/integration/test_routes.py:L1090-L1093`, "Apply,
  its reload and Clear are the one project GET route"). The product reads a GET form as a read, not a
  submission; RT-8 never says so, so a reader holding RT-8 to its words finds a form it does not
  cover. The sort controls and the All tasks list (FR-36, UX-S7) add more forms of the same kind.
- **Where it shows:** § 4 RT-8, its second sentence. The record it owes: whether "submission" means
  a form that asks for a change (POST), so a GET form that only narrows or orders a list is answered
  with the page and stays outside the redirect rule — or the opposite, with the redirect a GET form is
  then owed.
- **If a document has to be written:** none; RT-8's wording only. ADR-0006 and NFDR QC-7 state the
  same sentence and are raised on their own companion.
- **Answer:** <the owner fills this in>

**How it closes.** `product-sdd` folds it on its next run like every other item in this file, and
the trail copy and the delete-when-empty behaviour are unchanged.
