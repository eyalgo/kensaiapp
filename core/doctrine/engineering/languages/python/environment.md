---
version: "1.5.0"
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
two gates). The suite runs pytest (`testing_python.md`, the layer table), and pytest is not part of Python, so the container install below installs it before the suite runs. The official image runs as root, and pip warns on every install made as root unless its `--root-user-action` option is `ignore` ("Action if pip is run as a root user [warn, ignore] (default: warn)", `pip install --help`). `PIP_ROOT_USER_ACTION=ignore` sets that option. Whatever the product's own code imports is the product's to install. The product names that install on its project card as its `**Dependencies command:**` (`languages/README.md` § Gate environment defaults).

**Container install:** `PIP_ROOT_USER_ACTION=ignore python3 -m pip install --quiet pytest`

Where `languages/README.md` § Gate environment defaults sends the gates to the macOS guest instead,
that guest is set up as `swift/environment.md` § macOS guest provisioning states.

## In the macOS guest

| Tool | Folder |
|---|---|
| `python3` | — |

**Versioned Python folders:** `/opt/homebrew/opt/python@3.11/libexec/bin`, `/opt/homebrew/opt/python@3.12/libexec/bin`, `/opt/homebrew/opt/python@3.13/libexec/bin`, `/opt/homebrew/opt/python@3.14/libexec/bin`

On the guest's own PATH, `command -v python3` prints `/usr/bin/python3`, and `python3 --version`
prints `Python 3.9.6`.

**The base also holds Python 3.11, 3.12, 3.13 and 3.14, from Homebrew.** Install them in the base
with this step, as `swift/environment.md` § macOS guest provisioning step 1 states:

```sh
/opt/homebrew/bin/brew install python@3.11 python@3.12 python@3.13 python@3.14
```

Then reset the guest from the base, as step 5 of that section states.

Homebrew puts an unversioned `python3` for each of those versions in the formula's own
`libexec/bin` folder: "Unversioned and major-versioned symlinks `python`, `python3`, … are installed
into $HOMEBREW_PREFIX/opt/python@3.12/libexec/bin", in the installation caveats of
[python@3.12](https://formulae.brew.sh/formula/python@3.12), and the same for
[python@3.11](https://formulae.brew.sh/formula/python@3.11),
[python@3.13](https://formulae.brew.sh/formula/python@3.13) and
[python@3.14](https://formulae.brew.sh/formula/python@3.14). The `**Versioned Python folders:**` line
names those four folders. After the reset, `python3 --version` in each of them prints
`Python 3.11.17`, `Python 3.12.15`, `Python 3.13.17` and `Python 3.14.9`, in the line's order.

**A gate whose product's CI runs on both macOS and Linux is held to CI's Python version in the
guest.** That gate runs its suite in the guest once, at the newest Python version the product's CI
states. The containers run every version; the guest runs one, because the guest's suites run one at
a time and a run per version made the gate too slow (the owner's call, 2026-10-23). Before any suite
of the gate runs, `<CORE>/tools/gate_suite.py` looks on the guest's own PATH and in the four folders
for a `python3` whose `--version` reports that version, and the guest's suite runs with the
`python3` it found. Where that `python3` is in one of the four folders,
`<CORE>/tools/gate_suite.py` puts the folder ahead of the PATH for that suite alone. A version that
no `python3` there reports, such as 3.15, stops the gate before any suite runs, and the refusal
names that version. No gate installs, links or switches a Python in the guest or in the
base.

**A gate whose product's CI runs on macOS only is not held to CI's Python version.** That gate runs
its suite in the guest once, with the `python3` on the guest's own PATH, `Python 3.9.6`,
whatever version the product's CI states. It makes no version check and never searches the four
folders.

**The guest's own `python3` has no pytest, so the guest install below installs pytest at each run.** Measured 2026-10-23 in `kensai-macos`: `/usr/bin/python3 -c "import pytest"` printed `ModuleNotFoundError`. The install runs with the same `python3` the suite runs with, because `<CORE>/tools/gate_suite.py` puts a version's folder ahead of the PATH for the install as it does for the suite. It adds pytest to that Python, and it installs, links or switches no Python.

The guest's Pythons carry two different pips. Measured 2026-10-23 in `kensai-macos`: `/usr/bin/python3` carries pip 21.2.4, which has no `--break-system-packages` option. The Homebrew Python 3.13 carries pip 26.2.2 and an `EXTERNALLY-MANAGED` marker, which refuses an install unless that option is given ("Allow pip to modify an EXTERNALLY-MANAGED Python installation", `pip install --help`). pip takes each of its options from an environment variable named `PIP_` and the option's name in capitals (https://pip.pypa.io/en/stable/topics/configuration/#environment-variables). So `PIP_BREAK_SYSTEM_PACKAGES=1` gives the option to the pip that has it. On this reading a pip that lacks the option has nothing to take the variable for, so one line serves every Python in the guest. The line installs into the Python itself, as a product's CI does, so a suite that runs with its own `HOME` or with `PYTHONNOUSERSITE=1` still imports pytest. A Homebrew Python takes it there. `/usr/bin/python3`'s own folder is not writable, and its pip says so and installs into the user base instead: "Defaulting to user installation because normal site-packages is not writeable", measured 2026-10-23 in `kensai-macos`. That folder's `bin` is on no PATH a gate gets, so the line puts it, which `python3 -m site --user-base` names, ahead of the PATH. The guest install lands in the running guest and never in the base (`languages/README.md` § Gate environment defaults).

**Guest install:** `PIP_BREAK_SYSTEM_PACKAGES=1 python3 -m pip install --quiet pytest && export PATH="$(python3 -m site --user-base)/bin:$PATH"`
