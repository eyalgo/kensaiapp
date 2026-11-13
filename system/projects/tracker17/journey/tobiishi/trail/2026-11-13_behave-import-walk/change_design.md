# Change Design — the Behave folder gets its walk for QC-19's second clause

**Date:** 2026-11-13
**Category:** nfdr
**Behaviour:** changing
**Publishes text:** no
<!-- Decided by the CP-438 test: does this change put text in front of a person to read? `yes` names each place, as the person knows it. Otherwise write `no`. The chain reads the first word, which must be exactly `yes` or `no`. -->
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern file it routes (`toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`, and `<CORE>/doctrine/engineering/testing_python.md`)

---

## 1. Change Summary

A second walk joins the source walk in `tests/conftest.py`: `BehaveWalk`, reached through a new
`behave_walk_of` fixture shaped like `walk_of`. It reads every `.py` file under the product root's
`.behave/` by CP-798's rule, skipping only `.behave/.venv/` and any `__pycache__` folder, and hands
each one back as the existing `Module`, so `Module.imported()` is reused unchanged. A new layer-6
module, `tests/architecture/test_behave_imports.py`, holds QC-19's second clause over that folder. It
fails on any import whose first dotted piece is exactly `tests`, and fails, naming `.behave`, when the
entry exists but the walk reads nothing. It passes when the root holds no `.behave` entry, but its
real-product test fails if the product root holds no `.behave/` folder. The same module proves, on
planted roots, that the product-root walk misses both failing cases. `SourceWalk`, `walk_of`,
`Module` and every existing test stay as they are (CP-807). No product code, `.behave/` file or
product document changes.

---

## 2. Blast Radius

No new logic lands in a product part. Every piece is test code, and SDD § 3's parts table does not
cover test code: `tests/` is in the package unit (QC-1) but in no part's `Owns` (see Architect Review
Notes, kind (e)).

