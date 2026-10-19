<!-- Template metadata; this block is not copied into the instantiated document. What this stamps:
     the app-level cross-role overlay, landing at `system/CROSS_ROLE.md` — the instance layer over
     the shared contract at `<CORE>/roles/CROSS_ROLE.md`. Sibling of `system/loaders/`,
     `system/michi.md` and `system/nemawashi/`.

     No frontmatter, matching the instances on disk. Replace `<instance>`. -->
# Cross-role contract — <instance>

The lean contract for multi-role iteration work on this instance. Extends the shared cross-role contract
(`<CORE>/roles/CROSS_ROLE.md`) — this file carries only instance-specific iteration shape, not a
restatement of the shared contract.

---

## Roles on this instance

The standard set: cpo · cto · cdo · architect · tech-lead · developer · content-manager · content-editor · product-owner · pm · principal-pm · principal-architect · qa · scrum-master · senior-engineer.
Each has a global loader (`<CORE>/roles/loaders/<role>_global.md`) and, for the fourteen prefix-invoked roles,
an app-level overlay (`system/loaders/<role>.md`). QA is fork-invoked, not prefix-invoked — global-only,
no overlay, no context.

**The overlays are present and clean.** Each carries the thin shape and an explicitly undeclared domain
section. That is a stated state, not an oversight — the domain is authored per instance, and until it is,
the global posture governs alone.

## Hand-off spine

The change pipeline is folder-derived (no per-role inbox). One change travels through
`system/projects/<name>/journey/tobiishi/<key>/` as the chain runs one role per step:

development-specs (product-owner) → development-design (architect) → development-plan (tech-lead) →
development-content (content-editor) → development-implementation (developer) → development-code-integrity (senior-engineer) →
development-audit (the pipeline auditor, not a gate) → tobiishi-seal (pm).

QA is not a step; it is forked on a committed artifact, outside the chain.

---

> **What this layer adds:** instance-specific iteration lifecycle, verdict taxonomy, and
> falsification rules, written here as they accrue. Anything this file does not state is governed by
> the shared cross-role contract (`<CORE>/roles/CROSS_ROLE.md`) — read it there, not here.
