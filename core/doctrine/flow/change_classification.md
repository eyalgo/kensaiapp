---
version: "2.2.2"
---

# Change classification — two axes

Every iteration change (a run through the Stage 1–5 pipeline in `development_flow.md` § The stages)
is classified on **two orthogonal axes**: what kind of change it is, and whether it moves the
product's behaviour.

The two axes answer two different questions and must never be collapsed into one enum:

| Axis | Values | Drives |
|---|---|---|
| **Category** | `feature` \| `bug` \| `refactor` \| `nfdr` | **routing & provenance** — entry point, which decision file is source-of-truth, how the change is tracked |
| **Behaviour** | `preserving` \| `changing` | **mechanism** — spec mode, execution discipline |

**The axes are independent**, with two pairs ruled out (§ *Constraints*): a `feature` is always
`changing`, and a `refactor` is always `preserving`. The other categories take either value — a `bug` may be
behaviour-`preserving` (a structural/quality defect: code is correct but violates a standard) or
behaviour-`changing` (a functional defect: the observable behaviour is wrong). Therefore
behaviour-preserving is a **property a change has**, not a category it belongs to. "Refactor" names
one behaviour-preserving *category*; it is not the name of the property and not the name of the path.

---

## Behaviour-preserving — definition

A change is behaviour-`preserving` when it leaves unchanged:

1. the **FDR-level behavioural contract** (the behaviours the existing test suite pins), and
2. the **public interface** (the set of importable symbols and their signatures).

It also adds nothing to that contract. **Preserving is not the same as touching nothing.** A change
that leaves every existing behaviour and name alone but adds a new one has still changed the contract,
so it is `changing`. The test is what the product does or states after the change, not what the change
disturbs. Two things are not additions. A test that pins a behaviour the product already has adds a
check, not a behaviour (§ *Constraints*, characterization tests). Logs, latency and the other
observables the next paragraph sets outside the fence are not part of the contract at all.

For a product with no code, the contract is what its documents state, and there is no public
interface. A change that states something the documents did not state before is `changing`: a new
document, or a new section a reader will act on. A change that rewords, reorders, splits or moves what
is already stated, and leaves its meaning as it was, is `preserving`. That includes a new file made
only to hold text moved out of another, and a line left at the old place that only says where the
text now stands. That pointer is the documents' re-export: it keeps the old path to the text working
and states nothing new.

It is **not** required to preserve everything observable. Logs, latency, internal file layout, and
on-disk format internals may all change. The fence is *contract + public API* — nothing finer.
Without this scoping, "add logging" or "swap the DB library" could never qualify as preserving.

---

## The behaviour-preserving path (mechanism by stage)

When `Behaviour: preserving`, each stage's job shifts. The category is irrelevant to this column —
the same mechanism serves a preserving bug, refactor, or nfdr change.

| Stage | `changing` | `preserving` |
|---|---|---|
| `development-specs` | mint new CP-rules | pin a **characterization contract** (existing behaviour as the locked invariant); new halt `behaviour-delta-detected` if drafting reveals behaviour actually changes |
| `development-design` | new interfaces + test additions | **structural target** + interface-invariance constraint; §5 becomes test-*continuity*: no tests for *new* behaviour (there is none), but **adding characterization tests that pin existing behaviour is encouraged** — they tighten the regression fence without changing behaviour |
| `development-plan` | behaviour tasks | move/structural tasks; `#### Invariant gate` ("full existing suite green; public imports identical") instead of `#### Behaviours to verify` |
| `development-implementation` | TDD red → green | **TDD under green** — the existing suite is the guardrail; baseline green → change → green; **no red phase**. The one exception: tests `change_spec.md` names as red before the change, because it repairs what they check, may be red at baseline and must be green after |

### A product with no code

The table above assumes code: an import surface, a test suite, modules to move. A product made only
of documents has none of these. Its card reads `Test command: none` (`development_flow.md`), it
declares `Suite: none`, and its contract is what its documents state. A preserving change rewords,
reorders, splits or moves that text and leaves every statement true. Each stage keeps its preserving
shape and swaps code for documents, using its own `*.preserving_docs.md` template, or for the plan,
its template's docs block.

