# Change Text — Labels on a task

**Date:** 2026-10-12
**Category:** feature
**Behaviour:** changing

---

## Text

Every string below is written to `products/tracker17/docs/CONTENT.md` (Version 9) and to
`system/doctrine/writing_bar.md`. A part in braces is a variable part of its string, and the line
under the string says what fills it. Quotes, commas, full stops and spaces are part of each string and
are placed exactly as shown. A typed value is placed exactly as it was typed or saved, surrounding
spaces included, between the straight single quotes the string carries. Where a string names
`{label}` and no label value came with the outcome, `{label}` is empty and the two quotes stay.

Two variables recur:

- `{label}` is the label exactly as typed or saved, surrounding spaces and letter case included.
- `{title}` is the task's title exactly as saved, surrounding spaces included.

### The task page: the label heading

**The heading of the area that holds the task's labels and the Add form, in every state of the page**

> Labels

When the person sees it: on any task's page, after the edit form. It names the area where labels go
on and come off.

### The task page: the label field

**The visible label of the text field that takes one more label, in every state of the page.** It is
also the field's accessible name. The field states no maximum beside it.

> Label

When the person sees it: they reach the field to type a label, then press Add.

### The task page: the no-labels sentence

**The task carries no label.** In the place of the list of labels, with the label field and Add in
view. Two sentences, in this order.

> This task has no labels. Type a label and press Add.

When the person sees it: they opened a task that has never had a label, or they removed its last one.
They can type a label and press Add.

### The task page: the Add and Remove buttons

**The Add button: its visible label**

> Add

**The Add button: its accessible name.** The same word.

> Add

When the person hears it: they moved from the label field to the button that puts the typed label on
this task.

**The Remove button beside each label: its visible label**

> Remove

**The Remove button beside each label: its accessible name**

> Remove label '{label}' from '{title}'

`{label}` is the label this button takes off, as saved. `{title}` is the title of the task the page
shows.

When the person hears it: they moved to a Remove button, and they learn which label it takes off which
task before they press it.

### The task page: completion lines

**A label was added.** The one completion line, which is the accessible description of the added label
in the list. The same line shows on every reload of that page.

> You added the label '{label}' to '{title}'.

`{label}` is the added label as saved.

When the person sees it: they pressed Add, the label is saved at the end of the task's labels, and
focus is on that label. The next Tab press goes on to its Remove button.

**A label was removed.** The one completion line, at the top of the page, which is the accessible
description of the task's heading. The same line shows on every reload of that page.

> You removed the label '{label}' from '{title}'.

`{label}` is the removed label exactly as it was saved.

When the person sees it: they pressed Remove, the label has left the list, the task's other labels
stay in their order, and focus is on the task's heading.

### The task page: refusal reasons

**Refused: Add was pressed with the label field holding no character at all.** Beside the label field,
as its accessible description. Two sentences, in this order.

> A label needs at least one character. Type a label.

When the person sees it: they pressed Add with the field empty. Focus is in the label field, the field
holds what they typed, which is nothing, and they type a label.

**Refused: the label sent is longer than its maximum.** Beside the label field, as its accessible
description. Two sentences, in this order.

> A label can't be longer than {maximum} characters. Type a shorter one.

`{maximum}` is the label maximum, which is `200` today, written as digits with no separator. Where the
maximum is 1, the first sentence reads `A label can't be longer than 1 character.` The string quotes
nothing that was sent.

When the person sees it: a request built by hand sent a label over the maximum, since the field can't
send one. Focus is in the label field, the field is empty, and they type a shorter label.

**Refused: the label pressed Remove for isn't on the task.** In the label area, as the accessible
description of that area. Two sentences, in this order.

> The label '{label}' isn't on '{title}'. The labels shown are the ones the task carries.

`{label}` is the label the pressed Remove button was for, exactly as it was sent.

When the person sees it: they pressed Remove beside a label the task no longer carried when the
tracker read it. Nothing was changed, the labels listed are the task's labels as saved, and focus is
on the label area.

