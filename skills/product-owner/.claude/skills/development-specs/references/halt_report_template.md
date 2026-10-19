---
version: "1.4.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->

# Halt Report — development-specs

**Date:** YYYY-MM-DD
**Request:** <verbatim user request>

---

## Halt Reason

<one of: wrong-posture | no-active-change | ambiguous-active-change | missing-project-context |
invalid-behaviour-classification | multiple-changes | fdr-conflict | too-vague |
undecidable-direction | behaviour-delta-detected | worktree-not-created>

---

## Finding

<what the skill detected — concrete and specific>

---

## What Would Be Needed to Proceed

<specific: what information, split, or prior action would unblock this run>

---

<!-- Reason-specific guidance (remove unused blocks before writing) -->

<!-- wrong-posture:
Finding: development-specs was invoked outside product-owner posture, so the run refused before reading any project input.
Proceed: Re-run from a product-owner session — open one with the `product-owner:` prefix.
-->

<!-- no-active-change:
Finding: system/projects/<project>/journey/tobiishi/ holds no active change folder — only trail/ — so there is no change_request.md to take a Request from.
Proceed: Open the project's next change unit (tobiishi-open, PM posture), then re-run.
-->

<!-- ambiguous-active-change:
Finding: system/projects/<project>/journey/tobiishi/ holds more than one active change folder — name every key found. The Request comes from the single active one, so there is no unambiguous change to spec.
Proceed: Seal or park all but the one being worked (tobiishi-seal or the PM's own move), then re-run.
-->

<!-- missing-project-context:
Finding: No project was named, or system/projects/<project>/project.md is missing at <resolved path>.
Proceed: Re-run naming the project folder under system/projects/, and confirm its project.md exists.
-->

<!-- invalid-behaviour-classification:
Finding: change_request.md carries no Category or no Behaviour line; or states Behaviour: <value>, which is outside the closed vocabulary {preserving, changing}; or pairs Category: refactor with Behaviour: changing, or Category: feature with Behaviour: preserving. Name which.
Proceed: The PM sets or corrects the labels in change_request.md at source (tobiishi-open). This skill never defaults a missing label and never coerces an invalid one.
-->

<!-- multiple-changes:
Finding: The request covers N distinct changes: [list each change as a bullet]
Proceed: Split into N separate development-specs runs, one per change.
-->

<!-- fdr-conflict:
Finding: The request contradicts a locked FDR decision: <decision label and content>
Proceed: FDR decisions cannot be changed in the normal flow. Address via a dedicated decision-update process.
-->

<!-- too-vague:
Finding: The request cannot be expanded into testable rules. <what is unclear>
Proceed: <specific clarification — name the missing dimension>
-->

<!-- undecidable-direction:
Finding: Every material direction the request leaves open is destructive or irreversible, so the spec would carry no responsibly-specifiable change: [list each un-pickable element]
Proceed: Decide each element listed above in the request, then re-run.
-->

<!-- behaviour-delta-detected:
Finding: The request is classified Behaviour: preserving, but drafting showed it alters or adds to the FDR contract or the public interface, or on a product with no code drops, weakens or adds a statement: <what changes>
Proceed: Reclassify the request as Behaviour: changing and re-run.
-->

<!-- worktree-not-created:
Finding: create_change_worktree.py exited non-zero in Step 4. Quote its JSON fields as printed: error (the code), message, changed (whether any repository was changed before it stopped) and repos (each repository's branch_exists and worktree_exists, or null when no topology was resolved).
Proceed: Act on the message — it names the repository, the branch or path at fault, and the action that clears it — then re-run. The command never removes or reuses a branch or worktree, so whatever repos lists as existing stays until someone removes it.
-->
