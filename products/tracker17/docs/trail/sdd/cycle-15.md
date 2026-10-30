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
> Principal PM's seat, while answering `products/tracker17/docs/fdr_open_issues.md` § 3.1. That item
> corrects FDR R-20, which traces to § 9 TO-4 and shares its sentence, so the file exists to keep the
> two documents agreeing. `product-sdd` has no record of writing it. The run's reasoning is
> `products/tracker17/docs/trail/fdr/self_answer-3.md`.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — a best-effort answer was drafted; confirm or override

### 2.1 § 9 TO-4's "overwritten by the next save" does not hold while the unreadable-data page shows
- **Raised by:** Principal PM — outside the three lane seats, because the run that found it was answering the FDR's companion
- **Seat:** cto
- **Drafted into the SDD:** nothing yet. The lean is that TO-4's opening reads: "The file is read only at start, and a readable state is held in memory. While the tracker serves its saved data, a change made to the file by hand is overwritten by the next save. While the saved data cannot be read, the tracker holds no state and makes no save (SD-4), so a change made by hand stays, and the next start reads it." What it buys and what undoing it costs stand as written.
- **Rationale:** `SDD.md:1270-1271` says "A change made to the file by hand while the tracker runs is overwritten by the next save", with no mode. On unreadable data no save exists: `web/routes.py`, `UnreadableSite`, holds "no tracker, no reader and no saver", and § 4 SD-4 forbids the write. § 4 EX-13 already says the mode is fixed at start and cites TO-4 for it, and RN-69 says "a repair made while the page shows is read at the next start". TO-4 is the one line that still says otherwise. FDR R-20 carries the same sentence and traces to TO-4, and its correction is answered on `products/tracker17/docs/fdr_open_issues.md` § 3.1, so leaving TO-4 would have the two documents disagree.
- **If overridden:** TO-4 keeps its wider sentence and FDR R-20 reads narrower than the line it traces to. No slice, fence or § 7 edge moves either way, and no code changes.
- **Confirm or override:** confirm. TO-4's opening reads as drafted, its bold sentence included: "The file is read only at start, and a readable state is held in memory. While the tracker serves its saved data, a change made to the file by hand is overwritten by the next save. While the saved data cannot be read, the tracker holds no state and makes no save (SD-4), so a change made by hand stays, and the next start reads it." Its *buys* and *undoing it costs* stand as written. Reasoning: `products/tracker17/docs/trail/sdd/self_answer-18.md`.

## 3. Cut calls to confirm — where the slicing could reasonably have gone another way

None.

---

## 4. Disagreements — two seats hold different positions and neither yields

None.

## 5. Raised from downstream — an item from a seat that did not write the SDD

None.
