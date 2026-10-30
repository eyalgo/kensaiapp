# Change Spec — a start on unreadable saved data prints and serves a path with a non-text byte

**Date:** 2026-10-30
**Category:** feature
**Behaviour:** changing
**Request:** When the tracker's saved data sits at a path holding a byte that is not text and the data cannot be read, a start fails today: the unreadable-data page is built first (`web.UnreadableSite.__init__` encodes it as UTF-8) and the unreadable console line is printed after it, and both raise `UnicodeEncodeError`, so the tracker does not start. Make that start print the unreadable line and serve the unreadable-data page, each naming the path in the one form `products/tracker17/docs/CONTENT.md` § *A path the tracker prints* fixes: the byte as a backslash, an x and two hex digits (`\xe9`), nothing else in the path changed and no replacement mark, so a path decoded from `b'/tmp/caf\xe9/data'` shows as `/tmp/caf\xe9/data`. The ready start already does this through `main._shown_location`; bring the unreadable line and the page to the same form. Add tests under `products/tracker17/tests/`: one builds the unreadable line for `Path(os.fsdecode(b'/tmp/caf\xe9/data'))` and holds that it contains `/tmp/caf\xe9/data` (four characters `\xe9`), no U+FFFD and no character in U+DC80–U+DCFF, and that `.encode('utf-8')` does not raise; one builds `web.UnreadableSite` for that location and holds that it does not raise and that a request to the root answers with a page whose body carries the path in that form; and one starts the tracker through the start function on unreadable saved data at that location, with the file system calls faked (or skipped with the reason stated, as the ready start's valid-file case is, since this machine refuses the byte in a directory name), holding that the line is printed and the page is served. The line and page tests fail on `main` before the change (`UnicodeEncodeError` or a failed assertion on the path text) and pass after. A path with no such byte must print the line and the page exactly as before, so the existing unreadable-line and unreadable-page tests pass untouched, and the full suite passes as the project's `Test command:`. Sizing: one capability (the unreadable start on such a path, its line and its page being one behaviour, SDD § 6 S-8, and the page built before the line prints), one merge; the acceptance boundary is the station's reached-when 1 to 6. The failed-action console message is the seed's next item and stays out. Hold the path form to `CONTENT.md` with no new wording and no other message text changed. No document changes (FDR R-2, R-24 and R-25 hold as written). Saved data must never be written, replaced or deleted by this start or by serving the page (SDD SD-4); where the saved data lives (FDR R-16), the location the claim, the load and the saves use, the page's controls, the second-tracker refusal and the lock must not change, only how the location is shown.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `core/doctrine/engineering/languages/python/README.md`

---

## Change Summary

A start on saved data it cannot read, at a path holding a non-text byte, prints the unreadable line and serves the unreadable-data page instead of dying with `UnicodeEncodeError`, and both write the path in the one form `CONTENT.md` fixes. Sizing: one capability, one merge. The acceptance boundary is the unreadable start on such a path, from the station's reached-when 1 to 6, and every rule below is that capability or its proof.

---

## Rules

### The start

- **CP-757:** A start on saved data that cannot be read, at a location whose path holds a non-text byte, does not fail. Its first and only output is one line on standard output, `The tracker couldn't read its saved data at <location>, and nothing in it was changed. Open http://<host>:<port> in your browser to read this on a page. To start fresh on purpose, follow Setting saved data aside in the setup instructions.`, and standard error stays empty. It then serves until Ctrl-C, which stops it with status 0 and nothing more written.
- **CP-758:** While that start serves, every checked request is answered as on a path with no such byte: every address, whatever its query, gets the one unreadable-data page, 503, `Cache-Control: no-store`, with the page policy (NFDR QC-7, QC-33, QC-34); `GET /style.css` answers the stylesheet, 200; and a checked `post` marked `same-origin` is sent back with a 303. The page's sentence reads `The tracker couldn't read its saved data, which is kept at <location>. Nothing in it was changed or overwritten. To start fresh on purpose, follow Setting saved data aside in the setup instructions.`
- **CP-759:** `web.UnreadableSite`, built for the location as the file-name decoding gives it (`os.fsdecode(b'/tmp/caf\xe9/data')`), does not raise, and its page writes the path in CP-760's form. The form does not depend on the caller having converted the location first.

### The path's form

- **CP-760:** In the line and on the page, each non-text byte of the path is written as a backslash, an x and the byte's two lowercase hex digits, as `docs/CONTENT.md` § *A path the tracker prints* fixes. A path decoded from `b'/tmp/caf\xe9/data'` shows as `/tmp/caf\xe9/data`, where `\xe9` is four characters. Several such bytes are each written on their own, in place. Neither text holds U+FFFD, a character in U+DC80–U+DCFF, or the form `\udce9`, and `.encode('utf-8')` on each does not raise.
- **CP-761:** A non-text byte is any byte of the path that the machine's file-name decoding could not turn into text, whichever byte it is and wherever it sits. Which bytes those are is the machine's, and this spec fixes no list of them. Every other character of the path is written as it is today: a valid `é` stays that character, a real backslash stays, and on the page `<`, `&` and `"` in the path are shown as text (NFDR QC-36). The location is shown as one absolute path, as it is today.
- **CP-762:** The line is the same whatever encoding the console has: strict UTF-8, ASCII, the C locale and Python's UTF-8 mode each write the four characters, never the raw byte. Today every one of these fails before any output, at `products/tracker17/web/routes.py:1346`, which encodes the page before the line is printed.

