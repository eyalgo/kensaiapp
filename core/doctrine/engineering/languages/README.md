---
version: "2.8.0"
---

# Language packets — the per-language engineering-practice family

## What this owns

This file owns the language registry, the fixed concern set every packet carries, the gate-environment
defaults every packet shares, the resolution chain a run follows to reach a packet, precedence between
a packet and everything around it, the packet lifecycle, and the audit that keeps a language's router
honest against its folder.

It does **not** own any language's actual practice — that is each packet file's, under its own
`<language>/README.md` router — nor the language-agnostic floor
(`<CORE>/doctrine/engineering/languages/developer_standards.md`), which every packet refines rather than replaces,
nor the testing layer model (`testing_doctrine.md`), which a language's `testing.md` implements.

## The language registry

| Language | Folder | File extensions |
|---|---|---|
| JavaScript | javascript | `.js`, `.mjs`, `.cjs` |
| Python | python | `.py` |
| Rust | rust | `.rs` |
| Shell | shell | `.sh` |
| Swift | swift | `.swift` |
| TypeScript | typescript | `.ts`, `.tsx`, `.mts`, `.cts` |

A language with no row here has no packet: resolution falls through the chain below to the
language-agnostic floor, and the run that reached that point logs it. The registry deliberately
carries no detection-markers column and no status column — detection is extension-based (§ The
resolution chain), and a row's presence already says everything a status column would.

## The seven concerns — fixed, closed

Every packet folder addresses exactly these seven. The set does not grow by adding a language. It
grows only by a decision that re-cuts every packet's router at once, and each file that decision
changes moves its own version (§ Lifecycle, the *Version* bullet). Gate environment, the seventh, was
added by such a decision, the owner's ruling of 2026-10-14.

| Concern | File | It owns | It must not carry |
|---|---|---|---|
| Toolchain | `toolchain.md` | the build system, the package and dependency manager, the runtime-version policy, and how a dependency is added, pinned and locked | where a file of a given kind goes (Layout) or which checks run over it (Quality gates) |
| Layout | `layout.md` | the canonical source and test tree, where a new file of each kind goes, and file and module naming | class, function or variable naming (Conventions) |
| Quality gates | `quality_gates.md` | the formatter, the linter and the type checker — each one's exact invocation and the config file it reads | a rule no tool enforces (Conventions) |
| Conventions | `conventions.md` | naming, the constructs the house prefers and avoids, how each floor rule lands in this language, and, marked as such, what the language itself does with a construct | any command (Quality gates), and how a failure or an event is handled (Errors and logging) |
| Errors and logging | `errors_logging.md` | how this language raises, wraps and propagates a failure, and what it emits as an event — which error or exception type to reach for, structured versus plain output, and the level ladder | a naming or shape rule that is not about a failure or an event (Conventions) |
| Testing | `testing.md` | this language's implementation of the layer model in `testing_doctrine.md` — tool, file location and run command per layer | the pass/fail bar for a gate (Quality gates) |
| Gate environment | `environment.md` | the environment this language's gates run in, how that environment is provisioned, and how it is held to the product's CI toolchain | the runtime-version policy (Toolchain), the tool, file location and run command per layer (Testing), each gate's command and pass bar (Quality gates), and the defaults every language shares (§ Gate environment defaults) |

The line between Quality gates and Conventions is the sharpest cut in the set: **a rule a tool can
fail the build on is a quality gate; a rule only a reader can apply is a convention.** The line
between Conventions and Errors and logging is the same shape at a different seam: **what the code
does at a failure or an event is Errors and logging; how code is named and shaped the rest of the
time is Conventions.**

## The packet router

Each language's folder holds its own `<language>/README.md` — that language's router. **The router
lists all seven concerns by name, always, and gives each exactly one destination: a file in that
folder, a named owner outside the packet, or the floor.** A concern's entry is never absent. A
fixed-arity router cannot have a silent hole — a concern this instance has not written an answer for
still gets a line naming the floor as its destination, so the gap is visible on reading the router
rather than discoverable only by noticing a missing file.

The outside-owner destination is real, not hypothetical: a language whose Testing entry already has
a home elsewhere (an existing per-language testing doctrine that implements `testing_doctrine.md`)
names that file directly and carries no `testing.md` of its own — a file whose whole content would be
a pointer belongs in the router instead.

## The resolution chain

A run resolves a language in four steps, in order, and stops at the first that answers:

1. **`project.md` `Languages:`** — the standing product fact, when the run is on a managed project.
2. **Else the plan or invocation `Languages:`** — the surface behind an owner saying "developer for
   Python."
3. **Else inference from the file extensions present under the working root** — used, and logged in
   the run's own review notes as an inference rather than a declaration. A language is present when
   at least one git-tracked file under the working root carries its registry extension; an untracked
   or ignored file (a `node_modules/` tree, a build output) does not count.
4. **Else no packet** — proceed on `<CORE>/doctrine/engineering/languages/developer_standards.md`, and note that the
   run proceeded on the floor.

