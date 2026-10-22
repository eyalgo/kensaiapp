# Change Text — time a status move at full volume

**Date:** 2026-10-21
**Category:** nfdr
**Behaviour:** changing

---

## Text

The reader of every string below is a developer who ran the timed run from a terminal and is reading
its output to learn whether the move was fast enough and whether it happened. The four lines follow
the last line the run prints today, `assignee remove total at 1000 tasks: …`, in the order below, and
nothing follows them (`change_spec.md` CP-373). A brace marks a value the run fills in. The line under
each string says what fills it.

### The timed run's move fixture report

**The move's fixture, read back from where it was saved**

> move fixture: {tasks} tasks, {per task} comments each ({all} in all); title of {T} characters, comment of {C} characters

`{tasks}` is the number of tasks in the fixture as loaded back. `{per task}` is the number of comments
on each of those tasks. `{all}` is `{tasks}` times `{per task}`. `{T}` is the number of characters in
the moved task's title, and `{C}` the number in that task's first comment, counting one character per
code point. Each is a whole number in numerals, with no thousands separator. On the run's own fixture
the line begins `move fixture: 1000 tasks, 20 comments each (20000 in all); ` (CP-374). On the
varied fixture of CP-386 it reads
`move fixture: 300 tasks, 3 comments each (900 in all); title of 7 characters, comment of 6 characters`.

When the person sees it: they have just started the run, the older actions have printed, and this line
tells them what data the move about to be timed acts on. There is nothing to do.

### The timed run's three move timing rows

Each row is printed in one of four forms. `{ms}` is the row's time in milliseconds with exactly one
decimal place, such as `26.5`, `0.0` or `1000.0` (CP-375). The em dash and the space either side of it
are part of the string, and the two problems, where both apply, are joined by a comma and a space in
the order shown.

**The move submission — it counted as done and took under 1 second**

> move a task at 1000 tasks: {ms} ms

**The move submission — it did not count as done (CP-377), and took under 1 second**

> move a task at 1000 tasks: {ms} ms — refused or failed

**The move submission — it counted as done and took 1 second or more**

> move a task at 1000 tasks: {ms} ms — at or over 1 s

**The move submission — it did not count as done and took 1 second or more**

> move a task at 1000 tasks: {ms} ms — refused or failed, at or over 1 s

When the person sees it: they learn how long the one move submission took and whether the tracker
saved exactly that move. A row with a problem means the run will exit 1.

**The landing page — it counted as done (CP-378) and took under 1 second**

> move landing page at 1000 tasks: {ms} ms

**The landing page — it did not count as done, and took under 1 second**

> move landing page at 1000 tasks: {ms} ms — refused or failed

This form also covers the landing that was never requested, because the submission's answer was not
the exact redirect CP-377 (a) names. `{ms}` is then `0.0`, and the row reads
`move landing page at 1000 tasks: 0.0 ms — refused or failed` (CP-379).

**The landing page — it counted as done and took 1 second or more**

> move landing page at 1000 tasks: {ms} ms — at or over 1 s

**The landing page — it did not count as done and took 1 second or more**

> move landing page at 1000 tasks: {ms} ms — refused or failed, at or over 1 s

When the person sees it: they learn how long the page the move lands on took to load, and whether
that page showed the move's completion line.

**The total — both parts counted as done, and their sum is under 1 second**

> move total at 1000 tasks: {ms} ms

**The total — either part did not count as done, and the sum is under 1 second**

> move total at 1000 tasks: {ms} ms — refused or failed

**The total — both parts counted as done, and their sum is 1 second or more**

> move total at 1000 tasks: {ms} ms — at or over 1 s

This form applies even when each part is under 1 second (CP-380).

**The total — either part did not count as done, and the sum is 1 second or more**

> move total at 1000 tasks: {ms} ms — refused or failed, at or over 1 s

When the person sees it: `{ms}` is the submission's time plus the landing's time, not the time
between them (CP-376). When the landing was never requested, `{ms}` equals the submission row's time
(CP-379). This is the last line the run prints.

---

## Wording decisions

- The four strings are the exact strings `change_spec.md` CP-373 to CP-375 fixes, with no word
  changed. — The spec settled them in its Locked Answers (Gap 6), and they already match the run's
  existing output. The fixture line has the same shape as the fixture lines the run prints today for
  the comment add and the two assignee actions, such as "comment fixture: 1000 tasks, 20 comments each
  (20000 in all); title of". The three row labels follow the comment action's "add a comment at",
  "comment landing page at" and "comment total at". The two problem phrases, "refused or failed" and
  "at or over 1 s", are the ones every existing row already prints.
- Each row is written out in all four of its forms, not as one label plus a problem suffix. — The
  spec gives the forms as a rule (CP-375). Spelling each one out lets the Developer and the tests
  compare against a whole line without assembling one, and it names the state each form is for.
- The landing that is never requested is filed under the landing's "did not count as done" form, with
  `0.0` filled in, and has no string of its own. — It reads exactly like that form (CP-379), so a
  separate string would be two strings for one concept.
- Brace names are the spec's own (`{tasks}`, `{per task}`, `{all}`, `{T}`, `{C}`, `{ms}`). — Keeping
  them lets a reader check this file against CP-373 and CP-374 directly.
- The em dash, the semicolon, the colons and the word "failed" are kept. — The product's CONTENT.md
  § Scope says its wording standard "governs no output of a script a developer runs to check or
  measure the tracker, such as the timed run", and its RN-25 says of these rows "Their em dash,
  semicolon and 'failed' break no rule here." The banned-words check therefore had nothing to catch in
  these strings. The existing timed-run tests look for "over" and "refused" in a line to find a
  problem. Those two words appear only in the problem part, never in a label or in the fixture line,
  as `change_spec.md` Verified Claims also records. No label carries a colon, so text read up to a
  row's first colon is the whole label.
- The landing page's completion line, `You moved '{title}' to in-progress.`, is not text this change
  publishes. — The tracker writes that line, and the run only checks for it (CP-378). CONTENT.md
  § Scope governs such a string where the tracker writes it, so it is not written here.

---

## Findings for the Content Manager

None. CONTENT.md § Scope and RN-25 already state that the timed run's output sits outside the
product's wording standard, so no rule was missing for these strings.
