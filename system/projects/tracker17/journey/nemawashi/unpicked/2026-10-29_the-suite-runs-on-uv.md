# 根回し Nemawashi seed — the test suite's environment is made by uv

## What it is

Serves the Way `fit-to-publish`, which `system/michi.md` Way 5 ranks above it; cut now because tracker17 is the product the owner runs the crew on (`products/tracker17/docs/PRD.md:L12-L14`), so it moves a product rather than machinery (my reasoning, not a lookup). Moves the Agari toward **Works** (the full automated suite, whose environment this is) and keeps **Simple to set up** true, since the written instructions are what the owner follows.

Today the suite is set up with `python3 -m venv .venv` and `python -m pip install -r tests/requirements.txt` (`products/tracker17/README.md:L97-L99`), and no `uv.lock` exists (`ls products/tracker17/uv.lock` → no such file). The records already say otherwise: ADR-0013 (Accepted 2026-10-29) supersedes ADR-0002, and SDD § 4 RT-4 and NFDR QC-39 name uv. After this, the lock file is `uv.lock` beside `pyproject.toml`, `uv sync --locked` makes `.venv`, every suite command is typed through `uv run`, and `tests/requirements.txt` is gone. The tracker's own setup names uv nowhere.

Bar: `uv lock --check` exits 0; `test_pins.py` reads `pyproject.toml` with `tomllib` and fails on a test dependency not pinned with `==` or on a missing `uv.lock` (NFDR QC-39); `uv sync --locked` then `uv run pytest tests/unit tests/architecture` pass; the README's suite section and its "How it's built" line read uv; `tests/requirements.txt` is deleted.

## Source

Cut from `products/tracker17/docs/SDD.md` § 4 RT-4 and Review Notes RN-62/RN-63 ("`products/tracker17/README.md`'s suite section, `tests/requirements.txt` and the test that reads it are the product's to move, and which unit carries that is the PM's"); `products/tracker17/docs/nfdr.md` QC-39 ("The entry starts unmet"); `products/tracker17/docs/adr/0013-standard-library-only-no-web-framework-suite-environment-made-by-uv.md` § Decision. Product checked 2026-10-29 at `bded0358d`: `ls products/tracker17/uv.lock` → no such file; `ls products/tracker17/tests/requirements.txt` → present; `grep -n 'venv\|pip install' products/tracker17/README.md` → L97, L99, L135; `products/tracker17/tests/architecture/test_pins.py:L39` `test_the_lock_file_exists_and_every_line_is_exact` reads that file; `pyproject.toml:L8` names `tests/requirements.txt`. Named as owed by `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint`'s refine report, its next move 1 (`system/projects/tracker17/docs/nemawashi-refine/2026-10-29_start-tests-under-ignored-sigint_report.md`). Still owed in code, so it holds as stated.

## Stations — dynamic checklist

- [ ] lock-and-pins-test — `uv.lock` committed from the four pins, `uv lock --check` exits 0, `test_pins.py` reads `pyproject.toml` and the lock, `tests/requirements.txt` removed, `pyproject.toml` comments follow
- [ ] readme-on-uv — the README's suite section and "How it's built" give `uv sync --locked` and `uv run`, and the tracker's setup still names uv nowhere
- [ ] project-card-commands — the project card's Setup command and Test command read the uv commands, as SDD RN-63 says they follow RT-4

## Relation to existing work

Independent of `tracker17 · nemawashi · 2026-10-11_protect-saved-data`: neither needs the other, and both can be picked at any point. It follows `tracker17 · nemawashi · 2026-10-29_start-tests-under-ignored-sigint`, retired to `trail/`, which named it.

## Out (later / elsewhere)

QC-40's Dependabot/`uv.lock` review moment and QC-60's run on Python 3.11 (`uv run --python 3.11 pytest tests/`, SDD § 11 R-8) are review gates the owner and the Principal Architect hold (`products/tracker17/docs/nfdr.md`, header, version 19), not tests this seed adds. Any change to a record: ADR-0013 and the NFDR are settled.
