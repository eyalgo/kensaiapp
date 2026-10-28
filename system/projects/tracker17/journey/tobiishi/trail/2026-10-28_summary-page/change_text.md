# Change Text — a project's Summary view, counts as plain numbers

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing

---

## Text

Every string below is verbatim: place each one exactly as written, character for character. A part in
braces is a value. The line under the string says what the value is. All quotes are straight, and every
dash shown inside a page title is a plain hyphen with a space on each side.

### The Tasks and Summary links beneath a project's name

The same pair sits under the project's name on the Tasks view and on the Summary view. It appears in
every state of both views (CP-491).

**The link that opens the project's Tasks view**

> Tasks

When the person sees it: they are on a project, in either view. Opening it shows the project's task
list with no filter or sort chosen.

**The link that opens the project's Summary view**

> Summary

When the person sees it: they are on a project, in either view. Opening it shows the project's counts.

**The name of the pair, only where the pair is placed inside a navigation landmark of its own**

> Project views

When the person sees it: a screen reader announces it as the name of the navigation group that holds
the two links. It tells that group apart from the page header's navigation. Where the pair is not in a
landmark of its own, this string is not used.

### Both views' page titles

**The title of every page of the Tasks view**: the plain list, an empty project, a filtered or sorted
list, the page after an action, a refusal and a move confirmation

> {project name}: Tasks - tracker17

`{project name}` is the project's name exactly as saved, surrounding spaces included.

When the person sees it: in the browser tab and in the screen reader's page announcement. It tells
this project's task list apart from its summary and from every other page.

**The title of the Summary view**

> {project name}: Summary - tracker17

`{project name}` is the project's name exactly as saved, surrounding spaces included.

When the person sees it: in the browser tab and in the screen reader's page announcement, on the
project's Summary.

### The Summary's group headings and count labels

The Summary's heading is the project's name, as on the Tasks view. That heading is not new text. Under
it the counts come in four groups, in the order below. Each group has a heading, a two-column header
row and its rows. The first column holds the row labels and the second holds the counts. Every count is
a numeral, and a count of zero is `0`.

**Group 1, heading**

> Tasks by status

**Group 1, column headers**, first then second

> Status

> Tasks

**Group 1, row labels**, in this order

> Total

> todo

> in-progress

> done

> cancelled

When the person sees it: the total of the project's tasks comes first, then how many are in each
status. The four status rows add up to the total.

**Group 2, heading**

> Tasks by priority

**Group 2, column headers**, first then second

> Priority

> Tasks

**Group 2, row labels**, in this order

> low

> medium

> high

> critical

When the person sees it: how many of the project's tasks have each priority. The four rows add up to
the Total in group 1.

**Group 3, heading**

> Due dates

**Group 3, column headers**, first then second

> Due date

> Tasks

**Group 3, row labels**, in this order

> Overdue

> No due date

When the person sees it: how many tasks are past their due date and neither `done` nor `cancelled`,
then how many have no due date in any status. The two rows don't add up to anything, and nothing on
the page says they do.

**Group 4, heading**

> Open tasks by assignee

**Group 4, column headers**, first then second

> Assignee

> Open tasks

**Group 4, a row for a name**, one row per name, in the order CP-500 sets

> {assignee name}

`{assignee name}` is the name exactly as saved, with no quotes added. It covers each name on the
assignee list, and each name not on the list that an open task in this project still carries.

**Group 4, the last row**

> (unassigned)

When the person sees it: how many of the project's open tasks each person has, and, in the last row,
how many open tasks have no assignee. Tasks in `done` or `cancelled` are counted in no row of group 4.

### The Summary's first-task invitation and link

**A project with no tasks.** It shows beside the four groups, whose every count reads `0`. The word
`Tasks` in the sentence is the link, and it opens the same address as the `Tasks` link under the
project's name. It is one string, with the link set on that one word. It is not built from parts.

> This project has no tasks yet. Open Tasks to add the first task.

When the person sees it: they opened the Summary of a project that holds no tasks. Tasks are added on
the Tasks view, and the link takes them there.

### The timed run's Summary fixture and result lines

These two lines are printed by the timed run script after every line it prints today. The script
belongs to the product's own tests, and its existing lines are lowercase and use the same shape.

**The fixture line**, printed immediately before the result line

> summary fixture: {task count} tasks, {comments per task} comments each ({comment total} in all); title of {title length} characters, comment of {comment length} characters; project name of {project name length} characters

`{task count}` is the number of tasks in the loaded fixture. `{comments per task}` is the number of
comments each of them holds. `{comment total}` is the product of those two numbers. `{title length}`
is the length, in characters, of the title of the fixture's first task by task number.
`{comment length}` is the length, in characters, of that task's first comment.
`{project name length}` is the length, in characters, of the name of the project whose Summary is
timed. Every value is read from the loaded fixture, never written as a constant.

When the person sees it: a developer running the timed run reads which volume and which text lengths
the Summary was measured on.

**The result label**, which the run prints in its existing result-line form

> open a project summary at {task volume} tasks

`{task volume}` is the timed run's task volume, written as the run's other labels write it.

So a result line reads `open a project summary at {task volume} tasks: {milliseconds} ms`. Where the
measurement fails, the run's existing problem words follow it, as on every other line. This change
writes no new problem words.

When the person sees it: a developer reads how long opening the Summary took, and whether it passed.

