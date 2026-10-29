# Change Design — move the suite's lock and pin check to uv

**Date:** 2026-10-29
**Category:** nfdr
**Behaviour:** changing
**Publishes text:** yes — the note above the suite's test-tool declarations

Owns the implementation boundaries, lock-reader contract and verification mapping for
`tracker17 · tobiishi · 2026-10-29_uv-lock-and-pins-test`.
The inputs are this change's `change_spec.md` and `change_request.md`.
Product paths below are relative to `products/tracker17/`, as resolved by
`<CORE>/tools/development_path.py resolve --project tracker17 --key 2026-10-29_uv-lock-and-pins-test`
with the change worktree: exit 0, `product_path: products/tracker17`, one delivery repository.
Source inspections in this design describe commit `26f9414263379d62da0abc46f16900e9bc442dfe`.

---

## 1. Change Summary

Generate `uv.lock` beside `pyproject.toml`, retain all fifteen versions in the retiring pip file,
and replace the lock reader in `tests/architecture/test_pins.py`, as required by the spec's
CP-657–CP-663 (`change_spec.md:L56-L89`, **Rules**).
The configuration note names the new lock; the manifest's parsed contents remain identical
(`change_spec.md:L67-L71`, **CP-660**).
The lock-file test checks declared name/version pairs against parsed TOML package records;
`uv lock --check` separately checks whether the complete resolution matches the manifest
(`change_spec.md:L56-L60,L80-L89`, **CP-657**, **CP-658**, **CP-662**).

