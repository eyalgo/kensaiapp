---
version: "1.0.1"
---

# principal_pm_cut_seeds_run — the run shape every 根回し Nemawashi cut has

The shared mechanics of a **cut**: a Principal PM-posture run that reads some input and writes new
根回し Nemawashi seeds. Six things are the same whatever the input is — where the run works, where
each seed lands and under what name, the trace-back line every seed carries, what the run may move in
a seedbed, the commit, and the shape of a clean close and of a stop. They are stated here once, and
each cutter points at this file rather than carrying a copy.
**Single source — edit here, not in the carriers.**

It is shared material the cutters Read on demand, kept beside their two method prompts,
`principal_pm_cut_seeds.md` and `<CORE>/../skills/principal-pm/.claude/skills/seeds-from-product-docs/prompts/rich.md`.

**What this file does not own.** *What* to cut and *whether* to cut are the calling skill's **method
prompt**, named by that skill; the posture gate is the calling skill's; a seed's shape is
`<CORE>/templates/journey-templates/nemawashi_template.md`; the builder's own mechanics are
`<CORE>/doctrine/governance/commit_via_builder.md`, and a journey item's move is
`<CORE>/docs/journey_move.md`. All four are pointed at from here, never restated. Where a rule below turns on something only
the caller knows, it names *the method prompt's* section rather than a particular one.

## Where the run works — in the instance, in place

**A cut opens no worktree and no branch.** It works in the instance it was started in, on whatever
branch that instance is standing on, and it writes and commits there — the owner's call, 2026-09-05.
This **reverses** the call of 2026-08-30, which had every cut open its own worktree branched from
local `main`.

**What the reversal was about, so it is not re-argued from the old reasoning.** A cut's branch was
never landed by the thing that made it: this file said in as many words that the branch does not
merge back and that landing it is the owner's move. So a cut ended with its seeds sitting in a tree
nobody had a reason to visit, and they reached the pool a PM actually reads only if someone
remembered to merge. A branch that is always someone else's to land is a branch that is usually not
landed, and a seed nobody can find is the one failure a cut exists to prevent.

**So the seeds land where a PM will find them, immediately.** Write them at the paths § *Where a seed
lands, and under what name* fixes, in the instance as it stands, and commit them there per
§ *The commit*.

**Resolve every path the run was handed against that instance** — the tree the caller was looking at
when they started the run. A path that is not there is an input whose claim does not hold, which is
the method prompt's first stop case. It is no longer possibly a base-ref accident, and the long
argument this section used to carry about which ref a worktree defaults to is gone with the worktree
that needed it.

**What this costs, and it is real.** A cut's writes and its moves are immediate and shared. There is
no branch to discard, so a cut that goes wrong is undone with git against the commits it made rather
than by deleting a tree, and a run that halts mid-cut leaves its committed partial work in the
instance rather than parked out of the way. § *What the run may move, and what it does not* is where
this lands hardest, and it says so there rather than here.

## Where a seed lands, and under what name

- **A project's seed** → `system/projects/<project>/journey/nemawashi/unpicked/<name>.md`. The pool,
  never the seedbed root — lifting one to a root is the PM's pick, per `<CORE>/docs/michi_agari.md`,
  its *Cut an idea, or a product's settled documents, into seeds* row.
- **An instance seed** → `system/nemawashi/unpicked/<name>.md`, when the method prompt's § *Where the
  seed lands* puts it at instance level. Same reason as above rather than a second one — the manifest
  gives the instance seedbed the same two positions — "empty root means none is active, and the
  candidate pool sits in `unpicked/`" (`<CORE>/doctrine/setup/kensaiapp_structure.md`) — and a cut
  writing a **new** seed to that root would both make a pick and collide with whatever idea is already
  active there.
- **`<name>`** is the seed template's `<YYYY-MM-DD>_<slug>` form, with the date being the day of the
  cut. The template's opening block states the form; it is not restated here.

Create the `unpicked/` folder if a project's seedbed is missing one. Write nothing anywhere else: no
station file, no report file, no edit to a document the cut read.

