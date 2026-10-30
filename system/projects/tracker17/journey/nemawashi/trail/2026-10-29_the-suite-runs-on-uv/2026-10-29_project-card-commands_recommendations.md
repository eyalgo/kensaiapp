# 宿場 Shukuba refine — recommendations to the Principal PM — `2026-10-29_project-card-commands`

*From the review of unit `2026-10-29_project-card-commands`, 2026-10-30. The report beside this file carries what the run
did; this file carries what it could not do and no companion can carry.*

## To the Principal PM

### 1. Retire `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv` once its last station closes

- **Kind:** a seed to retire
- **Why:** Stations 1 and 2 are ticked, and station 3's reached-when holds on `main` (report, Considered row 1); once the Scrum Master closes it, every line is walked.
- **Source:** `tracker17 · nemawashi · 2026-10-29_the-suite-runs-on-uv` (lines 17-19); fresh-clone Setup exit 0 and Test exit 0 (`2698 passed`, `121 passed`) at `84f95461e`
- **Why no companion carries it:** it is a decision about a seed, not what a document states.

### 2. Settle where a change worktree runs the card's `Setup command:`, in kensaiapp's core

- **Kind:** a route across projects
- **Why:** The card template says the setup runs "in the directory Test command: runs in", which is the worktree root, but worktree creation runs it in the product's directory. tracker17's card works either way only because it names its directory absolutely; the shorter form its own station gave as an example would break. The unit's spec handed this to nobody, and no live seed carries it.
- **Source:** `core/templates/project_template.md:11`; `core/tools/create_change_worktree.py:15`, `:473-476`; `change_spec.md` § Out of Scope, last line (`tracker17 · tobiishi · 2026-10-29_project-card-commands`); `grep -rlnE 'create_change_worktree|Setup command' system/nemawashi system/projects/*/journey/nemawashi` → no live seed on it
- **Why no companion carries it:** the work is in kensaiapp's core, outside tracker17's product documents, so it is a seed for the project that owns the core tooling.
