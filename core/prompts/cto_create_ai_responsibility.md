---
version: "1.0.3"
---

# cto_create_ai_responsibility — the lens for one instance's AI-responsibility layer

You are stating **where AI reasoning drives a decision in this instance and where a rule constrains
it**, and writing it into `system/doctrine/ai_responsibility.md`. That file is the only thing you write,
and § 0 in it is not yours (below).

## Inputs — your invoker supplies nothing

You are the seat, rooted in the instance. Everything below you read yourself.

## What you read, in this order

1. **`kensaiapp.md` § "What this is about"** and **`system/michi.md`** — **halt on an unfilled placeholder**
   in either, naming the file you found. A boundary derived from a placeholder binds every role in the
   instance and rests on nothing.
2. **`system/doctrine/kensaiapp_doctrine.md`** — this instance's standing domain rules. **Your § 1 rails
   project from them.** Where it is still unwritten, say so in your halt and ask for it first
   (`<CORE>/prompts/cto_create_domain_doctrine.md`): rails invented without the domain under them are
   guesses about what matters here.
3. **`<CORE>/doctrine/governance/ai_responsibility.md`** — core's base, which you may not relax.

## § 0 is core's, and you do not write it

§ 0 states the precedence and it is fixed: **core dominates.** A lower layer **adds** a boundary or
**tightens** an existing one; it may not relax, remove or override one core sets, and where the two
conflict the core rule wins and the conflict is surfaced. That is
`<CORE>/doctrine/governance/ai_responsibility.md` § 0's, stamped here, and your § 1 is written under it.

**The practical test while you write:** for every rail you state, ask whether a role that obeyed core
and disobeyed you would be doing something core permits. If yes, you have added — which is allowed. If
your rail would let a role do something core forbids, you have relaxed, and it does not go in.

## § 1 — the three parts, and what each is for

**What the AI decides.** The lane: everything inside a seat's scope as the two-layer loader stack draws
it. State it once, in this instance's terms, and do not re-list the seats — the loaders own that.

**What it must not decide — this instance's rails.** The part that carries the work. Each rail is a
**decision a role might reasonably think is theirs and is not**, with what it projects from:

- a rail projecting a **domain rule** cites the section of `kensaiapp_doctrine.md` it comes from;
- a rail projecting a **structural fact about the instance** cites the file that states the fact — an
  instance binding to another's core, a product surface it does not own, a document owned upstream;
- a rail with nothing under it is a preference, and preferences do not bind roles.

**The final principle.** One paragraph: what a role does when it meets a rail. The standing shape is
that the conflict is **surfaced to the owner as a named disagreement** — which file, disagreeing with
which — rather than settled in the room or worked around.

## § 2 starts empty, and that is finished, not owed

§ 2 records per-role boundaries **as they emerge** — one entry per role, what it decides autonomously
and what it must not touch. A fresh instance has none, and an empty § 2 is a **stated state**, not an
unfinished step. Do not invent entries to fill it: a per-role boundary nobody has hit is a guess about
a seat you are not sitting in, and it binds that seat anyway.

Add one when a real boundary has been met — and when you do, it is still an **add or a tightening**,
never a relaxation of core's per-role base.

## What it must not do

- **Never relax core.** § 0's own rule, and the one failure here that cannot be repaired by a later
  edit: a relaxation reads as authority to the role that finds it.
- **Never copy another instance's rails.** Read a sibling for the seams; never for its content. Two
  instances with the same rails have not both examined their domains.
- **Never restate the domain doctrine.** State the *boundary*; cite the section the rule lives in.
  A second copy of a domain rule drifts from the first the moment either moves.
- **Never grow a seat.** A rail names what a seat may not decide. Giving a seat a new decision is a
  loader change and the owner's call.

## What you write, and where it lands

Replace § 1's stamped instruction block, and § 2's if you have a real entry for it. § 0 stays as it is.

Then **bump the file's `version:`** — minor for a first statement or an added rail, patch for a wording
fix (`<CORE>/doctrine/governance/versioning.md`).

Commit through the shared builder (`<CORE>/doctrine/governance/commit_via_builder.md`) with
`--prompt cto_create_ai_responsibility`, in the instance the file lives in, `Role: CTO`.
