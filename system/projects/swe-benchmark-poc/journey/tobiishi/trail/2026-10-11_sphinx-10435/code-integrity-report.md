# Code integrity report — 2026-10-11_sphinx-10435

Integrity: pass

**Date:** 2026-10-11 · **Mode:** workflow · **Seat:** Senior Engineer (`development-code-integrity`)
**Outcome:** clean pass. The code already does what its intent says, and no bug was found. I added
one test the intent implies and the suite did not carry: CP-11 on highlighted code whose own text
ends in a space. It is committed in the product repository as `c661d3ef5`.

This report records the review of the change's code against `change_spec.md` CP-9 to CP-14. It
names the one call I made where the plan left room, for the Tech Lead to confirm or reverse.

---

## Deferrals

**None.** The closing marker (`28632e1`, `developer: 2026-10-11_sphinx-10435 — implementation
complete`, the only marker on the branch) carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

The product lives in its own repository. `code_worktree` is
`<the issue's clone>/.worktrees/2026-10-11_sphinx-10435`.
I diffed it from `f1061c012` (base_commit) to `31fdf9db2` (the developer's last commit):

- `sphinx/writers/latex.py`: `LaTeXTranslator.visit_literal`, highlighted branch. The opener
  replacement gained a `%`. After the existing `\end{Verbatim}` strip, a new line puts `%` before
  the last character (`hlcode[:-1] + "%" + hlcode[-1:]`). I read the whole method, including its
  three early returns.
- `tests/test_build_latex.py`: the rewritten assertion in `test_latex_code_role`, and the new
  `test_latex_code_role_unhighlighted_unchanged` and `test_latex_code_role_boundaries`.
- `tests/roots/test-latex-code-role/` (`conf.py`, `index.rst`): the developer's probe root.

The developer's commits are `ff43f2859` (Task 1), then `e5716ef07` red, `af0d0418f` green and
`31fdf9db2` refactor (Task 2).

## The intent it was checked against

- `tl_instruction.md`: Tasks 1 and 2, their *Behaviours to verify*, both *Held by review* items,
  and the TL Review Notes.
- `change_spec.md`: CP-9 to CP-14, the Examples table, Verified Claims and Locked Answers Gaps 1–6.
- `change_design.md`: § 4 (both hints), § 5 (test additions and rule-implied edges), Architect
  Review Notes.
- `docs/fdr.md`: absent. The card reads `Definition: none` and the product has no `docs/`. It is
  optional context, and its absence is the normal case.

## Placement (Step 0)

**No parts table.** `docs/SDD.md` does not exist under the product worktree, and neither does
`docs/` (checked 2026-10-11; Sphinx's own documentation folder is `doc/`, which is not a parts
table). There was nothing to place against, so the step did not run, and no `… — placement` commit
was made. For the record, the only logic the change added is the two `%` insertions. They sit in
`visit_literal`, the method `change_design.md` § 2 names as the one that changes.

## Language resolution

- **Python**, answered at chain step 1 (`project.md` `Languages: Python`).
- **Packet opened:** `<CORE>/doctrine/engineering/languages/python/README.md`. I read
  `conventions.md`, `quality_gates.md` and `testing_python.md` (the Testing destination), and
  `layout.md` § *Two trees*. I did not open `toolchain.md` or `errors_logging.md`. The code I wrote
  adds no dependency and raises or logs nothing, so neither bears on it. The floor
  (`developer_standards.md`) still applies beneath the packet.
- **Quality gates.** Compile: `/home/kensai/issue-venv/bin/python -m compileall -q -f
  tests/test_build_latex.py` exited 0, run with the card's interpreter. Suite: the card's
  `Test command:` (below). No formatter or linter ran, because none is installed in the product's
  virtualenv.
- **Conventions.** Every line I added is within 100 columns. Strings are double-quoted
  (`conventions.md` § *Surface style*). That diverges from the surrounding Sphinx file, which is
  single-quoted. The packet outranks a file's habit (`languages/README.md` § *Precedence*), and the
  developer's new tests in the same file are double-quoted too. The one comment I added says why
  the root escapes the character after the trailing space: the rejected alternative, a bare space,
  is not accepted by docutils (`conventions.md` § *Comments and docstrings*, form 2).
- **Testing.** `testing_python.md`'s `tests/test_<domain>.py` location matches Sphinx's own layout,
  and the new root follows Sphinx's `tests/roots/test-<name>/` convention. The hand-written-fake rule
  has nothing to act on: the tests build a real document through Sphinx's `app` fixture and patch
  nothing.

## Tests added or fixed

**None fixed.** Every existing test, the developer's included, asserts what the intent says:

| Test | Intent it proves | Would it pass if the code were wrong? |
|---|---|---|
| `test_latex_code_role` (inline assertion, rewritten) | CP-9, CP-10, CP-11: the issue's three lines, whole | No. It fails at base, and it fails with either `%` reverted alone (the developer's marker records both reverts). |
| `test_latex_code_role` (code-block assertion, unchanged) | CP-12: the issue's `sphinxVerbatim` block | It is a fence. It passes on both trees, as it should. |
| `test_latex_code_role_boundaries` | Examples rows 2–5. CP-11's two-line case with its inner line end bare | No. A `%` on every line end fails the two-line assertion, and a missing `%` fails every row. |
| `test_latex_code_role_unhighlighted_unchanged` | CP-12: Examples rows 6–9 | It is a fence. A `%` leaking into the no-language, `:kbd:` or title branch fails it. |