### What stays as it is

- **CP-763:** For a path with no non-text byte, the line and the page do not change, byte for byte, and the existing unreadable-line and unreadable-page tests pass untouched.
- **CP-764:** Only how the location is shown changes. The location the claim, the load and the saves use, where the saved data lives (FDR R-16), the page's controls (none), the second-tracker refusal and the lock are as they are. Saved data is never written, replaced or deleted by this start or by serving the page (SDD SD-4, NFDR QC-51).

### The proof

- **CP-765:** A new test under `products/tracker17/tests/` builds the unreadable line for `Path(os.fsdecode(b'/tmp/caf\xe9/data'))` and holds that it contains `/tmp/caf\xe9/data` with the four characters `\xe9`, contains no U+FFFD and no character in U+DC80–U+DCFF, and that `.encode('utf-8')` on it does not raise.
- **CP-766:** A new test builds `web.UnreadableSite` for the location `os.fsdecode(b'/tmp/caf\xe9/data')` and holds that it does not raise, and that a request to the root answers 503 with a page whose body contains `/tmp/caf\xe9/data` with the four characters `\xe9`, no U+FFFD and no character in U+DC80–U+DCFF.
- **CP-767:** A new test makes a real start through `main.start` in a child process, with its console set to strict UTF-8 by the test, on saved data that cannot be read at a location holding the byte, placed beneath a regular file so that no directory with the byte need exist. It holds that standard output carries the whole line in CP-760's form, that the printed address serves the page in that form, that Ctrl-C gives status 0 with nothing more written, and that the regular file's bytes and its directory's listing are unchanged (NFDR QC-51). This case runs on every file system and never skips.
- **CP-768:** The same test also covers a `tracker.json` the tracker cannot read, in a directory really named with the byte, wherever the file system can hold one, asserting that file's bytes are unchanged and that no folder named with the four characters appears. On a file system that refuses the directory, that case reports as skipped with the refusal as its reason, and the skip rests on the refusal itself and on no check of the operating system (NFDR QC-61).
- **CP-769:** The tests of CP-765, CP-766 and CP-767 each fail on the tree this change starts from (`UnicodeEncodeError` or a failed assertion on the path text) and pass after. The failing run is recorded in the unit's report.
- **CP-770:** No new test patches a name inside a product module (NFDR QC-28, whose layer-6 walk in `tests/architecture/test_reach.py` fails on `monkeypatch.setattr` or `mock.patch` aimed at one), and every new or extended test module names the requirements it checks (NFDR QC-11).
- **CP-771:** The first console output on such a path is the line of CP-757, with nothing before it (NFDR QC-55, SDD OB-2). The test of CP-767 asserts this at its layer, and the existing layer-5 test, `tests/e2e/test_unreadable_data.py::test_the_browser_opens_the_unreadable_page_without_controls`, passes untouched.
- **CP-772:** The change passes Ruff's format check, Ruff's lint and mypy (NFDR QC-62); no module imports `main` (NFDR QC-2); no module outside `main.py` and the one site in `web/` writes to the console (NFDR QC-45); and no module outside `tests/` adds an operating-system check (NFDR QC-61). `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`, the project's `Test command:`, both exit 0.

