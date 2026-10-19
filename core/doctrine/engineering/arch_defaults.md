---
version: "2.0.2"
---

# Architectural Defaults

Candidate structural patterns the **Principal Architect** draws on when authoring a product's records.
Language-agnostic; the Python spellings are `arch_defaults_python.md` beside this file, and a product
in another language records its own.

**These are drawn on, not applied.** A default here becomes binding for a product only when that
product's **SDD chose a shape these serve** — and then it enters `docs/nfdr.md` as an ordinary entry,
traced to this file, with a `verified by:` tail like any other. Nothing stamps them in.

**Why the verb is *drawn on* — the owner's call, 2026-08-30.** A default that lands automatically
pre-decides a layered-clean shape before any SDD has weighed one, which is the recommender
`<CORE>/../skills/cto/.claude/skills/product-sdd/prompts/rich.md` § *Weighing the shape* forbids: *"a recommender… moves the choice
upstream of the SRS being read"*. It would also make SDD § 2 paperwork — the CTO does the
weighing and finds the answer already stamped. So the SDD decides the shape, and this file offers what
a run may propose once it has.

**A default a product departs from needs no justification here.** It was never binding. What needs a
reason is the opposite case — an entry in a product's NFDR that traces to nothing, which is an
invented requirement whatever it says.

---

## Package Structure

**Multi-module products:** when the system has 2+ layers with their own internal files, each module is
a package directory (`pkg/domain/`, `pkg/cli/`), not a flat file. Flat files suit single-file additions
or a small touch inside one module. A product whose FDR describes a full system takes the directories.

---

## Application Layer

Proposed for every non-trivial system. Two concerns justify it independently:

1. **Flow orchestration** — owns use-case logic (fetch entity, validate state, mutate, save). Does not
   live in entry-point handlers.
2. **Entry-point thinning** — CLI handlers and other adapters carry no logic: receive input, delegate,
   format output. This holds regardless of call count. A handler making "only one domain call" is
   still wrong if that call contains branching, transformation, or anything beyond delegation.

Do not reason from call count to omit the application layer. The question is whether the entry point
stays logic-free.

---

## Composition Root

The composition root (`main()` or an equivalent bootstrap module) is the only place that wires concrete
implementations to abstractions. It owns wiring, not flow — the only node in the dependency graph that
knows a given concrete implementation exists.

---

## Exception shape

Language-agnostic, and the spelling of each is the language overlay's:

- **A single named base.** One product-level base error type; every typed error derives from it, and
  none derives directly from the language's root error type. That is what lets an interface layer
  catch the product's failures in one clause without swallowing everything else.
- **One type per distinct condition.** A named type per error condition rather than one carrying a
  message, because callers map types to distinct outputs — exit codes, HTTP statuses, messages — and
  cannot map a string.

---

## Dependency Graph Rules

- Only the composition root imports concrete implementations. Every other module depends on
  abstractions.
- No dependency edge crosses from an inner layer to a concrete implementation.
- **Forbidden imports are stated explicitly** — never inferred from the allowed-imports list alone.
  A product's own graph lives in `docs/nfdr.md` § 1.2, both directions stated, and the Tech Lead runs
  structural verification off it.

---

## The seam with the quality floors

This file holds **structure** — what may import what, where wiring lives, how a system is packaged.
`quality_defaults.md` beside it holds **quality** — what a product must never do with a secret, what it
validates at its boundary, what blocks a release. Neither repeats the other, and an NFDR entry traces
to whichever of the two states the rule it realizes.

---

## The Python overlay

`arch_defaults_python.md` carries the Python spellings of the rules above — entity immutability,
repository typing, and the exception base — the way `testing_python.md` carries `testing_doctrine.md`'s.
It adds no rule this file does not state; if the two disagree about a rule, this file is right and the
overlay is the copy.
