# Change Spec — a start on readable saved data prints a path with a non-text byte

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing
**Request:** When the tracker's saved data sits at a path holding a byte that is not text, a start on readable saved data (none yet, or a valid file) currently fails while it builds the ready line: the line's text cannot be written to the console, `UnicodeEncodeError` is raised and the tracker does not start. Make that start print the ready line and serve its page. The path in the line is written in the one form `products/tracker17/docs/CONTENT.md` § *A path the tracker prints* fixes: the byte as a backslash, an x and two hex digits (`\xe9`), nothing else in the path changed and no replacement mark, so a path decoded from `b'/tmp/caf\xe9/data'` ends the line as `Saved data is kept at /tmp/caf\xe9/data.`. Add a test under `products/tracker17/tests/` that starts the tracker on readable saved data at such a location, holds that stdout carries that ready line and that the page is served on the printed address, and fails on `main` before the change with `UnicodeEncodeError`. The line for a path with no such byte must not change, so the existing ready-line tests pass untouched, and the full suite passes as the project's `Test command:`.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `core/doctrine/engineering/languages/python/README.md`

---

## Change Summary

A start on readable saved data at a path holding a non-text byte prints the ready line and serves, instead of dying on the line or writing the raw byte. Sizing: one capability, one merge. The acceptance boundary is the ready start on such a path, from the station's reached-when 1 to 4, and every rule below is that capability or its proof.

---

## Rules

### The start

- **CP-747:** A start on readable saved data (none yet, or a valid file) at a location whose path holds a non-text byte does not fail. Its first and only output is one line on standard output, `The tracker is running. Open http://<host>:<port> in your browser. Saved data is kept at <location>.`, and standard error stays empty. It then serves the tracker's page on the printed address (`GET /` answers 200) until Ctrl-C, which stops it with status 0 and nothing more written.

### The path's form

- **CP-748:** In that line, each non-text byte of the path is written as a backslash, an x and the byte's two lowercase hex digits, as `docs/CONTENT.md` § *A path the tracker prints* fixes. A path decoded from `b'/tmp/caf\xe9/data'` ends the line `Saved data is kept at /tmp/caf\xe9/data.`, where `\xe9` is four characters. Several such bytes are each written on their own, in place. No replacement mark appears, and neither does the form `\udce9`.
- **CP-749:** A non-text byte is any byte of the path that the machine's file-name decoding could not turn into text, whichever byte it is and wherever it sits. Which bytes those are is the machine's, and this spec fixes no list of them. Every other character of the path is written as it is today (CP-750).
- **CP-750:** The line is the same whatever encoding the console has. Today it depends on that encoding: under strict UTF-8 or ASCII the start raises `UnicodeEncodeError`, and under the C locale or Python's UTF-8 mode it writes the raw byte `0xE9` (`products/tracker17/main.py:139`). After the change each of these writes the four characters.

### What stays as it is

- **CP-751:** The line for a path with no non-text byte does not change, byte for byte. A valid non-ASCII character stays as that character (`/café` stays `/café`, not an escape). A real backslash in a folder name stays as it is. The existing ready-line tests pass untouched.

### The proof

- **CP-752:** A new test under `products/tracker17/tests/` makes a real start of the tracker in a child process, on saved data that does not exist yet, at a location decoded from a path holding `\xe9` (`os.fsdecode(b'/tmp/caf\xe9/data')` or an equivalent). It holds that standard output carries the whole ready line in CP-748's form and that the page is served on the address the line prints. The test sets the child's console to strict UTF-8 itself, so its verdict does not depend on the locale the suite runs under. On `main` before this change it fails with `UnicodeEncodeError`, and after the change it passes.
- **CP-753:** The same test also covers a valid file at such a location wherever the file system can hold one. On a file system that refuses to create such a directory, that case reports as skipped, not passed, and the skip rests on the refusal itself and on no check of the operating system.
- **CP-754:** A test holds CP-750's other console: a start with no strict console setting (the C locale or UTF-8 mode) writes the four characters and never the raw byte.
- **CP-755:** The first console output on such a path is still the address and then the location, with nothing before them (NFDR QC-55, SDD OB-2). The new test asserts this at the layer it runs at, and the existing layer-5 test of QC-55 passes untouched.
- **CP-756:** The change passes Ruff's format check, Ruff's lint and mypy (NFDR QC-62), and adds no operating-system check to any module outside `tests/` (NFDR QC-61). The full suite passes as `project.md` `Test command:` runs it.

