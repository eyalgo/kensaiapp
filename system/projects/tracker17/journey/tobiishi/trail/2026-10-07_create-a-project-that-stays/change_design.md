# Change Design — Create a first project that stays after a restart

**Date:** 2026-10-07
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the console message when the tracker is ready; the console message when a start finds saved data it can't read; the console message when creating a project fails; the Projects page (its title and heading, the header's Projects link, the no-projects sentence, the create form's field labels, the note beside the description field, the Create button, the reason given beside a field for a blank name, a name already in use, a name too long and a description too long, and the message when a project couldn't be created); a project's page (its title, the no-tasks sentence, and the line confirming the project was created)

---

## 1. Change Summary

This design builds tracker17's first working path, as `change_spec.md` in this folder states it in CP-1 to CP-29. `python3 main.py` starts a tracker on a fixed loopback address. A person creates a project in the browser, sees it listed, and finds it again after a stop and a start. All five parts of `docs/SDD.md` § 3 are created here (`domain/`, `application/`, `persistence/`, `web/`, `main.py`), and the create action crosses all seven seams. The change also pins the test dependencies, ignores `data/`, and adds the three test layers, the layer-6 architecture walks the NFDR assigns to the change that first builds each module (`docs/nfdr.md` § 9), the trace pointer test and the timed run.

Every path below is relative to the product root, `products/tracker17/`. `docs/` is `products/tracker17/docs/`.

---

## 2. Blast Radius

Each new piece of logic sits in the part `docs/SDD.md` § 3 gives it. The *What changes* cell names that part.

| Module | Status | What changes |
|---|---|---|
| `domain/` | New | `domain` part: the two text maximums and the length check, the project entity, the create rule (blank, in use, too long), the Projects list order, the tracker state value, the start-time build that applies the same rules to saved values, and one typed refusal per refused condition. `domain/projects.py` is the Projects feature entry point (SDD § 4 TS-3). |
| `application/` | New | `application` part: the saver and clock contracts as `typing.Protocol` classes, and the `Tracker` that holds the current state, creates a project (rule, then save, then make current), and answers what the pages show. It re-exports the two maximums and the refusal types for `web`. |
| `persistence/` | New | `persistence` part: the default location `data/` under the product root, worked out from the code's own path; the JSON file format; reading once at start (state, no saved data yet, or unreadable); and the whole-state atomic save. |
| `web/` | New | `web` part: the loopback listener, the request check (SEC-2), the one-request-at-a-time lock (RT-6), the routes, form reading with line-break normalization (RT-10), the one address builder (RT-8), the one failure site (OB-3), page building through the one escaping function (SEC-4), and the stylesheet. |
| `main.py` | Modified | `main` part: the address constant, the real clock, wiring the four parts, the ready message, the unreadable-data message and non-zero exit, and a stop on Ctrl-C with no traceback. Today `main` returns 0 and does nothing. |
| `errors.py` | Unchanged | — Every new error class derives from `AppError`. |
| `pyproject.toml` | Modified | `[dependency-groups] dev` moves from floors to exact `==` versions and gains the browser-driving library. The comment that says "Floors, not pins" is rewritten to match. |
| `tests/requirements.txt` | New | The one committed lock file: every test dependency and everything it pulls in, each pinned with `==`. |
| `.gitignore` | Modified | Ignores `data/`. |
| `tests/` | Modified | `tests/unit/test_the_harness_runs.py` is deleted, because its own docstring says "Delete it once this product has a real test". New: `tests/unit/`, `tests/integration/`, `tests/e2e/` and `tests/architecture/` modules, `tests/e2e/conftest.py`, the collection rule in `tests/conftest.py`, and `tests/timed_run.py`. |

**Transitive radius.** Today no module imports another product module except the harness test, which imports `errors`. Every edge this change adds is one `docs/nfdr.md` § 1.2 allows: QC-13 to QC-18.

---

## 3. Sub-jobs

The five product parts are cut one sub-job per part. Two more sub-jobs hold what lives in no part: the root files, and the tests that walk every part at once.

