---
name: stations-blind-review
description: >-
  PM-posture skill that reads the picked 根回し Nemawashi seed's route blind, as a fresh run that never
  saw the run that cut it, and reports where the route fails what the owner decided. It maps every
  ruling the seed records, every part a ruling lists and every bullet of the seed's What it is to the
  station whose reached-when proves it, quoting the bar's words, then names what no bar carries, what
  a bar contradicts or adds, what a fresh session cannot check, what cannot be met where it stands in
  the order, and what a divergence line claims that its station does not say. It edits no journey
  file; it writes one review in the project's docs/ and commits it. Requires PM posture and halts
  outside a pm session or the pm subagent. Use right after stations-from-seed has cut or re-cut a
  route, and before the first station of that route opens.
when_to_use: >-
  Trigger phrases — "review the route blind", "blind-review the stations", "check the route against
  the rulings", "does the route prove the rulings", "stations-blind-review". Do not use for cutting
  or re-cutting the route (stations-from-seed), fixing what the review found (the PM fixes the route,
  by hand or by re-running stations-from-seed), re-reading a route after a change unit lands
  (shukuba-refine), opening a station (shukuba-open), or reviewing a change's spec, design or plan.
license: MIT
metadata:
  author: Eyal Golan
  version: "1.0.0"
  created: "2026-11-12"
  category: journey
  tags: nemawashi, shukuba, stations, review, blind, pm, journey
  risk: safe
  depends-on: stations-from-seed
---

# stations-blind-review

## Purpose

A run that cuts a route does not find that route's defects. Measured on one seed, runs of
`stations-from-seed` kept the stations they were handed nearly word for word and fixed few of the
defects in them, while separate runs with this skill's method, reading only the finished route, found
most of those defects and more. What made the difference was that the reader did not write the route.

So this skill is a **second run, never a step inside the cutting run.** It reads the seed as it stands
on disk and nothing about how it got there.

**This file is the orchestrator.** It owns the posture gate, resolving the seed, the review's path and
the commit. **The method is `prompts/rich.md`** — read it in full at Step 2 and apply it. What the
review checks, how it quotes and what it reports are there, and none of it is repeated here.

## Posture

**PM only.** Run in a `pm:` session or as the `pm` subagent; invoked from anywhere else, halt, say the
posture is wrong, and name the way in. The route is the PM's (`<CORE>/roles/loaders/pm_global.md`
§ *Responsibilities*, item 2), and so is the decision about what to do with a finding against it.

**Blind means a fresh run.** Start it with `<CORE>/launchers/skill/launcher.sh stations-blind-review
<project>`, or as a new `pm` subagent. A session that cut the route, or that has read the cutting
run's report, is not blind: it reads the route through the reasons it already holds. If this session
did either, halt and name the launcher.

## Input

**The project** — `system/projects/<project>/`. If none is supplied, ask which one. The prompt's
§ *What you read* fixes everything read from there.

**Where the product's code runs.** If judging a bar means running any of the product's code, run it
in a disposable copy — a fresh clone at the commit you are reading — never the product's main
checkout (`<CORE>/roles/CROSS_ROLE.md` § *Every seat — a run leaves the product's main checkout as it
found it*). Reading the code needs no copy.

## Workflow

### Step 1 — Gate, then resolve the seed

Check the posture and blindness (§ *Posture*) and halt there rather than proceeding.

Resolve `<nema>` = `system/projects/<project>/journey/nemawashi`. The picked seed is the single item at
that root — a file, or a folder holding `seed.md` — excluding `README.md` and the `unpicked/`,
`trail/` and `drop/` subfolders.

- **No seed at the root** — stop, write nothing, and name `seed-pick`.
- **The seed has no section whose heading begins `## Stations`, or it lists no unticked station** —
  stop, write nothing, and name `stations-from-seed`. There is no route to review.

- **The seed has uncommitted changes** (`git status --porcelain -- <the seed>` prints anything) —
  stop, write nothing, and say the route must be committed first. The review names the commit it read,
  and a route that exists only on disk has no commit to name.

`<seed-name>` is the seed file's name without `.md`, or the folder's name for a folder-seed.

### Step 2 — Read the method, then review

Read `prompts/rich.md` in full and apply it to the seed at the commit `HEAD` names now. Record that
commit: the review is true of that route and no later one.

### Step 3 — Write the review

Write it to `system/projects/<project>/docs/stations-blind-review/<seed-name>_review.md`, in the shape
the prompt's § *The review's shape* fixes. A project's `docs/` is where a record of its own work lives
(`<CORE>/doctrine/setup/kensaiapp_structure.md` § 2 Per-project, which names this path). A second
review of the same seed replaces the first; git keeps the earlier one. The file's first lines name the
commit it read, and that is how `stations-from-seed` tells whether it still describes the route.

**Write nothing else.** Not the seed, not a station, not any file under `journey/`. A review that
fixes what it finds becomes a second cutter, and its fixes then have no blind reader of their own.

### Step 4 — Commit

Per `<CORE>/doctrine/governance/commit_via_builder.md`, staging the review and nothing else, with
`--skill stations-blind-review` and `--prompt stations-blind-review/rich`, `--role PM`, and the
directional `Finish-line: <project> — progress: the route of <seed-name> reviewed blind`.

### Step 5 — Close

Report how many items the review maps, how many findings it raises under each of its five headings,
how many readings it left open, and the next move:

- **Findings raised** — the PM fixes each one in the route before the first station opens, by hand or
  by re-running `stations-from-seed`, which reads this review while it still describes the route, then
  runs this skill again on the fixed route. An open reading is the owner's to settle.
- **No findings** — open the first unticked station, `shukuba-open`.

---

## Outputs

| File / effect | Produced when |
|---|---|
| `system/projects/<project>/docs/stations-blind-review/<seed-name>_review.md`, one commit | The review ran (Step 3) |
| No change; `seed-pick` named | The seedbed root holds no seed |
| No change; `stations-from-seed` named | The seed has no route, or no unticked station |
| No change; the launcher named | The session is not blind |

## Critical Rules

- **The review is the only file this skill writes.** It edits no journey file. A finding is reported,
  never fixed here.
- **A fresh run, or none.** A session that cut the route or read why it was cut does not review it.
- **Every claim quotes its file.** A mapping quotes the bar; a finding quotes the ruling and the bar it
  is measured against; a claim about the code cites the file and line it read in this run.
- **Ambiguity is surfaced, not settled.** Where a ruling reads two ways, the review gives both and says
  which bar follows which.
- **The method is the prompt's.** A second copy here would be free to drift.
