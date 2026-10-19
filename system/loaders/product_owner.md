---
version: "1.0.0"
---

# Product Owner loader — kensaiapp overlay

Extends `<CORE>/roles/loaders/product_owner_global.md` (role posture, skills, hand-off triggers). This overlay
adds only what is true of *this* instance — everything else is the global loader's; read it there
rather than trusting a summary here.

## On invocation

No on-invocation context read. Posture comes from the two-layer stack (the global core loader
above + this instance overlay); live state comes from the directed project's `journey/`, consulted
**deliberately** — not read reflexively here.

## Key files

- `system/projects/<name>/project.md` — the project card and product binding (`Product path:`).

## The domain

**Not declared yet.** This instance's domain section is deliberately empty — it is authored per
instance, and leaving it blank is a stated state, not an oversight. Until it is written, the global
loader's posture governs alone. Do not copy another instance's domain here.

## Project-specific rules / overrides

None yet — the global Product Owner posture governs.
