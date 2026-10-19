---
version: "1.0.5"
---

# outside_restatement — a role fact restated outside the role layer, drifting there

A seat's facts are restated in files that are not role files: governance doctrine that must name a seat
to say which `Role:` a commit takes, setup manifests that enumerate what each seat authors, templates
that describe the seat stamping them. Those restatements are repaired last, because a run repairing a
seat reads the seat's own directory. **The tell is a repair that landed inside the role layer, followed
by a copy outside it that still reads the old way.**

This lens is the outward-facing half of `fact_agreement.md`. The failure is the same; the search is
not, and an auditor given one must not be told to do the other's job, or the fresh read is gone.

## What this lens reads

Everything **except** the role layer, holding one seat fact as the thing being traced:

- `core/doctrine/**` — governance, setup, flow, engineering, kaizen.
- `core/templates/**`.
- `system/doctrine/**` and `system/michi.md`.
- `AGENTS.md` and `kensaiapp.md`, and the user-global instruction file above them.
- Executable machinery that encodes a seat: `core/tools/`, `.claude/hooks/`, `.claude/workflows/`.

The lens is given the fact as the role layer currently states it, with its citation. It does not
re-derive that fact — that is `fact_agreement.md`'s output, and re-deriving it here would let two
lenses disagree about the baseline.

## The question

**Does every statement of this seat fact outside the role layer match the role layer's statement of it?**

## What the shape looks like

| The lens finds | Which is a defect when | Must not |
|---|---|---|
| A doctrine file naming a different set of seats for one artifact than the loader does. | The doctrine file states it as current, not as history. | Report a file that is deliberately recording a past state. |
| An enumeration of what a seat authors that omits an artifact the loader claims. | The enumeration claims to be complete for that scope. | Treat a product-scoped list as incomplete because it omits instance-scoped work. |
| Machinery encoding a seat — a role map, an allowlist, a stage list — that disagrees with the loader. | The machinery is live rather than deprecated. | Read an allowlist's omission as an oversight; an allowlist's meaning can be in what it omits. |
| A template describing the seat that stamps it in terms the loader no longer uses. | The template still stamps new files. | Report a term that differs only in wording. |

## Evidence this shape is real

**Instance one — repaired 2026-08-26, and kept here because the repair is the evidence.**
`core/doctrine/governance/commit_format.md:119` stated that the CTO "authors the **SRS**
(`docs/SRS.md`) and co-authors the SDD with the CPO" — two seats, where the role layer says three at
`core/roles/loaders/cto_global.md:53`, "**The SDD — one run, three seats: you, the CPO and the CDO.**"
The role layer's own copies were repaired 2026-08-25 at `d5d9f260`; this one survived that sweep and
two before it, and was found only when a cold read of an unrelated station walked into it. **That is
the shape**: a restatement outside the role layer outlives every fence drawn around the role layer,
because no fence names it. Repaired at the `sdd-stale-facts-outside-every-fence` station.

**Instance two — live, and found by this lens.** `core/tools/commit_builder.py`'s `AGENT_ROLE` map,
which its own comment calls "this module's sole home for the actor -> Role mapping", holds fifteen
entries and no `qa` key. The role layer requires that seat to commit:
`core/roles/loaders/qa_global.md:19` reads "Read the produced artifact + its source of truth; write and
commit the verification file", and its three listed skills each say the seat "produces and commits" an
acceptance file. The agent exists at `skills/qa/.claude/agents/qa.md`. A seat obliged to commit has no Role to
commit as.

**The scale, measured 2026-08-25.** Twenty-six files outside the role layer assert what a seat owns:

```
grep -rln "the CTO\|the CPO\|the CDO\|the Content Manager\|the Principal PM\|the Product Owner\|the Tech Lead" \
  core/doctrine/ core/templates/ system/doctrine/ | wc -l
```

Twenty-six restatements repaired last is why this shape recurs, and why it is a separate search rather
than a wider setting on `fact_agreement.md`.

## What this lens may not assert

- **That the outside copy is the wrong one.** The role layer is the more likely place for a fact to be
  right, and likelier is not a verdict. Both sides are named.
- **That a restatement should not exist.** Whether a fact may be restated at all belongs to
  `core/doctrine/governance/single_source.md`. This lens asks only whether the copy agrees.
- **That an allowlist's omission is a defect.** `core/tools/commit_builder.py` says of its second table
  that it "IS AN ALLOWLIST, NOT A DICTIONARY, AND ITS MEANING IS IN WHAT IT OMITS". An omission from a
  table that declares itself an allowlist is reported as a question, never as drift.
- **That a file recording history is stale.** A file describing what a seat used to do, and saying so,
  is correct.

## Reporting

One finding per fact, naming the role-layer statement with its quoted phrase, every outside statement
that differs with its own quoted phrase, and whether each outside file is doctrine, machinery or a
template — because the three are repaired by different actors and a reader needs to know how many.

## The lens ran clean when

- every location outside the role layer stating the traced fact was found, not only the ones in
  doctrine;
- executable machinery was searched as well as prose, since a role map in code states a seat fact as
  firmly as a sentence does;
- every allowlist found was checked against its own declaration of what an omission means before any
  omission was reported;
- each finding quotes both sides and declares neither correct;
- the lens says so explicitly when it found nothing.
