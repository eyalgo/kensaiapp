# 根回し Nemawashi seed — the browser suite passes on every run

## What it is

Serves the Way `fit-to-publish`, which `system/michi.md` Way 5 ranks above it; cut now because tracker17 is the product the owner runs the crew on (`products/tracker17/docs/PRD.md:L12-L14`), and a suite that fails at random stalls every later station's close and seal on it (my reasoning, not a lookup).

On `main`, `pytest products/tracker17/tests/e2e/` fails on some runs and passes on others. The failing tests are all focus tests, in `tests/e2e/test_first_project.py` (`L107`, `L158`) and `tests/e2e/test_people.py` (`L90`, `L142`). No cause has been found. After this, the suite exits 0 run after run, because the cause is found and fixed in the tests or in what they measure. That holds the Agari's **Works** bar, "the full automated suite passes" (`system/projects/tracker17/agari.md:L22-L24`), and the "the browser suite exits 0" bar every station sets.

## Source

Cut from `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`, retired at `ad8d6b151`. Three of its `shukuba-refine` recommendations asked for this cut: `2026-10-11_add-and-list-tasks` § 1, `2026-10-11_edit-task-fields` § 1 and `2026-10-12_task-labels` § 2. `nemawashi-refine` answered them on 2026-10-12. Those reviews measured 6 green runs of 9, then 4 of 7, then 7 of 8. The developer measured 3 failures in 6 runs on a copy of `main` that held none of their change (`fa243757d` body). Re-measured for this cut, 2026-10-12, on a `git archive a041368b6 products/tracker17` copy, `git init`-ed, with the README's `.venv`: 8 runs gave 6 × `27 passed`, 1 × `1 failed` (`test_a_refused_name_puts_focus_in_the_name_field_with_the_reason_as_its_description`) and 1 × `2 failed` (that test and `test_a_hand_built_201_character_name_gets_the_reason_and_none_of_the_text`). No product document states this work (`grep -i 'flak\|determinis\|intermittent'` over `products/tracker17/docs` matches nothing).

## Stations — dynamic checklist

- [x] browser-suite-every-run — the cause of the intermittent focus-test failures is named and fixed in the tests or what they measure (no retry or rerun plugin), and `pytest products/tracker17/tests/e2e/`, the whole folder as it stands on `main`, exits 0 on 20 consecutive runs on a `git archive` copy

Route kept as one station: finding the cause alone leaves the suite as flaky as before (a station whose only value is that the fix needs it), so diagnosis and fix are one capability and one merge. Divergence from the proposal: the line now names the whole `e2e/` folder as it stands, not the four tests listed, because `tests/e2e/test_labels.py` has landed since the cut and the bar is the folder's exit code.

## Relation to existing work

Every candidate in the pool sets a "both suites pass" bar, and this seed is what lets that bar be met reliably. None of them rests on it.

## Out (later / elsewhere)

New end-to-end tests, and any behaviour change the fix does not need. A retry or rerun plugin that hides a failure instead of fixing it does not count as a fix.
