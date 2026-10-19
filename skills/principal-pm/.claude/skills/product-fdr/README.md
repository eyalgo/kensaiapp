# product-fdr

Before anyone designs a change, somebody has to say what the product already does — and say it
without leaving holes the next person fills in by guessing. `product-fdr` is the **Principal PM**'s
tool for producing that document, `docs/fdr.md`: the behavioural contract plus the product decisions
a later change must honour or escalate. It belongs to the **foundation step** — written once per
product, from the settled PRD, SRS and SDD, after the SDD settles.

**Its finish line is that nothing is left open**, and it gets there without ever asking a question
mid-run. The skill drafts the whole FDR best-effort and parks what it cannot settle in a companion
open-issues file the owner answers on their own time; a re-run folds those answers in. When the
companion is gone, the FDR is done — that absence is the done signal, and it is what lets the run
work headless as well as in a session.

## Version and ratification

`1.2.0` — set at the landing merge of 2026-08-30, which moved the marker twice in one branch. It has no ratification record yet.

## What It Does

- **Derives the FDR from the three settled upstream documents** — the PRD, the SRS and the SDD — and
  halts rather than guessing when one of them is missing.
- **Surfaces rather than interviews.** Anything the three sources do not settle becomes an item in
  the companion, led with the run's reasoning and, for a drafted call, with the answer to confirm.
- **Keeps the owner's answers.** Every answered companion is copied whole to `docs/trail/fdr/`
  before the fold rewrites it, so what the owner decided and why stays readable and citable.
- **Holds the requirements/design boundary.** What the product must do, its business rules, its
  error conditions and its product decisions belong in the FDR; module names, class names, file
  paths and code strategy belong to the SDD and the ADR. The test that draws the line is the
  authoring prompt's.
- **Runs once per product**, in the foundation step — after the SDD, not at project setup.

## File Structure

```
product-fdr/
├── SKILL.md     # the orchestrator: posture, the file loop, path resolution, staging, the commit
├── README.md    # this file
├── stack.json   # the substance files, read by the cold-read manifest
└── evals/       # behaviour evals
    └── evals.json
```

## Depends On

- `prompts/rich.md` — the authoring prompt: **how** to derive the FDR.
  The skill orchestrates; this file holds every rule the author applies.
- `<CORE>/templates/product-templates/fdr_template.md` — the FDR's section shape, and
  `fdr_open_issues_template.md` beside it — the companion's.
- `launcher.md` — what `<CORE>/launchers/skill/launcher.sh` reads to start the run as a
  `principal-pm` background agent and report when it finishes.

## Launching It

From the instance root:

```
<CORE>/launchers/skill/launcher.sh product-fdr <project> [--dry-run] [--keep-awake]
```

The prompt is a fixed literal in `launcher.md`, so nothing a caller types reaches the run; the
launcher detaches a completion watcher whose `fdr` reporter says, when the run stops, where the FDR
and its companion stand.

## When to Use

Reach for this when **a product's foundation is being laid** — its SDD has settled and the
behavioural contract every later change is built against has to be written — or when an answered
companion is waiting to be folded back in.

Not for: a single scoped change to an existing product (`development-specs`), the upstream documents
it derives from (`product-prd`, `product-srs`, `product-sdd`), the project's terminus
(`project-agari`), or the architecture records beside it (`product-architecture`).
