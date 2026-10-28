# Change Text — an All tasks list across every project, with the filter and sort controls

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing

---

## Text

Every string below is the whole text the person reads in that state. A string marked "as a project's
list shows it" is the same string, character for character, that a project's Tasks page shows today.
It is repeated here so the All tasks page can be placed from this file alone.

### The shared header

The header every page with a header shows, after the product name. The page for saved data that
can't be read still has no header.

**The three links, in this order**

> Projects

> All tasks

> People

When the person sees them: they are on any page with a header. Projects and People open the pages
they open today. All tasks opens the All tasks page. Each link's accessible name is its visible text
alone.

### Both not-found pages

The page for an address with no project at it, and the page for an address shaped like a task's with
no task at it. The page title stays "Not found - tracker17" and the heading of each stays as it is
today.

**The heading, no project at this address** (unchanged)

> There's no project at this address

**The heading, no task at this address** (unchanged)

> There's no task at this address

**The one paragraph after the heading, on both pages**

> Open Projects or All tasks.

"Projects" is a link to the Projects page and "All tasks" is a link to the All tasks page. The rest of
the sentence is plain text.

When the person sees it: they opened an address with nothing at it. They can open one of the two lists
the tracker has.

### All tasks: the heading

**The page title**

> All tasks - tracker17

**The page's one heading**

> All tasks

When the person sees them: they opened All tasks, from the header, a not-found page or a saved
address. The title and the heading are the same in every state of the page.

### All tasks: the task table

The table of tasks, shown when at least one task exists and the choices are not refused and match at
least one task.

**The column headers, in this order**

> Title

> Project

> Status

> Priority

> Assignee

> Labels

> Due date

> Moves

When the person sees them: they are reading the list. Project stands directly after Title.

**The Title cell**

> {title}

`{title}`: the task's title, as typed, as a link to the task's page. The link's accessible name is:

> {title}, number {position} on the task list

`{position}`: the row's place in the list as shown, as a numeral, counting from 1. This is the name a
project's list gives its title links.

**The Project cell**

> {project name}

`{project name}`: the name of the task's project, as typed, as a link to that project's page with no
filter or sort choice in its address. The link's accessible name is its visible text alone.

When the person sees it: they want to know, or open, the project a task belongs to.

**The Status, Priority, Assignee, Labels and Due date cells**, as a project's list shows them:

- Status: the task's status word, written as defined (`todo`, `in-progress`, `done`, `cancelled`).
- Priority: the task's priority word, written as defined (`low`, `medium`, `high`, `critical`).
- Assignee: the assignee's name as typed, or, for a task with none:

> unassigned

- Labels: the task's labels as typed, in the order the task carries them, each separated from the next
  by a comma and a space, or, for a task with none:

> none

- Due date: the date as `YYYY-MM-DD`, or, for a task with none:

> none

  and, after the date, when the task is overdue:

> Overdue

**The Moves cell**, as a project's list shows it: one button per move the task's status allows, in
the order the row offers them. Each button's visible label is the status the move goes to, written as
defined. Each button's accessible name is:

> Move '{title}' to {status}

`{title}`: the task's title. `{status}`: the status the button moves the task to.

**The in-place confirmation of a move to cancelled**, in the row, as a project's list shows it

> Move '{title}' to cancelled? A cancelled task can't be moved again.

The confirming control:

> Move to cancelled

The back-out control:

> Back out

When the person sees it: they pressed `cancelled` on a row. They can confirm the move or back out of
it, and either lands on All tasks with their choices kept.

### All tasks: the empty state

**No project holds a task: there is no project, or every project has no tasks**

> There are no tasks yet. Open Projects to add a task to a project.

"Projects" is a link to the Projects page. The rest of the sentence is plain text.

When the person sees it: they opened All tasks and the tracker has no task in any project. The page
shows this paragraph under the heading and nothing else, whatever choices the address carries. They can
open Projects, open or create a project there, and add its first task.

### All tasks: the controls

Shown above the list whenever at least one task exists, as a project's list shows them, in this order.
Applying a choice shows no message.

**The field labels, in this order**

> Status

> Priority

> Assignee

> Label

> Due from

> Due to

> Overdue

> Sort by

> Direction

**The accessible names of the Priority and Assignee fields**

> Priority filter

> Assignee filter

The other seven controls' accessible names are their visible labels alone.

**The no-value choice, first in each of the four lists**

> Any status

> Any priority

> Any assignee

> Any label

**The other choices in the four filter lists**

