---
version: "1.7.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# SDD open issues — <product>

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

---

## 1. Open issues — questions with no answer yet

### 1.1 <the question, in one line>
- **Raised by:** <CTO | CPO | CDO>
- **Seat:** <seat>
- **Why it matters:** <what in the SDD depends on this — which section, which slice by slug>
- **Answer:** <the owner fills this in>

<!-- add 1.2, 1.3, … as needed -->

## 2. Choices to confirm — a best-effort answer was drafted; confirm or override

### 2.1 <the decision, in one line>
- **Raised by:** <CTO | CPO | CDO>
- **Seat:** <seat>
- **Drafted into the SDD:** <the choice made and written into SDD.md>
- **Rationale:** <why this was the best-effort call, and the upstream source it derives from>
- **If overridden:** <the blast radius of not taking the draft — which sections, slices and edges
  move, and how>
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

<!-- add 2.2, 2.3, … as needed -->

## 3. Cut calls to confirm — where the slicing could reasonably have gone another way

<This section is the SDD's own, and has no twin in the upstream companions. The four tests in
`SDD.md` § 5 settle most cuts on their own; this section holds the ones they do not — a place where
two defensible cuts pass all four, and the choice between them is the owner's taste, appetite for
risk, or knowledge of what is coming next.

A cut that fails one of the four tests is not an item here. It is a defect, and it is fixed in the
SDD rather than asked about.>

### 3.1 <the cut, in one line — e.g. "`checkout-flow` is one slice, not three">
- **Raised by:** <CTO | CPO | CDO>
- **Seat:** <seat>
- **The cut as drafted:** <what § 6 currently says: which slices exist and where the boundary sits>
- **The alternative cut:** <the other defensible shape, and which slices it would produce instead>
- **What changes if it moves:** <the order in § 7, what lands first, and what is provable earlier or
  later as a result>
- **Why it is yours to call:** <what the four tests do not decide here — appetite for risk, the
  order you want value in, or something upstream that is not written down>
- **Keep or re-cut:** <"keep", or "re-cut: <the shape to take instead>">

<!-- add 3.2, 3.3, … as needed -->

---

## 4. Disagreements — two seats hold different positions and neither yields

<This section is the one bucket that does not have a raising seat, because it does not have one
raiser. §§ 1–3 each assume a call that could not be settled and was asked; here two seats each hold
a position on it, differently, and both positions survived the round — typically the CTO's
technical position against an answer a seat gave in an earlier round.

**Both positions are recorded. Neither is averaged.** A middle written into the SDD is a position no
seat holds and no seat will defend when it turns out wrong. What goes into `SDD.md` is whichever
position you pick; what stays here until you pick is both.

This is not a disagreement about who decides a section — that is answered by `SDD.md` § *Who decides
what*, and a draft that decides another seat's column has found an open issue of a different kind.
This is two seats inside their own lanes reaching incompatible conclusions.>

### 4.1 <what is disagreed, in one line>
- **Held by:** <seat> — *position:* <what this seat holds, in its own terms>
- **Held by:** <seat> — *position:* <what the other seat holds, in its own terms>
- **Seat:** <seat>
- **Where it bites:** <the section or the slice slug that reads differently depending on the answer>
- **What each seat gives up if the other wins:** <one line per seat — the cost each is arguing
  against, which is usually the fastest way to see what the disagreement is really about>
- **What the SDD says meanwhile:** <what § 6 or the section currently states, and which position it
  reflects — or that it states neither and the point is left open in the text>
- **Your call:** <the position to take, by seat — or "neither: <what to do instead>">

<!-- add 4.2, 4.3, … as needed -->

## 5. Raised from downstream — an item from a seat that did not write the SDD

<None of the three lane seats. The SDD is the most-read document in the chain, and the seat
that reads it hardest is the Principal PM cutting it into seeds. What it finds and cannot fix
itself lands here: a slice that cannot fill one of § 8's fields, an edge in § 7 drawn coarser than
the work it constrains, a document § 5 or § 6 names that nobody has written, two settled documents
whose designs disagree.

**A § 7 edge is a finding, not a re-cut.** The raising seat cuts against the SDD as it stands and
says here that the edge looks wrong; it does not reorder the slices on its own judgment. The owner's
ruling, 2026-08-25.

**One kind of item here is not about a gap at all.** A settled SDD can be complete and still stop
satisfying its template, because `sdd_template.md` moved underneath it — a section gained a shape,
a column, or a form its value has to take. Nothing is missing from the document; what changed is
what the document is measured against. That item uses the second shape below, which asks what the
re-cut owes rather than what is absent, and it is the only item here a downstream seat raises about
a document that is not at fault.>

### 5.1 <what the SDD is missing, or what it cannot fill, in one line>
- **Raised by:** <the seat — e.g. Principal PM> — <YYYY-MM-DD>
- **Seat:** <seat>
- **Tracked by:** <the 根回し Nemawashi seed watching this item, by its triple — `<project> · nemawashi · <YYYY-MM-DD>_<slug>` — never by path, which a pick or a retire moves>
- **What it blocks:** <the slice that could not be cut, the field that could not be filled, the seed
  that has nothing to trace to>
- **Where it shows:** <the slice slug, the § 7 row, or the § 6 field that is unfillable>
- **If a document has to be written:** <name it, where the SDD names it, and the tool its writing
  seat uses — where no tool exists, that absence is itself the finding>
- **Answer:** <the owner fills this in>

**How it closes.** `product-sdd` folds it on its next run like every other item in this file, and
the trail copy and the delete-when-empty behaviour are unchanged.

### 5.2 <the template moved under this document — what the re-cut owes, in one line>
- **Raised by:** <the seat — e.g. Principal PM> — <YYYY-MM-DD>
- **Seat:** <seat>
- **What moved:** <the section of `sdd_template.md` that changed, and what it now requires that it
  did not when this SDD was written>
- **Why it matters here:** <what now reads this section, and what it cannot do until the re-cut —
  a tool that parses it, a seat that cuts from it>
- **What the re-cut owes, per row or per section:** <the specific work — a value per row, a rename,
  a shape change. Name what is already correct too: a re-cut that touches more than it owes is the
  cost this slot exists to bound>
- **What it may leave alone:** <the halves of the section that already satisfy the new shape, and
  any field the template makes optional — an SDD is not obliged to invent information its design
  never captured>
- **Answer:** <the owner fills this in>

<!-- add 5.3, 5.4, … as needed -->
