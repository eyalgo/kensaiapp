---
version: "1.2.0"
---

# TypeScript — packet router

This file routes each of the seven language-packet concerns to the file that answers it for
TypeScript, and answers none of them itself. The concern set, the router rule, the resolution chain,
precedence and the packet lifecycle are one level up, in
`core/doctrine/engineering/languages/README.md`.

## The seven concerns and where each is answered

| Concern | Destination |
|---|---|
| Toolchain | `toolchain.md` |
| Layout | `layout.md` |
| Quality gates | `quality_gates.md` |
| Conventions | `conventions.md` |
| Errors and logging | `errors_logging.md` |
| Testing | `testing.md` |
| Gate environment | `environment.md` |

Each destination is a file in this folder, beside this one.

Every one of those seven refines `<CORE>/doctrine/engineering/languages/developer_standards.md`, the
language-agnostic floor, and none of them replaces it. A rule the floor states and this packet never
mentions is still in force over TypeScript code.
