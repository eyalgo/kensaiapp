---
version: "2.2.0"
---

# Kaizen — hardening a skill

A skill is built and checked once. A one-pass check is not the bar: it proves the skill runs, not
that it is good. Kaizen is how a skill earns its quality — exercise it against a **real case**,
audit what it produced, improve the **skill**, run it again. Round after round, until the owner is
satisfied.

**The skill is the product; the case is the instrument.** The artifact a round produces is
*evidence* that the skill works, never the deliverable. Getting this backwards is not a framing
error — it is the failure mode. If the goal is a good artifact, then writing the case's own answers
into the skill is the rational move: it is the fastest path to a good next artifact. The skill
becomes a cache of answers about one case, and stops being able to serve any other.

Human-in-the-middle. Not an automated workflow: the owner runs it, round by round.

## The loop

**The three steps that do the work are each named by what they read.** 2 reads the **skill** — and
fixes what it finds. 3 **runs** the skill against the case. 4 reads the **output** — the artifact the
run produced — and decides the fix. 5 applies it.

1. **Set up the skill and the files it's built from, its evals, and a baseline eval run** — building
   or skipping whichever already holds. A skill is not one file: it's a **stack** — the skill plus the
   related files it draws on (its authoring prompt, its templates, its `stack.json` manifest). The
   baseline is that whole stack **in the shape the loop needs**, not merely the skill file existing —
   so where the same content would sit in two of those files, step 1 is where it's settled into one
   home. Then step 2 cold-reads the stack, file by file. The loop names what must **exist** to enter
   it, not how the stack was made (an authoring tool, another skill, or by hand — out of scope). Also
   the loop's **escape hatch**: see *A fix subtracts or trades*.
2. **Cold-read the skill** — the skill file, and only it — in **four moves the owner drives**: a blind
   reader per substance file, each committing its report; then the fixes worked with the owner, finding
   by finding. There is no move that re-reads: the re-read is this step in the **next** round, which is
   why nothing here has to be remembered. The rest of the stack is read at 4. *Running the cold-read*
   owns how it runs, and why the re-read sits there rather than at the end of this step.
3. **Run** the skill against the case. If it surfaces work to the owner, the round is not over when
   the run ends — it ends when the owner has answered and the skill has folded those answers in.
   What it finally settles on is the evidence.
4. **Audit that evidence — and decide the fix.** The audit reads **only the outputs** — this
   round's evidence and the prior round's, never the producing stack. First a blind fan-out, one
   lens per auditor, none of them given the skill: the content comes first — the artifact is read
   adversarially, as something a reader will act on (a tool it names that does not exist or is
   used wrongly, a setup that would not work, a needed thing it never names — content defects,
   whatever skill produced it). Then synthesis: the two non-blind comparisons against the previous
   version — what the artifact **says**, and what the skill **chose to ask**. Then the deciding:
   the `kaizen-fix-author` reads those findings **and the producing stack** — the one hand at 4
   that reads it — and directs each fix to the layer that needs it (the layers are
   `lenses/contract.md` § Classification's; `lenses/locate_layer.md` owns the method — the layer
   named against its own text, at the producing version, with a quote). A leak into a shared layer
   travels further than one into the skill. The fix is written — **the deciding, not the
   applying** — into a fix packet the owner approves before 5 (`fix_packet.md` § State owns the
   gate). Findings that are about the case rather than the skill are recorded, not fixed. **All of
   4 runs in the audit instance** — the judging side that remembers every round; its own charter
   owns why it is separate.
5. **Apply the approved fix** and **bump the version**. The `kaizen-fixer`, in the **dev instance**,
   lands each entry in the layer its packet names. It runs in dev because that is where the skill
   lives — from the audit instance it is only a symlink — so the packet crosses the boundary as a
   committed file, `--add-dir`'d in. That boundary, plus the owner gate, is why the fix here is a
   committed packet where step 2's cold-read fix passes in-memory.
6. **Delete the round's results** — the artifact and everything the run wrote into the case. Not the
   evidence snapshot: that is the record.
7. **Back to 2.**

Snapshot the evidence before 6 deletes it, per `../engineering/skill_evidence.md`.

## Why cold-read before the run — and cold-read + evals after every fix

