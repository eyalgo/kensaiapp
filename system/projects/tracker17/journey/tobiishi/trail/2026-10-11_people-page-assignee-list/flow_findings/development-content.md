# Flow Findings — development-content  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Audited: `change_text.md` against `change_spec.md`, `change_design.md` (`Publishes text:`), `products/tracker17/docs/CONTENT.md` (Version 8) and `system/doctrine/writing_bar.md`.
Lens 10 result: every string was checked against CONTENT.md § Banned in anything a person sees and § Terminology's rejected terms, in every inflection. No banned or rejected word appears in any string. The writing bar bans no product word (§ 1.5, § 2). Sentence counts, contractions, quoting, punctuation and the 20-word limit hold. No string joins fragments or names an identifier or file. Every claim in a string is established by CP-84, CP-94, CP-96 or CP-97. Lenses 1–6, 8 produced nothing beyond the two findings below.

- **[non-blocking · change-local · step-specific contract (lens 10)]** The first block, "The header, on every page the tracker serves", carries the product name and the Projects link as well as the People link. The design's `Publishes text:` line names only "the header's People link". Where: `change_text.md §The header`; `change_design.md` line 6. Two of its three strings already exist in the product (`products/tracker17/web/pages.py` header, per `change_spec.md` § Verified Claims). The block names places the line does not, so either the line or the block is wrong. Direction: the block states only the People link, or the design's line is widened by its owner.
- **[non-blocking · change-local · step-specific contract]** Many "When the person sees it" notes restate focus and Tab behaviour that the spec and design own, for example "focus is on that name. The next Tab press goes on to its Remove button" and "Focus is on Add". Where: `change_text.md §The People page, after an add or a remove`. This is a second home for CP-87, CP-94, CP-97 and design § 3 Sub-job D's outcome table, so it can drift from them. They agree today. CONTENT.md § Localization asks for the state a string answers and what the reader had just done, not where focus lands. Direction: keep the state and the reader's action, and point at the owners for focus.

No blocking findings.
