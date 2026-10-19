---
version: "4.2.2"
---
<!-- The version above is template-file metadata; it is not copied into the stamped document. -->

<!-- The shape of the companion the `kensaiapp-writing-bar` skill writes:
     `system/doctrine/writing_bar_open_issues.md`.

     MODEL-FACING (`<CORE>/templates/README.md` § The rule — a template's format follows its
     consumer).

     SAME TWO SECTIONS AS EVERY SIBLING COMPANION, in the same order and numbered the same way —
     `srs`, `uxd`, `prd`, `agari` and the rest. A reader who knows one knows this one, and a rule
     elsewhere that names "the companion's § 2" means the same section here.

     What qualifies for which section is `<CORE>/../skills/content-manager/.claude/skills/kensaiapp-writing-bar/prompts/rich.md`'s, not
     stated here. -->

# Writing bar open issues — <instance name>

> Companion to `system/doctrine/writing_bar.md` — the bar every document authored in this instance is
> held to. The Content Manager settled that bar without stopping to interview you; this file holds
> the calls it made and wants your sign-off on, each with the reason behind it and what moves
> underneath it if you override, plus the few things it genuinely could not settle.
> **Answer inline** — fill each **Answer** / **Confirm-or-override** slot — **commit this file**,
> then re-run `kensaiapp-writing-bar`. It folds your answers in and drops the resolved items. When
> nothing is left open it **deletes this file**: no file = the writing bar is settled.
>
> **Commit before re-running.** The run that finishes a round removes this file, and git refuses to
> remove a file with uncommitted edits in it — so an uncommitted answer stops that run before it can
> commit anything, and the round's work is left on the floor.
>
> Your answers are never thrown away. Each time the Content Manager folds them in, it first copies
> this file whole to `system/doctrine/trail/writing_bar/` — so what you decided, and why, stays
> readable and citable for good.

---

## 1. Open issues

<!-- Things the run could not settle from the evidence. Omit the section when there are none. -->

### 1.1 <the question, in one line>
- **Why it matters:** <what in the bar depends on this — which rule, which line>
- **What was searched:** <where the evidence was looked for and what was found instead>
- **Answer:** <the owner fills this in>

<!-- add 1.2, 1.3, … as needed -->

## 2. Choices to confirm

<!-- Item shapes, one action: the owner confirms or overrides any of them. Number them in one
     sequence and use whichever fits — the 2.1 shape for something written into the writing bar, the
     2.2 shape for something deliberately left out. Omit the section when there is nothing in it. -->

### 2.1 <the rule, in one line>
- **Written into the writing bar:** <the bar as worded, quoted>
- **Grounds:** <what it derives from — a file and line, this instance's Michi or domain doctrine, a regulator's requirement, a named public standard given by name and publisher since it has no path here — or "none: the Content Manager's call, made to keep the bar coherent">
- **Confirm or override:** <"confirm", or "override: <what to do instead>">

### 2.2 <deliberately absent — a category this writing bar states nothing about>
- **Reason recorded in the writing bar:** <why nothing is stated there>
- **Confirm or override:** <"confirm", or "override: state it, because <…>">

<!-- add 2.3, 2.4, … as needed -->
