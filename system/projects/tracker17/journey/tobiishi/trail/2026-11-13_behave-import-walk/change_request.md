# Change request — 2026-11-13_behave-import-walk

---

**Request:** Add a layer-6 test in `products/tracker17/tests/architecture/` that walks `products/tracker17/.behave/` as its own root, reusing `SourceWalk` and `Module.imported()`, and checks NFDR QC-19's second clause. It fails on an import from `tests` (`import tests.x`, `from tests import y`, `from tests.x import y`) in any module there, and it fails, naming the folder, when `.behave/` exists but holds no `.py` file. When there is no `.behave/` folder it reads nothing and passes. On the real folder, which holds four modules in `features/` plus its `steps/`, it passes. It checks only those two clauses: third-party imports in `.behave/` (`behave` is imported there) stay allowed, and the QC-19 test and the QC-1 comparison keep passing. The root walk's by-name skip is already sealed (item 1), so `SourceWalk` still skips `tests/`, `.behave/`, `.venv/` and `__pycache__` from the product root and the real root still walks to exactly the five parts. No product code, `.behave/` file or document changes. Proof is by cases under `tmp_path`: a planted `.behave/features/x.py` with `from tests import conftest` fails and passes once the import is removed; an empty `.behave/` fails; no `.behave/` passes. A planted root also shows the root `SourceWalk` would not catch the first two cases. Sizing: one capability (QC-19's second clause gets its walk), one merge; the acceptance boundary is the station's reached-when 1 to 4.

**Category:** nfdr
**Behaviour:** changing
**Classified because:** the station adds a new check (a layer-6 walk of `.behave/`) that decides pass or fail on QC-19's second clause, so what an enforcement command reports changes, which is `changing` for an `nfdr` change; reached-when 1 to 3 name the new failing cases.

---

**Sealed:** 2026-11-13 — accepted; merged to `main` via `--no-ff`.
Environment: owners-mac — no CI
