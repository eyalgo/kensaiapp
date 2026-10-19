---
version: "1.0.4"
---

# seam — two seats whose owned artifacts overlap, or whose seam is never stated

Two seats exist because they do different things. Each loader asserts that difference in prose, and
nothing checks the assertion against the one thing that settles it: **which files each seat writes.**
Two seats that would write the same file are one seat carrying a second token cost, whatever their
prose says. **The tell is an artifact named as owned in two loaders**, or a seat with no stated seam at
all against its nearest neighbour.

The question is borrowed from the other direction. A split trigger asks what would have to become true
for one seat to become two; asked of two seats that already exist, it asks what keeps them apart, and a
seat that cannot answer has not been thought through.

## What this lens reads

- `core/roles/loaders/*_global.md` — every global loader, read for its owned-artifact set.
- `system/loaders/*.md` — the overlays, which may add owned artifacts.
- `core/doctrine/setup/setting_up_a_project.md` — which seat authors each product document.
- `core/doctrine/governance/commit_format.md` — which `Role:` each artifact's commits take, since two
  seats writing one file under two Roles is the same collision seen from the log.

The lens reads the whole set at once, by construction: a seam is a property of a pair, and a lens given
one loader cannot find one.

## The question

**For each pair of seats, is there a file both could reasonably claim?** And where no pair collides:
**does each seat state its seam with its nearest neighbour, or is the reader left to infer it?**

## What the shape looks like

| The lens finds | Which is a defect when | Must not |
|---|---|---|
| One artifact named as owned in two loaders. | Neither loader marks the overlap as deliberate shared authorship. | Report a genuinely shared artifact as a collision — a run worked by several seats is one artifact with several authors. |
| An overlap where one side is marked settled by the owner and the other was never updated. | The unmarked side still reads as current. | Treat the ratified side as the defect. |
| A seat with no stated seam and a neighbour doing adjacent work. | The neighbour's work is adjacent in altitude or in subject. | Demand a seam from a seat that has no neighbour. |
| Two seats whose owned sets are disjoint but whose stated purposes paraphrase each other. | The purposes cannot be told apart by a cold reader. | Report two seats as one on prose alone when their files differ. |

## Evidence this shape is real

**Instance one — a collision that ran live for weeks, one side ratified.** At `5c0e4dda`,
`pm_global.md:20` read "Own `fdr.md` — update it when scope changes; never delegate this to PO", with
`project-fdr` as its skill, while `principal_pm_global.md:203` read "**The FDR is yours, and the skill
that authors it disagrees — knowingly.**", marked "**settled (owner, 2026-08-11)**". Two seats owned
one file; one side recorded a ratification the other never absorbed, until `3e691cf2` took the ratified
side into the PM loader.

**Instance two — the stated-seam rate, re-measured 2026-09-06.** Six of fourteen global loaders carry a
seam section:

```
grep -ln "most easily confused" core/roles/loaders/*.md
```

returns `cdo_global.md`, `content_manager_global.md`, `cto_global.md`, `pm_global.md`,
`principal_architect_global.md` and `principal_pm_global.md`. Eight
loaders state no seam with any neighbour. The template that stamps them treats that as a defect:
`core/templates/role-templates/global_loader_template.md` reads "a role with no boundaries section and
no named confusable has not been thought through: the seam with its nearest neighbour is usually the
whole reason it exists."

**A claim this lens corrected.** The seed that prompted this set states that "Every global loader
carries a 'who you are most easily confused with' section". The
measurement above shows six of fourteen. The shape survives the correction and grows: the failure is
not only an untested assertion of distinctness, it is a distinctness never asserted.

## What this lens may not assert

- **That an overlap means one seat should be removed.** Merging or splitting seats is the owner's, and
  `core/doctrine/setup/adding_a_role.md` owns the procedure. The lens reports the collision.
- **That the unratified side is stale.** Where one side carries an owner's decision and a date, the
  lens reports that the other has not been reconciled with it — which is a statement about the
  reconciliation, not about which seat is right.
- **That two seats sharing an artifact is wrong.** Some artifacts are authored by several seats in one
  run. The defect is an *unmarked* overlap, and the mark is what distinguishes them.
- **That a missing seam section is a missing seam.** A seat may state its boundary in prose without the
  section heading. The lens reads for the content, and reports the absence of the section only when the
  content is absent too.

## Reporting

One finding per pair, never per seat, because a seam is a property of the pair and two findings would
be one fact told twice. Each carries both seats, the artifact or the adjacency at issue, each side's
quoted claim, and whether either side is marked ratified.

## The lens ran clean when

- every pair of seats was considered, not only the pairs whose names are similar — a collision between
  seats with unrelated names is the one nobody looks for;
- each loader's owned-artifact set was built from its own text before any pair was compared;
- every seat with no stated seam was named, with the neighbour it was tested against;
- no finding proposes a merge, a split, or a removal;
- the lens says so explicitly when it found nothing.
