# Change request — 2026-10-29_uv-lock-and-pins-test

*The PM-minted intake for one **飛び石 Tobiishi** — the single change the chain
(`core/launchers/chain-development/launcher.sh <project>` → `core/tools/chain_development.py`) carries
through the pipeline. Lives at `system/projects/<name>/journey/tobiishi/<key>/change_request.md` (`<key>` =
`<YYYY-MM-DD>_<slug>`). The PM writes this when opening the Tobiishi, through `tobiishi-open`; `development-specs`
reads it as the pipeline's first input — it does **not** coin the key or scan a queue. **No `Project:`
field** — the project is implied by which project's `journey/tobiishi/` this sits in.*

---

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

**Category:** nfdr
**Behaviour:** changing
**Classified because:** the station "the lock is `uv.lock`, and the pin test reads it" is a change an NFDR
row drives (QC-39, "The entry starts unmet"), and it changes what an enforcement command reports — the
pin test now fails on a missing `uv.lock` instead of a missing `tests/requirements.txt`
(`change_classification.md` § *Category notes*, `nfdr`).

**Sizing:** one capability, one honest merge. The acceptance boundary is the station's reached-when
(`lock-and-pins-test`, items 1-4); the lock file, its test and the comment that names it have one source
contract (ADR-0013, QC-39) and cannot land alone.
