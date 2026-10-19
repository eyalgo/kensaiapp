# development-specs

A change arrives as a sentence — *"add X"*, *"change how Y works"* — and the pipeline downstream of it
needs something a designer and an implementer can both work from. `development-specs` is the Product
Owner's tool for that expansion: it turns a casual request for an existing project into a structured
`change_spec.md`, at the front of the change pipeline.

**It halts rather than asks.** When it cannot proceed it writes a halt report and stops, instead of
opening an interview — which is what lets it run headless as a pipeline stage as well as in an
interactive session. A project with no `docs/fdr.md` is the normal starting case rather than an error;
the FDR is used as context when it exists.

## What It Does

- **Expands a casual change request** into a `change_spec.md` with the scope, the behaviours, and the
  acceptance the downstream steps read.
- **Works with or without an FDR.** `docs/fdr.md` is context when present and never a precondition.
- **Holds the change to the records above it.** Every test or check the product's `nfdr.md`, `SDD.md`
  or an ADR requires of the change becomes a rule, even where the request leaves it out or defers it.
- **Opens the change's isolated worktree** at the front of its run, so the whole change arc lands on a
  branch rather than on `main`.
- **Halts with a report** instead of guessing or interviewing, using its own halt-report shape.
- **Writes into the change folder** under the project's `journey/tobiishi/<YYYY-MM-DD>_<slug>/`, on the
  change branch.

## File Structure

```
development-specs/
├── SKILL.md                  # the orchestrator: posture, the outputs, the workflow, the commit
├── README.md                 # this file
├── references/               # the shapes it writes from
│   ├── change_spec_template.md
│   ├── change_spec_template.preserving.md
│   ├── deferred_decisions_template.md
│   └── halt_report_template.md
└── evals/                    # behaviour evals, fixtures, and the trigger-eval set
```

## Depends On

- `<CORE>/doctrine/flow/change_classification.md` — how a change is classified.
- `<CORE>/doctrine/flow/step_outcome_contract.md` — what a flow step must report.
- `<CORE>/tools/create_change_worktree.py` — run in Step 4 to create the change's branch and worktree.

## When to Use

Reach for this when **an existing project needs a scoped, single change** specced — including as the
first stage of the change pipeline.

Not for: new projects or first-time specs (`product-fdr`), or changes that require updating the FDR,
ADR or NFDR decision files.
