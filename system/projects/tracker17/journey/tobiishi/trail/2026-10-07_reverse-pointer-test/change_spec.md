# Change Spec — the pointer test fails in the reverse direction

**Date:** 2026-10-07
**Category:** nfdr
**Behaviour:** changing
**Request:** Make the pointer test fail in the reverse direction too. Run from `products/tracker17/` under `pytest tests/`. `tests/architecture/test_trace.py` today checks that a feature word listed as landed has its `domain/<word>.py` (`test_each_landed_feature_word_has_its_domain_module`), and nothing checks the other way. After this change it also holds a test that fails when a feature word in SDD § 4 TS-3's table has its `domain/<word>.py` and is not listed in `LANDED_FEATURE_WORDS`, so a slice that adds a feature module without adding its word to the test breaks `pytest tests/` (SDD § 4 TS-4, fourth clause; NFDR QC-11). The check reads only TS-3's words, so a `domain/` module that is no feature's entry (`refusals.py`, `state.py`, `text.py`) is never flagged. Where the table's words come from in code is the design's to settle, with the table in the SDD still the one place they are stated. Like its forward neighbour it ships with a test showing it can fail: a word with its module that is not listed is reported, and a listed word, or a module that is no feature's entry, is not. `pytest tests/` exits 0 on the product as it stands, where `projects` is the only word with a module and it is listed.

---

## Change Summary

The pointer test gains the fourth check SDD § 4 TS-4 and NFDR QC-11 state and the code does not yet
hold: a feature word in TS-3's table whose `domain/<word>.py` exists but which is not listed as landed
fails `pytest tests/`. Today an unlisted feature module passes the suite
(`tests/architecture/test_trace.py:L87-L89` checks only the forward direction; run-verified below).

Paths below are relative to the product root, which `system/projects/tracker17/project.md`
`Product path:` holds.

---

## Rules

### The reverse check

- **CP-47:** `pytest tests/`, run from the product root, fails when a word in the *Feature word*
  column of SDD § 4 TS-3's table has a file `domain/<word>.py` and the word is not in the pointer
  test's landed list. The landed list is the one the forward check already reads —
  `LANDED_FEATURE_WORDS` in `tests/architecture/test_trace.py`, the site NFDR QC-11's tail
  (`docs/nfdr.md:L108-L111`) and RN-21 name as owing this check. The new test lives in that same file,
  as QC-11's tail places it.
- **CP-48:** The set of words the reverse check reads is exactly the *Feature word* column of
  SDD § 4 TS-3's table — eleven words on 2026-10-07: `projects`, `tasks`, `workflow`, `priorities`,
  `assignees`, `labels`, `due_dates`, `comments`, `filtering`, `sorting`, `summary`. That table stays
  the one place in the product's documents the words are stated; this change does not edit it. How the
  test obtains the words is development-design's to settle.
