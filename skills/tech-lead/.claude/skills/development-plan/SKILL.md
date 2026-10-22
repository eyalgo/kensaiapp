---
name: development-plan
description: Tech Lead-posture skill for ongoing work. Reads change_spec.md + change_design.md + docs/adr/ + docs/fdr.md + docs/nfdr.md + the parts table of docs/SDD.md § 3, critically reviews the design against the spec, puts each new piece of logic in the task for the part that owns it, and produces tl_instruction.md — a scaffold the developer implements from failing tests.
license: MIT
metadata:
  version: "2.22.0"
  category: planning
  risk: safe
---

# Development Plan

## Purpose

Read `change_spec.md` (what was asked), `change_design.md` (the design delta), `docs/adr/` (the decision log — why the system is shaped as it is), `docs/fdr.md` (the behavioural contract, if it exists), `docs/nfdr.md` (the constraint set — the module set and its import graph, § 1.2), and `docs/SDD.md` § 3 (the parts table — which part owns which logic), then produce `tl_instruction.md` — a **scaffold** the developer implements from failing tests.

The Tech Lead's job is to **critically review the design and produce a better-specified scaffold than `change_design.md` + the records alone provide.** Not translate — improve. The TL owns the quality of what the developer receives. They are the last quality gate before the developer session.

Two things, and only two:

1. **Critically check the input** — does the design cover the spec, is every new piece of logic in the part that owns it, is every unit testable and atomic, is the build order sound, is every non-obvious unit hinted, are obvious edge cases present, are imprecise types upgraded.
2. **Write the developer instruction as a scaffold** — module responsibilities, behaviours to verify, and a hint only where the approach is non-obvious. The developer does the implementation reasoning; the plan must not do it for them.

## When to Use

- `development-design` has produced `change_design.md` in `system/projects/<project>/journey/tobiishi/<YYYY-MM-DD>_<slug>/` (the records under `docs/adr/`, `docs/nfdr.md` and `docs/SDD.md` are used when present, but are not required — see Pre-flight)
- A `tl_instruction.md` is needed
- `development-plan` is explicitly requested

## Enter the worktree

development-specs created an isolated worktree for this change and landed the spec arc on the branch — it is **not** on `main`. development-design then committed `change_design.md` there. Before reading anything, derive the worktree from the **change key** and operate inside it for the whole run.

The **change key** is `<YYYY-MM-DD>_<slug>` — the Tobiishi folder (`journey/tobiishi/<key>/`) / branch name. You know it from the invocation (the change you were asked to plan). If multiple worktrees exist under `<repo>/.worktrees/` and the intended change is ambiguous, ask which one — once.

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
WORKTREE="$REPO_ROOT/.worktrees/<key>"
test -d "$WORKTREE" || echo "No worktree for <key> — development-specs must run first."
```

If `$WORKTREE` does not exist, **STOP**: the upstream stages have not run for this change. Do not create it here and do not fall back to `main`.

**From here on, the worktree is the working root:** read every input from `$WORKTREE/` (`change_spec.md`, `change_design.md`, and the decision files), write `tl_instruction.md` under `$WORKTREE/`, and commit with `git -C "$WORKTREE"`. The change arc stays on the branch, never `main`. The path is derived from the key alone — identical convention to development-specs Step 4, development-design, and `ad-hoc-plan`; nothing is handed between sessions.

**Locate the project.** The orchestrator passes the **project name** `<project>` alongside the change key; the change-work folder is `$WORKTREE/system/projects/<project>/journey/tobiishi/<key>/`. The project's decision files are **not** assumed to be at the worktree root — a repo may hold more than one project, each owning its own `docs/`.

**Resolve `PROJECT_DOCS`.** The step resolves the path itself, from the path tool's contract — never from any header in the change_spec (the `Project:` header is retired), and never by composing a product path by hand:

```bash
python3 "<CORE>/tools/development_path.py" resolve --format json \
  --worktree "$WORKTREE" --project <project> --key <key>
