# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `2026-11-12_failed-action-path-non-text-byte` (tracker17) · category bug · behaviour preserving · reviewed at `a18618545`.

## Deferrals

None — the closing marker (`<a commit not in the public history>`) carries no `Deferred:` line.

## What was reviewed

`products/tracker17/tests/integration/test_failure_report.py`, the change's one code file (a new test module), and its subject `Site._report_failure` / `Site._guarded` in `products/tracker17/web/routes.py`, unchanged on the branch.

## The intent it was checked against

`tl_instruction.md` Task 1 (both `#### Behaviours to verify`, the review-held rules, the verification gate), `change_spec.md` (Invariants 3 and 4–6, Structural Goal, Locked Answers Gap 1), `change_design.md` § 5. `docs/fdr.md` not needed beyond what the spec cites.

## Tests added or fixed

None. Each behaviour of the intent already has a test that asserts it:

- Line 1 is the sentence and names no path; line 2 is `OSError: <text>` with the path as `\udce9`, exact, per form; nothing follows; no `\xe9` in either line → `test_failed_action_prints_its_sentence_then_the_error_as_reported[message|errno]` (exact two-line list equality, plus the `caf` / `\xe9` / U+00E9 checks and the trailing newline).
- Writing raises nothing; the action answers with its failure redirect → `test_failed_action_answers_with_its_failure_response[message|errno]` (`location` also asserts 303).
- The stream is Python's console handler (`utf-8`, `backslashreplace`) over a byte buffer, not a pytest capture (Gap 1); the failure enters through a handed `Tracker` subclass; nothing in `web` is patched (TS-2); the one class defines neither `save` nor `now` and has a product base (TS-6 / QC-64).

**Guard checked by mutation, in a disposable clone at `a18618545`, each reverted:**

| Mutation of `_report_failure` | Result |
|---|---|
| Rewrite the path to `\xe9` (raw surrogate and escaped spelling) | prints-test red in both forms; response test green |
| Write the kind line before the sentence | prints-test red in both forms |
| Encode the text strictly before writing (the write raises) | message form red in both tests; errno form green, as its text is already escaped |
| Write an extra line after line 2 | prints-test red in both forms |

The spec's grep (`report_failure\|Could not save` under the product's tests) prints the new module's docstring line on the branch.

## The finding

No issues. Nothing moved, every behaviour already had a correct test, and the full card passed: 3276 passed, 2 skipped (unit through application); 122 passed (e2e). The four new cases are among them. No production file changed (`git diff --name-only` against the merge base lists the module and the change's own journey files only).

## Calls made

- **How the test builds the path.** The module takes `PATH = os.fsdecode(b"/tmp/caf\xe9")` and expects the literal `\udce9`. That expectation holds only where the filesystem encoding is UTF-8 with `surrogateescape`, which macOS always uses and Linux uses under a UTF-8 or C locale (the official Python image sets `C.UTF-8`). Under a Latin-1 locale the decode would give `é` and the test would fail for a reason that is not the tracker's. Readings weighed: keep `os.fsdecode`, or write the surrogate literal. **Kept as written**, because the spec and the plan both name `os.fsdecode(b'/tmp/caf\xe9')` as the case, and the gate's environments (the owner's Mac, the Python image) decode it as the spec expects. Owner: the Tech Lead's plan (`tl_instruction.md` Task 1). If reversed, `PATH` becomes `"/tmp/caf\udce9"` and nothing else changes.

## Placement

Parts table read (`docs/SDD.md` § 3). **No new logic** in any part: the change adds one test module under `tests/`, which the one unit's language frame places at the product root. No placement commit.

## Language resolution

Python — step 1, `project.md` `Languages:`. Packet `languages/python/README.md` opened with every concern it routes: `toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`, and `testing_python.md`; `arch_defaults.md` and `testing_doctrine.md` read beside it. Against that bar: no collaborator built by product code (none written); the test hands its fakes in through `Site` and `Tracker`'s constructor and swaps the stream through the standard library, patching no product name; it reads nothing of the machine but the filesystem encoding noted under *Calls made*. The developer's two recorded departures — the layer-3 location under `tests/integration/` per the product's own layer table, and `-> None` on test functions per the product's mypy configuration — stand: the product's records outrank the packet.
