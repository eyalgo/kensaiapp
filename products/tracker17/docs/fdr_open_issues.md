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

### 2.1 The FDR has not read the upstream documents as they now stand, and SRS FR-41 has no rule here

> **No producing run wrote this item.** A `companion-self-answer` run raised it on 2026-10-30, after
> reading the FDR whole against its inputs to answer § 3. What prompted it is the FDR's own *Inputs
> read* line, which names versions the inputs have since moved past. § 2's "None." above predates
> this item.

- **Drafted into the FDR:** nothing yet. The lean is one fold of four changes: a new rule, R-121, that the README, which a reader arrives at first, opens by naming both purposes, the worked example and kensaiapp's own testing ground, and of the earlier versions names only tracker16-X, tracing to SRS § 3.1 FR-41; the Description names the second purpose; RN-11 gains drop-lines for SDD § 4 RT-11 and § 9 TO-8 and TO-9, and its line on SDD § Open Questions names the question that section now holds; and the *Inputs read* line reads PRD version 7, SRS version 6 and SDD version 17.
- **Rationale:** something upstream moved and this document has not seen it. `fdr.md:6` reads PRD version 5, SRS version 5 and SDD version 7, and their headers now read 7, 6 and 17. SRS FR-41 (`SRS.md:98-104`) and AC-21 are the behaviour PRD § Purpose asks for, "A reader learns both purposes from the first thing they read about tracker17", and no rule here states them, while `fdr.md:25` says only "It exists as a worked example". `fdr.md:572` names the Open Question on Chromium and `autofocus`; `SDD.md:3112` now holds one on assistive technology. No answer so far carried any of this, and a fold changes the FDR only where an answer or an upstream change traces to it, so raising it here is what puts it in front of that run.
- **If overridden:** FR-41 stays with no FDR rule, so the Product Owner and QA read no behavioural line for it, and the *Inputs read* line keeps naming versions older than the ones the rules were checked against. No other rule moves.
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

## 3. Raised from downstream — an item raised against the FDR after it settled

### 3.1 R-20's "the tracker's next save replaces it" does not hold while the unreadable-data page shows
- **Raised by:** PM — 2026-10-30
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. The rule locks a behaviour one startup mode does not have.
- **Where it shows:** `docs/fdr.md:L98-L100`. A tracker showing the unreadable-data page has no save, so an outside change is not replaced; it stays unread until the next start (`web/routes.py`, `UnreadableSite`, which holds no reader or saver). "Read once, at start" holds in both modes.
- **If a document has to be written:** none — `fdr.md` itself, by `product-fdr`.
- **Answer:** Correct R-20 to read: "The saved data is read once, at start. A change made to the saved data from outside the tracker while it runs is not shown. While the tracker serves its saved data, its next save replaces that change. While the saved data is unreadable it makes no save (R-27), so the change stays, and the next start reads it." Its trace adds SDD § 4 SD-4. OOS-16 and R-27 stand as written. Reasoning: `products/tracker17/docs/trail/fdr/self_answer-3.md`.

### 3.2 R-105's not-found page does not hold while the unreadable-data page shows
- **Raised by:** PM — 2026-10-30
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. The rule wants scoping to the normal mode.
- **Where it shows:** `docs/fdr.md:L326-L327`. On unreadable data an address for a project or task that does not exist answers the one page, under R-25 (`tests/integration/test_start.py`, `test_an_unreadable_start_serves_one_page_and_announces_once`, the unknown address among those it asks).
- **If a document has to be written:** none — `fdr.md` itself, by `product-fdr`.
- **Answer:** Correct R-105 to read: "While the tracker serves its saved data, an address for a project or task that does not exist shows a not-found page. While the saved data is unreadable, that address shows R-25's page, as every address does. Which of the two the tracker serves is fixed at start." Its trace stays SDD § 4 EX-13, which already says this, and RN-11's line naming EX-13 stands. The rule states no status code. Reasoning: `products/tracker17/docs/trail/fdr/self_answer-3.md`.

**How it closes.** `product-fdr` folds it on its next run like any other item.
