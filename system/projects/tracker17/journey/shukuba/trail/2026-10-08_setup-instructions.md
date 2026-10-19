# 宿場 Shukuba — setup instructions that take a fresh copy to the Projects page

*Item 2 on the active 根回し Nemawashi `tracker17 · nemawashi · 2026-10-07_first-project`. Slug: `setup-instructions`.*

## What it is

The artifact half of SDD § 6 S-1: `products/tracker17/README.md` becomes the written setup instructions a reader follows alone. It holds the UXD UX-S1 sections in order (prerequisites including the one-time network connection; the commands from a fresh copy to the tracker in the browser; what the start prints and the address to open; where the saved data is kept; "Starting the tracker again"; "Setting saved data aside") and the way to run the suite (SRS FR-4). Its § Status stops saying no code exists and says what runs now. The unreadable-data start message in `main.py` ends by pointing to "Setting saved data aside", which this station first creates (`docs/CONTENT.md:252`). It is one station because the README, its Status and that pointer must agree with each other and with the running start.

## Reached when

Each is checked in a fresh copy of the repository.

1. `products/tracker17/README.md` has a heading for each of the six UX-S1 sections, with "Starting the tracker again" and "Setting saved data aside" spelled exactly (`docs/CONTENT.md:161`), and a section saying how to make the virtual environment, install the test dependencies and run `pytest tests/` and `pytest tests/e2e/`. `grep -n -F -e 'Starting the tracker again' -e 'Setting saved data aside' products/tracker17/README.md` matches a heading line for each.
2. Its prerequisites section states Python 3.11 or later with the command that shows the version and what to do when it is lower; macOS and Linux, checked on macOS only, Windows not supported; and a network connection needed once, only to set up the test suite (SDD § 6 S-1 *Artifact*).
3. `README.md` § Status states what runs now: `grep -n -i -F -e 'no code exists' -e "isn't built yet" -e 'nothing to run' products/tracker17/README.md` matches nothing (it matches today), and the section names the start command `python3 main.py`.
4. With the saved data made unreadable (a `data/` file holding text the tracker cannot parse, in a disposable copy), `python3 main.py` exits non-zero, prints to stderr a message that ends with the sentence `See Setting saved data aside in the setup instructions.`, and writes nothing to `data/`. A test pins the message and the heading together: it fails if either is changed alone.
5. A reader following only the README, from a fresh copy (a disposable `git archive` copy) on a machine with only the stated prerequisites, reaches the Projects page in the browser in no more than three commands, and nothing asks for an account, a key or a sign-up. The check is run: the commands are taken from the README in order, the count is the number of shell commands typed, and the page at the printed address shows the Projects page.
6. The sentence the README says the start prints matches what `python3 main.py` prints (address and saved-data location), checked by running it.
7. `pytest tests/` and `pytest tests/e2e/` exit 0 from `products/tracker17/`.
8. From `## Status` up to `## How it's built`, the README keeps `docs/CONTENT.md` § Grammar and mechanics: no sentence is longer than 20 words (`:120`), and none says "today", "yesterday", "tomorrow", "now", "ago" or "recently" (`:126-127`). `grep -n -w -i -e today -e yesterday -e tomorrow -e now -e ago -e recently products/tracker17/README.md` matches nothing (it matches line 79 today), and section 1's sentence that names https://www.python.org/downloads/ (21 words today, line 23) is split.
9. Its § Running the tests holds what SDD § 6 S-1 *Artifact* and § 4 RT-4 give it (SDD v7, `docs/SDD.md:677-686`): for Linux, `python -m playwright install --with-deps chromium` in place of `python -m playwright install chromium`, that the command runs the package manager and asks for administrator rights, that the tracker and `pytest tests/` need none of it, and the Linux systems the pinned library lists; and that the full suite needs the copy to be a Git repository with `git` on the path, the one test that otherwise fails checking that Git ignores the saved data. `grep -n -F -e '--with-deps' -e 'Debian 12' products/tracker17/README.md` matches a line for each (it matches nothing today).

## Guardrail

- Do not add product behaviour: the start prints and serves what it does now. The one `main.py` change is the unreadable-data message's closing sentence.
- Do not add the unreadable-data page or the second-tracker refusal (slice `protect-saved-data`, not cut); the start still stops with one plain message and writes nothing (SDD § 4 SD-4).
- Do not edit the product's definition documents (`docs/`); a conflict between them and the README is raised, not resolved here.
- The README keeps its "How it's built" and "The documents" content, correct as it stands.
- **Not here:** `tracker17 · nemawashi · 2026-10-07_tasks-in-a-project`; `tracker17 · nemawashi · 2026-10-07_comment-on-a-task`; `tracker17 · nemawashi · 2026-10-07_status-moves`.

*Amended by `shukuba-refine`, 2026-10-08: reached-when 8 added. The README's setup instructions landed with "now" at line 79, which `docs/CONTENT.md:126-127` rules out of every string, and a 21-word sentence at line 23 over the 20-word limit at `:120`. The content audit marked the first blocking, and no station on the route fixes either.*

*Amended by `shukuba-refine`, 2026-10-11: reached-when 9 added. SDD v7 (`4156e81b2`) put RT-4's Linux setup line and the suite's Git prerequisite into S-1's *Artifact*, which this station is the artifact half of; `README.md:87-107` carries neither, and the last unit's plan named it owed outside its reach.*
