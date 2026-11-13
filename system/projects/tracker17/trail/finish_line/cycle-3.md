# Finish line open issues — tracker17

> Companion to `finish_line.md`. The CPO declared the finish line non-interactively; this file holds what it
> could not settle from the inputs (the settled PRD and the project card).
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**,
> then re-run `project-finish-line`. It folds your answers into the finish line and drops the resolved items.
> When nothing is left open, `project-finish-line` **deletes this file**: no file = the finish line is declared.
>
> **Commit before re-running.** The run that finishes clean removes this file, and git refuses to
> remove a file carrying uncommitted edits — so an uncommitted answer stops that run before it can
> commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CPO folds them in, it first copies this file
> whole to `trail/finish_line/` — so what you decided, and why, stays readable and citable for good.

> **No producing run wrote this file.** A `companion-self-answer` run opened it on 2026-11-13, in the
> Principal PM's seat, while answering `products/tracker17/docs/fdr_open_issues.md` § 2.1, to carry
> item § 2.1 below. `project-finish-line` has no record of writing it. It exists because that item's
> rationale found the finish line quoting `products/tracker17/docs/PRD.md` § Assumptions in words
> PRD version 8 removed, and named the correction as the CPO's without sending it anywhere. The
> finish line has no other companion, so without this file the correction reaches no seat. The answer
> run found the same removed wording in a second place, the third bar, and this item carries both.

---

## 1. Open issues — questions about the terminus with no answer yet

None.

## 2. Choices to confirm — the CPO drafted a best-effort answer; confirm or override

### 2.1 The finish line quotes PRD § Assumptions in words the PRD no longer holds, in two places
- **Drafted into the finish line:** nothing. The run that raised this item writes no finish line. What
  it hands the CPO to write:
  1. **§ What this finish line does not require.** Drop the quotes "stays that way until the owner
     decides to publish it" and "until then the owner is the only reader", and drop "Publishing is the
     owner's later decision", which is no longer true. In their place, say that PRD § Assumptions now
     reads "tracker17 is public": it ships as an example in kensaiapp's public release. Done still does
     not require publishing or a trial by an outside reader, because the owner's answer is "by myself"
     (`system/projects/tracker17/trail/finish_line/cycle-1.md` § 1.1), and because "Until there are
     outside readers, the owner's own reading and setup stand in for theirs" (PRD § Assumptions).
  2. **Bar 3, Simple to read.** The sentence "The owner also runs this bar alone, on their own machine,
     because the PRD makes them the only reader until they publish (`products/tracker17/docs/PRD.md`
     § Assumptions)" rests on the removed wording. Rest "alone" on the owner's "by myself" and on the
     PRD sentence quoted in point 1. The bar itself does not change.
- **Rationale:** PRD version 8 replaced the not-public assumption with "**tracker17 is public.** It
  ships as an example in kensaiapp's public release". Its own note says the old line "read 'not public
  yet', which stopped being true with the first release". On 2026-11-13, a search of
  `products/tracker17/docs/PRD.md` for "stays that way until" and "only reader" found 0 lines. Both of
  the finish line's citations now point at a section that says the opposite of what they quote. A fact
  that is now false is the strongest reason to reopen a document. Neither change moves the terminus or
  any of the three bars. Each conclusion still stands, on a ground the PRD still states. FDR OOS-1
  traces to § What this finish line does not require, and stays true either way.
- **If overridden:** the finish line keeps citing PRD words that are not in the PRD, so a reader who
  follows either citation finds that tracker17 is public. OOS-1 in `products/tracker17/docs/fdr.md`
  keeps tracing to a section whose stated reason is false, though its conclusion holds.
- **Confirm or override:** confirm, with two additions. Make both corrections as drafted. (a) The
  owner's "by myself" is the ground that carries "alone" in bar 3 and the exclusion of outside
  readers. The PRD's "Until there are outside readers, the owner's own reading and setup stand in for
  theirs" only supports it, because that sentence is bounded in time: once an outside reader arrives,
  the PRD itself says the bars "would need revisiting", and that is a PRD revision, not something that
  reopens this finish line. (b) Keep the heading "What this finish line does not require" word for
  word, because `products/tracker17/docs/fdr.md` OOS-1 and OOS-2 cite it by that name. Done does not
  depend on tracker17 being public. It already is. The reasoning is in
  `system/projects/tracker17/trail/finish_line/self_answer-2.md`.
