# Seed — define <project>: PRD → finish line

*Stamped by `project-stamp` when this project was created, because its card reads
`Definition: prd-and-finish-line`: the product is defined by its PRD and its finish line, and by
nothing after them. This is a **recommendation**: it is the ordinary way such a product gets
defined, not a rule. Edit it, reorder it, or delete it if this product starts somewhere else.*

## The idea

Take <project> from a folder that points at a product to a product that is defined — the PRD,
then the finish line off the back of it. Each station below is walked one at a time: it opens as the
single active 宿場 Shukuba, and when its reached-when is met the Shukuba file moves to
`shukuba/trail/` and the item is checked here.

## Read first

1. `system/projects/<project>/project.md` — the project card and its `Product path:` binding.
   Every `<product>/…` path below resolves through that field.
2. `<CORE>/doctrine/setup/setting_up_a_project.md` — the doctrine these stations are stamped
   from: the sequence, which part of it each `Definition:` walks, and how the definition skills
   run. It is the owner; this checklist is a copy of it, so when the two disagree the doctrine is
   right and this file is stale.

## Discipline

- **Posture per station.** The definition skills each require their role and halt without it —
  the role is named on each station below. Run each through the launcher named on its station,
  which supplies that posture. Why the launcher is the way is the doctrine's — § "How the
  definition skills run".
- **The definition skills run in rounds.** Each drafts its whole document, then parks what it
  could not settle in a companion `<doc>_open_issues.md`. Answer those inline, commit, re-run
  the same skill. The companion file's **absence** is the done signal.
- **Both stations walk as one.** `<CORE>/launchers/prd-and-finish-line/launcher.sh <project>` writes the
  PRD and then the finish line, and carries on from where it stopped when run again.

## Stations (dynamic checklist — grow it as the work reveals them)

- [ ] 1. **product-prd** — author <project>'s PRD, the product source of truth: what it is, who
  it is for, the problem it removes, what success looks like, what is out of scope. Lands at
  `<product>/docs/PRD.md` (CPO). Run it through
  `<CORE>/launchers/skill/launcher.sh product-prd <project>`.

  > **When this station is reached, check what the round left behind.** A PRD round settles
  > product questions, but it can also surface work that is *not* a PRD question — a condition
  > deferred from a ratification, a gap someone chose to defer, product work the round revealed.
  > That does not belong in the PRD's companion file and it is not carried by this seed. Seed it
  > as **its own file** in this seedbed, so it survives the round that found it.

- [ ] 2. **project-finish-line** — declare <project>'s finish line, the terminus: the condition under
  which this product is done or shipped. Fills `system/projects/<project>/finish_line.md` (CPO).
  Declared off the back of the settled PRD. Run it through
  `<CORE>/launchers/skill/launcher.sh project-finish-line <project>`.

**This seed ends at the finish line.** When both stations are checked the product is defined, and the
seed is finished: move it to `journey/nemawashi/trail/` (skill: `nemawashi-retire`). The work
continues by fresh seeds, each cut toward the finish line.
