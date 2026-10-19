# The JavaScript skeleton tree

Copied wholesale by `core/launchers/product-skeleton/launcher.sh` before any
product-specific code exists. This file states what the copy gives a product, what it deliberately
leaves out, and — for every choice — which file of
`core/doctrine/engineering/languages/javascript/` (the JS packet) fixed it, so a reader can check
the tree against that doctrine rather than trust this file's word for it. Citations below quote the
packet verbatim; a filename with no quote is the file this tree ships.

The router (`javascript/README.md`) sends every one of the seven concerns in
`languages/README.md` § *The seven concerns* to a file in the packet's own folder — none is routed to
an outside owner. Six of them fixed a file in this tree, and what follows is organized by that six-way
cut, plus a seventh section for what the job asked for beyond them (composition root, base error
type) and an eighth for the package.json syntax, verified against the vendor rather than the packet.
Gate environment fixed no file here. It decides where a product's gates run, not what the copy
ships.

## 1. Toolchain → `toolchain.md`

**`package.json`** carries `"type": "module"` and `"engines": { "node": ">=22.7.0" }`.

- `"type": "module"` — `toolchain.md` § Module system: workflow scripts here load as ES modules
  under Node's syntax-detection default, but a product's `package.json` states it explicitly once
  the file exists, because "Writing ES module syntax in 'ambiguous' files incurs a performance
  cost, and therefore it is encouraged that authors be explicit wherever possible" (quoted there
  from Node's own docs).
- `"engines": { "node": ">=22.7.0" }` — the runtime floor: "The supported floor is Node 22.7.0"
  (`toolchain.md` § Runtime), and the packet names exactly this gap: "Nothing enforces the floor —
  with no `package.json` there is no `engines` field to hold it, so it is a rule a reader applies"
  (same section). This tree ships the field the packet says would hold it.
- **`"dependencies": {}`, no lockfile.** `toolchain.md` § Dependencies: "Zero" is the observed
  state, and § Adding one names the lockfile as something a product commits "where one becomes
  necessary" — i.e. when the first dependency is added. This tree ships neither because neither is
  necessary yet.
- No bundler, transpiler or build step — `toolchain.md` § Build system: "None. A JavaScript file is
  executed as written."

**Open tension, surfaced rather than resolved (see the delegate report):** `toolchain.md` documents
*this instance's own* current state as "no `package.json`" (§ Module system: "There is no
`package.json`... no `\"type\"` field declares it") and describes a fresh `package.json` as
something a product adds "in the same change" as its **first dependency** (§ Adding one), not
before. This tree ships one anyway, at zero dependencies, because the job that produced this tree
names "the package manifest and its dependency/lock policy" as part of the frame every product
needs regardless. That is this run's resolution of a real disagreement between the packet's
observed practice and the job's mandate — not a doctrine reading either way.

## 2. Layout → `layout.md`, scoped out; `arch_defaults.md` § Package Structure instead

`layout.md` is scoped to **this instance's own tree**, not a product's: "JavaScript in this
instance is Claude Code Workflow scripts, and they live where Claude Code loads them from:
`.claude/workflows/<meta.name>.js`..." (§ The tree). Its "Where a new file goes" table and its
naming rules are keyed to that same tree (workflow scripts, their tests, a shared-helper
subdirectory) and do not describe a general product's package shape.

Per the job's own instruction, a product's package shape is drawn from
`arch_defaults.md` § Package Structure instead: "when the system has 2+ layers with their own
internal files, each module is a package directory... Flat files suit single-file additions or a
small touch inside one module." This skeleton has no modules yet — those are added per-product by
the launcher, one directory per SDD § 3 part — so it ships flat files at the tree root
(`main.js`, `errors.js`) rather than inventing a `src/`-style container no packet or default names.

**Open gap:** neither `layout.md` (instance-scoped) nor `arch_defaults.md` (language-agnostic, no
filenames) names a canonical path or filename for a product's composition root or base-error file
in JavaScript specifically. `main.js` and `errors.js` at the tree root are this run's naming, not a
doctrine-fixed one — see the delegate report.

**Test tree root** is `layout.md`'s explicit disclaimer to `testing.md`: "Where a test file goes...
is `testing.md`'s to state — file location is the Testing concern's" (§ Where a new file goes). See
§5 below.

## 3. Quality gates → `quality_gates.md`

