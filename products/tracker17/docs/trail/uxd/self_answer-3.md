# Self-answer report — UXD.md

## Header

- **Companion:** `products/tracker17/docs/UXD_open_issues.md`
- **Document:** `products/tracker17/docs/UXD.md` (version 3, Settled)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-07
- **Sources re-read:**
  - https://html.spec.whatwg.org/multipage/form-control-infrastructure.html, "Limiting user input
    length: the `maxlength` attribute". It says "User agents may prevent the user from causing the
    element's API value to be set to a value whose length is greater than the element's maximum
    allowed value length", as item 2.1 quotes. It says nothing about a paste, or about telling the
    user.
  - https://chromium.googlesource.com/external/WebKit_LayoutTests/+/master/fast/forms/textarea-maxlength.html,
    an archived WebKit layout test, read for what Chromium does with an insertion past the maximum.
    It expects an insertion into a full field to be rejected and the value left as it was. It is
    not current evidence: its line-break case lets three line breaks fill a maximum of 6, so it
    counts a line break as two characters. The current standard counts it as one, "with all newlines
    normalized to a single character", as `SDD.md` § 4 RT-10 quotes. **What current Chromium does
    with a paste longer than the maximum is unmeasured**, by this run and by the run that raised
    item 2.1.

## Items worked

### 2.1 — Where saved text cannot be changed, the page says the field's maximum length before the operator submits

- **Bucket:** 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The comment form and the create-project description field each say their maximum
  length beside the field, before the operator submits. Three additions: the other five fields
  do not say theirs; the number shown is the field's own maximum, from the one place the lengths
  are stated; and the second open question now cites `SRS.md` FR-40, since the SRS section it
  cited is gone.

  *Seat (check 1).* The UXD's own, and so mine in the owner's seat. The change lands in UX-F2,
  UX-F7 and the UXD's open question. It binds only the UXD's own experience. No outside person,
  money or risk turns on it. The item's lengths are not in question: the CPO's seat confirmed them
  (`products/tracker17/docs/trail/sdd/self_answer-4.md`, item 2.1), and they are `SRS.md` § 3.13
  FR-40 and `SDD.md` § 4 RT-10 now.

  *Whether the draft holds (check 2).* Its conclusion holds, and so does the reason it gives.
  The HTML standard lets a browser stop text at the maximum and requires no message
  (source re-read above). A comment cannot be edited (PRD § Core Features, Comments, "Comments
  can't be edited or deleted"), and a description cannot be changed after the project is created
  (`UXD.md` UX-F2). So text lost at the limit in those two fields cannot be put back. PRD § UX
  Notes, Refusals say why, makes a quiet partial refusal the thing to avoid. The draft says it did
  not measure what Chromium does with an over-long paste, and neither did this run. The argument
  does not need it. If the paste is cut, text is lost with no word. If the paste is rejected, the
  field ignores it with no word. Either way, the operator needs the limit in view before acting,
  and nothing else on the page can show it.

  The draft answered a smaller question than its heading asks. The heading covers every field
  whose text cannot be changed. The draft named two fields and left the other five as "the CDO's
  call". That call is part of the item, and I made it. The five single-line fields do not say their
  maximum. Text cut short in a one-line field is in view, and each of the five can be put right
  afterwards: a project is renamed (UX-F10), a title or the operator's name is edited (UX-F9,
  UX-F8), and a label or an assignee name is removed and added again (UX-F9, UX-F8). Putting a
  sentence beside all seven fields would add a line to every form for a case 200 characters makes
  rare, against PRD § Goals, It is simple. *Close call:* I weighed giving every field the sentence
  for consistency. What decided it was that the PRD's harm is a refusal with no reason, and in
  those five fields a cut value can still be fixed afterwards.

  *Against the settled record (check 3).* `SDD.md` § 4 EX-2, "No page runs a script", rules out a
  live count, and a sentence that never changes needs no script. `SDD.md` § 4 RT-8 and § 11 R-10
  rule out a refusal that keeps over-long text. The draft's "If overridden" names both, and neither
  constrains a fixed sentence. UX-I3's "no field is checked while the operator types" is not
  touched, because the sentence checks nothing. `CONTENT.md` § Accessibility of text, "An
  instruction is plain text beside the field and states the constraint in a full sentence", gives
  the form. `DESIGN.md` § Components, "A field hint, such as the note beside a project's
  description, sits under its field", gives the place. Neither needs a change. The
  open question's citation, `SRS.md` § Open Questions, no longer exists. `SRS.md` version 4's `## `
  headings are §§ 1 to 8 and the Review Notes, and its header says "the last open question closes".
  So the draft's condition, "once `SRS.md` states one", is met by FR-40. The open question's
  substance stands, because 200- and 4,000-character values are still far wider than any
  column, and `DESIGN.md` RN-14 already answers it with wrapping.

  *Failure paths (check 4).* **Stale:** if the lengths move, a sentence with its own copy of the
  number would disagree with the field. Addition (2) closes that: the number comes from the single
  place `SDD.md` § 4 RT-10 states it. **Refused:** a value the field let in is never refused as
  too long (`SRS.md` FR-40), so the sentence never promises a limit that a refusal then
  contradicts. **Uncovered, named:** the sentence states the limit and does not say that a
  particular paste was cut. Nothing on a page without a script can say that (EX-2), and a refusal
  from the tracker could not keep the text (RT-8, R-10). Text outside the Basic Multilingual Plane
  counts two in the field and one in the rule (`SDD.md` § 4 RT-10, § 11 R-11), so such a field can
  stop before the stated number. A sentence saying "at most" stays true then. **Empty:** a
  description is optional, and the sentence is in view whether or not anything is typed.

  *Downstream.* `DESIGN.md` RN-14 gives the same outdated reason as the UXD's open question,
  "no maximum length is set upstream (`products/tracker17/docs/SRS.md` § Open Questions)".
  `products/tracker17/docs/DESIGN_open_issues.md` now carries that (see § Companions opened).
  `CONTENT.md` is owed nothing: its instruction form covers the two sentences, and their words are
  written to it when a change publishes them. `SDD.md` is owed nothing now. Its § 11 R-11 already
  says "How a page tells the operator a field's maximum is the UXD's question". Its § 12 says it
  "changes nothing of the experience, which is the UXD's". It reads the folded UXD on its own next
  run.

