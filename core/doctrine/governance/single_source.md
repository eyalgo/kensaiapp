---
version: "1.4.0"
---

# Single source — a fact has one owner

Governs **every written artifact in the instance**: doctrine, skills, prompts, templates, loaders,
READMEs, agent files, the journey. This file owns the rule and nothing else — which file owns which
fact is always that file's own declaration, never a list kept here.

## The rule

**A fact has one owner. Every other file points at it and does not restate it.**

**A file declares what it owns.** That is the other half, and it is load-bearing rather than
decorative: without the declaration there is no way to ask whether a sentence belongs where it sits,
and the question collapses into taste.

**A restatement that disagrees with its owner is a bug in the copy.** Never a precedence call — the
owner is canonical, and the copy is deleted rather than reconciled.

## Why a copy is worse than it looks

**A copy is not wrong when it is written.** That is the whole problem. Whoever wrote it had just read
the owner; it was accurate, and it stayed accurate right up until the owner changed. At that moment it
became false — and nobody was wrong, nothing happened, and there is no pointer from the owner back to
the copy to say it has just been falsified.

So the failure has **no author and no moment**. Review cannot catch it, because review reads a change,
and this defect lands in the file nobody changed.

**A copy is a promise to keep two files in sync forever**, made silently, on behalf of everyone who
edits either one later — none of whom agreed to it and most of whom will never know it exists.

A copy usually feels like a service to the reader: they get the fact here instead of going to look
for it. That reading is the trap. A reader who follows a pointer gets what is true. A reader served a
copy gets what was true when someone else was writing.

## What this looked like when we found it

`kaizen/skills.md` predicted it, in the same sentence it was breaking:

> a second list here would be a copy free to drift, which is how the agent and the posture went
> missing the first time anyone wrote one out.

That file then carried two copies of the six-layer stack list, 190 lines apart, each naming three of
six — while stating, between them, that the list belongs to `kaizen/lenses/contract.md`. Nobody had
applied the rule to the file it was written in.

Five more of the same shape, all found in one session:

- `README.md` — the doctrine index — enumerated the kaizen lens set and missed `locate_layer.md`.
  **That list drifted the same day the file was created**, in the very session that fixed two of the
  others.
- `README.md` also restated this file's own predecessor rule (stub and body must agree), which
  `doctrine_structure.md` owns.
- `engineering/skill_evidence.md` said a skill "discards [the owner's answers] when it settles" —
  true until `product-prd` gave them a permanent trail. Three copies of that one sentence.
- The `kaizen-product-prd` station note said the answered companion "is gone the moment the round
  settles" — a fourth copy of that claim, missed by the fix that caught the other three.
- `kaizen/skills.md` said a round starts from "an empty product" — true of the one skill it was
  written beside, false of any skill that edits a live codebase.

Not one of them had an author who was wrong.

## What is not a copy

- **A pointer** — names the owner and stops. `per <owner> § <section>` is the whole form.
- **A declaration** — a file saying what it owns. Required, not merely permitted.
- **An index** — a file whose job is naming what exists, like `README.md` next door. An index owns
  the **names**. It does not own the **contents**, and the moment it enumerates what a named file
  contains, it has made a copy.

The tell that catches all three: **could this sentence become false without anyone editing this
file?** If yes, it is a copy, whatever it looks like.

## A pointer at a journey artifact names project, kind and name

One class of artifact has a path that spells its **state** rather than merely its home: a 根回し
Nemawashi seed, a 宿場 Shukuba station and a 飛び石 Tobiishi. The seedbed root says an idea is active,
`unpicked/` says it is a candidate, `trail/` says it ripened, `drop/` says it was killed, a station's
`parked/` says it waits. So a pick, un-pick, retire, drop or park **renames the file**, and a pointer
written as a path is falsified by a move nobody made against it — § *Why a copy is worse than it
looks*, arriving through the filesystem instead of through prose.

**So the pointer is the triple: project · kind · name.**

> `<project> · nemawashi · <YYYY-MM-DD>_<slug>`

**One backtick span, middot-separated — not three spans with the separator between them.** A
separator sitting *outside* a span is the line-wrap trap `check_journey_links.py` exists to defeat:
the normalisation that repairs a wrapped span only runs *inside* a span, so a three-span form is
invisible to it the moment prose wraps between two of the spans. One span keeps the whole triple
inside the repair the tool already runs, and carries no slash, so a reader cannot mistake it for a
path and "repair" it by prefixing `system/projects/`.

Kind is one of `nemawashi`, `shukuba`, `tobiishi`. Name is the artifact's `<YYYY-MM-DD>_<slug>` — for
a Tobiishi and a folder-seed, the **folder's** name, never a file inside it. A move changes none of
the three, so the pointer survives every move the journey can make.

