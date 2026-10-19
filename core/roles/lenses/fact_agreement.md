---
version: "1.0.1"
---

# fact_agreement — one role fact, stated in several role files, disagreeing with itself

A fact about a seat — who authors an artifact, how many seats work a run, which seat a handoff reaches
— is written in more than one file of the role layer. When one copy is repaired and the others are not,
the layer holds two answers and a cold reader takes whichever file they opened. **The tell is a fact
stated as a count or a list of seats: "two seats", "you and the CPO", "the CTO's and the CDO's".** A
count is the form that rots silently, because a reader has no way to know a third name was added
somewhere else.

## What this lens reads

The role layer, and nothing outside it:

- `core/roles/loaders/*_global.md` — every global loader, not only the seat under audit.
- `system/loaders/*.md` — every instance overlay.
- `core/roles/CROSS_ROLE.md` and `system/CROSS_ROLE.md`.
- `core/prompts/*.md` and `skills/*/.claude/skills/*/prompts/*.md` — the authoring prompts, which
  state seat facts while teaching.

A file outside this set is `outside_restatement.md`'s, not this lens's.

## The question

**For each fact this layer states about a seat, do all the files stating it say the same thing?**

Not: is the fact correct. The lens does not know which copy is right, and saying so is the point — a
disagreement is reported as a disagreement, with both sides named.

## What the shape looks like

| The lens finds | Which is a defect when | Must not |
|---|---|---|
| The same artifact given a different set of authoring seats in two files. | Neither file marks the difference as settled. | Assert which count is correct. |
| A seat's owned artifact named in one file and absent from another file that enumerates that seat's outputs. | The second file's enumeration claims to be complete. | Treat a file that never claimed completeness as having an omission. |
| A handoff whose two ends name different receiving seats. | Both files describe the same handoff. | Merge two handoffs that merely look alike. |
| A count of seats, steps or files that differs between two statements of it. | The two statements are of the same thing. | Recount from a third file and report that as the answer. |

## Evidence this shape is real

**Instance one — repaired, and the repair was incomplete.** `core/roles/loaders/cto_global.md` said the
SDD had two authoring seats in nine places while the CPO and CDO loaders said three. It was repaired
2026-08-25 at `d5d9f260`, whose subject line is "cto_global.md and cto_create_srs.md name the SDD's
three seats". The repair reached two files.

**Instance two — live, and found by this lens.**
`core/roles/loaders/principal_pm_global.md` carries the heading "## Three seams — CTO/CPO, PM, the
owner", naming two seats for a run that `core/roles/loaders/cto_global.md` describes as "**The SDD —
one run, three seats: you, the CPO and the CDO.**" The CDO is missing from the Principal PM's account
of the same seam. This copy survived `d5d9f260` because that repair read the CTO's files and not its
siblings'.

Two independent instances of one fact, in two different files, at two different times, is the shape.
The command that surfaced the second, run 2026-08-25:

```
grep -rn "SDD" core/roles/loaders/*.md system/loaders/*.md core/prompts/*.md \
  | grep -i "author\|co-author\|three seat\|two seat\|with the"
```

## What this lens may not assert

- **That a marked disagreement is a defect.** `core/roles/loaders/principal_pm_global.md` records one
  in its own text — "The FDR is yours, and the skill that authors it disagrees — knowingly" — and names
  it settled by the owner. A disagreement the layer already documents as examined is a record. Report it
  only if the file it points at has since moved.
- **Which copy is stale.** The lens has no access to intent. Both sides are named and the call is
  someone else's.
- **That two differently-worded statements disagree.** Two files may state one fact in different words
  and agree completely. The lens reports a disagreement in *content*, never in phrasing — a wording
  difference is `core/doctrine/kaizen/lenses/` territory if it is anyone's.
- **That the fact belongs in only one of the files.** Whether a copy should exist at all is
  `core/doctrine/governance/single_source.md`'s question, decided elsewhere.

## Reporting

One finding per fact, not per file. The finding carries: the fact in one sentence, every file stating
it with its quoted phrase, and what differs between them. A fact stated identically in six files and
differently in a seventh is one finding naming all seven, because a reader deciding the repair needs to
know how many copies move.

## The lens ran clean when

- every seat fact stated more than once in the read set was compared against each of its statements;
- every count and every seat-list in the read set was located and compared, since those are the form
  that rots;
- each disagreement found is reported with both sides quoted, and neither side declared correct;
- each disagreement the layer marks as settled was checked against the file it points at, and reported
  only if that file has moved;
- the lens says so explicitly when it found nothing, since an empty section reads as "not audited".
