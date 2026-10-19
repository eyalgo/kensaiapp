# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-07
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. The
  HTML-standard claims `SDD.md` § 4 RT-10 and § 11 R-2 carry were not re-read, because no answer
  leans on them: § 5.3 rests on what the product's own tests observe and on `web/routes.py:84`.
  What was read instead, all in-repo: `SDD.md` whole; `SRS.md` FR-2, FR-3, NFR-9, AC-20; `nfdr.md`
  QC-11; `architecture_open_issues.md` § 3.1; the open station
  `system/projects/tracker17/journey/shukuba/2026-10-07_a-project-that-stays.md`; `main.py`,
  `domain/text.py`, `web/routes.py:84`, `tests/architecture/test_trace.py`, `tests/unit/test_address.py`,
  `tests/e2e/conftest.py`, `tests/e2e/test_first_project.py:94-145`; and
  `CONTENT.md:27,246,274`. The non-browser suites were run in a disposable copy of HEAD
  (`git archive HEAD products/tracker17`): 183 passed, the one failure being
  `test_data_is_ignored_by_version_control`, which runs `git check-ignore` and cannot pass outside a
  repository — a property of the copy, not the product. `tests/architecture/test_trace.py` passed
  7 of 7 there. The end-to-end suite could not be run on this machine (no Playwright installed);
  its green stands on `691edf98b` (9 passed, exit 0), and `git diff --stat 691edf98b HEAD --
  products/tracker17 ':!products/tracker17/docs'` printed nothing, so the code it ran against is the
  code on `main`.

The companion held three open items, all in § 5 and all `Seat: cto`, and the invocation listed none,
so this run worked all three. None widens the document: each corrects a statement the code has made
false or settles a question the code has answered, so § *A widening item waits until it occurs* does
not apply.

## Items worked

### 5.1 — § 4 TS-4 asks the pointer test to fail on every feature word with no module, which no slice before the last can pass

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** confirmed with addition
- **Why:** The proposed wording is taken, and one clause is added to it.

  *Seat (check 1).* The change is one sentence in `SDD.md` § 4 TS-4, a CTO part; it binds nobody
  outside the document, and there is no ground the owner holds that this run could not see.

  *The reasoning holds (check 2).* TS-3's table names eleven feature words (`SDD.md:433-443`);
  `domain/` holds one of them, `projects.py`; a test that fails on any word with no module fails
  until the eleventh slice lands, and a test that cannot pass for ten slices is not a test. The
  test as built checks `LANDED_FEATURE_WORDS = ["projects"]` (`test_trace.py:19`), which is the
  only passable reading, and TS-4 does not say it. The wording the PM proposes says it.

  *Nothing settled moves (check 3).* SRS NFR-9 asks that a reader reach a feature's code "by
  following what the documents and the code point to" — for "every Core Feature the operator uses",
  which before the last slice means the features that exist. RN-9 derives TS-3 and TS-4 from NFR-9
  and AC-5 and says nothing about timing. `nfdr.md` QC-11's *verified by* carries the same clause
  and is already raised as `architecture_open_issues.md` § 3.1, which points at this item; the
  Principal Architect reads the SDD when it folds, so no second touch on that companion is needed
  and none was made.

  *The failure path, and the addition (check 4).* The *stale* case: a slice lands `domain/tasks.py`
  and does not add `tasks` to the list. Nothing fails, and that feature's pointers go unchecked —
  the exact drift § 11 R-6 names TS-4 as the signal for. The proposal's "each slice that delivers a
  feature adds its word to the test" is an obligation with no enforcement; the added clause gives it
  one: the test also fails when a table word has its module but is not listed as landed. The test
  has the first direction today (`test_each_landed_feature_word_has_its_domain_module`) and not the
  reverse, verified by reading all seven tests in `test_trace.py`. So the fold leaves TS-4 stating
  one check the code is owed. That is the normal direction for a design document and the check is
  small; the open station, which "may take several change units", is where it lands, and the
  answer says so rather than hide it. I was close to a plain *confirmed*, to keep TS-4 and the test
  equal on the day of the fold; what tipped it is that R-6's whole response rests on TS-4's test
  catching stale pointers, and the forgotten-word path defeats it silently.

