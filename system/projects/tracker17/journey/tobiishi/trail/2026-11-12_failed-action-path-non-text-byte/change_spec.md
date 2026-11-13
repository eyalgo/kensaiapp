# Change Spec — a failed action at a non-text-byte path prints its error text as the system reported it

**Date:** 2026-11-13
**Category:** bug
**Behaviour:** preserving
**Request:** When an action fails at a path holding a byte that is not text, the tracker writes its plain sentence, which names no path, then the error's kind and text to the console's error stream (`Site._report_failure`, `products/tracker17/web/routes.py`). `products/tracker17/docs/CONTENT.md` RN-35 settles that the path inside the error text is printed exactly as the system reported it (`\udce9`), not rewritten to `\xe9`. The site already does this and does not raise (measured 2026-11-05), but no test holds it. Add that test under `products/tracker17/tests/`: it makes an action fail with an `OSError` whose message holds the path `os.fsdecode(b'/tmp/caf\xe9')` (`/tmp/caf\udce9`) and captures what the tracker writes to the error stream. It holds that the plain sentence line (for example `Could not save.`) is written first and holds neither `caf` nor `\xe9`; that the next line holds the error's kind and the path as `\udce9`, exactly as the error carried it, and does not hold `\xe9`; and that the write raised nothing. Prove it is a real guard: the walker tries changing `_report_failure` to rewrite the path to `\xe9`, sees the test fail, reverts the mutation, and records that in the unit's report. Change production code only if the new test shows the write raises or the path is rewritten; otherwise the change is the test alone. `git grep -n 'report_failure\|Could not save' -- products/tracker17/tests` prints nothing before and the new test after. Both suites pass: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and the same on `products/tracker17/tests/e2e/`.
**Language resolution:** Python — step 1, `project.md` `Languages:` — `<CORE>/doctrine/engineering/languages/python/README.md` opened (recorded only: a preserving spec takes no invariant from the packet)

---

## Change Summary

The tracker already reports a failed action at a non-text-byte path the way `CONTENT.md` RN-35 settles, and nothing pins it. This change adds the test that pins it, and touches production code only if that test shows the write raises or the path is rewritten on the console's error stream. Behaviour is unchanged.

---

## Invariants (characterization contract)

