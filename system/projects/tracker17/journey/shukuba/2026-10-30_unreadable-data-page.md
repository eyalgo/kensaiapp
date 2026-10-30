# 宿場 Shukuba — a tracker that starts on unreadable saved data and says so on every page

*Item 2 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-11_protect-saved-data`. Slug: `unreadable-data-page`.*

## What it is

Today a start that cannot read its saved data prints one message and exits 1 (`products/tracker17/main.py:L123-L130`). This
station replaces that stop (SDD § 7, `supersedes`; SM-6, SD-5) with a tracker that starts, names the data's location on the
console, and answers every address with the one unreadable-data page (UXD UX-F11, UX-S9): where the data is, that nothing was
changed, no navigation and no control that acts on the data, and a pointer to the README's section on setting saved data
aside. After the operator sets the data aside as the README says, a restart starts empty and the set-aside file still holds
the earlier work. The start-level tests that assert the old exit-1 stop are rewritten, in `tests/integration/test_start.py`
and in `tests/integration/test_single_tracker.py` (the location-in-use order and the unclaimed-start scenarios). One test
per kind of break SRS DR-6 names, a value longer than its field's maximum among them, asserts the saved data's bytes are
unchanged at the start level (AC-7). The README describes what a start does in both cases, and its two wording faults are
mended in passages this station edits anyway: "the same commands" in "Starting the tracker again" with no commands before it
in that sentence, and one conclusion stated twice in "Setting saved data aside". It is one station because the page, its
tests and the README sentence describing it are one behaviour; nothing else on the seed's route waits on it.

## Reached when

All hold, checked from the repository root on `main`:

1. **The page.** A test under `products/tracker17/tests/` starts a tracker on saved data that cannot be read and asserts: the
   start does not exit; a request to the root and to at least two other addresses (one a real route, one unknown) each answer
   with the one page; the page names the data's location, says nothing was changed, points to the README's section on setting
   data aside, and holds no link and no form.
2. **The console.** A test asserts the start's console output says the data could not be read and names its location.
3. **Set-aside restart.** A test moves the unreadable data aside as the README's commands do, starts a tracker, asserts it
   serves with no projects, and asserts the set-aside file's bytes equal what was there before.
4. **One test per break.** For each kind of break SRS DR-6 names
   (read from `products/tracker17/docs/SRS.md`, DR-6, at the open), there is a start-level test that starts a tracker on data
   with that break and asserts the data file's bytes are identical before and after. Each such test fails when run against the
   tree at the commit this station was opened at, because that tree exits 1 and shows no page, and passes after.
5. **No stale stop.** No test under `products/tracker17/tests/` asserts that a start on unreadable saved data exits 1 or
   serves nothing, checked by reading `test_start.py` and `test_single_tracker.py` at the lines that start on such data.
6. **Suites.** `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and
   `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/` both exit 0.
7. **README.** The README passage on starting says that saved data that cannot be read gives a page and a console line, and
   that nothing is changed. The sentence "the same commands" appears with the commands it refers to in the same or the
   directly preceding sentence, checked by reading the passage. The conclusion that stood twice in "Setting saved data aside"
   is stated once, checked by reading the two sentences beginning "If `mv` says" and "If the new directory is empty".

## Guardrail

- Saved data is never written, replaced or deleted by a start on unreadable data, nor by serving the page (SDD SD-4).
- The page carries no control that sets data aside or repairs it; the README's section owns that (seed *Out*).
- The second-tracker refusal and the lock stay as landed; a second start on a location in use keeps its message and exit.
- The data model, the other screens and the address-taken behaviour are unchanged.
- **Not here:** the README's `readme-status` sentence "Nothing that the tracker was defined to do is left to build" and
  `docs/what_left.md` are `readme-status`'s and the product documents' (refine of 2026-10-30), not this station's.
- **Not here:** the word the README publishes for a missing content rule is the Content Manager's
  (`products/tracker17/docs/CONTENT_open_issues.md` § 3.1).