**`<project>` is a project name, or the literal `instance`.** Nemawashi and Shukuba each exist at
both levels (`kensaiapp_structure.md` §1) — the instance's own seedbed and router station,
`system/nemawashi/` and `system/shukuba/`, which sit outside every project and so have no project
name to carry. `instance · nemawashi · <name>` and `instance · shukuba · <name>` name those; there
is no instance Tobiishi (§1's "Not at app level"), so `instance · tobiishi · …` never resolves.

**All three parts are load-bearing, and nothing shorter resolves.** Kind, because one project may
hold a seed and a station under the same name. Project, because two projects may hold a seed under
the same name. Name alone identifies nothing. Both collisions occur in a real seedbed rather than in
principle — an instance can enumerate its own:

```bash
# a name held by both a seed and a station in one project — `<project>` is the bare name this
# section's own triple gives it, never a path, so the check spells the path itself; a wrong or
# missing project fails loudly here rather than comparing two empty streams and printing nothing.
for kind in nemawashi shukuba; do
  dir="system/projects/<project>/journey/$kind"
  [ -d "$dir" ] || { echo "no such directory: $dir — check <project>" >&2; exit 2; }
done
comm -12 <(find "system/projects/<project>/journey/nemawashi" -name '*.md' ! -name README.md | sed 's#.*/##' | sort -u) \
         <(find "system/projects/<project>/journey/shukuba"   -name '*.md' ! -name README.md | sed 's#.*/##' | sort -u)
```

**The invariant it rests on: within a project, a name occurs once per kind.** That is what makes the
triple a key rather than a description, and it is a property of the seedbeds rather than a rule
anything enforces — an instance whose pools broke it would have to say so here.

**A key into another instance carries a fourth part in front: the instance's name.**

> `<instance> · <project> · <kind> · <name>`

A satellite cites its host's journey, and a host may cite a satellite's. The three parts above
resolve in the instance the pointer is written in, so a correct pointer into another one reads as
dead, and prose naming the instance is never checked against a move. The fourth part is optional:
three parts still mean *this* instance, and the three keep every property stated above.
`<instance>` is the host's own name or this instance's own (each is the heading its `kensaiapp.md`
opens with), or the name the host's `system/satellites.md` gives a satellite. `check_journey_links.py`
resolves it to that instance's root and checks the key there. A name that is none of these is
dead, never skipped. Use the four-part key, not a path, for a journey artifact in another instance,
for the reason above: a move renames the path.

**What this does not reach.** Every other artifact is still named by its repo-relative path — the
triple is for the one class whose path moves. Prose still says where a thing sits when the position
*is* the point; what the triple replaces is the path used as an **identifier**, which is the only use
a move breaks. And core and doctrine cite no journey artifact at all, by path or by triple —
`core/tools/check_vendor_neutrality.py` reads a dated journey stem in a scanned file as a leak,
with or without its `system/projects/<name>/…/` prefix. So this form is the journey's own, and the
layers below it stay clear of the journey entirely.

Converting a path pointer that already exists is lazy work, and a broken one is repaired rather than
reported: `found_while_walking.md` § *A broken journey pointer is repaired, and the triple is what
stops it breaking*.

## Before you give a fact an owner, look for the one it already has

A fact found scattered across many files usually **already has a good owner, filed where nothing can
cite it.** The fix is then a `git mv` and a set of pointers, not a new file — no new content to
review, and every existing reference becomes a path edit rather than a rewrite.

Look before designing. A new file proposed for a fact that is already well stated somewhere adds a
second statement of it, which is what the rule above deletes.

**The tier is what usually hides the owner.** A file in the wrong tier is unreachable rather than
absent: `task_map.md` routes by bare filename resolvable through `README.md`, so a rule sitting
outside the doctrine set cannot be reached from the index — and everything that needs it copies it
instead. That is what a scatter of copies most often means.

**An owner's hint that a file may already exist is a pointer, not a hedge.** "I think we may have a
file", "isn't there already…" — go and look. Answering it with a design is the failure it was meant
to prevent.

## A record about an owner is not the owner

Our own records — a delegate report, a findings page, an audit, a prior session's handoff — describe
what someone found when they looked. **Citing one is not citing the thing it describes.** It has a
path and a line range, so it satisfies the shape of a citation while answering a different question:
what a session concluded, not what the file says.

A record is also frozen at the moment it was written, so it carries the owner's content forward
unchanged while the owner moves — the copy problem above, with an author and a date attached.

**Open the owner.** Where a record's claim is load-bearing, reach the file the record was describing
and cite that. This holds hardest for a claim that something is *absent* or *must not be done* —
nobody tests a reason not to act, so an inherited "X does not exist" survives long after X does.

## The stub is the copy we keep

One copy is deliberate. `AGENTS.md` carries contract-shape stubs of doctrine bodies, because the
runtime needs the contract every session and a body is loaded on demand. `doctrine_structure.md`
§ Consistency model owns which side is canonical.

It is a copy all the same, and it drifts like one. The exception is the loading requirement, not the
rule — a stub earns its duplication by being unable to be a pointer. Nothing else here can make that
argument, so nothing else gets the exception.

## The check

`kaizen/lenses/cold_read.md` asks it, one file at a time, at kaizen step 2. That file owns the
question.
