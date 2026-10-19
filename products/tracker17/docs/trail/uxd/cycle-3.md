# UXD open issues — tracker17

> Companion to `UXD.md`. The CDO authored the UXD non-interactively; this file holds
> what it could not settle from the inputs (the PRD, the project's Agari and its doctrine, the
> SRS when present, and any context the owner handed over) — and, when a design run has produced
> output for this product, the pointer to it. **Answer inline** — fill each **Answer** / **Confirm-or-override**
> slot — **commit this file**, then re-run `product-uxd`. It folds your answers into the UXD
> and drops the resolved items. When nothing is left open, `product-uxd` **deletes this file**:
> no file = the UXD is done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git
> refuses to remove a file with uncommitted edits in it — so an uncommitted answer stops
> that run before it can commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CDO folds them in, it first copies this
> file whole to `docs/trail/uxd/` — so what you decided, and why, stays readable and citable
> for good.
>
> **A third source of items, and it is not the CDO.** § 3 holds what a seat downstream of the UXD
> found missing while working from documents the UXD fed. It is answered here and folded by the same
> run, but it was never this run's question.

> **Opened by a `companion-self-answer` run on 2026-10-06, not written by a `product-uxd` run.** The
> UXD was settled and had no companion. The run was answering item 2.1 of
> `products/tracker17/docs/SDD_open_issues.md`, "Every text field has a maximum length", in the
> CPO's seat, and it confirmed the lengths. `UXD.md` describes every one of those fields and says
> nothing about a length, because none existed when it settled. Whether a page tells the operator
> a field's maximum is an experience call, and `products/tracker17/docs/SDD.md` § 12 says the SDD
> "changes nothing of the experience, which is the UXD's". So the run opened this file to carry it,
> and left `UXD.md` unchanged. Its reasoning is in
> `products/tracker17/docs/trail/sdd/self_answer-4.md`, under item 2.1.

Every `SDD §` reference below is to `products/tracker17/docs/SDD.md`, version 2. `PRD.md`,
`SRS.md`, `DESIGN.md` and `CONTENT.md` are the files of those names in `products/tracker17/docs/`.

---

## 1. Open issues — experience questions with no answer yet

None.

## 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override

### 2.1 Where saved text cannot be changed, the page says the field's maximum length before the operator submits
- **Drafted into the UXD:** nothing yet. `UXD.md` names no maximum length for any field, and its
  second open question says "No maximum length is set upstream". One is set now. The answer to item
  2.1 of `products/tracker17/docs/SDD_open_issues.md`, given on 2026-10-06 in the CPO's seat,
  confirmed SDD § 4 RT-10: at most 200 characters for a project name, a task title, an assignee
  name, the operator's name and a label, and at most 4,000 for a project description and a
  comment. RT-10 holds the browser to them: "The field's own `maxlength` attribute stops the
  browser at that length". The proposed change has two parts.
  - **One sentence beside two fields.** The comment form (UX-F7) and the description field of the
    create-project form (UX-F2) each say their maximum length beside the field, in view before the
    operator submits. These are the two fields whose text cannot be changed once saved. Whether
    the other five fields say theirs is the CDO's call.
  - **The second open question stops saying that no maximum length is set**, once `SRS.md` states
    one. `products/tracker17/docs/SRS_open_issues.md` § 2.1 carries that change to the SRS.
