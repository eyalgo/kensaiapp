# Change Text — a project's task list narrows by filter

**Date:** 2026-10-27
**Category:** feature
**Behaviour:** changing

---

## Text

Every string below is shown on a project's Tasks view, the page that lists one project's tasks, and
only while that project has at least one task. A project with no tasks shows its page as today, with
none of these words.

Placeholders, in every string where they appear:

- `{title}` is a task's title as saved, written exactly as typed. The quotes around it belong to the
  string.
- `{status}` is one status word, `todo`, `in-progress`, `done` or `cancelled`. Where `{status}`
  appears twice in one string, it is the same status both times.
- `{first move}`, `{second move}` and `{third move}` are the moves the task's status allows, each one
  status word, in the order the product already lists a task's moves.
- `{count}` is a whole number, written as numerals.
- `{value}` is the one value the address carried for that field, written exactly as it came, whole.
  The quotes around it belong to the string.
- `{name}` is the assignee name the address carried, written exactly as it came. The quotes around it
  belong to the string.
- `{due from}` and `{due to}` are the two dates the reader gave, each written `YYYY-MM-DD` by the
  product's one date formatter.

### The filter controls and their choices

**The field labels, always shown, in this order**

> Status

> Priority

> Assignee

> Label

> Due from

> Due to

> Overdue

When the person sees it: on every project page that lists tasks, each label above its own field.

**The accessible names of the two fields whose label the add-task form also uses**

> Priority filter

> Assignee filter

When the person sees it: a screen reader announces these for the filter's Priority and Assignee
fields, so they are told apart from the add-task form's Priority and Assignee fields. The other five
fields' accessible names are their labels, as written above.

**The two controls after the fields**

> Apply

> Clear

When the person sees it: Apply narrows the list to the choices in the fields, and Clear returns to
every task with every field at no value. Each control's accessible name is its label.

**The no-value choice, the first choice in each of the four lists**

> Any status

> Any priority

> Any assignee

> Any label

When the person sees it: in the Status, Priority, Assignee and Label lists, as the choice that
narrows nothing. It is the one shown when no value is set for that field.

**The other choices in each list**

- Status: `todo`, `in-progress`, `done`, `cancelled`, each written exactly as shown, in that order.
- Priority: `low`, `medium`, `high`, `critical`, each written exactly as shown, in that order.
- Assignee: each name on the assignee list, written exactly as typed, with no quotes and no other
  words.
- Label: each label the project's tasks carry, written exactly as typed, with no quotes and no other
  words.
- A value the address carried that is not among these, such as a label no task carries or a name no
  longer on the list, is shown as the selected choice exactly as it came, with no quotes and no other
  words.

Due from and Due to are the browser's own date fields, and Overdue is on or off. None of the three
has choices with words of the tracker's own.

### The match count

**At least one field is set, and 1 task matches**

> 1 task matches this filter.

When the person sees it: after Apply, or on a reload, Back or bookmark of a filtered list, with
the one matching task listed.

**At least one field is set, and 2 or more tasks match**

> {count} tasks match this filter.

When the person sees it: in the same moments, with those tasks listed. `{count}` is 2 or more.

When no task matches, there is no count string. The no-match state's first sentence says it. When no
field is set, no count is shown.

### The no-match state

**At least one field is set, the project has tasks, and none of them matches**

> No tasks match this filter. Press Clear to see every task.

When the person sees it: in place of the task list, with the fields still showing their choices and
Clear in view. They can change a choice and press Apply again, or press Clear.

### The field refusals

Each reason sits at the field it names. The page shows no task list, no count and no no-match line
while a reason shows. Clear is in view. Several fields can be refused at once, and each shows its own
reason.

**Due from is later than Due to** (shown at Due from)

> The Due from date, {due from}, is later than the Due to date, {due to}. Change one so Due from is the earlier date.

When the person sees it: they pressed Apply with a date range the wrong way round. Both dates are
still in their fields.

**The assignee is not on the assignee list, and the list holds at least one name** (shown at
Assignee)

> The name '{name}' isn't on the assignee list. Pick a name on the list, or pick Any assignee.

When the person sees it: the name was removed from the list after the page loaded, or was typed into
the address. The Assignee field now offers only the names on the list.

**The assignee is not on the assignee list, and the list holds no names** (shown at Assignee)

> The name '{name}' isn't on the assignee list. Pick Any assignee.

When the person sees it: as above, but the Assignee field offers only Any assignee.