- **CP-49:** A file under `domain/` whose stem is not a word in that column is never flagged by the
  reverse check — today `__init__.py`, `refusals.py`, `state.py` and `text.py`. "Has its module"
  means the file `domain/<word>.py` exists; a word in the table with no such file is not flagged by
  the reverse check, listed or not (a listed word with no file stays the forward check's failure).
- **CP-50:** When the reverse check fails, its failure output names every unlisted word that has its
  module, not only the first.

### Its proof that it can fail

- **CP-51:** The change ships a test that runs in `pytest tests/` and shows the reverse check can
  fail, on inputs the test constructs itself: a table word with its module and not listed is
  reported; a table word with its module and listed is not; a `domain/` module that is no table
  word's entry is not. The test adds no file under the product's own `domain/` and leaves the tree as
  it found it.

### What stays

- **CP-52:** `pytest tests/` exits 0 on the product as it stands, where `projects` is the only table
  word with a module and is listed.
- **CP-53:** The seven tests `tests/architecture/test_trace.py` holds today keep their names and keep
  passing and failing on exactly what they pass and fail on now. No product behaviour changes: no
  page, route, message or saved-data change; no tasks, People or All tasks links, rename or delete;
  no unreadable-data page and no second-tracker refusal; `README.md` is not touched.

---

## Examples

| Scenario | Expected behavior |
|---|---|
| The product as it stands: `domain/projects.py` exists, `LANDED_FEATURE_WORDS` lists `projects` (CP-52, CP-47) | `pytest tests/` exits 0 |
| A slice adds `domain/tasks.py` and does not add `tasks` to the landed list (CP-47) | `pytest tests/` exits non-zero; the failure names `tasks` |
| A slice adds `domain/tasks.py` and `domain/labels.py`, lists neither (CP-50) | the failure names both `tasks` and `labels` |
| A slice adds `domain/tasks.py` and lists `tasks` (CP-47) | the reverse check passes; the other trace checks apply to `tasks` as they do to `projects` |
| `domain/refusals.py`, `domain/state.py`, `domain/text.py`, `domain/__init__.py` present, none listed (CP-49) | the reverse check flags none of them |
| A new `domain/helpers.py` lands, `helpers` not in TS-3's table (CP-49, CP-48) | not flagged |
| `sorting` is in the table, has no `domain/sorting.py`, is not listed (CP-49) | not flagged by either direction |
| The can-fail test's constructed cases (CP-51) | the unlisted-with-module word is reported; the listed word and the non-entry module are not; the product's `domain/` is unchanged afterwards |
| The SDD's TS-3 table after the change (CP-48) | unchanged; still the eleven words above |
| The seven existing tests in `test_trace.py` (CP-53) | same names, same verdicts as before the change |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| `pytest tests/` exits 0 on the product as it stands (CP-52) | `python3 -m pytest tests/ -q` from `products/tracker17/` in the change worktree at `57b86b647`, real files, no harness | `209 passed`, exit 0 |
| Today an unlisted feature module passes the trace test — the present defect (Change Summary, CP-47) | scratch copy (`git archive` of `products/tracker17` at `57b86b647`), added `domain/tasks.py` with a one-line docstring, `tasks` not listed; ran `python3 -m pytest tests/architecture/test_trace.py -q` | `7 passed`, exit 0 |
| The trace file holds seven tests and only the forward module check (CP-53) | read `tests/architecture/test_trace.py:L56-L106` | seven `test_*` functions; `test_each_landed_feature_word_has_its_domain_module` at L87-L89 is the only module check |
| `LANDED_FEATURE_WORDS` lists only `projects` (CP-47, CP-52) | read `tests/architecture/test_trace.py:L19` | `LANDED_FEATURE_WORDS = ["projects"]` |
| `domain/` holds `projects.py` as its one feature entry, plus `__init__.py`, `refusals.py`, `state.py`, `text.py` (CP-49) | `ls products/tracker17/domain` | `__init__.py projects.py refusals.py state.py text.py` |
| TS-3's table has eleven feature words, as listed in CP-48 | read `docs/SDD.md:L441-L453` | the eleven words in CP-48, one per row |
| QC-11 owes the fourth check and names the file (CP-47) | read `docs/nfdr.md:L100-L112` | "holds the first three checks and not the fourth, which the code owes" |

---

## Out of Scope

- The station's final check that reached-when 1 to 7 hold; the README, which is the next station.
- A word listed as landed that is not in TS-3's table — neither direction checks it, and this change adds no such check.
- Any edit to `docs/SDD.md`, `docs/nfdr.md`, `docs/fdr.md` or `adr/`.
- Adding any feature word to the landed list, or any feature module to `domain/`.
- Any product behaviour: pages, routes, messages, saved data, links, rename, delete.

---

## Locked Answers (the divergence record — self-review 2026-10-07)

- **Gap 1 — what "reported" names:** the failure output names every offending word (CP-50) — a
  slice that forgets two words learns both from one run rather than one per run; reversible, and it
  adds to the report without changing the verdict.
- **Gap 2 — "has its module":** read as the file `domain/<word>.py` existing (CP-49) — the request and
  SDD § 4 TS-3 both state the entry point as that file, and the forward check already reads it the
  same way, so the two directions agree on one meaning.
- **Gap 3 — a table word with no module:** stated as not flagged by the reverse check (CP-49) — TS-4
  fails only on a word whose slice has landed and has no module; a word with neither a module nor a
  listing is a slice not yet built, which RN-34 exists to let pass.
- **Gap 4 — the can-fail test leaves the tree as found (CP-51):** the request asks for a test showing
  the check can fail and also that `pytest tests/` exits 0 on the product as it stands; a can-fail
  test that wrote a module into the real `domain/` would make the suite's verdict depend on test
  order and leave a file behind.
- **Gap 5 — the word set is the table's column, not a fixed list (CP-48):** the eleven words are named
  as today's members and the table as the domain, because the SDD owns the table and a later revision
  of it, not this spec, decides its rows.
