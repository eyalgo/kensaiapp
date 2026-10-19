---
version: "1.1.3"
---

# JavaScript — toolchain

The runtime, the module system, the dependency position, and how a dependency is added. Where a file
of a given kind goes is `layout.md`; which checks run over it is `quality_gates.md`.

## Runtime

Node.js, with no browser runtime in scope — every JavaScript file this packet is derived from is
executed by Node or by Claude Code's Workflow runner. `node --version` returned `v26.0.0` on this
machine on 2026-08-21.

**The supported floor is Node 22.7.0.** That follows from two facts rather than from a preference:
Node 20 is end-of-life (`https://nodejs.org/en/about/previous-releases`), and 22.7.0 is the release
that turns on the one runtime behaviour § Module system depends on. Nothing enforces the floor —
with no `package.json` there is no `engines` field to hold it, so it is a rule a reader applies.

## Module system

ES module syntax, split by half and never both in one file. The workflow scripts
(`.claude/workflows/*.js`) each export exactly one binding and never import:
`grep -c 'import' .claude/workflows/*.js` returns `0` for each, and `grep -c '^export ' .claude/workflows/*.js`
returns `1` for each, 2026-08-21. The test files (`.claude/workflows/tests/*.test.js`) each import
and never export: `grep -c '^import ' .claude/workflows/tests/*.test.js` returns `5` for each, and
`grep -c '^export' .claude/workflows/tests/*.test.js` returns `0` for each, 2026-08-21 — the word
`export` appears in three of them, but only inside a comment, a string or a regex literal, never as a
statement.

**There is no `package.json`, so no `"type"` field declares it.** `git ls-files 'package.json'`
returned nothing on 2026-08-21, and walking every directory from the repo root up to `/` on the same
day found none either. **The test files load as ES modules** because Node inspects ambiguous
input for ES module syntax and treats it as a module when it finds any — on by default since v22.7.0
and v20.19.0 (`https://nodejs.org/api/packages.html` § Syntax detection). That default is what fixes
the floor above.

**The workflow scripts do not load under Node at all.** `node .claude/workflows/run-skill-evals.js`
fails with `SyntaxError: Illegal return statement` (exit 1, run 2026-09-18): `export const meta` forces
ESM detection, and the script also carries a top-level `return`, which an ES module does not permit. They
are run by Claude Code's Workflow runner instead (§ Runtime above), never by Node's module loader —
`testing.md:69-70` states the same fact from the testing side: "A Claude Code Workflow script cannot
be imported: it has top-level `return` and it reads `agent`, `log`, `phase` and `args` as globals its
runner injects."

Node's own documentation names the cost: "Writing ES module syntax in 'ambiguous' files incurs a
performance cost, and therefore it is encouraged that authors be explicit wherever possible" (same
page). This house pays it, because the only way to be explicit is a `package.json`, and a
`package.json` carrying nothing but `"type": "module"` brings the whole dependency apparatus for one
line. **A product adding its first JavaScript dependency adds `package.json` with `"type": "module"`
in the same change** — at that point the explicit declaration costs nothing extra, because the file
has to exist anyway.

## Build system

None. A JavaScript file is executed as written: no bundler, no transpiler, no emitted artifact, no
generated directory.

## Dependencies

**Zero.** On 2026-08-21 `git ls-files 'package.json'` returned nothing, no `package-lock.json`,
`yarn.lock`, `pnpm-lock.yaml` or `bun.lockb` is tracked, and no `node_modules` directory exists
anywhere in the tree. Everything the code needs comes from Node's standard library, imported with the
`node:` prefix (`conventions.md` § Imports and exports).

The package manager, where one becomes necessary, is npm — `npm --version` returned `11.12.1` on this
machine on 2026-08-21.

### Adding one

Reaching outside Node's standard library is a product decision, not an implementation one. It is
recorded in that product's `docs/adr/`, which outranks this packet, and it lands in a single change
as three things:

- `package.json`, carrying `"type": "module"` and an `engines.node` floor;
- the generated lockfile, committed;
- the dependency, pinned to an exact version rather than a range.

No dependency has ever been added in this repository, so that procedure is this authoring run's
reasoning about the shape a first one should take, 2026-08-21, rather than an observed practice.

### The one standing exception

`.claude/hooks/development-bash-approve.py` auto-approves exactly two npm-registry invocations — the
same package at the same pinned version, in two argument shapes — and defers every other `npx` call.
Its reason, at `:166-168`: "`npx <spec>` fetches a package from the registry and executes it — there
is no bounded local behaviour to reason about, only the identity of the code being fetched." The
version is part of the pin for a second reason recorded at `:55-57`: an unpinned specifier "silently
adopts a new format version, which would change what passes the gate below without anyone deciding
to."

That exception is a shell-out to a published tool, not a dependency of any JavaScript file here.
Nothing in the repo imports it.
