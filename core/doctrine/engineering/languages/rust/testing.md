---
version: "1.0.1"
---

# Rust — testing

Rust's implementation of the layer model in `testing_doctrine.md`: the tool, the file location and
the run command for each layer. The three gates a change must pass are `quality_gates.md`, and none
of the layers below is one of them.

Read `testing_doctrine.md` first. It owns what each layer is, who writes it, and which layers are
optional; this file only says what each one is made of in Rust.

## One runner, and it is Cargo's

Every layer below runs through `cargo test`. Rust ships its test runner with the toolchain, so unlike
the other packets in this family this one picks no framework and adds no dependency for the first
five layers.

## Layers 1–5 — code-time

| Layer | Tool | Location | Run command |
|---|---|---|---|
| 1 — Unit | `cargo test` | `#[cfg(test)] mod tests` inside the module's own file | `cargo test --locked -p <library-crate>` |
| 2 — Integration | `cargo test` | `tests/<area>.rs` in the library crate | `cargo test --locked -p <library-crate> --test <area>` |
| 3 — Application | `cargo test` | `tests/<use_case>.rs` in the library crate | `cargo test --locked -p <library-crate> --test <use_case>` |
| 4 — UI | none — see below | — | — |
| 5 — End-to-end | `cargo test` driving the built executable | `tests/<flow>.rs` in the binary crate | `cargo test --locked -p <binary-crate> --test <flow>` |