### Sub-job A — `domain/`

**Scope:** `domain/__init__.py`, `domain/text.py`, `domain/refusals.py`, `domain/projects.py` and `domain/state.py`, with their unit tests. The old harness test is deleted here, because this sub-job lands the first real test.

**Exposes** (re-exported from `domain/__init__.py`):
- `SHORT_TEXT_MAX = 200` and `LONG_TEXT_MAX = 4000`. Both live in `domain/text.py`, the one place the lengths are stated (RT-10).
- `Refusal(AppError)` is the base of every refusal. `BlankName`, `NameInUse`, `TextTooLong` and `IdentityReused` derive from it. `TextTooLong` carries `field: str` (`"name"` or `"description"`) and `maximum: int`. No refusal carries wording shown to the operator.
- `Project(id: int, name: str, description: str)` is frozen. An empty `description` means the project has none.
- `TrackerState(projects: tuple[Project, ...], next_project_id: int)` is frozen. `empty_state()` returns it with no projects and `next_project_id` 1.
- `create_project(state, name, description) -> tuple[TrackerState, Project]` issues the next identity and raises a refusal. The checks run in this order: name too long, description too long, blank name, name in use. The values are kept exactly as given.
- `list_projects(state) -> tuple[Project, ...]` sorts by name with letter case ignored, and breaks a tie on the exact name.
- `find_project(state, project_id) -> Project | None`.
- `restore_state(projects: Sequence[tuple[int, str, str]], next_project_id: int) -> TrackerState` builds the state from saved values. Each project gets the same checks `create_project` applies. It raises `IdentityReused` when two projects share an identity or when an identity is not below `next_project_id` (SM-4, SD-5).

**Depends on:** none.

### Sub-job B — `persistence/`

**Scope:** `persistence/__init__.py` and `persistence/saved_data.py`, with their layer-2 tests.

**Exposes:**
- `DEFAULT_LOCATION: Path` is the absolute path of `data/` under the product root, worked out from the module's own file.
- `SavedData(location: Path)` keeps one file, `tracker.json`, inside `location`. It has these members:
  - `location`, the `Path` it was given.
  - `load() -> TrackerState | None` returns `None` when no saved data exists yet. It raises `UnreadableData` when the file cannot be read in full, is not the expected JSON shape, or breaks a `domain` rule that `restore_state` raises.
  - `save(state: TrackerState) -> None` replaces the file whole and atomically. It creates `location` when the directory is missing, and raises on failure.
- `UnreadableData(AppError)` carries `location`.
- The file holds a JSON object with `next_project_id`, and `projects` as a list of objects with `id`, `name` and `description`. Nothing else is stored.

**Depends on:** Sub-job A (`TrackerState`, `restore_state`, the refusal base `Refusal`).

### Sub-job C — `application/`

**Scope:** `application/__init__.py`, `application/contracts.py` and `application/tracker.py`, with their tests.

**Exposes** (re-exported from `application/__init__.py`):
- `Saver` is a Protocol with `save(state: TrackerState) -> None`. `Clock` is a Protocol with `now() -> datetime`, an aware UTC instant.
- `Tracker(state: TrackerState, saver: Saver, clock: Clock)` has these members:
  - `create_project(name: str, description: str) -> Project` applies `domain.create_project`, then calls `saver.save(new_state)`, and only then makes `new_state` current. A refusal propagates unchanged. A saver failure propagates unchanged, and the old state stays current.
  - `projects() -> tuple[Project, ...]`, ordered by `domain.list_projects`.
  - `project(project_id: int) -> Project | None`.
- `Project`, `TrackerState`, `SHORT_TEXT_MAX`, `LONG_TEXT_MAX`, `Refusal`, `BlankName`, `NameInUse` and `TextTooLong` are re-exported, so `web` imports only `application` (QC-5, QC-16).

**Depends on:** Sub-job A.

### Sub-job D — `web/`

**Scope:** `web/__init__.py`, `web/routes.py`, `web/pages.py`, `web/listener.py` and `web/style.css`, with the layer-3 and layer-4 tests.

