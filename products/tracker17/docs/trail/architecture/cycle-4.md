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

`SDD` is `products/tracker17/docs/SDD.md`. `QC-n` and `RN-n` are entries of
`products/tracker17/docs/nfdr.md`. The answered round of 2026-10-07, both § 3 items the PM raised, is
kept at `products/tracker17/docs/trail/architecture/cycle-3.md`; this file now holds only the item
that round left unanswered.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

### 2.1 RN-15 names the one SDD open question left, and says where SDD version 6 closed the other two

> The `companion-self-answer` run of 2026-10-07 raised this item, reading SDD version 6 against
> `nfdr.md` version 3; its reasoning is `products/tracker17/docs/trail/architecture/self_answer-5.md`
> § *Raised on this document*. The `product-architecture` run of the same day drafted it into the
> records.

- **Lands in:** `nfdr.md` RN-15, recorded by RN-23; `adr/0003-no-script-in-any-page.md` and
  `adr/0007-text-counted-once-in-domain-in-code-points.md`, which are not edited
- **Drafted into the records:** `nfdr.md` version 4's RN-15 names one SDD open question, whether
  Chromium honours `autofocus` on an element that is not a form control (ADR-0003). It says where
  the line-break question (ADR-0007; SDD RN-36) and the port question (QC-30; SDD RN-35) closed. It
  says that the question ADR-0007 calls open is answered, and that the item ADR-0003 cites as the
  second is now the list's only one, so a reader following either record's citation finds the answer
  there. Neither ADR is edited or superseded.
- **Rationale:** version 3's RN-15 counted three SDD open questions, as SDD version 4 held them. SDD
  version 6 holds one (`SDD.md` § Open Questions; RN-35, RN-36). ADR-0007's *Dependence* paragraph
  calls the line-break question open as "the first item", and ADR-0003's `## Traces to` cites
  "§ Open Questions, the second item". Neither decision moved: SDD RN-36 records each line break
  counted as one, and `web` turning CR LF into LF, which is what ADR-0007 decided. Both records are
  Accepted, so a citation of theirs that went stale is answered in the NFDR, not by rewriting them.
- **If overridden:** with "leave it", RN-15 goes back to counting three questions and describes an
  SDD that no longer exists; `Inputs read:` still names SDD version 6, because it records what the
  revision read. With "supersede both ADRs", two new records restate unchanged decisions only to move
  a citation, and ADR-0003 and ADR-0007 are marked superseded.
- **Confirm or override:** confirm, with an addition: the drafted RN-15 stands, and so does leaving
  both ADRs unedited and unsuperseded, but RN-15's claim that "a reader following either citation finds the
  answer" in this note does not hold as written — each ADR's citation leads into SDD § Open Questions,
  not into the NFDR. Restate that reason in RN-15 and RN-23: ADR-0003's cited item is the list's only
  one, and SDD RN-36, which the list names, records ADR-0007's closed question. Add "see RN-15" to
  QC-9's and QC-34's trace tags, so that each ADR's `## Binds` line reaches RN-15 too. Reasoning:
  `products/tracker17/docs/trail/architecture/self_answer-6.md` § 2.1

## 3. Raised from downstream — an item from a seat that did not write these records

None.
