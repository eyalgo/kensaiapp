# 宿場 Shukuba refine — recommendations to the Principal PM — `2026-10-11_edit-task-fields`

*From the review of unit `2026-10-11_edit-task-fields`, 2026-10-12. The report beside this file carries what the run
did; this file carries what it could not do and no companion can carry.*

## To the Principal PM

### 1. Cut a seed that makes tracker17's browser suite pass on every run

- **Kind:** a seed to cut
- **Why:** Every station's bar includes "the browser suite exits 0", and on `main` the suite fails on some runs, in People and first-project focus tests. The last review recommended this cut too. No seed carries it yet, and it fails again after this unit.
- **Source:** Measured in this run on a `git archive HEAD products/tracker17` copy, `git init`-ed: `pytest products/tracker17/tests/e2e/` run 7 times gave 4 × `23 passed` and 3 failed runs, one of them `test_people.py::test_a_stale_remove_focuses_the_heading_with_the_reason_and_a_reload_link`. The developer saw `test_first_project.py::test_a_refused_name_puts_focus_in_the_name_field_with_the_reason_as_its_description` fail once (`7ada48cae` body). The earlier measurement is in `2026-10-11_add-and-list-tasks_recommendations.md` § 1.
- **Why no companion carries it:** It is work, fixing the tests or what they measure, and not something a document should state.