### 2.2 — The task's edit form shows the task's assignee even after that name has left the list

- **Bucket:** 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The edit form's assignee control shows the task's current assignee even when that name
  is off the list, and a save that leaves it keeps it. UX-F9's refusal covers only an assignee
  changed to a name that left the list after the page loaded. Addition: when the task's assignee
  is off the list, a sentence beside the control says so, and says that choosing away replaces it.

  *Seat (check 1).* The UXD's own. The behaviour is the FDR's and is settled: `fdr.md` R-47,
  R-48, R-115 and R-118, and the Examples rows for `carol`. How the form shows that behaviour is
  experience, which `fdr.md` RN-12 itself hands to the UXD ("How the form shows that name is the
  UXD's to state").

  *Whether the draft holds (check 2).* It holds, for the reason it gives. `SRS.md` § 3.6 FR-22 and
  § 6 DR-2 make an unlisted name on a task a normal state. UX-F9's "a listed name, or none" cannot
  show it, and its refusal line, read as written, refuses every save of such a task, which R-48
  says is not refused. With the current name shown as the current choice, the submitted value
  equals what the page showed. So the field is unchanged under R-115, and R-47 and R-48 keep it. The
  draft's "cannot be chosen again once it is replaced" matches R-118 and the Examples row
  "`carol` cannot be set on T again while `carol` is off the list". UX-S6, "The task as saved",
  agrees.

  *The addition, and why.* Without it, the unlisted name sits in the control looking like any
  listed choice. The operator then has no way to know that it is offered on this task only, or that
  choosing away from it is the last time this control offers it (R-118). The name can come back only
  by being added on People again (UX-F8). A sentence beside the control says both, shown only when
  the task's assignee is off the list. Its words are `CONTENT.md`'s. I weighed putting the note
  inside the option's text instead. What decided against it is `DESIGN.md` RN-14, under which a
  closed select is "the one place the browser may cut a value". A note after a long name is the
  part that would be cut. A sentence beside a field is the device UX-F2 and UX-F8 already use.
  *Close call:* a plain *confirmed* was close, because the FDR rules hold without the sentence.
  What tipped it is check 4's refused path below.

  *Against the settled record (check 3).* `CONTENT.md` § Accessibility of text gives the form of an
  instruction beside a field. No settled text puts the unlisted name anywhere a filter could reach.
  The filter's assignee control still offers listed names only (UX-F5, and `fdr.md` Examples:
  "A filter by assignee `carol` is refused"). UX-F3's add-task form is untouched: a new task has
  no current assignee to keep. `SDD.md` § 6's slice text, "an assignee no longer on the list
  … refused where they were entered", reads the same under the narrowed refusal line.

  *Failure paths (check 4).* **Stale:** a task carrying a listed `alice` when the page loads, with
  `alice` removed in another tab before the save. If the save leaves the control as it showed, the
  field is unchanged, so the name is kept (R-48, R-115). If the save changes to a name removed since
  loading, it is refused as out of date with a reload (UX-I3). **Concurrent:** another tab changes
  the assignee, and this tab saves only a title. The field is unchanged against the page, so the
  other tab's value stands (R-47, the Examples row for tab 1 and tab 2). **Refused:** a save that
  blanks the title of a task carrying `carol` is refused whole (R-117), and the refused page still
  shows `carol` as current, because the task still carries it. The sentence is what tells the
  operator, then and before, why `carol` behaves differently from the names below it. **Empty:**
  with an empty assignee list, the control offers `carol` and none, and the sentence still applies.
  Whether the edit form also gets UX-F3's link to People for an empty list is not in this item,
  and I did not add it.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

- **products/tracker17/docs/DESIGN_open_issues.md** — **opened** — companion to `DESIGN.md`, landed in commit `b3a00490d25bd8b0b0715303146f6c89b062f098`

No item routed it, so no slot waited on it. It was found while reading `DESIGN.md` for item 2.1,
under the prompt's § *The items are not the whole of what a document is owed*, on the ground "A
fact in it is now false". `DESIGN.md` RN-14 gives as a reason that "no maximum length is set
upstream (`products/tracker17/docs/SRS.md` § Open Questions)". `SRS.md` § 3.13 FR-40 sets the
lengths, and `SRS.md` version 4 has no § Open Questions. The rule RN-14 supports, that long text
wraps and is never shortened, does not change. `products/tracker17/docs/trail/sdd/self_answer-4.md`
declined to reopen `DESIGN.md` for this, expecting "the round that closes the open question" to
carry it. That round was `product-srs`'s, which does not write `DESIGN.md`, so it was not carried.
The file holds one item, 2.1, in choices to confirm, with its slot left open for `product-design`'s
round.

## Launchers owed

- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/skill/launcher.sh product-uxd tracker17`
- **products/tracker17/docs/DESIGN.md** — `<CORE>/launchers/skill/launcher.sh product-design tracker17`
