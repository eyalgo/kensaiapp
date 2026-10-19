# Code integrity report — 2026-10-07_a-not-found-page

Integrity: pass

**Date:** 2026-10-07 · **Reviewer:** Senior Engineer (`development-code-integrity`) · **Mode:** workflow

## Deferrals

**None.** The newest marker, `06cd9a17a` (`developer: 2026-10-07_a-not-found-page — implementation
complete`), carries no `Deferred:` line and reads `Suite: green`. It supersedes `cc2205854`, as its own
re-close line says.

## What was reviewed

Every product file the branch changes under `products/tracker17/`, from `859e065d6` to `06cd9a17a`:
`web/pages.py` (`not_found_page`), `web/routes.py` (the `GET` fallback, `_html` taking a status,
`_not_found_page`), and the tests in `tests/integration/test_pages.py`, `test_routes.py`,
`test_listener.py` and `tests/e2e/test_first_project.py`.

## The intent it was checked against

`tl_instruction.md` (Tasks 1 and 2, their *Behaviours to verify*, the TL Review Notes),
`change_spec.md` (CP-30 to CP-38), `change_design.md` (§ 3 W1 and W2, § 5, the Architect Review Notes)
and `change_text.md`, all in this folder. Also `docs/SDD.md` § 3 and `docs/nfdr.md` QC-56 and QC-62.
`docs/fdr.md` was not needed for any finding.

Every string the page shows matches `change_text.md` word for word: the heading "There's no project at
this address" with no full stop, "Open Projects." with only `Projects` as the link, and the title "Not
found - tracker17" (`web/pages.py` `not_found_page`).

## Tests added or fixed

- **Added** `test_pages.py::test_the_not_found_page_gives_projects_in_a_paragraph_after_its_heading`.
  Task 1's *What to build* and design W1 put the page's body together this way: one `h1`, then one
  paragraph directly in `main` that holds the link to Projects, and nothing else. CP-33 says the
  sentence comes first and the link follows it. No test checked this structure. The existing test
  counts one `h1` on the page and one link in `main`, so it would still pass with the link inside the
  heading, or with the link in `main` and no paragraph. Either change would also drop the sheet that
  `web/style.css:79-82` gives a paragraph directly in `main`. The new test was green on first run.

No existing test needed fixing. Each test the developer wrote checks the intent and not the
implementation. The routes tests compare the body byte for byte with `pages.not_found_page()` for every
target. The page tests prove the words they assert. The developer's own mutation of the `GET` gate
(`if True`, 10 cases red) shows the gate is guarded.

## The finding

**No bug in the change.** All three suites were green before this review and are still green after it.

**One defect found while walking, and repaired:** QC-62's gate was red. `ruff check .` found 8 findings
and `mypy main.py errors.py domain application persistence web` found 3 errors. The same 8 and 3 were
there at `859e065d6`, before this change, so the change added none. Commit `2ac931bc2` repairs them all
without changing behaviour:

- `persistence/saved_data.py` TRY004: the two `ValueError` checks are merged into one, with the same
  exception and message and the same catch at `:54`.
- `web/routes.py` BLE001: turned off inline with a comment naming QC-56, which is QC-62's own standing
  case.
- `web/listener.py` and `main.py:50` mypy: `Listener` declares `server_address: tuple[str, int]`, and
  the handler for each listener is a class statement, so `site` is visible to mypy.
- In the tests: RUF059, FURB188 and four RUF100.

The call behind this repair is under *Calls made*. After the repair, `ruff check .` reports "All checks
passed!", `ruff format --check .` reports "103 files already formatted", and mypy reports "no issues
found in 16 source files".

**Suite after review:** `pytest products/tracker17/tests/` from the worktree root, 198 passed;
`pytest tests/` from the product root, 198 passed;
`uv run --no-project --with-requirements tests/requirements.txt python -m pytest tests/e2e/`, 11 passed;
`python3 -m compileall -q web persistence tests`, exit 0.

## Calls made

1. **Does this change carry QC-62's repair?**
   - *Readings weighed:* (a) No. `tl_instruction.md` says "Nothing else changes", lists `persistence/`,
     `web/listener.py` and `main.py` as unchanged, and the design's QC table does not include QC-62.
     The developer read it this way and left the question for the Tech Lead or the owner.
     (b) Yes. `docs/nfdr.md:461-463` says "The gate starts red … and the owner's answer has the first
     change after this revision repair them". Revision `1a9c8fb86` came after `691edf98b`, and this is
     the first change since. `found_while_walking.md` § *The rule* also says a defect found on a branch
     is fixed on that branch.
   - *Taken:* (b). It keeps the upstream record true as written. The plan's "Nothing else changes"
     describes behaviour, and the repair changes no behaviour (same suites, same results). Every edit is
     small and can be reverted on its own.
   - *Whose document:* the Tech Lead's (`tl_instruction.md`) and the owner's (QC-62's answer).
   - *If ruled the other way:* revert `2ac931bc2`. That commit is the whole repair, and nothing else on
     the branch depends on it.

## Placement

The parts table is `docs/SDD.md` § 3. Both pieces of logic are already in their owning part, so
nothing was moved:

- `pages.not_found_page`: `web`, which owns "building each whole HTML page". It is in `web/pages.py`.
- The `GET` fallback and the 404 status: `web`, which owns "the addresses of pages and actions". It is
  in `web/routes.py`. Whether a project exists is still answered by `application`
  (`Tracker.project`).

## Language resolution

- **Language:** Python, declared in `project.md` (`Languages: Python`). Chain step 1 answered.
- **Packet read:** `<CORE>/doctrine/engineering/languages/python/` — `quality_gates.md`,
  `conventions.md`, and `<CORE>/doctrine/engineering/testing_python.md` for Testing.
- **Applied:** the product installs Ruff and mypy, and QC-62 makes them gates. `quality_gates.md`
  § *What a product installs* lets a product do this. Those gates were the bar here, and they were
  repaired as described above. The code the change wrote follows the packet's conventions: annotated
  production functions (`not_found_page() -> str`, `_html(page: str, status: int = …) -> Response`), a
  leading underscore for internal helpers, a 100-column limit, and double quotes except in the one
  f-string that holds double quotes. The new test uses the file's own parser and no `monkeypatch`.
