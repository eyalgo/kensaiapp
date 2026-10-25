---
version: "1.9.2"
---

# Gate suite — read the product's evidence, then run the card's command through the tool

**This file is the reading method and the calls, and nothing else.** It owns how a run collects the
facts about a product that decide where its suite runs, the one executable call that issues the suite
there, and the call that asks whether those facts resolve an environment without issuing anything. It owns no packet default: which image or guest a language's gates run in is the
language packet's (`<CORE>/doctrine/engineering/languages/README.md` § Gate environment defaults, and
each `<CORE>/doctrine/engineering/languages/<language>/environment.md`), and which environment those
facts select is the tool's (`<CORE>/tools/gate_suite.py`). A caller points here rather than restating
either.

**Five callers run the suite through this file:** the developer's closing run of the card's test command
(`development-implementation`), the code-integrity run (`development-code-integrity`), the security
run (`development-security`, which keeps a dependency bump or a hole fix only on a green run), the
repair of a red `main` (`dependency-repair`, likewise) and the seal's run (`tobiishi-seal`). Each
passes its own gate name, except the security run and the repair: the tool has no gate of its own for
either yet, so both pass `code-integrity`. Each copies the
`Environment:` lines the tool printed into its own record. The developer and code-integrity runs copy
every one of them. The security run and the repair copy every one as a bullet, never as a bare line. The seal
keeps only the first, as its own skill says. None of them regenerates those lines from the facts it
read.

**Two more read it without running a suite.** The plan (`development-plan`) records the evidence of
Steps 3 and 4 in its instruction, and any run that has to know whether a product owes an environment
decision asks through § *The check — whether the evidence resolves, with nothing run*.

## The result is the tool's, never yours

The tool prints its `Environment:` lines first, one for each environment the call resolved. One
environment gives one line, `Environment: <kind> — <detail>`. When the call resolves several
containers, one for each version the product's Linux CI gives its languages, the tool prints one
`Environment: container — <image>:<tag>, <architecture>` line per container. When the product's CI
runs on both macOS and Linux, the call resolves each of those versions in a container and the
newest of them once more in the macOS guest. For such a call the tool prints each container's line as
above, and one `Environment: macos-guest — <guest name>, toolchain <version>` line for the guest. An environment that was not ready adds one more line for itself: `Environment: not-ready — <detail> — <cause>`, where `<detail>` is the text after `— ` on that environment's own line. The tool prints these lines after every `Environment:` line above and before any suite's output, one for each environment that was not ready, in the order of their environments' lines. They are among the run's `Environment:` lines. An environment is not ready when its packet states no install for it, when an install or the card's dependencies command fails, or when the test command exits 127. Its run counts as status `1`, and it is never a failed suite. Then the tool prints either the suites' output or the reason nothing ran, and exits with the suite's
own status or a nonzero refusal. With several environments, the status is `0` when every
environment's run passed, and otherwise the status of the first one, in the order of the
`Environment:` lines, that did not. **Take the lines and the status from that call and from nowhere
else.** Never write an `Environment:` line from the inputs you built, never infer one from a run you
did not make, and never copy one from an earlier record. A refusal, an environment that cannot be reached before any suite starts, and an environment that was not ready before its test command ran each leave the tool's `Environment:` lines and a nonzero status.
The test command was not run, and no result exists from this run. Never run the card's command by
hand to get one. On a CI that runs on both macOS and Linux, the macOS guest can also fail a check
for one version after the checks made before any suite have passed. The run at that version then
counts as failed with status `1`, and every other environment's run and result stand.

## Step 1 — resolve the paths

Ask the path tool for the change's complete contract, as the calling skill's own entry step does, and
use its `product_worktree` for every read of the product and as the checkout the suite runs in. For
an in-repo product it is the instance worktree; for an external product it is the product's own
worktree, a second repository. Read CI and decision files from it, and the tool runs the card's command there too. The one exception is the product's environment decision, which the tool reads itself from the product's `main` branch, as Step 3's *An environment entry on `main` outranks the worktree's decision* says.

## Step 2 — decide the ask

The owner's Mac is selected in exactly three ways: the product has no CI, the product's decision
files choose it, or **the owner asked**. The owner's ask has two sources, and only these two:

- **A managed walk's launch context.** `KENSAIAPP_GATE_OWNERS_MAC` set to exactly `1` in this run's
  environment. Any other value, and an unset variable, is no ask. The chain sets it only for a walk
  started with the ask, by the owner or by the queue that carries the owner's ask on to the next
  change.
