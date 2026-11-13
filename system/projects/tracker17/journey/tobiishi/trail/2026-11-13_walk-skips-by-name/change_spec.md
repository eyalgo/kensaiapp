# Change Spec — the source walk skips by name

**Date:** 2026-11-13
**Category:** nfdr
**Behaviour:** changing
**Request:** NFDR QC-1 says the source walk skips `tests/`, `.behave/` and `.venv/` by name and fails on any other root folder that holds a Python module. `SourceWalk._all` in `products/tracker17/tests/conftest.py` instead skips every path piece that begins with a dot, so code in any other dot-folder (say `.other/x.py`) passes unseen (`grep -nF 'startswith(".")' products/tracker17/tests/conftest.py` matches inside `_all` today). Change `_all` to skip `tests/`, `.behave/` and `.venv/` at the product root by name, and `__pycache__` anywhere, and to no longer test for a leading dot. Add a test in `products/tracker17/tests/architecture/` that builds a root under `tmp_path` holding the five parts, plus `tests/`, `.behave/features/x.py` and `.venv/x.py` (all skipped), plus `.other/x.py`, and asserts `top_level_parts(walk_of(root))` is not `PARTS` and contains `.other`. It must fail at `97603d4f3`, where the walk skips every dot piece, and pass once the walk is changed. A second case of the same root without `.other/` passes before and after and shows the three named folders stay skipped; removing `.other/x.py` makes the QC-1 comparison equal `PARTS` again. The change is one fixture and its tests; no product code, document or `.behave/` file changes. Both suites pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and the same on `products/tracker17/tests/e2e/`, each run from the repository root in a disposable clone at the commit under test, and the last line of each is read.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern it routes

---

## Change Summary

The source walk under the layer-6 tests (the `walk_of` fixture) stops leaving out every path that has a piece beginning with a dot, and leaves out only `tests/`, `.behave/` and `.venv/` at the product root, by name, and `__pycache__` at any depth — as NFDR QC-1 states. A new layer-6 test proves a code-holding dot-folder at the root now fails QC-1's comparison.

