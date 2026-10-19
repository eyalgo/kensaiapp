# Change Design — One plain message when something else holds the tracker's address

**Date:** 2026-10-07
**Category:** feature
**Behaviour:** changing
**Publishes text:** yes — the console message a start shows when something else is already using the tracker's address

---

## 1. Change Summary

This is the structural plan for `change_spec.md` in this folder (CP-39 to CP-46). It places the signal that the address is taken, the message that answers it, and the tests that prove both.

Today `listen` lets the bind error propagate (`web/listener.py:5`), so `python3 main.py` ends in a traceback when another program holds `127.0.0.1:8017`. After this change `web` turns that one bind failure into a typed signal. `main` catches the signal and writes one line to standard error, and the start returns 1. Every other bind failure propagates as it does today (CP-42).

Two parts change: `web` and `main`. Paths in this document are relative to the product root, `products/tracker17/`, which is what `system/projects/tracker17/project.md` names in `Product path:`.

---

## 2. Blast Radius

Every new piece of logic is placed by `docs/SDD.md` § 3's parts table:

- **Telling "the address is taken" from any other bind failure** is owned by `web`. Its `Owns` cell holds "listening on the loopback address" (`docs/SDD.md:194`), and seam `SM-6` names `web` as the owner of the contract whose outward side is "a running listener, or the signal that the address is taken" (`docs/SDD.md:217`).
- **Answering the signal with the console message and the failing status** is owned by `main`, whose `Owns` cell holds "writes the start messages to the console" (`docs/SDD.md:195`).

| Module | Status | What changes |
|---|---|---|
| `web/` | Modified | `web` part, `web/listener.py` and `web/__init__.py`. A new typed error, `AddressTaken`, derived from `errors.AppError`. `listen` raises it when the bind fails because the address is in use, and lets every other bind failure propagate unchanged. `web/__init__.py` re-exports it. The module docstring's last sentence (`web/listener.py:5`) is rewritten to say what `listen` now does. |
| `main.py` | Modified | `main` part. `start` catches `AddressTaken` around the call to `listen`, writes the one line to standard error, and returns 1. The address the line names is the address `start` was given. |
| `domain/` | Unchanged | — |
| `application/` | Unchanged | — |
| `persistence/` | Unchanged | — |
| `errors.py` | Unchanged | — |

**Transitive blast radius.** `web`'s public surface gains one name, `AddressTaken`, and `listen` keeps its signature. `main.py` is the only product module that imports `web` (`docs/nfdr.md` QC-17), and it is in the table. No import is added outside what QC-16 and QC-17 already allow: `web` imports `errors`, and `main` imports `web`.

---

## 3. Sub-jobs

### Sub-job W — `web/`, the signal that the address is taken

**Scope:** `web/listener.py` defines `AddressTaken(AppError)`. `listen` raises it when building the `Listener` fails with an `OSError` whose error number is the operating system's "address in use". Any other `OSError` propagates unchanged, so a start refused the address for another reason behaves as today (CP-42, Locked Answers Gap 5). `AddressTaken` carries no wording for the operator: `main` writes the words, and the type is the signal (SDD § 4 OB-4's by-type rule, applied to this signal). `web/__init__.py` adds `AddressTaken` to its imports and `__all__`. `web` writes nothing to the console on this path (QC-45). The `Listener` keeps `ThreadingHTTPServer`'s socket options as they are, in particular it does not switch on port reuse.

**Exposes:** `web.AddressTaken`, a subclass of `errors.AppError`, raised by `web.listen(address, tracker)` exactly when the address is in use. `listen`'s signature and its return on success are unchanged.

**Depends on:** none.

### Sub-job M — `main.py`, the message and the failing status

**Scope:** In `start`, the call `listen(address, tracker)` is guarded for `AddressTaken`. On it, `start` prints one line to standard error and returns 1. Nothing else changes in `start`: the saved data is still read first, and the ready line is still printed only after `listen` returns. The line is the content step's, from `change_text.md`, placed verbatim. The one variable part is the address, written as `<host>:<port>` from the `address` argument.

