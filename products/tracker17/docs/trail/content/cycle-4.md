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
> pages against the settled verbal language. It exists because `CONTENT.md` was settled and had no
> companion, so without one a disagreement would reach no seat that can settle it. Its item 3.1 is
> answered and folded (`docs/trail/content/cycle-3.md`).

---

## 1. Open issues

None.

## 2. Choices to confirm

### 2.1 RN-16 says tracker17 has no code yet, and the product now has pages with strings in them
> Raised by a `companion-self-answer` run on 2026-10-07, not written by a `product-content` run. The run was answering this file and read `CONTENT.md` whole to do it. No item asked about this. It found that Review Note RN-16 states a fact the repository no longer holds. The run left `CONTENT.md` unchanged and raised the change here. Its reasoning is in `docs/trail/content/self_answer-3.md` § Raised on this document.
- **Written into CONTENT.md:** RN-16 (`CONTENT.md:493`): "tracker17 has no strings of its own, because it has no code yet. The nearest evidence is its predecessor's command-line wording."
- **Grounds:** `web/pages.py` is committed and writes strings a reader sees, for instance "A project needs a name. Type one." (`web/pages.py:63`). So the product has strings of its own, and the nearest evidence is no longer the predecessor's wording. The product's own strings are what show that a rule can be applied to a real string. A cold reader of RN-16 is told no such corpus exists. The proposed change: RN-16 states that the product now has strings, in `web/pages.py`, written after the rules, and drops "because it has no code yet". It does not say whether those strings meet the rules, which a Content Editor run on a change that publishes text, or an audit, finds out. Line 434 and RN-15 (line 491) say "no corpus" as the reason a call was made at the time. They record history and stand.
- **What moves if you override:** nothing in any rule. RN-16 would keep telling a reader there is no corpus while one exists, and its evidence paragraph would keep pointing at the predecessor.
- **Confirm or override:** confirm, with one addition. The proposed RN-16 names the product's strings by where they are, and not only `web/pages.py`. Three files hold delivered strings: `web/pages.py` (the pages), `web/routes.py` (the terminal line printed when an action fails, line 210) and `main.py` (the terminal's ready line and its failed-start line, lines 41 and 50). All were committed on 2026-10-07, after `CONTENT.md` was settled on 2026-10-06. RN-16 says this is the state at the time of the revision, and that RN-2 and RN-15 give "no corpus" as the reason a call was made then. It still doesn't say whether the strings meet the rules. Reasoning in `docs/trail/content/self_answer-4.md`.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

None.
