---
version: "1.1.0"
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

Start a container from the official Node image, tagged with CI's Node version, by the command
`languages/README.md` § Gate environment defaults gives. Set pnpm up in it as `toolchain.md`
§ Package manager — pnpm states: `corepack enable`, preceded by `npm install -g corepack` on Node.js
25 or later. Then install the product's dependencies with pnpm before a gate runs.

Browser tests run in a second container, started the same way from Playwright's published image, with
pnpm set up and the dependencies installed in it the same way.

Where `languages/README.md` § Gate environment defaults sends the gates to the macOS guest instead,
that guest is set up as `swift/environment.md` § macOS guest provisioning states.

## In the macOS guest

| Tool | Folder |
|---|---|
| `node` | — |

The image carries it: inside the guest, `command -v node` prints `/opt/homebrew/bin/node`, a folder
on the guest's own PATH. So there is no install step. `node --version` prints `v24.21.0`. That is
the image's Node, not CI's, and nothing holds it to CI's version yet. `tsc` is not in the image; the
product's own dependencies supply it.
