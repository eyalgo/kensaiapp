---
version: "1.2.0"
---

# Written forward — a file states what is true now

Governs **every authored file in the instance**: doctrine, skills, prompts, templates, loaders,
agent files, READMEs, the journey. The one exception is the **commit message**, which is where the
story goes.

> **Owns:** whether a sentence about a file's own state, about what is built, or about a path not
> taken belongs in a file at all — and the form it takes when it stays. **Does not own:** whether a
> fact is duplicated across files (`single_source.md`), which of a carrier and its body holds a
> given sentence (`authoring_layers.md`), what a commit message must carry
> (`commit_format.md`), or which stations are built (`setting_up_a_project.md` § Which of these
> exist today).

The temporal instance of `single_source.md`. That file governs a fact copied **across files**; this
one governs a fact copied **across time** — the file and the moment that made it. Both fail
identically: accurate when written, false later, with no author and no moment, because the defect
lands in the file nobody changed.

---

## The rule

**A file states what is true now. The story of how it got here lives in git.**

### 1. A file does not narrate itself

Not its status, not its maturity, not how it was made, not what it will become.

```
**Status: stub.** Shape only. This file exists so the agent's load chain resolves — every
section below is TBD. It is step 1 of adding_a_role.md, and when it is written it is stamped
from the template.
```

Every clause there is addressed to the builder. The reader is not the builder: it is an agent that
has loaded this file in order to act, and there is nothing in the paragraph it can act on. The
build-order and the stamping source are `adding_a_role.md`'s to state, and it states them.

### 2. A file does not carry a build-state claim

*"not yet built"*, *"not yet wired"*, *"planned later"*, *"currently a stub"* — a claim that is
true on the day it is written and has nothing keeping it honest as the state changes. It outlives
the building every time, because the session that finishes the work is not reading the three files
that describe it as unfinished.

**Write against the finished world.** Name the capability and its real path in the present tense, as
though it exists. Where a build-state fact is genuinely needed, it has one owner —
`setting_up_a_project.md` § *Which of these exist today* — and other files point there rather than
carrying a parenthetical.

**The first of two carve-outs is an instruction, not a status.** A capability with no task, no plan and no
name anywhere may be fenced — but the sentence that stays is the one the reader acts on
(*"do not reach for a capability that isn't there"*), never the status note wrapped around it.

**The second carve-out is a product's what-left file, `<product>/docs/what_left.md`.** It is the one
place a product's "what is left to build" is stated, and every entry in it is a build-state claim by
design. It stays honest where a parenthetical status note does not. Every entry names the commit its
thing was missing at, and an entry leaves the file only once its thing has merged. The file's shape
and rules are `core/doctrine/setup/kensaiapp_structure.md` § 3 Product, *The what-left file — the one
place a product states what is still to build*.

### 3. Rationale is written forward

Reasoning stays. It changes form.

| | |
|---|---|
| **Story** — goes | *"Originally one file. On 2026-07-31 we split it because the loader kept drifting."* |
| **Constraint** — stays | *"Do not merge these two. Mechanics and authoring content change at different rates, so the fast side accretes into the slow side."* |

Same information. No date, no edit, no author — and the second one stops the next reader **before**
they start rather than after.

**A rejected path is the strongest case for this**, and it is written as a prohibition: not *"we
considered X and decided against it"* but **"Do not do X. X drifts, because Y."** A rejection told
as a story is the weakest possible defence of itself — it reads as a decision somebody once made,
which invites re-litigating; a rule reads as binding.

---

## The keep test

**Does the sentence change what the reader does this session?**

If yes it stays, whatever it is about. If no, it is narration however true it is. A sentence can be
accurate, well-written, and hard-won, and still be addressed to nobody in the room.

## The three moves

Narration is not deleted on sight. It is triaged.

| Move | When | Where it goes |
|---|---|---|
| **Delete** | The reader cannot act on it and nothing else needs it | Nowhere. `git log` already has it. |
| **Rewrite** | The information is live but told as a story | Stays in the file, in the present tense, as a constraint |
| **Relocate** | Genuinely archival, and worth finding again | The commit body (why this edit) or the journey seed / station (the decision and what it displaced) |

Reaching for **delete** first is the failure this table exists to prevent. Most narration is a live
constraint wearing the wrong tense.

---

## What this does not touch

- **Reasoning is not narration.** `authoring_layers.md` § *Why a teaching carrier fails harder than
  a copy elsewhere* is pure argument, in present tense, and it stays. A file may argue for its own
  rules at any length.
- **Evidence for a rule is not narration.** `single_source.md` § *What this looked like when we
  found it* recounts six real defects in past tense. Those describe **the system**, not the file
  they sit in — the distinction this whole page turns on is *self*-reference.
- **The journey is the record.** A seed's findings, a station's attempts, a trail entry, an audit
  report — these exist to hold what happened. Recording the work's history is their job; narrating
  their own maturity is not.

## The check

One checker, behind three callers, plus the judgement half a pattern cannot do.

`core/tools/written_forward.py` holds the phrase set and the scope — the single source `git commit`
and a Claude Code session both read, so the rule binds regardless of which one is writing:

- `core/githooks/pre-commit` — a git-native hook. Blocks the commit when the staged content is not
  clean.
- `.claude/hooks/` `PreToolUse` guard — refuses a `Write`/`Edit` that would put a violation on disk
  in the first place.
- `core/tools/test_written_forward.py` — the checker's own pytest.

**The ratchet is the gate: staged content must be clean.** A file nobody stages is never read; a
file someone touches is cleaned then. `written_forward.py --report` prints what the tree carries
without blocking anything — the question "what does the repo carry" has an answer on demand, not a
list that has to be edited to stay honest.

`kaizen/lenses/provenance.md` — the judgement half, at kaizen step 4. That file owns the question a
pattern cannot answer: rationale told as a story, a file describing how it was made, a date doing
work in live prose.
