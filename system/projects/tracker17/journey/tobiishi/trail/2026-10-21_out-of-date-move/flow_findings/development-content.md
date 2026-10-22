# Flow Findings — development-content  (audited 2026-10-21)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Checked: `change_text.md` against `change_spec.md` (CP-355 to CP-362), `change_design.md` (`Publishes text:`), `products/tracker17/docs/CONTENT.md` (Terminology, Grammar and mechanics, *A refusal*) and `system/doctrine/writing_bar.md`.

- **[non-blocking · change-local · coverage]** The "offers one move" string (both places) has no rule or example behind it. Where: `change_text.md §Text`, "Overtaken press, the task now offers one move". Spec CP-359 and the workflow give 0, 2 or 3 moves (`done`/`cancelled` none, `todo` two, `in-progress` three); no status offers one, and the Examples table has no such case. The string is unreachable today, yet it adds a line the Developer must place and a test must cover. Direction: keep it only if the design names a path that produces a single move, else drop it or record in Wording decisions why a count the product cannot reach is written.

Lens results with no finding:
- Lens 10: `Publishes text:` names two places (Tasks view row, task's page), and `change_text.md` has a block for each and none other. CP-361's address-refusal line is verbatim. No word from CONTENT.md's Terminology rejected list or the writing bar appears in any string (the "changed" use is recorded under Wording decisions). Strings are whole, contracted, two sentences, at most 20 words, with no relative-time word, identifier, file or reload. The `has changed` claim is the one CP-359 establishes. The hand-built-submission case where it can read wrongly is recorded in the spec's Locked Answers, Gap 1.
- Lens 3: `Category: feature` / `Behaviour: changing` copied from the spec.
- Lens 4: divergences (no "since this page loaded", no reload, four whole strings, no comma before "or") are recorded with reasons in Wording decisions and Findings for the Content Manager.
- Lens 8: no downstream role named. The opening paragraph restates the spec's focus and description contract (CP-358, CP-360) in a text record; it is a restatement, not an instruction, and is not raised.