| Module | Status | What changes |
|---|---|---|
| `domain/` | Unchanged | — |
| `application/` | Unchanged | — |
| `persistence/` | Unchanged | — |
| `web/` | Unchanged | — |
| `main.py` | Unchanged | — |
| `errors.py` | Unchanged | — |
| `.behave/` | Unchanged | — (the request rules it out). It is read, never written |
| `tests/conftest.py` | Modified | New class `BehaveWalk` (the scenario folder's walk, CP-797 to CP-799) and new fixture `behave_walk_of`. The module docstring's source-walk paragraph gains a sentence naming the second walk and what it skips. `SourceWalk`, `walk_of`, `Module`, `dotted` and the skip constants do not change |
| `tests/architecture/test_behave_imports.py` | New | The import-from-`tests` check (CP-800 to CP-803), the real-product test (CP-804), and the planted-root cases, CP-806's proof that the root walk misses them included |
| `tests/architecture/test_imports.py` | Unchanged | `violations` is imported by the new module and does not change. Its QC-19 test keeps its verdict (CP-807) |
| `tests/architecture/test_shapes.py` | Unchanged | `PARTS` and `top_level_parts` are imported by the new module and do not change |
| `tests/architecture/test_source_walk.py` | Unchanged | Its seven tests run on `SourceWalk`, which does not change |
| `tests/architecture/test_trace.py` | Unchanged | Reads the new module's docstring (§ 4 hint 3) |

No transitive blast radius. No public surface changes: `BehaveWalk` and `behave_walk_of` are
additions that only the new module uses, and the root walk's output over any root stays as it is.

---

## 3. Sub-jobs

Both sub-jobs sit in one unit of test code, `tests/`. The cut below module granularity is forced by
one ordering edge: the new test module takes its walk from the fixture sub-job A adds. The suite is
green after each sub-job, so no atomic-landing edge exists between them.

### Sub-job A — `tests/conftest.py`, the scenario folder's walk
**Scope:** `BehaveWalk` and the `behave_walk_of` fixture, plus the docstring sentence. Nothing else
in the file changes.
**Exposes:**
- `BehaveWalk(root)`: `root` is a **product root**, never the `.behave` folder itself, and is kept as
  `.root`.
- `BehaveWalk.modules() -> list[Module]`:
  - Where `root` holds no entry named `.behave`, it returns `[]` and reads nothing (CP-797).
  - Otherwise it returns one `Module` for every `.py` file at any depth under `root/.behave`, in
    sorted path order, except files under `root/.behave/.venv/` and files with a path piece named
    exactly `__pycache__` below `.behave/` (CP-798). Every other subfolder is read, including
    `tests/`, `.behave/`, dot-named folders and near names.
  - Each `Module` has `path` relative to the **product root** (so it begins `.behave/`), `part` set
    to the fixed string `.behave`, and `tree` set to the parsed file.
  - Where the entry exists but nothing is read, it raises `AssertionError` with a message that
    contains `.behave`. That covers no `.py` file, `.py` files only where the skip rule applies, and
    an entry that is a plain file and not a folder (CP-799).
- `behave_walk_of` fixture: returns a builder `(root: Path | None = None) -> BehaveWalk`. With no
  root, the builder uses the product root (`TESTS_DIRECTORY.parent`), as `walk_of` does.
**Depends on:** none

### Sub-job B — `tests/architecture/test_behave_imports.py`, the check and its proof
**Scope:** the new layer-6 module. It holds the check, the real-product test and every planted-root
case in § 5.
**Exposes:** nothing outside this module. Inside it:
- `tests_imports(walk) -> list[str]` returns one `"<module.path>: <name>"` entry for every name
  `Module.imported()` yields whose first dotted piece is exactly `tests`, across every module the
  walk returns. The shape is `violations`'s. The list is empty when the walk returns no module.
- One helper holds the real-product check, so a test can point it at another root. It is handed a
  `BehaveWalk`. It asserts that `walk.root / ".behave"` is a folder, with a message naming `.behave`,
  and that `tests_imports(walk) == []`.
**Depends on:** Sub-job A (needs `behave_walk_of`, `BehaveWalk.root` and `BehaveWalk.modules()`).
It also uses `walk_of`, `PARTS`, `top_level_parts` and `violations`, which already exist.

**Build sequence:**
```
Start: Sub-job A
After A: Sub-job B
```

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — `BehaveWalk` | (1) **Three states, told apart before any glob.** The entry is absent, or present and a folder, or present and not a folder. Glob only in the folder case. A plain-file `.behave` reads nothing and goes straight to the empty-walk assertion. Do not rely on `rglob` below a file to answer empty on Python 3.11. (2) **The skip reads the pieces of the path relative to `.behave/`, not relative to the product root.** Relative to the root, every first piece is `.behave`. The first piece is matched against `.venv` and every piece against `__pycache__`, both by exact equality, so `.venvs` and `__pycache__2` are read and `features/.venv/` is read. (3) **`part` is the constant `.behave`, never a path piece.** `Module.imported()` reports a relative import as the module's part. With a piece-derived part, `.behave/tests/y.py` would have part `tests`, and its `from . import x` would read as an import from `tests`, against CP-801. The constant's first dotted piece is empty, so a relative import can never match. (4) Keep to Python 3.11 (QC-60). `Path.exists(follow_symlinks=...)`, `Path.walk` and `relative_to(..., walk_up=...)` are 3.12. |
| A — `behave_walk_of` | None |
| B — `tests_imports` and the real-product helper | (1) **Match on `name.split(".")[0] == "tests"`, never on a prefix.** `testsuite`, `tests_util` and `mytests` must miss. (2) `Module.imported()` yields both `tests` and `tests.conftest` for `from tests import conftest`. Both entries are listed, so a test asserts which modules and names appear, never how many entries the list holds. `import os, tests.x` yields `tests.x` once. |
| B — the planted-root tests | (1) Plant files as `test_source_walk.py`'s `_plant` does: each relative path under `tmp_path`, parents first. For the CP-806 roots, plant the same six root files `test_source_walk.py` plants, under this module's own constant, since that one is module-private. (2) Take `PARTS` and `top_level_parts` from `test_shapes`, and `violations` from `test_imports`, by import, as `test_source_walk.py` already imports from `test_shapes`. (3) **The module docstring names SRS NFR-9 and AC-5, with NFDR QC-19 as the clause, and spells no planted path.** `test_trace.py` resolves every path-shaped token in a test module's docstring against the product root, and fails a test module that names no requirement. Describe planted files in words, or name them only in function docstrings and code. (4) The real-product case runs the helper over `behave_walk_of()`. Its pointed-elsewhere case runs the same helper over `behave_walk_of(tmp_path)`, where `tmp_path` holds no `.behave`, under `pytest.raises(AssertionError)`. |

---

## 5. Test Additions

Every new test is layer 6. It walks real files, either the product's own `.behave/` or files written
under `tmp_path` as the planted-root tests in `test_source_walk.py` do. It hands in no fake: the walk's
subject is files on disk, and its root arrives through `behave_walk_of(root)` or `walk_of(root)`. All
rows are in `tests/architecture/test_behave_imports.py`. "Fails" for the import cases means
`tests_imports(...)` is non-empty and holds the named entries. For the empty cases it means
`modules()` raises `AssertionError` with `.behave` in its message.

| Sub-job | Test file | Layer | Fakes handed in | What to add / modify |
|---|---|---|---|---|
| A + B | `test_behave_imports.py` | 6 — Architecture | none — real files under `tmp_path` | **CP-797:** a root with no `.behave` entry. `modules()` is `[]` and `tests_imports(...)` is `[]`, with no assertion raised |
| A + B | as above | 6 — Architecture | none, as above | **CP-800, CP-802, Example 2 and 3:** `.behave/features/x.py` holding `from tests import conftest`. The result holds an entry for `.behave/features/x.py` naming `tests` or `tests.conftest`. Then the file is rewritten without that line, kept on disk, and the result is `[]` |
| A | as above | 6 — Architecture | none, as above | **CP-799, empty folder:** `.behave/` exists and is empty. `modules()` raises, and the message contains `.behave` |
| A | as above | 6 — Architecture | none, as above | **CP-798, CP-799, only skipped files:** `.py` files only under `.behave/.venv/` and `.behave/features/__pycache__/`. `modules()` raises, and the message contains `.behave` |
| A | as above | 6 — Architecture | none, as above | **CP-799, plain file:** `.behave` written as a plain file. `modules()` raises, and the message contains `.behave` |
| A + B | as above | 6 — Architecture | none, as above | **CP-798, `.venv` skipped:** `.behave/.venv/lib/pkg.py` holding `import tests`, beside a clean `.behave/features/a.py`. The result is `[]`, and no walked path begins `.behave/.venv/` |
| A + B | as above | 6 — Architecture | none, as above | **CP-798, named and dot folders read:** `.behave/tests/y.py` holding `from tests import conftest`, and `.behave/.hidden/z.py` holding `import tests`. Both paths are listed. These are two Examples, and one test or two is the plan's call |
| A + B | as above | 6 — Architecture | none, as above | **CP-798, near names and nested names read (rule-implied edge):** `.behave/.venvs/a.py`, `.behave/features/__pycache__2/b.py`, `.behave/features/.venv/c.py` and `.behave/.behave/d.py`, each holding `import tests`. All four paths are listed |
| A + B | as above | 6 — Architecture | none, as above | **CP-800, inside a function:** `.behave/features/a.py` with `import tests` inside a function body. It is listed |
| A + B | as above | 6 — Architecture | none, as above | **CP-800, the remaining forms (rule-implied edge):** `import tests.x as y`, `from tests.x import y`, and `import tests` under an `if`, each in its own module. Each module is listed |
| A + B | as above | 6 — Architecture | none, as above | **CP-800, multi-name import:** `.behave/features/a.py` with `import os, tests.x`. It is listed with `tests.x`, and no entry names `os` |
| A + B | as above | 6 — Architecture | none, as above | **CP-802, every site in one run:** `a.py` with `import tests.x` and `b.py` with `from tests.y import z`, both in `.behave/features/`. One call lists both modules |
| A + B | as above | 6 — Architecture | none, as above | **CP-801:** `.behave/features/a.py` with `import testsuite`, `from tests_util import x` and `from .tests import y`. The result is `[]`. Add `from . import x` in `.behave/tests/w.py` beside it. It is still `[]`, which holds § 4 hint A(3) by construction |
| A + B | as above | 6 — Architecture | none, as above | **CP-803:** `.behave/features/a.py` with `from behave import given`, `import httpx`, `import subprocess` and `from server_way_in import request_page`. The result is `[]` |
| A + B | as above | 6 — Architecture | none — the product's own `.behave/`, read only | **CP-804, the real product:** the helper over `behave_walk_of()` passes. It asserts the folder is there and finds no import from `tests`. `modules()` asserts it read at least one module. No count is asserted (Architect Review Notes) |
| A + B | as above | 6 — Architecture | none — real files under `tmp_path` | **CP-804, pointed elsewhere:** the same helper over `behave_walk_of(tmp_path)`, a root with no `.behave`, raises `AssertionError` |
| B | as above | 6 — Architecture | none, as above | **CP-806:** two roots, each holding the six root files: one adds `.behave/features/x.py` with `from tests import conftest`, the other an empty `.behave/`. On each, `violations(walk_of(root), part) == []` for every part in `PARTS`, and `top_level_parts(walk_of(root)) == PARTS`. On the same roots the new check fails: the first lists `.behave/features/x.py`, and the second raises naming `.behave` |
| — | `test_source_walk.py`, `test_imports.py`, `test_shapes.py` | 6 — Architecture | — | No change. **CP-807** is their existing tests over the unchanged `SourceWalk`: the seven source-walk tests, `test_nothing_outside_tests_imports_third_party_or_tests`, `test_each_walk_fails_when_its_directory_holds_no_module` and `test_the_top_level_parts_are_the_five_the_sdd_names` |
| — | none — a disposable-clone mutation run | — | — | **CP-805** is a verification run, not a suite test. In a disposable clone at the commit under test, append `import tests.conftest` to `.behave/features/command_way_in.py` and run `pytest tests/architecture/`. Only the CP-804 real-product test fails. The QC-19 and QC-1 tests pass |
| — | the card's `Test command:` | — | — | **CP-796:** the new module sits under `tests/architecture/` with a `test_` name, so `pytest tests/` collects it. Both suites pass on the commit under test |

Coverage by rule, beyond the rows above:

- **QC-62** (Ruff format and lint) binds the new module and the edited `conftest.py`. That is a gate
  command, not a test.
- **CP-805's "only test that fails"** holds by construction. No existing architecture test reads
  `.behave/` (spec, Verified Claims: 92 passed with the mutation at the base).

**What the change stops proving.** No assertion is retired. No existing test or helper changes.

---

## Testing the change from outside the code

None. The way in the NFDR records is a browser (`docs/nfdr.md` § 9, `**Behave way in:** browser`),
and this change adds no behaviour of the tracker. It adds a layer-6 check that reads the scenario
folder's source, which no page shows. The request also rules out any `.behave/` change.

---

## Records this change makes false

- `docs/nfdr.md` § 1.2, preamble — "Every entry is verified by one layer-6 test that walks the
  imports of every module on disk" goes false for QC-19 once this lands, because two layer-6 tests
  then verify it: the product-root walk's, and the new walk of `.behave/` for its second clause. →
  It should say each entry is verified by a layer-6 import walk, and that QC-19's second clause over
  `.behave/` has a walk of its own, which fails as the others do when it finds nothing.
- `docs/nfdr.md` § 1.1, QC-1, *verified by* — "The source walk under it, which the import and reach
  walks of §§ 1.2, 1.3, 3 and 8 share" goes false once this lands. One § 1.2 import walk, QC-19's
  walk of `.behave/`, does not share it. → It should name that walk as the exception: it reads
  `.behave/` by its own rule, skipping only `.behave/.venv/` and `__pycache__`.

Read also, and nothing false found: `docs/adr/` (ADR-0001 to ADR-0016 and the index), `docs/fdr.md`,
`docs/SDD.md` § 3, `docs/what_left.md`, and QC-19's own *verified by*. That tail describes the walk
this change builds and becomes true with it. Naming the test and dating the entry is the Principal
Architect's (spec, Out of Scope). RN-66 and RN-78 are dated notes and stay true.

---

## Architect Review Notes

- **(e) Test code has no owning part:** the walk goes in `tests/conftest.py` beside `SourceWalk`, and
  the check goes in a new layer-6 module in `tests/architecture/`. SDD § 3's `Owns` column covers the
  five product parts. `tests/` is in the package unit (QC-1) but is no part. The location follows
  `testing_python.md` § Layer 6 (`tests/architecture/test_<property>.py`) and the request.
- **(c) The request's "reusing `SourceWalk`" is not followed. `Module.imported()` is:** the spec made
  the method this stage's (Locked Answers, Gap 1). `SourceWalk` rooted at `.behave/` skips
  `.behave/tests/` and `.behave/.behave/`, which CP-798 reads. It also derives `part` from the first
  path piece, so a relative import in `.behave/tests/` would read as `tests`, which CP-801 passes.
  Changing `SourceWalk` to fit would change the root walk, which CP-807 holds as it is. So the
  scenario folder gets its own small walk, which yields the existing `Module` and reuses
  `imported()` unchanged.
- **(b) The walk lives in `conftest.py`, reached by a fixture:** the suite imports nothing from
  `conftest` at run time (the e2e modules do so only under `TYPE_CHECKING`, and `tests/e2e/` has its
  own `conftest.py`). A fixture is how `Module` and `SourceWalk` already reach the architecture
  tests, so `behave_walk_of` mirrors `walk_of`.
- **(b) CP-797 and CP-804 split across two surfaces:** the walk returns `[]` on an absent entry, and
  the real-product helper alone asserts that the folder is there. The general check then passes on a
  root with no `.behave` (CP-797), and the real-product test cannot pass by reading nothing (CP-804,
  NFDR § 9).
- **(b) The real-product test asserts no module count:** the spec counts eight modules today, but
  `testing_python.md` § Layer 6 says "Enumerate from disk, never from a list". `modules()` asserting
  at least one, plus the folder-present assertion, is the bar. A ninth scenario module must not fail
  the suite.
- **(b) CP-801 realized by construction:** `part` is the constant `.behave` (§ 4 hint A(3)), and §
  5's CP-801 row adds `from . import x` inside `.behave/tests/` to prove it. Without that row, a walk
  that set `part` from the path would pass every Example and still break the rule.
- **(b) Duplicate entries per statement are allowed:** `from tests import y` lists both `tests` and
  `tests.y`, as `violations` already lists them for the root walk. CP-802 asks for every import and a
  dotted name beginning `tests`, and both entries meet it. Tests assert what appears, not how many
  entries there are.
- **(b) Rule-implied rows added:** the near-name and nested-name row (CP-798) and the
  remaining-forms row (CP-800) cover forms the rules state and the Examples omit.
- **(d) Sub-jobs below module granularity:** both files are in `tests/`. The cut is the one ordering
  edge, the fixture before the module that uses it (§ 3).
- **(d) `Testing the change from outside the code` is `None` though a way in is recorded:** the
  browser is recorded, but this change adds no tracker behaviour, and the request forbids `.behave/`
  changes.
- **Packet check, no conflict:** `conventions.md` § Constructs, "A module is given its
  collaborators", is met. `BehaveWalk` is handed its root through its constructor, which is the seam
  every planted-root case uses. Reading the files under that root is the walk's subject, as
  `testing_python.md` § Layer 6 says. The new tests are layer 6, not unit tests, and write only under
  `tmp_path`. No `deferred_decisions.md` entry is owed.
- **QC-12 review, pass:** the change adds no part. It adds one test walk and one layer-6 module, both
  paid for by QC-19's second clause.
- **QC-60 review, pass:** the walk and the tests use `pathlib`, `ast` and pytest's `tmp_path`, all in
  Python 3.11. § 4 hint A(4) names the 3.12-only calls to avoid.
- **QC-41 review, pass:** the change reads, holds and writes no secret.
- **QC-39, development-design moment — not owed:** the change touches neither `.behave/pyproject.toml`
  nor `.behave/uv.lock`.
- **QC-40 review, every-review moment — packages, met:** all 27 pinned packages in `uv.lock` and
  `.behave/uv.lock` (pytest 9.1.1, ruff 0.16.10, mypy 2.4.0, playwright 1.65.1, behave 1.3.3,
  httpx 0.28.1 and what they pull in) were checked against the OSV database's PyPI advisories on
  2026-11-13. None has an advisory. No dependency is added or moved.
- **QC-40 review, every-review moment — browser build, not blocking, owed by 2026-12-11:** the build
  `playwright==1.65.1` installs is Chromium 158.0.8127.18. The finding stands as the earlier review
  this day recorded it. The vendor's Stable Channel Update for Desktop of 2026-11-11 fixes five
  **Critical** advisories, and the vendor does not say whether 158.0.8127.18, first shipped to early
  stable on 2026-11-04, carries those fixes, so this review reads it as affected. The vendor's posts
  since then, through 2026-11-12, add no Critical advisory for desktop Chrome. Early stable now sits
  at 158.0.8127.36/.37. The advisories are 2 days old, inside QC-40's 30-day window, so they do not
  block this change. The fix is owed within 30 days of 2026-11-11: the pin moves, or the owner records
  a dated exception.
- **QC-40 review, package feed — down, moment still owed:** the account checking has admin on the
  repository that holds tracker17. The Dependabot alerts endpoint answered "Dependabot alerts are
  disabled for this repository" (403), and the asynchronous SBOM export answered 404. As QC-40 says,
  that is a feed that is down: this review records the feed as down and the moment as still owed, and
  raises no discrepancy.
