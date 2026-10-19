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
> item § 3.1. `product-srs` has no record of writing it. It exists because PRD v6 states a want about
> what a reader reads first, and the SRS still reads PRD § Purpose as intent with no requirement.

---

## 1. Open issues — technical questions with no answer yet

None.

## 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write the SRS

### 3.1 PRD § Purpose now wants the first thing a reader reads to name both purposes; the SRS states neither the second purpose nor that want
- **Raised by:** PM — 2026-10-11
- **Tracked by:** none — no 根回し Nemawashi seed carries the README's opening yet. `docs/what_left.md`
  records the want, at `20f9076c5`.
- **What it blocks:** walking the want against a settled requirement. Every slice is cut from the
  SRS through the SDD, and no SRS requirement or SDD slice asks for the README's opening to change, so
  no seed can be cut for it.
- **Where it shows:** `PRD.md:23-29` (PRD v6) — tracker17 "is also kensaiapp's own testing ground",
  and "A reader learns both purposes from the first thing they read about tracker17". `SRS.md:30-38`
  (§ 1) states only the worked-example purpose. `SRS.md:620-621` (RN-18) drops PRD § Purpose as
  intent that requires no behaviour, which no longer holds of its last sentence. In the product,
  `README.md:3` names only the first purpose: `grep -n -i 'testing ground' products/tracker17/README.md`
  prints nothing, exit 1.
- **If a document has to be written:** none. `SRS.md` changes through `product-srs`, and the
  documents below it change through their own producing skills.
- **Answer:** Yes. The SRS takes PRD v6's second purpose, and one requirement and one criterion for
  its want. (1) § 1 Purpose adds the second purpose beside the first: tracker17 is also kensaiapp's
  own testing ground, and building it with kensaiapp is how issues in kensaiapp are found and fixed
  (PRD § Blurb, § Purpose). (2) A new requirement in § 3.1, beside FR-4, takes the next free number,
  FR-41. The README is the document in a copy of tracker17 that carries the written setup
  instructions FR-4 lists, and a reader arrives at it first (PRD § UX Notes, Arrival). Its opening
  paragraph, under its title and before anything else, names both purposes: the worked example and
  kensaiapp's testing ground. Of the earlier versions it names only tracker16-X. It traces to the
  last sentence of PRD § Purpose and to the owner's answer at `trail/prd/cycle-6.md` § 1.1, "let the
  README tell it too". The words are `CONTENT.md`'s, not the SRS's. (3) A new criterion, AC-21:
  the owner reads the README's opening paragraph and finds both purposes named. It is verified by
  inspection, and it can be run again on any later release. (4) RN-18 changes: § Purpose is carried by
  § 1 as intent, except its last sentence, which FR-41 carries. The testing-ground purpose adds no
  behaviour to the tracker. The tracker records nothing about kensaiapp, and NFR-5's no-telemetry
  rule stands as written. (5) The Inputs line reads PRD v6. The reasoning is in
  `products/tracker17/docs/trail/srs/self_answer-5.md`.

**How it closes.** `product-srs` folds it on its next run like any other item, and nothing about this
file's lifecycle changes.
