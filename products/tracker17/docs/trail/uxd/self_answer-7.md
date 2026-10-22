# Self-answer report — UXD.md

## Header

- **Companion:** products/tracker17/docs/UXD_open_issues.md
- **Document:** products/tracker17/docs/UXD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-21
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Everything it leans on was read in this repository on 2026-10-21: `UXD.md` (version 8, Settled), `CONTENT.md` (§ Voice, RN-26, RN-27), `CONTENT_open_issues.md` (items 2.1 and 3.1, both answered), `SDD.md` § 6 `status-moves` (S-4), `docs/trail/uxd/cycle-6.md` § 2.2, `docs/trail/uxd/self_answer-6.md`, `docs/trail/content/self_answer-12.md`, `products/tracker17/web/routes.py` (`_move_view`, `_move_outcome`, the move submission handler), `products/tracker17/web/pages.py` (`_CHANGED`, `_OVERTAKEN_LINES`, `_ADDRESS_LINE`, `_refusal_line`, the assignee refusal lines), `tests/integration/test_move_routes.py:L87-L99` and `tests/integration/test_move_pages.py:L435-L450`. I read the code and ran no request against it.

## Items worked

### 2.1 — The page an overtaken move lands on, opened again by a reload, Back or a bookmark: does it still say the task's status has changed?

- **Bucket:** 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** No, it should not say the status has changed. The lean, (a), holds: the line states the task's current status and what that status allows, and claims no change. I added two things the draft did not carry.

  *Seat (check 1).* The edit lands in `UXD.md` (UX-F4, UX-I3, and their notes), so it is this document's. It binds no person, money or outside party, and I can name no ground the owner holds that I can't see. The item calls UX-F4's sentence one "the owner confirmed" (`cycle-6.md` § 2.2). That answer was given by a self-answer run (`self_answer-6.md`), and the question it settled was the reload, not the words "has changed". So replacing those words does not undo an owner call on them. It is mine to answer.

  *The draft (check 2).* The argument holds. The tracker turns every move refusal into an address and reads it back on each load (`web/routes.py`, `_move_outcome`). `_move_view` returns that outcome without reading the task's status, and the page shows the line whenever the address names a task on the page. So a reload, Back, a bookmark or a typed address shows "has changed to <status>", and the tracker can't establish a change from an address. `CONTENT.md` § Voice says "State only what the tracker established". Option (a) builds the line from the status the page reads when it is built, so it is true on the press and on every later visit. (b) leaves a known breach of a settled standard. (c) needs a one-time mechanism the product lacks, which adds a part for the reader to read (§ 1's test) and reopens the SDD's history rule.

  The draft is right and incomplete in two places, and both are the same claim in other forms.

  *Addition 1, UX-I3's "says so".* UX-I3 says a refusal caused by the page being out of date "says so and names what is left to do". Saying the page was out of date is the same claim about the past as "has changed", and it fails on a later visit the same way. If the fold changed only UX-F4, UX-I3 would still require what UX-F4 no longer says. So "says so" goes, and so do RN-34's "UX-I3's out-of-date refusal says the page was out of date" and RN-17's "the refusal still says so". UX-I3 states the reason once, as a rule: every refusal in this tracker is read from its page's address, so it is shown again whenever that address is opened, and it states what holds when its page is built, never an event before it. RN-17's reason for the refusal, that an address can outlive what it names, still holds.

  *Addition 2, the assignee refusals.* UX-F3 and UX-F9 say the reason "says the name has left the list". That is also a past event. The refusal rides in the address the same way (`web/routes.py` redirects with `task_refused` and `edit_refused`), and an address cannot show that the name was ever on the list. The requirement becomes "says the name is not on the list". The product's lines today read "is no longer on the assignee list" (`web/pages.py`, near lines 516, 967 and 1495). Changing them is a change that publishes text, and the words are `CONTENT.md`'s.

  *The settled record (check 3).* `CONTENT_open_issues.md` item 3.1 carried the same answer, (a), from the Content Manager's seat, and item 2.1 there changes RN-26 on the finding this answer acts on, so the two documents agree. The refusal formula's clause "names the move the address asks for … where the address carries one" (CONTENT item 2.1, addition 3) fits (a): the overtaken page's address names no move, and the line names none. UX-I3's other refusals (the wanted state already holds, RN-32; reached by an address, RN-33) already state what is true now and need no change. `SDD.md` S-4 repeats "says the task's status has changed", and the tests pin the wording (`test_move_routes.py:L87-L99`, `test_move_pages.py:L445`). Those follow on their own rounds once `product-uxd` folds this answer, so I raised nothing on the SDD now: it would ask the SDD to follow a UXD sentence that has not moved yet.

  *The failure paths (check 4).*
  - **Stale:** the status changed again between visits. The line names the newest status, because it reads the status when the page is built. True.
  - **Absent:** the task was deleted after the press. The move route sends the operator to the task's address, which shows UX-S10, and a later list address with no such task shows no line. Unchanged.
  - **Concurrent:** two tabs press the same move, and the second is refused because the task already has that status. Under (a) the line reads "The status of '…' is in-progress. A task in in-progress can be moved to …", which is true. Under the current wording it is also true. Whether naming the moves there counts as "naming an action" under RN-32's exception is not changed by this answer.
  - **Refused, from a tampered form:** a status value that is no status (`not-a-status`) gets the same line today (`_refusal_line` doesn't tell the two codes apart), so "has changed to" is false even on the press. Under (a) it is true.
  - **Empty:** a typed address for a task that was never moved. Today it shows "has changed to todo". Under (a) it shows the status and the moves it allows, which is true.
  - **Not covered:** a name added back to the list after an assignee refusal. A reload then shows "is not on the list" unless the page reads the list when it is built. Addition 1's rule covers it, and how the product meets that rule is the SDD's.

  *The cost.* The move line no longer says the press failed because the page was out of date. It still shows as a refusal beside the status, in the place the press was made, and the status it names is not the one the operator pressed from. That is enough to read what happened.

  *Close call.* The other answer I weighed was a fourth option: carry the pressed move in the address, so the line can say "The status of '…' is done, which doesn't allow a move to in-progress", in the same form as the refusal reached by an address (`_ADDRESS_LINE`). It is true on every visit and names the refused move. What tipped it is that it adds a field to the address and a change to the SDD and the tests, for words the status beside the line already conveys. If the owner wants the line to name the move that was refused, that is the option to take, and it overrides (a) without touching the two additions.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/skill/launcher.sh product-uxd tracker17`
