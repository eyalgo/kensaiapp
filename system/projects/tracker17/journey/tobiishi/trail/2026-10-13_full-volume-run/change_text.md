# Change Text — The timed run covers the comment add and the People assignee add and remove

**Date:** 2026-10-13
**Category:** nfdr
**Behaviour:** changing

---

## Text

The reader of every string below is the developer who starts the timed run from the product root
and reads what it prints, and the integration tests that read those lines.
The run prints the three blocks after every line it prints today, in this order: the comment add,
the assignee add, the assignee remove. Within a block the fixture line comes first and its three
rows follow it (`change_spec.md` § Rules, CP-285).

Each string is a whole line. Braces mark a variable part, and each one is described under its string.
Nothing else in a line is chosen at placement.

### The timed run's console fixture reports

**The comment add's fixture, printed before its three rows**

> comment fixture: 1000 tasks, 20 comments each (20000 in all); title of {title length} characters, comment of {comment length} characters, name of {name length} characters, added comment of {added comment length} characters

When the person sees it: the run has loaded the comment add's own fixture and is about to time the
add. They can check the volume and the text lengths the timing was taken at.
`1000`, `20` and `20000` are the fixture's task count, comments on each task, and total comments,
each read from the fixture the action ran on. `{title length}` is the character count of the title of
the task the comment is added to. `{comment length}` is the character count of one of that task's
own fixture comments. `{name length}` is the character count of the name the fixture saved, the one
the comment is written under. `{added comment length}` is the character count of the comment text
submitted. Every count is a numeral and counts one character per Unicode code point
(`change_spec.md` § Rules, CP-286).

**The assignee add's fixture, printed before its three rows**

> assignee add fixture: 1000 tasks, 20 comments each (20000 in all); title of {title length} characters, comment of {comment length} characters, name added of {name length} characters

When the person sees it: the run has loaded the assignee add's own fixture and is about to time the
add. They can check the volume and the text lengths the timing was taken at.
`1000`, `20` and `20000` are read from the fixture as in the comment add's line. `{title length}`
and `{comment length}` are a fixture task's title and one of its comments, counted as above.
`{name length}` is the character count of the name submitted to the assignee list.

**The assignee remove's fixture, printed before its three rows**

> assignee remove fixture: 1000 tasks, 20 comments each (20000 in all); title of {title length} characters, comment of {comment length} characters, name removed of {name length} characters

When the person sees it: the run has loaded the assignee remove's own fixture and is about to time
the remove. They can check the volume and the text lengths the timing was taken at.
`1000`, `20` and `20000`, `{title length}` and `{comment length}` are as in the assignee add's line.
`{name length}` is the character count of the name submitted for removal from the assignee list.

### The timed run's console action timing rows

Every row has four forms, one per state. `{ms}` is the row's measured duration in milliseconds, with
one decimal place, such as `33.8`. The run prints exactly one form per row.

- **Done and under the limit** — the label, a colon, the time, `ms`, and nothing after it.
- **Not done** — the action was refused or failed, its landing page did not show the result, or the
  landing was never requested because the submission was not done.
- **At or over the limit** — the row's duration is 1.0 second or more.
- **Not done and at or over the limit** — both.

The ` — ` before a problem is a space, an em dash and a space, the same characters every failing row
of the run prints today. `1 s` is the limit as the run writes it today.

**Adding a comment — the submission**

> add a comment at 1000 tasks: {ms} ms

> add a comment at 1000 tasks: {ms} ms — refused or failed

> add a comment at 1000 tasks: {ms} ms — at or over 1 s

> add a comment at 1000 tasks: {ms} ms — refused or failed, at or over 1 s

When the person sees it: the timed POST that adds one comment has answered. Done means the
comment is saved, last on its task, under the fixture's saved name, and nothing else in the saved
data changed (CP-279).

**Adding a comment — the landing page**

> comment landing page at 1000 tasks: {ms} ms

> comment landing page at 1000 tasks: {ms} ms — refused or failed

> comment landing page at 1000 tasks: {ms} ms — at or over 1 s

> comment landing page at 1000 tasks: {ms} ms — refused or failed, at or over 1 s

When the person sees it: the page the comment add redirected to has been timed, or was not
requested. Done means a `200` showing the comment add's completion line and the added comment's text
(CP-283). When the landing was not requested its duration reads `0.0`.

**Adding a comment — the total**

> comment total at 1000 tasks: {ms} ms

> comment total at 1000 tasks: {ms} ms — refused or failed

> comment total at 1000 tasks: {ms} ms — at or over 1 s

> comment total at 1000 tasks: {ms} ms — refused or failed, at or over 1 s

When the person sees it: the submission and its landing page have been added together. The total
can be at or over the limit while both parts are under it (CP-284), and it is not done whenever
either part is not done.

**Adding an assignee — the submission**

> add an assignee at 1000 tasks: {ms} ms

> add an assignee at 1000 tasks: {ms} ms — refused or failed

> add an assignee at 1000 tasks: {ms} ms — at or over 1 s

> add an assignee at 1000 tasks: {ms} ms — refused or failed, at or over 1 s

