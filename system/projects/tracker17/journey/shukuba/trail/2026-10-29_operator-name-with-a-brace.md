# 宿場 Shukuba — the People page shows an operator name holding a curly brace

*Item 1 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-29_operator-name-with-a-brace`. Slug: `operator-name-with-a-brace`.*

## What it is

A saved operator name such as `{x}` makes the People page raise on the address the save lands on. `_your_name_section` (`products/tracker17/web/pages.py`) puts the already-escaped outcome line into an f-string and then calls `.format` on it, so the name's braces are read as format fields. This station makes the Your name section show any name the form accepts as typed, on every outcome (saved, refused, failed), and proves it with tests. It is one defect in one function, so it is one merge; splitting by outcome would leave two outcomes still crashing.

## Reached when

1. `POST /operator-name` with `name={x}`, then `GET` of the address it redirects to, returns the People page with no error. The same holds for `name=}` and `name={0}`. This holds on the saved outcome and on the failed outcome (a save that fails shows the same section).
2. The saved line and the failed line show the name exactly as typed, with its braces (HTML-escaped as before).
3. With `{x}` already saved, a blank submission and a too-long submission each show their refusal line, and the page returns with no error. One test each.
4. For the saved outcome and for the failed outcome, one test each fails on the code at the commit this station was opened from and passes after the change. A refusal line carries no name, so the refusal tests are guards and are not required to fail beforehand.
5. `pytest products/tracker17/tests/` passes in a disposable clone at the merged commit, with its unit, integration, e2e and architecture folders all collected.

## Guardrail

- The fix keeps the outcome lines' wording, CSS classes, ids and focus behaviour exactly as they are; only how the name reaches the page changes.
- No other page's text building is touched, and no document is edited to fit the code.
- **Not here:** any other page that builds text with `.format` over a user-typed value, which this seed's Out section leaves to a later seed.
