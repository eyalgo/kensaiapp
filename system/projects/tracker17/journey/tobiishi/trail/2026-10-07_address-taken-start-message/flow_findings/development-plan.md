# Flow Findings — development-plan  (audited 2026-10-07)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 1–6 and 8 walked against `tl_instruction.md` beside `change_design.md` and `change_spec.md`. Every spec rule CP-39 to CP-46 maps to a test or a stated existing test, and the design's seven test rows appear as named cases. Header `Category: feature` / `Behaviour: changing` is copied verbatim. The product has no `docs/adr` conflict with the plan. Lenses 7, 9 and 10 do not apply to this step.

- **[non-blocking · change-local · divergence / enacted]** The plan fixes the message's words itself (Task 2 carries the CP-40 line, and every test asserts it) although the design names the content step as their owner ("from `change_text.md`", §3 Sub-job M). Where: `tl_instruction.md §Task 2`, `§TL Review Notes` "Input missing". The divergence is recorded with its reason, and the line is CP-40 verbatim, so the words match. The tests now hold a second copy of the words, so a later `change_text.md` edit would break them with no pointer back. Direction: the words stay the content step's, and the plan states the property (the line equals `change_text.md`'s with the address filled in).
- **[non-blocking · skill-general · coverage / ordering]** For a change whose design says `Publishes text: yes`, development-plan runs before development-content (plan commit `150ff22b8` precedes `59ca84814`, the text commit), so the TL can only quote words from the spec. Where: `change_design.md` header `Publishes text:`, `tl_instruction.md §TL Review Notes`. The "input missing" case is structural for every text-publishing change, not a slip of this run. → kaizen `plan-before-content-words-input`.
- **[non-blocking · change-local · coverage]** The plan has no case where `start` meets a non-address bind failure. CP-42 and Gap 5 require that failure to propagate unchanged. Task 1 proves it at `listen` (`test_listen_leaves_another_cause_unchanged`), but nothing says `main.start` lets it through rather than catching it. Where: `tl_instruction.md §Task 2 Behaviours to verify`. The code-integrity report records adding such a test after the fact, so the gap was real. Direction: a start-level case for the other-cause path.

Otherwise clean.