**Exposes:**
- `Site(tracker: Tracker, own_host: str)` is built by the listener and by the tests. `own_host` is `"127.0.0.1:<port>"`. It has these members:
  - `handle(method: str, target: str, headers: Mapping[str, str], body: bytes) -> Response` is the whole request path, run in one process with no socket. It holds the site's one lock from the request check until the response is built (RT-6).
  - `ROUTES` is the table of method, path pattern and kind (page or submission) that the QC-7 route test enumerates.
- `Response(status: int, headers: tuple[tuple[str, str], ...], body: bytes)`.
- `listen(address: tuple[str, int], tracker: Tracker) -> Listener` binds and listens. `Listener` has `serve_forever()` and `server_close()`. The signal that the address is taken is left to the next change unit, so a bind error propagates.
- The addresses are fixed. `GET /` is the Projects page, and its query optionally carries `refused`, `failed`, `field`, `name` and `description`. `GET /projects/<id>` is a project's page, and its query optionally carries `created`. `POST /projects` creates a project. `GET /style.css` is the stylesheet. Any other address gets a 404 with an empty body.

**Depends on:** Sub-job C (`Tracker`, the re-exported maximums and refusal types).

### Sub-job E — `main.py`

**Scope:** `main.py`, its layer-1 and layer-2 tests, the end-to-end harness and tests under `tests/e2e/`, and `tests/timed_run.py`.

**Exposes:**
- `ADDRESS = ("127.0.0.1", 8017)`.
- `main(argv: list[str] | None = None) -> int` reads no argument and returns `start(ADDRESS, DEFAULT_LOCATION)`.
- `start(address, location: Path) -> int` wires the four parts, and starts from `domain.empty_state()` when `load` returns `None` (CP-6). When the saved data is unreadable it writes one message naming `location` and returns 1. Otherwise it listens, writes the ready message (address, then location), flushes, and serves until Ctrl-C. Ctrl-C closes the listener and returns 0.

**Depends on:** Sub-jobs B and D, and Sub-job F, because the end-to-end tests need the pinned browser-driving library.

### Sub-job F — root files

**Scope:** `pyproject.toml`, `tests/requirements.txt` and `.gitignore`, plus the collection rule in `tests/conftest.py` that keeps `pytest tests/` from collecting `tests/e2e/`.

**Exposes:** a virtual environment built from `tests/requirements.txt` that holds pytest and the browser-driving library, and a `data/` that version control ignores.

**Depends on:** none.

### Sub-job G — `tests/architecture/`

**Scope:** the layer-6 walks and the TS-4 pointer test. The Projects entry point's opening docstring in `domain/projects.py` is finalized here, so every path it names exists.

**Exposes:** nothing.

**Depends on:** A, B, C, D, E and F. Every walk fails when the directory it walks holds no module (`docs/nfdr.md` § 1.2), and the pins test reads Sub-job F's files.

**Build sequence:**
```
Parallel start: A, F
After A: B, C  [parallel]
After C: D
After B + D + F: E
After E: G
```

