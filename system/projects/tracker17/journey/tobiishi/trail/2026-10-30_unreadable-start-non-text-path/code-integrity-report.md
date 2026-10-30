# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

## The deferrals

None. The newest implementation marker carries no `Deferred:` line.

## What was reviewed

The change's production diff in `products/tracker17/main.py` and `products/tracker17/web/pages.py`, and its three new test modules: `tests/unit/test_unreadable_message.py`, `tests/integration/test_unreadable_path.py` and `tests/integration/test_unreadable_start.py`.

## The intent it was checked against

`tl_instruction.md`, `change_spec.md` (CP-757 to CP-772), `change_design.md` and `change_text.md`, all in this change's folder. `docs/fdr.md` was named by the spec's own rules and no behaviour was read from it. Every expectation comes from those files. The whole-page text was taken from the page the merge base serves.

## The tests added or fixed

Added:

- `test_unreadable_byte_page_differs_only_in_the_location`: the whole page for a byte path. The title and heading had no test on such a path, and `change_text.md` states them.
- `test_unreadable_byte_path_answers_as_a_plain_path_does`: the status and headers of a byte path against a plain one, across reads, `PUT`, `HEAD`, the stylesheet, a same-origin `POST` and the refused requests. CP-758 says "as on a path with no such byte", and only two headers had been checked.
- Rows in the existing line and page cases: `only-the-byte` and `relative-stays-relative` on both, and `at-both-ends` and `before-valid-text` on the page. Design T11 says a direct formatter does not resolve or rewrite a path, and that had no test.

Fixed:

- `test_unreadable_page_keeps_ordinary_representations`: it matched a fragment of the page and compared the served bytes with the builder's own output. The instruction asks for the complete text and bytes against independent pre-change expectations, and it now compares both with the page written out.
- `test_unreadable_start_prints_then_serves_and_stops`: removed `listing(file.parent) == listing(tmp_path)`, which compares a folder with itself and cannot fail. Added the `Cache-Control` check on the first read and the check that the served page holds no marker or replacement mark.
- `tests/integration/test_unreadable_start.py`: `%` templates replaced by f-strings and byte concatenation, as `conventions.md:35` requires. Removed the unused `LINE_OPENING` constant and the unused port in the helper's return value.

## Test evidence

- An earlier run of the test command exited 1 and printed `Environment: owners-mac — no CI`.
- That run: 1 failed, 3271 passed, 2 skipped. The failure was the reviewer's own new test, settled under *Calls made*.
- The run this verdict rests on exited 0: first invocation 3272 passed, 2 skipped; second invocation 122 passed.
- Ruff format, Ruff lint and mypy, at the commands the instruction names, all pass on the same tree.
- Task 2's four product-root checks against the merge base: the documents and instructions, the existing tests and the other product paths each show no difference, no file is untracked, and the production diff changes only the two display fields, the page's private support and docstrings.

Checks outside the card's run, on disposable clones in a Linux container on the official Python 3.13 image:

- The final test modules: 305 passed, no skip. `test_unreadable_start_preserves_a_real_byte_named_saved_file` ran for real there. It skips on the owner's Mac, whose file system refuses the name, so the developer could not run it.
- CP-769, on the merge base's two production files with the new tests: the three primary proofs fail. The line and the site raise `UnicodeEncodeError`, and the real start ends with status 1 and empty standard output. All 305 cases give 293 failed, 12 passed.
- Deliberately broken code, each case run against the three modules:

| The break | Cases that failed |
|---|---|
| Page writes uppercase hex | 131 |
| Page skips the HTML escape | 1 |
| Page stops one marker short of the top of the range | 9 |
| Page also escapes U+DC7F | 1 |
| Page spells the surrogate as `\udce9` | 154 |
| Line writes the raw location | 149 |
| Line uses a replacement mark | 152 |

## The finding

No bug in the product code. The code does what its intent says. The review's findings were in the tests: one assertion that could not fail, one comparison weaker than the instruction asked for, and the untested behaviours listed above. All are fixed.

## Calls made

- **Question:** does a `PUT` to `/` count among the answers that carry no location? The reviewer's first draft of the new comparison test said yes, and it went red.
  **Readings weighed:** (a) a request that is neither `GET` nor `POST` should get an answer with no location; (b) CP-758's "every address, whatever its query, gets the one unreadable-data page" covers it, so the page and its location are right.
  **Taken:** (b). The test was wrong, not the code, and the `PUT` moved to the group compared on status and headers. No rule of the spec asks for (a), and it is the smaller, easier-to-reverse answer.
  **Whose document:** `change_spec.md`, the Product Owner's.
  **If ruled the other way:** the unreadable site would need a new answer for those methods, which is a change to the route policy and a change of its own.

## Placement

- The unreadable line's location field, in `main.py`: owned by `main`, which writes the start messages (`docs/SDD.md` § 3). Already there.
- `_shown_location` and its three range constants, in `web/pages.py`: owned by `web`, which builds each whole page (`docs/SDD.md` § 3). Already there. `web` may not import `main` (`docs/nfdr.md` QC-16), and `change_design.md` accepts the parallel helper.

Nothing was moved, and no logic lacks an owning part.

## The language resolution

Python, chain step 1, `project.md` `Languages:`. The Python packet's `README.md` was opened, with `conventions.md`, `quality_gates.md`, `environment.md` and its Testing destination `testing_python.md`.

- `conventions.md:35`, "**Interpolation is an f-string.**": the new start module diverged, and the code changed to follow the packet. A bytes template has no f-string form, so the line's expectation is built by concatenation.
- `quality_gates.md:66` and `:76`, Ruff and mypy: followed, and all pass.
- `testing_python.md`, "The seam is a hand-written fake": no new test patches a product module, and the real-start tests use child processes.
- `environment.md`, the Linux container default: the card's run went where the gate tool sent it, which is the owner's Mac because the product has no CI. The Linux runs above are extra evidence and are not the gate.
