# Self-answer report — UXD.md

## Header

- **Companion:** products/tracker17/docs/UXD_open_issues.md
- **Document:** products/tracker17/docs/UXD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-28
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Everything it leans on was read in this repository on 2026-10-28: `UXD.md` (version 9, Settled) whole, `CONTENT_open_issues.md` (item 3.1, unrelated), `CONTENT.md` (searched for the off-list lines), `products/tracker17/web/pages.py:L880-L920` (`_NOT_LISTED_ABSENT`, `_OFF_LIST_ADDRESS`, `_off_list_line`), `products/tracker17/web/routes.py:L570-L593` (`_off_list_task`) and `tests/integration/test_filter_move_routes.py:L35-L38` and `L755-L807`. I read the code and ran no request against it.

## Items worked

### 3.1 — A refusal reached by an address has no place when the filter leaves the task off the list

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the UXD
- **Verdict:** answered
- **Why:** The refusal goes above the results, in the line UX-I4's confirmation uses, on a project's Tasks view and on All tasks alike. It names the task and its status, says the task doesn't match the filter and so isn't in this list, and names no action, no reload and no Clear. The item came with no draft, so I answered it from scratch.

  *Is it answered at all (§ A widening item waits until it occurs).* The item widens the UXD: it asks for a case UX-S4 and UX-S7 do not state. It comes from downstream, so it gets a change only where it cites an occurrence. It cites one: a site in the product, `web/pages.py` `_OFF_LIST_ADDRESS` with `_off_list_line`, and `web/routes.py` `_off_list_task`, which finds the task that is not shown. A test pins it (`test_filter_move_routes.py:L755`, `test_final_task_replay_uses_visible_row_or_off_list_refusal`). I read all three, and they say what the item says. So "not until it occurs" does not apply.

  *Seat (check 1).* The edit lands in `UXD.md`: UX-S4's failure column, which UX-S7 takes "As UX-S4", and possibly UX-I3's sentence on where this refusal sits. It binds no person, money or outside party. It is a question about where a line sits on a page this document defines, and I can name no ground the owner holds that I can't see. So it is mine to answer.

  *The question (check 2).* It is the right question and it can be answered from what I have. It hides no second question with a different seat. What the line says is `CONTENT.md`'s, and that does not split the item, because the item asks only where the line goes.

  *The answer.* UX-I3 and UX-F4 put this refusal "beside the task's status, in the row or on the page", because no control was used (RN-33). With a status or Overdue filter on, a task that is now `done` or `cancelled` may have no row, and the list page does not show its status anywhere. That leaves one place on a list page that is about the whole page and not a row: the line above the results where UX-I4's completion line goes. UX-F4 already uses that line for a task that left the list ("the confirmation names it, so the operator knows where it went"). The product puts this refusal there (`line_of` reads the same element in the test). So:
  - It sits above the results, and above the no-match state when the filter leaves no rows. The test's last case checks the line with no table on the page.
  - It names the task by its title and states its status, because the row that would have shown both is missing.
  - It says the task doesn't match this filter, so it isn't in this list. That is what holds when the page is built (UX-I3, RN-35).
  - It names no action, offers no reload, and does not offer Clear. UX-I3 rules that this kind of refusal names no action because the task is final and nothing is left to do. Pressing Clear would show the task, but there is still nothing to do with it. The product's line takes the no-action ending (`_NOT_LISTED_ABSENT`, "so it isn't in this list"). Its other off-list refusals, where a move is still possible, end with "press Clear to see it" (`_NOT_LISTED_CLEAR`). That difference matches UX-I3.
  - No row is invented and no confirmation is shown, the same as the in-row case.

  *The settled record (check 3).* Nothing moves. UX-I3's "in the row or on the page" is not broken: it gains a third place for when there is neither. UX-A3 asks that a refusal be "associated with the control it concerns", and RN-33 reads that as the task's status. With no status on the page, the line meets the association by naming the task and its status itself. UX-A5 already says refusals are announced without moving focus, and this one is no different. The task's own page always shows the status, so UX-F4's placement there is unchanged. `CONTENT.md` has no rule on where this line sits. Its words are that document's, and the product's words fit its no-action rule, so I raised nothing there.

  *The failure paths (check 4).*
  - **Empty:** the filter leaves no rows. The line sits above the no-match state, and the no-match state still shows Clear as UX-S4 says. The line does not ask for Clear, but Clear stays where it always is.
  - **Stale:** the status changes again between visits. Only `done` and `cancelled` reach this case, and both are final, so the status the line names cannot change after it is first shown.
  - **Concurrent:** the task is listed on one visit and filtered out on the next. The page is built from the saved data each time, so the line moves between the row and the line above the results with the filter, and says what is true each time.
  - **Refused:** this case is itself the refusal. It changes nothing.
  - **Not covered:** a confirmation address for a task that was deleted in another tab, opened on a list. The item does not ask about it, it cites no occurrence of it, and this answer does not reach it. I name it here and raise nothing, by § *A widening item waits until it occurs*.

  *Close call.* The other answer I weighed was to say "press Clear to see it", the way the product's other off-list refusals end, so the operator can find the task. What tipped it is that UX-I3 says this kind of refusal names no action, and the product already chose the no-action ending for it. If the owner wants the line to point to Clear anyway, that changes UX-I3's no-action rule for this case and leaves the placement as it is.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/skill/launcher.sh product-uxd tracker17`
