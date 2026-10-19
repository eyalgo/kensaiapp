---
version: "1.0.0"
---

# Journey move — the one way a journey artifact changes folder

The shared mechanic for the skills that move a 根回し Nemawashi seed, a 宿場 Shukuba station, or a
飛び石 Tobiishi's change-work folder between its folder's root and one of that folder's siblings —
`trail/`, a seed's `unpicked/` or `drop/`, and a station's `parked/`. A Tobiishi moves as a
**folder**, and so does a seed in its folder form (`seed.md` inside a directory of the same name); a
station, and a seed in its file form, move as a file. A Tobiishi's caller declares two directory
prefixes rather than two paths; the ordering rule below is the same for all of them, because
`git mv` behaves the same way either way. Read on demand by any such skill — each names this file at
the steps it covers, and no roster
of them is kept here.
**Single source — edit here, not in the carriers.**

It is shared material the skills Read on demand, kept beside `michi_agari.md`, the journey model whose
moves it mechanises.

**What this file does not own.** Which verb each move is called — you **seal** a 飛び石 Tobiishi,
**close** a reached station, **retire** a finished idea, **unpick** an unfinished one — belongs to
`<CORE>/docs/michi_agari.md` § Quick reference. The builder's own mechanics belong to
`<CORE>/doctrine/governance/commit_via_builder.md`. Both are pointed at from here, never restated.

## The two levels, and what exists at each

A **project** (`system/projects/<name>/journey/`) has all three journey parts — a 根回し Nemawashi seedbed
with a pick mechanic (one active idea at the root, candidates in `unpicked/`, and two record bins —
`trail/` for the ideas that were walked, `drop/` for the ones that were killed), a 宿場 Shukuba holding
exactly one active station, and 飛び石 Tobiishi.

The **instance** carries a bearing (`system/michi.md`), its own seedbed (`system/nemawashi/`, with its own
`unpicked/`, `trail/` and `drop/`) and a router 宿場 Shukuba (`system/shukuba/`, with `trail/` and no `parked/`). The
seedbed's pick is made and undone **by hand**, not by any of these project-level skills
(`system/nemawashi/README.md` § "Pick one → see only it"). The router **coordinates and is never
walked** — it has no station-level reached-when for a project skill to check and no seed checklist item
to tick, and its file moves to `trail/` by hand too (`system/shukuba/README.md` §§ "A router coordinates"
and "Lifecycle"). The instance has **no 飛び石 Tobiishi** — nothing reaches the Michi, so it has no
change-pipeline of its own (`<CORE>/docs/michi_agari.md` § "Where the *work* lives";
`<CORE>/doctrine/setup/kensaiapp_structure.md` §1 App-level).

So a skill's level support follows from what it moves, and each says which applies to it. When an
invocation points at a level a skill does not serve, **say so and stop**, naming the skill that does —
never invent the missing part, and never create a folder the level does not have.

## The seedbed's `unpicked/` is the candidate pool

At project level, `unpicked/` **is** the candidate pool: it may hold any number of seeds at any time,
whether or not an idea is active. Its count is never a function of the pick — electing a seed does not
empty it, and no idea being active does not fill it.

**A pick elects one seed out of the pool; nothing else moves.** With no active idea, the root is
**empty** — that is the seedbed's resting shape, not a transitional one — and the pool sits in
`unpicked/`, however many candidates it holds. An **empty root is unambiguous**: it says no idea is
active without recourse to any seed's contents — a reader checks the root first, never the pool's
contents, to tell whether an idea is active.

### The pick and the un-pick

**Project level only.** The instance seedbed's pick and un-pick are done **by hand**, not by these
skills — `system/nemawashi/README.md` § "Pick one → see only it" names the move and says who does it.
These skills perform the project-level move only.

**A pick moves exactly one file: the elected seed, `unpicked/` → root.** No other candidate is
touched — the pool stays exactly as it was, minus the one seed elected.

```bash
git mv "<nema>/unpicked/<elected>.md" "<nema>/<elected>.md"
```