**Atomic-landing edges:** none. Each sub-job leaves `pytest tests/` green on its own.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| A — `domain/` refusal order | `create_project` checks in a fixed order: name length, description length, blank, in use. That order is how CP-20's precedence holds by construction, including the name winning when both values are too long. |
| A — `domain/` list order | Sort with the key `(name.casefold(), name)`. `casefold` is the Unicode case mapping CP-12 leaves to this stage, and the exact name breaks ties. |
| A — `domain/` blank name | A name is blank when every character satisfies `str.isspace()`, the set tracker16-X's `name.strip()` uses (spec, Locked Answers Gap 13). Length is `len(value)`, which counts code points (RT-10). |
| A — `domain/` module cycle | `projects.py` names `TrackerState` only for typing and builds the next state with `dataclasses.replace`. `state.py` can then import `projects.py` for `restore_state` with no import cycle at run time. |
| B — `persistence/` atomic save | Write to a second file in the same directory, flush it, `os.fsync` it, then `os.replace` it over `tracker.json` (ADR-0004). `load` never reads the second file. Missing file → `None`. A decode error, a JSON error, a wrong shape or type, and a `domain` `Refusal` from `restore_state` → `UnreadableData`. Read with `json`, never with a reader that executes (QC-37). |
| C — `application/` | None |
| D — `web/` listener | Use `http.server.ThreadingHTTPServer` with a handler that passes method, target, headers and body to `Site.handle`. Override the handler's `log_message` so it writes nothing (OB-1). Replace the default error page body so it carries no Python-produced text (CP-23). |
| D — `web/` request check | Read header names without regard to case. Refuse with 403 and an empty body when `Host` is not `own_host`, when `Sec-Fetch-Site` is `cross-site` or `same-site`, or when a submission is not marked `same-origin` (a missing mark included). |
| D — `web/` form values | Parse `application/x-www-form-urlencoded` with `urllib.parse.parse_qs(keep_blank_values=True)` as strict UTF-8. Answer an undecodable body with 400 and an empty body. Then replace every CR LF, and every lone CR, with LF before the value reaches `application` (RT-10). Truncate nothing. |
| D — `web/` addresses | Answer every submission with 303 to an address built by one function (RT-8). Success → `/projects/<id>?created`. Blank or in-use refusal → `/?refused=<code>&name=…&description=…`. `TextTooLong` → `/?refused=too-long&field=<field>`, carrying no typed value. Save failure → `/?failed=create&name=…&description=…`. Map a refusal to its code by its type, and read `TextTooLong.field` as an attribute (OB-4). Every other exception lands in the one `except` that writes the action and the error to `sys.stderr` (OB-3). |
| D — `web/` pages | One function escapes every value with `html.escape(…, quote=True)` (SEC-4). Write a newline straight after the `<textarea>` start tag, because the HTML parser drops one leading newline there. Show names and descriptions with `white-space: pre-wrap`, so surrounding spaces and line breaks show (CP-13). A refused or failed page puts `autofocus` and `aria-describedby` on the control used, either the field the reason concerns or the Create button for a failure (RT-9, EX-14). Every response carries `Content-Security-Policy: default-src 'self'; script-src 'none'; form-action 'self'; frame-ancestors 'none'` as a header. Write `maxlength` and the number in the description note from the two re-exported constants. |
| E — `main.py` | Write the ready line only after `listen` returns, flush stdout straight away, and then call `serve_forever` (OB-2). Catch `KeyboardInterrupt` around `serve_forever` and close the listener. |
| E — end-to-end harness | Bind port 0 to find a free port. Run `sys.executable -c` with an import of `main` and a call to `start((host, port), tmp_location)`, from a working directory that is not the product root and with `PYTHONPATH` set to the product root. Read stdout until the ready line arrives. Stop the process with `SIGINT`. Drive Chromium through the browser-driving library, and send the hand-built over-long request through its request API with `Host` and `Sec-Fetch-Site: same-origin` set. |
| F — root files | The browser-driving library is Playwright for Python (`playwright`), with plain pytest fixtures and no plugin. Build the lock by installing the pinned group into a fresh `venv` and freezing it to `tests/requirements.txt`, with every line `==`. In `tests/conftest.py`, `pytest_ignore_collect` skips `tests/e2e/` unless the command line names `tests/e2e`. |
| G — architecture walks | Walk with `ast` over every `.py` file outside `tests/`. Each walk fails when the directory it walks holds no module. The QC-35 audit hook cannot be removed once added, so the test records `socket.connect` events and asserts on the ones raised inside its own window. |

---

## 5. Test Additions

Layers follow `docs/nfdr.md` § 9. "Restart" means a new `Tracker` built from what the saver last saved (layer 3), or a new process (layer 5).

