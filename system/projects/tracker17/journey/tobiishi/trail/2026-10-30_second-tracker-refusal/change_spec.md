# Change Spec — a second tracker on the same saved data is refused

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing
**Request:** Make a second tracker started on the saved-data location a running tracker already uses refuse to start. It prints one plain message saying it is refused because another tracker is using that location, and exits without serving, while the first tracker carries on untouched and the saved data's bytes stay as they were. A tracker started after the first one was killed (a kill it cannot handle) on the same location starts and serves. The refusal is the one lock ADR-0009 names and SDD `SM-5` places between `main` and `persistence`, on the Unix path only. Two tests land under `products/tracker17/tests/`: one starts a tracker, starts a second on the same location and asserts the message, the exit without serving, that the first still answers a request, and that the data's bytes are unchanged; the other kills the first tracker and asserts a tracker started on that location serves (both halves of SRS AC-16). The README gains a passage saying a second start on a location in use is refused with a message while the first carries on, and that a start after a kill succeeds; it must contain the words "another tracker". Sizing: one capability, one merge. The acceptance boundary is SRS AC-16 / NFR-3 (one running tracker per location), taken from the station's five reached-when items. The lock, the message, the kill-recovery and the README sentence are one behaviour and its proof, so they stay together. The tests must fail on the tree as it was before this change and pass after. What must not be weakened: the lock is Unix only, with no Windows path, no operating-system check and no message for one (ADR-0009). A start on unreadable saved data keeps today's exit-1 stop; changing it is the next station's. Saved data is never written, replaced or deleted by the refusal (SDD SD-4). The address-taken behaviour, the screens and the data model do not change. The suite is not narrowed: both `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and the same on `products/tracker17/tests/e2e/` exit 0. Not here: the unreadable-data page, its console message, the set-aside restart, the one-test-per-DR-6-break work and the README's unreadable-data description (the seed's item 2, `unreadable-data-page`).
**Language resolution:** Python — step 1, `project.md` `Languages:` — `core/doctrine/engineering/languages/python/README.md`

---

## Change Summary

A start on a saved-data location a running tracker is using now prints one fixed message and exits 1, leaving the first tracker and the saved data as they were. A start after that tracker was killed serves. Sizing: one capability, with SRS AC-16 / NFR-3 as its acceptance boundary. The refusal, the recovery, their tests and the README passage are that capability and its proof.

---

## Rules

### The refusal

- **CP-693:** A start on a location another running tracker is using does not serve. It writes nothing to standard output and exactly this one line to standard error, then exits with status 1 (FDR R-5, CONTENT.md § Terminal messages, NFDR QC-58): `The tracker didn't start, because another tracker is already running on the same saved data. Stop that one first, then start this one.` It prints no ready line and takes no address.
- **CP-694:** The refused start changes nothing. The first tracker keeps answering requests. The saved file's bytes and the location's listing are as they were before the refused start (SRS AC-16, NFDR QC-58, SDD SD-4).
- **CP-695:** A location is in use for the whole time a tracker is running on it: before that tracker's first save, when the location holds no saved file, and after any number of saves.
- **CP-696:** Where more than one refusal applies, the start shows one line, and the first of these that applies decides it: another tracker on the location, then saved data that cannot be read, then the address taken. So the real second `python3 main.py`, which meets both a location in use and its own address taken, prints the CP-693 line and not the address line.
- **CP-697:** Two starts are on the same location when they name the same directory, however the path is written. A start on a different directory is never given the CP-693 line, whatever other tracker is running.
- **CP-698:** Of two starts made at the same moment on one location, at most one reaches its ready line. Any other gets the CP-693 line.

### The recovery

- **CP-699:** A tracker stopped by a kill it cannot handle does not stop the next start on that location (FDR R-6). That start prints its ready line and serves the saved data as the killed tracker left it, with no step by the operator and no message about the earlier tracker. The next start also serves after a tracker stopped with Ctrl-C.

### What stays as it is

- **CP-700:** A start on unreadable saved data, with no other tracker on the location, keeps today's behaviour: exit status 1, today's one line on standard error, and the file's bytes and the location's listing unchanged. This includes a location that is a file and a location the tracker has no permission to read.
- **CP-701:** A start whose address is taken, with no other tracker on the location, keeps today's behaviour: exit status 1, today's one address line on standard error, and the location's listing unchanged. A location that did not exist before that start does not exist after it. The same holds for a bind that fails for another reason, which still fails as it does today and is never told the address is taken.
- **CP-702:** A start where it cannot be determined whether another tracker is on the location never prints the CP-693 line, and does what it does today. Which causes fall in this class is not fixed here. The domain is every cause other than a tracker actually running. Examples are a location that does not exist and cannot be created, or a file system that offers no lock.
- **CP-703:** A running tracker that has saved nothing has no saved file. Its location may exist as an empty directory from the start onward, and may remain as an empty directory after that tracker stops. A start on an empty location reads it as no saved data yet. `tests/e2e/test_first_project.py::test_not_found_requests_write_nothing` changes at its `assert not tracker.location.exists()` line only: that line asserts instead that no saved file exists, and the test keeps every other assertion. No other existing test is named as changing.

### The proof

- **CP-704:** A test at layer 2 (NFDR QC-52, QC-58), which `pytest tests/` runs, starts a real tracker process, starts a second real process on the same location and a different port, and asserts: the CP-693 line and nothing else on both streams, exit status 1 with no ready line, that the first tracker then answers a request, and that the saved data's bytes are unchanged. It fails rather than hangs on a second start that serves.
- **CP-705:** A second test at layer 2 (NFDR QC-52) starts a real tracker process, shows a second start refused, kills the first with `SIGKILL`, then starts a tracker on that location and asserts it prints its ready line and answers a request. The shown refusal is part of the test, so it fails on the tree before this change, where the kill-and-restart half already passes.
- **CP-706:** The refusal is the one lock ADR-0009 names, with one path, on macOS and Linux only, and the primitive left to `persistence` as ADR-0009 leaves it. `persistence` owns the lock (NFDR QC-22) and gives `main` the signal "another tracker already running" across SDD `SM-5`. `main.py` writes the message (NFDR QC-24, QC-45). Only `persistence` writes or deletes on disk, and only inside the location (NFDR QC-42). The lock uses only the standard library (NFDR QC-19), any new exception derives from the one base error (NFDR QC-4), and nothing checks an operating system or carries a message for one (NFDR QC-61, ADR-0009).
- **CP-707:** Each new test module names the requirements or acceptance criteria it checks (NFDR QC-11). No test patches a name inside a part (SDD TS-2). The code passes Ruff's format check, Ruff's lint and mypy (NFDR QC-62).
- **CP-708:** `products/tracker17/README.md` gains a passage saying that a second start on a location in use is refused with a message while the first tracker carries on, and that a start after a kill succeeds (SDD § 6 `protect-saved-data`). `grep -c -i -F "another tracker" products/tracker17/README.md` prints at least 1.
- **CP-709:** `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/` both exit 0, with the suite narrowed by nothing beyond the one assertion CP-703 names.

---

## Examples

| Scenario | Expected behavior | Rules |
|---|---|---|
| First tracker running on a location with saved data; second start on it, another port | Standard error holds the CP-693 line, standard output is empty, exit 1. The first tracker answers a request, and the file's bytes and the listing are unchanged | CP-693, CP-694, CP-704 |
| First tracker running on a location that holds no saved file; second start on it | The CP-693 line, exit 1 | CP-695 |
| First tracker has saved once; second start on the location | The CP-693 line, exit 1, bytes unchanged | CP-695 |
| A second real `python3 main.py` while the first runs | The CP-693 line, not the address line | CP-696 |
| Another tracker on the location, and its saved file damaged by hand | The CP-693 line, not the unreadable line | CP-696 |
| The same directory named by a relative and an absolute path, or through a symbolic link | The second start gets the CP-693 line | CP-697 |
| A running tracker on one directory; a start on another directory, another port | It starts and serves | CP-697 |
| A running tracker on one directory; a start on another directory, same port | The address line | CP-697, CP-701 |
| Two starts at the same moment on one location | One reaches its ready line, the other gets the CP-693 line | CP-698 |
| First tracker killed with `SIGKILL`; start on the location | Ready line, and it serves the saved data as left | CP-699, CP-705 |
| First tracker killed before any save; start on the location | Ready line, and it serves with no projects | CP-699, CP-703 |
| First tracker stopped with Ctrl-C; start on the location | Ready line, and it serves | CP-699 |
| Unreadable saved file, no other tracker; start | Today's unreadable line, exit 1, nothing changed | CP-700 |
| The location is a file, or has no read permission; start | Today's unreadable line, exit 1 | CP-700 |
| Address held by another program, location absent, no other tracker; start | Today's address line, exit 1, location still absent | CP-701 |
| Location absent and its parent read-only; start | It serves, as today, and the CP-693 line never appears | CP-702 |
| A running tracker has saved nothing; not-found pages are opened | No saved file exists. The location may be an empty directory | CP-703 |
| The tree before this change, running both new tests | Both fail, and neither hangs | CP-704, CP-705 |
| The lock's module, `main.py` and the new tests under the architecture walks and CP-707's three commands | All pass | CP-706, CP-707 |
| `grep -c -i -F "another tracker"` on the README | Prints 0 before this change and at least 1 after | CP-708 |
| Both suite commands after this change | Each exits 0 | CP-709 |

---

## Verified Claims

Base: `00e82c6ba`. The product worktree is the base. The probe below ran in a disposable clone at that commit, with a throwaway lock on the location directory added. It is evidence that the rules can be met, not a design.

| Claim | Verified by | What came back |
|---|---|---|
| CP-700: an unreadable start keeps today's line, status and bytes | `tests/integration/test_start.py::test_an_unreadable_start_writes_exactly_the_one_line_with_the_closing_sentence`, `::test_an_unreadable_start_changes_nothing_in_the_location`, run by id | `00e82c6ba`: passed |
| CP-700: a location that is a file, and one with no permissions, get the unreadable line | `main.start` in a real process on each, at the base and in the probe | `00e82c6ba`: exit 1 with the unreadable line for both. Probe: the same |
| CP-701: the address line and the absent location stay | `tests/integration/test_start.py::test_a_start_with_a_held_address_prints_the_one_line_and_changes_nothing`, `::test_a_held_address_leaves_existing_saved_data_untouched`, `tests/e2e/test_start_command.py::test_the_real_start_command_with_the_address_held`, run by id | `00e82c6ba`: passed |
| CP-701: another bind failure is not told the address is taken | `tests/integration/test_start.py::test_a_start_refused_the_address_for_another_reason_is_not_told_it_is_taken`, run by id | `00e82c6ba`: passed |
| CP-696: unreadable data wins over a taken address | `tests/integration/test_start.py::test_unreadable_saved_data_wins_over_a_held_address`, run by id | `00e82c6ba`: passed |
| CP-702: an absent location with a read-only parent serves today | `main.start` in a real process, parent mode 555, at the base and in the probe | `00e82c6ba`: ready line, serving. Probe: the same |
| The defect: nothing stops a second start on a location in use today (`products/tracker17/main.py:102-124` holds no such check) | `main.start` in two real processes on one location, on another port and on the same port | `00e82c6ba`: another port, the second serves. Same port, exit 1 with the address line |
| CP-705: a kill-and-restart alone already passes at the base | `main.start` in a real process, `SIGKILL`, then a new start on the location | `00e82c6ba`: ready line. So a test holding only that half could not fail at the base |
| CP-693 to CP-696, CP-699 can be met together | The probe, with real processes: second start before a save and after a real save, on another port and the same port, then `SIGKILL` and restart, then Ctrl-C and restart | The CP-693 line and exit 1 in all four refused cases, bytes unchanged, first tracker answered 200. Ready line after both restarts |
| CP-703: exactly one existing test stands against a location that exists from the start | `uv run --locked pytest tests/` and `uv run --locked pytest tests/e2e/` in the probe | `tests/`: 2698 passed. `tests/e2e/`: 120 passed, 1 failed, `test_not_found_requests_write_nothing` at line 231 |
| CP-703: that test passes at the base | `tests/e2e/test_first_project.py::test_not_found_requests_write_nothing`, run by id | `00e82c6ba`: passed |
| CP-703: the probe holds under the walks of CP-706 | `tests/architecture/`, inside the `tests/` run above | Passed in the probe |
| CP-708: the README does not hold the words today | `grep -c -i -F "another tracker" products/tracker17/README.md` | `00e82c6ba`: 0 |
| CP-693: the fixed line | `products/tracker17/docs/CONTENT.md:265`, `docs/UXD.md:363` | The line is stated in CONTENT.md. No language-level fact is rendered, so no packet line bears on it |

---

## Out of Scope

- "the unreadable-data page, its console message, the set-aside restart, the one-test-per-DR-6-break work and the README's unreadable-data description": SRS FR-8 and SDD § 6 `protect-saved-data` state them, and the product still stops at `products/tracker17/main.py:104-113`. Parked in `deferred_decisions.md` as a record gap.
- Windows, or any other system's lock path (ADR-0009).
- Moving or setting aside the location while a tracker runs. The README already says to stop the tracker first.
- A control inside the tracker that clears or overrides the lock, or stops the other tracker.
- The address-taken line's wording, every screen and the data model.
- The README's `## Status` section and `docs/what_left.md`, which this change does not edit.

---

## Locked Answers (the divergence record — self-review 2026-10-30)

- **Gap 1 — the message's words (b):** CP-693 pins CONTENT.md's own line. The request gives the meaning, "another tracker is using that location", and no words. CONTENT.md's formula says a message names the location "where saved data is the reason", while its own line for this case names none and UXD UX-S2 names a location only for data that cannot be read. The line stands as written: the reason here is the other tracker, not the data.
- **Gap 2 — exit status and stream (b):** status 1 on standard error. The request says "exits without serving". Every other refused start reports this way, so an operator or a script sees one shape.
- **Gap 3 — which refusal wins (b):** another tracker, then unreadable data, then the address. The request does not order them. Without this, the real second `python3 main.py` would keep today's address line and the operator would never see the refusal. Another tracker comes before unreadable data because that line sends the operator to set the data aside, which is the wrong step while a tracker is running on it. The order between unreadable data and the address stays as it is today.
- **Gap 4 — in use before the first save (b):** CP-695. The request says a running tracker "already uses" the location, and a tracker that has saved nothing is still one the operator would overwrite on its first save.
- **Gap 5 — when it cannot be determined (b):** CP-702 keeps today's outcome and never claims another tracker. SRS NFR-3 refuses only "while another tracker is actually running", so a false refusal would tell the operator something untrue. It is reversible: a later change can make such a start stop. A location that cannot be created also cannot be saved to, so two trackers there cannot overwrite each other's data.
- **Gap 6 — a test the request did not name (f):** CP-703 names `test_not_found_requests_write_nothing`, which keeps asserting that no saved data is created (its docstring: "no saved data is created") and that its bytes stay the same. A tracker must be detectable before its first save (Gap 4), NFDR QC-42 limits what a start may leave on disk to inside the location, and a location that exists empty is the state that test's stricter line forbids. An empty directory is not saved data. The request's "the suite is not narrowed" stands on this one line, which is logged here so it can be reviewed.
- **Gap 7 — the recovery test must fail first (b):** CP-705 includes the shown refusal. The request asks that both tests "fail on the tree as it was before this change", and a kill followed by a restart passes there, because nothing stops a start today. The refusal inside the test is what makes it fail at the base and pass after.
- **Gap 8 — checks the records bind (e):** CP-706 and CP-707 state NFDR QC-4, QC-11, QC-19, QC-22, QC-24, QC-42, QC-45, QC-61, QC-62 and SDD TS-2, which the request does not name. They bind code this change adds. CP-704 and CP-705 place the tests at layer 2 because NFDR QC-52 and QC-58 say so, where the request says only "under `products/tracker17/tests/`".
