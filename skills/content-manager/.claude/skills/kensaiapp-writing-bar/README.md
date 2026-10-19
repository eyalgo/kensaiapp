# kensaiapp-writing-bar

An instance authors documents, those documents have a reader, and somewhere that reader's needs have to
be written down. `kensaiapp-writing-bar` is the Content Manager's tool for writing them down — step 3 of
`<CORE>/doctrine/setup/setting_up_an_instance.md`, after the instance's identity and Michi are declared
and before its experience layer is authored.

**Its output is the bar**: `system/doctrine/writing_bar.md`, stating what every document authored in
that instance is held to. The step is mandatory and it halts where the instance's identity or 道 Michi
is still a placeholder — core states no bar to fall back on, so a bar nobody stated is not some other
bar quietly holding; it is every future author guessing.

## What It Does

- **Authors the bar**, from `<CORE>/templates/writing-bar-templates/writing_bar_template.md`, grounded in
  three things: what the instance is for (its `kensaiapp.md` identity and `system/michi.md`), its domain
  doctrine, and the writing craft the Content Manager holds. Nothing sits underneath it, so the document
  is the whole bar — a reader holding only that file knows everything that binds.
- **Covers the parts a bar states** — who the reader is, the prose rules that reader needs, how the
  binding words bind, how a claim declares its kind, and what the instance's own subject adds.
- **Names each rule's ground in the bar itself**, so a rule that traces to something this instance
  holds stands on it, and only a rule that needs a ruling reaches the owner.
- **Surfaces rather than interviews.** What it cannot ground goes into a companion open-issues file the
  owner answers on their own time; a re-run folds the answers in, retires the answered companion whole
  to `system/doctrine/trail/writing_bar/`, and deletes the companion when nothing is left. **No companion
  = settled** — whichever way it settled.
- **Never removes a writing bar.** Removing one leaves every document in the instance with no bar at
  all, and the call is the owner's alone; where a run disagrees with a bar on disk it says so in the
  companion and leaves the file untouched.
- **Requires Content Manager posture** — halts outside a `content-manager:` session or the
  `content-manager` agent.

## File Structure

```
kensaiapp-writing-bar/
├── SKILL.md      # the orchestrator: posture, the file loop, path resolution, the commit
├── stack.json    # the split stack the cold-read chain reads: SKILL.md + the authoring prompt
├── README.md     # this file
└── evals/        # behaviour evals — fixtures and assertions
    ├── evals.json
    └── inputs/   # the fixture instances, and the README carrying their annotations
```

`evals/inputs/README.md` is where the fixtures' annotations live rather than inside the fixtures
themselves: a fixture file is read whole by a graded run, so a note inside one reaches the run as
instruction.

## Depends On

- `prompts/rich.md` — the thinking: what a writing bar covers, what
  grounds each rule in it, what a writing bar reaches, and what goes to the owner.
- `<CORE>/templates/writing-bar-templates/writing_bar_template.md` and `writing_bar_open_issues_template.md` —
  the two section shapes.
- `<CORE>/roles/loaders/content_manager_global.md` — why this seat holds an instance's writing bar,
  and the boundary that keeps the seat from being mis-scoped from either side.
- `<CORE>/doctrine/governance/commit_via_builder.md` — how it commits.

## Version and ratification

`kensaiapp-writing-bar` is a **two-file stack**: this orchestrating `SKILL.md` plus the fat authoring
prompt `prompts/rich.md`, which carries what a bar covers, what
grounds each rule, what a bar reaches, and what goes to the owner instead of being settled. Each
file's own frontmatter `version` is its version — this README does not restate either number, so it
cannot drift out of step with them. `stack.json` is the manifest of the two.

**Ratified at `SKILL.md` v6.0.1 with the prompt at v4.2.0 — RATIFY, no conditions.** The verdict
lives with the project that manages the skill, at
[`system/projects/dev-skills/docs/kensaiapp-writing-bar_ratification_verdict.md`](../../../../../system/projects/dev-skills/docs/kensaiapp-writing-bar_ratification_verdict.md)
— the home `<CORE>/doctrine/kaizen/ratification.md` § 5 names. Its reasoning,
the two cases it weighed, the ratifying model, the one recurring defect it names and the two items it
commends to the owner are the verdict's own and are not restated here; a second live copy of them is
what `<CORE>/doctrine/kaizen/ratification.md` forbids. The output it judged is frozen beside it in the
audit instance's vault, at `skills/content-manager/.claude/skills/kensaiapp-writing-bar/evidence/v6.0.1/`.

**The stack on disk is no longer the signed pair.** Both files have moved since the verdict, so the
stack reads *ratified at `SKILL.md` v6.0.1 with the prompt at v4.2.0, plus changes nobody has
signed* — the one fact a verdict cannot carry about itself, which is why this section states it
rather than leaving it to be inferred. Any bump to either file ends the standing claim, whatever the
edit changed (`<CORE>/doctrine/kaizen/ratification.md` § *The claim is about versions, and a bump
ends it*). What ended is the claim, not the verdict — it stays true about the versions it judged,
and re-earning the claim is a fresh round at the current stack, not a repair.

**Its two cases were instances, which is new.** Every prior ratification judged a `product-*` skill,
whose case names a project and resolves through that project's Product path. This bar is instance
altitude, so its cases are the instances themselves — two satellites.

**Its two templates sit outside the stack.** The round ran against
`<CORE>/templates/writing-bar-templates/writing_bar_template.md` @ **v2.3.1** and
`writing_bar_open_issues_template.md` @ **v4.1.0**, which shape the sections the prompt fills — but
neither is in `stack.json`'s substance, matching the `product-*` stacks, so a template bump does not
by itself unsign the pair. Whether it should is unsettled there too, and worth knowing before reading
the paragraph above as a full answer.

## When to Use

Reach for this when **authoring or revising an instance's writing bar** — at instance setup, or any
time after — and when someone asks what bar this instance's own documents are written to. It never
retires a bar: removing one is the owner's act.

Not for: the instance's identity or Michi (`kensaiapp-michi`), the experience layer
(`experience-visual`, `experience-voice`), one product's words (`product-content`), or any product
document.
