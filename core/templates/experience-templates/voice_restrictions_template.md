---
version: "1.4.2"
---
<!-- The version above is template-file metadata; it is not copied into the stamped document. -->

<!-- The single source of the shape of an instance's `system/experience/voice_restrictions.md`.

     MODEL-FACING (`<CORE>/templates/README.md` § The rule — a template's format follows its
     consumer): the `experience-voice` skill reads this file and authors a fresh document, so
     everything here may explain itself and none of it survives into the stamped result.

     WHAT THIS FILE OWNS: the sections of the document and their order, and nothing else. How an
     entry is derived, what evidence one needs, which medium a limit reaches, and how it is worded
     so a reader can check it are `<CORE>/../skills/content-manager/.claude/skills/experience-voice/prompts/rich.md`'s —
     the authoring body this shape is stamped under, declared on both sides
     (`<CORE>/doctrine/setup/authoring_layers.md` § The carriers).

     WHAT IT IS NOT: a product's `CONTENT.md`. This document is the instance's fence — the verbal
     limits every product under the instance holds. What one product says to its users is that
     product's own document, with its own owner
     (`<CORE>/doctrine/setup/kensaiapp_structure.md` § Instance-shared doctrine).

     WHY THE ENTRY BLOCK CARRIES THREE FACTS AND NOT TWO: the limit is what a checker reads, the
     origin is what makes it binding, and what it reaches is what ties it to its counterpart in the
     other medium under one slug. Drop the third and an entry that also binds the visual medium
     becomes indistinguishable from one that does not. -->

# Voice restrictions — <instance name>

**Status:** Draft | Settled | Locked
<!-- Draft = the companion `voice_restrictions_open_issues.md` is on disk, so something awaits the
       owner. The document itself is complete; every entry is written.
     Settled = the companion is gone. Nothing awaits the owner.
     Locked = ratified. The owner's act, never the run's. -->
**Owner:** Content Manager
**Version:** <n> — <one line on what this revision changed **about the subject** — what the
instance's products may now say, or may no longer; never the authoring cycle, so no "folded in
the owner's answers">

## 0. What governs this file

The rules this document is authored under are `<CORE>/doctrine/setup/setting_up_an_instance.md`
§ The three rules. Read them there. Nothing in this file repeats them, and a copy that disagrees is
a bug in the copy (`<CORE>/doctrine/governance/single_source.md`).

<!-- Carry the two sentences above into the stamped document as they stand — they are the § 0, not
     guidance about it. Point; never restate. This section is first so that whoever hand-edits the
     document meets the governing rules before they reach anything they might change. -->

## 1. What this fence is

<One short paragraph: these are the verbal limits every product under this instance holds, and a
product may not relax one. Say which kinds of writing the instance actually produces — interface
strings, documentation, notifications, anything read aloud — so a reader knows what the fence is
over. No product is named here.>

## 2. Entries

<One block per limit. The slug is the entry's name, and a limit that also reaches the visual medium
shares its slug with the entry that states it there.>

### `<slug>` — <short title>

- **The limit.** <What no product may say, or may say in a certain way, stated so that someone
  holding one string can tell whether it holds. A limit nobody can check by reading is a direction,
  and it belongs in `voice_direction.md` instead.>
- **Where it comes from.** <The owner's call, a regulator's rule, a standard this instance holds, or
  a rule already stated in `system/doctrine/` — with the citation.>
- **Reaches.** <The scope: every product, or the named surfaces.> <The medium, in the values
  `<CORE>/templates/experience-templates/visual_voice_contract_template.md`'s **Mediums** column
  declares — a limit reaching both shares its slug with the entry that states it there.>

<!-- TWO SLOTS, BOTH REQUIRED — a scope and a medium. They sit on different axes and neither answers
     the other: naming every product says nothing about which medium the limit reaches, and naming a
     medium says nothing about how far it reaches. Fill both. Leave one unfilled and its `<…>` ships
     into the stamped document, where it is the entry saying for itself that it is unfinished; delete
     one and the entry contradicts this line. The contract's Mediums cell is transcribed from this
     field, so a spelling of your own — `voice only` for what that column calls `voice` — lands a row
     outside the set it declares machine-readable, and a reader who has to infer the cell is
     guessing. -->

## 3. Deliberate absences

<Where this instance has decided a whole category of speech is not fenced — humour, second person,
sales language, whatever it is — say so here with one line of why, marked `n/a`, so a reader can
tell a decision from a hole. A fence with no entries at all is a legitimate state and is recorded
here, not left blank.>

## 4. Review notes

<Why each entry is worded the way it is, and what authorized it — an owner's answer folded from the
companion, or a citation. On a revision, every change to a settled entry carries the reason that
authorized it. The owner's answered companions are retired whole to `system/experience/trail/voice/`,
so their exact words stay citable; this section is where *this document* says why its entries are
what they are.>

- **RN-1:** <the entry, and what grounded it> — *because* <reason> *(re: `<slug>`; source: <owner answer / citation>)*
