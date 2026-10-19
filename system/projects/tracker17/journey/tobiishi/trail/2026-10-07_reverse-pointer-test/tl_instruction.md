# Tech Lead instruction — reverse-pointer-test: the pointer test fails in the reverse direction

**Product root:** products/tracker17 — every path below is relative to it.
**Category:** nfdr
**Behaviour:** changing
**Scope:** `tests/architecture/test_trace.py` gains a reader for SDD § 4 TS-3's *Feature word* column and the reverse check (a word with its `domain/<word>.py` that is not in `LANDED_FEATURE_WORDS` fails `pytest tests/`), with tests showing both can fail (CP-47 to CP-53).

---

## Project layout

```
products/tracker17/
  tests/
    architecture/
      test_trace.py        ← modified (the only file this change touches)
```

No new directory, no `__init__.py`. No product part changes: `domain/`, `application/`, `persistence/`, `web/`, `main.py` and `errors.py` stay as they are, and `docs/SDD.md` is read and never written (CP-48).

No part owns this logic — SDD § 3's parts table names the product's five parts, and this is test code. Placement follows `change_design.md §2`.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Task split:** the design's §4 gives one file two sub-jobs. They are two responsibilities, so Task 1 is the word reader and Task 2 is the reverse check. The reader has no ordering edge into the check (the check takes its words as an argument), so each lands green. Task 2's real-product test calls the reader, so Task 2 depends on Task 1.
- **Behaviour locked (the reader's reading of a malformed row):** the design says "read the rows that follow up to the first line that is not a table row". The input left implicit that a row with fewer cells than the header has a *Feature word* index for. Pinned: such a row is skipped rather than raising an error, because a reader that raises on an odd row would break the whole suite where the check's job is to compare words.
- **Behaviour added:** `test_the_reader_finds_the_words_only_in_the_table_whose_header_holds_the_cell` (Task 1) — §5 row 3 covers "a different table comes first" in prose; it is the test's name here so a reader that takes the first table it sees fails it.
- **Docstring held by review:** the module docstring sentence (§5 row 4) has no test of its own. The existing `test_every_path_named_in_a_test_module_docstring_exists` and `test_every_requirement_identifier_named_exists_in_the_srs` read it, and they are the check. They are carried as a `Held by review` line in Task 2, not as a behaviour.
- **Hint tightened:** the §4 hint says the header cell appears once, "at line 441". The line number is a fact about the SDD today and goes stale, so the hint below says to find the table by its header cell only.

## Corrections owed while there

- `tests/architecture/test_trace.py:L1-L8` — the module docstring says nothing of the reverse check or where its words come from → one sentence added saying the file also checks that every TS-3 word with its `domain/` file is listed as landed, and that the words are read from `docs/SDD.md`. Rides Task 2 (that task already opens this file).
- Owed outside this change's reach: `docs/nfdr.md` § 1.1 QC-11, the *verified by* tail (`:109-111`) — it says that on 2026-10-07 `tests/architecture/test_trace.py` holds the first three checks and not the fourth, which is false once this change lands → it should say that the file holds all four checks and that the fourth reads TS-3's words from `docs/SDD.md`.
- Owed outside this change's reach: `docs/nfdr.md` § NFDR Review Notes RN-21 (`:765-767`) — it says the reverse check is owed by the code and the test file tests only the forward direction, which is false once this change lands → it should say the reverse check is in `tests/architecture/test_trace.py`, with QC-11's tail updated to match.

### Task 1: Feature-word reader (`tests/architecture/test_trace.py`)

**Dependencies:** None

**What to build:** a function in `tests/architecture/test_trace.py` that returns, in row order, the words in the *Feature word* column of SDD § 4 TS-3's table, from a given text that defaults to the real `docs/SDD.md`. It returns an empty list when no table has that header.

#### Behaviours to verify (developer adds tests to `tests/architecture/test_trace.py`)

- `test_the_feature_words_are_read_from_the_table` — the input is a built text: an unrelated table first, then a table with the header `| PRD Core Feature | Feature word | SRS requirements |` and three rows with backticked words, then a paragraph. Exactly those three words come back, in row order, without backticks (CP-48).
- `test_the_reader_finds_the_words_only_in_the_table_whose_header_holds_the_cell` — a word in the unrelated first table's rows is not returned; a row after the paragraph that follows the table is not returned.
- `test_the_reader_returns_nothing_when_no_header_matches` — a text with no `Feature word` header gives `[]`, not an exception.
- `test_the_reader_skips_a_row_shorter_than_the_header` — a row with fewer cells than the header is skipped; the rows around it are still returned.
- `test_the_real_table_yields_its_eleven_words` — the reader over the real `docs/SDD.md` returns the eleven words of CP-48, in table order. It guards the reader against the table's present layout, and it does not copy the words into the test as the check's source: the check reads the table, and this test compares against the SDD's own statement of CP-48's list once, in the test body.

#### Implement

Infer from failing tests.

# Hint: find the table by its header cell, `Feature word`. Take that cell's index from the header row. Read the rows that follow, skipping the separator row, up to the first line that is not a table row, and strip the backticks around each word. If no header matches, return an empty list.

#### Verification gate

Run `pytest products/tracker17/tests/` from the worktree root.

Pass criteria: the five new tests pass; no new failures elsewhere (209 passed on `main`'s base before this change, plus the new tests).

### Task 2: The reverse check (`tests/architecture/test_trace.py`)

**Dependencies:** Task 1 (the real-product test calls the reader)

**What to build:** a function in `tests/architecture/test_trace.py` that returns, in table order, each word that has its file `<word>.py` in a given `domain` directory and is missing from a given landed list. Its words, landed list and directory are arguments with the real ones as defaults (the reader's words, `LANDED_FEATURE_WORDS`, `PRODUCT_ROOT / "domain"`). Two tests use it, and the module docstring gains a sentence about it.

#### Behaviours to verify (developer adds tests to `tests/architecture/test_trace.py`)

- `test_each_feature_word_with_its_domain_module_is_listed_as_landed` — over the real `docs/SDD.md`, the reader finds at least one word; the check over the real `domain/` and `LANDED_FEATURE_WORDS` returns `[]`. It passes on the product as it stands (CP-47, CP-49, CP-50, CP-52). When it fails, the report names every offender, because the whole returned list is asserted.
- `test_the_reverse_check_can_fail` — inputs the test builds under `tmp_path`: a `domain` directory holding `projects.py`, `tasks.py`, `labels.py`, `helpers.py` and `__init__.py`; the words `projects`, `tasks`, `labels`, `sorting`, with `sorting` having no file. Landed `["projects"]` returns `["tasks", "labels"]`, naming both and neither `helpers`, `__init__` nor the file-less `sorting`. Landed `["projects", "tasks"]` returns `["labels"]`. All four words landed returns `[]` (CP-49, CP-50, CP-51).
- `test_the_reverse_check_leaves_the_products_domain_directory_as_found` — records the real `domain/` listing before the three cases above run and asserts the same listing afterwards (CP-51). Held as its own test so its name says what it guards.
- `test_the_reverse_check_ignores_a_word_with_no_file` — a table word with no `<word>.py`, listed or not, is not returned (CP-49).
- `test_the_reverse_check_ignores_a_module_that_is_no_table_words_entry` — `refusals.py`, `state.py`, `text.py` and `__init__.py` in the directory, none listed, none a table word: `[]` (CP-49).

#### Held by review

- The module docstring sentence (`Corrections owed while there`, first line) — covered by no test of its own. The observable that stands for it is `test_every_path_named_in_a_test_module_docstring_exists` and `test_every_requirement_identifier_named_exists_in_the_srs`, which read the docstring: the sentence must not name a path that does not exist or a requirement identifier `docs/SRS.md` does not define. Its wording is held by reading the diff.
- CP-53: the seven existing tests keep their names and verdicts — covered by the suite running them. Held by reading the diff that none is edited and `LANDED_FEATURE_WORDS` stays `["projects"]`.

#### Implement

Infer from failing tests.

# Hint: loop over the words in table order and keep each word whose `<word>.py` is a file in the directory (`is_file()`, as the forward check does) and that is not in the landed list. Do not list the directory: a file that is no table word's entry is then never seen. Give the function its words, landed list and directory as arguments with the real ones as defaults, the shape `missing_paths(text, root=PRODUCT_ROOT)` already has, so the can-fail tests pass their own inputs and patch no module constant.

#### Verification gate

Run `pytest products/tracker17/tests/` from the worktree root.

Pass criteria: the five new tests pass; the seven tests the file held before keep their names and verdicts; `pytest products/tracker17/tests/` has no failures; no file under `domain/` was added.
