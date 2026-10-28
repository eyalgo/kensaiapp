# Flow Findings — development-content  (audited 2026-10-28)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Clean — no flow-issues found.

Lens 10 was walked against `products/tracker17/docs/CONTENT.md` and `system/doctrine/writing_bar.md`:

- **Places.** `change_design.md` names five places on its `Publishes text:` line: control labels and choices, refusal reasons, the sort-only count, and the timed run's fixture and timing lines. `change_text.md` has a block for each, and no block names a place the line does not.
- **Banned words and marks.** No string holds a word `CONTENT.md` § Terminology bans or a mark § Grammar and mechanics bans, in any inflection. The timed-run lines carry a semicolon and an em dash, which `CONTENT.md` § Scope (RN-25) leaves outside the product's wording rules. The writing bar binds the instance's own documents, not product strings.
- **Whole strings.** Each string stands whole. The two counts ("1 task" and "{count} tasks") are written out. The refusal "{count}" is always 2 or more, so it needs no singular form. No string names an identifier or a file.
- **Claims.** No string claims a cause, state or guarantee the spec does not establish. The refusals say only that no option sends the value.
- **Match with existing text.** The refusal shapes match the filter's existing reasons: "Due from takes one date, not {count}" and "The status filter can't be '{value}', because it isn't a status" appear in `web/pages.py`. The existing "Sort by" and "Direction" labels there match the text file.
- **Classification and divergences.** The header `Category: feature` and `Behaviour: changing` match `change_spec.md`. The "Wording decisions" section records the load-bearing choices with reasons: no zero form for the sort-only count, "Created time" kept against CP-432, and no "Any" option.
