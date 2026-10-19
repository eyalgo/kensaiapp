---
version: "1.1.2"
---
<!-- The version above is template-file metadata; it is not copied into the stamped document. -->

<!-- The shape of BOTH companions the `experience-voice` skill writes:
     `system/experience/voice_restrictions_open_issues.md` and `voice_direction_open_issues.md`. One
     shape serves both because the two documents raise the same kinds of item and the owner does the
     same thing with each; two near-identical templates would be a copy that drifts
     (`<CORE>/doctrine/governance/single_source.md`). Substitute <document> per companion.

     MODEL-FACING (`<CORE>/templates/README.md` § The rule — a template's format follows its
     consumer).

     SECTION 3 IS WHY THIS SHAPE IS ITS OWN FILE. The verbal half is the second author, so it is the
     only one of the two that can find a limit originating in its own medium and reaching the other.
     It cannot write the counterpart — that is the other seat's — so the item has to reach the owner,
     and no bucket for questions or confirmations holds it. What such an entry is owed is
     `<CORE>/doctrine/setup/setting_up_an_instance.md` § The three rules, rule 1.

     What qualifies for which section is
     `<CORE>/../skills/content-manager/.claude/skills/experience-voice/prompts/rich.md`'s, not stated here. -->

# <document> open issues — <instance name>

> Companion to `system/experience/<document>.md`. The Content Manager authored that document without
> stopping to interview you; this file holds the calls it made and wants your sign-off on — each with
> the reason behind it, and what moves underneath it if you override — plus the few things it
> genuinely could not settle.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**, then
> re-run `experience-voice`. It folds your answers into the document and drops the resolved items.
> When nothing is left open, `experience-voice` **deletes this file**: no file = that document is
> done.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git refuses to
> remove a file with uncommitted edits in it — so an uncommitted answer stops that run before it can
> commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the Content Manager folds them in, it first copies
> this file whole to `system/experience/trail/voice/` — so what you decided, and why, stays readable
> and citable for good.

---

## 1. Open issues

### 1.1 <the question, in one line>
- **Why it matters:** <what in the document depends on this — which entry, which line, which marker>
- **What was searched:** <where the evidence was looked for and what was found instead>
- **Answer:** <the owner fills this in>

<!-- add 1.2, 1.3, … as needed -->

## 2. Choices to confirm

<!-- Item shapes, one action: the owner confirms or overrides any of them. Number them in one
     sequence and use whichever fits — 2.1 for something written into the document, 2.2 for
     something deliberately left out or left to each product. -->

### 2.1 <the decision, in one line>
- **Written into the document:** <the fence entry, the inherited line, or the marker — quoted>
- **Grounds:** <the evidence it derives from — a file and line, an owner statement, a standard this instance holds — or "none: the Content Manager's call, made to keep the layer coherent">
- **If overridden:** <the blast radius of not taking the draft — which other entries, inherited lines
  or markers derive from this one, and whether a contract row moves with it>
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

### 2.2 <deliberately absent — a category with no shared answer, or a limit not fenced>
- **Reason recorded in the document:** <why nothing is stated there>
- **Confirm or override:** <"confirm", or "override: state it, because <…>">

<!-- add 2.3, 2.4, … as needed -->

## 3. Owed to the visual half

<!-- One item per entry written in this run that originates here and also reaches the visual medium.
     Nothing is asked of the owner about the wording; what is asked is whether the crossing is real,
     and the item clears once the visual pass it names has run. Omit this section entirely when this
     run wrote no such entry — an empty section reads as an open item. -->

### 3.1 `<slug>` — <short title>
- **The limit, in verbal terms:** <as written into `voice_restrictions.md`>
- **What reaches the other medium:** <the thing a reader would catch without reading a word>
- **Confirm or override:** <"confirm: run `experience-visual` again", or "override: this reaches words only, because <…>">

<!-- add 3.2, 3.3, … as needed -->