**Status is not one of the four statuses** (shown at Status)

> The status filter can't be '{value}', because it isn't a status. Pick a status, or pick Any status.

When the person sees it: the address carried a status value no choice offers.

**Priority is not one of the four priorities** (shown at Priority)

> The priority filter can't be '{value}', because it isn't a priority. Pick a priority, or pick Any priority.

When the person sees it: the address carried a priority value no choice offers.

**Due from is not a calendar date** (shown at Due from)

> The Due from date can't be '{value}', because it isn't a calendar date. Give a calendar date, or leave Due from empty.

When the person sees it: the address carried a Due from value that is no date on the calendar, such
as 2026-02-30.

**Due to is not a calendar date** (shown at Due to)

> The Due to date can't be '{value}', because it isn't a calendar date. Give a calendar date, or leave Due to empty.

When the person sees it: the same, for Due to.

**Overdue carries a value other than on** (shown at Overdue)

> The Overdue filter can't be '{value}', because it's either on or off. Turn Overdue on, or leave it off.

When the person sees it: the address carried an Overdue value that the Overdue field never sends.

**Status carries more than one value** (shown at Status)

> The status filter takes one status, not {count}. Pick one status, or pick Any status.

When the person sees it: the address carried the field more than once. `{count}` is 2 or more, so
the string has no form for one.

**Priority carries more than one value** (shown at Priority)

> The priority filter takes one priority, not {count}. Pick one priority, or pick Any priority.

When the person sees it: the same, for Priority.

**Assignee carries more than one value, and the assignee list holds at least one name** (shown at
Assignee)

> The assignee filter takes one name, not {count}. Pick one name on the list, or pick Any assignee.

When the person sees it: the same, for Assignee.

**Assignee carries more than one value, and the assignee list holds no names** (shown at Assignee)

> The assignee filter takes one name, not {count}. Pick Any assignee.

When the person sees it: the same, where the Assignee field offers only Any assignee.

**Label carries more than one value, and the project's tasks carry at least one label** (shown at
Label)

> The label filter takes one label, not {count}. Pick one label, or pick Any label.

When the person sees it: the same, for Label.

**Label carries more than one value, and the project's tasks carry no labels** (shown at Label)

> The label filter takes one label, not {count}. Pick Any label.

When the person sees it: the same, where the Label field offers only Any label.

**Due from carries more than one value** (shown at Due from)

> Due from takes one date, not {count}. Give one calendar date, or leave Due from empty.

When the person sees it: the same, for Due from.

**Due to carries more than one value** (shown at Due to)

> Due to takes one date, not {count}. Give one calendar date, or leave Due to empty.

When the person sees it: the same, for Due to.

**Overdue carries more than one value** (shown at Overdue)

> The Overdue filter takes one value, not {count}. Turn Overdue on, or leave it off.

When the person sees it: the same, for Overdue.

Where a field carried more than one value, each value it carried is still shown in that field's
area, each exactly as it came. The tracker adds no words, quotes or punctuation around or between
them.

### The move lines above a filtered list

These lines are shown only on a filtered list, and only when the task the line is about is not in
the list the page shows. A line about a task still in the list stays in its row, worded as today.

**A move took the task out of the list** (one completion line)

> You moved '{title}' to {status}, and it no longer matches this filter, so it has left this list.

When the person sees it: they pressed a move, or confirmed a move to `cancelled`, in a row of the
filtered list. The move was saved, and the task no longer shows. If no task is left matching, the
no-match state follows this line.

**A move failed, and the task is not in the list** (`{status}` is the status the move was to)

> The tracker couldn't move '{title}' to {status}, and nothing was changed. The task doesn't match this filter, so press Clear to see it.

When the person sees it: they pressed a move in a row, nothing was saved, and the task the line names
is not in this list. Clear shows every task, this one included.

**A move was refused, the task is not in the list, and its status allows no move** (its status is
`done` or `cancelled`)

> The status of '{title}' is {status}, and a task in {status} can't be moved. The task doesn't match this filter, so it isn't in this list.

When the person sees it: they pressed a move on a row loaded before the task's status changed.
Nothing was saved, and there is nothing to do with the task.

**A move was refused, the task is not in the list, and its status allows one move**

> The status of '{title}' is {status}, and a task in {status} can be moved to {first move}. The task doesn't match this filter, so press Clear to see it.

