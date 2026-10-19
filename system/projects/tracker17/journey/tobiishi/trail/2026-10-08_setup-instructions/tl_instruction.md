# Tech Lead instruction — setup-instructions: the README becomes the setup instructions, and the unreadable-data message points to it

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every path below is relative to it.
**Scope:** one closing sentence in `main.py`; `README.md` gains the seven setup sections and a true Status; three tests in `tests/integration/test_start.py`. The README's words are `change_text.md`'s, placed verbatim.

---

## Project layout

```
products/tracker17/
  main.py                          ← modified (one sentence in start's unreadable-data message)
  README.md                        ← modified (setup instructions; Status rewritten)
  tests/
    integration/
      test_start.py                ← modified (three tests; docstring gains CP-55, CP-65, CP-67, SRS FR-4, README.md)
```

Nothing is created. `domain/`, `application/`, `persistence/`, `web/` and `errors.py` are untouched.
`docs/SDD.md` § 3 parts table: the message is owned by `main` ("writes the start messages to the console"), so Task 1 writes it in `main.py`. The README is a document no part owns (SDD RN-10).

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Task cut (design §3 omits sub-jobs):** three seams are cut into two tasks. Task 1 is `main.py` with its whole-line test. Task 2 is `README.md` with the CP-55 and CP-67 tests. The design's one constraint is that the CP-67 test passes only on a tree holding both the sentence and the heading. Task 2 therefore uses Task 1's output, and its test-first red (heading absent) is real. No atomic-landing edge forces a merge, since the property concerns the final tree and not a green point between tasks.
- **Dependencies:** Task 2 is `Task 1` because the CP-67 test reads the message `main.start` writes, which carries the sentence only after Task 1. Task 1 is `None`.
- **README verification carried as review:** CP-54, CP-56 to CP-64 cannot be asserted by a suite test without freezing per-change copy (design §5, *Checked by running*). They sit in Task 2 under `#### Held by review`, each with its run-through, and not as invented behaviours.
- **Hints carried:** the design's §4 hint on the venv location and on the repeated set-aside is carried to Task 2 as a `# Hint:` block, reduced to the property and the check. The test-shape hint is carried to Task 2 and also governs Task 1's test, which shares the module.
- **Behaviour locked:** a heading line is read the same way in both heading tests, so Task 2 states one shared reader. This follows design §4, which says the CP-55 test shares the CP-67 test's reader.
- **Gate command:** `project.md` `Test command:` is `pytest products/tracker17/tests/`, which runs from the worktree root. The spec's claims ran `python -m pytest -q tests/` from the product root. I did not run the card's command to check it. The developer runs it once before Task 1, and uses the product-root form if it collects nothing. The suite excludes `tests/e2e/`, per `tests/conftest.py`.

## Corrections owed while there

- `README.md:9-11` — the Status says "defined and isn't built yet", "no code exists" and that the setup instructions "arrive in this file with the first slice of work" → rewritten by CP-63. Rides Task 2 (it already opens this file).
- Owed outside this change's reach: `docs/nfdr.md` QC-40 — the design's review passes the Chromium browser pin on the last day of its 30-day window. From 2026-10-09 every `development-design` review is blocked until the pin moves or the owner records a dated exception → the pin moves, or the exception is recorded in `docs/nfdr.md`'s Review Notes.
- Owed outside this change's reach: `docs/SDD.md` § 11 R-9 and `change_spec.md` Out of Scope — the end-to-end browser cannot start on Linux for want of `libglib-2.0.so.0`, and `test_data_is_ignored_by_version_control` fails in a copy that is not a git repository → the definition documents say whether the prerequisites should say more for Linux or name git.

---

### Task 1: The unreadable-data message's closing sentence (`main.py`, `tests/integration/test_start.py`)

**Dependencies:** None

**What to build:** in `start`, the line written to standard error when `SavedData.load` raises `UnreadableData` gains the closing sentence `See Setting saved data aside in the setup instructions.` after `Nothing in it was changed.`. It stays one line, the location is as today, and nothing else in `main.py` changes (CP-65, CP-66). The module and `start` docstrings are not edited.

#### Behaviours to verify (developer adds the test to `tests/integration/test_start.py`)

- `test_an_unreadable_start_writes_exactly_the_one_line_with_the_closing_sentence` — with `UNREADABLE` written to `tmp_path / "tracker.json"`, `main.start(("127.0.0.1", 0), tmp_path)` returns non-zero, standard output is empty, and standard error equals `The tracker didn't start, because it couldn't read its saved data at <tmp_path absolute>. Nothing in it was changed. See Setting saved data aside in the setup instructions.` followed by one newline. A second sentence on its own line, or a lost first half, fails.
- The existing tests (`test_an_unreadable_start_*`, `test_other_unreadable_files_are_refused_the_same_way`, `test_unreadable_saved_data_wins_over_a_held_address`) pass unchanged.

#### Implement

Infer from failing tests.

#### Verification gate

Run `pytest products/tracker17/tests/` from the worktree root.

Pass criteria: the new test passes; no new failures elsewhere. `tests/e2e/` is not collected.

---

### Task 2: The setup instructions and their two heading tests (`README.md`, `tests/integration/test_start.py`)