**An un-pick is the inverse: it moves exactly one file, the seed, root → `unpicked/`.** The end state
is an **empty root** — no idea active — and the pool now holds this seed alongside whatever else was
already in `unpicked/`.

```bash
git mv "<nema>/<seed>.md" "<nema>/unpicked/<seed>.md"
```

Neither move touches any other seed, and nothing about ending a seed's active-ness — by finishing it or
by only setting it down — obliges any other file to move. The one other file either move edits is the
Principal PM's context, below. The pool's shape after a pick, an un-pick, or
a retire is whatever it already was, unaffected by any of the three.

**A drop is the fourth move, and the only one that can subtract from the pool.** `nemawashi-drop` takes
a seed from the root *or* from `unpicked/`, so a drop of a candidate leaves the pool one shorter while a
drop of the active idea leaves it untouched — the one case where the invariant above does not hold, and
the reason it names the three rather than saying "any move".

### The Principal PM's picked seeds

**A project-level pick adds a line; the move that takes that seed off its root removes it, in the same
commit.** The line sits under `## Picked seeds` in the instance's `system/contexts/CONTEXT_PPM.md`, one
line per picked seed across every project, and is the one whose backtick span reads
`<project> · nemawashi · <slug>`. `nemawashi-pick`'s script appends it. `nemawashi-unpick`,
`nemawashi-retire` and `nemawashi-drop` of the active idea remove it:

- **Delete that one line and nothing else.** Other projects' lines, the section heading and every other
  section stay exactly as they are.
- **Stage it with `--add system/contexts/CONTEXT_PPM.md`** beside the move's `--staged` halves.
- **No file, no section, or no such line → nothing to remove.** Pass no `--add`, and say in the report
  that no line was there. A candidate dropped from `unpicked/` was never picked and never has a line,
  and an instance-level seed is never listed.

## Resolving the target

Every one of these skills is invoked against **one** journey item, named either as a path or as enough to
identify one — typically the project and the slug. Whichever form arrives, resolve it to a single item and
confirm three things before touching anything:

- the file **exists** — for a 根回し Nemawashi seed, a folder holding `seed.md` counts exactly as its
  `<slug>.md` file would (`kensaiapp_structure.md` § 2): `seed.md` is the one file ever read as the seed
  or edited as one, and the folder moves **whole**. Shukuba and Tobiishi never take this shape;
- its **containing folder is the right journey part** for this operation, and is that part's **root** —
  not one of its `trail/`, `drop/`, `unpicked/` or `parked/` subfolders, and not a sibling part. A file
  already in a subfolder has already been moved; moving it again is a different question, and the answer
  is usually that the caller means something else.

  **One exception, and it is `nemawashi-drop`'s: `unpicked/` is an accepted origin for a drop.** A
  candidate ruled out before it was ever picked never reached the root, so a root-only rule would refuse
  the case that skill exists for. The exception is stated here rather than left to the carrier, because a
  skill that quietly overrides the file it says it is following teaches its next reader to do the same.
  It is the only relaxation: `trail/`, `drop/` and the station folders stay refused for every skill,
  including that one;
