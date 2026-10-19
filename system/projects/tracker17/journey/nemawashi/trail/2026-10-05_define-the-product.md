# Seed — define tracker17: PRD → Agari → (SRS ∥ EXPERIENCE) → SDD

*Stamped by `project-stamp` when this project was created, so the seedbed starts with the
work that has to happen before anything is built. This is a **recommendation**: it is the
ordinary way a product gets defined, not a rule. Edit it, reorder it, or delete it if this
product starts somewhere else.*

## The idea

Take tracker17 from a folder that points at a product to a product that is defined — the
upstream chain, in order. Each station below is walked one at a time: it opens as the single
active 宿場 Shukuba, and when its reached-when is met the Shukuba file moves to
`shukuba/trail/` and the item is checked here.

## Read first

1. `system/projects/tracker17/project.md` — the project card and its `Product path:` binding.
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

- [x] product-prd — `products/tracker17/docs/PRD.md` carries `**Status:** Settled` and no `PRD_open_issues.md` sits beside it (CPO).
- [x] project-agari — `system/projects/tracker17/agari.md` states a "Reached when" and is no longer the stamped blank (CPO).
- [x] product-srs — `products/tracker17/docs/SRS.md` carries `**Status:** Settled` and no `SRS_open_issues.md` sits beside it (CTO).
- [x] product-uxd — `products/tracker17/docs/UXD.md` carries `**Status:** Settled` and no `UXD_open_issues.md` sits beside it (CDO).
- [x] product-content — `products/tracker17/docs/CONTENT.md` carries `**Status:** Settled` and no `CONTENT_open_issues.md` sits beside it (Content Manager).
- [x] product-design — `products/tracker17/docs/DESIGN.md` exists, settled, with no `DESIGN_open_issues.md` beside it (CDO).
- [x] product-sdd — `products/tracker17/docs/SDD.md` carries `**Status:** Settled`, no `SDD_open_issues.md` beside it, and it was authored with both the SRS and the UXD Settled (CTO).
- [x] design-run — the owner has handed the experience documents to Claude Design and brought a design system back, or has recorded in the seed that they decline it; owner-run, no skill, no launcher.
  **Declined by the owner, 2026-10-07:** "I'm skipping it." No design run is made for tracker17.

The prd round's check still stands for the `product-prd` station: when it is reached, look for work the round surfaced that is not a PRD question — a deferred ratification condition, a gap, product work — and seed it as its own file in this seedbed.

Re-cut by `stations-from-seed`, 2026-10-07. Divergences from the stamped proposal: (1) the EXPERIENCE station and its four `4↳` runs are flattened to four stations, because one station that bundles four documents closes only when all four do; (2) `design-run` moves from before `product-sdd` to last, because the SDD reads the SRS and the UXD and nothing in the chain reads the design run, so its place was the cutter's habit, and it is the one owner-run step; (3) `product-content` now precedes `product-design`, since the design language reads nothing from the verbal language and the order is free; (4) every line now names a reached-when a fresh session can check, which the proposal gave as activity. On disk at this re-cut every document above except the design run already reads Settled with no open-issues companion beside it (`products/tracker17/docs/`), so those stations are already reached and their close, via `shukuba-open` then `shukuba-retire`, needs no change unit.

**This seed ends at the SDD.** What comes after — the Principal PM's Delivery Plan, and the
**foundation step**: the FDR, the ADR and the NFDR — is not carried here. The foundation step
arrives as **its own seed, one per product**, seeded by the Principal PM when the definition above
has settled. It is not a station here, and it is not a station on a seed cut from the SDD — those
seeds *need* the three records rather than producing them. What it holds, who authors each record
and what each is written from: `<CORE>/doctrine/setup/setting_up_a_project.md` § *The foundation
step*.
