# Agari open issues — tracker17

> Companion to `agari.md`. The CPO declared the Agari non-interactively; this file holds what it
> could not settle from the inputs (the settled PRD and the project card).
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**,
> then re-run `project-agari`. It folds your answers into the Agari and drops the resolved items.
> When nothing is left open, `project-agari` **deletes this file**: no file = the Agari is declared.
>
> **Commit before re-running.** The run that finishes clean removes this file, and git refuses to
> remove a file carrying uncommitted edits — so an uncommitted answer stops that run before it can
> commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CPO folds them in, it first copies this file
> whole to `trail/agari/` — so what you decided, and why, stays readable and citable for good.

---

## 1. Open issues — questions about the terminus with no answer yet

None. Your round-0 answer, "I can use it locally easily by myself", is folded into `agari.md` and kept
at `system/projects/tracker17/trail/agari/cycle-1.md` § 1.1.

## 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override

### 2.1 Done also needs the Simple to read bar, not only your own use of the tracker
- **Drafted into the Agari:** tracker17 is done when all three bars in `products/tracker17/docs/PRD.md`
  § Success Metrics pass: **Works**, **Simple to set up** and **Simple to read**. The third bar is the
  cold read of the code, plus tracing one feature from the product definition to its code and tests.
- **Rationale:** Your answer speaks of using the tracker locally and easily, by yourself. **Works**
  and **Simple to set up** check exactly that. **Simple to read** checks something else: the reader
  the product exists for (`products/tracker17/docs/PRD.md` § Purpose, "a person who wants to see how
  kensaiapp builds apps has one simple product to read end to end"). The PRD says all three bars are
  "checked before the product is called done" (§ Success Metrics), so the draft follows it. You did
  not write that sentence yourself, though. The three bars were confirmed by a `companion-self-answer`
  run (`products/tracker17/docs/trail/prd/cycle-2.md` § 2.4, reasoning in
  `products/tracker17/docs/trail/prd/self_answer-1.md`). The read-and-trace part was added the same
  way (`products/tracker17/docs/trail/prd/cycle-4.md` § 2.1). Whether "done" stretches past your own
  answer is your call, so it waits here.
- **If overridden:** the Agari drops condition 3 and is reached on **Works** and **Simple to set up**
  alone. The PRD would then disagree with the Agari, because § Success Metrics still says all three
  bars are checked before done. That sentence would need a `product-prd` revision to match.
- **Confirm or override:** confirm, with one addition. Keep all three bars, condition 3 included. The
  read bar does not reach past your own answer. In the project-setup interview you said there is "no
  SIMPLE example of a kensaiapp product" and that a reader will "Look at the code"
  (`products/tracker17/docs/trail/prd/cycle-1.md` § 1.3 and § 1.4). You also run the read bar yourself,
  on your own machine, because the PRD makes you the only reader until you publish (§ Assumptions). So it
  fits "by myself". The addition: the Agari should give that as the reason for condition 3, citing
  those two answers. It should not describe the bar as one only a self-answer run put there. The trace
  half did come from self-answer runs, but it is in the settled PRD. Dropping it would be a `product-prd`
  change, not an Agari change. Reasoning in `system/projects/tracker17/trail/agari/self_answer-1.md`.
