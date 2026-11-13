# Change Design — the pins test reads the Behave folder's manifest and lock

**Date:** 2026-11-13
**Category:** nfdr
**Behaviour:** changing
**Publishes text:** no
<!-- Decided by the CP-438 test: the change adds one layer-6 test file's checks and puts no text in front of the tracker's operator. -->
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern file it routes (`toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`, and `testing_python.md`)

---

## 1. Change Summary

`tests/architecture/test_pins.py` gains a check of the Behave folder's set, `.behave/pyproject.toml`
and `.behave/uv.lock`, by NFDR QC-39's three checks (CP-773 to CP-778), and one test per case, each
run against a temporary copy of the product (CP-779). The file's four existing tests keep reading the
root pair, unchanged (CP-781). The file's shared exact-pin pattern also starts refusing a wildcard
version (`==1.*`), so both sets meet one bar. No other file in the product changes (CP-783). All
paths are relative to the product, `products/tracker17`.

---

## 2. Blast Radius

| Module | Status | What changes |
|---|---|---|
| `tests/architecture/test_pins.py` | Modified | (1) A check over a given product folder's `.behave/`, returning one finding per failure, each naming its case: manifest missing or not readable TOML (CP-774), lock missing or not readable TOML (CP-775), nothing declared (CP-777), a requirement not pinned exactly (CP-773), a lock with no package record or a declared pin the lock does not fix (CP-776). Nothing found when `.behave` is absent (CP-778). It reuses `declared_dependencies`, `normalized` and `EXACT`. (2) `EXACT`'s version part refuses `*`. (3) A test running the check on the product itself, a fixture making the temporary copy, and the case tests of §5. The four existing tests are unchanged. |
| `domain/`, `application/`, `persistence/`, `web/`, `main.py`, `errors.py` | Unchanged | — (CP-783) |
| `pyproject.toml`, `uv.lock`, `.behave/pyproject.toml`, `.behave/uv.lock` | Unchanged | — (CP-780, CP-783) |

No transitive blast radius. No module imports a test module (NFDR QC-19's second clause), and the
§ 1.2 import walks skip `tests/` by name (QC-1). Placement by SDD § 3: no part owns the new logic. It
is test code, and NFDR QC-39's *verified by* puts it in `tests/architecture/test_pins.py` (see
Architect Review Notes, (e)).

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| `tests/architecture/test_pins.py` | **The seam is the folder.** The check takes the product folder as a parameter and reads only under it. The product test hands it `PRODUCT_ROOT`. Each case test hands it the copy. **The copy:** a fixture in this file (not `conftest.py`, by CP-783) copies the product root into `tmp_path` with `shutil.copytree`, leaving out `.venv`, `.pytest_cache` and `__pycache__` through `ignore_patterns`. Each case then edits only the copy's `.behave/`: it rewrites the manifest's text, removes or overwrites a file, turns `.behave` into a plain file, or removes it (CP-778). Make the CP-776 mismatch the way CP-782 makes it, by replacing the `playwright` pin in the copied manifest. **Reading:** a file counts as missing when it is not a regular file, or when reading or parsing it raises one of the narrow errors that can arrive (`OSError`, `UnicodeDecodeError`, `tomllib.TOMLDecodeError`; `errors_logging.md` § Catching). When the manifest is missing, no later check runs over it. **Findings, not one assert:** the check returns its findings. The product test asserts there are none. Each failing case asserts that its own case's finding is among them, so a case cannot pass because some other check failed. **The pattern:** take `*` out of the characters `EXACT` accepts in a version, for both sets. **The trace (TS-3, TS-4):** the module docstring keeps naming SRS NFR-9 and adds the new rule ids. Write every path a docstring names from the product root. |

---

## 5. Test Additions

All new tests are in `tests/architecture/test_pins.py`, layer 6 (Architecture, NFDR § 9). Fakes handed
in: none. A case test's check reads real files in its own temporary copy under `tmp_path`, and the
product test reads the committed tree beside it (`testing_doctrine.md` § *A test reads nothing of the
machine it runs on*).

