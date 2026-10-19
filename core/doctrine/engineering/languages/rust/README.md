---
version: "1.1.0"
---

# Rust — packet router

Routes each of the seven language-packet concerns to the file that answers it for Rust, and answers
none of them itself. The concern set, the router rule, the resolution chain, precedence and the
packet lifecycle are one level up, in `languages/README.md`.

## The seven concerns and where each is answered

| Concern | Destination |
|---|---|
| Toolchain | `toolchain.md` |
| Layout | `layout.md` |
| Quality gates | `quality_gates.md` |
| Conventions | `conventions.md` |
| Errors and logging | `errors_logging.md` |
| Testing | `testing.md` |
| Gate environment | `environment.md` |

Each destination is a file in this folder, beside this one.

Every one of the seven refines `<CORE>/doctrine/engineering/languages/developer_standards.md`, the language-agnostic
floor, and none replaces it. A rule the floor states and this packet never mentions is still in force
over Rust code.

## What the registry row claims

`.rs`, and no second extension. Rust has one source extension; `Cargo.toml`, `Cargo.lock`,
`rustfmt.toml`, `clippy.toml` and `rust-toolchain.toml` are the manifests and configuration files
`toolchain.md` and `quality_gates.md` fix, and none of them is Rust source.

**A Rust product is reached by extension inference only once it has source tracked in git.** Step 3 of
`languages/README.md` § The resolution chain infers the language from "the file extensions present
under the working root", so a product at design stage — records written, no crate created — is
reached through step 1 or step 2 instead: its `project.md` `Languages:` line, or the invocation. A
run opening a repository whose only Rust is a `Cargo.toml` should open this packet on that manifest.

## Where this packet's rules come from

No Rust source is tracked in this instance — `git ls-files '*.rs' 'Cargo.toml' 'Cargo.lock'`
returned `0` on 2026-09-02 — so no rule here was read off code in this repository. Each rule instead
names one of three sources in the sentence that states it: the Rust project's own documentation, a
published practice with its URL, or a settled record of a Rust product outside this repository.
Where a call was the packet author's rather than a source's, the sentence says so and gives the
ground.

**A rule here is checked against the first Rust tree this instance writes.** Where that tree
contradicts a rule, the correction lands in this packet, not as a local departure inside the product
— `languages/README.md` § Precedence, which ranks a packet above "the surrounding code's own
habits", is what makes the packet the thing that moves.
