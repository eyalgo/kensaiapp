# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md`
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-12
- **Sources re-read:** None outside this repository. No answer rests on a vendor's or a platform's
  stated behaviour. uv's lock check over the scenario folder was measured by running it, not taken
  from uv's documentation. Read in this repository at `2bbbf8155`: the companion whole; `nfdr.md`
  whole, version 25; `adr/README.md`, and ADR-0013's Decision and `## Binds`; `SDD.md` § 4 RT-4
  (`:335-361`), § 12's "the § 4 statement wins" (`:1726`) and RN-77; `SRS.md` C-7 and C-8;
  `trail/architecture/self_answer-27.md` and the fold commit `2bbbf8155`; the project card's
  `Test command:` and `Behave:` lines; `<CORE>/doctrine/engineering/testing_doctrine.md`'s layer
  table; `testing_python.md` § Layer 7; `<CORE>/doctrine/flow/development_flow.md`, searched for
  "behave" and "scenario" (no match); `<CORE>/doctrine/setup/kensaiapp_structure.md` on the Behave
  starter and the start-of-run check; the SDD companion template. Under the product root:
  `.behave/pyproject.toml`, `.behave/README.md`, `.behave/.gitignore`, `.behave/uv.lock`'s package
  names, the three `.feature` files, every import, class, write and print under `.behave/features/`,
  the root `pyproject.toml`, `tests/architecture/test_pins.py` whole, and `application/contracts.py`'s
  classes. Under `tests/`, by a parse of each module's imports, calls and class bases: modules that import
  `main` (8), classes that derive straight from a built-in exception (4), modules that write files
  (15), and modules that call `print` or reach `sys.stdout` or `sys.stderr` (2). A first `grep`
  gave 9, 16 and 6 for the imports, writes and console, because it
  matched code held in strings: scripts the tests hand to child processes, and the fixtures the
  reach test feeds its walks. In a disposable clone at `2bbbf8155`, with uv 0.11.14: `uv lock --check
  --offline` at the product root and `uv lock --check --offline --project .behave` both exited 0,
  and the second exited 1 with `httpx` moved to 0.28.0. No test suite was run.

## Items worked

