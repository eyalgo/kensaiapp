# Change Design — the pointer test fails in the reverse direction

**Date:** 2026-10-07
**Category:** nfdr
**Behaviour:** changing
**Publishes text:** no

---

## 1. Change Summary

This is the structural plan for `change_spec.md` in this folder (CP-47 to CP-53). The pointer test gains its fourth check. When a word in SDD § 4 TS-3's *Feature word* column has its file `domain/<word>.py` and is not in `LANDED_FEATURE_WORDS`, `pytest tests/` fails, and the failure names every such word.

The test reads the words from `docs/SDD.md` when it runs. The test file does not copy them. This keeps the table the one place the words are stated (CP-48). The test file already reads `docs/SRS.md` the same way (`tests/architecture/test_trace.py:18`).

One file changes: `tests/architecture/test_trace.py`. No product part changes. Paths are relative to the product root, `products/tracker17/`, which is what `system/projects/tracker17/project.md` names in `Product path:`.

---

## 2. Blast Radius

The new logic is three pieces: reading the *Feature word* column out of the SDD text, the reverse check, and the test that shows the check can fail. None of the five parts in `docs/SDD.md` § 3 owns this logic, because the parts table names product parts only (`docs/SDD.md:189-195`). `docs/nfdr.md` QC-11's tail puts the pointer test in `tests/architecture/test_trace.py` (`docs/nfdr.md:105-111`). Review Note (e) records why.

| Module | Status | What changes |
|---|---|---|
| `tests/architecture/test_trace.py` | Modified | Three additions. (1) A function that reads the *Feature word* column of SDD § 4 TS-3's table from a given text, which defaults to `docs/SDD.md`. (2) A function that returns, in table order, each word that has its file in a given `domain` directory and is missing from a given landed list. Its defaults are the real words, `LANDED_FEATURE_WORDS` and `domain/`. (3) Three new tests (§5). The module docstring gets one sentence about the reverse check and where its words come from. The seven existing tests, `LANDED_FEATURE_WORDS` and the existing helpers stay as they are. |
| `domain/` | Unchanged | — |
| `application/` | Unchanged | — |
| `persistence/` | Unchanged | — |
| `web/` | Unchanged | — |
| `main.py` | Unchanged | — |
| `errors.py` | Unchanged | — |
| `docs/SDD.md` | Unchanged | The test reads it and never writes it (CP-48). |

**No transitive blast radius.** No module imports `tests/architecture/test_trace.py`. A search of `tests/`, the parts and `main.py` for `test_trace` and `LANDED_FEATURE_WORDS` found nothing outside the file itself. QC-19 forbids any product module to import from `tests/` (`docs/nfdr.md:149-151`).

---

## 4. Code Strategy

One module is affected, so the change is one delta and §3 is omitted. Inside the file, the reader and the check have no ordering edge between them, and each lands green.

| Sub-job / change | Hint |
|---|---|
| `tests/architecture/test_trace.py` — reading the words | Find the table by its header cell `Feature word`. That cell appears once in `docs/SDD.md`, at line 441. Take that column's index from the header row. Read the rows that follow up to the first line that is not a table row, skip the separator row, and strip the backticks around each word. If no header matches, return an empty list rather than raising an error. The real-product test then fails on that empty list (§5 row 1). Without that, a reader that found nothing would pass everything. |
| `tests/architecture/test_trace.py` — the reverse check | Give the function its words, its landed list and its `domain` directory as arguments, with the real ones as defaults. This is the shape `missing_paths(text, root=PRODUCT_ROOT)` already has. The can-fail test then passes its own inputs, and it patches no module constant. Loop over the table's words in table order and keep each word that has its `<word>.py` file (`is_file()`, as the forward check does at `:89`) and is not in the landed list. Do not list the `domain` directory. A file that is no feature's entry is then never even seen (CP-49). The real test asserts that the whole returned list is empty, so pytest's report names every offender (CP-50). |

---

## 5. Test Additions

Every row is in `tests/architecture/test_trace.py`.

