# Flow Findings — development-content  (audited 2026-10-11)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Clean — no flow-issues found.

Lens 10 (words the product can keep), checked against `products/tracker17/docs/CONTENT.md` § Terminology (banned table and "Banned in anything a person sees") and § Grammar and mechanics, and `system/doctrine/writing_bar.md` (§ 1.5 and § 2: it binds no product wording, so it adds no banned word):
- No banned or rejected word in either string in any inflection (scan run over `change_text.md`: none of admin, system as the tracker, just, simply, easy, please, failed, fails, failure, error, click, above, below, here, now, today in the strings; "system" appears only in "system libraries" and "operating system's", neither naming the tracker).
- Places: `change_design.md` `Publishes text:` names one place, "the setup instructions' Running the tests section". `change_text.md` has one place heading and two blocks inside it, matching design edit sites 1 and 2. No block names another place.
- Whole strings: both are complete paragraphs, nothing a runtime joins. Names only commands the spec requires (`python -m playwright install --with-deps chromium`, `pytest tests/`, `git`); no file or identifier.
- Claims: each traces to the spec (CP-70 to CP-75) and to `docs/SDD.md` § 4 RT-4; none states a cause or guarantee beyond them.
- Sentence lengths counted by hand: longest is 20 words, within the limit.

Other lenses: coverage — CP-70 to CP-76 each map to a sentence; CP-72's five systems and two architectures and the literal `Debian 12` all appear. Divergence — the three wording changes from the spec (operating system's, "every test", "1 test") are recorded with reasons under `## Wording decisions`. Classification — Category `bug` / Behaviour `changing` match `change_spec.md`.
