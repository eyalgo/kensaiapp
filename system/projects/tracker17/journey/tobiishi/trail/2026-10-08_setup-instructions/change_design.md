# Change Design — Setup instructions a reader follows alone, and the console pointing to them

**Date:** 2026-10-08
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the setup instructions and the status note above them, and the console message a start shows when it cannot read its saved data

---

## 1. Change Summary

This is the structural plan for `change_spec.md` in this folder (CP-54 to CP-68).

The change touches one code module and one document. `main.py` adds one closing sentence to the message it writes when the saved data cannot be read. Nothing else in it changes. `README.md` becomes the setup instructions. It gains seven sections, the six UX-S1 sections and then the suite section, and its `Status` is rewritten. Its `How it's built` and `The documents` sections stay as they are. A test in `pytest tests/` ties the console sentence to the README heading it quotes.

No part, seam, import or dependency is added. Paths below are relative to the product root, `products/tracker17/`, which is what `system/projects/tracker17/project.md` names in `Product path:`.

---

## 2. Blast Radius

New logic, placed by `docs/SDD.md` § 3's parts table:

- **The closing sentence of the unreadable-data message** is owned by `main`. Its `Owns` cell holds "writes the start messages to the console" (`docs/SDD.md:195`), and the message is already written there (`main.py:42-46`).
- **The setup instructions** are a document, not logic. No part owns them. `docs/SDD.md` RN-10 names `README.md` as their home, and § 6 S-1 *Artifact* says what they hold.
- **The test tying the sentence to the heading** lives in `tests/`. That is the frame's tests unit, not a part.

| Module | Status | What changes |
|---|---|---|
| `main.py` | Modified | `main` part. In `start`, the line written to standard error when `SavedData.load` raises `UnreadableData` gains its closing sentence, `See Setting saved data aside in the setup instructions.`, after `Nothing in it was changed.`. It stays one line, with the location as today. Nothing else in `main.py` changes (CP-66). The module and `start` docstrings stay true and are not edited. |
| `domain/` | Unchanged | — |
| `application/` | Unchanged | — |
| `persistence/` | Unchanged | — |
| `web/` | Unchanged | — |
| `errors.py` | Unchanged | — |

**Outside the module set, also changed:**

| File | What changes |
|---|---|
| `README.md` | Becomes the setup instructions (CP-54 to CP-63). The words are the content step's, from `change_text.md`, placed verbatim. The structural properties the placement must keep are in § 4. The text of `How it's built` and `The documents`, headings included, is byte-for-byte unchanged (CP-64). Their position in the file is the content step's to decide. |
| `tests/integration/test_start.py` | Gains the tests in § 5, and its module docstring names what they check. |

**Transitive blast radius.** None. `main.py`'s public surface is unchanged: `start` and `main` keep their signatures and return values. No module imports `main` (QC-2). `README.md` is imported by no code and is read only by the new test.

---

## 3. Sub-jobs

Omitted. One module is affected, and the change is a single delta.

The change has three seams: the sentence in `main.py`, the README, and the test. None of them builds on another's output. The one constraint between them is a property of the tree, not an order: **the CP-67 test passes only on a tree that holds both the message's closing sentence and the README heading it quotes.** There is no green point that has that test and only one of the two.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `main.py` — the closing sentence | None. |
| `README.md` — the setup instructions | **The virtual environment section 7 makes must sit where the suite does not look for product code.** That means a dot-named directory at the product root, such as `.venv` (the name the comment at `tests/requirements.txt:3` and `.gitignore:17` already use), or a directory outside the product root. `tests/conftest.py`'s source walk skips only `tests/`, dot-named folders and `__pycache__` (`tests/conftest.py:104-113`). A `venv/` or `env/` at the product root is ignored by git (`.gitignore:18-19`) but walked by the suite. `test_the_top_level_parts_are_the_five_the_sdd_names` (QC-1) then fails on a sixth part, and the layer-6 import walks read site-packages. **Setting data aside must also delete nothing when it is done a second time.** A second set-aside into the same named place must not overwrite or merge into the first, and the section must still say where the data went. Check both by running the section twice. |
| `tests/integration/test_start.py` — the CP-67 tie | Hold the section name once, as one constant, and build the expected closing sentence from it. The message check and the heading check then both read that one constant. That makes "the section name that sentence quotes" true by construction rather than by two literals that happen to agree. Take the message from a real `main.start` call on unreadable data, captured with `capsys`, and not from `main.py`'s source text. Read `README.md` from the product root, which is `PRODUCT_ROOT`, already in the module, and not from the working directory. A heading line is an ATX line. Strip the leading run of `#` and the space after it, then compare the rest for **equality**. Containment would let `Setting saved data aside again` pass. Accept any heading level, because whether the seven sections sit under a parent heading is the content step's choice. |

