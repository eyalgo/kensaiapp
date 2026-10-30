# Flow Findings — development-content  (audited 2026-10-30)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

- **[non-blocking · change-local · handed-down constraint]** One Wording decision says "the Developer places the strings in this order", naming a downstream role for the placement. Where: `change_text.md §Wording decisions` (the `The tracker didn't start` bullet). The order is content's own call (the spec fixes none), so deciding it is in scope. Naming the role that places it is not needed: state the order as a property of the section and stop. Mild, and nothing downstream is misled by it.

Lens 10 and the other lenses found nothing:
- **Places.** The design's `Publishes text:` line names one place, the "What the start prints" section. `change_text.md` has one block for that place and none for another.
- **Banned words.** Every string was read against `products/tracker17/docs/CONTENT.md` § Terminology (rejected terms) and "Banned in anything a person sees", in every inflection. No hit. "Stopped" is used as the setup instructions' own word, and the step records the missing term in its findings.
- **Mechanics.** No em dash, semicolon, ellipsis or exclamation mark. Colons appear only inside addresses. Negatives are contracted. The longest new sentence is 18 words, within the limit of 20 (CP-746). `system/doctrine/writing_bar.md` binds documents this instance authors, so it adds nothing to a product string.
- **Whole strings.** Each string is a whole sentence. None names an identifier or file. The only literals are program text and the example location.
- **Claims.** Each claim traces to the spec: still running (CP-738), the Projects page said of the ready line only (CP-740), "this start has stopped" (CP-741), no "three" and no claim that nothing else appears (CP-743). The decision that the line belongs to a start that went ahead on that data matches `products/tracker17/main.py` `_serve_claimed` and `_bind`.
- **Coverage.** CP-736 to CP-743 and CP-746 each map to a string. CP-744 and CP-745 are no-change rules and need none.
- **Divergence record.** Each departure from the request's wording (the "can't read" phrasing, the moved sentence, the bare heading, "in these setup instructions") has its reason in the Wording decisions.
- **Classification.** `Category: feature` and `Behaviour: changing` match the spec and the design.
