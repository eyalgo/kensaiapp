---
version: "2.9.0"
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
| 1 — Unit | Isolated domain logic — entities, rules, computation | Tech Lead + Developer | No real resource — § *A unit test hands its unit fakes and touches nothing real* |
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

## A unit test hands its unit fakes and touches nothing real

**A layer-1 unit test hands the unit a fake for every collaborator, through the same seam production wires the real collaborator through, and keeps the subject real.** The seam is the door the bullet *Reach a collaborator through a seam; never patch the subject* above describes. The form that door takes in each language is that language's `conventions.md` and `testing.md`, under `<CORE>/doctrine/engineering/languages/`.

**A unit test touches no real resource.** It starts no real process. It opens no network connection. It reads and writes no file outside a temporary folder the test makes for itself. It neither reads the real clock nor waits on it. Each of these reaches the unit as a collaborator, so each is handed in as a fake: a process runner that records the command it was given, a network client that answers what the test told it to answer, a clock that reports the time the test set.

**Real resources belong to layer 2, Integration, and layer 5, End-to-End.** A test that needs a real database, a real server, a real process or the real clock is written at one of those two layers and filed with that layer's tests. The table under *Mock what you are not testing; keep the subject real* keeps a real database, real HTTP and real file I/O for the adapter that owns each. On this reading each of those tests is layer 2, because its subject is the adapter that crosses the boundary. A file parser that reads a file the test wrote into its own temporary folder stays at layer 1.

**A unit that builds its own collaborator offers no seam, and the unit is fixed, not the test.** The fix hands the collaborator in through a parameter, and every caller passes it. The port the unit is then handed, and the fake that stands in for it, are not a topology decision (`<CORE>/doctrine/engineering/languages/README.md` § *A fix that hands a collaborator in is not a topology decision*). A change that edits such a unit makes the fix in that change (`<CORE>/doctrine/governance/found_while_walking.md` § *A module the change edits is brought up to the standard in the same change*).

**This section is the one statement of the rule.** A language guide states its own idiom for the seam and the fake, and points here. A skill that writes, plans or checks tests points here and restates none of it.

---

## A fake is verified against its port's contract

**A port has one fake, written once in a test-support module owned with the port and changed with it
— never in what a release build compiles, and never redefined in a test.** A test that needs
behaviour the fake lacks adds it to the fake, with that behaviour's case in the contract suite
below. Each test makes its own instance and configures it — seeding what it returns — and the
instance records what it received, so it serves as the stub and as the spy.

**A port has one contract suite, run against the real adapter and against the fake.** The suite
states the port's behaviour once, as tests written against the port alone. One run hands it the real
adapter and the other hands it the fake. Both runs are layer 2 and are filed with layer 2's tests,
because the suite's subject is the boundary the adapter crosses. The real run still obeys § *A test
reads nothing of the machine it runs on*: it works inside a temporary folder the test makes, starts
only a program the test wrote or the suite's own interpreter, and reaches only a server the test
started on loopback.

**A fake that fails its contract suite fails the test run**, as any failing test does. That is what
makes the fake verified: it cannot drift from the adapter it stands in for, so a layer-1 test that
passes on the fake says something about the real adapter too. A stand-in no contract suite checks
proves only itself.

**A language whose tests have no layer 2 has no contract suite**, since the suite's runs are layer
2; its fakes are unverified, and its testing file says so. **This section is the one statement of
the rule.** Each language's testing file states its form of a contract suite and where its fakes
live, says whether the language has a unit-tier sandbox — a guard that, while a unit test runs,
refuses the real resources § *A unit test hands its unit fakes and touches nothing real* forbids —
and points here.

---

## A test reads nothing of the machine it runs on

**A test reads only what is committed beside it or what it makes itself, and depends on nothing else
of the machine it runs on.** That holds on every layer,
in every language, in every instance and every product. A test may not read:

- the home folder of whoever runs it, or anything under it — settings, caches, logs, telemetry, a
  virtual environment, another project's files;
- a private project's folder, from a test that travels without it — a test under `<CORE>/`,
  `skills/` or `.claude/`, which a satellite runs without this instance's projects;
- a commit of the repository's history. A shallow clone, or a copy published without its
  history, carries none of it.

A test may not depend on four more things the machine supplies, none of them a read. Each item says
what the test does instead:

