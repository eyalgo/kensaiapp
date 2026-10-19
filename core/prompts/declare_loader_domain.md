---
version: "1.0.4"
---

# declare_loader_domain — the lens for declaring one seat's domain in one instance

You are declaring **what this instance's domain means for one seat's judgment**, and writing it into
that seat's loader overlay at `system/loaders/<role>.md`, § *The domain*. That section is the only
thing you write. The overlay's other sections are not yours in this run.

The prompt is **role-agnostic on purpose** — the reasoning is the same for every seat and only the
seat changes, so it takes a role-neutral name like `<CORE>/prompts/ratify_skill.md` rather than the
`<role_file>_create_<artifact>` form its neighbours use.

## Inputs — your invoker supplies these

- **`<role>`** — the role token, which is the stem of both `system/loaders/<role>.md` and
  `<CORE>/roles/loaders/<role>_global.md` (`content_manager`, `cpo`, `developer`, …).
- **`<Role Title>`** — how that seat is named in prose (Content Manager, CPO, Developer, …).

Everything else you read yourself, from the instance the session is rooted in.

## What you read, in this order

1. **`kensaiapp.md` § "What this is about"** and **`system/michi.md`** — what this instance is for and the
   Way(s) it steers by. **If either is still an unfilled placeholder, halt.** Name the file you found
   and say that identity and Michi have to land first. A domain declared off a placeholder describes
   an instance nobody has decided on yet, and every seat that reads the overlay inherits the guess.
2. **`system/doctrine/kensaiapp_doctrine.md`**, and the rest of `system/doctrine/` — the domain's
   standing evidence, law and argument. This is where the substance lives, once, for every role and
   every project.
3. **`<CORE>/roles/loaders/<role>_global.md` § What you own** — the seat's boundary. What you write
   must be *this seat's* judgment; the boundary tells you which calls are not.
4. **The instance's other filled overlays**, if any — read them for where the seams fall between
   seats, never for their content.

## The rule that shapes everything you write

**The doctrine holds the domain; the overlay holds what it means for this seat.** Do not restate the
evidence, the law, the numbers or the argument — point at the doctrine and write the *judgment* that
follows from it. A reader who wants the ground opens `system/doctrine/kensaiapp_doctrine.md`; a reader
in this seat wants to know what the domain changes about the calls they are about to make.

This is not a style preference. A second copy of the domain drifts from the first the moment either
moves, and `<CORE>/doctrine/governance/single_source.md` puts the fact in one place with everything
else pointing at it.

## What a good section does

- **Leads with the seat, in the heading.** `## The domain — <clause naming what is this seat's here>`.
  Not a bare `## The domain`.
- **Carries judgment as instinct, not as a checklist** someone else runs later. You are writing what
  the holder of this seat should already believe when they start work.
- **Names the consequence, not the topic.** "The documentation is the product, so a broken example is
  a release-blocking defect" is judgment. "Documentation matters here" is a topic.
- **Marks the seams outward.** Where a neighbouring seat owns the adjacent call, say so and name the
  seat. A domain section that claims the whole domain teaches the reader to overreach.
- **Ties to the instance's Way(s) where the tie is real** — and does not manufacture one where it
  is not.

## What it must not do

- **Never copy another instance's domain.** The stamped placeholder says so itself, and the reason is
  that two instances sharing a domain sentence have stopped being two instances. Read a sibling for
  its seams; never for its content.
- **Never grow the seat.** You are declaring what the domain means for a seat whose boundary is
  already fixed by its global loader. If the domain seems to demand a capability the seat does not
  have, that is a finding for the owner, not a sentence you write.
- **Never restate the global loader's posture.** It is read first, in the same stack, every time.

## When the honest answer is that there is nothing to declare

The stamped placeholder is a **stated state**, not a gap — *"leaving it blank is a stated state, not
an oversight."* Some seats in some instances genuinely have no domain-specific judgment: the global
posture governs and nothing about this instance changes it.

Where that is the case, **leave the placeholder and say why** — one added sentence naming what you
read and why nothing followed from it. An invented distinction is worse than a declared absence,
because the next reader cannot tell the two apart.

## What you write, and where it lands

Replace the `## The domain` block in `system/loaders/<role>.md` and nothing else. The heading takes
its clause; the placeholder paragraph goes.

Then **bump the overlay's own `version:`** — minor for a first declaration or an added distinction,
patch for a wording fix, per `<CORE>/doctrine/governance/versioning.md`.

Commit through the shared builder (`<CORE>/doctrine/governance/commit_via_builder.md`) with
`--prompt declare_loader_domain`, in the instance the overlay lives in, with `Role:` set to the seat that
made the declaration — this is that seat declaring its own domain, not bookkeeping about it.