---

## Examples

| Scenario | Expected behavior | Rules |
|---|---|---|
| Start, no saved data yet, location from `b'/tmp/caf\xe9/data'`, strict UTF-8 console | Stdout is one line, `The tracker is running. Open http://127.0.0.1:<port> in your browser. Saved data is kept at /tmp/caf\xe9/data.`. Stderr is empty and `GET /` on that address answers 200. Ctrl-C gives status 0. | CP-747, CP-748, CP-752, CP-755 |
| The same start on `main` before the change | `UnicodeEncodeError`, nothing on stdout, status 1 | CP-752 |
| Start on a valid `tracker.json` in a directory holding the byte, on a file system that allows it | The same line, and the page shows the saved data | CP-747, CP-753 |
| The same case on a file system that refuses the directory | Reported as skipped | CP-753 |
| Location from `b'/tmp/a\xe9\xff/data'` | The line ends `Saved data is kept at /tmp/a\xe9\xff/data.` | CP-748, CP-749 |
| The first example under the C locale, UTF-8 mode or an ASCII console | The same line, in four characters and with no raw byte | CP-750, CP-754 |
| Location `/tmp/café/data`, as valid UTF-8, UTF-8 console | The line ends `Saved data is kept at /tmp/café/data.` and the bytes written are `caf\xc3\xa9` | CP-749, CP-751 |
| A folder really named `a\xe9b`, seven plain characters | The line shows `a\xe9b` as it is, the same as today | CP-751 |
| Location with plain characters only | The line is identical to today's | CP-751 |
| The product's checks after the change | Ruff format, Ruff lint, mypy and the full `Test command:` pass | CP-756 |

---

## Verified Claims

Run on the product worktree at base commit `a7d507b23`, through real child-process starts of `main.start`, with the project's locked environment.

| Claim | Verified by | What came back |
|---|---|---|
| CP-750, CP-752: under strict UTF-8 the start fails in the ready line | Real start at `b'/tmp/caf\xe9/data'`, `PYTHONIOENCODING=utf-8:strict`, and again with the inherited UTF-8 locale | `a7d507b23`: status 1, stdout empty, `UnicodeEncodeError ... surrogates not allowed`, raised from `print` at `main.py:139` |
| CP-750: an ASCII console also fails today | The same start, `PYTHONIOENCODING=ascii` | `a7d507b23`: status 1, `UnicodeEncodeError` |
| CP-750, CP-754: under the C locale or UTF-8 mode it does not fail, and writes the raw byte | The same start, `LC_ALL=C`, then `PYTHONUTF8=1` | `a7d507b23`: status 0, the line ends with bytes `/tmp/caf\xe9/data.\n` holding the single raw byte `0xE9`, `GET /` answers 200 |
| CP-753: a file system may refuse the directory | `os.mkdir` of a path holding `\xe9` on the development machine's file system | `a7d507b23`: refused, errno 92 `Illegal byte sequence`, so a valid file at such a path cannot be built there; the valid-file case was not run there |
| CP-752: the none-yet case reaches the line on that same file system | The strict UTF-8 start above, which ran through the claim and the load before raising in `print` | `a7d507b23`: the failure is in the ready line, not in the unreadable branch |
| CP-751: a plain path's line, valid-file start | Real start on a valid `tracker.json`, then `GET /` | `a7d507b23`: status 0, the ready line, 200 |
| CP-751: a valid non-ASCII character stays | Real start at a path holding `café` as UTF-8 | `a7d507b23`: line ends `/caf` + bytes `\xc3\xa9` + `.`, status 0 |
| CP-751: a real backslash stays | Real start at a folder named `a\xe9b` in plain characters | `a7d507b23`: line ends `/a\xe9b.`, status 0 |
| CP-751: the existing ready-line tests pass today | `pytest tests/integration/test_start_stop.py::test_idle_stop_preserves_every_saved_path_and_byte`, `::test_real_start_keeps_the_non_raising_handler_through_its_return`, `::test_real_start_stops_at_the_completed_ready_write`, `::test_real_start_stops_while_a_real_request_is_saving`, `tests/integration/test_start.py::test_external_repair_does_not_change_the_running_unreadable_page`, `::test_set_aside_then_restart_preserves_the_earlier_work` | `a7d507b23`: 8 passed |
| CP-755: the layer-5 test of QC-55 passes today | `pytest tests/e2e/test_first_project.py -k "ready or start or console or first"`, which selects `test_the_first_output_is_the_ready_message_address_before_location` | `a7d507b23`: 11 passed |
| CP-756: the QC-62 gates are clean before the change | `ruff format --check .`, `ruff check .`, `mypy main.py errors.py domain application persistence web` | `a7d507b23`: all three pass |
| Out of Scope: the unreadable start stays as it is | `main._unreadable_line(...).encode('utf-8')` and `web.UnreadableSite(...)` on the path | `a7d507b23`: both raise `UnicodeEncodeError` |
| Out of Scope: the failed-action line stays as it is | Real start under `LC_ALL=C` at the path, then a `POST /projects` that cannot save | `a7d507b23`: stderr `OSError: [Errno 92] Illegal byte sequence: '/tmp/caf\udce9'` |
| Out of Scope: a valid character an ASCII console cannot write stays as it is | Real start at a path holding `café`, `PYTHONIOENCODING=ascii` | `a7d507b23`: status 1, `UnicodeEncodeError` on `'\xe9'` |

