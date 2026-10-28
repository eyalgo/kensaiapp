# Change Text — Delete a task from its page

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing

---

## Text

A part in braces is filled in when the page or line is built, and the line under each string says
what fills it. Every quote mark in a string is a straight single quote and belongs to the string, not
to the value.

### The task page's Delete task control, confirmation and failure line

**Any task's page, in every status, before Delete task is pressed — the control's label**

> Delete task

When the person sees it: they are reading one task and can press this to start deleting it. Pressing
it deletes nothing. The control's accessible name is its label alone, because a task's page shows one
task and no other control on it carries this label.

**After Delete task is pressed — the confirmation sentence, in the control's place, with focus on it**

> Delete '{title}'? You can't undo this.

`{title}` is the task's title as saved when this page is built, written whole.
When the person sees it: they pressed Delete task, nothing is deleted yet, and they choose between
the two controls that follow.

**After Delete task is pressed — the confirming control's label, after the sentence**

> Delete task

When the person sees it: pressing it deletes the task and its comments, and it cannot be undone.

**After Delete task is pressed — the back-out control's label, after the confirming control**

> Back out

When the person sees it: pressing it leaves the task as it is. This is the same label the move to
`cancelled` confirmation already shows, one string for one concept.

**After Back out is pressed**

No string. Delete task is back in its place with focus on it, and no line is shown.

**After a confirmed deletion whose save did not complete — the line beside Delete task, which has focus**

> The tracker couldn't delete '{title}', and nothing was changed. Try again.

`{title}` is the task's title as the tracker holds it when this page is built.
When the person sees it: they confirmed the deletion and it did not happen. The task and its comments
are still here, and pressing Delete task again opens the confirmation.

### The project's Tasks view — the line after a deletion

**After a confirmed deletion, on the deleted task's project, with focus at the page's start**

> You deleted '{title}'.

`{title}` is the deleted task's title as it was when the deletion ran, written whole.
When the person sees it: the task and its comments are gone from this project. The line stays the
same on a reload and on Back or Forward. When the deleted task was the project's last, the line sits
above the existing invitation to add a first task, which keeps its own words.

### The terminal's message when a deletion's save does not complete

The design and the spec call this window the console. The product's standard calls it the terminal,
the window the tracker was started from, and this file uses that word from here on.

**A confirmed deletion whose save did not complete — the first line the terminal prints**

> The tracker couldn't delete '{title}', and nothing was changed.

`{title}` is the task's title as the tracker holds it when the deletion is tried.
When the person sees it: they are a developer reading the terminal. The next line, which the tracker
already prints for every failed action, carries the underlying error text exactly as reported. This
change writes no words for that line.

### The timed run's deletion report

These lines follow the deletion's fixture in the order shown, after every line the run printed before
this change. `{task volume}` is the run's task count, the same number every other row in the run
names, 1000 today.

**The fixture line, printed before the three timing rows**

> delete fixture: {task count} tasks, {comments per task} comments each ({comment total} in all); title of {title length} characters, comment of {comment length} characters

`{task count}`, `{comments per task}` and `{comment total}` are read from the fixture as loaded, the
same three numbers every other fixture line states. `{title length}` and `{comment length}` are the
lengths, in characters, of the title of the task the deletion acts on and of that task's first
comment.
When the person sees it: they are a developer checking the fixture the deletion was timed on.

**The confirming submission's row**

> delete a task at {task volume} tasks: {milliseconds} ms

`{milliseconds}` is the submission's time, written with one decimal place, as every row writes it.

**The landing page's row**

> delete landing page at {task volume} tasks: {milliseconds} ms

`{milliseconds}` is the time of the request for the page the deletion lands on.

**The total's row**

> delete total at {task volume} tasks: {milliseconds} ms

`{milliseconds}` is the two times above added together.
When the person sees the three rows: each is under the limit and the deletion counted. Where a row
did not pass, it carries the endings the run already adds to any row, ` — refused or failed` and
` — at or over 1 s`, and this change writes no new ending.

---

## Wording decisions

- The confirmation sentence, the two control labels and the completion line are taken exactly as
  `change_spec.md` § Rules CP-530 and CP-534 state them — those rules fix them as the strings the tests
  read, and `products/tracker17/docs/CONTENT.md` § Needs confirming ("Delete 'Set up CI'? You can't
  undo this.") and § Completed (the verb "deleted") give the same words.
- The failure line is "The tracker couldn't delete '{title}', and nothing was changed. Try again." —
  `change_spec.md` § Rules CP-536 asks for a line "saying the task could not be deleted and nothing was
  changed" and leaves the wording to `CONTENT.md` § Error, *A failure that is not a refusal*. The
  formula's sentence about what was typed is left out because nothing is typed for a deletion, and the
  product's existing line for a pressed move that does not complete, on the task's page, has the same
  shape: "The tracker couldn't move '{title}' to {status}, and nothing was changed. Try again." It names
  no cause, because the tracker establishes none.
- The failure line takes the title the tracker holds when the failure page is built, not the title the
  person saw on the confirmation — `change_design.md` § Sub-job C uses the current task's title for
  confirmation and failure, and the task still exists after a save that did not complete.
- The terminal message is the page's failure line without "Try again." — the product's other failed
  actions print that shape to the terminal, as the move's message does: "The tracker couldn't move
  '{title}' to {status}, and nothing was changed." A developer
  reading the terminal is not the person who will press again, so the action is left out.
- The window is called the terminal, not the console — `CONTENT.md` § Terminology rejects "console" in
  any string and picks "terminal". The word appears in no string here, only in the name of the place.
- Back out produces no line — `CONTENT.md` § Completed: "backing out, produces none", and
  `change_spec.md` § Rules CP-532.
- The Delete task control carries no added accessible name — `CONTENT.md` § Accessibility of text adds
  the thing acted on only where the same visible label appears more than once on a page. The trigger and
  the confirming control share the label "Delete task", but the confirmation replaces the trigger, so the
  two are never on the page together.
- A deleted task's address and every submission sent for it get no new words — `change_spec.md` § Rules
  CP-538 and CP-540 reuse the existing not-found page and refusal, and the design's `Publishes text:`
  line names neither.
- The timed run's lines follow the shape of the run's existing rows: "move a task", "move landing page",
  "move total" and "move fixture", which the run prints today for the status move. `CONTENT.md` § Scope and RN-25 put the timed run's output outside the
  product's standard, so no rule there binds these lines, and the run's house shape is what keeps them
  readable beside the rows already printed.

---

## Findings for the Content Manager

- "Delete '{title}'? You can't undo this." — `CONTENT.md` § Needs confirming's formula asks the
  question "naming the thing and the count of what goes with it", and the same section's task example
  names no count, though a task's comments go with it. The standard does not say whether a task's
  comments count as what goes with it. The string follows the section's own task example and
  `change_spec.md` § Rules CP-530, which fixes it, meanwhile.
