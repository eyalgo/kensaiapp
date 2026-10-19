# Change Text — Add a task and read the project's ordered list

**Date:** 2026-10-11
**Category:** feature
**Behaviour:** changing

---

## Text

Every string below is written to `products/tracker17/docs/CONTENT.md` (Version 8) and to
`system/doctrine/writing_bar.md`. A part in braces is a variable part of its string, and the line
under the string says what fills it. Quotes, commas, full stops, spaces and the hyphen in a page
title are part of each string and are placed exactly as shown. A typed value is placed exactly as it
was typed or saved, surrounding spaces included, between the straight single quotes the string
carries. The header every page already carries (`tracker17`, `Projects`, `People`) is unchanged and
is not repeated here.

### The project's page: the add-task form

The form sits on the project's page whether or not the project holds tasks.

**The title field's label**

> Title

**The priority control's label**

> Priority

**The priority control's four options, in this order.** `medium` is chosen when the page opens.

> low

> medium

> high

> critical

**The assignee control's label**

> Assignee

**The assignee control's option for no assignee.** It comes first, before the names on the assignee
list, and is chosen when the page opens.

> unassigned

**The assignee list holds no name.** The control offers only the option above, and this sentence
sits beside the control. The word `People` in the second sentence is a link to the People page, and
its accessible name is the same word.

> There are no assignees yet. Open People to add one.

When the person sees it: they opened a project before adding any name on People. They can add the
task unassigned, or open People to add a name first.

**The due-date field's label**

> Due date

**The Add button.** Its accessible name is the same word.

> Add

### The project's page: the first-task invitation

**The project holds no task.** In the list's place, with the add-task form in view. It replaces
today's "This project has no tasks yet." line, whose first sentence it keeps.

> This project has no tasks yet. Give the first task a title and press Add.

When the person sees it: they opened a project, a new one included, that holds no task. They can
type a title and press Add.

### The project's page: the task list's column headers and empty cells

**The six column headers, in this order**

> Title

> Status

> Priority

> Assignee

> Labels

> Due date

**A row's title link: its visible text** is the task's title exactly as saved, and nothing else.

**A row's title link: its accessible name**

> {title}, number {position} on the task list

`{title}` is the task's title exactly as saved, surrounding spaces included, with no quotes.
`{position}` is the row's place in the list as this page shows it, counting from 1 at the top row,
written as digits.

When the person hears it: they moved to a task's title, and they learn which row it opens, even
where two tasks share a title.

**The assignee cell of a task with no assignee**

> unassigned

**The labels cell of a task that carries no label.** Every task holds none in this change.

> none

**The due-date cell of a task with no due date**

> none

### The project's page: the overdue marking

**An open task's due date is before today.** Beside the due date in that row's due-date cell, after
the date.

> Overdue

When the person sees it: they read the list and see which open tasks are past their due date. A task
due today, a task with no due date, and a task in `done` or `cancelled` show no marker.

### The project's page: when an add is refused or fails

**Refused: the title has no character other than spaces, tabs or line breaks, or is empty.** Beside
the title field, as its accessible description.

> A task needs a title. Type one.

When the person sees it: they pressed Add with a blank title. Focus is in the title field, what they
typed and chose in all four fields is still there, and they type a title.

**Refused: the title is longer than its maximum.** Beside the title field, as its accessible
description.

> A task title can't be longer than {maximum} characters. Type a shorter one.

`{maximum}` is the title field's maximum, which is `200` today, written as digits with no separator.
Where the maximum is 1, the first sentence reads `A task title can't be longer than 1 character.`
The string quotes nothing that was sent.

When the person sees it: a request built by hand sent a title over the maximum, since the form can't
send one. Focus is in the title field, the form shows its opening values, and they type a shorter
title.

**Refused: the assignee picked is no longer on the assignee list.** Beside the assignee control, as
its accessible description. Two sentences, in this order. The project's name in the second sentence
is a link to the project's page with no outcome on it, and its text is the project's name exactly as
saved, without the quotes, which stay outside the link as plain text.

> The name '{name}' is no longer on the assignee list. Open '{project}' again to reload the page.

`{name}` is the assignee name the add sent, exactly, surrounding spaces included. `{project}` is the
project's name exactly as saved, surrounding spaces included.

When the person sees it: they pressed Add with a name that left the assignee list after their page
loaded. Nothing was saved, focus is on the assignee control, which now offers the list as saved with
`unassigned` chosen, and the title, priority and due date are still as entered.

**Refused: the priority sent is not one of the four.** Beside the priority control, as its
accessible description.

> A task's priority has to be low, medium, high or critical. Pick one of the four.

When the person sees it: a request built by hand sent another priority, since the form can't send
one. Focus is on the priority control, which shows `medium`, and the other fields are as sent.

**Refused: the due date sent is not a calendar date.** Beside the due-date field, as its accessible
description.

> A due date has to be a calendar date. Pick one, or leave the due date empty.

