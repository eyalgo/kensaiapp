# Tech Lead instruction — failed-action-path-non-text-byte: pin the console report of a failed action at a non-text-byte path

**Category:** bug
**Behaviour:** preserving
**Language resolution:** Python — step 1, `project.md` `Languages:` — packet README.md opened, with every concern file it routes (`toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`, and `testing_python.md`)
**Product root:** `products/tracker17` — every path below is relative to it.
**Scope:** add one characterization test of `Site._report_failure` (`web/routes.py`); change no production code.

---

## Project layout

```
products/tracker17/
  tests/
    integration/
      test_failure_report.py     ← new
```

No production file is created or modified. `web/` is the subject and stays as it is; it changes only under the spec's conditional fix (a raise or a rewritten path), which the spec measured as not arising.

Parts table (`docs/SDD.md` § 3) read: the subject is `web`'s one catch-and-report site (OB-3). The test adds no logic to any part.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Task shape chosen:** the design's §5 adds a test for behaviour the code already has, and the spec measured it green at the base. The plan writes the one task in the already-green shape (`Tests cannot go red.` with a `Reason:` line), because no test of these behaviours can be made to fail first without changing production code. Not the relocation shape: nothing moves.
- **Behaviour added:** `test_failed_action_answers_with_its_failure_response` — implied by the design's table row "writing raises nothing" (`Site.handle` returns the action's failure response and nothing propagates); the design names it as an assertion but not as a behaviour with its own name, so it is named here.
- **Action fixed:** the design says to pick an action whose sentence names no typed value. The comment add on a task that does not exist qualifies: `Site._comment_failure_line` (`web/routes.py`) returns `The tracker couldn't add your comment, and nothing was changed.` when the task is not read, so line 1 holds neither `caf` nor `\xe9` whatever is typed. The comment-add request is posted to a task number the empty state does not hold.
- **Two checks that hold only while this change is built** — "the guard fails under the mutation, and the revert leaves `web/routes.py` unchanged" and "the spec's `git grep` prints nothing at the base and the new module after" — are stated as review-verified gate lines on the task, each against the branch's merge base, never as suite tests (Step 3 of the shared body). A mutation test in the suite would assert a fixed change forever.
- **Gate environment inputs:** the product has no CI configuration (tracked-file inventory found none) and no environment decision in its decision files, so `ci` carries the `none` finding and `candidates` is empty. The chain asks the gate tool what that resolves to.
- **Nothing reordered, split or upgraded:** one module, one cohesive responsibility, no build sequence; no imprecise type is involved. The design's §4 hint for the test is carried as a `# Hint:` block, cut back to the approach.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {"finding": "none",
         "inventory": "git ls-files filtered for any build-service, pipeline, runner or workflow configuration (a .github folder, GitLab, CircleCI, Travis, Azure Pipelines, Jenkinsfile, Buildkite, Drone, Bitbucket Pipelines, AppVeyor, Cloud Build, Woodpecker, tox, nox) returned no file"},
  "decisions": {"override": null, "amd64": null},
  "candidates": [],
  "guest": null
}
```

### Task 1: Characterization test of the failed-action console report (`tests/integration/test_failure_report.py`)

**Dependencies:** None

**What to build:** one new integration-layer test module that pins what `Site._report_failure` writes to the console's error stream when an action fails with an `OSError` whose text holds `os.fsdecode(b'/tmp/caf\xe9')` (`/tmp/caf\udce9`), in two error forms. The module's docstring names `Site._report_failure` in `web/routes.py` (so the spec's `git grep` prints the module), SRS NFR-8 and AC-18, `docs/CONTENT.md` RN-35 and SDD § 4 OB-3. Every path the docstring names is written from the product root (`docs/CONTENT.md`, not `CONTENT.md`), because the TS-4 pointer test checks each one there, and every requirement identifier it names is in `docs/SRS.md`. The module defines no class that defines `save` or `now` and none based on a test-support class (TS-6, QC-64); its one test class is a `Tracker` subclass whose comment-add action raises the case's `OSError`.

#### Behaviours to verify (developer adds tests to `tests/integration/test_failure_report.py`)

Both are parametrized over the two error forms; `path` is `os.fsdecode(b'/tmp/caf\xe9')`:
- message form: `OSError(f"cannot write {path}")`, whose line 2 is exactly `OSError: cannot write /tmp/caf\udce9`;
- errno form: `OSError(92, "Illegal byte sequence", path)`, whose line 2 is exactly `OSError: [Errno 92] Illegal byte sequence: '/tmp/caf\udce9'`.

- `test_failed_action_prints_its_sentence_then_the_error_as_reported` — layer 3 Application — fakes: the `Tracker` subclass handed to `Site` (raises the case's error from its comment-add action); the existing `SwitchedSaver` over `SavedData` in `tmp_path` and the existing `MovableClock`, both imported from `test_task_routes`, handed to the tracker's constructor — the stream's bytes hold exactly two lines. Line 1 equals `The tracker couldn't add your comment, and nothing was changed.` and holds neither `caf` nor `\xe9`. Line 2 equals the form's line above, once per form, and holds no `\xe9`. Nothing follows line 2.
- `test_failed_action_answers_with_its_failure_response` — layer 3 Application — fakes: as above — the request returns the comment add's failure redirect (the same response the neighbouring `Breaking` test in `test_comment_routes.py` asserts) and nothing propagates, so writing the path raised nothing.

