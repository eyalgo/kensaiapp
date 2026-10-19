# CONTENT open issues — tracker17

> Companion to `CONTENT.md`. The Content Manager authored the verbal language non-interactively;
> this file holds the calls it made and wants your sign-off on — each with the reason behind it,
> and what moves underneath it if you override — plus the few things it genuinely could not
> settle.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**,
> then re-run `product-content`. It folds your answers into `CONTENT.md` and drops the resolved
> items. When nothing is left open, `product-content` **deletes this file**: no file = the verbal
> language is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git refuses
> to remove a file with uncommitted edits in it — so an uncommitted answer stops that run before
> it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the Content Manager folds them in, it first copies
> this file whole to `docs/trail/content/` — so what you decided, and why, stays readable and
> citable for good.

> **No `product-content` run wrote this file.** The PM opened it on 2026-10-07, reading the product's
> pages against the settled verbal language, with the one item in § 3. It exists because `CONTENT.md`
> is settled and had no companion, so without one the disagreement would reach no seat that can settle it.

---

## 1. Open issues

None.

## 2. Choices to confirm

### 2.1 RN-16 says tracker17 has no code yet, and the product now has pages with strings in them
> Raised by a `companion-self-answer` run on 2026-10-07, not written by a `product-content` run. The run was answering this file and read `CONTENT.md` whole to do it. No item asked about this. It found that Review Note RN-16 states a fact the repository no longer holds. The run left `CONTENT.md` unchanged and raised the change here. Its reasoning is in `docs/trail/content/self_answer-3.md` § Raised on this document.
- **Written into CONTENT.md:** RN-16 (`CONTENT.md:493`): "tracker17 has no strings of its own, because it has no code yet. The nearest evidence is its predecessor's command-line wording."
- **Grounds:** `web/pages.py` is committed and writes strings a reader sees, for instance "A project needs a name. Type one." (`web/pages.py:63`). So the product has strings of its own, and the nearest evidence is no longer the predecessor's wording. The product's own strings are what show that a rule can be applied to a real string. A cold reader of RN-16 is told no such corpus exists. The proposed change: RN-16 states that the product now has strings, in `web/pages.py`, written after the rules, and drops "because it has no code yet". It does not say whether those strings meet the rules, which a Content Editor run on a change that publishes text, or an audit, finds out. Line 434 and RN-15 (line 491) say "no corpus" as the reason a call was made at the time. They record history and stand.
- **What moves if you override:** nothing in any rule. RN-16 would keep telling a reader there is no corpus while one exists, and its evidence paragraph would keep pointing at the predecessor.
- **Confirm or override:** <confirm, or `override: <what instead>`>

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 Terminology says `tracker17` appears only in page titles, and the design puts the product name in the header
- **Raised by:** PM — 2026-10-07
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_first-project`
- **What it blocks:** every page header holds wording one settled standard forbids. `web/pages.py:52` sets `tracker17` in the header (`<span class="product-name">`), as `DESIGN.md:350` ("The product name sits on the left") and `DESIGN.md:427` ask, while `CONTENT.md:144`, Terminology row "The running product", says "`tracker17` appears only in page titles".
- **Where it shows:** `CONTENT.md` § Terminology, the row "The running product". Proposed: the row also names the header, where the design places the product name. If the header should not carry it, the change is the design's, and this item routes to `DESIGN.md`'s companion instead.
- **If a document has to be written:** none.
- **Answer:** Overridden in wording, with the outcome the item proposes: the header may carry `tracker17`. In `CONTENT.md` § Terminology, row "The running product", the note "`tracker17` appears only in page titles." is replaced by "`tracker17` is the product's name, written as § Grammar and mechanics (Case) sets it. For itself, in a sentence, the tracker says "the tracker"." The row names no place, because where the name sits on a page is the design's (`DESIGN.md:350`, `DESIGN.md:427`), and the title pattern is already stated in § Accessibility of text. `DESIGN.md` and `web/pages.py:52` stay as they are, and nothing is raised on `DESIGN.md`'s companion. Reasoning: `products/tracker17/docs/trail/content/self_answer-3.md`.
