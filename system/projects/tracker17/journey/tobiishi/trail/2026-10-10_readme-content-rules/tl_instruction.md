# Tech Lead instruction — readme-content-rules: repair setup prose

This instruction owns the task cut and verification gates for the README prose repair.
The characterization contract is `tracker17 · tobiishi · 2026-10-10_readme-content-rules`, `change_spec.md` § Invariants.
Placement follows that Tobiishi's `change_design.md` § 3 Layout Plan.

**Date:** 2026-10-10
**Category:** bug
**Behaviour:** preserving
**Product root:** products/tracker17
**Scope:** Reword existing README setup prose in place, preserving the spec's invariants.

Task paths are relative to Product root.
Record citations are relative to the instance worktree root, and command blocks name their working directory.
The comparison base is `5dfc3343efecbc67362aea8d91b516c18a8a9809`, the output of `git merge-base main HEAD` during this review.

---

## Project layout

```text
products/tracker17/
  README.md                 ← modified: existing setup prose only
```

This is the modified path from `change_design.md:L23-L33`, § 2 Blast Radius, in the named Tobiishi.
No directory or package creation is needed for this task.
The parts table is present at `products/tracker17/docs/SDD.md:L186-L223`, § 3 The parts, and the seams between them.
No logic is added or moved by this task.
The module set and permitted imports remain those of `products/tracker17/docs/nfdr.md:L122-L153`, § 1.2 Forbidden imports.

## TL Review Notes

Tech Lead decisions, 2026-10-10:

- **Task shape:** Use one preserving task for the README's cohesive prose repair, retaining the design's in-place placement (`change_design.md:L35-L49`, § 3 Layout Plan).
  Adapt the preserving restructure body to rewording, because no symbol or test moves in that layout.
  Use `#### Invariant gate` and the preserving marker, because the propagated classification selects that shape (`core/doctrine/flow/change_classification.md:L60-L65`, The behaviour-preserving path).
  Leave replacement wording to implementation, as the spec permits (`change_spec.md:L62`, § Structural Goal).
- **Gate precision:** Keep the card's command and add the product-directory commands the spec measured, rather than treating the regular suite as the entire gate (`system/projects/tracker17/project.md:L10`, Test command; `change_spec.md:L31-L34`, § Invariants).
  The collection hook excludes end-to-end tests unless their directory is explicitly named (`products/tracker17/tests/conftest.py:L33-L48`, `pytest_ignore_collect`).
- **Baseline evidence:** The card command `pytest products/tracker17/tests/`, from the instance worktree root, first exited 1 with `5 failed, 203 passed, 16 errors`.
  Its socket tracebacks reported `PermissionError: [Errno 1] Operation not permitted` at `socket.bind`.
  The identical command with command approval exited 0 with `224 passed in 12.33s`.
  Both runs reported Python 3.14.7 and pytest 9.0.3.
  Keep final gates in the product's existing virtual environment, because the product locks pytest 9.1.1 (`products/tracker17/pyproject.toml:L11-L17`, dependency-groups dev).
- **End-to-end prerequisite:** Do not convert the spec's environmental failure into a `Red at baseline:` repair allowance.
  That allowance applies to a test this change repairs (`core/doctrine/flow/change_classification.md:L65`, The behaviour-preserving path).
  This change excludes code and test edits (`change_spec.md:L46-L48`, § Invariants).
  The existing test binds `127.0.0.1:8017` before starting the tracker (`products/tracker17/tests/e2e/test_start_command.py:L38-L55`, `test_the_real_start_command_with_the_address_held`).
  During this review, `lsof -nP -iTCP:8017 -sTCP:LISTEN` returned Python PID 86069 listening there.
  Port availability is therefore an unmet prerequisite at review time, not evidence that the prose repair can turn that failure green.
  No end-to-end suite result is claimed by this plan.
- **Repair-check evidence:** A read-only Python check of the complete bounded span reported `Checked 67 prose sentences` and only line 23 at 21 words.
  The exact grep from the spec exited 0 with its sole match on README line 81.
  Comparing README bytes with `git show 5dfc3343efecbc67362aea8d91b516c18a8a9809:products/tracker17/README.md` returned equality.
  Keep full-span checks, because two repaired lines do not establish the span's final constraints (`change_design.md:L65-L69`, § 5 C1–C5).
- **Additional standing gates:** Include compile, Ruff and mypy in Task 1's verification gate, because the NFDR makes them product gates (`products/tracker17/docs/nfdr.md:L472-L485`, QC-62; `:L523-L527`, § 9 Outside the layers).
  These checks add no code or test changes to the task.
- **Language resolution:** Python resolves from `system/projects/tracker17/project.md:L12`, Languages.
  Opened `core/doctrine/engineering/languages/python/README.md`, The six concerns and where each is answered, and its Quality gates and Testing destinations for the gate commands.

## Corrections owed while there

- Owed outside this change's reach: `products/tracker17/README.md:L87-L107`, § Running the tests, omits the Linux-specific browser setup and supported-system boundary required by `products/tracker17/docs/SDD.md:L281-L301`, § 4 RT-4.
  The corrected section would carry RT-4's Linux install command, administrator-rights explanation and suite boundary.
  This correction remains owed because the present spec protects every command and excludes changes to setup steps and supported platforms (`change_spec.md:L37-L48`, § Invariants; `:L94-L99`, § Out of Scope).

