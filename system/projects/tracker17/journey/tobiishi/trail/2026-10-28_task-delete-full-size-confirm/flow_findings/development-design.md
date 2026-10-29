# Flow Findings — development-design  (audited 2026-10-29)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Lenses 1 (coverage), 3 (classification), 6, 8 and 10 held. Every CP-609–CP-618 maps to a T row, the Examples numbers cited match the spec's table, and `Category: feature` / `Behaviour: changing` / `Publishes text: no` are copied verbatim. Lenses 7, 9 and 10 do not apply to this step. Two findings:

- **[non-blocking · change-local · contract-realized]** The design says the first-press/confirm height equality is realized "by construction" (§4, Architect Review Notes), but it is two separate 36px literals that agree today: `.strip-control button.button-confirm { height: 36px }` and `button.button-secondary { height: 36px }` (`web/style.css:345-357`, `:360-373`). Nothing ties them together. Where: `change_design.md §4 Code Strategy`, `§Architect Review Notes`. Only T1's measurement guards the equality, so name that as the guard (or share a token); don't call it construction.
- **[non-blocking · change-local · divergence-record]** "Retire the obsolete task-delete selector from the row-control stylesheet rules and correct the associated comments" adds a stylesheet clean-up the spec never asks for (spec Out of Scope is silent on CSS). It lands with no Architect Review Notes entry giving its reason, and no check that no other page still uses `delete-button`. Where: `change_design.md §2 Blast Radius (web/ row)`. Record the reason, or drop it from this change.