### The task page: failed-action messages

**The label couldn't be added, for a reason that is not a refusal.** Beside the Add form, as its
accessible description. Three sentences, in this order.

> The tracker couldn't add the label '{label}' to '{title}', and nothing was changed. What you typed is still in the form. Try again.

`{label}` is the label as typed.

When the person sees it: they pressed Add and the save didn't happen. What they typed is still in the
label field, and they press Add again.

**The label couldn't be removed, for a reason that is not a refusal.** In the label area, as the
accessible description of that area. Two sentences, in this order.

> The tracker couldn't remove the label '{label}' from '{title}', and nothing was changed. Try again.

`{label}` is the label the pressed Remove button was for, exactly as saved.

When the person sees it: they pressed Remove and the save didn't happen. The label is still listed,
focus is on the label area, and they press its Remove button again.

### The terminal: failed label actions

**An add failed for a reason that is not a refusal, and nothing was saved.** Two lines, in this order,
the second straight after the first.

> The tracker couldn't add the label '{label}' to '{title}', and nothing was changed.

> {error}

**A remove failed for a reason that is not a refusal, and nothing was saved.** Two lines, in this
order, the second straight after the first.

> The tracker couldn't remove the label '{label}' from '{title}', and nothing was changed.

> {error}

In both, `{label}` is the label exactly as it was sent. `{title}` is the task's title as saved when the
action was sent. `{error}` is the underlying error exactly as the system reported it, on its own line:
the kind of error first, then a colon, a space and the error's own text. Where the error carries no
text of its own, the line is the kind of error alone. This is the same second line every other failed
action already prints.

**An add or a remove failed before the task's title could be read.** The first line of the pair
above is replaced by the matching line below, and the `{error}` line follows it unchanged.

> The tracker couldn't add the label '{label}', and nothing was changed.

> The tracker couldn't remove the label '{label}', and nothing was changed.

When the person sees it: they are reading the terminal after the browser said the add or the remove
didn't happen. They learn which action failed, on which label of which task, and what the system
reported.

---

## Wording decisions

- **The no-labels place carries two sentences, where the spec says "a sentence".** CP-183 fixes what
  the place says, that the task has no labels with the field and Add in view. `CONTENT.md`
  § Message patterns, *Empty*, sets the formula as "one sentence that says what is absent", "Then one
  sentence naming the one thing to do next and the control to do it with, by its label". The second
  sentence follows the corpus's own invitation on a project with no tasks, "Give the first task a
  title and press Add." The meaning CP-183 fixes is unchanged.
- **The no-labels sentence says "has no labels", without "yet".** Every *Empty* example in
  `CONTENT.md` says "yet", and this state is also reached by removing a task's last label. "Yet" would
  then imply a label is expected. The formula itself asks only for "what is absent", so the smaller
  true sentence meets it.
- **The completion lines say "the label" before the quoted value and name the task.** A label is free
  text, and "You added 'ui' to 'Set up CI'." leaves a screen reader user to infer what 'ui' is. "The
  label" names the product's term (`CONTENT.md` § Terminology, "A word attached to a task"), and the
  task's title makes the line say who acted and on what, the first fallback in § Voice. The pair
  matches the Remove button's accessible name, which the standard fixes as "Remove label 'bug' from
  'Set up CI'" (`CONTENT.md` § Accessibility of text), so one action is worded one way on the button,
  the page and the terminal.
- **The removal line carries no consequence clause.** `CONTENT.md` § Message patterns, *Completed*,
  adds a consequence only "When the action's visible consequence differs from what the reader would
  assume". Removing a label from one task touches only that task, which is what a person removing it
  from that task's page assumes. The assignee removal's clause exists because a name stays on other
  tasks, and no label has a list of its own for that to apply to.
