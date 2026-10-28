# Flow Findings — development-content  (audited 2026-10-28)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Clean — no flow-issues found.

What was checked, so the file does not read as "not audited":

- **Lens 10, places.** `change_design.md` `Publishes text:` names five places: the link pair, both page titles, the Summary's group headings and count labels, the first-task invitation and link, and the timed run's fixture and result lines. `change_text.md` has a block for each and none for a place the line does not name. The pair's landmark name `Project views` sits inside the link-pair block.
- **Lens 10, lexicon.** Every string was read against the banned-words table, the terminology rejections and the punctuation bans in `products/tracker17/docs/CONTENT.md`. No hit. `No due date` matches "No", which that table bans only as a control label. The timed run's semicolons are outside the standard (`CONTENT.md` RN-25) and match the existing fixture lines in `products/tracker17/tests/timed_run.py` (for example the `comment fixture:` line). The writing bar governs the document's own prose and binds no product wording (`system/doctrine/writing_bar.md` § 1.5).
- **Lens 10, whole strings.** The invitation is one string with the link set on one word. Each page title is a single template with one value. No string names an identifier or file; `tracker17` is the product name.
- **Lens 10, claims.** The descriptions under each string match `change_spec.md`: CP-491 (links, no filter or sort), CP-492 (titles, spaces kept), CP-496 and CP-498 (rows and totals), CP-499 and CP-500 (open tasks, order, `(unassigned)` last), CP-502 (invitation links to the Tasks view).
- **Lens 8.** The landmark name is left conditional on the Developer's markup choice and stated as a property. No downstream role is named or overruled.
- **Lens 4.** Decisions that go beyond the input (the `Total` row, the heading wording, the invitation's second sentence, the added project-name length in the fixture line) each carry a reason under `## Wording decisions`. The two gaps in `CONTENT.md` are handed to the Content Manager under `## Findings for the Content Manager`.