**Dependencies:** Task 1 (the CP-67 test reads the message `main.start` writes, which carries the sentence only after Task 1)

**What to build:** `README.md` becomes the setup instructions, with its words taken verbatim from `change_text.md` in this change's folder. It names itself as the setup instructions and holds seven sections in order: the prerequisites; the commands from a fresh copy to the tracker in the browser; what the start prints and the address to open; where the saved data is kept; `Starting the tracker again`; `Setting saved data aside`; running the test suites (CP-54 to CP-62). The `Status` section says what runs now and names `python3 main.py` (CP-63). The text of `How it's built` and `The documents`, headings included, is byte-for-byte unchanged (CP-64). The developer writes no string of its own. A string that cannot be placed as written goes in Developer Review Notes, not reworded.

#### Behaviours to verify (developer adds tests to `tests/integration/test_start.py`)

Hold the section name `Setting saved data aside` once, as one module constant. Build the expected closing sentence from it. Both new tests read that constant, so "the section name the sentence quotes" holds by construction. Take the message from a real `main.start` call on unreadable data, captured with `capsys`, never from `main.py`'s source text. Read `README.md` from `PRODUCT_ROOT`, never from the working directory. Read headings with one shared helper: a heading line is an ATX line, the leading run of `#` and the space after it are stripped, and the rest is compared for **equality**. Any heading level counts.

- `test_the_message_closing_sentence_quotes_a_heading_the_readme_has` — the line captured from an unreadable start ends with the sentence built from the constant, and `README.md` has a heading line equal to the constant (CP-67). It fails when only the README heading is reworded, and when only the closing sentence is reworded or removed. Containment must not pass it, so `Setting saved data aside again` fails.
- `test_the_readme_has_both_fixed_headings` — `README.md` has a heading line equal to `Starting the tracker again` and one equal to `Setting saved data aside` (CP-55).
- The docstring of `tests/integration/test_start.py` gains CP-55, CP-65 and CP-67, SRS FR-4 (beside AC-7) and the path `README.md`. `tests/architecture/test_trace.py` checks that each named path exists and each requirement is in `docs/SRS.md`, and `README.md` and `FR-4` both pass.
- Before handing over, the developer makes each of the two edits once in a scratch copy (the README heading reworded with `main.py` untouched; the closing sentence reworded with the README untouched), and records that the CP-67 test fails on each.

#### Held by review

These rules reach no suite test, because a test would freeze the README's per-change copy (design §5). Each is checked by running in a disposable copy made with `git archive` (`<CORE>/roles/CROSS_ROLE.md` § *Every seat*), never in the main checkout. The developer records each result in Developer Review Notes:

- CP-54, CP-56, CP-59 — read the README top to bottom. Check the section order, that it names itself as the setup instructions, the contents of the prerequisites and of section 4. In a `git init` copy, `git check-ignore -v data/tracker.json` matches `.gitignore`'s `data/`.
- CP-57 — from the top of a fresh `git archive` copy with only Python on the machine, type section 2's commands in order. Each part of a line joined with `&&` or `;` counts separately. The count is at most three, the version check included. None installs anything or asks for an answer. The last prints the ready line, and the printed address serves the Projects page in its first-run state.
- CP-58 — run `python3 main.py` and compare its line with the README's. They differ only in the location.
- CP-60 — create `Alpha`, stop the tracker with Ctrl-C, follow section 5 from a new terminal at the top of the copy, and check that `Alpha` is listed. The section says the browser's "can't reach this page" means the tracker is not running.
- CP-61 — run all three spec Examples (readable data, unreadable data, `git status --short` in a `git init` copy) and compare `shasum` before and after. Then run the section a second time and check that nothing is deleted.
- CP-62 — follow section 7 in a fresh copy, and check that `pytest tests/` exits 0. The macOS run of `pytest tests/e2e/` is the owner's, since the end-to-end browser cannot start on this Linux machine.
- CP-63 — `grep -n -i -F -e 'no code exists' -e "isn't built yet" -e 'nothing to run' README.md` matches nothing. The Status names `python3 main.py` and no unbuilt feature.
- CP-64 — `git diff <base> -- README.md` changes no line inside `How it's built` or `The documents`.

#### Implement

Infer from failing tests.

# Hint: The virtual environment section 7 makes must sit where the suite does not look for product code. That means a dot-named directory at the product root, such as `.venv`, or a directory outside the product root. `tests/conftest.py`'s source walk (`:104-113`) skips only `tests/`, dot-named folders and `__pycache__`, so a `venv/` or `env/` at the product root is walked: the QC-1 test fails on a sixth part and the layer-6 import walks read site-packages. Setting data aside must also delete nothing when it is done a second time. A second set-aside into the same named place must not overwrite or merge into the first, and the section must still say where the data went. Check both by running the section twice. These are properties the placed text must keep. If `change_text.md` places either one differently, record it in Developer Review Notes and do not reword it.

#### Verification gate

Run `pytest products/tracker17/tests/` from the worktree root.

Pass criteria: both new tests pass, with the CP-67 test red before the README heading lands; every existing test passes unchanged; `tests/e2e/` is not collected. The Held-by-review checks above are recorded.
