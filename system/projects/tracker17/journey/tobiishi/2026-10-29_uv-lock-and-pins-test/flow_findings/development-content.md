# Flow Findings — development-content  (audited 2026-10-29)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Checked: lens 10 (banned words and punctuation in every inflection against `products/tracker17/docs/CONTENT.md` § Terminology and § Grammar and mechanics, and against `system/doctrine/writing_bar.md` § 1.2; one block for the one place the design's `Publishes text:` line names; the string whole, 100 columns or fewer, no fragment a runtime joins), plus lenses 1, 3, 4 and 6. `CONTENT.md` exists and scopes out code comments; the writing bar governs the note. No banned word or mark was found. The note as written matches the comment now in `products/tracker17/pyproject.toml`.

- **[non-blocking · change-local · step-specific contract]** The note carries two claims the spec does not establish: a pin edit is followed by `uv lock`, and `uv sync --locked` refuses a `uv.lock` out of step with the group. Where: `change_text.md §Text`, sentences 5 and 6. `change_spec.md` CP-660 asks only that the comment name `uv.lock` where it names `tests/requirements.txt`, and `change_design.md` calls the change "only the declaration-note comment block". Both claims come from `products/tracker17/docs/SDD.md` § 4 RT-4 and are recorded in `## Wording decisions`, so the divergence is recorded with its reason. RT-4 says the refusal is against `pyproject.toml`, and the note narrows it to "this group". Direction: the spec's owner confirms the wider note, or the spec names it.

_Lenses 1, 3, 4 and 6 and the banned-word half of lens 10: Clean._
