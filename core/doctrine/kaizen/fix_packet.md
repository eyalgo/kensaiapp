---
version: "1.5.0"
---

# The fix packet

Standing rules for the document that carries a decided fix from the author who wrote it to the fixer
who applies it. The author (`kaizen-fix-author`) emits one; the fixer (`kaizen-fixer`) executes it.
Both read this file — a handoff format only one side owns is a convention, not a contract.

The shape to stamp is `<CORE>/templates/fix_packet_template.md`. This says what the fields mean and
when the packet is fit to act on.

## The reader you are writing for

**The fixer has the packet and nothing else.** It has not read the audit, does not know which finding
an entry answers, and is not the party that should be deciding. Every field below exists so the fixer
can act without judgment — because the moment it has to interpret, the deciding has moved back onto
the tier this document exists to spare it.

That is the test for the whole packet: **could a reader who has never seen the audit apply this?** Not
*is it correct* — correctness was settled before the packet was written.

## The verdict comes first

A packet opens with `fix` or `rebuild`, and the second one is a real answer. `skills.md` § *A fix
subtracts or trades* names the conditions under which the correct move is to stop patching and rebuild
from the harvested principles. A packet that never asks did not decide; it assumed.

**On `rebuild` the packet carries the case and no entries at all.** No fixer is spawned. The verdict
is the deliverable, and what follows from it is the owner's to authorize.

## State — the gate, made mechanical

```
State: awaiting-owner | approved
```

A packet is written, then adjudicated, then applied, and the middle step is a person. **The fixer
refuses to act on any packet not marked `approved`** — not as a courtesy check, but because entries
can rest on a call the owner has not yet made, and an unapproved packet is a draft that happens to be
executable.

Only the owner moves it to `approved`.

## The owner answers in their own file

The owner's answers live in **`owner_answers.md`**, beside the packet in the round's evidence folder,
stamped from `<CORE>/templates/owner_answers_template.md`. It carries their adjudication calls, any
broader ruling they are setting, and the per-entry dispositions those imply.

**It is theirs; the author never writes it, and they never write the packet.** A packet the owner edits
is a record two hands wrote, and neither half stays attributable. Keeping them apart means the settled
packet traces to both, separately — the question in the author's words, the answer in the owner's.

## Settling — folding the answers back in

An answer usually changes the packet: an entry conditional on the call now applies or is withdrawn,
the projection moves, the tallies move. That is deciding work, so it belongs to the **author** — not
the fixer, which applies verbatim, and not whatever session happens to be open.

So the author runs a second time, over the packet and the answers together, and:

- **Applies what each answer implies** — a conditional entry becomes unconditional or goes; an entry a
  ruling withdraws leaves `## Entries`.
- **Moves a withdrawn entry to `## Out of scope`, with the reason. Never deletes it.** A later audit
  has no memory of the ruling and will raise the finding again; the recorded rejection is the only
  thing that meets it.
- **Recomputes the projection and the entry tallies from the surviving entries** — derived afresh, not
  decremented, because a decrement inherits whatever the first count got wrong.
- **Changes nothing else.** It does not re-decide what the owner did not raise, does not re-open
  settled entries, and does not touch `State` — settling is not approving, and the owner reads the
  settled packet before they approve it.

## Entries

One per edit. Each carries:

- **File** — which layer. The stack is more than the `SKILL.md`; `lenses/contract.md`
  § Classification owns that list, and naming one is yours: `lenses/locate_layer.md` is the
  method — the layer justified against its own text at the producing version, with a quote, never
  defaulted to the skill. For a producer skill with an authoring prompt, a content-doctrine entry whose `File:` is the
  `SKILL.md` must quote the orchestration text it fixes; an entry about what the artifact asserts lands
  in the prompt.
- **Anchor** — the exact current text being replaced, quoted, long enough to be unique in the file. A
  line number alone is not an anchor: the file shifts as earlier entries land. If the anchor is
  ambiguous, the entry is not ready.
- **Replacement** — the final prose, verbatim, as it will read in the file. Not an instruction, not a
  summary of intent. *"Tighten the locator rule"* is not a replacement; the sentences are.
- **Subtracts or trades** — the rule this removes or supersedes. **Required.** § *A fix subtracts or
  trades* makes a new rule name the rule it replaces; if it cannot, that is the tell the skill has
  become a changelog of its own history — so *"nothing; this can only add"* is a legitimate value and
  is itself a finding to report, never a field to leave blank.

