# SRS open issues — tracker17

> Companion to `SRS.md`. The CTO authored the SRS non-interactively; this file holds
> what it could not settle from the inputs (the PRD and any context/constraints).
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this
> file**, then re-run `product-srs`. It folds your answers into the SRS and drops the
> resolved items. When nothing is left open, `product-srs` **deletes this file**: no file =
> the SRS is done.
>
> Your answers are never thrown away. Each time the CTO folds them in, it first copies this
> file whole to `docs/trail/srs/` — so what you decided, and why, stays readable and citable
> for good.
>
> **§§ 1–2 are the CTO's own questions; § 3 is somebody else's.** A seat reading the SRS long after
> it settled can find a gap the authoring run had no way to see, and § 3 is where it says so.

> **No producing run wrote this file.** The PM opened it on 2026-10-11, in a route review, to carry
> item § 3.1. `product-srs` has no record of writing it. It exists because the PRD now states four
> priorities and the SRS still states three.

---

## 1. Open issues — technical questions with no answer yet

None.

## 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write the SRS

### 3.1 The SRS states three priorities; the PRD now states four, `critical` included
- **Raised by:** PM — 2026-10-11
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`
- **What it blocks:** walking task priorities against a settled set. The seed that adds priorities
  rests on SDD § 6 S-2, which is cut from the SRS, so it would build `low`, `medium` and `high` only.
- **Where it shows:** `PRD.md:128` — "A task is `low`, `medium`, `high` or `critical`, and `medium`
  is the default" (PRD v5). `SRS.md:231` — "ascending runs `low`, `medium`, `high`", and the note at
  `SRS.md:647-648`. The documents cut from the SRS read the same three: `fdr.md:175` (R-51, a
  priority other than the three is refused) and `fdr.md:278-279` (R-90). Where `critical` sits in the
  ascending order is not stated anywhere.
- **If a document has to be written:** none. `SRS.md` changes through `product-srs`, and the
  documents below it change through their own producing skills.
- **Answer:** the SRS takes PRD v5's four priorities, with `critical` the highest. Four changes:
  (1) FR-15 names the set: a priority is `low`, `medium`, `high` or `critical`, and `medium` when
  none is given. DR-6's "unknown priority" then means a value outside those four. (2) FR-36: priority
  ascending runs `low`, `medium`, `high`, `critical`. That is the owner's reason for the current order,
  "ascending means rising, and `high` is more than `low`" (`trail/srs/cycle-1.md` § 2.4), and it is
  the order PRD § Core Features lists the four in. (3) FR-38: the count for each of the four
  priorities, a zero count included. (4) C-5 carries the PRD's one exception (`PRD.md:115-116`): the
  predecessor's three-value priority set is not taken over. Without that, C-5 contradicts FR-15, and
  `fdr.md` R-51 traces its three-value refusal to C-5. RN-20 § 2.4 records the three-value call as it
  was made, so the fold adds a note that `critical` follows `high` for the same reason, citing PRD v5
  and `trail/prd/cycle-5.md` § 1.1. No acceptance criterion changes: AC-14 already sorts each field in
  both directions and checks every summary row. Saved data written with three values still loads.
  The FDR's three rules are carried in `products/tracker17/docs/fdr_open_issues.md` § 2.1. Reasoning
  in `products/tracker17/docs/trail/srs/self_answer-4.md`.

**How it closes.** `product-srs` folds it on its next run like any other item, and nothing about this
file's lifecycle changes.
