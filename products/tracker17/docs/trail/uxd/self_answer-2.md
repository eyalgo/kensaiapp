# Self-answer report — UXD.md

## Header

- **Companion:** products/tracker17/docs/UXD_open_issues.md
- **Document:** products/tracker17/docs/UXD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-06
- **Sources re-read:** W3C, Understanding SC 4.1.3 Status Messages
  (https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html). It defines a status message as a
  "change in content that is not a change of context", and it says that changes of context "by their
  nature, interrupt the user by taking focus" and fall outside the criterion. Addition (3) relies on
  this. SC 3.3.4 is relied on as `UXD.md` RN-25 already cites it, and this run did not re-read it,
  because no answer here turns on more than RN-25 says.

## Items worked

### 2.1 — When an irreversible action's confirmation appears, its sentence takes the first button's place and takes focus, and the confirming control does neither

- **Bucket:** 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft is confirmed: the consequence sentence takes the first button's place and takes
  focus, followed by the confirming control and then the back-out control. Three additions come from
  the failure paths.

  *Seat.* This item is the UXD's to answer. The edit lands in UX-I2, and it binds only how the
  document's own anatomy and focus behaviour fit together. `DESIGN.md` agrees: its
  `{components.confirm-strip}` entry says the order of the strip's parts, and which part takes focus,
  "are not this document's … `UXD.md` UX-I2 owns them" (`DESIGN.md:450-457`). No ground the owner
  holds and the run cannot see was found. The owner already set the bar this answer serves (WCAG 2.2
  AA, UX-A5) and the confirmation itself (UX-I2, RN-25).

  *The draft holds, for the reasons it gives.* With the keyboard, UX-I6 makes Enter or Space press the
  focused button (`UXD.md:325-326`). If focus lands on the confirming control, one repeated key deletes
  a project and every task in it (PRD § Core Features, Projects). With a pointer, the second click of a
  double click lands on whatever replaced the first button. Undo does not exist (UX-I2), so this
  confirmation is the only guard. Focus on the sentence also means a screen reader reads the
  consequence before reaching any choice. Its order puts the confirming control one Tab away and the
  back-out control two Tabs away. I considered the draft's alternative of putting focus on the
  back-out control. A repeated key would then also be harmless, but the consequence would be read
  after a choice instead of before it, so the draft's arrangement is the better one.

  *Addition (1), covering the spot.* "Takes the first button's place" could be read as starting at the
  same edge. A short sentence, or one starting at the left of a wider or right-aligned button, would
  then leave part of the old spot to whatever sits next to it. That could be the confirming control.
  The requirement is that the sentence covers the whole area the first button occupied. That is the
  outcome the pointer half needs, and the method is the SDD's and `DESIGN.md`'s.

  *Addition (2), the refused path.* UX-I2 says where focus goes when the strip appears, but not where it
  goes when the operator backs out, and the strip then gives way in the same manner. Under UX-I2's own
  stated reason, focus has to return to the first button. That button comes back in its own spot.
  Nothing destructive follows from a repeated press: a second Enter on the restored first button
  opens the strip again, with focus on the sentence.

  *Addition (3), the settled record (check 3).* UX-A5 requires "confirmations and refusals announced
  to assistive technology without moving focus (SC 4.1.3 Status Messages)" (`UXD.md:359-360`). Read
  alone, that contradicts focus landing on the confirmation. There is no conflict in substance. UX-I2's
  confirmation takes focus, which makes it a change of context, and W3C places changes of context
  outside SC 4.1.3 (source above). UX-A5's "confirmations" are UX-I4's completion lines. However, the
  UXD uses the one word for both, so UX-I2 should say outright that its confirmation takes focus on
  purpose and is not one of UX-A5's status messages. This item already moves that focus onto a
  non-interactive sentence, so this is the round to say it.

  *Named and not covered.* Stale: the count in the sentence ("its 12 tasks") is the count as the page
  was loaded, and another tab could add a task before the confirming press. UX-I9 (pages show data as
  loaded) governs that, and it was settled before this item. Empty: a project with no tasks still
  takes the confirmation. How its sentence reads is `CONTENT.md`'s. Concurrent: a target already
  deleted in another tab is refused under UX-I3 or shows UX-S10, which the UXD already states. After
  the confirming press on a list row's `cancelled` move, the row has no move buttons. Where focus goes
  then is the same as after any other move (UX-F4), and this item does not ask about it.

  *Close call.* I nearly confirmed this without addition (2). I added it because a back-out that drops
  focus to the top of the page fails UX-A1 in exactly the way the existing sentence was written to
  prevent. It is the same anatomy, so it belongs in the same round.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/skill/launcher.sh product-uxd tracker17`