### Task 1: Reword the existing setup prose (`README.md`)

**Dependencies:** None

**What to build:** Repair the existing prose in its existing sections according to `change_design.md` § 3 Layout Plan.
Keep the spec's characterization contract intact throughout the edit.

#### Invariant gate

Run before-checks against the comparison base and the unchanged working tree.
Run after-checks against the edited working tree and its diff from that base.
The exact reading commands are:

```sh
# From the instance worktree root:
git -C .worktrees/2026-10-10_readme-content-rules show 5dfc3343efecbc67362aea8d91b516c18a8a9809:products/tracker17/README.md
git -C .worktrees/2026-10-10_readme-content-rules diff --no-ext-diff 5dfc3343efecbc67362aea8d91b516c18a8a9809 -- products/tracker17/README.md
# From Product root:
nl -ba README.md
```

- **C1 — sentence lengths:** Before: read every prose sentence from `## Status` to immediately before `## How it's built` and record its whitespace-token count.
  After: repeat the complete-span reading, with every sentence at most 20 words.
  Treat addresses, paths, versions and inline commands as whole whitespace-separated tokens.
  Exclude headings and fenced commands, and do not split on a dot within a token (`change_spec.md:L71-L73`, § Structural Goal).
  Record the counts so this gate is reviewable.
- **C2 — banned words:** Before and after, run the following exact command from the instance worktree root:

  ```sh
  grep -n -w -i -e today -e yesterday -e tomorrow -e now -e ago -e recently products/tracker17/README.md
  ```

  Before: retain the matching lines as evidence.
  After: no returned line may fall in the bounded span, determined from the current headings.
  Exit 1 means no matches, exit 0 requires reviewing their locations, and an execution error fails this gate (`change_design.md:L66`, § 5 C2).
- **C3 — prerequisite meaning:** Compare the complete § What you need before and after.
  Check the lower-than-3.11 and missing-`python3` alternatives separately.
  Both must still lead to installing Python 3.11 or later from https://www.python.org/downloads/ and typing the version command again (`change_spec.md:L37-L41`, § Invariants).
- **C4 — set-aside meaning:** Compare the complete § Setting saved data aside before and after.
  Retain the home-directory location, `tracker17-set-aside`, date-and-time naming, `2026-10-08-143205` and `ls ~/tracker17-set-aside`.
  Retain the stop-first instruction, no-deletion consequence, unreadable-data use, missing-data `mv` branch and empty next start (`change_design.md:L68`, § 5 C4; `products/tracker17/README.md:L69-L85`, Setting saved data aside).
- **C5 — protected structure and remaining meaning:** Compare every heading's text, level and order, every fenced block and every inline command before and after.
  They must be identical in text and order.
  Compare the prefix before `## Status` and suffix starting at `## How it's built` byte for byte.
  They must be identical, including § The documents.
  Read every changed prose sentence against its before-text for unchanged instructions, conditions, consequences and next action (`change_spec.md:L37-L48`, § Invariants).
- **C6 — existing heading coverage:** Keep `tests/integration/test_start.py::test_the_readme_has_both_fixed_headings` and `tests/integration/test_start.py::test_the_message_closing_sentence_quotes_a_heading_the_readme_has` unchanged and passing.
  Their subjects remain real headings, as the existing reader excludes fences (`products/tracker17/tests/integration/test_start.py:L94-L120`, `_headings` and `_readme_headings`; `:L147-L162`, the two tests).
- **C7 — product continuity:** Before and after, run this exact command from the instance worktree root:

  ```sh
  git -C .worktrees/2026-10-10_readme-content-rules diff --exit-code 5dfc3343efecbc67362aea8d91b516c18a8a9809 -- products/tracker17 ':!products/tracker17/README.md'
  ```

  Pass: exit 0 and no output.
  The README diff must contain only the permitted prose repair.
  This preserves all code, public exports and signatures, tests and definition documents without changing assertions (`change_spec.md:L35-L48`, § Invariants).
- **C8 — full continuity:** Before the edit and after it, the regular and end-to-end suites must pass unchanged using the commands in the Verification gate (`change_design.md:L72`, § 5 C8).
  The end-to-end prerequisite is availability of port 8017 for the test's own listener (`tests/e2e/test_start_command.py:L38-L55`, `test_the_real_start_command_with_the_address_held`).
  A missing prerequisite is a blocked baseline, not a green result or a repair allowance.
  A prose edit that turns an existing test red is a reclassification event: stop and surface, leaving the test intact (`core/doctrine/flow/change_classification.md:L143-L145`, § Constraints).

#### Implement

Restructure per the §3 Layout Plan by rewording existing README prose in place.
Keep the test files and assertions intact.
**No new tests — TDD under green** (baseline green → prose repair → green; no red phase).

#### Verification gate

From Product root, inside its existing virtual environment:

```sh
source .venv/bin/activate
pytest tests/
pytest tests/e2e/
python3 -m compileall -q main.py errors.py domain application persistence web
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

From the instance worktree root, in the same virtual environment, retain the project card's invocation:

```sh
pytest products/tracker17/tests/
```

Pass: every command exits 0, both suites collect and pass their existing tests, and every after-check in C1–C7 holds.
The regular suite must include the two heading tests in C6.
No skipped failing test, changed address or weakened assertion satisfies C8 (`change_spec.md:L31-L34`, § Invariants; `change_design.md:L74-L75`, § 5 Test Continuity).