- **The empty refusal reads "A label needs at least one character."** It names the field's subject
  first, as `CONTENT.md` § Accessibility of text requires. "At least one character" is exactly the rule
  CP-188 and CP-190 fix: a label of spaces only is accepted, so a sentence asking for "a name" or "some
  text" would suggest a rule the tracker doesn't have. The action is "Type a label.", not the corpus's
  "Type one.", because "one" would sit after "character" and could be read as asking for one
  character.
- **The over-long refusal states the maximum, and the field states none.** This matches the task
  title's refusal in the corpus, "A task title can't be longer than {maximum} characters. Type a
  shorter one.", on the task page's edit form. The refusal is reached
  only by a request built by hand, and "Type a shorter one" can't be followed without the number. The
  field carries no note under CP-186.
- **The stale-remove refusal says "isn't on", not "is no longer on".** The People page's precedent
  reads "The name '{name}' is no longer on the assignee list." "No longer" claims the label was on the
  task before. The tracker establishes only that the label isn't on the task when the remove is read,
  and the design sends a forged value, including an empty one, to this same refusal
  (`change_design.md` § Architect Review Notes, *Missing-task and removal checks*). "Isn't on" is the
  smaller true thing (`CONTENT.md` § Voice, "State only what the tracker established"). The sentence
  names no other tab and no cause (`CONTENT.md` § Terminology, banned "another tab").
- **The stale-remove refusal's second sentence states the page's state instead of giving an action.**
  The page that answers already shows the task's labels as saved, so a reload changes nothing and the
  label the person wanted off is already off. The refusal formula asks for "one action", and § Voice
  says "Give one next action when one exists, and none when none does". The second sentence tells the
  person the list they now see is current, which is what a reader of an out-of-date page doubts. The
  missing rule is raised below.
- **The failed remove has no "What you typed is still in the form."** Nothing was typed for a remove,
  so the message has two sentences. This follows the corpus's failed assignee removal.
- **The terminal lines name the task as well as the label.** The terminal is read away from the page,
  and a label alone doesn't say which task the action was on. The failed edit's terminal line already
  names the task by its saved title, "The tracker couldn't save changes to '{title}', and nothing was
  changed." A shorter form with no title is written for a failure that comes before the title is
  read, so the Developer never fills `{title}` with nothing.
- **The Add button's accessible name is its own word.** `CONTENT.md` § Accessibility of text adds the
  acted-on thing only "Where the same visible label appears more than once on a page", and Add appears
  once on the task page today. When the comment form brings a second Add to this page, that rule
  applies to both, and the string is re-checked in that change.
- **The field label is "Label", and the heading is "Labels".** The heading follows the section-heading
  pattern `DESIGN.md` § Typography names ("Comments", "Your name", "Assignees"), and it matches the task
  list's Labels column. The field label is the singular, since the field takes one label, as the People
  page's field is "Name" under the Assignees heading.
- **A repeated add has no string.** CP-189 fixes that the page shows no completion line and no refusal,
  so no wording exists for that state.
- **Banned-word check.** Every string above was searched for each word in `CONTENT.md` § Terminology,
  *Banned in anything a person sees*, and for the banned punctuation in § Grammar and mechanics. No hit
  was found. The product carries no check that enforces its vocabulary, so none was run.

---

## Findings for the Content Manager

- "Remove label '{label}' from '{title}'" — § Accessibility of text gives this form as its example and
  states no rule for two labels on one task that an assistive technology may read alike, such as
  labels that differ only in surrounding spaces, or two labels of spaces only. CP-188 accepts both.
  The People page raised the same gap for assignee names (`tracker17 · tobiishi ·
  2026-10-11_people-page-assignee-list`, `change_text.md` § Findings for the Content Manager), and the
  standard still has no rule for it. Meanwhile the string is the standard's own example form, with no
  position added.
- "The label '{label}' isn't on '{title}'. The labels shown are the ones the task carries." — the
  refusal formula in § Message patterns, *Error*, asks for the reason "then one action", and § Voice
  says to give no next action where none exists. The standard doesn't say which governs a refusal
  whose page already shows the state the person wanted. Meanwhile the second sentence states that the
  labels shown are current, and gives no action.
