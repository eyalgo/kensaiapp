---
version: "1.1.2"
---

# Rust — layout

The source and test tree, where a new file of each kind goes, and how files, modules and packages
are named. What a type, function or variable is called is `conventions.md`. Which test file belongs
to which testing layer is `testing.md` — this file states only where the test tree sits.

## The tree Cargo already fixes

Cargo resolves a package's targets by directory, so most of this layout is the tool's rather than
this packet's (https://doc.rust-lang.org/cargo/guide/project-layout.html):

```
Cargo.toml             the manifest — toolchain.md
Cargo.lock             the committed lockfile — toolchain.md
rust-toolchain.toml    the toolchain channel and its components — toolchain.md
rustfmt.toml           the format gate's config — quality_gates.md
src/                   "Source code goes in the src directory."
  lib.rs               "The default library file is src/lib.rs."
  main.rs              "The default executable file is src/main.rs."
  bin/                 "Other executables can be placed in src/bin/."
tests/                 "Integration tests go in the tests directory."
benches/               "Benchmarks go in the benches directory."
examples/              "Examples go in the examples directory."
target/                build output, ignored and never committed
```

`target/` is the shared output directory a workspace "share[s]"
(https://doc.rust-lang.org/cargo/reference/workspaces.html), and it is a build artifact rather than
source.

## Logic lives in a library crate, and the binary is thin

**A product that ships an executable puts its logic in `src/lib.rs` and leaves `src/main.rs` small.**
This is the one layout rule with a hard consequence attached rather than a preference: "If our
project is a binary crate that only contains a _src/main.rs_ file and doesn't have a _src/lib.rs_
file, we can't create integration tests in the _tests_ directory and bring functions defined in the
_src/main.rs_ file into scope with a `use` statement"
(https://doc.rust-lang.org/book/ch11-03-test-organization.html). The same page names the structure
that follows: "Rust projects that provide a binary have a straightforward _src/main.rs_ file that
calls logic that lives in the _src/lib.rs_ file."

Everything `testing.md` says about layers 2 and 3 rests on this. A binary-only crate has no layer
above unit tests that `cargo test` can reach, so the split is what makes the test model possible
rather than a tidiness argument.

**`src/main.rs` is the composition root** — the only module that names a concrete implementation and
wires it to an abstraction. That is `arch_defaults.md` § Composition Root ("the only place that wires
concrete implementations to abstractions… It owns wiring, not flow"), which is language-agnostic and
reaches Rust directly. The one Rust product in this galaxy already draws its own boundary this way:
its binary crate "is the **composition root**: the one place a concrete implementation is wired to
the Git port" (its `docs/adr/0009-physical-module-set.md` § Decision).

**`src/lib.rs` declares the crate's modules and states its public surface, and holds no
implementation.** It carries `mod` and `pub use` lines and the crate-level `//!` documentation, and
the code lives in the named modules beside it. This is the Rust landing of the floor's rule that a
package's initialization file carries no implementation
(`<CORE>/doctrine/engineering/languages/developer_standards.md`, "`__init__.py` is for package initialization and
public re-exports only — never implementation"). A `lib.rs` that grew a function is the same defect
the floor names, wearing a different filename.

## Where a new module file goes

- **A module declared `mod name;` is the file `src/name.rs`, and a submodule of it is
  `src/name/sub.rs`.** The older `src/name/mod.rs` spelling is available and this packet does not use
  it, for the Book's own stated reason: "The main downside to the style that uses files named
  _mod.rs_ is that your project can end up with many files named _mod.rs_, which can get confusing
  when you have them open in your editor at the same time"
  (https://doc.rust-lang.org/book/ch07-05-separating-modules-into-different-files.html). The same
  page warns against mixing the two — "Using a mix of both styles for different modules in the same
  project is allowed but might be confusing for people navigating your project" — which is what makes
  one spelling per repository the rule rather than a taste.
- **One module per file, and the file is named for what it holds.** A module holding the `FileTree`
  type and the functions over it is `file_tree.rs`.
- **A bounded area is a directory under `src/` with a file of its own beside it**, not a file that
  grows. `src/git.rs` declares the area and `src/git/state.rs` holds a part of it.
- **There is no `utils.rs` and no `helpers.rs`.** The floor rejects generic labels
  (`<CORE>/doctrine/engineering/languages/developer_standards.md`, "no generic labels (`manager`, `handler`,
  `utils`)"), and a module named for no responsibility is where every item nobody placed ends up.
- **A type declared for one module lives in that module.** A `types.rs` is earned only when a type is
  genuinely shared across the area's modules, and then it holds only types.

## A multi-crate product

**Workspace members live under `crates/`, one directory per member.** Owner's call, 2026-09-02, and
the ground is the manifest: the Cargo Book's own workspace example is `members = ["crates/*"]`
(https://doc.rust-lang.org/cargo/reference/workspaces.html), so a member is added by creating a
directory and the root manifest needs no edit. Placing members at the repository root instead makes
`members` a hand-maintained list, and a crate added without the matching list edit builds locally and
is invisible to `cargo test --workspace`.

**This is the packet's answer and the products follow it, including the one whose records said
otherwise first.** At the time this file was written the only Rust product here placed both of its
crates' `tests/` directories at the repository root rather than under `crates/` (its
`docs/nfdr.md` § 9. Test
strategy), and this section recorded that as a standing divergence held open by
`languages/README.md` § Precedence. The owner closed it the other way: the packet's placement is the
house answer, and that product adapts. **§ Precedence is unchanged** — a product's own decision files
still outrank this packet, so a product may still fix a different placement; what is settled is that
no product does so merely because it was written before the packet existed.

**A crate boundary is drawn where a seam has to be enforced rather than reviewed.** Two crates of one
product cannot import each other in a cycle, and a forbidden edge across a crate boundary fails the
build. That is the property the one Rust product here reasons from — "a forbidden import across a
crate boundary is a build failure, not a convention"
(its `docs/adr/0009-physical-module-set.md` § Consequences) — and the same record rejects the
opposite extreme, one crate per part, as "more units than seams". Inside one crate the boundaries are
modules, and `testing.md` layer 6 says what checks them.

## Naming

| What | Case | Source |
|---|---|---|
| Package (`[package] name`) and directory | `kebab-case` | the settled record of the one Rust product here, whose two crates are a `<product>-core` / `<product>-app` pair (its `docs/adr/0009-physical-module-set.md` § Decision) |
| Module, and therefore the `.rs` file holding it | `snake_case` | RFC 430, via https://rust-lang.github.io/api-guidelines/naming.html |

A file's name does not repeat the directory it sits in — `src/git/state.rs`, not
`src/git/git_state.rs`, because the module path a reader sees is already `git::state`.

What a type, trait, function or constant inside those files is called is `conventions.md`.
