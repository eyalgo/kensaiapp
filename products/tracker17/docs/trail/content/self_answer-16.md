# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-28
- **Sources re-read:** W3C, Understanding SC 2.5.3 Label in Name (https://www.w3.org/WAI/WCAG22/Understanding/label-in-name.html), re-read 2026-10-28. It says "the name contains the text that is presented visually", so extra words in the name are allowed, and it calls the label at the start of the name a best practice and not a requirement. The answer rests on the first half: a suffix keeps the visible label inside the name.

## Items worked

### 3.1 — Two move buttons for two tasks with the same title get the same accessible name

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** answered
- **Why:** The section should say what tells same-titled tasks apart, and the answer is the position suffix the title link already carries: ", number {position} on the task list" at the end of the accessible name of every control that acts on a list row's task. The item is this document's own question, so the answer goes in its slot and no upstream companion is raised.
  1. **The item is a widening, and it cites its occurrence.** `CONTENT.md` § Accessibility of text, first rule, says the accessible name "adds the thing the control acts on" and names every example task by title alone. Nothing says what applies when titles repeat. The item cites product sites where the form is present now: the move button's name is built from the title alone (`web/pages.py`, the `aria-label` beginning "Move '" in `_move_forms`), the title link on the same row already carries the suffix (`web/pages.py`, `aria-label="{title}, number {position} on the task list"`), and titles repeat by design (`docs/fdr.md` R-40, "Titles need not be unique"). I re-read all three; each says what the item says it does. So the prompt's rule that a widening waits until it occurs does not apply, and the item is taken.
  2. **Why the suffix and nothing else.** The reader needs a name that tells two rows apart in words. A task's internal identifier is not something the reader sees, and the document names no identifiers. The row's position is what the title link already uses, with a test pinning it (`tests/integration/test_task_pages.py`, `"Spaced, number 2 on the task list"`). Reusing it keeps one way to tell same-titled tasks apart and no second one.
  3. **Why on every list row and not only on a title match.** A rule conditional on a match would change a button's name whenever another task was added or a title was edited, and it would have to decide what counts as the same title (case, spaces, quotes). The title link is unconditional today, so the unconditional rule is the one the product already follows. I was close to the conditional form and the tipping fact was that cost.
  4. **Check 3, against the document.** The suffix keeps the visible label inside the name, as the section's own label-in-name rule and WCAG 2.2 SC 2.5.3 require (source above). The title link's name already starts with its visible text. The same title on two rows is also what the section's rule "Two links to different places never share their text" would otherwise catch, so the answer states that the link keeps its suffix. The comma is not banned in § Grammar and mechanics, and a numeral is the form that section sets for numbers.
  5. **Check 4, the failure paths.** Empty: one row still gets "number 1", which is what the title link does. Absent: on a task's own page one task is shown and nothing repeats, so the title alone stands. Stale: the position is the one the page shows when it is built, and pages do not update themselves (UXD UX-I9), so the name is true for as long as that page is read. Concurrent: two same-titled tasks have two positions. Refused: a refused move rebuilds the page and the names are rebuilt with it. Not covered: a list sorted or filtered differently on the next visit numbers its rows differently, which is the same property the title link has, and the position names the row on the page in front of the reader, not the task.
  6. **The cancel confirmation is left alone.** Its sentence "Move '{title}' to cancelled? …" is visible text and not an accessible name. Only one confirmation is shown, because the interaction applies to one task (`web/pages.py`, `interaction.task_id == row.task.id`), and UXD UX-I2 puts it in the pressed button's place with focus on the sentence. The item cited it as a second ambiguous name; it is not one, and the answer says so in its slot.
  7. **The product does not yet meet the rule.** The move button's name carries the title alone. By the document's own convention (RN-23, RN-26, RN-27) that is a finding for a change that publishes text, not an edit in `CONTENT.md` and not something this run writes.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