### 2.2 — QC-39 says one lock file fixes every test dependency, and § 9 gives layer 7 no tool, while `.behave/` pins its own set and is Behave

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft holds on its facts, and I checked each on disk. The root `pyproject.toml`
  declares `mypy`, `playwright`, `pytest` and `ruff` and no `behave` or `httpx`. `.behave/pyproject.toml`
  pins `behave==1.3.3`, `httpx==0.28.1` and `playwright==1.63.0`, and `.behave/uv.lock` locks them.
  The layer-7 row reads "—" in both columns. The draft has a stronger reason than the one it gives.
  § 9's own Behave line reads `behave` (RN-67) while its layer-7 row names no tool, so two lines of
  one section disagree. And `testing_python.md` § Layer 7 says "A Python product writing them today
  records its runner in `docs/nfdr.md` § 9", which makes the row this seat's to fill. "Layer 7 has
  no producer" holds: `development_flow.md` has no match for "behave" or "scenario". The seat is
  mine, because both edits land in `nfdr.md`. I confirmed the draft and added five things.
  1. **QC-40 follows (an incomplete argument).** The draft's reason is that B-4 guards third-party
     code "whichever folder pins it". QC-40 is where B-4's advisory bar lives, and it says "the lock
     file of QC-39" and "the packages `uv.lock` fixes". Once QC-39 names two lock files, the first
     phrase no longer says which file, and the second leaves `behave`, `httpx` and what they pull in
     outside the 30-day window and the feed check. So both phrases name both files, and the browser
     clause reads "each pinned browser-driving library". Both pins are `playwright==1.63.0` today, so
     there is one build, 153.0.8010.12. That is the build RN-33's dated exception covered until the
     end of 2026-11-07. Its expiry is QC-40's existing state and this answer does not change it, but
     the scenario folder's browser is now inside it too.
  2. **The entry starts unmet in its test (the absent case).** `test_pins.py` builds every path from
     the product root, `pyproject.toml` and `uv.lock`, and reads nothing under `.behave/`. Its
     `declared_dependencies` already reads `[project] dependencies`, which is where the scenario
     folder declares its three. So the same two checks run over the second manifest with no new
     parser. They fail when `.behave/` exists and holds no manifest or no lock. They read nothing
     when the folder is absent, because QC-1 says the root "may also hold" it.
  3. **The command, and what the suite really gates.** `uv lock --check --project .behave`, typed
     from the product root, exited 0 offline in a clone at `2bbbf8155`, as the root's check did, and
     exited 1 with one pin moved. The card's `Test command:` runs `uv run --locked --project
     products/tracker17`, which refuses a stale root lock and never looks inside `.behave/`. So at
     the suite the scenario folder is held only by the pins test. That test checks each declared pin
     is locked at its version, and it does not see a lock still carrying a package the manifest
     dropped. The full check runs at the `development-design` review of a change to
     `.behave/pyproject.toml` or `.behave/uv.lock`, and QC-39's tail says so. Saying "gated at
     suite" for it would be false. That is the named uncovered case: between such reviews, a lock
     drifting from its manifest in a way that keeps every pin is caught by nothing.
  4. **No record moves, and the draft gives no reason.** I ran the significance test. ADR-0013's
     Decision says the test dependencies are "locked … in one committed file, `uv.lock`". That was
     true of the suite when written and still is. The suite's environment has not moved, and
     `.behave/` is a second environment made by uv the same way. Folding its three pins into the
     root `dev` group is one change, so the choice is not hard to reverse. And this product did not
     make it (the dependence test): the folder is core's Behave starter, written whole by the
     start-of-run check, and its README says it leaves the product's own `pyproject.toml` and
     `uv.lock` as they were. A later starter does not overwrite a committed `.behave/`, so the pins
     move only in this product's copy. So the narrowing goes in a Review Note, as RN-29 did for
     ADR-0009, and QC-39's trace tag names it, because ADR-0013's `## Binds` names QC-39.
  5. **The SDD says the same false thing (check 3).** QC-39 traces to SDD § 4 RT-4, which reads
     "They are declared in `pyproject.toml`, in its `dev` dependency group, and locked … in one
     committed file, `uv.lock`" (`SDD.md:335-337`). SDD § 12 says that where a § 4 condition and an
     entry disagree, "the § 4 statement wins". A widened QC-39 read against an unwidened RT-4 is
     overruled by the rule both documents share. The edit is RT-4's, and RT-4 is the CTO's. I opened
     `products/tracker17/docs/SDD_open_issues.md` with one item, § 2.1, for that seat. QC-39's
     change lands here and RT-4's lands there, whichever fold runs first, as companion § 2.1 handled
     TS-6 in the round before this one.

  **The layer-7 row says the scenarios run at no gate (the stale case).** The card's `Test command:`
  runs pytest twice and nothing in `.behave/`, and no stage runs `uv run --locked behave`. So a
  failing scenario fails nothing. The row says so, beside the draft's "test nothing of tracker17",
  so that a reader of the row does not take the named tool for a gated one. What decides whether a
  scenario becomes a gate is the card's and the flow's, not this document's.

  I decided this with 2.3. That item exempts `.behave/` from seven rules about the tracker's code,
  and this one binds it to the rule about test dependencies. The two agree: QC-1 calls the folder
  test code, and test code has dependencies and is no part of the tracker. The close call was
  (3). I nearly gave `uv lock --check --project .behave` a suite gate by having the pins test run
  uv. I did not, because `testing_doctrine.md` § A test reads nothing of the machine it runs on
  forbids a test depending on "the system's own tools", and the pins test already holds the half
  that C-8 asks for.

### 2.3 — Seven entries that say "outside `tests/`" still reach `.behave/` in their words, and the walk behind them now skips it by name