| Sub-job | Test file | Layer | Fakes handed in | What to add / modify |
|---|---|---|---|---|
| product | `tests/architecture/test_pins.py` | 6 — Architecture | none | **New:** the check run on `PRODUCT_ROOT` finds nothing. This is Example 1 (CP-773, CP-775, CP-776), and it is the test CP-782's mutation fails |
| CP-773 | same | 6 | none — the copy | **New, parametrized:** the copy's manifest declares one requirement not pinned exactly, and the finding names that entry. The cases cover all five forms CP-773 refuses, and each of the four lists at least once: `httpx>=0.28` in `[project] dependencies` and a bare `behave` in `[dependency-groups]` (the two Examples), `~=`, `==1.*` and a pin combined with a second specifier, spread over `[project.optional-dependencies]` and `[build-system] requires` |
| CP-774 | same | 6 | none — the copy | **New, parametrized:** the manifest finding appears when `.behave/` holds `uv.lock` and no `pyproject.toml`, when `.behave` is a plain file (both Examples), and when `pyproject.toml` is not readable TOML (Locked Answers, Gap 4) |
| CP-775 | same | 6 | none — the copy | **New, parametrized:** the lock finding appears when `.behave/` holds `pyproject.toml` and no `uv.lock` (Example), and when `uv.lock` is not readable TOML (Gap 4) |
| CP-776 | same | 6 | none — the copy | **New, parametrized:** the copied manifest says `playwright==1.65.0` against the lock's `1.65.1`, and the finding names it (Example). A copied lock with no package record gives its own finding (rule edge) |
| CP-776, the passing side | same | 6 | none — the copy | **New, parametrized:** `Behave==1.3.3` in place of `behave==1.3.3` gives no finding (Example). `httpx[http2]==0.28.1` gives none either, because extras are dropped (rule edge). Separator folding is the `normalized` the root lock test already uses |
| CP-777 | same | 6 | none — the copy | **New:** a manifest of `dependencies = []` and nothing else gives the nothing-declared finding (Example) |
| CP-778 | same | 6 | none — the copy | **New:** the copy with `.behave` removed gives no finding (Example). The root checks still run in it: they are the four existing tests, whose inputs hold nothing of `.behave`. Covered by the root rows |
| root (CP-781) | same | 6 | none | **Unchanged:** the four existing tests, every assertion kept. `test_the_exact_pattern_refuses_a_range_and_accepts_a_pin` still passes under the tightened `EXACT`. Its two accepted pins hold no `*`, and `pytest==9.*,<10` stays refused |

**Retired assertions:** none. The tightened `EXACT` refuses everything it refused before, and the
root manifest holds no `*`.

**Checked outside the suite** (CP-780, CP-782 to CP-784). These are the spec's own measurements, and a
test cannot make them, because a test reads no commit history:

- CP-780: after both suite runs, `git status --porcelain -- products/tracker17/.behave` in the change
  worktree prints nothing.
- CP-782: in a fresh clone at the change's commit, run from the product folder, with `playwright==1.65.1`
  changed to `playwright==1.65.0` in `.behave/pyproject.toml` only,
  `uv run --locked --project . pytest tests/architecture/test_pins.py` exits non-zero, and the product
  row is the test that fails. With the change reverted, it exits 0. The clone is removed from outside
  (`CROSS_ROLE.md` § *Every seat*).
- CP-783: `git diff --name-only <base>.. -- products/tracker17` lists `tests/architecture/test_pins.py`
  alone.
- CP-784: both halves of `Test command:`, each read at its last line. Also `ruff format --check` and
  `ruff check` over the file (QC-62).

---

## Testing the change from outside the code

- No behaviour of tracker17 changes. The way in that NFDR § 9 records, `browser`, reaches nothing new:
  the change is one layer-6 test file of the suite, and a scenario driving the tracker in a browser
  sees the same tracker. No scenario is owed.

---

## Records this change makes false

- `docs/nfdr.md` QC-39, *verified by* — "**The entry starts unmet in its test:** at `<a commit not in the public history>`,
  `test_pins.py` reads only the root `pyproject.toml` and `uv.lock`" goes false. It should say that the
  Behave half is met, that `test_pins.py` reads both pairs, and that it was verified by CP-782's
  mutation in a fresh clone at the landing commit: non-zero mutated, 0 reverted. RN-69's "QC-39 starts
  unmet in its test" is a dated note and stays as written, as RN-57 left its predecessors.

Read: `docs/adr/` (index; ADR-0013 whole), `docs/nfdr.md` §§ 1.1, 1.2, 2 (QC-39 to QC-41), 8
(QC-59, QC-60), 9 and 10, `docs/fdr.md` (grep for the pins test and `.behave`, no match), and
`docs/SDD.md` § 3 and § 4 RT-4, TS-1 to TS-6. Nothing else in them goes false.

---

## Architect Review Notes

- **(b) Wildcard refusal goes in the shared pattern.** CP-773 says `==1.*` fails. `EXACT` accepts it
  today: a scratch run of `EXACT.fullmatch("httpx==1.*")` gave a match. The pattern refuses `*`, and
  both sets use it, so QC-39's "both are held to this bar" is one bar. The root manifest holds no `*`,
  so CP-781 holds and nothing is weakened. The root half meets QC-39's "exact version" too, which is
  `found_while_walking.md` in the file the change edits. Not taken: a stricter pattern for the Behave
  set alone, which would hold the two sets to two bars.
- **(b) The check returns findings, and each case test asserts its own.** CP-779 says each failing case
  "asserts that the check fails there". Asserting only that something failed would let a broken copy
  pass every case. Each case test names the finding it expects.
