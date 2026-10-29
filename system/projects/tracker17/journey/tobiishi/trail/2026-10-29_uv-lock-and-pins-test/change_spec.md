# Change Spec — the lock file is `uv.lock`, and the pin test reads it

**Date:** 2026-10-29
**Category:** nfdr
**Behaviour:** changing
**Request:** Make uv's lock file the tracker's lock file. Today the suite's pins are locked by
`products/tracker17/tests/requirements.txt`, a pip lock file, and `tests/architecture/test_pins.py`
reads it (`test_the_lock_file_exists_and_every_line_is_exact`, L39-L53). ADR-0013 and NFDR QC-39 already
name uv. After this change:

- `uv.lock` sits beside `pyproject.toml` at the product root. It is generated from the exact pins
  already in `[dependency-groups] dev` (`mypy==2.4.0`, `playwright==1.63.0`, `pytest==9.1.1`,
  `ruff==0.16.10`), and `uv lock --check` exits 0.
- `tests/requirements.txt` is deleted.
- `tests/architecture/test_pins.py` checks `uv.lock` instead: its lock-file test fails when `uv.lock`
  is absent, and the dependency test still fails when a test dependency in `[dependency-groups]` is
  not pinned with `==`. The file reads no `tests/requirements.txt`.
- The `pyproject.toml` comment that names `tests/requirements.txt` (L8) is reworded to name `uv.lock`,
  so `grep -n "requirements.txt" pyproject.toml tests/architecture/test_pins.py` prints nothing.
- `uv sync --locked` exits 0, then `uv run pytest tests/unit tests/architecture` exits 0, both from the
  product root, checked in a fresh clone of the branch's commit.

The file, the test that reads it and the comment that names it move together, because the test reads
the old file and none of the three can land alone.

**What must not be weakened:** no dependency version changes — `uv.lock` resolves the existing exact
pins, and no pin in `pyproject.toml` is changed, added or removed. `test_every_declared_dependency_is_pinned_exactly`,
`test_requires_python_is_3_11` and `test_the_exact_pattern_refuses_a_range_and_accepts_a_pin` keep
passing and are not weakened. No test is deleted, skipped, retried or marked expected-to-fail. No tracker
code, no record under `docs/` and no project card line changes. The README's suite section and its "How
it's built" line, and the project card's Setup and Test commands, are the next two stations'; a README
sentence this change makes false may be corrected on the branch.

**Proof:** `test_pins.py`, run in a scratch copy, exits non-zero once with `uv.lock` removed and once with
`pytest==9.1.1` changed to `pytest>=9`; and the full set above passes in a fresh clone.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened

---

## Change Summary

The product's test-dependency lock file moves from pip's `tests/requirements.txt` to uv's `uv.lock`
beside `pyproject.toml`, fixing the same versions the pip file fixes today, and the layer-6 pin test
reads `uv.lock` instead. This meets NFDR QC-39 as ADR-0013 and SDD § 4 RT-4 restate it; the entry
starts unmet today.

Every path below is relative to the product root, the directory `system/projects/tracker17/project.md`
`Product path:` names, and every command is typed from there.

---

## Rules

### The lock file

- **CP-657:** `uv.lock` exists at the product root, beside `pyproject.toml`, and is committed: it is
  tracked by git and not ignored. `uv lock --check` exits 0 on the branch tree (NFDR QC-39, its
  `uv lock --check` row; ADR-0013 § Decision).
- **CP-658:** `uv lock --check --offline` also exits 0 on the branch tree, with an empty uv cache too
  (NFDR QC-39, "`--offline` included").
- **CP-659:** Every package `tests/requirements.txt` fixes on `main` today is fixed in `uv.lock` at the
  same version. Names compare case-insensitively, with `_` and `-` treated as the same character. The
  fifteen are: `ast_serialize==0.12.1`, `greenlet==3.5.6`, `iniconfig==2.3.1`, `librt==0.16.0`,
  `mypy==2.4.0`, `mypy_extensions==1.1.0`, `packaging==26.3`, `pathspec==1.1.1`,
  `playwright==1.63.0`, `pluggy==1.6.0`, `pyee==13.0.1`, `Pygments==2.21.0`, `pytest==9.1.1`,
  `ruff==0.16.10`, `typing_extensions==4.16.0`.
