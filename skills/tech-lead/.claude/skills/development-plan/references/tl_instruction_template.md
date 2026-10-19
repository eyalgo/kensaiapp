---
version: "1.5.0"
---
<!-- The version above is template-file metadata; it is not copied into the instantiated document. -->
<!-- The shape of one tl_instruction.md, in document order. development-plan owns every rule about
     what goes in it — which shape a task takes, the exact `#### Implement` markers (§ *Implement
     section rules*), and when a section may be omitted. This file carries the shape only. -->

# Tech Lead instruction — <slug>: <description>

**Product root:** <the product's folder, relative to the change worktree; an absolute path only for a product outside the instance> — every path below is relative to it.
**Scope:** <one-line scope description>

---

## Project layout

```
<product-root>/
  <package>/
    __init__.py
    <module>.py              ← flat module file
    <subpackage>/            ← subpackage (use when the module splits into multiple files)
      __init__.py
      <submodule>.py
  tests/
    __init__.py
    test_<module>.py
```

For **existing projects** (mixed "New" / "Modified" in `change_design.md §2`): list only the paths being added or modified. Mark each with `← new` or `← modified`.

When the product has no `docs/SDD.md` § 3 parts table, say so in one line under the tree: `No parts table — placement follows change_design.md §2.`

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):
- **Spec coverage:** `change_spec.md` asked for `<X>` — design §3 omitted it; added Task N.
- **Contract reconciled:** `change_spec.md` states `<ordering/structure contract>` but design §3 realizes it as `<incidental form>` (they coincide today) — Task N realizes the spec contract explicitly. *(Or, if kept: kept `<the design's form>` because `<reason>`.)*
- **Behaviour locked:** the input left `<behaviour>` implicit — pinned to `<choice>` because `<reason>`.
- **Override:** overrode design §`<n>`'s `<recommendation>` — `<reason>`.
- **Task split:** §3 sub-job bundled `<X>` and `<Y>` — split into Task 3 and Task 4 here.
- **Behaviour added:** `test_<behaviour>` added to Task 2 — implied by §3 interface but absent from §5.
- **Reordered:** Task 4 moved before Task 5 — `docs/nfdr.md § 1.2` requires it.
- **Placement corrected:** the design put the new filter inline where it is first called. Task 2 now writes it in its owning part's code (`docs/SDD.md` § 3), and Task 3 imports it.
- **Hint rewritten:** Task 5 hint in §4 was too vague — replaced with concrete algorithm shape.
- **Type upgraded:** `status` string → enum — closed value set.

## Corrections owed while there

- `<path>:<line>` — <what is wrong> → <the correction>. Rides Task N (that task already opens this file).
- `<path>:<line>` — <what is wrong> → <the correction>. Change-level: no task opens this file.
- Owed outside this change's reach: `<record>` — <what this change makes false> → <the correction>.

<!-- The task blocks follow: the standard shape, then the three other shapes development-plan
     § Implement section rules sanctions, each marked. Write each task in the one shape its rule picks. -->

### Task N: <Module name> (`<path>`)

> `<path>` is a single file, a subpackage directory, or a comma-separated list of files when a module splits across multiple files.

**Dependencies:** <the tasks whose output this one uses> (or "None")

**What to build:** <one-sentence module responsibility>. For modules with multiple entities or non-obvious structure, follow with a brief enumeration of key elements (class names, enum values, exception hierarchy, allowed transitions) — enough for the developer to know what to create without being given implementation code.

#### Behaviours to verify (developer adds tests to `tests/test_<module>.py`)

- `test_<behaviour>` — <one-line description of what passes>
- `test_<edge_case>` — expects `<ErrorClass>` on `<call_that_raises>()`

<!-- Only where a behaviour's failing test is red only sometimes, one line in exactly this form: -->
Red is probabilistic: <the behaviour> — <why the red is not deterministic>

Include minimal test stubs only when a behaviour cannot be adequately described in prose.

#### Held by review (omit when every rule of this task reaches a test)

- `<rule>` — covered by no test, and why. State the observable that stands for it, or say plainly that none exists and the rule is held by reading the diff.

A rule nobody wrote a test for is the claim most worth carrying forward, and `#### Behaviours to verify` is a list of test names with nowhere to put it. Written as prose under a heading reading "None in this task", it reaches no downstream stage: implementation reads the behaviour list, and acceptance reads the gate. Name the rule here or it travels as an assumption.

#### Implement

Infer from failing tests.

#### Verification gate

Use the test command from `project.md` `Test command:` On a card reading `none` (a product with no code), use the command or reading the spec's claim names instead.

