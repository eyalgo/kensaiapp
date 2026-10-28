# Tech Lead instruction — rename-a-project: rename from the Tasks view

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every path below is relative to it unless a command explicitly runs from the change worktree root.
**Scope:** Add project rename through the existing naming rules, save path and browser pages, with unchanged tasks and a full-volume timing measurement.

This instruction owns the task cut, verification behaviours and engineering resolutions for
`tracker17 · tobiishi · 2026-10-28_rename-a-project`. Its inputs are that change's
`change_spec.md` CP-546–CP-568 and `change_design.md` §§ 1–5. The output belongs beside those
inputs, per `<CORE>/doctrine/setup/kensaiapp_structure.md` § 2, *Per-project*, `journey/tobiishi/`.

## Project layout

```text
products/tracker17/
  domain/
    projects.py                         ← modified: rule, outcome, shared availability, trace
    __init__.py                         ← modified: public re-exports only
  application/
    tracker.py                          ← modified: rename action
    __init__.py                         ← modified: outcome re-export only
  web/
    pages.py                            ← modified: Rename area and shared refusal presentation
    routes.py                           ← modified: POST, shared translation, outcome decoding
    style.css                           ← modified only if existing styles fail CP-560
  tests/
    unit/
      test_projects.py                  ← modified
    integration/
      test_rename_tracker.py            ← new
      test_rename_pages.py              ← new
      test_rename_routes.py             ← new
      test_pages.py                     ← modified
      test_filter_pages.py              ← modified
      test_sort_pages.py                ← modified
      test_routes.py                    ← modified
      test_timed_run.py                 ← modified
    e2e/
      test_rename_project.py            ← new
      test_first_project.py             ← modified
    timed_run.py                        ← modified
```

Create the four new test modules in the existing directories; no directory or `__init__.py`
creation is needed (design § 5, T03–T12). Placement follows `docs/SDD.md` § 3, *The parts*: project rules belong in
`domain`, saving and publication in `application`, and requests, addresses and HTML in `web`.
Keep the import graph in `docs/nfdr.md` § 1.2: `web → application → domain`,
`persistence → domain`, `main →` all four parts; each may import `errors`. The forbidden
directions in QC-13–QC-19 remain binding. No persistence, composition, error-base or saved-format
change is needed by design § 2.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "From the change worktree, git ls-tree --name-only HEAD listed .claude, .env.example, .gitignore, .providers.toml.example, .python-version, .telemetry.env, AGENTS.md, Brewfile, CLAUDE.md, Containerfile, README.md, about, core, docs, kensaiapp.md, products, pyproject.toml, skills, system and uv.lock. git ls-files '*.yml' '*.yaml' '*.toml' '*Jenkins*' '*Containerfile*' '*Dockerfile*' '*Makefile*' '*Taskfile*' '*Justfile*' returned Containerfile, core/templates/skeleton-templates/python/pyproject.toml, core/templates/skeleton-templates/rust/Cargo.toml, core/templates/skeleton-templates/rust/crates/__PROJECT__/Cargo.toml, core/templates/skeleton-templates/rust/rust-toolchain.toml, core/templates/skeleton-templates/rust/rustfmt.toml, products/tracker17/pyproject.toml and pyproject.toml; no YAML or runner configuration. The tracked product inventory contains source, tests, docs, README, .gitignore and pyproject.toml. Read Containerfile and both real pyproject.toml files: Containerfile builds the local execution image and names no CI runner; the manifests configure dependencies and tools, not CI. The skeleton manifests are templates outside this product. No product CI configuration was found."
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

## TL Review Notes

Engineering decisions below are the Tech Lead's, 2026-10-28.

- **Language resolution:** Python, step 1, `project.md` `Languages:`. Opened
  `<CORE>/doctrine/engineering/languages/python/README.md` and its seven destinations.
  Product decisions govern the Python 3.11 compatibility floor, existing pins and test locations
  (`docs/adr/0002-standard-library-only-no-web-framework.md` § Decision;
  `docs/nfdr.md` QC-39, QC-59–QC-62 and § 9).
