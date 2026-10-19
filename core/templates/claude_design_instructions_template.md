# Claude Design — instructions for this repository

This repository is **<instance>**. It contains **no product**. It is the *managing* repository:
it holds the rules every product built here obeys, and it points at where each product actually lives.

**It names no product on purpose.** Which product a run is for is told to you in the conversation, not
written here — this file is the instance's, and it is the same file whichever product you are asked to
work on.

**It names no input files either, on purpose.** A list of filenames reads as a list of requirements,
and a design system may be asked for at any stage — including before the documents such a list would
name exist. Everything below tells you **where to look and what to do with whatever is there**. Read
the folders; do not expect a particular file, and never treat one you cannot find as a blocker.

**It restates none of this repository's rules, on purpose.** The rules are pointed at and read from
their own files. A summary here is a second thing to drift, and a summary that drifts into asserting
what its source declined to state is worse than none.

**Every path written below is inside this repository, and that is deliberate.** One of the two routes
links this folder and copies selected files out of it, so a path leading anywhere else is a string in
a file rather than a link anything follows. One path does leave — the product's own repository — and
it is not written here: you read it from a file inside this folder, and § *Two repositories, and you
need both* says which. **Do not add a path that leaves this folder to this file.** An instance's shared
foundation store may sit in a different repository entirely, so a pointer into it resolves for one
route and is dead for the other.

## Both routes reach this file, and the work is the same

Two routes reach it, and it serves both.

- **Create here** — the setup form where a folder is linked and a design system is generated.
- **Create using Claude Code** — a `/design-sync` run in this repository.

**Whichever one invoked you, the work below is the same: generate a design system down from
documents.** No instruction in this file changes with the route, and a run must never treat the route
it arrived by as a reason to do less of it. One thing does change with the route — where your output
lands — and § *Where the generated design system lands* states both.

**`/design-sync` also carries a converter, and where there is no built library it has nothing to
convert.** That converter turns an existing component library into an upload bundle, and it ships what
was already built rather than a reimplementation. Where the product you were named has no such library
on disk, that half of the route has no work in it, and the generating half is the whole of the run.

**Finding no components is an expected result**, not a misconfiguration, and not a reason to go
looking for a different repository. Record it under § *Required: report your sources* (2) and carry on.

What admitting the sync route gains is that a design system may be asked for at any stage, including
before any code exists. Its cost is stated here rather than left to be found: a run arriving by a
converter's route arrives with a converter's instinct, which is to stop where there is nothing to
convert — and a run that stops there returns nothing, having read nothing.

**A delegated run cannot invoke `/design-sync`, and that is not a misconfiguration either.** The
command is reserved for a person typing it: a subagent that tries is refused, and no permission mode
or setting opens it. So a run reaching this file by delegation rather than by a typed command has
only this brief, and **this brief is enough** — everything above and below fully defines the
generating work, which is the whole of the run wherever there is no built library. Proceed under it,
say so under § *Required: report your sources*, and carry on.

**What such a run must not do is reach around the refusal.** The converter's scripts sit on disk and
the design tool's own upload tools are callable; neither is the point. The refusal exists so that
half of the route waits for a person, and a delegated run that drives it anyway has taken a decision
that was not its to take. Generate, write the folder, and leave the converting and the uploading to
whoever types the command. If you believe the product genuinely needs that half — it has a built
library, and someone wants it in the tool — say so in your report and stop there.

## Two repositories, and you need both

Every product here lives in its **own repository, at a path outside this folder**. This repository
*manages* it, and holds what the product's own repository does not — the Way, the terminus the product
is built against, and the instance-level rules binding every product built here. A run that reads only
the product repository does not see those; a run that reads only this one does not see the product.

**Two words, and they name different things.** The folder at `system/projects/<name>/` is the
**project** — the management side, and it lives here. What that folder's `Product path:` field points
at is the **product** — the repository holding the documents and, where it exists, the code. You are
named a project; you need what both hold.

**How to find the product you were named.** Read `system/projects/<name>/project.md` and take its
`Product path:` field. That is the product's repository root, verbatim; its documents are in
`<Product path>/docs/`. If the name you were given does not resolve to a folder under
`system/projects/`, stop and say so — do not guess which product was meant, and do not infer one from
a resemblance.

**Whatever either repository contains is what it contains.** Absence is a fact about the product's
stage, not a missing input and not a gap for you to fill. What goes up is what exists.

## What to take

Three places. How deep you go into each is chosen per run — a level is a floor, and reaching into the
next one for a single file is normal.

### The product's own documents — `<Product path>/docs/`

