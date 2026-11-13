# Change Design — the source walk skips by name

**Date:** 2026-11-13
**Category:** nfdr
**Behaviour:** changing
**Publishes text:** no
<!-- Decided by the CP-438 test: does this change put text in front of a person to read? `yes` names each place, as the person knows it. Otherwise write `no`. The chain reads the first word, which must be exactly `yes` or `no`. -->
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern file it routes (`toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`, and `<CORE>/doctrine/engineering/testing_python.md`)

---

## 1. Change Summary

The source walk the layer-6 tests share (`SourceWalk._all` in `tests/conftest.py`, reached through the
`walk_of` fixture) stops leaving out every file with a path piece that begins with a dot. Instead it
leaves out, by exact name, a file whose first piece under the root is `tests`, `.behave` or `.venv`,
and a file with a piece named `__pycache__` at any depth (CP-785, CP-786). A new layer-6 module,
`tests/architecture/test_source_walk.py`, builds roots under `tmp_path` and proves that a code-holding
dot-folder now fails QC-1's comparison while the named folders stay skipped (CP-788 to CP-790). No
product code, product document or `.behave/` file changes. The walk's surface (`walk_of`,
`SourceWalk.modules`, `Module`) keeps its signatures, and its verdict over the product root stays
exactly `PARTS` (CP-787).

---

## 2. Blast Radius

No new logic lands in a product part. Every piece is test code, which SDD § 3's parts table does not
cover: `tests/` is in the package unit and is no part's `Owns` (see Architect Review Notes, kind (e)).

| Module | Status | What changes |
|---|---|---|
| `domain/` | Unchanged | — |
| `application/` | Unchanged | — |
| `persistence/` | Unchanged | — |
| `web/` | Unchanged | — |
| `main.py` | Unchanged | — |
| `errors.py` | Unchanged | — |
| `.behave/` | Unchanged | — (the request rules it out) |
| `tests/conftest.py` | Modified | `SourceWalk._all`: the skip test becomes two exact-name checks, the first piece against `tests`, `.behave` and `.venv`, and any piece against `__pycache__`. The leading-dot test goes. The `SourceWalk` docstring and the module docstring's source-walk paragraph say what is skipped, by name, in place of "a hidden folder". No signature changes |
| `tests/architecture/test_source_walk.py` | New | The tests for CP-786 and CP-788 to CP-790, over roots built under `tmp_path` |
| `tests/architecture/test_shapes.py` | Unchanged | Uses `walk_of`. Its QC-1 test keeps its verdict over the product root (CP-787). `PARTS` and `top_level_parts` are imported by the new module and do not change |
| `tests/architecture/test_imports.py` | Unchanged | Uses `walk_of` over the product root. It sees the same modules, because the product root holds no `.py` outside the six parts and the skipped folders (spec, Verified Claims) |
| `tests/architecture/test_reach.py` | Unchanged | Uses `walk_of` over the product root, as above. Its own walk over `tests/` (`:217-218`) is a different walk and stays as it is |

No transitive blast radius beyond these. The walk's public surface is unchanged, and the only change
in what it reports over the product root would be a `.py` file in a dot-folder other than `.behave/`
and `.venv/`. The product root holds none.

---

## 3. Sub-jobs

Omitted. One unit of test code changes: the walk in `tests/conftest.py` and the module that tests it.
No interface crosses between them that does not already exist (`walk_of`, `top_level_parts`, `PARTS`),
so there is no contract to state and no ordering edge between them. There is a green point at each
step: after the walk changes, the suite is green, and after the new module lands, it is green.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `tests/conftest.py` — `SourceWalk._all` skips by name | The skip set is data: a module-level constant holding the three root names, and the one name matched at any depth. The test is set membership on the relative path's pieces, the first piece for the root names and every piece for `__pycache__`, with no prefix, case-folding or pattern match, so that `.venvs`, `.behave2` and `Tests` miss. A file at the root has a first piece ending `.py`, so it can never equal a root name, and no separate guard for root files is needed. |
| `tests/architecture/test_source_walk.py` — the new tests | (1) Plant files the way `test_shapes.py`'s `test_each_walk_finds_a_violation_planted_where_it_looks` does: write each relative path under `tmp_path`, making parents first. Use one small builder for CP-788's root that CP-789 and CP-790 share, so the three cases cannot drift apart. (2) Take `PARTS` and `top_level_parts` from `test_shapes` by import, as `tests/integration/` modules import from their siblings, rather than copying the set. (3) **The module docstring must spell no planted path.** `test_trace.py`'s path pattern resolves every path-shaped token in a test module's docstring against the product root, and a planted name such as the CP-788 dot-folder file does not exist there. Describe planted files in words, or name them only in function docstrings and code. (4) **Plant `Tests/` in a root with no `tests/` folder.** On a filesystem that ignores case, the macOS default, the two names are one folder, and the near-name case would silently become the skipped one. (5) Keep to Python 3.11 (QC-60): `Path.walk` and `relative_to(..., walk_up=...)` are 3.12, and nothing here needs them. |

