# 宿場 Shukuba refine — recommendations to the Principal PM — `2026-10-29_operator-name-with-a-brace`

*From the review of unit `2026-10-29_operator-name-with-a-brace`, 2026-10-29. The report beside this file carries what the run
did; this file carries what it could not do and no companion can carry.*

## To the Principal PM

### 1. Retire `tracker17 · nemawashi · 2026-10-29_operator-name-with-a-brace` once its station closes

- **Kind:** a seed to retire
- **Why:** its one station's reached-when holds now; once the Scrum Master closes it, the checklist is fully walked. The retire is the Scrum Master's (`nemawashi-retire`).
- **Source:** report § Considered, not moved, row 1; `tracker17 · nemawashi · 2026-10-29_operator-name-with-a-brace` (line 21)
- **Why no companion carries it:** it is a seed's lifecycle, not something a document should state.

### 2. Cut a seed: the start tests fail when the suite is launched with SIGINT ignored

- **Kind:** a seed to cut
- **Why:** the Agari's **Works** bar needs the full automated suite to pass. In a disposable clone at the merge, launched as a background job (how unattended runs launch it), 12 `test_start.py` tests time out: the started tracker inherits an ignored SIGINT and never stops. The same tests pass in the foreground. Plan notes across several units met this and worked around it each time. No seed or station carries it.
- **Source:** clone at `fe98ceeb3`, `pytest products/tracker17/tests/` as a background job → `12 failed, 2639 passed in 779.04s`, all `subprocess.TimeoutExpired … timed out after 30 seconds`; one case backgrounded → `1 failed in 30.23s`, foreground → `3 passed in 0.31s`; `products/tracker17/tests/integration/test_start.py:529`; `grep -n 'signal' products/tracker17/main.py` → nothing
- **Why no companion carries it:** no document is wrong. The tests (or the start they drive) depend on how they were launched, so this is code work, a seed.
