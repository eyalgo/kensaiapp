# Cut report — an operator name holding a curly brace breaks the People page

*Brief: `system/projects/tracker17/docs/seeds-from-idea/2026-10-29_operator-name-with-a-brace_brief.md`. 2026-10-29. Outcome: cut.*

## The ask, line by line

| Ask line | Carried by | Or why not |
|---|---|---|
| "Cut a seed: an operator name holding a curly brace breaks the People page" | `tracker17 · nemawashi · 2026-10-29_operator-name-with-a-brace` | — |
| "The Your name section builds its outcome paragraph with `str.format` over a line that already holds the escaped name, so a saved name such as `{x}` raises on the page the save lands on." | `tracker17 · nemawashi · 2026-10-29_operator-name-with-a-brace` | — |
| "no document is wrong — the defect is code against settled text, so it is work, a seed." | `tracker17 · nemawashi · 2026-10-29_operator-name-with-a-brace` | — (the reason it is a seed, not a companion item) |

## Upstream items raised

none

## Earlier rulings this ask changes

none

## Could also be cut

- Other pages that call `.format` over text holding a user-typed value: `products/tracker17/web/pages.py` has several `.format` calls (e.g. L857, L882), not checked for the same defect.