**No formatter, linter or type-checker config ships**, because none is installed and the packet
says so directly: "No formatter, no linter and no type checker runs over JavaScript here... every
one of these tools is an installed package, and this house has no `package.json` to install it
into" (`quality_gates.md` § What is not installed). Per the job's own instruction — "where the
packet is silent, the tree is silent too" — this tree omits the file rather than inventing one.

**The two gates that do run need no config file**, only a command:

| Gate | Command | Where it lives in this tree |
|---|---|---|
| Parse | `node --check <file>` | run per file; no scaffolding needed |
| Suite | `node --test 'tests/*.test.js'` | `package.json` → `scripts.test` |

Both are `quality_gates.md` § The two gates, verbatim for the suite command (adapted from this
instance's own path, `.claude/workflows/tests/*.test.js`, to the product test-tree root `tests/`
that `testing.md`'s generic Layers table names — see §5).

## 4. Conventions → `conventions.md`

No file in `conventions.md` is a gate — "None of them is a gate... every style rule in
`conventions.md` is reader-applied" (§ heading and `quality_gates.md` § What is not installed) — so
nothing here is scaffolded as a config. `main.js` and `errors.js` follow the rules directly:

- No statement-terminating semicolons, two-space indent, single-quoted strings (§ Surface style).
- `const`/named `function` declarations, no `var` (§ Bindings and declarations).
- Named exports only, one per module, no default export (§ Imports and exports) — each of
  `main.js` and `errors.js` exports exactly one binding.
- A `//` header block above the imports, for reasoning "not recoverable from its code" (§ Comments,
  form 3) — used at the top of both files to carry the doctrine citation a reader would otherwise
  have to go find.

## 5. Testing → `testing.md`

**`tests/`** and **`tests/e2e/`** (each a `.gitkeep`-held empty directory) are the test tree root
and its Layer-5 subdirectory, from `testing.md`'s **generic** Layers 1–5 table — not the
instance-scoped override two paragraphs below it. The table itself names `tests/<module>.test.js`
for Layers 1–3 and `tests/e2e/<flow>.test.js` for Layer 5; the sentence "In this instance those
paths resolve to `.claude/workflows/tests/`" is explicitly the instance override, so this tree uses
the table's own paths rather than that override.

- **Layers 1–3** run as one command: `node --test 'tests/*.test.js'` (`testing.md` Layers table),
  captured as `package.json` → `scripts.test`.
- **Layer 5** runs separately: `node --test 'tests/e2e/*.test.js'` (same table, "Layer 5 runs
  separately, per `testing_doctrine.md` § Layers 1–5"), captured as `scripts["test:e2e"]`.
- **Layer 4 (UI)** ships nothing: "none standing — see below... a JavaScript product with a UI
  records its component-test tool in its own `docs/nfdr.md` § 9" (`testing.md` Layers table + § note)
  — a per-product decision, out of frame here.
- **Layers 6–7** ship nothing: "QA-role-owned... a division this file leaves as it found it"
  (`testing.md` § Layers 6–7) — no location this packet fixes, so nothing to scaffold.
- **No test framework config** — `node:test` and `node:assert/strict` are both Node standard
  library, both imported with the `node:` prefix; "No test framework is installed and none is
  needed" (`testing.md` § The tool).

## 6. Errors and logging → `errors_logging.md`, plus `arch_defaults.md` § Exception shape

The job asked for "the single named base error type" as part of the frame. `errors.js` ships
`export class BaseError extends Error`, sourced from two places that pull in different directions —
see the tension noted below.

- **The base-type mandate is `arch_defaults.md`'s, not the JS packet's**: "A single named base. One
  product-level base error type; every typed error derives from it, and none derives directly from
  the language's root error type" (§ Exception shape). `arch_defaults.md` itself says its defaults
  are "drawn on, not applied... binding for a product only when that product's SDD chose a shape
  these serve" — this skeleton ships the type anyway, at the job's direction, ahead of any SDD.
- **`errors_logging.md`'s own observed practice is the opposite of a subclass**: "No `Error`
  subclass, and none is needed until a caller branches on the type. All three throws use a plain
  `Error`" (§ Raising). `BaseError`'s constructor and `{ cause }` support follow that same section's
  raise/wrap shape (`throw new Error(message, { cause: err })`) so a subclass, once a product needs
  one, costs nothing beyond `extends BaseError`.
- **Open tension, surfaced rather than resolved (see the delegate report):** the JS packet's own
  errors doctrine says a base subclass is not needed until a caller branches on type; the
  language-agnostic architecture default says every product wires one in from the start once it
  adopts a layered shape; the job mandates the file exist in the frame regardless. This tree picks
  the mandate; the disagreement between the other two is not this run's to settle.
- **No logger, no JSON output, no level API** ship, because none exist to configure: "There is no
  logger, no JSON output and no level API" (`errors_logging.md` § Emitting) — the level ladder there
  (`HALT`, `⚠`, `✓`, unmarked) is a plain-text convention over `log()`, which is this *instance's*
  injected runner global, not something a product skeleton has standing to ship.

## 7. `.gitignore`

`node_modules/` only. No packet file states a `.gitignore` policy for JavaScript — this is a plain
consequence of `toolchain.md` § Dependencies naming npm as the package manager or where one becomes
necessary, and is otherwise this run's judgment, not a doctrine citation. Flagged in the delegate
report as a packet silence rather than claimed as fixed by any file.

## 8. `package.json` syntax — verified against the vendor, not the packet

The packet fixes *which* fields to set and *why* (§1 above); the *shape* of each field is npm's and
Node's, verified live rather than from recall, per the correction that reached this run mid-task:

- `"type"` — Node's own docs: `"The \"type\" field defines the module format that Node.js uses for
  all .js files that have that package.json file as their nearest parent"`, allowed values
  `"module"` and `"commonjs"` (`https://nodejs.org/api/packages.html`, retrieved 2026-09-02).
- `"engines"` — npm's own docs: `"You can specify the version of node that your stuff works on"`,
  shape `{ "engines": { "node": ">=0.10.3 <15" } }` (`https://docs.npmjs.com/cli/v11/configuring-npm/package-json`,
  retrieved 2026-09-02). This tree's value, `">=22.7.0"`, is the packet's floor (§1 above) in that
  same shape.
- `"scripts"` — npm's own docs: `"a dictionary containing script commands"`, keyed by script name
  (`https://docs.npmjs.com/cli/v11/configuring-npm/package-json`, retrieved 2026-09-02).
- `"dependencies"` — npm's own docs: `"a simple object that maps a package name to a version
  range"` (same page, retrieved 2026-09-02); empty here per §1 above.
- The `node --test` glob invocation — Node's own docs: custom glob patterns are given "as the final
  argument(s)," "enclosed in double quotes to prevent shell expansion" (this tree uses single
  quotes, which a POSIX shell treats identically for this purpose)
  (`https://nodejs.org/api/test.html`, retrieved 2026-09-02) — matches `quality_gates.md` and
  `testing.md`'s own citations of the same command.

No formatter, linter or type-checker config exists to verify against a vendor, because none is
installed (§3 above) — there is no syntax question to check for a file this tree does not ship.

## What this tree deliberately omits, and why

| Omitted | Why | Where it's decided instead |
|---|---|---|
| Formatter / linter / type-checker config | Packet: none installed, all reader-applied | A product's own `docs/adr/` (`quality_gates.md` § What is not installed) |
| Lockfile | Packet: zero dependencies, lockfile committed only once one is added | The change that adds the first dependency (`toolchain.md` § Adding one) |
| `src/`-style module container | No packet or default names one; modules are per-product | The launcher, per the product's SDD § 3 parts table |
| Layer 4 (UI) test tool | Packet: "none standing," needs an installed DOM package | The product's own `docs/nfdr.md` § 9 (`testing.md` Layers table) |
| Layer 6–7 test location | Packet: QA-role-owned, no location fixed here | `testing_doctrine.md` § Layers 6–7, product's `docs/nfdr.md` § 1.2 |
| `.claude/workflows/`-style instance layout | `layout.md` is explicitly this instance's tree, not a product's | N/A — out of scope for a product skeleton |

## Constraints this tree was built under

No `version:` marker — `core/templates/README.md` § *Adding a script-facing template*: a
script-copied template is "content only... Nothing to strip, nothing to unwrap, no frontmatter, no
comment blocks. If it is in the file, it is in the instance." This tree carries exactly one
substitution token (below) and no other instance fact — no host path, no project name, no sibling's
domain — so there is nothing here a copy would have to strip, and it carries no frontmatter of any
kind, including a `version:` one.

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