When the person sees it: they pressed a move on a row loaded before the task's status changed.
Nothing was saved, and Clear shows the task with the move named in the line.

**A move was refused, the task is not in the list, and its status allows two moves** (today, a task
in `todo`)

> The status of '{title}' is {status}, and a task in {status} can be moved to {first move} or {second move}. The task doesn't match this filter, so press Clear to see it.

When the person sees it: the same, with the two moves named in the line.

**A move was refused, the task is not in the list, and its status allows three moves** (today, a task
in `in-progress`)

> The status of '{title}' is {status}, and a task in {status} can be moved to {first move}, {second move} or {third move}. The task doesn't match this filter, so press Clear to see it.

When the person sees it: the same, with the three moves named in the line.

**The address asks to open, or back out of, the confirmation of a move to `cancelled`, and the task
is not in the list** (its status is `done` or `cancelled`)

> The status of '{title}' is {status}, which doesn't allow a move to cancelled. The task doesn't match this filter, so it isn't in this list.

When the person sees it: they opened an address by a reload, Back or a bookmark, with no press. No
confirmation shows, and there is nothing to do with the task.

Filled in for the spec's Examples, as the person reads them:

- List filtered by Status `todo`, `in-progress` pressed on `Set up CI`: "You moved 'Set up CI' to in-progress, and it no longer matches this filter, so it has left this list."
- Overdue on, an overdue task `Ship docs` moved to `done`: "You moved 'Ship docs' to done, and it no longer matches this filter, so it has left this list."
- Three tasks match: "3 tasks match this filter."
- Label `Bug` where tasks carry only `bug`: "No tasks match this filter. Press Clear to see every task."
- Due from 2026-10-10, Due to 2026-10-01: "The Due from date, 2026-10-10, is later than the Due to date, 2026-10-01. Change one so Due from is the earlier date."
- `carol` removed from a list that still holds `dana`: "The name 'carol' isn't on the assignee list. Pick a name on the list, or pick Any assignee."
- Address carries Status `blocked`: "The status filter can't be 'blocked', because it isn't a status. Pick a status, or pick Any status."
- Address carries Status twice: "The status filter takes one status, not 2. Pick one status, or pick Any status."
- Address carries Due to `2026-02-30`: "The Due to date can't be '2026-02-30', because it isn't a calendar date. Give a calendar date, or leave Due to empty."

---

## Wording decisions

