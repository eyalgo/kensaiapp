---
version: "2.1.0"
---
<!-- The version above is template-file metadata; it is not copied into the stamped document. -->

<!-- The single source of the shape of an instance's `system/experience/visual_voice_contract.md`.

     MODEL-FACING (`<CORE>/templates/README.md` § The rule — a template's format follows its
     consumer): `experience-visual` reads this file and creates the contract on the first run of the
     pair, and both halves then read the stamped document's own header.

     THE ONE SHAPE IN THIS FOLDER BELONGING TO NEITHER HALF. The other six are one half's each. This
     one is the handoff between them, so both halves resolve to it and neither owns it. What each
     half does with a row is the two skills' own: `experience-visual` creates the file and marks;
     `experience-voice` reads the marks as its work list and records its own rows back.

     PROVENANCE — the format is OURS: a markdown table with four named columns, adopted from no
     vendor. What checks it is ours too, and it is named at FOUR COLUMNS AND NO FIFTH below.

     NO `Status:` / `Owner:` / `Version:` HEADER, unlike every document template in this folder.
     Each of the three would be false here. A `Status:` is set from a companion's absence and this
     file has no companion; an `Owner:` would name one half of a pair that belongs to neither; and
     a handoff accretes rows rather than being revised about a subject.

     A HANDOFF, NOT A COMPANION, and nothing sits beside it. It persists, and its absence is a
     defect rather than a done signal (`<CORE>/doctrine/setup/setting_up_an_instance.md` § The three
     rules, rule 1). What awaits the owner lives in each half's own open-issues companion; this file
     never carries a question.

     FOUR COLUMNS AND NO FIFTH. Which half wrote a row is not stored, because it is derived: a row is
     owed to a medium when its **Mediums** names that medium and no entry with that slug exists in
     that medium's restrictions document. An origin column would give that one fact a second home,
     and the derived form is the one the pairing check reads over slugs — `check_pairing` in
     `<CORE>/tools/experience_gate.py`, which projects this table onto each medium and fails the
     layer on the difference. -->

# Visual ↔ voice contract — <instance name>

> The handoff between this instance's two experience halves. **Every** entry either half writes into
> its restrictions document has a row here, whichever mediums it reaches — with only the crossing ones
> recorded, a missing row and a deliberate single-medium entry look identical. A direction document
> states no entries in this sense and no row here answers for one.
> `experience-visual` creates this file and writes its rows first; `experience-voice` reads the rows
> reaching the verbal medium as its work list and records its own rows back. A row reaching a medium
> whose documents do not yet state it is owed a pass by that medium's author.
> There is no open-issues companion beside this file. Its absence is a defect, not a done signal.

## Rows

| Slug | Kind | Mediums | Reason |
|---|---|---|---|
| `<slug>` | `limit` | `visual` \| `voice` \| `visual + voice` | <one line: why the entry reaches the mediums named> |

<!-- SLUG — the entry's stable name, identical to the slug it carries in the document that states it.
     It is what a counterpart in the other medium shares, and the key the pairing check pairs on.

     KIND — `limit`, and no other value. An entry in a restrictions document is the only thing a row
     records: it is the only thing that carries a slug and a **Reaches**, and the only thing that can
     cross. A value or a line in a direction document carries neither and is not recorded here.
     `<CORE>/doctrine/setup/setting_up_an_instance.md` § The three rules, rule 2 says why, and what
     an author does with direction that would bind the other medium; it is not restated here. The
     column is a single-value one today by that rule, not by oversight.

     MEDIUMS — every medium the entry reaches, and **this column is the mark**. A row naming a medium
     other than the one whose author wrote it is that other author's work list. Use exactly
     `visual`, `voice`, or `visual + voice`, so the set is machine-readable over slugs.

     REASON — one line. Not the entry's wording and not its origin citation: both live in the
     document that states the entry, and a second copy here would drift from it. What belongs here
     is why the entry reaches the mediums it names.

     ONE ROW PER SLUG. An author finding its slug already in the table updates that row and never
     adds a second. Two rows for one slug is the state the shared slug exists to prevent, and the
     pairing check names it `duplicate row`.

     THIS TABLE IS CHECKED, NOT MERELY AGREED. A fence entry with no row here is an `unrowed entry`
     and a row naming a medium whose document does not state it is an `unmet reach`; either one
     fails the layer. What the checker is, and the rest of what it asks, are
     `<CORE>/tools/experience_gate.py`'s — read it there.

     A TABLE WITH NO ROWS IS A COMPLETE STATE, recorded with one line above it saying the run wrote
     no entries — not left as a bare header, which reads as an unfinished file. -->
