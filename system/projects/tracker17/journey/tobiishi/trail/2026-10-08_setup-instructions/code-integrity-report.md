# Code integrity report — 2026-10-08_setup-instructions

Integrity: pass

**Run:** 2026-10-08, workflow mode, `development-code-integrity`, Senior Engineer. **Branch:**
`2026-10-08_setup-instructions`, reviewed at the closing marker `e75934a65`. **Product:**
`products/tracker17`, which sits inside the instance repo, so the code worktree and the pipeline
worktree are the same.

## The finding

**One defect, in the test instrument, not in the product code.** `main.py` and `README.md` do what
the intent says. The shared heading reader that the CP-67 and CP-55 tests rely on counted every
line opening with a run of `#` and a space. That included a shell comment inside a fenced command
block, and a run of seven `#`, which is not an ATX heading. So the CP-67 test passed on a tree the
spec says it must fail on. In a disposable `git archive` copy, section 6's heading was reworded to
`Setting the saved data aside`, with `main.py` left alone, and `# Setting saved data aside` was added
as a comment in section 6's command block. Both the CP-67 and the CP-55 tests passed.

Fixed by red, then green:

- **Red** `9026ef1a0`: the new reader test, failing against the old reader (1 failed, 223 passed).
- **Green**: the reader now skips fenced code and accepts only one to six `#` then a space. The
  suite is 224 passed.

**No misplacement.** **No product code changed.**

## Deferrals

**None.** The newest closing marker, `e75934a65`
(`developer: 2026-10-08_setup-instructions — implementation complete`), carries no `Deferred:` line
and no `Failing:` line, and reads `Suite: green`. Every case in the suite is in scope.

## What was reviewed

The three files the change's code commits touched (`79fcfde21`, `8ecbe6d20`, `c0cc5d04f`,
`9f587e679`), all under `products/tracker17/`:

- `main.py`: the closing sentence added to `start`'s unreadable-data message.
- `tests/integration/test_start.py`: the module docstring, the constants `AGAIN_SECTION`,
  `SET_ASIDE_SECTION`, `CLOSING_SENTENCE` and `UNREADABLE_LINE`, the heading reader, and three
  tests.
- `README.md`: the setup instructions, the opening paragraph and the Status.

## The intent it was checked against

- `tl_instruction.md`, Tasks 1 and 2 and their `#### Behaviours to verify` and `#### Held by review`
  lists.
- `change_spec.md`, CP-54 to CP-68, its Examples and its Locked Answers.
- `change_design.md` § 4 (Code Strategy) and § 5 (Test Additions).
- `change_text.md`, for the README's words, which must be placed verbatim.
- `docs/fdr.md` exists. The spec cites its R-8 to R-14 and R-28, and this review needed nothing
  from it beyond that.

### How each rule is held

| Rule | Held by | Checked here |
|---|---|---|
| CP-65 | `test_an_unreadable_start_writes_exactly_the_one_line_with_the_closing_sentence`: the status is non-zero, standard output is empty, and standard error equals the whole line plus one newline | Yes. The test fails when the sentence is reworded or removed (scratch-copy runs below). |
| CP-65, bytes and listing unchanged | `test_an_unreadable_start_changes_nothing_in_the_location`, unchanged | Yes, passes |
| CP-66, precedence over a held address | `test_unreadable_saved_data_wins_over_a_held_address`, unchanged | Yes, passes |
| CP-67 | `test_the_message_closing_sentence_quotes_a_heading_the_readme_has`, with the corrected reader | Yes. It fails on all four wrong trees below. |
| CP-55 | `test_the_readme_has_both_fixed_headings`, with the corrected reader | Yes |
| CP-55 and CP-67, the reader itself | `test_the_heading_reader_counts_a_heading_and_no_other_line` (added) | Yes |
| CP-68, existing tests unchanged | No pre-change test body was edited | Yes. `git diff e7cfd84d1` touches only the docstring, the new constants, the reader and the new tests. |
| CP-54, CP-56, CP-59 to CP-62 | Review, by design § 5, because a suite test would freeze the per-change copy | The developer's runs are recorded in the marker. Here I re-checked that `README.md` holds all ten `change_text.md` blocks verbatim and in the reading order that file gives. |
| CP-58 | Review | Re-run here. `python3 main.py` in a disposable copy printed `The tracker is running. Open http://127.0.0.1:8017 in your browser. Saved data is kept at /tmp/ci-run.DCeE/products/tracker17/data.` The README's line differs only in the location. |
| CP-63 | Review | Re-run here. The grep matches nothing (exit 1), and the Status names `python3 main.py`. |
| CP-64 | Review | Re-run here. From `## How it's built` to the end, the file is byte-identical to `e7cfd84d1` (`cmp`). |

**Scratch-copy runs of the corrected tests.** Each was run on a `cp` of the working tree. In every
run, `test_data_is_ignored_by_version_control` also fails, because the copy is not a git repository.
That is the known case of spec Gap 11, not this change's.

| Tree | CP-67 test | CP-55 test | CP-65 whole-line test |
|---|---|---|---|
| Heading reworded, same words left only as a fenced comment | fails | fails | passes |
| Heading reworded to `Setting the saved data aside` | fails | fails | passes |
| Closing sentence reworded to `See Setting data aside …` | fails | passes | fails |
| Closing sentence removed | fails | passes | fails |
| Heading written as `####### Setting saved data aside` | fails | fails | passes |

