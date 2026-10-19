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
> UXD was settled and had no companion. The run was answering `DESIGN_open_issues.md` and, on item
> 2.7, the confirming press for an irreversible action, read UX-I2 whole. UX-I2 says keyboard focus
> lands on the confirmation, and that the confirmation "appears where the first press was made". It does
> not say which part of the confirmation takes focus, or which part takes the first button's place.
> If either is the confirming control, a second press meant for the first button confirms the
> deletion. Both choices belong to the UXD and not to the design language, because they are
> component anatomy and accessible behaviour. So the run opened this file to carry it, and left
> `UXD.md` unchanged. Its reasoning is in `docs/trail/design/self_answer-1.md` § Companions opened.

---

## 1. Open issues — experience questions with no answer yet

None.

## 2. Choices to confirm — the CDO drafted a best-effort answer; confirm or override

### 2.1 When an irreversible action's confirmation appears, its sentence takes the first button's place and takes focus, and the confirming control does neither
- **Drafted into the UXD:** nothing yet. UX-I2 reads: "When the confirmation appears, keyboard focus
  lands on it, so a keyboard user is not sent back to the top of the page when the first button gives
  way." It also says the confirmation "appears where the first press was made". It does not say
  which part of the confirmation takes focus, or which part takes the place the first button stood
  in. The proposed change adds two sentences to UX-I2. First, the sentence that
  states the consequence appears where the first button stood, followed by the confirming control and
  then the back-out control. Second, focus lands on that sentence and never on the confirming control.
  The operator reaches the confirming control with one Tab, and the back-out control with a second Tab.
- **Rationale:** both halves guard against the same slip, a second press meant for the first
  button. With a pointer, a double click lands on whatever replaced the first button, so that has to
  be words. With the keyboard, UX-I6 makes Enter or Space press the focused button. If focus lands on
  the confirming control, the operator's next Enter or Space confirms. A second press meant for the first
  button would then delete a project and every task in it (`PRD.md` § Core Features, Projects,
  "Deleting a project deletes all of its tasks"). No undo exists (UX-I2), so the confirmation is the
  only guard. SC 3.3.4 Error Prevention keeps that guard required while UX-A5's bar holds (RN-25).
  When focus lands on the sentence, a screen reader reads the consequence before any choice, and the
  same repeated key changes nothing. As written, UX-I2 allows either arrangement, and the SDD and
  the change specs would each pick one. Both are component anatomy and accessible behaviour, which
  the CDO contract puts in the UXD rather than in `DESIGN.md` (`<CORE>/roles/loaders/cdo_global.md`
  § Output, "it belongs in the UXD").
- **If overridden:** if focus lands on the back-out control instead, a repeated key backs out,
  which is also safe. A screen reader then reads "back out" before the consequence. If focus lands on
  the confirming control, a repeated key becomes one destructive press. If the confirming control
  takes the first button's place, a double click does the same.
- **Confirm or override:** confirm, with three additions. The order stands: the sentence that states the consequence, then the confirming control, then the back-out control. Focus lands on the sentence and never on the confirming control. (1) "Takes the first button's place" means the sentence covers the whole spot the first button stood in, so the second click of a double click lands on words and not on a control. Starting at the same edge is not enough. (2) Backing out is the other way the strip gives way. The first button comes back in the same spot, and keyboard focus returns to it. This is the reason UX-I2 already gives for where focus goes when the strip appears: a keyboard user is not sent back to the top of the page. (3) UX-I2 states that this confirmation takes focus on purpose. It is therefore not one of the status messages UX-A5 says are "announced to assistive technology without moving focus". Those are UX-I4's completion line and UX-I3's refusals. The UXD uses the word "confirmation" for both, and without this sentence an SDD reader could take UX-A5 as forbidding the focus move. Reasoning in `docs/trail/uxd/self_answer-2.md`.

## 3. Raised from downstream — an item from a seat that did not write the UXD

None.
