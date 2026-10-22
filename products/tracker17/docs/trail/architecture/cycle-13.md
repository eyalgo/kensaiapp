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

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

> § 2.1, the history-admission boundary, was answered and is folded into
> `adr/0010-pending-confirmation-answered-202-move-pages-not-stored.md` and `nfdr.md` QC-63
> (`docs/trail/architecture/cycle-12.md`). § 2.2 keeps its number so the reasoning that raised it
> still points at it.

### 2.2 RN-15 and RN-42 still call the EX-6 confirmation open, and SDD version 11 counts it verified

> A `companion-self-answer` run raised this item on 2026-10-21, in the Principal Architect's seat,
> while answering § 2.1 of this file. No producing run wrote it. It came from reading `nfdr.md`
> version 13 against SDD version 11. Its reasoning is
> `products/tracker17/docs/trail/architecture/self_answer-16.md` § *Raised on this document*.

- **Lands in:** `nfdr.md` RN-15, recorded by a new Review Note. RN-42 is a dated record and is not
  edited. `adr/0003-no-script-in-any-page.md` is not edited.
- **Drafted into the records:** nothing. This run writes no record. What the fold is handed: RN-15
  says the EX-6 confirmation is verified. Its three parts are the sentence alone holding focus, the
  double press that never confirms, and back-out returning focus. SDD § 11 R-2 at version 11 names
  the four tests in `tests/e2e/test_moves.py` that verify them, and records that all four passed in
  a fresh clone at `9b05680c7`, 67 passed, with `playwright==1.63.0` and Chromium 153.0.8010.12.
  Assistive-technology speech for EX-14 stays as the one open case, which one VoiceOver pass
  settles, as SDD § Open Questions now holds it alone. The result is tied to its commit, by RN-42's
  own rule. ADR-0003 is neither edited nor superseded, because its decision did not move and its
  *Dependence* was true on its date.
- **Rationale:** `nfdr.md` RN-15 reads "What stays open is two cases. The first is the confirmation
  of SDD § 4 EX-6", and RN-42 reads "so both stay: the EX-6 confirmation, which SDD § 6
  `status-moves` settles". SDD version 11 (`9c7db2266`) settled it: § 11 R-2 counts the
  confirmation case verified, and § Open Questions keeps only the assistive-technology case. A
  `development-design` review that reads RN-15 meets a case as open that the SDD has closed.
- **If overridden:** with "leave it", RN-15 keeps counting two open cases where the SDD holds one,
  and a reader following ADR-0003's `## Binds` line through QC-34 to RN-15 is told a verified case is
  unsettled.
- **Confirm or override:** confirm, with two additions. RN-15 is owed the change, and SDD version 11
  holds every fact the draft hands the fold: § 11 R-2 names the four `tests/e2e/test_moves.py` tests,
  all four are on disk at `HEAD`, and `git diff --stat 9b05680c7 HEAD` over the product outside
  `docs/` lists one line of `README.md` and no code. First, the browser is stated as R-2 states it,
  and not as the draft does. R-2 records the run with the pinned library, `playwright==1.63.0`. It
  has the build asserted by the run, `153.0.8010.12`, on the full Chromium of that install, through
  `test_history_matrix_revalidates_current_saved_status`. The four focus tests drive the headless
  shell the same install provides. RN-15 writes that, so it claims no more about the build than the
  SDD does. Second, RN-15's count and its two citation sentences move with the list. SDD § Open
  Questions now holds one item, the assistive-technology question, where version 10 held two. So
  RN-15's "Two SDD Open Questions bear on these records" now reads one. "ADR-0003's `## Traces to`
  cites the list's second item, which is now the question of assistive-technology speech" now says
  that question is the list's only item. "ADR-0007's *Dependence* calls the line-break question
  open as the list's first item, which now names SDD RN-36" now says the list's first item is the assistive-technology question and names no RN-36, and
  that SDD RN-36 itself records the line-break question closing. Neither record is edited or
  superseded, because neither decision moved and each citation was true on its date (RN-15's own
  rule). QC-9's and QC-34's trace tags still name RN-15, and § 10 gains no row. Reasoning:
  `products/tracker17/docs/trail/architecture/self_answer-17.md`

## 3. Raised from downstream — an item from a seat that did not write these records

None.