## Tests added or fixed

- **Fixed:** the heading reader in `tests/integration/test_start.py`. It is now `_headings(markdown)`,
  which `_readme_headings()` calls. It skips lines inside a fenced code block: a fence of three or
  more `` ` `` or `~`, indented up to three spaces, closed by a run of the same character at least as
  long. It accepts a heading only as one to six `#`, then a space. Why: CP-67 requires the test to
  fail when the README's heading is reworded. A fenced shell comment, or a seven-`#` line, carrying
  the old words let it pass. The README's sections 1, 2, 5, 6 and 7 are fenced command blocks, so a
  `#` comment in one is a plausible later edit. The plan's own words, "a heading line is an ATX
  line", exclude both, because CommonMark reads neither as an ATX heading.
- **Added:** `test_the_heading_reader_counts_a_heading_and_no_other_line`. It feeds the reader a text
  holding look-alike lines: a backtick fence with a `#` comment, a tilde fence that a backtick line
  must not close, a seven-`#` line, a `#` with no space, and a containment near-miss. It asserts that
  only the three real headings come back. Why: to keep the instrument the two heading tests stand on
  from drifting back.

The Tech Lead and the Architect also asked for "equality, not containment" and "any heading level".
Both are kept.

## Calls made

- **Question:** does a `#` line inside a fenced code block, or a run of seven `#`, count as "a
  heading line" for the CP-55 and CP-67 tests?
  **Readings weighed:** (a) every line opening with `#` and a space counts. This is what the
  developer's reader did. Its Review Notes put fenced lines "out of scope, the README has none". (b)
  Only a CommonMark ATX heading counts: one to six `#`, then a space, and not inside a fenced block.
  **Taken:** (b). The plan says "a heading line is an ATX line", and CP-55 and CP-67 say "heading
  line". Neither a fenced comment nor seven `#` is one. Reading (a) rests on what today's README
  happens to hold, which is a reading of the artifact under test, not of the intent. Reading (b)
  makes CP-67's "fails if either changes alone" true for the README's own command blocks.
  **Whose:** the Tech Lead's (`tl_instruction.md`, Task 2, the shared reader) and the Architect's
  (`change_design.md` § 4, the CP-67 row).
  **If reversed:** revert the reader to its `9026ef1a0` body and drop
  `test_the_heading_reader_counts_a_heading_and_no_other_line`. Nothing in the product changes.
- **Question:** may the red commit split the reader's signature, so that the new test can feed it a
  text?
  **Taken:** yes. The split into `_headings(markdown)` and `_readme_headings()` was
  behaviour-preserving, and it went in the red commit so that the red failed on the reader's logic,
  not on a missing name. The logic fix is wholly in the green commit.
  **Whose:** this skill's, under § *The work, in order*, step 2.
  **If reversed:** none needed. Both commits stand as written.

## Placement

The parts table is `products/tracker17/docs/SDD.md` § 3.

| Logic | Owning part | Result |
|---|---|---|
| The closing sentence of the unreadable-data message (`main.py`, `start`) | `main`: "writes the start messages to the console" | Already in place |
| `README.md`, the setup instructions | No part. The README is a document, per SDD RN-10, not logic. | Not code |
| The heading reader and the constants in `tests/integration/test_start.py` | Test code, not a part | Not product logic |

**No move. No `… — placement` commit.**

## Language resolution

- **Language:** Python. `project.md` declares `Languages: Python`, which is chain step 1 of
  `<CORE>/doctrine/engineering/languages/README.md`.
- **Packet read:** `languages/python/README.md` (router), with `conventions.md`, `quality_gates.md`
  and `testing_python.md` (Testing's destination, outside the folder). `toolchain.md`, `layout.md` and
  `errors_logging.md` bore on nothing this review wrote. No file was added and no dependency changed.
- **Held to:**
  - **Lines within 100 columns.** One docstring line I wrote ran to 106 columns, and I shortened it.
  - **Double quotes.**
  - **`from __future__ import annotations` first.** Unchanged.
  - **Builtin generics.** The reader returns `list[str]`.
  - **Test functions.** They follow the file's own annotated style.
  - **`.format()` only on a template held away from its use.** `UNREADABLE_LINE` is a constant.
  - **A leading underscore for module-internal names.** `_headings`, `_FENCE` and `_ATX_HEADING`
    follow it.
- **Quality gates:** `python3 -m compileall -q` exits 0. The card's suite command is
  `pytest products/tracker17/tests/`, run from the worktree root: 224 passed, with `tests/e2e/` not
  collected. The product also installs Ruff (`pyproject.toml`, `line-length = 100`).
  - `ruff check` flagged FLY002 on my red test's `"\n".join` of a literal list. I rewrote it as
    implicit string concatenation.
  - `ruff check` and `ruff format --check` now pass over `products/tracker17`.

## Not run, and why

- **`pytest tests/e2e/`.** The end-to-end browser cannot start on this Linux machine, for want of
  `libglib-2.0.so.0` (spec Verified Claims, SDD § 11 R-9). Its macOS run is the owner's, as the plan
  says.
- **CP-57, CP-60, CP-61 and CP-62.** I did not re-run these review-held run-throughs. The developer's
  records are in the closing marker. This review's scope is the tests against the intent, plus the
  CP-58, CP-63 and CP-64 spot-checks above.