The stream is a text wrapper over a byte buffer that the test builds with `encoding="utf-8"` and `errors="backslashreplace"` and aims `sys.stderr` at for the request; the assertions read the buffer's bytes. The test patches no name inside `web` (TS-2).

#### Held by review (omit when every rule of this task reaches a test)

- **TS-6 / QC-64 — no stand-in is added:** the module defines no class with `save` or `now` and none whose base a test-support module defines. The QC-64 walk does not exist yet (NFDR RN-65), so this is held by reading the diff.
- **TS-2 — the test hands in what it needs:** the failure enters through the handed `Tracker` subclass and the stream is swapped through the standard library; no product name is patched. Held by reading the diff (QC-28's walk flags only a patch aimed at a product module).

#### Implement

Tests cannot go red.

Reason: `Site._report_failure` already writes the sentence, then `<kind>: <text>`, with the path as `\udce9`, and raises nothing; the spec measured this at the base on the console's own stream, and no earlier task builds it.

# Hint: run the request inside `contextlib.redirect_stderr` aimed at an `io.TextIOWrapper` over an `io.BytesIO`, with `encoding="utf-8"` and `errors="backslashreplace"` — the handler Python opens `sys.stderr` with. Flush it before reading the buffer. Do not use `capsys` or any pytest capture: they encode strictly and raise on the message form, which is the capture's fault and not the tracker's. The failing action is the `Breaking(Tracker)` precedent in `test_comment_routes.py`: override the tracker's comment-add action to raise, hand the subclass to `Site`, and post the comment-add request for a task number the empty state does not hold, so line 1 names no title. TS-6 bars a new class that defines `save`, and the existing saver's error is a fixed `PermissionError`, so the failure has to come from the tracker.

#### Verification gate

Run from the change worktree's root:

1. `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` — expected exit 0, the new test among the passes.
2. `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/` — expected exit 0.
3. In `products/tracker17`: `uv run --locked --project . ruff format --check .` and `uv run --locked --project . ruff check .` — both exit 0 with the module in the tree (QC-62).

Pass criteria — run and recorded in `Developer Review Notes`:

- **The guard is real.** Change `Site._report_failure` so it rewrites the path inside the error text to its `\xe9` form; run the new test; see line 2 fail in both forms; revert the change; record the mutation, the failure it caused and the revert. After the revert, `git diff "$(git merge-base main HEAD)" -- products/tracker17/web/routes.py` prints nothing (run in the worktree; it also sees uncommitted edits).
- **The test was absent and is present.** `git grep -n 'report_failure\|Could not save' -- products/tracker17/tests` prints nothing at the merge base (`git grep -n 'report_failure\|Could not save' "$(git merge-base main HEAD)" -- products/tracker17/tests`, exit 1) and prints the new module after the change. The module's own text carries `report_failure` in its docstring.
- **Production code is unchanged** (the spec expects the test alone): `git diff "$(git merge-base main HEAD)" --name-only` lists the new module and nothing under `web/`, `domain/`, `application/` or `persistence/`. If the new test fails on the unchanged tree because the write raises or the path is rewritten, STOP and surface: that is the spec's one case for a fix, and a reclassification event for this plan, not something to patch inside the test.
- No public name of `web` changes: `AddressTaken`, `Listener`, `Response`, `Site`, `UnreadableSite`, `listen`, `listen_unreadable` stay exported.
