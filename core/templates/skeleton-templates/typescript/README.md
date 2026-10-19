# TypeScript skeleton tree

What `core/launchers/product-skeleton/launcher.sh` will copy wholesale into a TypeScript
product before any product-specific code exists — the frame every TypeScript product here
always needs and never varies. Every choice below traces to
`core/doctrine/engineering/languages/typescript/<file>.md`, which is that language's packet, and
its own router (`core/doctrine/engineering/languages/typescript/README.md`) gives each of the
seven concerns exactly one destination — all seven resolve inside this same folder, so nothing here
is answered by an outside owner.

This file states, per choice, which packet file fixed it, and — separately — which files needed a
vendor citation for their literal syntax (the packet fixes *policy*: which tool, which option;
the vendor's own docs fix what the config file for that tool *looks like*).

## What a copy of this tree gives a product

| File | What it is | Fixed by |
|---|---|---|
| `.nvmrc` | the Node.js major this product targets | `toolchain.md` § Runtime |
| `package.json` | manifest, scripts, `engines.node`, `packageManager` pin, dev dependencies | `toolchain.md` (whole file) |
| `pnpm-lock.yaml` | **deliberately absent** — see below | `toolchain.md` § Adding, pinning and locking a dependency |
| `tsconfig.json` | the type gate's config, verbatim from the packet | `quality_gates.md` § `tsconfig.json` |
| `.oxfmtrc.json` | the format gate's config, verbatim from the packet (`{}`) | `quality_gates.md` § `.oxfmtrc.json` and `.oxlintrc.json` |
| `.oxlintrc.json` | the lint gate's config, verbatim from the packet | `quality_gates.md` § `.oxfmtrc.json` and `.oxlintrc.json` |
| `vite.config.ts` | the build config, empty — a product's own plugins/aliases land here | `toolchain.md` § Build tool — Vite; shape from the vendor (see below) |
| `vitest.config.ts` | `test.projects`, splitting layers 1–3 (and 6) in Node from layer 4 in the browser | `testing.md` § The rules that make that table work |
| `playwright.config.ts` | `testDir` for layer 5 spec files | `testing.md` § Layers 6–7 — acceptance-time |
| `index.html` | the Vite entry, at the repo root because Vite resolves the app from it | `layout.md` § The tree |
| `.gitignore` | `node_modules/`, `dist/`, `dist-ssr/`, `.vite/`, `coverage/` — the exact set `layout.md` names | `layout.md` § The tree |
| `src/main.ts` | the composition root, empty | `layout.md` § The tree; `arch_defaults.md` § Composition Root |
| `src/logger.ts` | the one module that owns the `console` sink, all four levels | `errors_logging.md` § Logging |
| `src/app-error.ts` | the single named base error type | `arch_defaults.md` § Exception shape; `errors_logging.md` § Raising |
| `tests/{unit,integration,application,ui,architecture,e2e}/.gitkeep` | the test tree root, one folder per layer | `testing.md` (table under Layers 1–5 and Layers 6–7) |
| `public/.gitkeep` | files copied into the build output verbatim | `layout.md` § The tree |

## What it deliberately omits, and why

- **No `src/<area>/` directory, no `index.ts` re-export file, no component, route, entity or
  feature.** `layout.md` § Where a new file goes gives the rule for these but not their content —
  a bounded area is the product's own boundary, read per product from the SDD § 3 parts table,
  which is the launcher's job, not this tree's.
- **No `pnpm-lock.yaml`.** `toolchain.md` fixes the *policy* — "Exactly one lockfile is
  committed, and it is `pnpm-lock.yaml`" — but a lockfile is a resolution of a real dependency
  graph against the registry at install time, the same category as `node_modules/` and `dist/`:
  generated, not authored. It does not exist until a product runs its first `pnpm install`, so
  fabricating one here would be inventing a resolution nobody performed.
- **No `webServer` / `baseURL` in `playwright.config.ts`.** `testing.md` is explicit that layer 5
  "drives the built output rather than the dev server," but there is no built output for a frame
  with no product code — wiring one now would mean pointing at something that does not exist.
  `testDir` is the only setting this tree can honestly fix.
- **`.oxlintrc.json` carries only `typeAware`.** `quality_gates.md` states this is "the one option
  this packet turns on" and that oxlint's own defaults need no more.

## Where the seven concerns' destinations live, and the one still open

All seven of the TypeScript router's destinations
(`core/doctrine/engineering/languages/typescript/README.md`) are files inside this same packet
folder — Toolchain → `toolchain.md`, Layout → `layout.md`, Quality gates → `quality_gates.md`,
Conventions → `conventions.md`, Errors and logging → `errors_logging.md`, Testing → `testing.md`,
Gate environment → `environment.md`. Gate environment fixed no file in this tree, because it decides
where a product's gates run rather than what the copy ships. None of the seven routes outside the
folder for TypeScript, so `arch_defaults.md` § Package
Structure ("each module is a package directory... not a flat file") is not something this frame
needs to resolve — it only starts mattering once a product's `src/<area>/` directories exist, and
those are the launcher's to create per the SDD.

`layout.md` never distinguishes this instance's own code from a managed product's — its tree
diagram (`index.html`, `src/main.ts`, `src/<area>/`, …) reads as a product's structure throughout,
with nothing scoped to the host instance itself. So this tree took `layout.md` as the full answer
rather than falling back to `arch_defaults.md` for anything but the Composition Root and
Exception-shape rules it names explicitly by cross-reference.

## Syntax verified against the vendor, not the packet

The packet fixes *policy* (which tool, which option); a config file's literal shape is the
vendor's. Verified this session, each against the tool's own docs, retrieved 2026-09-02:

| File | Vendor source |
|---|---|
| `vite.config.ts` | `defineConfig` import/export shape — https://vite.dev/config/ |
| `vitest.config.ts` | `test.projects`, the `browser.provider`/`instances` shape, and the
  `@vitest/browser-playwright` install command (`pnpm add -D vitest @vitest/browser-playwright` —
  no separate `@vitest/browser` package) — https://vitest.dev/guide/browser/ |
| `playwright.config.ts` | `defineConfig` from `@playwright/test`, `testDir` — https://playwright.dev/docs/test-configuration |
| `index.html` | the `<script type="module" src="...">` entry shape — https://vite.dev/guide/features.html |
| `package.json` `engines.node: "24"` | a bare major version is an X-Range, `24 := >=24.0.0 <25.0.0-0` — https://github.com/npm/node-semver#ranges |
| `package.json` `engines` | advisory-only unless `engine-strict` — https://docs.npmjs.com/cli/v11/configuring-npm/package-json#engines |
| `package.json` `packageManager` | Corepack "accepts nothing but an exact version"; hash suffix optional — https://github.com/nodejs/corepack#readme |
| `.oxlintrc.json` | `{ "options": { "typeAware": true } }` shape confirmed against — https://oxc.rs/docs/guide/usage/linter/config-file-reference.html |
| `package.json` `scripts.dev/build/preview` | `vite`, `vite build`, `vite preview` are Vite's own CLI subcommand names — https://vite.dev/guide/cli.html |

`devDependencies` version ranges are caret ranges on each package's current registry `latest` at
the time of this run (`registry.npmjs.org/<pkg>/latest`, retrieved 2026-09-02): `typescript`
7.0.2, `vite` 8.2.2, `vitest` 4.1.11, `@vitest/browser-playwright` 4.1.11, `@playwright/test`
1.62.1, `oxlint` 1.81.0, `oxlint-tsgolint` 7.0.2001, `oxfmt` 0.66.0 — all consistent with the
majors `toolchain.md` and `quality_gates.md` fix (Vite 8, TypeScript 7) where the packet fixes
one, and reflecting the real current line where it does not. `pnpm` is pinned in
`packageManager` at its own current registry `latest`, 11.25.0.

## Decisions this tree had to make that the packet leaves open

**`arch_defaults.md` is language-agnostic and product-level — "One product-level base error
type" (§ Exception shape) — and that rule binds this tree regardless of what any one packet
example happens to show.** `errors_logging.md` gives TypeScript's spelling of the mechanism
(`class <Name>Error extends Error {}`, subclasses set their own `name`) but its own worked
example names a real product's error class, which this tree may not do. Two things below are
this tree's own supplied spelling where arch_defaults.md states the rule and neither file gives a
product-free spelling for it — flagged here rather than presented as doctrine:

- **`AppError` is a placeholder name**, not a spelling either file fixes. `src/app-error.ts` says
  so in its own doc comment.
- **Where the base-error module lives.** `layout.md` § The tree names `src/main.ts` and
  `src/logger.ts` as fixed files but its tree diagram does not list a module for the base error
  type, and does not name `arch_defaults.md`'s Exception shape rule as a Layout concern at all —
  the rule is product-level and binding (arch_defaults.md), but neither file spells out a
  location. This tree placed it at `src/app-error.ts`, following `layout.md`'s own naming rule
  ("one module per file, and the file is named for what it exports") since it is a module the
  whole product shares rather than one area's private type. Flagged in the run report as a
  genuine gap, not a packet-fixed placement.

- **`package.json` `name`.** Not one of the packet's seven concerns — a product's identity, not its
  toolchain — so no packet file fixes it. It carries the substitution token (below) rather than a
  value this tree invented, which is how a concern nobody's doctrine owns still lands correct.

## The placeholder this tree carries

One token, `__PROJECT__`, wherever the product's own name belongs.
`core/launchers/product-skeleton/launcher.sh` replaces it with the project card's `Package slug:`
when it copies this tree — in file contents and in path names alike. It substitutes nothing else,
and that this tree invents no second token is held by `core/tools/test_skeleton_trees.py` rather
than by the launcher: the trees are ours, so the check belongs where they are authored rather than
on the owner's machine at copy time.

**Which token set applies is the consuming script's** —
`core/templates/README.md` § *Adding a script-facing template*, step 2 names all three sets and
states that they never meet. The one not to reach for here is the project stamper's `<project>` /
`<name>` / `<scope>`, which stamps a project's management folder and knows nothing about a
product's code.
