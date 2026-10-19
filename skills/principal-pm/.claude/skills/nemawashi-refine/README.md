# nemawashi-refine

A walked seed carries the recommendations its `shukuba-refine` runs left for the Principal PM, and
`nemawashi-retire` files them in `trail/` unread. This skill is the Principal PM's answer, run after the
retire: every recommendation processed, the project's candidate pool re-read, and a report that opens
with what is owed next.

## What It Does

- Resolves the retired seed — the one named, or the one the project's latest retire commit names.
- Answers each recommendation one way: a companion item on a product document, a docs cut,
  carried by a candidate, a drop, a seed cut from an idea, a route across projects, or ignored with its reason.
- Keeps, modifies or drops every candidate in `unpicked/`.
- Fixes what it finds while reading — a dead pointer in the pool always — or cuts it, per
  `found_while_walking.md`; never only reports it.
- Writes companion items on product documents where an ask belongs there.
- Decides whether the product's documents are owed a cut — even with candidates left in `unpicked/` —
  and names it rather than running it.
- Always writes `system/projects/<project>/docs/nemawashi-refine/<seed>_report.md`, opening with
  `## Next moves` — the companion sweep (`chain-product` or `chain-agari`, as the project card's
  `**Definition:**` line names), `seeds-from-product-docs`, `nemawashi-pick`, `stations-from-seed`,
  plus a halted cut's re-run or a route across projects where owed — each with its seat and the
  command that starts it. It makes none of them.

## File Structure

```
nemawashi-refine/
├── SKILL.md            the orchestrator: posture gate, resolution, the moves' order, the report, commits
├── prompts/rich.md     the judgment: what each recommendation and candidate owes, and what comes next
├── templates/report.md the report's shape
├── launcher.md         the unattended launch
└── README.md           this file
```

## Depends On

- `nemawashi-drop` — drops a candidate the walk overtook or ruled out.
- `seeds-from-idea` — cuts work no product document should state.

## When to Use

In a `principal-pm:` session or as the `principal-pm` agent, after `nemawashi-retire` files a
project's walked seed in `trail/`, and before the PM picks the next one.
