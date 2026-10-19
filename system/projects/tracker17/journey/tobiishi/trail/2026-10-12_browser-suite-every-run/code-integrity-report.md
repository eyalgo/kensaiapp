# Code integrity report — 2026-10-12_browser-suite-every-run

Integrity: pass

Re-run on the tree the owner's revised route produced. That route is design `14b5ad5b8`, plan
`33f4bbad9`, task 3 `bd0fde96b`, and the closing marker `315e136f9`, which supersedes `7ba95e221`.
The earlier stop at `486d5dbae` was set aside by `a5edca0b2`. Every invariant holds on HEAD
`a5edca0b277416c232e8dbb38dd186bb775a72e1`, and I-3's twenty-run proof is 20 of 20.

## Deferrals

None. The newest closing marker, `315e136f9`, carries no `Deferred:` line.

## What was reviewed

The developer's commits `d03bcf36b` (task 1), `36e619d29` (task 2) and `bd0fde96b` (task 3). The
product diff since the station opened at `530d0c214` touches only four files:
`tests/e2e/test_first_project.py` (+4), `tests/e2e/test_people.py` (+8),
`tests/e2e/test_labels.py` (10 lines swapped) and `tests/e2e/test_tasks.py` (3 swapped). I read all 25 changed lines against
the base source.

- Tasks 1 and 2 put an `expect(<target>).to_be_focused()` in front of each existing focused-element
  snapshot. The snapshots are kept.
- Task 3 replaces each `wait_for_function("document.activeElement.<tagName|id> === …")` with
  `expect(<page>.locator(<target>)).to_be_focused()`, on the same page object. The targets are
  `main h1` for `H1` and `#<id>` for an id, as design § 4 lists them.
- A grep of `tests/e2e/` shows two things. Every focus read after a navigation now waits behind a
  `to_be_focused`. And no `wait_for_function` is left.
- The reads right after a key press stay immediate, as design § 4 requires: the eight Tab stops in
  `test_people.py`, and `tab_until` and the `remove-label-1` read in `test_labels.py`.

## The intent it was checked against

`tl_instruction.md`, tasks 1 to 3, is the primary source. Behind it are `change_spec.md` (I-1 to
I-12 and § Structural Goal) and `change_design.md` § 1 to § 5, including the Architect Review Note
dated 2026-10-12 that adds task 3. `docs/fdr.md` was not needed, because this change preserves
behaviour.

## Tests added or fixed

None. The change adds no end-to-end test (I-4; design § 5, "No test additions"). This review proves
the invariants by running commands. All of them ran on a `git archive` copy at HEAD,
`/private/tmp/t17-ci2.icZeEh`, with `git init` and the README's `.venv`. The environment was macOS
26.6.2, Python 3.14.7, pytest 9.1.1, playwright 1.63.0 and Chromium 153.0.8010.12.

| Invariant | Check | Result |
|---|---|---|
| I-1 | `pytest -q products/tracker17/tests/` | `813 passed`, exit 0. Holds. |
| I-2 | `git diff --name-only 530d0c214 HEAD -- products/tracker17` | Only the four e2e modules. No `__init__.py` and no `main.py`. Holds. |
| I-3 | The plan's twenty-run loop, `PYTEST_ADDOPTS=-v pytest -p no:cacheprovider products/tracker17/tests/e2e/` | **20 of 20 exited 0**, each `27 passed`. The log check exited 0. No log holds `SKIPPED`, `XFAIL`, `deselected` or `EvalError`. Holds. |
| I-4 | Sorted `^def test_` names at `530d0c214` compared with HEAD, plus `--collect-only` | Identical, 27 names. `27 tests collected`. No skip, xfail, deselect or ignore was added. Holds. |
| I-5, I-8 | Reading, plus the negative check below | Every original snapshot stays after its barrier. Each barrier names the same element. Holds. |
| I-6 | The added-line grep for `rerun\|flaky\|retry\|retries` | No output, exit 1. Holds. |
| I-7 | The closing marker `315e136f9` and the task 3 body `bd0fde96b` | Both causes are named: which tests failed, what varied, and why the fix removes it. Holds. |
| I-9 | `ruff format --check .` · `ruff check .` · `mypy …` | `168 files already formatted` · `All checks passed!` · `Success: no issues found in 21 source files`. Holds. |
| I-10, I-11 | Reading the diff | Nothing is patched. Module docstrings and helper signatures are unchanged. Holds. |
| I-12 | Dependency files | Unchanged, so this invariant does not apply. |

**The negative check (design § 5 C5).** In a second throwaway copy I deleted every ` autofocus` from
`web/pages.py`. The copy is `/private/tmp/t17-mut.Fc8UFu`, and nothing from it was committed. The whole folder then
gave `14 failed, 13 passed`. All 14 failures are `AssertionError: Locator expected to be focused`.
The 14 are the tests that assert focus:

- four in `test_first_project.py`;
- four in `test_people.py`, including the two that NFDR RN-15 names;
- four in `test_labels.py`;
- two in `test_tasks.py`.

The failing targets include a form control (`#name`), a non-control made focusable with
`tabindex="-1"` (`#assignee-<n>`, `#label-<n>`) and `H1`. So each new barrier still fails when focus
stays on the body.

The run logs are in `/private/tmp/t17-ci2.icZeEh/`: `run-1.log` to `run-20.log`,
`exit-statuses.log` and `collect.log`.

## The finding

No issues. Every behaviour already had a correct test, and everything passed. The two causes are now
removed where they live:

- **The autofocus race.** Tasks 1 and 2 removed it: `to_be_focused` now waits for native focus to
  settle before the snapshot reads it.
- **The polled string predicates.** Playwright evaluates them with `eval`, which the page's
  `script-src 'none'` refuses. Task 3 removed them, and the twenty-run proof has no `EvalError`.

Nothing was moved.

One target in task 3 is stricter than before. `main h1` names an element, whereas `tagName === 'H1'`
accepted any `H1`. The plan sets this (task 3, "`H1` reads as `main h1`, the page's only heading").
It makes the check able to fail in more cases, never fewer.

## Calls made

None.

## Placement

No new logic. The change adds or swaps test observations only, in `tests/e2e/`. That is layer 5's
home under NFDR § 9 (`docs/nfdr.md:L505-L512`). The parts table, `docs/SDD.md` § 3, has no production
logic to place, so nothing was moved and there is no placement commit.

## Language resolution

Python, from step 1 of the chain (`project.md` `Languages: Python`). I read
`core/doctrine/engineering/languages/python/README.md`, `quality_gates.md`, `conventions.md` and
`testing_python.md`.

- `quality_gates.md` § *The two gates*: "a red test is a failed gate". No run was red. The other
  gate in that section, Compile, also passes: `python3 -m compileall -q` on the four edited modules
  exited 0.
- `testing_python.md`: "Layer 5 lives in `tests/e2e/`". All four edits are there.
- No packet line conflicts with the edited files' own style.
