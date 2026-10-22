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
>
> **§ 3 comes from outside this run.** The verbal language is read by everyone who writes a string,
> and a seat downstream can find a pattern it has no rule for. It is recorded there, answered here,
> and folded by the same run.

> **Round 13 folded.** The earlier § 2.1 (RN-26 and the refusal reached without a press) is in
> `CONTENT.md` version 14, with RN-27's citation corrected. The earlier § 3.1 was answered "carried
> upstream", which settles nothing in this document, so it is re-raised below as § 3.1. The answered
> file is `docs/trail/content/cycle-13.md`.

---

## 1. Open issues

None.

## 2. Choices to confirm

None.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 What the page a refused out-of-date move lands on says when it is opened again with no press
- **Raised by:** PM — 2026-10-21 (the residue of the earlier § 3.2, re-raised by the Content Manager, and again after the cycle 13 answer)
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_status-moves`
- **What it blocks:** nothing is blocked. `CONTENT.md` keeps its current wording and examples until the CDO answers.
- **Where it shows:** the page a refused out-of-date press lands on carries the refusal in its address, so a reload, Back or a bookmark shows "The status of '…' has changed to {status}. …" again. The tracker sees an address and can't establish a change. One string serves both the first landing and a later visit, so any wording true on a later visit drops UX-F4's confirmed "says the task's status has changed". `CONTENT.md` § Error and RN-26 now state this: the formula for a refusal reached without a press names a move only where the address carries one, and the overtaken-move clause governs this page's line until the question below is answered. The examples for the overtaken-move form (RN-27) carry "has changed to" and move again if the answer drops it.
- **If a document has to be written:** `UXD.md`, by the CDO (`product-uxd`), carried on `docs/UXD_open_issues.md` item 2.1, which holds the lean "state the task's status and what it allows, and claim no change" and whose confirm-or-override slot is the one to answer. `CONTENT.md` follows the answer (RN-26, RN-27). The SDD `status-moves` unit and its tests repeat the current wording, and a change that publishes text rewrites `_CHANGED` and `_OVERTAKEN_LINES`.
- **Answer:** The page says what the tracker established and claims no change: it states the task's current status and what that status allows, so it is true on the first landing and on every later visit. "The status of 'Set up CI' is todo. A task in todo can be moved to in-progress or cancelled." and "The status of 'Set up CI' is done. A task in done can't be moved." This is the CDO's answer on `docs/UXD_open_issues.md` item 2.1 (confirmed, option (a)), and `CONTENT.md` follows it. The fold changes five places: the overtaken-move clause in § Error, its two examples, the banned-words row in § Voice that offers "has changed to {status}" as the safe form, the rationale line that says the same, and RN-26 and RN-27. RN-26 drops "until it is answered" and RN-27 drops the caveat that its examples move again. The refusal formula's "names the move the address asks for, where the address carries one" stays. The product's wording (`_CHANGED` and `_OVERTAKEN_LINES`) and its tests are a finding for a change that publishes text, not an edit here. Reasoning in `docs/trail/content/self_answer-14.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
