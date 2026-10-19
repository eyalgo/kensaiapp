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
> item § 3.1. `product-architecture` has no record of writing it.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 RN-15 says no product code has moved since the People focus run at `641bb58b5`; the comment code has
- **Raised by:** PM — 2026-10-12
- **Which record:** NFDR Review Notes, RN-15 (`nfdr.md:L730-L761`), which ADR-0003's focus tests
  lean on
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`
- **What it blocks:** nothing is blocked. RN-15 rests its "what is verified" on the claim that the
  tree has not moved since the recorded run, and that claim is now false, so a reader can no longer
  tell which tree the recorded Chromium result describes.
- **Where it shows:** `nfdr.md:L736-L738` — "Both passed at `641bb58b5` (`pytest
  products/tracker17/tests/e2e/`, 18 passed), with playwright 1.63.0 and Chromium 153.0.8010.12
  (SDD § 11 R-2, RN-41), and no product code has moved since." Measured:
  `git diff --stat 641bb58b5 4f6f59752 -- products/tracker17/web products/tracker17/domain` →
  `12 files changed, 2350 insertions(+), 26 deletions(-)`, `domain/comments.py` among them. The tree
  now also carries two comment focus tests, `tests/e2e/test_comments.py:L89`
  (`test_keyboard_comment_add_brings_the_new_comment_into_view_and_focus`) and `:L171`
  (`test_keyboard_comment_refusals_keep_text_focus_and_description`); `pytest
  products/tracker17/tests/e2e/` at `4f6f59752`, in a fresh clone with playwright 1.63.0, gave
  `33 passed`. The change asked: keep the dated People result as evidence for `641bb58b5`, drop
  "no product code has moved since", and state the comment focus tests with their own measured
  verdict. The two cases RN-15 leaves open are not touched by this.
- **If a document has to be written:** none. `nfdr.md` changes through `product-architecture`.
- **Answer:** Confirm the change, with one thing added. RN-15 should tie each test result to the commit
  it was measured at, and stop claiming that nothing has moved since — any such sentence goes false at
  the next merge. A reader checks staleness with `git diff <commit>`. So: keep the People result as
  evidence at `641bb58b5` (18 passed). Add the two comment tests (`tests/e2e/test_comments.py:L89`,
  `:L171`) as a second element that is not a control, focused with `tabindex="-1" autofocus`
  (`web/pages.py:L948`), with their own result: 33 passed at `4f6f59752` (PM). This run re-measured
  it in a fresh clone at `c0e4d65f4`, whose code and tests match `4f6f59752`: 33 passed,
  playwright 1.63.0, Chromium 153.0.8010.12. The two open cases, ADR-0003 and QC-34 stay as they are.
  Reasoning: `products/tracker17/docs/trail/architecture/self_answer-15.md`.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
