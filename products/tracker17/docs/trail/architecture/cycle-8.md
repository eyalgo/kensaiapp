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

> **No producing run wrote this file.** The PM opened it on 2026-10-11, in a route review, to carry
> item § 3.1. `product-architecture` has no record of writing it. It exists because ADR-0003's
> Dependence still calls the not-a-control focus case unverified, and a test of it now passes.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 ADR-0003's Dependence still calls the not-a-control focus case unverified; one form of it is now checked
- **Raised by:** PM — 2026-10-11
- **Which record:** `adr/0003-no-script-in-any-page.md` § Consequences, **Dependence**
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`
- **What it blocks:** nothing is blocked; the record's Dependence reads as wholly unverified, so a
  reader cannot tell which of its three focus tests is still owed before the decision is settled.
- **Where it shows:** `adr/0003-no-script-in-any-page.md:L45-L50` — whether Chromium "focuses an
  element that is not a control, brings it into view and reads its description is not verified", and
  three focus tests "settle it". In the product, `tests/e2e/test_people.py:L58-L78` asserts, in
  Chromium, that after an add on People the added name (a `span`, not a control) holds keyboard
  focus, is in the viewport, and has the completion line as its computed accessible description, with
  no script on the page. Measured on `main` at `641bb58b5`: `pytest products/tracker17/tests/e2e/` →
  `18 passed`. Still unchecked: the confirmation case, and assistive-technology speech, which a
  computed accessible description does not prove. The change asked: narrow the Dependence to those,
  with the no-script decision left in force.
- **If a document has to be written:** none. The record changes through `product-architecture`.
- **Answer:** override — narrow what reads unverified, with the no-script decision left in force, but
  not in ADR-0003. The record is Accepted and stays as written: an accepted record is never reworded,
  and a superseding record is for a decision that moved, which this one did not. Its Dependence was
  true on its date and cites SDD § 11 R-2 and § Open Questions, which SDD version 8 has already
  narrowed (SDD RN-41). The sentence that is false now is NFDR RN-15, the note QC-34's trace tag
  leads to from ADR-0003's `## Binds`. It still calls the not-a-control case open, and says
  ADR-0003's cited "second item" is the list's only one, where the list now has two. Revise RN-15
  to say four things. First, focus and in-view are verified on a form control (SDD RN-36) and on a
  focusable element that is not a control (`tests/e2e/test_people.py`, 18 passed at `641bb58b5`,
  Chromium 153.0.8010.12; no product code has moved since). Second, two cases stay open: the
  confirmation, which `status-moves`' tests settle, and assistive-technology speech, which none of
  ADR-0003's three tests reaches and one VoiceOver pass settles, with no slice requiring it. Third,
  both SDD Open Questions bear on ADR-0003, the cited second item being the speech one. Fourth, the
  passing tests stay as regression triggers, and a failure lands as a record superseding ADR-0003.
  Name SDD version 8 under `Inputs read:`. Reasoning:
  `products/tracker17/docs/trail/architecture/self_answer-12.md`.
