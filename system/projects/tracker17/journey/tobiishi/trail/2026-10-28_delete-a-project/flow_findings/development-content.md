# Flow Findings — development-content  (audited 2026-10-28)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Clean — no flow-issues found.

Checked:
- Lens 10, places: `change_text.md` has four blocks (Delete project control, confirmation and failure line, completion line on Projects, terminal message). They match the four places the design's `Publishes text:` line names, and no block names another place.
- Lens 10, words: every string was checked against `CONTENT.md` § Terminology rejected terms, the banned-in-anything-a-person-sees table, and § Grammar and mechanics (contractions, quotes, numerals, no semicolon or em dash, sentence length, control labels). "console" appears only in prose naming the place, not in a string. `writing_bar.md` states no word list, so nothing further binds the strings.
- Lens 10, whole strings: no fragment is joined at runtime (each count form is a whole sentence), no identifier or file is named, and no cause is claimed.
- Lens 1: the 2-or-more, 1 and 0 forms exist for both the confirmation (CP-570) and the completion line (CP-576). The failure line and terminal message (CP-578) and the Back out no-line case (CP-573) are covered. CP-580/582 reuse existing not-found pages and the block says so.
- Lens 4: each choice that departs from or fills a gap in the spec (zero-task completion wording, "the project" in the failure line, no "Try again." in the terminal line, no added accessible name, no-projects state kept) is recorded under Wording decisions with its reason.
- Cross-check against product source: `web/pages.py` and `web/routes.py` already carry the same failure and terminal wording, and `BACK_OUT_LABEL = "Back out"`, as the decisions section claims.
