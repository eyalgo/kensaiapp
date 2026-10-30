# Code integrity report

Integrity: pass
Environment: owners-mac — no CI

**Change:** `tracker17 · tobiishi · 2026-10-30_unreadable-data-page` · **Date:** 2026-10-30 · **Mode:** workflow

## Deferrals

None. The closing marker, `<a commit not in the public history>`, the newest `— implementation complete` commit on the branch, carries no `Deferred:` line and no `Failing:` line.

## What was reviewed

The branch's code commits `556105475`..`d6f117700` under `products/tracker17/`:

- `main.py`; `web/__init__.py`, `web/pages.py`, `web/routes.py`, `web/listener.py`.
- `README.md`: the two CP-734 passages, compared string by string with `change_text.md`. All seven approved README strings are present.
- The seven test modules named in `tl_instruction.md` § Project layout.
- `persistence/saved_data.py`, which the change does not touch, because CP-710 rests on what its load reports.

## The intent it was checked against

- `tl_instruction.md`: Tasks 1 to 5, their *Behaviours to verify* and *Held by review* items.
- `change_spec.md`: CP-710 to CP-735, the Examples table, § Out of Scope and § Locked Answers.
- `change_design.md` §§ 2, 3 and 5, rows T1 to T20. `change_text.md` for every published string.
- `docs/SRS.md` DR-6 and `docs/fdr.md` R-21 to R-23, which CP-710 names as what counts as unreadable.

## Language resolution

Python, chain step 1 (`project.md`, `Languages: Python`). Read `<CORE>/doctrine/engineering/languages/python/README.md`, `conventions.md`, `quality_gates.md`, `errors_logging.md` and `environment.md`, and `<CORE>/doctrine/engineering/testing_python.md`. The code passes them, with two divergences carried under **Calls made**. Ruff format and lint, mypy and `uv lock --check` all pass after the fix.

## Placement

Walked against `docs/SDD.md` § 3. Nothing was moved, so there is no placement commit.

| Logic | Owning part | Result |
|---|---|---|
| `unreadable_data_page`, `_framed` | `web` | already there (`web/pages.py`) |
| `UnreadableSite`, `_refused_before_routing` | `web` | already there (`web/routes.py`) |
| `listen_unreadable`, `_bind`, `Answers` | `web` | already there (`web/listener.py`) |
| Choosing the mode, `_bind`, both console lines | `main` | already there (`main.py`) |
| This review's fix: what counts as unreadable at the load | `persistence` | placed there (`persistence/saved_data.py`) |

## The tests added or fixed

Red against the code as it stood, in commit `005f49a92`. All four are cases of `test_other_invalid_saved_values_serve_without_changing_data`:

- `file-nested-too-deep`: CP-710, "the wrong shape". The load raised `RecursionError`.
- `file-lone-surrogate-is-not-text`: DR-6, "cannot read all of it". The load accepted it.
- `task-instant-before-the-calendar` and `comment-instant-after-the-calendar`: CP-710. The load raised `OverflowError`.

Green when written, added because the intent had no test for them:

- `test_a_relative_location_is_shown_as_one_absolute_path`: CP-711 and CP-716, one absolute path on the console and on the page. It fails when either line is handed the location as given.
- `test_a_saved_file_without_read_permission_serves_without_touching_it`: CP-710. The existing test denied the directory only. It fails when the load stops treating that error as unreadable.
- `test_unreadable_start_stops_quietly_and_releases_its_location[close]`: T10 names the close boundary, and the test covered only the other three.
- `test_each_dr6_document_loads_once_its_break_is_repaired`: CP-728. Each DR-6 document now has a repaired twin that loads, so each case fails for the break it names.

Strengthened: the announcement and return cases of the same stop test discarded the child's reports, so they would pass if the signal was never sent. Each now asserts its delivery report.

No existing test was wrong.

## The finding

**Three kinds of damaged saved file broke CP-710, and all three are fixed.** A file nested too deep and an instant outside the calendar made the start end with a traceback instead of serving the page. A lone surrogate loaded as data, and then every page holding it dropped the connection with a traceback. `SavedData.load` now reports each as `UnreadableData`.

To find them, every value in a valid document was replaced in turn with 25 hostile values. Only `OverflowError` escaped. `RecursionError` and the lone surrogate came from separate probes.

Two docstrings this change made false were corrected: `web/__init__.py` said every value comes from the tracker, and `web/routes.py` named only `Site.handle`.

Everything else in the intent already had a correct test and passed. No misplacement was found.

## Calls made

1. **May this change edit `persistence`?**
   - Readings: the design's *Unchanged* row and the plan's "Expect no diff", or CP-710's "whatever the cause".
   - Taken: edit it, by the smallest fix. Catching these errors in `main` would make `main` decide what counts as unreadable, which `docs/SDD.md` § 3 and CP-733 give to `persistence`. The signal is the same one, and nothing else about the load changes.
   - Owner: the Tech Lead's plan and the Architect's design.
   - If reversed: these files end the start with a traceback again, and CP-710 needs narrowing.
2. **Is a lone surrogate unreadable data?**
   - Readings: valid JSON that loads, or text the tracker cannot read.
   - Taken: unreadable. No page or save can encode it, and DR-6 says the file may be damaged by hand. The tracker's own saves never write one, so no data it wrote changes reading. CP-727 stands, because such a file never served a page.
   - Owner: the CTO, for DR-6.
   - If reversed: the start serves the normal tracker, and each page holding that value drops the connection.
3. **`Answers` is a `typing.Protocol`, against `conventions.md` "A port is a plain class".** Kept. That bullet states its own scope as code no gate runs over, mypy runs over `web`, and `docs/nfdr.md` QC-3 uses Protocols for this product's contracts. Owner: the Tech Lead. If reversed: one class changes shape, with no change in behaviour.
4. **`UnreadableSite.handle` reads the stylesheet file itself, against `conventions.md` "A module is given its collaborators".** Kept. The design fixes the signature `UnreadableSite(location, own_host)`, a product's design outranks the packet, and `Site` reads the same file the same way. Owner: the Architect. If reversed: both handlers are handed the stylesheet, which changes that signature.
5. **The developer did not deliver the policy header on a request line the library cannot read.** Accepted. Sent a one-word line, the listener writes no bytes at all, so no header exists to assert, and § Out of Scope leaves such requests as they are. The test still requires the policy on the malformed requests that do get an answer. Owner: the Tech Lead.
6. **A location whose path is not UTF-8 is left as it is, and handed on.** `UnreadableSite` raises when it builds the page for one. Such a path has no faithful text to show, and the choice would reach the readable start, which CP-727 keeps. It is in `deferred_decisions.md`. Owner: the PM, through `shukuba-refine`. If ruled in scope: both start lines need one agreed way to show the path.

## Test evidence

- An earlier run of the test command exited 1 and printed `Environment: owners-mac — no CI`.
- That run, with the new tests and no fix: 4 failed, 2809 passed. The second command did not run.
- The verdict's run, with the fix: exit 0, 2813 passed, then 122 passed.

**Not tried:** a saved file that is a named pipe. The load would wait on it, before any announcement, as it does on `main`.

**Most likely to bite:** the persistence edit sits outside the plan's stated boundary. Read Call 1 first.
