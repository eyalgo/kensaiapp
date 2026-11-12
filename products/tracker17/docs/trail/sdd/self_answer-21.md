# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md (version 19)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-12
- **Sources re-read:** None — no answer this run gave rests on a source outside this repository. Read
  in this repository at `<a commit not in the public history>`: the companion whole; `SDD.md` whole, §§ 1 to 12, the header, the
  Open Questions and RN-72 to RN-75; `<CORE>/doctrine/engineering/arch_defaults.md` (version 2.1.0)
  § The four layers at the three places the item cites, lines 85–87, 89–94 and 111, each saying what
  the item says it says; `<CORE>/doctrine/engineering/arch_defaults_python.md` § Repository typing;
  `<CORE>/doctrine/engineering/languages/python/conventions.md` § The four layers bullet and § A port
  is a plain class; `<CORE>/doctrine/engineering/testing_doctrine.md` § A unit test hands its unit
  fakes and § A fake is verified against its port's contract; `<CORE>/doctrine/engineering/testing_python.md`
  § 2's fakes bullet; `products/tracker17/docs/nfdr.md` §§ 1.1 to 1.4, § 9, § 10 and RN-54;
  `products/tracker17/docs/adr/0001-*.md` to its Decision; `products/tracker17/docs/architecture_open_issues.md`
  whole; `products/tracker17/docs/SRS.md` NFR-11 and C-6; `products/tracker17/docs/fdr.md` searched
  for "fake", "contract suite" and "four layer", which it does not name; under the product root,
  `application/contracts.py`, `application/__init__.py`, `main.py`, `persistence/__init__.py`,
  `persistence/saved_data.py` and `persistence/location_use.py` at their heads, `web/__init__.py`,
  `web/listener.py` at its head, `tests/conftest.py`, `tests/architecture/test_imports.py` and
  `tests/architecture/test_reach.py` at its head; `system/projects/tracker17/project.md`,
  `finish_line.md` and `journey/shukuba/`, the last as an input for the commit's directional alone
  — no station is open, so the commit resolves against the finish line; and
  `system/doctrine/writing_bar.md` § 1.

## Items worked

