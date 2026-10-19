# Seed — define <project>: PRD → Agari → (SRS ∥ EXPERIENCE) → SDD

*Stamped by `project-stamp` when this project was created, so the seedbed starts with the
work that has to happen before anything is built. This is a **recommendation**: it is the
ordinary way a product gets defined, not a rule. Edit it, reorder it, or delete it if this
product starts somewhere else.*

## The idea

Take <project> from a folder that points at a product to a product that is defined — the
upstream chain, in order. Each station below is walked one at a time: it opens as the single
active 宿場 Shukuba, and when its reached-when is met the Shukuba file moves to
`shukuba/trail/` and the item is checked here.

## Read first

1. `system/projects/<project>/project.md` — the project card and its `Product path:` binding.
   Every `<product>/…` path below resolves through that field.
2. `<CORE>/doctrine/setup/setting_up_a_project.md` — the doctrine these stations are stamped
   from: the sequence, why the Agari is declared before the SRS, and which stations are
   runnable today. It is the owner; this checklist is a copy of it, so when the two disagree
   the doctrine is right and this file is stale.

## Discipline

- **Posture per station.** The definition skills each require their role and halt without it —
  the role is named on each station below. Run each through the launcher named on its station,
  which supplies that posture; a station with no launcher line runs as a subagent of its role
  instead, and the posture gate accepts either. Why the launcher is the way, and which stations
  have one, are the doctrine's — § "How the definition skills run".
- **The definition skills run in rounds.** Each drafts its whole document, then parks what it
  could not settle in a companion `<doc>_open_issues.md`. Answer those inline, commit, re-run
  the same skill. The companion file's **absence** is the done signal.
- **Once the Agari is declared, pull each later station's guardrail from it.** That is what
  declaring it early buys.

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

- [ ] 2. **project-agari** — declare <project>'s 上がり Agari, the terminus: the condition under
  which this product is done or shipped. Fills `system/projects/<project>/agari.md` (CPO).
  Declared off the back of the settled PRD, and **before** the SRS. Run it through
  `<CORE>/launchers/skill/launcher.sh project-agari <project>`.

- [ ] 3. **product-srs** — author the SRS from the settled PRD: the technical answer to the
  PRD's *what* — system requirements, interfaces, data, constraints. Lands at
  `<product>/docs/SRS.md` (CTO). Run it through
  `<CORE>/launchers/skill/launcher.sh product-srs <project>`.

- [ ] 4. **EXPERIENCE** — what <project> is like to use, in four runs. The station carries **no
  single role**; each run below carries its own. Sits **beside** `product-srs` — both work off the
  settled PRD, neither derives from the other — and feeds the SDD, so the experience lands before
  the architecture locks: `PRD → (SRS ∥ EXPERIENCE) → SDD`. The UXD is walked first because
  everything else here reads it; the design language and the verbal language are **peers** off it,
  in either order or at the same time; the design run comes last because it reads what the other
  three produced. This station is reached when all four runs are.

  - [ ] 4↳. **product-uxd** — author the UXD from the settled PRD: users and their contexts, the
    information architecture, the key flows, the screen inventory with its states, the interaction
    patterns, and the accessibility bar. Lands at `<product>/docs/UXD.md` (CDO). Run it through
    `<CORE>/launchers/skill/launcher.sh product-uxd <project>`.

  - [ ] 4↳. **product-design** — author the design language off the UXD's direction call: the
    product's tokens and the rules that apply them. Lands at `<product>/docs/DESIGN.md` (CDO).
    Nothing else in this chain reads it, so it can settle after the SDD. Run it through
    `<CORE>/launchers/skill/launcher.sh product-design <project>`.

  - [ ] 4↳. **product-content** — author the verbal language off the UXD: voice and tone, grammar
    and mechanics, terminology, the message patterns for the states the UXD names, the
    accessibility bar for text, and localization rules. Lands at `<product>/docs/CONTENT.md`
    (Content Manager). The peer of the design language — how it looks belongs to `DESIGN.md`, what
    it says belongs here — and nothing else in this chain reads it either. Run it through
    `<CORE>/launchers/skill/launcher.sh product-content <project>`.

  - [ ] 4↳. **design run** — hand the experience documents out to **Claude Design** and bring the
    generated design system back. This one is the **owner's**: no skill, no launcher, and no
    posture. Any subset of the experience documents is a legitimate input, unsettled ones included.

- [ ] 5. **product-sdd** — author the SDD, the technical *how*. Lands at
  `<product>/docs/SDD.md`. Read `<CORE>/doctrine/setup/setting_up_a_project.md` § *Which of these
  exist today* before opening this item — it owns whether the station can run. The one real
  dependency in the chain: it needs **both** the SRS and the UXD, which is what keeps design
  upstream of the architecture instead of arriving after it has locked.

**This seed ends at the SDD.** What comes after — the Principal PM's Delivery Plan, and the
**foundation step**: the FDR, the ADR and the NFDR — is not carried here. The foundation step
arrives as **its own seed, one per product**, seeded by the Principal PM when the definition above
has settled. It is not a station here, and it is not a station on a seed cut from the SDD — those
seeds *need* the three records rather than producing them. What it holds, who authors each record
and what each is written from: `<CORE>/doctrine/setup/setting_up_a_project.md` § *The foundation
step*.
