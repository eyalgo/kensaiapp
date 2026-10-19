# Code integrity report — 2026-10-07_create-a-project-that-stays

Integrity: pass

**Date:** 2026-10-07 · **Reviewer:** Senior Engineer (`development-code-integrity`) · **Mode:** workflow

## Deferrals

**None.** The newest marker, `3c5569254` (`developer: 2026-10-07_create-a-project-that-stays —
implementation complete`), carries no `Deferred:` line and reads `Suite: green`. The stray deferral
label on the earlier pause `deba0675d` is superseded by that marker, as its own review notes say.

## What was reviewed

Every product file the branch adds or changes under `products/tracker17/`, from `83563a643` to
`3c5569254`: `domain/` (5 modules), `application/` (3), `persistence/` (2), `web/` (4 modules and
`style.css`), `main.py`, `pyproject.toml`, `.gitignore`, `tests/requirements.txt`, `tests/conftest.py`,
`tests/timed_run.py`, and the 18 test modules under `tests/unit/`, `tests/integration/`, `tests/e2e/` and
`tests/architecture/`.

## The intent it was checked against

`tl_instruction.md` (Tasks 1–18, their *Behaviours to verify* and the TL Review Notes), `change_spec.md`
(CP-1 to CP-29), `change_design.md` (§ 3 sub-jobs, § 4 hints, Architect Review Notes) and
`change_text.md` (every published string), all in this folder. Also `docs/SDD.md` § 3 and § 4 SD-1 to
SD-6, `docs/nfdr.md` QC-9 and QC-61, and `docs/adr/0004-whole-state-saved-atomically-on-every-change.md`.
`docs/fdr.md` was not needed for any finding.

Every string the pages and the console write matches `change_text.md` word for word (checked against
`web/pages.py`, `web/routes.py:_report_failure` and `main.py:start`).

## Tests added or fixed

All are in commit `8c7e4a659` (red).

- **Added** `test_routes.py::test_a_project_identity_too_long_to_read_as_a_number_gets_404_with_an_empty_body`.
  TL Task 9 locks this: "an identity no project holds" gets 404 with an empty body. The test uses a
  5000-digit identity.
- **Added** `test_listener.py::test_a_project_address_too_long_to_read_as_a_number_gets_404_and_writes_nothing`.
  It sends the same address over a real socket and checks OB-1 (a request writes nothing to the console).
- **Added** `test_routes.py::test_a_percent_encoded_value_that_is_not_utf_8_answers_400_with_an_empty_body`,
  with three cases: `%FF`, a cut sequence `%C3`, and an encoded surrogate. The intent is `change_design.md`
  § 4, "Parse … as strict UTF-8. Answer an undecodable body with 400 and an empty body", and
  `docs/nfdr.md:87-88`, where `web` "changes a typed value in no other way".
- **Fixed** `test_routes.py::test_a_failed_save_names_the_action_and_error_on_stderr_and_shows_the_failure_page`.
  Its restart was built from a `RecordingSaver` the site never used, so "a restart does not list the
  project" passed whatever the code did. Now one project is saved first, the second create fails, and the
  restart is built from the last state the saver actually kept: it lists `Beta` and not `Alpha`. This test
  is green against the developer's code. The unused `FailingSaver` class was removed.

## The finding

Two bugs were found and fixed in `web/routes.py`. The fix is in the green commit.

1. **An address of more than 4300 digits under `/projects/` crashed the request.** `int()` raised
   `ValueError` out of `Site.handle`. Over a socket the client got no answer at all, and the console got a
   `socketserver` traceback ("Exception occurred during processing of request…"). That breaks the TL
   Task 9 404 lock, OB-1, and CP-23's ban on Python error text. Fix: `_project_named_by` reads the
   identity and returns `None` when `int()` raises `ValueError`. The address then gets the same 404 with an
   empty body as any identity no project holds.
2. **A form value whose bytes are not UTF-8 was saved with U+FFFD in place of those bytes.** The raw body
   was decoded strictly, but `parse_qs` percent-decoded with its default `errors="replace"`. A browser's
   form body is ASCII, so the strict raw decode never fires on real input. Fix: `parse_qs(…,
   encoding="utf-8", errors="strict")`. Such a body now gets 400 with an empty body and nothing is saved.

No misplacement was found (§ Placement below).

**Suites after the fix:** `pytest tests/` gives 184 passed, exit 0. `.venv/bin/python -m pytest tests/e2e/`
gives 9 passed, exit 0. `python3 tests/timed_run.py` exits 0. `python3 -m compileall -q` exits 0. Ruff
`format --check` passes, and `check --select E,F,W,I` passes.

## Calls made

1. **Does "strict UTF-8" cover the percent-decoded values, or only the raw body bytes?**
   - Readings weighed: (a) raw bytes only, which is what the code did; (b) the decoded form values.
   - Taken: (b). Reading (a) makes the design's 400 unreachable for anything a browser sends, and
     QC-9 says `web` changes a typed value in no other way than line breaks. A replacement character is
     exactly such a change.
   - Whose document: the Architect's (`change_design.md` § 4, D — form values).
   - If reversed: drop `encoding=` and `errors="strict"` from the `parse_qs` call. The three-case test
     then expects a 303 and U+FFFD in the saved value.