---

## Examples

| Scenario | Expected behavior | Rules |
|---|---|---|
| The unreadable line for `Path(os.fsdecode(b'/tmp/caf\xe9/data'))` | Text holding `at /tmp/caf\xe9/data, and nothing`; four characters for the byte; `.encode('utf-8')` does not raise | CP-760, CP-765 |
| `web.UnreadableSite(os.fsdecode(b'/tmp/caf\xe9/data'), '127.0.0.1:8017')`, then `GET /` | Builds without raising; 503; body holds `kept at /tmp/caf\xe9/data.`, no U+FFFD, no U+DC80–U+DCFF | CP-759, CP-760, CP-766 |
| Real start at `<regular file>/caf\xe9`, strict UTF-8 console | Stdout is one line, naming `<regular file>/caf\xe9` as four characters. Stderr is empty. `GET /` on the printed address answers 503 with that path. Ctrl-C gives status 0. The file's bytes are unchanged | CP-757, CP-758, CP-760, CP-764, CP-767, CP-771 |
| The same start on the tree this change starts from | `UnicodeEncodeError`, nothing on stdout, status 1 | CP-762, CP-769 |
| That start under an ASCII console, the C locale or UTF-8 mode | The same line, four characters for the byte, no raw byte | CP-762 |
| `GET /people`, `GET /nothing?x=1`, `GET /style.css`, a same-origin `POST /projects` during that start | The same 503 page, the same page, the stylesheet with 200, a 303 | CP-758 |
| A directory really named with the byte, holding a `tracker.json` the tracker cannot read, on a file system that allows it | The line and page in the same form; the file's bytes unchanged; no folder named with the four characters | CP-764, CP-768 |
| The same case on a file system that refuses the directory | Reported as skipped, with the refusal as the reason | CP-768 |
| Location from `b'/tmp/a\xe9\xff/data'` | Line and page show `/tmp/a\xe9\xff/data` | CP-760, CP-761 |
| A path holding `<`, `&` and the byte, on the page | Shown as text beside `\xe9`; the raw page carries `&lt;` and `&amp;` | CP-761 |
| Location `/tmp/café/data`, valid UTF-8, on a UTF-8 console | Line and page show `/tmp/café/data`; `é` is that character | CP-761, CP-763 |
| A folder really named `a\xe9b`, seven plain characters | Line and page show `a\xe9b`, the same as today | CP-761, CP-763 |
| A relative location holding the byte | Shown as one absolute path, in the same form | CP-761 |
| A location with plain characters only | Line and page identical to today's | CP-763 |
| A second start on a location a running tracker is using | The one refusal message, unchanged | CP-764 |
| The new tests are read by the layer-6 walk | No patch of a product module; each module names what it checks | CP-770 |
| The product's checks after the change | Ruff format, Ruff lint, mypy and the full `Test command:` pass | CP-772 |

---

## Verified Claims

Run on the product worktree at base commit `ce9e51683`, with the project's locked environment. Real starts ran `main.start` in child processes. "Patched build" is the base with the path form applied to the page and the line from the child's own start program, in memory only, to test the rules against a tree that does not exist yet. The worktree stayed clean.

