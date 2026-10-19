# Code integrity report — 2026-10-11_readme-linux-setup-and-git

Integrity: pass

**Date:** 2026-10-11 · **Mode:** workflow · **Reviewer:** senior-engineer, `development-code-integrity`

## Deferrals

None. The closing marker `439add9e2` has no `Deferred:` line.

## What was reviewed

`products/tracker17/README.md`, § Running the tests. This is the only product path changed against the input revision `06af065b288da2e637e5b00868459d7191c33574`, according to `git diff --name-only`. The change is the task 1 commit `ded01918d`, with 3 lines added and 1 removed. No code was changed.

## The intent it was checked against

`tl_instruction.md` Task 1, V-1 to V-9; `change_spec.md` CP-69 to CP-79; `change_design.md` § 1 and § 5; `change_text.md`, as the verbatim source for the strings. Sources checked: `docs/SDD.md:285-296` (§ 4 RT-4), `docs/SDD.md:677-687` (§ 6 S-1 *Artifact*) and `docs/CONTENT.md:98-137` and `:170-192`. `docs/fdr.md` is present but was not needed: the spec's CPs already cite it.

## Tests added or fixed

None. CP-78 says no file other than `README.md` changes, and `change_design.md` § 5 replaces test files with artifact checks for that reason (Architect Review Notes, kind (d)). An added test would break the spec it proves. I re-ran the plan's verification gate and recorded one result per criterion:

| Check | Result |
|---|---|
| `pytest products/tracker17/tests/` | `224 passed in 10.58s`, exit 0. The worktree was clean before and after. |
| Six-word grep over the whole README | no output, exit 1 |
| `grep -n -F -e '--with-deps' -e 'Debian 12'` | exit 0. Both patterns match line 91, which sits between `### Running the tests` (87) and `## How it's built` (111). |
| `git diff --check 06af065b -- products/tracker17` | no output, exit 0 |
| `git diff --name-only 06af065b -- products/tracker17` | `products/tracker17/README.md` only |
| Strings vs `change_text.md` | both `>` paragraphs match a README line exactly (`grep -qxF`) |
| V-1 / CP-69 | holds. Line 91 says the `--with-deps` command should be typed "where the commands say `python -m playwright install chromium`", and the note comes before the block. |
| V-2 / CP-70, CP-71 | holds: "operating system's package manager", "administrator rights", "The tracker and `pytest tests/` need none of what it installs." |
| V-3 / CP-72 | holds. Debian 12 or 13, Ubuntu 22.04, 24.04 or 26.04, and x86-64 or arm64 all appear, which matches RT-4's list at `SDD.md:291-293`. No other system is named. |
| V-4 / CP-73, CP-75 | holds. Line 109 names both a Git repository and `git` on the path. It says "If either is missing … 1 test doesn't pass" and gives what that test checks. |
| V-5 / CP-74 | holds: "The tracker itself needs neither a Git repository nor `git`." |
| V-6 / CP-76 | holds. The Git explanation is one paragraph and the last in the section. Neither old sentence remains as written. |
| V-7 / CP-77 | holds. The 9 sentences run 5 to 20 words, with command spans counted. Neither new line has a colon, semicolon, parenthesis, em dash, ellipsis, exclamation mark or Latin abbreviation. Neither has an uncontracted negative or any of the § Terminology banned words. |
| V-8 / CP-78 | holds. The diff has 2 hunks, both inside the section. All 12 heading lines, the 7-command block (lines 93-101) and the paragraphs at 89, 103, 105 and 107 are unchanged. |
| V-9 / CP-79 | holds (see the grep row) |

## The finding

No issues. No logic was misplaced. Every criterion in the intent holds against the committed README. The existing suite passes, including the README heading tests at `tests/integration/test_start.py:147-162`.

## Calls made

None. The intent left no question open: the design settled the test question, and the spec settled placement and wording through `change_text.md`.

## Placement

No new logic. The parts table exists (`docs/SDD.md` § 3), but the change edits only the README, which is the S-1 setup artifact. It adds no runtime logic to place.

## Language resolution

Python, from `project.md` `Languages:` (step 1 of the chain in `languages/README.md`). The packet read was `<CORE>/doctrine/engineering/languages/python/README.md`. That file routes to `toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, and to `testing_python.md` for Testing. None of them applied to this change, which wrote no Python. The only relevant item was the suite command run under `python3` 3.14.7.