- **The owner's request in the current interactive session**, made in so many words.

**No other source is an ask.** A product decision file, the project card, the sourced input below
and a variable of any other value cannot make one. A decision file that names the owner's Mac is the
product's own decision: Step 3 reads it like any other decision, and the tool obeys it only when its
quoted source holds up and the product's CI can be read. It is not an ask, and it does not let a run
skip Steps 3 to 5.

With the ask, run the second block below and skip Steps 3 to 5; the tool needs no evidence to run
where the owner asked. Without it, go on.

**The tool reads the launch context's ask itself.** `run` with `KENSAIAPP_GATE_OWNERS_MAC` set to
exactly `1` treats the call as the second block, whichever block issued it. It never reads an inputs
file it was given, so even malformed evidence cannot refuse the run. So a run that missed the ask
still lands where the owner asked. A card with no suite still answers `none`, as it does with
`--owners-mac`. The check reads no ask at all. The engine sets or removes the variable on every
launch of a walk, so inside a walk it is the walk's ask and nothing else. Outside a walk it is
whatever the calling shell holds, which is why the interactive request goes through `--owners-mac`
and is never passed by exporting the variable.

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

**The product's decisions.** Read the product's decision files in the product's worktree (`docs/adr/`, `docs/nfdr.md`, `docs/SDD.md`, and any file the product names as its decisions) for a recorded environment for its gates, and for a recorded amd64 requirement. Supply what a decision says, with its file and line, as `decisions.override` (`environment`: `macos-guest`, `container`, `owners-mac` or `neither`, with `image`, `tag` and `architecture` when it gives them) and `decisions.amd64`. Where no decision says anything, supply nothing. Prose that is not a decision is not one.

**An environment entry on `main` outranks the worktree's decision.** At every call, the tool reads § 8 of the product's `docs/nfdr.md` as committed on the `main` branch of the repository that holds the product, in the form § *The environment entry — the one form the tool reads* gives. Where it finds an environment entry there, that entry is the decision, and it replaces any `decisions.override` you supply. Where it finds none, your `decisions.override` is used, exactly as before. That covers no `docs/nfdr.md` on `main`, no § 8 in it, and a § 8 with no environment entry. Collect `decisions.override` from the worktree either way: the tool decides which one applies, not you. Never copy an entry from `main` into `decisions.override` or into a plan's inputs, because the tool reads `main` again at every call. An edit to `docs/nfdr.md` that is not committed on `main` is not read. `decisions.amd64` is read from the worktree only, as before.

**The container candidates.** For each language, read the packet's `environment.md` at
`<CORE>/doctrine/engineering/languages/<language>/environment.md` and take the image it names, with
its source (`root`: `core`). Take the tag from the version CI or the toolchain file states, with
that file and line as `tag_source`; the anchor must contain the tag. A language whose packet names no
container gets a candidate with no `image`. A version you cannot read from a file is no tag: leave it
out and let the tool refuse, and never fill one in from the interpreter on this machine or from
`latest`. A matrix that gives a language several versions gives it one candidate per version, each with its own
`tag_source` quoting the line that states that version. Where one line states several versions, as
`python-version: ["3.11", "3.12", "3.13"]` does, each of those candidates quotes that same line. Never
fold the versions into one candidate, and never leave one out. Where no decision names the
environment, the product's CI runs on Linux only, and the languages call
for one image and each is given the same set of versions, the tool runs the suite once per version,
each in its own container. Where the product's CI runs on both macOS and Linux, and the same holds of
its languages, the tool runs each version in its own container and the newest version once in the
macOS guest. Before any suite runs, it checks that each language's guest tool is at that version in
the guest, and it refuses the run when one is not. The input names no version for the guest: the
tool takes the newest one from the candidates. Where the languages call for more than one
image, or are given different sets of versions, it refuses and says why, on a CI that runs on both
macOS and Linux as on one that runs on Linux only.

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

A matrix that gives python two versions gives two candidates, alike except for `tag`:

```json
"candidates": [{"language": "python", "image": "<the image the packet names>",
                "tag": "3.12",
                "image_source": {"root": "core",
                                 "file": "doctrine/engineering/languages/python/environment.md",
                                 "anchor": "<the line of that file that names the image>"},
                "tag_source": {"file": ".github/workflows/ci.yml",
                               "anchor": "python-version: [\"3.12\", \"3.13\"]"}},
               {"language": "python", "image": "<the image the packet names>",
                "tag": "3.13",
                "image_source": {"root": "core",
                                 "file": "doctrine/engineering/languages/python/environment.md",
                                 "anchor": "<the line of that file that names the image>"},
                "tag_source": {"file": ".github/workflows/ci.yml",
                               "anchor": "python-version: [\"3.12\", \"3.13\"]"}}]
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
`<output file>` and `<error file>` two files outside the tracked tree. Read the run's `Environment:` lines by § *Reading the run's lines*, below, and take the command's exit
status as the run's status. The call reads the environment entry on the product's `main` branch itself, at every run, so it takes no decision-record file.

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
file (never under the owner's ask, which reads none), or a product repository whose `main` branch fails when the tool reads it. Its message is on standard error; correct the input and call again. That is not a refusal and
not a no-suite finding.

## Reading the run's lines

The run's `Environment:` lines are the first lines of the output file. How many there are is read from
the rest of the run's output, never by looking down the output file for the prefix: a suite's own
output can hold a line that begins with `Environment:`, and that line is not the tool's.
Take the first of the three cases below that holds.

- **The output file ends in lines that begin `gate_suite: the run in `.** The run had several
  environments, and each of those lines gives one environment's result. Copy as many lines from the
  top of the output file as there are result lines. Those are the run's `Environment:` lines, in their order. Then, for each result line that ends `neither passed nor failed, because the environment was not ready.`, copy one more line from the top: the tool printed one `Environment: not-ready — …` line for each such environment, directly below the others. Never copy a result line as an `Environment:` line. This case holds even when the
  error file also holds the line the next case names. On a CI that runs on both macOS and Linux, the
  macOS guest can fail a check for its version after the checks made before any suite have passed,
  and the reason given for that version ends with that line.
- **The error file holds the line `The test command was not run, on the owner's Mac or anywhere
  else.`** No suite ran, and the output file holds the tool's `Environment:` lines and nothing else.
  Copy every line of it. When the environment was not ready, the last of those lines is its `Environment: not-ready — …` line.
- **Neither of the two.** The run had one environment. Copy the output file's first line. When the error file holds a line that begins `gate_suite: the environment was not ready for the suite in `, copy the output file's first two lines instead. The second is the `Environment: not-ready — …` line of an environment whose test command exited 127.

## The check — whether the evidence resolves, with nothing run

The check asks the tool what Step 5's call would decide for the same evidence, without the owner's
ask, and starts nothing: no suite, no container, no guest, no probe, and no file written into the
checkout. A run that has to know whether a product owes an environment decision, before any gate runs,
uses the check.

Read the evidence by Steps 1, 3 and 4, with two differences. Never take Step 2's ask: the check always
answers as if no ask were made. And give no guest: `guest` is `null`, because whether the guest runs
and reaches the checkout is a question for the run that issues the suite, not for the check. On a card
reading `Test command: none` the inputs file may hold an empty object, `{}`, and the check answers
without reading it.

Before the call, write three context files outside the tracked tree, beside the inputs file. The check reads all three and runs none of the commands that made them.

1. **The paths file** — the path tool's complete contract for the change, as JSON: the output of
   `python3 "<CORE>/tools/development_path.py" resolve --format json --worktree "<instance change worktree>" --project "<project>" --key "<key>"`.
2. **The tracked-files list** — the output of `git -C "<product root>" ls-files`, one product-relative
   file per line. `<product root>` is the product's own tree: the contract's `product_worktree` joined
   with its `product_path`, or with the part of an absolute `product_path` under `product_repo`. An
   empty list is a valid list.
3. **The decision-record file** — the output of the `record` call below, made with the paths file from item 1. It holds the product's `docs/nfdr.md` as committed on `main` at that moment, or says that `main` holds none. Make it immediately before each check, and never reuse one from an earlier check: a decision committed since then would not be in it.

The `record` call reads the product's repository and changes nothing in it. It starts no suite, no container and no guest. A `record` call that exits `2` could not read the record: its reason is on standard error, and the check is not made until a `record` call succeeds.

```sh
python3 "<CORE>/tools/gate_suite.py" record \
  --worktree "<instance change worktree>" --project "<project>" --key "<key>" \
  --paths "<paths file>" \
  > "<decision-record file>" 2> "<error file>"
```

```sh
python3 "<CORE>/tools/gate_suite.py" check \
  --worktree "<instance change worktree>" --project "<project>" --key "<key>" \
  --inputs "<inputs file>" --paths "<paths file>" --tracked-files "<tracked-files list>" \
  --decision-record "<decision-record file>" \
  > "<output file>" 2> "<error file>"
