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

> **No producing run wrote this file.** A `companion-self-answer` run opened it on 2026-10-30, in the
> Principal Architect's seat, while answering `products/tracker17/docs/architecture_open_issues.md`
> § 3.1. That item scopes NFDR QC-7's 200 to a tracker serving its saved data, and QC-7 traces to
> § 4 RT-8, which states the same 200 with no mode. § 12 has § 4 win where the two disagree, so the
> file exists to keep them agreeing. `product-sdd` has no record of writing it. The run's reasoning
> is `products/tracker17/docs/trail/architecture/self_answer-26.md`.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — a best-effort answer was drafted; confirm or override

### 2.1 § 4 RT-8's 200 for a form sent with method="get" does not hold while the unreadable-data page shows
- **Raised by:** Principal Architect — outside the three lane seats, because the run that found it was answering the architecture companion
- **Seat:** cto
- **Drafted into the SDD:** nothing yet. The lean is one sentence at the end of RT-8's `get` passage: "While the saved data cannot be read, such a form's address answers as every address does (EX-13), and this 200 does not reach it." § 4 still names no status for the unreadable-data page, and RT-8's rule for a tracker serving its saved data does not move.
- **Rationale:** `SDD.md:376-392`, RT-8, says "the tracker answers that address with the page, 200, as it answers a link", with no mode. On unreadable data that address answers 503 with the one page (`web/routes.py`, `UnreadableSite.handle`; `tests/integration/test_unreadable_routes.py`, `test_checked_unreadable_reads_share_one_representation`). RN-69 read RT-11's 404 as reached only while data is served, and said no condition in § 4 names a status for the page. RT-8 does name one, and a filter address kept in a bookmark still reaches it. § 12 says "the § 4 statement wins and the entry is re-derived", so once QC-7 is scoped, RT-8 read on its own would overrule it. EX-13 already says every address shows that page, so this may read as settled by EX-13 alone. That doubt is why this is a question and not a defect stated flat.
- **If overridden:** RT-8 keeps its wider sentence, and QC-7's scoped clause rests on EX-13 alone, with § 12's rule pointing the other way. No slice, fence or § 7 edge moves either way, and no code changes.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

## 3. Cut calls to confirm — where the slicing could reasonably have gone another way

None.

## 4. Disagreements — two seats hold different positions and neither yields

None.

## 5. Raised from downstream — an item from a seat that did not write the SDD

None.
