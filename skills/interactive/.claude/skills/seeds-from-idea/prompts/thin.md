---
version: "1.0.0"
---

# seeds-from-idea — the idea cut's own tightenings

This file is the `seeds-from-idea` skill's lens. It extends `<CORE>/prompts/principal_pm_cut_seeds.md`
and tightens three things in it, for an idea cut only.

**Read the base first, in full, and read it as the base this file extends.** Everything about cutting
an idea is stated there and is not restated here. Apply all of it, except where a section below names
a line of the base and replaces it. Where the base and this file disagree, this file governs.

Idea cuts have been killed for producing more seeds than the owner asked for (commits `24a9cb6fe`
and `b271198a1` record the owner's rulings). Seeds have been withdrawn for citing and proving on a
dropped attempt's output (commit `c83a1d791`). The owner agreed these three tightenings on
2026-10-12. The base also serves `seeds-from-product-docs`, which is why they live
here and not in it.

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