**Exposes:** nothing new. `start(address, location) -> int` returns 1 for a held address, as it already does for unreadable saved data.

**Depends on:** W (`web.AddressTaken`).

**Build sequence:**
```
W
After W: M
```

There is a green point after W: no existing test holds the address, so the suite passes with `listen` raising the new type before `main` catches it.

---

## 4. Code Strategy

| Sub-job / change | Hint |
|---|---|
| W — `web/listener.py`, the signal | Compare the caught `OSError`'s `errno` with `errno.EADDRINUSE`. Do not compare the number or the message text, because the number differs between macOS (48) and Linux (98). Raise `AddressTaken` from the original error, so the cause stays on the chain for a developer. `socketserver` already closes the socket when the bind fails inside the server's constructor. Derive from `AppError` alone, not also from `OSError`, so that no caller's `except OSError` catches the signal by accident. |
| M — `main.py`, the message | `tests/unit/test_address.py:47-50` requires `127.0.0.1` and `8017` to appear exactly once each in `main.py`. The line must therefore take the address from the `address` argument. It cannot write the address as a literal. |

---

## 5. Test Additions

Every test module touched names SRS FR-3 in its docstring, together with CP-39 to CP-46 and QC-58. The pointer test (`tests/architecture/test_trace.py`) checks that every requirement and path a docstring names exists.

A **holder** below is a TCP socket that the test binds to `127.0.0.1` and puts into listening mode. It answers one connection with a known byte string, so the test can tell afterwards that the connection reached the holder.

| Sub-job | Test file | What to add / modify |
|---|---|---|
| W | `tests/integration/test_listener.py` | New test (CP-39, CP-42): with a holder on `127.0.0.1:P`, `listen(("127.0.0.1", P), tracker)` raises `AddressTaken`. Parametrize the holder twice: once without address reuse and once with `SO_REUSEADDR` switched on (the CP-42 Examples row). Each time, the holder still answers a connection afterwards. |
| W | `tests/integration/test_listener.py` | New test (CP-42, another cause): `listen(("192.0.2.1", 0), tracker)` raises an `OSError` that is not an `AddressTaken`. `192.0.2.1` is a documentation address that no machine owns, so the bind fails with "address not available". |
| W | `tests/integration/test_listener.py` | New test (CP-42, a start that can still take the address): with a holder on `0.0.0.0:P`, first try a probe bind of `127.0.0.1:P` with `SO_REUSEADDR`, the option `Listener` sets, and release it. Then call `listen(("127.0.0.1", P), tracker)`. When the probe bound, `listen` returns a listener, which the test closes. When it did not, `listen` raises `AddressTaken`. The expected result comes from the probe, not from the platform's name. |
| M | `tests/integration/test_start.py` | New test (CP-39, CP-40, CP-41, no saved data): with a holder on `127.0.0.1:P`, `main.start(("127.0.0.1", P), tmp_path / "data")` returns non-zero. `capsys` shows nothing on standard output and exactly one line on standard error. That line is the `change_text.md` line with `127.0.0.1:P` as its address, and it holds no `Traceback`. `tmp_path / "data"` does not exist afterwards. The holder still answers a connection. |
| M | `tests/integration/test_start.py` | New test (CP-41, saved data present): a location that holds saved data with project `Alpha`. Write the file through `SavedData.save` before the start. With a holder on the address, `start` returns non-zero, the file's bytes and the directory's listing (`_listing`) are unchanged, and standard error is the one line. |
| M | `tests/integration/test_start.py` | New test (CP-43): `UNREADABLE` bytes saved and a holder on the address. `start` returns non-zero. Standard error is one line, the unreadable-data message naming the location, and it does not hold the address message. Standard output is empty and the bytes are unchanged. |
| M | `tests/e2e/test_start_command.py` (new) | New test (CP-39, CP-40, CP-41, CP-46, the real start command). The test opens a holder on `127.0.0.1:8017` and records the state of `data/` at the product root: whether it exists, its listing and every file's bytes. It runs `[sys.executable, "main.py"]` with the product root as its working directory and a timeout. The process ends by itself with a non-zero status. Standard output is empty. Standard error is exactly the `change_text.md` line with `127.0.0.1:8017`, followed by a newline. `data/` is as recorded. A connection to `127.0.0.1:8017` then reaches the holder. When the holder cannot bind `127.0.0.1:8017`, the test fails and names the address. It does not skip. |

