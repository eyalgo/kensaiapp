---
version: "1.3.2"
---
<!-- The version above is template-file metadata; it is not copied into the stamped document. -->

<!-- The single source of the shape of an instance's `system/experience/visual_restrictions.md`.

     MODEL-FACING (`<CORE>/templates/README.md` § the two-consumer table): the `experience-visual`
     skill reads this file and authors a fresh document, so everything here may explain itself and
     none of it survives into the stamped result.

     WHAT THIS FILE OWNS: the sections of the document and their order, and nothing else. How an
     entry is derived, what evidence one needs, and when a limit belongs at this layer at all are
     `<CORE>/../skills/cdo/.claude/skills/experience-visual/prompts/rich.md`'s — the authoring body this shape is stamped
     under, declared on both sides (`<CORE>/doctrine/setup/authoring_layers.md` § The carriers).

     PROVENANCE — the format is OURS, and that is a deliberate difference from the sibling shape in
     this folder. `visual_direction_template.md` follows an external vendor format with a linter, so
     a vague value there is caught by a machine. No vendor publishes a schema for a *fence*, so
     there is nothing external to adopt and nothing mechanical to check this document — the skill
     states the consequence flatly (`skills/cdo/.claude/skills/experience-visual/SKILL.md` § Step 3: this
     document has no machine format and is never linted). What stands where that linter stands is
     `<CORE>/../skills/cdo/.claude/skills/experience-visual/prompts/rich.md` § An entry needs an origin and its closing
     checkability sentence in § How it reads. Do not soften either.

     WHAT IT IS NOT: a product's `DESIGN.md`. This document is the instance's fence — the visual
     limits every product under the instance holds. A product's own token values live only in that
     product's design language (`<CORE>/roles/loaders/cdo_global.md` § What you own). -->

# Visual restrictions — <instance name>

**Status:** Draft | Settled | Locked
<!-- Draft = the companion `visual_restrictions_open_issues.md` is on disk, so something awaits the
       owner. The document itself is complete; every entry is written.
     Settled = the companion is gone. Nothing awaits the owner.
     Locked = ratified. The owner's act, never the run's. -->
**Owner:** CDO
**Version:** <n> — <one line on what this revision changed **about the fence** — which entry
appeared, moved or was relaxed. Not the authoring cycle: no "folded in the owner's answers".>

## 0. What governs this file

The rules this document is authored under are `<CORE>/doctrine/setup/setting_up_an_instance.md`
§ The three rules. Read them there. Nothing in this file repeats them, and a copy that disagrees is
a bug in the copy (`<CORE>/doctrine/governance/single_source.md`).

<!-- Carry the two sentences above into the stamped document as they stand — they are the § 0, not
     guidance about it. Point; never restate. This section is first so that whoever hand-edits the
     document meets the governing rules before they reach anything they might change. -->

## 1. What this fence is

<One short paragraph: these are the visual limits every product under this instance holds, and a
product may not relax one. Say which surfaces the instance actually has, so a reader knows what the
fence is over. No product is named here — an entry that could only belong to one product belongs in
that product's own documents.>

## 2. Entries

<One block per limit. The slug is the entry's name and the key the pairing check reads; it is also
what a limit reaching more than one medium shares with its counterpart entry.>

### `<slug>` — <short title>

- **The limit.** <What no product may do, stated in visual terms and stated so that someone looking
  at a screen can tell whether it holds.>
- **Where it comes from.** <The owner's call, a regulator's rule, a standard this instance holds —
  with the citation. A limit with no origin is not a limit; it is a preference, and
  `<CORE>/doctrine/governance/where_taste_appears.md` says where a preference may be expressed.>
- **Reaches.** <The scope: every product, or the named surfaces.> <The medium: `visual only`, or the
  other medium this limit also reaches — the counterpart entry carries the same slug.>

<!-- TWO SLOTS, BOTH REQUIRED — a scope and a medium. They sit on different axes and neither answers
     the other: naming every product says nothing about which medium the limit reaches, and naming a
     medium says nothing about how far it reaches. Fill both. Leave one unfilled and its `<…>` ships
     into the stamped document, where it is the entry saying for itself that it is unfinished; delete
     one and the entry contradicts this line. State the medium in the entry's own words — the
     contract's Mediums cell is transcribed from this field, and a reader who has to infer it is
     guessing. -->

## 3. Deliberate absences

<Where this instance has decided a whole category is not fenced, say so here with one line of why.
The house convention for a deliberate absence is `n/a` plus that one line
(`<CORE>/../skills/cdo/.claude/skills/product-uxd/prompts/rich.md`), so a reader can tell a decision from a hole. A fence with no
entries at all is a legitimate state and is recorded here, not left blank.>

## 4. Review notes

<Why each entry is worded the way it is, and what authorized it — an owner's answer folded from the
companion, or a citation. On a revision, every change to a settled entry carries the reason that
authorized it. The owner's answered companions are retired whole to
`system/experience/trail/visual/`, so their exact words stay citable; this section is where *this
document* says why its entries are what they are.>

- **RN-1:** <the entry, and what grounded it> — *because* <reason> *(re: `<slug>`; source: <owner answer / citation>)*
