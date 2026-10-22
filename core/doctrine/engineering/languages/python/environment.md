---
version: "1.2.0"
---

# Python — gate environment

Where Python's gates run, how that environment is provisioned, and how it is held to the Python
version the product's CI uses. The defaults every language shares are `languages/README.md` § Gate
environment defaults: the CI runner deciding the environment, the container runtime and its
architecture, a product's override, and the product with no CI. This file restates none of them. The
interpreter policy is `toolchain.md`'s, the gates are `quality_gates.md`'s, and the test layers are
`testing_python.md`'s.

## Default and CI alignment

**Python's gates run in a Linux container on the official Python image, at the Python version the
product's CI uses.** That is the owner's ruling of 2026-10-14.

**The image tag is CI's Python version.** The interpreter on the owner's Mac and the supported floor of
Python 3.13, both in `toolchain.md` § Interpreter, are not CI's version, and neither one picks the
tag.

## Provisioning

Start a container from the official Python image, `docker.io/library/python`, tagged with CI's
Python version, by the command `languages/README.md` § Gate environment defaults gives. The compile
gate needs nothing the image lacks, because it ships with the interpreter (`quality_gates.md` § The
two gates). The suite runs pytest (`testing_python.md`, the layer table), so pytest and whatever the
product's code imports are installed in the container before the suite runs.

Where `languages/README.md` § Gate environment defaults sends the gates to the macOS guest instead,
that guest is set up as `swift/environment.md` § macOS guest provisioning states.

## In the macOS guest

| Tool | Folder |
|---|---|
| `python3` | — |

The image carries it: inside the guest, `command -v python3` prints `/usr/bin/python3`, a folder on
the guest's own PATH. So there is no install step. `python3 --version` prints `Python 3.9.6`. That
is the image's Python, not CI's, and nothing holds it to CI's version yet.
