# Self-answer report — DESIGN.md

## Header

- **Companion:** products/tracker17/docs/DESIGN_open_issues.md
- **Document:** products/tracker17/docs/DESIGN.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-20
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Everything it leans on was read in this repository on 2026-10-20: `DESIGN.md` (version 3), `UXD.md` UX-I1 and UX-I2, `web/style.css`, `web/pages.py`.

## Items worked

### 3.1 — The confirm-strip's height on the task page

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the design language
- **Verdict:** confirmed with addition
- **Why:** The strip's height follows the button it replaces, and the § Components sentence that ties it to "a task row" versus "elsewhere" is the defect. The item's "If a document has to be written" line is a draft, so I weighed it rather than answering from scratch, and it holds.

  *Seat.* The edit lands in `DESIGN.md` § Components, the document this companion belongs to. It binds only that document's own consistency, and I can name no ground the owner holds that I can't see. So it is mine to answer in the owner's seat. It is one question and does not split.

  *Not a widening.* The item fixes a contradiction, so it corrects a statement and does not ask the document for a new case. It also cites its occurrence: the move to `cancelled` on the task page. So "not until it occurs" does not apply.

  *Check 2, the draft.* The contradiction is real. `DESIGN.md:452-453` makes {components.button-move} {spacing.row-control} tall "on a task row or on the task page", and `DESIGN.md:458-461` says the strip's sentence and confirming button take "the first button's height", then that "That height is {spacing.row-control} in a task row and {spacing.control} elsewhere". On the task page, the first sentence gives 28px and the second gives 36px. The draft keys the rule to the replaced button, which settles it. That is also the reason the document already gives: RN-25 says "The height is the first button's height token, so the confirmation does not shrink the spot a second click would land in", and UX-I2 says the sentence "covers the whole spot the first button stood in". The row/elsewhere sentence was a shortcut that held only while move buttons sat in rows alone. So only that one sentence moves. RN-25 and the Traceability row's "at the first button's height" already say the right thing.

  *The addition.* The rule binds the sentence and the confirming button only. The back-out control stays a full-size {components.button-secondary}, as the same bullet names it, and the stylesheet does this already (`web/style.css:310-311`, `button.button-secondary` at 36px). Without that clause, "the strip takes the height of the button it replaces" could be read as shrinking the back-out control to 28px as well. That would change a component contract the item never asked about.

  *Check 3.* Nothing settled moves. No token value changes. UX-I2's order, focus and coverage rules are untouched. The product already behaves this way: `web/pages.py:639` sets `TRIGGER_SIZE = "row-control"` for the one strip built today, the cancellation, on both the list and the task page, and `web/style.css:228-231` makes `button.move-button` 28px in both places. So the fold corrects the document to match the code, and no change unit is owed.

  *Failure paths.* Empty and absent: a task in `done` or `cancelled` has no move buttons (UX-I1), so no strip opens and the rule has nothing to size. A strip whose first button is a full-size {components.button-secondary}, Delete project's or Delete task's first press, takes {spacing.control}. No such strip exists in the code yet (`confirm_strip` has one caller, `_cancellation_strip`), and the rule covers it when one is built. Narrow window: the sentence is "at least as tall" as the first button and may wrap taller. The rule sets a floor, so wrapping still holds. Stale: if a future confirmation's first button is some third component, the rule still gives an answer, which is that button's own height token. That is the reason to key the rule to the button and not to a list of places.

  *Close call.* The alternative was to keep the place-based wording and add "or on the task page". That fixes today's case but fails again the next time a move button is placed somewhere else. Keying the rule to the button is the one wording that cannot drift from {components.button-move}.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/DESIGN.md** — `<CORE>/launchers/skill/launcher.sh product-design tracker17`
