# Self-answer report — UXD.md

## Header

- **Companion:** products/tracker17/docs/UXD_open_issues.md
- **Document:** products/tracker17/docs/UXD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-20
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Everything it leans on was read in this repository on 2026-10-20: `UXD.md` (v6, Settled), `CONTENT.md` (v12), `PRD.md` § UX Notes, `docs/trail/uxd/self_answer-4.md`, `docs/trail/content/self_answer-11.md`, `products/tracker17/web/routes.py` and `products/tracker17/web/pages.py`.

## Items worked

### 2.1 — A refusal shown on a page the operator reached without pressing: does the interface show one, and what does UX-F4 and UX-I3 say about it?

- **Bucket:** 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The interface keeps the refusal, with no action and no reload. UX-F4's sentence that the refusal "arises only when the task was moved in another tab after the page loaded" is corrected to name this second way in. The draft reached the right answer, but one of its reasons does not hold, and it left out two facts the UXD needs.

  *Seat.* The edit lands in `UXD.md` UX-F4 and UX-I3, which is this document. Whether a refusal appears at all is the interface's behaviour, and the UXD owns that. The answer binds no person, no outside party and no risk the owner carries, and I could name no ground the owner holds that I can't see. The wording is `CONTENT.md`'s and was already folded there (v12, RN-26), with a rule that holds only while the interface shows the refusal. So this is one question with one seat, and it does not split.

  *Check 2. The draft's facts hold.* `web/routes.py:L351-L352` returns the not-allowed refusal when the address asks for the cancelled confirmation and the task's status no longer allows that move. `web/pages.py:L760` writes the line. Only `done` and `cancelled` are final (PRD § Core Features, Status workflow).

  *Addition 1. The real reason.* The draft rests on UX-I3's v6 exception. That exception needs "the state the operator wanted already holds". That is true after a Back that follows a saved cancel, because the task is in `cancelled`. It is false for a task in `done`, because the move to `cancelled` never holds. Read as written, UX-I3 would then demand an action and a reload. The real ground is different. UX-I3's out-of-date clause covers a refusal "caused by the page being out of date, because another tab changed or moved the task". This page was just built from the saved data, so it is not out of date. UX-I3's first rule names an action only "where something is left for the operator to do", and with a final status nothing is. UX-A3 agrees: "where a correction exists". So UX-I3 names the case as its own: a refusal reached by an address and no control states what is true now, names no action and offers no reload, for a task in `done` and a task in `cancelled` alike.

  *Addition 2. The ways in.* The draft names only the confirmation's address (`move_task`, `move_confirm`). The back-out address (`move_back`) reaches the same refusal, because both give an interaction mode (`web/routes.py:L357-L362`) and the check at L351 runs for either. Both reach it on a project's task list row as well as on the task's page, because the list view goes through the same `_move_view` (`web/routes.py:L439`). The item's supporting text is incomplete here. It is not wrong.

  *Addition 3. The place.* No control was used, so "beside the control that was used" (UX-I3) and "the control it concerns" (UX-A3) have nothing to point at. The line sits beside the task's status in that row or on that page. The product already ties it there: on the task page the status element carries `aria-describedby` to the line (`web/pages.py`, `_status_word`).

  *Why keep it, rather than show the plain page.* The address asks for a step, the confirmation, and the page then doesn't show it. With no line, an operator who reloaded or bookmarked that address sees the confirmation vanish with no reason. PRD § UX Notes, Refusals say why rules that out. The other reading, that backing out is a reading action and produces no message (`CONTENT.md` § Voice), fits the Back-after-saved-cancel path, where the status alone already says it all. It does not fit a task in `done`, where the move the operator was about to confirm can never happen. Keeping the refusal also needs no change to the product. What would have tipped me to the override: the owner ruling that a page reached by Back never carries a message, whatever the address asked for.

  *Check 3.* Nothing settled requires the opposite. UX-I9 (pages do not update themselves) agrees, because the page reflects the saved data as it loads. `CONTENT.md` v12 RN-26 already writes the line's rule to this answer: the reason is a fact about the task, there is no action and no reload. UX-I2's confirmation is untouched, because this refusal shows only where the confirmation cannot. This is my only answer this run apart from raised item 2.2. That item changes the reload reasoning for the pressed path and is consistent with this one: neither case offers a reload on a page built after the refusal.

  *Check 4.* Empty: an address naming no task gives UX-S10, through `web/routes.py:L346-L347`. Absent: the same. Stale: a final status never changes, so the line can't go stale. A task in `todo` or `in-progress` allows the move, so the confirmation shows and no refusal is reached. Concurrent: two tabs opening the address show the same line. Refused: this is the refused case. *Named and not covered:* the product's line still says "the move you pressed", which does not meet `CONTENT.md` v12. That is a finding for a change that publishes text, already recorded in `docs/trail/content/self_answer-11.md`, and it is not this document's to fix.

## Left for the owner

None this run.

## Skipped

None this run.

## Raised on this document

### 2.2 — UX-F4 says a refused status move offers a reload, and the page that refusal lands on is already up to date

- **What the document is owed:** UX-F4 drops "offers a reload" from the overtaken-move refusal, and UX-I3 stops naming the overtaken status move as a reload case.
- **Why it is worth a cycle:** It contradicts a document it must agree with, and a fact it rests on is false. `prompts/rich.md` § The items are not the whole of what a document is owed names both grounds. The previous round kept the overtaken move as a reload case because "A refusal shown on the page the operator acted from would still owe a reload" (`docs/trail/uxd/self_answer-4.md` § 2.1, check 4). The interface never shows a refused move there. Both refused-move paths redirect to the list or task page, built from the saved data when it loads (`web/routes.py:L724-L737`). That page shows the current status and the moves that status allows, so by RN-32's own reason ("A reload offers something only on a page that is still out of date") a reload shows nothing new. The product's line offers none (`web/pages.py:L739-L744`). Left as written, UX-F4 tells the next delivery Architect to add a reload that shows the same page. This changes a prior answer of mine, so it is raised for the next round rather than corrected quietly. I did not check UX-I3's assignee cases (UX-F3, UX-F9), and the item says so.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/skill/launcher.sh product-uxd tracker17`
