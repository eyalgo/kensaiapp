---
version: "1.1.2"
---

# Rust — toolchain

The build system, the package and dependency manager, the toolchain-version policy, and how a
dependency is added, pinned and locked. Where a file of a given kind goes is `layout.md`. Which
checks run over it is `quality_gates.md`.

## Build system and package manager — Cargo, and there is no second choice to make

Cargo is both, so this packet picks neither. It resolves dependencies, drives the compiler, runs the
tests and reads one manifest for all of it: `Cargo.toml` "is about describing your dependencies in a
broad sense, and is written by you", while `Cargo.lock` "contains exact information about your
dependencies" and "is maintained by Cargo and should not be manually edited"
(https://doc.rust-lang.org/cargo/guide/cargo-toml-vs-cargo-lock.html).

## Toolchain version — `rust-toolchain.toml`, committed

The toolchain a product builds with is written down in the repository rather than left to whatever
each machine has installed. rustup reads a file named `rust-toolchain.toml` in the project's
directory, whose mandatory `[toolchain]` table carries `channel`, and optionally `components`,
`profile` and `targets` (https://rust-lang.github.io/rustup/overrides.html). Overrides in that file
"are also preferred by their proximity to the current directory", so the file at the workspace root
governs every crate under it (same page).

**`components` names the gates rather than assuming them.** `quality_gates.md` runs rustfmt and
Clippy, and rustfmt is added to a toolchain with `rustup component add rustfmt`
(https://github.com/rust-lang/rustfmt). Listing both in `rust-toolchain.toml` `components` is what
makes a fresh checkout able to run the gates without a second instruction.

**A published library also declares `rust-version` in `Cargo.toml`.** That field "tells cargo what
version of the Rust toolchain you support for your package", and "when your package is compiled on
an unsupported toolchain, Cargo will report that as an error to the user"
(https://doc.rust-lang.org/cargo/reference/rust-version.html). The two are different statements: the
toolchain file says what this repository builds with, and `rust-version` says what a consumer may
build with. A product that publishes nothing needs only the first.

## Edition — stated explicitly in every manifest

Each crate chooses its edition in its own `Cargo.toml`, and `cargo new` writes the field in for you.
The field is never omitted, because omission is not a neutral default: "If the `edition` field is not
present in `Cargo.toml`, the 2015 edition is assumed for backwards compatibility"
(https://doc.rust-lang.org/cargo/reference/manifest.html). A manifest with no `edition` line is
therefore a manifest silently pinned to the oldest edition, which is rarely what its author meant.

**A new crate takes the edition `cargo new` fills in**, which is the latest stable one (same page).
This packet names no edition year, so it does not go stale each time a new edition ships. Migrating
an existing crate is that product's decision: editions are opt-in, "crates in one edition **must**
seamlessly interoperate with those compiled with other editions", and the decision "is 'private' —
it won't affect other crates in the ecosystem"
(https://doc.rust-lang.org/edition-guide/editions/index.html).

## A multi-crate product is one Cargo workspace

A workspace is "a collection of one or more packages, called _workspace members_, that are managed
together"; it "shares a common `Cargo.lock` file which resides in the _workspace root_" and all
members "share a common output directory"
(https://doc.rust-lang.org/cargo/reference/workspaces.html). One lockfile across the members is the
reason to reach for it: two crates of one product resolving the same dependency to two versions is
not a possibility the workspace leaves open.

Three workspace-root tables carry what would otherwise be repeated in every member:

- **`[workspace.dependencies]`** — a version is written once at the root, and a member inherits it
  with `regex = { workspace = true, features = ["unicode"] }` or `cc.workspace = true` (same page).
- **`[workspace.lints]`** — the lint levels `quality_gates.md` fixes, written once. **Inheritance is
  opt-in and a member that omits it silently gets none**: the member's own manifest must carry
  `[lints]` with `workspace = true` (same page).
- **`resolver`** — set explicitly at the root, because it "must be set explicitly in virtual
  workspaces as they have no `package.edition` to infer it from" (same page).

## Adding, pinning and locking a dependency

- **A dependency is added with Cargo, never by hand-editing `Cargo.toml`** — `cargo add <crate>` for
  a dependency the product ships, `cargo add --dev <crate>` for a test- or build-time one, which
  adds it "as a development dependency" (https://doc.rust-lang.org/cargo/commands/cargo-add.html).
  A hand edit leaves the manifest and the lockfile describing different trees until the next resolve.
- **`Cargo.lock` is committed.** The Cargo Book's own guidance is "When in doubt, check `Cargo.lock`
  into the version control system", and the problem it names is the one this rule exists for: "we
  want reproducible builds"
  (https://doc.rust-lang.org/cargo/guide/cargo-toml-vs-cargo-lock.html). Committing it is also what
  the one Rust product in this galaxy already does — its constraint record QC-26 reads
  "`Cargo.lock` and `pnpm-lock.yaml` are committed" (its `docs/nfdr.md` § 2. Security, QC-26).
- **CI builds and tests with `--locked`.** The flag "asserts that the exact same dependencies and
  versions are used as when the existing `Cargo.lock` file was originally generated", and Cargo
  "will exit with an error" when the lockfile is missing or would change; the vendor names the
  context directly — "It may be used in environments where deterministic builds are desired, such as
  in CI pipelines" (https://doc.rust-lang.org/cargo/commands/cargo-check.html). Without it a CI run
  is free to resolve a newer dependency than the one anyone reviewed.
- **A version requirement in `Cargo.toml` is a range; the committed `Cargo.lock` is the resolution.**
  The manifest says what the product accepts and the lockfile says what it got, so a dependency
  review reads the lockfile diff rather than the manifest diff.
- **A dependency is a decision, and the smallest one is none.** The floor's YAGNI rule
  (`<CORE>/doctrine/engineering/languages/developer_standards.md`, "YAGNI — implement what is needed now") lands in
  Rust as: reach into `std` before reaching for a crate. This packet names four crates in total —
  `thiserror`, `anyhow`, `log` and `tracing` in `errors_logging.md` — and each is named there with
  the reason it beats writing the same thing by hand.

## Dependency auditing

**`cargo audit` is the packet's dependency-advisory gate, at release** — owner's call, 2026-09-02,
reversing this file's earlier statement that the packet fixed none. The tool, its one filter and the
reason it sits at release rather than per change are `quality_gates.md` § *Dependency advisories*;
what belongs here is only that it is installed rather than shipped with the toolchain, so it is not a
`rust-toolchain.toml` component and not a `Cargo.toml` dependency.
