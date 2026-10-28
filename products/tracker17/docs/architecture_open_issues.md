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

> **No producing run wrote this file.** The PM opened it on 2026-10-28, after reading the product's
> deletion tests against NFDR QC-63, to carry § 3.1. `product-architecture` has no record of writing it.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-63 still carries the task deletion's 202 as unmet and the project deletion's pages as unbound
- **Raised by:** PM — 2026-10-28
- **Which record:** `nfdr.md` § 1.1 QC-63, its *verified by:*
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_delete-and-rename`
- **What it blocks:** nothing is blocked. QC-63 reads as an obligation the product does not meet,
  and its verifier list names a test to come where tests exist.
- **Where it shows:** QC-63 says "**The task deletion's 202 is unmet** (RN-50)", that its verifiers
  "land with the change that aligns the product", and that "**The project deletion's pages** are
  bound when they land" (`docs/nfdr.md:L113-L118`). The product now answers both deletions' pending
  confirmations 202 and their other pages with `no-store`: `tests/integration/test_delete_routes.py`,
  `test_live_delete_views_have_their_response_policy`, asserts 202 on `?delete_confirm` (L455);
  `tests/integration/test_delete_project_routes.py`,
  `test_project_delete_response_policy_matches_rendered_state` (L268), covers the project deletion's
  pages; and the history tests are `tests/e2e/test_delete_task.py`,
  `test_confirmation_is_loaded_afresh_after_confirming` (L182), and `tests/e2e/test_delete_project.py`,
  `test_project_confirmation_is_loaded_afresh_after_confirming` (L290). `pytest
  products/tracker17/tests/` exited 0 with 2556 passed on 2026-10-28. QC-63 should name these as its
  verifiers and drop the unmet line; the obligation itself is unchanged.
- **If a document has to be written:** none — `nfdr.md` itself, by `product-architecture`.
- **Answer:** <the owner fills this in>

**How it closes.** `product-architecture` folds it on its next run like any other item here.
