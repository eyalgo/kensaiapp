# product-architecture

A product's design settles in the SDD, and then the reasons behind it evaporate: six months later
nobody can say which shape was a decision and which was an accident, and nothing states what a change
may not break. `product-architecture` is the **Principal Architect**'s tool for closing both gaps —
the append-only decision log at `docs/adr/`, one file per architecturally significant decision plus an
index, and the constraint set at `docs/nfdr.md`, which every later change is verified against. It
belongs to the **foundation step**, beside the Principal PM's FDR, written from the settled SRS, SDD
and FDR.

**It records; it does not decide.** The decisions were made in the SDD conversation, and this run
transcribes them faithfully — a decision it judges wrong becomes a companion item routed back to the
seat that owns it, never a record that quietly says something else. **One run writes both records**,
because the constraint set's entries trace to the records that run just wrote.

**Its finish line is that nothing is left open**, and it gets there without asking a question
mid-run. The skill derives both records best-effort and parks what it cannot settle in one companion
open-issues file the owner answers on their own time; a re-run folds those answers in. When the
companion is gone, both records are done — that absence is the done signal, and it is what lets the
run work headless as well as in a session.

## Version and ratification

`1.0.0` — the first marker this skill carries. It has no ratification record yet, and it has not yet
been run against a real product.

## What It Does

- **Reads all three upstream documents in full** — the SRS, the SDD and the FDR — and halts naming
  the file when one is missing at its resolved path, because every entry carries an upstream trace
  and with a source absent there is nothing to trace to.
- **Reads an unsettled input rather than waiting for it**, and records what it read on the constraint
  set's `Inputs read:` line. No step gates on `Locked`, on `Settled`, or on the absence of any marker.
  The rule and the line's form are `<CORE>/doctrine/governance/unsettled_inputs.md`'s, for every
  document in the chain.
- **Records only what earns a record** — hard to reverse, surprising without context, the result of a
  real trade-off. All three, or it is not a record. A log of everything is read by no one.
- **Never rewrites an accepted record.** A reversal is a new record whose Status names the one it
  supersedes; the superseded record's Status line is the only line in it that ever changes. The
  constraint set is the opposite — revised in place, versioned, under provenance.
- **Makes every constraint traced and named-verifiable.** An entry names the upstream fact it
  realizes and what fails when it is broken; claiming a review gate rather than a machine check is a
  downgrade the entry has to argue in its own tail.
- **Keeps the owner's answers.** Every answered companion is copied whole to
  `docs/trail/architecture/` before the fold rewrites it, so what the owner decided and why stays
  readable and citable.

## File Structure

```
product-architecture/
├── SKILL.md     # the orchestrator: posture, the file loop, path resolution, staging, the commit
├── README.md    # this file
├── stack.json   # the substance files, read by the cold-read manifest
└── evals/       # behaviour evals
    ├── evals.json
    └── inputs/  # the fixtures the cases run against, and the note that describes them
```

## Depends On

- `prompts/rich.md` — the authoring prompt: **how** to
  record and bind. The skill orchestrates; this file holds every rule the author applies — the
  authority order, the three significance gates, the ownership test, the constraint bar, the finish
  walk.
- `<CORE>/templates/product-templates/adr_record_template.md` and `adr_index_template.md` — one
  record's shape and the index's; `nfdr_template.md` — the constraint set's;
  `architecture_open_issues_template.md` — the companion's.
- `launcher.md` — what `<CORE>/launchers/skill/launcher.sh` reads to start the run as a
  `principal-architect` background agent and report when it finishes, through the `architecture`
  composer in `<CORE>/tools/reporters.py`.
- `<CORE>/roles/loaders/principal_architect_global.md` — the posture the skill gates to, and where
  the seat's boundary with the CTO and the delivery-tier Architect is settled.

There is **no acceptance skill to hand to** and no machine gate: nothing publishes a schema or a lint
for either document. What stands in their place is the prompt's finish walk and the constraint set's
own § 9 verification map.

## Launching It

From the instance root:

```
<CORE>/launchers/skill/launcher.sh product-architecture <project> [--dry-run] [--keep-awake]
```

The prompt is a fixed literal in `launcher.md`, so nothing a caller types reaches the run. The
launcher detaches a completion watcher whose `architecture` reporter says, when the run stops, where
the decision log, the constraint set and their companion stand.

## When to Use

Reach for this when **a product's foundation is being laid** — its SRS, SDD and FDR are written and
the decisions behind the design have to be recorded and their constraints bound — or when an answered
companion is waiting to be folded back in.

Not for: designing the system (`product-sdd`, the CTO's), designing one change
(`development-design`), the behavioural contract beside these records (`product-fdr`), the upstream
documents they derive from (`product-prd`, `product-srs`), or the project's terminus
(`project-agari`).
