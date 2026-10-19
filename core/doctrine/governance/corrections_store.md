---
version: "3.1.0"
---

# Corrections store — session-craft, and when it becomes doctrine

Governs the relationship between the two stores that hold a kensaiapp instance's rules: this doctrine
set, and the per-instance **corrections store** the harness keeps outside the repo. This file owns
which store a rule belongs in and what moves a rule between them. It owns nothing about what any
individual rule says — a graduated rule goes to the file that owns its subject — and nothing about the
store's format or mechanism, which are the harness's.

## The two stores

**`core/doctrine/` holds rules about the system and its products.** A commit's trailers, where a file
lives, what a skill may contain, how a change moves through the pipeline.

**The corrections store holds session-craft** — how a session conducts itself. Check whether an owner
already exists before designing one; verify a filter by its effect rather than by reading it; name the
SHA before a destructive git operation. True of the work, not of the artifact.

It lives at `~/.claude/projects/<instance-path-slug>/memory/`, one file per rule plus a `MEMORY.md`
index, and is **per instance**: five kensaiapp instances carried their own on 2026-08-24. It is
outside every repo, so no instance's doctrine can restate its contents and no repo operation can
reach it.

**The subjects do not overlap, and neither store is the other's cache.** A rule stated in both is a
copy, and `single_source.md` deletes a copy rather than reconciling it.

## Graduation — recurrence is the trigger

Parallel is the default, not the whole rule. **A craft lesson the system needed more than once hardens
into doctrine and leaves the store.** One incident is a correction; a correction that returns is a rule
the system needs, and the store is not where a rule the system needs belongs.

**The threshold is repetition, wherever it happened.** Three variants of one root cause inside a
single session is recurrence: the rule was needed three times, which is what makes the failure
structural rather than circumstantial. A cluster in one session counts; waiting for a later session to
reproduce it means holding a rule the system has already demonstrated it needs. One incident, once,
stays a correction.

Graduation is one act, not two: the rule is stated in the doctrine file that owns its subject, given
its `task_map.md` row, and **deleted from the store in the same breath**. A graduate left behind is a
copy, and it is the copy that reads as current when the doctrine moves under it.

**The rule is written from the correction, not copied from it.** A correction file is one session's
account of one incident. Doctrine states what is true now, per `written_forward.md`. Lifting the prose
carries the incident into a file whose subject is the rule.

## Recurrence is necessary, not sufficient — a graduate needs an owner

**A rule graduates only when both hold: it recurred, and a doctrine file owns its subject.** This set
is organised by system subject — commits, versioning, file layout, a language's practice. A craft rule
whose subject is the session's own rigour, rather than any artifact, has no file to land in.

**Where that happens, the rule stays in the store, and that is a finished state.** Not a backlog and
not a rule awaiting a home: forcing it into the nearest file puts it under a declaration that does not
cover it, and inventing a file per such rule spends a doctrine file on each. Both are worse than a
correction that stays a correction.

The test is the receiving file's own declaration. If landing the rule would require widening what that
file says it owns, the file is not its owner — `single_source.md` § *A file declares what it owns*.

**The case this was written from.** *Verify a filter by its effect, not by reading it, and re-derive a
count before it enters a document* met the threshold — two independent instances, both writing wrong
numbers into a document. It has no owner. Its subject is making a measured claim, and no file here
owns that: the nearest candidate governs how committed shell is named and shaped, while the failure
happens in the throwaway pipelines a session composes to measure something. So it stays a correction,
and this section is what it produced instead.

## A growing store means graduation has stalled

The store's size is a signal, and the signal is about this file's process rather than about the store.
It is not an archive: a correction either recurs and graduates, or it does not and stays small.

**This is what the absence of this file cost.** Measured 2026-08-24, before it existed: 71 files, 30,544
words, of which 14 stated a rule `core/doctrine/` already owned — graduates nobody deleted, because
nothing said graduation was a thing that happened.

## A delegated run does not read the store, and that is not fixed with a store

The corrections store reaches the session it belongs to. A subagent inherits none of it.

**The fix is upstream, at the brief.** `agent-invoke` already requires a brief to name the doctrine its
job routes through, its citations, and its constraints; a craft rule a delegated run needs is one the
brief carries. Two things this rules out, both tried: a hook injecting the store into every run, and a
second copy of the craft in a file delegates read. The first was built once and deleted with its own
doctrine after failing while in context from a session's first token.

## What this file does not govern

- **What any rule says.** Its owning file does. A graduated craft rule about git operations went to
  `commit_format.md` § Git operations on 2026-08-24; that is the pattern, not an exception.
- **The store's format, its index, or how the harness loads it.** Not kensaiapp's.
- **Whether a rule already stated is *reachable* by whoever it binds.** A rule stated where its
  audience never reads it is a routing defect, not a graduation candidate — `task_map.md` owns
  reachability, and a second copy is not the remedy.
