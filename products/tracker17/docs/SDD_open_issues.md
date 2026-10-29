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
> answers the item — `cto`, `cpo` or `cdo`. An item with no usable value is answered in the seat of
> the skill that produced this file.
>
> **§ 5 names a raiser from outside the SDD's lanes entirely** — a seat reading the SDD long after it
> settled and finding something only the SDD can fix.

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

### 5.1 § 6 S-1 and § 4 RT-4 disagree on whether the prerequisites section names uv
- **Raised by:** PM — 2026-10-29
- **Seat:** cto
- **Tracked by:** `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv`
- **What it blocks:** the README's prerequisites section cannot meet both sentences. § 6 S-1
  *Artifact* (`SDD.md:832-834`) says the prerequisites section holds "for the test suite only, uv
  and a network connection needed once". § 4 RT-4 (`SDD.md:302-305`) says "the tracker's own setup
  names it nowhere, because RT-1 and RT-2 hold without it", and ADR-0013 § Decision
  (`adr/0013-standard-library-only-no-web-framework-suite-environment-made-by-uv.md:35`) says the
  same. The SDD does not say whether the prerequisites section counts as the tracker's own setup.
- **Where it shows:** `products/tracker17/README.md:17-29`, `### What you need`, names Python 3.11 or
  later, the operating systems and the tests' one-time network connection, and not uv; uv is named
  first in `### Running the tests` (`README.md:91`). So the README holds RT-4's reading today and
  falls short of S-1's.
- **If a document has to be written:** none — the SDD settles which sentence holds; the README
  follows it.
- **Answer:** <the owner fills this in>

**How it closes.** `product-sdd` folds it on its next run like every other item in this file, and
the trail copy and the delete-when-empty behaviour are unchanged.
