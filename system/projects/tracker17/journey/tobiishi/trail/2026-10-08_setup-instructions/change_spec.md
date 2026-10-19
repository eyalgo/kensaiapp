# Change Spec — Setup instructions a reader follows alone, and the console pointing to them

**Date:** 2026-10-08
**Category:** feature
**Behaviour:** changing
**Inputs read:** fdr Settled · SRS Settled · SDD Settled · UXD Settled · CONTENT Settled
**Request:** the **Request** of `change_request.md` in this folder, verbatim:

> Write the setup instructions a reader follows alone, and make the tracker's one unreadable-data message point to them. `products/tracker17/README.md` gains the six UX-S1 sections in order (prerequisites, the commands from a fresh copy to the tracker in the browser, what the start prints and the address to open, where the saved data is kept, "Starting the tracker again", "Setting saved data aside") and a section on making the virtual environment, installing the test dependencies and running `pytest tests/` and `pytest tests/e2e/`. The prerequisites say Python 3.11 or later with the command that shows the version and what to do when it is lower; macOS and Linux, checked on macOS only, Windows not supported; and a network connection needed once, only to set up the test suite. "Starting the tracker again" and "Setting saved data aside" are spelled exactly as `docs/CONTENT.md` has them. The README's Status stops saying no code exists and says what runs now, naming `python3 main.py`; the sentence it gives for what the start prints matches what the start prints. In `main.py` the unreadable-data message gains its closing sentence, `See Setting saved data aside in the setup instructions.`, and a test pins that sentence and the README heading together, so it fails if either changes alone. A reader following only the README from a fresh copy reaches the Projects page in no more than three commands, with no account, key or sign-up; that is checked by running the README's commands in order in a disposable copy.
>
> What must not be weakened: the start prints and serves what it does now, and the closing sentence is the only change to `main.py`; the start that cannot read its saved data still stops with one plain message and writes nothing to `data/`; the unreadable-data page and the second-tracker refusal are not added; the product's `docs/` definition documents are not edited (a conflict between them and the README is raised, not resolved); the README keeps its "How it's built" and "The documents" content as it stands.

---

## Change Summary

This change turns `README.md` at the product root into the written setup instructions. A reader who has only a fresh copy and Python follows them to the tracker's Projects page in the browser. The same instructions say where the saved data lives, how to start the tracker again, how to set the saved data aside, and how to run both test suites. The console message for unreadable saved data gains a closing sentence that sends the reader to the instructions' "Setting saved data aside" section, and a test holds that sentence and that heading together.

The product root is the directory `system/projects/tracker17/project.md` names in `Product path:`, and every path below without a further prefix is relative to it. `R-n`, `PD-n` and `OOS-n` are `docs/fdr.md`'s. The SRS, SDD, UXD and CONTENT sections cited are `docs/SRS.md`, `docs/SDD.md`, `docs/UXD.md` and `docs/CONTENT.md`. `CP-1` to `CP-29` are the rules of the sealed spec `system/projects/tracker17/journey/tobiishi/trail/2026-10-07_create-a-project-that-stays/change_spec.md`, and `CP-39` to `CP-46` are those of `system/projects/tracker17/journey/tobiishi/trail/2026-10-07_address-taken-start-message/change_spec.md`. This change realizes R-8 to R-14 and R-28, which the FDR already states. It adds no rule the FDR does not hold.

**Sizing.** The acceptance boundary is one reader capability: following the written setup alone, from a fresh copy to the Projects page, with the console's one pointer into those instructions resolving to a real heading (station `tracker17 · shukuba · 2026-10-08_setup-instructions`, reached-when 1 to 7; SDD § 6 S-1, *Artifact*). The README's sections, its Status and the console pointer with its test are that capability's acceptance obligations. Each of them is checked against the others, so under `<CORE>/prompts/pm_right_size.md` § *Right-size to one honest merge* they stay one change and one development flow.