- **CP-660:** `pyproject.toml` keeps its `[project]` table, its `[dependency-groups]` table and every
  `[tool.*]` table exactly as they are today, and gains no table. No pin is changed, added or removed,
  and `requires-python` stays `">=3.11"`. The only text that changes is the comment above
  `[dependency-groups]`. It names `uv.lock` as the file that locks these pins with everything they pull
  in, where today it names `tests/requirements.txt`.

### The pip lock file goes

- **CP-661:** `tests/requirements.txt` does not exist on the branch tree, and
  `grep -n "requirements.txt" pyproject.toml tests/architecture/test_pins.py` prints nothing and exits 1.

### The pin test

- **CP-662:** `tests/architecture/test_pins.py` has a lock-file test that passes on the branch tree. It
  fails when `uv.lock` is absent from the product root (NFDR QC-39, *verified by*: "fails … on a missing
  `uv.lock`"). It also fails when a dependency `pyproject.toml` declares is not fixed in `uv.lock` at the
  version it declares. This test replaces `test_the_lock_file_exists_and_every_line_is_exact`, which
  reads `tests/requirements.txt` today (`tests/architecture/test_pins.py:39-51`).
- **CP-663:** `test_every_declared_dependency_is_pinned_exactly`, `test_requires_python_is_3_11` and
  `test_the_exact_pattern_refuses_a_range_and_accepts_a_pin` keep their names and their assertions
  unchanged. The first still fails when an entry in `[dependency-groups]` is not pinned with `==`, for
  example `pytest>=9` (NFDR QC-39). No test in the suite is deleted, skipped, retried or marked
  expected-to-fail. The lock-file test of CP-662 is the only test whose assertions change.

### The suite on uv

- **CP-664:** In a fresh clone of the branch's commit, `uv sync --locked` exits 0, and then
  `uv run pytest tests/unit tests/architecture` exits 0. Neither command changes `uv.lock`: after both,
  it is byte-identical to the committed file (SDD § 4 RT-4; ADR-0013 § Decision).

### Checks the records above require of this change

- **CP-665:** `uv run ruff format --check .` and `uv run ruff check .` exit 0 on the branch tree (NFDR
  QC-62, its formatting and lint rows, which run over the tree and so reach the edited
  `tests/architecture/test_pins.py`).
- **CP-666:** No version `uv.lock` fixes is one that a known critical advisory is against, while a
  version free of one is published on PyPI. This is checked at this change's `development-design`
  review, the moment NFDR QC-40 names for a change that "chooses the lock file's format", and at every
  review. The Chromium build that `playwright==1.63.0` installs stays under the owner's dated exception,
  NFDR RN-33, until the end of 2026-11-07.
- **CP-667:** The edited pin test uses no language or library feature that Python 3.11 lacks. This is
  checked at review at `development-design`, which is NFDR QC-60's *verified by* for a change that uses
  a language or library feature.

---

## Examples

| Scenario | Expected behavior |
|---|---|
| Branch tree, `uv lock --check` (CP-657) | exits 0 |
| Branch tree, `uv lock --check --offline` with an empty uv cache (CP-658) | exits 0 |
| Branch tree, `pyproject.toml` with `pytest==9.1.1` changed to `pytest>=9`, then `uv lock --check` (CP-657) | exits 1: the lock file is out of step |
| Branch tree, read `uv.lock`'s `pluggy` and `ast-serialize` entries (CP-659) | `1.6.0` and `0.12.1`, the pip file's versions. A plain `uv lock` from the pins alone picks `1.7.0` and `0.13.1`, which this rule refuses |
| Branch tree, `git diff main -- pyproject.toml` (CP-660) | only comment lines in the block above `[dependency-groups]` differ |
| Branch tree, `ls tests/requirements.txt`; the grep of CP-661 (CP-661) | no such file; the grep prints nothing and exits 1 |
| Scratch copy of the branch tree with `uv.lock` removed, `test_pins.py` run on the synced environment (CP-662) | exits non-zero: the lock-file test fails |
| Scratch copy, `pyproject.toml`'s `pytest==9.1.1` changed to `pytest>=9`, `test_pins.py` run on the synced environment without re-locking (CP-662, CP-663) | exits non-zero: `test_every_declared_dependency_is_pinned_exactly` fails, and so does the lock-file test |
| Branch tree, `test_pins.py` unmodified (CP-662, CP-663) | every test in the file passes |
| Fresh clone of the branch commit: `uv sync --locked`, then `uv run pytest tests/unit tests/architecture` (CP-664) | both exit 0; `uv.lock` is byte-identical to the committed file afterwards |
| Branch tree, `uv run ruff format --check .` and `uv run ruff check .` (CP-665) | both exit 0 |
| `development-design` review of this change (CP-666) | every version `uv.lock` fixes is checked against published critical advisories, the Windows-only `colorama` included. The Chromium build of `playwright==1.63.0` does not block, under RN-33 |
| `development-design` review of the edited test (CP-667) | no feature newer than Python 3.11 is found |

---

## Verified Claims

All runs used uv 0.11.14, CPython 3.14.5 (the interpreter uv picked for `requires-python`), in disposable
clones of the instance at `c4777b8b7`, working in `products/tracker17`. The post-change tree was built
there by hand: `tests/requirements.txt` removed, the comment reworded, and a lock-file test written to
CP-662. It was then run as described.

| Claim | Verified by | What came back |
|---|---|---|
| `tests/requirements.txt` fixes the fifteen versions CP-659 lists | read `tests/requirements.txt` on `main` | the fifteen `name==version` lines, under three comment lines |
| The lock-file test reads `tests/requirements.txt` today, and `pyproject.toml` L8 names it | `grep -n "requirements.txt" pyproject.toml tests/architecture/test_pins.py` on `main` | `pyproject.toml:8`, `tests/architecture/test_pins.py:40` |
| A plain `uv lock` from the four pins moves two versions the pip file fixes | `uv lock` on the `main` tree, then read each `[[package]]` in `uv.lock` | 17 packages: `ast-serialize 0.13.1` (pip file 0.12.1), `pluggy 1.7.0` (pip file 1.6.0), plus `colorama 0.4.6` (`sys_platform == 'win32'` only) and `tracker17` itself; the other thirteen match |
| CP-659 can be met with `pyproject.toml` unchanged (CP-660) | `uv lock --upgrade-package ast-serialize==0.12.1 --upgrade-package pluggy==1.6.0` on that tree | exit 0; `ast-serialize 0.12.1`, `pluggy 1.6.0`; all fifteen pip versions now in `uv.lock` |
| CP-657, CP-658 hold on that lock | `uv lock --check`; `uv lock --check --offline`; again with `UV_CACHE_DIR` set to an empty directory | each exits 0 |
| A moved pin makes `uv lock --check` exit 1 | `pytest==9.1.1` → `pytest>=9` in `pyproject.toml`, `uv lock --check` | exit 1; restored, exit 0 |
| `uv.lock` is not ignored | `git check-ignore -q products/tracker17/uv.lock` | exit 1 (not ignored) |
| CP-661's grep prints nothing on the post-change tree | the grep of CP-661 | no output, exit 1 |
| CP-664 holds | `uv sync --locked`, then `uv run --locked pytest tests/unit tests/architecture -q`; and on a second clone `uv sync --locked`, `uv run pytest …`, then `cmp` of `uv.lock` against its copy taken first | sync exit 0; 686 passed, exit 0; `uv.lock` unchanged |
| CP-662 fails on a missing `uv.lock` | `uv.lock` moved away, `.venv/bin/python -m pytest tests/architecture/test_pins.py` | exit 1; the lock-file test failed, 3 passed |
| CP-662 and CP-663 fail on `pytest>=9` | the pin edited, the same command, run on the synced environment so that `uv run` does not re-lock | exit 1; `test_every_declared_dependency_is_pinned_exactly` and the lock-file test failed |
| CP-665 holds on today's tree and on the edited test | `uvx ruff@0.16.10 format --check .` and `uvx ruff@0.16.10 check .` on the branch tree; `uv run --locked ruff format --check` and `ruff check` on the edited `test_pins.py` | 277 files already formatted, exit 0; All checks passed, exit 0; both on the edited file |
| No other test or tree file reads `tests/requirements.txt` | `grep -rn requirements` over `tests/` and the tracker's code | only `tests/requirements.txt` itself and `test_pins.py:40`; `test_trace.py`'s hits are SRS-requirement helpers, not the file |
| `playwright==1.63.0`'s Chromium build sits under a dated exception to 2026-11-07 | `docs/nfdr.md` RN-33 | "2026-10-10 to 2026-11-07", build `153.0.8010.12` |

No rule pins output that renders a language-level fact, so there is no language-rendering row.

---

## Out of Scope

- The README. Its suite section (`README.md:89-111`) gives `python3 -m venv`, `source
  .venv/bin/activate` and `python -m pip install -r tests/requirements.txt` (`:99`), and "How it's
  built" names `venv` (`:135`). SDD § 4 RT-4 and § 6's preamble say the suite instructions give `uv sync
  --locked` and `uv run`. The request gives both parts to the next station, "The README's suite section
  and its 'How it's built' line … are the next two stations'", so the gap is handed on as a record gap in
  `deferred_decisions.md`.
- The project card's `Setup command:` and `Test command:`. The request gives them to the next station.
- Every record under `docs/` stays as it is: `nfdr.md`, `SDD.md` and the ADRs keep naming
  `tests/requirements.txt` wherever they cite it as history.
- Moving any pin, adding or removing a test dependency, or changing `requires-python`.
- The suite's run on Python 3.11 itself (`uv run --python 3.11 pytest tests/`, SDD § 11 R-8). QC-60
  states that "no stage runs it". It is not a check QC-60 requires of this change, and CP-667 states
  the review QC-60 does require.
- `tests/integration` and `tests/e2e`. They need not be run for this change. CP-664's commands are the
  ones the request names.
- QC-40's dependency-graph confirmation. QC-40 assigns it to "the first review after `uv.lock` is on
  `main`", which is a later change's review, not this one's.

---

## Locked Answers (the divergence record — self-review 2026-10-29)

- **Gap 1 — the versions `uv.lock` fixes beyond the four pins (CP-659):** `uv.lock` fixes every version
  `tests/requirements.txt` fixes today. A plain `uv lock` does not: it picks `ast-serialize 0.13.1` and
  `pluggy 1.7.0`, where the pip file has `0.12.1` and `1.6.0`. (b): the request says "no dependency
  version changes" but does not say whether the packages the pins pull in are included. Keeping them is
  the conservative, reversible reading. SRS C-8, which ADR-0013 traces to, also asks that a fresh copy
  get "the same test dependency versions the suite last passed with". A later change may move them
  under QC-40's review.
- **Gap 2 — `pyproject.toml` holds still apart from its comment (CP-660):** (b): the request forbids a
  changed, added or removed pin. The spec reads that as "no table changes or appears either", because a
  constraint table would add pins by another name. The Verified Claims show CP-659 can be met without
  one.
- **Gap 3 — what the new lock-file test asserts besides presence (CP-662):** it also fails when a
  declared dependency is not fixed in `uv.lock` at its declared version. (b): the request names only the
  missing-file case. Today's test also asserts that every declared dependency is in the lock file
  (`tests/architecture/test_pins.py:49-51`). Carrying that assertion over to `uv.lock` keeps the
  replaced test from weakening. Its other assertion, that every line is `name==version`, has no
  counterpart in `uv.lock`'s format and is not carried.
- **Gap 4 — `uv lock --check --offline` (CP-658):** (e): NFDR QC-39's *verified by* says the command
  exits "0 otherwise, `--offline` included". The request names only `uv lock --check`.
- **Gap 5 — the format and lint gates (CP-665):** (e): NFDR QC-62's rows run over the tree, and the
  change edits a Python file in it. The request leaves them out.
- **Gap 6 — QC-40's advisory review (CP-666):** (e): QC-40 makes "a change that … chooses the lock file's
  format" a review moment at `development-design`, and adds a check "at every review". This change makes
  `uv.lock` the lock file. The station puts "QC-40's review moment" outside this seed. The spec reads
  that as the dependency-graph confirmation after `uv.lock` is on `main` (Out of Scope), because the
  advisory check is required of this change and folds in.
- **Gap 7 — QC-60's review (CP-667):** (e): QC-60's *verified by* is a review at `development-design`
  for a change that uses a language or library feature, and the edited test does. The station hands on
  "QC-60's Python 3.11 run", and the spec hands that on too (Out of Scope).
- **Gap 8 — the README is left unchanged:** (b): the request allows correcting "a README sentence this
  change makes false". The one such sentence, `README.md:99`, is inside the suite section, and the
  request reserves that section for the next station. The README is left whole for that station rather
  than half-rewritten here. Until it lands, `README.md:99` names a file this change deletes.
- **Gap 9 — the lock-file test is replaced (CP-662):** (f): the request names
  `test_the_lock_file_exists_and_every_line_is_exact` as the test that reads the old file. It is the
  one existing test that changes. It keeps asserting that the lock file exists and holds every declared
  dependency, now of `uv.lock`. Its name is the developer's to choose.