```

A non-zero exit is a STOP, with the tool's `message`. From the contract's `product_path`, `product_repo` and `product_worktree`: `<sub>` is `product_path` when it is relative, else `product_path` relative to `product_repo` (`.` when the same), and `PROJECT_DOCS = <product_worktree>/<sub>/docs`. For an in-repo product `product_worktree` is `$WORKTREE`. For an external one it is the product worktree opened for this change — by `create_change_worktree.py`, on the chain path and under `ad-hoc-plan` alike — `<product_worktree>/docs` when `Product path:` *is* the repo root — and **never** the product's primary checkout.

**Every `docs/<file>` reference in the steps below resolves to `$PROJECT_DOCS/<file>`** (`adr/`, `fdr.md`, `nfdr.md`, `SDD.md`) — never the worktree-root `docs/` unless `Product path:` points there.

**Locate the product code — anchor, do not scan.** Planning reads the product's *source* (the affected modules, the existing test layout) to scaffold tasks. The source tree is **not** found by searching `$WORKTREE` for "a product folder" — derive it from `$PROJECT_DOCS`:

```bash
PROJECT_ROOT="$(dirname "$PROJECT_DOCS")"   # $WORKTREE/products/<product> (in-repo) or /abs/external-product (external)
```

`$PROJECT_ROOT` is the directory holding the product's `pyproject.toml` / package / tests. **Read all product code strictly under `$PROJECT_ROOT`.** A multi-project instance commits other projects' in-repo products as siblings inside the worktree; for an **external** product `$PROJECT_ROOT` lies *outside* the worktree, so any sibling found by scanning is the **wrong** product — the external-product split-brain. Anchor on `$PROJECT_ROOT`; never scan.

## Pre-flight — Read decision files

Read `$PROJECT_DOCS/adr/` (the decision log and its index), `$PROJECT_DOCS/nfdr.md`, and `$PROJECT_DOCS/fdr.md` if they exist — absence is not an error. These decision files are **optional context**: when they are present, the module set and the import graph (`nfdr.md § 1.2`) below are binding, and a record in `adr/` whose Status reads **Accepted** is binding for the *why* behind them (one still **Proposed** is context). When `adr/` / `nfdr.md` are absent — a dogfood / FDR-less project with no `docs/` — do **not** halt: fall back to `change_design.md` + `change_spec.md` for module boundaries and dependency ordering. The execution/test context always comes from `project.md` (`Execution type:` + `Test command:`), whether or not the records exist. The records sharpen the plan when they exist; their absence is never an error.

**Read the parts table, `$PROJECT_DOCS/SDD.md` § 3.** Its `Owns` and `Must not own` columns say which part owns a piece of logic, and `Lives in` says where that part's code is. The import graph in `nfdr.md § 1.2` does not answer this (`<CORE>/doctrine/flow/development_flow.md` § *Code goes where the parts table puts it*, which defines *owning part* and *misplacement*). When the product has no § 3 parts table, `## Project layout` says so, and placement follows `change_design.md §2`.

---

## Workflow

### Step 1 — Read inputs

Read `change_spec.md` and `change_design.md` from `$WORKTREE/system/projects/<project>/journey/tobiishi/<key>/`. Verify both exist.

If `change_design.md` is missing, halt:

> "`change_design.md` not found — run `development-design` first."

Extract and record before drafting anything:

| What to extract | Source |
|---|---|
| Path — all outputs go here | `$WORKTREE/system/projects/<project>/journey/tobiishi/<key>/` (where `change_design.md` lives) |
| What the change must deliver | `change_spec.md` |
| Test command | `project.md` `Test command:` |
| Success definition | `change_design.md §1 Change Summary` |
| Module names | `docs/nfdr.md § 1.2` (every module appears in the graph) |
| Which part owns which logic, and where its code is | `docs/SDD.md` § 3 (the parts table — `Owns`, `Must not own`, `Lives in`) |
| Allowed imports | `docs/nfdr.md § 1.2` (the import graph) |
| Forbidden imports | `docs/nfdr.md § 1.2` (the same graph, both signs explicit) |
| Blast radius — which modules are new/modified | `change_design.md §2 Blast Radius` |
| Sub-jobs, interface contracts, build sequence | `change_design.md §3 Sub-jobs` |
| Per-sub-job hints (`None` where the approach is obvious) | `change_design.md §4 Code Strategy` |
| Test additions | `change_design.md §5 Test Additions` |
| Records this change makes false | `change_design.md` § *Records this change makes false* |

**Copy the classification — do not re-derive.** Copy `Category` and `Behaviour` from the `change_design.md` header **verbatim**; development-plan is a *propagator*, never a classifier (`change_classification.md` § *Constraints* — "every downstream artifact propagates them header-to-header"). `Behaviour` selects the task shape in Step 3. If the header is missing or out-of-vocabulary (`Behaviour` outside `{preserving, changing}`), **halt** — do not default, do not re-classify; reclassification happens only via the evidence-driven surface-and-halt escape hatch (`change_classification.md` § *Constraints* — "STOP, surface, and reclassify"). See `<CORE>/doctrine/flow/change_classification.md` (`<CORE>` is resolved at session start by the hook).

On `Behaviour: preserving`, the design's §3 is a **Layout Plan** (named modules + symbol→module mapping + `__init__.py` re-exports) and §5 is **Test Continuity** (no new-behaviour tests) — same sections, read the same way.

### Step 2 — Critical review pass

Before drafting, scan the design against the spec and the architecture for gaps the plan must fix:

| Check | Source | Action when gap found |
|---|---|---|
| `change_design.md` does not cover something `change_spec.md` asked for | `change_spec.md` vs `change_design.md` | Add the missing coverage to the plan; log it |
| `change_design.md` realizes a contract `change_spec.md` *stated*, but differently — even if they coincide today (e.g. spec "ascending by `id`" vs the design's incidental stored order) | `change_spec.md` vs `change_design.md` | Realize the spec's stated contract explicitly; if deliberately keeping the design's form, record the decision **and the reason** in `## TL Review Notes` |
| A sub-job in `change_design.md §3` has no test coverage in `§5` | `change_design.md §3 + §5` | Add behaviours to the task block; log it. **Unless no test can assert the deliverable** — a pinned version in a manifest, a generated file's shape, a copy string — **or the check holds only while this change is built** (Step 3): then write the task in the review-verified shape (§ *Implement section rules*) and log that choice. Never fabricate behaviours to fill the gap |
| A sub-job bundles multiple responsibilities | `change_design.md §3` | Split into separate tasks; log the split **Unless §3 carries an atomic-landing edge across them** — a pair with no green point between them is one task, because neither half leaves the suite green on its own |
| `change_design.md` places new logic in one part's code while another part owns it — typically inline where it is first called | `change_design.md §2–§3` vs `docs/SDD.md` § 3 | Put the logic in a task for the owning part's code, and have the caller's task import it; log it. **Where an atomic-landing edge joins the caller and the logic**, keep them one task and name both files in its path, with the logic in the owning part's file. **Where the move needs a unit `change_design.md §2` does not list, or an import `docs/nfdr.md § 1.2` forbids and the design does not allow**, both are the design's decisions: keep the design's placement and log the case |
| Build sequence violates `docs/nfdr.md § 1.2` forbidden imports | `change_design.md §3` vs `docs/nfdr.md § 1.2` | Reorder in the plan; log the reorder |
| `§4`'s Hint column reads `None` where the approach is genuinely non-obvious, or carries a hint that is vague or is really an implementation | `change_design.md §4` | Write the hint the task needs, or cut one back to the approach; log it. Never the commands for a write into another repository, which stay as given (Step 3) |
| An obvious edge case is missing from `§5` | `change_design.md §5` | Add to the task block; log it |
| An imprecise type (string field with a closed value set) | `change_design.md` / `docs/nfdr.md § 1.2` | Upgrade it (e.g. → enum); log it |
| A task's subject already satisfies the behaviours the task is ordered to verify | `change_design.md §3 + §5` vs the product source under `$PROJECT_ROOT` | Write the task in the already-green shape (§ *Implement section rules*) with its `Reason:` line; log it. Never drop the behaviours and never reorder the task to manufacture a red |
| A task's behaviours are tests that already exist and already fail on `main` — an earlier change unit committed them and deferred the task that passes them (its closing marker's `Failing:` and `Deferred:` lines) | `change_spec.md` / `change_design.md §5` vs the test command run under `$PROJECT_ROOT` | Write the task in the red-at-baseline shape (§ *Implement section rules*), one `Red at baseline:` line per failing test and a `Reason:` line naming the change unit that left them; log it. Never route it test-first: the developer cannot commit a red that is already on `main`, and the chain halts the finished change on `missing-red-commit` |
| The gate command runs nothing, or not what the spec measured | `project.md` `Test command:` vs `change_spec.md §Verified Claims` | Run the card's command once. Where it runs nothing, or differs from the invocation the spec's claims ran, put the working command in every `#### Verification gate` and log the divergence — a gate copied from a card that runs nothing passes every task. A card reading `Test command: none` is a product with no code, not a card that runs nothing: run nothing, invent no runner, and make each gate the command or reading the spec's claims name |

**Record every divergence from the input — mandatory.** Keep a running list of every decision where the plan departs from `change_design.md` / `change_spec.md`: any improvement (above), **and in particular** any decision that (a) **resolves a contradiction between two stated contracts** (e.g. the spec states an ordering the design realizes differently), (b) **locks an observable behaviour the input left implicit**, or (c) **overrides an upstream recommendation**. Each entry carries its **reason**. This list becomes the `## TL Review Notes` section in `tl_instruction.md`. A divergence that lands without an entry is the failure mode — a silent resolution turns a reviewable *decision* into an unexamined *assumption*. Omit the section only when the plan diverged from its input in no way at all.

