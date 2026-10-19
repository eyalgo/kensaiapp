---
version: "1.1.1"
---

# Gate suite — read the product's evidence, then run the card's command through the tool

**This file is the reading method and the call, and nothing else.** It owns how a run collects the
facts about a product that decide where its suite runs, and the one executable call that issues the
suite there. It owns no packet default: which image or guest a language's gates run in is the
language packet's (`<CORE>/doctrine/engineering/languages/README.md` § Gate environment defaults, and
each `<CORE>/doctrine/engineering/languages/<language>/environment.md`), and which environment those
facts select is the tool's (`<CORE>/tools/gate_suite.py`). A caller points here rather than restating
either.

**Three callers read this file:** the developer's closing run of the card's test command
(`development-implementation`), the code-integrity run (`development-code-integrity`) and the seal's
run (`tobiishi-seal`). Each passes its own gate name, and each copies the tool's printed first line
into its own record. None of them regenerates that line from the facts it read.

## The result is the tool's, never yours

The tool prints one line first, `Environment: <kind> — <detail>`, then either the suite's output or
the reason nothing ran, and exits with the suite's own status or a nonzero refusal. **Take the line
and the status from that call and from nowhere else.** Never write an `Environment:` line from the
inputs you built, never infer one from a run you did not make, and never copy one from an earlier
record. A refusal and an unreachable environment each leave a first line and a nonzero status: the
test command was not run, and no result exists from this run. Never run the card's command by hand
to get one.

## Step 1 — resolve the paths

Ask the path tool for the change's complete contract, as the calling skill's own entry step does, and
use its `product_worktree` for every read of the product and as the checkout the suite runs in. For
an in-repo product it is the instance worktree; for an external product it is the product's own
worktree, a second repository. Read CI and decision files from it; the tool runs the card's command
there too.

## Step 2 — decide the ask

The owner's Mac is selected in exactly two ways: the product has no CI, or **the owner asked**. The
owner's ask has two sources, and only these two:

- **A managed walk's launch context.** `KENSAIAPP_GATE_OWNERS_MAC` set to exactly `1` in this run's
  environment. Any other value, and an unset variable, is no ask. The chain sets it only for a walk
  its owner started with the ask.
- **The owner's request in the current interactive session**, made in so many words.

**No other source is an ask.** A product decision file, the project card, the sourced input below
and a variable of any other value cannot make one: a record that names the owner's Mac is a refusal
the tool reports, not a request.

With the ask, run the second block below and skip Steps 3 to 5; the tool needs no evidence to run
where the owner asked. Without it, go on.

## Step 3 — read the evidence

Collect source-backed facts into one input file. Write it outside the tracked tree — a temporary
directory made for this run — and remove it when the call returns. Every fact quotes the file it came
from and a line of that file; the tool re-opens each one in the product's checkout (or in `<CORE>`
for a packet) and refuses what the file does not hold.

**Languages.** The card's `Languages:` line, else the invocation's, else leave both empty and the
tool infers from the git-tracked files, exactly as the packet's resolution chain says. Never list a
language from an untracked or ignored file.

**The CI configuration.** Do not work from a list of services or file names; list the repository and
read what is there.

1. Inventory the tracked files. Anything that configures a build service, a pipeline, a runner or a
   workflow is CI: a hosted service's folder or file, a self-hosted one's, a build script that
   names a runner, and every file any of these includes or references.
2. Read every one of them in full, with every referenced configuration, reusable workflow and
   matrix. Record each job's runner. **A matrix is every runner it expands to**, not the first
   entry, and a job with a runner you cannot read is not skipped.
3. Give each runner as `{"platform": ..., "source": {"file": ..., "anchor": ...}}`. The platform is
   `macos` or `linux` when the runner is one of those — an `ubuntu-latest` runner is `linux` — and
   the CI's own words for anything else: the tool reads only those two values as macOS and Linux.
   Another platform than macOS or Linux is a fact to report, never one to drop.
4. **No CI is a finding that needs its evidence.** Write `{"finding": "none", "inventory": "<the
   listing command you ran and what it returned>"}` only after the inventory found no CI
   configuration. Leaving `ci` out, or the inventory, is not that finding: the tool treats it as a
   CI whose runner cannot be read, and refuses.
5. A configuration you could not read — a form you have no name for, a runner a variable supplies —
   is `{"finding": "unreadable", "reason": "<what you could not read>"}`. It is never evidence of
   absence.

**The product's decisions.** Read the product's decision files (`docs/adr/`, `docs/nfdr.md`,
`docs/SDD.md`, and any file the product names as its decisions) for a recorded environment for its
gates, and for a recorded amd64 requirement. Supply what a decision says, with its file and line, as
`decisions.override` (`environment`: `macos-guest`, `container`, `owners-mac` or `neither`, with
`image`, `tag` and `architecture` when it gives them) and `decisions.amd64`. Where no decision says
anything, supply nothing. Prose that is not a decision is not one.