- The completion line says "no longer matches this filter" where `CONTENT.md` § Completed's example
  says "the status filter" — the design has the page learn only that the task is no longer among the
  matches, never which field it fails (`change_design.md` § 3 C, "Membership comes from B's selected
  identities"). With Status and Overdue both set, a move to `done` fails both. "This filter" names the
  whole set of choices, as § Empty's "No tasks match this filter." does, and stays true in every case.
  One string therefore serves the status case and the Overdue case of CP-408.
- The completion line joins the move and the consequence with "and" rather than the example's "so" —
  the tracker cannot establish that the move alone took the task out. A label or assignee edit saved on
  the task's page after this page loaded would also leave it off the list. "No longer matches" is still
  true, because the task was in the list the reader pressed from.
- A zero match count has no string of its own. "0 tasks match" beside "No tasks match this filter."
  would be two strings for one fact, and `CONTENT.md` § Grammar and mechanics writes a zero count as
  "no" inside a sentence. The no-match state's first sentence carries the zero.
- The match count is a full sentence, "{count} tasks match this filter.", rather than a bare number.
  `CONTENT.md` § Voice's second fallback prefers a complete plain sentence. Its wording matches the
  no-match sentence, so the two read as one family. It gives no "of {total}", because the request asks
  for the number of matches only.
- The no-match state is § Empty's own example, word for word.
- The reversed-range refusal is § Error's own example, with the two dates as placeholders. It meets
  FR-34's "the dates are the wrong way round" without the banned "wrong".
- The unlisted-assignee reason says "isn't on the assignee list" rather than the product's existing
  "is no longer on the assignee list". A name typed into the address may never have been on the list,
  and "no longer" would claim a past the tracker did not establish. It has two forms, because "Pick a
  name on the list" offers a choice that does not exist when the list holds no names. The same split
  holds for the repeated-value reasons for Assignee and Label.
- Every refusal for a value no control sends quotes the value, as § Error, *A refusal*, requires
  ("quoting any typed value"). That also meets the design's requirement that a value that was refused
  stays visible at its field.
- The date refusals name the outcome, "Give a calendar date", and never a way to pick or type one, as
  § Grammar and mechanics (Dates and times) requires. The existing add-task line "Pick one, or leave
  the due date empty." breaks that rule (RN-23), and is not copied.
- The repeated-value reasons give the count, "not {count}", and do not list the values in the
  sentence. The number of values has no limit, and § Localization does not allow a sentence built from
  a list joined at runtime. The values stay visible in the field's area, with no words around them.
- Field names in sentences: "the status filter", "the priority filter", "the assignee filter" and
  "the label filter" use the lowercase term, as § Completed's example "the status filter" does.
  "The Overdue filter" is capitalised, because § Terminology writes this term as "Overdue" and calls
  the filter "the filter 'Overdue'". "The Due from date" and "The Due to date" follow § Error's own
  example. "Due from takes one date" opens with the field name to keep the sentence short. It names
  the field the reason sits at.
- The filter's Priority and Assignee fields get the accessible names "Priority filter" and "Assignee
  filter". The add-task form on the same page already has fields labelled Priority and Assignee, and
  § Accessibility of text requires a repeated label's accessible name to add what the control acts on.
  Each name begins with its visible label, so Label in Name holds. The other five keep their labels as
  their names, since none repeats on the page.
- The no-value choice reads "Any status", "Any priority", "Any assignee" and "Any label". A blank
  choice gives a screen reader nothing to announce. "None" or "unassigned" would claim a filter for
  tasks with no value, which UXD UX-F6 says no field expresses. "Any …" is the smaller true thing.
  It narrows nothing.
- The off-list refusal lines follow `CONTENT.md` version 15's clause for a move another change
  overtook. They state the status and the moves it allows, and claim no change. The status and its
  moves share one sentence, so the second sentence can say why the task isn't shown and still keep
  the refusal to two sentences. Where a move is left, that second sentence also gives the one action,
  Clear. For a final status it says what the page shows instead, as the formula asks. The in-row lines
  that still say "has changed to" are outside this change's places. The finding about them is already
  recorded in `CONTENT.md` RN-26 and RN-27.
- The off-list failure line drops the in-row line's "Try again." The task's row and its move buttons
  are not on this page, so the reader can't try again from it. The action given is Clear, which shows
  the task. The line says "The task", not "It", because "It" could be read as "the tracker" from the
  sentence before.
- Each list of moves is a whole string per count of moves, as the earlier change that wrote the
  in-row lines did. Each placeholder holds one status word.
- Banned-word check: every string was searched for each word in § Terminology's banned table and for
  the banned punctuation in § Grammar and mechanics, in every inflection. Nothing was found. The
  strings contain no relative time word, no "cannot" or "do not", no colon, semicolon, dash,
  parenthesis or exclamation mark, and no sentence over 20 words besides a quoted value. "Change one so
  Due from is the earlier date" is § Error's own example. The ban on "change" covers moving a task
  only. The product has no word-list check to run: its architecture tests check imports, not words.

---

## Findings for the Content Manager

- "Any status", "Any priority", "Any assignee", "Any label" — `CONTENT.md` states no wording for a
  filter field's no-value choice, and the All tasks list will need the same one. Written meanwhile as
  "Any" and the field's own term.
- "Turn Overdue on, or leave it off." — § Grammar and mechanics (Verbs for pressing) gives verbs for a
  button, a link, an option and typed text, and none for a checkbox. Written meanwhile as "turn on"
  and "leave off".
- "No tasks match this filter. Press Clear to see every task." and the other lines that say "press
  Clear" — the design makes Clear a link styled as a secondary button (`change_design.md` § 3 C;
  `DESIGN.md` § Components). § Verbs says a link is "opened", but § Empty's own example says "Press
  Clear". The standard doesn't say which verb a control takes when it looks like one thing and is
  another. Written meanwhile as "press", as the example has it.
- The repeated-value reasons — § Localization doesn't allow a list joined at runtime, and nothing says
  how to write back a set of typed values of any length. Written meanwhile as a count in the reason,
  with the values shown as they came in the field's area and no words of the tracker's own.
- "You moved '{title}' to {status}, and it no longer matches this filter, so it has left this list."
  — § Completed's example names "the status filter". Read as a pattern, it suggests the line names the
  field the task fails. A list filtered by several fields can't always name one, and the tracker as
  designed doesn't establish which. Written meanwhile as "this filter", with "and" in place of the
  causal "so".
