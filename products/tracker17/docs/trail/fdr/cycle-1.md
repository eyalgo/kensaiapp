# FDR open issues — tracker17

> Companion to `fdr.md`. The Principal PM authored the FDR non-interactively; this file holds what the
> run could not settle from its inputs — the PRD, the SRS and the SDD.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `product-fdr`. It folds your answers into the FDR and drops the resolved items. When nothing is
> left open, `product-fdr` **deletes this file**: no file = the FDR is done.
>
> Your answers are never thrown away. Each time the Principal PM folds them in, it first copies this
> file whole to `docs/trail/fdr/` — so what you decided, and why, stays readable and citable for good.
>
> **§ 3 is the odd one, and worth reading twice.** The Principal PM writes the FDR *and* is the seat
> most likely to raise an item against it later, cutting the same product's documents into seeds. The
> two are different acts at different times, and § 3 keeps the later one visible instead of letting
> it be quietly folded back into § 1 as though the authoring run had asked it.

Every `R-n`, `PD-n`, `OOS-n` and `RN-n` below is an entry of `products/tracker17/docs/fdr.md`, version 1.
Every `SRS` reference is to `products/tracker17/docs/SRS.md`.

---

## 1. Open issues — behavioural questions with no answer yet

None.

## 2. Choices to confirm — the Principal PM drafted a best-effort answer; confirm or override

### 2.1 Saving a task's edit form changes only the fields the operator changed on that page
- **Drafted into the FDR:** R-47 — "Saving a task's edit form changes only the fields the operator
  changed on that page. A field left as the page showed it keeps whatever value is saved at the
  moment the edit is applied." The Examples table carries one case that rests on it: a title change
  on a task whose assignee has left the list.
- **Rationale:** SRS § 4.2 NFR-3 says a plain field edit made from a stale page "replaces whatever
  the other tab saved for that field". It does not say what happens to the fields the operator did
  not touch. The task's edit form holds four fields (title, priority, assignee, due date). If a save
  writes all four, an operator who opens a task in tab 1, changes its priority in tab 2, and then
  fixes a typo in the title in tab 1 has the priority quietly put back. On this reading that is not
  "that field" but a field the operator never edited, and the change is lost with no refusal and no
  reason, which PRD § UX Notes, Refusals say why, sets itself against. Writing only the changed fields
  keeps NFR-3's stated case (the same field, last save wins, SRS AC-19) and loses nothing else. The
  inputs do not make this call, so it is the owner's.
- **If overridden:** with "a save writes every field the form shows", R-47 becomes that sentence, and
  R-104 and the stale-tab case in SRS AC-19 stand unchanged. R-48 then decides more: a title edit on
  a task carrying an unlisted assignee also re-submits that assignee, so § 2.2's answer governs every
  edit of such a task, not only a change of assignee. The Examples row "`carol` removed from the
  list … the operator changes T's title" moves with § 2.2's answer.
- **Confirm or override:** confirm, with two additions. (1) The reason that holds is SRS § 7 C-5, not PRD § UX Notes, Refusals say why, which covers refused actions and not a silent revert. tracker16-X writes each field on its own path, and its `update_task_priority` reads "a priority-only change leaves the assignee intact" (`task-tracker-X/tasktracker16x/application/task_service.py`). SRS § 4.2 NFR-3 scopes the stale-edit overwrite to "that field", which R-47 keeps. (2) A field counts as changed when its submitted value differs from the value the page showed, not from the value saved now. A save in which no field changed changes nothing and is not refused. A save in which one changed field is refused changes no field (R-100). Reasoning in `products/tracker17/docs/trail/fdr/self_answer-1.md`.

### 2.2 An edit that leaves an unlisted assignee unchanged keeps it, and is not refused
- **Drafted into the FDR:** R-48 — "An edit that leaves a task's assignee unchanged keeps an assignee
  name that is no longer on the list, and is not refused for it."
- **Rationale:** SRS § 3.6 FR-21 says "A task can be assigned only to a name on the list", and FR-22
  says removing a name "leaves that name on every task that already carries it". Neither says what an
  edit does to a task whose name has since left the list. On this reading, keeping a name the task
  already carries is not assigning it, so FR-21 does not reach it, and refusing the edit, or clearing
  the name, would undo FR-22's promise the first time the operator touched the task. Changing the
  assignee to a different name, or clearing it, still follows FR-21 and R-45.
- **If overridden:** with "refuse", any edit of such a task is refused until its assignee is cleared
  or changed to a listed name, and R-48 is replaced by that rule. With "clear", the edit succeeds and
  removes the name, which contradicts FR-22 and would need the SRS changed first. Either way the
  Examples row "`carol` removed from the list … the operator changes T's title" changes, and RN-5
  records the new call.
- **Confirm or override:** confirm, with two additions. (1) SRS § 6 DR-2 says the assignee name "stays valid after the name leaves the assignee list (FR-22)", which the draft did not cite and which carries R-48 most directly. tracker16-X agrees under SRS § 7 C-5: it checks the list only when an assignee is given (`task-tracker-X/tasktracker16x/application/task_service.py`, `update_task_assignee`). (2) Changing such a task's assignee to a listed name or to none replaces the unlisted name, and the unlisted name cannot be chosen again (FR-21). R-48 rests on R-47, decided together in § 2.1. `UXD.md` UX-F9 does not yet show such a name in the edit form and reads as refusing the save, so `products/tracker17/docs/UXD_open_issues.md` § 2.2 carries that change. Reasoning in `products/tracker17/docs/trail/fdr/self_answer-1.md`.

## 3. Raised from downstream — an item raised against the FDR after it settled

None.