**The container candidates.** For each language, read the packet's `environment.md` at
`<CORE>/doctrine/engineering/languages/<language>/environment.md` and take the image it names, with
its source (`root`: `core`). Take the tag from the version CI or the toolchain file states, with
that file and line as `tag_source`; the anchor must contain the tag. A language whose packet names no
container gets a candidate with no `image`. A version you cannot read from a file is no tag: leave it
out and let the tool refuse, and never fill one in from the interpreter on this machine or from
`latest`. A matrix that gives a language several versions gives it one candidate per version, and the
tool refuses rather than pick one.

**The guest.** When the product's CI runs on macOS, give the guest the host runs: its Tart name and
every share it was started with (`guest.name`, `guest.shares`). Each share is a host folder (`host`,
an absolute path) and the folder it appears at inside the guest (`guest`). Give the same name and the
whole list for every run on the host, whichever instance, project, worktree or core copy the run comes
from. Never give a share made for this run's checkout alone, and never give part of the list. The
host's guest is started by a login job, `~/Library/LaunchAgents/local.kensaiapp.macos-guest.plist`,
and its arguments are the record: the last argument is the guest's name, and each
`--dir=<name>:<host folder>` argument is one share, `{"host": "<host folder>", "guest":
"/Volumes/My Shared Files/<name>"}`.
`<CORE>/doctrine/engineering/languages/swift/environment.md` § macOS guest provisioning says how the
guest and its shares are set up. The tool reads each language's guest tool from that language's
packet, so the input names none. The tool finds this run's checkout inside the guest through the
share that holds it, and refuses a checkout under none of them. If the host has no such job, or no
guest is running, give none: the tool reports the missing guest and starts nothing.

## Step 4 — the shape

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {"finding": "readable",
         "runners": [{"platform": "linux",
                      "source": {"file": ".github/workflows/ci.yml", "anchor": "runs-on: ubuntu-latest"}}]},
  "decisions": {"override": null, "amd64": null},
  "candidates": [{"language": "python", "image": "<the image the packet names>",
                  "tag": "<the version CI states>",
                  "image_source": {"root": "core",
                                   "file": "doctrine/engineering/languages/python/environment.md",
                                   "anchor": "<the line of that file that names the image>"},
                  "tag_source": {"file": ".github/workflows/ci.yml",
                                 "anchor": "<the line of that file that states the version>"}}],
  "guest": null
}
```

A product whose CI runs on macOS gives the guest in place of `null`, with every share the host's guest
was started with:

```json
"guest": {"name": "kensai-macos",
          "shares": [{"host": "<products root>", "guest": "/Volumes/My Shared Files/products"},
                     {"host": "<instance repository>", "guest": "/Volumes/My Shared Files/<instance>"}]}
```

## Step 5 — the call

Fill the placeholders: `<instance change worktree>` is the absolute path of the change's instance
worktree, `<project>` and `<key>` the project and the change key, `<gate>` the calling skill's gate
(`developer`, `code-integrity` or `seal`), `<inputs file>` the file from Step 3, and
`<output file>` and `<error file>` two files outside the tracked tree. Read the first line of the
output file as the `Environment:` line and take the command's exit status as the run's status.

With the evidence:

```sh invocation
python3 "<CORE>/tools/gate_suite.py" run \
  --worktree "<instance change worktree>" --project "<project>" --key "<key>" \
  --gate "<gate>" --inputs "<inputs file>" \
  > "<output file>" 2> "<error file>"
```

With the owner's ask (Step 2), which needs no inputs:

```sh invocation-owners-ask
python3 "<CORE>/tools/gate_suite.py" run \
  --worktree "<instance change worktree>" --project "<project>" --key "<key>" \
  --gate "<gate>" --owners-mac \
  > "<output file>" 2> "<error file>"
```

When the card names no test command, or the seal's product is in its own repository, no evidence is
needed and nothing is probed or run; the tool prints the no-suite line itself:

```sh invocation-no-inputs
python3 "<CORE>/tools/gate_suite.py" run \
  --worktree "<instance change worktree>" --project "<project>" --key "<key>" \
  --gate "<gate>" \
  > "<output file>" 2> "<error file>"
```

A call that exits 2 could not be made — no card, no path contract, an unreadable or malformed input
file. Its message is on standard error; correct the input and call again. That is not a refusal and
not a no-suite finding.

## What stays outside this file

- Which environment a set of facts selects, and every refusal's words: the tool.
- Which image or guest a language runs in, and how it is provisioned: the packet.
- Where each record puts the printed line, and how a failed or refused run is recorded: the calling
  skill.
- Per-task test runs inside a developer's red and green phases: unchanged, and not routed here.
