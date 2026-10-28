# Self-answer report — UXD.md

## Header

- **Companion:** products/tracker17/docs/UXD_open_issues.md
- **Document:** products/tracker17/docs/UXD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-28
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Everything it leans on was read in this repository on 2026-10-28: `UXD.md` (version 10, Draft) whole, `trail/uxd/cycle-8.md` and `trail/uxd/self_answer-8.md`, `CONTENT_open_issues.md` (item 3.1, unrelated), `CONTENT.md` (searched for the off-list lines and for "Clear" and "Try again"), `products/tracker17/web/pages.py:L840-L920` (`_NOT_LISTED_CLEAR`, `_NOT_LISTED_ABSENT`, `_OFF_LIST_FAILURE`, `_OFF_LIST_REFUSALS`, `_OFF_LIST_ADDRESS`, `_off_list_line`) and `L1455-L1560` (where both list pages place that line), and `tests/integration/test_filter_move_routes.py:L227-L295`. I read the code and ran no request against it.

## Items worked

### 1.1 — Where a pressed move's refusal or failure goes when the filter leaves the task off the list

- **Bucket:** 1. Open issues — experience questions with no answer yet
- **Verdict:** confirmed with addition
- **Why:** The CDO's reading holds, and I added two things to it. The line goes above the results, in UX-I4's line, as RN-36 already places the refusal reached by an address. A refusal names the task, its status and the moves that status allows. It names Clear where a move is still possible, and names no action where the status is final. A failure names the task, the move that failed and Clear. The first addition: the line names the filter area's existing Clear, adds no control of its own, and offers no reload. The second: a failure line does not state the task's status.

  *Bucket.* The item sits under open issues, but it carries a lean ("My reading, for you to take or replace"). So I weighed it as a draft, not from scratch, as the prompt says to do for a bucket-1 item that has a lean.

  *Seat (check 1).* The edit lands in `UXD.md`: UX-F4, UX-I3, UX-S4 (UX-S7 takes it "As UX-S4") and UX-A3. It is a question about where a line sits on a page this document defines. It binds no person, money or outside party, and I can name no ground the owner holds that I can't see. So it is mine to answer. The words are `CONTENT.md`'s, and the item says so. That does not split the item, because the item asks where the line goes and what it carries, not how it is worded.

  *The draft (check 2).* The gap is real. UX-F4 gives "It offers no reload" because the page "already shows the task's current status and the moves that status allows", and UX-I3 puts every refusal "beside the control that was used". A status or Overdue filter can leave the task off the list after a move made in another tab, and then neither holds: there is no row, no control and no status on the page. The draft's argument holds: the line above the results is the one place on a list page that is about the page and not a row, and RN-36 already uses it for this situation. It also holds for its stated reason. UX-I3 says a refusal "names what is left to do on the page it lands on". On that page, what is left is to show the task, and Clear is the one control that does. The product does the same (`_OFF_LIST_REFUSALS`, `_OFF_LIST_FAILURE`, pinned by `test_off_list_refusal_and_failure_remain_visible`).

  The draft was right but did not cover two cases, which is why this is *confirmed with addition*:
  - **Whether "names Clear" adds a control.** The draft does not say. It does not, and the answer says so: the line names the Clear button in the filter area, which UX-F5 always shows. A second Clear inside the line would add a control for no case Clear does not already cover, against PRD § Goals, It is simple. The product's line is text only. No reload either, by UX-I3's own rule: the page is built after the press (UX-I9), so it is not out of date, and only the task is out of view.
  - **What a failure line carries.** The draft says "naming the task and its status, and the moves that status allows" for every case, and then treats the failure separately. A failure is not about the status: the rules allowed the move and the save failed (UX-I5). So the failure line names the task and the move that failed and says nothing was changed. Stating the status as well would read as the cause of the failure. The product's failure line does the same.

  *The settled record (check 3).* Nothing settled has to move. UX-I3 already says a refusal names what is left to do "where something is left for the operator to do". This answer applies that rule to a page that does not show the task. The final-status case agrees with RN-36: it names no action and no Clear, because even with the task shown nothing is left to do. The product shows the same split: "so it isn't in this list" for a final status, "so press Clear to see it" otherwise. UX-A3 asks that a refusal be "associated with the control it concerns". With no control and no status on the page, the line meets that by naming the task, and for a refusal its status, as RN-36 already reads it. UX-A5's announcement without moving focus is unchanged. `CONTENT.md` gives "one next action when one exists, and none when none does" (§ Voice, line 55), and the answer follows it. `CONTENT.md` has no pattern for these lines yet. That is for its own seat, not a change this answer owes it. The answer also agrees with RN-36 from the previous round (`self_answer-8.md`), which turned down Clear for the final-status case on the same grounds.

  *The failure paths (check 4).*
  - **Empty:** the filter leaves no rows. The line sits above the no-match state, which already shows Clear (UX-S4). The line and the no-match state name the same control.
  - **Stale:** a reload, Back or a bookmark shows the page again. UX-I3 says the line states what holds when the page is built, so the status and moves it names are read at that moment. If the task became final in the meantime, the line no longer names Clear. If the task matches the filter again, it has a row, and the line goes back beside its status (UX-F4). The product computes both when it builds the page (`_off_list_line`, `_has_move_line`).
  - **Concurrent:** another tab moves the task again before the operator presses Clear. Clear opens the plain list, built from the saved data, and the row shows whatever status the task holds then. Nothing in the line is relied on after Clear.
  - **Refused / absent:** a failure changes nothing (UX-I5), and the line says so.
  - **Not covered:** two cases next to this one, neither in the item and neither with a cited occurrence. (a) A task deleted in another tab, then pressed from a filtered list. (b) A confirmation address for a move to `cancelled` opened again when the task is off the list but not final. The product shows no line for (b) (`test_stale_off_list_confirmation_address_shows_current_workflow_refusal`, the "shows nothing" half). I name both here and raise neither, by § *A widening item waits until it occurs* and because neither is a fact in the UXD that is now false.

  *Close call.* The other answer I weighed was to send the operator to the task's own page, which always shows the status and the moves and keeps the filter, instead of to Clear, which drops it. What tipped it: the task's page is not on the page the refusal lands on, and a link to it would add a control. Clear is already there, and the product already uses it. If the owner would rather keep the filter, the change is to name the task's page in place of Clear. The placement stays the same either way.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/skill/launcher.sh product-uxd tracker17`