```

Remove the paths file, the tracked-files list and the decision-record file with the inputs file once the check's output is read.

The first line of the output file is the answer, then ` — ` and a detail:

- `resolves` — the evidence names the environment the gates run in, and the detail names its kind.
  Where the evidence resolves to several containers, one for each version the product's Linux CI
  gives, the detail names every container, in the order the run prints their `Environment:` lines.
  Where the product's CI runs on both macOS and Linux, the detail opens with both kinds, `container`
  and `macos-guest`, in the order those lines first give them. It then names every container and the
  macOS guest at its version, in the order the run prints their `Environment:` lines.
  Exit status `0`.
- `owes a decision` — the product's decision files record no override, its CI's runners are read, and
  the packet defaults still name no environment. The detail names the languages, or the platforms,
  behind the gap. The decision is recorded as an environment entry in § 8 of the product's `docs/nfdr.md`, committed on its `main` branch, where the tool reads it at the next check.
  Exit status `1`.
- `does not resolve` — the evidence names no environment, and the product does not owe a decision: its
  CI cannot be read, a quoted source does not hold up, its decision files name more than one environment, or it already records a decision that names no
  environment the tool can use. The detail is the text Step 5's call prints after
  `Environment: unresolved — `. Exit status `1`.

Tell the two nonzero answers apart by the first line's words, never by the status. A check that exits
`2` could not be made: its reason is on standard error and nothing is on standard output, as for
Step 5's call. **No answer of the check selects an environment or runs a suite.** A gate still runs
only through Step 5's call.

## The environment entry — the one form the tool reads

The product's environment decision is an environment entry in § 8 of its `docs/nfdr.md`: the section whose heading is numbered `8`, as in `## 8. Operational constraints`. This section is the one statement of how that entry is written. The architecture prompt that records the entry points here, and Step 3 reads by it.

§ 8 runs from its heading to the next heading of the same level or a higher one, and its subsections are part of it. An entry anywhere else in the file, § 7 included, is not the decision.

An environment entry is a Markdown list item in § 8 that holds the inline-code field `` `environment: <value>` ``, where `<value>` is `macos-guest`, `container`, `owners-mac` or `neither`. The field may sit anywhere in the item, among the item's own words, its trace and its `verified by:`. The same item may hold three more fields, each in an inline-code span of its own:

- `` `image: <image>` `` — the container's image, without its tag.
- `` `tag: <tag>` `` — the image's tag.
- `` `architecture: arm64` `` or `` `architecture: amd64` ``.

A list item's wrapped lines are part of it, so a field on a continuation line belongs to the item above it. Nothing else declares a decision. A field outside an inline-code span does not, prose or a heading that names an environment does not, and nothing inside a fenced block does, so an example in a fenced block records nothing.

Each of these is one complete environment entry:

```markdown
- **QC-1:** The product's gates run on the owner's Mac — `environment: owners-mac`, the owner's call when the packet defaults did not resolve. Verified by: the gate check answers `resolves`.
```

```markdown
- **QC-2:** The product's gates run in a container — `environment: container`, `image: docker.io/library/python`, `tag: 3.13`, `architecture: arm64`.
```

Several entries that give the same fields with the same values are one decision, whatever their wording and their order. Entries that differ in any field are refused. They differ when the environment, the image, the tag or the architecture differs, and when one gives a field that another leaves out. One item that gives a field twice with two values is refused the same way. The tool then uses none of them, and the check and every gate answer that the product's decision files name more than one environment.

A container entry needs both `image` and `tag`. With either missing, the tool refuses it, because the version to tag the image with cannot be determined. With no `architecture`, the tool chooses one as it does for an override that gives none. An entry naming `neither` records that the product can use neither the macOS guest nor a container, and the tool refuses it, because it names no environment to run in.

The entry is read after the owner's ask and the product's CI. With the owner's ask it is not read at all. With no CI the gates run on the owner's Mac. With a CI that cannot be read, the tool refuses before it reads the entry.

## What stays outside this file

- Which environment a set of facts selects, and every refusal's words: the tool.
- Which image or guest a language runs in, and how it is provisioned: the packet.
- Where each record puts the printed `Environment:` lines, and how a failed or refused run is recorded:
  the calling skill.
- Per-task test runs inside a developer's red and green phases: unchanged, and not routed here.