- **(b) The Behave check takes the folder, and the root tests stay as written.** The check is handed
  the product folder, which is the seam that lets it run on a copy (CP-779). The four root tests are
  not rewritten onto it: CP-781 holds them assertion by assertion, and they read only the committed
  tree beside them. The shared helpers (`declared_dependencies`, `normalized`, `EXACT`) are reused, so
  both sets read the same four lists and compare names the same way (Gap 3).
- **(b) "A temporary copy of the product"** is the product root copied into `tmp_path`, without the
  three ignored, untracked folders (`.venv`, `.pytest_cache`, `__pycache__`). That is about 5 MB
  outside `.venv`. Not taken: a folder holding only `.behave/`, which is not a copy of the product.
- **(b) CP-778's "the suite's checks still run"** is met by construction. The Behave check is its own
  test, and the four root tests have no `.behave` input, so an absent folder cannot skip them.
- **(e) No part owns the logic.** SDD § 3's five parts own tracker behaviour. `tests/` is test code in
  the package unit (NFDR QC-1). NFDR QC-39's *verified by* names `tests/architecture/test_pins.py`,
  and CP-783 confines the change to that file, so the fixture sits there and not in `conftest.py`.
- **Packet:** no conflict. The check is handed the folder it reads, and builds no collaborator. The
  case tests touch files only under `tmp_path`. The file keeps `from __future__ import annotations`,
  `pathlib` and 100 columns (`conventions.md`; `pyproject.toml` `[tool.ruff]`). No packet departure.
- **Delegated review — QC-12:** pass. Tests only, paid for by QC-39 (SRS C-8). No part added.
- **Delegated review — QC-60:** pass for the design. `tomllib` is new in 3.11. `shutil.copytree` with
  `ignore_patterns` predates 3.11. Nothing after 3.11 is required. No 3.11 run was made, and that gap
  stays as QC-60 records it.
- **Delegated review — QC-41:** pass. No secret, account or credential.
- **Delegated review — QC-39's `uv lock --check --project .behave`:** not triggered. Neither Behave
  file changes (CP-780, CP-783).
- **Delegated reviews not triggered:** QC-5, QC-8, QC-23, QC-25 to QC-27, QC-36, QC-46. No change touches
  `web`, `persistence`, the saving contract, page building, a refusal or a saved field. No dependency
  or pin moves, so QC-40's first moment does not arise.
- **Delegated review — QC-40, packages:** no critical advisory applies.
  `gh api --method GET /advisories --raw-field ecosystem=pip --raw-field severity=critical --field per_page=100 --paginate`
  returned 843 advisories. They were compared locally with the 27 external names in `uv.lock` and
  `.behave/uv.lock`. Five names matched, and each locked version is at or past its fix: Pygments
  2.21.0 (GHSA-fff8-4w9p-7v76, fixed 2.1), anyio 4.16.0 (GHSA-82r6-8w77-94w6, fixed 4.14.2), certifi
  2026.10.23 (GHSA-6q48-6c7w-9gw2, fixed 2026.10.18), h11 0.16.0 (GHSA-vqfr-h8mv-ghfj, fixed 0.16.0)
  and httpx 0.28.1 (GHSA-h8pj-cxx2-jfg2, fixed 0.23.0).
- **Delegated review — QC-40, browser:** the installed driver's `browsers.json` declares chromium and
  chromium-headless-shell revision 1254, 158.0.8127.18. Chrome Releases' feed, read 2026-11-13, shows
  the Stable Channel Update for Desktop of 2026-11-11 fixing five critical CVEs in 157.0.8103.78/.79:
  CVE-2026-126885, -126895, -126879, -126846 and -126911. The Early Stable update of 2026-11-12 moves
  158 to 158.0.8127.36/.37. Whether 158.0.8127.18 carries those fixes is not established. Either way
  the advisories are two days old, so QC-40's 30-day window runs to 2026-12-11. No critical advisory
  older than 30 days is shown against this build. Verdict: not blocking, and the owner watches the
  window.
- **Delegated review — QC-40, package feed:** down, and the graph moment stays owed, as the entry
  provides. `gh api repos/<owner>/<repository>` read `admin: true`.
  `gh api repos/<owner>/<repository>/dependabot/alerts` returned 403, "Dependabot alerts are disabled
  for this repository." The asynchronous SBOM export was not requested. This run's permission layer
  refused the POST, so this review read no graph. No discrepancy is raised.
- **Cold-read:** checks 1 to 10 hold. There is one module, so there are no sub-jobs, no interface
  contract and no build sequence. Every Example and every rule edge maps to a §5 row or a covered-by
  note. No reading of the spec was set aside and no packet departure arose, so `deferred_decisions.md`
  is not written.
