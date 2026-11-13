# Brief — the ignored-SIGINT proof test fails in a full run and passes alone

## Owning project

`tracker17`

## The ask

system/projects/tracker17/journey/nemawashi/trail/2026-11-13_the-source-walk-sees-the-behave-folder/2026-11-13_walk-skips-by-name_recommendations.md:L8-L8 "Cut a seed for the full-run timing failure of the ignored-SIGINT test"

system/projects/tracker17/journey/nemawashi/trail/2026-11-13_the-source-walk-sees-the-behave-folder/2026-11-13_walk-skips-by-name_recommendations.md:L11-L11 "failed in a full run of the card's suite and passed alone — a timing dependence in the product's own gate, carried by no seed or station. A red full run blocks any later seal."

system/projects/tracker17/journey/nemawashi/trail/2026-11-13_the-source-walk-sees-the-behave-folder/2026-11-13_walk-skips-by-name_recommendations.md:L13-L13 "it names work on the product's tests, not what a document should state."

## Evidence

The failure, seen at the base of the unit that raised it:

system/projects/tracker17/journey/tobiishi/trail/2026-11-13_walk-skips-by-name/tl_instruction.md:L35-L35 "3296 passed, 1 failed, 2 skipped"

system/projects/tracker17/journey/tobiishi/trail/2026-11-13_walk-skips-by-name/tl_instruction.md:L35-L35 "passed when run alone, so it is a full-run timing failure"

It has failed this way before, and the earlier fix closed one cause — a Ctrl-C landing between the ready line and the `try` — not every cause:

system/projects/tracker17/journey/tobiishi/trail/2026-10-29_the-start-is-stoppable-from-its-ready-line/change_request.md:L21-L22 "fail once in a full … foreground run that took 782 s"

The test hands a selected start case to a pytest launched with SIGINT ignored; that case waits a fixed 30 seconds for the tracker to stop:

products/tracker17/tests/integration/test_sigint_launch.py:L36-L37 "Longer than the 30 seconds the selected case waits for its tracker to stop"

products/tracker17/tests/integration/test_start.py:L707-L708 "child.communicate(timeout=30)"

## Security source

none

## Already swept

- No candidate carries it: the pool holds one candidate, `tracker17 · nemawashi · 2026-11-13_one-fake-and-one-contract-suite-per-contract`, about the `Saver` and `Clock` fakes; `git grep -n ignores_sigint -- system/projects/tracker17/journey/nemawashi/unpicked` printed nothing (this run's).
- No product document should state it: the recommendation's L13, quoted above; NFR-11's behaviour — a quiet stop on Ctrl-C — is already stated, and the defect is that its proof does not hold under load.

## Look at

- `products/tracker17/tests/integration/test_sigint_launch.py` — the proof test and its outer deadline.
- `products/tracker17/tests/integration/test_start.py` — the selected start case, which stops the tracker with SIGINT and waits 30 seconds.
- `products/tracker17/main.py` — `start`, the code the child runs, in case the cause is the product's rather than the test's.

## Out

No wait limit is raised to hide the failure, and no test is skipped, retried or marked expected-to-fail.

## Rulings

none
