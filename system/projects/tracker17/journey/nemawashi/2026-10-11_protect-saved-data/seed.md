# 根回し Nemawashi seed — saved data that cannot be read, and a second tracker

## What it is

Serves the Way `fit-to-publish`, which `system/michi.md` Way 5 ranks above it; cut now because tracker17 is the product the owner runs the crew on (`products/tracker17/docs/PRD.md:L12-L14`), so it moves a product rather than machinery (my reasoning, not a lookup). After this, an operator whose saved data cannot be read is told so on every page, with where it is and that nothing was changed, and a second tracker started on the same saved data refuses to start. Moves the Agari toward **Works** for the PRD's failure states.

A start that cannot read its data now serves the one unreadable-data page and names the location on the console (`products/tracker17/main.py:L126-L128`), and a second start on a location in use is refused (`products/tracker17/main.py:L115-L117`); both have landed. What is left is the setup instructions' account of the third line a start can print.

Rests on SDD § 3 SM-5 and SM-6 and § 4 SD-4 and SD-5. Its bar is SDD § 6 S-8 *Reached when*: the console names the data's location; every address shows the one unreadable-data page with no navigation and no control acting on the data, pointing to the README's section on setting saved data aside; after the operator sets it aside the tracker starts empty and the set-aside file still holds the earlier work; a second start on a location a running tracker uses shows one plain message while the first carries on; a start after a killed tracker succeeds; both suites pass, including one test per break SRS DR-6 names (a saved value longer than its field's maximum among them) asserting the bytes are unchanged (AC-7), and both halves of AC-16; the README describes what a start does in both cases.

**Why it is here.** It rests only on a finished seed, so it can be picked at any point. The SDD puts it last so AC-7's one-test-per-break is written once against the complete data model (SDD § 6 S-8, *Why here in the order*); that is a preference, and later it is picked the more complete the model its tests see.

## Source

Cut from `products/tracker17/docs/SDD.md` § 6 S-8, slug `protect-saved-data` ("After this, an operator whose saved data cannot be read is told so on every page"), and `products/tracker17/docs/adr/0009-one-unix-lock-no-windows.md` for the lock. Product checked on 2026-10-11: `grep -rln 'fcntl\|flock' products/tracker17 | grep -v pycache` lists only `docs/trail/sdd/self_answer-2.md`, so no lock exists in code; `grep -rn "UnreadableData" products/tracker17/web products/tracker17/application` matches nothing, so no page shows it. The work is still owed.

## Stations — dynamic checklist

- [x] second-tracker-refusal — a second start on a location a running tracker uses prints one plain message while the first carries on, a start after a kill succeeds (both halves of AC-16 as tests), and the README says so
- [x] unreadable-data-page — the tracker starts on unreadable data, every address shows the one page with no navigation or control, the console names the location, a restart after set-aside starts empty with the earlier work kept, one test per DR-6 break at that level asserts unchanged bytes (AC-7), both suites pass, and the README says what a start does, its two wording faults mended (`products/tracker17/README.md:L79`, "the same commands" with no commands before it; `:L95`, one conclusion stated twice)
- [ ] what-the-start-prints — the setup instructions' section "What the start prints" names the line that begins "The tracker couldn't read" beside the two it already describes, and says the tracker is still running when it shows it; both suites pass

Divergence from the proposal, six lines:
- `break-tests` dropped as a station: the DR-6 breaks (unknown status and priority, missing project, shared name, reused identity, over-long values) already each have a bytes-unchanged test at load and at start (`tests/integration/test_saved_data.py`, `tests/integration/test_start.py`), so its bar passes today; the start-level ones assert the exit-1 stop this seed supersedes, so they are rewritten inside `unreadable-data-page`.
- The README's two descriptions and AC-16's halves moved into the station that builds each behaviour, so no station's bar waits on a later one.
- The two stations swapped: the lock is the unproven part (no lock in the code, a kill-recovery nobody has shown), so it goes first; the order is a preference, neither station needs the other, and the last carries the seed's whole bar.
- `unreadable-data-page` gains the README's two wording faults: the audit of the refusal's text named them, the unit sealed with them, and this station edits those same passages (refine of 2026-10-30).
- The start-level tests of the exit-1 stop now also stand in `tests/integration/test_single_tracker.py:L45`, `:L350` and `:L485` (the location-in-use order and the unclaimed-start scenarios), so `unreadable-data-page` rewrites those too (refine of 2026-10-30).
- `what-the-start-prints` added: the section still names only the ready line and `The tracker didn't start` (`products/tracker17/README.md:L50`), `unreadable-data-page` was fenced to two other passages, and nothing else carries it (refine of 2026-10-30).

## Relation to existing work

Rests on `tracker17 · nemawashi · 2026-10-07_first-project`, retired to `trail/` (SDD § 7, `depends_on`); it replaces that seed's stop on unreadable data (`supersedes`). Rests on no seed in the pool.

## Out (later / elsewhere)

Any control inside the tracker that sets data aside or repairs it: the setup instructions own that, delivered by `tracker17 · nemawashi · 2026-10-07_first-project`.
