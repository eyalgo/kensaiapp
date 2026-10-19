# Change Text — Moving a task along its allowed status moves

**Date:** 2026-10-19
**Category:** feature
**Behaviour:** changing

---

## Text

Two variable parts recur below. **{title}** is the task's title as the saved data holds it when the
page is built, written whole and exactly as typed, inside the straight single quotes the string
already carries. **{status}** is one of the four status words, `todo`, `in-progress`, `done` or
`cancelled`, written exactly as defined, lowercase and hyphenated. Each block below says which status
it takes.

### The move buttons, on a row of a project's task list and in the status area on a task's page

**A task in `todo`: the visible label of its one button**

> in-progress

When the person sees it: they are reading a task in `todo`, and this is the one move they can press.

**A task in `in-progress`: the visible label of the first button**

> done

When the person sees it: they are reading a task in `in-progress`, and pressing this finishes it.

**A task in `in-progress`: the visible label of the second button, after `done`**

> todo

When the person sees it: they are reading a task in `in-progress`, and pressing this puts it back.

**A task in `done` or `cancelled`**

No button and no string. On a row the moves cell is left empty. On the task's page the status area
shows its heading and the status word only.

**Every move button: its accessible name**

> Move '{title}' to {status}

{status} is the button's own visible label: `in-progress`, `done` or `todo`. So the `done` button of
`Set up CI` is named "Move 'Set up CI' to done". When the person hears it: a screen reader names the
task and the move together, so the same label on several rows can be told apart.

### The moves column of a project's task list

**The column heading, last, after Due date**

> Moves

When the person sees it: they are reading the task list, and this column holds each task's moves.

### The status area on a task's page

**The area's heading, on every task's page**

> Status

When the person sees it: they are reading one task, and this area says where it stands and what it
can move to.

**The task's status, in its own element, under the heading**

> {status}

{status} is the task's saved status, any of the four words, written alone. When the person sees it:
it tells them the task's status in words. A task in `done` or `cancelled` shows this and no button.

### The line after a move

**A move was saved, on the row it was pressed on or in the task page's status area**

> You moved '{title}' to {status}.

{status} is the status the task moved to, as the page's address carries it. When the person sees it:
they pressed a move, it was saved, and the task's status beside this line is the new one. A reload
shows the same line again.

### The reason when a move is refused

One string per status the task has in the saved data when the move is refused. The same four strings
answer a move the workflow doesn't allow and a move that names something other than a status, or
nothing. The string for the task's saved status is the one shown.

**The task's saved status is `todo`**

> The status of '{title}' is todo, which doesn't allow the move you pressed. The moves shown are the ones you can press.

When the person sees it: the move they pressed wasn't made, and the page shows the task's saved
status, `todo`, with the move they can press.

**The task's saved status is `in-progress`**

> The status of '{title}' is in-progress, which doesn't allow the move you pressed. The moves shown are the ones you can press.

When the person sees it: the move they pressed wasn't made, and the page shows the task's saved
status, `in-progress`, with the moves they can press.

**The task's saved status is `done`**

> The status of '{title}' is done, which doesn't allow the move you pressed. A task in done can't be moved.

When the person sees it: the move they pressed wasn't made, and the page shows the task as `done`,
with nothing left to press.

**The task's saved status is `cancelled`**

> The status of '{title}' is cancelled, which doesn't allow the move you pressed. A task in cancelled can't be moved.

When the person sees it: the move they pressed wasn't made, and the page shows the task as
`cancelled`, with nothing left to press.

### The message when a move fails

**On the page, on the row it was pressed on or in the task page's status area**

> The tracker couldn't move '{title}' to {status}, and nothing was changed. Try again.

{status} is the status the move named, as the page's address carries it. When the person sees it:
they pressed a move, it wasn't saved, and the task still has the status and moves shown beside this
line, so the same move is there to press again.

**In the terminal the tracker was started from, the line before the underlying error text**

> The tracker couldn't move '{title}' to {status}, and nothing was changed.

{status} is the status the move submission named, written as the submission gave it. When the person
sees it: a developer reading the terminal learns which task and which move failed. The underlying
error text follows on its own line, as it already does for every other action, and is not this
change's words.

---

## Wording decisions

- **The standard is CONTENT.md alone.** The instance has no writing bar yet: its own doctrine is not
  declared, so the shared core governs, and core carries a template for a bar but no bar. Every string
  here was written to CONTENT.md and checked against it.
