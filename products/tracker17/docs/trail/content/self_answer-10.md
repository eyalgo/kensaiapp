# Self-answer report — CONTENT.md

## Header

- **Companion:** products/tracker17/docs/CONTENT_open_issues.md
- **Document:** products/tracker17/docs/CONTENT.md
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-13
- **Sources re-read:** None. No answer this run gave rests on a source outside this repository. Everything it leans on was read in this repository on 2026-10-13: `CONTENT.md` (v10), `UXD.md`, `SRS.md`, `SDD.md`, `nfdr.md`, `products/tracker17/tests/timed_run.py`.

## Items worked

### 3.1 — Whether § Scope governs what the timed run prints

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write the verbal language
- **Verdict:** answered
- **Why:** No. § Scope does not reach the timed run's output, and § Scope should say so in one added clause. The item carries no draft, so this was decided from scratch.

  *Seat.* The question is `CONTENT.md`'s own: what its Scope covers, and the edit lands in § Scope of this document. The answer binds no person and no outside party, and I could name no ground the owner holds that I can't see. So it is mine to answer in the owner's seat. It is one question and doesn't split. It states a case the document doesn't state now, so § *A widening item waits until it occurs* applies, and it is met: the item cites sites in the product as it stands, `tests/timed_run.py:153` and `:158` (the "refused or failed" verdict and the em-dash row) and `:691` and `:783` (the semicolon-joined fixture lines), which I re-read there. So "not until it occurs" does not apply.

  *Check 2, the question.* The item asks whether the timed run is within "every word tracker17 says to a person". The test in § Scope is who says the words, and the item's own facts show the timed run is not the tracker speaking:
  1. The run is a script a developer starts, `python3 tests/timed_run.py` (`tests/timed_run.py:L5-L9`). It runs `Site.handle` in-process on locations of its own in a temporary directory. It never starts the tracker, so its output is not "the text the tracker prints in the terminal it was started from" (`CONTENT.md` § Scope).
  2. It lives in `tests/` and is a verification instrument. SRS AC-15 and NFR-1 call it "a timed run on the owner's machine" (`SRS.md:L519-L521`), SDD TS-5 gives it its job (`SDD.md:L462-L465`), and NFDR QC-48 has it fail on a refused action and state its text lengths (`nfdr.md:L412-L415`). None of the three says anything about its wording. § Scope already excludes the two things that sit in the same place, a code comment and a test name.
  3. No UXD state names it. `grep -n -i 'timed' UXD.md PRD.md DESIGN.md` printed nothing (2026-10-13). § Traceability maps every rule to a UXD state, and the UXD's terminal surface is the start command alone (`UXD.md:L310`, UX-S2).
  4. The rules can't be applied to a row. § Voice asks every line that reports an action to name the actor and the resulting state, and starts it "You" or "The tracker". A row such as `comment total at 1000 tasks: 12.3 ms` reports a measurement, not an action the reader took, so a rule applied to it would produce nonsense or demand a new pattern for a state no document names.

  *Check 3.* Nothing settled requires the opposite. SDD TS-5 and NFDR QC-48 require the run to state its text lengths and to fail on a refused action, and impose no wording. § Terminology's "failed" ban reads "as a label or about what the reader typed", so it is about the product's reader and doesn't reach a harness verdict. My earlier answers in this companion: none, since 3.1 is its only item.

  *What the document becomes.* § Scope adds, in its own words, that the language governs no output of a script a developer runs to check or measure the tracker, such as the timed run, because the tracker doesn't print those words. It adds the boundary clause as well: where such a script prints a string the tracker wrote, the string is governed where the tracker writes it. I state the kind, not the file, because `CONTENT.md` holds standing rules and a path can move (RN-16 says the same of the files it names). The fold words it, and can record it as RN-25 with the occurrence `tests/timed_run.py:153`, `:158`, `:691`, `:783`.

  *Failure paths.* Empty: a script that prints nothing has no words, so the rule has nothing to say. Concurrent, the boundary case: a row that echoes a page's text would be the tracker's string. The run prints none today. Its `print` sites (`timed_run.py:156`, `:807`, `:811`, `:817`, `:823`, `:854`) print the harness's own labels, times and fixture reports, and the completion line is only checked, at `:472`. The boundary clause covers it if that changes. Stale, not covered by the answer and named here: it holds while the UXD names no such surface. If the UXD or the setup instructions ever make the timed run's output something the reader is told to read, § Scope follows the UXD, which is where states are named. That is the CDO's change to make first and it is not owed now. Absent and refused: the "refused" in the run's verdict means the product refused the action. The product's refusal text is governed where the product writes it (`web/pages.py`), and the harness doesn't repeat it.

  *Close call.* The other reading is that the owner reads these rows in a terminal, so the language should bind them. What would tip it is the UXD naming the run's output as a surface, or the owner wanting one voice across everything a terminal shows. Neither is stated anywhere I read, and the second is a taste call the owner can overrule by overriding this slot. If they do, the rows need a pattern for a measurement first, and the dash, the semicolon and "failed" are the smaller part of that work.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/CONTENT.md** — `<CORE>/launchers/skill/launcher.sh product-content tracker17`