**The audit at 4 only ever sees what reached the artifact.** The fix-author reads the skill, but
only to place a fix for a defect the artifact already revealed — nothing at 4 goes looking for
defects in the skill's text.
So a rule that contradicts another and never fires, a path that does not resolve, an instruction
nobody could act on: none of them reach an artifact, none of them become findings, and all of them
survive any number of rounds unseen.

A cold-read is one agent reading one file. A round is a run, plus the owner's time answering, plus
a fan-out of auditors. **Never spend a round on text nobody has read.**

**Evals are the cold-read's regression twin — run them after every fix too.** The cold-read guards
*coherence* (a contradiction, a dead path — text wrong on its face); the evals guard *regression*
(behavior the skill used to get right that a fix quietly broke). Neither sees the other's failure — a
never-fired contradiction produces no output for an eval to catch, and a regression can hide behind
text that reads clean. So a fix — a cold-read fix (step 2) or an audit fix (step 5) — is followed by
**both**: a cold-read and an eval run against step 1's baseline. A red eval is a finding, not a pass.

Step 7 returns to 2, not to 3, because **the fix — authored at 4 — is the most dangerous text in the
loop.** It is written in a hurry, aimed at one finding, with that finding's vocabulary sitting in the
author's head — which is exactly how a case's specifics get written into a general skill, one worked example
at a time, each looking reasonable alone. A fix also routinely introduces the next round's break.
The original draft gets read carefully; the fix is what sneaks past.

## Authoring the eval set — and the two paths a kensaiapp skill is graded on

The loop above says *when* evals run. This says who writes them and what a case set here has to
cover. Route eval authoring here, not through `setup/authoring_layers.md` — that file does not
mention evals, and a run that lands there stops looking rather than reporting an empty return.

**Authoring goes through the `skill-evals-creator` skill, invoked rather than imitated.** It owns the
`evals.json` schema, the assertion tiers and the precision rules, and none of that is repeated here —
a copy of a schema is the copy `../governance/single_source.md` deletes. What this file owns is that
the eval set is part of the loop rather than a side artifact, and the coverage floor below.

**Two paths that skill-evals-creator cannot know to ask for, because both are kensaiapp conventions
rather than eval conventions:**

- **The posture halt.** A kensaiapp skill that gates on a role refuses to run outside it. That refusal
  is behaviour, it is the cheapest thing for a fix to break silently, and it produces no output file —
  so a case set that never invokes the skill from the wrong posture has left the gate untested.
- **The path where success is an absence.** Several skills here are correct precisely when they write
  nothing: a companion removed because nothing is unresolved, a run that finds no change to make. An
  assertion that only checks for a produced file grades those backwards, and an empty output tree
  passes every case at once.

**An absence is never asserted alone.** Pair it with something positive the run must also have done —
the reasoning it recorded, the item it routed elsewhere, the companion it left behind. Alone, "no file
was written" is satisfied by a run that did nothing, crashed, or was never invoked, and the case that
was supposed to protect the skill's whole point is the one case that cannot fail.

Where a skill's success path is an absence and nothing positive accompanies it, that is worth saying
out loud rather than asserting around: a behaviour with no observable trace is one no eval can defend,
and the finding belongs to the skill's design, not to its eval set.

## Why every round starts clean

Step 6 deletes the case's artifacts so the next round begins from the same place the last one did:
the same inputs, nothing inherited from the last round, a different skill version. **That is the
experimental control.** With the first two held constant, every difference in what the skill
produces is attributable to the skill. Without it, a round measures skill-plus-history and nothing
can be attributed to anything.

**The skill version is held constant *within* a round, not only between them.** A round measures one
version against the case; a bump that lands **mid-round** — after the run has started, before the
round's evidence settles — breaks that control exactly as inherited state would. The round then spans
two versions and can attribute nothing to either. A bump that changes **artifact-bearing semantics**
does worse than blur attribution: it strands the settled artifact on the model the old version
implemented while the shipped skill now says something else, so a cold reader is told one thing by the
artifact and the opposite by its own producing skill. So **do not bump a skill while a round of it is
open.** A semantics fix waits for the round to close; if it genuinely cannot wait, the open round is
discarded, not straddled.

