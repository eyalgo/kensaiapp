# Tech Lead instruction — unreadable-start-non-text-path: display the saved-data path and keep serving

**Category:** feature
**Behaviour:** changing
**Product root:** products/tracker17 — every source and test path below is relative to it.
**Scope:** Implement CP-757–CP-772 of `change_spec.md` for `tracker17 · tobiishi · 2026-10-30_unreadable-start-non-text-path`.

This instruction owns the task cut, test behaviours and verification gates for the unreadable start. The requirements and public contracts remain in `change_spec.md` § Rules and `change_design.md` §§ 2–5 of the change named above.

## Project layout

```text
products/tracker17/
  main.py                                    ← modified: unreadable announcement's location field
  web/
    pages.py                                 ← modified: unreadable page's location field
  tests/
    unit/
      test_unreadable_message.py              ← new
    integration/
      test_unreadable_path.py                 ← new
      test_unreadable_start.py                ← new
```

Create the three test files in the existing directories. No new package or `__init__.py` is required: the existing test directories contain plain test modules (`tests/unit/test_start_message.py:1-20`, opening docstring and imports; `tests/integration/test_ready_start.py:1-39`, opening docstring and imports).

Console display belongs in `main.py`, and page display belongs in `web/pages.py`, per `docs/SDD.md:216-248` § 3, rows `main` and `web`. Keep the five-part module set and permitted imports of `docs/nfdr.md:32-45` QC-1–QC-2 and `docs/nfdr.md:180-211` § 1.2. In particular, `web` cannot import `main`, `domain`, `persistence`, tests or third-party packages (QC-16); `main` can import the four parts and `errors`, but neither tests nor third-party packages (QC-17). The remaining parts and `errors.py` retain their existing boundaries (QC-13–QC-15, QC-18–QC-19).

All shell commands below run from the change worktree root unless a block explicitly says product root. The project card names headless execution and Python (`system/projects/tracker17/project.md`, `Execution type:` and `Languages:`). Language resolution: Python, step 1, that card's `Languages:`; packet `core/doctrine/engineering/languages/python/README.md`, including its layout, conventions, errors/logging, quality-gates, environment and testing destinations.

## TL Review Notes

Tech Lead decisions, 2026-10-30:

- **Task cut:** Group design sub-jobs A and B and their shared real-start proof into Task 1. This is one cohesive responsibility, the unreadable start's path display. The reason is CP-769's requirement to observe all three new proofs fail on the starting tree: page construction precedes announcement (`main.py:124-144`, `_serve_claimed`; `web/routes.py:1344-1346`, `UnreadableSite.__init__`). One behavioural task keeps that proof available before either rendering change, while preserving the separate owners and the independent production interfaces of `change_design.md` § 3. This does not assert an atomic-landing edge or change the import graph.
- **One-change checks:** Task 2 carries the untouched-file and unchanged-regression-assertion checks from CP-763–CP-764 and `change_design.md` § 5, T12. These are deliverables verified against this branch's merge base, not lasting tests of repository history.
- **Trace precision:** The new test modules name their SRS requirements as well as CP/QC rules. The pointer checker reads requirement identifiers (`tests/architecture/test_trace.py:121-136`, `test_every_test_module_names_a_requirement_or_acceptance_criterion`); CP-770 requires that existing check to remain green.
- **Hint scope:** Task 1 carries design § 4 B's field-local conversion hint. Its console half needs no hint, as design § 4 A states. The real-child pattern remains a test-boundary constraint, with no added production seam (`change_design.md` § 4, paragraph beginning “The real-start proof”).
- **Gate-command check:** The card's exact command, `uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`, collected 2,969 tests in its first invocation and exited 1 with `152 failed, 2797 passed, 20 errors in 309.98s`; the second invocation did not execute. An independent `socket.bind(('127.0.0.1', 0))` probe returned `PermissionError: [Errno 1] Operation not permitted` in this planning sandbox. This is no green baseline and supplies no CP-769 encoding red. Retain the card's working collection command; the required green result remains a verification gate. The evidence-only `gate_suite.py check` returned `resolves — owners-mac: the product has no CI, so its gates run on the owner's Mac`, exit 0, using the JSON below.