Pass criteria: this task's tests pass; no new failures elsewhere.

<!-- The review-verified shape — a deliverable no test can assert. -->

### Task N: <what is being changed> (`<path>`)

**Dependencies:** <the tasks whose output this one uses> (or "None")

**What to build:** <one-sentence deliverable>.

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- `<path>` <deliverable> — <the criterion a reader checks it against>
- `<path>` <deliverable> — <criterion>

#### Implement

Verified by review — no test.

#### Verification gate

Use the test command from `project.md` `Test command:` On a card reading `none` (a product with no code), use the command or reading the spec's claim names instead.

Pass criteria: every criterion above is met on reading the diff; the full suite has no new failures.

<!-- The already-green shape — an ordinary task block whose `#### Implement` reads: -->

#### Implement

Tests cannot go red.

Reason: <why the subject already satisfies these behaviours — the earlier change unit, the earlier task, or the upstream dependency that landed it>.

<!-- The red-at-baseline shape — an ordinary task block whose gate and `#### Implement` read: -->

#### Behaviours to verify (existing tests, red on `main`; this task turns them green and adds none)

- Red at baseline: `<test id>` — one line each, verbatim; a test that fails at the change's base because an earlier change unit deferred the task that passes it. Nothing else goes here: a behaviour needing a new test is a task of its own.

#### Implement

Tests are red at baseline.

Reason: <the earlier change unit, and the `Deferred:` task in its closing marker, that left these tests failing on `main`>.

<!-- The preserving relocation shape (`Behaviour: preserving`). -->

### Task N: Relocate `<unit>` (`<module>.py`, `__init__.py`[, `tests/<mirrored path>` only if a test references a relocated path])

**Dependencies:** None

**What to move:** the symbols below move from `<source>` into the named module(s) per §3; `__init__.py` stays re-export-only. Matching tests move only if they reference a relocated path — an intra-package move behind the preserved re-export leaves test files put (assertions never change either way).

| Symbol | → Target module |
|---|---|
| `<Symbol>` | `<module>.py` |

#### Invariant gate (no new tests — the existing suite is the characterization contract)

- Full existing suite green: `<test command from project.md>`.
- Red at baseline: `<test id>` — only a test `change_spec.md` names as red before the change, because this change repairs what it checks; one line each, verbatim from the spec. Omit the line when the spec names none. It must be red before the move and green after.
- Public surface identical: every symbol importable before the move is importable after, same signature.
- A red existing test is a **reclassification event** — STOP and surface; never edit the test to pass.

#### Implement

Restructure per the §3 Layout Plan; move tests to mirror only where they reference a relocated path (production + its mirrored tests move together). **No new tests — TDD under green** (baseline green, or red on exactly the `Red at baseline:` tests → restructure → green; no red phase).

#### Verification gate

Run `<test command>`. Pass: the entire existing suite passes unchanged; no public symbol dropped from any `__init__.py`.

<!-- The preserving shape on a product with no code (`Behaviour: preserving`, card `Test command: none`) — <CORE>/doctrine/flow/change_classification.md § A product with no code. One task covers every document a moved statement leaves or enters; a reword confined to one document is a task of its own. -->

### Task N: Rearrange `<doc>`[, `<doc>`]

**Dependencies:** None

**What to move:** the invariants below leave, enter or are reworded in the named documents, per §3, with the pointers §3 names and the citation updates §2 names. No statement is added, dropped or weakened.

#### Invariant gate (no suite — each invariant is checked at its two places)

- I-<n> — before: stated in `<doc>` § <section> — check: `git -C <Product root> grep -cF -e '<one line>' -- . ':!system/'` on the working tree counts it in `<doc>`; keep the counts. One check per line of the statement | reading.
- I-<n> — after: stated in `<doc>` § <section> and nowhere else — check: the same command after the edit, uncommitted, gives the kept counts with one copy moved from `<before doc>` to `<after doc>`, one per line | reading.
- Pointer — `<doc>` § <old section> names `<doc>` § <new section> — check: reading.
- Write a `'` inside a line as `'\''`. The listing finds exact copies only (`change_classification.md` § *A product with no code*).
- An invariant missing at its before-place is a baseline halt. One missing at its after-place, or stated twice, is a **reclassification event** — STOP and surface.

#### Implement

Rearrange per the §3 Layout Plan. Record each invariant's quoted text before and after in `Developer Review Notes`. **No new tests — TDD under green** (every before-check holds → edit → every after-check holds; no red phase).

#### Verification gate

Run each check the Invariant gate lists. Pass: every after-check holds.
