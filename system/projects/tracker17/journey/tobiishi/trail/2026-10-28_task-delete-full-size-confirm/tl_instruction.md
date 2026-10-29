# Tech Lead instruction — task-delete-full-size-confirm: full-size Delete task controls

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every product path below is relative to it; commands explicitly name their working directory.
**Scope:** Implement CP-609–CP-618 for `tracker17 · tobiishi · 2026-10-28_task-delete-full-size-confirm`.

This instruction owns the task cut, behaviour checks and verification gates for this change. The change's spec owns its rules, and its design owns the rendering direction.

## Project layout

```text
products/tracker17/
  web/
    pages.py                         ← modified
    style.css                        ← modified
  tests/e2e/
    test_delete_task.py               ← modified: new browser checks
    test_delete_project.py            ← modified: task height assertion and its description
```

No directory, package, public interface or import edge is added. Keep the module set and allowed imports of `docs/nfdr.md:166-197`, § 1.2 “Forbidden imports”; page construction and the stylesheet belong to `web` (`docs/SDD.md:206-220`, “The parts”). The design's § 2 “Blast Radius” confines production edits to that part and test edits to the two modules above.

## TL Review Notes

Decisions below are the Tech Lead's, 2026-10-29.

- **Task cut:** the design has no separate § 3; § 2 instead declares one delta with no new interface or internal ordering dependency. Task 1 uses that delta and its atomic-landing edge: the task confirmation's size and the corrected project-test assertion have no green point between them (design § 2, “Atomic-landing edge”; `tests/e2e/test_delete_project.py:215-220`, move/task height checks). T1–T8 of design § 5 are covered within the same task and its gate.
- **Spec reconciliation retained:** resize both the first press and its confirmation. The spec's “Locked Answers”, Gap 1, corrects the request's premise; the source gives the first press `delete-button` and the strip `TRIGGER_SIZE`, both styled at 28px (`web/pages.py:855-890`, `_delete_strip` / `_delete_section`; `web/style.css:228-244`, row controls; `:314-324`, row-control confirmation). Do not implement only the strip half of CP-609–CP-610.
- **Test isolation clarified:** T1–T3 add tests alongside the existing task-deletion tests, rather than adding height assertions to their bodies, because CP-615 permits only the named existing assertion to change (spec “Tests and checks”, CP-615; design § 5, T1–T6). Update the receiving module's opening description to include the new geometry coverage; retain its SRS references and the already-existing feature pointer (`tests/e2e/test_delete_task.py:1-8`, opening docstring; `domain/tasks.py:17-31`, “Checked by”).
- **Gate coverage:** retain the card's exact non-browser command and add the separately invoked browser suite and QC-62 checks to Task 1's gate. The card command excludes e2e by design (`tests/conftest.py:7-9`, “collection rule”); copying that command alone would leave CP-609–CP-615 unmeasured (spec CP-616–CP-617; `docs/nfdr.md:532-545`, QC-62).
- **Measured baseline limitation:** the required one run of `pytest products/tracker17/tests/` from this worktree collected 2,629 tests and exited 1: `20 failed, 2578 passed, 31 errors in 273.10s`. Its listener setup traceback ends at `self.socket.bind(self.server_address)` with `PermissionError: [Errno 1] Operation not permitted`; the run reported Python 3.15.0. This establishes collection, but no green baseline. The command was not retried with changed permissions, and the browser suite was not run in this planning session. These results do not supply a red-at-baseline lane for Task 1: its new geometry tests do not yet exist. The implementation gate still requires both suites to exit 0.
- **Language resolution:** Python, step 1, from the project card's `Languages:` field. Opened `<CORE>/doctrine/engineering/languages/python/README.md` and its seven concern destinations; the product's locked decisions govern where they differ, per `<CORE>/doctrine/engineering/languages/README.md`, “Precedence”. No new type or library feature is needed by this task.

## Gate environment inputs

