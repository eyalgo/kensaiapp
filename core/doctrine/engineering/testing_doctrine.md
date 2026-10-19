---
version: "2.2.0"
name: testing-doctrine
description: 7-layer test pyramid. Layers 1–5 are code-time TDD (Tech Lead and Developer each add tests as they see fit). Layers 6–7 are ATDD — written by the QA role after specs/arch, before code, using ArchUnit-style and BDD + AI reasoning.
---

# Testing Doctrine

## Overview

Seven layers in two phases:

- **Layers 1–5 — Code-time (TDD):** Both Tech Lead and Developer add tests as they see fit. Tests are written before the code they cover.
- **Layers 6–7 — Acceptance-time (ATDD):** Written by the QA role after specs/arch changes are defined, but before any code is written. High-level acceptance criteria drive the implementation. Verified after the code is delivered.

### Three axes, not one ladder

The layer number orders **scope** — how much of the system runs, cheapest and narrowest first. Two other properties are routinely mistaken for layers and are not:

- **Scope** — how much of the system runs. This is what the numbering orders.
- **System layer** — which layer of the system is under test (domain, persistence, application, UI). A part of the system, not a rung on this ladder.
- **Phase** — code-time TDD (layers 1–5) vs acceptance-time ATDD (layers 6–7).

Every test has a coordinate on all three. Stating all three is what makes "every layer green" a claim that can be checked.

**Layer 3 (Application) vs layer 5 (End-to-End) is decided by which door you enter, not by how much runs underneath.** Layer 3 enters *inside* the boundary — it calls the use case in-process, bypassing the entry point. Layer 5 enters *outside* it, through the real entry point, the way a user does.

---

## Layers 1–5 — Code-Time (TDD)

| Layer | Scope | Ownership | Notes |
|---|---|---|---|
| 1 — Unit | Isolated domain logic — entities, rules, computation | Tech Lead + Developer | No I/O |
| 2 — Integration | Cross-boundary flows — real persistence, external adapters | Tech Lead + Developer | |
| 3 — Application | Full use-case flows wired through all layers, bypassing entry point | Tech Lead + Developer | **Optional** — omit with rationale in `docs/nfdr.md` |
| 4 — UI | A component renders truthfully given state — no full system, no driven session | Tech Lead + Developer | **Optional** — applies only to a product with a UI; omit with rationale in `docs/nfdr.md` |
| 5 — End-to-End | Full system via entry point — golden path + key error paths | Tech Lead + Developer | |

Both Tech Lead and Developer add tests as they see fit. Tests precede the code.

- **Test files mirror production structure.** A test file's location and naming follow the production module it covers.

  ```
  src/domain/Order            →  tests/unit/OrderTest
  src/persistence/OrderRepo   →  tests/integration/OrderRepoTest
  src/app/CreateOrderHandler  →  tests/application/CreateOrderHandlerTest
  src/ui/OrderRow             →  tests/ui/OrderRowTest
  ```

- **Mock what you are not testing; keep the subject real.**

  | Subject under test | Keep real    | Mock                        |
  |---|---|---|
  | DB repository      | real DB      | REST clients, message queues |
  | REST client        | real HTTP    | DB, file system              |
  | File parser        | real file I/O | network calls               |
  | UI component       | real component + real render | the application layer behind it |
- **Reach a collaborator through a seam; never patch the subject.** A test hands the unit a fake through the same door production wires the real one through, then asserts on **what that fake received** — the calls it got, in order, with their arguments. Replacing a name inside the module under test is not mocking, it is editing the subject: the assertion then holds against a module the entry point never runs, which is how a suite stays green over behaviour that does not exist. Where the subject offers no door to hand a fake through, the defect is the subject's shape and not the test's.
- **Layer 3 is optional.** Omitting it requires explicit rationale in `docs/nfdr.md`.
- **Layer 4 is optional, and inapplicable without a UI.** A CLI or a library has no components; omitting it requires explicit rationale in `docs/nfdr.md`. A product with a UI does not get the exemption.
- **Layer 5 runs separately.** End-to-end tests are not part of the layers 1–4 suite.

---

## Layers 6–7 — Acceptance-Time (ATDD)

| Layer | Scope | Ownership | Approach |
|---|---|---|---|
| 6 — Architecture | Structural rules — layer boundaries, dependency direction, coupling | QA role | ArchUnit-style + AI |
| 7 — Specification | Behavioural contracts — feature scenarios, acceptance criteria | QA role | BDD-style + AI |

The QA role writes the layer-6 acceptance file from the `development-design` output and the layer-7 file from the `development-specs` output, before code; verification runs after the code is delivered. Separate from developer test suites.

- **These layers prove what the other five structurally cannot.** Layers 1–5 prove behaviour for the paths a test happened to walk. Layer 6 proves a property over *every* path — that no module in a forbidden position can reach a forbidden dependency at all. A guarantee stated as an absolute ("never writes", "never executes") wants a layer-6 rule, not only a layer-5 test.
- **Where QA is not active on a project**, record layers 6–7 in `docs/nfdr.md` § 9 as QA-role-owned, naming what verifies them instead. That is a statement about the project's staffing, not about the model.
