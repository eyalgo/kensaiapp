# Code integrity report — 2026-10-07_reverse-pointer-test

Integrity: pass

**Mode:** workflow · **Reviewer:** Senior Engineer · **Date:** 2026-10-07
**Outcome:** clean pass. No code bug. One test added, one test corrected; all 220 cases green.

## Deferrals

None. The closing marker (`df7c793d3`, `developer: 2026-10-07_reverse-pointer-test — implementation complete`) carries no `Deferred:` line and reads `Suite: green`.

## What was reviewed

`products/tracker17/tests/architecture/test_trace.py` — the only file the change's code commits touch (`git diff main...HEAD -- products/` at `df7c793d3`): the reader `table_cells` / `feature_words`, the constant `FEATURE_WORDS`, the check `unlisted_feature_words`, the helpers `table_text` / `build_domain`, ten new tests, and the module docstring sentence.

## The intent it was checked against

- `tl_instruction.md` — Task 1 (feature-word reader) and Task 2 (reverse check), their `#### Behaviours to verify`, `#### Held by review` and *Corrections owed while there*.
- `change_spec.md` — CP-47 to CP-53 and the Examples table.
- `change_design.md` — §2, §4, §5 and Architect Review Notes.
- `docs/fdr.md` — not needed; the change is `nfdr` and touches no feature.

## Tests added or fixed

- **Added** `test_the_reader_reads_the_column_the_header_names` (`test_trace.py:189`). Every built table put `Feature word` at index 1, so a reader that hardcoded column 1, or matched the exact header line, passed every test. CP-48 and Task 1 say the words come from the *Feature word* column, found by its header cell. The new table puts the column at index 0. Shown to discriminate: with `column = 1` substituted in `feature_words`, it fails (`assert ['FR-10', 'FR-15'] == ['projects', 'tasks']`); restored, it passes.
- **Corrected** `test_the_reverse_check_leaves_the_products_domain_directory_as_found` (`test_trace.py:239`). It ran its own three calls on a different `tmp_path` domain (no `helpers.py`, no `__init__.py`), so it stayed green even if `test_the_reverse_check_can_fail` wrote into the real `domain/`. It now snapshots `DOMAIN_DIRECTORY`, runs `test_the_reverse_check_can_fail(tmp_path)` itself, and compares. See *Calls made*.

Every other new test matches its named behaviour in `tl_instruction.md` and is left as written.

## The finding

No bugs. The code matches CP-47 to CP-53:

- the reader finds the table by its header cell, skips the separator, stops at the first non-table line and skips short rows;
- the check walks the words in table order and tests `is_file()` per word without listing the directory;
- the real-product test asserts the word list is non-empty and the whole offender list is `[]` (CP-50);
- the seven existing tests are unedited and `LANDED_FEATURE_WORDS` is still `["projects"]` (CP-53);
- no file under `domain/` or `docs/` changed.

Suite: `python3 -m pytest products/tracker17/tests/` → `220 passed` (219 before this review plus the one added test). `python3 -m compileall -q` exit 0. `uvx ruff@0.16.10 format --check` and `check` on the file are clean, using the product's own `pyproject.toml` config.

Nothing was moved; see *Placement*.

The two `docs/nfdr.md` corrections the plan names (QC-11's *verified by* tail and RN-21) are owed outside this change's reach. They become false when this change lands, and they belong to the Principal Architect.

## Calls made

- **Question:** for the CP-51 guard, `tl_instruction.md` Task 2 says it "records the real `domain/` listing before the three cases above run and asserts the same listing afterwards". Does that mean the can-fail test's own cases, or any three similar calls?
  - **Readings weighed:** (a) re-state similar calls on a separate `tmp_path` domain, which is the code as written; (b) run the can-fail test's own cases between the two snapshots.
  - **Taken:** (b). "The three cases above" names the can-fail test's cases, and CP-51 is a property of *that* test ("The test adds no file under the product's own `domain/`"). Reading (a) guards calls that no other test makes. It is also the smaller change: one call replaces six lines.
  - **Whose document:** the Tech Lead's (`tl_instruction.md`).
  - **If reversed:** the guard goes back to its own inputs, and CP-51 is held only by reading the can-fail test.

## Placement

Parts table: `products/tracker17/docs/SDD.md` § 3 (`:189-195`) — `domain`, `application`, `persistence`, `web`, `main`.

- `table_cells`, `feature_words`, `FEATURE_WORDS`, `unlisted_feature_words`, `table_text`, `build_domain` (`test_trace.py:61-92`, `:149-221`): **no owning part**. This is test code. The parts table names product parts only, and `docs/nfdr.md` QC-11's tail and `change_design.md` §2 / Review Note (e) place it in `tests/architecture/test_trace.py`, where it already is.

No move. No placement commit.

## Language resolution

- **Python**, declared in `project.md` (`Languages: Python`) — chain step 1.
- **Packet:** `core/doctrine/engineering/languages/python/README.md`. It routes Toolchain, Layout, Quality gates, Conventions and Errors and logging to the folder, and Testing to `testing_python.md`. Read: `quality_gates.md`, `conventions.md`, `testing_python.md` § Layer 6.
- `quality_gates.md` — Compile and Suite are the gates. Both pass. The product also pins Ruff (`pyproject.toml` `[tool.ruff]`). It flagged FLY002 on my first draft of the added test, and I rewrote the test to a literal; it is clean now.
- `conventions.md` § Surface style — 100 columns: `awk 'length>100'` finds none. Double quotes are used, and the f-string usage is unchanged.
- `conventions.md` § Typing — the production-style helpers are annotated, and `from __future__ import annotations` is still first.
- `conventions.md` § Constructs — "a default on a collaborator is what this rule forbids". `unlisted_feature_words` defaults `domain` to `DOMAIN_DIRECTORY`. That is a `Path` value in a test module, not a port object, and `tl_instruction.md` Task 2 prescribes those defaults on the `missing_paths(text, root=PRODUCT_ROOT)` shape. I read it as not a breach.
- `testing_python.md:57` — "A layer-6 test that reads a hardcoded list is a layer-1 test wearing layer 6's name". The check reads its words from the SDD. The one hardcoded list is the CP-48 guard (`test_trace.py:199`), which the plan names, and the developer's marker records this divergence.
