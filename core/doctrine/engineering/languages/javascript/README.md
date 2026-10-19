---
version: "1.1.0"
---

# JavaScript — the packet router

Where each of the seven concerns in `languages/README.md` is answered for JavaScript. Every concern
below resolves to a file in this folder.

| Concern | Destination |
|---|---|
| Toolchain | `toolchain.md` |
| Layout | `layout.md` |
| Quality gates | `quality_gates.md` |
| Conventions | `conventions.md` |
| Errors and logging | `errors_logging.md` |
| Testing | `testing.md` |
| Gate environment | `environment.md` |

Precedence between this packet, a product's own decision files and
`<CORE>/doctrine/engineering/languages/developer_standards.md` is `languages/README.md` § Precedence, which states it
once for every packet.

## What the registry row claims, and what it leaves out

The row claims `.js`, `.mjs` and `.cjs` — the extensions Node resolves as JavaScript with nothing in
front of them (`https://nodejs.org/api/packages.html` § Determining module system).

`.jsx` is outside the row deliberately. It needs a transform before Node will run it, so a product
writing it carries a build toolchain `toolchain.md` does not describe, and that product states the
toolchain in its own `docs/adr/`, which outranks this packet. The reason to draw the line there is
that every file this packet is derived from runs as written, with no transform in front of it — by
Node directly, or by Claude Code's Workflow runner (`toolchain.md` § Module system) — and never
through a build step. On 2026-08-21 `git ls-files '*.js'` returned eight paths and
`git ls-files '*.jsx' '*.mjs' '*.cjs'` returned none. This authoring run's call, 2026-08-21.
