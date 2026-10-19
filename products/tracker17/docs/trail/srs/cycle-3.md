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

Every `SDD §` reference below is to `products/tracker17/docs/SDD.md`, version 2. `SRS.md`,
`UXD.md`, `DESIGN.md` and `CONTENT.md` are the files of those names in `products/tracker17/docs/`.

---

## 1. Open issues — technical questions with no answer yet

None.

## 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override

### 2.2 The open question on the runtime is answered, and closes

> **Raised by a `companion-self-answer` run on 2026-10-06, not written by a `product-srs` run.** That
> run was answering item 2.1 and read `SRS.md` whole. The second item of `SRS.md` § Open Questions
> still reads as open, but the SDD has answered it. This run's reasoning is in
> `products/tracker17/docs/trail/srs/self_answer-2.md`, under § Raised on this document.

- **Drafted into the SRS:** nothing yet. The one item left in `SRS.md` § Open Questions reads "The
  prerequisites FR-4 names follow from the SDD's choice of runtime, and C-7's ten-minute bound is
  measured against them. AC-3 is the check once the SDD has chosen." The proposed change removes
  that item. No requirement changes. FR-4 already lists the prerequisites in general terms, C-7
  already sets the bound, and AC-3 already checks it.
- **Rationale:** the SDD has made the choice the item waits for. SDD § 4 RT-1 reads "The tracker
  runs on Python 3.11 or later and imports nothing outside the Python standard library". It ends
  "*settles SRS § Open Questions, the second item*", and it is confirmed in
  `products/tracker17/docs/trail/sdd/cycle-1.md` § 2.1. An item marked `[OPEN]` that is no longer
  open says the SRS still waits on something. The runtime itself stays the SDD's, because it is
  how the system is built and not what it must do. So this change closes the question and copies
  nothing from RT-1 into the SRS.
- **If overridden:** the item stays, and the SRS keeps reading as if it waits on a choice already
  made. Copying the runtime into FR-4 is the other option. It would put a design choice in the
  SRS, and the SRS's own header keeps the how out ("Keep the **how** … out").
- **Confirm or override:** confirm, with one addition. The last item of `SRS.md` § Open Questions is removed, no requirement changes, and nothing from SDD § 4 RT-1 is copied into the SRS. (1) Closing the question does not wait for the SDD to reach Settled. No SRS requirement names the runtime. FR-4 asks for the prerequisites in general terms, C-7 sets the bound, and AC-3 checks it against whatever prerequisites the setup instructions state. So if a later round changed RT-1, the SRS would still be true, and AC-3 would check against the new prerequisites. FR-4's line that setup needs a network connection once also stays true under RT-1: the declared dependencies are the test suite's, and FR-4's instructions include setting the suite up. Closing this question leaves SDD § 4 RT-1 and SDD RN-3 pointing at an SRS open question that no longer exists. The SDD's companion carries that change, with the SDD's other stale references to SRS version 3, `products/tracker17/docs/SDD_open_issues.md` § 2.2. Reasoning in `products/tracker17/docs/trail/srs/self_answer-3.md`.

## 3. Raised from downstream — an item from a seat that did not write the SRS

None.