## Gate environment inputs

```json
{
  "languages": {"declared": ["python"], "invoked": null},
  "ci": {
    "finding": "none",
    "inventory": "git ls-files at the change worktree root: inspected the tracked root entries and the product's complete tracked-file listing; no CI configuration or runner configuration found. Root entries: .claude, .env.example, .gitignore, .providers.toml.example, .python-version, .telemetry.env, AGENTS.md, Brewfile, CLAUDE.md, Containerfile, README.md, about, core, docs, kensaiapp.md, products, pyproject.toml, skills, system, uv.lock. The product's only tracked build/config file is products/tracker17/pyproject.toml. The root Containerfile builds the interactive sandbox and names no CI runner."
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

### Task 1: Render the unreadable start's location at both display owners (`main.py`, `web/pages.py`)

**Dependencies:** None

**What to build:** Make the unreadable announcement and page accept an original filename-decoded path, display each U+DC80–U+DCFF marker as its lowercase four-character byte escape, and preserve every other character and surrounding word (CP-757–CP-764; `docs/CONTENT.md:135-139`, “A path the tracker prints”). Use the existing console formatter for `_unreadable_line`; put the page's conversion inside its page-building owner before the existing HTML escape (`change_design.md` § 3 A–B).

Preserve `_unreadable_line(host: str, port: int, location: Path) -> str`, `start(address: tuple[str, int], location: Path) -> int`, `unreadable_data_page(location: str) -> str`, `UnreadableSite(location: str, own_host: str)` and `listen_unreadable(address: tuple[str, int], location: str) -> Listener` (`change_design.md` § 3, Exposes). Direct field renderers preserve their input apart from the marker mapping; the real start supplies the absolute display path (`main.py:124-144`, `_serve_claimed`).

#### Behaviours to verify

Add tests in the three new modules shown in Project layout. Expected text is specified independently from the product formatters, using CP-757–CP-763 and the published strings, including `change_text.md` when present.

- `test_unreadable_line_displays_a_decoded_byte_as_four_characters` — in `tests/unit/test_unreadable_message.py`, call `_unreadable_line` with `Path(os.fsdecode(b'/tmp/caf\xe9/data'))`; compare the entire CP-757 line, the literal `/tmp/caf\xe9/data`, no U+FFFD, no U+DC80–U+DCFF and no `\udce9`, and successful strict UTF-8 encoding (CP-760, CP-765; design T1).
- `test_unreadable_line_escapes_each_filename_byte` — cover every marker U+DC80–U+DCFF, endpoints included, with independently specified lowercase expected digits (CP-760–CP-761; T8).
- `test_unreadable_line_preserves_positions_and_other_characters` — consecutive, separated, repeated and cross-component markers; `b'/tmp/a\xe9\xff/data'`; valid `é` and literal backslashes beside markers retain position and text (CP-760–CP-761; T8).
- `test_unreadable_line_keeps_ordinary_paths_verbatim` — compare the complete ordinary line for ASCII, `/tmp/café/data` and the literal-backslash name `a\xe9b` to pre-change expectations (CP-763; T10).
- `test_unreadable_line_leaves_other_surrogates_untouched` — U+DC7F, U+DD00 and U+D800 remain unchanged in the returned line, without broadening the supported filename-marker range (spec § Out of Scope; T10).
- `test_unreadable_site_accepts_the_original_decoded_location` — in `tests/integration/test_unreadable_path.py`, construct `UnreadableSite` with the original `os.fsdecode(b'/tmp/caf\xe9/data')`, without preprocessing. A checked `GET /` returns 503 and strict UTF-8 page bytes containing the required escape and no forbidden marker or replacement character. Assert the direct `pages.unreadable_data_page` representation too (CP-759–CP-760, CP-766; T2).
- `test_unreadable_page_escapes_each_filename_byte_in_place` — every marker, range endpoints, consecutive/separated/repeated/cross-component cases and the two-byte example retain all surrounding text; direct page and site assertions use independent expectations (CP-760–CP-761; T8).
- `test_unreadable_page_shows_markup_beside_byte_markers_as_text` — combine `<`, `&`, `"`, valid non-ASCII text, a real backslash and a marker. Parse the page using the existing `tests/integration/test_pages.py` parser; assert the paragraph's literal text, absence of injected elements and the existing raw HTML escape form (CP-761, QC-36; T9).
- `test_unreadable_page_keeps_ordinary_representations` — compare complete direct page text and served page bytes to independent pre-change ordinary-path expectations, including valid `é` and literal backslashes (CP-763; T10). Neither expectation is generated by the new formatter.
- `test_unreadable_site_still_rejects_other_surrogates` — construction with U+DC7F, U+DD00 or U+D800 still raises `UnicodeEncodeError`; direct page text preserves those characters (spec § Out of Scope; T10).
- `test_unreadable_byte_path_keeps_route_policy` — for one directly constructed site, checked reads at `/`, `/?x=1`, `/people` and `/nothing?x=1` have identical 503 bodies and `Cache-Control: no-store`; `GET /style.css` is 200; a `same-origin` `POST /projects` is 303 with the existing redirect destination. Verify page-policy headers and no navigation/data controls (CP-758, CP-764; T6). Keep existing request-refusal tests unchanged.
- `test_unreadable_start_prints_then_serves_and_stops` — in `tests/integration/test_unreadable_start.py`, create a regular file in test-owned storage and choose a decoded-byte location beneath that file. Start real `main.start` in a child with strict UTF-8 stdout and an ephemeral loopback port. Assert the complete first stdout line as bytes, parse its address, request the 503 page in the same escape form, send SIGINT, and assert exit 0, no later stdout and empty stderr. Compare the regular file's bytes and its containing directory listing before/after. This case never skips (CP-757, CP-760, CP-764, CP-767, CP-771; T3).
- `test_unreadable_start_is_independent_of_console_encoding` — repeat the never-skipping regular-file scenario under strict ASCII, the C locale with coercion disabled, and Python UTF-8 mode. Remove inherited console variables before selecting each case. Use ASCII fixture prefixes and both single and consecutive markers; check identical ASCII escape bytes, served page and quiet shutdown (CP-762; T5).
- `test_unreadable_start_preserves_a_real_byte_named_saved_file` — attempt creation of a directory actually named with the byte, write malformed `tracker.json`, and assert the full line/page, unchanged file bytes and directory listing, and absence of a directory named with the four-character display escape. Only an actual filename refusal during directory creation permits this case to skip, with that refusal in the reason; other setup failures fail. No OS-name guard (CP-764, CP-768; T7).
- `test_unreadable_relative_byte_path_is_shown_as_one_absolute_path` — start with a relative decoded-byte location beneath a regular file, check the single absolute displayed location in both surfaces, unchanged file bytes/listing and no directory with the escape spelling (CP-761, CP-764; T11).
- Existing architecture tests and new-module requirement headers — `tests/architecture/test_imports.py`, `test_reach.py`, `test_trace.py` stay green. New modules name SRS FR-1, FR-8, NFR-3, NFR-4, NFR-8 and AC-7 where applicable, plus their CP/QC coverage; patch no product-module name (CP-770, CP-772; T13).

