# Tech Lead instruction — create-a-project-that-stays: a first project that is listed after a restart

**Product root:** products/tracker17 — every path below is relative to it.
**Scope:** Build all five parts of `docs/SDD.md` § 3 (`domain/`, `application/`, `persistence/`, `web/`, `main.py`) so `python3 main.py` serves a tracker where a first project is created, refused when blank, in use or over-long, and listed after a stop and a start. Pin the test dependencies, ignore `data/`, and add the three test layers, the layer-6 walks, the trace pointer test and the timed run (`change_design.md` §1). Category `feature`, Behaviour `changing` (copied from the `change_design.md` header).

Every word a page or the console shows is the content stage's (`change_text.md`, from `docs/CONTENT.md`; SDD § 4 EX-11). The plan and the tasks hold no wording. The developer places that text and writes none of its own.

---

## Project layout

```
products/tracker17/
  main.py                          ← modified
  errors.py                        (unchanged)
  pyproject.toml                   ← modified
  .gitignore                       ← modified
  domain/                          ← new
    __init__.py
    text.py
    refusals.py
    state.py
    projects.py
  application/                     ← new
    __init__.py
    contracts.py
    tracker.py
  persistence/                     ← new
    __init__.py
    saved_data.py
  web/                             ← new
    __init__.py
    pages.py
    routes.py
    listener.py
    style.css
  tests/
    conftest.py                    ← modified
    requirements.txt               ← new
    timed_run.py                   ← new
    unit/
      test_the_harness_runs.py     ← deleted
      test_projects.py             ← new
      test_state.py                ← new
      test_address.py              ← new
    integration/                   ← new directory
      test_saved_data.py
      test_tracker.py
      test_pages.py
      test_routes.py
      test_listener.py
      test_start.py
    e2e/
      conftest.py                  ← new
      test_first_project.py        ← new
    architecture/
      test_imports.py              ← new
      test_reach.py                ← new
      test_shapes.py               ← new
      test_pins.py                 ← new
      test_trace.py                ← new
```

The directories and files above are the module set `docs/nfdr.md` § 1.2 walks and `change_design.md` §2 lists. `tests/integration/test_listener.py` is the one file added beyond the design's list (see TL Review Notes). Create each package's `__init__.py` as the re-export point `change_design.md` §3 names. `tests/` carries no `__init__.py`: every test module name above is unique, and the root `tests/conftest.py` shim puts the product root on `sys.path`.

