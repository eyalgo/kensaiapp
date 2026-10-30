# Change request — 2026-10-29_project-card-commands

---

**Request:** Change the two commands on the project card (`system/projects/tracker17/project.md`) that the chain runs in a new change worktree, so the suite is set up and run through uv. The Setup command stops being `none` and makes the suite's environment from `uv.lock` (for example `uv sync --locked --project products/tracker17`). The Test command runs the whole suite through uv (for example `uv run --project products/tracker17 pytest products/tracker17/tests/`) instead of a bare `pytest`. Both commands run from the worktree's root, while `pyproject.toml` and `uv.lock` sit in `products/tracker17`, so each names that directory. If a run of the suite shows the Playwright browser the end-to-end layer needs is not otherwise there, the Setup command makes it ready too. The card's `.venv` must come out under `products/tracker17`. One change, one merge: the two commands are one fact, since the environment the setup makes is the one the test command runs in.

What must not be weakened: `pyproject.toml`, `uv.lock`, every test and all tracker code stay as they are, and no pin, test or marker is changed to make the commands pass. The suite is not narrowed: the Test command still runs `products/tracker17/tests/` whole, with no layer excluded. The card's other lines (`Product path:`, `Languages:`, `Execution type:` and the rest) and the template comments on the two lines stay as they are. The README's uv instructions are done and are not re-written. Not here: the review moment (QC-40), the Python 3.11 run (QC-60), the SDD prerequisites wording, and the README `## Status`.

Acceptance (the station's reached-when, checked in a fresh clone from its root): (1) the Setup value is not `none` and contains `uv`, the Test value contains `uv` and no bare leading `pytest`; (2) with no `products/tracker17/.venv` beforehand, the Setup command through `/bin/sh` exits 0 and `.venv` exists afterwards; (3) the Test command through `/bin/sh` exits 0 with the unit, integration, architecture and end-to-end layers collected; (4) the diff touches `system/projects/tracker17/project.md` and nothing under `products/tracker17/` beyond a README sentence the edit makes false.

**Category:** nfdr
**Behaviour:** changing
**Classified because:** the station changes the card's Setup and Test commands, which are the tooling that says pass or fail for every later change; a check that decides its verdict on a different basis is a changed observable (`change_classification.md` § Category notes, `nfdr`).

**Sealed:** 2026-10-30 — accepted; merged to `main` via `--no-ff`.
Environment: owners-mac — no CI