- **exactly one** item matches. Zero or more than one → **stop**, naming what you found (§ *Ask, don't guess*).

Each skill adds its own conditions on top — whether the item is finished, whether it is the active one,
whether the level is served — and those gates are theirs to state.

## Park, don't strike

A journey artifact leaves its slot **by being moved**, never by being marked. It is not
`~~struck through~~`, not given a done-marker, not annotated in place. The folder it sits in *is* the
statement about it: the root says active, `trail/` says ripened, `drop/` says killed, and a seed's
`unpicked/` or a station's `parked/` says waiting.

That is also why a wrong destination cannot be repaired with a note. A file in `trail/` claims a walk
happened; if it did not, no annotation inside the file makes the record true — because the record is
read by looking at which folder things are in, not by reading every file in them.

## Move whole — and the one edit that is allowed

`git mv` the file — or, for a folder-seed, the whole folder in one `git mv`. Its content is preserved
verbatim, and the *why* of the move goes in the **commit body**, which is what a trail entry or a parked
candidate is read alongside. No outcome note, no closing summary, no set-aside paragraph is added to the
artifact itself.

**The one exception is a self-description the move just falsified.** A file may assert its own state
in its own text — a header saying it is *picked*, *active*, or *current* — and for a folder-seed that
text lives in `seed.md`, the one file inside the folder this exception ever touches. Sitting in
`unpicked/` while saying "active" is a contradiction between content and location, and correcting it is
not adding content: it is making the file's claim about itself true again.

Keep that correction tight:

- Correct only statements of **present** state — picked / active / current / being walked now.
- Leave **forward-looking** prose alone. "When this is picked, …" is accurate for a candidate and is
  falsified by nothing.
- Correct nothing else. If there is more to say, the commit body says it.
- **Invent no marker.** If the file makes no claim about its own currency — the common case — it moves
  whole, and the commit's stat shows the file as a pure rename with no content change (beside it, the
  one deleted line in `CONTEXT_PPM.md` when a move removed a picked line). A file that needs
  no correction does not get one added for symmetry.

**Move first, then edit.** `git mv` stages the rename against the file's **old committed content**, so
an edit made *before* the move is staged nowhere and is dropped from the commit silently. Move the
file, then edit it at its new path. This trap fires whenever one file is both moved and edited — which
is exactly the shape of a correction above, so it is a live hazard here rather than a theoretical one.

## Ensure the destination exists

```bash
mkdir -p "<destination>"
```