**And when a round goes inconsistent — the artifact stranded on removed semantics, or any state the
run cannot cleanly resolve — stop.** Discard the contaminated round (step 6 deletes its artifacts
anyway), fix the skill clean, and re-run from the same inputs. That is the escape hatch and the
human-in-the-middle this loop already has, not a new mechanism: a contaminated round is not evidence,
and auditing-then-fixing on it lands the fix on the wrong version. Stopping is the cheap, correct move,
not a failure of the round.

The delete clears the case, not the repo's history — which survives it by design. So the clean start
is a precondition the skill honours, never something the delete can enforce: tell the run its input
is what's on disk, at the point you start it.

It also removes the skill's excuses. A skill that inherits its own prior output can appear to
remember a decision it never re-derived; a skill that starts clean must earn every line again,
every round. If it silently changes something the owner settled last round, that is not the
protocol's fault for forgetting — it is the skill failing to surface a call it had no basis to
make.

Nothing the skill does for real users is on trial here. A skill may legitimately carry state
forward in production; kaizen still wipes it, because kaizen is measuring the skill and not
enjoying its features.

## The version's three digits

**The digits are `../governance/versioning.md` § *Bump semantics*' digits, not a second set.** That
file excludes skills from *whether* a marker is carried and *when* it moves — those are this layer's
— but the three digits are one set across every artifact, which it says itself. Read them there; what
follows is only what they read **against** for a skill.

| Digit | For a skill |
|---|---|
| **patch** | wording, a pointer, an example — nothing a run's behaviour turns on |
| **minor** | a step, a refusal, a gate, or an output shape added or changed |
| **major** | a rewrite, or a mandated rule removed or inverted |

The line that decides between patch and minor is **whether a run could come out differently**. A
refusal that keeps refusing but for a different stated reason is a minor: the reason is what the
skill hands its caller, so a caller reading it is told something new. Rewording the same reason is a
patch.

**A `description` is the one edit that line cannot read, so it reads against a second one.** The
frontmatter `description` is a **trigger surface**: no run reads it, a dispatcher does, to decide
whether to invoke the skill at all. So the question above is asked of a run that has already
started, and it answers *patch* for every description edit — including one that changes which
requests reach the skill in the first place. Read a description edit against **what it changes about
being chosen**:

| Digit | For a `description` |
|---|---|
| **patch** | the same requests still route here, said better — a rewording, a clearer example, a typo |
| **minor** | the set of requests that route here **moves** — a trigger phrase added or removed, a *do not use for* fence added or dropped, the stated scope widened or narrowed. A caller that would not have invoked this skill now does, or the reverse |
| **major** | unreachable by a description edit alone: major is a mandated rule removed or inverted, and a description mandates nothing |

**The test is the set, not the sentence.** Renaming an artifact the description already mentions —
a skill named inside a *do not use for* fence, say — changes the words and not the set: the same
requests are still fenced out, and only the name of where they go instead is corrected. That is a
**patch**. The fence being added, or removed, or made to cover a different kind of request, is the
**minor**.

This is a second reading of the same three digits, not a fourth digit and not a row in the table
above — those rows all read against the run, so a fourth would inherit the same blind spot. Two runs
raised this independently before it was written down, and both had to decide it by hand.

**Who makes the bump.** Inside a round, the fix packet and nothing else — `fix_packet.md` § *The
bump, and the projection*: the packet names the version it moves from and to, the author decides it,
and the fixer bumps nothing the packet did not name. Outside a round — an ordinary edit to a skill,
with no round open and no packet — the commit that lands the edit carries it, exactly as every other
versioned artifact works.

**Two things this section does not own.** *When* a bump may land is § *Why every round starts clean*
above: never mid-round, because the round measures one version. And a version is **bookkeeping, not a
quality claim** — § *Ratify* below owns that, and an unratified skill owes improvement no matter how
high its version.

## A fix subtracts or trades

Authoring the fix — step 4 — is where a skill rots. Each round names a defect; the natural fix appends a rule about it;
nothing ever removes one. Rules accumulate faster than principles are found, and the same principle
ends up restated once per instance that provoked it — which is why a skill can pass every fix on
target while its defect count rises. An instance-shaped rule only fires on the case it was written
for; the next defect arrives in a shape nobody catalogued.

So: **a new rule names the rule it replaces.** If it cannot — if it can only be added — that is the
tell that the skill has stopped being a specification and become a changelog of its own history.

