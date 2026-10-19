# Seed — set up <instance>: identity → doctrine → writing bar → experience

*Stamped by `spawn_satellite.py` when this instance was created, so the seedbed starts with the
setup this instance still owes. This is a **recommendation**: it is the ordinary way an instance is
set up, not a rule. Edit it, reorder it, or delete it if this instance starts somewhere else.*

## What it is

Take <instance> from a directory that has been stamped to one that can take projects: its identity
and 道 Michi declared, the standing rules of its subject written down, the bar its own documents are
written to stated, and its experience layer stating what its products may and may not look and sound
like. Step 1 of that sequence — the stamp —
is what produced this file, so it is already done by the time anyone reads it. The rest is below.

## Source

`<CORE>/doctrine/setup/setting_up_an_instance.md` § *The steps, in order* — the doctrine these items
are projected from: the five steps, what fixes their order, and the three standing rules. It is the
owner; this checklist is a copy of it, so when the two disagree the doctrine is right and this file
is stale.

## Discipline

- **Walk one item at a time, top to bottom.** An item is walked by running the skill named on it — or,
  where the item names a prompt instead, by opening a session in the posture it names and having it
  read that prompt — rooted in this instance. Tick it when its work is finished — for the items that
  carry a companion, that is when the companion is **gone** (next bullet but one), not when the first
  run lands. There
  is **no station file**: `system/shukuba/` is the instance's cross-project router
  (`<CORE>/doctrine/setup/kensaiapp_structure.md` § App-level), and a setup step is one skill run at
  instance altitude, not several projects pushing on one thing.
- **`experience-visual` and `experience-voice` have a launcher; the other items do not.**
  `<CORE>/launchers/skill/launcher.sh experience-visual` and
  `<CORE>/launchers/skill/launcher.sh experience-voice`, run from this instance's root — each spawns
  the run in the right posture from a fixed prompt. The other items
  run as a `<role>:` session or that role's subagent; the skills' posture gates accept either. **Two
  items name a prompt rather than a skill** — the seat's own session reads it, and there is no gate to
  accept anything, so the posture is yours to open correctly.
- **The skill-run items run in rounds.** Each drafts what it can, then parks what it could not settle
  in a companion open-issues file. Answer those inline, commit, then re-run it — through its
  launcher where it has one. The companion's **absence** is the done signal. The prompt-read items carry no companion: the seat writes what it can
  ground and states an honest absence where it cannot, which is a finished state rather than a round.
- **Nothing setup writes says anything about any one product.** The first artifact that could only
  belong to a product is that product's PRD, and that is station 1 of a *project's* journey.

## Stations — dynamic checklist (grow it as the work reveals them)

- [ ] 1. **kensaiapp-michi** — settle what <instance> is, then declare its 道 Michi, the Way(s) it
  steers by. Fills `kensaiapp.md` § *What this is about* and `system/michi.md`, and reconciles the
  instance `README.md` to both where one exists. Posture-neutral — no role prefix. Grouped, so the
  session reaches it only after `--add-dir` / `/add-dir` on `skills/interactive-product/`. Everything below
  is written against what this settles, which is why it is first.

- [ ] 1a. **The doctrine layer** — state the standing rules of <instance>'s subject, the AI boundaries
  that follow from them, and the meta-layer that classifies both. Fills the three files step 1 stamped
  into `system/doctrine/`. **No skill runs this**: open a `cto:` session and have it read one lens per
  file — `<CORE>/prompts/cto_create_domain_doctrine.md`,
  `<CORE>/prompts/cto_create_ai_responsibility.md`, `<CORE>/prompts/cto_create_doctrine_structure.md`.
  The first two **halt** on item 1's placeholders. **An honest emptiness is a finished state**: an
  instance whose subject the layer below already governs says so in the file and stops, and
  `ai_responsibility.md` § 2 starts empty by design. One commit per file, `Role: CTO`.

- [ ] 1b. **Each seat's domain** — declare what <instance>'s domain means for the seats it actually
  uses, in § *The domain* of each `system/loaders/<role>.md`. **No skill runs this**: open a session
  in the seat and have it read `<CORE>/prompts/declare_loader_domain.md`. The substance stays in
  `system/doctrine/`; the overlay carries only the judgment that follows for that seat. **Partial is
  finished** — a seat whose global posture governs unchanged keeps its stamped placeholder, which is
  a stated state, not a gap. Halts on item 1's placeholders, same as item 2. One commit per seat, in
  that seat's own `Role:`.

- [ ] 2. **kensaiapp-writing-bar** — state the bar every document authored in <instance> is held to.
  Writes `system/doctrine/writing_bar.md` — **the step's output**: who those documents' reader is and
  what follows from that reader. **This item is not optional.** Core states no bar to fall back on, so until this file
  exists nothing binds how <instance>'s documents read. The run **halts** if item 1 has not landed — a bar written off a
  placeholder identity is grounded in nothing. Content Manager posture.

- [ ] 3. **experience-visual** — author what <instance>'s products may and may not look like:
  `system/experience/visual_restrictions.md`, `visual_direction.md`, and the cross-medium entries
  marked in `visual_voice_contract.md`. CDO posture. **Ordered before item 4, and that order is
  fixed** — the marks this run leaves are what make the next one's job total.

- [ ] 4. **experience-voice** — author what <instance>'s products may and may not sound like:
  `system/experience/voice_restrictions.md` and `voice_direction.md`, written off the entries item 3
  marked. Content Manager posture.

**This seed ends where setup ends** — at the point <instance> can take a project. Registering the
first product is the next altitude down and begins at
`<CORE>/doctrine/setup/setting_up_a_project.md`, which stamps its own seed in that project's
seedbed. Nothing about any product is decided here.
