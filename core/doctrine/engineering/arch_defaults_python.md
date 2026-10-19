---
version: "1.0.0"
---

# Architectural Defaults — Python

Python's spellings of the structural patterns in `arch_defaults.md`. That file owns the rules and why
they exist; this one says what each looks like in Python, the way `testing_python.md` overlays
`testing_doctrine.md`.

**Drawn on, not applied** — the verb is the body's, and it governs here too. A default becomes binding
for a product only when that product's SDD chose a shape it serves, and then it enters `docs/nfdr.md`
§ 1.1 as an ordinary entry traced to this file.

**This file adds no rule the body does not state.** Where the two disagree about a rule, the body is
right and this is the copy. Where the body is silent, this file is silent too — a Python-only
constraint with no agnostic rule behind it belongs in a product's own records, not in an overlay.

---

## Entity immutability

`@dataclass(frozen=True)`. Every mutating method returns a new instance via `dataclasses.replace()`
and never mutates in place.

---

## Repository typing

`typing.Protocol`. The concrete implementation satisfies it **structurally and must not inherit from
the Protocol class** — inheriting turns a structural contract into a nominal one and couples the
implementation to the abstraction it was meant to be swappable behind.

That non-inheritance clause is greppable, which is what makes it a layer-6 rule rather than a review
note: `testing_python.md` § *Layer 6 — Architecture* is where a product's check for it runs.

---

## Exception hierarchy

The body's § *Exception shape* states the two rules; in Python they read:

- A single named base inheriting `Exception` — `TaskTrackerError(Exception)` in a product called
  task-tracker. Every typed exception inherits from it, and none inherits directly from bare
  `Exception`, so an interface layer catches `except TaskTrackerError` without swallowing
  `KeyboardInterrupt` or a genuine bug.
- One named exception class per distinct error condition — `InvalidTransitionError`,
  `DuplicateProjectNameError` — rather than one class carrying a message string.

---

## What is not here

**Package structure, the application layer, the composition root and the dependency-graph rules are
not Python-specific** and are not repeated in this file. They are `arch_defaults.md`'s, and they apply
to a Python product by being architecture rather than by being restated here. Two TypeScript packets
already apply them for the same reason.
