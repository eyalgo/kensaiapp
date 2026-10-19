---
version: "1.1.2"
---

# TypeScript — toolchain

The build system, the package manager, the runtime-version policy, and how a dependency is added,
pinned and locked. Where a file of a given kind goes is `layout.md`. Which checks run over it is
`quality_gates.md`.

## Runtime — the Active LTS line of Node.js

A TypeScript product targets whichever Node.js major is **Active LTS** when it is scaffolded, and
stays on that line until the next major reaches Active LTS. Which major that is changes over time,
by the vendor's own page: "Historically (up to Node.js 26), odd-numbered releases… become
unsupported after six months, and even-numbered releases… move to Active LTS status", but "Starting
with Node.js 27, the release cycle will be annual and every major version will move to LTS status
after its six-month Current phase" (https://nodejs.org/en/about/previous-releases). Node's own
schedule page states the constraint this policy follows — "Production applications should only use
_Active LTS_ or _Maintenance LTS_ releases" — and lists v24 (Krypton) as the Active LTS line, last
updated 2026-08-03 (same page).

The line is written down twice, and both files are committed:

- `.nvmrc` — the major version, read by the developer's version manager.
- `package.json` `engines.node` — the same constraint, read by the installer.

Vite sets a floor under that policy rather than competing with it: "Vite 8 requires Node.js 20.19+,
22.12+" (https://vite.dev/blog/announcing-vite8). An Active LTS line is always at or above that
floor, so the two never disagree.

## Build tool — Vite

Vite is the build tool, and that is the products' choice rather than this packet's:
one product's `docs/proposal.md` § *Recommended Stack* names it in the Build tool row, and a second
product's `docs/product_request.md` § 6 carries the same choice forward.

Vite 8 was released 2026-03-12 and put one Rust toolchain under both dev and build: "Vite 8 ships
with Rolldown as its single, unified, Rust-based bundler", and the same announcement names the three
pieces as "the build tool (Vite), the bundler (Rolldown), and the compiler (Oxc)"
(https://vite.dev/blog/announcing-vite8). That the compiler inside the build is Oxc is the fact
`quality_gates.md` reasons from when it picks a linter and a formatter.

**Vite does not type-check, and a green build is not evidence that the types hold.** "Vite only
performs transpilation on `.ts` files and does **NOT** perform type checking." The vendor's own
guidance covers both contexts this packet's gate runs in, not only a release build: "For production
builds, you can run `tsc --noEmit` in addition to Vite's build command", and "During development…
we recommend running `tsc --noEmit --watch` in a separate process"
(https://vite.dev/guide/features). The type check is therefore a gate of its own — on every change
and in CI alike, per `quality_gates.md` — never something Vite's own build step covers for you.

## Package manager — pnpm

**pnpm is the package manager — the packet author's call, 2026-08-21**, made on one property the
alternatives do not have. pnpm's `node_modules` is not flat: "By default, pnpm uses symlinks to add
only the direct dependencies of the project into the root of the modules directory"
(https://pnpm.io/motivation). The reason to want that: a package the product never declared cannot
be imported, so a phantom dependency fails at the import rather than surviving until an unrelated
lockfile change drops the transitive package that was carrying it.

The pnpm version is pinned in `package.json` `packageManager`, which Corepack reads. Corepack "is
distributed with Node.js from version 14.19.0 up to (but not including) 25.0.0"
(https://github.com/nodejs/corepack), so on the Active LTS line `corepack enable` is the whole
setup, and from Node.js 25 onward Corepack is installed first with `npm install -g corepack`.

## TypeScript — the compiler package

`typescript` is a dev dependency and never a runtime one. TypeScript 7.0 was released 2026-07-08 and
is the same compiler ported to Go — "a native port of TypeScript built in Go"
(https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/).

One consequence of that release binds every tool that reads TypeScript programmatically rather than
through the command line: "While TypeScript 7.0 is here, it does not ship with an API. We expect
TypeScript 7.1 to ship with a new (and different) API" (same announcement). A tool that needs the
6.0 API is installed beside 7.0 under an npm alias, in the announcement's own form
`npm install -D typescript@npm:@typescript/typescript6`. **The gates this packet picks need no such
alias**, which is one of the reasons `quality_gates.md` picks them.

## Adding, pinning and locking a dependency

- **A dependency is added with the package manager, never by hand-editing `package.json`** —
  `pnpm add <package>` for a runtime dependency, `pnpm add -D <package>` for a build- or test-time
  one. A hand edit leaves the lockfile describing a different tree from the manifest.
- **Exactly one lockfile is committed**, and it is `pnpm-lock.yaml`. A second lockfile from another
  manager is a second resolution of the same dependency graph, and nothing keeps the two agreeing.
- **CI installs from the lockfile and fails rather than updating it** —
  `pnpm install --frozen-lockfile`. An install that may rewrite the lockfile makes the build a
  moving target.
- **A version range in `package.json` is carried by the lockfile, not by pinning every entry to an
  exact version.** The range says what the product accepts; the committed lockfile says what it
  actually resolved; a review reads the lockfile diff.
- **A dependency is a decision, and the smallest one is none.** The floor's YAGNI rule
  (`<CORE>/doctrine/engineering/languages/developer_standards.md`) lands in TypeScript as: reach for a platform API
  before a package. `Error` `cause`, `structuredClone`, `AbortController`, `URL` and `Intl` are all
  in the browser these products run in, and each one taken from the platform is a dependency that
  never enters the lockfile.
