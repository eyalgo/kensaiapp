---
version: "1.3.0"
---

# Python — packet router

Routes each of the seven language-packet concerns to the file that answers it for Python, and
answers none of them itself. The concern set, the router rule, the resolution chain, precedence
and the packet lifecycle are one level up, in `languages/README.md`.

## The seven concerns and where each is answered

| Concern | Destination |
|---|---|
| Toolchain | `toolchain.md` |
| Layout | `layout.md` |
| Quality gates | `quality_gates.md` |
| Conventions | `conventions.md` |
| Errors and logging | `errors_logging.md` |
| Testing | `testing_python.md` — outside this folder; layers 1–6 answered there, layer 7 routed |
| Gate environment | `environment.md` |

Six destinations sit beside this file. **Testing's does not.** `testing_python.md` already
implements the layer model for Python — it describes itself as "Python-specific tooling and
layout" and fixes the file location and the run command for layers 1 through 5, and the tool for
four of those five: layer 4 has no standing Python tool (`testing_python.md:20`, "no standing tool
— see the rule below"; `testing_python.md:30`, "Layer 4 has no standing Python tool."). It answers
layer 6 as well — `testing_python.md:36` heads "Layer 6 — Architecture" over a filled table and four
rules — and it routes layer 7 rather than answering it: `:66-70`, "**Not answered here.**… A Python
product writing them today records its runner in `docs/nfdr.md` § 9." A `testing.md` here would
carry a pointer and nothing else, which `languages/README.md` § The packet router puts in this table
instead.

Every one of the seven refines `<CORE>/doctrine/engineering/languages/developer_standards.md`, the language-agnostic
floor, and none replaces it. A rule the floor states and this packet never mentions is still in
force over Python code.

## What the registry row claims

`.py`, and no second extension. No `.pyi`, `.pyw`, `.pyx` or `.ipynb` file is tracked —
`git ls-files '*.pyi' '*.pyw' '*.pyx' '*.ipynb'` returned nothing on 2026-08-21 — so there is no
second file kind for the row to name and no build step in front of the one it does.
