# Code integrity — README content rules

Integrity: pass

Senior Engineer review on 2026-10-11 of `tracker17 · tobiishi · 2026-10-10_readme-content-rules`.
Every gate in Task 1 (C1–C8) and the Verification gate held when I ran it myself. That includes the end-to-end suite: 12 passed, exit 0.

## Deferrals

None. The newest closing marker, `39cff98eb`, has no `Deferred:` line (`git log -1 main..2026-10-10_readme-content-rules --grep='2026-10-10_readme-content-rules — implementation complete' --format=%B`).

## What was reviewed

`products/tracker17/README.md` at `2e6bb71cd`, compared with base `5dfc3343efecbc67362aea8d91b516c18a8a9809` (`git merge-base main HEAD`).
The product diff is two lines, README 23 and 81, landed in `4ceb32809` (`git diff --stat 5dfc3343e -- products/tracker17`: `1 file changed, 2 insertions(+), 2 deletions(-)`).
`development_path.py resolve` returns `kind: relative`, with `code_worktree` and `pipeline_worktree` both set to this change's worktree.

## Intent

- `tl_instruction.md` Task 1: § Invariant gate C1–C8 and § Verification gate.
- `change_spec.md` § Invariants and § Structural Goal.
- `change_design.md` § 3 Layout Plan and § 5 Test Continuity.
- The rules being repaired are `products/tracker17/docs/CONTENT.md` § Grammar and mechanics: "Sentence length" and "Dates and times".

## Placement

No new logic. The only change is README prose (the diff above), so `docs/SDD.md` § 3 has nothing to place. No placement commit.

## Tests added or fixed

None. Why is under Calls made.
The two README-heading tests that C6 names are unchanged and pass: `2 passed in 0.03s` when run by node ID.

## Checks run

I ran these myself on 2026-10-11 and did not reuse the developer's numbers. The worktree was clean before and after (`git status --short` printed nothing).

| Gate | Check | Result |
|---|---|---|
| C1 | A Python script I wrote reads the span from `## Status` up to `## How it's built`. It skips headings and fenced blocks, splits sentences at `.`/`!`/`?` followed by whitespace, and counts whitespace-separated tokens. | Before: 67 sentences, max 21, line 23 the only one over 20. After: 68 sentences, max 20, none over. Only lines 23 (`21,5` → `19,4,5`) and 81 (`15,18,9` → `14,18,9`) changed count. |
| C2 | The spec's exact `grep -n -w -i -e today … -e recently products/tracker17/README.md`, run from the worktree root | No output, exit 1. |
| C3 | Read § What you need before and after | Line 23 still sends both cases, a version below 3.11 and a missing `python3`, to installing Python 3.11 or later. The address https://www.python.org/downloads/ and "Then type the command again." are kept. The only change is a sentence break plus "Get it from". |
| C4 | Read § Setting saved data aside before and after | Line 81 drops "now" and nothing else. The home-directory location, `tracker17-set-aside`, the date-and-time naming, `2026-10-08-143205` and `ls ~/tracker17-set-aside` are kept. So are the stop-first step, the no-deletion consequence, the unreadable-data case, the `mv` branch and the empty next start. |
| C5 | Same script, comparing before and after | Headings (12), fenced blocks (6) and inline code spans (54) identical in text and order. The text before `## Status` and from `## How it's built` on is byte-identical. |
| C6 | The two heading tests in `tests/integration/test_start.py` | Unchanged and passing. |
| C7 | `git diff --exit-code 5dfc3343e… -- products/tracker17 ':!products/tracker17/README.md'` | No output, exit 0. |
| C8 | `pytest tests/` and `pytest tests/e2e/` from the product directory, in its `.venv` (Python 3.14.7, pytest 9.1.1) | `224 passed in 12.32s`, exit 0. `12 passed in 2.27s`, exit 0. Before the run, `lsof -nP -iTCP:8017 -sTCP:LISTEN` found no listener (exit 1). |

The rest of the Verification gate, all exit 0:

- The card command, run from the worktree root: `224 passed in 12.38s`.
- `compileall`: no output.
- `ruff format --check .`: `119 files already formatted`.
- `ruff check .`: `All checks passed!`.
- `mypy main.py errors.py domain application persistence web`: `Success: no issues found in 16 source files`.

## The finding

No issues. Both content-rule breaks are fixed, the full-span check finds no other break, and every invariant holds.

The earlier stopped report, `7325cabb1`, recorded an end-to-end failure: `test_a_created_project_is_listed_after_a_stop_and_a_start` timed out on stop. `2e6bb71cd` reverted that report. In this run the same test passed, inside a `12 passed` result.
I don't know why it failed before. Its run was on Codex (the `Surface: Codex` trailer on `7325cabb1`), and this one is on Claude Code. Repeating the e2e suite under both surfaces would tell an environment cause from a flaky test. That question is outside this change, because C7 shows no code or test byte changed.

## Calls made

- **No committed test for the content rules.** One reading of Step 1 says the intent implies a test: a README sentence-length and banned-word check under `products/tracker17/tests/`.
  - **Why not.** `change_spec.md` § Invariants (Product continuity) says the tests stay unchanged. `change_design.md` § 5 says "No test additions". C7 requires an empty product diff outside the README. A new test would break all three.
  - **What I did instead.** I proved C1 and C2 with checks I ran, recorded above, as the design's RN-2 calls for ("repair checks, not new product tests").
  - **Who can reverse it.** This belongs to the Product Owner's spec. If the PO wants the content rules enforced by a lasting test, that would be a separate change to the product's tests.

## Language resolution

Python, at chain step 1, from `system/projects/tracker17/project.md` `Languages:`.
Read `<CORE>/doctrine/engineering/languages/README.md` § The resolution chain and the Python router `languages/python/README.md`.

| Concern | File | What it decided |
|---|---|---|
| Quality gates | `quality_gates.md` | Compile `:14`, suite bar `:33`, Ruff `:66`, mypy `:76`. These set the gates run above. |
| Testing | `testing_python.md:23` | Regular and end-to-end suites run as separate invocations. |
| Conventions | `conventions.md` | Read. It applied to no code, because no Python changed. |

No packet rule diverged from the file's own style.