That is the trigger for **1**, the escape hatch: stop fixing. **Harvest the principles out of the
audits** — they are the asset; they hold the reasoning each round bought, and they hold it in the
right place, keyed to the version that earned it. Rebuild the skill from those. The rounds are not
wasted; only the prose is.

**And then diff the rebuild against the skill you are replacing** — this is not optional, it is what
makes the harvest safe. **The audits only record what failed.** A rule that was quietly working never
produced a finding, so it is nowhere in the evidence, so a harvest cannot see it and the rebuild drops
it silently. The rebuild loses precisely the rules that were doing their job — and it loses them
without a trace, because nothing in the audits will miss them. So walk the old skill rule by rule and
account for each one: harvested, deliberately dropped, or **missed**. The third pile is the reason for
the walk.

Anything you keep this way, keep as a principle, not as the sentence you found. A rule that survived
because it worked is still an instance if it was written as one.

Other signals for the same move: the skill grows every version and never shrinks; a fix lands on its
target and the round still fails; a rule's worked examples are drawn from one case.

**A check that keeps needing another case is not incomplete — it is inferring.** When round after
round widens the same guard with one more state it failed to cover, the rounds are not converging on a
complete list; there is no complete list. The guard is reconstructing, from what it can see, a fact
that something else already knows for certain. The next case is not the fix. Get the fact from a
**record** — have the step that knows it write down what it actually did — or change the operation so
it **does not care**, which is the better answer when it is available: a computation that cannot be
wrong-footed needs no guard in front of it. A rule that stops needing the check beats a check that
finally covers everything, because the second one never arrives.

## The shape that cannot see an absence

A good rule reads as *a question you can fail, applied to a thing you are about to write*. That shape
is why principles beat instances — it fires on any sentence, not just the one that provoked it. It is
also, exactly and unavoidably, **blind to the thing that was never written.**

Nothing about a sentence tells you a different sentence should have been there too. So a rule set made
entirely of this shape produces an artifact with nothing wrong in it and something missing from it —
and every reader will sign it off, because reviewing means reading what is on the page.

**Both halves of the loop share the bias, which is what makes it survive.** The audits read the
artifact, so they only ever find what is present and wrong; the harvest reads the audits, so it only
ever rebuilds present-and-wrong rules; and the next audit reads the next artifact. Nothing in that
circuit is looking at the gap. This is the mechanism behind the harvest's blind spot above — the rules
that vanish silently are disproportionately the ones that required something to *be there*.

So: **a skill needs at least one check that is read against the finished artifact and asks what is not
in it** — and a lens set needs at least one lens that does the same, or the audit will not catch what
the skill missed. Those checks look different from the others, and should: they are not tests you
apply while writing, they are a pass you make when you think you are done.

When you rebuild, count the shapes. If every rule in the new skill is a test-on-a-sentence, the
rebuild has quietly dropped a category, and the diff above will show you which.


## The shape that cannot see a rule that should not be there

The section above is one half of a pair, and this is the other. There, the loop cannot see what was
never written. Here, it cannot see what was written and should never have been.

A reader asks whether the rule in front of it is correct — and a rule can be correct, well-argued, and
still answer a question the skill never had to ask. Nothing on the page says so. The audits will not
find it, because it is not wrong. The harvest will not drop it, because the audits never flagged it —
and a rebuild harvests from the file it is rebuilding, so a rule an earlier round invented returns
promoted to a principle. It survives every pass the loop has, and it survives them by being fine.

Both halves have one cause: **every read in the loop has the same referent — the artifact in front of
it.** A rule set cannot be judged complete or necessary from the inside, and the loop has no outside.

So give it one. Where a **ratified sibling** exists — a skill doing the same kind of work, beside this
one or upstream of it, that has already earned the owner's "ship it" — at least one read puts the two
side by side and asks, of every mechanic present here and absent there, why.
`lenses/compare_sibling.md` owns that read: what counts as a referent, when it runs, what it asks, and
why the sibling is read-only. The short version is that the answer is often good and
the difference earns it; when nobody can say why, the mechanic is a round's own invention that
outlived the round, and the fix is to delete it rather than refine it.

This is the one check whose cost falls as the instance grows: every skill the owner ratifies becomes a
referent the next one gets for free.


