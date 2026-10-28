# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-28
- **Sources re-read:** None. No answer rested on a source outside this repository.

## Items worked

### 3.1 — § Needs confirming does not say whether a task's comments are "what goes with it"

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** answered
- **Why:** Comments do not count, for a task or for a project's tasks, and the section should say what the count is of. The item is this document's own question, so the answer goes in its slot and no upstream companion is raised.
  1. **The item asks the section to state a case, and it cites its occurrence.** It sits under "Raised from downstream" and asks `CONTENT.md` § Needs confirming to say whether comments are counted, which the section does not say. The item cites a site where the case is present now: the task deletion sentence in `web/pages.py` line 782 (`DELETE_SENTENCE = "Delete '{title}'? You can't undo this."`), and the requirement that a task's comments go with it, `docs/SRS.md` line 156 (FR-17). I re-read both and each says what the item says. So the rule that a widening waits until it occurs does not apply, and the item is taken.
  2. **The line is whether the reader manages the things one by one.** A project's tasks each have their own page, status and controls, so a count tells the reader the scale of the loss. A task's comments have none of that: they show "as a flat list" and "can't be edited or deleted" (`docs/PRD.md` § Core Features, Comments). A task's labels, assignee and due date also go with it and nobody asks for those to be counted; comments are in the same position, the part of the task that happens to vary in size. The line is applicable to a real string: a count names one kind of thing, the items the thing holds that the reader works on separately.
  3. **Check 3, against the document and its inputs.** The task example already names no count and the project example counts tasks only (`docs/CONTENT.md` § Needs confirming), so the examples are right and the formula's first sentence is the loose part. The UXD agrees: UX-F10 lists the project's task count among the data the page needs for the delete confirmation, and UX-F9 lists no comment count for the task's. UX-F9's "Delete task removes the task and its comments" states what the action does and does not say the sentence names it. The completion line already counts "tasks the action deleted" for a project only, so it follows the same rule with no change. The product (`web/pages.py` line 782) already holds this reading.
  4. **Check 4, the failure paths.** Empty: a task with no comments and one with many get the same sentence, so no extra form is needed (a project with no tasks keeps its own form). Stale: a count of comments would be the page as loaded and could be out of date when a comment is added in another tab; not counting them removes that case, where the project's count stays covered by the completion line reading the count when the action ran. Concurrent: a comment added between load and confirm goes with the task and was never counted, which is the same under either reading. Refused: the failure sentence says nothing was changed and does not depend on a count. **Not covered:** a reader who does not know comments go with a task is not told so by the sentence. The comments are on the same page beside the Delete task control, and the second sentence says the step can't be undone. If operators are surprised, the first change is the UXD's data list in UX-F9, not a new rule here.
  5. **The other reading, and what tipped it.** I was close to "comments count, with their own form for a task with none". The tipping facts were that it needs a data item the UXD does not list, that it changes a shipped, tested sentence, and that it would count comments on a project's tasks too, to be consistent, making the project sentence three clauses long. None of that serves a reader who can see the comments on the page.
  6. **What the fold writes.** The first sentence of the formula states what the count is of and what goes with the thing without being counted; the examples stand. The wording is `product-content`'s.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
