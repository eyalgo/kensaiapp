---
version: "1.1.1"
---

# Quality Defaults

The universal quality floors a product's **NFDR** realizes — obligations true of every product this
system builds, held here so a run applies them **with provenance** rather than inventing them from
expertise. Language-agnostic; a tool, a linter flag or a package name belongs to a language packet or
to a product's own toolchain decision, never here.

**Drawn on, not applied** — the same verb `arch_defaults.md` carries, for a different reason. A floor
is not binding until a product's NFDR realizes it as an entry, with that product's own measure, its own
`verified by:` tail, and a trace back to this file. Nothing here stamps an entry into an NFDR.

**Where the SRS states a bar, the SRS wins.** These floors exist for the case the authoring prompt
calls upstream silence: `<CORE>/../skills/principal-architect/.claude/skills/product-architecture/prompts/rich.md` § *When upstream is
silent* sends a run to a doctrine floor where one exists, cites it, and moves on. Where the SRS *does*
state the obligation, the entry traces there instead and this file is not involved. A floor never
overrides an upstream sentence.

**A floor is a rule a change could violate, and the violation can be named.** That is the bar the
constraint set holds every entry to, so anything here that fails it could never become one. Each floor
below therefore carries its verification the same two ways an NFDR entry does — a machine check, or a
named review gate that says why no command can check it.

**This file holds quality; `arch_defaults.md` holds structure.** Neither repeats the other. A rule
about which module may import which is that file's; a rule about what the product must never do with a
secret is this one's.

---

## Secrets

- **A secret is never committed to the repository.** Verified by a machine check: a secrets scan over
  the tree, gating the change. A product with no scanner names the gap in its own entry rather than
  omitting the obligation.
- **A secret is never written to a log, an error message, or a completion report.** Verified by a
  machine check where the product has structured logging a test can read; by a named review gate at
  `development-design` otherwise, because a value's presence in a formatted string is not reliably
  greppable once it has been interpolated.

## Input at the boundary

- **Every value entering from outside the product is validated at the boundary it enters through**,
  before it reaches domain logic. Outside means a user, a file, a network response, an environment
  variable, or another process. Verified by a named review gate at `development-design`, checked
  against the entry points the change touches — **no machine check exists for this one**, because
  what counts as validation is the domain's and a scanner cannot tell a real check from a truthy
  test. The next bullet is the part of it that *is* checkable, which is why it is stated separately.
- **A path supplied from outside is constrained to the directory it is allowed to reach.** Verified by
  error-path tests at layer 5 for each accepting entry point; a new accepting entry point adds its
  own, which is checked at `development-design` against the change's touched surface.

## Dependencies

- **A dependency with a known critical vulnerability blocks release.** Verified by a machine check —
  the language packet's audit command, run as a gate.
- **A known critical vulnerability has a stated remediation window**, and the window starts when the
  advisory is published rather than when someone notices. Verified by a named review gate — no command
  can measure a window — with the gate naming who watches the advisory feed. A product that names no
  window has an obligation nobody is late against.
- **A dependency is added deliberately, not incidentally.** Adding one is a toolchain decision the
  language packet's own § *Adding one* governs; the floor here is only that the decision is recorded
  where a later reader finds it. Verified by a machine check where the product's manifest is under
  version control — a change whose diff adds a dependency and records nothing is mechanically
  detectable — and by a named review gate at `development-design` otherwise.

## Failure visibility

- **A failure is visible from outside the process.** For a CLI: a non-zero exit code and a message on
  stderr naming the failing input. For a served product: a structured event. Verified by error-path
  tests at layer 5.
- **No stack trace reaches an end user** as the product's error output. Verified with the same tests.

## Data

- **A product holds no personal data it has no stated reason to hold.** Verified by a named review
  gate: re-reviewed whenever a change adds a data field, since `development-specs` names new fields
  and a new personal-data field reopens the question. There is no machine check for a reason.

## The boundary set

- **The set of points at which data or control enters the product from outside is named where a reader
  can open it, and the product has no entry point outside that set.** Every product has one, including
  one of size three: a CLI's is its argument vector, its files and its environment; a skill stack's is
  the content a run reads and the tools it is granted; a served product's is its request surface.
  Verified by a machine check where the language's input and network primitives are enumerable — a test
  asserting the socket set and the read set of a full run — and by a named review gate at
  `development-design` otherwise, triggered by a change that adds an entry point. The gate's reason is
  worth stating in the entry: **a scanner can find a new socket, it cannot find a new trust
  assumption.**

- **Every destination the product connects to is named, and the product connects to no other. A product
  that connects to none says so.** Held apart from the boundary set above rather than folded into it,
  because egress is the half that mechanizes cleanly in every language and the half a user would
  actually care about; folding it in would attach the strong check to the weaker obligation and lose it.
  Verified by a machine check for most products — a test asserting the connection set of a full run.

## Outside content

- **Content the product reads from outside is treated as data. Where the product must act on it, the
  authority available at that point is bounded and the bound is named.** One obligation in four
  costumes: deserializing an untrusted store, rendering unaudited file content, an instruction injected
  into content a run reads, an untrusted response from a peer system. Written generally on purpose —
  naming one threat would date the floor to one technology and would not cover the others.

  Verified in two halves, because the two clauses verify differently. The *treated as data* half is a
  machine check at a named sink — a fixture carrying a payload, driven through. The *bounded authority*
  half is what makes the floor hold where the first half cannot be proven: for an agent reading content,
  OWASP's LLM01 states that it is unclear whether fool-proof prevention of prompt injection exists, so
  an entry claiming prevention is claiming what its own source denies. **Write the blast radius instead
  of the prevention** — the authority available to an influenced run is a set of grants, and a set is
  enumerable.

## Capability

- **No component holds a capability it does not use.** A part of the product holds only the authority
  its own job requires: the credentials it reads, the paths it writes, the destinations it reaches, the
  processes it starts. Verified by a machine check wherever the capability is granted in a file — a tool
  grant, a scope list, a configuration key — and by a named review gate at `development-design` where it
  is implicit in code.

  **This is reach, not import, and that is why it is here rather than in `arch_defaults.md`.** That file
  owns which module may import which. A module can import nothing forbidden and still read `~/.env`.
  Two graphs, two checks.

---

## What is not a floor

**A rule that holds for one product shape and not another.** A latency ceiling, an availability
target, a retention period — these are real obligations and they belong to the **conditional
sections** of a product's NFDR, which `<CORE>/templates/product-templates/nfdr_template.md` carries
as §§ 5–8 and which are declared not applicable with a reason where they do not bind. A floor holds
for every product this system builds or it is not a floor, and stretching one to fit is how a
conditional obligation ends up stated as universal and then quietly ignored.
