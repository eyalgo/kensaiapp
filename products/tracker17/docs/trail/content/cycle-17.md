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

> **No producing run wrote this file.** It was opened on 2026-10-30 by the PM, to carry § 3.1.
> `product-content` has no record of writing it.

---

## 1. Open issues

None.

## 2. Choices to confirm

None.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 Terminology has no term for a tracker ended by a kill it can't handle
- **Raised by:** PM — 2026-10-30
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. The published string stands with a word no rule approves or rejects.
- **Where it shows:** `README.md:L79` says "A tracker that was killed doesn't prevent the next start." `CONTENT.md` § Terminology names "the running product" and nothing for how one ended, and `grep -n -i kill docs/CONTENT.md` prints nothing. The word comes from SRS AC-16, "a tracker was killed".
- **If a document has to be written:** none — `CONTENT.md` itself, by `product-content`.
- **Answer:** Answered: add one row to § Terminology and no other rule. Concept: a tracker the reader ended by force rather than with Ctrl-C. Term: "killed". Rejected: "killed process" and "process", which name a mechanism as "server" does in the row for the running product; and "stopped", which is the setup instructions' word for Ctrl-C, so using it for both would hide the end the sentence is about. Notes: only the setup instructions say it, as the reader's own condition ("A tracker that was killed…"). No string the tracker prints says how an earlier tracker ended, because it can't establish that. The row claims nothing about what the tracker could finish before it ended. A crash and a power cut get no term until a string names one. Reasoning: `docs/trail/content/self_answer-18.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
