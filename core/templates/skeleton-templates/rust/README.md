# Rust skeleton tree

What a copy of this tree gives a Rust product, what it deliberately leaves out, and — per file —
which of the Rust language packet's six destination files fixed the choice (`toolchain.md`,
`layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `testing.md`). Every claim
below was checked against the cited file this session; where a claim is about the vendor's own syntax
rather than this house's policy, the citation is the vendor's own page plus the date it was retrieved
(2026-09-02).

This tree carries no `version:` marker — it is a script-copied shape, not a doctrine file: the
governing rule is that a script-read template is the file itself, content only, with nothing that
must not survive the copy (its own home's README, § *Adding a script-facing template*, step 3).

## The `__PROJECT__` token

`crates/__PROJECT__/` and the `name = "__PROJECT__"` line in its manifest carry the literal token, not
an invented crate name. `core/launchers/product-skeleton/launcher.sh` substitutes it from the project
card's `Package slug:` field when it copies this tree — in path names as well as in file contents,
which is why the directory itself is spelled that way. It substitutes nothing else, and that this
tree invents no second token is held by `core/tools/test_skeleton_trees.py` rather than by the
launcher. Where a member's name would be the product name plus a suffix (a second crate under
`crates/`), it is written the same way: the token plus the suffix, e.g. `__PROJECT__-core`, never a
spelled-out name.

**Which token set applies is the consuming script's** —
`core/templates/README.md` § *Adding a script-facing template*, step 2 names all three sets and
states that they never meet. The one not to reach for here is the project stamper's `<project>` /
`<name>` / `<scope>`, which stamps a project's management folder and knows nothing about a
product's code.

This tree is why the three are spelled differently: the token is a **directory name** here, and
Windows forbids `<` and `>` in a filename, so `crates/<project>/` could not be checked out at all.

## What is here, and which packet file fixed it

| File | What it is | Fixed by |
|---|---|---|
| `Cargo.toml` (root) | the workspace's root manifest — a **virtual manifest** (a `[workspace]` table and no `[package]` table) | `toolchain.md` — Cargo "is both" the build system and the dependency manager (`toolchain.md:13`); `resolver` is set explicitly because a virtual workspace "must be set explicitly... as they have no `package.edition` to infer it from" (`toolchain.md:71-72`, quoting https://doc.rust-lang.org/cargo/reference/workspaces.html, verified against that page 2026-09-02) |
| `Cargo.toml` (root) `[workspace.lints.rust] unsafe_code = "forbid"` | the one lint level the packet fixes | `quality_gates.md:90,113` — "this packet's default, and it is the packet author's call, 2026-09-02" |
| `rust-toolchain.toml` | the committed toolchain channel, with the two components the quality gates need | `toolchain.md:28` — "`components` names the gates rather than assuming them... Listing both in `rust-toolchain.toml` `components` is what makes a fresh checkout able to run the gates without a second instruction" |
| `rustfmt.toml` | the format gate's config, committed empty | `quality_gates.md:40` — "`rustfmt.toml` is committed even when it is empty, and it carries only the options a product genuinely departs on" |
| `.gitignore` | ignores the one directory Cargo itself produces | `layout.md:28` — "`target/` build output, ignored and never committed" |
| `crates/__PROJECT__/Cargo.toml` | the workspace's one starting member | `layout.md:88` — "Workspace members live under `crates/`, one directory per member" |
| `crates/__PROJECT__/src/lib.rs` | declares the crate's module(s) and public surface, no implementation | `layout.md:57` — "`src/lib.rs` declares the crate's modules and states its public surface, and holds no implementation" |
| `crates/__PROJECT__/src/error.rs` | the single named base error type | `arch_defaults.md:63-68` (product-level rule) + `errors_logging.md:29,34-41` (Rust spelling) — below |
| `crates/__PROJECT__/src/main.rs` | the composition root | `arch_defaults.md:53-55` (product-level rule) + `layout.md:50-51` (Rust spelling) — below |

No `Cargo.lock` and no `clippy.toml` are in this tree. Why, below.

## The four quality gates this tree wires

Each is `quality_gates.md`'s, verbatim:

| Gate | Command | Config in this tree |
|---|---|---|
| Format | `cargo fmt --all --check` | `rustfmt.toml` |
| Lint | `cargo clippy --workspace --all-targets --locked -- -D warnings` | `[workspace.lints.rust]` in the root `Cargo.toml`, inherited by `crates/__PROJECT__` via its own `[lints] workspace = true` |
| Types | `cargo check --workspace --all-targets --locked` | `crates/__PROJECT__/Cargo.toml` — `edition` |
| Dependency advisories | `cargo audit` | none — `quality_gates.md:147`, "It has no severity threshold... a silenced advisory carries its reason beside the id"; run at release, per `quality_gates.md:142-149` |

`--locked` on every per-change command asserts the committed lockfile is what actually gets built
against (`toolchain.md:80`, quoting the Cargo Book's guidance to commit `Cargo.lock`, "we want
reproducible builds").

## Why no `Cargo.lock` ships

A lockfile records the dependency graph Cargo's resolver actually chose — exact versions and registry
checksums — and that can only be produced by running the resolver, which this run had no `cargo`
binary to do (`which cargo` returned nothing this session). Writing one by hand would mean guessing
checksums this run cannot verify against the registry, which is the fabrication `cite it or don't say
it` exists to catch. `toolchain.md:80`'s "`Cargo.lock` is committed" is honored the ordinary way
instead: the first `cargo build` after this tree is copied generates it, and it is committed
immediately after, before any other change — the same bootstrap sequence `cargo new` itself leaves to
its caller.

`thiserror = "2.0.20"` and `anyhow = "1.0.104"` in `crates/__PROJECT__/Cargo.toml` are the current
published versions on docs.rs, retrieved 2026-09-02 (https://docs.rs/thiserror,
https://docs.rs/anyhow) — real version constraints, not guessed ones, even though no lockfile pins the
resolution yet.

## Workspace, not a single crate — the one shape question this language forces, and it is not fully settled

`layout.md`'s literal default tree (`layout.md:16-29`) is a **single** crate — `Cargo.toml`,
`src/lib.rs`, `src/main.rs` at the repository root, no `crates/` folder — and treats a workspace as an
opt-in, reached only once "A multi-crate product" needs it (`layout.md:88` section heading and body).
`arch_defaults.md` § *Package Structure* is the product-level rule that governs this
(`arch_defaults.md:30-32`): "when the system has 2+ layers with their own internal files, each module
is a package directory... not a flat file" — but that rule is about a **module** growing into a
directory inside one crate (which `layout.md`'s own "A bounded area is a directory under `src/`" rule
already spells for Rust, `layout.md:78`), not about whether the **whole product** is one crate or
several. Neither source fixes workspace-versus-single-crate as the tree's starting shape.

**This tree starts as a workspace, with one member (`crates/__PROJECT__/`), rather than a single crate
at the root.** The reasoning, and it is this run's own call rather than a packet answer:

- The SDD § 3 parts table's `Lives in` column can name either a module or a crate per part, decided
  per product, and the launcher this job describes is mechanical — it "creates per-part directories
  under whatever this tree establishes" (this run's own job brief, quoting the station's framing). A
  launcher that only creates directories cannot also convert a single-crate root into a workspace root
  when a product's parts turn out to be crates.
- Starting as a workspace makes both cases the same mechanical operation: a module-only product stays
  at one crate under `crates/`; a multi-crate product adds more, each `crates/__PROJECT__-<part>/`.
  Neither requires touching a file this tree already wrote. Starting single-crate-at-root would work
  for the module-only case for free, but converting to a workspace once a product turns out to need
  multiple crates means moving `Cargo.toml`, `src/lib.rs` and `src/main.rs` into a new
  `crates/__PROJECT__/` and turning the root manifest into a virtual one — exactly the rewrite the brief
  asked this run to avoid forcing.

**This is presented as this run's judgment, not as something either doctrine source settled** — see
the run report's *Surfaced, not settled* section.

## The composition root and the base error type

Both are **product-level** rules from `arch_defaults.md`, given their Rust spelling by the packet, per
this run's second correction: a product-level rule from `arch_defaults.md` binds this tree regardless
of what the packet's own code (measured over this instance, not a product) does, and where the packet
gives it a language spelling, that spelling is used rather than one this run invents.

- **Composition root** — `arch_defaults.md:53-55` (§ *Composition Root*): "the only place that wires
  concrete implementations to abstractions… It owns wiring, not flow." Rust spelling —
  `layout.md:50-51`: "`src/main.rs` is the composition root — the only module that names a concrete
  implementation and wires it to an abstraction." `crates/__PROJECT__/src/main.rs` is that file, empty
  of wiring because no product exists to wire yet, returning `anyhow::Result<()>` per
  `errors_logging.md:61-64` ("A binary crate propagates with `anyhow` and adds context on the way
  up").
- **Base error type** — `arch_defaults.md:63-68` (§ *Exception shape*): "A single named base… every
  typed error derives from it" and "One type per distinct condition… because callers map types to
  distinct outputs… and cannot map a string." Rust spelling — `errors_logging.md:29`: "A library crate
  defines one error type, with one variant per condition," and `errors_logging.md:34,39-41`: "That enum
  implements `std::error::Error`… `thiserror` writes those implementations." `crates/__PROJECT__/src/error.rs`
  is that type: zero variants today, because no failure condition exists yet to name one for — a
  developer adds a variant per condition as the product grows, per the pattern already commented in
  the file.

## What this tree deliberately omits, and why

- **`clippy.toml`** — `quality_gates.md`'s own words: "this packet does not require one." A product
  that tunes a Clippy lint's threshold value (not its level) adds the file at the workspace root.
- **`[workspace.dependencies]`** — the packet fixes no product dependency beyond the two crate-kind
  choices already wired above (`errors_logging.md`). A product adds shared version pins here once it
  has more than one crate sharing a dependency, per `toolchain.md`'s own worked example.
- **A `log` vs `tracing` choice** — `errors_logging.md`'s own words: "Either. The packet fixes no
  default; the product chooses and records the choice in its own `docs/nfdr.md`"
  (`errors_logging.md:118`). Neither crate is added here because there is nothing to choose yet.
- **Layer 4 (UI) testing tooling** — `testing.md:74`'s own answer: "optional, and inapplicable without
  a UI. A CLI or a library has no components." No product exists yet to have or lack one.
- **Layer 6/7 acceptance scaffolding** (`tests/architecture.rs`) — `testing.md:135`'s own words: "The
  content of a layer-6 or layer-7 rule is the product's." Nothing to assert over yet.
- **`rust-version` in the manifest** — `toolchain.md:33` scopes this to "a published library"; this
  tree does not know whether the product publishes one.
- **`tests/` directory** — `testing.md`'s layers 2, 3 and 5 live in `tests/` beside `src/`
  (`testing.md`'s own table), but every file there is named for a specific area, use case or flow the
  product has not written yet. `layer 1` unit tests already have their home, `#[cfg(test)] mod tests`
  inside the module they test, which is where the first one lands once `src/` holds real logic.