**Added**, in product commit `c661d3ef5`:

| Test | Intent it proves | Why it was missing | At base | Second-strip mutant | The change |
|---|---|---|---|---|---|
| `test_latex_code_role_trailing_space_kept`, with the new root `tests/roots/test-latex-code-role-trailing-space/` (input `` :python:`x = 1 \ ` ``, role text `x = 1 `) | CP-10 and CP-11 together. The `%` follows the last character of the highlighted text even when that character is a space, and the space stays (`\PYG{l+m+mi}{1} %⏎}}`). | `tl_instruction.md` held this rule by review. It said no reST input can end in whitespace. An escaped trailing space does reach the highlighted branch (probed below). | red: no `%` | red: the space is eaten | green |

**The probe behind it**, run 2026-10-11 with the card's interpreter on scratch copies under `/tmp`
(`git archive` of `f1061c012` and of `31fdf9db2`). Neither product checkout was touched:

- At base, `` :python:`x = 1 \ ` `` builds to `\PYG{l+m+mi}{1} ⏎}}`. The trailing space is in today's
  highlighted text, so CP-11 requires it to stay byte-identical.
- On the change, it builds to `\PYG{l+m+mi}{1} %⏎}}`. The code is correct.
- A mutant that finds the trailer by a second strip (`hlcode.rstrip() + "%\n"`, the construction
  `change_design.md` § 4 warns against) builds to `\PYG{l+m+mi}{1}%⏎}}`. It passed all 77 tests of
  the developer's suite. Only the added test fails on it.

**The suite.** The card's `Test command:` (`/home/kensai/issue-test.sh`), run from the product
worktree after `c661d3ef5`: `78 passed, 8 skipped`, exit 0. That is the developer's 77 plus the one
added. The baseline is empty, so CP-14 holds.

## The finding

**No issues in the code.** Both `%` insertions meet CP-9 and CP-10. The trailer is placed before
the single last line end, with no second strip, as `change_design.md` § 4 requires. CP-12's outputs
do not move. No logic was misplaced and nothing was moved.

**One gap in the proof, now closed.** CP-11's byte-identity on highlighted text ending in a space
was unproved. The plan's reason for leaving it to review rests on a premise that does not hold (see
*Calls made*, 1).

**Both *Held by review* items, read on the diff:**

- Task 1. `tests/roots/test-latex-code-role/index.rst` holds the inputs `change_design.md` § 5
  lists and nothing else. The additions are the top title "Probe" and the role names, which the
  marker records and the document needs.
- Task 2. The trailer is `hlcode[:-1] + "%" + hlcode[-1:]` after the one existing strip. It is now
  also held by the added test.

**Observed, not tested.** `` :python:`\ ` `` (a role whose text is empty) builds to
`\sphinxupquote{%⏎%⏎}}` on the change, where base builds `\sphinxupquote{⏎⏎}}`. The intent does not
name the empty case. Each `%` comments out the line end after it, so it typesets no space, which is
the issue's aim. I added no test, because no sentence of the intent states the expected bytes.

**Domain overlay (`system/loaders/senior_engineer.md` § *The domain*).** Nothing to act on. The
change touches no presence surface. It stores, collects, embeds and publishes nothing
(`change_design.md` § 1, *Outward boundary*). The fixture text states nothing about KensaiApp or
about Eyal.

## Calls made

1. **Add the trailing-space test that the plan chose not to add.**
   - *The question.* `tl_instruction.md` § TL Review Notes, *Behaviour kept, not added*, declined a
     test for highlighted code ending in a space. Its reason: "A docutils interpreted-text role cannot
     end in whitespace", so the input is unreachable. Its *Held by review* item for Task 2 rests on
     the same claim.
   - *Readings weighed.* (a) Follow the plan and leave the rule to review. (b) Add the test, because
     the plan's premise is false and CP-11's byte-identity, which the design's § 4 hint protects by
     name, is reachable and unguarded.
   - *Taken: (b).* The escaped form `` :python:`x = 1 \ ` `` reaches the branch with role text
     `x = 1 `. The design's own § 4 probe uses exactly the source `x = 1 `. A second-strip trailer
     passes every existing test. The test asserts only what CP-10 and CP-11 already say.
   - *Whose it is.* The **Tech Lead**'s (`tl_instruction.md`). The reachability fact also touches
     the **Architect**'s § 4 hint, which it confirms rather than contradicts.
   - *If reversed.* Remove the test and its root (`c661d3ef5`). No code changes, and the rule goes
     back to being held by review only.

2. **Give the added input a root of its own rather than adding it to `test-latex-code-role`.**
   - *The question.* Where the new input lives. Neither the plan nor the design names a place for it.
   - *Readings weighed.* (a) Add a line to `tests/roots/test-latex-code-role/index.rst` and an
     assertion to `test_latex_code_role_boundaries`. (b) A new root and a new test.
   - *Taken: (b).* Task 1's *Held by review* item says that root holds only the inputs
     `change_design.md` § 5 lists. Reading (a) would make that sentence false. Reading (b) keeps it
     true and costs one small fixture folder.
   - *Whose it is.* The **Tech Lead**'s (`tl_instruction.md` Task 1) and the **Architect**'s
     (`change_design.md` § 5).
   - *If reversed.* Move the one input line into `test-latex-code-role/index.rst` and the one
     assertion into `test_latex_code_role_boundaries`, then delete the new root. The proof is
     unchanged.
