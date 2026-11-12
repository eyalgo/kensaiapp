# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-12
- **Sources re-read:** None outside this repository. No answer rests on a vendor's or a platform's
  behaviour: Ruff's reach over `.behave/` was measured by running it, not taken from its
  documentation. Read in this repository at `28d68f4f6`: the companion whole; `nfdr.md` header, § 1,
  § 3, § 9 and § 10 whole, and QC-35, QC-37, QC-39, QC-59, QC-61 and QC-62; `adr/README.md` and
  ADR-0001 whole; `SDD.md` header, § 3 (parts, units, seams, direction, the four layers), § 4 TS-1 to
  TS-6, § 9 TO-10, RN-76 and RN-77; `<CORE>/doctrine/engineering/arch_defaults.md` § The four layers;
  `testing_doctrine.md` § A fake is verified against its port's contract, § A test reads nothing of
  the machine it runs on, and its layer table; `testing_python.md` § 2's fakes bullet. Under the
  product root: `application/contracts.py` whole; `main.py`'s `SystemClock`; `tests/conftest.py` at
  its docstring and its dot-folder skip (`:142`); the test names in `tests/architecture/test_shapes.py`;
  `.behave/README.md`, `.behave/pyproject.toml`, `.behave/.gitignore`, the three `.feature` files'
  heads, and every import line under `.behave/features/`. Commands, from the product root:
  `grep -rnE '^\s*class \w*(Clock|Saver)\b' tests --include='*.py' | grep -v /e2e/` (60, as the item
  says); `grep -rnE '^\s+def (save|now)\(' tests --include='*.py'` (69 definitions in 26 modules, four
  of them in `tests/e2e/`); and, in a disposable clone at `28d68f4f6`, the product's own
  `ruff check --no-cache` and `ruff format --no-cache --check` over `.behave` and over `.` (all pass).
  No test suite was run.

## Items worked

### 2.1 — Once the SDD names the four layers and the verified fakes, § 1.2 names the layer each clause binds and a new entry binds one fake and one contract suite per port

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft holds. The item waited on the SDD, and the SDD has now folded its answer:
  version 20, Settled, with § 3's four-layer paragraph, § 4 TS-6 (one fake and one contract suite per
  contract) and § 9 TO-10 (the ports stay in `application`). The layer mapping the draft names is the
  one § 3 now states, word for word. The doctrine sections the draft cites say what it says they say:
  `testing_doctrine.md` § A fake is verified against its port's contract files both suite runs at
  layer 2, and `testing_python.md` § 2 puts the fakes in a test-support module "such as
  `tests/fakes.py`". I confirmed it and added six things, each from a failure path the draft does not
  reach.
  1. **Trace (stale).** The draft traces the new entry to SDD § 4 TS-1 and TS-2. TS-6 did not exist
     when the draft was written, and it is now the SDD's own statement of the rule, so the entry
     traces to TS-6 and the layer names trace to § 3's four layers. QC-1 also traces to § 9 TO-10. A
     reader who comes from the Python guide looks for a `ports/` folder, and QC-1 is where that
     reader meets the five parts.
  2. **Where it sits, and a third contract (stale).** The entry goes in § 1.4, beside QC-28 and QC-29.
     Those two say the clock and the saver are handed in, and this one says the stand-ins are
     verified. It names "each contract `application/contracts.py` states", not "the two", so a third
     contract is bound the day it lands. For the same reason its walk reads the method names off those
     `Protocol` classes (`save` and `now` today) and fails when it reads none. That is the rule QC-11's
     fourth check already follows for TS-3's words.
  3. **A subclass escapes a method-name walk (the case the happy path does not reach).** The test
     modules already subclass fakes: `OnlySaves(RecordingSaver)` twice in
     `tests/integration/test_routes.py`, `_ReadingSaver(RecordingSaver)` in `test_task_tracker.py`,
     and `ReadCountingClock(MovableClock)` in `test_comment_routes.py`. Once the fakes move into one
     module, a test-local subclass that changes behaviour without overriding `save` or `now` is a
     stand-in of the test's own, which TS-6 forbids, and the draft's walk would not see it. So the
     walk also fails on a class outside the test-support module whose base is a class that module
     defines.
  4. **Absence passes (empty).** As drafted, the walk only finds a class in the wrong place, and the
     suites are checked only by passing. A deleted suite, or a test-support module that never got
     written, then passes. § 9 already makes every layer-6 walk fail when it finds nothing. This entry
     follows the same rule: its walk fails when the test-support module is missing, holds no fake for
     a contract, or a contract has no suite run against both the real implementation and the fake.
  5. **§ 9's layer-2 row.** It reads "`persistence` against real files". The clock suite's real run
     hands it `main.SystemClock`, which is not persistence and touches no file, so the row names the
     contract suites too. The real run reads the machine's clock. That is allowed:
     `testing_doctrine.md` § A test reads nothing of the machine it runs on forbids seven things, and
     the clock is not one of them.
  6. **`errors.py` has no layer.** The draft names a layer for QC-13 to QC-17 and says nothing about
     QC-18. SDD § 3's four-layer paragraph places `errors.py` in no layer, so QC-18 names none. If the
     records gave it one, they would be deciding the design. I nearly raised this on the SDD, because
     the doctrine's table lets `domain` import only `domain`, `ports` and the standard library, and
     `domain/` imports `errors`. I did not raise it because no rule moves either way: QC-18 and § 3's
     "Every part may import `errors.py`" already settle every import. A change that needs `errors.py`'s
     layer to decide an import would tip it.

  **The count understates, and the rule is wider than the count.** The draft's command leaves out
  `tests/e2e/`. TS-6 and the draft's own walk over `tests/` both reach it, and it holds four more clock
  fakes: `FixedClock` in `test_sorting.py`, `test_summary.py` and `test_filters.py`, and `SeedClock` in
  `test_delete_project.py`. So the rule moves 64 classes across 26 modules, not 60 across 22. I report
  the supporting text and do not correct it.

  **No ADR is written, and the draft's reason for that is too small.** "No ADR moves" says that no
  existing record changes. It does not say whether the choice earns a new record. I tested that: TO-10
  is a real trade-off and would surprise a reader without context. What fails is the third test, "hard
  to reverse". ADR-0001 already fixes five parts and already says "A change that adds a sixth part …
  needs a new record that supersedes this one", and that sentence is the whole of what TO-10 says
  undoing would cost. Naming the layers moves no import rule (RN-76). So no new trade-off exists for a
  record to hold, and the decision log stays at sixteen records. This was the close call. § 3 also
  rules out an alternative ADR-0001 never names: putting `web`'s handler in `entrypoints`. I weighed
  that one too. Moving it later would be cheap, because § 3 keeps `web`'s narrower import rule whichever
  layer the handler is named in. What would tip this to a new record is an alternative that is
  expensive to reverse and that ADR-0001 does not already cover.

