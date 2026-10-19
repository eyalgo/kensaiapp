---
version: "1.4.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# SRS open issues — <product>

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

---

## 1. Open issues — technical questions with no answer yet

### 1.1 <the question, in one line>
- **Why it matters:** <what in the SRS depends on this — which FR / NFR / interface / constraint>
- **Answer:** <the owner fills this in>

<!-- add 1.2, 1.3, … as needed -->

## 2. Choices to confirm — the CTO drafted a best-effort answer; confirm or override

### 2.1 <the decision, in one line>
- **Drafted into the SRS:** <the choice the CTO made and wrote into SRS.md>
- **Rationale:** <why this was the best-effort call, and the PRD source it derives from>
- **If overridden:** <the blast radius of not taking the draft — which requirements, acceptance
  criteria, and notes move, and how>
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

<!-- add 2.2, 2.3, … as needed -->

## 3. Raised from downstream — an item from a seat that did not write the SRS

<Not the CTO's question. A seat working from what the SRS specifies — most often the Principal PM,
cutting a product's settled documents into seeds — hit something only the SRS can settle: a slice in
the SDD with no requirement behind it, a requirement the design silently dropped, an `FR-n` or
`NFR-n` two documents read differently.

The raising seat does not edit the SRS and does not renegotiate it. It writes here instead.>

### 3.1 <what the SRS is missing or contradicts, in one line>
- **Raised by:** <the seat — e.g. Principal PM> — <YYYY-MM-DD>
- **Tracked by:** <the 根回し Nemawashi seed watching this item, by its triple — `<project> · nemawashi · <YYYY-MM-DD>_<slug>` — never by path, which a pick or a retire moves>
- **What it blocks:** <what the raising seat could not do without it>
- **Where it shows:** <the requirement id, or the two documents and the lines that disagree>
- **If a document has to be written:** <name it, and the tool its writing seat uses — or say plainly
  that no tool exists, which is itself a finding>
- **Answer:** <the owner fills this in>

**How it closes.** `product-srs` folds it on its next run like any other item, and nothing about this
file's lifecycle changes.

<!-- add 3.2, 3.3, … as needed -->
