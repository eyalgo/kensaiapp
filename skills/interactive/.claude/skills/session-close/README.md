# session-close

A session's output is not the same as its residue. The repo keeps the files that were written; what
dies when the turn ends is everything around them — which of the dirty paths were deliberate, where the
station actually stands versus where its file says it stands, the three things the session noticed and
correctly refused to act on, and the correction it earned the hard way. None of that shows up in
`git status`, which is why a clean tree has never been evidence that a session closed cleanly.

This skill is the sweep that recovers it. It replaces a retired `/session-close` slash command whose
three steps each pointed at machinery that no longer exists: an `inbox.md` this instance does not have,
a `save-memory` command targeting a directory absent since `98c0946`, and a `dual-commit` skill that
lives only in `~/.claude/skills_parked/`. What survived the command was its intent, not its shape — so
this is a rebuild against the surfaces that exist now (the journey, the shared commit builder, the
corrections store), not a repointing of the old body.

**It routes; it does not act.** Every move the sweep identifies already has an owner. Performing them
here would make this a second implementation of five journey verbs, each free to drift from the first —
and the distinctions that would get lost are the load-bearing ones (park leaves a seed item unticked,
retire ticks it). So each sweep's output is a named move and the skill that owns it.

## What It Does

- **Sweep 1 — uncommitted work.** Reads the tree of every repo and worktree the session touched, not
  just the one it started in, and sorts each dirty path into commit / deliberately-left / not-yours.
  Commits go through the shared builder recipe, path by path; `git add -A` is ruled out because on a
  shared index it sweeps in another session's work.
- **Sweep 2 — journey position.** Runs `journey_status.py` rather than trusting the session's own
  account, then maps what the session did to the journey verb that owns the move. Includes the common
  answer that no move is owed, because an open station whose file describes the work *is* the
  continuation record.
- **Sweep 3 — loose findings.** Sweeps what the session surfaced but was right not to do into 根回し
  Nemawashi seeds, in the project whose Agari the finding serves — searching the board first so a seed
  already filed does not get a duplicate. This is the sweep with no other home.
- **Sweep 4 — session-craft.** Decides which of the two stores a durable lesson belongs in per
  `corrections_store.md`, and writes to neither: the store's mechanism is the harness's, and graduation
  is one act that must not be done by halves at session close.
- **A close-out summary** with a mandatory `## Left open` section, so a close-out that could not settle
  something says so instead of reading as complete.

## File Structure

```
session-close/
├── SKILL.md     the four sweeps, their gates, the routing tables, and the summary template
└── README.md    this file
```

No `evals/`. The skill's output is a routing decision over whatever live state the instance happens to
be in, so a fixture would have to freeze an instance's journey, working tree and store to assert
against — and the dev-skills Agari adds evals only where a skill earns them rather than as a blanket
gate (`system/projects/dev-skills/agari.md:33-38`). If the routing tables prove unreliable in use, that
is when they earn a fixture.

## Depends On

Named, not invoked — the sweep hands each move to its owner and stops:

| Skill | The move it owns |
|---|---|
| `shukuba-retire` | Close a station whose reached-when is met; tick the seed item |
| `shukuba-park` | Set an unreached station down; leave the seed item unticked |
| `nemawashi-drop` | Drop a killed idea — ruled out, superseded, not going to be done |
| `nemawashi-unpick` | Return the active idea to the candidate pool |
| `tobiishi-seal` | Seal a change and merge it |

It also reads `<CORE>/doctrine/governance/commit_via_builder.md` (how sweep 1 commits) and runs
`<CORE>/tools/journey_status.py` (what sweep 2 reads). Neither is a skill.

## When to Use

At the end of a working session, or when handing one over. The case worth naming is the one that looks
like it does not need it: a session that committed everything it wrote and left the tree clean has
still not run sweeps 3 and 4, and those are the two whose contents exist nowhere else.

Not for the journey moves themselves — those are the skills in the table above, invoked directly. Not
for a routine mid-session commit, which is the shared recipe alone. Not for deciding that a station, an
idea, or a change is finished: this skill closes a *session*, and never claims a leg was walked.
