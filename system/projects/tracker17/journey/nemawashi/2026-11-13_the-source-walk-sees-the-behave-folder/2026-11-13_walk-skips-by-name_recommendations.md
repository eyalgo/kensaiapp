# 宿場 Shukuba refine — recommendations to the Principal PM — `2026-11-13_walk-skips-by-name`

*From the review of unit `2026-11-13_walk-skips-by-name`, 2026-11-13. The report beside this file carries what the run
did; this file carries what it could not do and no companion can carry.*

## To the Principal PM

### 1. Cut a seed for the full-run timing failure of the ignored-SIGINT test

- **Kind:** a seed to cut
- **Why:** `tests/integration/test_sigint_launch.py::test_real_start_stops_when_pytest_launch_ignores_sigint` failed in a full run of the card's suite and passed alone — a timing dependence in the product's own gate, carried by no seed or station. A red full run blocks any later seal.
- **Source:** `tl_instruction.md` § TL Review Notes, *Gate command checked*, of `tracker17 · tobiishi · 2026-11-13_walk-skips-by-name` ("3296 passed, 1 failed, 2 skipped … passed when run alone"); `flow_findings/development-plan.md` of the same unit; `products/tracker17/tests/integration/test_sigint_launch.py:L36-L77` (fixed waits of 30 seconds and an outer deadline)
- **Why no companion carries it:** it names work on the product's tests, not what a document should state.
