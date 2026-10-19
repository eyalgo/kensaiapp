---
version: "1.1.1"
---

# Rust — quality gates

The checks that must pass, each with the command that runs it and the file that configures it. A rule
no tool can fail the build on is not a gate and is not here — it is in `conventions.md`.

## The gates

| Gate | Tool | Command | Config file | When |
|---|---|---|---|---|
| Format | rustfmt | `cargo fmt --all --check` | `rustfmt.toml` | every change |
| Lint | Clippy | `cargo clippy --workspace --all-targets --locked -- -D warnings` | the `[lints]` tables in `Cargo.toml` | every change |
| Types | rustc, through Cargo | `cargo check --workspace --all-targets --locked` | `Cargo.toml` — `edition` and `rust-version` | every change |
| Dependency advisories | cargo-audit | `cargo audit` | none; each silenced advisory is `--ignore <RUSTSEC-id>` with its reason | release |

The first three run on every change and in CI, in that order — formatting first, because a
reformatting diff mixed into a lint or type fix hides the fix. **The fourth runs at release and not
per change**, for the reason § *Dependency advisories* gives: its verdict moves without the tree
moving.

Two of the three ship with the toolchain rather than being installed per product: rustfmt is added
with `rustup component add rustfmt` (https://github.com/rust-lang/rustfmt), and `toolchain.md` puts
both it and Clippy in `rust-toolchain.toml` `components` so a fresh checkout can run these commands.
Nothing here is a dependency in `Cargo.toml`.

## Format — rustfmt

rustfmt is "A tool for formatting Rust code according to style guidelines"
(https://github.com/rust-lang/rustfmt), and the guidelines are its defaults, so a product that
configures nothing is already conforming.

The gate has two forms. `cargo fmt` rewrites files and is what a developer runs; `--check` is the CI
form — "When running with `--check`, rustfmt exits with `0` if no formatting changes would be made,
and `1` if changes are needed" (same page). `--all` extends either form across every member of a
workspace.

**`rustfmt.toml` is committed even when it is empty**, and it carries only the options a product
genuinely departs on. rustfmt "reads settings from a file named `rustfmt.toml` or `.rustfmt.toml`
placed in the project directory or any parent directory" (same page); this packet uses the first
name, at the workspace root. Committing the empty file means a later option is a diff against a real
file rather than a configuration nobody wrote down.

## Lint — Clippy

Clippy is "a collection of lints to catch common mistakes and improve your Rust code"
(https://doc.rust-lang.org/clippy/), and it is the only linter this packet names, because the Rust
project ships it and there is no second one to weigh.

**`-D warnings` is what makes it a gate.** `cargo clippy -- -Dwarnings` is the vendor's own form for
failing on a warning, with its own caveat attached: "Adding `-D warnings` will cause your build to
fail if **any** warnings are found in your code. That includes warnings found by rustc (e.g.
`dead_code`, etc.)" (https://doc.rust-lang.org/clippy/usage.html). `--all-targets` extends the pass
over tests, benches and examples, which are otherwise unlinted code that later gets copied into
product code.

**`clippy::all` is the level this packet takes, and `clippy::pedantic` is not enabled wholesale.**
`clippy::all` is on by default and covers correctness, suspicious, style, complexity and perf, with
`correctness` at `deny` (https://doc.rust-lang.org/clippy/). `pedantic` is allow-by-default, and the
Clippy Book's own advice is to leave it there: "Instead of enabling the whole group (like Clippy
itself does), you may want to cherry-pick lints out of the pedantic group", because "If you enable
this group, expect to also use `#[allow]` attributes generously throughout your code"
(https://doc.rust-lang.org/clippy/lints.html). A gate whose normal operation is adding suppressions
teaches a reader that suppressions are routine, which is the habit that lets a real one through. A
product that wants pedantic lints cherry-picks them by name in its `[lints.clippy]` table.

**`clippy::restriction` is never enabled as a group either.** The same page: "It is **not**
recommended to enable the whole group, but rather cherry-pick lints that are useful for your code
base and your use case", and Clippy "will produce a warning if it finds a
`#![warn(clippy::restriction)]` attribute in your code"
(https://doc.rust-lang.org/clippy/lints.html). Individual restriction lints are enabled by name, and
the same page asks for "a comment justifying that" wherever one is then allowed in a special case.

## Where the lint levels are written

**In `Cargo.toml`, not in an attribute at the top of `lib.rs`.** The `[lints]` section exists to
"override the default level of lints from different tools by assigning them to a new level in a
table", with the levels `forbid`, `deny`, `warn` and `allow`
(https://doc.rust-lang.org/cargo/reference/manifest.html). A level written in the manifest is read by
anyone opening the manifest; the same level written as a crate attribute is discoverable only by
opening the crate root.

In a workspace the levels are written once at the root and inherited:

```toml
# the workspace root Cargo.toml
[workspace.lints.rust]
unsafe_code = "forbid"

# each member's Cargo.toml
[lints]
workspace = true
```

That is the Cargo Book's own worked example, including the lint
(https://doc.rust-lang.org/cargo/reference/workspaces.html). **Inheritance is opt-in**, so a member
whose manifest omits `[lints] workspace = true` gets none of the workspace's levels and reports
nothing about it — `toolchain.md` states the same trap from the manifest's side, and this is where it
costs a gate.

Cargo "only applies these to the current package and not to dependencies"
(https://doc.rust-lang.org/cargo/reference/manifest.html), so a strict level here never breaks a
build over code the product does not own.

**A `clippy.toml` is a different file for a different job, and this packet does not require one.**
Clippy is configurable "via **clippy.toml** file, **[lints] table** in Cargo.toml, [and]
**Attributes**" (https://doc.rust-lang.org/clippy/); the `[lints]` table sets a lint's *level* and
`clippy.toml` sets the *values* individual lints read, such as a threshold. A product that tunes such
a value adds the file at the workspace root; a product that tunes none has nothing to put in it.

**`unsafe_code = "forbid"` is this packet's default, and it is the packet author's call,
2026-09-02.** The ground is that `unsafe` is the one construct in the language whose misuse none of
the three gates above can see: rustfmt formats it, Clippy lints it, and the type checker accepts it
by definition, because `unsafe` is the keyword that tells the compiler to stop checking. The reason
to make the default a refusal rather than a warning is that a warning is satisfied by a suppression
written in the same file, so nothing outside the change ever learns of it. A crate that genuinely
needs `unsafe` — a foreign-function binding is the ordinary case — records why in its own
`docs/adr/`, which outranks this packet per `languages/README.md` § Precedence, and relaxes the level
in its own manifest.

## Types — the compiler

Rust's type checker is the compiler, so the type gate is a compile without code generation.
`cargo check` will "essentially compile the packages without performing the final step of code
generation, which is faster than running `cargo build`"
(https://doc.rust-lang.org/cargo/commands/cargo-check.html).

**The lint gate already runs this check, and the type gate is still listed separately for a reason
worth knowing.** Clippy's `-D warnings` "includes warnings found by rustc"
(https://doc.rust-lang.org/clippy/usage.html), so a green Clippy pass implies a green type pass and a
CI job may run only the two commands it needs. `cargo check` is named here because it is the fast
local loop — the one a developer runs between edits — and because the vendor attaches a limitation to
it that a reader should hold: "Some diagnostics and errors are only emitted during code generation,
so they inherently won't be reported with `cargo check`"
(https://doc.rust-lang.org/cargo/commands/cargo-check.html). A green `cargo check` is therefore not a
statement that the product builds; `cargo build` and the test run in `testing.md` are.

## Dependency advisories — cargo-audit

`cargo audit` will "Audit your dependencies for crates with security vulnerabilities reported to the
RustSec Advisory Database" (https://github.com/rustsec/rustsec/blob/main/cargo-audit/README.md).
Unlike the three gates above it does not ship with the toolchain: it is installed with `cargo install
cargo-audit` (same page), so a product's release procedure installs it rather than assuming it.

**It has no severity threshold.** The one filter the tool offers is `--ignore` against a single
advisory id — `cargo audit --ignore RUSTSEC-2017-0001` (same page) — so an advisory is either fixed
or silenced by name. **A silenced advisory carries its reason beside the id**, in whatever runs the
gate; an `--ignore` with no reason is a suppression nobody can review, and the list only grows.

**It runs at release, not on every change, and the reason is what it audits.** The other three gates
judge what the change wrote, so their verdict moves only when the tree moves. This one judges what
the tree depends on against a database published elsewhere, so a run that was green yesterday fails
today with the tree untouched. On a per-change gate that is a build failing for a reason the change
did not cause; at release it is exactly the question worth asking.

**Owner's call, 2026-09-02.** Until then this packet fixed no dependency-audit gate, on the ground
that the one Rust product here reached for the tool because no packet existed — its `docs/nfdr.md`
§ NFDR Review Notes, RN-7. That product gates its release on it already (the same record's § 10,
QC-27, every advisory with `--ignore <RUSTSEC-id>` and its reason), so adopting it makes the packet
agree with the only evidence there is rather than generalizing past it.

**`--locked` is on every per-change gate command above.** It "asserts that the exact same dependencies and
versions are used as when the existing `Cargo.lock` file was originally generated" and exits with an
error otherwise (same page). A gate that is allowed to re-resolve dependencies is a gate run against
a tree nobody reviewed.