- **The existing test suite passes unchanged.** Both commands of `project.md` `Test command:` exit 0: `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `uv run --locked --project products/tracker17 pytest products/tracker17/tests/e2e/`.
- **Public interface:** the names `web` exports stay as they are: `AddressTaken`, `Listener`, `Response`, `Site`, `UnreadableSite`, `listen`, `listen_unreadable`. No other package's exports change.
- **A failed action at a non-text-byte path, on the console's error stream** (`CONTENT.md` RN-35, § Grammar and mechanics *A path the tracker prints*, § Message patterns *Terminal messages*; SDD § 4 OB-3; FDR R-107). When an action fails with an `OSError` whose text holds the path `os.fsdecode(b'/tmp/caf\xe9')`, the tracker writes two lines to the error stream of the console it was started from, and writing them raises nothing:
  1. the action's plain sentence first. It names no path, so it holds neither `caf` nor `\xe9`;
  2. then the error's kind and its text exactly as the system reported it, with the path in it as `\udce9`. The line does not hold `\xe9`.

  "The console's error stream" is the stream the tracker writes to when started from a console. It is not a capture that refuses what that stream would write (Locked Answers, Gap 1).
- **A test is added and defines no stand-in of its own** (SDD § 4 TS-6; NFDR QC-64). The change adds no class under `products/tracker17/tests/` that stands in for the object that saves or for the clock. A class stands in when it defines `save` or `now`, or when its base is a class the test-support module defines. QC-64's own walk lands with the change that moves the stand-ins already there (NFDR RN-65). This change adds none to the ones that change must move.
- **The test hands in what it needs** (SDD § 4 TS-2). It makes the action fail through what it hands the part under test, and it patches no name inside that part.
- **The test module names what it checks** (SDD § 4 TS-3, TS-4). The module that holds the new test names the requirements or acceptance criteria it checks. Every requirement identifier it names is in `products/tracker17/docs/SRS.md`.
- **The tree passes the format and lint gates** (NFDR QC-62). `ruff format --check .` and `ruff check .`, run in the product directory `project.md` `Product path:` names, both exit 0 with the new test in the tree.
- **If production code changes, the failure is still reported from one place** (SDD § 4 OB-3; NFDR QC-45, QC-56, QC-57). Any fix stays in the one catch-and-report site in `web`, which writes the action and the error to the console. Outside `tests/` and `.behave/`, only `main.py` and that one site in `web` write to the console, and no page shows error text from Python.

---

## Structural Goal

- A test under `products/tracker17/tests/` pins the third invariant. Which layer and module it sits in is development-design's decision.
- **It is a real guard.** The walker changes the reporter so it rewrites the path to `\xe9`, sees the new test fail, reverts the change, and records all three in the unit's report.
- **It was absent, and now it is there.** `git grep -n 'report_failure\|Could not save' -- products/tracker17/tests` prints nothing at the base commit and prints the new test after the change. The product's own sentences hold neither string (Verified Claims), so the test matches only by naming one of them itself.
- **Production code changes only if the new test shows the write raises, or shows the path rewritten, on the console's error stream.** At the base it shows neither (Verified Claims), so the change is expected to be the test alone.

---

## Verified Claims

| Claim | Verified by | What came back |
|---|---|---|
| The reporter writes the sentence, then `<kind>: <text>`, to the error stream | Read `web/routes.py:1308-1332` at `<a commit not in the public history>` (`_guarded` catches any `Exception` and calls `_report_failure`; that writes `f"{message}\n"`, then `f"{kind}: {text}\n"`, to `sys.stderr`) | Holds |
| On the console's error stream the path prints as `\udce9`, never `\xe9`, and the write raises nothing | Ran `Site._report_failure("Could not save.", err)` in a Python started by `uv run --locked --project .` in the product worktree at `<a commit not in the public history>`, its standard error going to a file (the real `sys.stderr` as Python opens it, not a capture). Ran with `PYTHONIOENCODING` unset and set to `ascii`, for two errors: `OSError(92, 'Illegal byte sequence', path)` and `OSError(f"cannot write {path}")`, with `path = os.fsdecode(b'/tmp/caf\xe9')` | Exit 0 and returned in all four runs. Bytes on the stream: `Could not save.\n`, then `OSError: [Errno 92] Illegal byte sequence: '/tmp/caf\udce9'\n` or `OSError: cannot write /tmp/caf\udce9\n`. No `\xe9` in either |
| A capture that encodes the line strictly is a different stream | The same two errors under pytest's `capsys`, in a scratch test outside the tree, at `<a commit not in the public history>` | Filename form passed. Message form raised `UnicodeEncodeError: 'utf-8' codec can't encode character '\udce9' ... surrogates not allowed` at `web/routes.py:1332`. That verdict is the capture's, not the tracker's (Locked Answers, Gap 1) |
| No action's plain sentence names a path | Read the 13 `_guarded` call sites in `web/routes.py` at `<a commit not in the public history>` | Each sentence names the action and what the operator typed or chose (a name, a title, a status), and none names a location or path. A sentence holds `caf` only if the name the test types holds it |
| No test holds this today, and the grep prints nothing at the base | `git grep -n 'report_failure\|Could not save' -- products/tracker17/tests` at `<a commit not in the public history>` | No output, exit 1 |
| `Could not save` is not a product sentence | `git grep -n 'Could not save' -- products/tracker17` at `<a commit not in the public history>` | One hit only, in `docs/trail/content/cycle-20.md:40`, where it is an example. No code or test holds it |
| `web` exports the seven names the second invariant lists | Read `web/__init__.py` at `<a commit not in the public history>` | `__all__` holds exactly those seven |
| Both suites pass at the base | `uv run --locked --project products/tracker17 pytest products/tracker17/tests/` and `… products/tracker17/tests/e2e/`, in the instance worktree at `<a commit not in the public history>` | `3272 passed, 2 skipped`, exit 0; `122 passed`, exit 0 |
| QC-62's format and lint pass at the base | `ruff format --check .` and `ruff check .` through `uv run --locked --project .` in the product worktree at `<a commit not in the public history>` | `344 files already formatted`, exit 0; `All checks passed!`, exit 0 |
| QC-64 starts unmet and its walk lands with another change | Read NFDR QC-64 and RN-65 at `<a commit not in the public history>`; listed classes ending in `Saver` under `tests/` | NFDR: "The entry starts unmet", and "Until a change moves those fakes and writes the suites, QC-64's walk fails, so it lands with that change". No `tests/fakes.py` exists. Stand-ins such as `FailingSaver` sit in `tests/integration/test_task_tracker.py:80` and `test_comment_tracker.py:102` |

---

## Out of Scope

- A character that is valid text but that the terminal's own encoding cannot write, and a folder whose name really holds a backslash, an x and two hex digits: `CONTENT.md` RN-33's "Not covered", and RN-35's "keeping the write of that line from raising on a character the terminal can't encode".
- The tracker's own path form (`\xe9`) on the ready line, the unreadable-data line and the unreadable-data page: already landed, and they stay as they are.
- Any document: `CONTENT.md` already settles the line, and no product document is edited.
- The page a failed action answers with: unchanged.
- The stand-ins for the saver and the clock that already sit in other test modules: they stay where they are. Moving them into one test-support module, and writing the contract suites, is the change QC-64's walk lands with (NFDR RN-65). That walk is not this change's.
- Any production change beyond the fix the Structural Goal allows.

---

## Locked Answers (the divergence record — self-review 2026-11-13)

- **Gap 1 — which error stream:** "the error stream" in the request, and its "only if the new test shows the write raises", mean the stream the tracker writes to when started from a console, as the third invariant says. A capture that refuses what that stream writes does not count. — A capture that encodes strictly raised on the message form (Verified Claims), while the console's stream wrote `\udce9` and raised nothing in every run. Reading the capture's verdict as the tracker's would set off the request's production fix for a fault in the capture alone.
- **Gap 2 — (e) the records' checks on a new test:** SDD § 4 TS-2, TS-3 and TS-4, TS-6 with NFDR QC-64, and NFDR QC-62 are stated as Invariants, though the request names none of them. — Each binds every test the product adds, and the request adds one. QC-64 binds only so far as this change adds no stand-in: the record lands its walk with the change that moves the existing ones.
- **Gap 3 — (e) the records' checks on a conditional fix:** SDD § 4 OB-3 and NFDR QC-45, QC-56 and QC-57 are stated as an Invariant on any production change. — The request allows a fix to the reporter. These records fix where a failure is caught and reported and where the console is written, and a fix must keep them.