| Claim | Verified by | What came back |
|---|---|---|
| CP-760, CP-765: the line cannot be encoded today | `main._unreadable_line('127.0.0.1', 8017, Path(os.fsdecode(b'/tmp/caf\xe9/data'))).encode('utf-8')` | `ce9e51683`: `UnicodeEncodeError`, surrogates not allowed |
| CP-759, CP-766: the site cannot be built today | `web.UnreadableSite(str(<that location>), '127.0.0.1:8017')` | `ce9e51683`: `UnicodeEncodeError` from `web/routes.py:1346` |
| CP-762, CP-767, CP-769: a real unreadable start can run on this machine, and fails today on every console | Real start at `<scratch>/afile/caf\xe9`, where `afile` is a regular file, under `PYTHONIOENCODING=utf-8:strict`, `PYTHONIOENCODING=ascii`, `LC_ALL=C` and `PYTHONUTF8=1` | `ce9e51683`: each gives status 1, empty stdout, `UnicodeEncodeError ... '\udce9'` |
| CP-757, CP-760, CP-762, CP-767: such a start gives the line in the form | The same four starts on the patched build | Each: status 0, stdout one line naming `<scratch>/afile/caf\xe9` as four characters, stderr empty |
| CP-758, CP-760, CP-764: such a start serves the page and leaves the data | The strict UTF-8 start on the patched build, then `GET /`, `/people`, `/nothing?x=1`, `/style.css` and a same-origin `POST /projects`, then SIGINT | 503, 503, 503 with one body, `no-store` and a policy header; page shows `<scratch>/afile/caf\xe9`, no U+FFFD, no U+DC80–U+DCFF; stylesheet 200; `POST` 303; stop status 0, nothing more written; `afile` still holds its one byte and the directory listing is unchanged |
| CP-761: markup beside the byte stays text on the page | The same start on the patched build, leaf `a<b>&\xe9` | The raw page holds `a&lt;b&gt;&amp;\xe9` |
| CP-768: a file system may refuse the directory | `os.mkdir(os.fsdecode(b'/tmp/caf\xe9'))` on this machine | `ce9e51683`: refused, errno 92 `EILSEQ` |
| CP-768 and the Locked Answer on the request's skip: a location beneath no regular file is not unreadable here | `SavedData(Path(os.fsdecode(b'/tmp/caf\xe9/data'))).load()` | `ce9e51683`: `None`, no saved data, so this location alone reaches the ready start on this machine |
| CP-763: the existing unreadable-page and route tests pass at the base | `pytest tests/integration/test_unreadable_pages.py tests/integration/test_unreadable_routes.py tests/integration/test_start.py` (run with the modules of the next rows: 317 passed, 1 skipped) | `ce9e51683`: passed; the one skip is `test_ready_start.py`'s valid-file case |
| CP-763, CP-771: the existing line assertions and the layer-5 test pass at the base | `tests/integration/test_start.py::test_an_unreadable_start_serves_one_page_and_announces_once`, `::test_a_relative_location_is_shown_as_one_absolute_path`; `tests/e2e/test_unreadable_data.py` | `ce9e51683`: passed; e2e 1 passed |
| CP-763: a plain path's line at a real start | Real start at `<scratch>/afile/plain`, strict UTF-8 console | `ce9e51683`: status 0, the line as written in CP-757 |
| CP-761, CP-763: a valid `é` and a real backslash stay as they are | `main._unreadable_line` and `web.UnreadableSite(...)` then `GET /`, on `/tmp/café/data` and on a folder named `a\xe9b` in seven plain characters | `ce9e51683`: each path appears unchanged in the line and in the page's bytes |
| CP-764: the second-tracker refusal, the lock, where the data lives | `pytest tests/integration/test_single_tracker.py tests/integration/test_location_use.py tests/integration/test_saved_data.py tests/unit/test_address.py` | `ce9e51683`: passed |
| CP-764: the page's controls | `tests/integration/test_unreadable_pages.py::test_unreadable_page_offers_no_navigation_or_data_control` | `ce9e51683`: passed |
| CP-764: saved data is left as it was by an unreadable start | `tests/integration/test_start.py::test_an_unreadable_start_changes_nothing_in_the_location`, `::test_an_unreadable_lifetime_preserves_all_saved_paths_and_bytes` | `ce9e51683`: passed |
| CP-770: a test may not patch a product module | `tests/architecture/test_reach.py` | `ce9e51683`: passed; its own cases show `monkeypatch.setattr(main, 'x', 1)` is reported and `monkeypatch.setattr(os, 'getcwd', 1)` is not |
| CP-772: no module imports `main` is a standing rule the page's form must meet | `docs/nfdr.md` QC-2, read | "No module imports `main`." |
| CP-772: the QC-62 gates are clean before the change | `ruff format --check .`, `ruff check .`, `mypy main.py errors.py domain application persistence web` | `ce9e51683`: all three pass |
| Out of Scope: the ready start stays as it is | `pytest tests/unit/test_start_message.py tests/integration/test_ready_start.py` | `ce9e51683`: passed, the one skip as above |
| Out of Scope: the failed-action line stays as it is | Real start under `LC_ALL=C` at `<scratch>/caf\xe9/data`, then a `POST /projects` that cannot save | `ce9e51683`: stderr ends `OSError: [Errno 92] Illegal byte sequence: '<scratch>/caf\udce9'` |
| Out of Scope: a valid character an ASCII console cannot write stays as it is | Real start at `<scratch>/afile/café`, `PYTHONIOENCODING=ascii` | `ce9e51683`: status 1, `UnicodeEncodeError` on `'\xe9'` |
| Out of Scope: a surrogate no file-name decoding gives stays as it is | `main._unreadable_line` and `web.UnreadableSite` on paths holding `\ud800`, `\udc7f` and `\udd00` | `ce9e51683`: the line holds the character as it is; the site raises `UnicodeEncodeError` |
| CP-760: the `\xe9` form renders a product-chosen form, not a language-level fact | `packet does not fix it` — no line under `core/doctrine/engineering/languages/python/` or `testing_python.md` mentions surrogates or file-name decoding; `docs/CONTENT.md` § *A path the tracker prints* chooses the form | `\xe9`, two lowercase hex digits |

