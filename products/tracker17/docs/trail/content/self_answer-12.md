# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-21
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Everything it leans on was read in this repository on 2026-10-21: `CONTENT.md` (version 12), `UXD.md` (version 8, Settled), `SDD.md` (version 11, § 6 `status-moves`), `PRD.md` (§ Core Features, Status workflow), `products/tracker17/web/pages.py`, `products/tracker17/web/routes.py`, `products/tracker17/tests/integration/test_move_routes.py`, and the trail entries `trail/content/self_answer-9.md` and `self_answer-11.md`. I read the code and ran no request against it.

## Items worked

### 3.1 — The out-of-date refusal example still offers a reload that no refusal may offer

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** confirmed with addition
- **Why:** Yes, the fifth example is out of date and is replaced. The item carries a lean ("the example should show the no-reload form, naming the moves"), so I weighed it as a draft, and it holds.

  *Seat.* The edit lands in `CONTENT.md` § Message patterns, Error, *A refusal*. It binds no person and no outside party, and I could name no ground the owner holds that I can't see. It is mine to answer in the owner's seat.

  *It is a correction, not a widening.* The document already states this case, as example 5, and the example is false against the settled record. So § *A widening item waits until it occurs* does not apply, and the item also cites the product's line (`web/pages.py:L751-L756`).

  *Check 2, the draft.* The conclusion holds and rests on the right reason. UXD version 8 says an overtaken move says the status has changed, names the moves the page now shows or none for a final status, and offers no reload, because the page it lands on is built after the refusal (UX-F4 `UXD.md:L176-L180`, UX-I3 `UXD.md:L370-L386`). SDD version 11 § 6 `status-moves` says the same (`SDD.md:L881-L885`). The draft is right and incomplete: three things follow from the replacement that the item did not carry.

  *Addition 1, the formula.* § Message patterns, Error says a refusal gets "then one action where one exists". The replacement examples name the moves the page shows, which is not one action. Left alone, the examples contradict their own formula, and my own answer in `self_answer-9.md` (no action where the wanted state already holds) would read as the only exception. So the formula gains a clause: for a move another change overtook, the second sentence names the moves the page now shows, or says there are none for a final status. This stays inside the formula's two-sentence limit.

  *Addition 2, "since this page loaded".* The banned-words row for "another tab" and RN-11 give "since this page loaded" as the replacement. For this refusal it is now wrong: the page the refusal lands on is built after the refusal, so the phrase claims the opposite. The product's line does not use it (`web/pages.py:L751`). Both places are revised to a form that doesn't date the page.

  *Addition 3, RN-24.* RN-24 says UX-I3 "still says" an out-of-date refusal offers a reload and that this is raised on `docs/UXD_open_issues.md` item 2.1. Both statements are false now: UXD version 8 says no refusal offers a reload on a page built after it, and that earlier item was folded and removed. A fact in the document that is now false is the strongest ground for a change, so RN-24 is corrected here and not left for a later item.

  *The examples.* Two forms replace the one, each of which the product's tests pin (`tests/integration/test_move_routes.py:L87-L99`): a non-final status with two moves, and a final status with none. Every sentence is under 20 words, ends with a full stop, uses contractions and starts with "The" or "A", so none starts with a status word.

  *Check 3.* My earlier answers in this document: item 3.1 of cycle 9 (`self_answer-9.md`, a refusal gives no action where the wanted state already holds) and item 3.1 of cycle 11 (`self_answer-11.md`, a refusal reached without a press). Neither contradicts this one. This answer extends the first to the opposite case, where the wanted state does not hold and the moves are the way forward. It also depends on item 3.2: the examples carry "has changed to", which the UXD half of 3.2 questions for a visit with no press. If the CDO drops that wording, these examples move again, and I said so in the slot.

  *Check 4.* Final status: no moves, "can't be moved". One, two or three moves: the product writes four forms, `_OVERTAKEN_LINES` (`web/pages.py:L752-L757`). The task deleted since the press: the move route redirects to the task's address, which shows the not-found page, a separate pattern. Concurrent: two overtaken presses each get the same line. Stale: the page is built after the refusal, so the line can't be stale on arrival. A later visit is item 3.2's case.

  *Close call.* None. The only other reading is to leave the example and wait for the CDO, and that would leave a false example in a Settled document.