| Sub-job | Test file | What to add / modify |
|---|---|---|
| A | `tests/unit/test_the_harness_runs.py` | Delete it. It proves `issubclass(AppError, Exception)`, which `tests/architecture/test_shapes.py` re-proves for QC-4. |
| A | `tests/unit/test_projects.py` | CP-12: `beta`, `Alpha`, `alpha` list as `Alpha`, `alpha`, `beta`, and a non-ASCII pair such as `Émile`/`émile` also compares case-blind. CP-13: `  Alpha  ` and a two-line description are kept exactly. CP-14: empty, three spaces, tab and line break, and two U+00A0 are each `BlankName`. CP-15: `Alpha` is refused once `Alpha` exists, while `alpha` and `Alpha ` are accepted. CP-16: a 200-character name and a 4,000-character description are accepted, 201 and 4,001 raise `TextTooLong` with the right `field`, and a non-BMP character counts as one. CP-20: an over-long name with a blank name gives `TextTooLong("name")`, a blank name with a 4,001-character description gives `TextTooLong("description")`, and both over-long gives `"name"`. Identities rise from 1. The predecessor's project-name tests come over with the rule (SDD § 11 R-5). |
| A | `tests/unit/test_state.py` | CP-8, SD-5: `restore_state` raises a refusal for a blank name, two projects with one exact name, a 201-character name, a 4,001-character description, a shared identity, and an identity not below the counter. A valid set round-trips. |
| E | `tests/unit/test_address.py` | QC-30: `main.ADDRESS`'s host is loopback. CP-2 is covered here too: the address is one constant, so every start uses it. |
| B | `tests/integration/test_saved_data.py` | CP-6: no file → `None`. Save then load round-trips, and the first save creates the directory. CP-7, CP-8: a truncated file, bytes that are not UTF-8, the wrong JSON shape, and each `restore_state` break all raise `UnreadableData`, and the file's bytes are unchanged afterwards. CP-4, QC-42: `DEFAULT_LOCATION` printed by a subprocess started from another working directory equals `<product root>/data`. CP-26, AC-9: a subprocess saves alternating states in a loop and is killed with `SIGKILL` at a random moment, many times over. After each kill, `load` returns one of the saved states and never raises. A leftover second file beside `tracker.json` is ignored. QC-46: after creates, the file holds only the keys in § 3 Sub-job B. |
| C | `tests/integration/test_tracker.py` | QC-49, CP-24: the saver receives the new state before `projects()` shows it. With a failing saver (AC-18), the state is unchanged and the error propagates. A refusal makes no save call. Restart from the last saved state lists the project. A project identity is not issued twice across a restart (QC-10, project half). |
| D | `tests/integration/test_pages.py` (layer 4) | CP-11: builds the create form and finds the number the description note states equal to the description field's `maxlength`, with the name `maxlength` at 200. CP-9: every page has a header with exactly one link, to Projects. CP-10: the first-run Projects page has the no-projects sentence and the form. CP-12: the list shows names as links in order, with descriptions. CP-17: a project's page has its name, description and the no-tasks sentence, and no other form or control. CP-23, QC-36: `<b>A&B</b>` and `"` come out escaped in the list, on the project page, and in the prefilled field and textarea. A description starting with a line break keeps it. No page has `<script>`, a `<meta>` policy, or an outside address (QC-33). CP-19: the refused page puts `autofocus` and `aria-describedby` on the name field, pointing at the reason. |
| D | `tests/integration/test_routes.py` (layer 3) | CP-18: a create answers 303 to `/projects/<id>?created`, and two GETs of that address leave one project and show the same line. CP-19, CP-21: duplicate and blank names answer with the Projects page holding the reason and both typed values, make no save call, and give the same reason on reload. CP-20, CP-16: an over-long description, an over-long name, a blank name with a 4,001-character description, and both values over-long each give the right field, and the response address and page hold none of the sent text. CP-22, AC-10: POSTs marked `cross-site`, `same-site`, `none` and unmarked are each refused with the state unchanged, a GET marked `none` opens the page, and a GET marked `cross-site` is refused. QC-31: a wrong `Host` is refused. CP-25, AC-18, QC-56, QC-57: with a failing saver, stderr names the action and the error, the failure page keeps the typed values with no traceback or exception text, and a restart does not list the project. RT-10: a description sent with CR LF and lone CR is saved with LF. QC-7, QC-8, QC-34: for every entry in `ROUTES`, a non-submission leaves the state unchanged, a submission gets a redirect, and no response sets a cookie or lacks the policy header. QC-53: a saver held open makes a second submission wait. QC-35: an audit hook sees no `socket.connect` across the actions. An unknown project identity gets a 404 with no Python text. |
| E | `tests/integration/test_start.py` (layer 2) | CP-7: `start` against an unreadable location returns non-zero, writes one message naming the location and no ready message, and leaves the bytes unchanged. CP-5, QC-47: `git check-ignore -q data/tracker.json`, run from the product root, exits 0. |
| E | `tests/e2e/test_first_project.py` (layer 5) | CP-1, QC-55: the first stdout output is the ready message, with the address before the location. CP-10, CP-13, CP-17, CP-18: on first run, create `  Alpha  ` with a two-line description, land on its page, and find the spaces, the line break, the no-tasks sentence and the created line. CP-3, CP-24, AC-6 (project half): create `Alpha` with description `x`, send `SIGINT`, see a clean exit with no `Traceback` on stderr, start again, and find `Alpha` with `x` listed. CP-12: `beta`, `Alpha`, `alpha` list in order. CP-19: with `Alpha` saved, creating `Alpha` with `notes` puts focus on the name field, with the reason as its accessible description and both values kept. CP-16, AC-20: fill the description to 4,000 characters with line breaks, and the saved file holds it whole. CP-20, AC-12: a hand-built 201-character name gets a page that gives the reason with focus on the name field and none of the 201 characters, and the file's bytes are unchanged. CP-23: `<b>A&B</b>` shows as text. |
| E | `tests/timed_run.py` | TS-5, QC-48: one location of its own, a real `SavedData`, and project creation timed through `Site.handle` with `same-origin` marks, at stated ordinary lengths. It exits non-zero on a refused or failed action, or on any action over 1 second. |
| G | `tests/architecture/test_imports.py` | QC-13 to QC-19 and QC-43, as import walks. |
| G | `tests/architecture/test_reach.py` | QC-20 (no `open`, `print`, `input`, `html` or clock in `domain/`), QC-42, QC-44, QC-45 (`print` and `sys.std*` only in `main.py` and one `web/` module), QC-37 (`pickle`, `marshal`, `shelve`, `eval`, `exec`), QC-61, QC-28 (no `monkeypatch.setattr` or `mock.patch` aimed at a product module), and QC-9 (no `200` or `4000` length literal outside `domain/`). |
| G | `tests/architecture/test_shapes.py` | QC-1 (the top-level parts), QC-2 (concrete `persistence` and `web` classes named only in `main.py`), QC-3 (no class inherits `Saver` or `Clock`), QC-4 (one base from `Exception`, and every other exception from it), QC-6 (`domain/` dataclasses are frozen). |
| G | `tests/architecture/test_pins.py` | QC-39, CP-28: every `pyproject.toml` dependency uses `==`, and `tests/requirements.txt` exists with every line `==`. QC-59: `requires-python = ">=3.11"`. |
| G | `tests/architecture/test_trace.py` | TS-4, QC-11: every path named in the `domain/projects.py` docstring and in each test module's docstring exists. Every requirement identifier named there appears in `docs/SRS.md`. Each feature word whose slice has landed, today only `projects`, has its `domain/<word>.py` (see Architect Review Notes, the trace test). |