## Naming, once more code exists

`conventions.md`'s casing table and `layout.md`'s naming table govern every file a developer or the
launcher adds under `crates/__PROJECT__/src/` — `snake_case` modules and functions, `UpperCamelCase`
types and traits, `kebab-case` for a package/directory name (`layout.md:116-117`), which is why a
second crate's directory is `__PROJECT__-<part>` rather than `__PROJECT___<part>`.

## The one value here the packet deliberately refuses to fix

`crates/__PROJECT__/Cargo.toml` pins `edition = "2024"`, and the packet's toolchain destination
names no edition year on purpose — so that it does not go stale each time a new edition ships.

This tree cannot follow that. `cargo new` asks the installed toolchain what the current edition is;
a copied file has nobody to ask, and Cargo refuses a `[package]` with no edition at all. So a value
had to be written, and a written value is the thing the packet was avoiding.

**What follows from that, for whoever reads this next.** The pin is this tree's, not doctrine's, and
it is the one line here that goes stale on its own. When a new Rust edition ships, this file is
where to change it, and nothing will fail loudly in the meantime — a product stamped from this tree
simply starts one edition behind. If that becomes a recurring cost, the fix is not a better guess
here: it is for the launcher to read the edition from the toolchain at copy time, which would make
this tree behave the way `cargo new` does.