The real-start tests follow the bounded child-process pattern in `tests/integration/test_ready_start.py:37-185`, `START_PROGRAM`, `child_environment` and `_Start`: path bytes reach the child losslessly, decoding happens there, every read/request/wait has a deadline, and teardown reaps children on assertion failure (design § 4). Keep this test harness local to the new test module; no existing test assertion needs changing.

The three required primary proofs are red against the starting product, before either display changes, and green after: the full line test, direct-site test and strict UTF-8 real-start test. Record the actual failing commands and failures and subsequent passing results in the implementation evidence (CP-769; T4). A socket-permission failure is not evidence of the required encoding failure. No lasting test reads Git history.

#### Held by review

- Field ownership and capability boundaries — read the production diff against `docs/SDD.md` § 3 and `docs/nfdr.md` QC-2, QC-23–QC-24, QC-36 and QC-45: the page mapping precedes the one `_escape`; there is no state, filesystem/clock reach, new console writer or cross-part formatter import. The architecture suite checks the machine-readable subset, not semantic ownership.
- Unchanged original persistence location — review the diff for CP-764: only display fields change; `start`, `_serve_claimed`, claim/load/save operations, listener/routing policy, `_ready_line`, the existing `_shown_location` algorithm and failed-action reporting retain their behaviour. The real-file and directory snapshots and existing regression suites provide the observable proof.

