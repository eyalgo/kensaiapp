# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `2026-11-13_pins-test-reads-behave-lock` (tracker17) — the pins test reads the Behave
folder's manifest and lock.
**Mode:** workflow. **Reviewer:** Senior Engineer, `development-code-integrity`.

## Deferrals

**None.** The newest `developer: 2026-11-13_pins-test-reads-behave-lock — implementation complete`
marker (`<a commit not in the public history>`) carries no `Deferred:` line and no `Failing:` line, so there was nothing to
check.

## What was reviewed

`products/tracker17/tests/architecture/test_pins.py`, the only file the change touches inside the
product. The change's code commits are `f819265ae` to `<a commit not in the public history>`. The file holds the tightened
`EXACT` pattern, the new helpers `pinned_pair`, `locked_pairs` and `read_toml`, the check
`behave_findings`, the `product_copy` fixture and the new tests. The four root tests were also read,
to confirm CP-781.

## The intent it was checked against

- `tl_instruction.md`, Tasks 1 to 4 and their *Behaviours to verify*: the primary intent.
- `change_spec.md`, rules CP-773 to CP-784, its Examples and its Locked Answers (Gaps 1 to 5).
- `change_design.md` §§ 4 and 5, and the Architect Review Notes.
- `docs/fdr.md` adds nothing here: the design records that it does not name the pins test or
  `.behave`.

## Tests added or fixed

Two tests were added and none was fixed. Every existing test already matches the intent.

- **`test_a_name_the_lock_does_not_hold_is_found`** (CP-776). The rule says the lock must hold a
  record "whose name equals the declared name **and** whose version equals the declared version".
  Every existing lock-mismatch case changed the version and kept the name, so a check that compared
  only versions would have passed the whole file. The new case declares `requests==0.28.1`. That is a
  name the lock does not hold, at the version the lock fixes for `httpx`, so only the name can catch
  it. Proved to tell the two apart: a copy of the file whose check compares versions only fails this
  test and no other (1 failed, 24 passed).
- **`test_a_separator_run_is_still_fixed_by_the_lock`** (CP-776). The rule says "any run of `-`, `_`
  and `.` counts as one `-`". The Behave side tested case-folding and dropped extras, and nothing
  tested separator folding. The design rests that on "the `normalized` the root lock test already
  uses", but no root case exercises it. The new case declares `typing_.extensions==4.16.0` against
  the lock's `typing-extensions` 4.16.0 and expects no finding. Proved to tell the two apart: a copy
  of the file whose `normalized` only lowercases fails this test and no other (1 failed, 24
  passed).

Both copies were throwaway files in the change worktree's test folder. They were removed after their
runs, and the tree was checked clean apart from the edit above.

## The finding

**No bug found, and nothing was moved.** The code already did what its intent says. The two added
tests were green on the code as committed. They close two gaps where the suite would have stayed
green over a wrong check. Each was proved against a deliberately broken copy, as above.

Checked against the spec, beyond the suite:

- **CP-780.** After both halves of the card's command ran, `git status --porcelain --
  products/tracker17/.behave` printed nothing.
- **CP-781.** The four root tests keep every assertion. The one edit in them replaces the in-test
  parsing of `wanted` with `pinned_pair`, which does the same split, normalization and extras cut.
- **CP-782, re-run by this review.** In a fresh clone at `84d492b09`, made with `mktemp -d` and
  removed from outside in a command of its own, `playwright==1.65.1` was changed to
  `playwright==1.65.0` in `.behave/pyproject.toml` only. Then `uv run --locked --project . pytest -q
  tests/architecture/test_pins.py` was run from the clone's product folder. It exited 1 with `4
  failed, 19 passed`, and
  `test_the_behave_folder_of_the_product_holds_every_pin` was among the failures. With the change
  reverted it exited 0 with `23 passed`. The other three failures edit or rely on the same pin, as
  the developer's marker records.
- **CP-783.** The diff against the merge base, inside the product, lists
  `tests/architecture/test_pins.py` alone. This review adds to the same file only.
- **QC-62.** `ruff format --check` reported `1 file already formatted`, and `ruff check` reported
  `All checks passed!` over the file after the additions.

**Test evidence.** The full card ran once, through the gate tool (`--gate code-integrity`, no CI,
no owner's ask), and that run is the verdict's. It exited 0. The first half's last line was `3297
passed, 2 skipped, 6 warnings in 396.17s (0:06:36)`, and the second half's was `122 passed, 6
warnings in 55.95s`. The developer's closing run had 3295 in the first half, and this review's two
tests account for the difference. The six warnings are pytest's `rm_rf` notices about leftover
temporary folders from other test files. Nothing in this change raises them.

## Calls made

- **Does CP-776's lock comparison cover a requirement that is not an exact pin?** CP-776 reads "fixes
  each dependency CP-773 reads at its declared version". The readings weighed were (a) compare
  every declared entry with the lock, or (b) compare only entries `EXACT` accepts, because an entry
  that is not one already fails under CP-773 and has no single version to look up. The developer
  took (b) and recorded it. This review confirms (b): the pins test fails on such a manifest either
  way, as CP-776 requires, and (b) gives one finding per defect, which the design's "each failing
  case asserts its own finding" relies on. **Owner:** the Product Owner (`change_spec.md`). **If
  ruled (a):** an entry that is not pinned exactly would also get a lock finding. That is a one-line
  change to the comparison's filter, and no test would change verdict.

## Placement

**No owning part, because this is test code.** `docs/SDD.md` § 3's five parts (`domain`,
`application`, `persistence`, `web`, `main`) own tracker behaviour. The new logic is `EXACT`'s
tightening, `pinned_pair`, `locked_pairs`, `read_toml`, `behave_findings` and the `product_copy`
fixture, and all of it is layer-6 test code. NFDR QC-39's *verified by* and CP-783 place it in
`tests/architecture/test_pins.py`, where it is. Nothing was moved, and no placement commit was made.

## Language resolution

Python, answered at step 1 of the chain (`project.md` `Languages: Python`). The packet read was
`<CORE>/doctrine/engineering/languages/python/README.md` with its concern files `toolchain.md`,
`layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md` and `environment.md`, plus
`testing_python.md`. `<CORE>/doctrine/engineering/arch_defaults.md` and
`<CORE>/doctrine/engineering/testing_doctrine.md` were read beside them. The code meets that bar:

- **The check builds no collaborator.** It is handed the folder it reads (`conventions.md`, *A module
  is given its collaborators*).
- **Every file a test touches is real data that the test is allowed to read.** The case tests touch
  files only under `tmp_path`, and the product test reads the committed tree beside it.
  `testing_doctrine.md` § *A test reads nothing of the machine it runs on* allows both, and layer 6
  reads real files by design (`testing_python.md` § Layer 6).
- **`read_toml` catches only `OSError`, `UnicodeDecodeError` and `tomllib.TOMLDecodeError`**
  (`errors_logging.md` § Catching).
- **Imports, typing and line length follow the house rules:** `from __future__ import annotations`,
  builtin generics, `pathlib`, and 100 columns. Test functions carry no annotations, which
  `conventions.md` § Typing records as the house form.

No packet departure arose, so `deferred_decisions.md` is not written.

## For the PM

This change makes one record false, and it lies outside the change's reach. The plan and the marker
both record it: `docs/nfdr.md` QC-39, *verified by*, "The entry starts unmet in its test". The CP-782
re-run above is the evidence that its correction can cite.