### 3.1 — QC-1 says no other top-level code part exists, and `.behave/` now holds Python at the root

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** The item proposes a correction ("A corrected QC-1 would name `.behave/` … beside `tests/`"),
  so I weighed it as a draft. It is a correction of a sentence that is now false, not a widening, so
  "not until it occurs" does not apply. The seat is mine: the edit lands in `nfdr.md`. On disk, the
  root holds `.behave/` with eight Python modules under `features/`, its own `pyproject.toml` and its
  own `uv.lock`. Its README says the folder carries its own Python setup and leaves the product's
  `pyproject.toml` and `uv.lock` as they were. So it is test code outside the package unit, and it is
  no part of the tracker. The correction stands as drafted, worded as allowed and not required
  ("may also hold"), so that a product without the folder still passes. **The addition is the test.**
  The words went false while the test passed because `SourceWalk._all` in `tests/conftest.py:142`
  skips every path piece that starts with a dot. If only the words are corrected, the next dot-folder
  holding code passes unseen in exactly the same way. So the corrected test skips `.venv/` and
  `.behave/` by name, as it already skips `tests/`, and fails on any other root folder that holds a
  Python module. I decided this together with 3.2 and 3.3, because their walks share that skip.
  Named skips are what make all three corrected entries agree with their tests.

### 3.2 — QC-19 says no module outside `tests/` imports a third-party module, and `.behave/`'s modules do

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** The item proposes "outside `tests/` and `.behave/`", so I weighed it as a draft. The
  draft holds. The imports are as the item says: `environment.py:3` imports `behave.runner`,
  `server_way_in.py:5` imports `httpx`, `browser_way_in.py:6` imports `playwright`, and every step
  file imports `behave`. **The addition:** the second clause, "no module outside `tests/` imports from
  `tests/`", keeps binding `.behave/`, and it holds there today. The walk skips `.behave/` by name,
  per 3.1, so the words and the test agree. Exempting the folder from QC-19 leaves its third-party set
  outside every check unless QC-39 picks it up, and QC-39 does not. That gap is raised as § 2.2 on
  this companion, not folded into this slot, because it is a different entry with a different
  boundary (B-4).

### 3.3 — QC-43 says no module outside `web/` imports `http.server`, and a `.behave/` step file does

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** The item proposes exempting `.behave/` from the import clause. The draft answers a smaller
  question than the entry asks. `page_steps.py:3` imports `http.server`, and that step also listens,
  which falsifies QC-43's first sentence, "Only `web` opens a socket, and only to listen". Its server
  way in opens client connections through `httpx`, which falsifies the same sentence again. The
  exemption therefore covers the whole entry. **And `tests/` breaks QC-43's words already.** Ten
  test modules import `socket`, `http.server` or `http.client` (eight under `tests/integration/`, and
  `tests/e2e/conftest.py` and `test_start_command.py`). The walk in
  `tests/architecture/test_imports.py` (`WEB_ONLY`, `BANNED_EVERYWHERE`) is silent only because the
  source walk skips `tests/`. So the corrected entry opens "Outside `tests/` and `.behave/`:", and
  every clause after it stands under that. Both skips are by name, per 3.1. QC-35, "The running
  tracker opens no outbound connection", is about the tracker and does not move.

## Left for the owner

None this run.

## Skipped

None this run.

## Raised on this document

### 2.2 — QC-39 says one lock file fixes every test dependency, and § 9 gives layer 7 no tool, while `.behave/` pins its own set and is Behave

- **What the document is owed:** QC-39 covers `.behave/`'s own pinned set and lock file and holds
  them to the same checks. § 9's layer-7 row names Behave and `.behave/features/`.
- **Why it is worth a cycle:** "A fact in it is now false". QC-39 says "one committed lock file", and
  the product holds two: `uv.lock` and `.behave/uv.lock`. `behave` and `httpx` are test dependencies
  that the root `pyproject.toml` does not declare. § 9's layer 7 is `testing_doctrine.md`'s "feature
  scenarios", in the BDD style, and its row reads "—" while that tool is committed at the product root.
  I read every other `nfdr.md` entry scoped to the whole product against `.behave/`. QC-37, QC-45,
  QC-59 and QC-61 hold there. QC-62 holds too: Ruff's lint and format check both pass over `.behave`
  in a disposable clone at `28d68f4f6`. § 9's "Layer 7 has no producer" holds, because
  `development_flow.md` names no step that writes scenarios. Only QC-39 and the layer-7 row are false.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/nfdr.md** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
