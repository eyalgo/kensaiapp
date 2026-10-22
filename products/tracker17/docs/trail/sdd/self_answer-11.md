# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-21
- **Sources re-read:** None. The one item rests on this repository's own tests and records, read on
  disk: `SDD.md` whole, and § 4 EX-6, § 7, § 9 TO-2, § 11 R-2, § 12, RN-36, RN-41, RN-46 to RN-48,
  § Open Questions; the companion whole, its filled §§ 5.1 and 5.2 included;
  `tests/e2e/test_moves.py` (the four tests at lines 174, 208, 321 and 606, the parametrizations at
  296-321, `PINNED_BROWSER` at 452 and its assertion at 541); `tests/e2e/conftest.py:120-165` (the
  `browser` and `history_browser` fixtures); `pyproject.toml:14`; `tests/integration/test_start.py`
  (the README-heading reads); `nfdr.md` RN-15 and RN-33; `trail/architecture/cycle-11.md` § 3.1;
  `architecture_open_issues.md` whole; the seed `2026-10-07_status-moves`, its refine report
  `2026-10-20_history-after-confirm_report.md` and the closed station
  `shukuba/trail/2026-10-19_cancel-confirmation.md`; the unit's `code-integrity-report.md` (lines
  40-52 and 140-170); `trail/sdd/self_answer-10.md`. Measured: `git diff --stat 9b05680c7 HEAD --
  products/tracker17 ':!products/tracker17/docs'` at `72d80bffa` → `products/tracker17/README.md | 2 +-`,
  one line of the Status paragraph (`819818875`), no heading (`git diff … | grep -c '^[-+]#'` → 0).
  No suite was run: the item is about whether recorded runs settle a case, the record holds the
  count at its commit, no code moved since, and this round changes no code.

The companion held one open item, § 2.1, `Seat: cto`, raised by the previous `companion-self-answer`
run on this companion; §§ 5.1 and 5.2 were already filled. The invocation listed no items, so this
run worked the one open item. It did not split: one question, one seat.

## Items worked

### 2.1 — § 11 R-2 and the first Open Question still call the confirmation case unverified; its tests have run and passed