- **Baseline and launch conditions:** From the change worktree, the card's exact command
  `pytest products/tracker17/tests/` collected 2,273 tests and ended with
  `20 failed, 2222 passed, 31 errors in 196.96s`; listener setup reported
  `PermissionError: [Errno 1] Operation not permitted` at `socket.bind`. An approved
  `pytest products/tracker17/tests/ --lf` run in terminal mode then returned
  `51 passed in 10.69s`. These are separate runs, not a claim that one full run passed.
  The intervening pipe-mode retry was stopped, exit 143, after shutdown failures: a signal probe
  returned `parent SIGINT: 1`, `child SIGINT: 1` under pipes, while terminal mode returned
  `default_int_handler`. The suite needs local socket binding and a launch that gives child
  servers normal SIGINT handling; its start helper sends SIGINT and waits for exit
  (`tests/integration/test_start.py:516-535`, `_run_real_start`). The gate commands below retain
  the card's command; these launch conditions are prerequisites, not product changes.
- **Environment evidence checked:** `gate_suite.py record` returned exit 0, and
  `gate_suite.py check` on the JSON above returned
  `resolves — owners-mac: the product has no CI, so its gates run on the owner's Mac`, exit 0.
  This check started no suite. No CI version supplies a candidate tag, so none is invented.
- **Task cut:** Preserve design A → B → C → D as Tasks 1–4. Task 3 keeps the web form, route,
  outcomes and released old presence assertions together: those checks describe the same web
  change. Separate the final Projects trace review as Task 5 so its test-module references name
  files already built by Tasks 2–4; new tests carry their own requirement docstrings immediately
  (design T13/T16; `domain/projects.py` opening *Checked by* paragraph).
- **Type upgraded:** Design C leaves the recognized project-refusal code's type implicit. Use a
  shared `ProjectNameRefusal` enum in `web/pages.py` for the translator result and Rename area's
  optional refusal, with values matching existing `BLANK_NAME`, `NAME_IN_USE`, `TEXT_TOO_LONG`.
  Preserve those existing string constants and address values, and pass the value into the one
  `_name_reason`. This types the closed set without a second wording scheme or changed creation
  interface (`web/pages.py:54-56`, existing constants; design § 3 C).
- **Additional coverage:** Add missing-target-plus-invalid-name precedence to Task 1, because
  design A finds the target before validation. Add a second rename of the same project to Task 2
  to prove `previous_name` comes from the current state. Task 3 compares creation and rename's
  visible reasons for the same invalid name, including hostile duplicate text, alongside review
  of their shared path: equal output alone cannot prove reuse (design A/C; CP-555).
- **Trace is review-verified:** Task 5 uses the review lane. The existing pointer checks validate
  named paths and requirement identifiers, while exhaustive participation and accurate prose
  still require reading the diff (`tests/architecture/test_trace.py`; QC-11). No invented
  behaviour test stands in for that review.
- **Corrections ride their file:** Task 4 updates the timed run's opening and helper docstrings
  that call sort or deletion the last measurement. They must describe the new final rename block
  (`tests/timed_run.py:31-45`, `main`, `_run_sort`, `_run_summary`, `_run_delete`).

### Task 1: Shared project naming and immutable rename (`domain/projects.py`, `domain/__init__.py`)

**Dependencies:** None

**What to build:** Design § 3 A's `ProjectRenameOutcome` and `rename_project`, sharing creation's
value validation and name-availability rule. The frozen outcome holds `project: Project`,
`previous_name: str`, `changed: bool`. The rule accepts the state, project identity and new name,
and returns the new state and outcome. Find the target first, then use creation's validation and
availability before comparing exactly with its current saved name. A missing identity raises
`ProjectNotFound`; another project's exact name raises `NameInUse`. Own current name returns the
input state and no change. A changed result replaces only that project's name in its existing
tuple position, retaining tasks and counters. Export the outcome and rule through `domain`.
Update the unit test module's requirement docstring for FR-12 as its rename tests are added.

#### Behaviours to verify (developer adds tests to `tests/unit/test_projects.py`)

- `test_rename_changes_only_the_selected_project_name` — compare the entire returned state with
  an independently constructed expected state, keeping other projects, task/comment values,
  description, identities, assignees, operator name and counters; input remains unchanged.
- `test_rename_reports_the_current_and_previous_name` — returned project is the renamed project,
  previous name is the exact pre-action name and changed is true.
- `test_own_name_is_accepted_without_a_change` — unchanged outcome, same input state, self name
  excluded from availability; no extra identity or field.
