# Change Text — Comments on a task's page

**Date:** 2026-10-12
**Category:** feature
**Behaviour:** changing

---

## Text

This file holds every word that change `tracker17 · tobiishi · 2026-10-12_comments-on-the-page` puts in front of a person. Each string is verbatim. A part in braces is a placeholder, described under the string. The placeholders are:

- `{title}` — the task's title as saved, shown whole. The straight single quotes around it belong to the string, not to the value.
- `{author}` — the comment's author as saved, shown exactly and whole, with no quotes.
- `{written}` — the moment the comment was written, in the machine's local time, from the one date-and-time formatter, as `YYYY-MM-DD HH:MM` (for example `2026-10-12 14:32`).
- `{count}` — the comment field's maximum, the same number as the field's own limit, written the way the project form's description note already writes its maximum (for example `4000`).

### The task page's Comments heading

**Always, at the top of the Comments area**

> Comments

When the person sees it: they are on a task's page, below its fields and labels, and this heading starts the area that lists the task's comments and holds the form to add one.

### The Comments area's empty state

**The task has no comments, and your name is set**

> This task has no comments yet. Type a comment and press Add.

When the person sees it: the task has no comments, the form is in view, and pressing Add with text will add the first one.

**The task has no comments, and no name is set**

> This task has no comments yet.

When the person sees it: the task has no comments, and the no-name notice sits with the form and names the one thing to do first, which is set a name on People.

### A comment's author and time

**Every comment in the list, on its meta line above the comment's text**

> {author}, {written}

When the person sees it: they are reading the task's comments oldest first, and this line tells them who wrote each one and when. The comment's text follows on its own lines, exactly as saved.

### The comment field's label and maximum sentence

**The field's visible label, always**

> Comment

When the person sees it: they are at the add-comment form, and this label names the multi-line field they type in.

**The sentence beside the field, always, when the maximum is 1**

> A comment can hold up to 1 character.

**The sentence beside the field, always, for any other maximum**

> A comment can hold up to {count} characters.

When the person sees it: before they type, they learn the most a comment holds, and the number is the field's own limit. The product's maximum is 4000, so the second form is the one shown. The first form exists because every string that carries a count has a written form for one.

### The no-name notice and its People link

**No name is set**

> You need a name to comment. Set your name on the People page.

Link: the word `People` in the second sentence is the link, and it opens People. No other word in the notice is part of the link.

When the person sees it: no name is saved, so a comment would be refused. The notice is in view before they type, and the link takes them to the place to set a name.

**A name is set**

No notice is shown, and no words take its place.

### The Add button

**Always, the visible label**

> Add

**Always, the button's accessible name**

> Add comment to '{title}'

When the person sees it: they have typed a comment and press Add to put it on the task. A screen-reader user hears the accessible name, which tells this Add apart from the label area's Add on the same page.

### Refusal reasons

Each reason sits beside the comment field. Exactly one shows, as the change's rules choose it.

**The comment is longer than the maximum, when the maximum is 1**

> A comment can't be longer than 1 character. Type a shorter one.

**The comment is longer than the maximum, for any other maximum**

> A comment can't be longer than {count} characters. Type a shorter one.

When the person sees it: the tracker refused an over-long comment that only a request no page sends can carry, saved nothing, and the field is empty. They can type a comment within the maximum and press Add.

**The comment is blank: empty, or only spaces, line breaks or other whitespace**

> A comment can't be blank. Type a comment.

When the person sees it: they pressed Add with nothing to show, nothing was saved, and the field still holds what they typed. They can type a comment and press Add again.

**No name is set**

> A comment needs your name. Set it on the People page, then add the comment.

When the person sees it: they pressed Add with no name saved, nothing was saved, and the field still holds what they typed. The notice's People link is on the same page, and after the name is set they can add the comment.

### The failure line

**The add didn't happen for a reason that isn't a refusal**

> The tracker couldn't add your comment to '{title}', and nothing was changed. What you typed is still in the form. Try again.

When the person sees it: the comment was not saved and the task's comments are as they were. Their text is still in the field, focus is on Add, and pressing Add again retries.

### The completion line

**A comment was added**

> You added a comment to '{title}'.

When the person sees it: the comment is saved and is now last in the list, in view and focused. The line reports the result and does not take focus.

### Accessible descriptions

These associations use the strings above and add no words of their own.

**A comment was added**

The completion line above is the accessible description of the new comment, which holds focus.

**A refusal**

The refusal reason above is the accessible description of the comment field, which holds focus.

**A failure**

The failure line above is the accessible description of the Add button, which holds focus.

When the person sees it: a screen-reader user hears the focused element and then the one line that says what happened, with no second announcement.

### The terminal's failed-comment action line

**An add fails for a reason that isn't a refusal, and the tracker can read the task's title**

> The tracker couldn't add your comment to '{title}', and nothing was changed.

**An add fails for a reason that isn't a refusal, and the tracker can't read the task**

> The tracker couldn't add your comment, and nothing was changed.

When the person sees it: they are reading the terminal the tracker was started from. The line names the action, and the underlying error text follows on its own line, verbatim, as for every other failed action.

---

## Wording decisions