**An invariant is one statement, with two places.** It is quoted as the documents state it now, with
the document and section it stands in before the change, and the document and section it will stand
in after. A statement that is not moving has the same place twice. A statement that moves holds when it
is stated at its new place and no longer at its old one, so the move adds no copy and leaves none
behind. A reworded
statement holds when its meaning is unchanged, whatever its words. A new file holding only moved
statements is `New (moved text only)`. A document left with a pointer to a moved statement's new place
is `Modified (text moved out, pointer left)`. A pointer that says anything beyond where the text now
stands, and a new file that states anything else, make the change `changing`.

**A check command proves one line, and compares two listings.** `grep -F` reads each line of a
multi-line pattern as a separate pattern and passes when any one matches, so a statement longer than a
line gets one check per line, or a reading. The command is `git grep -cF`, which searches tracked files
only, prints the same paths on every machine, counts the copies in each file, and takes the line safely
after `-e`. It has two forms:

- **On the working tree**, for the developer, who checks before committing:
  `git -C <product root> grep -cF -e '<line>' -- . ':!system/'`. Run once before the edit and once
  after, and compare.
- **Between two commits**, for code-integrity and the seal:
  `git -C <product root> grep -cF -e '<line>' <rev> -- . ':!system/' | sed 's/^[^:]*://'`, at
  `$(git -C <product root> merge-base main HEAD)` and at `HEAD`. Given a revision, `git grep` prefixes
  each line with it, and the `sed` strips only that prefix, so a path holding `:` survives.

