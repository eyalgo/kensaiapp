# Change Design — LaTeX output of highlighted inline code has no space at its start and end

**Date:** 2026-10-11
**Category:** bug
**Behaviour:** changing
**Publishes text:** no

---

## 1. Change Summary

The LaTeX writer turns highlighted inline code into `\sphinxcode{\sphinxupquote{…}}` by taking
Pygments' `Verbatim` block, swapping its opener for `\sphinxcode{\sphinxupquote{` and cutting off
`\end{Verbatim}`. Both boundary line ends that Pygments wrote survive that swap, and TeX typesets
them as the two spaces the issue reports. The change puts a `%` directly before each of those two
line ends and changes nothing else (CP-9 to CP-11). It is confined to one method,
`LaTeXTranslator.visit_literal` in `sphinx/writers/latex.py`, on the branch that handles a `code`
literal carrying a language. The branches for titles, `:kbd:` and literals without a language
return before that point, so CP-12 holds because of how the method is built, and those outputs do
not move. The tests move with the change. The existing `test_latex_code_role` assertion that pins
today's markup is rewritten to CP-11's three lines, and a new test root covers the rest of the
spec's Examples.

**Outward boundary.** The change stores nothing on a device, collects nothing and sends nothing to a
third party. It is a local patch to a clone that is never pushed (`project.md`, `Manages: none`), so
it publishes nothing. Its cross-surface blast radius is nothing: no presence surface states this
markup.

---

## 2. Blast Radius

The product has no `docs/`, so there is no `adr/`, no `nfdr.md` and no `SDD.md` § 3 parts table. No
part is named for placement. The module set below is drawn from the spec's own boundaries and from
the code.

| Module | Status | What changes |
|---|---|---|
| `sphinx/writers/latex.py` | Modified | `LaTeXTranslator.visit_literal`, highlighted branch only. The `%` goes in the replacement opener, and another goes before the trailer's last line end. The method's signature and the other three branches are untouched. |
| `sphinx/highlighting.py` | Unchanged | `PygmentsBridge.highlight_block` still returns the full `Verbatim` block. The writer adapts that block, as it does today. |
| `sphinx/texinputs/` (`sphinxlatexliterals.sty` etc.) | Unchanged | The `\sphinxcode` and `\sphinxupquote` macros are out of scope. |
| `sphinx/writers/{html,html5,text,texinfo,manpage}.py` | Unchanged | They have their own `visit_literal` or none, and do not import the LaTeX one (CP-12, other builders). |
| `tests/test_build_latex.py` | Modified | `test_latex_code_role` moves to CP-11's markup, and new tests cover the rest of the Examples (§5). |
| `tests/roots/test-latex-code-role/` | New | A test root holding the probe document for the Examples that the issue's `index.rst` does not carry (§5). |
| `tests/roots/test-reST-code-role/` | Unchanged | It is the issue's reproduction as it stands. `test_build_html.py::test_html_code_role` reads it too, and it stays untouched. |

**Transitive radius.** `visit_literal` keeps its signature, and no in-tree class overrides it or
calls it except docutils' dispatch. A third-party subclass of `LaTeXTranslator` inherits the new
output, and CP-12 ("`latex` and its subclasses") puts that output in scope. No importing module is
affected.

---

## 3. Sub-jobs

Omitted: one module is affected, and its one change has no inner seams with an ordering edge between
them. The opener `%` and the trailer `%` sit in one branch of one method. Each is shown by the same
tests (CP-9 and CP-10 are asserted together on every highlighted Example), so the two have no
separate green point. They land as one delta.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `sphinx/writers/latex.py`: opener `%` (CP-9) | Put the `%` in the string the `Verbatim` opener is replaced with. Pygments writes a line end directly after the opener, and that line end becomes the one CP-9 wants after the `%`, so no line end is added or removed. |
| `sphinx/writers/latex.py`: trailer `%` (CP-10, CP-11) | After the existing strip of `\end{Verbatim}`, the text ends in exactly one character: the line end Pygments placed before `\end{Verbatim}`. Insert the `%` before that single last character. Do **not** strip whitespace a second time to find the boundary. Pygments writes whitespace tokens raw (probed: source `x = 1 ` gives `…\PY{l+m+mi}{1} ⏎\end{Verbatim}`), so a second strip would eat the highlighted text's own trailing spaces and break CP-11's byte-identity. Inner line ends of multi-line code come before that last character and are never touched. |

---

## 5. Test Additions

The card's `Test command:` runs `tests/test_build_latex.py` alone, so every new test lives in that
file.

