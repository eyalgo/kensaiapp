# Change Spec — the Behave folder gets its walk for QC-19's second clause

**Date:** 2026-11-13
**Category:** nfdr
**Behaviour:** changing
**Request:** Add a layer-6 test in `products/tracker17/tests/architecture/` that walks `products/tracker17/.behave/` as its own root, reusing `SourceWalk` and `Module.imported()`, and checks NFDR QC-19's second clause. It fails on an import from `tests` (`import tests.x`, `from tests import y`, `from tests.x import y`) in any module there, and it fails, naming the folder, when `.behave/` exists but holds no `.py` file. When there is no `.behave/` folder it reads nothing and passes. On the real folder, which holds four modules in `features/` plus its `steps/`, it passes. It checks only those two clauses: third-party imports in `.behave/` (`behave` is imported there) stay allowed, and the QC-19 test and the QC-1 comparison keep passing. The root walk's by-name skip is already sealed (item 1), so `SourceWalk` still skips `tests/`, `.behave/`, `.venv/` and `__pycache__` from the product root and the real root still walks to exactly the five parts. No product code, `.behave/` file or document changes. Proof is by cases under `tmp_path`: a planted `.behave/features/x.py` with `from tests import conftest` fails and passes once the import is removed; an empty `.behave/` fails; no `.behave/` passes. A planted root also shows the root `SourceWalk` would not catch the first two cases. Sizing: one capability (QC-19's second clause gets its walk), one merge; the acceptance boundary is the station's reached-when 1 to 4.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened; no rule here renders a language-level fact

---

## Change Summary

NFDR QC-19 says no module outside `tests/` imports from `tests/`, and that this clause binds the
Behave scenario folder `.behave/`. The product-root walk skips `.behave/` by name, so nothing checks
the folder today. This change adds the layer-6 check QC-19's *verified by* names for it. The check
fails on an import from `tests` anywhere in the folder, and fails while the folder exists but holds
no module. Paths below are relative to the product root, which `project.md` `Product path:` names.

---

## Rules

### What the check is and where it runs

- **CP-796:** A new test module under `tests/architecture/` checks QC-19's second clause over
  `.behave/`. It is the walk QC-19's *verified by* names: "a walk of that folder that fails on an
  import from `tests` and, while the folder exists, on finding no module in it" (NFDR QC-19). It
  runs in `pytest tests/`, so the card's `Test command:` gates it at the suite (NFDR § 10, the
  QC-19 row).
