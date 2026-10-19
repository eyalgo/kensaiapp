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

> **No `product-content` run wrote this file.** The PM opened it on 2026-10-07, reading the product's start messages against the settled verbal language, with the one item in § 3.

---

## 1. Open issues

None.

## 2. Choices to confirm

None.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 The terminal-message examples name an address the tracker does not use
- **Raised by:** PM — 2026-10-07
- **Tracked by:** `tracker17 · nemawashi · 2026-10-07_first-project`
- **What it blocks:** any string or document written from the examples word for word. `CONTENT.md:250` ("…already using the address 127.0.0.1:8000…") and `CONTENT.md:278` ("Open http://127.0.0.1:8000 in your browser") name port 8000. SDD § 4 RT-5 records the tracker's address as `127.0.0.1:8017` (`SDD.md:286`), and `main.py:20` reads `ADDRESS = ("127.0.0.1", 8017)`. The console says 8017 and the examples say 8000. The setup instructions quote what the start prints and the address to open (UXD UX-S1), so a writer copying the example would send the reader to the wrong address.
- **Where it shows:** `CONTENT.md` § Message patterns, Error, "Terminal messages" (line 250), and the start's ready message example (line 278). Proposed: the examples name `127.0.0.1:8017`, or say the address is a placeholder for the tracker's own. The doubt: they may be meant as illustrations only, and then saying so is the fix.
- **If a document has to be written:** none.
- **Answer:** Confirmed with addition. Both examples name `127.0.0.1:8017`, and neither gets a placeholder note. The terminal strings fill the address from the one the start was given (`main.py:55`, `main.py:61`), and a real start prints `127.0.0.1:8017` (`tests/e2e/test_start_command.py:22`), so the examples show what the reader will see. No other line of `CONTENT.md` names a port. Reasoning in `products/tracker17/docs/trail/content/self_answer-6.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