#### Implement

Infer from failing tests.

# Hint:
Apply a field-local mapping of U+DC80–U+DCFF to lowercase byte escapes before the existing HTML escape. The existing `main._shown_location` is the shape reference, not an import target. Broad Unicode backslash replacement would spell a surrogate rather than the required byte; changing `_escape` would reach unrelated fields.

#### Verification gate

From the change worktree root, the focused command is:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/unit/test_unreadable_message.py products/tracker17/tests/integration/test_unreadable_path.py products/tracker17/tests/integration/test_unreadable_start.py
```

Run the project's complete test command, unchanged:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/
```

From the product root, check QC-62 through its locked environment:

```sh
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked mypy main.py errors.py domain application persistence web
```

Pass: the focused command and both card invocations exit 0, all three primary proofs have their required encoding/path red and green evidence, and all three quality commands exit 0. The real byte-directory case alone may skip on its actual filename refusal. Existing ordinary unreadable-line, page, route, single-tracker, location, saved-data, ready-start and browser assertions pass untouched (CP-763–CP-764, CP-768–CP-772; design T12–T14).

### Task 2: Verify this change's untouched boundaries (`main.py`, `web/pages.py`, `tests/`)

**Dependencies:** Task 1 — reviews its completed production and test diff.

**What to build:** A review verdict for the change-specific boundaries of CP-763–CP-764 and spec § Out of Scope, without adding permanent tests of repository history.

#### Deliverables verified by review

- Product definition and instructions are unchanged — from the product root, `git diff "$(git merge-base main HEAD)" -- docs README.md pyproject.toml uv.lock` prints nothing, including uncommitted edits.
- Existing test files are unchanged — from the product root, `git diff "$(git merge-base main HEAD)" -- tests ':!tests/unit/test_unreadable_message.py' ':!tests/integration/test_unreadable_path.py' ':!tests/integration/test_unreadable_start.py'` prints nothing. This includes the browser's `test_the_browser_opens_the_unreadable_page_without_controls` (CP-771; design T12).
- No other product path changes — from the product root, `git diff --name-only "$(git merge-base main HEAD)" -- . ':!main.py' ':!web/pages.py' ':!tests/unit/test_unreadable_message.py' ':!tests/integration/test_unreadable_path.py' ':!tests/integration/test_unreadable_start.py'` prints nothing. Inspect `git ls-files --others --exclude-standard` there too: only those three declared new tests may be untracked before their landing.
- Existing functions in the two allowed production files retain their contracts — read `git diff "$(git merge-base main HEAD)" -- main.py web/pages.py` from the product root. Only unreadable display-field handling, its private page-local support and directly relevant docstrings change; the ready formatter and line, original-location plumbing, public signatures, common HTML escaping, other messages and failed-action reporting retain their meaning (CP-763–CP-764; design §§ 2–3).

#### Implement

Verified by review — no test.

#### Verification gate

Run each product-root review command above and the exact project-card test command from the change worktree root:

```sh
uv run --locked --project products/tracker17 pytest products/tracker17/tests/ && uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/
```

Pass: every review criterion holds, with a verdict per deliverable in Developer Review Notes, and both suite invocations exit 0 with no new failures. These merge-base comparisons end with this change and never enter the lasting suite.
