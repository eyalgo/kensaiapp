---
version: "1.5.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

<!-- STAMPED FROM by `skills/companion/.claude/skills/companion-self-answer/SKILL.md` § Step 5, into
     `trail/<doc>/self_answer-<N>.md`, the trail of the document this run answered.

     THE HEADINGS BELOW ARE THE PARSER'S CONTRACT, and it has three parts.
     `<CORE>/tools/reporters.py`'s `companion-self-answer` reporter reads this file for the
     completion message the owner gets hours later, and each part fails differently:

       1. FIVE HEADINGS ARE REQUIRED — `## Header`, `## Items worked`, `## Left for the
          owner`, `## Skipped`, `## Companions opened`. They are how the reporter tells a
          report from any other file at that path. Rename or drop one and it stops reporting
          a tally at all: it says the file is not in the template's shape, names its path, and
          sends the owner to read it. Keep all five even when a section is empty — write
          "None this run." under the heading, because an omitted heading and an empty one are
          not the same fact to a parser that never sees the file being written.
       2. `## Launchers owed` IS READ BY ITS HEADING — its bullets share a shape with
          `## Companions opened`'s, so the reporter takes them from inside this section and
          nowhere else. Drop the heading and the message loses the one thing the owner acts
          on: what to run next. It falls back to naming the documents a round is owed on,
          which is a document name where a command should be.
       3. THE `**Verdict:**` FIELD IS READ ANYWHERE IN THE FILE, by field and not by section.
          Drop or rename it on an entry and that entry silently leaves the split.

     Reordering the sections changes nothing the reporter reads — keep the order below for the
     person reading it, not for the parser.

     Every `**Verdict:**` value is one of the prompt's six literals, verbatim:
     answered | confirmed | confirmed with addition | overridden | raised upstream |
     left for the owner. `## Left for the owner` entries carry the literal `left for the
     owner` too — the same field, the same six-value set, in every entry the report has —
     so the reporter's one scan for the field is the whole tally: no per-section counting,
     no inferring a split from prose. `## Unnamed verdict` entries carry no `**Verdict:**`
     field at all, by construction: they are exactly the items none of the six covers, and a
     borrowed literal there would mis-tally the split.

     Write each section as you decide its items (SKILL.md § Step 4's own rule — item by item,
     never in one pass at the end), and when a section has nothing, keep its heading and write
     "None this run." under it — a missing heading reads to the parser as never written, not
     as empty. TWO SECTIONS ARE THE EXCEPTION and are omitted whole rather than kept empty:
     `## Unnamed verdict` and `## Raised on this document`. Each says so in its own note. The
     difference is that the five required headings answer a question every run has an answer
     to — how many items, how many left, how many skipped — while these two record something
     that either happened or did not, where an empty section says nothing an absent one does
     not.

     `## Companions opened`'s bullets carry an ACTION WORD — opened | appended | updated —
     because the three are different things for the owner to walk into: a document that newly
     reads open, one that gained a question, one that had a question rewritten. -->

<!-- Added 2026-08-29 on the owner's call, with the run's new reaches: the answer under a
     left-for-the-owner entry, `## Raised on this document`, and the action word. -->

# Self-answer report — <the document the companion belongs to>

## Header

- **Companion:** <path to the companion this run answered>
- **Document:** <the document the companion belongs to>
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v<the prompt version this run read>
- **Date:** <YYYY-MM-DD>
- **Sources re-read:** <every source outside this repository that an answer this run gave rests on,
  named and re-read at the source per the prompt's check 3, each with what it said. `None` where no
  answer rested on one, and `unreachable: <which>` where one could not be read. A source the record
  merely repeats is not one this run read.>

## Items worked

<One `###` entry per item this run decided this pass — every verdict except "left for the owner".
Keep this heading and write "None this run." beneath it when nothing was decided.>

### <n>.<m> — <the item's heading, as the companion states it>

- **Bucket:** <the `## ` section heading the item sat under in the companion>
- **Verdict:** answered | confirmed | confirmed with addition | overridden | raised upstream
- **Why:** <the reasoning, at the prompt's § Tone bar — plain language, the verdict first,
  standalone from the other entries>

<!-- repeat one ### block per item worked -->

## Left for the owner

<Every item this run could not decide in the owner's seat — check 1's third outcome. This list is
the point of the file: the owner reads it to learn which items are still theirs, so the *why* has to
stand on its own without the companion open beside it. Keep this heading and write "None this run."
beneath it when there are none.>

### <n>.<m> — <the item's heading, as the companion states it>

- **Bucket:** <the `## ` section heading the item sat under in the companion>
- **Verdict:** left for the owner
- **Why:** <why this is the owner's call and not the run's — the risk, the taste, the
  commitment, or the ground the run could not see, named rather than gestured at>
- **The answer I would have given:** <the answer this run reached before deciding the call was
  not its to make. The prompt requires it: leaving the decision does not excuse leaving the
  question, and this line is what the owner reads first. The one case it may say "none" is an
  item whose supporting text is too wrong to read a question out of — say that in those words.>

<!-- repeat one ### block per item left -->

## Unnamed verdict