The exclusion keeps the instance's journey out when the product root is the instance root. A `'` inside
the line is written `'\''`. "Nowhere else" is not a count of one, because a line may already stand in
several documents before the change. The counts after must be the counts before, with one copy moved
from the before-place to the after-place. A copy left behind, or a second copy anywhere, changes a
count. The check finds exact copies only. A reworded copy is for a reading to find.

**A product document that cites a moved statement's old place is in the blast radius**, whether or
not the change touches it. It goes false when the text moves, so the design lists it, and the plan
updates the citation or leaves the pointer that keeps it true. A product record (`adr/`, `nfdr.md`,
`fdr.md`, `SDD.md` § 3) is the exception. The change never edits one, so a record that goes false is
listed under *Records this change makes false* and carried as owed, as it is for code.

| Stage | `preserving`, product with no code |
|---|---|
| `development-specs` | `## Invariants` lists every statement the change touches, each with its two places. They come from the request and the documents' own words, never from a reading of what the text might imply. `## Structural Goal` names the arrangement the change makes. `behaviour-delta-detected` fires on any statement the change would drop, weaken or add |
| `development-design` | The blast radius lists every document touched or citing a moved statement's old place, by the four statuses of `change_design_template.preserving_docs.md`, except a product record that cites it, which goes under *Records this change makes false* and stays owed. The Layout Plan confirms or settles each invariant's after-place where the spec left a section open. §4 Code Strategy is `None — no code`. Test continuity is `No suite — each invariant is checked by reading`. The cold read asks whether every invariant is placed, whether any is stated twice, and whether anything new is stated. A "yes" to the last is a STOP for reclassification, as a changed signature is for code |
| `development-plan` | A task covers every document a moved statement leaves or enters, so no commit leaves a statement stated nowhere or twice. A reword confined to one document is a task of its own. `#### Invariant gate` lists the task's invariants, each with its before-place and after-place check. A check is a reading, or a `git grep` listing as the paragraph above sets out. The `#### Implement` body still ends in `No new tests — TDD under green` |
| `development-implementation` | The preserving lane with checks instead of a suite run. Baseline: every invariant holds at its before-place. If one does not, the documents are not what the spec described, and the run halts as on an unexpected red at baseline. Then the edit. After: every invariant holds at its after-place and nowhere else. If one does not, that is the reclassification event, and the run halts as it would on a test gone red. Each invariant's quoted text before and after the edit goes in `Developer Review Notes`, which are never omitted on this path. `Suite: none` |
| `development-code-integrity` | No test to write and no suite to run. The report re-checks each invariant against the branch and is committed on its own (that skill's *How the tests get run*, in Step 2) |
| `tobiishi-seal` | On the one-repo path, after taking `main`'s advance, the seal re-runs every after-check that is a command, in its between-two-commits form. The before-checks are meant to fail by then. A reading-only check is not re-run. A failing command halts the seal as a failing suite would. A product in its own repo takes no advance at the seal, so code-integrity's re-check is its last |

---

## Category notes

- **`feature`** — behaviour-`changing` by definition (introduces new behaviour). Standard red/green path.
- **`bug`** — **either** behaviour value. A structural/quality bug (violates a standard, behaviour fine) is `preserving`; a functional bug (wrong observable behaviour) is `changing`. The bug's "spec" is the violated contract.
- **`refactor`** — always `preserving`, always elective (restructure code that is *already correct*). Distinct from the constant green→refactor step inside per-task TDD; this is a *pipeline-level* refactor of already-landed code.
- **`nfdr`** — a non-functional change (dependency/library swap, observability, build/tooling), **either** behaviour value. It is `preserving` where the toolchain moves under unchanged observable behaviour, and `changing` where the change alters what an enforcement command reports — a check that gains a rule, or a rule identifier that moves, is a new observable even though no product behaviour moved. Source-of-truth is `nfdr.md`.

A product's first skeleton is not a change and takes no category: `<CORE>/launchers/product-skeleton/`
stamps it before the pipeline runs. The `greenfield-skeleton` category that stood here, with the
behaviour axis N/A, was retired on 2026-09-11 — the owner's call — so every change carries both labels.

---

## Constraints (standing rules)

**Classification is set at entry and stamped in the header.** The PM→Product-Owner request fixes both
axes; `development-specs` records them in the `change_spec.md` header (`Category:` + `Behaviour:`) and every
downstream artifact propagates them header-to-header. Routing reads `Category`; the mechanism reads
`Behaviour`.

**A red test under a `preserving` change is a reclassification event, not a fix target.** If executing
a behaviour-`preserving` change turns an existing test red, behaviour changed — **STOP**, surface, and
reclassify. Never edit the test to pass.

**The behaviour axis selects the mechanism; the category selects routing. Never merge them into one
field.** One enum that mixes `feature/bug/refactor` with `preserving/changing` re-creates exactly the
conflation this doctrine exists to prevent.

**Two pairs contradict themselves, and `development-specs` halts on both.** `refactor` + `changing`
does, because a refactor preserves behaviour by definition. `feature` + `preserving` does too, because a
feature adds behaviour, and adding is changing (§ *Behaviour-preserving — definition*). The PM sets both
labels at `tobiishi-open` and corrects them there.

**The Behaviour vocabulary is closed: `{preserving, changing}` — nothing else.** Values like
`additive`, `new`, `enhancement`, or `breaking` are **not** Behaviour values. A `feature` is
`changing` by definition (it introduces new behaviour). "Additive" / "breaking" describe a change's
*blast radius / compatibility* (does it touch existing surfaces?), which is a separate property the
architect computes in the blast-radius analysis — never a Behaviour. Every producer and propagator of
the header (the front-door Tobiishi, `development-specs`, `development-design`, `development-plan`,
`development-implementation`) must emit or accept only the two values; `development-specs` **halts**
`invalid-behaviour-classification` on a missing or out-of-vocabulary value rather than defaulting or
propagating it.

**Adding characterization tests is always in scope for a `preserving` change.** Tests that assert
*existing* behaviour change nothing observable and tighten the regression fence — prefer adding them
over leaving a surface uncovered. Only tests for *new* behaviour are out of scope (a preserving
change introduces none).

---

## Worked example — a create-project slice

Production code for the create-project slice was written into each layer's `__init__.py` instead of
named modules, violating the `__init__.py`-is-re-export-only standard in `development-implementation`.

- **Category:** `bug` — the code violates a codified standard (it is non-conformant, not merely improvable).
- **Behaviour:** `preserving` — public imports (`from <package>.domain import Project`) and the test suite are unchanged; only file location moves.
- Its spec is the violated standard itself: *"make the code satisfy the `__init__.py` standard; behaviour unchanged."*

---

*Ratified 2026-06-18 (architect-posture session, Product-ratified).
References `development_flow.md` § The stages (canonical stage list) and `folder_state_handoff.md` (handoff + action-file pattern).*
