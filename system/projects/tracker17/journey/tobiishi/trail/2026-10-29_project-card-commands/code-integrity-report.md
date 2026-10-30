# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-29_project-card-commands`, reviewed at `<a commit not in the public history>` (the newest closing marker).

## The finding

No issues. The card's two new values do what CP-685 to CP-692 say. Nothing was misplaced, no bug was found, and no code or test was changed.

## Deferrals

None. The closing marker (`<a commit not in the public history>`) carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

`system/projects/tracker17/project.md`, lines 10–11, the only code this change wrote:

- Test: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`
- Setup: `uv sync --locked --project "$(git rev-parse --show-toplevel)/products/tracker17"`

## The intent it was checked against

`tl_instruction.md` Task 1 and its T1–T8 table; `change_spec.md` § Rules CP-685 to CP-692, § Examples and § Out of Scope; `change_design.md` §§ 2, 4 and 5. FDR context was not needed: the spec states every rule the card must meet.

## Tests added or fixed

None committed. See *Calls made* 1. In their place, every T1–T8 check was re-run by this review, in its own fresh clones at `<a commit not in the public history>` whose path held spaces, with the card's own values pulled out and run through `/bin/sh`. Results:

| Check | What this review did | Result |
|---|---|---|
| T1 — fresh Setup | Setup from the clone root, and from `products/tracker17` in a second clone, with no `.venv` beforehand | exit 0 both; only `products/tracker17/.venv` made; no root `.venv`, no `products/tracker17/products/`; 0 `warning:` lines |
| T2 — stale Setup | `requires-python` set to `>=3.12`, Setup from each directory | exit 1 both; `uv.lock` sha256 unchanged |
| T3 — the values | read both values | Setup is `uv sync --locked`; Test starts with `uv`; 2 × `uv run --locked --project products/tracker17`; no `--frozen`, `-k`, `-m`, `--deselect`, `--ignore`, `||` or redirect |
| T4 — clean full run | Setup, then Test from the clone root | exit 0; `2698 passed`, then `121 passed`; all four layers in the output (architecture, integration, unit, e2e); 0 skipped or deselected; lock unchanged; `git status --short -- products/tracker17` empty |
| T5 — failing tests | one forced failure added to a unit file; in another clone, to an e2e file | unit: exit 1, `1 failed, 2698 passed`, second suite never started. e2e: first suite `2698 passed`, then exit 1 with `1 failed, 121 passed` |
| T6 — collection | a missing import in a unit file; in another clone, in an e2e file. Then each suite emptied by a collection hook | unit import: exit 2, `1 error`. e2e import: first suite green, then exit 2, `1 error`. First suite emptied: exit 5, `no tests ran`. Second suite emptied: first suite green, then exit 5, `no tests ran` |
| T7 — locked Test | stale manifest after Setup, then Test; separately, a scratch unit test that makes the manifest stale as the last test of the first suite | first case: exit 2, "needs to be updated, but `--locked` was provided", nothing collected. Second case: `2699 passed`, then the second `uv run` exits 2 with the same message before collecting. Lock unchanged in both |
| T8 — edit boundary | diff against the merge base `858d64443` | card lines 10 and 11 only; with the two values masked, the old and new card bytes are identical; nothing under `products/tracker17/`; the other changed files are this change's own records; `git diff --check` silent |

## Test evidence

- The full-card run through the gate tool, in the change worktree: `Environment: owners-mac — no CI`, exit 0, `collected 2698 items` → `2698 passed in 269.30s`, then `collected 121 items` → `121 passed in 54.64s`. `git status --short` empty afterwards.
- The T4–T7 clones ran six at a time, so their times (up to 6 min for the first suite) are slower than the gate's run. That is load, not a finding.
- The first try at T7's second case failed in the first suite. The scratch test file named no requirement, which the architecture rule QC-11 (`tests/architecture/test_trace.py::test_every_test_module_names_a_requirement_or_acceptance_criterion`) refuses. Re-run with a docstring that names one, it gave the result above. This was a slip in the scratch test, not something the card did.
- All clones were removed after their output was read.

## Calls made

1. **No lasting test is added.** *The question:* this skill adds a missing test, but the intent forbids any test change. *The readings:* (a) add a test of the card under `products/tracker17/tests/`; (b) re-run T1–T8 as throwaway checks and record them here. *Taken:* (b). CP-692 and § Out of Scope keep every test and allow no diff under `products/tracker17/`. TL Review Note 2 and design § 5 make T1–T8 temporary checks. *Whose:* the Tech Lead's plan and the Product Owner's spec. *If reversed:* a later change would have to put a card test somewhere outside the product, which the spec does not allow today.
2. **A refused Setup still leaves a `.venv` behind.** *The question:* in T2, `uv sync --locked` exits 1 on a stale lock, but it has already made `products/tracker17/.venv` (its error stream prints "Creating virtual environment" before "Resolved 17 packages"). Does that break the spec? *The readings:* (a) a defect, because Setup should refuse without side effects; (b) not a defect. *Taken:* (b). CP-687 asks only for a non-zero exit and a byte-identical `uv.lock`, and both hold. T1's "only the product `.venv`" rule is about a fresh Setup that succeeds. uv makes the folder before it checks the lock, so no card value could avoid it while keeping `uv sync --locked` (ADR-0013). *Whose:* the Product Owner's (CP-687). *If reversed:* CP-687 would need a clean-up rule, and the Setup value would need to remove the folder after a failure.

## Placement

The logic walked is the card's two values: choosing the product, locked sync, two locked suite runs, and failure passed on through `&&`. **No owning part.** The SDD § 3 parts table (`domain`, `application`, `persistence`, `web`, `main`) owns no suite tooling. NFDR § 8 gives the suite command to the card ("The execution context — headless, and the suite command — is `system/projects/tracker17/project.md`'s"), and design § 2 places the logic there too. Nothing was moved and there is no placement commit.

## Language resolution

Python. It is declared on the card (`Languages: Python`), step 1 of the chain. Packet read: `<CORE>/doctrine/engineering/languages/python/README.md` (version 1.3.0) and its concerns. `toolchain.md` applies: "A suite run with a bare `pytest` still gets whatever pytest the machine has", and both Test runs go through `uv run --locked`, so this is followed. `quality_gates.md` applies too: a red, an empty or an uncollectable suite fails the gate, and T5 and T6 show exits 1, 5 and 2, with no success fallback. The second suite runs as a process of its own (`testing_python.md`), as in T4. `environment.md`: with no CI, the gate tool ran on the owner's Mac. `layout.md`, `conventions.md` and `errors_logging.md` bear on nothing here, because no Python was written.

## Left as it was

`products/tracker17/docs/nfdr.md:633-634` (§ 10 preamble) still calls the card's Test value `pytest tests/`. It is already handed on in `deferred_decisions.md`, and this change may not edit it (CP-692). The browser boundary stays: Setup fetches no Chromium, so a machine without Playwright's pinned Chromium fails the e2e suite. That is the spec's Out of Scope.
