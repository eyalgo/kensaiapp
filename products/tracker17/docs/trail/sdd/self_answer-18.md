# Self-answer report — SDD.md

## Header

- **Companion:** products/tracker17/docs/SDD_open_issues.md
- **Document:** products/tracker17/docs/SDD.md (version 17)
- **Decided by:** `<CORE>/../skills/companion/.claude/skills/companion-self-answer/prompts/rich.md` v1.3.1
- **Date:** 2026-10-30
- **Sources re-read:** None — no answer rests on a source outside this repository. Read in this
  repository at `136cc55d8`: the companion whole; `SDD.md` whole (Parts A to D, and the review
  notes at every line naming a save, a hand change or the state in memory — RN-6, RN-69, RN-70,
  RN-71); `SRS.md` FR-8, NFR-3, DR-6; `UXD.md` § 4 and UX-S9; `fdr.md` R-20 and OOS-16;
  `fdr_open_issues.md` §§ 3.1 and 3.2 with `trail/fdr/self_answer-3.md`; `trail/sdd/self_answer-17.md`;
  `web/routes.py` (`UnreadableSite`), `main.py` (`start`, `_serve_claimed`),
  `persistence/saved_data.py` (`save`); the open station the item's raiser walks, as an input.

## Items worked

### 2.1 — § 9 TO-4's "overwritten by the next save" does not hold while the unreadable-data page shows

- **Bucket:** 2. Choices to confirm — a best-effort answer was drafted; confirm or override
- **Verdict:** confirmed
- **Why:** The draft is taken as it stands, its rewording of TO-4's bold sentence included. Check 1:
  the edit lands in § 9, a CTO column in § *Who decides what*, and binds the document's consistency
  and nothing outside it — no person, money or risk — so it is this seat's. The item carries a
  Principal PM `Raised by:` under a § 2 heading that the header reserves for the three lane seats; it
  carries a real lean, so it is weighed as a draft and not re-bucketed. Check 2: every citation
  holds — `SDD.md:1270-1271` carries the sentence with no mode; `web/routes.py:1339`,
  `UnreadableSite`, says "no tracker, no reader and no saver"; § 4 SD-4 forbids the write; § 4 EX-13
  cites TO-4 for the mode fixed at start; RN-69 says a repair made while the page shows "is read at
  the next start"; FDR R-20 (`fdr.md:98-100`) traces to TO-4 and its matching correction is answered
  on `fdr_open_issues.md` § 3.1. The argument carries its conclusion for the reason it gives: a
  correction of a statement false in one mode, not a widening, and it cites its occurrence. The
  bold sentence's change, "the state" to "a readable state", is what keeps the heading true in both
  modes, and what cites it survives: EX-13 leans on "read only at start" and RN-6 on the in-memory
  state being the saved data's, which "a readable state" still says. Check 3: it agrees with SD-1
  ("read once, at start, and never again"), SD-4, EX-13, RN-69, S-8's bar ("nothing was changed"),
  SRS FR-8 and DR-6 ("At start"), and with the corrected R-20, whose "its next save replaces that
  change" is the same statement in the FDR's words; OOS-16's "read only at start" holds under both.
  Nothing else in the SDD carries the sentence (`grep -n "by hand\|next save"` hits TO-4 alone).
  The *buys* clause holds in both modes, and *undoing it costs* already names the mid-run decision
  the SRS does not make. Check 4: absent — a file removed by hand while the page shows leaves the
  next start empty, which "the next start reads it" covers; stale — the hand change is never shown
  while this tracker runs, in either mode, and the draft says so for the unreadable one; concurrent
  — `main.py` `start` claims the location before it loads, so "the next save" is this tracker's own
  and a second start is refused in both modes; refused — a POST on unreadable data is redirected
  with its body unread, so no save arises. One case named and not added: a tracker serving its data
  that makes no further save before it stops leaves the hand change on disk for the next start.
  The sentence does not claim a save comes, TO-4 is a trade-off and not a rule, and FDR R-20 reads
  the same way, so the case is recorded here and not written in. The close call was *confirmed with
  addition* for that case; it lost because the addition would state what the sentence already does
  not deny.

## Left for the owner

None this run.

## Skipped

None this run.

## Companions opened

None this run.

## Launchers owed

- **products/tracker17/docs/SDD.md** — `<CORE>/launchers/skill/launcher.sh product-sdd tracker17`