## Hardening a chain of skills

Where skills form a chain — each one's output is the next one's input — the loop above still runs per
skill, but **the order is not free: harden upstream first, and never audit a downstream artifact
built on an un-ratified upstream.**

The reason is the control again. A round measures the skill by what it produced; if what it consumed
came from a skill that is still moving, the round measures both and can attribute neither. Worse, the
downstream skill will be *correctly* faithful to a bad input, so its audit finds defects that are not
its own and the fix lands on the wrong skill.

So a downstream artifact built on an un-ratified upstream is not evidence — it is a draft that will
have to be thrown away, and the honest move is to throw it away rather than audit it. When an
upstream skill finally ratifies, **recreate** downstream from its output; do not patch what was built
on the old one.

This is what makes a chain expensive to harden and worth sequencing deliberately: the first skill's
rounds gate everything behind it.

## Ratify

**Ratify is the owner's "ship it."** Not an auditor-clean gate. The auditors advise — they surface
what the owner should see before deciding, and they do not hold the door.

This matters because an auditor-clean gate is not reachable. A blind fan-out over a substantial
document always finds something, and a loop that only ends when the finders go quiet does not end.
Requiring both the owner's judgment **and** a clean fan-out is the shape to avoid: it reads as
rigour and behaves as a trap.

Never self-ratify on a clean pass — and never on **maturity**. A version is bookkeeping, keyed to
the round that produced the evidence; it is not a verdict on quality. A skill is unratified until the
owner says "ship it," and an unratified skill still owes improvement **no matter how high its
version**. So an auditor never treats maturity — a high version in the frontmatter, a polished read, a
long fix history — as grounds to grade a defect down or to stop looking. The version records what
produced the text; it says nothing about whether the text is done.

**What the owner's "ship it" then costs is `ratification.md`** — the preconditions a verdict rests
on, where the verdict lives, the three places a ratification is recorded (the vault freeze, the
skill's README, the round's close), and the rule that a later bump ends the claim. This section owns
the meaning; that file owns the act.

## Running the cold-read

**Four moves, and the owner drives them.** There is no automated loop inside step 2 — the
human-in-the-middle this file opens with applies here exactly as it applies everywhere else.

1. **Read.** One blind `kensaiapp-auditor` per substance file, carrying the `cold_read` lens, given
   its file and nothing else. Where the stack has more than one substance file, one further reader is
   given the whole set and asked only what lies **between** the files.
2. **Commit the reports.** Each reader commits its own, before anything is decided about it. Hand a
   reader a path to write to, never a caller to return prose to: a finding that exists only in a
   session dies with it, and the next round starts from nothing.
3. **Work the fixes with the owner** — finding by finding, the owner ruling each. *A fix subtracts or
   trades* binds these exactly as it binds step 4's. **Do not automate this move.** A hand aimed at one
   finding, with no budget and no view of what the file is for, finds adding a clause cheaper than
   subtracting one — every fix defensible alone and the set of them a violation, because nothing in
   the move sees the trajectory. Move 4 is what sees it.
4. **There is no fourth move.** The re-read is step 1 of the **next** round.

**Do not write the re-read as a fourth move.** A procedure that must be remembered to work is the
same defect as a rule that must be remembered to fire, and a fourth move reading *now read it again*
is prose wearing a number. It would be dropped the same way, and for a reason that
has nothing to do with diligence: **the move that gets dropped is the trailing one**, because nothing
downstream is waiting on it and its omission leaves no gap anyone trips over.

So the fix is not a mechanism to force the re-read. It is that **the re-read is not trailing.** It is
the head of the next round, holding the position every other step holds — with something behind it.
No next round, and nothing is owed: the reads are done, the fixes are landed, and there is no dangling
obligation to forget. A next round, and the read is the first thing that happens in it, before the
run and before the audit, with the whole round waiting on it. A step nobody can reach past is not a
step anyone has to remember.

**One reader, one file, the rest of the stack withheld.** A reader holding less subtracts; a reader
given the surrounding stack adds. Measured on this skill: one reader per pass over the skill file
alone cut it 478 → 365, and readers anchored to one file with the stack available grew it both times
it was tried — 363 → 405, then 405 → 550, every pass net-positive and none subtracting, which is
worse on the one axis *A fix subtracts or trades* makes a rule about. **Why** is not established and
is not asserted; only which way the evidence runs. The axis is the **window**, not the head count — several readers at once is fine, and is what
move 1 runs, so long as each holds one file.