- **The column heading is "Moves".** DESIGN.md lists the columns as "title, status, priority,
  assignee, labels, due date and moves", and the terminology fixes "move" for this concept. It is in
  sentence case with no end punctuation, like the six headings before it.
- **The status area gets the heading "Status".** The design names the area as a place for words but
  gives no heading. The task page's other areas each open with a one-word heading, "Labels" and
  "Comments". Without one, the status word would sit alone and nothing on the page would say what
  `done` is. CONTENT.md says state is carried by words, and the UXD calls the area "its status with its
  allowed moves".
- **A `done` or `cancelled` task's moves cell stays empty and doesn't say "none".** The labels and
  due-date cells say "none" when they are empty. CONTENT.md's traceability row for the task page says a
  task in `done` or `cancelled` "shows no move buttons and so no words for them", and the design and its
  row test leave the cell empty.
- **The accessible name and the line after a move are the words CP-298 and CP-305 fix.** They match
  CONTENT.md's own examples, "Move 'Set up CI' to in-progress" and "You moved 'Set up CI' to done.". No
  word was changed.
- **The line after a move adds no consequence clause.** The Completed formula adds one only when the
  visible result differs from what the reader would assume. A task moved to `done` losing its Overdue
  word is what they would assume. The other form, a task that leaves a status-filtered list, can't
  happen yet, because the product has no status filter.
- **The refusal doesn't say the status changed since the page loaded, and offers no reload.** The
  request rules out handling for an out-of-date page, and the spec leaves both out. The tracker also
  can't establish that the page was out of date: it knows only the saved status and the move that was
  sent, and a hand-built submission gets the same refusal. The smaller true thing is the saved status,
  which the landing page shows beside the reason.
- **The refusal names no target status.** The address that answers a refusal carries the task and the
  refusal's code, not the status the move named. For a move that names something other than a status,
  there is no status to name.
- **One set of refusal strings answers both refusal codes.** The design allows the same words for both
  (its D-6), and the spec answers a move naming something other than a status the way it answers a
  move the workflow refuses (CP-309). The strings are true of both, because no status allows a move to
  something that isn't a status.
- **The refusal is four whole strings, one per saved status, not one string with a status in it.** The
  second sentence differs: a task in `todo` or `in-progress` has moves to press, and a task in `done` or
  `cancelled` has none. Writing them whole leaves no sentence for the page to assemble.
- **"The moves shown are the ones you can press", not "the ones its status allows".** The page holds
  back the move to `cancelled` in this change, so the moves shown aren't every move the status allows.
  The sentence follows the label refusal's form, "The labels shown are the ones the task carries.", and
  says what the page shows.
- **The refusal gives no imperative such as "Press one of the moves shown".** The tracker doesn't know
  the reader wants a different move. In the stale case, the task already has the status they pressed.
  An instruction to press something would be the advice-closing guide that § Voice rejects.
- **The page failure leaves out "What you typed is still in the form".** The Failure formula includes
  that sentence only where it is true, and a move button has no field to type in.
- **The terminal line has one form only.** The task is read before the move is tried, and a task that
  isn't found gets the not-found page, so the title is always known. The label and comment lines need a
  second form without a title, and this line doesn't. The status is written as the submission named it,
  because choosing a second form for a value that isn't a status would make the page part check the
  value, and the design keeps that check out of the page part.

---

## Findings for the Content Manager

- "The status of '{title}' is done, which doesn't allow the move you pressed. A task in done can't be
  moved." — The refusal formula has two sentences, a reason and then one action where one exists. Its
  only rule for a refusal with no action covers the case where the state the reader wanted already
  holds, and then the second sentence says what the page shows. It doesn't say what the second sentence
  is when no action exists because the task's status is final, and the wanted state may not hold. —
  Meanwhile the second sentence states the fact that leaves no action, in the form of the
  Needs confirming example "A cancelled task can't be moved again.", without "again".
- "The status of '{title}' is todo, which doesn't allow the move you pressed." and the first sentence
  of the three refusals like it — The standard's only example of a move refusal, "The status of 'Set up CI' has changed since this
  page loaded. Reload the page to see it.", says the page is out of date. When it refuses a move, the
  tracker knows only the saved status and the move that was sent, so it can't establish that the page
  was out of date. No rule says how to word a move refusal when the tracker can't establish why the
  status shown differed from the status saved. This change didn't need that example, because the
  request leaves out the out-of-date wording, but the later change that adds it will meet the same gap.
  — Meanwhile the strings name the saved status, which the tracker does establish.
