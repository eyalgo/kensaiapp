# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-21_out-of-date-move`
**Mode:** workflow. The product is inside the instance, so `code_worktree` and `pipeline_worktree`
are the same change worktree.
**Outcome:** clean pass. The code does what its intent says. One gap in the tests was closed: no
test showed that a refusal line escapes the title.

## Test evidence

- The card's `Test command:` (`pytest products/tracker17/tests/`), run through the gate tool with
  `--gate code-integrity`, exited 0 and printed `1316 passed in 95.25s`. That is the developer's
  closing 1310 plus the 6 cases this review added. It ran on the owner's Mac because the product has
  no CI. The CI inventory of tracked files returned 0, and no product decision names a gate
  environment. That interpreter's pytest is 9.0.3, not the locked 9.1.1.
- These checks ran outside the gate tool, with the product's locked tools in `products/tracker17/.venv`
  (pytest 9.1.1, ruff 0.16.10, mypy 2.4.0). Every one exited 0:
  - `pytest products/tracker17/tests/e2e/`: 75 passed. The 71 before this review plus 4 added cases.
  - `pytest products/tracker17/tests/architecture/test_trace.py`: 27 passed.
  - From the product root: `ruff format --check .` ("207 files already formatted"), `ruff check .`
    ("All checks passed!"), `mypy main.py errors.py domain application persistence web` ("no
    issues found in 24 source files"), and `python3 -m compileall -q web`.
- `grep -rn "the move you pressed" products/tracker17/web` printed nothing and exited 1 (CP-362).
- Two mutation probes ran in a throwaway clone of the branch, which was then removed:
  - **Address context removed.** `_move_view` built the default context in place of
    `CANCELLATION_ADDRESS`. `pytest products/tracker17/tests/integration/` gave
    `32 failed, 957 passed`. The tests catch it.
  - **Title escaping removed.** `_refusal_line` took `task.title` in place of `_escape(task.title)`.
    The two move test modules gave `145 passed`, so nothing caught it. With the tests below added,
    the same mutant failed 6 integration cases and 4 browser cases. The unchanged code passes all of
    them.

## Deferrals

None. The newest closing marker (`61b380e78`, `developer: 2026-10-21_out-of-date-move — implementation
complete`) has no `Deferred:` line and no `Failing:` line.

## What was reviewed

The diff from the merge base `06d6aea1a` to the marker `61b380e78`, under `products/tracker17/`:

- `web/pages.py`: `MoveRefusalContext`, the appended `MoveOutcome.refusal_context` field,
  `_OVERTAKEN_LINES` and `_ADDRESS_LINE`, `_has_move_line`, `_refusal_line`, the extended
  `_move_line`, and the shared `offered` tuple in `_task_list`, `_task_row` and `task_page`.
- `web/routes.py`: `_move_view`'s address-context selection.
- `tests/integration/test_move_routes.py`, `tests/integration/test_move_pages.py` and
  `tests/e2e/test_moves.py`.

## The intent it was checked against

- `tl_instruction.md`: Tasks 1 to 3, their *Behaviours to verify* and *Held by review* entries, and
  the TL Review Notes.
- `change_spec.md`: CP-355 to CP-370, the Examples and the Locked Answers.
- `change_text.md`: every published string, checked character by character against
  `web/pages.py` `_CHANGED`, `_OVERTAKEN_LINES` and `_ADDRESS_LINE`. They match.
- `change_design.md` § 2 to § 5, rows T1 to T13.
- `products/tracker17/docs/fdr.md` exists. It was read only as context, for R-112 (a title shows as
  typed).

Checked against that intent:

- **CP-355 / CP-359.** The four landing statuses at both places are tested, each through a loaded
  earlier page and a real change made by the tracker. The named moves are asserted equal to the
  buttons and to the workflow's own answer, in order.
- **CP-356 / CP-361.** Done and cancelled, through both addresses, at both places, are tested, and
  repeated loads save nothing.
- **CP-357.** The tests cover all four non-status values at both places, and both URL refusal codes
  are kept.
- **CP-358 / CP-360 / CP-362.** `assert_one_status_line` checks: one focused non-control status, the
  line as its description, the line taking no focus, and no reload, link or control in the line.
- **CP-363.** The diff leaves the failure and completion strings in `_move_line` unchanged.
- **CP-364.** The line and the buttons share one tuple. A test injects an order that differs from the
  workflow's, and reading the diff finds no status-to-moves table in `web`.
- **CP-365.** The landings and addresses are answered 200 with `no-store`, and the QC-63 tests are
  unchanged and pass.
- **CP-366.** Every refusal case snapshots the bytes and the save count.
- **CP-368.** Trace, ruff and mypy pass.
- **CP-370.** Each test the spec names was changed to the new words and keeps its non-word
  assertions.
- **Held by review.** The context is chosen from the request, never from the message. No new outcome
  code or state between requests is added. `web` imports only what it imported before. Each title
  passes through `_escape` once, and the finished line is not escaped again.

## Tests added or fixed

- `tests/integration/test_move_routes.py`: `HOSTILE_TITLES` adds the title `'<b>a</b> & "c"'` beside
  the spec's `'a < b & "c"'`. Both titles now parametrize
  `test_overtaken_press_uses_the_current_title_as_text` (2 → 4 cases) and
  `test_address_refusal_shows_the_current_escaped_title` (4 → 8 cases). **Why:** CP-359 and CP-361
  say a title holding `<`, `&` or `"` shows as typed (fdr R-112). The spec's title has no
  tag-forming `<`, so it parses to the same text whether or not it was escaped. The existing
  "no injected element" assertion (`no <b>`) could therefore never fail. The added title forms a
  `<b>` element and loses its text unless `_escape` runs. The escaping mutant above confirms the
  change.
- `tests/e2e/test_moves.py`: the same two titles (`HOSTILE_TITLES`) parametrize
  `test_overtaken_press_shows_the_title_as_typed` and `test_address_refusal_shows_the_title_as_typed`
  (2 → 4 cases each), for the same reason at layer 5 (design T9). There, the
  `#move-line *` count of 0 is what the added title makes discriminating.

No existing test was wrong. None asserted behaviour that differs from the intent.

## The finding

**No issues in the code.** No bug was found and nothing was moved. One coverage gap was closed: no
test showed that a refusal line escapes the title (above). Every other behaviour in the intent
already had a correct test, and everything passes.

## Calls made

- **Question:** is "a title holding `<`, `&` and `"`" (CP-366, last bullet) met by the spec's example
  title alone, or must the test also show escaping for a title that would form markup?
  **Readings weighed:** (a) the example title is enough, because the spec's Examples name it;
  (b) CP-359 and CP-361 say any such title "shows as typed", so a test has to be able to fail when it
  would not. **Taken:** (b), keeping the spec's title and adding a second one. A test that cannot go
  red over unescaped output does not prove R-112, and the addition changes no document's meaning.
  **Owner:** Product Owner (CP-366) and Tech Lead (T5 / T9 allocation). **If reversed:** drop the
  second `HOSTILE_TITLES` entry in both modules. No code changes either way.

## Placement

Parts table: `products/tracker17/docs/SDD.md` § 3. `web` owns "building each whole HTML page" and
request handling, and "never works out which moves are allowed".

- `MoveRefusalContext`, `MoveOutcome.refusal_context`, `_OVERTAKEN_LINES` / `_ADDRESS_LINE`,
  `_has_move_line`, `_refusal_line` and the shared `offered` tuple → `web/pages.py`. Owning part:
  **web**. Already there. These are page building and words. The moves come from the injected
  `allowed_moves` query, and the table is indexed by how many moves there are, not by status.
- The address-context selection in `_move_view` → `web/routes.py`. Owning part: **web**. Already
  there. It reads `self._tracker.allowed_moves`, the application query.

Nothing was misplaced, so there was no `… — placement` commit.

## Language resolution

- **Python**: resolution chain step 1, `project.md` `Languages: Python`.
- **Packet:** `<CORE>/doctrine/engineering/languages/python/README.md` (version 1.3.0) and its
  concern files `conventions.md`, `environment.md` and `testing_python.md`. The rest were already
  cited on the developer's marker and were not re-read.
- **What bore on the review:**
  - The new code follows the Conventions entries: `Enum` for the closed set, the existing frozen
    dataclass, builtin generics, annotated private functions, and underscore-private names.
  - For Testing, the seam is a hand-written injected callable, and no product name is patched.
  - For Quality gates, ruff and mypy are clean.
  - For Gate environment, there is no CI, so the tool selected the owner's Mac.
- The added tests follow the module's own existing parametrize style. No divergence was found between
  the packet and the file.
