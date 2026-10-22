---
version: "1.2.0"
---

# JavaScript — gate environment

Where JavaScript's gates run, how that environment is provisioned, and how it is held to the Node
version the product's CI uses. The defaults every language shares are `languages/README.md` § Gate
environment defaults: the CI runner deciding the environment, the container runtime and its
architecture, a product's override, and the product with no CI. This file restates none of them. The
runtime-version policy is `toolchain.md`'s, and the gates themselves are `quality_gates.md` and
`testing.md`.

## Default and CI alignment

**JavaScript's gates run in a Linux container on the official Node image, at the Node version the
product's CI uses.** That is the owner's ruling of 2026-10-14.

**The image tag is CI's Node version.** The supported floor and the version measured on the owner's
Mac, both in `toolchain.md` § Runtime, are not CI's version, and neither one picks the tag.

**Browser tests run in the published image of the browser-test tool.** This packet names no such tool,
because it holds no browser runtime (`toolchain.md` § Runtime, "Node.js, with no browser runtime in
scope"). A product that writes browser tests runs them in the published image of the tool it chose.

## Provisioning

Start a container from the official Node image, `docker.io/library/node`, tagged with CI's Node
version, by the command `languages/README.md` § Gate environment defaults gives. Nothing is
installed in it before the gates run, because both gates "ship with Node and need no installed
dependency" (`quality_gates.md` § The two gates).

Where `languages/README.md` § Gate environment defaults sends the gates to the macOS guest instead,
that guest is set up as `swift/environment.md` § macOS guest provisioning states.

## In the macOS guest

| Tool | Folder |
|---|---|
| `node` | — |

The image carries it: inside the guest, `command -v node` prints `/opt/homebrew/bin/node`, a folder
on the guest's own PATH. So there is no install step. `node --version` prints `v24.21.0`. That is
the image's Node, not CI's, and nothing holds it to CI's version yet.
