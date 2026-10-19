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

> **The PM opened this file on 2026-10-08, in a route review, to carry § 3.1.** The
> `product-architecture` run of 2026-10-08 folded the owner's answer to § 2.1 into QC-40 (NFDR
> version 8, RN-31; the answered file is `docs/trail/architecture/cycle-6.md`) and rewrote this file
> with what stays open.

---

## 1. Open issues — questions with no answer yet

None.

## 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item from a seat that did not write these records

### 3.1 QC-40's 30-day window for the pinned browser build closes on 2026-10-08, and no newer pin exists
> **Since this item was raised:** its "Also open" question, whether QC-40's first sentence covers
> the browser, is settled. The owner answered it as § 2.1 (`docs/trail/architecture/cycle-6.md`
> § 2.1), and NFDR version 8 folds the answer in (RN-31). QC-40's first sentence now binds the change
> that chooses a version, and the browser build `playwright==1.63.0` installs is held by the 30-day
> window alone. So the setup instructions are not blocked by the first sentence, and a dated
> exception from the window is enough to unblock the reviews. This item now asks one thing: does the
> owner record that exception, or let QC-40's block stand?

- **Raised by:** PM — 2026-10-08
- **Which record:** `nfdr.md` § QC-40 (`nfdr.md:291-308`), and its Review Notes, where QC-40 says a dated exception is recorded
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_first-project`
- **What it blocks:** every `development-design` review from 2026-10-09. QC-40's *verified by* says "a critical advisory more than 30 days old blocks the change until the pin moves or a dated exception is recorded".
- **Where it shows:** `tests/requirements.txt:12` pins `playwright==1.63.0`, which installs Chromium and Chrome Headless Shell `153.0.8010.12`, revision 1243 (`browsers.json` at tag `v1.63.0`). The Chrome Releases post of 2026-09-08 rates five CVEs Critical, all fixed in `153.0.8010.36`: CVE-2026-87438, -87464, -87488, -87527 and -87628. Counted from that post, they are 30 days old on 2026-10-08, the last day QC-40's window allows. PyPI's newest Playwright is still 1.63.0, uploaded 2026-09-15 (`https://pypi.org/pypi/playwright/json`, read 2026-10-08), so the pin cannot move. QC-40 leaves two other ways out: replace or remove the dependency, or have the owner record a dated exception with its reason in a Review Note. Neither is recorded. Also open: does QC-40's first sentence, "a test dependency with a known critical vulnerability is not installed by the setup instructions", cover the browser? The README's "Running the tests" section now installs it with `python -m playwright install chromium`. If it does, the window does not apply to the browser, and the setup instructions are blocked today.
- **If a document has to be written:** none — the fold is an edit to `nfdr.md`, by `product-architecture`. An exception is the owner's to record. Replacing the browser-driving library would also move SDD § 4 RT-4 and the end-to-end layer it pins.
- **Answer:** Record the dated exception, from 2026-10-10 to 2026-11-07, for Chromium `153.0.8010.12` as installed by `playwright==1.63.0`. The reason: no newer Playwright exists on PyPI, so the pin cannot move, and the browser drives only tracker17's own local pages in tests. Ending the exception, by moving the pin or renewing it with a reason, is a row in the instance's upkeep register, `system/upkeep.md`.

**How it closes.** `product-architecture` folds it on its next run like any other item here.
