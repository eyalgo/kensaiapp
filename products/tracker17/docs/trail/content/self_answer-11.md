# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-20
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Everything it leans on was read in this repository on 2026-10-20: `CONTENT.md` (v11), `UXD.md` (v6, Settled), `PRD.md` (Settled), `products/tracker17/web/pages.py`, `products/tracker17/web/routes.py`.

## Items worked

### 3.1 — A refusal shown when the reader pressed nothing

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** answered
- **Why:** Yes. The one refusal formula covers a refusal reached without a press, with one added rule: its reason is a fact about the task and what its status allows, never a fact about a press. It gives no action and no reload. The item carries no draft, so this was decided from scratch.

  *Seat.* The question is `CONTENT.md`'s: what the refusal formula says and which reason it allows, and the edit lands in § Message patterns, Error, *A refusal*. The answer binds no person and no outside party, and I could name no ground the owner holds that I can't see. So it is mine to answer in the owner's seat. One half of the item is not mine, whether the interface shows a refusal here at all, and that is handled below as a raised item and not as a split. The wording answer stands whatever the CDO decides about that, so the two halves are not one question in two coats, and the second is raised as an item and not left to the owner.

  *It is a widening item, and it cites an occurrence.* The formula does not state the case now, so § *A widening item waits until it occurs* applies. The item cites a site in the product as it stands, and I re-read it. `web/routes.py:351-352` returns the not-allowed refusal when the request is a page load for the confirmation of a move to `cancelled` and `cancelled` is not among the moves the task's status allows. `web/pages.py:760` writes the line. The press path is separate, at `web/routes.py:725-736`. So "not until it occurs" does not apply.

  *Check 2, the question.* The item's facts hold. The line says "the move you pressed", and in this step the reader pressed nothing: the tracker sees an address carrying `move_task` and `move_confirm`, and it can't establish that a press produced it. A reader can arrive by a bookmark, a typed address, a reload or Back. Voice says "State only what the tracker established" (`CONTENT.md` § Voice), and the formula's reason is "a fact about what the reader typed or pressed". For this refusal there is no typed or pressed thing to state a fact about, so the formula has a gap and not a conflict. After a Back that follows a saved move the line is worse than false: the status beside it, `cancelled`, shows the move took effect, and the line says the move was refused.

  *What the added rule says.* The reason is a fact about the thing the address names and its current state: "The status of 'Set up CI' is done, which doesn't allow a move to cancelled." That is 15 words, one claim, and it holds in both cases the page can meet. The second sentence says what the page shows, as the formula already says for a refusal with no action: "A task in done can't be moved." The two-sentence limit holds.

  *Why no action and no reload.* The page is built from the saved data when it loads. `done` and `cancelled` are final (`PRD.md` § Core Features, Status workflow), so no action ever makes the move allowed, and a reload shows the same page. `UXD.md` UX-I3 (v6) already bounds a reload to a page "still out of date", and this page is not. The formula's "then one action where one exists" governs, and none exists.

  *Check 3.* Nothing settled requires the opposite, with one exception that is raised and not relaxed. `UXD.md` UX-F4 says this refusal "arises only when the task was moved in another tab after the page loaded" and "offers a reload", UX-I3 places a refusal "beside the control that was used", and UX-A3 associates it with "the control it concerns". The case here has no other tab and no control used. I did not decide the experience. The `CONTENT.md` rule is written for the refusal as the interface shows it, and it stops applying if the CDO removes the refusal. My earlier answers in this companion: none, since 3.1 is its only item. My earlier answers to other items in this document, as the trail holds them, concern a refusal with no action (`trail/content/self_answer-9.md`), and this one extends the same reading to the case where the wanted state does not hold and can never hold.

  *Failure paths.* Empty: no task at the address gives the not-found page, through the `identity is None or task is None` branch at `web/routes.py:346-347`, and it has its own pattern. Absent: same. Stale: a final status never moves, so the line can't go stale, and a task in `todo` or `in-progress` allows the move, so the confirmation shows and no refusal is reached. Concurrent: two tabs reaching the address give the same line. Refused: this is the case. *Named and not covered:* a refusal shown after a redirect from a real press (`web/routes.py:725-736`), then reloaded, has the same property, because the address alone can't establish the press either. The item cites no site for it, so by § *A widening item waits until it occurs* it waits.

  *Close call.* The other reading is that no refusal should be shown and the plain task page, with its status and no move buttons, is enough, since backing out of a confirmation is a reading action that produces no message (`CONTENT.md` § Voice). That reading is the interface's change and the CDO's call. What would tip this answer is the CDO taking it, which removes the clause on the next `product-content` run, and `UXD_open_issues.md` item 2.1 carries that question.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

- **products/tracker17/docs/UXD_open_issues.md** — **opened** — companion to `UXD.md`, landed in commit `8d9f6e99e`

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/companion-self-answer/launcher.sh tracker17 UXD`
