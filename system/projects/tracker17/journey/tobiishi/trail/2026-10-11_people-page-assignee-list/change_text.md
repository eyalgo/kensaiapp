# Change Text — The People page keeps the assignee list

**Date:** 2026-10-11
**Category:** feature
**Behaviour:** changing

---

## Text

Every string below is written to `products/tracker17/docs/CONTENT.md` (Version 8) and to
`system/doctrine/writing_bar.md`. A part in braces is a variable part of its string, and the line
under the string says what fills it. Quotes, commas, full stops, spaces and the hyphen in the page
title are part of each string and are placed exactly as shown. A typed value is placed exactly as it
was typed or saved, surrounding spaces included, between the straight single quotes the string
carries.

### The header, on every page the tracker serves

**The header, on the Projects page, a project's page, the not-found page and the People page.** The
product name, then two links, in this order.

> tracker17

> Projects

> People

The first is the product name as it sits in the header. The second is the link to the Projects page.
The third is the link to the People page. Each link's accessible name is its own word.

When the person sees it: on any page, they can open Projects or People from the header.

### The People page

**The page title, in every state of the page**

> People - tracker17

When the person sees it: in the browser tab and window title, on the People page.

**The page heading, in every state of the page**

> People

**The heading of the area that holds the assignee list and the Add form, in every state of the page**

> Assignees

**The assignee list holds no name.** In the list's place, with the Add form in view.

> There are no assignees yet. Tasks can be assigned only to names on this list.

When the person sees it: they opened People before adding any name, or they removed the last one.
They can type a name and press Add.

**The Add form's field label**

> Name

**The Add button.** Its accessible name is the same word.

> Add

**The Remove button beside each listed name: its visible label**

> Remove

**The Remove button beside each listed name: its accessible name**

> Remove '{name}', number {position} on the assignee list

`{name}` is the listed name exactly as saved, surrounding spaces included. `{position}` is the row's
place in the list as this page shows it, counting from 1 at the earliest-added name, written as
digits.

When the person hears it: they moved to a Remove button, and they learn which name it takes off the
list before they press it.

### The People page, after an add or a remove

**A name was added.** The completion line, which is the accessible description of the added name in
the list. The same line shows on every reload of that page.

> You added '{name}' to the assignees.

`{name}` is the added name exactly as saved, surrounding spaces included.

When the person sees it: they pressed Add, the name is saved at the end of the list, and focus is on
that name. The next Tab press goes on to its Remove button.

**A name was removed.** The completion line, at the top of the Assignees area, which is the
accessible description of the Assignees heading. The same line shows on every reload of that page.

> You removed '{name}' from the assignees, and tasks that already carry the name keep it.

`{name}` is the removed name exactly as it was saved, surrounding spaces included.

When the person sees it: they pressed a Remove button, the name has left the list, and focus is on
the Assignees heading.

**Refused: the name has no character other than spaces, tabs or line breaks, or is empty.** Beside
the name field, as its accessible description.

> An assignee needs a name. Type one.

When the person sees it: they pressed Add with a blank name. Focus is in the name field, what they
typed is still in it, and they type a name.

**Refused: exactly this name is already on the assignee list.** Beside the name field, as its
accessible description.

> An assignee named '{name}' is already on the list. Choose a different name.

`{name}` is the name as typed, exactly, surrounding spaces included.

When the person sees it: they pressed Add with a name the list already holds, compared exactly.
Focus is in the name field, what they typed is still in it, and they change the name.

**Refused: the name is longer than its maximum.** Beside the name field, as its accessible
description.

> An assignee name can't be longer than {maximum} characters. Type a shorter one.

`{maximum}` is the name field's maximum, which is `200` today, written as digits with no separator.
Where the maximum is 1, the first sentence reads `An assignee name can't be longer than 1 character.`
The string quotes nothing that was sent.

When the person sees it: a request built by hand sent a name over the maximum, since the form can't
send one. Focus is in the name field, the field is empty, and they type a shorter name.

**Refused: the name pressed Remove for is no longer on the assignee list.** In the completion line's
place at the top of the Assignees area, as the accessible description of the Assignees heading. Two
sentences, in this order. The word `People` in the second sentence is a link to the People page with
no outcome on it, so opening it shows the list with no line.

