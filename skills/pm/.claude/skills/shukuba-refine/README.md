# shukuba-refine

When a change unit lands or halts, it leaves audits, an integrity report, a closing commit with its `Deferred:` lines, sometimes a
deferred-decisions file, the corrections its plan owed to records it could not edit, and the work its
spec handed on — and the documents upstream of the route may have moved while it was built.
Nothing else reads either against the project's route. This skill is the PM's review after a seal or a halt: it
reads both, acts on the route, and leaves a record of what it did, why, and from where.

## What It Does

- Resolves the reviewed unit — a sealed Tobiishi, a halted Tobiishi, or an ad-hoc merge — by the key
  it is given, or else the sealed change the project's `contexts/CONTEXT_PM.md` names. It finds the unit's station and seed
  from the unit's own commits and the station's item line.
- Reads what moved upstream in the product's `docs/`, and holds anything a chain in flight may still
  move.
- Makes the six moves the method calls for: modify a seed or station in place, park or
  un-pick through their own skills, raise a companion item on an upstream document, or drop a
  halted unit through `tobiishi-drop`. A station found
  reached is named as owed to the Scrum Master to close, not made here — unless the park finds it
  reached and closes it through `shukuba-retire` itself.
- Always writes `<key>_report.md` and `<key>_recommendations.md` with the seed, turning a file-seed
  into a folder the first time.
- Opens the report with `## Next moves`: what the run leaves owed — the next change, a companion sweep,
  a station close, a pick and its route, a seed's retire, drop or cut — whose each is, and the command that starts it.
  It makes none of them. An unattended run's completion message is read off that table.

## File Structure

```
shukuba-refine/
├── SKILL.md    the orchestrator: posture gate, resolution, the moves' order, the two files, commits
└── README.md   this file
```

The method lives in `prompts/rich.md`; the two files' shapes in
`<CORE>/templates/journey-templates/shukuba_refine_report_template.md` and
`shukuba_refine_recommendations_template.md`.

## Depends On

- `shukuba-park` — parks a station that cannot be walked as written.
- `nemawashi-unpick` — un-picks the active seed, only to free the slot.
- `tobiishi-drop` — drops a halted unit whose intake will not be walked as written: its subject no longer holds, or the route has split it into separate units.

## When to Use

In a `pm:` session or as the `pm` agent, after `tobiishi-seal` (or an ad-hoc merge) lands a unit, or a
walk halts on one, with the project. The project's context names a sealed unit, and a halted one whose
walk ended halted, so neither needs its key given; an ad-hoc merge does. A unit already reviewed is
reviewed again in full, against the current method. Before a seed is walked, splitting it into stations is `stations-from-seed`'s job instead.
