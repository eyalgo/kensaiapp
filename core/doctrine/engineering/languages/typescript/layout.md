---
version: "1.2.3"
---

# TypeScript — layout

The source tree, where a new file of each kind goes, and how files and directories are named. What a
type, function or variable is called is `conventions.md`. Which test file belongs to which testing
layer, and what it is called, is `testing.md` — this file states only where the test tree sits and
what it mirrors.

## The tree

```
index.html             the Vite entry — the app's HTML document, at the repository root
vite.config.ts         the build config — testing.md's Vitest reads this same file
.nvmrc                 the Node.js major this product targets — toolchain.md
package.json           manifest, scripts and the pnpm pin — toolchain.md
pnpm-lock.yaml          the committed lockfile — toolchain.md
tsconfig.json           the type gate's config — quality_gates.md
.oxfmtrc.json           the format gate's config — quality_gates.md
.oxlintrc.json          the lint gate's config — quality_gates.md
src/                   every line of TypeScript the product ships
  main.ts              the entry module index.html loads, and the composition root
  logger.ts            the one module that owns the console sink — errors_logging.md
  <area>/              one directory per bounded area of the product
    index.ts           re-exports only — the area's public surface
public/                files copied into the build output verbatim, never imported
tests/                 the test tree, mirroring src/ — testing.md gives the per-layer folders
dist/                  build output, ignored and never committed
```

**`index.html` sits at the repository root because Vite resolves the app from it**, not as a
convention that could be tidied away: "in a Vite project, `index.html` is front-and-central instead
of being tucked away inside `public`", and "Vite treats `index.html` as source code and part of the
module graph" (https://vite.dev/guide/). Moving it under `src/` moves Vite's project root with it,
which is a change to the build rather than a change to the layout.

**`public/` is for files that must survive the build byte-for-byte** — a favicon, a `robots.txt`, a
vendored asset referenced by URL. Anything a module imports goes under `src/`, so that the bundler
sees it, hashes it and fails when it is missing.

**Build output is ignored rather than committed.** A product here already lists `node_modules/`,
`dist/`, `dist-ssr/`, `.vite/` and `coverage/` in its `.gitignore`, and a TypeScript product here
starts from that set.

## Where a new file goes

- **One module per file, and the file is named for what it exports.** A module exporting the
  `FileTree` type and the functions over it is `file-tree.ts`.
- **A bounded area of the product is a directory under `src/`, not a file that grows.** The
  boundary is what the area is responsible for, not how large it has become.
- **`index.ts` holds re-exports and nothing else.** This is the TypeScript landing of the floor's
  rule that a package's initialization file carries no implementation
  (`<CORE>/doctrine/engineering/languages/developer_standards.md`, the `__init__.py` bullet). Implementation lives
  in the named modules beside it, and `index.ts` states which of them the rest of the product may
  reach. An area whose `index.ts` contains a function is the same defect the floor names, wearing a
  different filename.
- **`src/main.ts` is the only module that wires a concrete implementation to an abstraction** — `arch_defaults.md`
  § Composition Root, which is language-agnostic and reaches here on its own — the Python spellings are
  `arch_defaults_python.md`'s, not the body's (the owner's call, 2026-08-30).
- **There is no `utils.ts`, and no `helpers.ts`.** The floor rejects generic labels for names
  (`<CORE>/doctrine/engineering/languages/developer_standards.md`, "no generic labels"), and a file named for no
  responsibility is where every module that has not been placed ends up.
- **A type declared for one module lives in that module.** A `types.ts` is justified only when a
  type is genuinely shared across the area's modules, and then it holds only types.

## Naming files and directories

**File and directory names are `kebab-case`** — `file-tree.ts`, `read-only-editor.ts`,
`src/editor-view/`.
The packet author's call, 2026-08-21, and the ground is the filesystem rather than taste. On the
macOS host this family develops on, `git config core.ignorecase` returned `true` in the instance that holds the shared
core on 2026-08-21, so a rename that changes only a letter's case is invisible to git. Such a rename
lands in another checkout as a file that resolves locally and fails in CI, and a convention with one
case never produces it.

A file's name does not repeat the directory it is in — `src/git/state.ts`, not
`src/git/git-state.ts`.
