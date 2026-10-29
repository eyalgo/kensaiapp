# Brief — an operator name holding a curly brace breaks the People page

## Owning project

`tracker17`

## The ask

system/projects/tracker17/journey/nemawashi/trail/2026-10-11_delete-and-rename/2026-10-28_rename-a-project_recommendations.md:L8-L8 "Cut a seed: an operator name holding a curly brace breaks the People page"

system/projects/tracker17/journey/nemawashi/trail/2026-10-11_delete-and-rename/2026-10-28_rename-a-project_recommendations.md:L11-L11 "The Your name section builds its outcome paragraph with `str.format` over a line that already holds the escaped name, so a saved name such as `{x}` raises on the page the save lands on."

system/projects/tracker17/journey/nemawashi/trail/2026-10-11_delete-and-rename/2026-10-28_rename-a-project_recommendations.md:L13-L13 "no document is wrong — the defect is code against settled text, so it is work, a seed."

## Evidence

The defect still stands on `main` at the time of writing; the line numbers the recommendation cites have moved (session's):

products/tracker17/web/pages.py:L2819-L2819 "paragraph = f'<p class="

products/tracker17/web/pages.py:L2827-L2827 "completion_block = paragraph.format("

The recommendation's own measurement, taken in a scratch clone:

system/projects/tracker17/journey/nemawashi/trail/2026-10-11_delete-and-rename/2026-10-28_rename-a-project_recommendations.md:L12-L12 "then `GET` that address → `KeyError: 'x'`"

`grep -rn -i 'brace\|{x}' products/tracker17/tests` printed nothing: no test covers a name holding a brace (session's).

## Security source

none

## Already swept

- No candidate carries it: `grep -rln -i 'people\|operator name\|your name' system/projects/tracker17/journey/nemawashi/unpicked` printed nothing; the pool holds one candidate, `tracker17 · nemawashi · 2026-10-11_protect-saved-data`, about unreadable saved data (session's).
- No product document should state it: the documents already state the Your name behaviour, and the defect is the code failing it for one kind of input (the recommendation's L13, quoted above).

## Look at

- `products/tracker17/web/pages.py` — `_your_name_section`, where the outcome paragraph is built.
- `products/tracker17/web/pages.py` — `_operator_line`, which builds the line holding the escaped name.

## Out

none

## Rulings

none
