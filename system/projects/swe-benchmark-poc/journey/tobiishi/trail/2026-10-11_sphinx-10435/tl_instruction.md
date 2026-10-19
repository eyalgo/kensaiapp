# Tech Lead instruction — sphinx-10435: `%` before the boundary line ends of highlighted inline code

**Product root:** <the issue's clone>/.worktrees/2026-10-11_sphinx-10435 — every path below is relative to it.
**Category:** bug
**Behaviour:** changing
**Scope:** In the LaTeX writer, highlighted inline code gets a `%` directly before its opening and closing boundary line ends (CP-9 to CP-11). Nothing else in any output moves (CP-12). The tests move with it (CP-13), and the card's `Test command:` exits 0 with an empty baseline (CP-14).

**What a task may bring in.** Every task below introduces no third-party origin and no device storage. None adds a dependency, a font, a script or a network call. The change is a local patch to an unpushed clone and publishes nothing.

**Where every string comes from.** The only strings a task writes are the expected `.tex` forms and the test-root document text that `change_spec.md` (CP-11, Examples) and `change_design.md §5` give. A string those do not give is an unapproved addition.

---

## Project layout

```
<product-root>/
  sphinx/
    writers/
      latex.py                     ← modified (LaTeXTranslator.visit_literal, highlighted branch only)
  tests/
    test_build_latex.py            ← modified (test_latex_code_role) + new tests
    roots/
      test-latex-code-role/        ← new directory
        conf.py                    ← new
        index.rst                  ← new
```

