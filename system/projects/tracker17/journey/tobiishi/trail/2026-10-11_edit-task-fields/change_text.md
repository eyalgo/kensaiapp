# Change Text — The task page changes a task's four fields and shows its project

**Date:** 2026-10-11
**Category:** feature
**Behaviour:** changing

---

## Text

Every string below is written to `products/tracker17/docs/CONTENT.md` (Version 9) and to
`system/doctrine/writing_bar.md`. A part in braces is a variable part of its string, and the line
under the string says what fills it. Quotes, commas, full stops and spaces are part of each string
and are placed exactly as shown. A typed value is placed exactly as saved or sent, surrounding spaces
included, between the straight single quotes the string carries. The page title, the heading and the
header every page already carries are unchanged and are not repeated here.

### The task's page: the edit form's field labels and Save button

The form is on every task's page, whatever the task's status.

**The title field's label.** The field states no maximum beside it.

> Title

**The priority control's label**

> Priority

**The priority control's four options, in this order.** The task's priority is chosen.

> low

> medium

> high

> critical

**The assignee control's label**

> Assignee

**The assignee control's option for no assignee.** It comes first, before the names on the assignee
list. It is chosen when the task has no assignee.

> unassigned

Every other option is an assignee name exactly as saved, surrounding spaces included, with no quotes.

**The due-date field's label**

> Due date

**The Save button.** Its accessible name is the same word.

> Save

### The task's page: the project label

**The label, followed by the project's name as plain text.** The name is not a link and no control
changes it.

> Project

The value beside the label is the project's name exactly as saved, surrounding spaces included, with
no quotes.

### The task's page: the left-the-list assignee notice

**The task carries an assignee name that is not on the assignee list.** Plain text beside the
assignee control, never inside the option. Three sentences, in this order. A task whose assignee is
on the list, or that is unassigned, shows no notice.

> The name '{name}' is no longer on the assignee list. Picking another assignee or unassigned replaces it. After that, '{name}' can't be assigned to a task until it's added back on People.

`{name}` is the name the task carries, exactly as saved, surrounding spaces included. Both
occurrences are the same name.

When the person sees it: they opened a task whose assignee was removed on People. They can save
other changes and keep the name, or pick another assignee or `unassigned` to replace it.

### The task's page: the saved-change completion line

**A save changed at least one field and is on disk.** The accessible description of the page
heading, which takes focus. It shows only on the page that answers such a save, and on each reload of
that page.

> You saved changes to '{title}'.

`{title}` is the task's title as now saved, surrounding spaces included.

When the person sees it: they pressed Save with a change, the change is saved, and focus is on the
task's title. They read the new values in the form.

### The task's page: refusal reasons and the reload link

Each reason sits beside the control named, as that control's accessible description. Only one
reason shows at a time.

**Refused: the title has no character other than spaces, tabs or line breaks, or is empty.** Beside
the title field.

> A task needs a title. Type one.

When the person sees it: they pressed Save with a blank title. Nothing was saved, focus is in the
title field, and what they typed and chose in all four fields is still there. They type a title.

**Refused: the title is longer than its maximum.** Beside the title field.

> A task title can't be longer than {maximum} characters. Type a shorter one.

`{maximum}` is the title field's maximum, which is `200` today, written as digits with no separator.
Where the maximum is 1, the first sentence reads `A task title can't be longer than 1 character.`
The string quotes nothing that was sent.

When the person sees it: a request built by hand sent a title over the maximum, since the form can't
send one. Nothing was saved, focus is in the title field, and the form shows the task as saved.

**Refused: the assignee picked is no longer on the assignee list.** Beside the assignee control.
Two sentences, in this order. The task's title in the second sentence is the reload link: a link to
the task's own page with no outcome on it. Its text is the task's title exactly as saved, without the
quotes, which stay outside the link as plain text.

> The name '{name}' is no longer on the assignee list, so this page is out of date. Open '{title}' again to reload the page.

`{name}` is the assignee name the save sent, exactly, surrounding spaces included. `{title}` is the
task's title exactly as saved, surrounding spaces included.

When the person sees it: they pressed Save with a name that left the assignee list after their page
loaded. Nothing was saved, focus is on the assignee control, and the title, priority and due date are
still as entered. Opening the link reloads the page with the assignee list as saved.

**Refused: the priority sent is not one of the four.** Beside the priority control.

> A task's priority has to be low, medium, high or critical. Pick one of the four.

When the person sees it: a request built by hand sent another priority, since the form can't send
one. Nothing was saved and focus is on the priority control.

**Refused: the due date sent is not a calendar date.** Beside the due-date field.

> A due date has to be a calendar date. Give one, or leave the due date empty.

When the person sees it: a request built by hand sent a due date that isn't a calendar date, since
the browser's date field can't send one. Nothing was saved and focus is in the due-date field.

### The task's page: the failed-save message

**A save failed for a reason that is not a refusal.** The accessible description of the edit form,
which takes focus. Three sentences, in this order.

> The tracker couldn't save changes to '{title}', and nothing was changed. What you typed is still in the form. Try again.

`{title}` is the task's title as saved, which the failed save left as it was, surrounding spaces
included. It is not the title typed into the form.

When the person sees it: they pressed Save and the save didn't happen. The task is unchanged, what
they typed and chose is still in the four fields, and they press Save again.