---

## Out of Scope

- The failed-action console message. `docs/CONTENT.md` § *A path the tracker prints* says "one form in every place a path is written", and `products/tracker17/web/routes.py:1327-1332` writes the error text as it comes, which shows the path as `\udce9`. The request says "The failed-action console message is the seed's next item and stays out", so it is handed on in `deferred_decisions.md`.
- The ready start, which already writes this form.
- A valid character a console's own encoding cannot write, which is a different cause with the same traceback (`docs/CONTENT.md` RN-33).
- A folder name that really holds a backslash, an x and two hex digits, which reads the same as an escaped byte (`docs/CONTENT.md` RN-33).
- A surrogate no file-name decoding can give, outside U+DC80–U+DCFF. It is no file-name byte, so it is never escaped; the line writes it as it is and the page still raises, both as today.
- Any document change, and any change to a message's wording beyond the path's form. FDR R-2, R-24 and R-25 hold as written.

---

## Locked Answers (the divergence record — self-review 2026-10-30)

- **Gap 1 — the start test is a real start, and its first case never skips:** (b), going beyond the request's "faked (or skipped ...)". Its reason for allowing either was that this machine refuses the byte in a directory name. The refusal is real, but a location beneath a regular file needs no such directory: the start there reads as unreadable on this machine, and it fails at the base and works on a patched build (Verified Claims). A proof that runs is worth more than a skip, and the same case makes CP-769 hold for the start as well as for the line and the page. The directory case the request described stays, as CP-768, with the skip it allowed.
- **Gap 2 — faking is limited by a record:** CP-770 states NFDR QC-28, (e). The request allows the file system calls to be faked, and a fake aimed at a product module fails QC-28's layer-6 walk, so that one form of faking is closed. Faking is not needed for CP-767.
- **Gap 3 — hex case:** lowercase, (b). `docs/CONTENT.md` says "two hex digits" and its only examples are lowercase, and the ready line writes them so.
- **Gap 4 — several bytes:** each is written on its own, in place, (b). The form names a byte and the request names one, and this is the only reading that keeps "nothing else in the path changed".
- **Gap 5 — the console encoding:** the form holds on every console, (b). The request names none, and `docs/CONTENT.md` says one form in every place. Without this, the line could write a raw byte under the C locale once the page stops raising, which is what the ready start did before its own change.
- **Gap 6 — the site is given the decoded location:** CP-759 holds for a site built with the location as decoded, (b). The request and the station's reached-when 2 build the site that way, so a start that only converted the location before handing it over would pass a real start and fail this test. Where the conversion lives is the design's, within NFDR QC-2.
- **Gap 7 — the page's other answers:** CP-758 pins the status, the headers, the stylesheet and the `post` on such a path, (b) and (e) for NFDR QC-7, QC-33 and QC-34. The request names only the root, and those records bind every address.
- **Gap 8 — checks the request left out:** CP-761 states NFDR QC-36; CP-764 and CP-767 state NFDR QC-51; CP-770 states NFDR QC-11; CP-771 states NFDR QC-55; CP-768 and CP-772 state NFDR QC-61; CP-772 states NFDR QC-2, QC-45 and QC-62, (e). The request names SD-4 and the full suite, and these records bind any change to this start, its page and its tests.
- **Gap 9 — a surrogate no decoding gives:** left as it is and never escaped, (b). The request's form is for a byte that is not text, and the ready line already treats these characters this way.