- `test_rename_keeps_case_spaces_and_code_points` — case-only and leading/trailing-space changes,
  exact 200-code-point names containing a supplementary character, and normalized LF are kept.
- `test_rename_refuses_blank_names_as_creation_does` — empty, ASCII whitespace, mixed whitespace
  and creation's non-ASCII whitespace cases raise `BlankName`, with unchanged input.
- `test_rename_refuses_only_another_projects_exact_name` — another exact name raises `NameInUse`;
  case and space variants stay distinct.
- `test_rename_refuses_overlong_before_blank` — 201 code points and 201 spaces raise
  `TextTooLong` for `TextField.NAME`, with creation's maximum and unchanged input.
- `test_missing_rename_target_precedes_name_validation` — missing identity, also with invalid
  names, raises `ProjectNotFound` and changes nothing.
- Keep existing creation and restoration tests. Creation's length order remains name length,
  description length, blank, in use; specifically blank name plus overlong description still
  refuses the description. Verify explicit Projects sorting after rename with the existing
  casefold/exact-name tie-break, independently of retained tuple position (T01/T02; CP-551–555).

#### Held by review

- CP-555 — creation and rename call one value-validation path and one shared availability path;
  output tests cannot distinguish shared code from duplicated equivalent code.
- QC-20 — domain contains no published refusal wording, HTML, request detail or I/O; read the diff.

#### Implement

Infer from failing tests.

# Hint:
Reuse `check_project_values` with the unchanged description, and one shared availability check
with self exclusion. Retain creation's cross-field refusal precedence; immutable replacement
changes only the selected project within the state.

#### Verification gate

From the change worktree root run `pytest products/tracker17/tests/unit/test_projects.py`, then
`pytest products/tracker17/tests/`. Pass: new rename behaviours and existing project behaviours
pass, with no new failures in the full suite.

### Task 2: Save before publishing rename (`application/tracker.py`, `application/__init__.py`)

**Dependencies:** Task 1 — domain rename rule and outcome.