When the person sees it: a request built by hand sent a due date that isn't a calendar date, since
the browser's date picker can't send one. Focus is in the due-date field, which is empty, and the
other fields are as sent.

**The task couldn't be added, for a reason that is not a refusal.** As the accessible description of
the add-task form, which takes focus. Three sentences, in this order.

> The tracker couldn't add '{title}', and nothing was changed. What you typed is still in the form. Try again.

`{title}` is the title as typed, exactly, surrounding spaces included.

When the person sees it: they pressed Add and the save didn't happen. No task was added, what they
typed and chose is still in the four fields, and they press Add again.

### The task's page and its completion line

**The page title, in every state of the page**

> {title} - tracker17

`{title}` is the task's title exactly as saved, surrounding spaces included, with no quotes.

**The page heading, in every state of the page**

> {title}

`{title}` is the task's title exactly as saved, surrounding spaces included, with no quotes.

**The three labels under the heading, in this order, each followed by its value**

> Priority

> Assignee

> Due date

**The Priority value** is the task's priority word as saved: `low`, `medium`, `high` or `critical`.

**The Assignee value** is the assignee name exactly as saved, surrounding spaces included, with no
quotes. A task with no assignee shows:

> unassigned

**The Due date value** is the due date written `YYYY-MM-DD`. A task with no due date shows:

> none

**A task was added.** The completion line, which is the accessible description of the page heading.
It shows only on the page that answers an add, and on each reload of that page.

> You added '{title}'.

`{title}` is the added task's title exactly as saved, surrounding spaces included.

When the person sees it: they pressed Add, the task is saved, and focus is on the task's title. They
read back what they added.

### The missing-task page

**An address shaped like a task's address that names no task.** The page title, the heading, then
one sentence. The word `Projects` in the sentence is a link to the Projects page, and its accessible
name is the same word.

> Not found - tracker17

> There's no task at this address

> Open Projects.

When the person sees it: they opened a task address with nothing at it. They can open Projects.

### The terminal, when an add fails

**An add failed for a reason that is not a refusal, and nothing was saved.** Two lines, in this
order, the second straight after the first.

> The tracker couldn't add '{title}', and nothing was changed.

> {error}

`{title}` is the title exactly as it was sent, surrounding spaces included. `{error}` is the
underlying error exactly as the system reported it, on its own line: the kind of error first, then a
colon, a space and the error's own text. Where the error carries no text of its own, the line is the
kind of error alone. This is the same second line the failed create and the failed assignee actions
already print.

When the person sees it: they are reading the terminal after the browser said the add didn't happen,
and they learn which action failed, on which title, and what the system reported.

---

## Wording decisions

- **The first-task invitation is the standard's own example, used verbatim.** `CONTENT.md`
  § Message patterns, *Empty*, gives "This project has no tasks yet. Give the first task a title and
  press Add." CP-126 needs what it says. Its first sentence is the line the page shows today, so the
  page keeps it and adds the invitation.
- **The blank-title refusal, the failure message and the completion line are the standard's own
  examples, used verbatim.** "A task needs a title. Type one." (§ *Error*, refusal), "The tracker
  couldn't add 'Set up CI', and nothing was changed. What you typed is still in the form. Try again."
  (§ *Error*, failure) and "You added 'Set up CI'." (§ *Completed*).
- **The completion line and the failure message don't name the project.** CP-124 says the task's page
  shows nothing else of the task, so the completion line names the title alone. The failure message
  is shown on the project's own page. The terminal line repeats the browser's first sentence, as the
  failed create and the assignee lines already do. The assignee lines carry "to the assignees", so a
  bare "couldn't add '{title}'" is the task's.
- **The no-assignee option reads `unassigned`, not "none".** The UXD calls the option "none" (UX-F3).
  `CONTENT.md` § Terminology fixes "unassigned" for a task with no assignee, and the task's row and
  page say it. Using the same word in the control means one term for the concept, and a reader who
  picks it sees the same word come back.
- **The empty assignee list gets a sentence, not a bare link.** CP-109 puts a link to People beside
  the control "so the operator can see why there is no one to pick". On its own, a link reading
  "People" doesn't say why. The sentence follows the *Empty* formula: what is absent, in the
  standard's own People wording ("There are no assignees yet."), then the one thing to do, naming the
  link by its label. The link shares its text with the header's People link, which `CONTENT.md` RN-20
  allows for two links to one address. `DESIGN.md` § Components counts four field hints in the
  product. This sentence is an empty state, not a hint about filling the field. If the design treats
  it as a hint, it doesn't count it yet.
- **An empty labels cell and an undated due date show `none`, and the task page's undated value is the
  same word.** CP-128 and CP-129 leave the empty cells to this step, and CP-124 needs the task page to
  say a task has no due date. A blank cell leaves a sighted reader guessing, and some screen readers
  read it as "blank". One short word under the column header says the value is absent. It is
  lowercase like `unassigned` and the status and priority words in the cells beside it, which are
  lowercase as `CONTENT.md` defines them. One word for "this cell has no value" means two strings
  for one concept are not written.