---

## 5. Test Additions

Every new test is layer 6. It walks real files that it writes under `tmp_path`, as the existing
planted-root tests in `test_shapes.py` do, and hands in no fake: the walk's subject is files on disk,
and its root arrives through `walk_of(root)`.

| Sub-job | Test file | Layer | Fakes handed in | What to add / modify |
|---|---|---|---|---|
| walk + test | `tests/architecture/test_source_walk.py` | 6 — Architecture | none — real files under `tmp_path`, root handed to `walk_of` | **CP-788, CP-789:** build CP-788's root (the six parts; `tests/x.py`, `.behave/features/x.py`, `.venv/x.py`, `__pycache__/x.py`, `domain/__pycache__/x.py`; `.other/x.py`). Assert `top_level_parts(walk_of(root))` is not `PARTS` and holds `.other`. Then remove `.other/x.py` and assert it equals `PARTS`. Fails at `97603d4f3` on its first assertion and passes after the change |
| walk + test | `tests/architecture/test_source_walk.py` | 6 — Architecture | none, as above | **CP-790, CP-785:** CP-788's root built without `.other/`. Assert `top_level_parts(...) == PARTS` and that no walked module's path has a first piece in the three root names or any piece named `__pycache__`. Passes before and after |
| walk + test | `tests/architecture/test_source_walk.py` | 6 — Architecture | none, as above | **CP-786, root file:** the six parts plus `.x.py` at the root. The parts reported are `PARTS` plus `.x` |
| walk + test | `tests/architecture/test_source_walk.py` | 6 — Architecture | none, as above | **CP-786, inside a part:** the six parts plus `web/.hidden/y.py`, `domain/.venv/x.py` and `domain/tests/x.py`. All three paths are among the walked modules, with parts `web`, `domain` and `domain`, and `top_level_parts` equals `PARTS` |
| walk + test | `tests/architecture/test_source_walk.py` | 6 — Architecture | none, as above | **CP-786, near names:** the six parts plus `.venvs/x.py`, `.behave2/x.py` and `Tests/x.py`, in a root with no `tests/` (§ 4 hint 4). The parts reported are `PARTS` plus `.venvs`, `.behave2` and `Tests`, so QC-1's comparison is not equal |
| — | `tests/architecture/test_shapes.py` | 6 — Architecture | — | No change. **CP-787** is its `test_the_top_level_parts_are_the_five_the_sdd_names`, run over the product root in a worktree and in a disposable clone, each holding `.venv/` and `.behave/`. The other layer-6 tests over the product root (`test_shapes.py`, `test_imports.py`, `test_reach.py`) cover "every other layer-6 test passes as at the base" |
| — | `tests/architecture/test_trace.py` | 6 — Architecture | — | No change. **CP-791** is its four docstring checks reading the new module: its docstring names SRS NFR-9 and AC-5 (with NFDR QC-1 as the clause), as `test_shapes.py`'s does, and names only existing paths |

Coverage by rule, beyond the rows above:

- **CP-792** (Ruff format and lint, exit 0) is a gate command, not a test. The base passes both, so
  the new module and the edited fixture must keep them green.
- **CP-793 and CP-794** are this design's reviews. Both are recorded under Architect Review Notes.
- **CP-795** is the two suite commands, run in a disposable clone at the commit under test.

**What the change stops proving.** No assertion is retired. No existing test plants a dot-folder in a
root it walks (spec, Verified Claims), so nothing asserted that a dot-folder is skipped. The clause
that went with the leading-dot test, "a hidden folder is not walked", is itself gone, by CP-786.

---

## Testing the change from outside the code

None. The way in the NFDR records is a browser (`docs/nfdr.md` § 9, `**Behave way in:** browser`),
and this change adds no behaviour of the tracker. It changes only which files the layer-6 source walk
reads, which no page shows, so no scenario can reach it. The request also rules out any `.behave/`
change.

---

## Records this change makes false

- `docs/nfdr.md` § 1.1, QC-1, *verified by* — "The entry starts unmet in its test: at `373ecc8a8`,
  `SourceWalk._all` in `tests/conftest.py` skips every path piece that begins with a dot, so a
  dot-folder holding code passes unseen" goes false once the walk skips by name. → It should say the
  entry is met: the walk skips the three root folders and `__pycache__` by name, and
  `tests/architecture/test_source_walk.py` fails on a code-holding dot-folder at the root. It should
  date the unmet half to the last commit before this change lands, as QC-39's tail dates its own.