## The trace-back line

**Every seed a cut writes carries one, in its `## Source` section, and it opens with `Cut from `.**
The path or the standing-in words follow — which of the two, and why the line is owed at all, are the
method prompt's, at its section on tracing a seed back to what it came from.

The fixed opening is this file's, and it is what makes the chain findable: `git grep "Cut from"` over
the seedbeds returns every seed a cut produced, and returns nothing at all if the line drifts into
prose. It is the wording seeds already carry — that command returned 3 files on 2026-08-30, each one
naming the idea it came from — so the rule here fixes a convention rather than inventing one.

## What the run may move, and what it does not

The seedbeds are the run's to move — the owner's call, 2026-08-30. The moves themselves are
`<CORE>/docs/journey_move.md`'s; what is a cut's own is which of them a cut is allowed.

**A move is no longer free, and that changes what a cut should be willing to do.** The 2026-08-30
permission rested on the worktree: a move on a branch nobody had landed cost nothing, so a cut could
move first and leave the owner to decide by landing the branch or discarding it. There is no branch
now (§ *Where the run works*), so every move a cut makes is immediate and shared — the decision the
branch used to defer to the owner is now taken by the cut. **So a cut makes a move only where it is
certain.** Where it is not, it writes the seed, makes no move, and names in its report the move it
did not make and what would settle it. A move a run was unsure about does not become cheaper by being
made.

**Picking a seed the cut produced is not the run's.** Those land in a project's `unpicked/`, which is
the whole reason a cut writes into a pool rather than a root, and electing one is the PM's call.

**A cutter whose input is itself a journey artifact may have moves on that input.** Whether it does,
and which, is that skill's own to state — this file grants none.

**A router station already open on something else.** No file moves. A cut writes a routing seed and
never a station (the method prompt's § *When a routing seed is earned*), and the router is opened
later from that seed's checklist item — so nothing a run produces wants the one active slot while the
run is happening. Setting the open station aside therefore costs no move at all. What the routing seed
owes instead is a sentence naming the station that is open, so the seat that opens the router later
meets it knowingly rather than by surprise.

**Where a set-aside station would go, if a move were ever really needed, is undecided.** The instance
router has one destination — "There is no `parked/` here" and "a router station has one destination"
(`<CORE>/doctrine/setup/kensaiapp_structure.md`) — and `trail/` records a station that was reached.
Answering it would be a doctrine change, and no cut is blocked by it while the paragraph above holds.

## The commit

Through the one builder, per `<CORE>/doctrine/governance/commit_via_builder.md`. That file owns the flag forms,
the staged-set guard and the `git mv` declaration; read it there rather than from here. Three things
are the run's to supply:

- **`--actor principal-pm`** — every cutter runs in the Principal PM posture and halts outside it, so
  name it, never derive it.
- **`--skill <the cutting skill>`**, since that skill produced what is being committed, and
  **`--prompt <its method prompt>`** for the method it was cut by.
- **One commit per scope.** A commit carries exactly one directional trailer, so seeds written into a
  project's pool commit separately from seeds written into the instance seedbed, and separately again
  per project. Which trailer each takes is the same recipe's item 6.

A move the run was allowed to make rides in the commit for its own scope, its rename declared per the
recipe.

## Close, or stop

**A clean cut** reports what it wrote — each seed by its triple, `<project> · nemawashi · <name>`, and
the routing seed if one was earned — and stops there. Picking a seed the cut produced, opening a station and walking it
are the PM's.

**A stop** happens the moment the method prompt's § *When you stop* is met. Commit what has already
been written (§ *The commit*), then report, in the run's closing message rather than in a new file:
which case fired, the claim or the seed by its triple that fired it, and the check that produced the
verdict. Write no further seeds, and do not shrink the input until the obstacle stops mattering. The
committed partial work stays in the instance, where the method prompt's re-run-after-a-stop section
folds it — and where anyone reading the seedbed meets it, which is why a stop says plainly that the
cut is unfinished rather than leaving a half-cut pool to be read as a whole one.
