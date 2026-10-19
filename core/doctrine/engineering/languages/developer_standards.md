---
version: "1.0.2"
---

# Developer standards — the engineering floor for every implementer

The shared engineering standards for any skill whose session writes code. Cited as the language-agnostic
floor by every packet under `<CORE>/doctrine/engineering/languages/`. **Single source — edit here, not in the carriers.**

It is shared material the skills Read on demand, kept beside the language packets that cite it as
their floor. (`development-implementation`
still carries its own inline copy of these standards; pointing it here and deleting that copy is a
deferred, eval-gated kaizen round of its own — do not edit that skill as a side effect of editing this
file.)

## Developer Standards

These apply unconditionally — every task, every line, regardless of what the input contract (a
`tl_instruction.md` or a plan) says. The planner defines the scaffold; the implementer brings
implementation expertise to it. The implementer is not a transcriber — they are the last quality gate
before the code lands.

**Engineering judgment — improve what is imprecise (the carrier's critical review pass)**
- Upgrade imprecise constructs encountered during implementation (string with a closed value set → enum) — even if the input contract did not say so.
- Add test behaviours clearly implied by a task's responsibility but not enumerated; cover edge cases the implementation would hit anyway.
- Increase coverage or precision wherever the scaffold is thin.
- **Every improvement is logged in the carrier's Review Notes block** (closing commit body) with its reason. Topology stays binding — type-level and coverage improvements are in scope; module/package/layer changes are not.

**SOLID**
- **Single Responsibility** — one class, one reason to change
- **Open/Closed** — extend via addition, not modification
- **Liskov Substitution** — subtypes honour the parent contract
- **Interface Segregation** — small, focused interfaces
- **Dependency Inversion** — depend on abstractions; inject dependencies

**Clean code**
- Intent-revealing names — no abbreviations, no generic labels (`manager`, `handler`, `utils`)
- One level of abstraction per function
- No magic numbers or strings — named constants
- Pure functions by default — minimise hidden state and side effects
- Immutable data structures unless mutability is required
- **`__init__.py` is for package initialization and public re-exports only — never implementation.** Entities, services, repositories, CLI logic live in named modules (`domain/models.py`, `domain/exceptions.py`, `persistence/json_repository.py`, …); `__init__.py` re-exports the public interface the decision files (or the plan) specify. This holds **even when the input contract lists `<package>/__init__.py ← modified` as the target or sanctions keeping code there** — treat it as an imprecise layout (the carrier's critical review pass): create the named modules, re-export, log it in the Review Notes. Splitting a package's internal files is layout, not topology — the package boundary stays binding, so it is squarely within the implementer's improvement latitude. **The one exception is a package's composition edge** — an `__init__.py` whose whole content wires that package's own named modules together and holds no domain logic, the shape `checks/deps/__init__.py` already carries. Where the design mandates that shape, build it, and log the choice in the Review Notes as the exception it is. Without a named exception this rule loses silently: a design-sanctioned pattern meets an absolute rule, the implementer follows the design, and nothing records that a rule was set aside.
- **A comment that says *what* the code does is the smell.** The fix is a rename, an extraction, or the test that would have failed — the comment itself cannot fail, and that asymmetry is the whole argument. The one exception is a comment recording *why* the code is shaped this way and not the obvious other way, with a citation: `commit_builder.py` and `product-card/launcher.sh` both carry headers of exactly that kind, because the reasoning is not recoverable from the code — it is about the alternatives that were rejected. Which doc-comment form carries that exception in a given language is that language's `conventions.md` to state, per `<CORE>/doctrine/engineering/languages/README.md`.

**Design patterns**
- Apply when the problem shape matches — do not force a pattern
- A forced pattern is worse than no pattern

**Always**
- DRY — no duplicated logic
- YAGNI — implement what is needed now
- Every public interface has an explicit contract (types, signatures, documented invariants)
- Every commit leaves the codebase cleaner than it found it
