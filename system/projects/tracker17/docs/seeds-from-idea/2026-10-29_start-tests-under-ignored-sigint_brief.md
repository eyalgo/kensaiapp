# Brief — the start tests time out when the suite is launched with SIGINT ignored

## Owning project

`tracker17`

## The ask

system/projects/tracker17/journey/nemawashi/trail/2026-10-29_operator-name-with-a-brace/2026-10-29_operator-name-with-a-brace_recommendations.md:L15-L15 "Cut a seed: the start tests fail when the suite is launched with SIGINT ignored"

system/projects/tracker17/journey/nemawashi/trail/2026-10-29_operator-name-with-a-brace/2026-10-29_operator-name-with-a-brace_recommendations.md:L18-L18 "the Agari's **Works** bar needs the full automated suite to pass."

system/projects/tracker17/journey/nemawashi/trail/2026-10-29_operator-name-with-a-brace/2026-10-29_operator-name-with-a-brace_recommendations.md:L20-L20 "no document is wrong. The tests (or the start they drive) depend on how they were launched, so this is code work, a seed."

## Evidence

The recommendation's own measurement, taken in a disposable clone at the merge:

system/projects/tracker17/journey/nemawashi/trail/2026-10-29_operator-name-with-a-brace/2026-10-29_operator-name-with-a-brace_recommendations.md:L19-L19 "one case backgrounded → `1 failed in 30.23s`, foreground → `3 passed in 0.31s`"

The test stops the started tracker the way Ctrl-C does, and waits 30 seconds for it:

products/tracker17/tests/integration/test_start.py:L529-L529 "child.send_signal(signal.SIGINT)"

The start installs no signal handling of its own: `grep -n 'signal' products/tracker17/main.py` printed nothing (session's).

Earlier units met the same failure and worked around it rather than routing it:

system/projects/tracker17/journey/tobiishi/trail/2026-10-29_operator-name-with-a-brace/flow_findings/development-plan.md:L10-L10 "(all `tests/integration/test_start.py`, SIGINT ignored without a terminal)"

system/projects/tracker17/journey/tobiishi/trail/2026-10-28_rename-a-project/flow_findings/development-plan.md:L8-L8 "say the failures come from socket binding and SIGINT handling"

## Security source

none

## Already swept

- No candidate carries it: `grep -rln -i 'sigint' system/projects/tracker17/journey/nemawashi/unpicked` printed nothing; the pool holds one candidate, `tracker17 · nemawashi · 2026-10-11_protect-saved-data`, about unreadable saved data and a second tracker (session's).
- No product document should state it: the recommendation's L20, quoted above.

## Look at

- `products/tracker17/tests/integration/test_start.py` — `_run_real_start`, which starts the tracker in a child process and stops it with SIGINT.
- `products/tracker17/main.py` — `start`, the code the child runs.

## Out

none

## Rulings

none
