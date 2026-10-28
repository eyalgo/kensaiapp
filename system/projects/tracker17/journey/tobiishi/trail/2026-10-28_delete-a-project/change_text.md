# Change Text — Delete a project with its tasks, and finish the slice's deletion contract

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing

---

## Text

A part in braces is filled in when the page or line is built, and the line under each string says
what fills it. Every quote mark in a string is a straight single quote and belongs to the string, not
to the value. A typed value is written whole and exactly as typed, whatever characters it holds.

### Delete project on a project's Tasks view

**A project's Tasks view in every state, before Delete project is pressed: with tasks, with no tasks yet, under a filter that matches nothing, and under a filter or sort the page refused — the control's label**

> Delete project

When the person sees it: they are reading one project's tasks and can press this to start deleting
the project. Pressing it deletes nothing. The control's accessible name is its label alone, because no
other control on the Tasks view carries this label while the control shows.

**After Back out is pressed**

No string. Delete project is back in its place with focus on it, and no line is shown.

### Its confirmation and failure line

**After Delete project is pressed, when the project holds 2 or more tasks — the confirmation sentence, in the control's place, with focus on it**

> Delete '{name}' and its {count} tasks? You can't undo this.

**After Delete project is pressed, when the project holds 1 task — the confirmation sentence**

> Delete '{name}' and its 1 task? You can't undo this.

**After Delete project is pressed, when the project holds no tasks — the confirmation sentence**

> Delete '{name}', which has no tasks? You can't undo this.

`{name}` is the project's name as saved when this page is built. `{count}` is the number of tasks the
project holds when this page is built, every task in every status, whether or not the list's filter
shows it. Comments are never counted. The form is chosen by that number: 2 or more, exactly 1, or 0.
When the person sees it: they pressed Delete project, nothing is deleted yet, and they choose between
the two controls that follow.

**After Delete project is pressed — the confirming control's label, after the sentence**

> Delete project

When the person sees it: pressing it deletes the project, its tasks and their comments, and it can't
be undone. The trigger with the same label is gone from the page while this control shows, so its
accessible name is its label alone.

**After Delete project is pressed — the back-out control's label, after the confirming control**

> Back out

When the person sees it: pressing it leaves the project as it is. This is the string the move to
`cancelled` and Delete task confirmations already show, one string for one concept.

**After a confirmed deletion whose save did not complete — the line beside Delete project, which has focus**

> The tracker couldn't delete the project '{name}', and nothing was changed. Try again.

`{name}` is the project's name as the tracker holds it when this page is built.
When the person sees it: they confirmed the deletion and it did not happen. The project, its tasks
and their comments are all still here, and pressing Delete project again opens the confirmation.

### The completion line on Projects

**After a confirmed deletion that removed 2 or more tasks — the line, with focus on the page's heading**

> You deleted '{name}' and its {count} tasks.

**After a confirmed deletion that removed 1 task — the line**

> You deleted '{name}' and its 1 task.

**After a confirmed deletion of a project that held no tasks — the line**

> You deleted '{name}', which had no tasks.

`{name}` is the project's name as it was when the deletion ran. `{count}` is the number of tasks the
deletion removed, read when it ran, which may differ from the count the confirmation showed. The form
is chosen by that number: 2 or more, exactly 1, or 0.
When the person sees it: the project, its tasks and their comments are gone, and the project is not
in the list. The line stays the same on a reload and on Back or Forward. When the deleted project was
the only one, the line sits with the existing no-projects state, which keeps its own words.

### The console message for a failed project deletion

The design and the spec call this window the console. The product's standard calls it the terminal,
the window the tracker was started from, and this file uses that word from here on.

**A confirmed deletion whose save did not complete — the first line the terminal prints**

> The tracker couldn't delete the project '{name}', and nothing was changed.

`{name}` is the project's name as the tracker holds it when the deletion is tried.
When the person sees it: they are a developer reading the terminal. The next line, which the tracker
already prints for every failed action, carries the underlying error text exactly as reported. This
change writes no words for that line.

---

## Wording decisions

- The three confirmation sentences, both control labels and the 2-or-more and 1-task completion lines
  are taken exactly as `change_spec.md` § Rules CP-570 and CP-576 state them. Those rules fix them, and
  `products/tracker17/docs/CONTENT.md` § Needs confirming ("Delete 'Alpha' and its 12 tasks? You can't
  undo this." and "Delete 'Alpha', which has no tasks? You can't undo this.") and § Completed ("You
  deleted 'Alpha' and its 12 tasks.") give the same words.
- The zero-task completion line is "You deleted '{name}', which had no tasks." `change_spec.md` § Rules
  CP-576 leaves its words to the standard and this stage, and offers this sentence as its example.
  It follows `CONTENT.md` § Grammar and mechanics *Numbers* ("A count of zero is "no" inside a
  sentence"). It also follows § Completed, where a consequence follows the object "in the same
  sentence after a comma". It mirrors the zero-task confirmation in the past tense, so one shape serves
  both moments.
- The page's failure line names "the project" before the name: "The tracker couldn't delete the
  project '{name}', and nothing was changed. Try again." `change_spec.md` § Rules CP-578 asks for a
  line saying the project could not be deleted and nothing was changed, and leaves the wording to
  `CONTENT.md` § Error, *A failure that is not a refusal*. The task deletion's line reads "The tracker
  couldn't delete '{title}'…". A task and a project may carry the same text, and the tracker prints
  the terminal line with no page around it. Adding "the project" tells the two deletions apart in
  the terminal, and the page line uses the same words so one failure has one sentence. The product's
  rename failure already names its object this way: "The tracker couldn't rename the project to
  '{name}', and nothing was changed."
- The failure line leaves out the formula's sentence about what was typed, because nothing is typed
  for a deletion. It does not mention the project's tasks: "nothing was changed" already covers them,
  and a count there would be a second number beside the confirmation's. It names no cause, because the
  tracker establishes none.
- The terminal message is the page's failure line without "Try again." The task deletion's terminal
  line and the other failed actions use the same shape. A developer reading the terminal is not the
  person who will press again, so the action is left out. `change_spec.md` § Rules CP-578 asks for a
  message "naming the deletion of that project and the error", and the error is the line the tracker
  already prints after it.
- The window is called the terminal, not the console. `CONTENT.md` § Terminology rejects "console" in
  any string and picks "terminal". The word appears in no string here, only in the name of the place,
  which keeps the design's wording so the place can be traced.
- Back out produces no line. `CONTENT.md` § Completed says "backing out, produces none", and
  `change_spec.md` § Rules CP-573 says the same.
- Neither Delete project control carries an added accessible name. `CONTENT.md` § Accessibility of
  text adds the thing acted on only "Where the same visible label appears more than once on a page".
  The trigger and the confirming control share the label, but the confirmation replaces the trigger,
  so the two are never on the page together.
- The no-projects state that shows beside the completion line after the last project is deleted keeps
  its existing words, "There are no projects yet." followed by its invitation. That string is outside
  the places the design's `Publishes text:` line names, and on this reading "yet" means "so far", which
  stays true after a deletion.
- A deleted project's addresses, its tasks' addresses and every submission sent for them get no new
  words. `change_spec.md` § Rules CP-580 and CP-582 reuse the existing not-found pages and say "No
  refusal wording is added", and the design's `Publishes text:` line names neither.
- The banned lexicon in `CONTENT.md` § Terminology and the writing bar were checked against every
  string here, in every inflection, and no string carries a banned word. The product has no
  word-list check of its own to run.

---

## Findings for the Content Manager

None. The standard answered every string.
