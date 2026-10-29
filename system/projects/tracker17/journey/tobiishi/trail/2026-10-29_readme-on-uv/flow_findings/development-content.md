# Flow Findings — development-content  (audited 2026-10-29)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Checked: `change_text.md` against `change_spec.md` (CP-668 to CP-684), `change_design.md` (its `Publishes text:` line), `products/tracker17/docs/CONTENT.md` (§ Grammar and mechanics, § Terminology, the banned table) and `system/doctrine/writing_bar.md`. The writing bar bans no word, so lens 10's writing-bar check found nothing to match.

- **[non-blocking · change-local · claims-beyond-spec]** The opening paragraph says setting up the tests needs a network connection "for `uv sync --locked` and `uv run playwright install chromium` only". The same paragraph tells the reader to install uv from uv's page first, and that install needs the network too. The word "only" claims a bound the spec does not establish. CP-675 says only that the network is needed for setting up, and the old sentence's "install commands only" did not name uv's own install either. Where: `change_text.md §The README's Running the tests section`, string 1; `§Wording decisions`, the network-sentence bullet. Direction: state the smaller true thing, or keep "only" and say what it excludes.
- **[non-blocking · change-local · referent]** The opening paragraph now names two commands before its last sentence, "Open a terminal at the top of your copy and type these commands." That sentence is kept word for word, but "these commands" no longer points at the block two paragraphs below. It can read as the two commands just named. Where: `change_text.md §The README's Running the tests section`, string 1; `§Wording decisions`, the bullet keeping that sentence. The Wording decisions record the keep and its reason (CP-669) but not the new ambiguity. Direction: weigh the keep against the reader's reading, and record the choice either way.

## Lenses with nothing found

- **Coverage (1):** Clean. Every CP rule that touches published text (668 to 678) maps to a string, and rule-implied cases are covered: the Linux variant, a misplaced environment, a new terminal, the Git paragraph kept. CP-679 to CP-684 bind checks, not strings.
- **Classification (3):** Clean. `nfdr` and `changing` match the spec and the design verbatim.
- **Divergence record (4):** Clean. The `## Wording decisions` and `## Findings for the Content Manager` sections carry each departure with its reason, including the two open scope questions about punctuation and a sentence starting with a tool name.
- **Places named by `Publishes text:` (10):** Clean. Blocks exist for the Running the tests section, the two How it's built bullets and The documents line, and none names another place.
- **Banned words (10):** Clean. No hit in the banned table or the rejected terms, in any inflection. The README's fixed-string grep from CP-680 matches nothing in the strings. The only matches in `change_text.md` are in the wording-decision prose that quotes the old text.
- **Sentence length (10):** Clean. No string has a sentence over 20 words; the longest are exactly 20.
- **Whole strings, no identifier claims (10):** Clean. Each string is whole. File and path names appear only where the README's reader types them.
- **Altitude, handed-down constraints (2, 8):** Clean. No downstream role is named or decided for.
- **Not applicable:** Lenses 7 and 9 apply to other steps.