Paths below are relative to the product root, which `project.md` `Product path:` names. "The walk" is the source walk `walk_of` builds; "a part" is the name the walk reports for a module (its first path piece under the root, or the file's stem for a file at the root); `PARTS` is the six names `tests/architecture/test_shapes.py` compares against: `domain`, `application`, `persistence`, `web`, `main`, `errors`.

---

## Rules

### What the walk leaves out (NFDR QC-1)

- **CP-785:** The walk over a root leaves out exactly these `.py` files, each matched by its exact name: a file whose first path piece under the root is `tests`, `.behave` or `.venv`; and a file with a path piece named `__pycache__` at any depth, the root included. This is the skip set NFDR QC-1's *verified by* names ("skips `tests/`, `.behave/` and `.venv/` by name"), with `__pycache__` read as Locked Answer Gap 4 records.
- **CP-786:** The walk leaves out no other file. No file is left out because a piece of its path begins with a dot — the defect this rule removes, at `SourceWalk._all`, `tests/conftest.py:141-143`, where `piece.startswith(".")` (line 142) leaves out every such file today. So, after the change: a `.py` file in any other root folder is walked, with that folder's name as its part (`.other/x.py` → part `.other`); a `.py` file at the root is walked as its own part whatever its name begins with (`.x.py` → part `.x`); a folder inside a part is walked as that part whatever its name begins with (`web/.hidden/y.py` → part `web`); and a folder named `tests`, `.behave` or `.venv` below the root is walked as the part holding it. A near name is not a match: `.venvs/`, `.behave2/` and `Tests/` at the root are walked.
- **CP-787:** QC-1's check of the product itself keeps its verdict: the walk of the product root — holding `.venv/` and `.behave/`, as a change worktree and a disposable clone do once their suite environment is made — reports exactly `PARTS`, and `tests/architecture/test_shapes.py::test_the_top_level_parts_are_the_five_the_sdd_names` passes. Every other layer-6 test over the product root passes as it does at the base.

### The test that proves it

- **CP-788:** A test in `tests/architecture/` builds a root under `tmp_path` holding: the five parts — `domain/`, `application/`, `persistence/` and `web/` each with one module, and `main.py` — and `errors.py`; the skipped files `tests/x.py`, `.behave/features/x.py`, `.venv/x.py`, `__pycache__/x.py` and `domain/__pycache__/x.py`; and `.other/x.py`. It asserts that `top_level_parts(walk_of(root))` is not `PARTS` and contains `.other`. Run against the walk at `97603d4f3` it fails, because that walk reports exactly `PARTS` for this root; it passes once CP-785 and CP-786 hold.
- **CP-789:** Removing `.other/x.py` from CP-788's root makes `top_level_parts(walk_of(root))` equal `PARTS`.
- **CP-790:** A second case builds CP-788's root without `.other/` and asserts `top_level_parts(walk_of(root))` equals `PARTS`. It passes against the walk at `97603d4f3` and after the change, so the files CP-785 leaves out stay out.

### What the records above the change require of it

- **CP-791:** Every test module this change adds or alters names, in its opening docstring, the requirements or acceptance criteria it checks, and every path and requirement identifier a docstring names exists, so the pointer test `tests/architecture/test_trace.py` passes (NFDR QC-11, "Every test module names the requirements or acceptance criteria it checks").
- **CP-792:** After the change, `ruff format --check .` and `ruff check .`, run through `uv run` from the product root, each exit 0 (NFDR QC-62 and its two Ruff rows in § 10, which run over the tree, test code included).
- **CP-793:** The change adds no part that no requirement pays for, judged at `development-design` review (NFDR QC-12).
- **CP-794:** The tests the change adds or alters run on Python 3.11, judged at `development-design` review where they use a language or library feature (NFDR QC-60, "The tracker and its tests run on Python 3.11").

### Acceptance

- **CP-795:** At the commit under test, `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`, each run from the repository root in a disposable clone, pass; the last line of each is read and reports passed tests and no failed or errored one.

---

## Examples

| Scenario | Expected behavior |
|---|---|
| CP-785 — root holds `tests/x.py`, `.behave/features/x.py`, `.venv/x.py`, `__pycache__/x.py`, `domain/__pycache__/x.py` beside the six parts | None of the five files is walked; the parts reported are exactly `PARTS` |
| CP-786 — root holds `.other/x.py` beside the six parts | `.other/x.py` is walked as part `.other`; the parts reported are `PARTS` plus `.other` |
| CP-786 — root holds a file `.x.py` | Walked as part `.x` |
| CP-786 — `web/.hidden/y.py` | Walked as part `web`; no new part is reported |
| CP-786 — `domain/.venv/x.py`, `domain/tests/x.py` | Walked as part `domain` |
| CP-786 — root holds `.venvs/x.py` or `.behave2/x.py` | Walked as part `.venvs` / `.behave2`; QC-1's comparison is not equal |
| CP-787 — the product root in a change worktree, with `.venv/` and `.behave/` present | Parts reported are exactly `PARTS`; the QC-1 test passes |
| CP-788 — CP-788's root, walk at `97603d4f3` | Parts reported are exactly `PARTS`; the test fails on its first assertion |
| CP-788 — CP-788's root, walk after the change | Parts reported are `PARTS` plus `.other`; the test passes |
| CP-789 — CP-788's root after `.other/x.py` is removed | Parts reported equal `PARTS` |
| CP-790 — CP-788's root built without `.other/`, at `97603d4f3` and after | Parts reported equal `PARTS` at both |
| CP-791 — the test lands in a new module under `tests/architecture/` | Its docstring names the SRS identifiers it checks (as the other layer-6 modules name NFR-9 and AC-5) and the pointer test passes |
| CP-792 — after the change | `ruff format --check .` and `ruff check .` exit 0 from the product root |
| CP-793 — design review | The change adds only the walk's new skip set and its tests; no new part |
| CP-794 — design review | No construct in the new tests needs a Python newer than 3.11 |
| CP-795 — both suites in a disposable clone at the commit under test | Last line of each reports passed tests and no failure or error |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| CP-786: `piece.startswith(".")` sits inside `SourceWalk._all` today | `grep -nF 'startswith(".")' tests/conftest.py` in the change worktree at the base | `142:` inside `_all` (lines 138-147); the only match, at `654de549c` |
| CP-788, CP-790: "the walk at `97603d4f3`" is the base's walk | `git diff --stat 97603d4f3 654de549c -- products/tracker17` | Empty: the product tree is the same at both commits, so the base stands for `97603d4f3` |
| CP-788: the walk at `97603d4f3` reports exactly `PARTS` for CP-788's root, so the test fails there | A scratch script, run on the product's locked environment, importing the real `SourceWalk` from the change worktree's `tests/conftest.py` at `654de549c` and walking real files written under a temporary directory as CP-788 lists them | `['application', 'domain', 'errors', 'main', 'persistence', 'web']`, equal to `PARTS`; `.other` absent |
| CP-789, CP-790: the base walk reports `PARTS` for the root without `.other/x.py` | Same script and conditions, the root built without `.other/`, and CP-788's root with `.other/x.py` removed | `PARTS` in both, at `654de549c` |
| CP-785 to CP-790: the skip set CP-785 states gives the verdicts CP-788 to CP-790 and CP-787 claim | Same script, with a subclass of the real `SourceWalk` whose `_all` leaves out only CP-785's set; a model of the change, not the shipped code, which CP-788 to CP-790's own tests verify at implementation | CP-788's root → `PARTS` plus `.other`; with `.other/x.py` removed → `PARTS`; built without `.other/` → `PARTS`; `web/.hidden/y.py` → part `web`; `.x.py` at the root → part `.x`; no file under `tests/`, `.behave/`, `.venv/` or `__pycache__/` walked; the product root in the change worktree, holding `.venv/` and `.behave/` → `PARTS` |
| CP-787: the product root walks to `PARTS` and the QC-1 test passes at the base (behaviour kept) | `uv run --locked --project products/tracker17 pytest -p no:cacheprovider products/tracker17/tests/architecture/test_shapes.py::test_the_top_level_parts_are_the_five_the_sdd_names`, with `test_trace.py`, `test_imports.py`, `test_reach.py` and `test_shapes.py`, from the change worktree's root | `654de549c`: 60 passed |
| CP-787: the product root holds no other code-holding folder the new walk would report | `find` over the product root in the main checkout and the worktree, leaving out `tests/`, `.behave/`, `.venv/` and `__pycache__/` | `.py` files only under the six parts; the one other dot-folder, `.pytest_cache/`, holds no `.py` |
| Locked Answer Gap 4: the root's `__pycache__/` holds no source module | `find __pycache__ -name '*.py'` at the product root, main checkout | 0 files; it holds `.pyc` files such as `errors.cpython-314.pyc` |
| CP-792: Ruff's two checks pass at the base, so CP-792 asks only that the change keep them green | `uv run --locked ruff format --check --no-cache .` and `uv run --locked ruff check --no-cache .` from the product root in the change worktree, ruff 0.16.10 | `654de549c`: "349 files already formatted", exit 0; "All checks passed!" |
| CP-786, CP-790: no existing test plants a dot-folder in a root it walks, so no existing test changes | `grep -n '"\.[a-z_]*/' tests/architecture/*.py` | No match |
| CP-788: `top_level_parts`, `PARTS` and `walk_of` exist as named | `tests/architecture/test_shapes.py:20` (`PARTS`), `:43` (`top_level_parts`); `tests/conftest.py:150-157` (`walk_of`, a root given or the product root) | Present at `654de549c` |
| Out of Scope: no test walks `.behave/` today | `grep -n behave tests/architecture/test_imports.py tests/architecture/test_reach.py` | No match at `654de549c` |
| Out of Scope: root folders git ignores without a leading dot are walked, as at the base (behaviour kept) | The scratch script's conditions, `venv/x.py`, `env/x.py`, `build/x.py` and `dist/x.py` added beside the six parts, walked by the real base walk and by the model of CP-785's set | `654de549c`: both report `build`, `dist`, `env`, `venv` beyond `PARTS` |
| Out of Scope: `test_reach.py`'s walk over `tests/` is a separate walk, kept as it is | `tests/architecture/test_reach.py:217-218` read (`TESTS_DIRECTORY.rglob`, its own `.venv` and `__pycache__` test); its test `test_no_test_patches_a_product_module` ran in the 60 above | `654de549c`: passed |
| Language rendering | No rule pins output rendering a language-level fact: the rules fix which files a walk reports and which tests pass | No rendering row owed |

---

## Out of Scope

- Product code, every product document and every file under `.behave/` — the request's words: "no product code, document or `.behave/` file changes".
- The layer-6 walk of `.behave/` that NFDR QC-19's *verified by* names for its second clause ("a walk of that folder that fails on an import from `tests`") — the request's words: "The layer-6 walk of `.behave/` (item 2 of the seed) … [is a] separate change and not part of this one". Today no test walks `.behave/` (`tests/architecture/test_imports.py` and `test_reach.py` hold no `behave`). Parked in `deferred_decisions.md` as a record gap.
- The seeds `2026-11-13_one-fake-and-one-contract-suite-per-contract` and `2026-11-13_the-pins-test-reads-the-behave-lock` — the request names them separate changes.
- NFDR QC-1's sentence "The entry starts unmet in its test" goes out of date when this change lands; the NFDR is not edited here, and the sentence is its owner's to fold.
- The walk `tests/architecture/test_reach.py:217-218` makes over `tests/` itself, which leaves out `.venv` and `__pycache__` by its own test — a different walk from the source walk, unchanged.
- No new name joins the skip set: root folders git ignores without a leading dot (`venv/`, `env/`, `build/`, `dist/`) are walked, as at the base.
- No dependency is added.

---

## Locked Answers (the divergence record — self-review 2026-11-13)

- **Gap 1 — `errors.py` in the built root:** CP-788's root holds `errors.py` beside "the five parts". (b) — `PARTS` holds `errors`, so a root without `errors.py` could never make CP-789's and CP-790's comparison equal `PARTS`, which the request says it does.
- **Gap 2 — `__pycache__` planted in the built root:** CP-788's root also holds `__pycache__/x.py` and `domain/__pycache__/x.py`. (b) — the request's sizing says "the walk must keep skipping … `__pycache__`, no module those skip may become visible"; a planted file is the only way the test sees that. Additive: it adds two files to a root the request already builds.
- **Gap 3 — what "by name" and "no leading-dot test" reach:** names match exactly (`.venvs/` is walked); the three named folders are left out at the root only, and below it they are walked as the part holding them; a `.py` file at the root whose name begins with a dot is walked as its own part; a dot-folder inside a part is walked as that part (CP-786). (b) — the request says "at the product root by name" and "no longer test for a leading dot", and QC-1 says "No other top-level code part exists" and the walk "fails on any other root folder that holds a Python module, whatever its name begins with". Every reading here makes the walk see more code, never less.
- **Gap 4 — `__pycache__` against QC-1's wording:** QC-1 names three root folders the walk skips and says it fails on "any other root folder that holds a Python module"; the request skips `__pycache__` anywhere, the root included (CP-785). (b) — read as one rule, not a conflict: QC-1's subject is "the product's code", `__pycache__` is the folder Python writes compiled files into and holds no source module (the product root's holds only `.pyc` files), and QC-1's own statement of what starts unmet names only the leading-dot test. The NFDR is not changed here.
- **Gap 5 — NFDR QC-11 stated as a rule (CP-791):** (e) — the request is silent on it; QC-11 requires every test module to name what it checks, and binds whichever module holds CP-788 to CP-790's tests.
- **Gap 6 — NFDR QC-62 stated as a rule (CP-792):** (e) — the request is silent on it; QC-62's Ruff checks run over the tree, so they bind the test code this change adds and alters. Both pass at the base.
- **Gap 7 — NFDR QC-12 stated as a rule (CP-793):** (e) — the request is silent on it; QC-12's review at `development-design` asks it of every change that adds code.
- **Gap 8 — NFDR QC-60 stated as a rule (CP-794):** (e) — the request is silent on it; QC-60 says the tests run on Python 3.11, checked at `development-design` review for a change that uses a language or library feature.
