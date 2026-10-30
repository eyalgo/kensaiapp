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

> **No producing run wrote this file.** It was opened on 2026-10-30 by the PM, to carry § 3.
> `product-content` has no record of writing it.

---

## 1. Open issues

None.

## 2. Choices to confirm

None.

## 3. Raised from downstream — an item from a seat that did not write the verbal language

### 3.1 "Stopped" is recorded as the word for Ctrl-C, and the setup instructions also use it for a refused start
- **Raised by:** PM — 2026-10-30
- **Tracked by:** `tracker17 · nemawashi · 2026-10-11_protect-saved-data`
- **What it blocks:** nothing is blocked. The published sentence stands; the row that governs its word no longer describes what the setup instructions say.
- **Where it shows:** `docs/CONTENT.md:L178`, the "killed" row, rejects "Stopped" as "the setup instructions' word for Ctrl-C, so using it for both would hide the end the sentence is about". `README.md:L56` reads "A line that starts with `The tracker didn't start` means this start has stopped.", a start that ended by itself after a refusal. § Terminology has no term for that end. The PM's lean: approve "stopped" for it, with "this start" as what keeps it apart from a tracker the reader stopped with Ctrl-C, and correct the row to say so. Otherwise name the term to use, and the README sentence changes with it.
- **If a document has to be written:** none — `CONTENT.md` itself, by `product-content`.
- **Answer:** Confirmed with addition. Approve "stopped" for a start that ended by itself after its refusal, written "this start has stopped", and leave the sentence in the setup instructions' "What the start prints" as it is. § Terminology gains a row for that end. The term is "this start has stopped", and the subject "this start" is part of the term. Rejected: "the tracker isn't running", which is false after the line "The tracker didn't start, because another tracker is already running on the same saved data", because a tracker is running then. Rejected: "exits", the setup instructions' word in "Starting the tracker again" for the same end, because it names a mechanism as "process" does. That sentence is then a finding for a change that publishes text, and the fold edits nothing there. Rejected: "failed", which the banned words bar, and "crashed", which names a cause the tracker did not establish. The row's note says only the setup instructions use the term, to explain the line that begins "The tracker didn't start". The "killed" row is corrected and its term stays. Its claim that "Stopped" is the setup instructions' word for Ctrl-C is replaced by the true reason: the setup instructions use "stop" for any end of a tracker that is not the forced one, which covers the reader's Ctrl-C, a refused start and a tracker's end in general, so the word names no one end and cannot stand for the forced end. Reasoning in `products/tracker17/docs/trail/content/self_answer-20.md`.

**How it closes.** `product-content` folds it on its next run exactly as it folds §§ 1–2.
