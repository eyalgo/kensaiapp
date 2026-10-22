# Change Text — The `cancelled` button and its in-place confirmation

**Date:** 2026-10-19
**Category:** feature
**Behaviour:** changing

---

## Text

Every string below is written in the exact characters the person reads. `{title}` stands for the
task's title as saved when the page is built, shown whole and exactly as typed. A title holding `<`,
`&`, `"` or `'` shows those characters as typed, once, and never as their escaped form. The straight
single quotes around `{title}` belong to the string, not to the title.

### The `cancelled` button, on a task's row in the project's task list and on the task's page

**Offered, before any press (the task is `todo` or `in-progress`)**

Visible label:

> cancelled

Accessible name:

> Move '{title}' to cancelled

When the person sees it: the task is open and the workflow allows the move. Pressing it opens the
confirmation and saves nothing.

**Back in its spot after Back out**

Visible label:

> cancelled

Accessible name:

> Move '{title}' to cancelled

When the person sees it: they backed out, nothing was saved, and focus is on this button. No line
appears beside it or anywhere else on the page.

### The confirmation, in the place the `cancelled` button stood

**Open, after the first press, and again after a reload while the move is still allowed**

The sentence:

> Move '{title}' to cancelled? A cancelled task can't be moved again.

The confirming control, visible label and accessible name:

> Move to cancelled

The back-out control, visible label and accessible name:

> Back out

When the person sees it: they pressed `cancelled` and nothing is saved yet. Focus is on the
sentence. One Tab reaches Move to cancelled, which saves the move. A second Tab reaches Back out,
which restores the button. Doing nothing leaves the task as it is.

### The line beside the task's status, after the move is saved

**Saved, on the project's page at the task's row and on the task's page at its status**

> You moved '{title}' to cancelled.

When the person sees it: the move to `cancelled` is saved, the status reads `cancelled`, and the
task offers no move. A reload shows the same line and saves nothing.

### The reason beside the task's status, when the move to `cancelled` is refused or fails

**Refused, because the task's saved status is `done`**

> The status of '{title}' is done, which doesn't allow the move you pressed. A task in done can't be moved.

When the person sees it: they pressed `cancelled` or Move to cancelled, or opened the
confirmation's page again, and the saved status no longer allows the move. Nothing was saved, and
there is nothing for them to do.

**Refused, because the task's saved status is `cancelled`**

> The status of '{title}' is cancelled, which doesn't allow the move you pressed. A task in cancelled can't be moved.

When the person sees it: the same as the refusal for `done`. This is also what they see when they
go back to the confirmation's page after the move was saved.

**Failed, for a reason that is not a refusal, after Move to cancelled**

> The tracker couldn't move '{title}' to cancelled, and nothing was changed. Try again.

When the person sees it: the save behind Move to cancelled didn't complete, and the task is as it
was before the press. The `cancelled` button is offered again, so trying again means pressing it
and confirming.

### The terminal the tracker was started from, when the move's save fails

**Failed, for a reason that is not a refusal, after Move to cancelled**

> The tracker couldn't move '{title}' to cancelled, and nothing was changed.

When the person sees it: they are a developer reading the terminal. The next line, which is not
this change's wording, carries the underlying error exactly as it was reported. Here `{title}` is
the title exactly as saved, with no change to any character.

---

## Wording decisions

- The sentence, the two control labels and the completion line are the strings the spec fixes, in
  `change_spec.md` CP-322 and CP-327, and `CONTENT.md` § Needs confirming (the fourth example) and
  § Completed. They are kept word for word — the standard already gives these exact words for this
  case, and nothing found in the corpus or the states argues for others.
- The completion line, the failure line and the terminal line are the product's existing move
  strings with the status `cancelled` in them. No second string was written for any of them. The
  existing ones read "You moved '{title}' to {status}." and "The tracker couldn't move '{title}' to
  {status}, and nothing was changed." on the pages and in the terminal today. One concept keeps one
  string, and a separate cancelled wording would make two strings for one action.
- The completion line carries no consequence clause. `CONTENT.md` § Completed adds one only when the
  visible consequence differs from what the reader would assume. The pages have no status filter
  for the task to leave (a search of the product's page strings for "filter" found none), and the confirmation sentence
  already said the task can't be moved again, so the absence of move buttons is what the reader
  expects.
- The two refusals are the product's existing per-status refusal strings for `done` and
  `cancelled`, unchanged. They are shared with every other move's refusal, and `change_spec.md`
  CP-342 keeps every refusal assertion of the existing move tests. Rewording them here would change
  every move's refusal, which is beyond this change. The refusal stays true in the three states this
  change sends to it, including a page opened again after the move was saved. In that state the
  move the person pressed is the one that reached the confirmation's page, and it was the move to
  `cancelled`. The unclear fit is raised below as a finding.
- The confirming and back-out controls carry their visible labels as their whole accessible names,
  with no title added. `CONTENT.md` § Accessibility of text adds the thing a control acts on only
  where the same visible label appears more than once on a page. A page shows at most one
  confirmation (`change_spec.md` CP-326), so each label appears once. The sentence just before them,
  which holds the focus, names the task.
- Back out has no line. Opening the confirmation has no line, and reloading it has none. All three
  are reading actions, and `CONTENT.md` § Voice and § Completed give a reading action no message.
- The failure's next action is "Try again." with no "What you typed is still in the form." The
  failure formula includes that sentence only where it is true, and a move has nothing typed.
- A press for a task no task holds answers with the product's existing not-found page, as
  `change_design.md` § A.1 says. This change adds no words to that page, so it has no block above.
- The place for the last block is named "the terminal", not "the console" as the design calls it.
  `CONTENT.md` § Terminology picks "terminal" for that window. The word is used only in this file,
  and no string says either.

---

## Findings for the Content Manager

- "The status of '{title}' is cancelled, which doesn't allow the move you pressed. A task in
  cancelled can't be moved." and its `done` form — `CONTENT.md` § Message patterns, Error, the
  refusal formula states the reason "as a fact about what the reader typed or pressed". It states
  no rule for a refusal shown when the page was opened by a reload or by going back or forward,
  with no press in that request. `change_spec.md` CP-326 and CP-331 now create that state for a
  confirmation's page. The worst case is a reader who confirmed the move, went back, and is told the
  move they pressed isn't allowed, beside a status that shows the move took effect. Meanwhile the
  existing string was kept unchanged, because the press it names did happen, earlier.
