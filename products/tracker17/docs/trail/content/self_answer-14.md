# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-21
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Everything it leans on was read in this repository on 2026-10-21: `products/tracker17/docs/CONTENT.md` (version 14), `UXD.md` (version 8, Settled), `docs/UXD_open_issues.md` (item 2.1, answered), `docs/trail/uxd/self_answer-7.md`, `docs/trail/uxd/cycle-6.md` § 2.2, `docs/trail/content/self_answer-13.md`, `products/tracker17/web/pages.py` (`_CHANGED`, `_OVERTAKEN_LINES`, `_ADDRESS_LINE`), `products/tracker17/web/routes.py` (`_move_outcome`) and `tests/integration/test_move_routes.py`. I read the code and ran no request against it.

## Items worked

### 3.1 — What the page a refused out-of-date move lands on says when it is opened again with no press

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** answered
- **Why:** The page states the task's current status and what that status allows, and claims no change. `CONTENT.md` follows the CDO's answer to the same question, and the slot lists the places the fold changes. The item carries a lean, the CDO's, and I weighed it as a draft.

  *Why the last answer settled nothing, and this one does.* The earlier run (`self_answer-13.md`) said "raised upstream" because the CDO's answer did not exist yet. That verdict is right while the question is open upstream and gives this document nothing to fold, which is why the PM re-raised the item. The CDO's seat has now answered: `docs/UXD_open_issues.md` item 2.1 holds "confirm, with two additions", option (a), reasoning in `docs/trail/uxd/self_answer-7.md`. With that answer on disk, the wording standard here is mine to state, and it is the same sentence.

  *Seat (check 1).* The edit lands in `CONTENT.md`: the overtaken-move clause in § Error, its examples, the banned-words row in § Voice, and RN-26 and RN-27. It binds no person and no outside party, and I could name no ground the owner holds that I can't see. The UXD half, UX-F4's and UX-I3's words, is the CDO's and is carried on their companion, so this is one question with both halves answered the same way and not a split. The item does not widen the document: the page it asks about is one the document already has a clause for, and the occurrence is the product's own line (`web/pages.py` lines 751 to 757).

  *Check 2, the draft.* The lean holds, and for a reason stronger than the item gives. The address carries the task and the refusal code only (`_move_outcome` in `web/routes.py` reads `move_task`, `move_refused`, `move_failed` and `moved`). It carries no target move and no earlier status. So "has changed to {status}" is a claim about the past the tracker can't back on any visit but the first, and not reliably then. `CONTENT.md` § Voice says "State only what the tracker established", and RN-11 already replaced "another tab" for the same reason. A bare statement of the status and the moves it allows is true on every arrival.

  *Check 3.* It contradicts two things written in this document and one in the UXD. In this document, § Error, the two examples, the banned-words row, the rationale line and RN-27 say "has changed to". They were written on the condition that the CDO had not answered, and RN-26 and RN-27 say so; my earlier answers (`self_answer-12.md`, `self_answer-13.md`) kept them only until the CDO answered, so the earlier ones don't move. In the UXD, UX-F4 still says the reason "says the task's status has changed" until `product-uxd` folds item 2.1. I treat that as unsettled ground under `unsettled_inputs.md` and answer best-effort. The item calls that UXD sentence one the owner confirmed. The sentence came in through `cycle-6.md` § 2.2, which a self-answer run answered, and the question it settled was the reload, not the words "has changed". So no owner call on those words is overturned. The refusal formula's clause "where the address carries one" stays: this page's address carries no move, and the new line names none.

  *Check 4.* Empty: a typed address for a task never moved shows the task's status and its moves, which is true. Absent: a deleted task goes to the not-found page, a separate pattern. Stale: the status changed again between visits, and the line names the status the page reads when it is built. Concurrent: two tabs pressing the same move show the same line, true of the task now. Refused, from a tampered form: today's line says "has changed to" even on the press; the new one is true there too. Not covered: on the first landing the line no longer says the press was refused. It still sits beside the status and the buttons as the refusal, and the status it names is not the one the operator pressed from. That is the cost the CDO accepted, and I take it.

  *Close call.* A fourth option, carrying the pressed move in the address so the line can name the refused move as `_ADDRESS_LINE` does. It would be true on every visit, but it adds a field to the address and changes to the SDD and the tests for words the status already conveys, and it is a design call that is not this document's. If the owner wants it, it overrides this answer and the CDO's.

  *Order.* The fold reads the UXD, so `product-uxd` should fold item 2.1 first. If `product-content` runs first, the fold records the UXD as Settled version 8 and the departure is visible in the header, as the doctrine intends.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
