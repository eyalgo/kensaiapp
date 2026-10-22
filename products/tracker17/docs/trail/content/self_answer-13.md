# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-21
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Everything it leans on was read in this repository on 2026-10-21: `products/tracker17/docs/CONTENT.md` (version 13), `UXD.md` (version 8, Settled, UX-F4), `docs/UXD_open_issues.md`, `docs/trail/uxd/cycle-5.md` § 2.1, `docs/trail/content/self_answer-12.md`, `products/tracker17/web/pages.py`, `products/tracker17/web/routes.py` and `tests/integration/test_move_routes.py`. I read the code and ran no request against it.

## Items worked

### 2.1 — RN-26 records an occurrence that is gone and says the reloaded case waits, and it doesn't

- **Bucket:** 2. Choices to confirm
- **Verdict:** confirmed with addition
- **Why:** The four drafted changes to RN-26 hold, and three things are added. The draft is a proposal from the earlier run (`self_answer-12.md`), so I put it through the four checks.

  *Seat.* The edit lands in `CONTENT.md` (RN-26 and § Error). It binds no person and no outside party, and I could name no ground the owner holds that I can't see. It is mine to answer in the owner's seat.

  *Check 2, the draft.* Each drafted fact checks out against the files today. `grep -rn "the move you pressed" products/tracker17/web` prints nothing (exit 1). The cancellation-address refusal is now `_ADDRESS_LINE` (`web/pages.py` lines 758 to 761, "The status of '{title}' is {status}, which doesn't allow a move to cancelled."), and it meets the rule. The overtaken-move line is shown from `move_refused`, which `_move_outcome` in `web/routes.py` reads on every load. `_move_view` returns the outcome as soon as it holds a refusal, and `_has_move_line` in `web/pages.py` checks only that the outcome names the task on the page. Nothing compares the address with the task's status, so an address typed for a task never moved shows "has changed to todo". The draft's conclusion rests on the right reason, § Voice, "State only what the tracker established". The earlier UXD item 2.1 was folded into UXD version 8 (UX-F4, `docs/trail/uxd/cycle-5.md` § 2.1), so the pointer to it as pending is false.

  *Addition 1, the citation.* The draft and RN-27 cite the overtaken-move wording at `web/pages.py` lines 751 to 756. `_CHANGED` is line 751 and `_OVERTAKEN_LINES` runs to line 757. The slot gives the corrected range.

  *Addition 2, the pointer.* The draft drops the pending pointer but not the sentence beside it. RN-26 also says "Whether it does is the UXD's call" and "if the CDO removes the refusal the clause goes with it". UXD version 8 keeps the refusal in UX-F4's second way in, so both go. The settled case to cite is UX-F4 and the trail entry.

  *Addition 3, the formula.* This is the case the draft's argument did not reach. § Error says a refusal reached with no press "names the move the address asks for". The cancellation address carries a move, and the overtaken page's address does not. `_move_outcome` reads only `move_task`, `move_refused`, `move_failed` and `moved`. The overtaken page can't meet that clause, and the document's two statements about it (the overtaken-move clause in § Error and the no-press clause) disagree for that page until the UXD answers. The formula gains "where the address carries one", and RN-26 says which rule governs and why one line serves both arrivals. The cancellation example is unaffected.

  *Check 3.* My earlier answers in this document are `self_answer-9.md` (no action where the wanted state holds), `self_answer-11.md` (a refusal reached without a press) and `self_answer-12.md` (the overtaken-move examples). None contradicts this one. Item 3.1 below was decided with this item: the wording that fits both arrivals is the CDO's, and RN-27's "has changed to" examples move again if the CDO drops that wording.

  *Check 4.* Empty: a task with no move left is the final-status form. Absent: a deleted task redirects to the not-found page, a separate pattern. Stale: a reload is the case in question. Concurrent: two overtaken presses show the same line. Refused: covered by the pinned wording in `tests/integration/test_move_routes.py` ("SUBMISSION_FOR" and "ADDRESS_FOR").

  *Noticed, not raised.* RN-23 says the date refusal "ends 'Pick one'" at `web/pages.py:276`. The string is now at line 523 and reads "Pick one, or leave the due date empty." It still breaks the rule RN-23 states, so the finding holds and only its place and ending moved. RN-16 already says a named file is not a promise that strings stay put. A reader finds it by searching "Pick one", so I judged it not worth a cycle.

  *Close call.* None. Overriding would leave RN-26 citing a refusal the product no longer writes.

### 3.1 — What the page a refused out-of-date move lands on says when it is opened again with no press

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** raised upstream
- **Why:** The change is the CDO's and is already written on their companion, so the slot says it is carried there and gives my answer. This item is the remainder of an earlier item that held two questions, and the other half is item 2.1 above (decided with this one). The item carries a lean ("state the task's status and what it allows, and claim no change"), and I weighed it as a draft.

  *Seat.* Where would the edit land? In `UXD.md`: UX-F4's sentence that the reason "says the task's status has changed", which the owner confirmed (`docs/trail/uxd/cycle-6.md` § 2.2), and UX-I3. The SDD § 6 `status-moves` and its tests repeat the wording. A `CONTENT.md` edit alone can't settle it, because one string serves the first landing and every later visit. The item binds no person and no outside party, and I could name no ground the owner holds that I can't see. It is the CDO's, not the owner's.

  *Where it is written.* `docs/UXD_open_issues.md` item 2.1 holds this change, with its slot at its placeholder. An earlier self-answer run opened that file and committed it as `feb76b2d9` (`git log --oneline -1 feb76b2d9` prints it). I didn't revise the item. Its facts hold, apart from the line range `web/pages.py` 751 to 756, which is a slip of one line and not worth a cycle.

  *Check 2, the draft.* The lean is right and I take it as the answer: state the status and what it allows, and claim no change. The reason it holds is stronger than the item gives. The address carries the task and the code `not_allowed` only (`_move_outcome` in `web/routes.py`). It carries no target move and no earlier status. So any wording that says the move isn't allowed is false for an address typed for a task in `todo`. A bare statement of the status and its moves is true on every arrival.

  *Check 3.* The answer would replace an owner-confirmed UXD sentence, which is why it goes upstream and isn't written into `CONTENT.md`. It doesn't contradict item 2.1: `CONTENT.md` keeps its wording and examples until the CDO answers.

  *Check 4.* The cost of the lean: the line no longer says the press was refused, and on the first landing a reader who pressed `todo` and sees `in-progress` is left to read the status and the buttons. Both are on the page. Final status: "can't be moved". Concurrent presses show the same line. Task deleted since: the not-found page, a separate pattern.

  *Close call.* I considered answering the wording in `CONTENT.md` under the seat's duty to replace a message that asserts what the tracker can't establish, as RN-11 did with "another tab". What tipped it was that the departure is from a sentence the owner confirmed in the UXD.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/companion-self-answer/launcher.sh tracker17 UXD`