`docs/SDD.md` § 3 gives every part an empty `Lives in`, so each part sits at the product root.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Task split — `domain/`:** §3 Sub-job A became Task 3 (text, refusals, the state value, the create/list/find rules) and Task 4 (`restore_state`). `restore_state` is the start-time rule that persistence uses, with its own test file and its own refusal cases, and it is not needed by Task 3's tests.
- **Task split — `web/`:** §3 Sub-job D bundled pages, the stylesheet, the request path and the listener. It is Tasks 7 (`pages.py`), 8 (`style.css`), 9 (`routes.py`) and 10 (`listener.py`). Each has its own tests or its own review criterion, and the import order is pages → routes → listener.
- **Task split — `main.py`:** §3 Sub-job E became Task 11 (`main.py`, layers 1–2), Task 12 (the end-to-end harness and tests) and Task 13 (`tests/timed_run.py`).
- **Task split — root files and walks:** Sub-job F became Tasks 1 (manifest, lock, ignore) and 2 (the collection rule). Sub-job G became Tasks 14–18, one per test file, because each walk checks a different clause set.
- **Type upgraded:** `TextTooLong.field` is a string with the closed set `"name"` / `"description"` (§3 Sub-job A). Task 3 makes it a `str`-valued enumeration whose values are those two words, so the address `?field=<field>` is unchanged. `application` re-exports it with the refusal types (Task 6), so `web` still imports only `application` (QC-16).
- **Behaviour added — listener:** Task 10 has a layer-3 file, `tests/integration/test_listener.py`, which §5 does not list. The design's hints (OB-1 no log line, CP-23 no Python-produced error body) name properties no other row exercises through a socket: the routes tests call `Site.handle` with no socket, and the end-to-end tests do not send an unsupported method.
- **Behaviour locked — wrong method on a known address:** the input leaves implicit what `PUT /`, `POST /style.css` and `GET /projects` (a method or address not in `ROUTES`) answer. Task 9 pins it to the one rule §3 states, "any other address gets a 404 with an empty body", because `ROUTES` enumerates method and path together.
- **Behaviour locked — a project address that is not a project:** `/projects/abc`, `/projects/0` and an identity no project holds each get 404 with an empty body. §5 names only "an unknown project identity".
- **Behaviour locked — what the Projects page reads from its address:** a hand-typed address is also a request no page sends. Task 9 pins that an unknown `refused` code, or a `too-long` refusal with a `field` outside the closed set, shows the plain Projects page, and that a `too-long` refusal ignores any `name` or `description` in the address. That keeps CP-20's "none of the sent text" true when the address is built by hand, not only when `web` built it.
- **Behaviour added — persistence:** Task 5 adds a directory in place of `tracker.json`, an empty file, `id` or `next_project_id` written as JSON `true`, and a non-string name. Each is a way a file is not the expected shape (CP-7), and `bool` passes an `int` check unless it is excluded. It also adds a save failure that raises while the old file stays whole (§5 has the failing saver only at layer 3).
- **Behaviour added — start:** Task 11 adds that the location's listing is unchanged after an unreadable start, because CP-7 says "writes nothing", which is wider than "no byte changed".
- **Behaviour added — trace:** Task 18 adds `test_projects_entry_docstring_names_its_parts`. QC-11 says the entry docstring names requirements, the `application` and `web` modules, and the test modules, and §5 checks only that what is named exists.
- **Behaviour added — test module docstrings:** QC-11 requires every test module to name the requirements or acceptance criteria it checks, and Task 18 reads them. §5 does not list this per file, so every test-writing task below opens its test module that way.
- **Gap filled — Chromium:** Sub-job F exposes "a virtual environment that holds pytest and the browser-driving library". `pytest tests/e2e/` also needs the browser binary, which a `pip install` does not fetch. Task 12's gate installs it into that environment, and nothing committed holds it.
- **Hint placement:** in Tasks 1, 2, 14–17 the marker text is fixed (`Verified by review — no test.` / `Tests cannot go red.`), so the §4 hint is carried under `What to build` and not in `#### Implement`. Nothing was dropped.
- **Shape choice — already green:** Tasks 12 and 14–17 verify behaviours of code that Tasks 3–11 have already built, so no test of them can be made to fail first. Each carries its `Reason:`. Task 18 can go red, so it is test-first.
- **Shape choice — review-verified:** Tasks 1, 2, 8 and 13 deliver a manifest, a lock and an ignore line, a collection rule, a stylesheet and a timed script. A test asserts none of them (Task 2's rule has no collectable test until Task 12 lands).
- **Wording is not in the plan:** `change_design.md` publishes text (`Publishes text: yes`). The tasks below name where a message is shown and never what it says. Tests check that a reason is present beside the field it concerns, not its words, so they hold against whatever `change_text.md` supplies.
- **Missed record:** `README.md` § Status says no code exists and the setup instructions arrive "with the first slice". This change makes that false, and `change_design.md` § *Records this change makes false* does not list it. It is carried below. SDD § 4 EX-12 says the setup instructions describe the tracker as it stands after each slice, and the design's `Publishes text:` line names no setup text, so this one is flagged for whoever owns it.

## Corrections owed while there

- `main.py:5` and `main.py:17` — the module docstring says "The skeleton ships with nothing to wire", and `main()`'s says "Empty on purpose — the frame carries no modules to wire yet" → both say what Task 11's wiring replaces. Rides Task 11 (that task already opens this file).
- `pyproject.toml:7` — "Floors, not pins: a frame is copied into products that outlive any exact version" is false once the `dev` group pins with `==` → rewrite it to say the versions are exact and why. Rides Task 1 (that task already opens this file).
- `tests/conftest.py:1-6` — the docstring says the file only "puts the project root on sys.path" → once Task 2 adds the collection rule it says half of what the file does. Rides Task 2 (that task already opens this file).
- Owed outside this change's reach: `docs/SDD.md` § 4 TS-4 — the sentence "or when a feature word in the table below has no module" goes false → "…or when a feature word whose slice has landed has no module; each slice that delivers a feature adds its word to the test."
- Owed outside this change's reach: `docs/nfdr.md` QC-11 *verified by* — the clause "or a feature word with no module" goes false → "…or a feature word, among those whose slice has landed, with no module."
- Owed outside this change's reach: `docs/SDD.md` § Open Questions, third item ("Which port the fixed address uses") — this change settles it → remove it, and record the port as `8017` in § 4 RT-5.
- Owed outside this change's reach: `docs/SDD.md` § Open Questions, first item (how Chromium counts a line break against `maxlength`) and the form-control half of the second item (whether Chromium honours `autofocus`) — both are answered when the CP-16 and CP-19 end-to-end tests pass → remove the first item, and narrow the second to an element that is not a control, which `tasks-in-a-project` tests.
- Owed outside this change's reach: `README.md:9-11` § Status — "tracker17 is defined and isn't built yet… no code exists, so there's nothing to run. The setup instructions arrive in this file with the first slice of work" goes false → it should say what runs now and carry the setup instructions for the tracker as it stands after this slice.

---

### Task 1: Pin the test dependencies, lock them, ignore `data/` (`pyproject.toml`, `tests/requirements.txt`, `.gitignore`)

**Dependencies:** None

**What to build:** `[dependency-groups] dev` in `pyproject.toml` moves from floors to exact `==` versions and gains `playwright`. `tests/requirements.txt` is the one committed lock: every test dependency and everything it pulls in, each `==`. `.gitignore` ignores `data/`. Hint (from `change_design.md` §4, F): the browser-driving library is Playwright for Python with plain pytest fixtures and no plugin. Build the lock by installing the pinned group into a fresh `venv` and freezing it to `tests/requirements.txt`, with every line `==`. Each pin is the current release on the day it is installed (the design's QC-40 condition). Also rewrite the comment at `pyproject.toml:7`, as § *Corrections owed* says.

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- `pyproject.toml` `[dependency-groups] dev` — every entry uses `==`, none uses `>=`, `~=` or a range, and `playwright` is among them; the criterion is CP-28.
- `pyproject.toml` `requires-python` — still reads `">=3.11"` (QC-59).
- `tests/requirements.txt` — every non-comment line is `name==version`; it lists pytest, playwright and what they pull in, from a fresh `venv`'s `pip freeze`; the criterion is CP-28 and QC-39.
- `tests/requirements.txt` — each version is the newest release published on the day it was installed, which the developer checks with `pip index versions <name>` and records per pin in `Developer Review Notes`. The advisory check of those pins is not performed here: `change_design.md` Architect Review Notes, QC-40.
- `.gitignore` — has a line that ignores `data/`, and `git check-ignore -v data/tracker.json`, run from the product root, prints a rule and exits 0; the criterion is CP-5.
- `pyproject.toml:7` — the "Floors, not pins" sentence is rewritten to match the pins.

#### Implement

Verified by review — no test.

#### Verification gate

`pytest tests/` from the product root (the card's `Test command:`).

Pass criteria: every criterion above is met on reading the diff; the full suite has no new failures.

### Task 2: Keep `pytest tests/` from collecting `tests/e2e/` (`tests/conftest.py`)

**Dependencies:** None

**What to build:** a collection rule in `tests/conftest.py`: `pytest tests/` skips everything under `tests/e2e/`, and `pytest tests/e2e/` collects it (`docs/nfdr.md` § 10 treats them as two suites). Hint (from `change_design.md` §4, F): in `tests/conftest.py`, `pytest_ignore_collect` skips `tests/e2e/` unless the command line names `tests/e2e`. Keep the `sys.path` shim as it is, and rewrite the file's docstring to cover both duties.

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- `tests/conftest.py` — defines `pytest_ignore_collect`, which returns true for a path under `tests/e2e/` only when no command-line argument names `tests/e2e`.
- `tests/conftest.py` — the `sys.path` insertion is unchanged.
- `tests/conftest.py` — the opening docstring names both the shim and the collection rule.

#### Implement

Verified by review — no test.

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: every criterion above is met on reading the diff; the full suite has no new failures. The two-suite behaviour is run against real e2e tests in Task 12's gate.

### Task 3: `domain/` — text maximums, refusals, the state value, the Projects rules (`domain/__init__.py`, `domain/text.py`, `domain/refusals.py`, `domain/state.py`, `domain/projects.py`, `tests/unit/test_projects.py`)

**Dependencies:** None

**What to build:** the `domain` part of `docs/SDD.md` § 3 for projects. It takes and returns plain values, does no input or output, and holds no operator-facing wording.
- `domain/text.py`: `SHORT_TEXT_MAX = 200`, `LONG_TEXT_MAX = 4000` and the length check, the one place the lengths are stated (RT-10).
- `domain/refusals.py`: `Refusal(AppError)`, and `BlankName`, `NameInUse`, `TextTooLong`, `IdentityReused` deriving from it. `TextTooLong` carries `field` (a closed enumeration whose values are `"name"` and `"description"`) and `maximum: int`.
- `domain/state.py`: frozen `TrackerState(projects: tuple[Project, ...], next_project_id: int)` and `empty_state()`, which has no projects and `next_project_id` 1.
- `domain/projects.py`: frozen `Project(id, name, description)` (an empty description means none), `create_project(state, name, description) -> (new_state, project)`, `list_projects(state)`, `find_project(state, project_id) -> Project | None`. Its opening docstring names the feature and the SRS requirements it realizes; the `application`, `web` and test modules that take part are named in Task 18, where each exists.
- `domain/__init__.py` re-exports all of the above.
- Delete `tests/unit/test_the_harness_runs.py`: its docstring says to delete it once the product has a real test, and `tests/architecture/test_shapes.py` (Task 16) re-proves its assertion for QC-4.
- Every error class derives from `errors.AppError`. Write nothing newer than Python 3.11 (QC-60).

#### Behaviours to verify (developer adds tests to `tests/unit/test_projects.py`)

- `test_list_orders_names_ignoring_letter_case` — `beta`, `Alpha`, `alpha` list as `Alpha`, `alpha`, `beta` (CP-12).
- `test_list_orders_non_ascii_names_ignoring_letter_case` — a pair such as `Émile` / `émile` compares case-blind and ties break on the exact text (CP-12).
- `test_name_and_description_are_kept_exactly_as_given` — `  Alpha  ` and a two-line description come back unchanged (CP-13).
- `test_a_blank_name_is_refused` — an empty name, three spaces, a tab and a line break, and two U+00A0 each raise `BlankName` (CP-14).
- `test_a_name_in_use_is_refused_by_exact_text` — with `Alpha` present, `Alpha` raises `NameInUse`, and `alpha` and `Alpha ` are accepted (CP-15).
- `test_length_limits_are_inclusive` — a 200-character name and a 4,000-character description are accepted; 201 and 4,001 raise `TextTooLong` with the right `field` and `maximum` (CP-16).
- `test_a_character_outside_the_basic_plane_counts_as_one` — a non-BMP character adds one to the length (CP-16, RT-10).
- `test_over_long_wins_over_blank_and_in_use` — an over-long name with a blank name, a blank name with a 4,001-character description, an over-long description with a name in use, and both values over-long (which gives `"name"`) each raise the `TextTooLong` the spec's CP-20 gives.
- `test_identities_rise_from_one_and_the_counter_moves_on` — the first project has identity 1, the next 2, and each returned state's `next_project_id` is one past the last issued.
- `test_a_refused_create_returns_no_new_state` — after any refusal the state passed in still holds the same projects and the same counter (the value is immutable; nothing leaks out of a refusal).
- `test_find_project_returns_none_for_an_unknown_identity` — and returns the project for a known one.
- `test_the_predecessors_project_name_rules_come_over` — the project-name tests of tracker16-X's `domain/project.py` suite, re-expressed for these rules (SDD § 11 R-5).

#### Implement

Infer from failing tests.

# Hint:
- `create_project` checks in a fixed order: name length, description length, blank, in use. That order is how CP-20's precedence holds by construction, including the name winning when both values are too long.
- Sort with the key `(name.casefold(), name)`. `casefold` is the Unicode case mapping CP-12 leaves to this stage, and the exact name breaks ties.
- A name is blank when every character satisfies `str.isspace()`, the set tracker16-X's `name.strip()` uses (spec, Locked Answers Gap 13). Length is `len(value)`, which counts code points (RT-10).
- `projects.py` names `TrackerState` only for typing and builds the next state with `dataclasses.replace`. `state.py` can then import `projects.py` for `restore_state` (Task 4) with no import cycle at run time.

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: this task's tests pass; no new failures elsewhere.

### Task 4: `domain/` — `restore_state`, the start-time build (`domain/state.py`, `domain/__init__.py`, `tests/unit/test_state.py`)

**Dependencies:** Task 3

**What to build:** `restore_state(projects: Sequence[tuple[int, str, str]], next_project_id: int) -> TrackerState` in `domain/state.py`, re-exported from `domain/__init__.py`. Each project gets the same checks `create_project` applies, and it raises `IdentityReused` when two projects share an identity or when an identity is not below `next_project_id` (SM-4, SD-5). It never returns part of the data.

#### Behaviours to verify (developer adds tests to `tests/unit/test_state.py`)

- `test_restore_refuses_a_blank_name` — raises `BlankName` (CP-8, SD-5).
- `test_restore_refuses_two_projects_with_one_exact_name` — raises `NameInUse`.
- `test_restore_accepts_names_that_differ_only_by_case` — names compare exactly, as at create (CP-15).
- `test_restore_refuses_over_long_values` — a 201-character name and a 4,001-character description raise `TextTooLong` with the right `field`.
- `test_restore_refuses_a_shared_identity` — raises `IdentityReused`.
- `test_restore_refuses_an_identity_not_below_the_counter` — an identity equal to `next_project_id`, and one above it, each raise `IdentityReused`.
- `test_a_valid_set_round_trips` — projects built by `create_project` and handed back through `restore_state` give an equal `TrackerState`.
- `test_restore_of_no_projects_is_the_empty_state` — no projects and `next_project_id` 1 equals `empty_state()`.

#### Implement

Infer from failing tests.

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: this task's tests pass; no new failures elsewhere.

### Task 5: `persistence/` — the saved data (`persistence/__init__.py`, `persistence/saved_data.py`, `tests/integration/test_saved_data.py`)

**Dependencies:** Task 3, Task 4

**What to build:** the `persistence` part: it imports `domain` and `errors` only and holds no data rule. It owns where the file is, its format, the read at start and the whole-state atomic save.
- `DEFAULT_LOCATION: Path` — absolute `data/` under the product root, worked out from the module's own file.
- `SavedData(location: Path)`, keeping one file, `tracker.json`, in `location`: `location`; `load() -> TrackerState | None` (`None` when no saved data exists; `UnreadableData` when the file cannot be read in full, is not the expected shape, or breaks a rule `restore_state` raises); `save(state) -> None` (replaces the file whole and atomically, creates `location` when missing, raises on failure).
- `UnreadableData(AppError)` carries `location`.
- The file is a JSON object with `next_project_id` and `projects`, a list of objects with `id`, `name`, `description`. Nothing else is stored (QC-46).
- `persistence/__init__.py` re-exports `DEFAULT_LOCATION`, `SavedData`, `UnreadableData`.

#### Behaviours to verify (developer adds tests to `tests/integration/test_saved_data.py`)

- `test_no_file_loads_as_none` — a location with no file gives `None` (CP-6).
- `test_save_then_load_round_trips` — the loaded state equals the saved one, including a description with a line break and surrounding spaces.
- `test_the_first_save_creates_the_directory` — a location that does not exist is created.
- `test_unreadable_files_raise_and_stay_unchanged` — a truncated file, bytes that are not UTF-8, an empty file, the wrong JSON shape, and a directory in place of `tracker.json` each raise `UnreadableData` carrying the location (CP-7). For a file, its bytes are the same afterwards.
- `test_a_wrong_type_is_unreadable` — a name that is not a string, and an `id` or `next_project_id` written as JSON `true`, raise `UnreadableData`.
- `test_a_broken_domain_rule_is_unreadable` — a blank name, a duplicate name, a 201-character name, a 4,001-character description, a shared identity and an identity not below the counter each raise `UnreadableData`, with the bytes unchanged (CP-8, SD-5).
- `test_default_location_is_the_product_data_directory` — `DEFAULT_LOCATION` printed by a subprocess started from another working directory equals `<product root>/data` (CP-4, QC-42).
- `test_a_killed_save_leaves_one_whole_state` — a subprocess saves alternating states in a loop and is killed with `SIGKILL` at a random moment, many times over; after each kill `load` returns one of the saved states and never raises (CP-26, AC-9).
- `test_a_leftover_second_file_is_ignored` — a stray file beside `tracker.json` does not change what `load` returns.
- `test_a_failed_save_raises_and_leaves_the_old_file_whole` — saving to a location that cannot be written raises, and a file saved earlier is unchanged.
- `test_the_saved_file_holds_only_its_keys` — after creates, the file's keys are exactly `next_project_id` and `projects`, and each project's `id`, `name`, `description` (QC-46).

Red is probabilistic: `test_a_killed_save_leaves_one_whole_state` — the red depends on where in a save the kill lands, so a single run can pass on a tree that does not save atomically.

#### Implement

Infer from failing tests.

# Hint:
- Write to a second file in the same directory, flush it, `os.fsync` it, then `os.replace` it over `tracker.json` (ADR-0004). `load` never reads the second file. Missing file → `None`. A decode error, a JSON error, a wrong shape or type, and a `domain` `Refusal` from `restore_state` → `UnreadableData`. Read with `json`, never with a reader that executes (QC-37).

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: this task's tests pass; no new failures elsewhere.

### Task 6: `application/` — the `Tracker` and its two contracts (`application/__init__.py`, `application/contracts.py`, `application/tracker.py`, `tests/integration/test_tracker.py`)

**Dependencies:** Task 3

**What to build:** the `application` part: it imports `domain` and `errors` only, decides no rule, and knows nothing of how or where the state is saved.
- `contracts.py`: `Saver` (a `typing.Protocol` with `save(state) -> None`) and `Clock` (a Protocol with `now() -> datetime`, an aware UTC instant).
- `tracker.py`: `Tracker(state, saver, clock)` with `create_project(name, description) -> Project` (applies `domain.create_project`, calls `saver.save(new_state)`, and only then makes `new_state` current; a refusal and a saver failure each propagate unchanged, and the old state stays current), `projects()` (ordered by `domain.list_projects`) and `project(project_id) -> Project | None`.
- `__init__.py` re-exports `Saver`, `Clock`, `Tracker`, `Project`, `TrackerState`, `SHORT_TEXT_MAX`, `LONG_TEXT_MAX`, `Refusal`, `BlankName`, `NameInUse`, `TextTooLong` and the closed `field` type Task 3 made, so `web` imports only `application` (QC-5, QC-16).

#### Behaviours to verify (developer adds tests to `tests/integration/test_tracker.py`)

- `test_the_saver_gets_the_new_state_before_it_is_shown` — when `save` is called, `projects()` does not yet list the new project; after `create_project` returns, it does (QC-49, CP-24).
- `test_a_failing_saver_leaves_the_state_unchanged` — the saver's error propagates unchanged and `projects()` is as before (AC-18).
- `test_a_refusal_makes_no_save_call` — a blank name, a name in use and an over-long value each raise their refusal with no call to the saver.
- `test_a_restart_lists_the_project` — a `Tracker` built from the last state the saver received lists the project (layer 3's "restart").
- `test_an_identity_is_not_issued_twice_across_a_restart` — a project created after a restart has an identity the first run did not issue (QC-10, project half).
- `test_projects_come_back_in_the_domain_order` — three projects created out of order list as `domain` orders them.
- `test_project_returns_none_for_an_unknown_identity` — and the project for a known one.
- `test_the_names_web_needs_are_reexported` — each name in the list above is importable from `application`.

#### Implement

Infer from failing tests.

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: this task's tests pass; no new failures elsewhere.

### Task 7: `web/` — the pages (`web/__init__.py`, `web/pages.py`, `tests/integration/test_pages.py`)

**Dependencies:** Task 6

**What to build:** `web/pages.py`, which builds each whole HTML page as a string. It imports `application` only (QC-16), keeps no state, and shows plain values it is handed. It builds the Projects page (first run, list, refused and failed variants, prefilled values) and a project's page (with and without the created line). Every page has the header with exactly one link, to Projects. All wording is `change_text.md`'s.

#### Behaviours to verify (developer adds tests to `tests/integration/test_pages.py`)

- `test_the_note_number_equals_the_description_maxlength` — the number the note beside the description field states equals that field's `maxlength`, and the name field's `maxlength` is 200 and states no maximum (CP-11).
- `test_every_page_has_a_header_with_one_link_to_projects` — and no link to tasks, People, All tasks, renaming or deleting (CP-9).
- `test_the_first_run_page_says_there_are_no_projects_and_has_the_form` (CP-10).
- `test_the_list_shows_names_as_links_in_order_with_descriptions` — a project without a description shows none (CP-12).
- `test_a_project_page_shows_name_description_and_no_tasks_and_no_other_control` — no add-task form, no words inviting a first task, no rename or delete control (CP-17).
- `test_the_created_line_names_the_project` — present with the created flag, absent without it (CP-18).
- `test_values_are_escaped_everywhere` — `<b>A&B</b>` and `"` come out escaped in the list, on the project page, in the prefilled name field and in the prefilled textarea (CP-23, QC-36).
- `test_a_description_starting_with_a_line_break_keeps_it` — in the prefilled textarea and on the project page.
- `test_no_page_has_a_script_a_meta_policy_or_an_outside_address` (QC-33, CP-23).
- `test_the_refused_page_puts_focus_and_the_reason_on_the_name_field` — `autofocus` and `aria-describedby` on the name field, pointing at the element holding the reason, for a blank name and a name in use (CP-19).
- `test_a_too_long_refusal_focuses_the_field_that_was_too_long` — the description field for an over-long description, the name field for an over-long name or both; the page holds no typed values (CP-20).
- `test_a_failed_page_focuses_the_create_button_and_keeps_typed_values` — `autofocus` and `aria-describedby` on the Create button (EX-4, EX-14).
- `test_the_created_project_page_opens_on_its_heading` — `autofocus` on the heading, with the created line as its accessible description (EX-5, EX-14).

#### Implement

Infer from failing tests.

# Hint:
- One function escapes every value with `html.escape(…, quote=True)` (SEC-4). Write a newline straight after the `<textarea>` start tag, because the HTML parser drops one leading newline there. Show names and descriptions with `white-space: pre-wrap`, so surrounding spaces and line breaks show (CP-13). A refused or failed page puts `autofocus` and `aria-describedby` on the control used, either the field the reason concerns or the Create button for a failure (RT-9, EX-14). Write `maxlength` and the number in the description note from the two re-exported constants.

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: this task's tests pass; no new failures elsewhere.

### Task 8: `web/` — the stylesheet (`web/style.css`)

**Dependencies:** Task 7

**What to build:** the one stylesheet every page links, with the values of `docs/DESIGN.md`. It carries whatever class names Task 7's pages use.

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- `web/style.css` — every colour, size and spacing value comes from `docs/DESIGN.md`, and none is invented; the criterion is that the values are `docs/DESIGN.md`'s (SDD § 4, UXD § 9).
- `web/style.css` — names and descriptions are shown with `white-space: pre-wrap`, so surrounding spaces and line breaks show (CP-13).
- `web/style.css` — nothing is fetched from outside the machine: no `url(` or `@import` naming a host (CP-23, R-111).
- `web/style.css` — every class selector it uses is one `web/pages.py` writes.

#### Implement

Verified by review — no test.

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: every criterion above is met on reading the diff; the full suite has no new failures.

### Task 9: `web/` — the request path (`web/routes.py`, `web/__init__.py`, `tests/integration/test_routes.py`)

**Dependencies:** Task 6, Task 7, Task 8

**What to build:** `web/routes.py`: `Response(status, headers, body)`, `Site(tracker, own_host)` with `ROUTES` (method, path pattern, kind page or submission) and `handle(method, target, headers, body) -> Response`, the whole request path in one process with no socket. The lock lives on the `Site` object, not in a module-level value, so `Site` keeps nothing between requests (QC-8). Addresses: `GET /` (query optionally `refused`, `failed`, `field`, `name`, `description`), `GET /projects/<id>` (query optionally `created`), `POST /projects`, `GET /style.css`, anything else 404 with an empty body. Each page-building call goes to `web/pages.py`.

#### Behaviours to verify (developer adds tests to `tests/integration/test_routes.py`)

- `test_a_create_answers_303_to_the_project_page_and_a_reload_changes_nothing` — 303 to `/projects/<id>?created`, and two GETs of that address leave one project and show the same line (CP-18).
- `test_a_blank_or_duplicate_name_answers_with_the_projects_page_holding_the_reason_and_both_values` — no save call, and the same reason on reload (CP-19, CP-21).
- `test_an_over_long_value_names_the_right_field_and_holds_none_of_the_sent_text` — an over-long description, an over-long name, a blank name with a 4,001-character description, and both values over-long; neither the response address nor the page holds any of the sent text (CP-20, CP-16).
- `test_a_submission_not_marked_same_origin_is_refused` — POSTs marked `cross-site`, `same-site`, `none` and unmarked are refused with the state unchanged; a GET marked `none` opens the page; a GET marked `cross-site` is refused (CP-22, AC-10).
- `test_a_wrong_host_is_refused` (QC-31).
- `test_a_failed_save_names_the_action_and_error_on_stderr_and_shows_the_failure_page` — the page keeps the typed values with no traceback or exception text, and a restart does not list the project (CP-25, AC-18, QC-56, QC-57).
- `test_line_breaks_in_a_description_are_saved_as_lf` — a description sent with CR LF and lone CR is saved with LF (RT-10).
- `test_an_undecodable_body_answers_400_with_an_empty_body`.
- `test_every_route_leaves_state_and_headers_as_the_rules_say` — for each entry in `ROUTES`, a non-submission leaves the state unchanged, a submission gets a redirect, and no response sets a cookie or lacks the `Content-Security-Policy` header (QC-7, QC-8, QC-34).
- `test_a_saver_held_open_makes_a_second_submission_wait` (QC-53, RT-6).
- `test_no_socket_connection_is_made` — an audit hook sees no `socket.connect` across the actions (QC-35).
- `test_an_unknown_address_gets_404_with_an_empty_body` — including `/projects/abc`, `/projects/0`, and a project identity no project holds.
- `test_a_method_not_in_routes_gets_404_with_an_empty_body` — `PUT /`, `POST /style.css`, `GET /projects`; state unchanged.
- `test_an_unknown_refusal_code_in_the_address_shows_the_plain_projects_page` — an unknown `refused` value, and a `too-long` refusal with a `field` outside `name` / `description`.
- `test_a_too_long_refusal_ignores_name_and_description_in_the_address` — a hand-typed `name` or `description` is not shown.
- `test_the_stylesheet_is_served` — `GET /style.css` answers with the stylesheet and the policy header.

#### Implement

Infer from failing tests.

# Hint:
- Read header names without regard to case. Refuse with 403 and an empty body when `Host` is not `own_host`, when `Sec-Fetch-Site` is `cross-site` or `same-site`, or when a submission is not marked `same-origin` (a missing mark included).
- Parse `application/x-www-form-urlencoded` with `urllib.parse.parse_qs(keep_blank_values=True)` as strict UTF-8. Answer an undecodable body with 400 and an empty body. Then replace every CR LF, and every lone CR, with LF before the value reaches `application` (RT-10). Truncate nothing.
- Answer every submission with 303 to an address built by one function (RT-8). Success → `/projects/<id>?created`. Blank or in-use refusal → `/?refused=<code>&name=…&description=…`. `TextTooLong` → `/?refused=too-long&field=<field>`, carrying no typed value. Save failure → `/?failed=create&name=…&description=…`. Map a refusal to its code by its type, and read `TextTooLong.field` as an attribute (OB-4). Every other exception lands in the one `except` that writes the action and the error to `sys.stderr` (OB-3).
- Every response carries `Content-Security-Policy: default-src 'self'; script-src 'none'; form-action 'self'; frame-ancestors 'none'` as a header.

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: this task's tests pass; no new failures elsewhere.

### Task 10: `web/` — the listener (`web/listener.py`, `web/__init__.py`, `tests/integration/test_listener.py`)

**Dependencies:** Task 9

**What to build:** `listen(address, tracker) -> Listener` binds and listens on the loopback address; `Listener` has `serve_forever()` and `server_close()`. It passes method, target, headers and body of each request to `Site.handle` and writes the response. The "address is taken" signal belongs to the next change unit, so a bind error propagates. `web/__init__.py` re-exports `Site`, `Response`, `listen`.

#### Behaviours to verify (developer adds tests to `tests/integration/test_listener.py`)

- `test_a_request_over_a_real_socket_gets_the_page` — a `GET /` to a listener bound on port 0 answers with the Projects page.
- `test_a_request_writes_nothing_to_stdout_or_stderr` — after serving a page and a 404 (OB-1).
- `test_an_unsupported_method_gets_an_empty_body_and_no_python_text` — `PUT`, `DELETE` and `HEAD` answer with a body that holds none of the default error page's text (CP-23).
- `test_a_malformed_request_line_gets_no_python_text` — the answer holds none of the default error page's text.
- `test_the_listener_stops_on_server_close` — after `server_close()` a new connection to the port is refused.

#### Implement

Infer from failing tests.

# Hint:
- Use `http.server.ThreadingHTTPServer` with a handler that passes method, target, headers and body to `Site.handle`. Override the handler's `log_message` so it writes nothing (OB-1). Replace the default error page body so it carries no Python-produced text (CP-23).

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: this task's tests pass; no new failures elsewhere.

### Task 11: `main.py` — wire the four parts and start (`main.py`, `tests/unit/test_address.py`, `tests/integration/test_start.py`)

**Dependencies:** Task 1, Task 3, Task 5, Task 6, Task 10

**What to build:** the composition root, the only module that names a concrete `persistence` or `web` class. `ADDRESS = ("127.0.0.1", 8017)`. `main(argv=None) -> int` reads no argument and returns `start(ADDRESS, DEFAULT_LOCATION)`. `start(address, location) -> int` builds a `SavedData`, loads, starts from `domain.empty_state()` when `load` returns `None` (CP-6), builds the `Tracker` with the saver and the real clock, and listens. When the saved data is unreadable it writes one message naming `location` and returns 1. Otherwise it writes the ready message (address, then location), flushes, and serves until Ctrl-C, which closes the listener and returns 0. Rewrite both docstrings that say the frame has nothing to wire (§ *Corrections owed*).

#### Behaviours to verify (developer adds tests to `tests/unit/test_address.py` and `tests/integration/test_start.py`)

- `test_the_address_host_is_loopback` — `main.ADDRESS`'s host is loopback (QC-30), and `main()` starts on that one constant (CP-2).
- `test_an_unreadable_start_returns_non_zero_with_one_message_naming_the_location` — and no ready message (CP-7).
- `test_an_unreadable_start_changes_nothing_in_the_location` — every byte of the file is the same, and the location's directory listing is the same (CP-7).
- `test_data_is_ignored_by_version_control` — `git check-ignore -q data/tracker.json`, run from the product root, exits 0 (CP-5, QC-47).

#### Implement

Infer from failing tests.

# Hint:
- Write the ready line only after `listen` returns, flush stdout straight away, and then call `serve_forever` (OB-2). Catch `KeyboardInterrupt` around `serve_forever` and close the listener.

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: this task's tests pass; no new failures elsewhere.

### Task 12: End-to-end — the first project in a browser (`tests/e2e/conftest.py`, `tests/e2e/test_first_project.py`)

**Dependencies:** Task 1, Task 2, Task 11

**What to build:** the layer-5 harness and tests. The harness starts a tracker through `main.start` in a child process and drives Chromium through Playwright. Hint (from `change_design.md` §4, E): bind port 0 to find a free port. Run `sys.executable -c` with an import of `main` and a call to `start((host, port), tmp_location)`, from a working directory that is not the product root and with `PYTHONPATH` set to the product root. Read stdout until the ready line arrives. Stop the process with `SIGINT`. Drive Chromium through the browser-driving library, and send the hand-built over-long request through its request API with `Host` and `Sec-Fetch-Site: same-origin` set.

#### Behaviours to verify (developer adds tests to `tests/e2e/test_first_project.py`)

- `test_the_first_output_is_the_ready_message_address_before_location` (CP-1, QC-55).
- `test_the_first_project_lands_on_its_page_with_spaces_line_break_and_created_line` — create `  Alpha  ` with a two-line description on first run (CP-10, CP-13, CP-17, CP-18).
- `test_a_created_project_is_listed_after_a_stop_and_a_start` — create `Alpha` with description `x`, send `SIGINT`, see a clean exit with no `Traceback` on stderr, start again, and find `Alpha` with `x` (CP-3, CP-24, AC-6, project half).
- `test_names_list_in_case_blind_order` — `beta`, `Alpha`, `alpha` (CP-12).
- `test_a_refused_name_puts_focus_in_the_name_field_with_the_reason_as_its_description` — with `Alpha` saved, creating `Alpha` with `notes` keeps both values (CP-19).
- `test_a_description_of_4000_characters_with_line_breaks_is_saved_whole` — the saved file holds it whole (CP-16, AC-20).
- `test_a_hand_built_201_character_name_gets_the_reason_and_none_of_the_text` — focus on the name field, none of the 201 characters on the page, and the file's bytes unchanged (CP-20, AC-12).
- `test_a_hand_built_over_long_description_is_refused` — the reason is given and the file's bytes are unchanged (CP-16, RT-10).
- `test_markup_in_a_name_shows_as_text` — `<b>A&B</b>` (CP-23).

#### Implement

Tests cannot go red.

Reason: the subject of every behaviour above is built by Tasks 3–11 (`main.start`, the pages, the routes, the listener and the saved data), and a browser-level test of a finished path has nothing to fail against. A test that fails here is a defect in one of those tasks.

#### Verification gate

From the product root, build the environment and run both suites in it: `python3 -m venv .venv`, `.venv/bin/python -m pip install -r tests/requirements.txt`, `.venv/bin/playwright install chromium`, then `.venv/bin/python -m pytest tests/` and `.venv/bin/python -m pytest tests/e2e/`. Also run `.venv/bin/python -m pytest tests/ --collect-only -q`.

Pass criteria: both suites exit 0 with the tests above among those run; the `--collect-only` listing names no path under `tests/e2e/` (Task 2's rule).

### Task 13: The timed run (`tests/timed_run.py`)

**Dependencies:** Task 5, Task 9

**What to build:** a script, not a collected test: one location of its own, a real `SavedData`, and project creation timed through `Site.handle` with `same-origin` marks, at stated ordinary lengths. It exits non-zero on a refused or failed action, or on any action over 1 second (TS-5, QC-48). It times project creation only (`change_design.md` Architect Review Notes: "The timed run times project creation only").

#### Deliverables verified by review (no test asserts these — the gate is the diff)

- `tests/timed_run.py` — running `python3 tests/timed_run.py` from the product root exits 0 on a tracker as built, and its output names each timed action with its time.
- `tests/timed_run.py` — it uses a real `SavedData` at a location of its own, and never `data/`.
- `tests/timed_run.py` — it exits non-zero on a refused or failed action and on one over 1 second; the developer shows each by running it against a deliberately failing action and recording the exit status in `Developer Review Notes`.
- `tests/timed_run.py` — pytest does not collect it, so `pytest tests/` does not run it.

#### Implement

Verified by review — no test.

#### Verification gate

`pytest tests/` from the product root, then `python3 tests/timed_run.py`.

Pass criteria: every criterion above is met on reading the diff; the full suite has no new failures; the script exits 0.

### Task 14: Layer-6 walk — imports (`tests/architecture/test_imports.py`)

**Dependencies:** Task 3, Task 5, Task 6, Task 9, Task 10, Task 11

**What to build:** QC-13 to QC-19 and QC-43 as import walks over every `.py` file outside `tests/`. Hint (from `change_design.md` §4, G): walk with `ast`, and fail when the directory a walk covers holds no module (`docs/nfdr.md` § 1.2), so a wrong root cannot pass by finding nothing.

#### Behaviours to verify (developer adds tests to `tests/architecture/test_imports.py`)

- `test_domain_imports_only_errors_and_the_standard_library` (QC-13).
- `test_application_imports_only_domain_and_errors` (QC-14).
- `test_persistence_imports_only_domain_and_errors` (QC-15).
- `test_web_imports_only_application_and_errors` (QC-16).
- `test_main_imports_the_four_parts_and_errors_and_nothing_from_tests` (QC-17).
- `test_errors_imports_no_part` (QC-18).
- `test_nothing_outside_tests_imports_third_party_or_tests` (QC-19, QC-43).
- `test_each_walk_fails_when_its_directory_holds_no_module` — a walk rooted at an empty directory fails.

#### Implement

Tests cannot go red.

Reason: Tasks 3, 5, 6, 9, 10 and 11 build every directory this walk covers, each written inside the import graph, so the walk finds no violation to fail on.

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: this task's tests pass; no new failures elsewhere.

### Task 15: Layer-6 walk — what code may reach (`tests/architecture/test_reach.py`)

**Dependencies:** Task 3, Task 5, Task 6, Task 9, Task 10, Task 11

**What to build:** QC-20 (no `open`, `print`, `input`, `html` or clock in `domain/`), QC-42, QC-44, QC-45 (`print` and `sys.std*` only in `main.py` and one `web/` module), QC-37 (no `pickle`, `marshal`, `shelve`, `eval`, `exec`), QC-61, QC-28 (no `monkeypatch.setattr` or `mock.patch` aimed at a product module) and QC-9 (no `200` or `4000` length literal outside `domain/`). Hint (from §4, G): walk with `ast` over every `.py` file outside `tests/`, and fail when a walked directory holds no module. The QC-35 audit hook cannot be removed once added, so the test that uses it records `socket.connect` events and asserts only on those raised inside its own window.

#### Behaviours to verify (developer adds tests to `tests/architecture/test_reach.py`)

- `test_domain_does_no_input_output_and_reads_no_clock` (QC-20).
- `test_default_location_and_clock_are_reached_only_where_the_clauses_allow` (QC-42, QC-44).
- `test_print_and_std_streams_appear_only_in_main_and_one_web_module` (QC-45).
- `test_no_executing_reader_is_used` — `pickle`, `marshal`, `shelve`, `eval`, `exec` (QC-37).
- `test_no_test_patches_a_product_module` (QC-28).
- `test_no_length_literal_of_200_or_4000_outside_domain` (QC-9).
- `test_qc_61_holds` — as `docs/nfdr.md` QC-61 states it.
- `test_each_walk_fails_when_its_directory_holds_no_module`.

#### Implement

Tests cannot go red.

Reason: Tasks 3, 5, 6, 9, 10 and 11 build the code these clauses constrain, and each was written to them (Task 3 keeps wording and input/output out of `domain/`, Task 9 uses the re-exported maximums and not literals), so no clause is broken.

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: this task's tests pass; no new failures elsewhere.

### Task 16: Layer-6 walk — shapes (`tests/architecture/test_shapes.py`)

**Dependencies:** Task 3, Task 5, Task 6, Task 9, Task 10, Task 11

**What to build:** QC-1 (the top-level parts), QC-2 (concrete `persistence` and `web` classes named only in `main.py`), QC-3 (no class inherits `Saver` or `Clock`), QC-4 (one base from `Exception`, and every other exception from it), QC-6 (`domain/` dataclasses are frozen). It also re-proves what the deleted harness test asserted: `AppError` derives from `Exception`.

#### Behaviours to verify (developer adds tests to `tests/architecture/test_shapes.py`)

- `test_the_top_level_parts_are_the_five_the_sdd_names` (QC-1).
- `test_concrete_persistence_and_web_classes_are_named_only_in_main` (QC-2).
- `test_no_class_inherits_saver_or_clock` (QC-3).
- `test_one_base_error_and_every_other_derives_from_it` — `AppError` derives from `Exception`, and no other class does (QC-4).
- `test_domain_dataclasses_are_frozen` (QC-6).
- `test_each_walk_fails_when_its_directory_holds_no_module`.

#### Implement

Tests cannot go red.

Reason: Tasks 3, 5, 6, 9, 10 and 11 build every class these clauses cover (`Saver` and `Clock` are Protocols nothing inherits, every refusal derives from `AppError`, every `domain` dataclass is written frozen).

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: this task's tests pass; no new failures elsewhere.

### Task 17: Layer-6 check — pins (`tests/architecture/test_pins.py`)

**Dependencies:** Task 1

**What to build:** QC-39 and CP-28: every `pyproject.toml` dependency uses `==`, and `tests/requirements.txt` exists with every line `==`. QC-59: `requires-python = ">=3.11"`.

#### Behaviours to verify (developer adds tests to `tests/architecture/test_pins.py`)

- `test_every_declared_dependency_is_pinned_exactly` — every entry in every dependency list of `pyproject.toml` uses `==` (QC-39, CP-28).
- `test_the_lock_file_exists_and_every_line_is_exact` — `tests/requirements.txt` exists and each non-comment line is `name==version`.
- `test_requires_python_is_3_11` — `requires-python` reads `">=3.11"` (QC-59).

#### Implement

Tests cannot go red.

Reason: Task 1 pins every dependency and writes the lock, and these three tests read exactly the files Task 1 delivers.

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: this task's tests pass; no new failures elsewhere.

### Task 18: The trace pointer test, and the Projects entry docstring (`tests/architecture/test_trace.py`, `domain/projects.py`)

**Dependencies:** Task 3, Task 5, Task 6, Task 9, Task 10, Task 11, Task 12

**What to build:** the pointer test of SDD § 4 TS-4 (QC-11), and the finished opening docstring of `domain/projects.py`, which names the SRS requirements it realizes, every `application` and `web` module that takes part, and the test modules that check it, each of which exists. The test keeps a list of the feature words whose slice has landed, today only `projects`, and each later slice adds its own word (§ *Corrections owed*, SDD § 4 TS-4 and QC-11).

#### Behaviours to verify (developer adds tests to `tests/architecture/test_trace.py`)

- `test_every_path_named_in_the_entry_docstring_exists` — each path named in `domain/projects.py`'s docstring.
- `test_every_path_named_in_a_test_module_docstring_exists`.
- `test_every_requirement_identifier_named_exists_in_the_srs` — in the entry docstring and in each test module's docstring, against `docs/SRS.md` (QC-11).
- `test_every_test_module_names_a_requirement_or_acceptance_criterion` (QC-11).
- `test_each_landed_feature_word_has_its_domain_module` — today `projects` has `domain/projects.py`.
- `test_projects_entry_docstring_names_its_parts` — the docstring names at least one SRS requirement, one `application` module, one `web` module and one test module (QC-11: the entry docstring names them).

#### Implement

Infer from failing tests.

#### Verification gate

`pytest tests/` from the product root.

Pass criteria: this task's tests pass; no new failures elsewhere.
