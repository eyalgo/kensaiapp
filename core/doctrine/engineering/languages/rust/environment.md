---
version: "1.2.0"
---

# Rust — gate environment

Where Rust's gates run, how that environment is provisioned, and how it is held to the toolchain the
product's CI builds with. The defaults every language shares are `languages/README.md` § Gate
environment defaults: the CI runner deciding the environment, the container runtime and its
architecture, a product's override, and the product with no CI. This file restates none of them. The
toolchain-version policy is `toolchain.md`'s, and the gates themselves are `quality_gates.md` and
`testing.md`.

## Default and CI alignment

**Where the product's CI builds Rust on macOS, Rust's gates run in the macOS guest. Otherwise they run
in a Linux container on the official Rust image.** That is the owner's ruling of 2026-10-14.

**The toolchain is held to CI by the file that already pins it.** The committed `rust-toolchain.toml`
names the toolchain the repository builds with, and its `components` list names the gates' tools
(`toolchain.md` § Toolchain version — `rust-toolchain.toml`, committed). The container's official Rust
image is taken at the toolchain that file names. This answer adds no version or tag of its own.

## Provisioning

- **In the macOS guest:** set up as `swift/environment.md` § macOS guest provisioning states, with
  rustup installed into the base by the step § In the macOS guest names, once a card whose product's
  CI runs on macOS declares Rust. The image carries no Rust.
- **In a Linux container:** start a container from the official Rust image,
  `docker.io/library/rust`, at the toolchain `rust-toolchain.toml` names, by the command
  `languages/README.md` § Gate environment defaults gives.

## In the macOS guest

| Tool | Folder |
|---|---|
| `cargo` | `/Users/admin/.cargo/bin` |

**The base carries rustup and no toolchain.** Install it with the command rustup's own installation
guide gives for this, "first install rustup without a toolchain"
(https://rust-lang.github.io/rustup/installation/index.html):

```sh
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- --default-toolchain none -y
```

`--default-toolchain none` is "Use 'none' to not install any toolchains at all", and `-y` is
"Disable confirmation prompt" (`rustup-init --help`). So the base holds no version of its own, and
the product's committed `rust-toolchain.toml` picks the toolchain and its components, as it does for
the container. rustup installs that toolchain at the first `cargo` a gate runs: `RUSTUP_AUTO_INSTALL`
"(default: 1) When set to 1, installs the active toolchain when it is absent"
(https://rust-lang.github.io/rustup/environment-variables.html). It is installed into the guest, so
a reset erases it and the next gate installs it again.

**The folder is on no PATH a gate gets.** rustup puts its tools in "Cargo's bin directory. On Unix it
is located at $HOME/.cargo/bin" (the installation guide above), and the guest's user is `admin`.
`tart exec` runs a non-login shell whose PATH is `/bin:/usr/bin:/usr/sbin:/usr/local/bin:/opt/homebrew/bin`,
so the profile line the installer writes never reaches it. `<CORE>/tools/gate_suite.py` puts the
folder this table names ahead of that PATH, for its probe and for the suite.
