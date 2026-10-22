# Change Text — The move refusal for an overtaken press, and for one reached by an address

**Date:** 2026-10-21
**Category:** feature
**Behaviour:** changing

---

## Text

Both places show the same strings. Each string is the move refusal's whole line. It sits beside the
task's status in words, it is that status word's accessible description, and it takes no focus.

In every string, `{title}` is the task's title as saved, written exactly as typed. `{status}` is the
task's saved status, one of `todo`, `in-progress`, `done` or `cancelled`. Where `{status}` appears
twice in one string, it is the same status both times. `{first move}`, `{second move}` and
`{third move}` are the moves the page offers for that task, each one status word, in the order the
page shows their buttons. The quotes around `{title}` belong to the string.

For an overtaken press, the string is picked by how many moves the page offers for the task: none,
one, two or three. Three is the most there can be, because a task can only be moved to one of the
other three statuses. A submission that names no status, or something that isn't a status, gets the
same string as an overtaken press on the same task.

### A project's Tasks view, beside the task's status in its row

**Overtaken press, the task now offers no move** (its status is `done` or `cancelled`)

> The status of '{title}' has changed to {status}. A task in {status} can't be moved.

When the person sees it: they pressed a move on a page loaded before the status changed, nothing was
saved, and the row shows the saved status with no move buttons, so there is nothing to press.

**Overtaken press, the task now offers one move**

> The status of '{title}' has changed to {status}. A task in {status} can be moved to {first move}.

When the person sees it: nothing was saved, and the row shows the saved status and the one move
button named in the line.

**Overtaken press, the task now offers two moves** (today, a task in `todo`)

> The status of '{title}' has changed to {status}. A task in {status} can be moved to {first move} or {second move}.

When the person sees it: nothing was saved, and the row shows the saved status and the two move
buttons named in the line, in that order.

**Overtaken press, the task now offers three moves** (today, a task in `in-progress`)

> The status of '{title}' has changed to {status}. A task in {status} can be moved to {first move}, {second move} or {third move}.

When the person sees it: nothing was saved, and the row shows the saved status and the three move
buttons named in the line, in that order.

**Address refusal, for a task in `done` or `cancelled`** (the address asks to open the confirmation
of a move to `cancelled`, or to back out of it)

> The status of '{title}' is {status}, which doesn't allow a move to cancelled. A task in {status} can't be moved.

When the person sees it: they opened an address, by Back, a reload, a bookmark or by typing, with no
press. Nothing was saved, no confirmation shows and the task offers no move, so there is nothing to
do.

### The task's page, beside its status

**Overtaken press, the task now offers no move** (its status is `done` or `cancelled`)

> The status of '{title}' has changed to {status}. A task in {status} can't be moved.

When the person sees it: they pressed a move on a page loaded before the status changed, nothing was
saved, and the page shows the saved status with no move buttons, so there is nothing to press.

**Overtaken press, the task now offers one move**

> The status of '{title}' has changed to {status}. A task in {status} can be moved to {first move}.

When the person sees it: nothing was saved, and the page shows the saved status and the one move
button named in the line.

**Overtaken press, the task now offers two moves** (today, a task in `todo`)

> The status of '{title}' has changed to {status}. A task in {status} can be moved to {first move} or {second move}.

When the person sees it: nothing was saved, and the page shows the saved status and the two move
buttons named in the line, in that order.

**Overtaken press, the task now offers three moves** (today, a task in `in-progress`)

> The status of '{title}' has changed to {status}. A task in {status} can be moved to {first move}, {second move} or {third move}.

When the person sees it: nothing was saved, and the page shows the saved status and the three move
buttons named in the line, in that order.

**Address refusal, for a task in `done` or `cancelled`** (the address asks to open the confirmation
of a move to `cancelled`, or to back out of it)

> The status of '{title}' is {status}, which doesn't allow a move to cancelled. A task in {status} can't be moved.

When the person sees it: they opened an address, by Back, a reload, a bookmark or by typing, with no
press. Nothing was saved, no confirmation shows and the task offers no move, so there is nothing to
do.

Filled in for the spec's Examples, as the person reads them:

- `Set up CI` overtaken into `in-progress`: "The status of 'Set up CI' has changed to in-progress. A task in in-progress can be moved to done, cancelled or todo."
- `Set up CI` overtaken into `todo`: "The status of 'Set up CI' has changed to todo. A task in todo can be moved to in-progress or cancelled."
- `Set up CI` overtaken into `done`: "The status of 'Set up CI' has changed to done. A task in done can't be moved."
- `Set up CI` in `done`, reached by the confirmation's address: "The status of 'Set up CI' is done, which doesn't allow a move to cancelled. A task in done can't be moved."

---

## Wording decisions

- The overtaken press's line names the saved status ("has changed to {status}"), where the spec asks
  only that it say the status has changed — the focused status word is what the line describes, so the
  line states what that word now reads. The claim is grounded: moves depend only on the status, so a
  press the page offered can be refused only when the saved status differs from the one that page
  loaded with.
- The overtaken press's line leaves out "since this page loaded", the standard's replacement for
  "another tab" — the line is shown on a page built after the refusal, so "this page" is the new page,
  and its status has not changed since it loaded. The plain "has changed" is the smaller true thing.
  "Another tab" and "another window" are not used, as § Terminology bans them.
- The second sentence states what the status allows ("A task in {status} can be moved to …") rather
  than an action such as "Press done to move it" — in the spec's first example the reader pressed
  `in-progress` and the task is already `in-progress`. There the state they wanted already holds, so
  no action exists, and a refusal's second sentence then says what the page shows (§ Message patterns,
  Error, *A refusal*). The same sentence form also reads true where an action does exist.
- The second sentence is shaped like the address refusal's "A task in {status} can't be moved.", so the
  four overtaken-press forms and the address refusal read as one family. The `done` and `cancelled`
  forms keep today's tail words exactly.
- The list of moves is four whole strings, one for each count of moves, and not one sentence with a
  joined list in a single placeholder — § Localization says no string is assembled from fragments and a
  placeholder holds one value. The design has the line name whatever ordered moves the page is given,
  so a fixed string per status would not fit it. Each move placeholder holds one status word.
- The three-move list takes no comma before "or", as the product's own "low, medium, high or critical"
  does.
- "A task in in-progress" repeats "in" — kept, because the status word is written as defined and the
  same frame serves all four statuses.
- The address refusal is CP-361's line exactly, as the seventh example of *A refusal* in `CONTENT.md`
  gives it. One string with `{status}` serves `done` and `cancelled`, as that rule says the same
  formula does.
- "has changed" is kept although § Terminology rejects "change" as the word for moving a task — here
  it says the status changed, not what the reader did, and CP-359 and *A refusal*'s fifth example both
  word it that way. The move itself is still called a move ("can be moved", "a move to cancelled").
- "the move you pressed" appears in no string. No string offers a reload, a link or a control.
- Checked every string against § Terminology's banned list, § Grammar and mechanics and the
  writing bar: no banned word in any inflection, no "now" or other relative time word, no status word
  starting a sentence, contractions as required, two sentences per refusal, and each sentence at most
  15 words besides the title. The product carries no vocabulary check to run: its architecture tests
  check imports, not words.

---

## Findings for the Content Manager

- "The status of '{title}' has changed to {status}. …" — § Terminology's banned list says to write
  "since this page loaded" in place of "another tab" when explaining an out-of-date page, and *A
  refusal*'s fifth example uses it. Neither says what to write when the refusal is shown on a page built
  after the refusal, where "this page" is the new page and the phrase is false. Written meanwhile as a
  bare "has changed", with no time phrase.
- The same strings — *A refusal*'s fifth example still ends "Reload the page to see it.", and UXD
  version 8 (UX-I3, UX-F4) says the overtaken press offers no reload. `CONTENT.md` has no example for
  the overtaken press as the UXD now has it. Written meanwhile with no reload, to the UXD and CP-362. The
  spec records the same disagreement (Locked Answers, Gap 4).
- "A task in {status} can be moved to {first move}, {second move} or {third move}." — § Localization
  says a placeholder holds one value and no string is assembled from fragments, but states no rule for
  a list whose length varies at runtime. Written meanwhile as one whole string per list length, each
  placeholder holding one status word.