- **The empty state has two strings, one for each name state.** The no-comments line follows the Empty formula and the label area's own line, "This task has no labels. Type a label and press Add." (`products/tracker17/web/pages.py`, `NO_LABELS`). With no name set, "press Add" would send the reader into the no-name refusal, a next action the tracker can't keep. The notice already names the one thing to do then, so that form keeps only the first sentence (`products/tracker17/docs/CONTENT.md` § Voice, "Give one next action when one exists"). The design and the spec name one empty state (CP-244). The second string covers a state they left unworded, and the page already knows whether a name is set (`change_design.md` § 3 Sub-job D, "Site supplies the current `Tracker.operator_name()` at GET time").
- **The blank reason says "can't be blank" and not "needs text".** A whitespace-only comment holds characters, so "needs text" or "needs at least one character" would be false for it. The wording matches the product's own reason for the same rule on the reader's name, "Your name can't be blank. Type a name." (`products/tracker17/web/pages.py`, Your name refusals), and names the field's subject first (`CONTENT.md` § Accessibility of text, "Its first sentence names the field's subject").
- **The no-name reason is `CONTENT.md`'s own example, word for word**: "A comment needs your name. Set it on the People page, then add the comment." (`CONTENT.md` § Message patterns, Error, "A refusal"). It carries no link. When no name is saved the notice is on the same page and holds the page's one link to People, and CP-274 admits exactly one link in the task's main area in that state.
- **The notice uses "your name", the product's term.** The first sentence keeps the corpus wording "You need a name to comment." (`products/tracker17/web/pages.py`, Your name section, "No name is set. You need a name to comment."). The action sentence uses the term `CONTENT.md` § Terminology fixes for the concept, "your name". The link text is `People` alone, because link text names the destination and nothing else (`CONTENT.md` § Accessibility of text, "Link text means something read out of context").
- **The failure line and the terminal line name the comment as "your comment to '{title}'" and do not quote the typed text.** The failure formula quotes the typed value (`CONTENT.md` § Message patterns, Error, "the typed value quoted"). A comment can run to 4000 characters across many lines, and nothing the tracker says is shortened (`CONTENT.md` § Grammar and mechanics, Quotes). Quoted whole, the comment would bury the result sentence and break the terminal's one-line action message. The text is still in the form on that page, so naming its task is the smaller sufficient thing. This gap is raised in the Findings section below.
- **The terminal line has a form for when the task can't be read**, matching the label actions' terminal line, which names the task only "when it is read" (`products/tracker17/web/routes.py`, `_label_failure_line`). Without it the Developer would have to choose words for that case.
- **The comment form's Add button gets an accessible name that adds what it acts on, "Add comment to '{title}'".** After this change the task's page has two buttons labelled Add, the label area's and the comment form's. `CONTENT.md` § Accessibility of text says the accessible name of a repeated label adds the thing the control acts on and keeps the visible label as one unbroken string, as in "Move 'Set up CI' to in-progress". The label area's Add keeps its present name. The request allows "no wording change outside the comment text the content record names" (`change_spec.md`, Request), so that button is not renamed here. Under the same rule it should become something like "Add label to '{title}'", and that is left to a later change that may touch the label area's words.
- **The maximum sentence follows the project form's description note**, "A description can hold up to {count} characters." (`products/tracker17/web/pages.py`, project create form). It uses the same count rendering, so the number matches the field's limit, as CP-245 requires. No "can't change" sentence was added beside it. UXD UX-F7 gives that as the reason the maximum is shown, but the design's `Publishes text:` line names only the maximum sentence.
- **Both count-bearing strings have a form for one**, because every string that carries a count has a written form for one and for the rest (`CONTENT.md` § Localization, "Plurals are written out"). The product's maximum is 4000, so only the plural form appears today.
- **The completion line says "a comment" and not the comment's text**, for the same reason as the failure line. The verb "added" is the one `CONTENT.md` § Message patterns, Completed fixes for Add. The new comment is focused and shows its own text, so the line names only the result.

---

## Findings for the Content Manager

- `{author}, {written}` — `CONTENT.md` states no rule for a non-sentence line that pairs a typed value with a date and time, such as a byline. It doesn't say which separator to use, whether the typed value is quoted (§ Grammar and mechanics, Quotes, covers a typed value "in a sentence" only), or which part comes first. Meanwhile the string puts the author first, so the reader can name who acted (§ Voice, first fallback). It separates the parts with a comma, the plainest punctuation the bans leave, and doesn't quote the author, as the task facts and table cells already show typed values unquoted. Because the time never holds a comma, the line reads unambiguously from its end even when an author's name holds one.
- `The tracker couldn't add your comment to '{title}', and nothing was changed.` (page and terminal) — the failure formula quotes the typed value and § Grammar and mechanics, Quotes forbids shortening it. Neither rule says what to do when the typed value is long, multi-line text, as a comment or a project description can be. Meanwhile the string names the thing by its task and quotes the task's title instead.
- `This task has no comments yet.` — the Empty formula requires a second sentence naming the one thing to do next with its control. It doesn't cover an empty state where that action is impossible until another condition is met, and a separate notice on the same page already names the condition. Meanwhile the no-name form drops the second sentence and leaves the action to the notice.
