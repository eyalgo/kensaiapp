---
version: "1.0.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->
<!-- Nor is this block. What this stamps: the **pm** instance overlay, landing at
     `system/loaders/pm.md`.

     Why pm has its own template rather than a slot in `overlay_template.md`: pm is the only role in
     a kensaiapp that reads a context on invocation, and that context is **per-project** —
     `system/projects/<name>/contexts/CONTEXT_PM.md`, written by `tobiishi-open` and marked done by
     `tobiishi-seal`, never hand-edited (`<CORE>/doctrine/setup/kensaiapp_structure.md` §1: the PM's
     is the only per-role context). Folding that into a substitution slot would hide a structural
     difference inside a string.

     Replace `<instance>`. The stamped file starts its own `version` at 1.0.0 and carries no comment
     blocks. -->

# PM loader — <instance> overlay

Extends `<CORE>/roles/loaders/pm_global.md` (role posture, skills, hand-off triggers). This overlay
adds only what is true of *this* instance — everything else is the global loader's; read it there
rather than trusting a summary here.

## On invocation

Read the directed project's `system/projects/<name>/contexts/CONTEXT_PM.md` — the
per-project PM context, holding that project's current change from the PM's view. This is the only
overlay that carries an on-invocation context read.

## Key files

- `system/projects/<name>/project.md` — the project card and product binding (`Product path:`).

## The domain

**Not declared yet.** This instance's domain section is deliberately empty — it is authored per
instance, and leaving it blank is a stated state, not an oversight. Until it is written, the global
loader's posture governs alone. Do not copy another instance's domain here.

## Project-specific rules / overrides

None yet — the global pm posture governs.
