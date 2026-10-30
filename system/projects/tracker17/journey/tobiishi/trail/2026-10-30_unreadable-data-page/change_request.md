# Change request — 2026-10-30_unreadable-data-page

---

**Request:** Right now, if the tracker is started and its saved data cannot be read, it prints one message and exits with status 1. Change that: the tracker should start anyway, say on the console that the data could not be read and where it is, and then answer every address with one plain "unreadable data" page. The page says where the data is, says nothing was changed, has no navigation and no control that acts on the data, and points to the README's section on setting saved data aside (SDD § 7 `supersedes`, SM-6, SD-5; UXD UX-F11, UX-S9). After the operator sets the data aside as the README says, a restart starts empty and the set-aside file still holds the earlier work.

The start-level tests that assert the old exit-1 stop are rewritten, in `tests/integration/test_start.py` and `tests/integration/test_single_tracker.py` (the location-in-use order and the unclaimed-start scenarios). There is one start-level test per kind of break SRS DR-6 names (a value longer than its field's maximum among them), each asserting the saved data's bytes are unchanged (AC-7). The README says what a start does in both cases, and its two wording faults are mended in the passages this change edits anyway: "the same commands" in "Starting the tracker again" with no commands before it in that sentence, and the one conclusion stated twice in "Setting saved data aside".

What must not be weakened: saved data is never written, replaced or deleted by a start on unreadable data or by serving the page (SD-4); the page carries no control that sets data aside or repairs it; the second-tracker refusal and the lock stay as landed; the data model, the other screens and the address-taken behaviour stay unchanged. Not in this change: the README's `readme-status` sentence and `docs/what_left.md`, and the word the README publishes for a missing content rule.

**Sizing:** one capability, one merge. The acceptance boundary is the station's reached-when (the unreadable-data start behaviour, source SDD § 7 / SM-6 / SD-5 / UX-F11 / UX-S9 / SRS DR-6 / AC-7). The page, its tests and the README sentence describing it are one behaviour, so they are not split.

**Category:** feature
**Behaviour:** changing
**Classified because:** the station's reached-when has a start on unreadable saved data stop exiting 1 and serve a new page instead. That is a new observable behaviour and it changes what a start returns, so it is `changing` and a `feature`.

---

**Sealed:** 2026-10-30 — accepted; merged to `main` via `--no-ff`.
Environment: owners-mac — no CI
