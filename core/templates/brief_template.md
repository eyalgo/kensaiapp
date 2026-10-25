---
version: "1.1.0"
---
<!-- The version above is template-file metadata; it is not copied into a brief. Nor is this block.

     What this is: the COMMON part of a brief — the checked input a skill takes in place of a loose
     idea. No skill reads this file alone. Each skill that takes a brief has its own brief template,
     which names this one, adds the sections that are its own, and says where its brief lands and in
     what order the sections stand. A model reads both and writes one fresh file. Nothing here is
     copied.

     Who writes a brief, and what happens when there is none, is each skill's own to say.

     DRAFTING ONE IN A SESSION. Where a skill's brief is drafted in a session, the session writes it
     from the two templates, shows it to the owner whole, and the skill runs only once they say it
     stands. Their correction is folded in and shown again. This is the one exchange the run has with
     anyone, and it comes before the run. While drafting:
     - `## The ask` holds only the owner's lines, verbatim, each dated. Nothing the session said goes
       there, and nothing the session inferred from what the owner said. A seed was dropped as
       "complete failure" on 2026-10-23 for exactly this: the owner answered a reply holding two
       options with "I suggest what you say", and the cut wrote its own reading of that into the seed
       as the owner's meaning.
     - A line that points back at the session's own words ("what you say", "your option", "like you
       suggested") is not a choice among them. Quote the line as it stands, and before the owner
       confirms, put to them the one sentence of the session's you take it to mean. Their answer, in
       their words, is what goes in `## The ask`.
     - What the session adds goes in `## Evidence`, marked `(session's)`. It may point the skill at a
       file; it grounds nothing the skill writes.
     - A new thing stays a new thing. An ask for a new skill, report or step does not become a change
       to an existing one unless the owner's own lines name that one.
     - The files, images and sites the owner asks the skill to read go in `## Look at`, each with what
       it is for. The session opens them while drafting, so what it quotes in `## Evidence` is what is
       there.

     EVERY CITATION OF A FILE CARRIES ITS QUOTE, on the citation's own line, in double quotes:
         path/to/file.md:L12-L20 "the sentence that is actually there"
     `<CORE>/tools/check_brief_quotes.py <brief>` checks each one before the skill reads anything else,
     and a quote that is not at its lines stops it. The check reads a quote only in the 300 characters
     after its citation and never across a blank line, so keep each quote under about 250 characters
     (elide a longer passage with `…`, quoting its pieces in order), and put no double quote inside
     one. A quote shorter than eight characters is not read as a quote.

     A section with nothing true to say is written as `none`, never left out: an absent section and an
     empty one read the same to a cold reader, and only `none` says somebody looked. -->

# Brief — <the ask, in a phrase>

## The ask

<Only the words of whoever asked, verbatim. Each with where it was said or written:
- the owner in session: the line, then `— owner, <YYYY-MM-DD>, in session`;
- a file, a report or a seed: `path:Lstart-Lend "the words"`.
Nothing here is the caller's own. A term the skill needs that is not in these words, or in the
owner's `## Rulings` below, is not in what it writes.>

## Evidence

<What the caller found, each item with its quote: `path:Lstart-Lend "the text there"`, or a command
and the output it printed. Anything the session itself wrote or concluded is marked `(session's)`; it
can point the skill at something, and it grounds nothing the skill writes.>

## Look at

<Each file, image or site the skill should open, with one line saying what it is for. Or `none`.>

## Out

<What the ask is not, as whoever asked set it out. Or `none`.>

## Rulings

<The owner's rulings that bind this run, each quoted with its date and where it was given. Or `none`.>