Read also, and nothing false found: `docs/adr/` (ADR-0001 to ADR-0016 and the index), `docs/fdr.md`,
`docs/SDD.md` § 3 and every other mention of the source walk in `docs/nfdr.md`. The QC-2, QC-3,
QC-4, QC-42, QC-43, QC-45 and QC-61 tails, "the source walk that skips `tests/` and `.behave/` by
name (QC-1)", become true with this change and do not go false. RN-66 records why the test was to be
corrected, and stays true.

---

## Architect Review Notes

- **(e) Test code has no owning part:** the walk's new skip set stays in `tests/conftest.py`, and its
  tests go in a new layer-6 module in `tests/architecture/`. SDD § 3's `Owns` column covers the five
  product parts. `tests/` is in the package unit (QC-1) but is no part, so the parts table places
  none of this. The location follows `testing_python.md` § Layer 6 (`tests/architecture/test_<property>.py`)
  and the request.
- **(b) The near-name and nested cases are planted, not left implicit:** § 5 adds rows for `.x.py`,
  the nested `web/.hidden`, `domain/.venv` and `domain/tests`, and the near names `.venvs`, `.behave2`
  and `Tests`. The spec states these in CP-786 and its Examples, and each Example needs a row.
  Without them, the CP-788 test alone would pass for a walk that skipped `tests/`, `.behave/` and
  `.venv/` at any depth, or by prefix.
- **(b) CP-785 realized by construction:** the CP-790 row asserts on the walked paths themselves, not
  only on the part set. A root whose skipped files all sat in folders named after real parts could
  otherwise report `PARTS` while walking files that CP-785 leaves out.
- **(d) `Testing the change from outside the code` is `None` though a way in is recorded:** the
  template's zero form is for a product with no recorded way in. Here the browser is recorded, but
  the change adds no behaviour a browser can see, and the request forbids `.behave/` changes.
- **(d) No sub-jobs:** two files change, but they are one seam with no contract between them and a
  green point after each (§ 3).
- **Packet check, no conflict:** `conventions.md` § Constructs, "A module is given its collaborators",
  is met. `SourceWalk` is handed its root through its constructor (`walk_of(root)`), which is the
  seam every planted-root test uses. Reading the files under that root is the walk's subject, and
  `testing_python.md` § Layer 6 says such a walk reads the files on disk. The new tests are layer 6,
  not unit tests, and write only under `tmp_path`. No `deferred_decisions.md` entry is owed.
- **QC-12 review (CP-793), pass:** the change adds no part. It adds one constant in a test fixture and
  one layer-6 test module, both paid for by NFDR QC-1.
- **QC-60 review (CP-794), pass:** the edited walk and the new tests use only `pathlib`, set
  membership and pytest's `tmp_path`, all present in Python 3.11. Hint 5 in § 4 names the 3.12-only
  calls to avoid. `pathlib`'s `rglob` matches names that begin with a dot on 3.11, as the walk at the
  base already relies on.
- **QC-41 review, pass:** the change reads, holds and writes no secret.
- **QC-40 review, every-review moment — packages, met:** all 27 pinned packages in `uv.lock` and
  `.behave/uv.lock` (pytest 9.1.1, ruff 0.16.10, mypy 2.4.0, playwright 1.65.1, behave 1.3.3,
  httpx 0.28.1 and what they pull in) were checked against the OSV database's PyPI advisories on
  2026-11-13. None has an advisory. No dependency is added or moved.
- **QC-40 review, every-review moment — browser build, not blocking, owed by 2026-12-11:** the
  build `playwright==1.65.1` installs is Chromium 158.0.8127.18. The vendor's Stable Channel Update
  for Desktop of 2026-11-11 (157.0.8103.78) fixes five **Critical** advisories: CVE-2026-126885,
  CVE-2026-126895, CVE-2026-126879, CVE-2026-126846 and CVE-2026-126911. 158.0.8127.18 first shipped
  on the early-stable channel on 2026-11-04, before that release, and the vendor has since moved
  early stable to 158.0.8127.36/.37 (2026-11-12). Whether the pinned build carries those fixes is not
  stated by the vendor, so this review reads it as affected. The advisories are 2 days old, inside
  QC-40's 30-day window, so they do not block this change. The fix is owed within 30 days of
  2026-11-11: the pin moves, or the owner records a dated exception.
- **QC-40 review, package feed — down, moment still owed:** the account checking has admin on the
  repository that holds tracker17. The Dependabot alerts endpoint answered "Dependabot alerts are
  disabled for this repository" (403), and the asynchronous SBOM export answered 404. As QC-40 says,
  that is a feed that is down: this review records the feed as down and the moment as still owed, and
  raises no discrepancy.
