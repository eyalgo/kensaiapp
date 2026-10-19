# Self-answer report — fdr.md

## Header

- **Companion:** products/tracker17/docs/fdr_open_issues.md
- **Document:** products/tracker17/docs/fdr.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-06
- **Sources re-read:** one source outside this repository, read on 2026-10-06. It is tracker17's
  rule source under `products/tracker17/docs/SRS.md` § 7 C-5, tracker16-X's working code at
  `task-tracker-X`.
  - `tasktracker16x/application/task_service.py`, `update_task_priority`, docstring: "This path
    touches only the priority field — it never routes through the assignee update, so a
    priority-only change leaves the assignee intact."
  - The same file, `update_task_assignee`, checks the list only when a name is given:
    `if assignee is not None and not self._repository.assignee_name_exists(assignee): raise
    UnknownAssigneeError`.
  - `tasktracker16x/cli/app.py`, `_update_task`: due date, priority and assignee each run on their
    own branch, and the assignee branch runs "only when an assignee flag was actually given", so
    that an update of another field does not "spuriously clear the assignee".

## Items worked

### 2.1 — Saving a task's edit form changes only the fields the operator changed on that page

- **Bucket:** 2. Choices to confirm — the Principal PM drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** R-47 stands. A save of the task's edit form writes only the fields the operator changed.
  The draft's conclusion is right. Part of its argument does not hold, and the rule left three cases
  open.

  **The reason that holds.** The draft leans on PRD § UX Notes, Refusals say why. That note governs
  refused actions, and a field quietly put back is not a refusal, so the note does not carry the
  weight. Two settled sources do. First, `products/tracker17/docs/SRS.md` § 4.2 NFR-3 limits the
  stale-edit overwrite to "whatever the other tab saved for that field". A save that writes every
  field reaches fields the operator did not edit, which NFR-3 does not grant. Second, SRS § 7 C-5
  makes tracker16-X's task rules tracker17's wherever both cover one. tracker16-X writes each field
  on its own path, and an update of one field leaves the others as saved (Header, Sources
  re-read). So R-47 is a derivation from C-5 and NFR-3, not an open product call. The draft's
  closing line, "The inputs do not make this call, so it is the owner's", was the producing run's
  reason for asking, and it does not hold once C-5 is read against the code.

  **The cases the rule left open, now stated.**
  1. *Concurrent and stale.* A field counts as changed when its submitted value differs from the
     value the page showed. It is not compared with the value saved now. Tab 1 shows priority
     `low`. Tab 2 saves `high`. Tab 1 edits only the title, so the priority stays `high`. If tab 1
     changes the priority to `medium`, `medium` replaces `high`, which is R-104 and SRS AC-19.
  2. *Empty.* A save in which no field changed changes nothing and is not refused. That matches the
     FDR's own treatment of no-op actions: R-34 does not refuse a rename to the same name, and R-65
     does not refuse adding a label the task already carries.
  3. *Refused.* A save in which any changed field is refused changes no field, under R-100. A blank
     title saved with a new priority leaves the priority as it was.
  4. *Absent.* A save on a task another tab deleted is refused under R-103. R-47 adds nothing there.

  **Checked against the record.** R-47 contradicts nothing in `fdr.md`, the SRS or the SDD.
  `products/tracker17/docs/SDD.md` § S-2, Tasks in a project, says the task's page "changes title,
  priority, assignee and due date", and it says nothing on which fields a save writes. The UXD's
  presentation of an unlisted assignee is item 2.2's consequence, carried on the UXD companion.

  **What would have tipped it to the owner.** A named reason to prefer a whole-form overwrite, such
  as a stated wish for "last save wins for the whole task". No input states one. tracker16-X's code
  states the opposite.

### 2.2 — An edit that leaves an unlisted assignee unchanged keeps it, and is not refused

- **Bucket:** 2. Choices to confirm — the Principal PM drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** R-48 stands. An edit that does not change a task's assignee keeps a name that has left
  the list, and the edit is not refused for it. This item was decided after § 2.1, and it rests on
  § 2.1's answer: under R-47 an unchanged assignee is not part of the save, so FR-21's check on
  assigning never reaches it.

  **The source the draft missed.** The draft reasons from FR-21 and FR-22, and its argument holds.
  The most direct source is `products/tracker17/docs/SRS.md` § 6 DR-2: the assignee name "is plain
  text and stays valid after the name leaves the assignee list (FR-22)". A name the data rules call
  valid cannot be grounds for refusing an edit of a different field. tracker16-X agrees under SRS
  § 7 C-5. It checks the list only when an assignee is given, and a priority update leaves the
  assignee intact (Header, Sources re-read). `products/tracker17/docs/fdr.md` RN-10 already leans on
  the same reading when it keeps such a name out of the unreadable-data checks.

  **The cases stated.**
  1. *Changed away.* Changing such a task's assignee to a listed name, or to none, replaces the
     unlisted name. The name cannot be chosen again, because FR-21 allows only listed names. That
     is intended, and R-45 and R-60 already say it.
  2. *Stale.* The page loaded while `carol` was listed, another tab then removed `carol`, and the
     operator edits only the title. `carol` stays, under R-47 and R-48. If the operator instead
     changes the assignee to `carol`, the change is refused with the reason under R-60 and R-102,
     because `carol` is checked against the list at the moment the edit is applied.
  3. *Concurrent.* Tab 2 changes T's assignee from `carol` to `alice`. Tab 1, still showing
     `carol`, edits the title. T keeps `alice`, under R-47.

  **One consequence carried elsewhere.** `products/tracker17/docs/UXD.md` UX-F9 has the edit form
  offer "a listed name, or none" and says "an assignee not on the list, is refused under UX-I3".
  Read literally, the form cannot show such a task's saved assignee, and the refusal line refuses
  that task's every save, which R-48 says is not refused. The FDR states behaviour, and how the
  form shows the name is the UXD's to state. This run therefore raised the change as item 2.2 on
  `products/tracker17/docs/UXD_open_issues.md`, and left the FDR rule as drafted.

  **What would have tipped it.** A settled line requiring that a task's assignee always be a listed
  name. No such line exists. FR-22 and DR-2 say the opposite.

## Left for the owner

None this run.

## Skipped

None this run. Both open items were answered. § 1 and § 3 of the companion hold no items.

## Companions opened

- **products/tracker17/docs/UXD_open_issues.md** — **appended** — companion to `UXD.md`, landed in commit `e24ad0900`

Item 2.2 there, under choices to confirm, with its slot left open for the UXD's own round. It asks
UX-F9 to show a task's current assignee in the edit form even after the name has left the list, and
to refuse only a change to a name that has since left it. This FDR companion's § 2.2 slot names it.

## Launchers owed

- **products/tracker17/docs/fdr.md** — `<CORE>/launchers/skill/launcher.sh product-fdr tracker17`
- **products/tracker17/docs/UXD.md** — `<CORE>/launchers/skill/launcher.sh product-uxd tracker17`