**Coverage map.**
- CP-27 is covered by the G rows.
- CP-29 is covered by both suites exiting 0 with the rows above among the tests run.
- CP-6's page half is covered by the CP-10 row in `test_pages.py`.
- CP-21's "before or after a restart" is covered by the restart rows in `test_routes.py` and `test_tracker.py`.

**What this change stops proving:** the deleted harness test's assertion is re-proved by QC-4 in `test_shapes.py`.

---

## Records this change makes false

- `docs/SDD.md` § 4 TS-4: the sentence "or when a feature word in the table below has no module" goes false. The pointer test lands in this slice (§ 11 R-6, "that test runs in `pytest tests/` from `first-project` on"), and ten of the eleven feature words have no module yet. → "…or when a feature word whose slice has landed has no module; each slice that delivers a feature adds its word to the test."
- `docs/nfdr.md` QC-11 *verified by*: the clause "or a feature word with no module" goes false for the same reason. → "…or a feature word, among those whose slice has landed, with no module."
- `docs/SDD.md` § Open Questions, the third item ("Which port the fixed address uses"): this change settles it. → Remove it, and record the port as `8017` in § 4 RT-5.
- `docs/SDD.md` § Open Questions, the first item (how Chromium counts a line break against `maxlength`), and the form-control half of the second item (whether Chromium honours `autofocus`): both are answered when the CP-16 and CP-19 end-to-end tests pass. → Remove the first item. Narrow the second to an element that is not a control, which `tasks-in-a-project` tests.

