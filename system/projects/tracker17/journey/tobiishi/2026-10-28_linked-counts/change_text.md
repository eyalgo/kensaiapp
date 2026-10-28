# Change Text — a project's Summary counts as links into its filtered task list

**Date:** 2026-10-28
**Category:** feature
**Behaviour:** changing

---

## Text

### The accessible names of the nine linked counts on a project's Summary

Each name below is what a screen reader announces for one count link. The link's visible text stays
the numeral alone. Every name has two forms: one for a count of 1, and one for every other count, 0
included. `{count}` is the numeral the link shows, written as digits exactly as the cell shows it
(`0`, `2`, `12`). Each string is whole, with no punctuation at its end.

**The todo count, when it is 1**

> 1 task in todo

When the person sees it: they hear what the number counts. Opening the link shows this project's tasks in `todo`.

**The todo count, at any other value, 0 included**

> {count} tasks in todo

When the person sees it: as above, for a count other than 1.

**The in-progress count, when it is 1**

> 1 task in in-progress

When the person sees it: they hear what the number counts. Opening the link shows this project's tasks in `in-progress`.

**The in-progress count, at any other value, 0 included**

> {count} tasks in in-progress

When the person sees it: as above, for a count other than 1.

**The done count, when it is 1**

> 1 task in done

When the person sees it: they hear what the number counts. Opening the link shows this project's tasks in `done`.

**The done count, at any other value, 0 included**

> {count} tasks in done

When the person sees it: as above, for a count other than 1.

**The cancelled count, when it is 1**

> 1 task in cancelled

When the person sees it: they hear what the number counts. Opening the link shows this project's tasks in `cancelled`.

**The cancelled count, at any other value, 0 included**

> {count} tasks in cancelled

When the person sees it: as above, for a count other than 1.

**The low priority count, when it is 1**

> 1 task with low priority

When the person sees it: they hear what the number counts. Opening the link shows this project's tasks with priority `low`.

**The low priority count, at any other value, 0 included**

> {count} tasks with low priority

When the person sees it: as above, for a count other than 1.

**The medium priority count, when it is 1**

> 1 task with medium priority

When the person sees it: they hear what the number counts. Opening the link shows this project's tasks with priority `medium`.

**The medium priority count, at any other value, 0 included**

> {count} tasks with medium priority

When the person sees it: as above, for a count other than 1.

**The high priority count, when it is 1**

> 1 task with high priority

When the person sees it: they hear what the number counts. Opening the link shows this project's tasks with priority `high`.

**The high priority count, at any other value, 0 included**

> {count} tasks with high priority

When the person sees it: as above, for a count other than 1.

**The critical priority count, when it is 1**

> 1 task with critical priority

When the person sees it: they hear what the number counts. Opening the link shows this project's tasks with priority `critical`.

**The critical priority count, at any other value, 0 included**

> {count} tasks with critical priority

When the person sees it: as above, for a count other than 1.

**The overdue count, when it is 1**

> 1 overdue task

When the person sees it: they hear what the number counts. Opening the link shows this project's overdue tasks.

**The overdue count, at any other value, 0 included**

> {count} overdue tasks

When the person sees it: as above, for a count other than 1.

---

## Wording decisions

- The four status names follow the name `CONTENT.md` § Accessibility of text fixes, "12 tasks in todo", with one pattern for all four statuses. The `in-progress` names therefore read "tasks in in-progress". The status word stays whole and hyphenated, because § Terminology rejects "In progress" as a spelling of the status. The same "a task in {status}" shape is the one `CONTENT.md` already uses in its refusal examples ("A task in todo can be moved…").
- The four priority names read "{count} tasks with {priority} priority". `CONTENT.md` fixes no priority name, and its rule asks only that the name start with the number and say what it counts. "12 high tasks" does not say that the word is a priority, and "12 medium tasks" reads as a size. Naming the noun "priority" says what is counted, and the priority word stays lowercase as § Terminology defines it. The product prose has no earlier phrasing of a priority count to follow (`web/pages.py`, searched for "priority").
- The overdue names follow the second name `CONTENT.md` fixes, "3 overdue tasks", lowercase as written there. The singular is "1 overdue task".
- A count of 0 takes the numeral and the plural form ("0 tasks in todo"), not the word "no". § Grammar and mechanics (Numbers) has "no" inside a sentence, and an accessible name is not a sentence. § Accessibility of text requires a number link's name to start with that number, and the visible text here is `0`, so the name has to contain it (SC 2.5.3, Label in Name). § Localization asks for a zero form only "where the text says 'no'", so zero shares the plural form.
- Every name is written out whole, eighteen strings for the nine links. None is assembled at runtime from a status or priority word and a frame. That follows § Localization ("No string is assembled from fragments"), so the Developer places each string without choosing a word. `{count}` is the only variable part, and it holds one number.
- No name says "open tasks". The status and priority counts include `done` and `cancelled` tasks, because each one counts every project task the filter returns for that one choice (`domain/summary.py`, `_matching`). "Open" would claim a narrower set than the number counts. The overdue count already excludes final statuses by the overdue rule, so "overdue" says enough.
- No name carries the project's name or the word "Summary". One project is shown per Summary, and the nine categories already differ, so the nine names are distinct from each other on every Summary (CP-522). None of them equals a header or view link ("Projects", "All tasks", "People", "Tasks", "Summary").
- No name ends with a full stop. § Grammar and mechanics (Sentence endings) gives links no end punctuation.

---

## Findings for the Content Manager

None. `CONTENT.md` § Accessibility of text and § Localization answered every string. The priority wording and the zero form above are applications of those rules, not new rules.
