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

> **No producing run wrote this file.** The PM opened it on 2026-10-12, in a route review, to carry
> item § 3.1. `product-architecture` has no record of writing it. It exists because QC-21 and
> ADR-0001 say every action saves, and an edit that changes nothing now saves nothing.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-21 and ADR-0001 say every action saves; an edit that changes no field saves nothing
- **Raised by:** PM — 2026-10-12
- **Which record:** `nfdr.md` QC-21, and `adr/0001-rule-core-behind-server-rendered-pages.md` § Decision, the `application/` bullet
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`
- **What it blocks:** nothing is blocked. Both records state as unconditional a sequence the product
  no longer follows for every action, so QC-21's review at `development-design` would read the
  intended behaviour as a breach.
- **Where it shows:** `nfdr.md:L167-L168` (QC-21) — "Each action is one call: apply a `domain` rule,
  save, then make the new state current." `adr/0001-rule-core-behind-server-rendered-pages.md:L26-L28`
  — "Each applies a `domain` rule to the current state, saves the result, and only then makes it
  current." In the product, `application/tracker.py:L105-L114` (`Tracker.edit_task`) saves and
  publishes only when the `domain` outcome reports a changed field: "one that reports none saves and
  publishes nothing". The change asked: in QC-21, qualify save-before-publication as applying to an
  action whose `domain` outcome reports a change, without giving `application` a comparison or
  membership rule of its own. ADR-0001 is Accepted and its log is append-only (`adr/README.md:L3-L6`),
  so the qualification is recorded beside QC-21 rather than by editing the ADR's text. The same
  sentence is in SDD § 3's `application` row, raised on `SDD_open_issues.md` § 5.1.
- **If a document has to be written:** none. Both records change through `product-architecture`.
- **Answer:** Confirmed with addition — take the change as asked. Qualify QC-21 the way SDD v9's § 3 `application` row now reads, since the NFDR derives from that row. An action whose `domain` outcome reports a change saves the new state and only then makes it current. An action whose outcome reports none returns the current state and saves nothing. Which outcomes report none is `domain`'s, decided per action and read off the outcome. Add three things. (1) The bound: the report is `domain`'s comparison of the submitted value with the value the page showed (SDD § 4 RT-7), never of the new state with the current one, so `application` compares nothing. Without this, QC-21's no-rule half would read a state comparison as a fix. (2) The new half's teeth: `tests/integration/test_task_tracker.py::test_tracker_unchanged_edit_never_saves` fails when an unchanged edit reaches the saver. Name it in QC-21's *verified by:*. Trace the entry to SDD § 3's `application` row (`trail/sdd/cycle-6.md` § 5.1) and move *Inputs read:* to SDD version 9. (3) ADR-0001: no superseding record and no edit. The record is Accepted, and `product-architecture` changes only its Status line. The qualification fails the significance test, because no part, edge or trade-off of the decision moves. Say in an NFDR Review Note that ADR-0001's `application` bullet is the 2026-10-06 statement and QC-21 is the current one. ADR-0004 ("on every change"), QC-49, QC-53 and QC-54 stay true as written. Reasoning: `docs/trail/architecture/self_answer-13.md` § 3.1.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