**`Behaviour: preserving`:** the build-sequence-vs-forbidden-imports and sub-job-atomicity checks are moot — a relocation exposes no new interface and has no build sequence. What still applies: the §3 Layout Plan covers the structural goal `change_spec.md` asked for, and the existing suite (`change_design.md §5`) covers every public surface the relocation touches. If a touched surface is uncovered, add a characterization test — it pins existing behaviour, changing nothing (`<CORE>/doctrine/engineering/testing_doctrine.md`). The Layout Plan is binding — do not re-open module boundaries (that is development-design's decision). On a product with no code there is no suite to cover a surface and no characterization test to add: what applies is that every invariant in the Layout Plan has a before-check and an after-check in some task's gate.

### Step 3 — Write tl_instruction.md

Write `tl_instruction.md` to the Path recorded in Step 1.

Write tasks from `change_design.md §3 Sub-jobs`, ordered by the build sequence (respecting `docs/nfdr.md § 1.2`). **An atomic-landing edge in §3 binds the cut:** the sub-jobs it joins become one task, since neither leaves the suite green on its own. The design states the property; deciding the task granularity from it is this step's own call, and splitting such a pair is the one way to get it wrong. **One task is all the edge decides — never a commit count.** A test-first task lands as a red commit and then a green one (`development-implementation` Step 2), and a red commit is not a green point, so the pair keeps its red. Writing *one commit* for a task whose `#### Implement` routes it test-first forbids the red its own lane requires, and the chain then halts the finished change on `missing-red-commit`. For each task:

- **Hints from `change_design.md §4`:** where the row carries a hint, carry it into `#### Implement` as a `# Hint:` block and write nothing more — never a working implementation. The commands for a write into another repository are the one exception (next rule). Where the row reads `None`, the task carries no hint. Dropping a hint the architect wrote is a divergence: carry it, or log the drop in `## TL Review Notes` with the reason.
- **A write into another repository keeps its commands verbatim.** Where the §4 row gives the commands for a write outside the instance and product worktrees, the task carries them unchanged, one call each. They go in the task's `**What to build:**`, under a line reading exactly `Commands for a write into another repository:`. They never go in `#### Implement`, whose marker stays exact. A §4 row holding only those commands counts as `None` when the task's marker is chosen. Never merge them into one call, wrap them in a script, or put a check inside them. The harness matches a call by its literal text, so any of those makes the call match no allow rule (`<CORE>/doctrine/governance/commit_format.md` § *A write into another repository is plain commands, one call each*). A `No allow rule:` line travels with them unchanged, so the developer defers the task rather than attempting the write. Where the design gives such a write as prose instead of commands, write the commands into the task in that doctrine section's form, with the allow rule each matches or a `No allow rule:` line, and log it in `## TL Review Notes`.
- **Behaviours to verify from `change_design.md §5`:** list the behaviours each task must verify. Default to prose; write minimal test stubs only when a behaviour cannot be described in prose.
- **A check that holds only for this change is never a suite test.** Some acceptance rows are true only
  while this change is being built: a file unchanged against the change's base, nothing else moved, every
  copied test still present. Written into the suite, such a test keeps asserting a fixed commit after the
  seal, and the first later commit with a reason to touch those files turns `main` red — measured
  2026-10-12, when a test pinned to `06a17ba` asserted `docs/PRD.md` unchanged and the next PRD
  revision broke the product's `main`. State it as a deliverable verified by review (§ *Implement section
  rules*), each with a command checked against the branch's own merge base, never a pinned SHA, and
  run in the repository whose files it names — the product worktree for a product held in its own
  repo. For "unchanged" that is `git diff "$(git merge-base main HEAD)" -- <paths>`, which also sees
  edits not yet committed; "nothing else moved" adds `--name-only` with exclude pathspecs; "still
  present" compares the merge base's listing with the tree's. The developer and code integrity run it
  on the branch, and it ends with the change.
- **Choose the task's shape before writing it.** Each shape has one exact `#### Implement` marker and one gate subsection, and `development-implementation` routes on that literal text — so the shape is decided here, once, and never left for the developer to infer. The shapes and their markers are § *Implement section rules*.

**`Behaviour: preserving` — relocation tasks under green.** On a product with no code (a card reading `Test command: none`), use the template's docs block instead, by `<CORE>/doctrine/flow/change_classification.md` § *A product with no code*. One task covers every document a moved statement leaves or enters, so no commit leaves a statement stated nowhere or twice. A reword confined to one document is a task of its own. Each `#### Invariant gate` lists the task's invariants with a before-check and an after-check, each a reading or a `git grep` listing compared at the branch's base and head, one per line, as that section sets out. The rest of this paragraph is for code. Write one task per affected unit from the §3 Layout Plan. Each task moves the mapped symbols into the named module(s) and keeps the `__init__.py` re-export-only. **Tests follow production structure only where the relocation changes what they reference** (`<CORE>/doctrine/engineering/testing_doctrine.md`: test files mirror production structure): a test that imports a relocated path moves/updates to mirror it; a move hidden behind a preserved re-export (the tests import the package surface, which is unchanged) leaves the test files where they are. Assertions never change — production and any mirrored tests move **together** as one atomic relocation, so the suite stays green throughout (no red phase). **Where `change_spec.md` names existing tests that are red before the change because this change repairs what they check** (a preserving bug that violates a standard a test already enforces), copy each into the task's `#### Invariant gate` as a `Red at baseline:` line, verbatim from the spec. The developer's baseline accepts exactly those as red and no others, and the change must turn them green. Never add a name the spec does not give. Swap the task's `#### Behaviours to verify` for `#### Invariant gate` and the `#### Implement` body for the no-red restructure instruction (see **Task Structure → Preserving variant**). There are no new tests and no build sequence — every task is `Dependencies: None`.

**Record the gate environment inputs.** `tl_instruction.md` carries one `## Gate environment inputs` section, before the first task block, holding one JSON block: the product's sourced evidence, read from the change's product worktree by `<CORE>/prompts/gate_suite.md` Steps 1, 3 and 4. Read that file and follow it as a gate run does, with three differences: take no owner's ask, give no guest (`"guest": null`), and write no `Environment:` line. On a card reading `Test command: none` the block is `{}`. A CI configuration you cannot read is recorded as unreadable, by that file's Step 3, never as no CI. Write the section whether or not the change publishes text, and commit it with `tl_instruction.md`. You decide nothing from it: just before implementation, the chain asks the gate tool whether this evidence resolves an environment, and stops the walk when the product owes a decision.

The document's shape is `references/tl_instruction_template.md`. The rules for each of its parts — **Plan Header**, **Project Layout**, **TL Review Notes**, **Corrections owed while there**, and **Task Structure** — are below.