> The name '{name}' is no longer on the assignee list. Open People again to reload the list.

`{name}` is the name the pressed Remove button was for, exactly as that page showed it, surrounding
spaces included. The link's text is `People` and nothing else, and its accessible name is the same
word.

When the person sees it: they pressed Remove beside a name that had left the list after their page
loaded. The list shown is the list as saved, nothing was changed, and focus is on the Assignees
heading.

**The name couldn't be added, for a reason that is not a refusal.** Beside the Add button, as its
accessible description. Three sentences, in this order.

> The tracker couldn't add '{name}' to the assignees, and nothing was changed. What you typed is still in the form. Try again.

`{name}` is the name as typed, exactly, surrounding spaces included.

When the person sees it: they pressed Add and the save didn't happen. Focus is on Add, what they
typed is still in the name field, and they press Add again.

**The name couldn't be removed, for a reason that is not a refusal.** Beside that name's Remove
button, as its accessible description. Two sentences, in this order.

> The tracker couldn't remove '{name}' from the assignees, and nothing was changed. Try again.

`{name}` is the name the pressed Remove button was for, exactly as saved, surrounding spaces
included.

When the person sees it: they pressed Remove and the save didn't happen. The name is still listed,
focus is on its Remove button, and they press Remove again.

### The terminal, when an add or a remove fails

**An add failed for a reason that is not a refusal, and nothing was saved.** Two lines, in this
order, the second straight after the first.

> The tracker couldn't add '{name}' to the assignees, and nothing was changed.

> {error}

**A remove failed for a reason that is not a refusal, and nothing was saved.** Two lines, in this
order, the second straight after the first.

> The tracker couldn't remove '{name}' from the assignees, and nothing was changed.

> {error}

In both, `{name}` is the name exactly as it was sent, surrounding spaces included. `{error}` is the
underlying error exactly as the system reported it, on its own line: the kind of error first, then a
colon, a space and the error's own text, such as
`PermissionError: [Errno 13] Permission denied: '/Users/sam/tracker17/data/tracker.json'`. Where the
error carries no text of its own, the line is the kind of error alone. This is the same second line
the failed create already prints.

When the person sees it: they are reading the terminal after the browser said the add or the remove
didn't happen, and they learn which action failed, on which name, and what the system reported.

---

## Wording decisions

- **Remove's accessible name carries the row's position as well as the name.** CP-83 requires that
  "two Remove controls never share an accessible name", and CP-88 lets two names differ only in
  repeated spaces, which an assistive technology may read as one. The design fixes the device
  (`change_design.md` § Architect Review Notes, *Accessible-name uniqueness*, "Include the row ordinal
  in Remove's accessible wording"), and the words are this record's. "Number {position} on the
  assignee list" names the position in the product's own term for the list. "Remove" opens the name,
  so the visible label is one unbroken string at its start. The rule the standard lacks for this case
  is raised below.
- **The add and remove lines name the assignees as where the name went or came from.** The standard's
  own removal example reads "You removed 'Dana' from the assignees, and tasks that already carry the
  name keep it." (`CONTENT.md` § Message patterns, *Completed*), and that line is used verbatim. The
  add line, both browser failure messages and both terminal lines take the same "to the assignees" or
  "from the assignees", so one action is worded one way in every place. The terminal line especially
  needs it, because it is read away from the page, and later changes will add tasks and labels too.
- **The empty state and the removal line mention tasks, though CP-85 says no word on People points at
  a task or an assignment.** CP-84 requires the empty state to say "that tasks can be assigned only to
  names on this list", and CP-94 requires the removal line to say "that tasks already carrying the
  name keep it". The spec's own example row for the empty page sets both side by side (`change_spec.md`
  § Examples, "`GET` People, list empty"). On that reading, CP-85 bars a link to, a control for or an
  instruction about the task features, and both sentences state a rule about the list. Both claims
  hold today, because no task exists to break them. The empty state is the standard's own People
  example (`CONTENT.md` § Message patterns, *Empty*).
- **The empty state names no control, though the Empty formula's second sentence does.** The formula
  asks for "one sentence naming the one thing to do next and the control to do it with", and the
  standard's own People example, which CP-84 requires in substance, has a rule about the list
  instead. The Add form is in view under it. The difference in the standard is raised below.