When the person sees it: the timed POST that adds one name to the assignee list on People has
answered. Done means that one name is on the saved list and nothing else changed (CP-280).

**Adding an assignee — the landing page**

> assignee add landing page at 1000 tasks: {ms} ms

> assignee add landing page at 1000 tasks: {ms} ms — refused or failed

> assignee add landing page at 1000 tasks: {ms} ms — at or over 1 s

> assignee add landing page at 1000 tasks: {ms} ms — refused or failed, at or over 1 s

When the person sees it: the People page the add redirected to has been timed, or was not
requested. Done means a `200` showing the add's completion line (CP-283).

**Adding an assignee — the total**

> assignee add total at 1000 tasks: {ms} ms

> assignee add total at 1000 tasks: {ms} ms — refused or failed

> assignee add total at 1000 tasks: {ms} ms — at or over 1 s

> assignee add total at 1000 tasks: {ms} ms — refused or failed, at or over 1 s

When the person sees it: the add's submission and landing page have been added together, held to
the same limit as each part.

**Removing an assignee — the submission**

> remove an assignee at 1000 tasks: {ms} ms

> remove an assignee at 1000 tasks: {ms} ms — refused or failed

> remove an assignee at 1000 tasks: {ms} ms — at or over 1 s

> remove an assignee at 1000 tasks: {ms} ms — refused or failed, at or over 1 s

When the person sees it: the timed POST that removes one name from the assignee list on People has
answered. Done means that one name is gone from the saved list, every task keeps its assignee, and
nothing else changed (CP-281).

**Removing an assignee — the landing page**

> assignee remove landing page at 1000 tasks: {ms} ms

> assignee remove landing page at 1000 tasks: {ms} ms — refused or failed

> assignee remove landing page at 1000 tasks: {ms} ms — at or over 1 s

> assignee remove landing page at 1000 tasks: {ms} ms — refused or failed, at or over 1 s

When the person sees it: the People page the remove redirected to has been timed, or was not
requested. Done means a `200` showing the remove's completion line (CP-283).

**Removing an assignee — the total**

> assignee remove total at 1000 tasks: {ms} ms

> assignee remove total at 1000 tasks: {ms} ms — refused or failed

> assignee remove total at 1000 tasks: {ms} ms — at or over 1 s

> assignee remove total at 1000 tasks: {ms} ms — refused or failed, at or over 1 s

When the person sees it: the remove's submission and landing page have been added together, held to
the same limit as each part.

---

## Wording decisions

- Every label and fixture line is the spec's own, character for character (`change_spec.md` § Rules,
  CP-285 and CP-286). No wording was changed. The spec fixed them so a test can check them, and its
  Locked Answers, Gap 2, derive them from the run's existing label rows.
- The four forms of a row were written out whole, one per state, though the request names only the
  passing row. The reason is that the failing forms are what a developer meets when the run exits `1`,
  and a form left unwritten would leave the Developer to compose it. Each failing form uses the
  problem words and separator every failing row of the run prints today (`change_spec.md` § Rules,
  CP-285, "drawn from `refused or failed` and `at or over 1 s`"), because CP-276 keeps the existing rows as they are and a
  different suffix on three new actions would give one state two wordings.
- `refused or failed` is kept as one phrase for every way a row is not done, including a landing that
  was not requested and a landing that did not show the result. CP-282 and CP-283 report all of these
  the same way. Splitting them would claim a cause the row's single done flag does not record.
- `1000` and `20000` carry no thousands separator, matching the existing fixture lines and rows of the
  run. The spec's prose writes `1,000`, and the printed form follows the corpus.
- The banned-lexicon scan over every string found the em dash, "failed" and the semicolon, and no
  other banned word. All three were kept. The reason is that the spec fixes each string verbatim
  (CP-285, CP-286), and every line the run prints today already carries them. On this reading
  `CONTENT.md` § Scope does not reach the timed run's output, so its ban does not apply. Whether it
  should is the finding below. The product carries no word-list check to run over the strings.
- The verbs and nouns are the product's own terms: "add" and "remove" for a name on the assignee list,
  never "delete", and "comment" and "assignee" (`products/tracker17/docs/CONTENT.md` § Terminology,
  the Add, Remove, comment and assignee rows).

---

## Findings for the Content Manager

- Every string above, the fixture lines and the timing rows of the timed run. The standard does not
  say whether it governs them. `products/tracker17/docs/CONTENT.md` § Scope names
  "the pages in the browser, the text the tracker prints in the terminal it was started from, and the
  written setup instructions", and excludes "code comment" and "test name". The timed run's console
  report is a developer check's output, read in a terminal, and is none of those. Were it governed,
  three things in these strings would break its rules. The failing suffix's em dash and the fixture
  lines' semicolon are under § Grammar and mechanics, "Banned punctuation". "failed" is under
  § Terminology, "Banned in anything a person sees". The labels
  would also break § Grammar and mechanics, "Case" and "Sentence endings", only if a row counts as a
  sentence. Meanwhile the strings were written in the run's existing shapes, which the spec fixes and
  the existing tests read. Rewording the suffix would change rows that CP-276 keeps unchanged.
