# 宿場 Shukuba refine — recommendations to the Principal PM — `2026-10-12_task-labels`

*From the review of unit `2026-10-12_task-labels`, 2026-10-12. The report beside this file carries what the run
did; this file carries what it could not do and no companion can carry.*

## To the Principal PM

### 1. Retire `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project` once `task-labels` closes

- **Kind:** a seed to retire
- **Why:** Three of its four stations are ticked. The fourth, `task-labels`, is reached and its close is owed. After that close every line is walked.
- **Source:** `seed.md` § Stations — dynamic checklist; the report beside this file, Considered row 1 (gates measured on a `git archive 1aaa622e9` copy).
- **Why no companion carries it:** A retire is a move on the route, not something a document states.

### 2. Cut a seed that makes tracker17's browser suite pass on every run

- **Kind:** a seed to cut
- **Why:** Every station's bar asks the browser suite to exit 0, and on `main` it still fails on some runs. The last two reviews recommended this cut, and no seed carries it yet.
- **Source:** Measured in this run on a `git archive 1aaa622e9 products/tracker17` copy, `git init`-ed: 8 runs of `pytest products/tracker17/tests/e2e/` gave 7 × `27 passed` and 1 × `1 failed, 26 passed` (`test_first_project.py::test_a_hand_built_201_character_name_gets_the_reason_and_none_of_the_text`). Earlier measurements: `2026-10-11_edit-task-fields_recommendations.md` § 1.
- **Why no companion carries it:** It is work — fixing the tests or what they measure — and not something a document should state.
