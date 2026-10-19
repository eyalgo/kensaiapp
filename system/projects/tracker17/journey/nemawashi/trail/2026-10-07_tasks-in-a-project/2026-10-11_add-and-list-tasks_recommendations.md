# 宿場 Shukuba refine — recommendations to the Principal PM — `2026-10-11_add-and-list-tasks`

*From the review of unit `2026-10-11_add-and-list-tasks`, 2026-10-11. The report beside this file carries what the run
did; this file carries what it could not do and no companion can carry.*

## To the Principal PM

### 1. Cut a seed that makes tracker17's browser suite pass on every run

- **Kind:** a seed to cut
- **Why:** The browser suite is a gate on every station, and it fails on some runs on `main`, in People and first-project focus tests. Each station's "the suites pass" bar is met only on some runs. No seed carries the fix.
- **Source:** Measured in this run on a `git archive HEAD` copy: `pytest products/tracker17/tests/e2e/` run 9 times gave 6 runs of `21 passed` and 3 failed runs. The failures included `test_people.py::test_people_keyboard_refusals_and_removal_keep_focus_at_the_action` and `test_first_project.py::test_a_refused_name_puts_focus_in_the_name_field_with_the_reason_as_its_description`. The developer measured the same on a copy of `main` holding none of the change, 3 of 6 runs, cause not found (`fa243757d`, body L57).
- **Why no companion carries it:** It is work, fixing the tests or what they measure, not something a document should state.
