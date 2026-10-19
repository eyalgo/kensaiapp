# Change Spec — LaTeX output of highlighted inline code has no space at its start and end

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Request:** "Fix the issue below in the product, the repository that the project card's
`Product path:` names (`sphinx-doc/sphinx`). The repository stands at the commit before the issue was
fixed. Make the change the issue asks for, with tests of your own that show it, and leave the rest of
the product's behaviour as it is." The issue is `sphinx-doc__sphinx-10435`, quoted in full in this
folder's `change_request.md` § *The issue*. Its constraints are that file's § *What must not be done*.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, and every concern it routes read (`toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `testing_python.md`)

---

## Change Summary

When Sphinx's LaTeX builder writes highlighted inline code, it puts a bare line end directly after
the opening `\sphinxcode{\sphinxupquote{` and another directly before the closing `}}`. TeX typesets
each of those line ends as a space, so the PDF shows a space at the start and at the end of the
inline code. After this change, each of those two line ends is preceded by a `%`, which is the markup
the issue gives as "a priori, mark-up should be". Nothing else in the output changes.

**Terms used below.**

- **Highlighted inline code** is text in reST input marked with the `code` role, or a role derived
  from it, whose role sets a `:language:` option. The option can hold any value, including one
  Pygments does not know (e.g. `nosuchlang`) and `none`. The text is written in body text, not in a
  section title, and the role is not `:kbd:`. The issue's `:python:` role is the standard case.
  Today the LaTeX builder writes every such text as `\sphinxcode{\sphinxupquote{`, a line end, the
  **highlighted text**, a line end, and `}}` (Verified Claims).
- The **highlighted text** is what sits between those two line ends today: the `\PYG{…}{…}`
  sequence, which contains a line end of its own only where the code spans more than one line.
- The **`.tex` output** is the `.tex` file the `latex` builder writes, e.g. `python.tex` for a
  project with no `project` setting.

---

## Rules

### The LaTeX output of highlighted inline code

- **CP-9:** In the `.tex` output, the opening `\sphinxcode{\sphinxupquote{` of highlighted inline
  code is followed directly by `%` and then a line end. Nothing stands between `{` and `%`, or between
  `%` and the line end. This removes a present defect. Today `sphinx/writers/latex.py` lines
  1712–1713 write the opening as `\sphinxcode{\sphinxupquote{` followed by a bare line end. The issue
  reports that line end as the space at the start.
- **CP-10:** The last character of the highlighted text is followed directly by `%`, then a line
  end, then `}}`. Nothing else stands between them. This removes the matching present defect.
  Today `sphinx/writers/latex.py` lines 1715–1717 leave a bare line end after the highlighted text and
  then append `}}`. The issue reports that line end as the space at the end.
- **CP-11:** Everything around the two `%` stays as it is today. The highlighted text is
  byte-identical: the same `\PYG` tokens, the same spaces inside it, and, for code that spans more
  than one line, the same line ends inside it. The text before `\sphinxcode` and after `}}` is
  unchanged as well. For the issue's reproduction the `.tex` output therefore holds exactly these
  three lines:

  ```
  Inline \sphinxcode{\sphinxupquote{%
  \PYG{k}{def} \PYG{n+nf}{foo}\PYG{p}{(}\PYG{l+m+mi}{1} \PYG{o}{+} \PYG{l+m+mi}{2} \PYG{o}{+} \PYG{k+kc}{None} \PYG{o}{+} \PYG{l+s+s2}{\PYGZdq{}}\PYG{l+s+s2}{abc}\PYG{l+s+s2}{\PYGZdq{}}\PYG{p}{)}\PYG{p}{:} \PYG{k}{pass}%
  }} code block
  ```

### What does not change

- **CP-12:** CP-9 to CP-11 apply to highlighted inline code only. Every other output keeps
  today's bytes. That covers the LaTeX output of:
  - a plain inline literal (` ``literal text`` `), which is `\sphinxcode{\sphinxupquote{literal text}}`;
  - a `code` role with no language (`:code:` alone, or a role derived from `code` with no
    `:language:`), which is `\sphinxcode{\sphinxupquote{x = 1}}`;
  - `:kbd:`, which is `\sphinxkeyboard{\sphinxupquote{Ctrl+C}}`;
  - any inline literal in a section title, a highlighted role included, which is
    `\sphinxstyleliteralintitle{\sphinxupquote{x = 1}}` and stays unhighlighted;
  - a `code-block` and every other literal block, which is `\begin{sphinxVerbatim}…\end{sphinxVerbatim}`.

  It also covers the output of every builder other than `latex` and its subclasses.

### Proof

- **CP-13:** The change carries tests of its own, and the card's `Test command:` runs them. The tests
  that show CP-9 and CP-10 fail on the unchanged tree and pass with the change. Together the tests
  cover at least:
  - the issue's reproduction (its `index.rst`, which is the same text as
    `tests/roots/test-reST-code-role/index.rst`), asserting the three lines in CP-11;
  - highlighted inline code that spans two lines, showing that its inner line end stays (CP-11);
  - the issue's code-block in the same document, showing that its `sphinxVerbatim` output is unchanged (CP-12).
- **CP-14:** The card's `Test command:` exits 0, and no test in its run fails. At `base_commit` no
  test fails, so the baseline it allows is empty.

---

## Examples

"Today" is the `.tex` output at `base_commit`, built on 2026-10-11 (see Verified Claims). `⏎` marks a
line end.

| Rule | Input (reST) | Today (`.tex`) | Expected (`.tex`) |
|---|---|---|---|
| CP-9, CP-10, CP-11 | the issue's ``Inline :python:`def foo(1 + 2 + None + "abc"): pass` code block`` | `Inline \sphinxcode{\sphinxupquote{⏎\PYG{k}{def} … \PYG{k}{pass}⏎}} code block` | `Inline \sphinxcode{\sphinxupquote{%⏎\PYG{k}{def} … \PYG{k}{pass}%⏎}} code block`, the `…` byte-identical to today |
| CP-9, CP-10 | ``:python:`1` `` | `\sphinxcode{\sphinxupquote{⏎\PYG{l+m+mi}{1}⏎}}` | `\sphinxcode{\sphinxupquote{%⏎\PYG{l+m+mi}{1}%⏎}}` |
| CP-9, CP-10 | a role with `:language: nosuchlang` on `x = 1` (Pygments warns that the lexer is not known, as today) | `\sphinxcode{\sphinxupquote{⏎x = 1⏎}}` | `\sphinxcode{\sphinxupquote{%⏎x = 1%⏎}}` |
| CP-9, CP-10 | a role with `:language: none` on `x = 1` | `\sphinxcode{\sphinxupquote{⏎x = 1⏎}}` | `\sphinxcode{\sphinxupquote{%⏎x = 1%⏎}}` |
| CP-11 | ``:python:`a = 1`` / ``b = 2` `` (one role spanning two source lines) | `\sphinxcode{\sphinxupquote{⏎\PYG{n}{a} \PYG{o}{=} \PYG{l+m+mi}{1}⏎\PYG{n}{b} \PYG{o}{=} \PYG{l+m+mi}{2}⏎}}` | `\sphinxcode{\sphinxupquote{%⏎\PYG{n}{a} \PYG{o}{=} \PYG{l+m+mi}{1}⏎\PYG{n}{b} \PYG{o}{=} \PYG{l+m+mi}{2}%⏎}}`: the inner line end stays bare |
| CP-12 | ` ``literal text`` ` | `\sphinxcode{\sphinxupquote{literal text}}` | unchanged |
| CP-12 | ``:code:`x = 1` `` (no language) | `\sphinxcode{\sphinxupquote{x = 1}}` | unchanged |
| CP-12 | ``:kbd:`Ctrl+C` `` | `\sphinxkeyboard{\sphinxupquote{Ctrl+C}}` | unchanged |
| CP-12 | a section title ``Sub with :python:`x = 1` inside`` | `\chapter{Sub with \sphinxstyleliteralintitle{\sphinxupquote{x = 1}} inside}` | unchanged |
| CP-12 | the issue's `.. code-block:: python` | `\begin{sphinxVerbatim}[commandchars=\\\{\}]⏎\PYG{k}{def} … \PYG{k}{pass}⏎\end{sphinxVerbatim}` | unchanged |
| CP-13 | the change's own CP-9/CP-10 tests, run on the unchanged tree | — | they fail |
| CP-13 | the change's own tests, run with the change | — | they pass |
| CP-14 | the card's `Test command:` run with the change | exit 0, `75 passed, 8 skipped` | exit 0, no failing test |

---

## Verified Claims

Every build ran on 2026-10-11 with the card's interpreter (`/home/kensai/issue-venv/bin/python`,
Python 3.9.25, Sphinx 5.0.0). Each ran `python -m sphinx -q -b latex` on a scratch source directory
under `/tmp`, against a disposable copy of the product worktree's `HEAD` (`git archive`) at
`base_commit` `f1061c012`. For the post-change rows, the copy also carried a scratch edit made only to
check that the rules can be met together. That edit is not a design. Nothing outside the clone was
consulted: no upstream history, no pull request, no benchmark copy. Both product checkouts stayed clean
(`git status --short` empty).

| Claim | Verified by | What came back |
|---|---|---|
| Today the issue's reproduction is written with a bare line end after `\sphinxupquote{` and before `}}` | built `tests/roots/test-reST-code-role` (the issue's `index.rst`) and read `python.tex` with `cat -A` | `Inline \sphinxcode{\sphinxupquote{$` / the `\PYG` line ending `\PYG{k}{pass}$` / `}} code block$`. This is the issue's "with current" markup |
| The writer code cited in CP-9 and CP-10 produces it | read `sphinx/writers/latex.py` 1695–1718 (`visit_literal`) | 1712–1713 replace the Verbatim opener with `\sphinxcode{\sphinxupquote{` and keep the line end after it. 1715 strips `\end{Verbatim}` and leaves the line end before it. 1716–1717 append the text, then `}}` |
| The class "highlighted inline code" is exactly the inputs with the boundary line ends | built a probe document holding a highlighted role, a two-line highlighted role, a plain literal, `:kbd:`, a derived `code` role with no language, `:code:` alone, roles with `:language: nosuchlang` and `:language: none`, and a highlighted role in a subsection title | Only the roles carrying a language had the boundary line ends, the unknown and `none` languages included. Each other input was written on one line exactly as the CP-12 rows show, and the title case was unhighlighted |
| The rules can be met together, and CP-12's outputs do not move | the same probe documents, built against the scratch post-change copy | every *Expected* cell of the Examples table matched, including the two-line row with its inner line end still bare, and the `sphinxVerbatim` block unchanged |
| The card's `Test command:` passes at base with no failure | ran `/home/kensai/issue-test.sh` from the root of the disposable base copy (with `PYTHONPATH` set to that copy) | `75 passed, 8 skipped, 1 warning`, exit 0 |
| The existing `test_latex_code_role` asserts today's defective markup, so the card's command cannot pass on a fixed tree with that assertion as written (Locked Answers, Gap 5) | read `tests/test_build_latex.py` 1605–1630. Ran the card's command on the scratch post-change copy with the test files untouched | lines 1626–1627 assert `\sphinxupquote{` + `'\n'` + text + `'\n}} code block'`. Result: `FAILED tests/test_build_latex.py::test_latex_code_role`, `1 failed, 74 passed`, `issue-test: failures not in the baseline`, exit 1 |
| With only that assertion moved to CP-11's markup, the command passes and the code-block assertion (1628–1630) holds unchanged | same copy, with lines 1626–1627 rewritten to the `%` form | `75 passed, 8 skipped`, exit 0 |
| A `%` before a line end stops TeX typesetting that line end as a space, so CP-9 and CP-10 remove the PDF's spaces | **not run.** No TeX engine is on this machine (`which pdflatex lualatex xelatex latexmk` found none), and the card's command builds no PDF | rests on the issue's own screenshot "if space characters removed from `.tex` file". The spec's acceptance is therefore stated on the `.tex` output |

**Language rendering.** No rule pins output that renders a language-level fact. CP-9 to CP-12 pin
LaTeX markup that Sphinx chooses to write, so the Python packet decides none of them. LaTeX is not a
language the resolution chain resolved, and no packet was opened for it.

---

## Out of Scope

- **How the PDF looks beyond the two spaces.** That covers fonts, colours, the `\sphinxcode` and
  `\sphinxupquote` macros, and `sphinxlatexliterals.sty` and the other style files. No PDF is built
  as part of this change (Verified Claims, last row).
- **The highlighted text itself.** Its Pygments tokens, the spaces inside it, and the line ends
  inside multi-line code all stay as today (CP-11). A multi-line inline code's inner line end still
  renders as one space, as an inline line break ordinarily does.
- **Inline literals that are not highlighted inline code, and every literal block** (CP-12),
  including highlighted roles in section titles, which stay unhighlighted.
- **Every builder other than `latex`.** HTML, text, Texinfo, man pages and the rest keep their output.
- **Pygments' `nowrap` option** named in the TODO at `sphinx/writers/latex.py` lines 1710–1711. The
  request does not ask for it, and CP-11 holds whichever way the output is produced.
- **`CHANGES` and the documentation.** The request asks for no entry. Other surfaces were not
  looked at for statements of this markup.
- **Anything outside the local clone.** The patch is not pushed (`project.md`, `Manages: none`), and
  nothing is published. Per the request, no record, grade or benchmark file is produced.

---

## Locked Answers (the divergence record — self-review 2026-10-11)

- **Gap 1: the spaces are a defect to remove.** The issue ends its markup with "But I have no no
  strong opinion if good or bad." The spec removes the spaces anyway, for three reasons. The issue's
  title reports them as a bug ("adds whitespace at start and end in pdf output"). Its screenshots set
  the current output beside the output without the spaces and the output before #10251. The request
  asks for "the change the issue asks for", and the PM classified it as a `bug`.
- **Gap 2: the `%` markup the issue gives, exactly (CP-9 to CP-11).** Other markup would also
  remove the spaces, such as putting the highlighted text on the same line as the braces. The spec
  pins the issue's "a priori, mark-up should be" instead. It is the only form the issue states. It
  also leaves every other byte of the output as it is today, which is what the request's "leave the
  rest" asks.
- **Gap 3: every language is in the class, including unknown ones and `none` (the Terms).** The
  issue shows Python only. Each of the other cases writes the same bare line ends today, so it has
  the same spaces (Verified Claims). Leaving them out would leave the issue's defect standing for
  those inputs. The change only moves output, so it is reversible.
- **Gap 4: multi-line inline code keeps its inner line end (CP-11).** The issue concerns the start
  and the end only. An inner line end is an inline line break, and it renders as one space as it
  does today. Removing it would change what the reader sees between two words of code, which the
  issue does not ask for.
- **Gap 5: the existing assertion at `tests/test_build_latex.py` 1626–1627 moves with the change
  (CP-14).** The request says to leave the rest of the product's behaviour as it is, and that
  assertion holds the exact markup the issue reports. It is the behaviour this change exists to
  move, not part of "the rest". On a fixed tree, the card's command fails on it and on nothing else
  (Verified Claims). The code-block assertion at 1628–1630 stays as it is. How the test is brought
  into line is development-design's decision.
- **Gap 6: acceptance is on the `.tex` output, not the PDF (CP-9 to CP-13).** The issue states its
  expected markup at the `.tex` level. No TeX engine is available to build the PDF, and the card's
  command builds none. A rule on the PDF could not be checked by anyone downstream.
