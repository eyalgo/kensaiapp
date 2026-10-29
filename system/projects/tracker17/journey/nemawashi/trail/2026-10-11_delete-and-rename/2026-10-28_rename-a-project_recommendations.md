# 宿場 Shukuba refine — recommendations to the Principal PM — `2026-10-28_rename-a-project`

*From the review of unit `2026-10-28_rename-a-project`, 2026-10-28. The report beside this file carries what the run
did; this file carries what it could not do and no companion can carry.*

## To the Principal PM

### 1. Cut a seed: an operator name holding a curly brace breaks the People page

- **Kind:** a seed to cut
- **Why:** The Your name section builds its outcome paragraph with `str.format` over a line that already holds the escaped name, so a saved name such as `{x}` raises on the page the save lands on. It is a defect in a walked feature (operator name), outside this unit's reach, and no seed in the pool carries People.
- **Source:** `products/tracker17/web/pages.py:L2673-L2684`; measured in a scratch clone at `1eecb6c0e`: `POST /operator-name` with `name={x}` → `303 /people?operator_saved=%7Bx%7D`, then `GET` that address → `KeyError: 'x'` at `pages.py:2682`; `_your_name_section('a{0}b', …)` → `ValueError`. Raised first in the developer's closing commit `<a commit not in the public history>` (Developer Review Notes, task 3).
- **Why no companion carries it:** no document is wrong — the defect is code against settled text, so it is work, a seed.
