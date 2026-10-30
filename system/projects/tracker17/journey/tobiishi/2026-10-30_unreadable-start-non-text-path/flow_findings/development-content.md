# Flow Findings — development-content  (audited 2026-10-30)

Findings for this step's output only, produced by the `development-audit` skill.
Change-local findings live here; skill-general findings are also raised as kaizen items.

Read against: `change_spec.md` (CP-757–CP-772, Out of Scope), `change_design.md` (`Publishes text:` names the unreadable-data console line and the unreadable-data page), `products/tracker17/docs/CONTENT.md` (banned words, § Grammar and mechanics "A path the tracker prints", § Error), `system/doctrine/writing_bar.md`, and the strings in `products/tracker17/main.py` (`_unreadable_line`) and `web/pages.py`.

Lens 10 results: every string matches the product's existing words except the path form; no banned word or rejected term in any inflection; the line's sentences are 16, 12 and 14 words and the page's are within the three-sentence and 20-word limits; the two places the design names each have a block and no other block exists; no string names an identifier or file; the title's hyphen is the product's existing form. Lenses 1–6 and 8: coverage, altitude, classification (`feature` / `changing` copied from the spec header) and divergence record (Wording decisions, Findings for the Content Manager) hold.

- **[non-blocking · change-local · words the product can keep]** The intro paragraph says "The same form is written whatever encoding the terminal has", a guarantee the spec does not establish for the whole path. Where: `change_text.md §Text` (opening paragraph, table row 3). `change_spec.md §Out of Scope` leaves a valid character the console cannot write (`é` on an ASCII console) failing as today, while row 3 shows `/tmp/café/data` with no console named. CP-762 establishes the guarantee for the non-text byte only. Direction: scope the sentence to the byte, or name the UTF-8 console on row 3.

Otherwise clean — no further flow-issues found.
