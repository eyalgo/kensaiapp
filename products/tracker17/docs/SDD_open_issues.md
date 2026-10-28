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
- **Answer:** <the owner fills this in>

**How it closes.** `product-sdd` folds it on its next run like every other item in this file, and
the trail copy and the delete-when-empty behaviour are unchanged.
