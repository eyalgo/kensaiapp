# Flow Findings — development-content  (audited 2026-10-28)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Checked: every string in `change_text.md` against `products/tracker17/docs/CONTENT.md` (§ Terminology banned list, § Grammar and mechanics, § Message patterns Error and Completed) and `system/doctrine/writing_bar.md`; the design's `Publishes text:` line against the blocks; the spec's CP-546–CP-557 and CP-566 for what each string may claim. Header `Category: feature` / `Behaviour: changing` match the spec verbatim. Seven places named by `Publishes text:`, seven groups of blocks, none extra. No banned word, punctuation, Latin abbreviation or "click" in any string; every typed value is quoted in straight single quotes; every sentence is under 20 words. The refusal reasons match CP-555 word for word. No fragment is joined at runtime, no identifier or file name appears, and no cause is claimed.

- **[non-blocking · change-local · divergence-record]** The "no heading" call for the Rename area rests on CP-546 alone and does not mention the two inputs that read the other way. Where: `change_text.md §Wording decisions`, first bullet. UXD UX-F10 (`docs/UXD.md` § 5.10) writes "**Rename** with the current name in a field → Save", and the spec's Examples row for `/projects/1` reads "Below the list: Rename, a labelled field holding `Alpha`, then `Save`". Both can be read as a visible word "Rename". The stage may well be right, and CP-546's parts list supports it, but the entry should say it saw those two lines and why they do not give the area a visible name, so a Developer or QA reader doesn't find an unrecorded departure. Direction: add the reason to the existing bullet.
- **[non-blocking · change-local · divergence-record]** Typo in the same bullet group: "the design.s rename outcome" (`§Wording decisions`, second bullet). The sentence is also over-long and repeats the quoted design line. Where: `change_text.md §Wording decisions`. Direction: split it.

_Lens 10 result: no blocking hit. `docs/CONTENT.md` is present and was used._
_Lens 7 (content): the banned-word check in the record was by reading; the product has no vocabulary check, which this audit confirmed by grep of `tests/`. Nothing further to run._
