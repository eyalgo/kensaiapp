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

### 2.1 The header, § 12 and § 4 RT-4 still read the records at ADR-0012 and NFDR version 18
- **Raised by:** CTO
- **Seat:** cto
- **Drafted into the SDD:** nothing yet — the lean is this: the header's *Inputs read* reads
  ADR-0001 to ADR-0013, ADR-0002 Superseded by ADR-0013, NFDR version 19, and
  `products/tracker17/docs/architecture_open_issues.md` live again with one item; § 12 counts
  thirteen records, ADR-0001 to ADR-0013; and RT-4 names ADR-0013 as the record of the suite's
  environment, the way RT-8 names ADR-0011 and RT-11 names ADR-0012.
- **Rationale:** three facts in the document are false on disk. The header's *Inputs read* says
  "ADR-0001 to ADR-0012 … NFDR Settled (version 18 … `products/tracker17/docs/architecture_open_issues.md`
  no longer exists, removed at `66e29daa9`" (`SDD.md:6`); § 12 says "ADR-0001 to ADR-0012"
  (`SDD.md:1636-1637`); and RT-4 (`SDD.md:299-339`) names no record while every other condition
  with a record names it. `adr/README.md` lists ADR-0013, Accepted 2026-10-29, and ADR-0002
  "Superseded by ADR-0013"; ADR-0013 § Context says it follows "SDD version 15 § 4 RT-4"; `nfdr.md`
  is at version 19, its header tracing QC-19, QC-36, QC-39, QC-43, QC-59 and QC-60 to ADR-0013
  (both at `909fc536c`); and `architecture_open_issues.md` was opened again on 2026-10-29 by the PM
  with its one item, § 3.1 on QC-40, unanswered (`f86543f50`). What QC-40 asks is the Principal
  Architect's, carried on that companion, not this document's. RN-63's "a new record superseding
  it is theirs to write" is a dated record of that round and stays as written.
- **If overridden:** nothing moves in any slice, fence or edge. The three lines stay false, and a
  reader of RT-4 finds no record for a decision the records hold, and is told a companion is gone
  that is live.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

> **No producing run wrote this item.** A `companion-self-answer` run raised it on 2026-10-29 while
> answering § 5.1, after reading the header, RT-4 and § 12 against `adr/README.md`, ADR-0013 and
> `nfdr.md`'s header. `product-sdd` has no record of writing it. The fold's own input catch-up may
> reach the same lines unprompted, as it did for cycle 11's § 2.1 (RN-60); the item is here so that
> it is not missed.

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
- **Answer:** § 6 S-1 holds, and § 4 RT-4 is reworded to agree with it. The prerequisites section
  names uv, for the test suite only, beside the one-time network line, and the section on running
  the suite says how to install it. The prerequisites section is not "the tracker's own setup":
  that phrase in RT-4 means the tracker's prerequisites, Python 3.11 or later on macOS or Linux,
  and the two commands RT-2 gives, and RT-4 says so in those words. A suite-only prerequisite,
  named as the suite's, sits in the prerequisites section the way RT-1 already places the suite's
  one-time network connection there. The inputs put it there too: SRS FR-4's first bullet has the
  prerequisites say that setup needs a network connection once "to fetch the declared
  dependencies", which only the tests have (RT-4), and UXD UX-S1 lists "prerequisites (including
  the one-time network connection setup needs)"; RN-62 already reads uv as joining that list.
  SRS C-7 and AC-3 do not move: a prerequisite stated as the suite's leaves the tracker's setup at
  two commands on a machine with Python alone, as the network line already does. A reader checking
  what they need (UXD UX-F1) then learns of uv before the suite's section rather than at it.
  `products/tracker17/README.md`'s `### What you need` is owed one sentence, and which unit
  carries it is the PM's. Reasoning: `products/tracker17/docs/trail/sdd/self_answer-16.md`.

**How it closes.** `product-sdd` folds it on its next run like every other item in this file, and
the trail copy and the delete-when-empty behaviour are unchanged.
