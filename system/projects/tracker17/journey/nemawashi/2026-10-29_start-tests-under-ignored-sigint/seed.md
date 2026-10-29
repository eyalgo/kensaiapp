# 根回し Nemawashi seed — the start tests time out when the suite is launched with SIGINT ignored

## What it is

Serves the Way `fit-to-publish`, which `system/michi.md` Way 5 ranks above it; cut now because tracker17 is the product the owner runs the crew on, and a suite that fails depending on how it is launched leaves the Agari's **Works** bar ("the full automated suite passes") unmeasurable by an unattended run (my reasoning, not a lookup).

Today a test that starts the real tracker in a child process stops it with SIGINT, as Ctrl-C does, and waits 30 seconds (`products/tracker17/tests/integration/test_start.py:L529`). Launched as a background job, the child inherits an ignored SIGINT, never stops, and the test times out; the start installs no signal handling of its own (`grep -n 'signal' products/tracker17/main.py` prints nothing). After this, the full suite passes the same way launched in the background as in the foreground. Whether the fix sits in the tests or in the start they drive is the walk's call — the ask names both.

Measured 2026-10-29 in a disposable clone at `418f71e31`: `pytest products/tracker17/tests/integration/test_start.py -k legacy_form` → `3 passed in 0.87s` in the foreground; one case as a background job → `1 failed in 30.17s`. `_run_real_start` has four callers in that file (`grep -n '_run_real_start(' …` → L560, L585, L708, L756), some parametrized; the refine's full-suite run counted 12 failures.

## Source

Cut from `system/projects/tracker17/docs/seeds-from-idea/2026-10-29_start-tests-under-ignored-sigint_brief.md`, whose ask quotes the recommendation `tracker17 · nemawashi · 2026-10-29_operator-name-with-a-brace` left from unit `2026-10-29_operator-name-with-a-brace`, verbatim:

- "Cut a seed: the start tests fail when the suite is launched with SIGINT ignored"
- "the Agari's **Works** bar needs the full automated suite to pass."
- "no document is wrong. The tests (or the start they drive) depend on how they were launched, so this is code work, a seed."

Earlier units met it and worked around it: `tracker17 · tobiishi · 2026-10-28_rename-a-project` and `tracker17 · tobiishi · 2026-10-29_operator-name-with-a-brace`, each in its `flow_findings/development-plan.md`.

## Stations — dynamic checklist

- [ ] start-tests-under-ignored-sigint — the product's two suites, `products/tracker17/tests/` and `products/tracker17/tests/e2e/`, each exit 0 in the foreground and with SIGINT ignored, with no `test_start.py` timeout, and a test that fails on `970f6a4ca` proves it

Route re-cut (stations-from-seed, 2026-10-29): kept as one station, since the ask is one capability with one acceptance boundary, and tightened its reached-when to an exit-0 background run; the foreground-versus-background wording was prose, not a check.
Route amended (shukuba-refine, 2026-10-29): the one root run covering four folders became the product's two suites, because the collection rule and five basenames shared by `unit/` and `e2e/` keep them apart; the proof test the first unit deferred was added to the line, so the station is not reached until it lands.

## Out (later / elsewhere)

Any change to what Ctrl-C does for an operator at a terminal: not named by the ask.
