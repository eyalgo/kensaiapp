---
version: "1.0.1"
---

# Unsettled inputs — a run derived from one says so and continues

Governs every document in a product's definition chain (`setup/setting_up_a_project.md` § The flow at
a glance) and every document a change is carried through (`flow/development_flow.md`).

> **Owns:** whether a run halts for an unsettled input (it does not), that it records what it read,
> and the one form that record takes. **Does not own:** what the status values are or what they mean
> (each document's own `Status:` line and its template), whether a given document is settled (its
> owner), or what a run's companion open-issues file is for (the producing skill).

---

## The rule

**A run never halts for an unsettled input.** It derives best-effort from what the input holds, and
never asks the owner to settle an upstream document first. A pipeline that stalls on a `Draft` is a
pipeline that cannot run unattended, and every producer in this house is meant to.

**It records what it read.** In one line, in the document's own header:

```
**Inputs read:** <Name> <Status> · <Name> <Status> · <Name> <Status>
```

**Every input the revision read, not only the unsettled ones.** A line that appears only when
something was `Draft` is indistinguishable from a run that forgot to write it — presence must mean
"this was checked", or the absence of the line says nothing at all.

**In the header, once, not per entry.** These documents are revised in place while their entries are
append-only, so a per-entry copy would repeat the same statuses across every entry one run wrote.

Deriving and recording are two halves of one bargain. A run that derives from moving ground and does
not say so produces a document nobody can later tell was built that way — which is the failure the
rule exists to prevent, not the halting.

## A companion open issue is not a record

Routing an unsettled input to the run's companion satisfies neither half. A companion is an
**escalation**: it addresses the owner, it is answered, and it is folded in and retired. A record
addresses a **later reader** of the document, and has to still be there when they arrive. The two
have different audiences and different lifetimes, and a stack that only escalates leaves nothing
behind once the question is answered.

Escalate as well, where the producing skill says to. Never instead.

## Why the form is fixed rather than left to the run

Because a machine reads it. `core/tools/reporters.py` parses this line to report which inputs were
unsettled when a run read them; with no fixed form that report degrades to a regex near the word
`Draft`, which is what it was before this rule had one.

It was found the hard way: the behaviour was required and the wording was not, so three spellings all
satisfied it and the reader had to guess. Fixing it for one stack is what left the other eight
documents free to drift, which is why the rule sits here and not in a template.

## What a run does when it cannot judge the status

A missing status line, or a value the document's own template does not carry, **is itself the finding**:
record what was actually found in the `Inputs read:` line rather than a guess, and raise it on the
companion. An input whose state cannot be read is not the same as one that is settled, and the record
must not flatten the two.

---

Codified 2026-09-01. The behaviour is the owner's ruling of 2026-08-30; what this file adds is that
one file owns it, so the nine producers stop implementing it three ways.