**Order them when they interact.** Two entries against the same passage, or one whose anchor only
exists after another has landed, are applied in the order given. Say so; do not leave it to be
discovered.

**Mark the conditional ones.** An entry that depends on an adjudication carries what it depends on and
is un-appliable until that call resolves. A conditional entry in an `approved` packet whose condition
never got answered is a defect in the packet.

## When the packet does not fit the file

**Stop and report. Never infer where the text was meant to go.** Three things end the run:

- an anchor does not match its file exactly;
- an entry is conditional on an adjudication nobody answered;
- applying one entry leaves a later entry's anchor unresolvable.

Each says the same thing — the packet was written against a version the files have since moved past.
And the fixer is the one party in the loop that cannot tell a passage that moved from one that was
mistyped, because it has not read the audit; that blindness is the point of handing it a packet at all.
So the inference it would have to make here is exactly the one it exists not to make. A wrong guess is
not a failed run: it is the right words in the wrong passage, committed, and in a `--bg` run there is
nobody to catch it.

**Report means: which entries landed, which one stopped you, and what you found in place of the
anchor.** Leave what already applied in place and commit it. A half-applied packet whose stopping point
is on the record can be resumed; one that unwound itself leaves nothing to resume from.

## Name what is out of scope

Findings that were declined, findings the audit classified as being about the artifact rather than the
instrument, adjudications deferred to the owner — **list them, with the reason.** The fixer needs to
know what it is *not* being asked to do; absent that, an unlisted finding reads as an oversight and
invites exactly the improvisation the packet exists to prevent.

**Read this section in the packets already in the skill's evidence vault before you draft.** An audit
has no memory of what the owner ruled on a previous round, so a finding that was raised and rejected
will be raised again — and drafting it a second time is the failure this record exists to prevent. A
ruling recorded here binds until the owner changes it.

## The bump, and the projection

The packet names the version it moves from and to, and **projects the net line change**. The fixer
checks its own work against that number.

This is not bookkeeping. § *A fix subtracts or trades* names growth-without-subtraction as the shape
that rots a skill, so a batch's direction is a fact worth predicting and then checking. An author who
mispredicts its own diff did not understand its own edits.

## Committing the round

**The commit is specified here because nothing else specifies it.** The fixer's task prompt names a
packet and nothing more, and the packet is a list of edits — so a fixer that reaches the commit
uninstructed improvises one, and an improvised commit fails the `commit-msg` hook for missing
trailers. In a `--bg` run there is nobody to answer that, so it does not fail: it stops.

**One commit per repo the entries name** — not one for the round. A role runs in more than one
instance and each instance carries its own loader, so a packet that fixes a role fixes that loader in
every copy, and its entries land in more than one repo. Group the entries by the repo their `File:`
resolves to and commit each group separately. Two independent per-repo commits, never one commit
reaching across a boundary: staging a path outside its own repo does not produce a wide commit, it
fails.

Every commit goes through `<CORE>/tools/commit_builder.py`. Never a hand-written `git commit`, never
a spelled-out trailer block, and never `cd` into a repo to stage — pass the paths and the builder
stages them with `git -C`. What the packet supplies:

- **`--repo`** — the root of the repo that group belongs to.
- **`--add`** — that group's files, and only those.
- **`--actor kaizen-fixer`** — the builder derives `Role:` from it. Never state a `Role:` yourself.
- **`--directional`** — `Shukuba: kaizen-<skill> — progress: <what this round fixed>`. Take the
  skill and the version move from the packet's own heading rather than guessing them. **The same
  directional on every commit of the round** — that is what makes several commits read as one move
  rather than as unrelated work that happened the same afternoon.
- **`--subject` / `--body`** — what this repo's share fixed, and what each of its entries subtracted
  or traded. The subject differs per repo; the directional does not.
- **`--surface`** and **`--co-authored-by`** — the surface you ran on, and your OWN running model as
  a display name read from your runtime, never a model token copied from an example.

`<CORE>/doctrine/governance/commit_format.md` owns what the trailers mean; take nothing else about
them from here.

**Bump nothing the packet did not tell you to.** A version bump is an entry like any other — decided
by the author, anchored, and counted in the projection. One the fixer makes on its own initiative is
a change nobody decided.
