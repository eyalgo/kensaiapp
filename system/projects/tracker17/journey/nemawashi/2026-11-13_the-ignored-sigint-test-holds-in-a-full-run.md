# 根回し Nemawashi seed — the ignored-SIGINT proof test holds in a full run

## What it is

Serves the Way `product-downstream`: the failure is in tracker17's own gate, the product the crew is proven on (my reasoning, not a lookup). Moves the Agari toward **Works**, which needs "the full automated suite passes" (`system/projects/tracker17/finish_line.md:L22-L24`).

`tests/integration/test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint` failed in a full run of the card's suite and passed alone at the base of `tracker17 · tobiishi · 2026-11-13_walk-skips-by-name` ("3296 passed, 1 failed, 2 skipped"), then passed in the next unit's full run ("3335 passed, 2 skipped", `tracker17 · tobiishi · 2026-11-13_behave-import-walk`, recorded in its refine report). It failed the same way on 2026-10-29, and `tracker17 · tobiishi · 2026-10-29_the-start-is-stoppable-from-its-ready-line` removed one cause, a Ctrl-C landing between the ready line and the `try`; the recurrence says another remains (my reasoning). The test hands a start case to a pytest launched with SIGINT ignored, and that case waits a fixed 30 seconds for the tracker to stop (`tests/integration/test_start.py:L707-L708`; `tests/integration/test_sigint_launch.py:L36-L38`). After this, the cause is named and removed, and a red full run no longer comes from this test.

## Source

Cut from `system/projects/tracker17/docs/seeds-from-idea/2026-11-13_the-ignored-sigint-test-fails-in-a-full-run_brief.md`, whose ask is the recommendation of `tracker17 · nemawashi · 2026-11-13_the-source-walk-sees-the-behave-folder`, at `2026-11-13_walk-skips-by-name_recommendations.md`: L8 "Cut a seed for the full-run timing failure of the ignored-SIGINT test"; L11 "a timing dependence in the product's own gate, carried by no seed or station. A red full run blocks any later seal."; L13 "it names work on the product's tests, not what a document should state."

## Stations — dynamic checklist

- [ ] the-ignored-sigint-cause — the timing dependence that fails the proof test in a full run is found and named, with a measurement that reproduces it, and removed; the test passes in a full run of the card's suite and alone, and both suites stay green

## Relation to existing work

Follows `tracker17 · tobiishi · 2026-10-29_the-start-is-stoppable-from-its-ready-line`, which closed the ready-line gap. Independent of `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract`.

## Out (later / elsewhere)

No wait limit is raised to hide the failure, and no test is skipped, retried or marked expected-to-fail.
