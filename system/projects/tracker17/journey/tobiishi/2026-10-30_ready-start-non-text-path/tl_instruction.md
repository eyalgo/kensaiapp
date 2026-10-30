# Tech Lead instruction — ready-start-non-text-path: display undecodable path bytes at a readable start

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every product path below is relative to it.
**Scope:** Render the readable ready message's location and prove a real start prints it, serves and stops quietly, per `change_spec.md` CP-747–CP-756 beside this file.

This is the developer scaffold for `tracker17 · tobiishi · 2026-10-30_ready-start-non-text-path`.
It owns the task cut, verification gates and review decisions. The behaviour is owned by
`change_spec.md`; placement and the approach are owned by `change_design.md`, both beside this file.
Commands labelled **instance root** run at the change worktree's root; all other commands run at
the product root above. Keep the published text to `change_text.md` beside this file when present.

## Project layout

```text
products/tracker17/
  main.py                              ← modified
  tests/
    unit/test_start_message.py         ← new
    integration/test_ready_start.py    ← new
```

Use the existing test directories; create no package or `__init__.py` for this change.
The owning part is `main`, which writes start messages (`docs/SDD.md:L220-L236`, § 3,
the `main` row). Keep the transform private to `main.py` and retain `_ready_line`'s arguments
and string result (`change_design.md` § 2; `main.py:L161-L165`, `_ready_line`).
The module set and allowed/forbidden imports remain those in `docs/nfdr.md:L180-L211`, § 1.2,
QC-13–QC-19; in particular, no product part imports `main`, and no runtime third-party import
is allowed. Use no new dependency.

## TL Review Notes

Decisions by the Tech Lead, 2026-10-30:

- **Task cut:** The design's § 2 declares a single delta instead of separate sub-jobs.
  Task 1 keeps the formatter and both new test modules together because they prove one
  production responsibility (`change_design.md` § 2, “Single delta”, and § 5 T1–T6).
  T2 is the strict missing-data test's red observation, not another lasting test of old code
  (`change_design.md` § 5 T2; `change_spec.md` CP-752).
- **Review lane:** Task 2 carries the branch-only check that existing tests and other product
  files are untouched. It is a review-verified deliverable rather than a suite test: a later
  change must be free to edit those files (`<CORE>/prompts/tech_lead_create_tl_instruction.md`
  Step 3, “A check that holds only for this change”). T7–T9 remain verification gates, not
  invented new behaviours (`change_design.md` § 5 T7–T9).
- **Environment isolation clarified:** For the strict ASCII and non-strict cases, make the child
  environment explicit, including removal of inherited console and UTF-8-mode overrides where
  they would change the selected case. Otherwise T5 could pass while exercising the same
  strict UTF-8 setting twice (`change_design.md` § 5 T5; `change_spec.md` CP-750, CP-754).
- **Skip boundary clarified:** Attempt the byte-bearing directory creation separately from
  writing valid saved data. Only an actual refusal of that name permits the valid-file
  parameter to skip; a subsequent write, import, bind or request failure must fail the test.
  This keeps CP-753's exception from hiding unrelated setup errors (`change_design.md` § 5 T3).
- **Expected output clarified:** Apply T4's independent expected text to the real-start tests
  too. Building the expected path with the formatter under test would let the same wrong
  representation pass both sides of the comparison (`change_design.md` § 5 T1, T4–T6).
- **Language resolution:** Python, step 1, from the `Languages:` field in
  `system/projects/tracker17/project.md:L12-L12` (instance-relative); packet read:
  `<CORE>/doctrine/engineering/languages/python/README.md`. Preserve the product's Python 3.11
  floor (`docs/nfdr.md:L564-L575`, QC-59–QC-60).
