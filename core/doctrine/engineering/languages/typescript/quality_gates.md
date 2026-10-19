---
version: "1.1.0"
---

# TypeScript — quality gates

The three checks a change must pass, each with the command that runs it and the file that configures
it. A rule no tool can fail the build on is not a gate and is not here — it is in `conventions.md`.

## The three gates

| Gate | Tool | Command | Config file |
|---|---|---|---|
| Format | oxfmt | `pnpm exec oxfmt --check` | `.oxfmtrc.json` |
| Lint | oxlint | `pnpm exec oxlint --type-aware --deny-warnings` | `.oxlintrc.json` |
| Types | tsc | `pnpm exec tsc --noEmit` | `tsconfig.json` |

All three run on every change and all three run in CI, in that order — formatting first, because a
reformatting diff mixed into a lint or type fix hides the fix.

The format gate has two forms. `pnpm exec oxfmt` rewrites files and is what a developer runs;
`--check` is the CI form, and what it does is "Check if files are formatted, also show statistics"
(https://oxc.rs/docs/guide/usage/formatter/cli.html). oxfmt finds its configuration by walking up
from each file, looking for `.oxfmtrc.json`, `.oxfmtrc.jsonc`, `oxfmt.config.ts` and
`oxfmt.config.mts` in that order (https://oxc.rs/docs/guide/usage/formatter/config.html); this
packet uses the first, at the repository root.

The lint gate is type-aware, which is not oxlint's default. `--type-aware` turns it on, and the
equivalent in `.oxlintrc.json` is `"options": { "typeAware": true }` — with the vendor's own caveat
that "this requires the oxlint-tsgolint package to be installed"
(https://oxc.rs/docs/guide/usage/linter/config-file-reference.html), so that package is a dev
dependency by default; a project that drops `--type-aware` in its own decision file drops the
package with it, per `languages/README.md` § Precedence. A lint pass that reads only syntax cannot see a
floating promise or a comparison between two types that never overlap, which is most of what this
gate exists to catch.

## Why the Oxc tools rather than ESLint with Prettier

**The packet author's call, 2026-08-21.** ESLint with typescript-eslint and Prettier is the wider
choice in the ecosystem, and this packet does not pick it. Two reasons, both about this stack rather
than about tool quality:

1. **The build already contains Oxc.** Vite 8's own announcement names "the build tool (Vite), the
   bundler (Rolldown), and the compiler (Oxc)" (https://vite.dev/blog/announcing-vite8), and
   `toolchain.md` fixes Vite as the build tool. oxlint is "a high-performance linter for JavaScript
   and TypeScript built on the Oxc compiler stack" (https://oxc.rs/docs/guide/usage/linter.html).
   The reason to prefer that: the parser that decides what the code means in the gate is the parser
   that decides what it means in the build, so the two cannot disagree about a syntax the project
   uses.
2. **Type-aware linting on TypeScript 7 needs no second compiler.** oxlint "leverages the native Go
   port of the TypeScript compiler (tsgo aka TypeScript 7), providing full TypeScript compatibility"
   (https://oxc.rs/docs/guide/usage/linter.html), which is the same compiler `tsc --noEmit` runs.
   typescript-eslint reads TypeScript through its programmatic API, and TypeScript 7.0 "does not
   ship with an API" (https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/) — so
   taking that path today means installing TypeScript 6 alongside 7 under an npm alias
   (`toolchain.md` § TypeScript — the compiler package) and type-checking twice, with two compiler
   versions, against one codebase.

**Choosing oxfmt costs no formatting difference.** oxfmt "matches Prettier's JavaScript formatting",
"passes 100% of Prettier's JavaScript and TypeScript conformance tests", and treats any difference
as a bug (https://oxc.rs/docs/guide/usage/formatter.html). A product that wants Prettier itself gets
byte-identical output and one more process.

A project that takes ESLint with Prettier instead records it as its own decision, and the cost it is
accepting is the second compiler in reason 2 above. `core/doctrine/engineering/languages/README.md`
§ Scope and § Precedence own how that departure is recorded and which of the two then governs.

Two stability facts belong to that same weighing: oxfmt is at `0.64.0`, a 0.x line with no
versioning-stability page of its own (https://oxc.rs/docs/guide/usage/formatter/versioning.md
returns 404, against https://oxc.rs/docs/guide/usage/linter/versioning.md's 200 for oxlint), and
oxlint's own versioning page carves the type-aware mode this gate requires out of its semver
guarantee — listed under *Features Not Subject to Semver* as something that "may introduce breaking
changes at any time, even in patch or minor releases," where "Type-aware rules and their behavior may
change as this feature evolves" (https://oxc.rs/docs/guide/usage/linter/versioning.md).

## `.oxfmtrc.json` and `.oxlintrc.json` — the other two gates' config files

```json
{}
```

**`.oxfmtrc.json` is committed empty.** oxfmt's own README: "No configurations are required"
(https://github.com/oxc-project/oxc/blob/main/npm/oxfmt/README.md) — matching Prettier's output
(§ above) is the default, not an option this packet sets. The file is committed anyway, so a later
option a product does want is a diff against a real file rather than a config nobody wrote down.

```json
{
  "options": { "typeAware": true }
}
```

**`.oxlintrc.json` carries the one option this packet turns on** — the vendor's own equivalent for
`--type-aware`, per § above (https://oxc.rs/docs/guide/usage/linter/config-file-reference.html).
oxlint's own README makes the same "no configurations are required" claim
(https://github.com/oxc-project/oxc/blob/main/npm/oxlint/README.md), so this one line is the whole
departure from its defaults.

## `tsconfig.json` — the compiler options the type gate reads

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "moduleDetection": "force",
    "isolatedModules": true,
    "verbatimModuleSyntax": true,
    "erasableSyntaxOnly": true,
    "noEmit": true,
    "skipLibCheck": true,
    "strict": true,
    "useUnknownInCatchVariables": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  },
  "include": ["src", "tests"]
}
```

Six of those options carry more than their name suggests, and a product that drops one is dropping a
guarantee the rest of this packet assumes:

- **`isolatedModules`** — Vite's own instruction is "You must set `"isolatedModules": true` in your
  tsconfig.json under compilerOptions" (https://vite.dev/guide/features), because its transformer
  works one file at a time with no type information. Without it the type check accepts code the
  build cannot emit.
- **`verbatimModuleSyntax`** — an import is emitted exactly as written, so a type-only import that
  does not say `import type` becomes a real runtime import of a module that may only hold types.
  `conventions.md` states the import form this requires.
- **`erasableSyntaxOnly`** — errors on the TypeScript constructs that have runtime behaviour rather
  than erasing: `enum` declarations, namespaces with runtime code, class parameter properties,
  `import =` and `export =` assignments, and `<prefix>`-style assertions
  (https://www.typescriptlang.org/tsconfig/erasableSyntaxOnly.html). Several rules in
  `conventions.md` are consequences of this option rather than independent preferences.
- **`useUnknownInCatchVariables`** — a caught value is typed `unknown` rather than `any`, so it must
  be narrowed before it is read (https://www.typescriptlang.org/tsconfig/useUnknownInCatchVariables.html).
  `errors_logging.md` builds its catch rule directly on this.
- **`noUncheckedIndexedAccess`** — indexing an array or a record yields `T | undefined`, which is
  what indexing actually does at runtime. Turning it off is choosing not to see the most common
  source of an undefined at runtime in a typed codebase.
- **`noEmit`** — the bundler emits, and `tsc` is here only to check. A `tsc` that also emitted would
  put a second set of build artifacts beside Vite's.

`target` and `lib` name ES2022 because `Error` `cause`, which `errors_logging.md` requires, is part
of it. Raising them is a product's decision; lowering them below ES2022 removes a construct this
packet depends on.

The remaining options each carry a citation rather than a story:

- **`module: "ESNext"`** — "Sets the module system for the program"
  (https://www.typescriptlang.org/tsconfig/module.html), and ESNext is the spelling a bundler that
  resolves ES module syntax itself expects to receive; `moduleResolution` below is the matching
  resolution mode.
- **`moduleResolution: "bundler"`** — the vendor's own words: "'bundler' for use with bundlers... this
  mode supports package.json 'imports' and 'exports', but unlike the Node.js resolution modes,
  `bundler` never requires file extensions on relative paths in imports"
  (https://www.typescriptlang.org/tsconfig/moduleResolution.html). `conventions.md` states the
  extensionless import form this makes valid.
- **`moduleDetection: "force"`** — "Ensures that every non-declaration file is treated as a module"
  (https://www.typescriptlang.org/tsconfig/moduleDetection.html), so a file with no `import` or
  `export` of its own is never silently read as a plain script.
- **`strict`** — "enables a wide range of type checking behavior that results in stronger guarantees
  of program correctness" (https://www.typescriptlang.org/tsconfig/strict.html); this packet takes
  the whole family rather than picking checks by hand.
- **`exactOptionalPropertyTypes`, `noImplicitOverride`, `noImplicitReturns`,
  `noFallthroughCasesInSwitch`, `noUnusedLocals`, `noUnusedParameters`** — five distinct bug shapes
  TypeScript's own reference names one at a time (https://www.typescriptlang.org/tsconfig/): an
  optional property silently widened to include `undefined`, a class override missing the `override`
  keyword, a code path that forgets to return, a `switch` case that falls through unintentionally, and
  a variable or parameter nothing reads. **The packet author's call, 2026-08-21**: each is a real bug
  shape rather than a style preference, so each stays on rather than being picked selectively.
- **`skipLibCheck`** — the vendor's own tradeoff: "This can save time during compilation at the
  expense of type-system accuracy" (https://www.typescriptlang.org/tsconfig/skipLibCheck.html).
  **The packet author's call, 2026-08-21**: this stack does not author its own `.d.ts` files, so the
  accuracy that check buys is over code nobody here wrote.
