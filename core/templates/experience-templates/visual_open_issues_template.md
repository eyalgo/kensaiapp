---
version: "1.2.1"
---
<!-- The version above is template-file metadata; it is not copied into the stamped document. -->

<!-- The shape of BOTH companions the `experience-visual` skill writes:
     `system/experience/visual_restrictions_open_issues.md` and
     `visual_direction_open_issues.md`. One shape serves both because the two documents raise the
     same two kinds of item and the owner does the same thing with each; two near-identical
     templates would be a copy that drifts (`<CORE>/doctrine/governance/single_source.md`).
     Substitute <document> per companion. The verbal half states its own shape in
     `voice_open_issues_template.md` beside this file, and neither binds the other.

     MODEL-FACING (`<CORE>/templates/README.md` § the two-consumer table).

     Matched to `<CORE>/templates/product-templates/design_open_issues_template.md` — same buckets,
     same answer-inline-then-re-run loop, same absence-is-done signal — because an owner who has
     answered one of these should not have to learn a second shape. What sends an item to § 1 rather
     than § 2 is `<CORE>/../skills/cdo/.claude/skills/experience-visual/prompts/rich.md` § Which companion section an item
     goes in. Which of § 2's two item shapes fits is this file's, at § 2 below. -->

# <document> open issues — <instance name>

> Companion to `system/experience/<document>.md`. The CDO authored that document without stopping
> to interview you; this file holds the calls it made and wants your sign-off on — each with the
> reason behind it, and what moves underneath it if you override — plus the few things it genuinely
> could not settle.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `experience-visual`. It folds your answers into the document and drops the resolved items.
> When nothing is left open, `experience-visual` **deletes this file**: no file = that document is
> done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git refuses to
> remove a file with uncommitted edits in it — so an uncommitted answer stops that run before it can
> commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the CDO folds them in, it first copies this file
> whole to `system/experience/trail/visual/` — so what you decided, and why, stays readable and
> citable for good.

---

## 1. Open issues

### 1.1 <the question, in one line>
- **Why it matters:** <what in the document depends on this — which entry, which value, which marker>
- **What was searched:** <where the evidence was looked for and what was found instead>
- **Answer:** <the owner fills this in>

<!-- add 1.2, 1.3, … as needed -->

## 2. Choices to confirm

<!-- Item shapes, one action: the owner confirms or overrides any of them. Number them in one
     sequence and use whichever fits — 2.1 for something written into the document, 2.2 for
     something deliberately left out or left absent. -->

### 2.1 <the decision, in one line>
- **Written into the document:** <the fence entry, the value, or the marker — quoted>
- **Grounds:** <the evidence it derives from — a file and line, an owner statement, a standard this instance holds — or "none: the CDO's call, made to keep the layer coherent">
- **If overridden:** <the blast radius — what else in the layer moves, and how>
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

### 2.2 <deliberately absent — a category with no shared value, or a limit not fenced>
- **Reason recorded in the document:** <why nothing is stated there>
- **If overridden:** <the blast radius — what every product inherits once it is stated>
- **Confirm or override:** <"confirm", or "override: state it, because <…>">

<!-- add 2.3, 2.4, … as needed -->
