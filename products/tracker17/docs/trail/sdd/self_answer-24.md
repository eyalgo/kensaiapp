# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md (version 22)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-11-13
- **Sources re-read:** None. Every claim the answer rests on is in this repository, read at
  `f3749d5bf`: the companion whole; `SDD.md` whole, §§ 1 to 12, its Review Notes prologue and the
  notes on re-cuts (RN-43, RN-60, RN-76, RN-80, RN-81), and its Open Questions; `PRD.md` § Core
  Features, Project summary and Due dates (version 9); `SRS.md` § 3.11 FR-38, § 3.8 FR-25, AC-13,
  AC-14 and RN-26 (version 8); `UXD.md` § 5.6 UX-F6, § 4 UX-S5 and RN-38 (version 12);
  `trail/uxd/cycle-10.md` § 3.1 whole; `CONTENT.md` § Terminology's "Due on {date}" row, § Accessibility
  of text and RN-36 (version 22); `fdr.md` § Project summary R-96 to R-99 (version 6; no due-today
  count); `nfdr.md` and `DESIGN.md` grepped for the summary; `what_left.md` whole; the seed
  `system/projects/tracker17/journey/nemawashi/unpicked/2026-11-13_the-sdd-carries-the-due-today-count.md`
  whole, and the open station `2026-11-13_the-ignored-sigint-cause` for the commit's directional alone.
  Under the product root: `domain/summary.py` whole, `application/tracker.py` at `project_summary`
  (one clock read, lines 298 to 305), `web/pages.py` at `summary_page`, `tests/architecture/test_trace.py`
  at `LANDED_FEATURE_WORDS`, the test names in `tests/unit/test_summary.py` and `tests/e2e/test_summary.py`,
  and `tests/timed_run.py` at its Summary step. `grep -ciE 'due.today' products/tracker17/docs/SDD.md`
  printed `0`, as the item says. No test suite was run; this run changes no code and no document.

## Items worked

### 5.1 — The project-summary slice delivers no due-today count, and PRD version 9, SRS version 8 and UXD version 12 require one