**Who writes the words.** The words of the README are the change's published text. CONTENT § Message patterns lists UX-S1 with the note "The written commands are per-change copy. The two section headings others point to are fixed in § Terminology." The rules below therefore fix what each section must let a reader do, and the strings that upstream documents fix. Every other word is the content step's to write.

---

## Rules

### The setup instructions — their shape

- **CP-54:** `README.md` holds the setup instructions. It names them as the setup instructions, so that a reader sent to "the setup instructions" by a console message finds them under that name (CONTENT § Terminology, "setup instructions"). They are six sections, each under its own Markdown heading, in this order (UXD UX-S1):
  1. the prerequisites;
  2. the commands that take a fresh copy to the tracker open in the browser;
  3. what the start prints, and the address to open;
  4. where the saved data is kept;
  5. starting the tracker again;
  6. setting the saved data aside to start fresh.

  A seventh section, on running the automated test suite, comes after the sixth (R-8; SRS FR-4). *(R-8; UXD UX-S1, RN-1)*
- **CP-55:** The heading of section 5 is exactly `Starting the tracker again`, and the heading of section 6 is exactly `Setting saved data aside`, with this capitalisation and no other words on the heading line (CONTENT § Terminology, the row "Two sections of the setup instructions that other strings point to"). `grep -n -F -e 'Starting the tracker again' -e 'Setting saved data aside' README.md` matches a heading line for each. Today it matches nothing. The headings of sections 1 to 4 and 7 are not fixed here.

### The setup instructions — what each section lets the reader do

- **CP-56:** The prerequisites section states:
  - that the tracker needs Python 3.11 or later, the command that shows the installed Python version, and what to do when that version is lower (R-9; SDD § 4 RT-1);
  - that macOS and Linux are supported, that the tracker has been checked on macOS only, and that Windows is not supported (R-10; SDD § 4 RT-3);
  - that a network connection is needed once, only to set up the test suite, to fetch the test dependencies and the browser the end-to-end tests drive (R-11; SRS FR-4).

  Nothing in the prerequisites, or anywhere in the setup instructions, asks for an account, a key, a sign-up or a payment (R-14).
- **CP-57:** Section 2's commands, typed in order on a machine that has only the stated prerequisites, take the reader from a fresh copy to the Projects page open in the browser, in its first-run state with the create form in view (UXD UX-F1, UX-S3). The count is at most three commands and the time is within ten minutes (R-13). The count follows these terms:
  - it starts at a terminal whose working directory is the top of the fresh copy, so making the copy is not counted;
  - every command the README asks the reader to type on the way to the Projects page counts, the prerequisites' version check included;
  - commands joined with `&&` or `;` count as separate commands (R-13).

  None of the commands installs anything, needs a network connection, or asks the reader to type an answer. The last of them is the start command, `python3 main.py`, typed from the product root (R-1; CP-1). This rule is checked by running: in a disposable copy made with `git archive`, the commands are typed from the README in order and counted, and the page at the printed address is opened.
- **CP-58:** Section 3 shows the line the start prints when it is ready, word for word as the start prints it:

  `The tracker is running. Open http://127.0.0.1:8017 in your browser. Saved data is kept at <location>.`

  The address appears exactly as printed. The saved data's location is the one part that differs between machines. The README shows it as an example path and says the reader's own location appears in its place. The section tells the reader to open the printed address in the browser. It also says the tracker keeps running in that terminal until it is stopped, and that Ctrl-C typed there stops it (CP-3). This rule is checked by running `python3 main.py` and comparing its line with the README's. *(R-2; CP-1; UXD UX-S2)*