| Sub-job | Test file | What to add / modify |
|---|---|---|
| `latex.py` | `tests/test_build_latex.py` | **Modify** `test_latex_code_role` (root `reST-code-role`, the issue's `index.rst`). Its inline assertion at 1626–1627 changes from `\sphinxupquote{` + line end + text + line end + `}} code block` to CP-11's three lines: `Inline \sphinxcode{\sphinxupquote{%` + line end + the unchanged `common_content` + `%` + line end + `}} code block`. The code-block assertion at 1628–1630 stays byte-for-byte (CP-12, the issue's code-block). Fails on the unchanged tree. Covers Example rows 1 and 10. |
| `latex.py` | `tests/roots/test-latex-code-role/` (new: `conf.py`, `index.rst`) | A probe document holding: a `python` role derived from `code`; ``:python:`1` ``; one `:python:` role spanning two source lines (`a = 1` / `b = 2`); roles derived from `code` with `:language: nosuchlang` and `:language: none`, each on `x = 1`; a role derived from `code` with no `:language:`; `:code:` alone on `x = 1`; a plain ` ``literal text`` `; ``:kbd:`Ctrl+C` ``; and a section title holding a highlighted role on `x = 1`. |
| `latex.py` | `tests/test_build_latex.py` | **New** test on that root, asserting each highlighted Example's exact expected form. ``:python:`1` `` gives `\sphinxcode{\sphinxupquote{%⏎\PYG{l+m+mi}{1}%⏎}}`. `nosuchlang` and `none` each give `\sphinxcode{\sphinxupquote{%⏎x = 1%⏎}}`. The two-line role gives its form with the **inner line end bare** and `%` only at the two boundaries. Fails on the unchanged tree. Covers Example rows 2–5, CP-9, CP-10, and the multi-line case of CP-11 that CP-13 names. |
| `latex.py` | `tests/test_build_latex.py` | **New** test on the same root, asserting CP-12's unchanged forms. ` ``literal text`` ` gives `\sphinxcode{\sphinxupquote{literal text}}`. `:code:` alone and the derived role with no language each give `\sphinxcode{\sphinxupquote{x = 1}}`. `:kbd:` gives `\sphinxkeyboard{\sphinxupquote{Ctrl+C}}`. The title gives `\sphinxstyleliteralintitle{\sphinxupquote{x = 1}}`, with no `\PYG` and no `%` inside it. This is a regression fence and passes on both trees. Covers Example rows 6–9. |

**Rule-implied edges.**

- An unknown lexer warns but still goes through the highlighted branch. Covered by the `nosuchlang`
  row. The test asserts the markup and does not suppress or assert the warning, which is today's.
- `none` goes through the same branch. Covered by the `none` row.
- A section title takes the title branch even when it carries a language. Covered by the CP-12 title
  assertion.
- No `%` appears anywhere except the two boundaries. Covered by the exact-form assertions, which pin
  whole strings, and by the two-line row's bare inner line end.
- The edge "no other builder moves" has no LaTeX test. The writer change cannot reach another
  builder (§2). The suite the card runs holds no HTML test.

**CP-13 / CP-14 rows (Examples 11–13).** The modified test and the first new test fail on the
unchanged tree and pass with the change. That is their red-then-green. The card's command
(`/home/kensai/issue-test.sh`) must then exit 0 with an empty baseline. This is checked by running
it, not by a test row.

**What the change stops proving.** One assertion is retired: today's
`\sphinxupquote{` + line end + text + line end + `}} code block` at 1626–1627, which pins the
defect. Its clause, "the issue's reproduction is written as the writer writes it", is re-proved in
its corrected form by the modified assertion in row 1. No other assertion is retired.

---

## Records this change makes false

None. I looked for `adr/`, `nfdr.md`, `fdr.md` and `SDD.md` under
`<product_worktree>/docs/`, and the product has no `docs/` folder, so there is no record for this
change to make false.

---

## Architect Review Notes

- **(b) Trailer `%` placed before the single last line end, not found by stripping whitespace
  again:** I made CP-10's position explicit. The `%` goes immediately before the one line end
  that Pygments puts ahead of `\end{Verbatim}`, so every earlier byte stays as Pygments wrote it.
  Reason: CP-11 requires the highlighted text to be byte-identical. Pygments writes trailing
  whitespace raw (probed with the card's interpreter), so any boundary found by a second strip
  would meet CP-10 only when the text happens to end in a non-space. This makes it hold every time.
- **(b) The issue's reproduction test is changed in place, not duplicated:** the spec's Gap 5 left
  open how the old assertion is brought into line. `test_latex_code_role`'s inline assertion is
  rewritten to CP-11's markup, and its code-block assertion stays as it is. Reason: the old
  assertion pins exactly the defect this change exists to move. A second test on the same root
  would leave two assertions disagreeing about one output, and the card's command fails on the old
  one (spec, Verified Claims).
- **(b) New test root instead of extending `test-reST-code-role`:** the other Examples go in a new
  root, `tests/roots/test-latex-code-role/`. Reason: `test-reST-code-role` is the issue's own
  `index.rst`, and `test_build_html.py::test_html_code_role` reads it too. Leaving it untouched keeps
  the issue's reproduction exact, and no HTML test outside the card's suite can be disturbed.
- **(d) No sub-jobs, and the opener and trailer `%` land as one delta:** this matches the skill's
  single-module rule. It is logged because two edits to one method could look like two seams. They
  share one branch and are asserted together on every highlighted Example, so neither has a green
  point of its own.
- **Outward boundary stated as "nothing":** the instance overlay asks a design to name what it
  stores, collects and sends, and its cross-surface radius. All four are nothing here (§1). That is
  stated so the silence cannot be read as an omission.