- Status: the four status words, as defined, in the order a project's list offers them.
- Priority: the four priority words, as defined, in the order a project's list offers them.
- Assignee: the names on the assignee list, as typed, in the list's order.
- Label: each distinct label any task of any project carries, as typed, once, in code-point order.

**The Sort by choices, in this order**

> Due date

> Priority

> Created time

> Title

**The Direction choices, in this order**

> Ascending

> Descending

**The two controls after the fields**

> Apply

> Clear

When the person sees them: there is at least one task in the tracker. They can pick choices and press
Apply, or press Clear to see every task in the default order.

### All tasks: the count

Shown above the table when the address carries a filter field or a sort choice and at least one task
is listed.

**At least one filter field is set, and 1 task matches** (as a project's list shows it)

> 1 task matches this filter.

**At least one filter field is set, and 2 or more tasks match** (as a project's list shows it)

> {count} tasks match this filter.

`{count}`: the number of tasks listed, as a numeral.

When the person sees it: they applied a filter, with or without a sort, and the list shows the tasks
that match it from every project.

**A sort is chosen and no filter field is set, and the tracker has 1 task**

> The tracker has 1 task.

**A sort is chosen and no filter field is set, and the tracker has 2 or more tasks**

> The tracker has {count} tasks.

`{count}`: the number of tasks in every project together, as a numeral, which is every task the list
shows.

When the person sees it: they applied a sort with no filter, and the list shows every task of every
project in the order they picked.

**At least one task exists, a filter field is set, and none matches** (as a project's list shows it)

> No tasks match this filter. Press Clear to see every task.

When the person sees it: they applied a filter that matches no task in any project. The controls still
show their choices, Clear is in view, and no table and no count are shown.

### All tasks: the refusals

Each reason stands beside the field it is about, as a project's list shows it. No list and no count are
shown while a choice is refused. `{value}` is the value the address carried for that field, exactly as
it came. `{count}` is the number of values the address carried for that field, as a numeral, always 2
or more.

**Due from is later than Due to** (shown at Due from)

> The Due from date, {due from}, is later than the Due to date, {due to}. Change one so Due from is the earlier date.

`{due from}` and `{due to}`: the two dates, as `YYYY-MM-DD`.

**The assignee is not on the assignee list, and the list holds at least one name** (shown at Assignee)

> The name '{name}' isn't on the assignee list. Pick a name on the list, or pick Any assignee.

`{name}`: the name the address carried, exactly as it came.

**The assignee is not on the assignee list, and the list holds no names** (shown at Assignee)

> The name '{name}' isn't on the assignee list. Pick Any assignee.

**Status is not one of the four statuses** (shown at Status)

> The status filter can't be '{value}', because it isn't a status. Pick a status, or pick Any status.

**Priority is not one of the four priorities** (shown at Priority)

> The priority filter can't be '{value}', because it isn't a priority. Pick a priority, or pick Any priority.

**Due from is not a calendar date** (shown at Due from)

> The Due from date can't be '{value}', because it isn't a calendar date. Give a calendar date, or leave Due from empty.

**Due to is not a calendar date** (shown at Due to)

> The Due to date can't be '{value}', because it isn't a calendar date. Give a calendar date, or leave Due to empty.

**Overdue carries a value other than on** (shown at Overdue)

> The Overdue filter can't be '{value}', because it's either on or off. Turn Overdue on, or leave it off.

**Status carries more than one value** (shown at Status)

> The status filter takes one status, not {count}. Pick one status, or pick Any status.

**Priority carries more than one value** (shown at Priority)

> The priority filter takes one priority, not {count}. Pick one priority, or pick Any priority.

**Assignee carries more than one value, and the assignee list holds at least one name** (shown at
Assignee)

> The assignee filter takes one name, not {count}. Pick one name on the list, or pick Any assignee.

**Assignee carries more than one value, and the assignee list holds no names** (shown at Assignee)

> The assignee filter takes one name, not {count}. Pick Any assignee.

**Label carries more than one value, and at least one task of any project carries a label** (shown at
Label)

> The label filter takes one label, not {count}. Pick one label, or pick Any label.

**Label carries more than one value, and no task of any project carries a label** (shown at Label)

> The label filter takes one label, not {count}. Pick Any label.

**Due from carries more than one value** (shown at Due from)

> Due from takes one date, not {count}. Give one calendar date, or leave Due from empty.

**Due to carries more than one value** (shown at Due to)

> Due to takes one date, not {count}. Give one calendar date, or leave Due to empty.

**Overdue carries more than one value** (shown at Overdue)

> The Overdue filter takes one value, not {count}. Turn Overdue on, or leave it off.

**Sort by is not one of its choices** (shown at Sort by)

> Sort by can't be '{value}', because the list doesn't sort by that. Pick Due date, Priority, Created time or Title.

**Sort by carries more than one value** (shown at Sort by)

> Sort by takes one value, not {count}. Pick Due date, Priority, Created time or Title.

**Direction is not one of its choices** (shown at Direction)

> Direction can't be '{value}', because the list doesn't sort that way. Pick Ascending or Descending.

**Direction carries more than one value** (shown at Direction)

> Direction takes one value, not {count}. Pick Ascending or Descending.

When the person sees them: they opened an All tasks address whose choices the list refuses, by a
reload, a bookmark or a move pressed on such a list. Focus is on the first refused field. They can fix
the field and press Apply, or press Clear.

### All tasks: the move outcomes

A move pressed on an All tasks row always lands on All tasks with the same choices. `{title}` is the
task's title and `{status}` is its status now, both as the saved data holds them when the page is
built. `{first move}`, `{second move}` and `{third move}` are the moves its status allows, each a
status word, in the order the row offers them.

#### In the task's row, when the task is listed

Each line stands beside the task's status in its row.

**The move was saved** (as a project's list shows it)

> You moved '{title}' to {status}.

**The move failed and nothing was saved** (as a project's list shows it; `{status}` is the status the
move was to)

> The tracker couldn't move '{title}' to {status}, and nothing was changed. Try again.

**The move was refused because the task's status no longer allows it, and that status allows no move**

> The status of '{title}' is {status}. A task in {status} can't be moved.

**The same refusal, and the status allows one move**

> The status of '{title}' is {status}. A task in {status} can be moved to {first move}.

**The same refusal, and the status allows two moves**

> The status of '{title}' is {status}. A task in {status} can be moved to {first move} or {second move}.

**The same refusal, and the status allows three moves**

> The status of '{title}' is {status}. A task in {status} can be moved to {first move}, {second move} or {third move}.

When the person sees these four: they pressed a move the task's current status doesn't allow, or
reloaded that landing. The row shows the status and the moves it allows.

**The address asks to open, or back out of, the confirmation of a move to cancelled, and the task is
in a final status** (as a project's list shows it)

> The status of '{title}' is {status}, which doesn't allow a move to cancelled. A task in {status} can't be moved.

When the person sees it: they reopened a confirmation or back-out address, by a reload, Back or a saved
address, after the task reached `done` or `cancelled`.

#### Above the list, when the task is not listed

Each line stands above the list, or above the no-match sentence when no task is left matching, and
describes the list section, which takes the focus.

**A move took the task out of the list** (as a project's list shows it; one completion line)

> You moved '{title}' to {status}, and it no longer matches this filter, so it has left this list.

When the person sees it: they moved a task out of the status they filter by, or to `done` or
`cancelled` under Overdue. The task was saved in its new status and isn't listed.

**A move failed, and the task is not in the list** (as a project's list shows it; `{status}` is the
status the move was to)

> The tracker couldn't move '{title}' to {status}, and nothing was changed. The task doesn't match this filter, so press Clear to see it.

**A move was refused, the task is not in the list, and its status allows no move** (as a project's
list shows it)

> The status of '{title}' is {status}, and a task in {status} can't be moved. The task doesn't match this filter, so it isn't in this list.

**A move was refused, the task is not in the list, and its status allows one move** (as a project's
list shows it)

> The status of '{title}' is {status}, and a task in {status} can be moved to {first move}. The task doesn't match this filter, so press Clear to see it.

**A move was refused, the task is not in the list, and its status allows two moves** (as a project's
list shows it)

> The status of '{title}' is {status}, and a task in {status} can be moved to {first move} or {second move}. The task doesn't match this filter, so press Clear to see it.

**A move was refused, the task is not in the list, and its status allows three moves** (as a
project's list shows it)

> The status of '{title}' is {status}, and a task in {status} can be moved to {first move}, {second move} or {third move}. The task doesn't match this filter, so press Clear to see it.

**The address asks to open, or back out of, the confirmation of a move to cancelled, the task is in a
final status, and the task is not in the list** (as a project's list shows it)

> The status of '{title}' is {status}, which doesn't allow a move to cancelled. The task doesn't match this filter, so it isn't in this list.

When the person sees these: the task their move or address is about doesn't match the choices, so the
list doesn't show it. The line tells them where the task stands and, where a move is left, how to see
it.

---

## Wording decisions

- The in-row refusal for a move the task's status no longer allows reads "The status of '{title}' is {status}." on All tasks, not the "has changed to" a project's list shows today — `CONTENT.md` § Message patterns, Error, says this refusal "states the task's current status and the moves that status allows" and "claims no change", and its two examples are these strings. The page is built after the refusal, so "has changed to" claims an event the tracker can't establish, and a reload shows the same line with no press (`CONTENT.md` RN-26, RN-27). The same task's line above the list already says "is", so on All tasks the two forms of the refusal now agree. A project's list keeps "has changed to": the change spec's Out of Scope keeps "a project's list, its controls and its move landings" as they are, and CP-487 changes no other existing test, while the product's existing move tests pin that wording. That line stays the standing finding `CONTENT.md` RN-26 and RN-27 record, for a later change that publishes text on a project's list.
- The sort-only count reads "The tracker has {count} tasks." — CP-470 says that number is every task of every project and that its words don't say a filter is applied. A project's list says "This project has {count} tasks.", which would be false here. "The tracker" is the product's own term for itself (`CONTENT.md` § Terminology, "The running product"), and the present-tense state form matches § Grammar and mechanics (Tense). It has a form for one and for the rest and none for zero, because the page never shows a count with no task listed: no task anywhere gives the empty state, and a filter matching nothing gives the no-match sentence (`CONTENT.md` § Localization, "Plurals are written out").
- The empty state reads "There are no tasks yet. Open Projects to add a task to a project." — CP-466 asks that it say there are no tasks yet, link to Projects and never mention a filter. Its first sentence follows the product's "There are no projects yet.", and its second names the one thing to do and the control by its label (`CONTENT.md` § Message patterns, Empty). It says where a task is added and not how, so the one sentence holds whether there is no project at all or only empty ones. It says "Open", because a link is opened (`CONTENT.md` § Grammar and mechanics, Verbs for pressing).
- The not-found paragraph is "Open Projects or All tasks." on both pages — `CONTENT.md` § Message patterns, Error, "An address with nothing at it", gives this exact two-place form for both, and CP-460 quotes it. The heading of each page is unchanged.
- The header's All tasks link and the not-found page's All tasks link share their text and both open the All tasks page, so they share one accessible name with no added words — `CONTENT.md` § Accessibility of text, "Links that share a label and open the same address share one name" (RN-20). The empty state's Projects link and the header's Projects link are the same case.
- The project column's header is "Project", in the singular like "Assignee", and it is the word the task's own page already uses for the same fact. The cell's link text is the project's name alone, because link text names the destination (`CONTENT.md` § Accessibility of text). Project names are unique, and every link to one project opens the same address, so repeated project links share one name.
- The controls, choices, accessible names, count with a filter, no-match sentence, refusals, confirmation and every other move line are the project list's own strings, unchanged — CP-467, CP-470, CP-471, CP-474 and CP-475 make each of those states the same as a project's list, and one string for one concept keeps a reader who has used one list able to read the other. Each was read for words that are only true of one project. None was found: "this filter", "the list", "every task" and "this list" all read true across every project. "Priority filter" and "Assignee filter" are kept on All tasks, though it has no add-task form, so the same control has the same name on both lists.
- The second forms of the repeated-assignee and repeated-label refusals keep their conditions with the scope widened: the label one is chosen when no task of any project carries a label, following CP-468's label choices.
- The title link's accessible name keeps ", number {position} on the task list" — two tasks in different projects may share a title, and the position is what tells their links apart.
- Banned-word check: every string above was searched for each word `CONTENT.md` § Terminology bans, in every inflection, and for its banned punctuation (exclamation mark, em dash, semicolon, ellipsis, and a colon outside a page title). Nothing was found in the tracker's own strings. "Left" in "has left this list" is the verb of leaving, not the position word the ban is about, and the string is `CONTENT.md`'s own completion example's ending. `cancelled` is the status word and not the banned control word. The product carries no vocabulary check of its own to run. A search of its tests for a banned-word list found only checks on which modules may be imported.

---

## Findings for the Content Manager

- "Move '{title}' to {status}", the move button's accessible name, and the confirmation sentence "Move '{title}' to cancelled? A cancelled task can't be moved again." — `CONTENT.md` § Accessibility of text says that where a visible label repeats, the accessible name adds "the thing the control acts on", and names a task by its title. It doesn't say what tells two tasks apart when they share a title. A project's list already allows that, and All tasks makes it more likely, since every project can hold a task with the same title, such as 'Set up CI'. Meanwhile the strings are written as a project's list writes them, naming the task by its title alone.
