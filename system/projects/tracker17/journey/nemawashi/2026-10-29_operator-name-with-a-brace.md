# 根回し Nemawashi seed — an operator name holding a curly brace breaks the People page

## What it is

Serves the Way `fit-to-publish`, which `system/michi.md` Way 5 ranks above it; cut now because tracker17 is the product the owner runs the crew on, and a page that crashes on a saved name is a defect in a walked feature (my reasoning, not a lookup). Moves the Agari toward **Works**: no error and no wrong result.

Today a saved operator name holding a curly brace, such as `{x}`, makes the People page raise on the address the save lands on. The Your name section builds its outcome paragraph as an f-string holding the already-escaped name, then calls `.format` on it (`products/tracker17/web/pages.py:L2819-L2829`), so the name's braces are read as format fields. After this, any name the form accepts is saved and shown on the People page as typed, and a test proves it.

## Source

Cut from `system/projects/tracker17/docs/seeds-from-idea/2026-10-29_operator-name-with-a-brace_brief.md`, whose ask quotes `tracker17 · nemawashi · 2026-10-11_delete-and-rename`'s recommendation from unit `2026-10-28_rename-a-project`, verbatim:

- "Cut a seed: an operator name holding a curly brace breaks the People page"
- "The Your name section builds its outcome paragraph with `str.format` over a line that already holds the escaped name, so a saved name such as `{x}` raises on the page the save lands on."
- "no document is wrong — the defect is code against settled text, so it is work, a seed."

Measured there: `POST /operator-name` with `name={x}`, then `GET` the address it redirects to → `KeyError: 'x'`. Checked on 2026-10-29: `grep -rn -i 'brace\|{x}' products/tracker17/tests` prints nothing, so no test covers it.

## Stations — dynamic checklist

- [ ] operator-name-with-a-brace — a name holding `{`, `}` or `{0}` is saved and shown on the People page as typed, on every outcome the Your name section shows (saved, refused, failed); a test per outcome; both suites pass

## Out (later / elsewhere)

Any other page that builds text with `.format` over a user-typed value: not named by the ask.