- **Rationale:** a field with a maximum length takes no text past it, and nothing has the browser
  say so. The HTML standard's sentence is "User agents may prevent the user from causing the
  element's API value to be set to a value whose length is greater than the element's maximum
  allowed value length"
  (https://html.spec.whatwg.org/multipage/form-control-infrastructure.html, "Limiting user input
  length: the `maxlength` attribute"). The reason to expect harm is a paste: an operator who
  pastes a long log into a comment can submit less than they pasted and not know it. This run did
  not test what Chromium does with a paste longer than the maximum. Whether it keeps the first
  4,000 characters or keeps none, the page as designed says nothing about why.

  In two fields the loss cannot be repaired. PRD § Core Features, Comments, says "Comments can't
  be edited or deleted". UX-F2 says "the description cannot be changed after the project is
  created". A title, a name or a label that was cut can be edited, or removed and added again.

  The PRD source is § UX Notes, Refusals say why: a refused action "tells the operator the reason
  in plain words". On this reading, a field that quietly takes less than the operator entered has
  turned part of the entry down without a reason.

  The UXD already uses this device twice. UX-F2 has the create form say "beside the description
  field" that the description cannot be changed, and UX-F8 has the Your name section say "beside
  the field" that existing comments keep their name. `CONTENT.md` § Accessibility of text has the
  form of words: "An instruction is plain text beside the field and states the constraint in a full
  sentence". `DESIGN.md` § Components has the place: "A field hint, such as the note beside a
  project's description, sits under its field".
- **If overridden:** the fields carry their maximum either way, because the lengths are the SDD's
  and, once it folds, the SRS's. With no entry here, no page mentions a length, and a comment
  pasted past 4,000 characters is saved short and stays that way.

  Another way of telling the operator is the CDO's to choose. Two are closed by settled text. A
  count that changes as the operator types needs a script, and SDD § 4 EX-2 says "No page runs a
  script". A refusal that keeps the over-long text is not available, because SDD § 4 RT-8 carries
  kept text in the page's address and § 11 R-10 says an address cannot hold it.
- **Confirm or override:** confirm, with three additions. The comment form (UX-F7) and the create-project description field (UX-F2) each say their maximum length beside the field, in view before the operator submits, in the field-hint place `DESIGN.md` § Components already has and the instruction form `CONTENT.md` § Accessibility of text already has. (1) The other five fields do not say theirs. The draft left that call open, and this answer makes it. A project name, a task title, the operator's name, a label and an assignee name are each one line, so a value cut short is in view in the field, and each can be put right afterwards: a project is renamed (UX-F10), a title or the operator's name is edited (UX-F9, UX-F8), and a label or an assignee name is removed and added again. A sentence beside every one of them would add a line to every form for a case 200 characters makes rare, against PRD § Goals, It is simple. (2) The number the sentence states is the field's own maximum, from the same single source as the field's limit (SDD § 4 RT-10 states the lengths once), so the sentence and the field cannot disagree. (3) The second open question's condition is met. `SRS.md` § 3.13 FR-40 states both maximums, and `SRS.md` version 4 has no § Open Questions, so that citation now points at nothing. The question stops saying no maximum length is set and cites FR-40 instead. Its substance stands, because a 200-character title and a 4,000-character comment are still wider than any column, so how long text wraps is still `DESIGN.md`'s. `DESIGN.md` RN-14 repeats the same outdated reason, and `products/tracker17/docs/DESIGN_open_issues.md` § 2.1 carries that. Reasoning in `docs/trail/uxd/self_answer-3.md`.

### 2.2 The task's edit form shows the task's assignee even after that name has left the list

> **Raised by a `companion-self-answer` run on 2026-10-06, not written by a `product-uxd` run.** The
> run was answering `products/tracker17/docs/fdr_open_issues.md` in the owner's seat. It confirmed
> two FDR rules there: § 2.1, R-47, a save of the task's edit form changes only the fields the
> operator changed, and § 2.2, R-48, an edit that leaves an unlisted assignee unchanged keeps it and
> is not refused. Reading UX-F9 against them, it found UX-F9 does not say what the edit form shows
> for a task whose assignee has left the list, and its refusal line reads as refusing that task's
> save. It left `UXD.md` unchanged. Its reasoning is in
> `products/tracker17/docs/trail/fdr/self_answer-1.md`.

- **Drafted into the UXD:** nothing yet. The proposed change to UX-F9 has two parts.
  - **The assignee control shows the task's current assignee as its current choice**, even when that
    name is no longer on the list. The other choices stay the listed names and none. A save that
    leaves the control as it showed keeps the name. Choosing a listed name or none changes it, and
    the unlisted name cannot be chosen again once it is replaced.
  - **The refusal line covers only a changed assignee.** "An assignee not on the list, is refused"
    becomes: an assignee changed to a name that has left the list since the page loaded is refused
    with the reason. That is the stale-page case UX-F3 already describes for the add-task form.
- **Rationale:** UX-F9 says the form edits "assignee (a listed name, or none)", and its
  failure line says "an assignee not on the list, is refused under UX-I3". SRS § 3.6 FR-22 keeps a
  removed name on every task that carries it, and SRS § 6 DR-2 says that name "stays valid after the
  name leaves the assignee list". So a task carrying such a name is a normal state. UX-F9 offers no
  way to show it. A control limited to listed names and none has to show the task as unassigned or
  as someone else. The page then misstates the task, and a builder reading the refusal line refuses
  every save of that task, which `products/tracker17/docs/fdr.md` R-48 says is not refused. The FDR
  Examples table carries the case: "`carol` removed from the list, task T carries `carol`, the
  operator changes T's title", accepted, T keeps `carol`. UX-S6 already says the task page shows
  "The task as saved", so the change brings the edit form in line with the page around it.
- **If overridden:** the FDR rules stand, because they are behaviour and not presentation. The form
  then shows something other than the saved assignee for such a task, and the CDO says what it shows
  and how a save that leaves it still keeps the name, as R-47 and R-48 require.
- **Confirm or override:** confirm, with one addition. The assignee control shows the task's current assignee as its current choice even after that name has left the list, and offers the listed names and none beside it. A save that leaves the control as it showed keeps the name (FDR R-47, R-48, R-115). Choosing a listed name or none replaces it (R-118). UX-F9's refusal line covers only an assignee changed to a name that left the list after the page loaded, the out-of-date case UX-I3 already describes. The addition: when the task's assignee is no longer on the list, a sentence beside the assignee control says so, and says that choosing another assignee or none replaces the name, which can be set again only after it is added back on People. The words are `CONTENT.md`'s. Without the sentence, the name looks like any listed choice, although the operator cannot pick it on any other task and loses it from this one by choosing away. The sentence goes beside the control, not inside the option, because `DESIGN.md` RN-14 lets the browser cut a value in a closed select, and a note on a long name would be the part cut. This is the same device UX-F2 and UX-F8 already use beside a field. Reasoning in `docs/trail/uxd/self_answer-3.md`.

## 3. Raised from downstream — an item from a seat that did not write the UXD

None.