- **The stale remove's reason starts "The name '{name}'", not "An assignee named".** The name is no
  longer an assignee, so a subject calling it one would contradict the sentence's own claim. "No
  longer" says only that it left the list. It names no cause and no other tab (`CONTENT.md`
  § Terminology, banned "another tab", "another window").
- **The stale remove's action is "Open People again to reload the list.", with `People` as the
  link.** CP-96 requires the reason to offer a reload. A browser reload of this page shows the same
  reason again (`products/tracker17/docs/SDD.md` § 4 RT-8, "A reload of that page, or a return to it
  through back, shows the same line at the same place"), so the reload the design gives is a link to
  the People page with no outcome on it (`change_design.md` § 3, Sub-job D, the outcome table's
  stale-remove row). Link text names the destination and nothing else (`CONTENT.md` § Accessibility of text),
  and a link to the same address as the header's People link shares its text (`CONTENT.md` RN-20).
  "Again" tells the reader why the page links to itself. The sentence doesn't say the reload shows the
  list as saved, because the page already shows it. The missing rule is raised below.
- **The failed remove has no "What you typed is still in the form."** Nothing was typed for a remove.
  Its second sentence is the action, so the message has two sentences.
- **The duplicate refusal opens "An assignee named '{name}'".** That follows the project refusal's
  shape, "A project named 'Alpha' already exists." (`CONTENT.md` § Message patterns, *Error*), so the
  first words name the field's subject, as § Accessibility of text requires. "Is already on the list"
  is what CP-90 says is true. The action, "Choose a different name.", is the corpus's own words for the
  same next step.
- **The over-long refusal states the maximum, and the name field states none.** UXD version 4 keeps
  the maximum beside only the comment and description fields (`products/tracker17/docs/UXD.md`, the
  Version line). The refusal is reached only by a request built by hand, and "Type a shorter one"
  can't be followed without the number. This matches the project name's refusal.
- **The field label is "Name".** It is the corpus's label for the project form's name field, and the
  Assignees heading above it says whose name it is. The field carries no note, under the same UXD
  version 4 rule.
- **The header carries Projects and People, and no All tasks.** `products/tracker17/docs/DESIGN.md`
  § Layout, *Header*, lists three links in the order Projects, All tasks, People. CP-85 bars a word
  for an area the tracker doesn't have yet, and the design omits absent areas (`change_design.md` § 3,
  Sub-job D, "with absent areas omitted under CP-85").
- **The People page has two headings and no form heading.** "People" is the page title heading and
  "Assignees" is the section heading (`DESIGN.md` § Typography, the page-title and section-heading
  rows, which name both words). The
  design names the Assignees heading as the focus target after a remove. A heading over the Add form
  would add a word the reader doesn't need, since the form's one field is labelled.
- **No Your name heading or sentence, and no comment wording.** CP-85 and the spec's § Out of Scope.
- **A later page whose added or failed-remove name has left the list shows the same line.** The design
  keeps the outcome line and moves its focus to the Assignees heading (`change_design.md` § 3, Sub-job
  D, "keep the outcome line and use the sheet heading as its description target"). Each line is past
  tense or states what the tracker did, so it stays true, and no second string is written for it.

---

## Findings for the Content Manager

- "Remove '{name}', number {position} on the assignee list" — § Accessibility of text says the
  accessible name "adds the thing the control acts on" where a visible label repeats, and states no
  rule for two things whose names an assistive technology may read alike, such as names that differ
  only in repeated spaces. Meanwhile the name adds the row's position after the name, in the
  product's term for the list.
- "Open People again to reload the list." — § Accessibility of text says link text "names the
  destination and nothing else", and the out-of-date refusal's example, "Reload the page to see it.",
  doesn't say which words are the link. No rule covers a link whose destination is the page the reader
  is on. Meanwhile the link's text is `People`, matching the header link to the same address, and
  "again" carries why it is offered.
- "There are no assignees yet. Tasks can be assigned only to names on this list." — § Message patterns,
  *Empty*, gives a formula whose second sentence names the next thing to do and its control, and then
  gives this People example, whose second sentence states a rule about the list instead. The standard
  doesn't say which governs. Meanwhile the example is used verbatim, because CP-84 requires its
  content.
