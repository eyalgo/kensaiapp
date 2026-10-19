# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-07
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Everything it leans on was read in this repository on 2026-10-07: `main.py`, `docs/SDD.md` § 4 RT-5, `tests/e2e/test_start_command.py`, `tests/integration/test_start.py`.

## Items worked

### 3.1 — The terminal-message examples name an address the tracker does not use

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** confirmed with addition
- **Why:** Both examples are changed to `127.0.0.1:8017`, and neither gets a note calling the address a placeholder.

  *Seat.* The item is `CONTENT.md`'s. The edit lands in two example lines of this document, binds no person and no outside party, and I could name no ground the owner holds that I can't see. It is one question, so it doesn't split.

  *Widening.* It isn't one. It asks for a false statement to be corrected, not for the document to state a new case, so "not until it occurs" doesn't apply.

  *Check 2.* The item's facts hold. `CONTENT.md:250` and `CONTENT.md:278` both name `127.0.0.1:8000`, and no other line of `CONTENT.md` names a port (`grep -nE "8000|8017"` over the product, outside trail). `main.py:20` reads `ADDRESS = ("127.0.0.1", 8017)`, and `SDD.md:286` records the address as `127.0.0.1:8017`, fixed in one constant. The item leaves a doubt open: the examples may be illustrations only. That doubt is the part I decided.

  *Why 8017 and not a placeholder note.* The terminal strings aren't fixed text. They fill the address from the one the start was given (`main.py:55`, `main.py:61`), and `tests/integration/test_start.py:130-136` checks that a start on another port prints that port. In a real run of the product the address is `127.0.0.1:8017`, and `tests/e2e/test_start_command.py:22` expects exactly that line. So the example with 8017 is the string the reader sees, and 8000 is a string the product never prints. A note saying the address stands for the tracker's own would add words to a document whose job is saying less (§ Voice), and it would still leave a wrong number on the page for the next writer to copy. `/Users/sam/tracker17/data` in the same examples is plainly somebody's path. A port number isn't, which is why the same doubt doesn't reach it.

  *Check 3.* The change doesn't move anything settled. `CONTENT.md:27-28` says the examples illustrate a rule and specify no screen, and the corrected examples still do that. The Localization section keeps addresses out of translation (`CONTENT.md:394`), and the Grammar section allows a colon inside an address (`CONTENT.md:108-110`), so `127.0.0.1:8017` breaks no rule. No upstream document names a port (`SDD.md:1614-1615`), so the SDD is the one owner of the number, and this answer restates it only as an example.

  *Check 4.* One case isn't covered, and I'm naming it. If the SDD's `ADDRESS` constant ever changes, the two examples go stale the same way the 8000 did. Nothing in this answer keeps them in step, and it shouldn't try: a line that would need editing when a feature ships is per-change copy, and the address is fixed by RT-5, not by a change. The same fold that follows an SDD change would carry it. Empty, absent, concurrent and refused have no meaning for an example line.

  *Close call.* The verdict was close to *overridden* if the proposal's second option, the placeholder note, had been the better one. What tipped it to 8017 is `main.py:55` and `main.py:61`: the product itself prints the real address in every ordinary run.

  *For the fold.* The version and a review note are the fold's to write. `CONTENT.md` currently has no review note about the terminal examples, and RN-16 names the terminal's two lines in `main.py` as part of the corpus.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