| Sub-job | Test file | What to add / modify |
|---|---|---|
| reverse check | `tests/architecture/test_trace.py` | **New** `test_each_feature_word_with_its_domain_module_is_listed_as_landed` (CP-47, CP-49, CP-50, CP-52). It reads the words from the real `docs/SDD.md` and asserts at least one was found. It then asserts that the check's list over the real `domain/` and `LANDED_FEATURE_WORDS` equals `[]`. It passes on the product as it stands. |
| reverse check | `tests/architecture/test_trace.py` | **New** `test_the_reverse_check_can_fail` (CP-49, CP-50, CP-51). Inputs are built by the test. The `domain` directory is under `tmp_path` and holds `projects.py`, `tasks.py`, `labels.py`, `helpers.py` and `__init__.py`. The words are `projects`, `tasks`, `labels`, `sorting`, and `sorting` has no file. Three cases. Landed `["projects"]` gives `["tasks", "labels"]`, so both are named and `helpers`, `__init__` and the file-less `sorting` are not. Landed `["projects", "tasks"]` gives `["labels"]`. All four words landed gives `[]`. The test records the product's real `domain/` listing before the cases and asserts it is the same afterwards. |
| word reader | `tests/architecture/test_trace.py` | **New** `test_the_feature_words_are_read_from_the_table` (CP-48). Input is a built text. A different table comes first, then a table with the header `\| PRD Core Feature \| Feature word \| SRS requirements \|` and three rows with backticked words, then a paragraph. Exactly those three words come back, in row order. A text with no such header returns `[]`. |
| module docstring | `tests/architecture/test_trace.py` | Modify. Add a sentence saying the file also checks that every TS-3 word with its `domain/<word>.py` is listed as landed, and that the words are read from `docs/SDD.md`. `test_every_path_named_in_a_test_module_docstring_exists` checks the new path. The docstring must name no requirement identifier that `docs/SRS.md` does not define. |

**Examples and rule-implied edges, covered:**

- **The product as it stands exits 0 (CP-52):** row 1, plus the whole suite.
- **`tasks.py` added, not listed. Then `tasks.py` and `labels.py` added, neither listed (CP-47, CP-50):** row 2's first case on built inputs. On the real tree, row 1 is the test that fails and names the words.
- **`tasks.py` added and listed (CP-47):** row 2's second case for the reverse check. The forward checks already loop over `LANDED_FEATURE_WORDS` (`:57`, `:71`, `:88`), so they apply to `tasks` with no change. Review Note (b) covers `test_projects_entry_docstring_names_its_parts`.
- **`refusals.py`, `state.py`, `text.py`, `__init__.py` not flagged. A new `helpers.py` not flagged (CP-49):** row 1 on the real tree and row 2 (`helpers.py`, `__init__.py`).
- **`sorting` in the table, no file, not listed (CP-49):** row 2. The forward check does not read an unlisted word.
- **The can-fail test leaves the tree as it found it (CP-51):** row 2 writes only under `tmp_path` and asserts the real listing is unchanged.
- **The TS-3 table is unchanged (CP-48):** the change does not touch `docs/SDD.md`, and the diff shows it.
- **A wrong or missing table makes the check pass on nothing:** row 1's non-empty assertion, together with row 3's no-header case.
- **The seven existing tests keep their names and verdicts (CP-53):** none is edited, and the suite runs them.

**What this change stops proving.** No assertion is retired. No existing test or helper is edited, and `LANDED_FEATURE_WORDS` stays `["projects"]`.

---

## Records this change makes false

- `docs/nfdr.md` § 1.1 QC-11, the *verified by* tail (`:109-111`). It says "On 2026-10-07 `tests/architecture/test_trace.py` holds the first three checks and not the fourth, which the code owes". This is false once the change lands. It should say that `tests/architecture/test_trace.py` holds all four checks and that the fourth reads TS-3's words from `docs/SDD.md`.
- `docs/nfdr.md` § NFDR Review Notes RN-21 (`:765-767`). It says "The reverse check is owed by the code: `tests/architecture/test_trace.py` … tests only that each listed word has its module, and the entry's tail says so". This is false once the change lands. It should say that the reverse check is in `tests/architecture/test_trace.py`, with QC-11's tail updated to match.