---

## Architect Review Notes

**Decisions beyond the spec**

- **The port is 8017 (b).** CP-2 leaves the port to this stage, and SDD § Open Questions asks for it. 8017 is fixed in `main.ADDRESS`. 8000, the port in CONTENT's examples, was not taken, because Python's own `http.server` defaults to it and it is the one most likely to be in use.
- **The case mapping is `str.casefold`, with the exact name breaking ties (b).** CP-12 leaves the mapping here, and requires `A` to `Z` and `a` to `z` to compare equal. `casefold` satisfies that and covers Unicode letters. The order comes from an explicit sort key, so it holds by construction rather than by insertion order.
- **Blank means `str.isspace` on every character (b).** CP-14 asks for every character Unicode classes as whitespace. The spec's Locked Answers Gap 13 fixes the predecessor's `strip()`, which uses the `isspace` set.
- **Refusal precedence comes from the check order (b).** CP-20 states the outcome, and the fixed order in `create_project` produces it.
- **`Refusal` is a base class in `domain/refusals.py` (b).** It lets `persistence` report any rule break as unreadable, and lets `web` tell a refusal from a failure, by type alone. The SDD names no such base (`docs/nfdr.md` RN-5). Adding one changes no import edge.
- **`IdentityReused` is checked at start (b).** The project identity arrives in this change (SDD § 3, "What the system holds"), so its rule is one SD-5 requires to be checked at start. CP-8 does not list it.
- **An empty description means none (b).** The form always sends the field, so one representation is enough. tracker16-X's `str | None` is not carried over, because it gives two values for one fact.
- **The saved data's location is the `data/` directory, and its file is `data/tracker.json` in JSON (b).** The ready message and the unreadable message name the directory. CONTENT's examples name a directory too ("Saved data is kept at /Users/sam/tracker17/data").
- **The browser-driving library is Playwright, and the lock is `tests/requirements.txt` in pip's requirements format (b).** No upstream document names the library (`docs/nfdr.md` § 9). The pip format is the one QC-40's RN-18 cites as read by GitHub's dependency graph. I don't know whether that graph reads a file inside `products/tracker17/tests/`. The check is the repository's dependency-graph page once the change is pushed.
- **`pytest tests/` does not collect `tests/e2e/` (b).** `docs/nfdr.md` § 10 treats `pytest tests/` and `pytest tests/e2e/` as two suites. The project card's `Test command: pytest tests/` runs on the machine's pytest, where `python3 -c "import playwright"` printed `ModuleNotFoundError: No module named 'playwright'` on 2026-10-07. The end-to-end suite runs inside the `venv` that `tests/requirements.txt` builds.
- **A request the check refuses gets 403 with an empty body, and an unknown address gets 404 with an empty body (b).** No UXD or CONTENT entry gives either one words. The not-found page belongs to a later change unit of this station (spec, Out of Scope).
- **A failed create opens at the Create button (b).** EX-4 opens a failed submission "at the control that was used". For a failure the reason concerns no single field, so the control used is the button.
- **A project's page after a create puts `autofocus` on its heading, which is focusable but not a Tab stop, and the created line is that heading's accessible description (b).** EX-5 opens a different page at its start, and EX-14 makes the line the accessible description of the element the page opens on. The heading is that element. This tests SDD § 11 R-2's non-control case earlier than planned, at layer 4 only. The browser-level test stays with `tasks-in-a-project`.
- **"None of the sent text" holds because the address carries no sent value (b).** The refusal address for `TextTooLong` carries only the reason code and the field, so nothing on the page comes from the request. A saved project whose name happens to match sent text is still listed, because it is saved data. The tests use sent text that matches no saved project.
- **The unreadable-data exit status is 1 (b).** CP-7 asks for non-zero.
- **The timed run times project creation only (b).** The spec leaves TS-5 to this stage. SRS NFR-1 lists "creating", so the run exists from this slice on. Neither tasks nor comments exist yet, so it builds no volume. SDD § 11 R-1 puts full volume in `comment-on-a-task`.
- **The layer-6 walks, the route test, the policy test, the audit-hook test and the lock test land here (b).** The spec names none of them. `docs/nfdr.md` § 9 assigns each to "the change that first builds the module it checks", and this change builds every module.
- **The clock crosses SM-7 with no rule reading it yet (b).** The request requires the seams to be "used as written", and SM-7 carries the clock. `main` builds the real clock and hands it in, as QC-44 requires. The first rule that reads it arrives with tasks.