### 3.2 — RN-26's reloaded-press case now occurs, and the occurrence it cites is gone

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** raised upstream
- **Why:** This item holds two questions with two seats, and I split it. This is the remainder, which is the UXD's and is carried on `docs/UXD_open_issues.md` item 2.1. The other half, which is `CONTENT.md`'s, is item 2.1 of this companion, under § 2.

  *Why it is two items and not one.* The item asks (a) whether the line meets the rule when reached with no press, and RN-26's cited occurrence, which is gone, and (b) what the line says instead. They are separable: (a) is answerable without (b). They resolve to different seats: (a) lands in `CONTENT.md` (RN-26), and (b) can't be answered without changing UX-F4's sentence that the reason "says the task's status has changed", which the owner confirmed (`trail/uxd/cycle-6.md` § 2.2). And I hold an answer to (a) that stands without (b). That is the three conditions the prompt sets for a split.

  *What is the remainder, and why it is the UXD's.* The occurrence is real: `web/routes.py:L384-L396` reads `move_refused` from the address on every load, and `web/pages.py:L751-L756` writes "has changed to {status}" from it. The tracker sees only the address, so a reload, Back, a bookmark and the first landing are one request, and one string serves all of them. I checked what that does: `web/routes.py:L353` returns the outcome without reading the task's status, and `web/pages.py:L764-L770` shows the line whenever the address names the task on the page. So an address typed for a task that was never moved prints "has changed to todo". Whatever wording is true on a later visit drops "has changed" on the press too, because the press and the later visit can't be told apart. That is a change to a settled, owner-confirmed UXD sentence and to the SDD that repeats it (`SDD.md:L881-L885`), whose wording is pinned by tests. It is the CDO's to answer, not the Content Manager's to rewrite, and the item itself says whether the page shows the refusal at all is UX-I3's.

  *The answer I carried.* The lean on the UXD companion is: state what the tracker established, the task's status and what it allows ("The status of 'Set up CI' is done. A task in done can't be moved."), and claim no change. The alternatives are to keep "has changed" and accept that a later visit repeats it, or to hide the refusal on a later visit, which needs a mechanism the product lacks. I could not reach a verdict on the choice from the files, and the lean is only that.

  *Close call.* I considered answering (b) here under the Content Manager's remit to replace a message that asserts what the system can't establish with the smaller true thing, as RN-11 did with "another tab". What tipped it was that the departure would be from a sentence the owner confirmed in the UXD, and that the SDD's tests pin the string. The check against the settled record sends it upstream.

  *Not left for the owner.* Nothing in it is a risk, a commitment or a taste the owner reserved. `CONTENT.md` keeps its current wording and examples until the CDO answers. Check 4: Empty, absent, stale, concurrent and refused are all the one case of a later visit with no press, and they are the content of the UXD item.

### 2.1 — RN-26 records an occurrence that is gone and says the reloaded case waits, and it doesn't

- **Bucket:** 2. Choices to confirm
- **Verdict:** answered
- **Why:** This is the answered half of item 3.2, moved out of it as the split requires, and appended to § 2 with its confirm-or-override slot at its placeholder. The reasoning is this run's and the decision is the next round's. The answer: yes, the line doesn't meet the rule when reached with no press, because "has changed to" is a claim about the past that an address can't back; and RN-26's cited occurrence is gone (`grep -rn "the move you pressed" products/tracker17/web` prints nothing on 2026-10-21; the cancellation-address line is now `_ADDRESS_LINE`, which meets the rule), while the case it said waits now occurs. RN-26 is revised in four places and the formula and the examples don't change. The rule's reach, "by a reload, Back, or a saved or typed address", already includes the reloaded page, so the finding is that the product's line breaks the rule and not that the rule has a gap. The remainder of item 3.2 is carried to the UXD, as the entry above says. I added this item once and made no second split of it.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

- **products/tracker17/docs/UXD_open_issues.md** — **opened** — companion to `UXD.md`, landed in commit `feb76b2d9`

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/companion-self-answer/launcher.sh tracker17 UXD`
