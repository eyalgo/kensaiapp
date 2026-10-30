# Change request — 2026-10-30_what-the-start-prints

---

**Request:** Make the README section "What the start prints" (`products/tracker17/README.md`, under `### What the start prints`) name all three lines a start can print. Today it describes the ready line and says a line starting `The tracker didn't start` is the other outcome. Add the third line, the one starting `The tracker couldn't read`, printed when the saved data cannot be read, beside those two, with a sentence that names the line and says the tracker is still running when it shows, and that tells the operator what to do next (follow "Setting saved data aside"). A reader of only this section must be able to say which of the three lines means the tracker is up and which means it stopped. The wording quoted is the program's own: the sentence beginning `The tracker couldn't read` matches the start of the text `_unreadable_line` builds in `main.py`, and the README quotes it rather than rewording it. The check is `awk '/^### What the start prints/{f=1;next} /^### /{f=0} f' products/tracker17/README.md | grep -cF "The tracker couldn't read"` printing 1 or more, where it prints 0 now. Both suites pass.

What must not be weakened: the section still describes the ready line and the `The tracker didn't start` line; the README passage on the unreadable start under the starting instructions (the block quoted near lines 70 to 76) stays true and is not rewritten to fit, only pointed at if useful; `main.py`, the unreadable-data page, the lock and every test stay as they are, apart from any README test that already reads this text.

**Sizing:** the acceptance boundary is the station's reached-when 1 to 4 (seed `2026-10-11_protect-saved-data` item 3 of 3; SDD § 6 S-8, the README describes what a start does in both cases): one reader capability, the section telling an operator what each of the three lines means. It is one passage, one capability and one flow, so the station takes this single change.
**Category:** feature
**Behaviour:** changing
**Classified because:** the station's reached-when 1 and 2 add a statement a reader acts on to the setup instructions (a third line the start can print, and that the tracker keeps running when it shows), which adds to the document's contract rather than rewording text already there.

**Sealed:** 2026-10-30 — accepted; merged to `main` via `--no-ff`.
Environment: owners-mac — no CI