**The crate is what separates layer 5 from the rest, and `layout.md` already drew that line.** Layers
1 to 3 live in the library crate and layer 5 lives in the binary crate, so `-p <library-crate>` is the
layers-1-to-3 suite and layer 5 has a command of its own. That is how a Rust product satisfies
`testing_doctrine.md`'s "Layer 5 runs separately" — end-to-end tests are "not part of the layers 1–4
suite" — without a second runner or a naming convention to remember. `cargo test --workspace
--locked` runs every layer at once and is the release-time run rather than the change-time one.

`--locked` is on every command for the reason `quality_gates.md` § Types — the compiler gives: a run
allowed to re-resolve dependencies is a run against a tree nobody reviewed.

## The rules that make that table work

- **Layer 1 lives beside the code and may reach private items.** Unit tests are "Located in the _src_
  directory in each file with the code that they're testing", they "can test private interfaces",
  and the `#[cfg(test)]` annotation "tells Rust to compile and run the test code only when you run
  `cargo test`, not when you run `cargo build`"
  (https://doc.rust-lang.org/book/ch11-03-test-organization.html). So a layer-1 test costs nothing in
  the shipped artifact: "the tests are not included" (same page).
- **Layers 2, 3 and 5 live in `tests/` and see only the public interface.** Integration tests are
  "entirely external to your library and use your code in the same way any other external code
  would, using only the public interface"; they sit in "a _tests_ directory at the top level of the
  project directory, next to _src_"; and "Each file in the _tests_ directory is compiled as an
  individual crate" with no `#[cfg(test)]` needed (same page). One file per area or flow is therefore
  not a filing convention — it is what `--test <name>` addresses.
- **Helpers shared between those files go in `tests/common/mod.rs`.** Files in subdirectories of
  `tests/` "don't get compiled as separate crates or have sections in the test output — they can be
  used as modules by other integration test files" (same page). A helper written as
  `tests/common.rs` instead becomes a test crate of its own that reports zero tests every run.
- **Layer 3 and layer 5 differ by the door, and in Rust the door is visible in the code.**
  `testing_doctrine.md` fixes the distinction — layer 3 "calls the use case in-process, bypassing the
  entry point", layer 5 "enters *outside* it, through the real entry point". A layer-3 file `use`s
  the library crate; a layer-5 file starts the built binary as a subprocess. Cargo hands it the path:
  `CARGO_BIN_EXE_<name>` is "The absolute path to a binary target's executable… only set when
  building an integration test or benchmark", it "may be used with the `env` macro to find the
  executable to run for testing purposes", and "Binaries are automatically built when the test is
  built" (https://doc.rust-lang.org/cargo/reference/environment-variables.html). Hard-coding
  `target/debug/<name>` instead breaks under `--release` and under a workspace's shared output
  directory.
- **Layers 2, 3 and 5 all rest on `layout.md`'s library-first rule.** A binary-only crate cannot be
  reached from `tests/` at all — "we can't create integration tests in the _tests_ directory and
  bring functions defined in the _src/main.rs_ file into scope with a `use` statement"
  (https://doc.rust-lang.org/book/ch11-03-test-organization.html) — so a product that keeps its logic
  in `main.rs` has no layers above unit tests, whatever it writes in its records.
- **Layer 4 has no Rust tool here, and that is `testing_doctrine.md`'s own answer rather than a
  gap.** That file states "Layer 4 is optional, and inapplicable without a UI. A CLI or a library has
  no components", and a Rust crate in this house is one of those two — the one Rust product in this
  galaxy renders nothing in Rust, its renderer being a separate TypeScript unit
  (its `docs/adr/0009-physical-module-set.md` § Decision, where that renderer "is the only unit
  that… renders anything"). A Rust product that does render components records its layer-4 tooling in
  its own `docs/nfdr.md` § 9, and the doctrine's exemption rule is what governs the omission
  otherwise.
- **What is mocked is `testing_doctrine.md`'s table, and the seam is a trait.** The subject stays
  real; the collaborator arrives through the trait `conventions.md` requires, and the test hands it a
  struct implementing that trait. The doctrine's own words for what this is protecting: "A test hands
  the unit a fake through the same door production wires the real one through", and "Where the
  subject offers no door to hand a fake through, the defect is the subject's shape and not the
  test's" (`testing_doctrine.md` § Layers 1–5 — Code-Time (TDD)). **The reason to expect this rule to
  cost less in Rust than elsewhere** is that a unit constructing its own collaborator leaves a test no
  door at all, so the shape the doctrine calls a defect shows up as a test that cannot be written
  rather than as a test that quietly patches its subject.

## Doc tests sit outside the seven layers

`cargo test` also compiles and runs the examples in `///` comments — "Running `cargo test` will run
the code examples in your documentation as tests!", reported under a `Doc-tests` heading
(https://doc.rust-lang.org/book/ch14-02-publishing-to-crates-io.html).

These are not a layer and they do not substitute for one. They exist to keep a public item's stated
contract honest, which is why `conventions.md` requires the example on the item rather than requiring
the test here. A doc test that grows assertions about behaviour has become a layer-1 test written in
the wrong place, and it moves into `#[cfg(test)] mod tests`.

## Layers 6–7 — acceptance-time

Owned by the QA role and written from the design and the specs before code, per
`testing_doctrine.md`, which also says where a project with no active QA role records that.

**Layer 6 runs on `cargo test`, in `tests/architecture.rs`:**

| Layer | Tool | Location | Run command |
|---|---|---|---|
| 6 — Architecture | `cargo test` | `tests/architecture.rs` in the crate whose structure is under test | `cargo test --locked -p <crate> --test architecture` |

The reasoning is the one the TypeScript packet reached on 2026-08-30 and states in
`languages/typescript/testing.md` § Layers 6–7 — acceptance-time: **what** a layer-6 rule says is the
product's and varies, **what runs** the rule is the language's and does not. A layer-6 rule is an
assertion over module structure, `cargo test` runs an assertion, and no second dependency is needed
to get one.

Two Rust facts change what a layer-6 rule has to cover, and both reduce it:

- **A forbidden edge between two crates is already a build failure.** The one Rust product in this
  galaxy reasons from exactly that property — "a forbidden import across a crate boundary is a build
  failure, not a convention" (its `docs/adr/0009-physical-module-set.md` § Consequences) — so a
  layer-6 rule that restates a crate boundary is testing the compiler. The rules worth writing are
  the ones *inside* a crate, between modules, where nothing enforces them.
- **The dependency graph is reportable without a test.** `cargo tree` prints it, and the same product
  uses it as a check that a build-time crate never became a shipped dependency (its `docs/nfdr.md`
  § 1.2, QC-14). A rule a command already answers is stated with that command rather than
  reimplemented as an assertion.

**Layer 7 runs through layer 5's mechanism** — a specification-level scenario enters the product
through its real entry point, which is the built executable a layer-5 test already drives, so the
layer needs no second runner.

**Where the rule itself lives.** The content of a layer-6 or layer-7 rule is the product's, in its
own `docs/nfdr.md`, and the entry there names the layer in its `verified by:` tail. This file says
only what runs it.