**A contradiction between two records**

- **The trace test checks only the feature words whose slice has landed (a).** SDD § 4 TS-4 says the test fails on any feature word in the table with no module. § 11 R-6 says the test runs from `first-project` on. Both cannot hold while ten features are unbuilt. The test keeps a list of landed words, and each slice adds its own. The Records section above carries the correction.

**Logic the parts table alone could not place**

- **The RT-6 lock lives in `web`'s `Site` (e).** No row of SDD § 3 names the lock. RT-6 starts it "from the moment a request's check begins", and the request check is `web`'s (SEC-2). A lock in `application` would leave the check outside it. The lock sits on the `Site` object rather than in a module-level value, so QC-8's "keeps nothing between requests" holds.

**Reviews `docs/nfdr.md` delegates to `development-design`**

| QC | Verdict |
|---|---|
| QC-5 | Pass. `web` maps refusals by type, `application` defines no refusal, and `TextTooLong.field` is read as an attribute. |
| QC-8 | Pass. A `Site` holds only the tracker, `own_host` and the lock. |
| QC-12 | Pass. The design adds the SDD's five parts, one module per concern inside each, and nothing else. The clock is the one item paid for by a seam rather than a behaviour, as noted above. |
| QC-20 | Pass. The refusals carry field identifiers and no wording. |
| QC-21 | Pass. `Tracker` calls `domain` for every rule and the order. |
| QC-22 | Pass. `persistence` checks shape and types only, and rules come from `restore_state`. |
| QC-23 | Pass. `web` checks no value. Line-break normalization is the one change RT-10 allows. |
| QC-24 | Pass. `main` decides only to exit on unreadable data, which its row gives it. |
| QC-25 | Pass. The format is confined to `persistence/saved_data.py`. |
| QC-26 | Pass. This change introduces the whole-state save as ADR-0004 states it. |
| QC-27 | Pass. HTML and request detail stay in `web`. |
| QC-36 | Pass. One escaping function in `web/pages.py` takes every value, attributes and textarea content included. |
| QC-41 | Pass. The design reads, holds and writes no secret. |
| QC-46 | Pass. The design stores only DR-1's fields, the identity and its counter, and `test_saved_data.py` checks the keys. |
| QC-60 | Pass on a condition, because the harness gap stands. The code must use nothing newer than Python 3.11, such as the `type` statement, PEP 695 generics, `itertools.batched` or `Path.walk`. |
| QC-40 | Not performed. This change adds test dependencies and chooses the lock format, which are both review moments. The concrete pins do not exist until implementation installs them, so there is nothing yet to check against advisories. I also had no way to read advisory feeds or Chromium's security releases in this run. The condition this design sets is that each pin is the current release on the day it is installed. The check of those pins against advisories needs a reviewer, and it is the first item of the next `development-design` review. |
