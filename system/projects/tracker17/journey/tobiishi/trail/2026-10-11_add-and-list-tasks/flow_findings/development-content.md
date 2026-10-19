# Flow Findings — development-content  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Checked: every string in `change_text.md` against `products/tracker17/docs/CONTENT.md` § Terminology and its "Banned in anything a person sees" table (a pattern search over the quoted strings returned only the `{error}` placeholder) and § Grammar and mechanics (contractions, punctuation, sentence count, case); `system/doctrine/writing_bar.md` binds this instance's own prose, not product strings. Blocks against the design's `Publishes text:` line: all eight places have a block and no block names a place the line does not. Wording divergences (`unassigned` for the UXD's "none", the position in the link's accessible name, the stale-assignee reload) are recorded under `## Wording decisions` / `## Findings for the Content Manager` with reasons.

- **[non-blocking · change-local · words the product can keep]** The due-date refusal's second sentence, "Pick one, or leave the due date empty.", tells the reader to pick a date. Where: `change_text.md` § when an add is refused or fails, due-date refusal; `CONTENT.md` § Grammar and mechanics, Dates and times ("no string tells the reader how to type or pick a date"). The wording decision justifies it as saying nothing about *how*, but the rule's text bars telling the reader to pick; direction: the owner of CONTENT.md rules whether "pick" is allowed here, or the sentence becomes "Leave the due date empty, or give a calendar date."

No other findings: lenses 1 (coverage of CP-106–CP-132 text places), 4 (divergences recorded), 8 (nothing enacted for a successor) and the rest of lens 10 (whole strings, no identifier, no unestablished cause or guarantee) came back clean.