**What to build:** Design § 3 B's `Tracker.rename_project(project_id: int, name: str) ->
ProjectRenameOutcome` and application outcome export. Apply the domain rule once to current state;
save and publish only when its outcome reports a change. Return the outcome after the save.
Application compares no names and reads neither saved data nor the clock. Add
`tests/integration/test_rename_tracker.py` with its SRS requirement docstring (T03/T04).

#### Behaviours to verify (developer adds tests to `tests/integration/test_rename_tracker.py`)

- `test_rename_saves_once_before_publishing` — an injected recording saver sees the candidate
  state while readers still show the old name; only after saving do readers and the outcome show
  the new name. A recording clock receives no call.
- `test_unchanged_rename_never_saves` — exact own name returns unchanged outcome, with zero saves
  and no clock call, including after a preceding rename.
- `test_refused_rename_keeps_the_current_state` — parameterize blank, duplicate, overlong and
  missing identity; typed refusals propagate, zero saves and every current value unchanged.
- `test_failed_rename_keeps_the_current_state` — injected failing saver propagates its failure,
  records one attempted save and leaves all readers on the pre-action state.
- `test_each_rename_uses_the_name_current_at_the_action` — successive renames report the actual
  previous saved name, allow a stale old name to rename back and suppress a value already current.
- `test_rename_preserves_tasks_and_survives_restart` — use real SavedData in `tmp_path` with
  several tasks in varied statuses, comments/authors/times, labels, assignee, due date, another
  project and descriptions. Compare the whole expected state in memory and reloaded from disk;
  inspect stored key sets, both counters and identities. Reconstruct a fresh Tracker on that
  saved state and assert the new name and unchanged tasks/comments field by field (CP-554/562).
- `test_rename_saver_receives_only_saves` — a recording saver receives only the expected changed
  save, never a read, including on later page-data reads (QC-54; CP-567).

#### Held by review

- QC-21 — application only branches on the domain outcome's change flag; it adds no name
  validation, comparison or saved-format knowledge. The behavioural checks alone cannot prove
  absence of a second rule.

#### Implement

Infer from failing tests.

#### Verification gate

From the change worktree root run
`pytest products/tracker17/tests/integration/test_rename_tracker.py`, then
`pytest products/tracker17/tests/`. Pass: changed save, unchanged/refused/failed actions,
whole-state preservation and restart checks pass, with no new full-suite failures.

### Task 3: Rename form and complete request path (`web/pages.py`, `web/routes.py`, `web/style.css` if needed)

**Dependencies:** Task 2 — application rename action and outcome export.

**What to build:** Design § 3 C's request-scoped frozen `ProjectRenameArea`, optional
`rename_area: ProjectRenameArea | None = None` keyword on `project_page`, shared typed project
refusal translator, and `POST /projects/{id}/rename` registered as `SUBMISSION`. The form is below
every Tasks-view list/result state. Its field is visibly labelled, contains the exact saved name,
uses application's exported `SHORT_TEXT_MAX`, and precedes Save. Only this page offers rename.

Keep the design's address contract: changed → 303 to the unfiltered project address with
`rename_saved`; `rename_from` only when the authored completion needs the old name; unchanged →
bare project address; refused → `rename_refused` with `rename_typed` only for blank/in-use;
failed → `rename_failed=save` and `rename_typed`. No shown-name field, list choices or fragment.
Unknown codes are inert and a too-long refusal discards forged typed text. Missing project uses
the existing project-not-found page, 404. Creation and rename share typed translation, including
creation's description-too-long detail, and the existing `_name_reason` (CP-555).

Success/refusal focus the Rename field, failure its Save. The one relevant line describes that
element through `aria-describedby` and never takes focus. Ordinary loads/unchanged submissions
add no line or autofocus. Existing creation, add, move and deletion outcomes retain precedence
on combined queries. All new displayed strings come verbatim from this change's `change_text.md`;
the plan fixes no additional wording (CP-548; design `Publishes text: yes`).

Add the three new test modules below. Update the old presence, route enumeration, no-outbound and
first-project tests identified in design T13/T14 without weakening their other assertions.

#### Behaviours to verify (developer adds tests to `tests/integration/test_rename_pages.py`, `tests/integration/test_rename_routes.py`, `tests/e2e/test_rename_project.py`)

- `test_every_tasks_view_state_has_the_rename_area` — layer 4, tasks, no tasks, no matches,
  refused filter/sort, creation/add completion/refusal/failure, visible/off-list move outcome,
  cancellation confirmation/back-out and task-deletion completion. Area is after results in
  every case, exact saved value and field-before-Save order. Existing outcome focus wins when
  combined with forged rename markers; never two autofocus elements (T05).
- `test_rename_control_has_label_limit_and_no_limit_sentence` — visible label, maxlength equal
  to the application export, POST action names the correct project, no old-name/shown-name field
  and no maximum sentence. Projects, Summary, All tasks and task builders offer no rename (T05).
- `test_successful_rename_lands_with_one_described_completion` — layer 3, first POST saves once,
  303 follows design's exact address keys; no filter/sort/fragment. GET is 200, new heading/title,
  exact authored completion, saved-name field and field focus described by the line (T06).
- `test_rename_outcome_reload_does_not_save` — GET success and refusal locations repeatedly;
  same line, field and focus, no save. Exact own-name POST saves nothing, redirects bare and
  lands with neither completion/refusal nor autofocus (T06; CP-550/553/556).
- `test_renamed_project_is_current_on_every_page` — Alpha → Zed beside Gamma/delta yields
  Projects order delta, Gamma, Zed. Verify Tasks/Summary headings and document titles, every
  task's All tasks Project cell and task-page Project field. Old name is absent as this project's
  name; project/summary/task links and identities remain. Include empty description and empty
  project cases (T07).
- `test_blank_rename_keeps_saved_data_and_typed_text` — separate layer-3 refusal test with empty
  and whitespace parameters; exact creation reason, old heading/title, retained typed text,
  focused field and reason description. Saved bytes and whole state equal before/after, zero
  saves (T08; CP-563).
- `test_duplicate_rename_keeps_saved_data_and_typed_text` — another exact project name, same
  refusal/data assertions as blank, with creation's exact duplicate-name reason (T08).
- `test_overlong_rename_discards_all_submitted_text` — forged POST of 201 code points and 201
  spaces, reason is too-long before blank, saved-name field, field focus, no submitted text in
  HTML or Location, old heading/title, identical saved bytes/state and zero saves (T08).
- `test_missing_rename_project_answers_404_without_saving` — no Location, existing project
  not-found heading, unchanged bytes/state and zero saves; include identities beyond Python's
  integer conversion limit as the existing request decoder handles them (T08; CP-558).
- `test_stale_rename_checks_current_saved_state` — another tab creates desired name → refusal;
  another tab renames target → a new value overwrites it; unchanged stale field renames it back;
  a value now equal to current name saves nothing. No compare-with-shown-name scheme (T09).
- `test_failed_rename_retains_text_and_focuses_save` — injected save failure, unchanged bytes,
  state and every name-displaying read; console names rename and error. Landing retains typed
  value, focuses Save with authored failure description, and exposes no exception text in HTML
  or Location (T10).
- `test_rename_passes_the_existing_request_checks` — cross-site, same-site, none, absent and
  unknown non-same-origin marks refuse before action, with unchanged data; wrong Host too.
  Valid direct POSTs carry same-origin. CRLF and CR normalize to LF once; no other mutation (T11).
- `test_rename_shows_hostile_text_literally` — `<`, `&`, quotes, leading/trailing spaces in
  field, heading/title, completion, Projects and duplicate-name reason; compare creation and
  rename refusal text for the same input. Forged too-long+typed query drops typed text; unknown
  refusal/failure codes render the ordinary area (T11; CP-561).
- `test_rename_is_keyboard_operable_and_described` — layer 5 Chromium, Tab reaches field and
  Save, Enter submits once without confirmation; success/refusal focus and accessible
  descriptions, visible keyboard focus and Save's UX-A6 pointer-target floor (T12).
- `test_hostile_name_survives_browser_rename_and_history` — Chromium types the spec's hostile
  name, verifies literal heading/title/Projects/field/completion and duplicate refusal; actual
  reload, Back and Forward preserve completed/refused lines without another save (T12).
- Existing `test_pages.py`, `test_filter_pages.py`, `test_sort_pages.py` and
  `test_first_project.py`: scope old add-form checks to its action and Add button, assert Rename
  separately, keep creation heading/description/title/invitation/line/focus, header addresses,
  no deletion, and empty project's absence of GET/filter/sort/table (T13).
- Extend `test_routes.py` route sample/body maps, keeping route-set equality, one successful
  changed save, redirect, no cookies and CSP headers; drive rename plus landing in the existing
  no-outbound sequence while retaining every old action (T14; CP-567).

#### Held by review

- CP-555 and QC-5 — one typed translation and one `_name_reason` serve both create and rename;
  creation's description-too-long handling and retained fields are still intact. Read the diff.
- QC-23/QC-36 — all HTML value interpolation uses `_escape`, addresses use `_address`, web keeps
  no request state between requests and performs no name rule. Tests sample outputs; review
  checks the entire new path.
- CP-548 — each newly published string matches the authored text, including console failure
  wording; this is a string-placement review, not permission to choose copy.

#### Implement

Infer from failing tests.

# Hint:
Share typed refusal translation and `_name_reason` with creation; carry outcomes through
`_address`/`_redirect`, and use native autofocus with one described line. No session or page script.

#### Verification gate

From the change worktree root run
`pytest products/tracker17/tests/integration/test_rename_pages.py products/tracker17/tests/integration/test_rename_routes.py products/tracker17/tests/integration/test_pages.py products/tracker17/tests/integration/test_filter_pages.py products/tracker17/tests/integration/test_sort_pages.py products/tracker17/tests/integration/test_routes.py`,
then `pytest products/tracker17/tests/`. Separately run
`pytest products/tracker17/tests/e2e/test_rename_project.py products/tracker17/tests/e2e/test_first_project.py`.
Pass: all new page/request/browser checks and revised presence assertions pass; no new suite
failures; existing outcome focus, routes and controls retain their assertions.

### Task 4: Timed rename at task volume (`tests/timed_run.py`, `tests/integration/test_timed_run.py`)

**Dependencies:** Task 3 — live rename POST, redirect and completion contract.

**What to build:** Design § 3 D's rename measurement, fixture report and final run block. Use a
separately seeded fixture of 1,000 tasks, 20 comments each, ordinary text lengths and a target
project with tasks. Report lengths and counts. Append rename after existing deletion measurements,
retaining each old fixture/action/verdict. Include request, landing and total in the one-second
verdict and aggregate exit status. Expected state is independently constructed by replacing only
the loaded target project's name. Disk inspection sits outside measured intervals.

Correction riding this task: update the opening docstring and helper descriptions that call sort
or deletion the last action, plus `main`'s action list, to make the new order true throughout this
file (`tests/timed_run.py` opening paragraphs and `main`, `_run_move`, `_run_sort`, `_run_summary`,
`_run_delete`). Add the new rename labels and report verbatim from the authored change text.

#### Behaviours to verify (developer adds tests to `tests/integration/test_timed_run.py`)

- `test_timed_rename_records_request_landing_and_total` — correct same-origin POST, changed save,
  exact redirect, then 200 landing with new heading and authored completion; four injected timer
  readings produce three measured results and disk inspection contributes no interval.
- `test_timed_rename_requires_exact_saved_delta` — no-op, wrong name, unchanged data, extra task,
  counter or other-project change fail; independent expected whole state catches all differences.
- `test_timed_rename_rejects_bad_request_outcomes` — refusal, failure, non-303 or wrong Location
  cannot count as completed; landing/total verdicts stay failed as appropriate.
- `test_timed_rename_requires_the_correct_landing` — non-200, old/wrong heading, missing/wrong
  completion cannot pass the landing or total, even when the save was correct.
- `test_timed_rename_enforces_each_interval_and_total` — request, landing and sum each pass only
  below one second; exactly at/above limit fails, including a sum over limit with each part below.
- `test_rename_fixture_report_states_real_volume_and_lengths` — independently inspect the loaded
  fixture, all comments and target project's nonempty task set; report matches counts and ordinary
  name/title/comment/description lengths (CP-566).
- `test_whole_run_keeps_older_actions_and_appends_rename` — update `_run_readings`, every fixed
  reading sequence and label order with rename's four readings and three labels after deletion;
  keep every earlier result and fixture assertion. A failed rename or any older failed action
  makes the aggregate exit nonzero; complete success exits 0 (T15).

#### Held by review

- CP-566 — expected state is calculated from the fixture without calling the production rename
  rule, and each old action retains its own fixture. Read measurement and harness diff together.
- CP-548 — published timing labels and fixture wording match the authored text.

#### Implement

Infer from failing tests.

# Hint:
Reuse `TimedAction`/`_measure_action` for the request, landing and total; its saved-state predicate
compares an independently constructed expected whole state.

#### Verification gate

From the change worktree root run
`pytest products/tracker17/tests/integration/test_timed_run.py`,
`pytest products/tracker17/tests/`, and `python3 products/tracker17/tests/timed_run.py`.
Pass: harness and suite have no new failures; real timing exits 0, retains all earlier actions,
and counts rename only with the exact saved delta and correct landing. Request, landing and total
are each below one second.

### Task 5: Projects feature trace and final review (`domain/projects.py` opening docstring)

**Dependencies:** Tasks 1–4 — implemented rename paths and their created test modules.

**What to build:** Complete the Projects feature trace for this change only, preserving prior
references. Each new test module's requirement docstring is part of its owning task above.

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- `domain/projects.py` opening docstring — names FR-12 alongside existing realized requirements,
  describes create and rename accurately, names participating `application/tracker.py`,
  `web/pages.py`, `web/routes.py`, and every test module that now checks Projects, including the
  new rename modules, revised existing page/route/browser modules and timing harness. Every
  referenced path exists; no prior true reference is dropped (CP-568, QC-11; design T16).
- New test module docstrings — each names the actual SRS requirements/acceptance criteria it
  checks, rather than only CP/T row labels. Review the requirement-to-behaviour match.
- Product diff — existing presence assertions change only as design T13 authorizes; no project
  deletion, description-edit or task-reparenting behaviour is introduced. Review with
  `git diff "$(git merge-base main HEAD)" -- products/tracker17/` from the change worktree root;
  this change-local scope check is not a persistent suite test.

#### Implement

Verified by review — no test.

#### Verification gate

From the change worktree root run
`pytest products/tracker17/tests/architecture/test_trace.py`,
`pytest products/tracker17/tests/`, and `python3 -m compileall -q products/tracker17/`.
From the product root run `ruff format --check .`, `ruff check .`, and
`mypy main.py errors.py domain application persistence web` (NFDR QC-62).
Pass: every review criterion is met, pointer checks pass, compile succeeds and the suite gains no
failures; Ruff and mypy exit 0. This task adds no tests of its own.
