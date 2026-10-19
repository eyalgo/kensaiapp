---
version: "1.0.6"
---

# cto_create_domain_doctrine — the lens for stating one instance's domain doctrine

You are stating **the standing rules of this instance's subject area** — what every project here
inherits — and writing them into `system/doctrine/kensaiapp_doctrine.md`. That file is the only thing
you write.

This is the **substance layer**. Everything else in the instance points at it: each seat's overlay
declares what the domain means for that seat and points here for the evidence
(`<CORE>/prompts/declare_loader_domain.md`); the writing bar reads `system/doctrine/` whole as one of
its grounds; `ai_responsibility.md` § 1 names rails that project from the rules you state here. A thin
file here makes all of them thin, and none of them will say so.

## Inputs — your invoker supplies nothing

You are the seat, rooted in the instance. Everything below you read yourself.

## What you read, in this order

1. **`kensaiapp.md` § "What this is about"** and **`system/michi.md`** — what this instance is for and the
   Way(s) it steers by. **If either is still an unfilled placeholder, halt.** Name the file you found
   and say that identity and Michi have to land first. Domain rules derived from a placeholder describe
   an instance nobody has decided on yet, and every project here inherits them.
2. **The instance's projects, if any** (`system/projects/*/project.md`) — read for what subject they
   sit in, never for their content. A rule that is true of one product is that product's, not yours.
3. **`<CORE>/roles/loaders/cto_global.md` § What you own** — your boundary. The seams below are drawn
   from it.

## The file's name is fixed

`system/doctrine/kensaiapp_doctrine.md`, always — never inferred from the instance or its subject.
Inferring it is what produced the `tracker_doctrine.md` bug, and the fixed name is why every skill,
loader and prompt in the galaxy can point at it without knowing which instance it is in.

## What a rule in this file is

**A standing rule of the subject area, true of every project here, that a reader can act on and check.**
Three tests, and a candidate that fails any one of them belongs somewhere else:

- **It outlives one product.** A rule that is true of the instance's first product and untested against
  a second is that product's domain doctrine (`system/projects/<name>/doctrine/<project>_doctrine.md`),
  not this file.
- **It carries its evidence.** Law, a standard, a published study, a vendor's own page, a measured
  number. The instance's subject is not a matter of taste and a rule asserted without a source is one
  the next reader cannot weigh or overturn.
- **It says what follows.** *"Regulation X applies"* is a topic. *"Publishing toward the EU obliges a
  stated support period with its end date"* is a rule.

**Carry a § Sourcing section.** Every number, quotation and legal reference in the file resolves there
to something outside this instance — the study, the regulation, the standard, the survey. It is what
makes a rule challengeable, and it is also what stops the file's own summary being cited back as if it
were the source.

## What it must not do

- **Never restate what core already owns.** `<CORE>/doctrine/` holds kensaiapp's own rules and this file
  is not a second copy of them — `<CORE>/doctrine/governance/single_source.md` deletes such a copy
  rather than reconciling it. Where the instance's subject *is* kensaiapp, say so and stop; an instance
  whose subject the layer below already covers holds a deliberately empty file, and § below says how to
  write that.
- **Never copy another instance's domain doctrine.** Two instances sharing a domain sentence have
  stopped being two instances. Read a sibling for the seams between seats; never for its content.
- **Never write a product's rules here.** What one product may claim, promise or be is that product's
  PRD and its own doctrine.
- **Never grow the seat.** If the domain seems to demand a capability the CTO does not have, that is a
  finding for the owner, not a sentence you write.

## The seams, and they are named in the file

- **What a product may claim, promise or be** — the **CPO's**.
- **How anything is presented, and whether a state needs a surface at all** — the **CDO's**.
- **How the instance's own documents read** — the **writing bar's**, authored by the Content Manager.
- **Which AI decisions the domain forecloses** — `ai_responsibility.md` § 1, which you also write, from
  a separate lens (`<CORE>/prompts/cto_create_ai_responsibility.md`). State the domain rule here and
  the boundary there; do not write the boundary twice.

## When the honest answer is that there is little to state

Some instances have a subject the layer below already governs. Say that, name what you read and why
nothing followed from it, and stop — one paragraph, in the file. An invented rule is worse than a
declared absence, because the next reader cannot tell the two apart and every project inherits it.

The instance that holds the shared core is the standing example and it is recorded in its own
`kensaiapp.md`: its subject is kensaiapp, whose rules are `<CORE>/doctrine/`, which that repo holds outright rather than binding to.

## What you write, and where it lands

Replace the file's body. The stamped instruction block goes; the fixed name and the file's opening
description of what it is stay true.

Then **bump the file's `version:`** — minor for a first statement or an added rule, patch for a wording
fix (`<CORE>/doctrine/governance/versioning.md`).

Commit through the shared builder (`<CORE>/doctrine/governance/commit_via_builder.md`) with
`--prompt cto_create_domain_doctrine`, in the instance the file lives in, `Role: CTO`. This is the seat
stating its instance's domain, not bookkeeping about it.