### 5.1 — The design does not yet say whether it takes the four layers and verified fakes

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** confirmed with addition
- **Why:** The item carries a lean — "take the shape: § 3 already holds the separation, so the cost
  is naming it plus two contract suites" — so it was weighed as a draft, as RN-72 and RN-74 weighed
  the two downstream items before it. The draft's conclusion holds and its reason holds: every
  dependency rule the four layers state is already true of tracker17 and verified by a layer-6 test
  (`tests/architecture/test_imports.py`, QC-13 to QC-19; `tests/architecture/test_reach.py`, QC-20,
  QC-42 to QC-45), and `arch_defaults.md` § The four layers binds a product "only once that SDD has
  chosen it", so the choice is the document's to make and costs the code nothing on the dependency
  side. Four additions, each a case the lean did not state. First, the mapping the item asked for and
  did not draw: the `domain` layer is `domain/` and `application/` together, because the doctrine's
  table puts "the flow § Application Layer orchestrates" inside `domain`; the `ports` are the two
  contracts in `application` (`application/contracts.py`, `Saver` and `Clock`, both `typing.Protocol`
  as `arch_defaults_python.md` § Repository typing spells a port, and QC-3 already checks that nothing
  inherits them); the `adapters` are `persistence/` (`SavedData`), the real clock (`main.py`,
  `SystemClock`, which no part imports under QC-2) and `web/`; `main.py` is `entrypoints`. Second,
  `web` is an adapter whole, routes included, not an entrypoint: it is the one part that touches the
  socket (QC-43, `web/listener.py` imports `http.server`), and it is handed the `application` object
  it calls (SM-6, `main.py` `listen(address, tracker)`), which is the doctrine's "handed what it
  calls". The doctrine seats a logic-free inbound handler in `entrypoints`, where it may import
  everything; tracker17 keeps its handler in `web` under QC-16, which forbids `domain` and
  `persistence`. That is narrower, and a lower layer may tighten a rule, so it stays and the answer
  says so. Third, the fakes are the real cost, and the lean undercounted it as "two contract suites".
  `testing_doctrine.md` § A fake is verified against its port's contract says a port has one fake,
  written once in a test-support module and "never redefined in a test". From the product root,
  `grep -rnE '^\s*class \w*(Clock|Saver)\b' tests --include='*.py' | grep -v /e2e/` listed 60 fake
  clock and saver classes across 22 test modules on 2026-11-12 — `FixedClock` in six modules,
  `RecordingSaver` in nine, `FailingSaver` in seven — and no contract suite exists. Taking the shape
  means two fakes in one module, two suites, and 22 modules moving to the shared fakes; that is a seed,
  which the item already says `seeds-from-product-docs` cuts, and it is a reduction in what the reader
  reads, not an addition, so § 1's bar is served rather than spent. Fourth, where tracker17's form
  departs from the Python guide: `conventions.md` spells a port as "an abstraction in the `ports`
  package", and tracker17's sit in `application`. `arch_defaults.md` lets `domain` and `ports` share a
  unit ("elsewhere each may be its own" is permission, not a requirement), and a sixth top-level part
  would move § 3, QC-1 and ADR-0001 — a re-cut under § 10 and a superseding ADR — for no change in the
  rule. The answer records the departure and its reason, so a reader meeting the guide's spelling does
  not take the layout for an oversight. This was the point closest to a different verdict: had the
  guide's `ports` package read as a requirement rather than a spelling, the shape would be taken by
  restructuring and the cost would be an ADR, not words. On the widening rule: the item sits under
  the `Raised from downstream` heading and asks the document to state a requirement it does not state
  now, so it widens, and it cites its occurrence — the two contracts `application` states, which are
  present in the product as it stands (`application/contracts.py`), and the parts `main` builds. The
  fakes rule attaches to a port, so the ports' occurrence is its occurrence; the 60 classes above are
  my own check, not the item's citation, and the verdict does not rest on them. Check 3: the answer
  contradicts nothing settled — § 2's "one contract toward the saved data and one toward the clock" is
  the two ports, ADR-0001's five parts and QC-1 stand, and TS-2 already says the clock and the saver are
  handed in. Check 4: the Saver port has one operation, `save(state) -> None`, raising on failure, so
  its contract suite is small — the fake records what it received and can be told to fail; the real
  one writes inside `tmp_path` — and that smallness is the port's shape, not a hole. The Clock
  contract is `now()` returning an aware UTC instant, assertable against `SystemClock` and the fake
  alike. The item's three doctrine line citations were read at `arch_defaults.md` version 2.1.0 and
  hold. The NFDR's side — the layer names on QC-13 to QC-17 and a new entry binding the fakes rule —
  is the Principal Architect's and rides on `products/tracker17/docs/architecture_open_issues.md`
  § 2.1, committed at `1586fb6f3` before this slot was written; NFDR RN-54 is the precedent for an SDD
  change reaching the records through an item on that companion. The header's *Inputs read* line
  says no architecture companion sits beside the NFDR, which stopped being true when the PM opened
  one at `9d0edf12e` today; three prior folds caught that line up without an item (RN-60, RN-66,
  RN-70), so no item is raised for it here.

## Left for the owner

None this run.

## Skipped

None this run. §§ 1 to 4 each read "None.", and § 5.1 is the companion's only item.

## Companions opened

- **products/tracker17/docs/architecture_open_issues.md** — **appended** — companion to `adr/` and
  `nfdr.md`, landed in commit `1586fb6f3`

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
- **products/tracker17/docs/architecture_open_issues.md** — `<CORE>/launchers/companion-self-answer/launcher.sh tracker17 architecture`