**Covered by existing rows:**

- **CP-44, a good start's first output is the ready line:** `test_the_first_output_is_the_ready_message_address_before_location` in `tests/e2e/test_first_project.py:42`, unchanged.
- **CP-43, the sealed unreadable start without a held address:** the CP-7 tests in `tests/integration/test_start.py`, unchanged.
- **CP-45, no new part, seam or dependency, and `main` the only wiring site:** `tests/architecture/test_imports.py` (QC-13 to QC-19) and `tests/architecture/test_shapes.py` (QC-1, QC-2, and QC-4, which walks `AddressTaken` and fails if it does not derive from `AppError`), unchanged. That `web` writes nothing to the console on the new path is `tests/architecture/test_reach.py`'s QC-45 walk, unchanged. That the words are CONTENT's is the content step's job, and the diff carries it.
- **CP-46, both suites exit 0:** the two suites are run.
- **"No ready message" on a failed start (CP-39):** the rows above assert the exact standard error and an empty standard output. The ready line goes to standard output, so the rows exclude it.

**What this change stops proving.** No assertion is retired. No existing test exercises a held address. `grep -rn 'OSError\|EADDRINUSE\|Address already' tests` finds only `tests/integration/test_routes.py:195,218` and `tests/integration/test_saved_data.py:273`, which concern a failed save and a failed read, not a bind.

---

## Records this change makes false

None. I read `docs/adr/` (0001 to 0009, all Accepted), `docs/nfdr.md`, `docs/fdr.md` and `docs/SDD.md` § 3, and nothing in them goes false. Three of them describe what this change builds. `docs/SDD.md:217` (`SM-6`) names "the signal that the address is taken" as `web`'s. `docs/nfdr.md:431` (QC-58) and its row in the verification map (`:570`) expect layer-2 tests under `pytest tests/`, which the `tests/integration/test_start.py` rows supply. `docs/fdr.md:44-46` (R-4) is the rule realized. The one sentence this change makes false is in code, at `web/listener.py:5`, and Sub-job W rewrites it.

---

## Architect Review Notes

