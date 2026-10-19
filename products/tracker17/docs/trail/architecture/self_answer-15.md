# Self-answer report — `adr/` and `nfdr.md`

## Header

- **Companion:** `products/tracker17/docs/architecture_open_issues.md`
- **Document:** `products/tracker17/docs/adr/` and `products/tracker17/docs/nfdr.md` (NFDR version 12, Settled)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-13
- **Sources re-read:** None. The answer rests on files and commits in this repository: `nfdr.md:L730-L761` (RN-15), `adr/0003-no-script-in-any-page.md` (*Dependence*, `## Binds`), `tests/e2e/test_comments.py:L89` and `:L171`, and `web/pages.py:L948`. It also rests on one suite run made by this run (below).

## Items worked

### 3.1 — RN-15 says no product code has moved since the People focus run at `641bb58b5`; the comment code has

- **Bucket:** 3. Raised from downstream — an item from a seat that did not write these records
- **Verdict:** confirmed with addition
- **Why:** One sentence in RN-15 is now false. `nfdr.md:L736-L738` says the People focus tests "passed at `641bb58b5` … and no product code has moved since". `git diff --stat 641bb58b5 4f6f59752 -- products/tracker17/web products/tracker17/domain` gives `12 files changed, 2350 insertions(+), 26 deletions(-)`, and `domain/comments.py` is one of them. This corrects a false statement, so it is not a widening. The item also cites the occurrence: the two comment tests on disk. I read "The change asked" as the draft. The change is right.
  - **The addition: tie each result to its commit, and make no "since" claim.** Change "no product code has moved since" to a newer date and the sentence goes false again at the next merge. That is how this one went false. RN-15 already names a commit for each result, so a reader can check staleness with `git diff <commit>`. The fold should drop the present-tense claim and write no replacement for it.
  - **What the comment tests prove.** `web/pages.py:L948` gives the added comment `tabindex="-1" autofocus aria-describedby`. That makes it a second element that is not a control and is focused on page load, which is the case ADR-0003's *Dependence* says was unverified. So the comment tests are more evidence for RN-15's "what is verified". They do not reach either open case. The EX-6 confirmation is still settled by SDD § 6 `status-moves`. Whether assistive technology speaks the description (EX-14) is still settled by one VoiceOver pass. A computed description does not prove the line is spoken.
  - **The measured verdict, checked here.** The PM measured 33 passed at `4f6f59752`. This run made a fresh clone (`git clone` and `checkout c0e4d65f4`, under `/tmp`, per `<CORE>/roles/CROSS_ROLE.md` § *Every seat*). It installed `tests/requirements.txt` in a `.venv` and ran `pytest -q tests/e2e/`: `33 passed in 8.66s`, playwright 1.63.0 (`python -m playwright --version`), and Chromium `153.0.8010.12` (`browser.version`). Between `4f6f59752` and `c0e4d65f4`, `git diff` shows nothing changed in `products/tracker17` outside `docs/` except `README.md`. The two runs therefore tested the same code and tests.
  - **What stays.** ADR-0003 stays Accepted and unedited. Its decision did not move, and its *Dependence* was true on its date. That matches RN-15's own rule for both records. QC-34's obligation and trace do not change. The People result stays as evidence at `641bb58b5`.
  - **Failure paths.** *Stale*: this is the case the addition handles. A result tied to a commit never goes false, and a "since" claim always eventually does. *Refused*: if a later Chromium fails a comment focus test, RN-15's existing fallback applies, as a record superseding ADR-0003. Nothing new is needed for that. *Concurrent/flaky*: I ran the suite once, so one green run does not prove it never fails. RN-15 should state the result as a count at a commit, not as a guarantee.
  - I considered *confirmed* and did not choose it. The item fixes the wording but not what made it go false. The addition fixes that.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **`products/tracker17/docs/nfdr.md`** — `<CORE>/launchers/skill/launcher.sh product-architecture tracker17`