- **CP-797:** Where the product root holds no entry named `.behave`, the check reads nothing and
  passes. The product root may hold the folder and need not (NFDR QC-1, "The root may also hold
  `.behave/`").

### Which files the check reads

- **CP-798:** The check reads every `.py` file at any depth under `.behave/`, with two exceptions:
  files under `.behave/.venv/`, and files under any folder named exactly `__pycache__`. Every
  other subfolder is read, whatever its name. That includes a folder whose name begins with a dot,
  and folders named `tests` or `.behave` inside `.behave/`. A near name such as `.venvs` or
  `__pycache__2` is read too.
- **CP-799:** Where `.behave` exists but the check finds no file to read under it, the check fails,
  and its failure message contains `.behave`. This covers three cases:
  - no `.py` file at all;
  - `.py` files only under `.behave/.venv/` or a `__pycache__` folder;
  - `.behave` is a plain file and not a folder.

### What fails, and what passes

- **CP-800:** An import from `tests` fails the check. An import from `tests` is an import statement
  whose absolute module name has `tests` as its first dotted piece, exactly. The statement may sit
  anywhere in the module: at top level, inside a function or class, or under a condition. These
  forms all count:
  - `import tests`
  - `import tests.x`
  - `import tests.x as y`
  - `from tests import y`
  - `from tests.x import y`
  - `import os, tests.x`, which counts once, for `tests.x`
- **CP-801:** These are not imports from `tests` and pass:
  - a name whose first piece merely starts or ends with `tests`, such as `testsuite`, `tests_util`
    or `mytests`;
  - a relative import such as `from . import x` or `from .tests import y`, which names a module
    inside `.behave/` itself.
- **CP-802:** A failure lists every import from `tests` the check found in that run, not only the
  first. Each entry gives the module's path from the product root and a dotted name beginning
  `tests` for what it imported. For `from tests import conftest` in `.behave/features/x.py`, that is
  the path and `tests` or `tests.conftest`.
- **CP-803:** No other import fails this check. A third-party import (`behave`, `httpx`,
  `playwright`), a standard-library import, and an import of a sibling module by name (`from
  server_way_in import request_page`) all pass. QC-19's first clause exempts `.behave/`. The check
  applies no other NFDR entry to the folder.

### On the real product

- **CP-804:** On the real product the check passes, reading the modules `.behave/` holds. Today
  those are four in `.behave/features/` and four in `.behave/features/steps/`, and none imports from
  `tests`. The test that runs the check on the real product fails if that product root holds no
  `.behave/` folder. A check aimed at the wrong root therefore cannot pass that test by reading
  nothing (NFDR § 9, "Every layer-6 walk fails when the directory it walks holds no module, so a walk
  rooted at the wrong path, or run before the module exists, cannot pass by finding nothing").
- **CP-805:** A disposable clone at the commit under test can have `import tests.conftest` or
  `from tests.x import y` added to a real `.behave/features/*.py`. When it does, the new check fails,
  and it is the only test in `tests/architecture/` that fails. `test_nothing_outside_tests_imports_third_party_or_tests`
  (QC-19) and `test_the_top_level_parts_are_the_five_the_sdd_names` (QC-1) keep passing.

### The proof that the root walk does not already catch it

- **CP-806:** The new tests prove two failing cases, each on a root planted under `tmp_path` that
  also holds the six root names the QC-1 comparison expects:
  - `.behave/features/x.py` containing `from tests import conftest`;
  - an empty `.behave/`.

  On each of those roots, the product-root walk the QC-19 test uses reports no violation, and its
  parts are still exactly `domain`, `application`, `persistence`, `web`, `main` and `errors`.

### Left as it is

- **CP-807:** The product-root source walk is unchanged. It skips `tests/`, `.behave/` and `.venv/`
  by exact name at the product root only, and `__pycache__` at any depth (NFDR QC-1). These tests
  pass unchanged:
  - the seven in `tests/architecture/test_source_walk.py`;
  - `test_nothing_outside_tests_imports_third_party_or_tests`;
  - `test_each_walk_fails_when_its_directory_holds_no_module`;
  - `test_the_top_level_parts_are_the_five_the_sdd_names`, whose real-root set is `domain`,
    `application`, `persistence`, `web`, `main` and `errors`.

---

## Examples

| Scenario | Expected behavior | Rule |
|---|---|---|
| Root under `tmp_path` with no `.behave` entry | the check passes, reading nothing | CP-797 |
| Root with `.behave/features/x.py` containing `from tests import conftest` | the check fails, listing `.behave/features/x.py` with `tests` or `tests.conftest` | CP-800, CP-802 |
| The same root, with that line removed (the file kept) | the check passes | CP-800 |
| Root with `.behave/` that exists and is empty | the check fails; the message contains `.behave` | CP-799 |
| Root whose `.behave/` holds `.py` files only under `.behave/.venv/` and `.behave/features/__pycache__/` | the check fails; the message contains `.behave` | CP-798, CP-799 |
| Root where `.behave` is a plain file | the check fails; the message contains `.behave` | CP-799 |
| `.behave/.venv/lib/pkg.py` containing `import tests`, beside a clean `.behave/features/a.py` | the check passes | CP-798 |
| `.behave/tests/y.py` containing `from tests import conftest` | the check fails, listing `.behave/tests/y.py` | CP-798, CP-800 |
| `.behave/.hidden/z.py` containing `import tests` | the check fails, listing `.behave/.hidden/z.py` | CP-798, CP-800 |
| `.behave/features/a.py` with `import tests` inside a function body | the check fails | CP-800 |
| `.behave/features/a.py` with `import os, tests.x` | the check fails, listing `tests.x` | CP-800 |
| `.behave/features/a.py` with `import tests.x` and `.behave/features/b.py` with `from tests.y import z` | one run fails and lists both modules | CP-802 |
| `.behave/features/a.py` with `import testsuite`, `from tests_util import x`, `from .tests import y` | the check passes | CP-801 |
| `.behave/features/a.py` with `from behave import given`, `import httpx`, `import subprocess`, `from server_way_in import request_page` | the check passes | CP-803 |
| The real product's tree | the check passes, having read the eight modules under `.behave/features/` | CP-804 |
| The test that checks the real product, pointed at a root that holds no `.behave/` | that test fails | CP-804 |
| Disposable clone with `import tests.conftest` appended to `.behave/features/command_way_in.py` | `pytest tests/architecture/` fails on the new check alone; the QC-19 and QC-1 tests pass | CP-805 |
| The two planted failing roots, given to the product-root walk | no QC-19 violation, parts equal the six names | CP-806 |
| The real product root, given to the product-root walk | the six names; the seven source-walk tests, the QC-19 test and the empty-walk test pass | CP-807 |
| The card's `Test command:` on the commit under test | both suites pass, `pytest tests/` including the new check | CP-796 |

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| CP-807: the product-root walk's tests pass at the base, unchanged | `pytest -q -p no:cacheprovider --basetemp <scratch>` in the product worktree on `tests/architecture/test_source_walk.py`, `test_imports.py::test_nothing_outside_tests_imports_third_party_or_tests`, `test_imports.py::test_each_walk_fails_when_its_directory_holds_no_module` and `test_shapes.py::test_the_top_level_parts_are_the_five_the_sdd_names`, run with the worktree's own environment and a private temp folder | `d9a66ad9d`: 10 passed |
| CP-807: the real-root set compared for QC-1 is six names | `tests/architecture/test_shapes.py:20` `PARTS = {"domain", "application", "persistence", "web", "main", "errors"}`, and `:135-137`, which asserts `top_level_parts(walk_of()) == PARTS` | `d9a66ad9d`: six names, matching QC-1's "five parts … plus `errors.py`" |
| CP-806: the product-root walk does not catch either planted failing case | a script outside the repository builds two roots, each holding the six names. One adds `.behave/features/x.py` with `from tests import conftest`, the other an empty `.behave/`. It runs `SourceWalk(root)` from `tests/conftest.py` and `violations` from `tests/architecture/test_imports.py` over every part, then `top_level_parts` from `test_shapes.py` | `d9a66ad9d`: both roots give violations `[]` and parts equal to `PARTS` |
| CP-805: no current architecture test catches an import from `tests` in `.behave/` | disposable clone at `d9a66ad9d`, `uv sync --locked --offline` in the product, two lines `import tests.conftest` and `from tests.x import y` appended to `.behave/features/command_way_in.py`, then `pytest -q -p no:cacheprovider --basetemp <scratch> products/tracker17/tests/architecture/`; clone removed afterwards | `d9a66ad9d`: 92 passed |
| Locked Answer 1: the product-root `SourceWalk`, given `.behave/` as its root, skips `.behave/tests/` | the same scripted run: `SourceWalk(root / ".behave").modules()` over a `.behave/` holding `tests/y.py` (with `from tests import conftest`) and `features/z.py` | `d9a66ad9d`: reads only `features/z.py` |
| CP-804: the real `.behave/` holds eight modules and none imports from `tests` | `find .behave -name '*.py'` and a grep of every `import`/`from` line under `.behave/features/` | four in `features/` (`browser_way_in.py`, `command_way_in.py`, `environment.py`, `server_way_in.py`), four in `features/steps/`. Third-party: `behave`, `httpx`, `playwright.sync_api`. Standard library and sibling modules otherwise. No `tests` |
| Locked Answer 2: `.behave/` keeps its environment and compiled files out of the repository | `.behave/.gitignore` | `.venv/` and `__pycache__/` |
| Locked Answer 4: the product already treats a plain-file `.behave` as a finding | `tests/architecture/test_pins.py:208-228`, `make_behave_a_plain_file` in `test_a_missing_or_unreadable_manifest_is_found` (CP-774) | `d9a66ad9d`: that case asserts a finding |

---

## Out of Scope

- No product code, no file under `.behave/` and no product document changes. That includes QC-19's
  *verified by* tail, whose wording is the Principal Architect's to update once this lands.
- QC-19's first clause over `.behave/`. Third-party imports there stay allowed, because QC-19
  exempts the folder.
- Every other NFDR entry over `.behave/`, including QC-13 to QC-18 and QC-43. This check applies
  none of them.
- Imports that are not import statements, such as `importlib.import_module("tests")`,
  `__import__("tests")` or `exec`. The check reads import statements only, as the product-root
  QC-19 walk does.
- The product-root walk's by-name skip. That was sealed by the earlier change on this station
  (item 1), and CP-807 holds it as it is.
- Running the Behave scenarios (layer 7), and the pins and lock checks over `.behave/` (QC-39).

---

## Locked Answers (the divergence record — self-review 2026-11-13)

- **Gap 1 — the request's "reusing `SourceWalk` and `Module.imported()`" is not a rule (c):**
  the spec states which files the check reads (CP-798) and leaves the method to
  `development-design`. *Reason:* the product-root walk, given `.behave/` as its root, skips
  `.behave/tests/`, `.behave/.behave/` and `.behave/.venv/` (Verified Claims). QC-19's second clause
  binds every module under `.behave/`, and a module in `.behave/tests/` is outside the product's
  `tests/`. Reusing the walk exactly as it stands would leave those files unread. No record fixes
  which walk this check uses. QC-1 fixes the product-root walk's skips only.
- **Gap 2 — `.behave/.venv/` and `__pycache__` are not read (b):** *Reason:* `.behave/.venv/` is
  the folder's own installed environment. SDD § 4 RT-4 says `uv run --locked behave`, typed inside
  `.behave/`, builds it. It holds third-party packages, not the folder's code, and
  `.behave/.gitignore` lists it with `__pycache__/`. Without this skip, a machine that had run the
  scenarios would fail the suite on code the product does not own. The product-root walk skips
  `.venv/` and `__pycache__` for the same reason (QC-1).
- **Gap 3 — every other subfolder of `.behave/` is read, whatever its name (b):** *Reason:* QC-19
  binds every module outside the product's `tests/`, and a check that skipped a subfolder by name
  would let a module there import from `tests` unseen. That is the gap QC-1's own history records for
  the dot-folder skip.
- **Gap 4 — a `.behave` that exists only as a plain file, or holds `.py` files only where CP-798
  does not read, fails as empty (b):** *Reason:* the request fails an existing `.behave/` that holds
  no module. A plain file and a folder holding only skipped files both leave the check nothing to
  read, and NFDR § 9 fails every layer-6 walk that finds nothing. The QC-39 pins test already treats
  a plain-file `.behave` as a finding (CP-774). Failing is the safe choice and can be reversed.
- **Gap 5 — what counts as an import from `tests` (b):** the request names three forms. CP-800
  adds bare `import tests`, `import … as`, a name inside a multi-name import, and an import inside a
  function or under a condition. CP-801 excludes near names and relative imports. *Reason:* QC-19
  forbids any import from `tests/`, and each added form is one. A relative import inside `.behave/`
  names a module of that folder, never the product's `tests/`. A near name such as `testsuite` is a
  different module.
- **Gap 6 — a failure lists every offending import with its module path and dotted name (b):**
  *Reason:* the request says the check fails but not what the failure shows. Listing every import
  in one run, each with module and name, shows the reader every site to fix. The product-root QC-19
  test reports `(path, name)` the same way.
- **Gap 7 — the real-product test fails when that root holds no `.behave/` (e):** the request asks
  only that the real folder passes. *Reason:* NFDR § 9 requires every layer-6 walk to fail when it
  finds nothing, "so a walk rooted at the wrong path … cannot pass by finding nothing". CP-797 lets
  the check pass on a missing folder. Without CP-804, a check aimed at the wrong root would pass on
  the real product while reading nothing.
- **Gap 8 — "exactly the five parts" is stated as the six names the QC-1 comparison holds (g):**
  *Reason:* at the base, `test_the_top_level_parts_are_the_five_the_sdd_names` compares the real
  root to `domain`, `application`, `persistence`, `web`, `main` and `errors` (Verified Claims). QC-1
  counts five parts plus `errors.py`. CP-807 names the set the test asserts, so the unchanged-rule
  claim can be checked as written.