---

## Wording decisions

- **The total is labelled `Total` and is the first row of group 1.** CP-496 puts the total first and
  leaves its label to the standard. `docs/DESIGN.md` § Layout ("Summary is a set of small two-column
  tables, Status, Priority, Due dates and Assignees") names four sheets and no place for the total.
  Putting the total at the head of the status group keeps it first and keeps four groups. The status
  rows add up to it, so a reader sees the total beside its parts. "Tasks" and "All tasks" were rejected
  as the label because both are already link labels on the same page, and "All tasks" names the
  cross-project list.
- **The group headings say what is counted: `Tasks by status`, `Tasks by priority`, `Due dates`,
  `Open tasks by assignee`.** DESIGN names the four sheets by subject only. A heading reading
  `Assignees` over group 4 would let the reader take its counts as all tasks. FR-38 counts only open
  tasks there, so the heading says "Open tasks". That is the one term `docs/CONTENT.md` § Terminology
  gives for a task neither `done` nor `cancelled`. The other headings follow the same pattern.
  `Due dates` keeps DESIGN's own name, because "Tasks by due date" would promise a breakdown that
  adds up to the total, and Overdue plus No due date doesn't.
- **Each group carries a column header row.** The product's task table already names its columns, and
  a count column with no header would leave a screen reader announcing a bare number. The count
  column says `Tasks` in groups 1 to 3 and `Open tasks` in group 4, for the same reason as the
  headings.
- **The row labels `Overdue` and `No due date`.** `Overdue` is the product's one word for that state,
  already used as the list marker and the filter (`docs/CONTENT.md` § Terminology). `No due date` uses
  the product's term "due date" and is sentence case.
- **Status and priority rows are the bare words, lowercase.** `docs/CONTENT.md` § Grammar and
  mechanics allows a string that is only a status or priority word, and names "a summary row label".
- **Assignee names in the rows carry no quotes.** The standard quotes a typed value "whenever it
  appears in a sentence". A table cell isn't a sentence, and the existing task table shows the assignee
  bare.
- **A listed name typed as `(unassigned)` gets no distinguishing word.** The spec keeps both rows
  (change_spec.md, Locked Answer b-5), and the real unassigned row is always last. Adding a word to
  either row would change how a name or the bucket is shown, which the spec does not ask for.
- **The first-task line is `This project has no tasks yet. Open Tasks to add the first task.`** Its
  first sentence is the Tasks view's own no-tasks sentence, word for word, so one fact has one
  wording across both views. The Tasks view's second sentence names the add form, which the Summary
  doesn't have. The second sentence here names the one thing to do and the link to do it with, by its
  label, as § Message patterns, Empty sets. It follows the corpus pattern on All tasks, "Open Projects
  to add a task to a project." The request said only "invites a first task".
- **The invitation's link text is `Tasks`, the same as the view link.** Both open the same address,
  and `docs/CONTENT.md` § Accessibility of text says "Links that share a label and open the same
  address share one name". A second wording for one destination would make two names for one place.
  "Open Tasks" sits close to the term "open tasks" in group 4's heading. That is accepted because the
  link marks `Tasks` as a destination, and "Open" is the product's fixed verb for a link.
- **`Project views` as the pair's group name, only for a navigation landmark.** The design leaves the
  pair's markup to the Developer. If it becomes a second navigation landmark, a screen reader would
  otherwise announce two unnamed navigation groups, and the Developer would have to pick a name. The
  string is written so that no word is chosen at placement. The project's name is left out, because
  the heading just before the pair already says it.
- **The page titles follow the standard's own examples.** `docs/CONTENT.md` § Accessibility of text
  gives "Alpha: Tasks - tracker17" and "Alpha: Summary - tracker17". The spec quotes the same form
  (CP-492). Nothing was changed.
- **The timed run's lines follow its existing lines, not the page standard.** `docs/CONTENT.md`
  § Scope governs no output of the timed run (RN-25). The fixture line copies the shape of the run's
  filter and sort fixture lines, semicolons included. It adds the project name's length, because the
  project name is the one typed text the Summary page shows, and the task titles and comments are
  not. The result label follows the run's verb-first labels, such as "filter a task list at
  {task volume} tasks". The design names one timed request, so there is one label and no landing or
  total label.
- **Banned-word check.** Every page string above was searched against the banned lexicon in
  `docs/CONTENT.md` § Terminology and its punctuation bans, in every inflection. Three strings matched,
  and each is permitted. `No due date` and "no tasks yet" match "No", which is banned only as a control
  label, and "This project has no tasks yet." is the standard's own Empty example. The fixture line's
  semicolons are in timed-run output, which § Scope leaves outside the standard (RN-25). The product
  carries no check that lints its vocabulary across strings, so none could be run.

---

## Findings for the Content Manager

- `Project views` — `docs/CONTENT.md` states no rule for the name of a group of controls or a
  navigation landmark, and the header's own navigation has none. The string was written in sentence
  case, naming what the group holds, by the rule for control labels and link text.
- `Total` as the first row of group 1 — `docs/CONTENT.md` names the total, overdue and no-due-date
  labels as its own to write (change_spec.md CP-496), but states none of them, and `docs/DESIGN.md`
  gives the total no sheet. The labels were written meanwhile from § Terminology and § Grammar and
  mechanics, Case.
