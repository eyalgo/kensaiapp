# Release notes

What each release of KensaiApp changed, newest first. Releases are numbered 0.x until v1; a 0.x
release makes no promise of stability, as the README's section "What it does not promise" says.

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
