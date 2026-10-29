# 宿場 Shukuba — the project card sets up and runs the suite through uv

*Item 3 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv`. Slug: `project-card-commands`.*

## What it is

Change the two lines of `system/projects/tracker17/project.md` the chain runs in a new change worktree. `Setup command:` stops being `none` and makes the suite's environment from `uv.lock`; `Test command:` runs the suite through uv. Both run from the worktree's root, while `pyproject.toml` and `uv.lock` sit in `products/tracker17`, so each command names that directory (for example `uv sync --locked --project products/tracker17`). The Playwright browser the end-to-end layer needs is the setup's to make ready, if the suite run shows it is not otherwise there. One station because the two commands are one fact: the environment the setup makes is the one the test command runs in.

## Reached when

All hold on `main` after the change lands, checked in a fresh clone of the repository, from its root:

1. The card's `**Setup command:**` value is not `none` and contains the word `uv`; the card's `**Test command:**` value contains the word `uv` and no bare leading `pytest` (`grep -nE '^\*\*(Setup|Test) command:\*\*' system/projects/tracker17/project.md` shows both lines; before the work the Setup line reads `none` and the Test line begins `pytest`).
2. In that clone, with no `products/tracker17/.venv` present beforehand, the card's Setup command run through `/bin/sh` from the clone's root exits 0, and `products/tracker17/.venv` exists afterwards.
3. Then the card's Test command run through `/bin/sh` from the same root exits 0, with the unit, integration, architecture and end-to-end layers collected (the run's summary line shows no collection error and no deselected layer).
4. `git diff --stat` between the commit before this change and its merge touches `system/projects/tracker17/project.md` and nothing under `products/tracker17/` other than a README sentence the edit makes false.

## Guardrail

- `pyproject.toml`, `uv.lock`, every test and all tracker code stay as they are: no pin, test or marker is changed to make the commands pass.
- The suite is not narrowed: the Test command still runs `products/tracker17/tests/` whole, with no layer excluded.
- The card's other lines (`Product path:`, `Languages:`, `Execution type:` and the rest) stay as they are; the template comments on the two lines stay.
- The README's uv instructions are done (`tracker17 · shukuba · 2026-10-29_readme-on-uv`) and are not re-written here.
- **Not here:** QC-40's review moment and QC-60's Python 3.11 run, which are held outside this seed (`tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv`, § Out); the SDD prerequisites wording (companion `SDD_open_issues.md` § 5.1); README `## Status` (`readme-status`).