- **(b) The signal is a typed error in `web`, not a refusal type in `domain`.** The spec leaves the mechanism open. `SM-6` makes `web` the owner of the address-taken signal. Its sibling at start, unreadable saved data under `SM-5`, is the same shape: `persistence/saved_data.py:24` defines `UnreadableData(AppError)`, and `main` catches it. QC-5's one-refusal-type-per-condition rule is about `domain`'s refusals of an operator's action. This signal is not one of those.
- **(b) "Something else holds the address" is decided by the bind's error number, and only there (CP-42).** The tracker does not probe the address beforehand and does not read any other cause. A start the operating system lets bind takes the address and serves, as on macOS beside a `0.0.0.0` holder. A start refused for another cause propagates as today (Locked Answers Gap 5). This realizes CP-42's "whatever address form that program listens on" by construction. It makes no claim about how each operating system decides.
- **(b) The line names the address `start` was given.** CP-40 fixes the words with `127.0.0.1:8017`, and Locked Answers Gap 3 says the message must name the address the tracker tried. Writing it from the `address` argument gives `127.0.0.1:8017` under `python3 main.py`. A test that starts on another port gets its own port in the line. `tests/unit/test_address.py:47-50` also forbids a second address literal in `main.py`.
- **(b) CP-43's order and CP-41's no-write are realized by the order `start` already has.** The saved data is read before `listen` is called, so unreadable data wins and the two messages can never both show. Nothing between the read and `listen` saves: `Tracker`'s constructor only holds the state. The only write path, `SavedData.save`, makes `data/` (`persistence/saved_data.py:67`), and it is reached only from an action while serving. M keeps that order, and the CP-41 rows check it.
- **(b) The status is 1.** CP-39 asks for non-zero. 1 is what the unreadable start returns (`main.py`, `start`'s docstring), and it is what the start returns today.
- **(b) CP-39's "the holder keeps the address" holds because the listener does not switch on port reuse.** `ThreadingHTTPServer` sets `allow_reuse_address` only. `python3 -c "import http.server; print(http.server.HTTPServer.allow_reuse_address, http.server.HTTPServer.allow_reuse_port)"` printed `True False` on Python 3.14.7. With port reuse off on the tracker's side, the tracker cannot share the port with a holder. W keeps the option off, and the W and M rows check that the holder still answers.
- **(b) The process-level test lives in `tests/e2e/`, in a module of its own, and it does not skip.** `docs/nfdr.md` QC-55 already places the real start command at layer 5. `tests/conftest.py` keeps `tests/e2e/` out of `pytest tests/`, so the test does not take the machine's real `127.0.0.1:8017` during the default suite. A separate module keeps it apart from the browser tests, which start their trackers through `main.start` on a free port. If the test skipped when `8017` was busy, the suite would pass without checking anything, so the test fails instead and names the address.

**Reviews `docs/nfdr.md` delegates to `development-design`**

This change touches `web` and `main.py`. The reviews for a change to `web` apply, as does the review run on every change.

| QC | Verdict |
|---|---|
| QC-8 | Pass. `AddressTaken` is a type, and `listen` keeps nothing new between requests. |
| QC-12 | Pass. The change adds one error type and one guarded call. It adds no part. |
| QC-23 | Pass. `web` decides no rule. Telling "address in use" from other bind failures is part of listening, which `web` owns. |
| QC-24 | Pass. `main` writes one more start message. It holds no rule, no page and no file format. |
| QC-27 | Pass. Only `web` and the wiring in `main.py` change. `domain`, `application` and `persistence` do not. |
| QC-41 | Pass. The change reads, holds and writes no secret. |
| QC-60 | Pass on a condition, because the harness gap stands. `errno.EADDRINUSE` and exception chaining are in Python 3.11. The new code must use nothing newer than 3.11. |
| QC-5, QC-20 to QC-22, QC-25, QC-26, QC-36, QC-46 | Not applicable. The change adds no `domain` refusal, saved field or page. It does not touch the saving contract, `domain`, `application` or `persistence`. QC-5 is not applicable for the reason given in the first note above. |
| QC-40 | **Packages:** Pass. On 2026-10-07 I sent all 15 pins in `tests/requirements.txt` to `https://api.osv.dev/v1/querybatch`, and it returned no advisory for any of them. PyPI's newest Playwright is still 1.63.0 (`https://pypi.org/pypi/playwright/json`). **Browser:** Pass today, failing tomorrow. Playwright 1.63.0 installs Chromium `153.0.8010.12` (`packages/playwright-core/browsers.json` at tag `v1.63.0`, revision 1243). The Chrome Releases blog's post of 2026-09-08, which promoted Chrome 153 to stable as `153.0.8010.36`, lists five critical CVEs: CVE-2026-87464, CVE-2026-87488, CVE-2026-87438, CVE-2026-87527 and CVE-2026-87628. Today they are 29 days old, and they pass 30 days on 2026-10-08. No newer Playwright exists to move the pin to. From 2026-10-08, QC-40 blocks the next change unless the browser is replaced or the owner records a dated exception in `docs/nfdr.md`'s Review Notes. The previous design (`trail/2026-10-07_a-not-found-page/change_design.md`, QC-40 row) recorded the same deadline. |