- **Gate completeness:** Add the packet's compile check over the three changed Python files
  alongside the product's QC-62 checks, so the gate names both packet requirements
  (`<CORE>/doctrine/engineering/languages/python/quality_gates.md` § The two gates).

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git -C products/tracker17 ls-files listed the product's tracked source, tests, docs, README.md, .gitignore, pyproject.toml and uv.lock, with no CI configuration or runner script. A repository-wide git ls-files inventory contained 6166 files; inspection for CI service directories, pipeline/build configuration names and YAML files returned 0 candidates."
  },
  "decisions": {"override": null, "amd64": null},
  "candidates": [
    {
      "language": "python",
      "image": "docker.io/library/python",
      "image_source": {
        "root": "core",
        "file": "doctrine/engineering/languages/python/environment.md",
        "anchor": "Start a container from the official Python image, `docker.io/library/python`, tagged with CI's"
      }
    }
  ],
  "guest": null
}
```

### Task 1: Render the readable ready path and prove real startup (`main.py`, `tests/unit/test_start_message.py`, `tests/integration/test_ready_start.py`)

**Dependencies:** None

**What to build:** Display formatting only for the location field of `_ready_line`, with isolated
formatter tests and real child-process startup tests. Keep the original `Path` in all filesystem
operations and retain the existing absolute-path calculation, announcement write and lifetime
(`change_design.md` § 2, Boundary contract; `main.py:L113-L141`, `_serve_claimed`).

#### Behaviours to verify

Add the following coverage to `tests/unit/test_start_message.py`:

- `test_ready_line_escapes_each_filename_byte` — cover every marker from U+DC80 through U+DCFF,
  including both endpoints. Each yields its corresponding byte as a backslash, `x` and two
  lowercase hex digits in the complete ready line. Expected fixture text must be independent of
  the production renderer (CP-748, CP-749; design T4).
- `test_ready_line_preserves_byte_positions_and_other_text` — cover consecutive and separated
  markers, markers in different path components, and a mixture with valid Unicode and literal
  backslashes. Preserve all non-marker characters in order; exclude replacement marks and
  surrogate-code-point spellings (CP-748, CP-749; design T4, T6).
- `test_ready_line_keeps_ordinary_paths_verbatim` — distinct fixtures for plain text, valid
  `café`, and a literal folder name `a\xe9b`. Assert the entire ready line, including its address
  before its location, without changing existing tests (CP-751; design T6).

Add the following coverage to `tests/integration/test_ready_start.py`:

- `test_readable_start_prints_non_text_path_and_serves` — parameterize the same real-start proof
  for missing saved data and a valid `tracker.json` containing a named project. Derive the path
  from a test-owned temporary directory with a component decoded from bytes containing `0xe9`.
  Pass the original path to a child entering through the existing two-argument `main.start`.
  Explicitly set `PYTHONIOENCODING=utf-8:strict`. Assert the complete first stdout line as raw
  bytes, with the four literal escape characters and an independently specified expected path,
  never an expectation built by the production formatter. Extract the actual bound address from
  that line and require `GET /` there to return 200. Require the empty tracker for missing data
  and the named project for valid data. Send SIGINT, require exit 0, empty stderr and no output
  after the first line. The valid file's bytes remain identical after reads and stop
  (CP-747, CP-748, CP-752, CP-753, CP-755; design T1–T3).
- The missing-data parameter above never skips. The valid-file parameter skips only when the
  test's attempt to create the byte-bearing directory is refused by the filesystem; report the
  actual refusal. Do not infer refusal from the OS or catch unrelated setup failures as skips
  (CP-753; design T3).
- On unchanged production code, the strict UTF-8 missing-data parameter must fail on its success
  assertion with the child's status 1, empty stdout and `UnicodeEncodeError` visible in its
  diagnostic. Diagnose early exit rather than waiting for a readiness timeout. The lasting test
  asserts successful startup; it reads no Git history and has no baseline-dependent expectation
  (CP-752; design T2).
- `test_readable_start_path_is_independent_of_console_policy` — repeat the missing-data proof
  for strict ASCII, the C locale and Python UTF-8 mode, including a path with consecutive
  `0xe9` and `0xff` bytes. Use an otherwise ASCII path for the strict ASCII console. Remove
  inherited `PYTHONIOENCODING` for non-strict variants and explicitly control locale, locale
  coercion and UTF-8 mode so each variant exercises its named console. Assert the complete raw
  line with lowercase byte escapes, no raw non-text byte, no replacement mark and no
  `\udce9` spelling. Require the same serving and quiet-stop proof as above
  (CP-748, CP-750, CP-754; design T5).
- `test_readable_start_preserves_ordinary_and_mixed_paths` — on a strict UTF-8 console, cover
  plain text, valid UTF-8 `café`, a real backslash in `a\xe9b`, and a path mixing valid Unicode
  with a non-text byte. Assert the whole line's bytes, retaining UTF-8 for the valid `é` and
  literal backslashes. Require HTTP 200 at the printed address and quiet SIGINT exit
  (CP-749, CP-751; design T6).

Keep new process helpers local to `tests/integration/test_ready_start.py`. Use a free loopback
port, raw pipes, deadlines for readiness, requests and shutdown, and unconditional child cleanup
with bounded reap. Retain bytes read after the first newline for the no-extra-output assertion.
Patch no product name and use no shared literal temporary location (design § 5, Harness boundary;
`tests/integration/test_start.py:L114-L215`, `_Child` and `_Starts`). Each test module's opening
docstring names the CP rules and NFDR obligations it checks (`docs/nfdr.md:L157-L173`, QC-11).

#### Implement

Infer from failing tests.

```text
# Hint:
Walk the path's decoded text in order. Recognize only Python's filename-decoding surrogate-escape
range, recover each represented byte, and emit its lowercase two-digit escape. Copy other
characters verbatim. This is display formatting at `_ready_line`, independent of the console
encoding; do not reconfigure stdout, catch a failed write as the rendering strategy, or escape
the entire path as a Python literal. See [Python 3.11 codecs](https://docs.python.org/3.11/library/codecs.html#error-handlers)
and CP-748 to CP-751 (design § 4).
```

#### Verification gate

From the **instance root**, run the new tests:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/unit/test_start_message.py products/tracker17/tests/integration/test_ready_start.py
```

From the product root, run the packet's compile gate and the quality checks fixed by
`docs/nfdr.md:L576-L593`, QC-62:

```sh
uv run --locked python -m compileall -q main.py tests/unit/test_start_message.py tests/integration/test_ready_start.py
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy main.py errors.py domain application persistence web
```

From the **instance root**, run the card's full command:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/
```

Pass: every new behaviour above passes, with only the evidence-backed valid-file refusal
parameter eligible to skip. All four quality commands exit 0; the full suite has no new failure,
including existing first-output, refused-start, unreadable-start, lock-release and quiet-stop
checks (CP-756; design T7–T9). Keep the existing layer-5 test
`tests/e2e/test_first_project.py::test_the_first_output_is_the_ready_message_address_before_location`
untouched and passing (CP-755; design T7).

### Task 2: Review the change's scope and test continuity (`main.py`, `tests/`)

**Dependencies:** Task 1 — its formatter and new tests are the deliverables reviewed here.

**What to build:** A review verdict against each criterion below, recorded in Developer Review
Notes. These are checks of this change's diff, not additions to the lasting suite.

#### Deliverables verified by review

- Only `main.py` and the two new test files change within the product. From the product root,
  `git diff --name-only "$(git merge-base main HEAD)" -- . ':!main.py' ':!tests/unit/test_start_message.py' ':!tests/integration/test_ready_start.py'`
  must print nothing. This includes retaining every existing ready-message assertion and leaving
  product documents, dependency pins and other production parts untouched
  (CP-751; design § 2 and T7–T9).
- Read `git diff "$(git merge-base main HEAD)" -- main.py` from the product root. The only
  changed production responsibility is the readable ready line's displayed location. Signatures,
  original filesystem path, absolute-path calculation, claim/load/bind decisions, single flushed
  announcement and stop lifetime retain their contracts. No unreadable message/page,
  refused-start message or failed-action output changes; no stdout reconfiguration or new OS
  check appears (design § 2, Boundary contract; `change_spec.md` § Out of Scope).
- Read `git diff "$(git merge-base main HEAD)" -- tests/unit/test_start_message.py tests/integration/test_ready_start.py`
  after the new files are tracked. The lasting tests assert success on the code beside them;
  they read no historical commit, primary checkout or machine-owned fixture. Their cleanup and
  skip logic meet Task 1's criteria (design T2–T3 and Harness boundary).

#### Implement

Verified by review — no test.

#### Verification gate

Run the review commands above from the product root. From the **instance root**, run:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/
```

Pass: every review criterion holds, each has an explicit verdict in Developer Review Notes, and
the full suite has no new failure. The suite includes QC-61's architecture walk and the retained
QC-55 first-output proof (`docs/nfdr.md:L641-L717`, § 10 Verification map).
