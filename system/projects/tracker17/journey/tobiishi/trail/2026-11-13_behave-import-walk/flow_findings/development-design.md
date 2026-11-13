# Flow Findings — development-design  (audited 2026-11-13)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 1 to 6 and 8 walked against `change_design.md`, read beside `change_spec.md`, `docs/nfdr.md` and the existing `tests/conftest.py`, `test_imports.py` and `test_trace.py`. Lenses 7, 9 and 10 do not apply to this step.

- **[non-blocking · change-local · coverage]** A `.py` file under `.behave/` that does not parse, or is not UTF-8, has no row and no stated outcome. Where: `change_design.md §5 Test Additions`, `§3 Sub-job A`. `BehaveWalk.modules()` parses every file it reads, so such a file ends the run with a `SyntaxError` or a decode error instead of the `AssertionError` the design's own contract names for "reads nothing". The spec is silent too, so the design had to either add a row or record the gap in its notes; direction: state the intended outcome, or note it as accepted.

Checked and held:

- Category and Behaviour (`nfdr`, `changing`) are copied verbatim from the spec.
- Every rule CP-796 to CP-807 maps to a Test Additions row. The rule-implied edges (near names, nested `.venv`, remaining import forms) are added and marked as such.
- The one divergence from the input, not reusing `SourceWalk`, is recorded with its reason under Architect Review Notes (c). The input's Locked Answers 1 and 8 are honoured.
- CP-801 is realized by construction (constant `part`), with a row that would fail a path-derived `part`.
- The handed-down property of the build order is stated, not enacted. "One test or two is the plan's call" leaves task granularity to the plan.
- The design's claims about existing code hold: `Module.imported()` returns the part for a relative import, `SourceWalk` asserts on empty, `violations` takes `(walk, part)` and flags non-stdlib names, and `test_trace.py` reads test-module docstrings.
- The Records This Change Makes False section names two NFDR entries.