### 5.2 — The port of the fixed address is now chosen, and § Open Questions still asks for it

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** confirmed with addition
- **Why:** The open question is removed and the address is recorded in RT-5; the addition is that
  the whole address is recorded, not only the port.

  *Seat (check 1).* RT-5 and § Open Questions are CTO parts; a port on a loopback address commits
  nobody.

  *The reasoning holds (check 2).* `main.py:20` reads `ADDRESS = ("127.0.0.1", 8017)`;
  `tests/unit/test_address.py` asserts the host is loopback and `port == 8017`; the SDD's own
  § Open Questions said `first-project` "settles it when it writes the constant § 4 RT-5 names"
  (`SDD.md:1590-1591`). The constant is written. The item answers a smaller question than RT-5
  leaves open: RT-5 says "one loopback address" (`SDD.md:283`) and there is more than one, so
  recording `8017` alone would leave the host unstated while the code fixes it. The answer records
  `127.0.0.1:8017`.

  *Nothing settled moves (check 3).* `grep -n '8017\|port ' SRS.md PRD.md UXD.md` printed nothing
  bearing on it: no upstream document names a port, so the SDD recording one contradicts nothing.
  `CONTENT.md:246,274` show `127.0.0.1:8000`, and `CONTENT.md:27` says its examples "illustrate a
  rule. None of them specifies" — an example value, not a settled string, so no change is owed
  there and none was raised.

  *Failure paths (check 4).* *Stale*: a later change of port makes RT-5 false — but the port is one
  constant, pinned by a unit test, and a change to it is a change to the SDD first, which is the
  order this document already imposes on everything in § 4. *Concurrent*: TS-1 already has each
  end-to-end test start its tracker on a free port of its own (`tests/e2e/conftest.py`,
  `_free_port`), so recording the fixed port does not touch the tests.

### 5.3 — Two Chromium questions in § Open Questions are answered by the end-to-end tests that now pass

- **Bucket:** 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** confirmed with addition
- **Why:** Both edits are taken as proposed — the first open question goes, the second narrows to an
  element that is not a form control — and one sentence is added to how the SDD records the first.

  *Seat (check 1).* § Open Questions is a CTO part (`SDD.md:81`), and the edits commit nobody.

  *What the tests observe (check 2).* The item says the test at `test_first_project.py:108`
  "answers how Chromium counts a line break against `maxlength`". It does: the test fills the
  description with 4,000 characters holding fifty line breaks, presses one more and finds the value
  unchanged, submits, and reads the saved description equal to what was typed — so the field
  counted each line break as one, and the value reached the saved data whole. It does *not* answer
  the second half of the open question as written, "and sends it as CR LF": `web/routes.py:84`
  turns CR LF and a lone CR into LF before `application` sees the value, so a submission in either
  form saves the same bytes, and the test cannot tell them apart. That is the addition: the SDD
  closes the question because RT-10's design no longer turns on what Chromium sends — RT-10 already
  normalizes, and `tests/integration/test_routes.py:228` checks the normalization on
  `"a\r\nb\rc\nd"` — not because CR LF was observed. Written as the item proposes alone, a reader
  would take the removal as an observation that was never made. The focus test at `:94` observes
  what R-2 asks for a form control: focus lands in the name field and the reason is its accessible
  description. "Brings it into view" is not asserted, and for a form at the head of a first-run page
  it needs no assertion; the narrowed question keeps that clause for the non-control case, where it
  matters.

  *Nothing settled moves (check 3).* § 11 R-2 already places the three focus tests in "the first,
  second and fourth slices" (`SDD.md:1131-1132`), so narrowing the open question to the second and
  fourth is what R-2 says. RT-10's statements from the HTML standard stay as the standard's; this
  answer neither relies on nor re-reads them. The e2e green is `691edf98b` (9 passed, exit 0) and the
  product code has not moved since (Header).

  *Failure paths (check 4).* *Stale*: a Chromium release could change either behaviour; both tests
  run on every slice, and R-2 already names a focus test failing as the signal, so a regression
  surfaces where the SDD says it will. *Absent*: with Playwright missing on this machine the suite
  cannot be re-run here, which is why the answer rests on the recorded run and the empty diff, and
  says so.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
