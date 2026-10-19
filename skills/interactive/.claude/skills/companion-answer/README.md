# companion-answer

Several skills in this instance author a document without stopping to interview the owner, and park what
they could not settle in a `*_open_issues.md` companion beside it. The loop that closes those questions
has always had a hole in the middle: the authoring half is a skill, the folding half is a skill, and the
part where a person actually answers is a text editor. The owner's workaround was to ask a session *"go
over this file with me, one at a time, plainly"* — and composing that ask each time is what this skill
replaces.

It exists as one skill rather than one per document because **it is general by construction**. It carries
no list of producing skills, documents or companion paths: every fact it needs is read off the companion
in front of it — which document, which skill re-runs it, which sections exist, which slots the owner
fills. A list would be a copy of a set that already moves, and a new producing skill would be invisible
to this one from the day it landed. If a future edit adds a skill name here, that is the defect.

## What It Does

- **Finds the live companion** — two filters, neither a list. It globs `*_open_issues.md` one level deep
  in the document homes (the instance's own document folders, the project cards, each product's `docs/`),
  then checks each candidate's own header pointer: a live companion sits where it says its document is,
  and one that does not is a copy (an archived round, an extracted tree, a fixture) whose answers nothing
  would ever fold in.
- **Reads the header for the run's four facts** — the document, the skill that re-runs it, the slot
  labels the owner fills, and the trail promise (which is the producing skill's to keep, not this one's).
- **Selects the items that are the owner's** — those carrying an owner slot still at its placeholder.
  Filled slots are answers already given; items with no owner slot belong to another actor and are
  reported, not written.
- **Walks them one at a time**, in plain language, with the item's own context compressed and the skill's
  own opinion offered where it has grounds for one — and writes each answer into its slot as it goes.
- **Opens a companion on another document** when an item turns out to belong there — on the owner's word,
  from that document's own template, carrying the one item and where it came from. A settled document has
  no other channel: with nothing beside it, its producing skill re-runs and finds nothing to act on. The
  file is committed and checked *before* the walked item is answered, because that answer says the change
  is carried elsewhere and the producing skill folds it and drops the item.
- **Commits the companion** through the shared builder, in whichever repo the companion lives in, so the
  answers cannot be stranded by the producing run that later removes the file.
- **Names the launcher that re-runs the producing skill**, derived rather than assumed — then stops. It
  spawns nothing and runs nothing.

## File Structure

```
companion-answer/
├── SKILL.md                # the skill: purpose, the generality rule, the five-step workflow
├── README.md               # this file
└── evals/
    ├── evals.json          # behaviour eval cases, run by skill-evals
    └── inputs/             # fixture trees, one per shape the skill has to handle
        ├── README.md       # what each tree is for — annotations live here, never in a fixture
        ├── harbourlight/   # one live companion, one copy of it, one non-owner section
        ├── northgate/      # a settled document: no live companion, one archived round
        ├── ledgerworks/    # a live companion whose header names no skill to re-run
        └── twinfields/     # two live companions in one directory
```

## Depends On

Nothing it invokes. It reads two shared files on demand:

- `<CORE>/doctrine/governance/commit_via_builder.md` — the commit recipe (flag forms, the staged-set guard).
- `<CORE>/doctrine/governance/commit_format.md` — which directional trailer a commit takes, by scope.

## When to Use

When the owner wants to work through a document's open questions with a session rather than by editing
the file: "go over the open issues", "walk the companion", "answer the questions that run left open",
"what's still open on this document". Also when they name the document rather than the file — finding the
companion is the skill's first step, not a precondition.

Not for authoring or revising the document (its producing skill's job), not for deleting a companion or
creating the one being walked (both the producing skill's — a companion's absence is its document's done
signal), and not for running the producing skill afterwards, which is the owner's own move. Opening a
companion on a *different* document is the one thing it does create, and only when an item it is walking
belongs there.
