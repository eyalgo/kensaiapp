# 宿場 Shukuba refine — recommendations to the Principal PM — `2026-10-29_the-start-is-stoppable-from-its-ready-line`

*From the review of unit `2026-10-29_the-start-is-stoppable-from-its-ready-line`, 2026-10-29. The report beside this file carries what the run
did; this file carries what it could not do and no companion can carry.*

## To the Principal PM

### 1. Retire `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint` once its one station closes

- **Kind:** a seed to retire
- **Why:** The seed's only station is reached on `main`; once the Scrum Master closes it, the whole checklist is walked. The retire is the Scrum Master's, after which `nemawashi-refine` names the next pick.
- **Source:** `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint` (line 23); the report beside this file, Considered row 1 (clone at `5768d462e`: both suites exit 0 in both launches; the proof fails at `970f6a4ca`)
- **Why no companion carries it:** it is a decision about a seed, not what a document should state.

### 2. Cut a seed: move the product's test suite to the uv environment SDD § 4 RT-4 and NFDR QC-39 now state

- **Kind:** a seed to cut
- **Why:** SDD v15 and NFDR v19 settled the suite's environment on uv (`uv.lock`, `uv sync --locked`, `uv run`), and QC-39's `uv lock --check` gate fails on `main`; the product still makes it with `venv` and `pip` from `tests/requirements.txt`. No seed or station carries the move, and it is outside the active seed's scope. The SDD names placing it as the PM's, which needs a seed in the pool first.
- **Source:** `products/tracker17/docs/SDD.md:2838-2840`; `products/tracker17/docs/nfdr.md:358`; `products/tracker17/README.md:97-99`; clone at `5768d462e`: `uv lock --check` → exit 2, no `uv.lock`; `tracker17 · tobiishi · 2026-10-29_the-start-is-stoppable-from-its-ready-line`, `deferred_decisions.md` (Owner: none)
- **Why no companion carries it:** the documents already state it; what is missing is product work, a seed.
