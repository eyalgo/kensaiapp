---
version: "1.0.0"
---

# PM loader — kensaiapp overlay

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
