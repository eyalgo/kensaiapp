---
version: "1.1.0"
---

# Shell — packet router

Routes each of the seven language-packet concerns to the file that answers it for shell, and answers
none of them itself. The concern set, the router rule, the resolution chain, precedence and the packet
lifecycle are one level up, in `languages/README.md`.

**This packet's practice is bash, not POSIX `sh`.** All twenty shell files in the instance declare
`#!/usr/bin/env bash` — the eighteen `.sh` files `git ls-files '*.sh'` returns and the two extensionless
git hooks below — and none is invoked through `sh`. The registry names the row `Shell` for the extension
it detects on; every rule under it was measured over bash.

## The seven concerns and where each is answered

| Concern | Destination |
|---|---|
| Toolchain | `toolchain.md` |
| Layout | `kensaiapp_structure.md` § Owner-run launcher folder and § Shared-tools layer — outside this folder |
| Quality gates | `quality_gates.md` |
| Conventions | `conventions.md` |
| Errors and logging | `errors_logging.md` |
| Testing | `testing.md` |
| Gate environment | `environment.md` |

Six destinations sit beside this file. **Layout's does not.** `kensaiapp_structure.md` already owns
where a shell file goes and what it is called: § Owner-run launcher folder fixes the folder
(`core/launchers/<identity>/`), the script name ("the script itself is named for its role, the folder
carries the identity"), the bare-identity folder rule, and the test-file naming rule that exists because
"pytest imports test modules by basename"; § Shared-tools layer fixes the other home, `core/tools/`, and
the line between them — "`core/tools/` is system-called machinery (a kensaiapp element calls it), while a
launcher here is owner-run (the owner invokes it directly)". A `layout.md` here would carry a pointer and
nothing else, which `languages/README.md` § The packet router puts in this table instead.

Every one of the seven refines `<CORE>/doctrine/engineering/languages/developer_standards.md`, the language-agnostic
floor, and none replaces it. A rule the floor states and this packet never mentions is still in force
over shell code.

## What the registry row claims

`.sh`, and no second extension. No `.bash`, `.zsh`, `.ksh` or `.bats` file is tracked —
`git ls-files '*.bash' '*.zsh' '*.ksh' '*.bats' | wc -l` returned 0 on 2026-08-23 — so there is no
second file kind for the row to name.

**Two bash files carry no extension at all, and extension-based detection cannot reach them.**
`core/githooks/commit-msg` and `core/githooks/pre-commit` are git-native hook shims, invoked by git
through `core.hooksPath` and named by git rather than by this house, so neither can take a `.sh`
suffix. Both open `#!/usr/bin/env bash` and both hold every rule in this packet. A run that resolves
its language at step 3 of `languages/README.md` § The resolution chain — inference from the file
extensions present under the working root — will not see them; a run that touches either should open
this packet on the shebang.