- **CP-59:** Section 4 says that the saved data is kept in `data/`, in the product root, which is the directory that holds `main.py`, whatever directory the start command is typed from (R-16; CP-4). It says that the start prints the location in full (CP-58). It says that version control ignores `data/`, so the saved data is never committed. It also says that, for the same reason, a clean of the copy that removes ignored files deletes the saved data (R-12; SRS FR-4).
- **CP-60:** Section 5, `Starting the tracker again`, takes a reader whose tracker has stopped back to the running tracker with the same saved data. Every project created before the stop is still listed (R-15). The section holds every command this needs from a new terminal at the top of the copy, the change to the product root included. It says that when the browser cannot reach the tracker's address, the tracker is not running and this section starts it again (UXD UX-F1, Failure/recovery, "Later, the tracker is not running").
- **CP-61:** Section 6, `Setting saved data aside`, takes a reader from a tracker with saved data, readable or not, to a tracker that starts empty on purpose (R-28; UXD UX-F11). The section:
  - says to stop the tracker first;
  - moves the saved data aside and deletes nothing, so that afterwards the set-aside data holds every byte the saved data held;
  - says where the set-aside data now is;
  - leaves the set-aside data where `git status`, run in a copy that is a git repository, does not list it as a change to commit, as R-16 keeps the saved data itself.

  After the section is followed, the next `python3 main.py` shows the ready line, and the Projects page is in its first-run state (R-17, R-28). This rule is checked by running: a project is created, the tracker is stopped, the section is followed, and the tracker is started again.
- **CP-62:** Section 7 holds the commands that, typed from the product root of a fresh copy with a network connection, make a virtual environment, install the test dependencies and the browser the end-to-end tests drive, and then run `pytest tests/` and `pytest tests/e2e/` inside that environment (R-8, R-11; SDD § 6, "Both suites pass"). On macOS, the system the tracker is checked on (R-10), following the section ends with both commands exiting 0. The section says the network connection is needed for the installing commands only.

### The README's other sections

