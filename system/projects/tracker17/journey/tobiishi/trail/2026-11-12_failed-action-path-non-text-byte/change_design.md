# Change Design — a failed action at a non-text-byte path prints its error text as the system reported it

**Date:** 2026-11-13
**Category:** bug
**Behaviour:** preserving
**Publishes text:** no
<!-- A preserving change adds no words, so the line is always `no`. Moving existing text is placement, and placement is the Developer's. -->
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened, with every concern file it routes (`toolchain.md`, `layout.md`, `quality_gates.md`, `conventions.md`, `errors_logging.md`, `environment.md`, and `testing_python.md`)

---

## 1. Change Summary

One characterization test pins what the tracker already writes to the console's error stream when an
action fails with an `OSError` whose text holds `os.fsdecode(b'/tmp/caf\xe9')`. Line 1 is the action's
plain sentence. Line 2 is `OSError: <text>` with the path written as `\udce9`. The write raises nothing
(`docs/CONTENT.md` RN-35; SDD § 4 OB-3). No production module moves and no import changes. Production
code changes only if the new test fails at the base. The spec measured that it does not.

---

## 2. Blast Radius

No transitive blast radius — public surfaces unchanged, so no importing module is affected.

| Module | Status | What changes |
|---|---|---|
| `web/` | Unchanged | — (`Site._report_failure`, `web/routes.py:1326-1332`, is the subject; it changes only under the spec's conditional fix, and then only inside that one site) |
| `domain/`, `application/`, `persistence/`, `main.py`, `errors.py` | Unchanged | — |
| `tests/integration/` | Modified (test added) | New module `tests/integration/test_failure_report.py` holding the characterization test |

`web/__init__.py`'s exports stay the seven names: `AddressTaken`, `Listener`, `Response`, `Site`,
`UnreadableSite`, `listen`, `listen_unreadable`. Placement by SDD § 3: the subject is `web`'s one failure site
(OB-3; NFDR QC-23, QC-45, QC-56). The test adds no logic to any part.

---

## 3. Layout Plan

No production symbol moves. The spec left one placement open: where the test sits.

- **Layer:** 3 — Application (NFDR § 9 table). The test drives `web` with `application` in one process with
  no socket, and the clock and saver are handed in (SDD § 4 TS-1). This is the same layer as the AC-18 tests
  in the `tests/integration/test_*_routes.py` modules.
- **Module:** `tests/integration/test_failure_report.py`, which is new. No existing file has that name. Its
  only subject is the console report. That report runs across every feature's routes, so no
  `test_<feature>_routes.py` module owns it.

| Symbol | Kind | Target module |
|---|---|---|
| the characterization test (the developer names it), parametrized over the two error forms of §5 | test function | `tests/integration/test_failure_report.py` |
| the `Tracker` subclass whose one action raises the case's `OSError` | test class | `tests/integration/test_failure_report.py` |

- **`web/__init__.py` re-exports:** the seven names in §2. Unchanged, nothing added or removed.

---

## 4. Code Strategy

| Module | Hint |
|---|---|
| `web/` | None — unchanged. If the new test shows a raise or a rewritten path at the base, the fix stays inside `Site._report_failure`. It keeps OB-3's two lines and the single write site QC-45 requires, adds no state (QC-8) and no rule (QC-23), and puts no Python text on a page (QC-57). |
| `tests/integration/test_failure_report.py` | **The stream.** Run the request inside `contextlib.redirect_stderr`, aimed at an `io.TextIOWrapper` over an `io.BytesIO`. Give it `encoding="utf-8"` and `errors="backslashreplace"`, the error handler Python opens `sys.stderr` with. Then assert on the bytes in the buffer. Do not use `capsys`: it encodes strictly and raises on the message form (spec, Verified Claims). Do not use any other pytest capture: pytest builds those streams, not Python's console. **The failure.** Hand `Site` a `Tracker` subclass whose one action raises the case's `OSError`. The precedent is `Breaking(Tracker)` in `tests/integration/test_comment_routes.py`. Give it a saver and a clock imported from the stand-ins the integration modules already define (`SwitchedSaver`, `MovableClock` in `test_task_routes.py`). TS-6 bars a new class that defines `save` or `now`, and the existing saver's error is fixed, so the failure has to come from the tracker. Pick an action whose sentence names no typed value, or type nothing that holds `caf`. The short comment-add sentence is one such. **The trace.** The module docstring names `Site._report_failure` in `web/routes.py`. That makes the spec's grep print the test. It also names SRS NFR-8 and AC-18. Write every path the docstring names from the product root (`docs/CONTENT.md`, not `CONTENT.md`), because TS-4's pointer test checks each one there. |

---

## 5. Test Continuity

The existing suite is the characterization contract and passes unchanged. One characterization test is
added, because no test covers this surface today (spec, Verified Claims: the grep prints nothing at the
base). The test asserts no new behaviour.

| Affected public surface | Existing coverage | Characterization test to add? |
|---|---|---|
| The console report of a failed action, `Site._report_failure` reached through `Site.handle`, on an `OSError` whose text holds `/tmp/caf\udce9` | none | **Yes** — `tests/integration/test_failure_report.py`, layer 3. Fakes handed in: the `Tracker` subclass, the existing `SwitchedSaver` over `SavedData` in the test's `tmp_path`, and the existing `MovableClock` |
| `from web import …` — the seven names | the existing suite imports them | No |

What the new test asserts, against each spec line:

| Spec line | Assertion |
|---|---|
| Invariant 3.1 — the sentence comes first and names no path | Line 1 of the stream's bytes equals the action's sentence exactly, and it holds neither `caf` nor `\xe9` |
| Invariant 3.2 — the kind and the text as the system reported them | Line 2 equals the expected line exactly, once for each form. Message form, `OSError(f"cannot write {path}")`: `OSError: cannot write /tmp/caf\udce9`. Errno form, `OSError(92, "Illegal byte sequence", path)`: `OSError: [Errno 92] Illegal byte sequence: '/tmp/caf\udce9'`. Neither line holds `\xe9`, and nothing follows line 2 |
| Invariant 3 — writing raises nothing | `Site.handle` returns the action's failure response, and nothing propagates |
| Structural Goal — a real guard | Under the mutation the spec names (`_report_failure` rewrites the path to `\xe9`), line 2 fails in both forms. The unit's report records the mutation, the failure it caused, and the revert |
| Structural Goal — absent, then present | The docstring names `_report_failure`, so `git grep -n 'report_failure\|Could not save' -- products/tracker17/tests` prints the new module |
| Invariants 1, 6 | Both suite commands and `ruff format --check .` / `ruff check .` exit 0 with the module in the tree |
| Invariant 4 — no stand-in added | The new module defines no class with `save` or `now`, and none based on a test-support class. The QC-64 walk is not built yet (NFDR RN-65), so this holds by review |

Retired assertions: none. The rule's other branch, an error with no text (`f"{kind}\n"`), carries no path.
This change does not touch it, and its coverage is unchanged.

---

## Records this change makes false

None — read `docs/adr/` (index and records), `docs/nfdr.md`, `docs/fdr.md`, `docs/SDD.md` § 3 and § 4
OB-3 / TS-1 to TS-6, and `docs/CONTENT.md` RN-33 and RN-35; nothing in them goes false.

---

## Architect Review Notes

- **(b) How "the console's error stream" is realized:** in-process, on a stream built with Python's own
  `sys.stderr` error handler (`backslashreplace`). Not done: a child process, and pytest's capture. The test
  writes the same bytes the console stream writes, by construction. A product-interpreter scratch run on
  2026-11-13 read `sys.stderr.errors` as `backslashreplace`, and such a wrapper wrote
  `cannot write /tmp/caf\udce9` and `[Errno 92] Illegal byte sequence: '/tmp/caf\udce9'`. A child process was
  not used because SDD § 4 TS-1 tests `web` in one process with no socket, and the spec's mutation is
  in-process. This is the spec's Gap 1, settled by construction: the stream is not a capture that refuses.
- **(b) Both error forms, line 2 by exact equality:** the spec measured both forms. Each catches a different
  rewrite. The message form passes a raw surrogate to the stream. The errno form passes text that is
  already escaped. An exact line is what "exactly as the error carried it" requires.
- **(b) The failure enters through a handed `Tracker`, not a saver:** the existing saver stand-in raises a
  fixed `PermissionError`, and TS-6 / QC-64 bar a new class that defines `save`. A `Tracker` subclass
  defines neither `save` nor `now` and has a product base, so it is not a stand-in under the spec's
  definition. It is handed to `Site`, which keeps TS-2.
- **Packet:** no conflict. `web` is the adapter that touches the socket and the console (SDD § 3, the four
  layers), so the reporter writing `sys.stderr` from its body is the adapter's own reach, and it builds no
  collaborator. The test hands in every collaborator. It swaps the stream through the standard library and
  patches no product name. QC-28's walk flags only patches aimed at a product module, and
  `tests/architecture/test_reach.py` exempts a standard-library target.
- **Delegated review — QC-12:** pass. One test module, paid for by SRS NFR-8 / AC-18 and CONTENT RN-35.
  No part added.
- **Delegated review — QC-60:** pass for the design. `contextlib.redirect_stderr` and `io.TextIOWrapper`
  predate 3.11, and no post-3.11 feature is required. No 3.11 run was made; that gap stays as QC-60
  records it.
- **Delegated review — QC-41:** pass. No secret, account or credential.
- **Delegated reviews not triggered:** QC-5, QC-8, QC-23, QC-25, QC-26, QC-27, QC-36 and QC-46. No change
  touches `web`, `persistence`, the saving contract, page building, a refusal or a saved field. The §4
  `web/` row binds the conditional fix to QC-8 / QC-23. No dependency or pin moves, so QC-40's first
  moment does not arise.
- **Delegated review — QC-40, packages:** no applicable critical advisory. `gh api --method GET /advisories
  --raw-field ecosystem=pip --raw-field severity=critical --field per_page=100 --paginate` returned 842
  advisories. These were compared locally against the 27 external names in `uv.lock` and
  `.behave/uv.lock`, and five names matched. Each locked version is at or past its fix: Pygments 2.21.0
  (GHSA-fff8-4w9p-7v76, fixed 2.1), anyio 4.16.0 (GHSA-82r6-8w77-94w6, fixed 4.14.2), certifi 2026.10.23
  (GHSA-6q48-6c7w-9gw2, fixed 2026.10.18), h11 0.16.0 (GHSA-vqfr-h8mv-ghfj, fixed 0.16.0) and httpx 0.28.1
  (GHSA-h8pj-cxx2-jfg2, fixed 0.23.0). The request sent no dependency name.
- **Delegated review — QC-40, browser:** the installed driver's `browsers.json` declares chromium and
  chromium-headless-shell revision 1254, 158.0.8127.18. Google's Stable Channel Update for Desktop of
  2026-11-11 fixes five critical CVEs in 157.0.8103.78/.79: CVE-2026-126885, -126895, -126879, -126846 and
  -126911 (`https://chromereleases.googleblog.com/2026/11/stable-channel-update-for-desktop_01744469280.html`).
  Whether 158.0.8127.18 carries those fixes is not established. Either way the advisory is two days old,
  so QC-40's 30-day window runs to 2026-12-11. No critical advisory older than 30 days is shown against
  this build. Verdict: not blocking. The owner watches the window.
- **Delegated review — QC-40, package feed:** down; the graph moment stays owed, as the entry provides.
  `gh api repos/<owner>/<repository>` read `admin: true`. `gh api repos/<owner>/<repository>/dependabot/alerts`
  returned 403, "Dependabot alerts are disabled for this repository." `gh api -X POST
  repos/<owner>/<repository>/dependency-graph/sbom/exports` returned 404. No discrepancy is raised.
- **Cold-read:** checks 5–10 and preserving checks 1–5 hold. No symbol moves, the re-exports are
  unchanged, `test_failure_report.py` collides with no file, and nothing changes an importable symbol.
  §3 carries no import wiring. No reading of the spec was set aside and no packet departure arose, so
  `deferred_decisions.md` is not written.