- **Who runs it.** Whether a file can be read depends on the user who runs the test. `root` ignores a
  `chmod`, so a test that makes a file unreadable with one proves nothing when `root` runs it.
  Instead, the code reads through a seam, and the test hands it a reader that raises
  `PermissionError`.
- **The system's own tools.** A tool the host carries can be missing on the next machine, or behave
  differently there. Instead, the test fakes every process the code starts, the host's tools
  included.
- **The system's terminal.** Whether a terminal is attached, and what a write to it returns, changes
  with where the suite runs. Instead, where a write to the terminal fails with `EIO`, the test reads
  that as nothing written.
- **The network.** A download that works where the network answers fails where it does not.
  Preparing a pin, the copy of the host's `<CORE>` that a launch runs on, can download a Python.
  Instead, a test that makes a pin hands it a Python already on the machine, or a fake uv.

A test that depends on any of the seven things this section forbids passes on a machine where that
thing is as the test expects, and proves nothing anywhere else. A
skip when the thing is missing is not a fix: the skip hides the dependency instead of removing it.

**What to do instead.** Build what the test reads in a temporary folder, or commit it beside the test
as data. A test of code that defaults to a path under the home hands that code a home the test made.
A proof that ran once against an old commit is deleted when it is done; if a lasting guard is wanted,
its inputs and expected outputs are committed as data.

**Two places check three of this section's seven rules** — the owner's call, 2026-10-29, after the
rule, written down only as a note to the model, was broken again:

- **At commit time**, `<CORE>/tools/check_test_isolation.py` reads every test file a commit carries and
  refuses the commit when one names the home folder, looks the home up, names a real path in a
  project's folder from a test that travels without it, or hands a real commit to git. Comments
  and docstrings are not read: a citation reads nothing. It runs from `<CORE>/githooks/pre-commit`,
  which reaches every commit made in an instance on a host, in a product repository a project card
  names (the session-start hook wires both), and in any repository a pinned run commits in, on
  either provider. A line whose lookup reads nothing — text fed to a checker, or the home guard's
  own subject — carries `test-isolation: allowed — <reason>` on that line. **Whoever sees a
  violation fixes it, on the branch they are on** — at commit, or on running the check with
  `--all` — whether they wrote the line or not (`<CORE>/doctrine/governance/found_while_walking.md`).
- **While tests run**, a test gets an empty home of its own. A Python suite under `<CORE>/` and an
  instance's own `system/tests/` run inside `<CORE>/tools/pytest_guardrails.py`, whose guard 7 gives
  one to every test. A product's suite run on the owner's Mac gets one from
  `<CORE>/tools/gate_suite.py`, in any language. A suite run in a container or the macOS guest
  already has a home that is not the owner's. Both keep each toolchain's own folders where they
  are (`<CORE>/tools/empty_home.py`), so the tools work and nothing the test reads comes across.

Which place checks which rule:

| Rule | At commit time | While tests run |
|---|---|---|
| The home folder of whoever runs it | Checks it | Checks it |
| A private project's folder | Checks it | Does not check it |
| A commit of the repository's history | Checks it | Does not check it |
| Who runs it | Does not check it | Does not check it |
| The system's own tools | Does not check it | Does not check it |
| The system's terminal | Does not check it | Does not check it |
| The network | Does not check it | Does not check it |

Who runs it, the system's own tools, the system's terminal and the network are held by neither place.
Neither place refuses a commit, or makes a test fail, because the test depends on one of these four.

---

## Layers 6–7 — Acceptance-Time (ATDD)

| Layer | Scope | Ownership | Approach |
|---|---|---|---|
| 6 — Architecture | Structural rules — layer boundaries, dependency direction, coupling | QA role | ArchUnit-style + AI |
| 7 — Specification | Behavioural contracts — feature scenarios, acceptance criteria | QA role | BDD-style + AI |

The QA role writes the layer-6 acceptance file from the `development-design` output and the layer-7 file from the `development-specs` output, before code; verification runs after the code is delivered. Separate from developer test suites.

- **These layers prove what the other five structurally cannot.** Layers 1–5 prove behaviour for the paths a test happened to walk. Layer 6 proves a property over *every* path — that no module in a forbidden position can reach a forbidden dependency at all. A guarantee stated as an absolute ("never writes", "never executes") wants a layer-6 rule, not only a layer-5 test.
- **Where QA is not active on a project**, record layers 6–7 in `docs/nfdr.md` § 9 as QA-role-owned, naming what verifies them instead. That is a statement about the project's staffing, not about the model.