- **A row's title link has an accessible name that adds its position.** CP-111 lets two tasks in one
  project share a title, and CP-127 makes each title a link to its own task's page. `CONTENT.md`
  § Accessibility of text says "Two links to different places never share their text", and also says
  link text is "a task's own title". The visible text stays the title alone. The accessible name
  begins with the title, so the visible label is one unbroken string at its start (SC 2.5.3), and
  then adds the row's position, as the People page's Remove button already does ("number {position}
  on the assignee list"). Every row gets it, so the name never depends on whether another title
  matches. That also covers titles that differ only in repeated spaces. The gap in the standard is
  raised below.
- **The stale-assignee refusal opens "The name '{name}'", not "An assignee named".** The name is no
  longer an assignee, so calling it one would contradict the sentence. The sentence is the People
  page's stale-remove reason word for word, so one fact is worded one way. "No longer" names no cause
  and no other tab (`CONTENT.md` § Terminology, banned "another tab", "another window").
- **The stale-assignee reload is a link named by the project, and the sentence says it reloads the
  page.** CP-119 requires the reason to offer a reload, and `change_design.md` § 3, Sub-job D, gives
  "an ordinary reload link". Link text names the destination (`CONTENT.md` § Accessibility of text),
  and the destination is the project's own page. "Again" says why the page links to itself, as "Open
  People again" does on People. **For the owner of the change's meaning:** the refused page already
  rebuilds the assignee choices from the saved list (`change_design.md` § 3, the outcome table's
  "Assignee no longer listed" row). The reload therefore shows the reader nothing new, and it opens
  the form at its opening values, so the title, priority and due date the refusal kept are gone. The
  string does what the spec and design ask. It doesn't tell the reader to pick again from the
  rebuilt list, because that would replace the reload the spec requires. If the reload should go,
  that is a spec change, and the second sentence would become "Pick another name, or pick
  unassigned."
- **The over-long refusal states the maximum, and the title field states none.** This matches the
  project-name and assignee-name refusals. The refusal is reached only by a request built by hand,
  and "Type a shorter one" can't be followed without the number. Its subject is "A task title" so
  the first words name the field (`CONTENT.md` § Accessibility of text).
- **The priority and due-date refusals don't quote the value sent.** Only a request built by hand
  sends either, as with the over-long title, which quotes nothing sent. Each sentence states the rule
  the value broke, without "invalid" or "wrong" (`CONTENT.md` § Terminology, the banned list). The
  priority words are written as defined and don't start the sentence (§ Grammar and mechanics,
  Case).
- **The due-date refusal offers leaving the field empty.** The due date is optional (CP-110), and
  "Pick one." alone would read as if a date were needed. The sentence says nothing about how to type
  or pick a date, since the field's display is the browser's own (§ Grammar and mechanics, Dates and
  times).
- **The form and the list have no heading of their own.** The spec and the design name none. Every
  field is labelled, the column headers name the list's contents, and the page heading is the
  project's name. A heading would add words the reader doesn't need. This follows the People change,
  which put no heading over its one-field form.
- **The task page shows no "Overdue" marker.** `DESIGN.md` § Components says "The task page shows the
  same marker beside its due date". CP-124 and `change_design.md` § 3, Sub-job D ("New task pages show
  only title/priority/assignee/due date"), don't create that state on this page, and whether a state
  exists isn't this step's call. A task added with a past due date shows its date on its page with no
  marker, and with the marker in the project's list.
- **The task page carries no link back to its project.** Neither the spec nor the design names one,
  and CP-124 says the page shows nothing else of the task. The reader returns through Projects, which
  `products/tracker17/docs/UXD.md` RN-27 accepts ("adding several tasks in a row means returning to the
  project each time").

---

## Findings for the Content Manager

- "{title}, number {position} on the task list" — § Accessibility of text says "Two links to
  different places never share their text" and gives "a task's own title" as link text. It states
  no rule for two tasks whose titles match, which CP-111 allows. Meanwhile the visible text stays the
  title, and the accessible name adds the row's position in the words the People page's Remove
  button uses. This is the same gap the People change raised for Remove buttons, now for links.
- "unassigned" and "none" in table cells — § Grammar and mechanics, Case, makes the product name and
  the status and priority words the only exceptions to sentence case, and names table cells only for
  those words. § Terminology writes "unassigned" lowercase for a task row. The standard doesn't say
  what case a cell's own word takes. Meanwhile both are lowercase, matching the Terminology row and
  the status and priority words in the cells beside them.
- "Open '{project}' again to reload the page." — § Accessibility of text says link text "names the
  destination and nothing else". It doesn't say how quotes around a typed value used as link text
  sit, or how to word a link to the page the reader is on. The People change raised the second gap.
  Meanwhile the link's text is the project's name alone, with the string's quotes outside it as plain
  text.
