# Cut report — the start tests time out when the suite is launched with SIGINT ignored

*Brief: `system/projects/tracker17/docs/seeds-from-idea/2026-10-29_start-tests-under-ignored-sigint_brief.md`. 2026-10-29. Outcome: cut.*

## The ask, line by line

| Ask line | Carried by | Or why not |
|---|---|---|
| "Cut a seed: the start tests fail when the suite is launched with SIGINT ignored" | `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint` | — |
| "the Agari's **Works** bar needs the full automated suite to pass." | `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint` | — |
| "no document is wrong. The tests (or the start they drive) depend on how they were launched, so this is code work, a seed." | `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint` | — |

## Upstream items raised

none

## Earlier rulings this ask changes

none

## Could also be cut

- The e2e harness stops its tracker with SIGINT too (`products/tracker17/tests/e2e/conftest.py:L55-L56`); the refine's run saw e2e pass, so it is not measured failing. The seed's full-suite bar would catch it if it did.

## Sweep

`grep -rli 'sigint' system/nemawashi system/projects/*/journey/nemawashi` → only the retired seed's own refine files; no candidate or trail seed carries it. Claim re-measured in a disposable clone at `418f71e31`: foreground `3 passed in 0.87s`, background `1 failed in 30.17s`.
