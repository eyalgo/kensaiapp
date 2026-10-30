# FDR open issues — tracker17

> Companion to `fdr.md`. The Principal PM authored the FDR non-interactively; this file holds what the
> run could not settle from its inputs — the PRD, the SRS and the SDD.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-fdr`. It folds your answers into the FDR and drops the resolved items. When nothing is
> left open, `product-fdr` **deletes this file**: no file = the FDR is done.
>
> Your answers are never thrown away. Each time the Principal PM folds them in, it first copies this
> file whole to `docs/trail/fdr/` — so what you decided, and why, stays readable and citable for good.
>
> **§ 3 is the odd one, and worth reading twice.** The Principal PM writes the FDR *and* is the seat
> most likely to raise an item against it later, cutting the same product's documents into seeds. The
> two are different acts at different times, and § 3 keeps the later one visible instead of letting
> it be quietly folded back into § 1 as though the authoring run had asked it.

> **No producing run wrote this file.** It was opened on 2026-10-30 by the PM, to carry § 3.
> `product-fdr` has no record of writing it.

---

## 1. Open issues — behavioural questions with no answer yet

None.

## 2. Choices to confirm — the Principal PM drafted a best-effort answer; confirm or override

None.

## 3. Raised from downstream — an item raised against the FDR after it settled

### 3.1 R-20's "the tracker's next save replaces it" does not hold while the unreadable-data page shows
- **Raised by:** PM — 2026-10-30
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. The rule locks a behaviour one startup mode does not have.
- **Where it shows:** `docs/fdr.md:L98-L100`. A tracker showing the unreadable-data page has no save, so an outside change is not replaced; it stays unread until the next start (`web/routes.py`, `UnreadableSite`, which holds no reader or saver). "Read once, at start" holds in both modes.
- **If a document has to be written:** none — `fdr.md` itself, by `product-fdr`.
- **Answer:**

### 3.2 R-105's not-found page does not hold while the unreadable-data page shows
- **Raised by:** PM — 2026-10-30
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. The rule wants scoping to the normal mode.
- **Where it shows:** `docs/fdr.md:L326-L327`. On unreadable data an address for a project or task that does not exist answers the one page, under R-25 (`tests/integration/test_start.py`, `test_an_unreadable_start_serves_one_page_and_announces_once`, the unknown address among those it asks).
- **If a document has to be written:** none — `fdr.md` itself, by `product-fdr`.
- **Answer:**

**How it closes.** `product-fdr` folds it on its next run like any other item.