- **Bucket:** 2. Choices to confirm — the Principal Architect drafted a best-effort answer; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft's choice holds. The seven take the scope of test code, `tests/` and
  `.behave/`, and no walk of `.behave/` is added. The seat is mine, because every edit lands in
  `nfdr.md`. I checked the draft's facts. `.behave/features/browser_way_in.py:17` defines
  `ChromiumMissing(AssertionError)`, so QC-4's words are false there today, as the item says. The
  other six hold there. Nothing under `.behave/features/` imports `pickle`, `marshal`, `shelve` or
  `main`, or calls `eval` or `exec`. Its one write is `page_steps.py:28`'s `self.wfile.write`, which
  writes to a socket and not to a file. Its one `print` sits inside a string handed to a subprocess
  (`command_steps.py:12`). It reads no `sys.platform`, `os.name` or `platform`, and names no
  contract as a base. I weighed the override, a walk of `.behave/` per entry, and it fails on QC-4.
  The walk would make `ChromiumMissing` derive from tracker17's `errors.py`, and `.behave/` cannot
  import that file. It runs in its own environment outside the package unit (QC-1), and it is
  core's starter, written to run the same whatever the product's language. So the override asks for
  an import QC-1 rules out. I confirmed the draft and added three things.
  1. **The draft answers a smaller question than the item asks.** It gives two forms: change
     "outside `tests/`" to "outside `tests/` and `.behave/`", or name `.behave/` where an entry names
     what it does not bind. Only QC-37 and QC-61 have either in their words. QC-2, QC-3, QC-4, QC-42
     and QC-45 name no folder in their words, and their scope sits only in their tails ("outside
     `tests/`"). As drafted, those five have nothing to rewrite, and their words go on reaching
     `.behave/`. So each opens with the scope in its words, as QC-43 now does: "Outside `tests/` and
     `.behave/`: …".
  2. **Four of those five are already false in `tests/` (the case the item does not reach).** This
     is what companion § 3.3 found for QC-43 in cycle 23. Counted by a parse of each module under
     `tests/`: 8 import `main`, against QC-2's "No module imports `main`"; 4 classes derive straight
     from `Exception` or `ValueError`, against QC-4's "every other exception class in the product"
     (`tests/timed_run.py:389`, `tests/unit/test_start_lifecycle.py:34`,
     `tests/integration/test_location_use.py:307`, `tests/integration/test_listener.py:263`); 15
     write files, against QC-42's "Only `persistence` opens a file for writing"; and 2 call `print`
     or reach `sys.stdout` or `sys.stderr`, against QC-45's "Only `main.py`, and one site in `web/`"
     (`tests/timed_run.py` and `tests/unit/test_start_lifecycle.py`). QC-3 holds in `tests/`. Its
     one contract base there is a string fixture in `tests/architecture/test_shapes.py:227`. So the
     scoped words correct both folders, and the item's own heading undercounts what was false. There
     is also a consequence inside this document. QC-64's clock suite hands in `main.SystemClock` for
     its real run, so a test must import `main`, and an unscoped QC-2 forbids it.
  3. **Each tail names the walk it rests on.** Each tail says the source walk skips `tests/` and
     `.behave/` by name (QC-1). QC-42's walk runs "outside `persistence/`, `tests/` and
     `.behave/`", and QC-45's fails "elsewhere outside `tests/` and `.behave/`".

  **Considered and not added.** QC-11 says "Every test module names the requirements or acceptance
  criteria it checks", and QC-28 says "no test patches a name inside a product module". Both reach
  `.behave/` as test code, and no walk reads it. QC-28 holds: nothing there patches. QC-11 holds
  only because the starter's scenarios check no requirement, so its modules have none to name. The
  day a scenario tests tracker17, QC-11's words reach a module the pointer test does not read. That
  is the stale case this answer does not cover. I did not add it, because no such scenario exists,
  and binding one would widen the entry with no occurrence behind it. QC-64's walk is scoped to
  `tests/`, and `.behave/` defines no class that stands in for a contract.

  I decided this with 2.2. This item exempts `.behave/` from rules about the tracker's code, and
  2.2 binds it to the rule about test dependencies. The two agree, because QC-1 calls the folder
  test code and no part of the tracker.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

- **products/tracker17/docs/SDD_open_issues.md** — **opened** — companion to `SDD.md`, landed in commit `082e1eb4a`

## Launchers owed

- **products/tracker17/docs/nfdr.md** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/companion-self-answer/launcher.sh tracker17 SDD`
