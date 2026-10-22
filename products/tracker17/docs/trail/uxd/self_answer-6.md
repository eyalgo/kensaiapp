# Self-answer report — UXD.md

## Header

- **Companion:** products/tracker17/docs/UXD_open_issues.md
- **Document:** products/tracker17/docs/UXD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-20
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Everything it leans on was read in this repository on 2026-10-20: `UXD.md` (v7, Draft), `CONTENT.md` (v12), `SRS.md` NFR-3, `SDD.md` (`status-moves`, `tasks-in-a-project`, and the change record that names UXD v6), `nfdr.md`, `DESIGN.md` § Focus, `docs/trail/uxd/self_answer-5.md`, `docs/trail/uxd/cycle-5.md`, `products/tracker17/web/routes.py` and `products/tracker17/web/pages.py`.

## Items worked

### 2.2 — UX-F4 says a refused status move offers a reload, and the page that refusal lands on is already up to date

- **Bucket:** 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The overtaken status move offers no reload, as the draft says. The two assignee refusals UX-I3 names in the same sentence go the same way, and UX-I3's reload sentence becomes conditional, because no refusal on this interface is left showing on a page that is still out of date.

  *Seat.* Every edit lands in `UXD.md`: UX-F4, UX-F3, UX-F9 and UX-I3. The answer binds no person, no outside party and no risk the owner carries. It is the document's agreement with its own RN-32 and with what the interface does. I could name no ground the owner holds that I cannot see. The item's heading is about the move only. The `product-uxd` run's added field makes the assignee refusals part of it ("Whether their reload holds, by RN-32's reason, is part of this item"). So the draft answers a smaller question than the item now asks. Both questions have the same seat, so the item does not split, and I answer both in the one slot.

  *Check 2. The draft holds, for the reason it gives.* `web/routes.py` `_move_task` answers a refused move with a redirect to the place the button was on: the project's page for a list row, the task's page otherwise (the `MoveNotAllowed` branch, and the first-press refusal for `cancelled` above it). That page is built when it loads, so it shows the task's current status and the moves that status allows. A reload builds the same page. The product's line already ends without one: "The moves shown are the ones you can press." for `todo` and `in-progress`, and "A task in done can't be moved." for a final status (`web/pages.py`, `_REFUSAL_TAILS`). The previous round's reason for keeping the reload, "A refusal shown on the page the operator acted from would still owe a reload" (`docs/trail/uxd/self_answer-4.md` § 2.1), rested on a page the interface never shows.

  *Addition 1. The assignee refusals.* A refused add redirects to the project's Tasks view with what was typed in the address (`web/routes.py` `_add_task`). That page's assignee control is built from the current list. A name no longer listed is not offered and the control falls back to unassigned, while the title, priority and due date are kept (`web/pages.py` `_add_task_form`). A refused edit redirects to the task's page (`_edit_task`). That page offers the current listed names and shows the refused name only as the failed choice: "A refused name is echoed as the failed choice only; it is never an eligible one" (`_edit_form`). Both pages are up to date with the list, so by RN-32's reason ("A reload offers something only on a page that is still out of date") a reload shows nothing new. Worse, both lines link to the page's plain address, which drops what was typed. That works against UX-I3's "Everything the operator typed stays in the form" for an operator who follows the link. Something is left to do: pick another assignee, or none. UX-I3's "names what to do" therefore holds for these refusals, and what it names is that pick. UX-F3 and UX-F9 keep their refusals, and UX-I3 stops naming them as reload cases.

  *Addition 2. UX-I3's reload sentence.* With the move and both assignee refusals gone, "A refusal caused by the page being out of date, because another tab changed or moved the task, says so and offers a reload" has no case on this interface. The label and People refusals are already its exception, and RN-33's address case is its own case. Every refusal here lands on a page built after it, because every submission is answered by sending the browser to a page address (`SDD.md` § 4 RT-8). I am keeping the sentence rather than deleting it, restated as a condition: the refusal says the page was out of date and names what is left to do on the page it lands on, and it offers a reload only where the page that shows it is itself still out of date. That is RN-32's own reason stated as the rule. It keeps the UXD from depending on a redirect the architecture chose. RN-17's reason for the out-of-date refusal still holds, because an address can outlive what it names and the refusal still says so.

  *Check 3.* Nothing settled needs the reload. SRS NFR-3 says an action no longer valid "is refused under FR-39 with the reason", and its "The operator reloads the page to see the current state" is about seeing another tab's changes (UX-I9), not about what a refusal offers. RN-32 and RN-33 agree, and so does my earlier answer, 2.1 (`self_answer-5.md`): no refusal offers a reload on a page built after it. The answer reaches four downstream places, and none of them is this document. I opened no companion for them, because the UXD has not changed yet. They see it when they next read UXD v8. (a) `SDD.md` `status-moves` says a move from an out-of-date page "offers a reload (UX-I3)". `SDD.md`'s change record also names the overtaken move and the assignee refusals as the cases that "still offer one". (b) `CONTENT.md` § Message patterns, *A refusal*, carries the example "The status of 'Set up CI' has changed since this page loaded. Reload the page to see it." (c) `DESIGN.md` § Focus names "the refusal around the reload control it offers" as a focus ground. (d) The product's two assignee lines (`web/pages.py` `_task_reason`, `_edit_reason`) offer a reload. That is a finding for a change that publishes text. The `nfdr.md` change record says no obligation names UX-I3's reload, so the NFDR is not reached.

  *Check 4.* Empty: with an empty assignee list the add-task control offers only unassigned, beside the note that links to People (`_add_task_form`), so "pick another or none" still names a real action. Absent: a task deleted in the meantime gives UX-S10, not this refusal (`_move_task`, `_edit_task` → `TaskNotFound`). Stale: the page the refusal lands on can go out of date again if a third change is made in another tab. The next press is then refused the same way, on a page built after it, so the rule still holds. Concurrent: two tabs pressing the same move: the second is refused and lands on a page showing the first's result. Refused: this is the refused case. *Named and not covered:* a refused move pressed on a status-filtered list redirects to the project's plain address (`_move_task`, `place`), so the filter is not kept. I did not check what UX-F4's filtered-list sentence then means for a refusal. That is not this item, and I raise no change for it.

  What would have tipped me to override: the owner ruling that every out-of-date refusal offers a reload whatever page it lands on, as a fixed reassurance. RN-32 already rejects that reading ("the only action left is a reload that shows nothing new").

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/skill/launcher.sh product-uxd tracker17`