- **Bucket:** § 5. Raised from downstream — an item from a seat that did not write the SDD
- **Verdict:** answered
- **Why:** The item carries no draft, so it was answered from scratch. **Check 1 — the seat is the
  CTO's, in the owner's seat.** The edit lands in § 6 S-6, § 7 and § 10, and the item's three
  questions are § 5 step 2's and step 4's (slice or re-cut), § 7's (the edge) and § 4's fifth
  group's (what the tests must hold), every one of them the CTO's by § Who decides what. The
  clauses of S-6 that the CPO and the CDO decide move only to restate what their own documents now
  say — the PRD at version 9 and the UXD at version 12 — so no item is owed either seat, as RC-3 and
  RC-6 folded the PRD's and the UXD's moves without one. Nothing binds a person, money or a risk
  outside the document; no ground is unseen. Not the owner's: the owner already made the call, in
  `trail/prd/cycle-7.md` § 1.1, and this answer only carries it down. **Check 2 — the question is
  sound and is one question.** Three parts, one seat, so one slot. It widens the document, and it
  cites its occurrence twice over: `what_left.md` names the count as not built at `7ffd5c365`, and
  `grep -ciE 'due.today'` over `SDD.md` prints `0`, which I re-ran; it is also a correction, because
  S-6 claims to trace UX-F6 and UX-F6 now names a count S-6 does not, so "not until it occurs" does
  not apply. Its supporting text is right on every point I checked: S-6 is built and retired
  (`CHANGELOG.md`, the Summary entry; `LANDED_FEATURE_WORDS` holds `summary`), § 10 counts RC-1 to
  RC-6, and the SRS and UXD quotations match the files. **The answer.** A re-cut of S-6, not a ninth
  slice. § 5 step 2 strikes a cut whose only value is what a later cut gives it, and step 4 calls a
  slice too narrow when finishing it cannot change what happens next; a slice made of one plain
  number in a table that exists is both, and the count is inside S-6's *Delivers* as written, "where
  the project stands". RC-3 is the precedent in this document: FR-41's paragraph landed in
  `first-project`'s *Artifact* with "no new part and no new slice, and a slice made of it alone would
  be the fragment § 5 step 2 strikes", leaving the bar unmet on the day of the fold for the build to
  meet. The seed that raised this item already plans the same shape: its *Out* says "the seed that
  builds the count in the product" waits for the SDD, and § 8 lets a slice's *Reached when* divide
  across seeds. Whose ground moved is the CPO's, carried down by the SRS and the UXD, and one record
  covers all three as RC-3 covered two. § 7 does not move: the one edge into `project-summary` rests
  on the linked counts (its *Why* column says so), and the due-today count is a plain number by
  UX-F6, so no dependency is added, and the data it needs is already in by `tasks-in-a-project` and
  `status-moves`. § 4's fifth group holds as written: I read each of TS-1 to TS-6 against the count
  and none changes — the `summary` row already names FR-38, which now states the count; the clock is
  handed in (TS-2) and the product already reads it once per summary (`application/tracker.py`,
  `project_summary`); the timed run already opens a summary (TS-5); the fake clock already supplies
  a date (TS-6). I was close to adding a § 4 condition for the one-"today" rule, and did not: FR-38
  binds it on the summary alone, FR-25's "the moment the system produces the list, the summary or the
  filter result" already binds every date-dependent read, and § 3 `SM-2` — one date crossing inward
  per read — is the design fact that makes it hold, so a new condition would restate the SRS and
  § 3 for a case no slice outside S-6 can break. It lands in S-6's behaviour line instead. The label
  is CONTENT's, "Due on {date}" (CONTENT version 22, RN-36), not "Due today", because a summary read
  after midnight would otherwise lie; the SDD keeps the definition phrase and names no label, under
  § 4 EX-11. **Check 3 — nothing settled moves.** § 12 still holds: the answer changes no
  requirement and nothing of the experience; it follows them. S-6's fence, "a summary across
  projects", stands and the new fence line adds the two forms RN-26 excludes. No earlier answer in
  this file bears on it, and no claim rests on a source outside the repository. **Check 4 — failure
  paths.** Empty: an empty project shows the count as 0 with the rest (UX-F6's failure line, UX-S5).
  Absent: a task with no due date is in the no-due-date count and never in this one. Stale: a
  summary is a snapshot (UX-I9; `tests/e2e/test_summary.py`,
  `test_browser_summary_stays_a_snapshot_until_reloaded`), its two date counts share one "today", and
  its label carries that date, so the page stays true after midnight. Concurrent: a task another tab
  adds due today shows on the next load, by § 4 RT-7, and the summary read holds RT-6's lock.
  Refused: nothing to refuse — a plain number, no link and no form; while the saved data cannot be
  read, the summary address shows the unreadable-data page as every address does (§ 4 EX-13),
  unchanged. **Not raised, and why.** The FDR (R-96) and the NFDR carry no due-today count; the item
  and the seed state that both follow the SDD and that the Principal PM re-runs the FDR after this
  seed retires, so a companion on either now would double-track work a seat already owns and would
  fold before the SDD does. The product's README Status says nothing is left to build while
  `what_left.md` names the count; that is a product artifact S-6's build meets (§ 4 EX-12, the
  instructions describe the tracker as it stands), not a definition document. The header's *Inputs
  read* line reads PRD 8, SRS 7 and UXD 11, and the fold this report owes catches it up, as every
  prior fold did without an item (RN-60, RN-66, RN-70; self_answer-23 declined it for the same
  reason).

## Left for the owner

None this run.

## Skipped

None this run. § 5.1 is the companion's only item; its **Answer** slot was at its placeholder and is
now filled.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
