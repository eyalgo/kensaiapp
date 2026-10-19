# Change Text — Your name on People

**Date:** 2026-10-12
**Category:** feature
**Behaviour:** changing

This file holds the exact words that the Your name change puts on the People page and in the terminal. Each string below is placed verbatim, and the state it belongs to is named above it. The strings follow `products/tracker17/docs/CONTENT.md` (Version 10), and they take their terms from the product's existing People and project strings in `products/tracker17/web/pages.py`.

---

## Text

### The Your name section on People

**Always, as the section's heading**

> Your name

When the person sees it: they have opened People, and the heading names the section that holds their own name. It comes before the Assignees heading.

### The field's label

**Always, as the visible label of the one text field in the Your name section**

> Your name

When the person sees it: the label names the field they type their name into. The field holds the saved name, or nothing when no name is saved.

### The Save button

**Always, as the button after the field**

> Save

When the person sees it: they have typed a name and press this button to keep it. The button's accessible name is the same word, because no other control on People reads `Save`.

### The sentence about earlier comments

**Always, as the plain text beside the field**

> Comments you've already written keep the name they were written under.

When the person sees it: they are about to set or change their name, and the sentence tells them that changing it leaves earlier comments as they are.

### The no-name line

**When no name is saved**

> No name is set. You need a name to comment.

When the person sees it: People has opened with an empty field, and the line tells them a name is missing and why they would want one. The line is absent once a name is saved.

### The blank reason

**When the person pressed Save with an empty field, or with only whitespace in it**

> Your name can't be blank. Type a name.

When the person sees it: their save was refused, the saved name is as it was, the field still holds what they typed, and focus is on the field. They can type a name and press Save again.

### The too-long reason

**When a save sent a name longer than the maximum, for each count except one**

> Your name can't be longer than {maximum} characters. Type a shorter one.

`{maximum}` is the tracker's short-text maximum, the same number the field's own character limit uses. It is 200 today, so the string reads "Your name can't be longer than 200 characters. Type a shorter one."

**The same state, when the maximum is 1**

> Your name can't be longer than 1 character. Type a shorter one.

When the person sees it: a save that no page of the tracker sends was refused, because the field stops at the maximum. The field shows the saved name, or nothing when none is saved, and focus is on the field. No part of the sent text appears.

### The save failure line

**When the save failed for a reason that is not a refusal**

> The tracker couldn't set your name to '{name}', and nothing was changed. What you typed is still in the form. Try again.

`{name}` is the name the person typed, written back exactly as typed, inside the straight single quotes the string carries.

When the person sees it: they pressed Save, the tracker didn't keep the name, the saved name is as it was, the field still holds what they typed, and focus is on Save. They can press Save again.

### The completion line

**When the save kept a name that differs from the one saved before, whether it is the first name or a replacement**

> You set your name to '{name}'.

`{name}` is the name now saved, written back exactly as saved, inside the straight single quotes the string carries.

When the person sees it: their name is saved, the field shows it, and focus is on the field with this line as its description. Nothing further is needed.

**When the person pressed Save with exactly the name already saved**

No string. People shows no completion line and no refusal, because nothing was saved (`change_spec.md` CP-218, "People shows no completion line and no refusal").

### The terminal line naming a failed name save

`change_design.md` names this place "the console line naming a failed name save". The console and the terminal are the same window, and `CONTENT.md` § Terminology uses "terminal".

**When the save failed for a reason that is not a refusal, printed in the terminal before the error text**

> The tracker couldn't set your name to '{name}', and nothing was changed.

`{name}` is the name the person typed, written back exactly as typed, inside the straight single quotes the string carries. The tracker prints the underlying error on its own line after this one, and that error text is not part of this file.

When the person sees it: they are reading the terminal the tracker was started from, and the line names the action that failed so the error text after it has a subject.

---

## Wording decisions

- The field's label is "Your name", not "Name". The assignee field on the same page is labelled "Name" (`products/tracker17/web/pages.py`, `_assignee_form`, `<label ...>Name</label>`). `CONTENT.md` § Accessibility of text says "A field's label is its name", so a second field labelled "Name" would give People two fields with one accessible name and nothing to tell them apart. "Your name" is the term `CONTENT.md` § Terminology fixes for this concept ("The reader's own name, set in the tracker"). The heading and the label read alike, and the heading names the section while the label names the field.
- The sentence about earlier comments and the no-name line are `CONTENT.md`'s own examples, taken word for word. The first is at § Accessibility of text ("Comments you've already written keep the name they were written under."), the second at § Message patterns, Empty ("No name is set. You need a name to comment."). Each says what `change_spec.md` CP-211 and CP-212 require. The keep-their-name claim is grounded: a saved comment carries its own author string (`products/tracker17/domain/tasks.py`, `class Comment`, `author: str`), and `change_design.md` § 3 A has the set operation return "a state differing only in `operator_name`".
- The blank reason says "can't be blank", not "needs at least one character" and not "can't be empty or only spaces". The rule refuses a name made only of whitespace (`change_spec.md` CP-220), so "at least one character" is false for a name of three spaces. "Only spaces" would be false for a tab or another whitespace character that the rule also refuses. "Blank" is the rule's own word, and it covers both cases exactly. The project and assignee reasons ("A project needs a name. Type one.") put the subject before "needs a name", and the reader's own name has no subject that can need one, so the form changes and the two-sentence shape stays. The action "Type a name." is the imperative `CONTENT.md` § Grammar and mechanics uses as its example for an instruction.
- The too-long reason follows the assignee and project reasons word for word, with "Your name" as the subject ("An assignee name can't be longer than {maximum} characters. Type a shorter one.", `products/tracker17/web/pages.py`, `_field_reason`). The count is written out for one and for the rest, as `CONTENT.md` § Localization requires ("Plurals are written out").
- The failure line and the completion line use the verb "set", which `CONTENT.md` § Message patterns, Completed lists among the fixed verbs. Its example is "You set your name to 'Sam'.". Setting a first name and replacing an earlier one share one completion string, because the person did the same thing both times and the line names the result. The failure line follows the failure formula and keeps "What you typed is still in the form", which is true here, because `change_spec.md` CP-222 keeps the typed text in the field.
- The terminal line is the failure line's first sentence, the form the product's existing actions already print (`products/tracker17/web/routes.py`, "The tracker couldn't add '{name}' to the assignees, and nothing was changed."). The design calls this place the console line. `CONTENT.md` § Terminology uses "terminal" for the same window, so this file does too.
- No string carries a word the People page tests still forbid after `change_spec.md` CP-238: "all tasks", "operator" and "assign to" (`products/tracker17/tests/integration/test_people_pages.py`, `for unavailable in`).
- Banned-word check: every string was searched for each word in `CONTENT.md` § Terminology, "Banned in anything a person sees", in every inflection, and for the banned punctuation in § Grammar and mechanics. The search found none. The product carries no check that reads its strings for banned words: the two test files whose names hit a search for "banned" check imports, not prose (`products/tracker17/tests/architecture/test_imports.py`, `BANNED_EVERYWHERE = ("http.client", ...)`).

---

## Findings for the Content Manager

- "No name is set. You need a name to comment." — `CONTENT.md` § Message patterns, Empty states the second sentence as "one sentence naming the one thing to do next and the control to do it with, by its label". The standard's own example for this state, the line used here, names no control, and so does its assignee example ("Tasks can be assigned only to names on this list."). The standard doesn't say whether the formula or the examples win when the next step is to use the control right beside the line. Meanwhile the line is the standard's own example, word for word, because it is the standard applied to this exact state and it says what `change_spec.md` CP-212 requires.