<Optional. Only where the run met an item needing a verdict outside the prompt's six named ones —
"the set is open" (`<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` § The set is open). Omit this whole section,
heading and all, when the run met none.>

### <n>.<m> — <the item's heading, as the companion states it>

- **Bucket:** <the `## ` section heading the item sat under in the companion>
- **Would-be verdict:** <the run's own word for what it did>
- **Why none of the six fit:** <the reasoning the prompt asks be reported>

<!-- repeat one ### block per item, if any -->

## Skipped

<Everything not worked and not left for the owner — a slot already filled, an item addressed to the
producing skill rather than the owner, an item whose supporting text is wrong, a document with no
companion template on disk. Keep this heading and write "None this run." beneath it when there are
none.>

- **<n>.<m> — <the item's heading>** — <why it was skipped>

<!-- one bullet per item skipped -->

## Raised on this document

<Optional. Only where the run judged the document it was answering owed a change no item raised,
and appended one item to its own companion (SKILL.md § Raising a change on the companion you are
answering). Omit this whole section, heading and all, when the run raised nothing — like
`## Unnamed verdict` and unlike the five required headings, its absence is a fact and not a gap.>

### <n>.<m> — <the heading of the item this run appended>

- **What the document is owed:** <the change, in one line>
- **Why it is worth a cycle:** <which of the prompt's grounds this meets, named as that file names
  it — `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` § The items are not the whole of what a document is owed —
  and the measurement or citation behind it. The grounds are not listed here: they have one home,
  and a second copy is the one that drifts.>

<!-- repeat one ### block per item raised, if any -->

## Companions opened

<Every companion this run opened, appended to, or revised an item on — on a document other than
the one it was answering (SKILL.md § When a change belongs to another document). Keep this heading
and write "None this run." beneath it when there are none.>

- **<path to the companion>** — **<opened | appended | updated>** — companion to `<the document it
  belongs to>`, landed in commit `<the commit SHA that carried it>`
- **<path to the companion>** — **updated** — companion to `<the document it belongs to>`, item
  `<n>.<m>`, which previously read `<what it said before>`, landed in commit `<the commit SHA>`

<!-- ONE BULLET SHAPE, and every bullet carries `companion to \`<doc>\`` — the reporter matches on
     that field, so a bullet written without it is not a differently-shaped entry, it is an entry
     that never reaches the owner at all. The `updated` line above is the same shape with two
     clauses added, not a second form. Measured 2026-08-29: the second form as first written
     omitted the field and the reporter dropped it whole, which took `updated` — half of what the
     run may now do — out of the notification silently. Caught by the reporter's own code-integrity
     pass at `55bab7cb`, not by anyone reading this file.

     One bullet per companion touched. The action word is what tells the owner whether a document
     newly reads open, gained a question, or had one of its questions rewritten — three different
     things to walk into. An `updated` entry carries what the item said before, because the file
     itself no longer does. -->

## Launchers owed

<The list SKILL.md § Step 6 derives and stops at — one entry per document a round is now owed on,
this run's own included: the producing skill for the document this run answered, and
`companion-self-answer` for each companion it opened elsewhere that the answer launcher can find
(SKILL.md § Step 6 says which those are; any other keeps its producing skill). Derive each producing
skill's launcher there (its `launcher.md`, else its own folder, else the fixed prompt-literal grep,
else the honest absence); never write a path you have not seen. When an answer this run wrote into a
slot owes a field of a project's card, the list ends with one more bullet, for that card: the third
bullet below, with the real project name in place of both `<project>`s, written once per card
however many answers or fields owe it, after every document's bullet. An item whose verdict is
`left for the owner` or `raised upstream` wrote no answer into a slot here, so it never owes the
card. SKILL.md § Step 6 says which answers and fields count. A run whose answers owe no card field
leaves the card's bullet out. Keep this heading and write "None this run." beneath it when the run
committed nothing. This is the section the completion notification turns into what the owner runs
next, so an entry is the command, not a description of it — the filled-in invocation Step 6
requires: the launcher path and its positional arguments, with the real values in place, and none
of the `# USAGE` block's bracketed flags. THE BULLET ENDS AT THE COMMAND: nothing follows it, not
the block's flag descriptions, not a condition, not an ordering. This section is read by machines —
the reporter today, and the chain that walks the owed set unattended — and a tail is either
boilerplate the reader already has or a condition that goes stale in the file carrying it. Both
measured 2026-08-30 on one live report: a bullet that carried the USAGE block's flag lines, and a
bullet that gated its command on the owner answering an item the same report tallied as already
answered. Step 6 carries that report's citation. What a tail wants to say is already carried where
it stays true — the `**Verdict:**` field, `## Left for the owner`, and `## Companions opened`.>

- **<the document a round is owed on>** — `<the exact command to run it>`
- **<the document with no launcher>** — no launcher; run `<the producing skill>` from a
  `<the posture its own file requires>` session
- **system/projects/<project>/project.md** — `<CORE>/launchers/product-card/launcher.sh <project>`

<!-- one bullet per document owed a round, and then, only when an answer this run wrote owes a field
     of a project's card, one bullet for that card, last and once -->
