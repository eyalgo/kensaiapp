---
version: "2.3.0"
---

# Found while walking — a defect found mid-route is fixed before the merge

Governs every session working on a branch, whatever posture it holds and whatever route it is on —
a station walked by hand, a change unit carried through the pipeline, an ad-hoc arc.

> **Owns:** what happens to a defect a session finds while it is working on something else, what that
> costs the merge, where a surfaced defect is written down, and — for a journey pointer
> specifically — when a live-but-superseded citation form converts to the current one.
> **Does not own:** who may authorize a merge or what its commit carries
> (`commit_format.md`), how a change is classified once it is one
> (`flow/change_classification.md`), the shape of the journey and who makes each of its moves
> (`<CORE>/docs/michi_agari.md`), or how an idea is cut into seeds (the Principal PM's seat).

---

## The rule

**A defect found while walking is fixed on the build branch.** Informally, *the boy-scout rule*. The
owner's standing rule, restated 2026-08-31.

Three clauses, and they are one rule:

1. **Small — fixed in place, on the branch.** The session that found it repairs it where it stands,
   in the branch it is already on. No handoff, no note, no ticket.
2. **Big — cut as a seed on the branch, and walked *before* the merge.** The seed is cut where the
   defect was found, and the branch does not merge until that seed has been walked. "Before the
   merge" is the whole of the clause: a seed cut on a branch and merged unwalked has deferred the
   work while looking like it captured it.
3. **Only a decision not to walk it sends that seed to `main`.** That decision is the one exit, and
   it is a decision someone makes — not what happens by default when a branch is ready and the seed
   is not.

**The rule does not fix where small ends and big begins — except for one class pre-classified
below.** That call belongs to the session that found the defect, with one standing exception: a
dead journey pointer is always clause 1, no exception, by the section right after this one. Outside
that one pre-classified class, misjudging the size costs a redirect and skipping the rule costs the
fix — what the rule fixes is what follows from either answer, not which answer it is.

## A broken journey pointer is repaired, and the triple is what stops it breaking

**A pointer aimed at a journey artifact that a move has broken is repaired by the session that finds
it** — clause 1, with no exception. Reporting it and walking on leaves the guard off: a routing
seed's items name the seeds they route to and those seeds name the item back, and a dead pointer
removes the only check against a missed tick without announcing that it has.

**The break has a cause.** A journey artifact cited by its path is cited by its *position*, and a
pick, un-pick, retire, drop or park changes the position. Cited by the triple a move does not
change — project · kind · name — it cannot break at all; the form is `single_source.md` § *A pointer
at a journey artifact names project, kind and name*.

**Converting the path pointers that already exist is lazy work, never a sweep — for a pool that still
carries them.** A live file you open converts its own as part of that turn — the shape of
`kaizen/lenses/containment.md` § *Sweep retired vocabulary the same way*, and for its reason: a
whole-tree pass over files nobody is working in is a tool's job rather than a walking session's, and
seven such pointers repaired by hand on one branch were four dead again about a hundred commits
later. Do not open a file in order to convert it, in an instance whose pools are not yet converted.
`trail/`, `drop/` and `parked/` are never converted — a retired seed naming where a sibling sat when
it retired is correct as history.

**An instance that has converted is held there by a test, not by this clause.** Once a bulk pass
has converted every live path-form pointer it could reach, the lazy clause above has nothing left to
govern in that instance. What keeps the pool converted is a test that fails the suite the moment a
live path-form pointer reappears — `core/tools/test_journey_pointers_are_triples.py` is one, and it
checks only the instance holding the `core/` it sits in. Every pool that has not been converted,
a satellite's included, stays under the lazy clause until its own instance runs a pass and stands up
its own gate.

**That shape is a model to borrow, not a proof it works.** The sea metaphor containment.md's own
rule converts on open was retired 2026-08-27, and the same convert-on-open convention has governed
it since — yet `fleet` was written into `core/` in 15 commits after that date
(`git log --since=2026-08-27 -S'fleet' -- core/`, filtered to commits that add the word rather than
merely touch a line naming it; measured 2026-09-12). Lazy conversion does not stop recurrence by
itself; what stops it here is `found_while_walking.md`'s own clause 1 treating a *dead* pointer as
never optional, which the retired-vocabulary sweep has no equivalent of — a stale word does not
break a build the way a dead pointer breaks a routing seed's guard.

**Convert only where a check can resolve the result.** A path pointer is at least visible to a
checker that resolves paths; a triple that nothing resolves yet is invisible, so converting ahead of
the resolver removes the guard instead of repairing it — the same silent pass as a filter that
matches nothing. Where the tooling cannot yet read the triple, repair the pointer in the form it is
written in and leave the conversion for the turn after the resolver lands.

**Repair and conversion are different obligations, and the difference is broken versus old.** A
*dead* pointer is a defect and is repaired now, whatever form it is written in. A *live* path pointer
is merely old, and converts when its file is next opened.

The move-side mechanics — when to run the check, and why its exit code never gates the move — are
`<CORE>/docs/journey_move.md` § *After the move, say which pointers it broke*, which
carries no second statement of this rule.

## Where a surfaced defect is written down

A defect that is surfaced rather than fixed needs somewhere to land, or surfacing is a sentence in a
transcript — the failure § *What it prevents* names. **The instance's own `docs/findings/` is that
place**, one file per run that found something wrong with kensaiapp's machinery rather than with a
product. `setup/kensaiapp_structure.md` § 1 Root owns the path and what each entry names; this
section owns the rest.

**It is written by the seat whose run met the defect, in that seat's own instance.** No skill
carries a step for it: `product-sdd` and `product-architecture` runs have each filed one from this rule
alone. The rule is the
seat writes where its run found the defect, not that one skill owns the store.

**The run that writes a finding commits it, in a commit of its own, before the run ends.** That holds
when the rest of the run did not land, and it holds when another finding already lies uncommitted
beside it. Neither stopping early nor finding an uncommitted sibling is a reason to leave the finding
for someone else to commit. An uncommitted finding leaves the working tree dirty, and a journey move
that runs next refuses on a dirty tree — on 2026-09-23 two findings left untracked by `product-sdd`
and `product-architecture` stopped a satellite's `chain-change` at `shukuba-open`.

**A satellite writes to its own `docs/findings/`, never to the host's** — the owner's call,
2026-09-12. A satellite reads the host's `core/` through `<CORE>` and finds defects in files it does
not hold, so the tempting move is to write the finding where the broken file lives. It does not: the
finding is a record of what that run found, and it stays in the instance that ran.
`setup/shared_core_instance.md` is why — a satellite has no write on the host's tree, and a store that
accepted cross-instance writes would make every satellite's PPM a committer in a repo it cannot test.

**The host reading those stores is by hand, and that is the current design rather than a gap** — the
owner's call, same day. There is no harvest, no sweep, and no tool that gathers a satellite's findings
into the host; the owner carries them across. So a satellite's finding is written to be read cold by a
person, and a run that files one has discharged its whole duty. Nothing further is owed by it, and
nothing downstream is waiting on it.

**A finding whose defect is resolved moves to `docs/findings/resolved/`** — the owner's call,
2026-10-13, naming what this host and its satellites had already been doing. The move is a plain
`git mv`, the file unedited, and the commit that makes it names what resolved the defect: the commit
that fixed it, or the report-back that says it landed. The instance that holds the finding moves it.
A satellite moves its own once the host's answer checks out against the host's `main`, and the host
never moves a satellite's. A finding still open stays at the top level, so the top level is what is
still owed. `resolved/` is `[user]` like its parent: the first resolved finding creates it.

**The folder is `[user]`, so the first finding creates it.** Setup never stamps it, exactly as it never
stamps `docs/proposals/` or `docs/reviews/`, and an instance with none has simply not filed one — this
host included, as of 2026-09-12. Absence is not drift.

**A file here is never the repair.** It records that something is wrong; whether that something is
fixed in place or left is § *The rule* above, and writing it down does not answer that question or
discharge it.

## The default is the owner's to override, per case

Clause 3 is the lever, and the owner pulls it. On 2026-08-31 the owner overrode the default for one
finding on the ground that it was its own investigation, and that seed went to `main` instead of
being walked on the branch it was found on. The default holds until someone decides otherwise; the
deciding is the owner's.

## What it prevents

The owner's reason, 2026-09-01: without a rule here, a defect found mid-walk becomes *"backlog of
bugs or bugs without a backlog for them"*.

Those are the two failures, and they are the same failure at two speeds. A finding written down and
left is a backlog nobody empties. A finding not written down is worse — the branch merges, the walk
ends, the session's context is gone, and the only record that anything was wrong was a sentence in a
transcript. Fixing on the branch is what makes the third state possible: the defect leaves the
system in the run that found it, while the one context that understood it still exists.

## This file is read by the session it binds

A run that lands a rule is itself walking a branch, so a defect it finds while landing this file is
governed by the sentence it is writing. That is not a curiosity — it is the cheapest available test
of the rule, and `doctrine_structure.md` § *A rule-stating file is its own first reader* requires it
of every file here.