No parts table — placement follows change_design.md §2. The product has no `docs/`, so there is no `adr/`, `nfdr.md` or `SDD.md`; module boundaries and ordering come from `change_design.md` and `change_spec.md`. `tests/roots/test-reST-code-role/` stays untouched: it is the issue's own `index.rst`, and `tests/test_build_html.py::test_html_code_role` reads it too.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):
- **Task split:** the design has no §3 sub-jobs and treats the change as one delta. The plan cuts two tasks along the test lanes instead. Task 1 creates the new test root and the CP-12 regression fence, which passes on the unchanged tree and so cannot go red. Task 2 is the writer change with its two red tests. Reason: one task holding both would be routed to one lane, and either lane would be wrong for half of it. A fence test written test-first has no red to commit, and the writer fix has one. The opener `%` and the trailer `%` stay together in Task 2, as the design says: each is shown by the same tests and neither has a green point of its own.
- **Ordering:** Task 1 goes before Task 2 because Task 2's new test reads the root Task 1 creates. `Dependencies:` states that use and nothing more.
- **Already-green shape on Task 1:** the design's §5 calls the CP-12 test "a regression fence that passes on both trees". I read the writer: `visit_literal` returns before the highlighted branch for titles, `:kbd:` and literals with no language, and the plain `` ``literal`` `` goes through the same no-language branch. So those outputs are already today's, and Task 1 is written in the already-green shape with its `Reason:` line. The behaviours are kept in full.
- **Behaviour kept, not added:** I looked for a missing edge case, namely highlighted code whose text ends in a space (the design's §4 hint for the trailer). A docutils interpreted-text role cannot end in whitespace before its closing backquote, so no reST input reaches it, and adding a test for it would fabricate an unreachable input. The design's hint already protects it, and Task 2's exact-form assertions fail if a second strip ever eats a character.
- **Held by review:** the trailer `%` goes before the single last line end, not at a boundary found by a second whitespace strip (design §4). The reachable inputs above all end in a non-space, so a second strip would pass every test here. That rule is held by reading the diff, and Task 2 says so under *Held by review*.
- **Gate command taken from the spec's check:** I did not run the card's `Test command:` (`/home/kensai/issue-test.sh`) myself. The spec's Verified Claims ran it at base from a disposable copy and got `75 passed, 8 skipped`, exit 0, so it runs something and the gates use it unchanged. The spec's note stands: on a fixed tree with the old assertion untouched, the command fails on `test_latex_code_role`, which is why Task 2 moves that assertion.
- **Hints:** both `change_design.md §4` hints are carried into Task 2 as the approach. Neither is rewritten.

---

### Task 1: New test root `test-latex-code-role` and the CP-12 fence (`tests/roots/test-latex-code-role/`, `tests/test_build_latex.py`)

**Dependencies:** None

**What to build:** A test root holding one probe document (`conf.py` and `index.rst`, shaped like the sibling root `tests/roots/test-reST-code-role/`). It holds the inputs listed under `change_design.md §5` and nothing else, in this order of kinds: a `python` role derived from `code`; `` :python:`1` ``; one `:python:` role spanning two source lines (`a = 1` / `b = 2`); roles derived from `code` with `:language: nosuchlang` and `:language: none`, each on `x = 1`; a role derived from `code` with no `:language:`; `:code:` alone on `x = 1`; a plain `` ``literal text`` ``; `` :kbd:`Ctrl+C` ``; and a section title holding a highlighted role on `x = 1`. One new test in `tests/test_build_latex.py` builds it with the `latex` builder and asserts the CP-12 forms.

#### Behaviours to verify (developer adds the test to `tests/test_build_latex.py`)

- `test_latex_code_role_unhighlighted_unchanged` — reads `python.tex` of the new root and asserts these whole strings:
  - the plain literal is `\sphinxcode{\sphinxupquote{literal text}}`
  - `:code:` alone and the derived role with no language are each `\sphinxcode{\sphinxupquote{x = 1}}`
  - `:kbd:` gives `\sphinxkeyboard{\sphinxupquote{Ctrl+C}}`
  - the title is `\sphinxstyleliteralintitle{\sphinxupquote{x = 1}}` with no `\PYG` and no `%` inside it
- The test asserts nothing about the unknown-lexer warning. Pygments warns for `nosuchlang` as it does today, and the test neither suppresses nor checks that.

#### Held by review

- Whether the root's `index.rst` holds only the inputs `change_design.md §5` lists — no test fails if one is missing or if a stray one is added. It is held by reading the diff.

#### Implement

Tests cannot go red.

Reason: the writer's `visit_literal` returns before the highlighted branch for a title, for `:kbd:` and for a literal with no language, so those four outputs are today's bytes on the unchanged tree. The test fences them against Task 2.

#### Verification gate

Run `/home/kensai/issue-test.sh` from the product root.

Pass criteria: exit 0 with `75 passed` plus the one new test, and no failure; the new test passes on the unchanged writer.

---

### Task 2: Highlighted inline code boundaries (`sphinx/writers/latex.py`, `tests/test_build_latex.py`)

**Dependencies:** Task 1 (its new test reads the root Task 1 creates)

**What to build:** In `LaTeXTranslator.visit_literal`, the branch that handles a `code` literal carrying a language, put a `%` directly after `\sphinxcode{\sphinxupquote{` and another directly before the last line end of the highlighted block, so the output reads `…\sphinxupquote{%⏎<highlighted text>%⏎}}` (CP-9, CP-10). The highlighted text stays byte-identical, inner line ends of multi-line code included (CP-11). The method's signature and its three early-return branches stay as they are, and no other builder and no other file's output moves (CP-12). Alongside it, `test_latex_code_role` moves to CP-11's markup, and one new test covers the remaining highlighted Examples.

#### Behaviours to verify (developer edits and adds tests in `tests/test_build_latex.py`)

- `test_latex_code_role` (modified, root `reST-code-role`) — the inline assertion is replaced. It now expects `Inline \sphinxcode{\sphinxupquote{%` + line end + the unchanged `common_content` + `%` + line end + `}} code block`. The code-block assertion that follows stays byte-for-byte, so the `sphinxVerbatim` output of the issue's code-block is unchanged (CP-12). Fails on the unchanged tree.
- `test_latex_code_role_boundaries` (new, root `latex-code-role`) — asserts the exact form of each highlighted input, as whole strings:
  - `` :python:`1` `` gives `\sphinxcode{\sphinxupquote{%` + line end + `\PYG{l+m+mi}{1}%` + line end + `}}`
  - `nosuchlang` and `none`, each on `x = 1`, give `\sphinxcode{\sphinxupquote{%` + line end + `x = 1%` + line end + `}}`
  - the two-line role gives `\sphinxcode{\sphinxupquote{%` + line end + `\PYG{n}{a} \PYG{o}{=} \PYG{l+m+mi}{1}` + line end + `\PYG{n}{b} \PYG{o}{=} \PYG{l+m+mi}{2}%` + line end + `}}`, with the inner line end bare and the `%` only at the two boundaries
  - Fails on the unchanged tree.

#### Held by review

- The trailer `%` sits before the single last line end that Pygments leaves after the `\end{Verbatim}` strip, and is not found by a second whitespace strip (design §4). No reachable reST input ends in whitespace (docutils rejects it before the closing backquote), so every test here passes under either construction. The rule is held by reading the diff.

#### Implement

Infer from failing tests.

# Hint: the opener `%` goes in the string the `Verbatim` opener is replaced with. Pygments writes a line end directly after the opener, and that line end is the one CP-9 wants after the `%`, so no line end is added or removed.

# Hint: after the existing strip of `\end{Verbatim}`, the text ends in exactly one character, the line end Pygments placed before it. The trailer `%` goes immediately before that single last character. Do not strip whitespace a second time to find the boundary: Pygments writes whitespace tokens raw, so a second strip would eat the highlighted text's own trailing spaces and break CP-11's byte-identity. Inner line ends of multi-line code come before that last character and are never touched.

#### Verification gate

Run `/home/kensai/issue-test.sh` from the product root.

Pass criteria: exit 0 with no failing test and an empty baseline (CP-14); both Task 2 tests pass, and `test_latex_code_role_unhighlighted_unchanged` from Task 1 still passes. Both Task 2 tests failed on the unchanged tree.