### The terminal: the failed-edit action message

**A save failed for a reason that is not a refusal, and nothing was saved.** Two lines, in this
order, the second straight after the first.

> The tracker couldn't save changes to '{title}', and nothing was changed.

> {error}

`{title}` is the task's title as saved, which the failed save left as it was, surrounding spaces
included. `{error}` is the underlying error exactly as the system reported it, on its own line: the
kind of error first, then a colon, a space and the error's own text. Where the error carries no text
of its own, the line is the kind of error alone. This is the same second line the failed create,
add-task and assignee actions already print.

When the person sees it: they are reading the terminal after the browser said the save didn't happen,
and they learn which action failed, on which task, and what the system reported.

---

## Wording decisions

- **The blank-title, too-long and priority refusals are the add-task form's strings, word for word.**
  The same rule refuses the same value on both forms (CP-165 uses the add's order for that reason), so
  one concept keeps one string. The blank-title refusal is also `CONTENT.md` § Message patterns,
  *Error*'s own example.
- **The due-date refusal ends "Give one, or leave the due date empty.", not the add form's "Pick one,
  or leave the due date empty."** `CONTENT.md` Version 9, § Grammar and mechanics, *Dates and times*,
  says no string tells the reader how to type or pick a date, a refusal included, and names the
  outcome instead ("Give a calendar date, or leave the due date empty."). "Give one" is that example,
  with "one" standing for "a calendar date" from the sentence before, so "calendar date" isn't said
  twice. The add form's string still says "Pick one", which `CONTENT.md` RN-23 records as not meeting
  the rule. This change publishes no text on the project's page, so that string stays as it is here.
  Until a later change aligns it, the two forms word this one refusal two ways.
- **The out-of-date refusal adds "so this page is out of date" to the add form's first sentence.**
  CP-163 requires the reason to say the page is out of date because the name left the list. The
  clause keeps the field's subject at the start (§ Accessibility of text) and keeps the refusal at two
  sentences. "No longer" and "this page is out of date" name no cause and no other tab (§ Terminology,
  the banned "another tab").
- **The reload link is named by the task's title.** Link text names the destination (`CONTENT.md`
  § Accessibility of text, which lists "a task's own title"), and the destination is the task's own
  page. "Again" says why the page links to itself, as "Open People again" and the add form's
  "Open '{project}' again" already do. The reload opens the form from saved values, so the title,
  priority and due date the refusal kept are not on the reloaded page. CP-163 requires the reload,
  and the same trade was raised for the owner in the add-task change, so it isn't raised again.
- **The notice says "Picking another assignee or unassigned", not "choosing another assignee or
  none".** The control's no-assignee option reads `unassigned`, as on the add form, which settled that
  word over the UXD's "none" because `CONTENT.md` § Terminology fixes "unassigned". "Picking" is the
  standard's verb for an option (§ Grammar and mechanics, *Verbs for pressing*).
- **The notice's third sentence says "can't be assigned to a task until it's added back on People".**
  CP-148 asks that the name can be set again only once added back on People. "Set" is the standard's
  verb for your name, and the product already says "Tasks can be assigned only to names on this list."
  on People. `People` is plain text, not a link. The sentence states a consequence and gives no next
  action, so a link would add a step the reader didn't ask for.
- **The completion line is the standard's formula with its fixed verb.** "You saved changes to
  '{title}'." names the task by its title as now saved, so after a title change the reader reads the
  new name. A save with no changed field shows no line (CP-157), so no string is written for it.
- **The failed-save message and the terminal line name the task by its saved title, not the typed
  one.** The save didn't happen, so the task still carries its saved title, and a typed title would
  name a task that doesn't exist. The add form quotes the typed title because the task it would have
  added has no other name. "Couldn't save changes to" pairs with the completion verb.
- **The project label reads "Project".** UXD UX-F9 says the project "shows as text and cannot be
  changed". A labelled value matches the four field labels around it, and the value is the name alone,
  with no quotes, as the task page already writes the assignee's name.
- **The title field states no maximum.** `products/tracker17/docs/UXD.md`'s Version line says the
  comment field and the project-description field state their maximum beside the field, "and no other
  field does". The too-long refusal states the number, as the add
  form's does.
- **A missing task gets no new string.** CP-167 answers with the existing task not-found page, whose
  words the not-found change wrote.
- **The edit form carries no empty-assignee-list sentence.** The design's `Publishes text:` line names
  no such place. When the assignee list is empty, the assignee control offers `unassigned`, plus the
  carried name where there is one.

---

## Findings for the Content Manager

- "The name '{name}' is no longer on the assignee list. Picking another assignee or unassigned
  replaces it. After that, '{name}' can't be assigned to a task until it's added back on People." —
  § Accessibility of text says an instruction beside a field "states the constraint in a full
  sentence", and its two examples are one sentence each. § Grammar and mechanics caps a message at
  three sentences, but the standard doesn't say whether a field instruction is a message or how long
  one may be. Meanwhile the notice keeps to three sentences, each one claim and under 20 words, which
  covers the three things UXD UX-F9 requires it to say.
- "Open '{title}' again to reload the page." — the add-task change raised the same gap for a link
  whose text is a quoted typed value, and for a link to the page the reader is on. This change has
  the same case on the task's page. Meanwhile the link's text is the task's title alone, with the
  string's quotes outside it as plain text.