**A missing or partial packet is never a STOP.** Every step short of the registry itself degrades to
the language-agnostic floor rather than blocking the run. That is a statement about the **packet's
presence** — what a run does when practice has not been written down — and it is unchanged.

**Resolving the chain is not optional, and the record is owed whatever it returns.** Every run that
writes or reviews code walks these four steps and states in its own output where it landed: the
language, which step answered, and the packet it opened or the floor it fell to. A run that resolved
and found no packet has something to say; a run that never looked has nothing to say; **and the two
must not look the same on disk.** This clause exists because they did — on 2026-08-21 a run read the
instruction, skipped it, recorded nothing, and broke no rule doing so, because every obligation below
was conditional on having taken the branch it describes. This one is conditional on nothing.

**This inverts what this section used to say** — "the chain exists to find practice when it is there,
not to require it" — on the owner's ruling of 2026-08-21, and it spends the argument the family was
accepted on (`docs/proposals/archive/language-packets-v2/rationale.md:179-183`: missing a packet
"degrades rather than misleads … the difference from a skill router, where a missed reference file can
remove a mandated step"). That argument held while the registry was empty. By the ruling, three packets
carried practice a run changes its output by reading, so the family has become the thing that paragraph
contrasted itself against, and the honest move is to say so rather than let a run keep the licence the
empty registry earned it.

## Conflict and polyglot

`project.md` is authoritative for what the product **is**. An invocation may narrow which of the
project's declared languages the current run touches, and an invocation naming a language the
project does not declare is honoured and logged as a divergence rather than refused.

A polyglot project resolves every declared language's packet and applies each one per task, by the
extensions of the files that task touches. A declared language with no packet folder proceeds on the
floor for that language and logs it — the log line is the signal that a packet is worth authoring.

## Precedence

```
project decision files (ADR / NFDR / FDR)   this product's own locked decisions
  ⊃ language packet                          the language's default practice
    ⊃ <CORE>/doctrine/engineering/languages/developer_standards.md   the language-agnostic floor
```

Narrowest owner wins. A packet never overrides the product's own records; a packet refines the floor. This chain
is stated once, here — a packet's own router points at this section and restates none of it.

**A packet also outranks the surrounding code's own habits.** Where a packet's answer and the local
style of the file being edited disagree, the packet wins and the run records that it diverged from the
file — not the reverse. The chain above ranks owners of a *rule*; this ranks a rule against a *habit*,
which nothing here settled before. It matters because the alternative has no floor: a file's existing
style is whatever the last hand left, so deferring to it makes the packet unfalsifiable — a reviewer
comparing code against the file always finds agreement. Splitting a file's style is an acceptable cost
and a recordable one; a rule that cannot be checked is not.

## Gate environment defaults

These defaults hold for every language. Each packet's `environment.md` points at this section and
restates none of it. All of them are the owner's ruling of 2026-10-14. A packet's own answer picks
only its language's guest or image, and states how that one is provisioned and held to CI.

- **The product's CI runner decides the environment.** A product whose CI runs on macOS runs the
  gates of every language it holds in the macOS guest, which `swift/environment.md` § macOS guest
  provisioning sets up. Each language names its own tool there, in its `environment.md` § In the
  macOS guest, and the guest's base carries the tools of the languages the cards declare. A
  language whose packet names no guest tool has no guest default. The section is one table, under
  the heading `## In the macOS guest` written exactly so, with the header row `| Tool | Folder |`
  and one row: the tool in backticks, then either the folder that holds it, in backticks, or `—`
  (an em dash) where the guest's own PATH already reaches it. `<CORE>/tools/gate_suite.py` reads
  that row and no other shape, and reads a packet whose section is written any other way as naming
  no guest tool. A product whose CI runs on
  Linux runs each language's gates in that language's container default, which its
  `environment.md` names.
- **A product's own decision files may override a language's default**, and they outrank every packet
  (§ Precedence). A product that can use neither the language's guest nor its container says so in
  those files. That covers a CI platform that is neither macOS nor Linux, and a language with no
  default for the product's CI platform. No packet gives either case a default.
- **A product with no CI runs its gates on the owner's Mac.**
- **The container runtime is Podman.** On macOS, Podman runs its containers inside a virtual machine
  it manages: "Podman on MacOS and Windows requires a virtual machine"
  (https://docs.podman.io/en/latest/markdown/podman-machine.1.html). `podman machine init` creates
  that machine once, and `podman machine start` starts it before a run.
- **A container runs arm64 by default, and amd64 under emulation when the product asks for it.**
  Podman chooses an image's architecture from the machine it runs on. Its `--arch` option is "use
  ARCH instead of the architecture of the machine for choosing images" (`podman run --help`, Podman
  6.1.3). The owner's Mac is arm64: `/bin/bash --version` prints `arm64-apple-darwin25`
  (`shell/toolchain.md` § The runtime is bash 3.2). A product that asks for amd64 adds
  `--arch amd64`.

A gate runs in a container started from the product's checkout root. `<image>` is the image the
language's `environment.md` names. `<gate command>` is a command from that language's Quality gates
or Testing answer.

```sh
podman run --rm -v "$PWD":/work -w /work <image> <gate command>
```

"If the image is not already loaded then podman run will pull the image"
(https://docs.podman.io/en/latest/markdown/podman-run.1.html). `-v` mounts the checkout into the
container, and `-w` makes it the working directory. `--rm` removes the container when the gate exits.

## Lifecycle

- **Add a language** — create `languages/<language>/`, write its `README.md` naming all seven
  concerns, write the files whose answers already exist, and add the registry row above — all in one
  commit. A row and its folder travel together; neither lands without the other.
- **Add a concern's answer later** — write the file, and change that concern's entry in the
  language's router from its outside owner or the floor to the new file, in one commit.
- **Version** — every file under a language's packet is doctrine, so each carries its own
  frontmatter `version:` per `versioning.md`, moved independently of its siblings.
- **Scope** — core only. A project's deviation from a packet's default belongs in that project's own
  ADR, which outranks the packet (§ Precedence). An instance-level overlay is a later decision, made
  only once an instance-specific practice fact actually exists.

## Audit

Three diffs against disk keep a language's router honest against its folder. Run each from the repo
root. Each is one command, in a fenced block rather than an inline span, because a command holding a
backtick cannot survive a code span — the span closes on it, and what a reader copies out is a
fragment that will not parse.

1. **A registry row with no folder.** For each row's Folder column, confirm the folder exists:

   ```sh
   awk -F'|' '/^## /{r = /registry/} r && /^\| / && $2 !~ /Language/ && $3 !~ /^ *-+ *$/ {gsub(/ /,"",$3); print $3}' core/doctrine/engineering/languages/README.md |
     while read -r f; do [ -d "core/doctrine/engineering/languages/$f" ] || echo "row with no folder: $f"; done
   ```

2. **A folder with no registry row.** Diff the folders on disk against the registry's Folder column:

   ```sh
   { awk -F'|' '/^## /{r = /registry/} r && /^\| / && $2 !~ /Language/ && $3 !~ /^ *-+ *$/ {gsub(/ /,"",$3); print $3; print $3}' core/doctrine/engineering/languages/README.md
     find core/doctrine/engineering/languages -mindepth 1 -maxdepth 1 -type d -exec basename {} \; ; } | sort | uniq -u
   ```

3. **A `.md` file in a language folder that its router does not name.** Diff the folder's files
   against the names its `README.md` router carries — substitute the folder for `<language>`:

   ```sh
   { awk -F'|' '/^\| /{print $3}' core/doctrine/engineering/languages/<language>/README.md | grep -oE '[a-z_]+\.md' | sort -u | sed p
     find core/doctrine/engineering/languages/<language> -maxdepth 1 -name '*.md' ! -name README.md -exec basename {} \; ; } | sort | uniq -u
   ```

Two things the awk in checks 1 and 2 has to get right, and both are load-bearing. It tracks the
current `##` heading so it reads **only** the registry table — this file carries a second table, the
seven concerns, whose rows have the same leading-pipe shape, and a pattern keyed on that shape alone
reads eight concern rows as registry rows, the header and all seven. And it drops the header and separator rows, whose Folder
column holds `Folder` and `---`. A check that reports findings against a correct tree is worse than
no check: the first reader learns to skip it, and every reader after inherits the habit.

**Checks 2 and 3 are set differences, and neither uses process substitution.** `comm -23 <(…) <(…)`
is the obvious spelling and it is the one a sandboxed run cannot execute: a worktree-isolated agent's
Bash is refused when the command's reach cannot be established statically, and a subshell cannot be.
Measured 2026-09-02, when a delegated run authoring the Rust packet was refused both commands and had
to write them into a file to run them at all — the check survived only because that run bothered.
What replaces it needs no subshell: each side prints, the registry side twice (`print $3; print $3`
in check 2, `sed p` in check 3), and `sort | uniq -u` keeps the names that appear exactly once, which
are the ones on the first side and not the second. `comm`'s answer, without the fork.

Neither `find` here uses `-printf`. It is a GNU extension, absent from the BSD `find` on macOS,
where it fails the whole command with `unknown primary or operator` — and a check that silently
produces nothing looks exactly like a check that passes.

**Check 3's router side is the Destination column, not the file.** A `grep` over the whole router
counts a filename appearing anywhere in its prose as a routed destination, which is the one failure
this check exists to catch — a file nothing points at, passing because something merely mentions it.
Measured 2026-08-21, before this scoping: the whole-file form harvested `testing.md` from python's
router, a name that router does not route and that folder does not hold, plus `standards.md` and
`adr/` from all three and `product_request.md` and `proposal.md` from TypeScript's.

**The third is the dangerous one.** A router naming a file that does not exist fails loudly the
moment anything opens it; a file the router omits is silently unreachable — nothing ever points at
it, and nothing ever complains that nothing does.
