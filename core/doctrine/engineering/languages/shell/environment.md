---
version: "1.2.0"
---

# Shell — gate environment

Where shell's gates run, how that environment is provisioned, and how it is held to the distribution
the product's CI runs. The defaults every language shares are `languages/README.md` § Gate environment
defaults: the CI runner deciding the environment, the container runtime and its architecture, a
product's override, and the product with no CI. This file restates none of them. The runtime a shell
file targets is `toolchain.md`'s, and the gates themselves are `quality_gates.md` and `testing.md`.

## Default and CI alignment

**Shell's gates run in a Linux container on the distribution the product's CI runs, at the release CI
runs.** That is the owner's ruling of 2026-10-14.

**The reason is the bash.** The owner's ruling gives it: the Mac's bash is 3.2 and CI's is bash 5, so
a gate run on the Mac runs a different bash from the one CI runs. The Mac's version is measured in
`toolchain.md` § The runtime is bash 3.2, where `/bin/bash --version` prints
`GNU bash, version 3.2.57(1)-release (arm64-apple-darwin25)`.

**The container decides where the gates run, not what a file may use.** `toolchain.md` § The runtime
is bash 3.2, and that is a ceiling rather than a floor, still holds every shell file to what bash 3.2
offers.

## Provisioning

Start a container from the image of CI's distribution, at CI's release, by the command
`languages/README.md` § Gate environment defaults gives. Where CI's distribution is Ubuntu, that
image is `docker.io/library/ubuntu`. This file names no image for any other distribution. The parse
gate needs bash in the image. The suite is written in Python and run with pytest (`testing.md` § The
tool is pytest, and the tests are written in Python), so `python3` and pytest are installed in the
container before the suite runs.

Where `languages/README.md` § Gate environment defaults sends the gates to the macOS guest instead,
that guest is set up as `swift/environment.md` § macOS guest provisioning states.

## In the macOS guest

| Tool | Folder |
|---|---|
| `bash` | — |

The image carries it: inside the guest, `command -v bash` prints `/bin/bash`, a folder on the
guest's own PATH. So there is no install step. It is the Mac's bash 3.2, not CI's bash 5, which the
container default exists to avoid; a product that sends shell's gates to the guest takes that.