- **Bucket:** 2. Choices to confirm — a best-effort answer was drafted; confirm or override
- **Verdict:** confirmed with addition
- **Why:** The draft is right and holds for the reason it gives; four things are added so the
  sentence R-2 gains claims exactly what the record shows.

  *Seat (check 1).* The edit lands in § 11 and § Open Questions, both CTO rows of § *Who decides
  what*, and binds only this document's agreement with the product's tests. No person, party or
  risk is committed, and I can name no ground I cannot see. Mine. The item was raised by a run in
  this same seat, so I read it as a colleague's proposal and put it through the checks rather than
  taking it as already decided.

  *The draft holds (check 2).* The four tests exist where the item says and cover the three parts
  of R-2's case: `test_keyboard_opening_focuses_the_visible_sentence` (174) expects the sentence
  focused and in the viewport, with repeated Enter and Space changing nothing;
  `test_keyboard_confirming_and_back_out_use_their_own_intents` (208) expects the trigger focused
  and in the viewport after backing out; `test_double_click_never_confirms_at_the_original_trigger_coordinates`
  (321) double-clicks for real, on `short-row`, `task-page` and `row-40-of-60` with
  `window.scrollY > 0`; `test_keyboard_opening_on_a_far_row_focuses_the_visible_sentence` (606)
  does the focus case on row 40 of 60, scrolled. The count, 67 passed at `9b05680c7` in a fresh
  clone, is the refine report's first "Considered, not moved" row and the unit's code-integrity
  report ("The browser folder … `67 passed in 30.68s`, with no skip"). RN-36 closed the form-control
  case and RN-41 the not-a-control case, so the draft's "as RN-36 and RN-41 closed the other two"
  is right. § 7's `validates` row says the tests "show whether", which stays true once they show
  that they can. **Addition one** is the dated form: the draft's "printed nothing on 2026-10-20"
  was true at `ca2f9e98a` and is not true at `72d80bffa`, where the diff lists one README line and
  no code. The README's headings did not change and the only test reading it is layer 3, so "no
  product code moved" still holds — but the sentence R-2 gains is written as a count at its commit
  with a dated diff, the form R-2 already uses and the form NFDR RN-15 settled on at
  `trail/architecture/cycle-11.md` § 3.1 ("stop claiming that nothing has moved since — any such
  sentence goes false at the next merge"). **Addition two** is where the browser build comes from.
  The refine record names no build; the run itself does: `test_moves.py:541` asserts
  `browser.version == PINNED_BROWSER`, `"153.0.8010.12"`, inside the history matrix, one of the
  67. The four focus tests run on the headless shell of the same install (`conftest.py`, `browser`
  fixture) and the assertion is on the full Chromium of that install (`history_browser`,
  `channel="chromium"`), both from `playwright==1.63.0`. R-2 says that, as RN-41 said
  `tabindex="-1"`: a sentence written from the item's words alone would claim the build was
  measured on the focus tests' binary, which it was not. I was close to a plain *confirmed*; this
  is what tipped it. **Addition three** is that the change is a correction and not a § 10 re-cut:
  no *Reached when*, fence, place or § 7 edge moves, S-4's *Why here in the order* and TO-2 explain
  an ordering and stand. **Addition four** names what stays open downstream and why nothing is
  raised there (below).

  *Nothing settled moves (check 3).* SRS NFR-13 bounds the product to Chromium-based browsers,
  where the tests ran. UXD UX-I2 and § 4 EX-6 are what the tests show; neither moves. ADR-0003's
  no-script decision gains evidence and does not move. My answer to 5.1 in `self_answer-10.md`
  rests on the same 67-passed run at the same commit; the two agree. The settled form for dated
  results (`cycle-11.md` § 3.1) is followed, not contradicted. **Downstream, considered and not
  raised:** `nfdr.md` RN-15 ("What stays open is two cases. The first is the confirmation of SDD
  § 4 EX-6") and ADR-0003's *Dependence* will read stale once this folds. Both are the Principal
  Architect's and read this document (§ 12). The precedent is NFDR RN-23: when SDD version 6 closed
  two of the three questions RN-15 counted, the Principal Architect caught it by reading the SDD's
  change, with no companion item. Today the NFDR's sentence is true — the SDD still lists the case
  open — so there is no false fact to raise, and `architecture_open_issues.md` is live and owed a
  round that reads the SDD as it then stands. If `product-architecture` runs before `product-sdd`
  folds this, RN-15 goes stale with nothing scheduling its catch-up; that is the one thing a reader
  who disagrees would hold against this, and the fold's Review Note is where it is answered.

  *Failure paths (check 4).* *Empty*: the tests make their own project and tasks; nothing rests on
  prior state. *Absent*: the browser folder runs only where layer 5 runs (macOS or the listed
  Linux); the 2026-10-19 Fedora run gave `2 passed, 34 errors` before any test ran. The count is a
  count on the owner's Mac at a commit and claims nothing wider; R-9 covers Linux. *Stale*: a
  Chromium release that moves focus or double-press behaviour is R-2's own trigger — the four tests
  stay among them and both suites run on every slice (TS-1). NFDR RN-33's dated exception to QC-40
  ends 2026-11-07, after which the pin moves and the tests run against a newer build; the trigger
  is what catches it, and R-2's bound (the operator's current Chrome against the pinned build)
  stands. *Concurrent*: another tab moving the task between press and confirm is the out-of-date
  case, seed item 3, not this. *Refused*: a first press for a move no longer allowed opening no
  confirmation is `test_stale_first_press_refuses_at_the_visible_current_status` (365), EX-6's last
  sentence and not part of R-2's three-part case; not claimed by the answer.

## Left for the owner

None this run.

## Skipped

- **5.1 — No record names how a move's pages behave in the browser's history** — its **Answer**
  slot is already filled (by `self_answer-10.md`); an answer already given is left as it stands.
- **5.2 — § 6 S-4's bar has an out-of-date move offer a reload; UX-I3 now says it offers none** —
  its **Answer** slot is already filled (by `self_answer-10.md`); left as it stands.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
