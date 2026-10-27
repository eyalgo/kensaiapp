# Change Text — a project's task list sorts by one field

**Date:** 2026-10-27
**Category:** feature
**Behaviour:** changing

---

## Text

### The project's task list

The project's Tasks page, on a project that has at least one task. The sort controls stand with the
filter's controls, after Overdue and before Apply and Clear. Apply and Clear keep the labels they
have today, and they apply and clear the sort along with the filter.

**The Sort by control's visible label**

> Sort by

When the person sees it: they are on the list with tasks and can pick the field the list is ordered by. No other control on the page has this label, so its accessible name is this label alone.

**The Sort by options, in this order**

> Due date

> Priority

> Created time

> Title

When the person sees them: they open Sort by and pick one. Due date is the one shown when the address carries no Sort by choice.

**The Direction control's visible label**

> Direction

When the person sees it: they are on the list with tasks and can pick which way the order runs. No other control on the page has this label, so its accessible name is this label alone.

**The Direction options, in this order**

> Ascending

> Descending

When the person sees them: they open Direction and pick one. Ascending is the one shown when the address carries no Direction choice.

**The count, when a sort is applied and no filter field is set, for one task**

> This project has 1 task.

When the person sees it: they applied a sort, with no filter, to a project with one task, and the list shows that task.

**The count, when a sort is applied and no filter field is set, for more than one task**

> This project has {count} tasks.

`{count}`: the number of tasks in the project, as a numeral, which is every task the list shows.

When the person sees it: they applied a sort, with no filter, and the list shows every task of the project in the order they picked.

**Sort by refused, because its value isn't one the control offers**

> Sort by can't be '{value}', because the list doesn't sort by that. Pick Due date, Priority, Created time or Title.

`{value}`: the Sort by value the address carried, exactly as it came.

When the person sees it: they opened an address whose Sort by value no option sends, and the list isn't shown. They can pick an option and press Apply.

**Sort by refused, because it was given more than one value**

> Sort by takes one value, not {count}. Pick Due date, Priority, Created time or Title.

`{count}`: the number of Sort by values the address carried, as a numeral, always 2 or more.

When the person sees it: they opened an address carrying Sort by more than once, and the list isn't shown. They can pick one option and press Apply.

**Direction refused, because its value isn't one the control offers**

> Direction can't be '{value}', because the list doesn't sort that way. Pick Ascending or Descending.

`{value}`: the Direction value the address carried, exactly as it came.

When the person sees it: they opened an address whose Direction value no option sends, and the list isn't shown. They can pick an option and press Apply.

**Direction refused, because it was given more than one value**

> Direction takes one value, not {count}. Pick Ascending or Descending.

`{count}`: the number of Direction values the address carried, as a numeral, always 2 or more.

When the person sees it: they opened an address carrying Direction more than once, and the list isn't shown. They can pick one option and press Apply.

### The timed run's sort lines

The four lines the timed run prints after its filter block, in this order and with nothing after them.
These are the change spec's CP-452 lines, copied verbatim. The product's `CONTENT.md` § Scope places
the output of a script a developer runs to measure the tracker outside the product's wording rules.

**The sort fixture line**

> sort fixture: {tasks} tasks, {per task} comments each ({all} in all); title of {T} characters, comment of {C} characters; sort priority descending, {N} listed

`{tasks}`, `{per task}` and `{all}`: the task count, the comments on each task and the comments in all, read from the fixture as loaded. `{T}` and `{C}`: the length in code points of the title, and of the first comment, of the first task the sorted list shows. `{N}`: the number of the fixture's tasks in the project.

When the person sees it: they ran the timed run and are reading which fixture the sort was timed on.

**The Apply timing row**

> sort a task list at 1000 tasks: {ms} ms{problems}

**The landing timing row**

> sort landing page at 1000 tasks: {ms} ms{problems}

**The total timing row**

> sort total at 1000 tasks: {ms} ms{problems}

`{ms}` and `{problems}`: written as every existing timing row writes them, the time in milliseconds to one decimal place, and the run's existing problem suffix, or nothing when the row has no problem.

When the person sees them: they ran the timed run and are reading how long the sort's Apply, its landing and their sum took, and whether any of them failed.

---

## Wording decisions

- The sort-only count reads "This project has {count} tasks." and not "{count} tasks match this filter." — CP-435 requires that the words not say a filter is applied, and `CONTENT.md` § Message patterns, Empty, says the no-tasks and no-match states are different facts. "This project has" is the present-tense state form `CONTENT.md` § Grammar and mechanics (Tense) sets, and it shares its frame with the product's own "This project has no tasks yet.", so the two lines about the whole project read as one family.
- The sort-only count has a written form for one and for the rest, and none for zero — `CONTENT.md` § Localization, "Plurals are written out", asks for a zero form only "where the text says no". This count never shows zero: a project with no tasks shows no sort controls (CP-426), and a sort over a filter that matches nothing keeps the filter's existing no-match sentence with no count (change design, Architect Review Notes, "Zero-match count reading").
- When a filter field is set, the count keeps the filter's existing words, with or without a sort — the change spec's Out of Scope keeps "its count's words when a filter field is set" as they are. No new string is written for that state.
- The four refusal reasons follow the shape of the filter's existing reasons ("The status filter can't be '{value}', because it isn't a status." and "The Overdue filter takes one value, not {count}.") — one form per refusal kind keeps a reader who has met one refusal on the page able to read the next. Each opens with the control's own label, as the product's "Due from takes one date, not {count}." already does, so a screen reader announcing it out of place says what it is about (`CONTENT.md` § Accessibility of text).
- The invalid-value reasons say "because the list doesn't sort by that" and "because the list doesn't sort that way", and not a reason the tracker didn't establish — the tracker knows only that no option sends the value. It doesn't know how the value reached the address, so no reason mentions a press, a link or a typing slip (`CONTENT.md` § Voice, "State only what the tracker established").
- Every refusal ends with one action naming the options by their labels, and no reload — the refused control shows the value as sent, and the person can pick an option and press Apply on the same page. The refusal is reached by an address rather than a press, as the filter's refusals are. The product's filter reasons already give an action for this case ("Pick a status, or pick Any status."), so the same form is used here. The `CONTENT.md` clause for a refusal reached without a press is about a task's status and doesn't reach a list choice.
- The sort refusals offer no "Any" option, unlike the filter's — the sort controls have no "any" choice. With nothing picked they show Due date and Ascending (CP-436), so naming an "Any" option would name a control that doesn't exist.
- "Created time" is kept as the option label, though the sort orders tasks by creation order and not by the recorded time (CP-432) — "created time" is the definition documents' term (FDR R-89, SRS FR-36). No page shows a task's recorded creation time, so the person has no visible time to find out of step with the order. "Creation order" would rename a defined field to describe its mechanism.
- "Title", "Due date" and "Priority" are the same words as the task list's column headers — one term per concept (`CONTENT.md` § Terminology), so an option names the column the list is ordered by.
- The timed run's four lines are copied from CP-452 unchanged — `CONTENT.md` § Scope (RN-25) leaves a measuring script's output outside the product's wording rules, and CP-452 fixes the lines exactly. The fixture line's semicolons and the problem suffix's dash follow the existing timed-run lines and break no product rule.
- Banned-word check: every string above was searched for each word and mark `CONTENT.md` § Terminology bans, in every inflection, and for its banned punctuation. Nothing was found in the tracker's own strings. The product carries no vocabulary check of its own to run. A search of its tests for a banned-word list found only checks on which modules may be imported.

---

## Findings for the Content Manager

None
