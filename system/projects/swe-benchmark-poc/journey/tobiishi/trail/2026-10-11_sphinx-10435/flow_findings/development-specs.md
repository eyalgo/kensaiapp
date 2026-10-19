# Flow Findings — development-specs  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 3 (Category `bug` / Behaviour `changing` copied verbatim from `change_request.md`), 4 (Gaps 1–6 each carry a reason; the existing-test divergence is recorded as Gap 5), 5, 6, 8 and 7 (`## Verified Claims` present; every verdict about what the builder writes was run with command, tree, interpreter and result; the one unrun claim is stated as not run) found nothing.

- **[non-blocking · change-local · altitude]** Rules CP-9 and CP-10 anchor on the writer's mechanism: source file and line numbers (`sphinx/writers/latex.py` lines 1712–1713, 1715–1717) and how the code "appends" `}}`. Where: `change_spec.md §Rules` CP-9, CP-10. The rule's observable is the `.tex` bytes, which each rule already states. The source anchors belong in Verified Claims, where they already appear, and not in the rule text.
- **[non-blocking · change-local · coverage]** CP-13's proof floor ("at least") names three tests: the reproduction, the two-line code, and the code-block. It names none for the rule-implied edges that the Examples table pins: unknown language, `none`, no language, `:kbd:`, plain literal, and a title. Where: `change_spec.md §Rules` CP-13 against `§Examples`. Only the code-block half of CP-12 is covered, so a regression that adds `%` to non-highlighted literals or the title form would pass the required tests. Direction: have downstream rows carry those Examples.
- **[non-blocking · change-local · evidence]** CP-12 says every builder other than `latex` and "its subclasses" keeps today's bytes. No Verified Claim built any other builder or any subclass. Where: `change_spec.md §Rules` CP-12, `§Verified Claims`. The claim rests on reading and reasoning, not on a run. Direction: run it, or state it as not run, as the TeX claim is.