---

## 5. Test Additions

Every test below runs under `pytest tests/` without the browser. It goes in `tests/integration/test_start.py`, whose docstring gains CP-55, CP-65 and CP-67, SRS FR-4 (beside FR-8's AC-7, which it already names) and the path `README.md`. The pointer test (`tests/architecture/test_trace.py`) checks that each named path exists and each requirement is in `docs/SRS.md`. `README.md` and `FR-4` both pass that check.

| Sub-job | Test file | What to add / modify |
|---|---|---|
| `main.py` | `tests/integration/test_start.py` | New test (CP-65): `UNREADABLE` written to `tmp_path / "tracker.json"`, then `main.start(("127.0.0.1", 0), tmp_path)`. The status is non-zero and standard output is empty. Standard error is **exactly** the `change_text.md` line, with `tmp_path`'s absolute form as the location, followed by one newline. Today's tests assert only that there is one line and that it names the location (`:33-44`). This row pins the whole line, so a second sentence on its own line, or a lost first half, fails. |
| `main.py` + `README.md` | `tests/integration/test_start.py` | New test (CP-67): the tie, per the § 4 hint. It asserts that the captured line ends with the closing sentence built from the section-name constant, and that `README.md` has a heading line whose text equals that constant. |
| `README.md` | `tests/integration/test_start.py` | New test (CP-55): `README.md` has a heading line equal to `Starting the tracker again` and one equal to `Setting saved data aside`, read the same way as the CP-67 test. |

**Spec Examples and rule-implied edges, row by row:**

- **CP-55**, grep matches two heading lines: the CP-55 row above.
- **CP-65**, the truncated file: the CP-65 row above. That the bytes are unchanged is already covered by `test_an_unreadable_start_changes_nothing_in_the_location` (`:47-54`), unchanged.
- **CP-65 on the other unreadable shapes** (empty, not UTF-8, missing key, wrong shape): covered by `test_other_unreadable_files_are_refused_the_same_way` (`:57-68`), unchanged. The sentence is added on the one path every shape takes, so no per-shape row is needed.
- **CP-66**, the ready line as before: covered by `tests/e2e/test_first_project.py:42-47`, unchanged.
- **CP-66**, the held address together with unreadable data: covered by `test_unreadable_saved_data_wins_over_a_held_address` (`:157-173`), unchanged. It asserts one line, the location, and no address message.
- **CP-67**, the README heading reworded and `main.py` left alone: the CP-67 row. Its heading equality fails.
- **CP-67**, the closing sentence reworded and the README left alone: the CP-67 row. Its ends-with check fails. Before handing over, the developer makes each of the two edits once, in a scratch copy, and records that the test fails on each.
- **CP-68**, both suites exit 0, with the CP-67 test among those `pytest tests/` runs: both suites are run. `pytest tests/` is run here. `pytest tests/e2e/` cannot start its browser on this Linux machine (spec Verified Claims, `libglib-2.0.so.0`), so its macOS run is the owner's.

**Checked by running, not by the suite.** The spec makes these checks run-throughs, and they test the README's copy, which CONTENT § Message patterns calls per-change. A suite test would freeze that copy. Every one runs in a disposable copy made with `git archive` (`<CORE>/roles/CROSS_ROLE.md` § *Every seat*), never in the main checkout, and the developer records each result in Developer Review Notes:

| Rule | Run |
|---|---|
| CP-54, CP-56, CP-59 | Read the README top to bottom. Check the section order, that the README names itself as the setup instructions, the prerequisites' contents and section 4's contents. For CP-59, `git check-ignore -v data/tracker.json` in a `git init` copy matches `.gitignore`'s `data/`. |
| CP-57 | From the top of a fresh `git archive` copy, on a machine with nothing installed beyond Python, type section 2's commands in order and count them. Each part of a line joined with `&&` or `;` counts as a separate command. The count is at most three, the version check included. None of the commands installs anything or asks for an answer. The last command prints the ready line, and the printed address serves the Projects page in its first-run state. |
| CP-58 | Run `python3 main.py` and compare its line with the README's. They differ only in the location. |
| CP-60 | Create `Alpha`, stop the tracker with Ctrl-C, then follow section 5 from a new terminal at the top of the copy. `Alpha` is listed. Read section 5: it says the browser's "can't reach this page" for the tracker's address means the tracker is not running, and that the section starts it again. |
| CP-61 | Run all three Examples: readable data, unreadable data, and `git status --short` in a `git init` copy. Compare `shasum` before and after. Then run the section a second time (§ 4) and check that nothing is deleted. |
| CP-62 | Follow section 7 in a fresh copy. `pytest tests/` exits 0. That catches a venv placed where the source walk reads it (§ 4). The macOS run of `pytest tests/e2e/` is the owner's. |
| CP-63 | Run `grep -n -i -F -e 'no code exists' -e "isn't built yet" -e 'nothing to run' README.md`. It matches nothing. Read the Status: it names `python3 main.py` and no unbuilt feature. |
| CP-64 | Run `git diff <base> -- README.md`. No line inside `How it's built` or `The documents` changes. |

**What this change stops proving.** No assertion is retired. The existing unreadable-start tests assert containment (the location is in the one line) and a line count. Neither breaks when the line gains a sentence. No test asserts the README's current text.

---

## Records this change makes false

None. I read `docs/adr/` (0001 to 0009, all Accepted), `docs/nfdr.md`, `docs/fdr.md` and `docs/SDD.md` § 3, and nothing in them goes false. Three of them describe what this change builds rather than contradict it:

- `docs/SDD.md` RN-10 names `README.md` as the setup instructions, and § 6 S-1 *Artifact* (`:655`) lists what they hold.
- `docs/fdr.md` R-8 to R-14 and R-28 are the rules realized.
- `docs/nfdr.md` QC-40's first sentence reads "A test dependency with a known critical vulnerability is not installed by the setup instructions." It binds for the first time now that setup instructions exist. Its reading is in the QC-40 row below.

The sentences this change makes false are in `README.md` lines 9 to 11 (the `Status`). The README is not a record, and CP-63 rewrites those lines.

---

## Architect Review Notes

- **(b) The CP-67 test derives the quoted section name from one constant.** The spec says the test checks the sentence and "the section name that sentence quotes". Holding the name once and building the sentence from it realizes that by construction. Two literals would agree only by coincidence, and the test could not tell a reworded pair from a matching one.
- **(b) The tie test reads `main.start`'s real output, not `main.py`'s source.** The spec does not say which. The behaviour is what the reader sees on the console, and a source-text match would pass a sentence that never reaches standard error.
- **(b) The tie test and the heading test go in `tests/integration/test_start.py`.** The spec places the test only in "the suite that `pytest tests/` runs" (Locked Answers, Gap 10). That module already drives the unreadable start and holds `UNREADABLE` and `PRODUCT_ROOT`. A new module would repeat both.
- **(b) CP-55 gets a suite test, beyond the grep the spec names.** Without it, nothing keeps the `Starting the tracker again` heading after this change lands. CONTENT § Terminology fixes that heading for strings that point to it, as it fixes the other. The cost is one test, sharing the CP-67 test's heading reader.
- **(b) CP-65 is pinned as the whole line.** The spec states the whole line. Today's tests assert containment. The CP-65 row asserts equality, so the "exactly one line" and "ends with" halves both hold by construction.
- **(b) Where the virtual environment sits, and a repeated set-aside, are stated as properties (§ 4).** The spec leaves both to the content step's commands. Each one is a way the README's copy can break the suite or lose data while still reading correctly, and neither shows up until someone runs it. The venv constraint comes from the code (`tests/conftest.py:104-113`, `.gitignore:18-19`), not from taste.
- **(d) § 3 is omitted although three seams change.** Only one of the three is in the module set. None of the three depends on another's output, so there is no ordering edge to cut on. The one constraint is the CP-67 property § 3 states.

**Reviews `docs/nfdr.md` delegates to `development-design`**

This change touches `main.py`. The review run on every change applies.

| QC | Verdict |
|---|---|
| QC-12 | Pass. The change adds no part. It adds one sentence and three tests, and a document the SRS requires (FR-4). |
| QC-24 | Pass. `main` writes a longer start message. It holds no rule, no page and no file format. |
| QC-41 | Pass. Nothing is read, held or written as a secret. CP-56 forbids the setup instructions from asking for an account, a key, a sign-up or a payment. |
| QC-60 | Pass on a condition, because the harness gap stands. The `main.py` change is string concatenation. The new tests must use nothing newer than Python 3.11. |
| QC-5, QC-8, QC-20 to QC-23, QC-25 to QC-27, QC-36, QC-46 | Not applicable. The change adds no refusal, saved field or page, and does not touch `domain`, `application`, `persistence`, `web` or the saving contract. |
| QC-40 | **Packages: Pass.** On 2026-10-08 I sent all 15 pins in `tests/requirements.txt` to `https://api.osv.dev/v1/querybatch`, and it returned no advisory for any of them. PyPI's newest Playwright is still 1.63.0, uploaded 2026-09-15 (`https://pypi.org/pypi/playwright/json`). **Browser: Pass, on the last day of the window.** Playwright 1.63.0 installs Chromium and Chrome Headless Shell `153.0.8010.12`, revision 1243 (`packages/playwright-core/browsers.json` at tag `v1.63.0`). The Chrome Releases post of Tuesday 2026-09-08 rates five CVEs Critical, all fixed in `153.0.8010.36`: CVE-2026-87438, -87464, -87488, -87527 and -87628. NVD published them on 2026-09-09. Today they are 30 days old, counted from the vendor's post. QC-40 blocks on an advisory "more than 30 days old" and requires a fix "within 30 days", so day 30 is inside the window. The later Critical CVEs, from the posts of 2026-09-22 (eleven) and 2026-09-29 (one), are 16 and 9 days old. **From 2026-10-09, QC-40 blocks every `development-design` review** until the browser pin moves or the owner records a dated exception in `docs/nfdr.md`'s Review Notes. No newer Playwright exists to move to. This overrides (c) the reading in the two previous designs (`trail/2026-10-07_reverse-pointer-test/change_design.md` and `trail/2026-10-07_address-taken-start-message/change_design.md`, QC-40 rows), which put the block at 2026-10-08. They counted day 30 as past the window. QC-40's own words count it as inside. |
| QC-40, first sentence | **Read as binding the lock file's packages. The browser falls under the window.** This change writes the instructions that install the browser, so the sentence binds now for the first time. QC-40 names two things separately: "a test dependency the lock file of QC-39 fixes" and "the browser build the pinned browser-driving library installs". Only the second has a 30-day window for a published critical advisory. Read the other way, the first sentence would block today, inside the window QC-40 itself grants, and the window would mean nothing. The packages pass. The browser is inside its window today. If the owner reads the sentence as covering the browser, this change is blocked until the pin moves. |