---

## Out of Scope

- The unreadable start, its line and the unreadable-data page, which still raise on such a path. This is the seed's next item, `unreadable-start`.
- The failed-action console message. `docs/CONTENT.md` § *A path the tracker prints* says "one form in every place a path is written", and `products/tracker17/web/routes.py:1327-1332` writes the error text as it comes, which shows the path as `\udce9`. The request says "no other message text changed", so this is handed on in `deferred_decisions.md`.
- A valid character a console's own encoding cannot write, which is a different cause with the same traceback (`docs/CONTENT.md` RN-33).
- A folder name that really holds a backslash, an x and two hex digits, which reads the same as an escaped byte (`docs/CONTENT.md` RN-33).
- Whether saved data can be stored at such a path on a file system that refuses it. A save there still fails as any failed save does.
- Any document change, and any change to the wording of a message beyond the path's form. FDR R-2, R-24 and R-25 hold as written.
- Where the saved data lives (FDR R-16), the claim, the lock and the page, beyond what the ready start needs.

---

## Locked Answers (the divergence record — self-review 2026-10-30)

- **Gap 1 — hex case:** lowercase, (b). `docs/CONTENT.md` says "two hex digits" and its only examples are lowercase, so the line matches what the document shows.
- **Gap 2 — several bytes:** each is written on its own, in place, (b). The form names a byte and the request names one, and this is the only reading that keeps "nothing else in the path changed".
- **Gap 3 — the console encoding:** the form holds on every console, (b). The request names only the failing case, but a start under the C locale succeeds today and writes a raw byte, which breaks `docs/CONTENT.md`'s one form, and fixing only the strict case would leave the output depending on the locale. CP-750 and CP-754 follow from this.
- **Gap 4 — what the test sets:** the test sets strict UTF-8 itself, (b). Without that, the same test on a C-locale run would see no `UnicodeEncodeError` on `main`, and the request requires that failure.
- **Gap 5 — the valid-file case:** it runs where the file system can hold the directory, and otherwise reports as skipped, (b). The request accepts either readable case, and the development machine's file system refuses the directory, so a required valid-file case could never pass there. A skip stays visible where a silent pass would not.
- **Gap 6 — checks the request left out:** CP-755 states NFDR QC-55, and CP-756 states NFDR QC-62 and QC-61, (e). The request names only the full suite, and these records bind any change to the ready line and the code.