`trail/`, `drop/`, `unpicked/` and `parked/` are `[create]` directory stubs in the manifest
(`<CORE>/doctrine/setup/kensaiapp_structure.md` §1 for the instance seedbed, §2 for a project's);
create the one you need if setup has not yet.

**`trail/` and `drop/` are two bins, not one with a note in it.** A seed reaches `trail/` by ripening
into work — walked to the end, or, at instance level, cut into the seeds that will walk it — and
`drop/` by being killed. `nemawashi-drop` performs the second move, and never takes the first's case. The distinction is the folder, because a commit body is not where a reader looks while walking.

## The commit

`<CORE>/doctrine/governance/commit_via_builder.md` owns the builder's mechanics — read it rather than working
from a sketch. What is specific to a journey move:

- **`Product` where the owner directed the move.** A journey move is often made on the owner's word
  rather than out of a seat's own judgment, and that is what the `Role:` then carries. Which of
  `--actor` and `--role` carries it is `commit_via_builder.md` § *The variables the caller supplies*
  item 2, and is not restated here.
- **Declare every move with `--staged`, naming both halves.** A `git mv` is in the index the moment you
  run it, so it needs no `--add` — but the staged-set guard refuses any commit whose staged set is not
  declared, and a rename is read as its two halves. A directory prefix covering them is permitted, but
  **name the halves**: a prefix also silently covers whatever *another session* happened to stage under
  it, which is the contamination the guard exists to prevent.
- **`--add` only when you actually edited.** A file corrected after its move rides `--add` as well —
  `--staged` declares the rename's paths, `--add` stages the content change on top of it. A pure move
  needs no `--add` at all, and adding one "for safety" stages nothing and says something false about what
  the commit contains.
- **Pass no `--skill` on the move commit.** Nothing a *move* commits is a produced artifact: the seed
  or station was authored elsewhere and this commit is bookkeeping. What the absence of a
  `Skill-Version:` line positively means is
  `<CORE>/doctrine/governance/commit_format.md` § `Skill-Version:` trailer.

  **A skill that also writes a file of its own stamps that commit normally**, with `--skill <name>`,
  and `--prompt <name>` where a prompt produced the file. This rule is about the move, not about every
  commit a moving skill makes, and reading it wider makes a produced artifact claim no skill authored
  it — which is the one thing the absent trailer positively asserts. A skill whose only commit is the
  move never hits this. `shukuba-open` stamps the station it writes while its take-up of a parked one stays a bare move — the
  way `shukuba-refine` and `seeds-from-idea` stamp the files they land in a seed folder.
- **`--directional` follows the scope of what moved**, per
  `<CORE>/doctrine/governance/commit_format.md` § Directional trailer. **Project-level** →
  `Shukuba: <YYYY-MM-DD>_<slug>` when a station is open, else `Agari: <project>` resolved against its `agari.md` —
  never `Shukuba: none`, which doctrine retired. **Instance-level** → `Michi: <way-slug>`. A project
  move never carries `Michi:`, and an instance move never carries `Shukuba:`/`Agari:`.
- **The reading follows the move, not the referent.** A move that **completes** something reads
  `progress:` (or `serves:` under `Michi:`). A move that **sets something down** reads `aside:` — parking
  is not advancing, and a directional claiming progress for a move that stopped work is the same
  overstatement as filing an unfinished thing in a `trail/`. A move that **takes something up again** —
  a parked station back to the root — reads `progress:`: the walk resumes toward the station, which is
  what `commit_format.md` § Directional trailer means by it.

**Then eyeball `git show --stat`.** It must show one rename per move, with content changes only where
you deliberately made one — a corrected currency marker, or the one deleted line in
`system/contexts/CONTEXT_PPM.md` when the move removed a picked line. A rename reading `0 insertions(+), 0 deletions(-)` when you know you edited
something means the edit did not land — see *Move first, then edit*. The inverse — content where you
edited nothing — means something was touched that should not have been.

## After the move, say which pointers it broke

**A move renames a file that other seeds cite by path**, and a seed's path spells its position, so a
pick, an un-pick, a retire, a park or a take-up breaks every pointer aimed at where the file used to be. Nothing
in the move updates them.

**So after the move lands, run it and report what it names:**

```bash
python3 "<CORE>/tools/check_journey_links.py" --repo "<instance root>"
```

Anything it lists is a seed, a station, a finding in `docs/findings/` or a product document — in the
product's own repository when its path is absolute — naming a file that is not there. **Repair what it names** —
the rule, and why a citation by project · kind · name would not have broken in the first place, are
`<CORE>/doctrine/governance/found_while_walking.md` § *A broken journey pointer is repaired, and the
triple is what stops it breaking*, and this file states no second copy of them.

**What form the repair takes.** Either — a path repaired to where the file now sits is a repair, and
so is the triple, which the checker resolves. Prefer the triple: it is the last time that pointer
needs touching. What is not permitted is leaving it, and what the doctrine above forbids is writing a
form nothing can resolve.

**What is this file's own is that the check never gates the move.** A retire that refuses because
some other seed points at the wrong folder is stricter than the journey wants. The exit code is
information for you to pass on — `1` means it found some — never a gate on the move you were asked to
make.

**After, not before.** The pointers that break are the ones aimed at the file you just moved, so a run
beforehand reports the state nobody is about to change.

## Don't bloat the journey

Journey artifacts — seeds and stations — are **working notes, not reports**. A move adds **nothing** to
them: no summary, no outcome section, no pointer list. If the move has something to say, the commit
body says it.

This is load-bearing, not style: the journey is read *while walking it*, in the moment someone needs to
know what "reached" means here, or what an idea's remaining route is — and an artifact that has grown
into a report buries the one thing a reader opened it for. Length costs the artifact its function.
(Source case: a Findings entry written at 62 lines was cut to 25 with nothing lost.) The rule is *why*,
not a line count — hold it in cases it does not name.

## Ask, don't guess

The moves are cheap to make and expensive to make wrongly: a file in the wrong sibling folder misstates
the journey's own history, and a later reader has no way to tell that it does. When the target does not
resolve to exactly one file, or when the destination turns on a judgement the invocation did not settle,
**stop and name the candidates** — never a guess and never a silent default. Neither case can continue,
so neither makes the move.

**Who reads that stop is the run's, not the skill's.** Several of these skills run unattended — from a
launcher or a delegate, with nobody in the room — and there the stop is the report the caller reads.
In a session with the owner present, the same stop is a question.