## Where a part from the SDD lands

**`members` is the glob `crates/*`** (`Cargo.toml`), because `layout.md` § A multi-crate product
requires it: a member is added by creating a directory, and the root manifest needs no edit. The cost
of a glob is that everything it matches must be a crate. Cargo checks that every member exists as a
manifest and errors when one does not: *"Cargo proactively checks the existence of `Cargo.toml` to
include a member, and throws an error if `Cargo.toml` doesn't exist, which makes globbing patterns
like `**/*` often invalid"* (<https://github.com/rust-lang/cargo/issues/11988>, read 2026-09-02).
So nothing may land directly under `crates/` without a manifest.

**When the SDD § 3 carries a units table**, each `crate` unit is copied from
`crates/__PROJECT__/` to the unit's own path, manifest included, and the glob picks it up.

**When it carries none**, the launcher creates one empty directory per part, placed by that row's
`Lives in`. An empty directory is inert in every other language, but under `crates/` it is a member
with no manifest, and the workspace stops building. So a part is a module inside this crate: write
its `Lives in` as `crates/__PROJECT__/src`, and the part lands at `crates/<slug>/src/<part>/`, a
module the crate's own `lib.rs` declares. Making a part its own crate is then the product's move: a
manifest and a source root under `crates/`, which the glob includes with no edit to `members`.