The targeted listing `git ls-files | rg -i '(^|/)(\.github/|\.gitlab|\.circleci/|Jenkinsfile|azure-pipelines|buildkite|\.travis|Makefile|justfile)|(^|/)(ci|build|pipeline)[^/]*\.(yml|yaml|toml|sh)$'` returned no paths. A wider build-file listing returned only the root `Containerfile`; reading it found a sandbox image and a shell entry point, with no CI runner or test job (`Containerfile:3-69`, image build and entry point). On that inventory, no CI configuration was found. No environment override or amd64 decision was found by `rg -n 'environment|container|owners-mac|guest|amd64|CI |workflow|runner'` over the product's ADRs, NFDR and SDD; its hits describe the product's virtual environment and status workflow. No container tag is invented from the installed interpreter or the supported Python floor.

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git ls-files | rg -i for .github/, .gitlab, .circleci/, Jenkinsfile, azure-pipelines, buildkite, .travis, Makefile, justfile and ci/build/pipeline scripts returned no paths. Wider git ls-files filtering for build/pipeline/workflow/runner/ci YAML, TOML and Shell files and Makefile/justfile/Jenkinsfile/Dockerfile/Containerfile returned only Containerfile. Read Containerfile in full: sandbox image, shell entry point, no CI runner or test job."
  },
  "decisions": {"override": null, "amd64": null},
  "candidates": [],
  "guest": null
}
```

### Task 1: Full-size task-deletion rendering and browser coverage (`web/pages.py`, `web/style.css`, `tests/e2e/test_delete_task.py`, `tests/e2e/test_delete_project.py`)

**Dependencies:** None

**What to build:** Make every ordinary, backed-out and failed Delete task first press the existing full-size secondary component, and make its confirmation use the existing full-size strip context, with browser measurements proving the absolute and relative height contract. Keep these rendering selections in `_delete_section` and `_delete_strip`. Remove the obsolete task-delete selector from the row-control rules and align their comments; describe the full-size strip rule to cover its task and project callers. These are the existing component selections in `web/pages.py:855-897`, `_delete_strip` / `_delete_section` / `FULL_SIZE`, and `web/style.css:228-373`, row-control and full-size rules; their prescribed use is design §§ 1–2 and spec CP-609–CP-613.

Add the new tests in `tests/e2e/test_delete_task.py` using the real process/browser fixtures in `tests/e2e/conftest.py`. Preserve existing task-deletion test bodies. In `tests/e2e/test_delete_project.py::test_project_strip_uses_full_size_controls`, change the `task_confirm` expectation to `CONTROL_HEIGHT` and align that test's description, retaining its status-move `ROW_CONTROL_HEIGHT` assertion, project measurements and tolerance (CP-615; design § 5 T4).

#### Behaviours to verify

Add these tests to `tests/e2e/test_delete_task.py`:

- `test_delete_task_confirmation_matches_full_size_trigger` — parameterize ordinary and scrolled page-bottom cases. Create the task through the running tracker, measure the first press at `/tasks/1`, and open its confirmation at `/tasks/1?delete_confirm`. In Chromium bounding boxes, the first press and confirming button are each 36px ±0.5 and differ by at most 0.5px; the sentence is at least 35.5px tall and no shorter than the measured first press within 0.5px; Back out is 36px ±0.5. Compare the old first-press rectangle with the sentence in document coordinates across the page loads and assert coverage on both axes, within 0.5px. The scrolled variant reaches the real page bottom before opening confirmation. This test must fail against the pre-change rendering on the required 36px height, rather than treating two equally undersized controls as success (CP-609–CP-612, CP-614; design § 5 T1).
- `test_delete_task_back_out_restores_full_size_trigger` — open confirmation and use Back out; reach `delete_back`, measure the restored first press at 36px ±0.5, verify its focus and the absent strip, and verify the saved bytes are unchanged (CP-609; design § 5 T2).
- `test_delete_task_save_failure_restores_full_size_trigger` — open confirmation, obstruct `tracker.json.partial` in this test's temporary data location with a directory, and press the confirming control. Reach `delete_failed`, measure the restored first press at 36px ±0.5, verify the existing failure line and its description/focus association, and verify the task remains available and the saved bytes are unchanged. Remove the obstruction during cleanup even if the check fails. The obstruction targets the real saver's pre-replacement open (`persistence/saved_data.py:124-130`, partial-file write); use neither a permission-bit assumption nor a patched product name (CP-609; design § 5 T3).

Retain and run these existing checks:

- `test_project_strip_uses_full_size_controls` — after its one corrected height assertion, the task confirming button is 36px ±0.5, the status-move confirming button stays 28px ±0.5, and every existing project-strip measurement remains (CP-613, CP-615; design § 5 T4).
- `test_delete_confirmation_is_keyboard_operable`, `test_double_press_never_confirms_deletion`, `test_completion_survives_actual_reload_back_and_forward`, `test_confirmation_is_loaded_afresh_after_confirming`, and `test_deletion_titles_stay_text_in_the_browser` — preserve their bodies and their keyboard, real double/third click, no-save, history, redirect and escaped-title assertions (design § 5 T5).
- `tests/architecture/test_trace.py` — keep its checks unchanged; the receiving module retains its SRS requirement references and its existing `domain/tasks.py` feature-entry pointer, with every named path resolving (CP-618; design § 5 T6).

#### Held by review

- CP-615 and design § 5 “Baseline and retirement” — only the task confirmation's old height assertion is retired. Compare the two test-module diffs with the branch's merge base: additions in the task module and the named assertion/description correction in the project module; no other existing test body changes. This is a change-specific review, not a permanent test against a fixed revision.
- Spec “Out of Scope” — wording, form destinations, strip part order, focus branches, response policy, deletion/save behavior and the project strip remain as prescribed. Existing tests cover sampled behavior; read the production diff as well to check the entire change boundary. Row-control geometry stays local to status moves; do not enlarge the shared row-control token.
- Stylesheet cleanup — the retired task-delete selector and its old size claim are removed; the full-size strip comment names its general full-size context. No screenshot or test of comment text stands in for reading this diff (design § 2 “Blast Radius”).

#### Implement

Infer from failing tests.

#### Verification gate

From the **change worktree root**, run:

```sh
pytest products/tracker17/tests/e2e/test_delete_task.py products/tracker17/tests/e2e/test_delete_project.py
pytest products/tracker17/tests/
pytest products/tracker17/tests/e2e/
```

Pass: the added geometry tests demonstrate the pre-change failure and then pass; both full suites separately exit 0 with no new failures. The corrected project test still proves the move confirmation is 28px, while the task confirmation is 36px (CP-614–CP-616).

From the **product root**, run:

```sh
python3 -m compileall -q main.py errors.py domain application persistence web tests
ruff format --check .
ruff check .
mypy main.py errors.py domain application persistence web
```

Pass: every command exits 0. Use the product's locked test tools, including Ruff 0.16.10 and mypy 2.4.0 (`tests/requirements.txt:8-18`, exact pins; CP-617; `docs/nfdr.md:532-545`, QC-62).

From the **change worktree root**, review these change-only diffs:

```sh
git diff "$(git merge-base main HEAD)" -- products/tracker17/tests/e2e/test_delete_task.py products/tracker17/tests/e2e/test_delete_project.py
git diff "$(git merge-base main HEAD)" -- products/tracker17/web/pages.py products/tracker17/web/style.css
git diff "$(git merge-base main HEAD)" -- products/tracker17/domain products/tracker17/application products/tracker17/persistence products/tracker17/main.py products/tracker17/errors.py products/tracker17/web/routes.py products/tracker17/web/listener.py products/tracker17/web/__init__.py
```

Pass: the first two diffs satisfy every Held by review criterion; the final diff is empty. The trace checks in the non-browser suite pass, including the receiving test module's requirement references (CP-618).
