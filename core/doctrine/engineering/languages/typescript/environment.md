---
version: "1.3.1"
---

# TypeScript — gate environment

Where TypeScript's gates run, how that environment is provisioned, and how it is held to the Node
version and the browser tooling the product's CI uses. The defaults every language shares are
`languages/README.md` § Gate environment defaults: the CI runner deciding the environment, the
container runtime and its architecture, a product's override, and the product with no CI. This file
restates none of them. The Node line a product targets is `toolchain.md`'s, and the gates themselves
are `quality_gates.md` and `testing.md`.

## Default and CI alignment

**TypeScript's gates run in a Linux container on the official Node image, at the Node version the
product's CI uses.** That is the owner's ruling of 2026-10-14.

**The image tag is CI's Node version.** Which Node line the product targets stays with `toolchain.md`
§ Runtime — the Active LTS line of Node.js. The tag is the version CI runs, not one this file
chooses.

**Browser tests run in Playwright's published image.** That is the owner's ruling of 2026-10-14, read
against `testing.md` § Layers 1–5 — code-time, which names Playwright as layer 5's tool and as the
provider layer 4's Vitest Browser Mode runs on. The image is taken at the Playwright version the
product's CI runs.

## Provisioning

Start a container from the official Node image, `docker.io/library/node`, tagged with CI's Node
version, by the command `languages/README.md` § Gate environment defaults gives. Set pnpm up in it
as `toolchain.md` § Package manager — pnpm states: `corepack enable`, preceded by
`npm install -g --force corepack` on Node.js 25 or later. The container install below does that before a gate runs. Its `COREPACK_ENABLE_DOWNLOAD_PROMPT=0` keeps Corepack from prompting before it downloads pnpm, since no one is there to answer. The product's own dependencies are not this packet's. The product names their install on its project card as its `**Dependencies command:**`, which for a pnpm product is `pnpm install --frozen-lockfile`, and `<CORE>/tools/gate_suite.py` runs it after this install (`languages/README.md` § Gate environment defaults).

**Container install:** `export COREPACK_ENABLE_DOWNLOAD_PROMPT=0 && if [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 25 ]; then npm install -g --force corepack; fi && corepack enable`

Browser tests run in a second container, started the same way from Playwright's published image, with
pnpm set up and the dependencies installed in it the same way.

Where `languages/README.md` § Gate environment defaults sends the gates to the macOS guest instead,
that guest is set up as `swift/environment.md` § macOS guest provisioning states.

## In the macOS guest

| Tool | Folder |
|---|---|
| `node` | — |

The image carries it: inside the guest, `command -v node` prints `/opt/homebrew/bin/node`, a folder
on the guest's own PATH. So node needs no install step in the base. `node --version` prints `v24.21.0`. That is
the image's Node, not CI's, and nothing holds it to CI's version yet. `tsc` is not in the image. The product's own dependencies supply it, through the card's `**Dependencies command:**`.

**pnpm is set up at each run, by the guest install below, the same command as the container's.** The image's Node is 24, below 25, so the line skips the Corepack install there (`toolchain.md` § Package manager — pnpm).

**Guest install:** `export COREPACK_ENABLE_DOWNLOAD_PROMPT=0 && if [ "$(node -p 'process.versions.node.split(".")[0]')" -ge 25 ]; then npm install -g --force corepack; fi && corepack enable`