The scope has no tracker-code or project-card edits, and leaves the README rewrite with the
existing deferred entry (`change_spec.md:L161-L179`, **Out of Scope**;
`deferred_decisions.md`, **The README's suite instructions on uv**).

---

## 2. Blast Radius

The SDD's parts table assigns runtime rules, actions, persistence, pages and wiring, but no part
owns dependency-lock inspection (`products/tracker17/docs/SDD.md:L204-L225`, **The parts** and
**The units**).
Architect placement decision, 2026-10-29: keep the new checking logic in the existing layer-6
test, whose verification responsibility is NFDR QC-39 (`products/tracker17/docs/nfdr.md:L352-L361`,
**QC-39**); keep generated dependency data and its declaration note at the product root.
This placement adds no runtime part or import edge.

| Module / artifact boundary | Status | What changes |
|---|---|---|
| Product-root dependency tooling: `uv.lock` | New | Supply the generated lock consumed by uv and the pin test (CP-657–CP-659). |
| Product-root dependency tooling: `pyproject.toml` | Modified | Change only the note above `[dependency-groups]`; preserve every TOML table, pin and Python floor (CP-660). |
| `tests/` | Modified | The layer-6 pin checker owns TOML reading, canonical package-name matching and declared-version membership at `tests/architecture/test_pins.py`. Delete `tests/requirements.txt` in the same delivered change (CP-661–CP-663). |
| `domain/` | Unchanged | No rules, entities or public surfaces change. |
| `application/` | Unchanged | No actions or contracts change. |
| `persistence/` | Unchanged | No saved-data handling changes. |
| `web/` | Unchanged | No pages, requests or published tracker messages change. |
| `main.py` | Unchanged | No wiring changes. |
| `errors.py` | Unchanged | No error types change. |

The unchanged rows follow the request's prohibition on tracker-code changes
(`change_request.md`, **What must not be weakened**).
NFDR § 1.2 lists those six runtime import boundaries and forbids their importing tests
(`products/tracker17/docs/nfdr.md:L166-L197`, **Forbidden imports**, QC-13–QC-19).
No runtime public interface changes, so that graph yields no transitive caller changes.

---

## 3. Sub-jobs

These are two artifact boundaries inside the SDD's one Python unit, rather than two new runtime
parts (`products/tracker17/docs/SDD.md:L216-L225`, **The units**).

### Sub-job A — product-root dependency tooling

**Scope:** generate `uv.lock` and change the existing declaration note only.

**Exposes:** a uv-generated TOML lock at the product root, with its `package` array carrying
the resolved distribution names and versions; all fifteen baseline distributions retain their
versions (CP-659). uv remains responsible for lock metadata, dependency edges, sources, markers
and artifact hashes. uv documents this as a generated, version-controlled lock rather than a
hand-edited file (https://docs.astral.sh/uv/concepts/projects/layout/#the-lockfile).

**Depends on:** none.

### Sub-job B — `tests/`

**Scope:** replace the existing lock-file test in `tests/architecture/test_pins.py` and remove
`tests/requirements.txt`; retain the three protected tests and their assertions unchanged
(`change_spec.md:L75-L89`, **CP-661–CP-663**).

**Exposes:** one replacement lock-file test which reads only committed project files and:

- requires the product-root `uv.lock` file and a nonempty parsed package collection;
- obtains declarations through the existing `manifest()` and `declared_dependencies()` helpers;
- rejects every declaration not accepted by the existing `EXACT.fullmatch` predicate before
  extracting its name and exact version;
- compares each declared distribution and version with a locked pair, dropping an extras suffix
  from the distribution name and normalizing names according to PyPA's name-normalization rule
  (https://packaging.python.org/en/latest/specifications/name-normalization/#name-normalization);
- fails when any declared name is absent or its declared version has no matching lock entry.

Architect choice, 2026-10-29: use a collection of name/version pairs rather than a one-version
dictionary, so package-array order cannot choose which locked version is considered.
Extra transitive packages are permitted; equality between declared and resolved package sets
would contradict the requirement to lock dependencies pulled in by the declarations
(`change_spec.md:L61-L71`, **CP-659**, **CP-660**).
The replaced test's current presence, nonempty-lock and declaration-membership assertions are
at `tests/architecture/test_pins.py:L39-L51`, **test_the_lock_file_exists_and_every_line_is_exact**.

**Depends on:** A's generated lock and its name/version package records.

**Build sequence:** A exposes the generated lock, then B consumes it.
The request's delivery constraint binds A and B together: the final change includes the lock,
replacement reader, retirement of the pip file and updated note (`change_request.md`,
**Request**, "The file, the test that reads it and the comment that names it move together").

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — generated lock and declaration note | Use uv's resolver with version-specific package selections to retain the existing transitive versions, without adding manifest constraints. An isolated resolution using `uv lock --upgrade-package ast-serialize==0.12.1 --upgrade-package pluggy==1.6.0` exited 0 and retained the fifteen baseline versions; the reviewed result is recorded below. Leave generated metadata to uv. |
| B — lock reader and pip-file retirement | Parse TOML with the existing standard-library `tomllib`; compare normalized name/version pairs, with exactness checked before splitting declarations. Do not replace this with a subprocess invoking uv: the missing-lock and loose-pin probes must reach the test without uv repairing their inputs. |

No write into another repository is part of either sub-job; the path resolver returned one
delivery repository, as recorded above.

---

## 5. Test Additions

Only the lock-file test changes its assertions (CP-663).
The rows below map the spec's Examples in their displayed order; command and mutation probes
are disposable verification, not additional permanent tests of the test implementation.

| Row | Sub-job | Test file / check | What to add / modify |
|---|---|---|---|
| T1 | A | Lock freshness; Examples 1 and 3; CP-657 | Require `uv lock --check` exit 0 on the completed tree. In a separate scratch clone change `pytest==9.1.1` to `pytest>=9`; require the command to exit 1 without repairing the lock. Check the new file is tracked with `git ls-files --error-unmatch products/tracker17/uv.lock` and not ignored with `git check-ignore -q products/tracker17/uv.lock` returning 1, both at the instance clone root. |
| T2 | A | Offline freshness; Example 2; CP-658 | Require `uv lock --check --offline` exit 0 with a newly created empty `UV_CACHE_DIR`; this check must not rely on a warm package cache. |
| T3 | A | Resolved-version comparison; Example 4; CP-659 | Compare every baseline pip name/version pair with parsed lock entries using normalized names. Include the explicitly named `pluggy` and `ast-serialize` versions, not only the four direct pins. Read the baseline file from inspected commit `26f9414263379d62da0abc46f16900e9bc442dfe` for this one-time comparison; commit no history-dependent test. |
| T4 | A | Manifest diff; Example 5; CP-660 | Compare parsed TOML before/after for equality, and inspect the text diff: only the declaration-note comment block changes. No new tables, dependencies or constraints; `requires-python` stays `>=3.11`. |
| T5 | A + B | Retired file and references; Example 6; CP-661 | Require the pip file absent. Run the spec's exact grep over `pyproject.toml` and `tests/architecture/test_pins.py`: no output, exit 1. |
| T6 | B | `tests/architecture/test_pins.py`; Examples 7–9; CP-662–CP-663 | Replace the lock-file test; require all four tests green. In independent scratch clones run the already-synced environment's Python directly: missing `uv.lock` makes the replacement fail; `pytest>=9` without re-locking makes both the exact-declaration test and replacement lock test fail. Retain names and assertions of the other three tests. |
| T7 | B | Additional CP-662 failure edges, temporary probes | Independently remove the declared `pytest` package entry, change only its locked version, and replace the lock with valid TOML holding an empty package array. Each must make the replacement fail. Malformed TOML must fail rather than be treated as an empty successful result. A name-spelling probe, such as `MyPy` for `mypy`, must preserve a successful match. Restore the clean tree between probes. |
| T8 | A + B | Fresh-clone setup and suite; Example 10; CP-664 | At the completed branch commit, in a fresh Git clone, save the committed lock bytes; run `uv sync --locked`, then exactly `uv run pytest tests/unit tests/architecture`, each exit 0. Compare the lock bytes after each command with the committed bytes. |
| T9 | B | Formatting and lint; Example 11; CP-665 | Require `uv run ruff format --check .` and `uv run ruff check .` exit 0 over the completed product tree. |
| T10 | A | Dependency and browser review; Example 12; CP-666 | Completed design review is below. The generated registry name/version set must match the reviewed set; a different resolved package or version requires an advisory check before acceptance. |
| T11 | B | Python compatibility review; Example 13; CP-667 | The design uses `tomllib`, `pathlib`, `re`, and ordinary collections available in Python 3.11. Review the edited test against this design; do not infer an actual Python 3.11 suite run from this API review. |

Rule pass: CP-657's tracked/not-ignored and stale-lock paths are T1; CP-658 is T2;
CP-659 is T3; CP-660 is T4; CP-661 is T5; CP-662's presence, empty, malformed, missing-name,
wrong-version and normalized-name cases are T6–T7; CP-663's unchanged assertions and malformed
pin are T6; CP-664's fresh environment and immutable bytes are T8; CP-665–CP-667 are T9–T11.
The assertion that every pip-format line is `name==version` is retired because the lock becomes
TOML; T1 re-proves resolution freshness, and T6–T7 re-prove file presence, nonempty data and
declared dependency/version membership (CP-662; `tests/architecture/test_pins.py:L41-L51`).
No other assertion or signature is retired by this design.

Commands above are typed at the product root unless their row says otherwise.
Failure probes use the synced environment directly so `uv run` cannot re-lock the mutated tree;
uv documents its automatic lock/sync behavior at
https://docs.astral.sh/uv/concepts/projects/sync/#automatic-lock-and-sync.

---

## Records this change makes false

- `products/tracker17/docs/nfdr.md` § 2, **QC-39**, "The entry starts unmet": after landing,
  replace the outstanding-migration wording with the installed `uv.lock` check and its verification
  evidence. Preserve the explicitly dated observation at commit `9219be1e1` as history; that
  observation is not made false by this change (`products/tracker17/docs/nfdr.md:L352-L361`).
- No decision or import boundary in `products/tracker17/docs/adr/`, `products/tracker17/docs/fdr.md`
  or `products/tracker17/docs/SDD.md` § 3 is changed. ADR-0013 § **Decision** and NFDR QC-39 already
  prescribe the target. References to the old file in dated review notes remain historical.

The README's removed-file command is a product gap, not a reason to change the foundation's
requirement to document the suite: retain the existing deferred entry against FDR R-8 and SDD
RT-4 (`products/tracker17/docs/fdr.md:L57-L60`, **R-8**;
`products/tracker17/README.md:L89-L103`, **Running the tests**;
`deferred_decisions.md`, **The README's suite instructions on uv**).
This design edits no foundation record.

---

## Architect Review Notes

- **Placement outside the parts table — kind (e), architect, 2026-10-29:** dependency checking
  belongs in the existing architecture test, not a runtime part. SDD § 3 has no testing part,
  while its unit places `tests/` at the root and NFDR QC-39 delegates this check to layer 6
  (`products/tracker17/docs/SDD.md:L204-L225`; `products/tracker17/docs/nfdr.md:L352-L361`).
- **Artifact-boundary decomposition — kind (d), architect, 2026-10-29:** § 3 separates generated
  root tooling from its consuming `tests/` module because the package records are the dependency
  between them. This changes no SDD unit and creates no runtime module.
- **Version matching by construction — kind (b), architect, 2026-10-29:** CP-662's locked-version
  clause is realized by explicit pair membership, not package-name presence alone. Names use PyPA
  normalization and extras are removed before lookup, preserving the existing helper's declaration
  coverage (`tests/architecture/test_pins.py:L21-L29,L49-L51`;
  https://packaging.python.org/en/latest/specifications/name-normalization/#name-normalization).
- **Published-text decision — architect, 2026-10-29:** the changed manifest note is prose for a
  person reading the tool declarations, so `Publishes text` is `yes`. Its place is the existing
  comment block only (CP-660); no new assertion message or README wording is required.
- **Delegated gate sweep:** searching `docs/nfdr.md` and `docs/adr/` for `development-design`
  found the applicable reviews QC-12, QC-40, QC-41 and QC-60
  (`products/tracker17/docs/nfdr.md:L159-L164,L359-L394,L534-L541`). QC-12 passes: no added runtime part,
  parser dependency or permanent testing subsystem. QC-41 passes: this design introduces no
  account, key, credential or secret. Gates for refusals, runtime state, saved fields and page
  handling are not triggered by the § 2 boundaries.
- **QC-40 / CP-666 — pass for the reviewed resolution, 2026-10-29:** an isolated temporary
  project copied only the current manifest and resolved with the § 4 package selections.
  `uv lock` exited 0: `Using CPython 3.14.5`, `Resolved 17 packages in 390ms`.
  Parsing its registry packages produced the sixteen rows below; the seventeenth package is
  the local project. `POST https://api.osv.dev/v1/querybatch`, using those sixteen PyPI
  name/version pairs, returned `{"results":[{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}]}`.
  Each PyPI per-version response below had the matching `info.version`, at least one release
  file and `vulnerabilities: []`. These are the checked feeds' results, not a claim that an
  unpublished vulnerability cannot exist.

| Reviewed distribution | Version | PyPI evidence, read 2026-10-29 |
|---|---|---|
| ast-serialize | 0.12.1 | https://pypi.org/pypi/ast-serialize/0.12.1/json |
| colorama | 0.4.6 | https://pypi.org/pypi/colorama/0.4.6/json |
| greenlet | 3.5.6 | https://pypi.org/pypi/greenlet/3.5.6/json |
| iniconfig | 2.3.1 | https://pypi.org/pypi/iniconfig/2.3.1/json |
| librt | 0.16.0 | https://pypi.org/pypi/librt/0.16.0/json |
| mypy | 2.4.0 | https://pypi.org/pypi/mypy/2.4.0/json |
| mypy-extensions | 1.1.0 | https://pypi.org/pypi/mypy-extensions/1.1.0/json |
| packaging | 26.3 | https://pypi.org/pypi/packaging/26.3/json |
| pathspec | 1.1.1 | https://pypi.org/pypi/pathspec/1.1.1/json |
| playwright | 1.63.0 | https://pypi.org/pypi/playwright/1.63.0/json |
| pluggy | 1.6.0 | https://pypi.org/pypi/pluggy/1.6.0/json |
| pyee | 13.0.1 | https://pypi.org/pypi/pyee/13.0.1/json |
| pygments | 2.21.0 | https://pypi.org/pypi/pygments/2.21.0/json |
| pytest | 9.1.1 | https://pypi.org/pypi/pytest/9.1.1/json |
| ruff | 0.16.10 | https://pypi.org/pypi/ruff/0.16.10/json |
| typing-extensions | 4.16.0 | https://pypi.org/pypi/typing-extensions/4.16.0/json |

- **Browser review — pass under the existing exception:** Playwright's versioned browser manifest
  names Chromium and its headless shell as `153.0.8010.12`
  (https://raw.githubusercontent.com/microsoft/playwright/v1.63.0/packages/playwright-core/browsers.json).
  Google's 2026-10-27 desktop release lists critical fixes at `156.0.8078.73/.74`
  (https://chromereleases.googleblog.com/2026/10/stable-channel-update-for-desktop_0562499947.html).
  The older pinned build is not cleared as free of critical advisories. It passes this review
  under the owner's build-specific exception through the end of 2026-11-07
  (`products/tracker17/docs/nfdr.md:L1068-L1079`, **RN-33**).
  QC-40's dependency-graph confirmation is assigned to the first review after `uv.lock` is on
  `main`, not this review (`products/tracker17/docs/nfdr.md:L381-L386`, **QC-40**).
- **QC-60 / CP-667 — design API review passes:** `tomllib` and its TOML reader are available in
  Python 3.11 (https://docs.python.org/3.11/library/tomllib.html). The remaining proposed operations
  use the existing `re`, `Path` and collection operations (`tests/architecture/test_pins.py:L9-L29`).
  No new runtime, parser package or newer syntax is required. This is the review of the proposed
  edit; T11 covers inspection of the actual edit, and no Python 3.11 suite run is claimed.
- **Language resolution:** Python, step 1, `system/projects/tracker17/project.md` **Languages**;
  opened `<CORE>/doctrine/engineering/languages/python/README.md` and the relevant toolchain,
  conventions and testing doctrine. The product's Python floor and dependency choices remain
  those of ADR-0013 and NFDR QC-59/QC-60.
- **Reading check:** no spec line is set aside. The existing README record gap stays in
  `deferred_decisions.md`; this run adds no deferred entry.

The cold read accounts for all runtime boundaries, the A-to-B contract, every Example and the
rule-implied failure paths. The design uses no production-code snippets or cross-repository writes.
