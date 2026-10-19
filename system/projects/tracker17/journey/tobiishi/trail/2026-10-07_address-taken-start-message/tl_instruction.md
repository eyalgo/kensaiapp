# Tech Lead instruction — address-taken-start-message: one plain message when something else holds the tracker's address

**Product root:** products/tracker17 — every path below is relative to it.
**Category:** feature
**Behaviour:** changing
**Scope:** `web` raises a typed `AddressTaken` when the bind fails because the address is in use; `main.start` answers it with one plain line on standard error and returns 1. Realizes CP-39 to CP-46 of `change_spec.md`.

---

## Project layout

```
products/tracker17/
  web/
    __init__.py              ← modified (re-export AddressTaken)
    listener.py              ← modified (AddressTaken, listen, module docstring)
  main.py                    ← modified (start)
  tests/
    integration/
      test_listener.py       ← modified (three new tests, plus the cause/type checks)
      test_start.py          ← modified (three new tests)
    e2e/
      test_start_command.py  ← new
```

No new directory and no `__init__.py` to create. `domain/`, `application/`, `persistence/` and `errors.py` are unchanged.

`docs/SDD.md` § 3 parts table applies: `web` owns listening and telling "the address is taken" from other bind failures; `main` owns writing the start messages.

## TL Review Notes

Decisions that diverged from `change_design.md` / `change_spec.md` (each with its reason):

- **Input missing — the message's words:** `change_design.md` §3 and §5 say the line comes "from `change_text.md`". No `change_text.md` exists in this change's folder. The line is CP-40's, verbatim, with `{host}:{port}` taken from the `address` argument. Every test below asserts that exact text, so a wrong word fails a test.
- **Behaviour added (Task 1):** `test_address_taken_is_not_an_oserror` and `test_address_taken_carries_the_original_error_as_its_cause` — implied by §4's hint (derive from `AppError` alone; raise from the original error) but absent from §5.
- **Behaviour added (Task 2):** `test_a_start_on_another_port_names_that_port` — implied by §3's "address the line names is the address `start` was given" and by `tests/unit/test_address.py:47-50`, absent from §5 as its own test.
- **Behaviour added (Task 2):** `test_a_start_with_a_held_address_prints_no_ready_message` is covered by the exact-stdout-empty assertion already in the CP-39 test; no separate test added.
- **Hint carried and sharpened:** §4's two hints are carried unchanged in substance; the M hint is stated as a property of the line (no second address literal in `main.py`), not as code.
- **Sub-jobs kept as tasks W→Task 1, M→Task 2:** §3's build sequence agrees with `docs/nfdr.md` QC-16 and QC-17 (`web` imports `errors`; `main` imports `web`). Task 2 uses `web.AddressTaken`, so it depends on Task 1.
- **Gate command:** the card's `Test command:` was run once from the worktree root and collected 198 tests, all passing. The real end-to-end suite is a separate run, `pytest products/tracker17/tests/e2e/`, because `tests/conftest.py` keeps `tests/e2e/` out of the default run. Both gates are named in Task 2.

## Corrections owed while there

- `web/listener.py:5` — the module docstring says "A bind error propagates: the signal that the address is taken is the next change unit's." → rewrite the last sentence to say `listen` raises `AddressTaken` when the address is in use and lets every other bind failure propagate. Rides Task 1 (that task already opens this file).
- `main.py` `start` docstring — "Returns 1, having written one message and changed nothing, when the saved data cannot be read." → also say it returns 1 with one message when the address is taken. Rides Task 2 (that task already opens this file).

### Task 1: The address-taken signal (`web/listener.py`, `web/__init__.py`)

**Dependencies:** None

**What to build:** `web` turns the one bind failure "address in use" into a typed signal. Add `AddressTaken`, a subclass of `errors.AppError` only (not also of `OSError`), carrying no operator wording. `listen(address, tracker)` raises it exactly when building the `Listener` fails with an `OSError` whose error number is the operating system's "address in use"; every other `OSError` propagates unchanged. `listen`'s signature and its return on success are unchanged. `web/__init__.py` imports and lists `AddressTaken` in `__all__`. `web` writes nothing to the console on this path, and the `Listener` keeps `ThreadingHTTPServer`'s socket options as they are (no port reuse switched on).

#### Behaviours to verify (developer adds tests to `tests/integration/test_listener.py`; its docstring names SRS FR-3, CP-39 to CP-46 and QC-58)

A **holder** is a TCP socket the test binds to `127.0.0.1` and puts into listening mode; it answers one connection with a known byte string.