- **CP-63:** The README's `Status` section states what runs today and names the start command `python3 main.py`. Every statement it makes is true of the product as this change leaves it. It names no feature as available that the running tracker does not offer, such as tasks, labels, comments, People or All tasks. `grep -n -i -F -e 'no code exists' -e "isn't built yet" -e 'nothing to run' README.md` matches nothing. Today it matches lines 9 and 10, under the `Status` heading.
- **CP-64:** The text of the README's `How it's built` and `The documents` sections, headings included, is unchanged by this change.

### The console's pointer to the instructions

- **CP-65:** A start whose saved data cannot be read shows exactly one line on standard error, and the line ends with the sentence `See Setting saved data aside in the setup instructions.` The whole line is:

  `The tracker didn't start, because it couldn't read its saved data at <location>. Nothing in it was changed. See Setting saved data aside in the setup instructions.`

  `<location>` is the saved data's absolute location, as today. This is CONTENT's third example under § Message patterns, Error, "Terminal messages", with the tracker's own location in place of the example's. Everything else CP-7 sealed is unchanged: nothing on standard output, no ready line, a non-zero exit status, and every byte of the saved data and its directory's listing unchanged. *(R-24, R-27; SDD § 4 SD-4; CONTENT § Message patterns, Error)*
- **CP-66:** The start's other output and behaviour are unchanged. The ready line (CP-1, CP-58), the address-taken message (CP-40) and the precedence of the unreadable-data message over the address-taken message (CP-43) stay as they were sealed. The unreadable-data message is the only change to `main.py`.
- **CP-67:** A test in the suite that `pytest tests/` runs ties the unreadable-data message to the README heading it quotes. It checks that the message ends with `See Setting saved data aside in the setup instructions.`, and that `README.md` has a heading line whose text is exactly the section name that sentence quotes. The test fails in each of these trees:
  - the README's `Setting saved data aside` heading is reworded, and the message is not;
  - the message's closing sentence is reworded or removed, and the README is not.

  It passes on the tree this change delivers. It runs without the browser, because `pytest tests/` does not collect `tests/e2e/` (`tests/conftest.py`, "The collection rule keeps ``pytest tests/`` from collecting ``tests/e2e/``").

### Its tests

- **CP-68:** `pytest tests/` and `pytest tests/e2e/`, each typed from the product root inside the virtual environment CP-62's section makes, each exit 0 on macOS (SDD § 6, "Both suites pass"). The tests that exist before this change pass unchanged, the unreadable-start tests in `tests/integration/test_start.py` included. They include the CP-67 test.

---

## Examples

| Rule | Scenario | Expected behaviour |
|---|---|---|
| CP-54 | Reading `README.md` from the top | The six setup sections appear in UX-S1's order, then the suite section. The README names them as the setup instructions. |
| CP-55 | `grep -n -F -e 'Starting the tracker again' -e 'Setting saved data aside' README.md` | Two matches, each a Markdown heading line holding exactly that text. |
| CP-56 | Reading the prerequisites section | Python 3.11 or later, the version command, and what to do when it is lower. macOS and Linux, checked on macOS only. Windows not supported. A network connection once, only for the test suite. No account, key, sign-up or payment. |
| CP-57 | A disposable `git archive` copy, a terminal at its top, only Python 3.11 or later on the machine. The README's commands are typed in order | At most three commands, the version check included. The last prints the ready line. The printed address shows the Projects page, saying there are no projects yet, with the create form in view. |
| CP-57 | A README whose commands join a directory change and the start with `&&` | Counted as two commands. |
| CP-58 | `python3 main.py` in a copy whose product root is `/Users/sam/tracker17` | It prints `The tracker is running. Open http://127.0.0.1:8017 in your browser. Saved data is kept at /Users/sam/tracker17/data.` The README's line differs from it only in the location. |
| CP-59 | Reading section 4 | `data/` in the product root, the same whatever directory the start is typed from. It is ignored by version control, and a clean that removes ignored files deletes it. |
| CP-60 | Project `Alpha` created, the tracker stopped with Ctrl-C, a new terminal opened at the top of the copy, section 5 followed | The tracker starts, and the Projects page lists `Alpha`. |
| CP-60 | The browser shows its "can't reach this page" for `http://127.0.0.1:8017` | Section 5 says this means the tracker is not running, and its commands start it again. |
| CP-61 | Project `Alpha` saved, the tracker stopped, section 6 followed, then `python3 main.py` | The Projects page is in its first-run state. The set-aside data holds the same bytes as before, at the place section 6 named. |
| CP-61 | `data/tracker.json` cannot be read, the start printed the CP-65 line, section 6 followed, then `python3 main.py` | The ready line, and an empty Projects page. The unreadable file is kept, byte for byte, where section 6 says. |
| CP-61 | Section 6 followed in a copy that is a git repository, then `git status --short` | Nothing is listed for the set-aside data. |
| CP-62 | A fresh clone on macOS, with a network connection. Section 7's commands typed from the product root | Both `pytest tests/` and `pytest tests/e2e/` exit 0. |
| CP-63 | `grep -n -i -F -e 'no code exists' -e "isn't built yet" -e 'nothing to run' README.md` | No match. The Status section names `python3 main.py`. |
| CP-63 | Reading the Status section | It says a reader can start the tracker and create a project that stays. It does not say tasks exist. |
| CP-64 | `git diff` of `README.md` against the change's base | No line inside `How it's built` or `The documents` is changed. |
| CP-65 | `data/tracker.json` holds `{"next_project_id": 3, "projects": [ truncated`, then `python3 main.py` | Exit status non-zero. Standard output empty. Standard error is one line ending `Nothing in it was changed. See Setting saved data aside in the setup instructions.` The file's bytes are unchanged. |
| CP-66 | Nothing holds the address, and no saved data exists. `python3 main.py` | The ready line, as before the change. |
| CP-66 | The address is held and the saved data is unreadable | The CP-65 line alone, with no address-taken message. |
| CP-67 | The README heading is changed to `Setting the saved data aside`, and `main.py` is left alone | The test fails. |
| CP-67 | The message's closing sentence is changed to `See Setting data aside in the setup instructions.`, and the README is left alone | The test fails. |
| CP-68 | `pytest tests/`, then `pytest tests/e2e/`, from the product root on macOS | Both exit 0. The CP-67 test is among those `pytest tests/` runs. |

---

## Verified Claims

Unless a row says otherwise, the commands ran on 2026-10-08 against commit `e7cfd84d1`, the base of this change's branch, in a disposable copy made with `git archive e7cfd84d1` into a scratch directory (`<CORE>/roles/CROSS_ROLE.md` § *Every seat*). The machine was Linux aarch64 (`uname -sm`), under Python 3.12.12, with nothing installed beyond the standard library unless a row says so. That is not macOS, the system the tracker is checked on (R-10).

| Claim | Verified by | What came back |
|---|---|---|
| The ready line's words and the address (CP-58) | `python3 main.py` from the copy's product root, no `data/` present | Standard output: `The tracker is running. Open http://127.0.0.1:8017 in your browser. Saved data is kept at /tmp/specs-verify.XLep/products/tracker17/data.` |
| Two commands reach the Projects page from the top of a fresh copy, with nothing installed (CP-57) | From the copy's top, `cd products/tracker17`, then `python3 main.py`, then `curl -s http://127.0.0.1:8017/` | `<title>Projects - tracker17</title>`, `<h1>Projects</h1>`, "There are no projects yet. Type a name for your first project and press Create.", and the create form. With the version check, that is three commands. Whether the start needs no network was not run here: the sandbox could isolate the network but could not bring its loopback interface up, because it has no `ip` tool. R-7 and PD-6 state it, and this change does not touch it. |
| Today's unreadable-data message (CP-65) | `data/tracker.json` holding `{"next_project_id": 3, "projects": [ truncated`, then `python3 main.py` | Exit `1`. Standard output empty. Standard error one line: `The tracker didn't start, because it couldn't read its saved data at /tmp/specs-verify.XLep/products/tracker17/data. Nothing in it was changed.` `shasum` unchanged. |
| After the change, the message is one line ending with the new sentence, and nothing else about that start changes (CP-65) | The constructed post-change tree: the copy's `main.py` with ` See Setting saved data aside in the setup instructions.` appended to the message's second sentence and nothing else changed, then the same start | Exit `1`. Standard output empty. Standard error one line: `… Nothing in it was changed. See Setting saved data aside in the setup instructions.` `shasum` unchanged, and `data/` lists only `tracker.json`. |
| The existing start tests pass on the post-change tree (CP-66, CP-68) | The tree from the row above, with a virtual environment holding `tests/requirements.txt` installed by `uv pip`. `python -m pytest -q tests/integration/test_start.py tests/e2e/test_start_command.py` | `13 passed`. |
| `pytest tests/` passes on the post-change tree, without the browser (CP-67, CP-68) | The same tree and environment. The copy had been made a git repository by `git init` and `git add -A`, with no commit, so `git check-ignore` could answer. `python -m pytest -q tests/` | `220 passed`. The count equals `pytest tests/ --ignore=tests/e2e`, so `pytest tests/` does not collect the end-to-end suite. |
| `pytest tests/e2e/` cannot run its browser tests on this machine (CP-62, CP-68) | `python -m playwright install chromium` in the environment, then `python -m pytest -q tests/e2e/` | The browser downloaded. Every browser test then errored: `chrome-headless-shell: error while loading shared libraries: libglib-2.0.so.0: cannot open shared object file`. No verdict on the end-to-end suite was reached here. This is the shape SDD § 11 R-9 names, "a setup or a suite failure on a Linux machine", and Out of Scope records it. |
| A copy that is not a git repository fails one test in `pytest tests/` (Locked Answers, Gap 11) | A second `git archive e7cfd84d1 products/tracker17` copy with no `.git`, then `python -m pytest -q tests/integration/test_start.py` | `1 failed, 11 passed`. The failure is `test_data_is_ignored_by_version_control`. |
| Version control ignores `data/`, and which cleans delete it (CP-59) | In the `git init` copy, `data/tracker.json` created, then `git check-ignore -v data/tracker.json`, `git clean -n -dX .`, `git clean -n -dx .` and `git clean -n -d .` from the product root | `products/tracker17/.gitignore:26:data/`. `-dX` and `-dx` each print `Would remove data/`. `-d` lists nothing under `data/`. |
| A project stays after a stop and a start (CP-60) | A start, a project `Beta` created by a same-origin form post, the start stopped, a second start, the Projects page fetched | The page holds `>Beta<`. |
| Moving `data/` out of the copy gives an empty next start and keeps the bytes (CP-61) | A project `Alpha` created and the tracker stopped, `shasum data/tracker.json`, `mv data "$HOME/tracker17-set-aside-check"`, a new start, the Projects page fetched, `shasum` of the moved file | "There are no projects yet". The moved file's `shasum` is unchanged. |
| Moving `data/` to a plain sibling inside a git copy shows it as a change to commit (CP-61) | In the `git init` copy, `mv data data-set-aside`, then `git status --short --untracked-files=all .` | `?? data-set-aside/tracker.json`. |
| The two headings' fixed spelling, and the message's words (CP-55, CP-65) | Reading `docs/CONTENT.md` § Terminology and § Message patterns, Error | The Terminology row "Two sections of the setup instructions that other strings point to" holds "Starting the tracker again" and "Setting saved data aside", with the rule "A string that points to one quotes its heading exactly." The third "Terminal messages" example reads "The tracker didn't start, because it couldn't read its saved data at /Users/sam/tracker17/data. Nothing in it was changed. See Setting saved data aside in the setup instructions." |
| The six sections and their order (CP-54) | Reading `docs/UXD.md` § 6, row UX-S1 | "Its sections, in order: prerequisites (including the one-time network connection setup needs) · the commands that take a fresh copy to the tracker in the browser · what the start prints, and the address to open · where the saved data is kept · starting the tracker again · setting the saved data aside to start fresh." |
| Today the README has neither heading, and its Status says no code exists (CP-55, CP-63) | `grep -n -F -e 'Starting the tracker again' -e 'Setting saved data aside' README.md`. Then `grep -n -i -F -e 'no code exists' -e "isn't built yet" -e 'nothing to run' README.md`, both in the main checkout at `e7cfd84d1` | The first exits 1 with no match. The second matches line 9, "tracker17 is defined and isn't built yet", and line 10, "and no code exists, so there's nothing to run". |
| `pytest tests/` does not collect `tests/e2e/` (CP-67) | Reading `tests/conftest.py`'s module docstring | "The collection rule keeps ``pytest tests/`` from collecting ``tests/e2e/``." |
| The highest `CP-<n>` in the project's record is CP-53, so this series starts at CP-54 | `grep -rhoE 'CP-[0-9]+' system/projects/tracker17/journey/tobiishi/trail products/tracker17`, numbers sorted | Highest is `53`. |

---

## Out of Scope

- The page for saved data that cannot be read (UXD UX-S9; R-25, R-26) and the refusal of a second tracker on the same saved data (R-5). Both belong to slice `protect-saved-data` (SDD § 6). The start that cannot read its saved data keeps stopping with one plain message (CP-65).
- Bringing set-aside data back. Section 6 says where the data went (CP-61). How to restore it is not among UX-S1's sections or R-8's statements.
- Any edit to the product's definition documents under `docs/`. Two facts this spec's verification turned up are raised here and not resolved. The PM reads them when the unit lands.
  - On this Linux machine the end-to-end browser could not start, for want of the system library `libglib-2.0.so.0` (Verified Claims). SDD § 11 R-9 names this risk and answers it with the "checked on macOS only" line, which CP-56 carries. Whether the prerequisites should say more for Linux is the definition documents' call.
  - `pytest tests/` fails one test in a copy that is not a git repository (Verified Claims). Gap 11 says why this change does not act on it.
- Listing the start's failure messages in the README. UX-S1 names the README as where console failures point, and it does not ask the README to repeat them.
- Any change to the wording of the ready line or the address-taken message (CP-66).
- The words of the README beyond the strings this spec fixes. They are the content step's (CONTENT § Message patterns, the UX-S1 row).
- Running the setup or the suites on Linux as an acceptance check, and anything for Windows (R-10; PD-8; OOS-13).
- Publishing tracker17, or a trial of the instructions by an outside reader (OOS-1).
- Tasks, the add-task form, People, All tasks, renaming and deleting a project. They belong to later slices, and CP-63 keeps the Status from claiming them.

---

## Locked Answers (the divergence record — self-review 2026-10-08)

- **Gap 1 — where the suite section sits:** after the six setup sections (CP-54). The request lists it apart from the six and does not place it. UXD UX-S1's success state is "The reader can follow it top to bottom with no section skipped and no choice to make". A suite section placed among the six would sit on the reader's path to the Projects page, where it does not belong. The choice is reversible.
- **Gap 2 — the README names itself as the setup instructions (CP-54):** the request does not say. The console line ends "in the setup instructions", and CONTENT § Terminology makes "setup instructions" the term for the document while listing "README" among the words not to use for it. On this reading a reader holding the console line has to find that term in the README. The wording is the content step's.
- **Gap 3 — how the three commands are counted (CP-57):** from a terminal at the top of the fresh copy, with the version check counted and the making of the copy not counted. R-13 counts "From a fresh copy", so the copy exists before the count starts. Counting the version check is the strict reading of "a reader following only the README", and the tree meets it (Verified Claims, three commands). The choice is reversible: a looser count only admits more READMEs.
- **Gap 4 — ten minutes (CP-57):** included, though the request names only the three commands. R-13 binds both, and a spec that dropped one would let a README meet the request while breaking the FDR.
- **Gap 5 — the location in the README's ready line (CP-58):** shown as an example path, with every other word as printed. The request says the sentence "matches what the start prints", and the location is the one part that cannot match on every machine, because the start prints the reader's own absolute path.
- **Gap 6 — stopping with Ctrl-C (CP-58):** stated, though the request does not ask for it. Section 5 is about a tracker that "has stopped" (R-8), and a reader who never learns how to stop the tracker meets section 5 only after a crash. CP-3 already makes Ctrl-C the stop, so saying so adds no behaviour.
- **Gap 7 — the clean warning (CP-59):** included, though the request's list of sections does not mention it. R-12 and SRS FR-4 put it in the instructions, beside where the saved data is kept. Leaving it out would leave R-12 unmet by the one document that realizes it.
- **Gap 8 — the "can't reach" pointer (CP-60):** included. UXD UX-F1's failure path ends with the browser's own "can't reach this page" and "a section on starting the tracker again, findable by its heading". Saying in that section what the browser's page means is how a reader arriving from it knows they are in the right place.
- **Gap 9 — how the saved data is set aside (CP-61):** the tracker stopped first, nothing deleted, the new place named, and kept out of what `git status` offers to commit. The request names only the section. R-28 requires that "the set-aside data still holds the earlier work". A tracker still running would write a new saved file on its next action, so the next start would not be empty (R-20). The set-aside data holds what the operator entered, and R-16 keeps that data out of version control. A plain move inside the copy would leave it listed as a change to commit (Verified Claims). Where the data goes is the content step's choice within those terms.
- **Gap 10 — the CP-67 test runs under `pytest tests/` (CP-67):** the request says only "a test". The pointer joins a console line to a document, and neither needs a browser. Placing the test in the suite that runs without one means it runs on any machine the suite runs on, this Linux machine included (Verified Claims).
- **Gap 11 — a copy that is not a git repository:** CP-62 and CP-68 hold for a fresh clone, and CP-57's walk holds for any fresh copy, a `git archive` one included. One existing test checks that version control ignores the saved data, and it fails where there is no version control (Verified Claims). The request does not reach that test. Changing it, or naming git among the prerequisites, would add to what SDD § 6 S-1 *Artifact* says the prerequisites section holds. The fact is raised under Out of Scope and not resolved here.
- **Gap 12 — what the Status may say (CP-63):** every statement true of the product as this change leaves it, and no unbuilt feature named as available. The request says the Status "says what runs now". Today's Status also says the setup instructions "arrive in this file with the first slice of work", which this change makes false even though it contains none of the three grepped phrases.
- **Gap 13 — "keeps its content as it stands" (CP-64):** read as the two sections' text unchanged, headings included. The request calls that content correct as it stands, and an edit for style would be an edit the request did not ask for.
