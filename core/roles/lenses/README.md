---
version: "1.1.1"
---

# Role lenses

The lenses an audit of the **role layer** reads with. Each is one file, versioned on its own, loaded by
one auditor. A reader who stops here knows the set's purpose: it asks whether a seat's own files still
agree with each other and with the machinery that runs the seat.

**A role lens judges the role's files, by reading them.** There is no produced artifact in between. That
is the whole difference from `core/doctrine/kaizen/lenses/`, whose contract is "A lens judges the skill,
through its output" — a question no role lens can answer, because a role is not a skill and emits no
artifact of its own to be judged. That set's § *What does not live here* sanctions exactly this
arrangement, naming flow-audit's lenses as "a different set answering a different question"; this is a
second such set.

**One lens per auditor, and it loads only its own.** An auditor that reads its siblings' definitions
learns which failures are somebody else's job and stops looking there. That rule is the kaizen set's and
is adopted here unchanged, which is why these are separate files rather than one list.

## The set

| File | Reads | The question it asks |
|---|---|---|
| `fact_agreement.md` | The role layer's own files. | Does one role fact say the same thing everywhere inside the layer? |
| `outside_restatement.md` | Every file outside the role layer that asserts what a seat owns. | Does a role fact restated outside the layer still match the layer? |
| `capability_match.md` | A loader against its agent file. | Does the agent permit what the loader requires? |
| `seam.md` | Two seats' owned-artifact sets. | Would these two seats ever write the same file? |
| `wiring_closure.md` | A role file against the machinery it names, in both directions. | Does everything each side names actually exist? |

## What every lens in this set owes

**A ratified disagreement is not a defect.** This layer can contain disagreements that were examined
and kept. `core/roles/loaders/principal_pm_global.md` carried one in its own text until `c3a2010c`
resolved it — at `5c0e4dda` it read "The FDR is yours, and the skill that authors it disagrees —
knowingly", settled by the owner and marked as settled. A lens that reports such a record has found
the record, not the fault. Every lens here therefore carries a
§ *What this lens may not assert*, and a finding that steps over that line is withdrawn rather than
downgraded.

**A finding names the two places, never one.** A disagreement has two sides and the lens does not know
which is stale. Naming one side asserts a repair the lens is not entitled to; naming both leaves the
call where it belongs.

**The lens does not repair.** Reporting is the whole output. Which layer carries a fix is decided
elsewhere, the way `core/doctrine/kaizen/lenses/locate_layer.md` decides it for a skill.

## Growing the set

A new lens names a **shape of failure, not an instance of one**. If it fires only on the case that
prompted it, it is a finding and belongs in a seed. That bar is
`core/doctrine/kaizen/lenses/README.md` § *Growing the set*, adopted here rather than restated in its
own words, because a second wording of one rule drifts from the first.

**A lens is not written per role.** Fourteen lenses named for fourteen seats would each fire on exactly
one seat, which is the bar's own definition of a finding. Every lens here is read against every seat.

**Evidence carries the commit it was true at.** A lens that quotes a live file to show its shape is real
goes stale as that file moves — three of this set's worked examples decayed inside a month, one of them
rewritten by a sweep into a sentence that had never been true at any commit. So cite the **SHA** the
quoted text stood at, beside the path and line. A quotation anchored to a commit stays true permanently;
one anchored to a path is true until the next person edits the file, and nothing announces when it stops.

Bump a lens's own version when you sharpen it, so an audit can say which version found what.

## What does not live here

- **The kaizen set.** `core/doctrine/kaizen/lenses/` judges a skill through its output; nothing in this
  set is a substitute for it, and nothing here re-scopes or judges it.
- **The job that runs these.** No role audit exists on disk today. Until one does, these are read by a
  brief that names the lens and the seat, and that absence is a stated state rather than a gap this
  file can close.
- **What a role is, and how one is added.** `core/doctrine/setup/adding_a_role.md` owns the order of
  the steps; `core/doctrine/setup/authoring_layers.md` owns what may be written in each file.