- `test_listen_raises_address_taken_when_a_holder_has_the_address` — parametrized twice, holder without address reuse and holder with `SO_REUSEADDR` on; `listen(("127.0.0.1", P), tracker)` raises `AddressTaken`, and the holder still answers a connection afterwards (CP-39, CP-42).
- `test_listen_leaves_another_cause_unchanged` — `listen(("192.0.2.1", 0), tracker)` raises an `OSError` that is not an `AddressTaken` (CP-42, Gap 5); `192.0.2.1` is a documentation address no machine owns.
- `test_listen_takes_the_address_a_zero_address_holder_leaves_free` — with a holder on `0.0.0.0:P`, first probe-bind `127.0.0.1:P` with `SO_REUSEADDR` and release it; then `listen(("127.0.0.1", P), tracker)` returns a listener (closed by the test) when the probe bound, and raises `AddressTaken` when it did not. The expectation comes from the probe, never from the platform name (CP-42).
- `test_address_taken_is_not_an_oserror` — `AddressTaken` derives from `AppError` and is not an `OSError`, so no caller's `except OSError` catches it by accident.
- `test_address_taken_carries_the_original_error_as_its_cause` — the raised `AddressTaken`'s `__cause__` is the original `OSError`.

#### Implement

Infer from failing tests.

# Hint: Decide "address in use" by comparing the caught `OSError`'s `errno` with `errno.EADDRINUSE`, never a number or the message text, because the number differs between macOS and Linux. Raise `AddressTaken` from the original error so the cause stays on the chain. `socketserver` already closes the socket when the bind fails inside the server's constructor. Use nothing newer than Python 3.11 (QC-60).

#### Verification gate

Run `pytest products/tracker17/tests/` from the worktree root.

Pass criteria: this task's tests pass; no new failures elsewhere (the suite stays green after this task alone, as no existing test holds an address).

### Task 2: The message and the failing status (`main.py`)

**Dependencies:** Task 1 (`web.AddressTaken`)

**What to build:** In `start`, guard the call `listen(address, tracker)` for `AddressTaken`. On it, print one line to standard error and return 1. Nothing else in `start` changes: the saved data is still read first, so unreadable data wins (CP-43), and the ready line is printed only after `listen` returns. The line is CP-40's, one paragraph on one line, standard output untouched:

`The tracker didn't start, because something else is already using the address 127.0.0.1:8017. Stop that program, then start the tracker again.`

The address part is `<host>:<port>` written from the `address` argument. Do not write the address as a literal: `tests/unit/test_address.py:47-50` requires `127.0.0.1` and `8017` to appear exactly once each in `main.py`.

#### Behaviours to verify (developer adds tests to `tests/integration/test_start.py` and to the new `tests/e2e/test_start_command.py`; docstrings name SRS FR-3, CP-39 to CP-46 and QC-58)

- `test_a_start_with_a_held_address_prints_the_one_line_and_changes_nothing` — holder on `127.0.0.1:P`, `main.start(("127.0.0.1", P), tmp_path / "data")` returns non-zero; `capsys` shows empty standard output and exactly one line on standard error, which is the CP-40 line with `127.0.0.1:P` as its address and holds no `Traceback`; `tmp_path / "data"` does not exist afterwards; the holder still answers a connection (CP-39, CP-40, CP-41).
- `test_a_start_on_another_port_names_that_port` — the line names the port the start was given, not 8017 (CP-40, Gap 3).
- `test_a_held_address_leaves_existing_saved_data_untouched` — a location holding saved data with project `Alpha`, written through `SavedData.save` before the start; with a holder on the address, `start` returns non-zero, the file's bytes and the directory's listing (`_listing`) are unchanged, and standard error is the one line (CP-41).
- `test_unreadable_saved_data_wins_over_a_held_address` — `UNREADABLE` bytes saved and a holder on the address; `start` returns non-zero, standard error is one line, the unreadable-data message naming the location, and it does not hold the address message; standard output is empty and the bytes are unchanged (CP-43).
- `test_the_real_start_command_with_the_address_held` (new `tests/e2e/test_start_command.py`) — open a holder on `127.0.0.1:8017` and record `data/` at the product root (whether it exists, its listing, every file's bytes). Run `[sys.executable, "main.py"]` with the product root as its working directory and a timeout. The process ends by itself with a non-zero status; standard output is empty; standard error is exactly the CP-40 line with `127.0.0.1:8017` followed by a newline; `data/` is as recorded; a connection to `127.0.0.1:8017` then reaches the holder. When the holder cannot bind `127.0.0.1:8017`, the test fails and names the address. It does not skip (CP-39, CP-40, CP-41, CP-46).

Covered by existing tests, unchanged: CP-44 by `test_the_first_output_is_the_ready_message_address_before_location` in `tests/e2e/test_first_project.py`; the sealed CP-7 unreadable-start tests in `tests/integration/test_start.py`; CP-45 by `tests/architecture/test_imports.py`, `test_shapes.py` and `test_reach.py`.

#### Held by review

- CP-45 "the message's words are ones `docs/CONTENT.md` holds" — no test reads CONTENT. The observable is the diff: the line in `main.py` equals CP-40's text, whose source is `docs/CONTENT.md:250` with the address replaced.

#### Implement

Infer from failing tests.

# Hint: `tests/unit/test_address.py:47-50` forbids a second address literal in `main.py`, so build the line from the `address` argument.

#### Verification gate

Run `pytest products/tracker17/tests/` and `pytest products/tracker17/tests/e2e/` from the worktree root.

Pass criteria: this task's tests pass; both commands exit 0 (CP-46); the CP-7 tests in `tests/integration/test_start.py` pass unchanged.
