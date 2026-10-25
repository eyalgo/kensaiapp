---
version: "1.1.0"
---

# seeds-from-idea — the idea cut's own tightenings

This file is the `seeds-from-idea` skill's lens. It extends `<CORE>/prompts/principal_pm_cut_seeds.md`
for an idea cut only: it tightens three things in it, and it holds the cut's output to the bar
`seeds-from-product-docs` holds its own to. **The base's idea is, for this cut, the brief**
(`templates/brief.md`): where the base speaks of an unstructured idea and its claims, read the brief's
`## The ask` and the claims in it. How those claims are grounded is unchanged.

**Read the base first, in full, and read it as the base this file extends.** Everything about cutting
an idea is stated there and is not restated here. Apply all of it, except where a section below names
a line of the base and replaces it. Where the base and this file disagree, this file governs.

Idea cuts have been killed for producing more seeds than the owner asked for (commits `24a9cb6fe`
and `b271198a1` record the owner's rulings). Seeds have been withdrawn for citing and proving on a
dropped attempt's output (commit `c83a1d791`). The owner agreed these three tightenings on
2026-10-12. The base also serves `seeds-from-product-docs`, which is why they live
here and not in it.

The output bar is the owner's call of 2026-10-24: "The output of the *idea* should be like of
*product-docs*", "*without touching* `seeds-from-product-docs`". So § *The output bar* below points at
that skill's lens, `<CORE>/../skills/principal-pm/.claude/skills/seeds-from-product-docs/prompts/rich.md`,
where its rules already say what is wanted, and states here only what an idea changes in them. That
lens is read, never edited, from here.

---

## How many seeds — one, unless the idea's own words name more

This replaces the base's § *One idea becomes 1 to N seeds*, at the line *"**One idea yields 1 to N
seeds**, and N is decided by the work rather than by the shape of the idea."* That line does not
apply to this cut. The same sentence in `<CORE>/roles/loaders/principal_pm_global.md` § *Cutting
seeds from an idea*, *"**One idea yields 1 to N seeds.**"*, does not apply to it either.

**The default is one seed: the thing the idea's own words ask for.** Cut a second or later seed only
where the idea's own words name that piece too. The idea's words are whoever wrote it: the owner's,
when the idea is something the owner said, and the source's, when it is a finding a run surfaced, a
note, or a seed someone else wrote.

**Everything else the cut notices is not a seed.** It goes in the seed's `## Out (later / elsewhere)`,
or in the run report under "could also be cut".

The rest of that base section still binds every seed you do cut: the three tests, the four defects,
and the station checklist.

## Routing seeds — only when the owner asks for one

This tightens the base's § *When a routing seed is earned*, at its line *"a cut whose seeds span
projects earns one"*, and the loader's matching line in § *Cutting seeds from an idea*, *"Where a
cut's seeds span projects it earns one"*.

**Plant a routing seed only when the owner asks for one.** Seeds that span projects do not earn one on
their own. Where the owner asks for one, the rest of that base section says how to write it.

## Dead inputs — never grounding, never a proof subject

This adds to the base's § *Sweep the seedbeds before you write one*.

**Nothing in a `drop/` folder, nothing reverted, and no output of a dropped attempt may be cited as
grounding or used as a proof subject.**

---

## The output bar — a seed cut from an idea reads like one cut from the documents

Six rules. Each adds to the base; where one names a section of the docs lens, read it there.

### 1. Every term in a seed is in the brief's ask

The brief (`templates/brief.md`) is the whole input. **A seed says nothing the brief's `## The ask` does
not say**, in its words or in words the evidence shows on disk. The owner's `## Rulings` in the brief
are the owner's words too, and ground a term the same way; the brief's `## Out` is the first thing the
seed's `## Out` carries. The owner's call, 2026-10-24. A term that is neither — an option the
session offered, a skill nobody named, a scope the cut inferred — is not in the seed; it goes in the run
report under "could also be cut", or nowhere.

The seed's `## Source` **quotes the ask lines it was cut from, verbatim**, each with where it was said,
and names the brief by its path — the docs lens's § *Every seed traces back to the documents it was
drawn from*, "cite the section and quote the phrase you cut against", applied to an ask instead of a
document. Paraphrase is not a citation: the 2026-10-23 seed this rule comes from paraphrased the owner
and put its own reading in their mouth.

**An ask that changes an earlier ruling is followed, and the change is reported.** Where the sweep
finds a seed or a record holding an owner's ruling the ask goes against, the ask wins — the owner's
later words, and their rulings evolve. The new seed names the old ruling by its seed's triple and
quotes it in `## Relation to existing work`; the report lists it under *Earlier rulings this ask
changes*; the old seed is not edited, since this run edits no document it read. The owner's call,
2026-10-24.

### 2. Four kinds of seed

The docs lens's § *Four kinds of seed* binds here — downstream, documentation, upstream and scaffold,
with what each lands as and what retires it. An idea reaches each kind this way:

- **Downstream** — the ordinary kind: the ask is work on the product.
- **Documentation** — the ask names a document that is not there. Check the absence, as that section says.
- **Upstream** — the ask is for a change only a definition-tier document can make: the PRD, the SRS, the
  UXD, the SDD, the FDR, an ADR or the NFDR. Raise the item on that document's companion and write the
  seed that tracks it, both by hand, exactly as that section says. Never edit the document.
- **Scaffold** — the ask needs a project that does not exist.

### 3. Order, when the ask names more than one piece

The one-seed default above stands. Where the ask's own words name more pieces, order the seeds by the
docs lens's § *Priority and incremental slicing*: slice through the product, not across it; a hard
dependency first, risk early everywhere else; a quality seed ahead of a feature seed. Its parts about
the SDD's § 7 and § 8 have no idea counterpart and do not apply.

### 4. A security seed keeps its flag

Where the brief's `## Security source` names a security-report line, the seed cut from it is a
**security seed**: its `## What it is` says so, and its `## Source` names the unit by its triple,
`<project> · tobiishi · <key>`, and quotes the report's line — the docs lens's § *Inputs — four you draw
from, five you read against*, the NFDR bullet. The PM can tell at the pick that it is one only if it
does (`<CORE>/docs/michi_agari.md` § *How we work — walking a project's journey*, step 1).

### 5. The close accounts for the whole ask

On a clean close the report — the file beside the brief, in the shape of `templates/report.md`
(`SKILL.md` § *The cut's report*) — says, for **every line of the brief's `## The ask`**, which seed carries it,
or why no seed does — out of scope, carried by a seed already in a pool, or left for a later cut and
what would make it ready. An ask line the report does not account for cannot be told apart from one
the cut never read. It also names **every upstream item raised**, by the companion's path and the item,
so the owner knows which documents are owed a re-run.

### 6. An unsettled input stops the cut

Three things stop the run before it writes a seed, beside the base's four cases:

- the brief's quote check printed a line, or its `## The ask` is empty — the skill's Step 1;
- the ask cites a definition-tier document that is still `Draft`, or carries a standing
  `*_open_issues.md` companion, and the seed would be cut against what it says — the docs lens's fifth
  stop, in its § *Inputs — four you draw from, five you read against*, including its exception: a
  security seed is cut before this stop;
- in a session, the owner has not confirmed the brief.