### Step 4 — Commit tl_instruction.md

Commit `tl_instruction.md` on the change branch (never `main`) through the shared builder — read `<CORE>/doctrine/governance/commit_via_builder.md` and supply its variables: `<repo>` = `$WORKTREE`, `<staged file(s)>` = `tl_instruction.md`, plus subject / body / **`--actor tech-lead`** (the agent `launcher.md` launches this skill as — name it, never derive it) / `--skill development-plan` (this skill's own name, so `Skill-Version:` records what ran) / directional. Never hand-write `git commit` or a trailer. This skill does not advance the pipeline inboxes — that baton-pass is handled separately.

The skill is done.

---

## TL Standards

These apply unconditionally — every plan, regardless of what `change_design.md` or the records say. The architect defines the architecture; the Tech Lead brings software-engineering expertise to it. The TL is not a translator — they are the last quality gate before the developer.

**Engineering judgment — improve what is imprecise**
- When the design used a technically imprecise construct, upgrade it. Canonical example: a string field with a closed list of values should be an enum — the architect may not have said "enum," but a good TL will.
- Add test behaviours clearly implied by the design but not enumerated. Edge cases the developer would hit anyway belong in the plan even if the architect omitted them.
- Increase isolation, coverage, or precision wherever the plan is thin.
- **Every addition and improvement is logged in `## TL Review Notes` with the reason.**

**Task atomicity**
- A task covers exactly one module or one cohesive responsibility. An atomic-landing pair is one task whichever modules it spans (Step 2's split and placement rows, and Step 3).
- If the design bundles multiple responsibilities into one unit, split it — each part becomes its own task.
- Every task is independently testable: its tests can fail and pass without depending on in-progress adjacent tasks.

**Dependency fidelity**
- Task ordering must honour the import graph (`docs/nfdr.md § 1.2` / `change_design.md §3`).
- If the design's build sequence violates the graph, reorder in the plan — do not follow it blindly.

**Hint precision**
- A hint describes the architectural approach (algorithm shape, data layout, atomicity pattern) — not implementation detail and not vague platitudes.
- A hint too vague ("use a suitable data structure") misleads as much as no hint. A hint too specific ("define a list with these exact methods") does the developer's work. The commands for a write into another repository are not a hint, and are carried as given (Step 3).

**What the TL does not do**
- Does not remove behaviours — they carry forward unless one directly contradicts the spec. Reduction requires a logged reason.
- Does not change structural/topology decisions — module boundaries, sub-folders vs flat files, layer count are the architect's and are binding. Placing logic in its owning part is not one of these (Step 2's placement row). Type-level improvements (string → enum) are in scope; topology changes are not.
- Does not silently drop any architect decision — overrides are logged.
- Does not implement for the developer — improvements raise the bar on the scaffold, not on the implementation. The developer still infers from failing tests.

---

## Plan Header

Every `tl_instruction.md` starts with the header in `references/tl_instruction_template.md`.

**`Product root:` names `$PROJECT_ROOT`, as § Enter the worktree resolved it.** It is the
directory the developer writes code into. On an in-repo product it is written **relative to
`$WORKTREE`** (`products/<product>`, or `.` when the product is the repo root), never as the absolute
path: the instruction is a record that ships with the instance, and an absolute path carries the
machine it was written on. On an external product it names the **product worktree** that
development-specs Step 4, or `ad-hoc-plan` Step 4, opened (under the contract's `product_worktree`), absolute, because nothing
relative to the instance reaches it.

**Never copy `project.md` `Product path:` into this line.** That field names the product's *primary*
checkout, and `$PROJECT_ROOT` names the branch worktree. A plan that stamps `Product path:` sends the
developer's code to a tree this change is not on.

---

## Project Layout

After the header, write a `## Project layout` section: the file tree derived from `docs/nfdr.md § 1.2` (the full module set) and `change_design.md §2 Blast Radius` (new vs modified). Include a creation note for any directories or `__init__.py` files the developer must create. On a product with no code, the section lists the documents instead, from `change_design.md §2`, each marked modified or new (moved text only).

**The constraint set is the topology boundary.** The TL may add file-level specificity (exact filenames, `__init__.py` notes, `← new` / `← modified` markers) but must not add modules, rename packages, or change the module set defined in `docs/nfdr.md § 1.2`.

Its shape is the template's `## Project layout` block.

---

## TL Review Notes (the divergence record — mandatory when the plan diverges from its input)

This is development-plan's **divergence record**: every decision where the plan departs from `change_design.md` / `change_spec.md` is logged here **with its reason**. It is **required** whenever any divergence occurred — not optional. Write it immediately before the first task, in the template's `## TL Review Notes` shape; its example lines name the kinds of divergence that recur.

Omit the section only when the plan diverged from its input in no way at all.

---

## Corrections owed while there (change-level — omit only when the walk turned up none and `change_design.md` § *Records this change makes false* carries its zero form)

Two sources feed it — what the walk turns up under `<CORE>/doctrine/governance/found_while_walking.md` clause 1, which fires on every walk, and every entry in `change_design.md` § *Records this change makes false* — so it arrives on most plans. A correction belonging to no single task has no task to ride, and hanging the change's whole sweep off whichever task happens to be last puts work in a task whose scope is one file — where a reader cannot tell a deliberate end-of-change sweep from an accident of the table being change-level.

Three line shapes, in the template's `## Corrections owed while there` block: *Rides Task N*, *Change-level: no task opens this file*, and *Owed outside this change's reach*.

**Route each correction to the task that already opens its file**, and list here only what no task opens. A correction whose file belongs to a task and is listed here instead is a batching smell: the task's gate passes while its own file is left stale.

**A record this change makes false, and may not edit, takes the third shape.** The first two shapes presume a file this change edits. A product record under `docs/` is not one: this skill reads `docs/` and never writes it (§ *Critical Rules*, "Inputs read, never written"), and the developer writes code only (`development-implementation` § *Inputs*, "writes only code + commits"). So a sentence in such a record that goes false when this change lands has no task to ride and no change-level home. Write it in the third shape rather than drop it. `<record>` is the path and the section. The correction is what the record should say once this change has landed. Every entry in `change_design.md` § *Records this change makes false* is carried here, one line each, because this is the last pipeline artifact that can carry it; a record the design missed and this review finds is carried too.

The third shape states two facts about the record: which record it is, and what it will say wrongly. It names no owner — the record decides where its correction goes. It tells no stage what to do, which is the form `<CORE>/doctrine/flow/folder_state_handoff.md` § *A constraint handed down is stated as a property* requires. Nothing in this change discharges it.

---

## Task Structure

The standard task block is the template's first `### Task N` block.

**Behaviour description rules (always):**

- Default: a bulleted list of test names with one-line descriptions. **No Python code.**
- Name tests after the behaviour (`test_archived_task_rejects_edit`), not after implementation details (`test_status_field_equals_archived`).
- Describe what the behaviour IS, not what field holds it.
- No forward references: a task block must not reference modules or behaviours that don't exist until a later task.
- **`Dependencies:` names what the task uses, never an order.** List a task there only when this one uses something it makes — a file, a module, an interface. A task that only goes after another, to meet a risk first or because the order reads better, says `None`. The task numbers already carry the order, and a reason for it goes in TL Review Notes. When a task is blocked, the developer defers the tasks that use its output, and it reads this line as the plan's claim about which those are (`development-implementation` Step 2 § *Deferring a task*). An order written here can still cost the change work it could have landed.

**When writing minimal stubs (exception — only when prose is insufficient):**

- No import statements. Stubs are fragments, not a complete test file.
- No `@pytest.fixture` definitions. Fixture helpers appear as call stubs (`make_task()`) only.
- No attribute reads on domain objects (`.status`, `.title`). Verify behaviour through `pytest.raises()`, helper returns, and predicate calls. Exception: immutability tests that assign to a field inside a `pytest.raises` block.

**Implement section rules — the sanctioned task shapes.**

`#### Implement` carries one of the markers below, and `development-implementation` routes the task on that **literal text** (its § Step 2, step 2). The marker is a contract, not a phrasing choice: text that is close but not exact routes the task to the wrong lane, and a shape with no sanctioned marker is one every run improvises differently. If a task fits none of these shapes, **STOP and surface** — never invent a marker or a subsection.

| Task shape | Gate subsection | `#### Implement` content |
|---|---|---|
| The task has tests and the approach is obvious | `#### Behaviours to verify` | exactly `Infer from failing tests.` |
| The task has tests and `change_design.md §4` carries a hint | `#### Behaviours to verify` | `Infer from failing tests.` followed by a `# Hint:` block |
| The task has nothing to test — a package skeleton, an `__init__.py` set, a Protocol definition, a `pyproject.toml`, a README | none | exactly `No spec tests — implement per project layout above.` |
| The deliverable is a content change no test can assert — a pinned version in a manifest, a generated file's shape, a copy string — or a check true only while this change is built, checked against the branch's merge base (Step 3) | `#### Deliverables verified by review` | exactly `Verified by review — no test.` |
| The task's behaviours are real, but its subject already satisfies them, so no test of them can be made to fail first | `#### Behaviours to verify` | exactly `Tests cannot go red.` followed by a `Reason:` line |
| The task's behaviours are tests that already exist and already fail on `main`, left by an earlier change unit that deferred the task that passes them | `#### Behaviours to verify`, listing each such test on a `Red at baseline:` line | exactly `Tests are red at baseline.` followed by a `Reason:` line |
| A `Behaviour: preserving` relocation | `#### Invariant gate` | the no-red restructure body ending in `No new tests — TDD under green` (§ *Preserving variant*) |

**A task whose red is probabilistic says so — as a property, not as instructions.** Where a behaviour's failing test is red only sometimes on the tree as it stands — a race, a timing window, anything whose red depends on scheduling — add one line to that task's `#### Behaviours to verify`, in exactly the form the template's standard task block carries (`Red is probabilistic: …`).

This is a sanctioned line, not an invented marker: it names a fact about the task and leaves the `#### Implement` marker and the lane untouched. Do **not** write what the implementer must do about it — forcing the red, the repetition count, and whether to STOP are that stage's decisions, and prose telling it how travels as advice the lane does not route on (`<CORE>/doctrine/flow/folder_state_handoff.md` § *A constraint handed down is stated as a property*).

**A hint is the approach, never the code.** Allowed in a `# Hint:` block: algorithm shape, data layout, atomicity pattern, the key library call (e.g. "load the file, mutate in-memory, write back atomically"). Not allowed: production code, type annotations, working function definitions, complete logic. A hint a developer could paste is a finished production statement, and it takes the implementation reasoning the developer owns. This is the fence `change_design.md §4` points at for the hints it writes. The commands for a write into another repository are the one exception (Step 3), because the permission layer, not the developer, decides their shape.

**The review-verified shape — what its gate subsection carries.** `#### Deliverables verified by review` stands *in place of* `#### Behaviours to verify` and lists each deliverable against the criterion a reader checks it by, one per line. The criterion is what makes the review falsifiable, so "looks right" is not one; "`pyproject.toml` pins `ruff` to the version ADR-0019 fixes" is. The developer records a verdict per line in `Developer Review Notes` (`development-implementation` § Step 3), so the marker buys a record and not only a lane.

**The already-green shape — the `Reason:` line is required, and it is what the marker buys.** The line names why the subject already satisfies the behaviours: the code landed in an earlier change unit, an earlier task in this plan built it, or an upstream dependency supplies it. Write the marker only after reading the subject under `$PROJECT_ROOT` and finding it green — a guess here sends a task to a lane that forbids the red phase it may actually need. The behaviours themselves are written in full as usual: they are real, they must be asserted, and the only thing this shape changes is that nobody claims to have watched them fail.

**The red-at-baseline shape — the tests are the red, and the developer watches it rather than commits it.** Each `Red at baseline:` line names one existing test, verbatim, that fails at the change's base; the `Reason:` line names the earlier change unit whose `Deferred:` task left it failing. Write the marker only after running those tests under `$PROJECT_ROOT` and seeing each fail. The task lists nothing else. The red already sits on `main`, so the task lands as one commit with no red commit of its own; a behaviour that needs a new test would lose its red inside that commit, so it goes in a task of its own, in the test-first lane. Without the shape the case has nowhere to go: a test-first marker demands a red commit nobody can honestly make, and free text such as `Red at baseline` under an invented heading is good practice the router cannot see.

**Ordering a task whose tests cannot go red is legitimate, and `development-implementation`'s *never merge phases* does not forbid it.** A plan orders by the import graph and by what the change needs verified, not by what happens to be unwritten yet. Where the two meet there was no red phase to merge, and the two rules stop contradicting each other the moment the shape is stated. Without a shape to record it in, a task like that lands as one commit whose missing red is silent and reads exactly like a skipped phase.

**Never fabricate behaviours to fill a gate, and never invent a subsection to hold what has no shape.** Where a deliverable genuinely cannot be asserted by a test, or holds only while this change is built, the review-verified shape is the answer; where the behaviours are real but their subject is already green, the already-green shape is; where the failing tests already sit on `main`, the red-at-baseline shape is. Writing invented behaviours instead, or hanging the truth under a heading of your own, sends the task to the test-driven lane, where the developer manufactures a red phase for a task that has none. An invented subsection is the tell: it is good practice the router cannot see.

**The `#### Verification gate` on a task with no tests of its own** states what is run and what passes anyway: the full suite has no new failures, plus whatever the deliverable itself can be checked with (`python -c "import …"`, a lint, a build). It never says "this task's tests pass" where the task has none.

The review-verified task block is the template's.

The already-green shape is an ordinary task block whose `#### Implement` states the lane — the template's already-green `#### Implement` block.

The red-at-baseline shape is an ordinary task block with the template's red-at-baseline `#### Behaviours to verify` and `#### Implement` blocks.

---

## Preserving variant (`Behaviour: preserving`)

A relocation task keeps the same H3 header but states `**What to build:**` as *what moves where*, and swaps two subsections — `#### Invariant gate` for `#### Behaviours to verify`, and a no-red restructure body for `#### Implement`. Its block is the template's preserving relocation task.

The §3 Layout Plan is binding (it is development-design's decision) and the developer performs the move (this skill only scaffolds it) — the two altitude fences around this stage.

---

## Critical Rules

- **A one-change check stays in the change.** An acceptance row true only while this change is built —
  unchanged against the base, nothing else moved — is a review-verified deliverable checked against
  the branch's merge base, never a suite test and never a pinned SHA (Step 3).
- **Operate inside the worktree, never `main`.** Derive `$WORKTREE = <repo>/.worktrees/<key>` from the change key (same convention as development-specs Step 4, development-design, and `ad-hoc-plan`); read all inputs, write `tl_instruction.md`, and commit (`git -C "$WORKTREE"`) there. If the worktree is absent, STOP — do not create it and do not fall back to `main`.
- **Project root from `project.md`, not a header.** A repo may hold multiple projects, each with its own `docs/`. Resolve `PROJECT_DOCS` (absolute) from `project.md` `Product path:`: relative → `$WORKTREE/<Product path>/docs`; absolute → the product worktree opened for this change, by `create_change_worktree.py`, on the chain path and under `ad-hoc-plan` alike (never the primary checkout). Assuming `$WORKTREE/docs/` halts on a multi-project repo where the project lives in a subfolder (e.g. `<product>/docs/`). **Product *code* roots the same way — `PROJECT_ROOT=$(dirname "$PROJECT_DOCS")`; read all product source strictly under it, never by scanning `$WORKTREE` for a product folder.** A sibling in-repo product would be the wrong one — the external-product split-brain.
- **Inputs read, never written: `change_spec.md`, `change_design.md`, `docs/adr/`, `docs/nfdr.md`, `docs/SDD.md` § 3 (and `docs/fdr.md` if present).** Do not read `arch_and_design.md`, `specs.md`, or any other requirements file. Every prescription in `tl_instruction.md` must be consistent with the records.
- **Spec-vs-design coverage is the first check.** `change_spec.md` is read so the plan can verify the design actually delivers what was asked. A spec requirement absent from the design is a gap the plan fixes and logs.
- **Record every divergence from the input — mandatory.** Every decision where the plan departs from `change_design.md` / `change_spec.md` appears in `## TL Review Notes` **with its reason**: improvements (split, added behaviour, reorder, better hint, type upgrade, spec-coverage fix, placement corrected) **and** load-bearing resolutions — resolving a spec↔design contradiction, locking an observable behaviour the input left implicit, or overriding an upstream recommendation. A silent resolution turns a reviewable decision into an unexamined assumption; it is the failure mode.
- **A record this change makes false but may not edit is carried, never dropped.** It is a `## Corrections owed while there` line in the third shape, *Owed outside this change's reach* — every entry in `change_design.md` § *Records this change makes false* among them. What the line carries is § *Corrections owed while there*.
- **`#### Implement` carries one of the sanctioned markers.** The shapes and their exact text are § *Implement section rules*, and `development-implementation` routes on the literal string. A task written in a shape with no marker reaches the test-driven lane silently, where the developer manufactures a red phase for a task that has none. Never invent a marker or a gate subsection; if a task fits no shape, STOP and surface.
- **The plan is a scaffold, not an implementation.** The developer does the implementation reasoning. Spec tests define behaviours to verify, not how to build the entity. Hints describe architectural approach, not working code, except the commands for a write into another repository (Step 3). A task with no hint gets no guidance beyond its tests.
- **No commit choreography.** The plan cuts tasks and gives each its lane marker; how a task is committed is `development-implementation`'s, which reads no commit instruction from the plan (its § *Critical Rules*). Nowhere in `tl_instruction.md` — a task block or `## TL Review Notes` — says *one commit*, *a single commit* or *commit A with B*, an atomic-landing edge included (Step 3).
- **Hints, not solutions.** A hint in `change_design.md §4` is carried into `#### Implement` as a `# Hint:` block and nothing more. Dropping a hint the architect wrote is a divergence, logged in `## TL Review Notes` with its reason; shipping a hint the developer could paste as production code is a violation. The one exception is the commands for a write into another repository (next rule). There is no `Simple | Complex` axis on a task — retired 2026-09-09, the owner's call, because a hint's presence already carried it and the two could disagree. `development-design` § *Step 4 — Code strategy* states the same retirement at the other end of the §4 contract.
- **A write into another repository keeps its commands verbatim.** One plain call each, as `change_design.md §4` gives them, never combined, wrapped or bundled with a check (Step 3).
- **Topology is binding.** The TL works within the module set the constraint set fixes (`docs/nfdr.md § 1.2`). Type-level improvements are in scope; module/package/layer changes are not.
- **Placement is part of the task, never left to the developer** — the owner's call, 2026-10-01 (`<CORE>/doctrine/flow/development_flow.md` § *Code goes where the parts table puts it*). Each new piece of logic is in the task for its owning part's code (Step 2's placement row). Moving logic into an owning part whose unit the design already lists adds no module, and the import the caller then needs is one the graph allows (otherwise the row keeps the design's placement), so on this reading it re-opens no topology decision.
- **Always include exact paths and exact commands.**
- **Always define expected outcomes for test/verification steps.**
- **Task sections use H3.** `### Task N: <name>`. `## Project layout`, `## TL Review Notes` are H2. Never write `## Task`.
- **The TL's own critical-review pass (Step 2) runs unconditionally before drafting.**
- **Two-axis classification.** Every change carries `Category` + `Behaviour` (`<CORE>/doctrine/flow/change_classification.md`). `Behaviour: preserving` swaps the task shape only: `#### Invariant gate` replaces `#### Behaviours to verify` (with a `Red at baseline:` line for each test `change_spec.md` names as red before the change, and none otherwise), `#### Implement` is the no-red restructure, tests mirror the relocated production **only where they reference it** (`<CORE>/doctrine/engineering/testing_doctrine.md`), every task is `Dependencies: None`. Altitude fences: the §3 Layout Plan is binding (do not re-open module boundaries — development-design's decision), and this skill does not perform the move (the developer's). Do not fork the skill — the axis selects the subsections.
