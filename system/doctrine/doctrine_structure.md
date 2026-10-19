# Doctrine structure — kensaiapp

*The **meta-layer**: how this instance's doctrine is tiered, kept consistent, and evolved — not domain
rules, not AI rules (those live in their own doctrine files), only the structural principles. `AGENTS.md`
§ doctrine stubs points here. Extends **core's doctrine meta-layer**
(`<CORE>/doctrine/governance/doctrine_structure.md`). Stamped verbatim into
`system/doctrine/doctrine_structure.md`.*

---

## Tiers

- **Instance doctrine** (`system/doctrine/`) — shared across all projects: the domain doctrine
  (`kensaiapp_doctrine.md`), AI responsibility (`ai_responsibility.md`), the writing bar
  (`writing_bar.md`), and this file.
- **Per-project doctrine** (`system/projects/<name>/doctrine/`) — one project's own domain doctrine and
  AI-responsibility layer, adding only what is specific to that product.
- **Product decision records** (`<product>/docs/fdr.md`, `<product>/docs/nfdr.md`, and the decision
  log `<product>/docs/adr/`) — scoped to one product; travel with the product.

Which files sit in `system/doctrine/` at all, and how each arrives — stamped from a template or
authored — is `<CORE>/doctrine/setup/kensaiapp_structure.md` § *Instance-shared doctrine*, where they
are `[create]`: created if missing, never overwritten.

## Consistency model

A structural change is a single-source edit: the file tree, and each entry's disposition, lives in
**core's instance manifest** (`<CORE>/doctrine/setup/kensaiapp_structure.md`); disposition behaviour +
drift checks live in core's scope file (`<CORE>/doctrine/setup/setup_scope.md`). This instance's
stubs **project** from those — they do not restate the tree.

---

> **Tiering grows with the doctrine set.** Add the ADR-promotion lifecycle and a project-specific
> tier-classification table as doctrine accrues; both extend core's meta-layer rather than
> restating it.