Hand each reader its lens and its file, and — where earlier rounds fixed things — what they fixed;
the lens asks for exactly that, so it calibrates to what remains instead of re-litigating what is
gone. Say nothing else about what you expect it to find. Every sentence beyond those is a sentence
telling the reader what you suspect, and a reader who can tell what you want will find it.

The rest is **when**, and **what you must hand it**:

- **Every fix is followed by a cold-read**, and under the shape above that sentence needs no
  enforcement: the cold-read that follows a fix *is* the next round's move 1. That holds for a fix
  answering the cold-read and for the fix that answered the *audit* — step 7 returns to 2 before any
  round is spent, and 2 opens by reading. Different findings, and neither is trusted unread.
- **Hand it the skill, and only the skill.** Nothing else in the stack — that is read at 4, and every
  time a reader here was handed any of it the skill grew. The lens already allows this: it says to
  read the stack *when you are given it*, and here you are not. What counts as a layer — the list step
  4 works from — is the audit contract's, `lenses/contract.md` § Classification. It owns that fact,
  and a second list here would be a copy free to drift — an enumeration written out twice loses an
  entry on one side and nothing notices.
- **For a split stack, move 1 is one reader per substance file, plus the seam.** A producing stack
  that splits orchestration (the skill — structure) from authoring doctrine (a prompt — content) has
  two substance files. Each gets its own reader holding that file alone, per the evidence above;
  skipping the prompt's read turns it into exactly what this rule guards against, load-bearing text
  nobody reads. **They run at once, not in order** — ordering bought something only while a fix landed
  between reads, and no fix lands between these: every reader sees the same text whatever order they
  start in. What the split costs instead is the **seam**: a reader fenced to one file files as a
  defect what the counterpart file answers, which is why move 1 adds the reader whose only subject is
  what lies between them. `lenses/cold_read.md` owns what each of them does with a question its window
  cannot settle.
- **Templates are recommended supplements, never read subjects.** A template carries *shape*, not
  substance, so it is never cold-read on its own. When a read of a substance file surfaces a template
  shape problem (a section that should not exist, a missing slot, a comment that misleads or restates
  doctrine it should only point at), the fix is worked at move 3 like every other — reached from a
  substance read, riding in that round's commit, never a read of its own.

The wiring is `<CORE>/launchers/cold-read/launcher.sh <skill> --project <project>`, which reads the
skill's `.claude/skills/<skill>/stack.json` manifest and opens move 1's readers — one per substance
file, plus the seam reader when there is more than one — each committing its own report. It stops
there, and that is load-bearing rather than a scope note: **a launcher that grows a fix step is the
retired loop under a new name.** The launcher is a mechanism; the scope above is the principle, and a
single-file skill declares a one-entry manifest rather than falling out of the read.

Expect several rounds. The reads that find the most are usually not the first one over a fresh draft
— they are the ones over your fixes. And when the reads keep finding breaks round after round and each
fix buys the next one, stop: that is not a failed loop, it is **1**, the escape hatch, arriving on
time.

## Relationship to other docs

- `../engineering/skill_evidence.md` — where a round's evidence lives and how it is keyed (by producing version),
  and what a snapshot must hold. Kaizen is what produces it; that file owns the convention.
- The **`kensaiapp-auditor` agent** — what runs every job at step 4, and the cold-read at step 2.
  Which jobs those are is `lenses/README.md` § The set; a count kept here would drift the way a
  second layer list does. The agent is plumbing and owns none of this: `lenses/contract.md` and the
  file it is handed own how a read is looked for and reported. This file owns why, when, and the
  loop the cold-reads sit in.
- `evals/` (per skill) — synthetic fixtures and graded runs. A different **question** — evals ask
  whether a skill still does what it did; kaizen asks whether what it does is good enough yet — but
  not a separate process: the loop creates them at step 1, baselines them there, and re-runs them
  after every fix as the cold-read's regression twin (see *Why cold-read before the run…*). The eval
  set is owned per skill; the loop owns when it runs, and § *Authoring the eval set* owns who writes
  it and the two paths it must cover.