**List the directory and read every Markdown file in it.** They are the product: what it is, who it is
for, what is out of scope, the constraints it lives within, its experience definition, and — where they
have been written — its design and verbal languages. You do not need to know their names in advance,
and you must not conclude anything about the product from a name you did not open.

**Then read what sits in its subdirectories, whatever the format.** A product may hold drawn screens,
rendered frames, or screenshots of the real thing, and for a design run that is among the most useful
material either repository holds. You do not need to know the folder's name in advance; a product with
no such folder is a product at a different stage, and every file you open is a line under
§ *Required: report your sources* (1), the same as a document.

Four things to honour as you read:

- **Each document's own `Status:`.** *Settled* means its values are decided and none is yours to move.
  Anything else is provisional: render it, and say in the sources section that you did.
- **A `*_open_issues.md` companion is not an input.** Do not take it. Its presence is what tells you
  the document beside it is unfinished, and the calls inside it are the owner's.
- **What is not a document is evidence, never a source.** A frame, a prototype or a screenshot shows
  what has already been drawn, and you may redraw any of it. Where it and a settled document differ,
  the document governs.
- **A frame never licenses a breach of `system/experience/`.** Drawn material may predate the fence it
  is read against. Where a frame and a limit in that directory disagree, the limit holds and the frame
  is the thing that is wrong.

If the product's design or verbal language is not there, **that is a run you can still do** — the
experience definition and the product documents are enough to propose from, and what you propose is a
proposal. Say plainly under the sources section which of them you did not find.

### This instance's standing rules — `system/experience/`

**List this directory and read every file in it, without exception, before you decide anything.**

It holds two kinds. **Restrictions** are limits every product here holds and no product may relax.
**Directions** are what every product inherits — values and the tie-breakers for a case no limit
covers. Both kinds exist for the visual medium and the verbal one, and one rule reaching both mediums
appears in each with the same slug: that is one limit in two places, not two limits.

**Read them from the files, not from any summary — including any summary in this repository.** The
files are the rules; this paragraph is a pointer.

**A design that breaches one of those limits is a defect, not a draft.** That is why this directory is
not optional at any level, and why the sources section asks about it specifically.

**What a breach costs in <instance>'s own domain is stated in the line below, and a run reads the
directory against it. Where that line is empty, hold every limit as absolute and trade none of them
against anything.**

> The cost of a breach here:

### The instance's own framing — `system/`

`system/michi.md` is the Way this instance steers by, `system/projects/<name>/agari.md` is what "done"
means for the product you were named, and `system/doctrine/` holds the standing domain law. Read what
is there.

### If the product has built code

Only if it exists, and the vendor's own guidance applies: *"For large codebases, we recommend
attaching a frontend-focused subfolder"* — the subfolder implementing the design system, never the
whole repository.

### Assets — fonts, logo, imagery

**Not a run's to decide.** Where you need one and this repository names none, say so under the sources
section (2) and design around its absence rather than choosing one.

## What you own and what you do not

You own visual direction, layout and interaction exploration, and you **propose** design tokens and
component appearance. You do **not** own production components, application logic, architecture,
tests, or the state of any repository. Nothing you produce is authoritative until it is reviewed on
the code side.

Truth flows one way: **both repositories are pushed to you, and nothing either one already holds is
overwritten by you.** A Claude Code run writes exactly one thing, and it is the new folder named under
§ *Where the generated design system lands*. Every other file in either repository is an input, and a
run that edits one has exceeded what this file gives it.

## Where the generated design system lands

It lands in the **product's** repository, at `<Product path>/docs/design_system/` — beside the
documents it was generated from, and in the repository whose front-end implements it. It does **not**
land in this repository: what this one holds is the shared layer every product inherits, and a single
product's rendering is not that.

Who puts it there is the one thing the route decides.

- **Create here** — you produce the folder, and bringing it down is a step someone else takes.
- **Create using Claude Code** — the product repository is on disk in front of you, so you write the
  folder there yourself, at that path. You must never write it into this repository instead.

Either way, that destination fixes the shape your output has to have: a folder that can be dropped
into a product repository whole.

## Required: report your sources

Your generated output **must** contain a section titled `## Sources` listing, exactly:

1. **Read** — every file path you actually opened, one per line.
2. **Looked for and did not find** — every directory you listed that was absent or empty, and every
   kind of document named above that was not there. This is expected output, not failure.
3. **Assumed** — anything about the product you concluded without reading it here.

**`system/experience/` must appear by name under (1) or (2), file by file.** A run can produce a
defensible design system without opening any of it, and this section is the only place that becomes
visible afterwards.

If you could not reach the product's repository at all, say so plainly under (2) and do **not** infer
what the product is from its name or from this file. An empty (3) is the expected result; a populated
(3) is a finding, not a failure.