Also read: `docs/adr/` (0001 to 0009, all Accepted), `docs/fdr.md` and `docs/SDD.md` § 3, § 4 TS-3/TS-4 and § 11 R-6. Nothing in them goes false. SDD RN-34 (`:1598-1600`) says what the test held "on the day of the fold", which is dated and stays true.

---

## Architect Review Notes

- **(b) The words are read from `docs/SDD.md` when the test runs. They are not copied into the test file (CP-48).** The spec left the source open. A list in the test would state the eleven words a second time, and it would drift silently when a later SDD revision changed a row. Reading the table keeps the SDD the one place the words are stated. This is the same thing the file already does with `docs/SRS.md`. The cost is that the test depends on how the table is laid out. That is guarded by finding the table by its header cell and by row 1 failing when no word is read.
- **(b) "Every offender is named" (CP-50) is realized by construction.** The check returns the whole list in table order, and the test asserts the list equals `[]`. It does not stop at the first offender, and it does not depend on pytest stopping early.
- **(b) "Has its module" (CP-49) means the file `domain/<word>.py` exists, and is checked word by word.** The `domain` directory is never listed. A file that is no feature's entry cannot be flagged, whatever files later appear there.
- **(b) The CP-47 Examples row "the other trace checks apply to `tasks` as they do to `projects`" is read as the checks that loop over `LANDED_FEATURE_WORDS`.** `test_projects_entry_docstring_names_its_parts` is written for `projects` only (`:92-99`). CP-53 keeps its name and verdict. A slice that lands `tasks` gets the path, requirement and module checks, but not the parts check. Making that check general is outside this change: the request says no check is added beyond the reverse one.
- **(e) No part owns the new logic.** SDD § 3's parts are the product's five parts (`docs/SDD.md:189-195`), and the pointer test is test code. The unit's language frame places `tests/` at the product root (`docs/SDD.md:203-205`). `docs/nfdr.md` QC-11's tail names `tests/architecture/test_trace.py` as the file that owes the fourth check (`:109-111`). That file is where the logic goes.

**Reviews `docs/nfdr.md` delegates to `development-design`**

This change touches only `tests/architecture/test_trace.py`. Only the reviews that run on every change, or on a change of this kind, apply.

| QC | Verdict |
|---|---|
| QC-12 | Pass. The change adds two helpers and three tests to an existing test file. It adds no part. SDD § 4 TS-4 and QC-11 pay for it. |
| QC-41 | Pass. The change reads, holds and writes no secret. |
| QC-60 | Pass on a condition, because the harness gap stands. Reading a file, splitting strings and `Path.is_file()` are all in Python 3.11. The new code must use nothing newer than 3.11, and `pyproject.toml` sets Ruff's `target-version = "py311"`. |
| QC-5, QC-8, QC-20 to QC-27, QC-36, QC-46 | Not applicable. The change touches no part, refusal, page, saved field or saving contract. |
| QC-40 | **Packages:** Pass. On 2026-10-07 I sent all 15 pins in `tests/requirements.txt` to `https://api.osv.dev/v1/querybatch`, and it returned no advisory for any of them. PyPI's newest Playwright is still 1.63.0 (`https://pypi.org/pypi/playwright/json`). **Browser:** Pass today. From 2026-10-08 it blocks. Playwright 1.63.0 installs Chromium `153.0.8010.12` (`packages/playwright-core/browsers.json` at tag `v1.63.0`, revision 1243). The Chrome Releases blog's Stable Channel post of 2026-09-08, `153.0.8010.36`, lists five critical CVEs: CVE-2026-87438, -87464, -87488, -87527 and -87628. NVD gives CVE-2026-87464 as "prior to 153.0.8010.36". Today they are 29 days old. The earlier critical CVEs on that feed from 2026-08-20 to 2026-09-01 are bounded below 153 in NVD: CVE-2026-76017 is "prior to 151.0.7922.173", CVE-2026-79282 is "prior to 152.0.7977.65", and CVE-2026-84352 and -84353 are "prior to 152.0.7977.75". From 2026-10-08, QC-40 blocks the next change unless the browser is replaced or the owner records a dated exception in `docs/nfdr.md`'s Review Notes. No newer Playwright exists to move the pin to. |