2. **What does a project address too long to read as a number answer?**
   - Taken: 404 with an empty body. The TL's lock puts "an identity no project holds" at 404, and no
     project can hold an identity Python will not read.
   - Whose document: the Tech Lead's (`tl_instruction.md` Task 9, *Behaviour locked*).
   - If reversed: whatever answer replaces it must still write nothing to the console (OB-1) and no
     Python text to the page (CP-23).
3. **A failure in `pytest tests/e2e/` that could not be reproduced.**
   - What happened: the first run of this review failed
     `test_a_hand_built_201_character_name_gets_the_reason_and_none_of_the_text`. 107 later full runs before the fix
     passed (7, then 25, 15 under twelve busy CPU loops, and 60 more), and so did the 1 run after it. The failure's traceback was not captured.
   - Readings weighed: (a) treat it as today's red and change the harness; (b) record it and pass.
   - Taken: (b). The one cause I suspected was a click-then-`wait_for_load_state()` race in
     `tests/e2e/test_first_project.py:create`. Playwright 1.63's own docstrings contradict it: `click`
     says "Actions that initiate navigations are waiting for these navigations to happen and for pages to
     start loading", and `wait_for_load_state` gives the harness's exact pattern as its usage example.
     Changing a test on a guess would be inventing a fix. I don't know the cause.
   - The check that would find it: run the e2e suite in a loop with Playwright tracing on (`context.tracing`),
     keeping the trace and the pytest output of the first failing run.
   - Whose document: the Tech Lead's (`tl_instruction.md` Task 12, the harness).
   - If reversed: the change waits on that investigation.

## Placement

Walked against `docs/SDD.md` § 3. The parts table lives at the product root, so `Lives in` is empty on
every row.

| Logic | Owning part | Where it is |
|---|---|---|
| Text maximums and the length check | `domain` | `domain/text.py`, already there |
| Refusal types and `TextField` | `domain` | `domain/refusals.py`, already there |
| `Project`, create / list / find, the value checks | `domain` | `domain/projects.py`, already there |
| `TrackerState`, `empty_state`, `restore_state` | `domain` | `domain/state.py`, already there |
| `Saver` / `Clock` contracts, `Tracker` (rule, save, then current) | `application` | `application/`, already there |
| Location, file format, shape and type checks, read, atomic save | `persistence` | `persistence/saved_data.py`, already there |
| Request check, routes, form reading, line-break normalization, redirects, failure report | `web` | `web/routes.py`, already there |
| Page building and escaping, stylesheet | `web` | `web/pages.py`, `web/style.css`, already there |
| Listener | `web` | `web/listener.py`, already there |
| Address, real clock, wiring, start messages, unreadable exit | `main` | `main.py`, already there |
| This review's `_project_named_by` (address → identity) | `web` (the addresses of pages) | `web/routes.py` |

The RT-6 lock in `Site` is the one placement the table could not settle alone. `change_design.md`
records it under *Logic the parts table alone could not place*, and it sits where the design put it.
Nothing was moved, so there is no placement commit.

## Language resolution

- **Language:** Python, declared in `project.md` `Languages:` (step 1 of the chain).
- **Packet:** `languages/python/README.md` v1.2.1. Read: `conventions.md` v1.2.7, `quality_gates.md`
  v1.0.2, `errors_logging.md` v1.1.3 (§ Catching), and `testing_python.md` v2.2.0.
- **This review's code meets the packet:**
  - "Catch the narrowest type that can actually arrive" (`errors_logging.md` § Catching): only
    `ValueError` is caught.
  - A leading underscore marks module-internal (`_project_named_by`).
  - A `#` block above the construct says why (`conventions.md` § Comments and docstrings, form 2).
- **The developer's three divergences stand under `languages/README.md` § Precedence**, where the
  product's decision files outrank the packet. The three are: `typing.Protocol` ports (NFDR QC-3,
  ADR-0004/0005), no `__version__` in product modules, and the tests laid out by layer
  (`docs/nfdr.md` § 9).
- **Gates** (`quality_gates.md`): Compile and Suite both pass (§ The finding).
- **Not gates here:** no product record names Ruff or mypy as one (grep over `docs/nfdr.md`,
  `docs/SDD.md` and `docs/adr/` returned nothing). Two results are recorded and not acted on:
  - `.venv/bin/mypy` reports 3 errors, the same before and after this review. Two are `str-bytes-safe`
    on `server_address` (`main.py:50`, `web/listener.py:60`) and one is `attr-defined` on
    `handler.site` (`web/listener.py:60`).
  - `ruff check` with Ruff 0.16.10's default rules reports 8 style findings, none of them behavioural.

## Left as found

- `README.md` § Status still says no code exists. The developer flagged it as owed outside this change
  (`tl_instruction.md` § Corrections owed). It is the setup instructions' owner's, and not this review's
  to change.
