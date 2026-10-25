# Release notes

What each release of KensaiApp changed, newest first. Releases are numbered 0.x until v1; a 0.x
release makes no promise of stability, as the README's section "What it does not promise" says.

## 0.4.0 — 2026-10-25

### KensaiApp

- A new step in every change, Security, between Prove and Audit: the senior engineer runs the
  product's dependency audit and reads the change's code for security holes. It fixes what its rules
  allow, writes an exception for an advisory the product does not reach, and reports the rest for the
  PM. It stops the walk only when a fix needs a move it may not make. It is a first iteration.
- **If you set up a clone of an earlier release**, add `security = "claude"` under `[steps]` in your
  `.providers.toml`, as `.providers.toml.example` now has it: a step with no entry is refused by name.
- `dependency-repair`: when a product's main branch turns red with no commit behind it, because its
  dependency audit reads an advisory published since the last green run, the chain repairs it once on
  a branch and merges it before it stops the walk.
- A new stop, `environment-not-ready`, when a test environment cannot install the product's languages
  or dependencies, before any test runs.
- Where a product's CI runs a matrix, each version gets its own test container.
- `--gate-owners-mac` carries from a walk to the queue after it, and `build-idea` takes it.
- `seeds-from-idea` runs in a session, from the `principal-pm` group, and has no launcher. An idea
  arrives as a brief you confirm, with the files it rests on quoted and checked.
- `ad-hoc-plan` starts from a brief you confirm, and every run leaves a report beside it.
- The panel shows how long a walk and its step have run, and which task of the plan the build is on.

### The front door

- A new guide, How it works: the three checks on a change, where what they find goes, the PM's review
  of the route, the two kinds of finding, when a walk stops for you, and what a change costs.
- The pipeline in the README and the overview diagram show the Security step.
- The audit is described as what it is: a check of how well each of KensaiApp's steps did its job,
  not of the product, which is why it does not stop a change.
- What KensaiApp does not promise is said more plainly, and the README says it may support other
  workflows with the right adjustments.
- ka-telemetry's entry links what building it cost.

## 0.3.0 — 2026-10-22

### KensaiApp

- Telemetry and the context cap run on [ka-telemetry](https://github.com/eyalgo/ka-telemetry), an
  open-source package KensaiApp built, on PyPI as `ka-telemetry`. The bundled receiver and its
  settings script are gone: the package is installed once into `~/.kensaiapp/venv`, and
  `.telemetry.env` names its command.
- The panel shows each project's route as a tree.
- A walk's gates stop before implementation when a product still owes a decision on where its tests
  run.

### The front door

- The README carries a version badge, and the Python badge reads 3.13+.
- Getting started lists pytest and pytest-xdist in step 1, with their install command. Setting up
  your first project is step 4, and the two optional steps, the panel and telemetry, follow it.
- Telemetry's setup moved to a new how-to section, How to collect telemetry.
- A new README section, Built with KensaiApp, lists ka-telemetry.
- The how-to guide names the check to run after a Python upgrade, and the stop a walk makes when a
  product owes that decision on where its tests run.

### tracker17

- A task in `todo` or `in-progress` has a `cancelled` move on its list row and its page. The first
  press opens a confirmation in place, and only confirming saves the move.
- Going Back in the browser after confirming no longer brings the old confirmation back to life.
- A move pressed on a page whose task has since changed status saves nothing, and the page says the
  status has changed and which moves it now allows.
- The timed run covers a status move at 1,000 tasks of 20 comments each.

## 0.2.0 — 2026-10-19

### The front door

- The README is reordered for a first-time reader: what KensaiApp is, who it is for, how one change
  moves, how the work is kept in check and how to start, with an overview diagram and one shipped
  change walked through its files.
- The reference material moved, word for word, into two new guides, the architecture overview and
  the operations guide.

### tracker17

- A task can be moved through its status workflow.

## 0.1.0 — 2026-10-19

The first release: the shared core, the roles, the skills, the tools, the launchers, the hooks and
the templates a fresh clone needs, with two example projects, tracker17 and swe-benchmark-poc.
