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

> **No producing run wrote this file.** The PM opened it on 2026-10-27, after reading the product's
> filter form against these records, to carry § 3.1. `product-architecture` has no record of writing it.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 ADR-0006 and QC-7 say every form submission is redirected; the filter form is answered with a page
- **Raised by:** PM — 2026-10-27
- **Which record:** `adr/0006-last-action-travels-in-the-page-address.md` (line 20, "Every submission
  is answered by sending the browser to a page address") and NFDR QC-7 ("every form submission is
  answered by sending the browser to a page address", `nfdr.md:L73-L78`)
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_narrow-and-sort`
- **What it blocks:** nothing is blocked. The project page now carries a filter form sent with
  `method="get"` (`web/pages.py:L1189`); Apply, its reload and Clear are answered with the project
  page, 200, and save nothing. QC-7's route test treats them as non-submissions
  (`tests/integration/test_routes.py:L1090-L1093`). Neither record says a GET form is not a
  submission, so held to their words they are false of the product, and the sort controls and the
  All tasks list (FR-36, UX-S7) add more forms of the same kind.
- **Where it shows:** ADR-0006 § Decision and QC-7's first obligation and its *verified by* ("sends
  each submission and asserts a redirect"). The record owed: whether a submission is a form that asks
  for a change, so a GET form that only narrows or orders a list is answered with the page — or the
  opposite, with the redirect such a form is then owed.
- **If a document has to be written:** none; the wording of ADR-0006 and QC-7 only. SDD § 4 RT-8
  carries the same sentence and is raised on the SDD's companion.
- **Answer:** A submission is a form sent with `method="post"`, a request for a change. A form sent
  with `method="get"` is a read: the tracker answers the address the browser built with its page,
  200, saves nothing and sends no redirect. This is SDD version 12 § 4 RT-8 (RN-53), settled
  2026-10-27, and these records follow it. **ADR-0006 is superseded, not edited.** A new record,
  ADR-0011, restates ADR-0006's decision whole with the word defined: a `get` form is a read, and
  its refusal is answered with the page at the asked address, the reason beside the control.
  ADR-0011 adds RT-8's purpose for the redirect, the standard's GET "Mutate action URL" as the
  reason the word needs defining, and § 11 R-10's bound on a `get` form's values (seven keys under
  6,000 of 65,536 bytes) to its *Dependence*. ADR-0006's Status line becomes `Superseded by
  ADR-0011`. Held to its words and the standard's, ADR-0006 owed the filter form a redirect, so this
  is a change of decision, which the log records by supersession. **QC-7 is revised in place:** it
  defines the word as RT-8 does, and its *verified by* names
  `test_filter_apply_reload_and_clear_are_pages_that_save_and_set_nothing` beside the route
  enumeration. QC-7 traces to ADR-0011 and SDD RN-53. QC-8 keeps its words and its ADR-0006 trace
  re-points to ADR-0011. QC-32's "not a submission" now reads by QC-7's definition and keeps its
  words. Notes that are dated records are not edited. No code or test changes. Reasoning:
  `products/tracker17/docs/trail/architecture/self_answer-18.md` § 3.1.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
