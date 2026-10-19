# Code integrity report — 2026-10-11_add-and-list-tasks

Integrity: pass

**Reviewer:** Senior Engineer, `development-code-integrity`, 2026-10-11 · **Outcome:** clean pass. One
test was added and the code was not changed.

## Deferrals

None. The closing marker `fa243757d` (`developer: 2026-10-11_add-and-list-tasks — implementation
complete`) carries no `Deferred:` line and reads `Suite: green`.

## What was reviewed

Everything the change put under `products/tracker17/` in `main..fa243757d`:

- `domain/` — `tasks.py`, `priorities.py` and `due_dates.py`, which are new, plus `state.py`,
  `refusals.py` and `__init__.py`.
- `application/` — `tracker.py` and `__init__.py`.
- `persistence/saved_data.py`.
- `web/` — `routes.py`, `pages.py` and `style.css`.
- `tests/timed_run.py`, and the 20 test files the change added or modified.

## The intent it was checked against

- `tl_instruction.md` — Tasks 1 to 5 and each task's *Behaviours to verify*.
- `change_spec.md` — CP-106 to CP-143 and its Examples.
- `change_design.md` — sections 2 to 5.
- `change_text.md` — every published string. Each string in `web/pages.py` and the console line in
  `web/routes.py` was compared with this file and matches it word for word.
- `docs/fdr.md` was not needed.

## Tests added or fixed

- **Added:** `tests/integration/test_task_pages.py::test_the_page_builder_shows_no_sent_text_beside_a_too_long_title`
  (CP-118). The route drops every sent field when a title is too long, and `pages.project_page`
  enforces the same rule a second time on its own, as `TaskForm`'s docstring states. No test
  covered the page builder's guard: deleting it left all 573 tests green. The new test hands the
  builder a too-long outcome together with sent fields. It asserts that the page shows none of
  them, that the form shows its opening values, and that focus and the reason are on the title.
  It fails when the guard is removed.
- The module docstring now names CP-118.
- **Fixed:** none. No existing test asserted behaviour that contradicts the intent.

## The finding

**No bugs.** The code does what CP-106 to CP-143 say.

The suites were checked by mutation. Each of 37 changes to the rules this change wrote was applied
to a disposable `git archive` copy, and the non-browser suite was run on it:

- **35 were caught.** They cover the refusal order, the default priority and the assignee check,
  the date shape, the overdue `<` boundary and its status rule, sorting by identity, the counter
  and project invariants, the instant and boolean-ID shape checks, the legacy counter, local
  versus UTC today, too-long retention, escaping, the row position, the `added` flag, the labels
  and undated words, line-feed handling, and the timed harness's bound, saved-state check and
  landing check.
- **1 was not caught, and is now covered.** Removing the page builder's own too-long discard
  went unnoticed until the test above was added. That test now catches it.
- **1 cannot be caught.** When a priority is refused, the route could keep the sent priority in
  the redirect address. The page would still show `medium`, because it shows any priority outside
  the four as `medium`. The operator sees the same page either way, so no test can tell the two
  apart.

Suite results in the worktree after the change:

| Check | Result |
|---|---|
| `pytest products/tracker17/tests/` | 574 passed (573 before the change) |
| `pytest products/tracker17/tests/e2e/` | 21 passed |
| `python3 products/tracker17/tests/timed_run.py` | exit 0: adding a task took 29.6 ms and its landing page 0.1 ms, at 1,000 tasks |
| `ruff format --check .`, `ruff check .`, `mypy`, `compileall` | each exits 0 |

## Placement

The parts table is `docs/SDD.md` § 3. Every piece of new logic is already in the part that owns it,
so nothing was moved and there is no `… — placement` commit.

| Logic | Owning part | Where it is |
|---|---|---|
| Task and Comment values; creation, defaults, refusal order, restoration rules; identity and project invariants; ordering by due date then identity; the overdue predicate; date and priority parsing | `domain` | `domain/` — already there |
| Save before publishing; one clock read converted to the local date; overdue flags by asking `domain` | `application` | `application/tracker.py` — already there |
| The five-key layout, legacy key sets, shape and type checks, instant encoding | `persistence` | `persistence/saved_data.py` — already there |
| Routes, stateless outcomes, field retention, rendering, escaping | `web` | `web/` — already there. `web/pages.py` shows an unknown priority as `medium` and an unlisted assignee as none. Both are display defaults that the design's outcome table sets, not rules. |
| The timed fixture and measurement | none: test-side harness | `tests/timed_run.py` — not product code |

## Calls made

1. **`__version__` on product modules.** `languages/python/conventions.md:148` says "Every non-test
   module carries `__version__`". No tracker17 module carries one: `git grep -l __version__ --
   '*.py'` under `products/tracker17` returns nothing, and the developer's marker recorded this as
   a departure for someone else to settle.
   - *Readings weighed:* (a) add the marker to the packages this change touched; (b) leave it out.
   - *Taken:* (b). The rule describes itself as "`versioning.md`'s marker for a script".
     `versioning.md:150-152` places a product's artifacts outside its scope: "A product's artifacts
     version by the product's rules, not the instance's". tracker17's records (`docs/nfdr.md`,
     `docs/adr/`) state no rule for marking modules. Reading (a) would also mark two of tracker17's
     four packages and leave the other two without one.
   - *Whose call:* the owner, through the Python packet's `conventions.md`.
   - *If reversed:* the marker goes product-wide in one change, once in each package `__init__.py`
     (`domain`, `application`, `persistence`, `web`) and in `main.py` and `errors.py`, not in this
     change alone.
2. **`maxlength="200"` counts UTF-16 code units, not characters.** ADR-0007 counts code points, so
   in a browser 200 non-BMP characters stop at 100.
   - *Readings weighed:* (a) CP-107's "lets in at most 200 characters" is met; (b) the field must
     let in exactly 200 code points.
   - *Taken:* (a). The field never lets in more than 200 characters, and the rule is a maximum.
     The project-name field already uses the same attribute.
   - *Whose call:* the Product Owner, for CP-107.
   - *If reversed:* (b) needs a field that counts code points, which means a script. CP-110 rules
     a script out ("The page runs no script"), so a reversal would change the spec as well as the
     code.

## Language resolution

- **Language:** Python. `project.md` declares `Languages: Python`, which answers at step 1 of the
  resolution chain.
- **Files read:** the packet router `languages/python/README.md`, `conventions.md` (§ Surface style,
  § Typing, § Constructs, § Naming) and `quality_gates.md`. Testing comes from `testing_python.md`,
  which the router points to outside the packet folder.
- **How the added test follows them:**
  - Lines stay within 100 columns (`conventions.md:17`). The docstring line this run edited was
    re-wrapped to meet it.
  - `from __future__ import annotations` is the first statement (`conventions.md:46`). The file
    already had it.
  - The test patches no product name and uses no `monkeypatch` (`testing_python.md:31`).
  - Both gates and the product's configured ruff and mypy checks exit 0 (`quality_gates.md`).
- **Packet against the code:** the one place the code departs from the packet is `__version__`,
  which is Call 1.
